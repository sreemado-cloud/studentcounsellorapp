"""
Notes API with multi-tenant isolation.
Uses institution-based tenancy with audit logging.
"""
from fastapi import APIRouter, HTTPException, status, Depends, Query, Request
from typing import List, Optional
from datetime import datetime
from bson import ObjectId

from app.core.database import get_database
from app.core.tenant import get_tenant_dependency, TenantContext
from app.core.tenant_strategy import TenantAwareRepository
from app.core.audit import AuditLogger, AuditAction
from app.models.note import NoteCreate, NoteResponse, NoteUpdate, NoteCategory
from app.models.user import UserRole

router = APIRouter(prefix="/api/notes", tags=["Notes"])


def get_student_tenant() -> TenantContext:
    """Dependency that ensures user is a student and returns tenant context"""
    ctx = get_tenant_dependency()
    if ctx.role != UserRole.STUDENT:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only students can access personal notes"
        )
    return ctx


@router.post("/", response_model=NoteResponse, status_code=status.HTTP_201_CREATED)
async def create_note(
    note: NoteCreate,
    request: Request,
    tenant: TenantContext = Depends(get_student_tenant)
):
    """
    Create a new note.
    
    MULTI-TENANCY:
    - Institution-level: Note is tagged with institution_id
    - Student-level: Note is tagged with student_id (user's own data)
    """
    database = await get_database()
    repo = TenantAwareRepository(database, "notes")
    
    note_dict = note.model_dump()
    note_dict["student_id"] = tenant.user_id  # Student can only create their own notes
    note_dict["created_at"] = datetime.utcnow()
    note_dict["updated_at"] = None
    
    # Repository automatically adds institution_id
    result = await repo.insert_one(tenant.institution_id, note_dict)
    
    # Audit log
    await AuditLogger.log_action(
        institution_id=tenant.institution_id,
        user_id=tenant.user_id,
        action=AuditAction.CREATE,
        resource_type="note",
        resource_id=str(result.inserted_id),
        request=request
    )
    
    return NoteResponse(
        id=str(result.inserted_id),
        student_id=tenant.user_id,
        title=note.title,
        content=note.content,
        category=note.category,
        tags=note.tags or [],
        is_private=note.is_private,
        created_at=note_dict["created_at"]
    )


@router.get("/", response_model=List[NoteResponse])
async def get_notes(
    category: Optional[NoteCategory] = None,
    search: Optional[str] = Query(None, min_length=2),
    request: Request = None,
    tenant: TenantContext = Depends(get_student_tenant)
):
    """
    Get notes for the current student.
    
    MULTI-TENANCY:
    - Automatically filtered by institution_id
    - Further filtered by student_id (students only see their own notes)
    """
    database = await get_database()
    repo = TenantAwareRepository(database, "notes")
    
    # Students only see their own notes
    query = {"student_id": tenant.user_id}
    
    if category:
        query["category"] = category
    
    if search:
        query["$or"] = [
            {"title": {"$regex": search, "$options": "i"}},
            {"content": {"$regex": search, "$options": "i"}},
            {"tags": {"$in": [search]}}
        ]
    
    # Repository automatically adds institution_id filter
    cursor = await repo.find(
        tenant.institution_id,
        query,
        sort=[("created_at", -1)]
    )
    
    notes = []
    async for note in cursor:
        notes.append(NoteResponse(
            id=str(note["_id"]),
            student_id=note["student_id"],
            title=note["title"],
            content=note["content"],
            category=note["category"],
            tags=note.get("tags", []),
            is_private=note.get("is_private", True),
            created_at=note["created_at"],
            updated_at=note.get("updated_at")
        ))
    
    # Audit log
    await AuditLogger.log_action(
        institution_id=tenant.institution_id,
        user_id=tenant.user_id,
        action=AuditAction.LIST,
        resource_type="note",
        request=request,
        metadata={"count": len(notes), "filters": {"category": category, "search": search}}
    )
    
    return notes


@router.get("/{note_id}", response_model=NoteResponse)
async def get_note(
    note_id: str,
    request: Request,
    tenant: TenantContext = Depends(get_student_tenant)
):
    """
    Get a specific note.
    
    MULTI-TENANCY:
    - Verifies institution ownership
    - Verifies student ownership (students can only see their own notes)
    """
    database = await get_database()
    repo = TenantAwareRepository(database, "notes")
    
    # Find note within institution and for this student
    note = await repo.find_one(
        tenant.institution_id,
        {"_id": ObjectId(note_id), "student_id": tenant.user_id}
    )
    
    if not note:
        raise HTTPException(status_code=404, detail="Note not found")
    
    # Audit log
    await AuditLogger.log_action(
        institution_id=tenant.institution_id,
        user_id=tenant.user_id,
        action=AuditAction.READ,
        resource_type="note",
        resource_id=note_id,
        request=request
    )
    
    return NoteResponse(
        id=str(note["_id"]),
        student_id=note["student_id"],
        title=note["title"],
        content=note["content"],
        category=note["category"],
        tags=note.get("tags", []),
        is_private=note.get("is_private", True),
        created_at=note["created_at"],
        updated_at=note.get("updated_at")
    )


@router.put("/{note_id}", response_model=NoteResponse)
async def update_note(
    note_id: str,
    update_data: NoteUpdate,
    request: Request,
    tenant: TenantContext = Depends(get_student_tenant)
):
    """
    Update a note.
    
    MULTI-TENANCY:
    - Verifies institution and student ownership before update
    """
    database = await get_database()
    repo = TenantAwareRepository(database, "notes")
    
    # Verify ownership
    existing = await repo.find_one(
        tenant.institution_id,
        {"_id": ObjectId(note_id), "student_id": tenant.user_id}
    )
    
    if not existing:
        raise HTTPException(status_code=404, detail="Note not found")
    
    update_dict = {k: v for k, v in update_data.model_dump().items() if v is not None}
    update_dict["updated_at"] = datetime.utcnow()
    
    await repo.update_one(
        tenant.institution_id,
        {"_id": ObjectId(note_id), "student_id": tenant.user_id},
        {"$set": update_dict}
    )
    
    # Audit log
    await AuditLogger.log_action(
        institution_id=tenant.institution_id,
        user_id=tenant.user_id,
        action=AuditAction.UPDATE,
        resource_type="note",
        resource_id=note_id,
        request=request,
        metadata={"updated_fields": list(update_dict.keys())}
    )
    
    return await get_note(note_id, request, tenant)


@router.delete("/{note_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_note(
    note_id: str,
    request: Request,
    tenant: TenantContext = Depends(get_student_tenant)
):
    """
    Delete a note.
    
    MULTI-TENANCY:
    - Verifies institution and student ownership before delete
    """
    database = await get_database()
    repo = TenantAwareRepository(database, "notes")
    
    # Verify ownership
    existing = await repo.find_one(
        tenant.institution_id,
        {"_id": ObjectId(note_id), "student_id": tenant.user_id}
    )
    
    if not existing:
        raise HTTPException(status_code=404, detail="Note not found")
    
    await repo.delete_one(
        tenant.institution_id,
        {"_id": ObjectId(note_id), "student_id": tenant.user_id}
    )
    
    # Audit log
    await AuditLogger.log_action(
        institution_id=tenant.institution_id,
        user_id=tenant.user_id,
        action=AuditAction.DELETE,
        resource_type="note",
        resource_id=note_id,
        request=request
    )
