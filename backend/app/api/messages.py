"""
Messages API with multi-tenant isolation.
Uses institution-based tenancy with audit logging.
"""
from fastapi import APIRouter, HTTPException, status, Depends, Request
from typing import List
from datetime import datetime
from bson import ObjectId

from app.core.database import get_database, get_default_database
from app.core.tenant import get_tenant_dependency, TenantContext, is_super_admin
from app.core.tenant_strategy import TenantAwareRepository
from app.core.audit import AuditLogger, AuditAction
from app.models.message import MessageCreate, MessageResponse, ConversationResponse
from app.models.user import UserRole

router = APIRouter(prefix="/api/messages", tags=["Messages"])


async def verify_message_access(message_id: str, tenant: TenantContext, database) -> dict:
    """
    Verify the current user has access to this message.
    
    MULTI-TENANCY RULES:
    - Must be in the same institution
    - Students can access messages where:
      * They are the student (student_id matches their ID)
      * They are sender or recipient
    - Counsellors can access messages where:
      * They are sender or recipient
      * The student_id is assigned to them
    """
    repo = TenantAwareRepository(database, "messages")
    mid = validate_object_id(message_id, "message_id")
    msg = await repo.find_one(tenant.institution_id, {"_id": mid})

    if not msg:
        raise HTTPException(status_code=404, detail="Message not found")
    
    # Check access based on role
    if tenant.role == UserRole.STUDENT:
        # Students can access messages where:
        # 1. They are the student (student_id matches)
        # 2. They are sender or recipient
        if (msg.get("student_id") != tenant.user_id and 
            msg["sender_id"] != tenant.user_id and 
            msg["recipient_id"] != tenant.user_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied - this is not your message"
            )
    elif tenant.role == UserRole.COUNSELLOR:
        # Counsellors can access messages where:
        # 1. They are sender or recipient
        # 2. The student_id is in their assigned students (check if assigned)
        if msg["sender_id"] != tenant.user_id and msg["recipient_id"] != tenant.user_id:
            # Check if student_id is assigned to this counsellor
            if msg.get("student_id"):
                assigned_students = await database.users.find({
                    "institution_id": tenant.institution_id,
                    "_id": ObjectId(msg["student_id"]),
                    "assigned_counsellor_id": tenant.user_id,
                    "role": "student",
                    "is_active": True
                }).to_list(length=1)
                
                if not assigned_students:
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail="Access denied - you are not part of this conversation"
                    )
            else:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Access denied - you are not part of this conversation"
                )
    
    return msg


@router.post("/", response_model=MessageResponse, status_code=status.HTTP_201_CREATED)
async def send_message(
    message: MessageCreate,
    request: Request,
    tenant: TenantContext = Depends(get_tenant_dependency)
):
    """
    Send a message.
    
    MULTI-TENANCY:
    - sender_id is set from tenant context
    - Recipient must be in the same institution
    - student_id is automatically determined for tenant isolation
    """
    database = await get_database()
    
    # Verify recipient exists in the same institution
    recipient = await database.users.find_one({
        "_id": ObjectId(message.recipient_id),
        "institution_id": tenant.institution_id
    })
    
    if not recipient:
        raise HTTPException(
            status_code=404, 
            detail="Recipient not found in your institution"
        )
    
    # Students may only message their assigned counsellor
    if tenant.role == UserRole.STUDENT:
        sender_doc = await database.users.find_one({"_id": ObjectId(tenant.user_id)})
        assigned_id = (sender_doc or {}).get("assigned_counsellor_id")
        if not assigned_id or str(recipient["_id"]) != str(assigned_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You may only message your assigned counsellor"
            )
    
    # Determine student_id for multi-tenancy
    if tenant.role == UserRole.STUDENT:
        student_id = tenant.user_id
    elif recipient["role"] == UserRole.STUDENT:
        student_id = str(recipient["_id"])
    else:
        student_id = None
    
    # Get sender info for response
    sender = await database.users.find_one({"_id": ObjectId(tenant.user_id)})
    
    repo = TenantAwareRepository(database, "messages")
    
    message_dict = {
        "sender_id": tenant.user_id,
        "recipient_id": message.recipient_id,
        "subject": message.subject,
        "content": message.content,
        "student_id": student_id,
        "is_read": False,
        "created_at": datetime.utcnow(),
        "read_at": None
    }
    
    result = await repo.insert_one(tenant.institution_id, message_dict)
    
    # Audit log
    await AuditLogger.log_action(
        institution_id=tenant.institution_id,
        user_id=tenant.user_id,
        action=AuditAction.CREATE,
        resource_type="message",
        resource_id=str(result.inserted_id),
        request=request,
        metadata={"recipient_id": message.recipient_id}
    )
    
    # Mask previous counsellor names if applicable
    sender_name = sender["full_name"] if sender else "Unknown"
    recipient_name = recipient["full_name"]
    
    return MessageResponse(
        id=str(result.inserted_id),
        sender_id=tenant.user_id,
        sender_name=sender_name,
        recipient_id=message.recipient_id,
        recipient_name=recipient_name,
        subject=message.subject,
        content=message.content,
        is_read=False,
        created_at=message_dict["created_at"],
        student_id=student_id or tenant.user_id
    )


