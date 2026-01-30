"""
Users API with multi-tenant isolation.
Users can only see other users within their institution.
"""
from fastapi import APIRouter, HTTPException, status, Depends, Request
from typing import List
from bson import ObjectId

from app.core.database import get_database, get_default_database
from app.core.tenant import get_tenant_dependency, TenantContext
from app.core.validators import validate_object_id
from app.core.audit import AuditLogger, AuditAction
from app.models.user import UserResponse, UserUpdate, UserRole

router = APIRouter(prefix="/api/users", tags=["Users"])


@router.get("/counsellors", response_model=List[UserResponse])
async def get_counsellors(
    request: Request,
    tenant: TenantContext = Depends(get_tenant_dependency)
):
    """
    Get all available counsellors in the current institution.
    
    MULTI-TENANCY: Only returns counsellors from the same institution.
    """
    database = await get_database()
    
    cursor = database.users.find({
        "institution_id": tenant.institution_id,  # Same institution only
        "role": UserRole.COUNSELLOR,
        "is_active": True
    })
    
    counsellors = []
    async for counsellor in cursor:
        counsellors.append(UserResponse(
            id=str(counsellor["_id"]),
            email=counsellor["email"],
            full_name=counsellor["full_name"],
            role=counsellor["role"],
            institution_id=counsellor.get("institution_id", ""),
            phone=counsellor.get("phone"),
            bio=counsellor.get("bio"),
            profile_image=counsellor.get("profile_image"),
            created_at=counsellor["created_at"],
            is_active=True
        ))
    
    # Audit log
    await AuditLogger.log_action(
        institution_id=tenant.institution_id,
        user_id=tenant.user_id,
        action=AuditAction.LIST,
        resource_type="user",
        request=request,
        metadata={"filter": "counsellors", "count": len(counsellors)}
    )
    
    return counsellors


@router.put("/me", response_model=UserResponse)
async def update_profile(
    update_data: UserUpdate,
    request: Request,
    tenant: TenantContext = Depends(get_tenant_dependency)
):
    """Update current user's profile"""
    database = await get_database()
    
    # Filter out None values
    update_dict = {k: v for k, v in update_data.model_dump().items() if v is not None}
    
    if not update_dict:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No fields to update"
        )
    
    await database.users.update_one(
        {"_id": ObjectId(tenant.user_id)},
        {"$set": update_dict}
    )
    
    # Fetch updated user
    updated_user = await database.users.find_one({"_id": ObjectId(tenant.user_id)})
    
    # Get institution name from shared DB (institutions are global)
    institution_name = None
    if updated_user.get("institution_id"):
        try:
            default_db = get_default_database()
            institution = await default_db.institutions.find_one({
                "_id": ObjectId(str(updated_user["institution_id"]))
            })
            if institution:
                institution_name = institution["name"]
        except Exception:
            pass
    
    # Audit log
    await AuditLogger.log_action(
        institution_id=tenant.institution_id,
        user_id=tenant.user_id,
        action=AuditAction.UPDATE,
        resource_type="user",
        resource_id=tenant.user_id,
        request=request,
        metadata={"updated_fields": list(update_dict.keys())}
    )
    
    return UserResponse(
        id=str(updated_user["_id"]),
        email=updated_user["email"],
        full_name=updated_user["full_name"],
        role=updated_user["role"],
        institution_id=updated_user.get("institution_id", ""),
        institution_name=institution_name,
        phone=updated_user.get("phone"),
        grade=updated_user.get("grade"),
        major=updated_user.get("major"),
        bio=updated_user.get("bio"),
        profile_image=updated_user.get("profile_image"),
        created_at=updated_user["created_at"],
        is_active=updated_user.get("is_active", True)
    )


@router.get("/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: str,
    request: Request,
    tenant: TenantContext = Depends(get_tenant_dependency)
):
    """
    Get user by ID.
    
    MULTI-TENANCY: Can only view users in the same institution.
    """
    database = await get_database()
    
    uid = validate_object_id(user_id, "user_id")
    user = await database.users.find_one({
        "_id": uid,
        "institution_id": tenant.institution_id
    })
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Get institution name from shared DB (institutions are global)
    institution_name = None
    if user.get("institution_id"):
        try:
            default_db = get_default_database()
            institution = await default_db.institutions.find_one({
                "_id": ObjectId(str(user["institution_id"]))
            })
            if institution:
                institution_name = institution["name"]
        except Exception:
            pass
    
    # Audit log
    await AuditLogger.log_action(
        institution_id=tenant.institution_id,
        user_id=tenant.user_id,
        action=AuditAction.READ,
        resource_type="user",
        resource_id=user_id,
        request=request
    )
    
    return UserResponse(
        id=str(user["_id"]),
        email=user["email"],
        full_name=user["full_name"],
        role=user["role"],
        institution_id=user.get("institution_id", ""),
        institution_name=institution_name,
        phone=user.get("phone"),
        bio=user.get("bio"),
        profile_image=user.get("profile_image"),
        created_at=user["created_at"],
        is_active=user.get("is_active", True)
    )
