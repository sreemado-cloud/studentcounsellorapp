"""
Institution management API.
Institutions are the top-level tenants in the multi-tenant architecture.
"""
from fastapi import APIRouter, HTTPException, status, Depends, Query
from typing import List, Optional
from datetime import datetime
from bson import ObjectId

from app.core.database import get_database
from app.core.tenant import (
    get_tenant_dependency,
    require_institution_admin,
    TenantContext,
    is_email_super_admin,
    is_super_admin,
)
from app.core.audit import AuditLogger, AuditAction
from app.models.institution import (
    InstitutionCreate,
    InstitutionResponse,
    InstitutionUpdate,
    InstitutionSettings,
    InstitutionStats
)
from app.models.user import UserRole

router = APIRouter(prefix="/api/institutions", tags=["Institutions"])


@router.get("/", response_model=List[InstitutionResponse])
async def list_institutions(
    active_only: bool = Query(True, description="Only return active institutions"),
    limit: int = Query(50, le=100),
    skip: int = Query(0, ge=0)
):
    """
    List all institutions.
    Public endpoint for registration - users need to select their institution.
    """
    database = await get_database()
    
    query = {}
    if active_only:
        query["is_active"] = True
    
    cursor = database.institutions.find(query)\
        .sort("name", 1)\
        .skip(skip)\
        .limit(limit)
    
    institutions = []
    async for inst in cursor:
        institutions.append(InstitutionResponse(
            id=str(inst["_id"]),
            name=inst["name"],
            domain=inst.get("domain"),
            subscription_tier=inst.get("subscription_tier", "free"),
            settings=InstitutionSettings(**inst.get("settings", {})),
            is_active=inst.get("is_active", True),
            created_at=inst["created_at"],
            updated_at=inst.get("updated_at")
        ))
    
    return institutions


@router.post("/", response_model=InstitutionResponse, status_code=status.HTTP_201_CREATED)
async def create_institution(institution: InstitutionCreate):
    """
    Create a new institution.
    This is typically done by system admins or during onboarding.
    """
    database = await get_database()
    
    # Check if institution with same name exists
    existing = await database.institutions.find_one({"name": institution.name})
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Institution with this name already exists"
        )
    
    # Check domain uniqueness if provided
    if institution.domain:
        existing_domain = await database.institutions.find_one({"domain": institution.domain})
        if existing_domain:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Institution with this domain already exists"
            )
    
    inst_dict = institution.model_dump()
    inst_dict["settings"] = inst_dict.get("settings") or InstitutionSettings().model_dump()
    inst_dict["is_active"] = True
    inst_dict["created_at"] = datetime.utcnow()
    inst_dict["updated_at"] = None
    
    result = await database.institutions.insert_one(inst_dict)
    
    return InstitutionResponse(
        id=str(result.inserted_id),
        name=institution.name,
        domain=institution.domain,
        subscription_tier=institution.subscription_tier,
        settings=InstitutionSettings(**inst_dict["settings"]),
        is_active=True,
        created_at=inst_dict["created_at"]
    )


@router.get("/current", response_model=InstitutionResponse)
async def get_current_institution(
    tenant: TenantContext = Depends(get_tenant_dependency)
):
    """Get the current user's institution details"""
    database = await get_database()
    
    inst = await database.institutions.find_one({"_id": ObjectId(tenant.institution_id)})
    
    if not inst:
        raise HTTPException(status_code=404, detail="Institution not found")
    
    # Get user count
    user_count = await database.users.count_documents({
        "institution_id": tenant.institution_id,
        "is_active": True
    })
    
    return InstitutionResponse(
        id=str(inst["_id"]),
        name=inst["name"],
        domain=inst.get("domain"),
        subscription_tier=inst.get("subscription_tier", "free"),
        settings=InstitutionSettings(**inst.get("settings", {})),
        is_active=inst.get("is_active", True),
        created_at=inst["created_at"],
        updated_at=inst.get("updated_at"),
        user_count=user_count
    )


@router.get("/current/stats", response_model=InstitutionStats)
async def get_institution_stats(
    tenant: TenantContext = Depends(get_tenant_dependency)
):
    """Get statistics for the current institution"""
    database = await get_database()
    
    institution_id = tenant.institution_id
    
    # Count users by role
    total_students = await database.users.count_documents({
        "institution_id": institution_id,
        "role": UserRole.STUDENT,
        "is_active": True
    })
    
    total_counsellors = await database.users.count_documents({
        "institution_id": institution_id,
        "role": UserRole.COUNSELLOR,
        "is_active": True
    })
    
    # Count appointments and messages
    total_appointments = await database.appointments.count_documents({
        "institution_id": institution_id
    })
    
    total_messages = await database.messages.count_documents({
        "institution_id": institution_id
    })
    
    # Log the stats access
    await AuditLogger.log_action(
        institution_id=institution_id,
        user_id=tenant.user_id,
        action=AuditAction.READ,
        resource_type="institution_stats",
        metadata={"stats_type": "summary"}
    )
    
    return InstitutionStats(
        institution_id=institution_id,
        total_students=total_students,
        total_counsellors=total_counsellors,
        total_appointments=total_appointments,
        total_messages=total_messages
    )