@router.get("/", response_model=List[MessageResponse])
async def get_messages(
    request: Request,
    tenant: TenantContext = Depends(get_tenant_dependency)
):
    """
    Get all messages.
    
    MULTI-TENANCY:
    - Automatically filtered by institution_id
    - Students see messages where:
      * They are the student (student_id matches their ID)
      * They are sender or recipient (to see messages they sent/received)
    - Counsellors see messages where:
      * They are sender or recipient (to see messages they sent/received)
      * The student_id is in their assigned students list
    """
    database = await get_database()
    repo = TenantAwareRepository(database, "messages")
    
    # Build query based on role
    if tenant.role == UserRole.STUDENT:
        # Students can see messages where:
        # 1. They are the student (student_id matches their ID)
        # 2. They are sender or recipient (to see messages they sent/received)
        query = {
            "$or": [
                {"student_id": tenant.user_id},
                {"sender_id": tenant.user_id},
                {"recipient_id": tenant.user_id}
            ]
        }
    elif tenant.role == UserRole.COUNSELLOR:
        # Counsellors can see messages where:
        # 1. They are sender or recipient (to see messages they sent/received)
        # 2. The student_id is in their assigned students list
        # Get list of assigned student IDs
        assigned_students = await database.users.find({
            "institution_id": tenant.institution_id,
            "assigned_counsellor_id": tenant.user_id,
            "role": "student",
            "is_active": True
        }).to_list(length=None)
        
        assigned_student_ids = [str(s["_id"]) for s in assigned_students]
        
        # Build query: messages where counsellor is sender/recipient OR student_id is assigned
        # Always include sender/recipient check first (most important)
        or_conditions = [
            {"sender_id": tenant.user_id},
            {"recipient_id": tenant.user_id}
        ]
        
        # Only add student_id condition if there are assigned students
        if assigned_student_ids:
            or_conditions.append({"student_id": {"$in": assigned_student_ids}})
        
        query = {"$or": or_conditions}
    else:
        # Admin can see all messages in their institution
        query = {}
    
    cursor = await repo.find(
        tenant.institution_id,
        query,
        sort=[("created_at", -1)]
    )
    
    messages = []
    async for msg in cursor:
        sender = await database.users.find_one({"_id": ObjectId(msg["sender_id"])})
        recipient = await database.users.find_one({"_id": ObjectId(msg["recipient_id"])})
        
        # Mask previous counsellor names for privacy
        sender_name = sender["full_name"] if sender else "Unknown"
        recipient_name = recipient["full_name"] if recipient else "Unknown"
        
        # If this is a message from a previous counsellor (masked), show masked name
        if msg.get("previous_counsellor_masked") and msg.get("masked_counsellor_id"):
            if msg["sender_id"] == msg.get("masked_counsellor_id"):
                sender_name = "Previous Counsellor"
            if msg["recipient_id"] == msg.get("masked_counsellor_id"):
                recipient_name = "Previous Counsellor"
        
        messages.append(MessageResponse(
            id=str(msg["_id"]),
            sender_id=msg["sender_id"],
            sender_name=sender_name,
            recipient_id=msg["recipient_id"],
            recipient_name=recipient_name,
            subject=msg.get("subject"),
            content=msg["content"],
            is_read=msg.get("is_read", False),
            created_at=msg["created_at"],
            read_at=msg.get("read_at"),
            student_id=msg.get("student_id") or msg["sender_id"]
        ))
    
    # Audit log
    await AuditLogger.log_action(
        institution_id=tenant.institution_id,
        user_id=tenant.user_id,
        action=AuditAction.LIST,
        resource_type="message",
        request=request,
        metadata={"count": len(messages)}
    )
    
    return messages


