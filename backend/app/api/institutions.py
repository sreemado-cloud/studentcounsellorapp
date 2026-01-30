"""
Institution management API.
Institutions are the top-level tenants in the multi-tenant architecture.
"""
from fastapi import APIRouter, HTTPException, status, Depends, Query
from typing import List, Optional
from datetime import datetime
from bson import ObjectId

from app.core.database import get_database, get_default_database
from app.core.validators import validate_object_id
from app.core.tenant import (
    get_tenant_dependency,
    require_institution_admin,
    require_role,
    require_super_admin,
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
    InstitutionStats,
    PlatformInstitutionSummary,
    PlatformInstitutionItem,
    TenantIsolationLevel,
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


@router.get("/platform/summary", response_model=PlatformInstitutionSummary)
async def get_platform_institution_summary(
    tenant: TenantContext = Depends(require_super_admin()),
):
    """
    Platform-wide institution count and list (all tenants).
    Super admin only.
    """
    database = await get_database()
    total = await database.institutions.count_documents({})
    cursor = database.institutions.find({}).sort("name", 1)
    institutions = []
    async for inst in cursor:
        level = inst.get("tenant_isolation_level") or "high"
        if level not in ("high", "low"):
            level = "high"
        institutions.append(PlatformInstitutionItem(
            id=str(inst["_id"]),
            name=inst["name"],
            is_active=inst.get("is_active", True),
            tenant_isolation_level=level,
        ))
    return PlatformInstitutionSummary(count=total, institutions=institutions)


@router.post("/", response_model=InstitutionResponse, status_code=status.HTTP_201_CREATED)
async def create_institution(
    institution: InstitutionCreate,
    tenant: TenantContext = Depends(require_super_admin()),
):
    """
    Create a new institution (tenant).
    Super admin only. Supports tenant isolation level (high / low).
    """
    database = await get_database()

    existing = await database.institutions.find_one({"name": institution.name})
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Institution with this name already exists",
        )

    if institution.domain:
        existing_domain = await database.institutions.find_one({"domain": institution.domain})
        if existing_domain:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Institution with this domain already exists",
            )

    isolation = institution.tenant_isolation_level
    if isinstance(isolation, TenantIsolationLevel):
        isolation = isolation.value

    inst_dict = institution.model_dump()
    inst_dict["settings"] = inst_dict.get("settings") or InstitutionSettings().model_dump()
    inst_dict["is_active"] = True
    inst_dict["created_at"] = datetime.utcnow()
    inst_dict["updated_at"] = None
    inst_dict["tenant_isolation_level"] = isolation

    result = await database.institutions.insert_one(inst_dict)

    await AuditLogger.log_action(
        institution_id=str(result.inserted_id),
        user_id=tenant.user_id,
        action=AuditAction.CREATE,
        resource_type="institution",
        resource_id=str(result.inserted_id),
        metadata={"name": institution.name, "tenant_isolation_level": isolation},
    )

    return InstitutionResponse(
        id=str(result.inserted_id),
        name=institution.name,
        domain=institution.domain,
        subscription_tier=institution.subscription_tier,
        settings=InstitutionSettings(**inst_dict["settings"]),
        is_active=True,
        created_at=inst_dict["created_at"],
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
    """Get statistics for the current institution.
    For super admins: platform-wide stats across all institutions.
    For counsellors: total_students = count of assigned students only (matches My Students).
    For regular admins: institution-scoped stats.
    """
    database = await get_database()
    default_db = get_default_database()
    institution_id = tenant.institution_id

    # Super admin: platform-wide stats
    if is_super_admin(tenant):
        total_students = await default_db.users.count_documents({
            "role": UserRole.STUDENT,
            "is_active": True
        })
        total_counsellors = await default_db.users.count_documents({
            "role": UserRole.COUNSELLOR,
            "is_active": True
        })
        total_appointments = await default_db.appointments.count_documents({})
        total_messages = await default_db.messages.count_documents({})
        
        return InstitutionStats(
            institution_id="platform",
            total_students=total_students,
            total_counsellors=total_counsellors,
            total_appointments=total_appointments,
            total_messages=total_messages
        )

    # Institution-scoped stats
    base_students_filter: dict = {
        "institution_id": institution_id,
        "role": UserRole.STUDENT,
    }
    if tenant.role == "counsellor":
        or_active = [{"is_active": True}, {"approval_status": "pending"}]
        or_ac = [{"assigned_counsellor_id": tenant.user_id}]
        try:
            or_ac.append({"assigned_counsellor_id": ObjectId(tenant.user_id)})
        except Exception:
            pass
        total_students = await database.users.count_documents({
            **base_students_filter,
            "$and": [
                {"$or": or_active},
                {"$or": or_ac},
            ],
        })
    else:
        base_students_filter["is_active"] = True
        total_students = await database.users.count_documents(base_students_filter)
    
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
    limit: int = Query(50, le=500, description="Max 500 for super admin"),
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
    default_db = get_default_database()

    # Super admin with include_inactive: return users from ALL institutions (platform-wide)
    # This enables Super Admin to see and manage all users across the platform
    if is_super_admin(tenant) and include_inactive:
        plat_conditions: list = []
        if role:
            plat_conditions.append({"role": role})
        # include_inactive=True means no active filter
        plat_query = {"$and": plat_conditions} if plat_conditions else {}
        cursor = default_db.users.find(plat_query, {"password": 0}).sort("created_at", -1)
        raw_users = [u async for u in cursor.skip(skip).limit(limit)]
        return await _build_user_list(database, default_db, raw_users)

    # Institution-scoped listing
    # Match institution_id as string or ObjectId so no user is excluded by type mismatch
    inst_id = tenant.institution_id
    try:
        inst_oid = ObjectId(inst_id) if inst_id and inst_id != "default" else None
    except Exception:
        inst_oid = None
    if inst_oid is not None:
        base_inst_query = {"$or": [{"institution_id": inst_id}, {"institution_id": inst_oid}]}
    else:
        base_inst_query = {"institution_id": inst_id} if inst_id and inst_id != "default" else {}

    # For super admin: also include users with no institution (so they can be assigned)
    if is_super_admin(tenant) and base_inst_query:
        base_query = {"$or": [
            base_inst_query,
            {"institution_id": None},
            {"institution_id": {"$exists": False}},
        ]}
    else:
        base_query = base_inst_query

    if not base_query:
        # No institution (e.g. default) and not super admin - return empty
        return await _build_user_list(database, default_db, [])

    conditions = [base_query]
    if not include_inactive:
        # Include active users OR pending students (so admins can approve/reject)
        conditions.append({
            "$or": [
                {"is_active": True},
                {"role": "student", "approval_status": "pending"},
            ]
        })
    if role:
        conditions.append({"role": role})
    query = {"$and": conditions} if len(conditions) > 1 else conditions[0]

    # When super admin and we included no-institution users, merge then sort then skip/limit
    cursor = database.users.find(query, {"password": 0}).sort("created_at", -1)
    # Only fetch no-institution from default_db when using db-per-tenant (database != default_db)
    # so we don't double-count when shared DB already returned them in the $or query
    need_merge = (
        is_super_admin(tenant)
        and base_inst_query
        and (base_query != base_inst_query)
        and database.name != default_db.name
    )
    if need_merge:
        inst_cap = 2000
        raw_from_inst = [u async for u in cursor.limit(inst_cap)]
        no_inst_conditions = [{"$or": [{"institution_id": None}, {"institution_id": {"$exists": False}}]}]
        if not include_inactive:
            no_inst_conditions.append({"$or": [{"is_active": True}, {"role": "student", "approval_status": "pending"}]})
        if role:
            no_inst_conditions.append({"role": role})
        no_inst_query = {"$and": no_inst_conditions} if len(no_inst_conditions) > 1 else no_inst_conditions[0]
        no_inst_cursor = default_db.users.find(no_inst_query, {"password": 0}).sort("created_at", -1).limit(500)
        no_inst_users = [u async for u in no_inst_cursor]
        seen = {u["_id"] for u in raw_from_inst}
        for u in no_inst_users:
            if u["_id"] not in seen:
                raw_from_inst.append(u)
                seen.add(u["_id"])
        raw_from_inst.sort(key=lambda x: x.get("created_at") or datetime.min, reverse=True)
        raw_users = raw_from_inst[skip : skip + limit]
    else:
        raw_users = [u async for u in cursor.skip(skip).limit(limit)]
    return await _build_user_list(database, default_db, raw_users)


def _sid(x):
    return str(x) if x is not None else None


async def _build_user_list(database, default_db, raw_users: list) -> list:
    """Build list of user dicts with institution_name and assigned_counsellor_name."""
    inst_ids = {_sid(u["institution_id"]) for u in raw_users if u.get("institution_id")}
    inst_map = {}
    for iid in inst_ids:
        try:
            inst = await default_db.institutions.find_one({"_id": ObjectId(iid)})
            if inst:
                inst_map[iid] = inst.get("name") or None
        except Exception:
            pass
    counsellor_ids = {_sid(u["assigned_counsellor_id"]) for u in raw_users if u.get("assigned_counsellor_id")}
    counsellor_map = {}
    for cid in counsellor_ids:
        try:
            c = await database.users.find_one({"_id": ObjectId(cid)})
            if c:
                counsellor_map[cid] = c.get("full_name") or None
        except Exception:
            pass
    users = []
    for user in raw_users:
        iid = _sid(user.get("institution_id"))
        institution_name = inst_map.get(iid) if iid else None
        cid = _sid(user.get("assigned_counsellor_id")) if user.get("assigned_counsellor_id") else None
        user_dict = {
            "id": str(user["_id"]),
            "email": user["email"],
            "full_name": user["full_name"],
            "role": user["role"],
            "institution_id": iid,
            "institution_name": institution_name,
            "phone": user.get("phone"),
            "grade": user.get("grade"),
            "major": user.get("major"),
            "bio": user.get("bio"),
            "profile_image": user.get("profile_image"),
            "created_at": user["created_at"],
            "is_active": user.get("is_active", True),
            "approval_status": user.get("approval_status"),
            "assigned_counsellor_id": cid,
            "is_super_admin": is_email_super_admin(user.get("email", "") or ""),
        }
        if cid:
            user_dict["assigned_counsellor_name"] = counsellor_map.get(cid)
        users.append(user_dict)
    return users


@router.get("/current/assigned-students", response_model=List[dict])
async def list_assigned_students(
    tenant: TenantContext = Depends(require_role("admin", "counsellor")),
):
    """
    List students for My Students page.
    - Super admins: all students across all institutions.
    - Admins: all students in the institution.
    - Counsellors: only students assigned to them.
    """
    database = await get_database()
    default_db = get_default_database()

    # Super admin: all students across all institutions
    if is_super_admin(tenant):
        query = {
            "role": UserRole.STUDENT,
            "$or": [{"is_active": True}, {"approval_status": "pending"}],
        }
        cursor = default_db.users.find(query, {"password": 0}).sort("created_at", -1).limit(500)
        raw_users = [u async for u in cursor]
        return await _build_user_list(database, default_db, raw_users)

    # Regular admin or counsellor: institution-scoped
    query = {
        "institution_id": tenant.institution_id,
        "role": UserRole.STUDENT,
        "$and": [
            {"$or": [{"is_active": True}, {"approval_status": "pending"}]},
        ],
    }
    if tenant.role == "counsellor":
        or_ac = [{"assigned_counsellor_id": tenant.user_id}]
        try:
            or_ac.append({"assigned_counsellor_id": ObjectId(tenant.user_id)})
        except Exception:
            pass
        query["$and"].append({"$or": or_ac})
    cursor = database.users.find(query, {"password": 0}).sort("created_at", -1)
    raw_users = [u async for u in cursor]
    return await _build_user_list(database, default_db, raw_users)


@router.get("/{institution_id}", response_model=InstitutionResponse)
async def get_institution(institution_id: str):
    """Get a specific institution by ID (public info only)"""
    database = await get_database()
    
    oid = validate_object_id(institution_id, "institution_id")
    inst = await database.institutions.find_one({"_id": oid})

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