@router.put("/current", response_model=InstitutionResponse)
async def update_institution(
    update_data: InstitutionUpdate,
    tenant: TenantContext = Depends(require_institution_admin())
):
    """
    Update institution settings.
    Only institution admins can update.
    """
    database = await get_database()
    
    # Check domain uniqueness if being updated
    if update_data.domain:
        existing = await database.institutions.find_one({
            "domain": update_data.domain,
            "_id": {"$ne": ObjectId(tenant.institution_id)}
        })
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Another institution with this domain already exists"
            )
    
    update_dict = {k: v for k, v in update_data.model_dump().items() if v is not None}
    
    if update_dict.get("settings"):
        update_dict["settings"] = update_dict["settings"].model_dump() if hasattr(update_dict["settings"], 'model_dump') else update_dict["settings"]
    
    update_dict["updated_at"] = datetime.utcnow()
    
    await database.institutions.update_one(
        {"_id": ObjectId(tenant.institution_id)},
        {"$set": update_dict}
    )
    
    # Log the update
    await AuditLogger.log_action(
        institution_id=tenant.institution_id,
        user_id=tenant.user_id,
        action=AuditAction.UPDATE,
        resource_type="institution",
        resource_id=tenant.institution_id,
        metadata={"updated_fields": list(update_dict.keys())}
    )
    
    return await get_current_institution(tenant)


@router.get("/current/users", response_model=List[dict])
async def list_institution_users(
    role: Optional[UserRole] = None,
    limit: int = Query(50, le=100),
    skip: int = Query(0, ge=0),
    include_inactive: bool = Query(False, description="Include inactive users; requires super admin"),
    tenant: TenantContext = Depends(require_institution_admin()),
):
    """
    List users in the current institution.
    Only admins can see all users.
    include_inactive: only super admins may set this; returns disabled users too.
    """
    if include_inactive and not is_super_admin(tenant):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only super admins can list inactive users.",
        )

    database = await get_database()
    query = {"institution_id": tenant.institution_id}
    if not include_inactive:
        query["is_active"] = True
    if role:
        query["role"] = role

    cursor = database.users.find(query, {"password": 0}).sort("created_at", -1).skip(skip).limit(limit)

    # Resolve institution name once
    inst = await database.institutions.find_one({"_id": ObjectId(tenant.institution_id)})
    institution_name = inst.get("name") if inst else None

    users = []
    async for user in cursor:
        user_dict = {
            "id": str(user["_id"]),
            "email": user["email"],
            "full_name": user["full_name"],
            "role": user["role"],
            "institution_id": user["institution_id"],
            "institution_name": institution_name,
            "phone": user.get("phone"),
            "grade": user.get("grade"),
            "major": user.get("major"),
            "bio": user.get("bio"),
            "profile_image": user.get("profile_image"),
            "created_at": user["created_at"],
            "is_active": user.get("is_active", True),
            "assigned_counsellor_id": user.get("assigned_counsellor_id"),
            "is_super_admin": is_email_super_admin(user.get("email", "") or ""),
        }

        if user_dict["assigned_counsellor_id"]:
            try:
                counsellor = await database.users.find_one({
                    "_id": ObjectId(user_dict["assigned_counsellor_id"]),
                })
                if counsellor:
                    user_dict["assigned_counsellor_name"] = counsellor.get("full_name")
            except Exception:
                pass

        users.append(user_dict)

    return users


@router.get("/{institution_id}", response_model=InstitutionResponse)
async def get_institution(institution_id: str):
    """Get a specific institution by ID (public info only)"""
    database = await get_database()
    
    try:
        inst = await database.institutions.find_one({"_id": ObjectId(institution_id)})
    except:
        raise HTTPException(status_code=404, detail="Institution not found")
    
    if not inst:
        raise HTTPException(status_code=404, detail="Institution not found")
    
    return InstitutionResponse(
        id=str(inst["_id"]),
        name=inst["name"],
        domain=inst.get("domain"),
        subscription_tier=inst.get("subscription_tier", "free"),
        settings=InstitutionSettings(**inst.get("settings", {})),
        is_active=inst.get("is_active", True),
        created_at=inst["created_at"],
        updated_at=inst.get("updated_at")
    )