@router.get("/conversations", response_model=List[ConversationResponse])
async def get_conversations(
    request: Request,
    tenant: TenantContext = Depends(get_tenant_dependency)
):
    """Get conversation summaries."""
    database = await get_database()
    default_db = get_default_database()

    # Super admin: platform-wide conversations (all messages)
    if is_super_admin(tenant):
        user_id_str = str(tenant.user_id)
        pipeline = [
            {"$sort": {"created_at": -1}},
            {
                "$addFields": {
                    "sender_id_str": {"$toString": "$sender_id"},
                    "recipient_id_str": {"$toString": "$recipient_id"},
                }
            },
            {
                "$group": {
                    "_id": {
                        "$cond": [
                            {"$eq": ["$sender_id_str", user_id_str]},
                            "$recipient_id_str",
                            "$sender_id_str"
                        ]
                    },
                    "last_message": {"$first": "$content"},
                    "last_message_time": {"$first": "$created_at"},
                    "unread_count": {
                        "$sum": {
                            "$cond": [
                                {
                                    "$and": [
                                        {"$eq": ["$recipient_id_str", user_id_str]},
                                        {"$eq": ["$is_read", False]}
                                    ]
                                },
                                1,
                                0
                            ]
                        }
                    }
                }
            },
            {"$limit": 100}
        ]
        conversations = []
        async for conv in default_db.messages.aggregate(pipeline):
            try:
                participant_id = conv["_id"]
                if not isinstance(participant_id, str):
                    participant_id = str(participant_id)
                participant = await default_db.users.find_one({"_id": ObjectId(participant_id)})
                if participant:
                    conversations.append(ConversationResponse(
                        participant_id=participant_id,
                        participant_name=participant["full_name"],
                        participant_role=participant["role"],
                        last_message=conv["last_message"][:100] + "..." if len(conv["last_message"]) > 100 else conv["last_message"],
                        last_message_time=conv["last_message_time"],
                        unread_count=conv["unread_count"]
                    ))
            except Exception:
                continue
        return conversations

    repo = TenantAwareRepository(database, "messages")
    
    # Build query based on role
    if tenant.role == UserRole.STUDENT:
        # Students can see conversations where they are sender or recipient
        base_query = {
            "$or": [
                {"student_id": tenant.user_id},
                {"sender_id": tenant.user_id},
                {"recipient_id": tenant.user_id}
            ]
        }
    elif tenant.role == UserRole.COUNSELLOR:
        # Counsellors can see conversations where:
        # 1. They are sender or recipient
        # 2. The student_id is in their assigned students list
        # Handle assigned_counsellor_id as string or ObjectId
        counsellor_id_conditions = [{"assigned_counsellor_id": tenant.user_id}]
        try:
            counsellor_id_conditions.append({"assigned_counsellor_id": ObjectId(tenant.user_id)})
        except Exception:
            pass
        assigned_students = await database.users.find({
            "institution_id": tenant.institution_id,
            "$or": counsellor_id_conditions,
            "role": "student",
            "is_active": True
        }).to_list(length=None)
        
        assigned_student_ids = [str(s["_id"]) for s in assigned_students]
        
        # Always include sender/recipient check first (most important)
        or_conditions = [
            {"sender_id": tenant.user_id},
            {"recipient_id": tenant.user_id}
        ]
        
        # Only add student_id condition if there are assigned students
        if assigned_student_ids:
            or_conditions.append({"student_id": {"$in": assigned_student_ids}})
        
        base_query = {"$or": or_conditions}
    else:
        # Admin can see all conversations
        base_query = {}
    
    # Get collection using the same approach as get_messages
    from app.core.tenant_strategy import TenantStrategyFactory
    strategy = TenantStrategyFactory.get_strategy()
    
    # Apply tenant filter (this handles institution_id for row-level, or returns base_query for collection/db-per-tenant)
    query = strategy.get_tenant_filter(tenant.institution_id, base_query)
    
    # Get collection
    collection_name = strategy.get_collection_name("messages", tenant.institution_id)
    collection = database[collection_name]
    
    # Aggregate to get unique conversations
    # Use $toString to normalize ObjectId/string comparisons
    user_id_str = str(tenant.user_id)
    pipeline = [
        {"$match": query},
        {"$sort": {"created_at": -1}},
        {
            "$addFields": {
                "sender_id_str": {"$toString": "$sender_id"},
                "recipient_id_str": {"$toString": "$recipient_id"},
            }
        },
        {
            "$group": {
                "_id": {
                    "$cond": [
                        {"$eq": ["$sender_id_str", user_id_str]},
                        "$recipient_id_str",
                        "$sender_id_str"
                    ]
                },
                "last_message": {"$first": "$content"},
                "last_message_time": {"$first": "$created_at"},
                "unread_count": {
                    "$sum": {
                        "$cond": [
                            {
                                "$and": [
                                    {"$eq": ["$recipient_id_str", user_id_str]},
                                    {"$eq": ["$is_read", False]}
                                ]
                            },
                            1,
                            0
                        ]
                    }
                }
            }
        }
    ]
    
    conversations = []
    async for conv in collection.aggregate(pipeline):
        try:
            participant_id = conv["_id"]
            # Ensure participant_id is a string for ObjectId conversion
            if not isinstance(participant_id, str):
                participant_id = str(participant_id)
            
            participant = await database.users.find_one({
                "_id": ObjectId(participant_id),
                "institution_id": tenant.institution_id  # Ensure same institution
            })
            
            if participant:
                conversations.append(ConversationResponse(
                    participant_id=participant_id,
                    participant_name=participant["full_name"],
                    participant_role=participant["role"],
                    last_message=conv["last_message"][:100] + "..." if len(conv["last_message"]) > 100 else conv["last_message"],
                    last_message_time=conv["last_message_time"],
                    unread_count=conv["unread_count"]
                ))
        except Exception as e:
            # Log error but continue processing other conversations
            import logging
            logger = logging.getLogger(__name__)
            logger.warning(f"Failed to process conversation participant {conv.get('_id')}: {e}")
            continue
    
    return conversations


@router.put("/{message_id}/read", response_model=MessageResponse)
async def mark_as_read(
    message_id: str,
    request: Request,
    tenant: TenantContext = Depends(get_tenant_dependency)
):
    """Mark a message as read."""
    database = await get_database()
    repo = TenantAwareRepository(database, "messages")
    
    # Verify access
    msg = await verify_message_access(message_id, tenant, database)
    
    # Only recipient can mark as read
    if msg["recipient_id"] != tenant.user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only the recipient can mark messages as read"
        )
    
    await repo.update_one(
        tenant.institution_id,
        {"_id": msg["_id"], "recipient_id": tenant.user_id},
        {"$set": {"is_read": True, "read_at": datetime.utcnow()}}
    )
    
    sender = await database.users.find_one({"_id": ObjectId(msg["sender_id"])})
    recipient = await database.users.find_one({"_id": ObjectId(msg["recipient_id"])})
    
    # Audit log
    await AuditLogger.log_action(
        institution_id=tenant.institution_id,
        user_id=tenant.user_id,
        action=AuditAction.UPDATE,
        resource_type="message",
        resource_id=message_id,
        request=request,
        metadata={"action": "mark_read"}
    )
    
    return MessageResponse(
        id=str(msg["_id"]),
        sender_id=msg["sender_id"],
        sender_name=sender["full_name"] if sender else "Unknown",
        recipient_id=msg["recipient_id"],
        recipient_name=recipient["full_name"] if recipient else "Unknown",
        subject=msg.get("subject"),
        content=msg["content"],
        is_read=True,
        created_at=msg["created_at"],
        read_at=datetime.utcnow(),
        student_id=msg.get("student_id") or msg["sender_id"]
    )
