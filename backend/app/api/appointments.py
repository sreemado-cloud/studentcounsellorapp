"""
Appointments API with multi-tenant isolation.
Uses institution-based tenancy with audit logging.
"""
from fastapi import APIRouter, HTTPException, status, Depends, Query, Request
from typing import List, Optional, Tuple
from datetime import datetime, timedelta
from bson import ObjectId

from app.core.database import get_database, get_default_database
from app.core.tenant import get_tenant_dependency, TenantContext, is_super_admin
from app.core.tenant_strategy import TenantAwareRepository
from app.core.validators import validate_object_id
from app.core.audit import AuditLogger, AuditAction
from app.models.appointment import (
    AppointmentCreate, 
    AppointmentResponse, 
    AppointmentUpdate,
    AppointmentStatus
)
from app.models.user import UserRole

router = APIRouter(prefix="/api/appointments", tags=["Appointments"])


# Default working hours for availability (30-min slots)
AVAILABILITY_START_HOUR = 9
AVAILABILITY_END_HOUR = 17
SLOT_MINUTES = 30


def _slots_overlap(
    start_a: datetime, end_a: datetime,
    start_b: datetime, end_b: datetime,
) -> bool:
    """True if the two time ranges overlap (excluding exact adjacency)."""
    return start_a < end_b and start_b < end_a


async def _get_counsellor_busy_ranges(
    repo: TenantAwareRepository,
    institution_id: str,
    counsellor_id: str,
    day_start: datetime,
    day_end: datetime,
    exclude_appointment_id: Optional[str] = None,
) -> List[Tuple[datetime, datetime]]:
    """Return list of (start, end) for non-cancelled appointments on the given day."""
    query = {
        "counsellor_id": counsellor_id,
        "status": {"$ne": AppointmentStatus.CANCELLED},
        "date": {"$gte": day_start, "$lt": day_end},
    }
    if exclude_appointment_id:
        try:
            query["_id"] = {"$ne": ObjectId(exclude_appointment_id)}
        except Exception:
            pass
    cursor = await repo.find(institution_id, query, sort=[("date", 1)])
    ranges = []
    async for apt in cursor:
        s = apt["date"]
        e = s + timedelta(minutes=apt.get("duration_minutes", 30))
        ranges.append((s, e))
    return ranges


async def _counsellor_slot_taken(
    repo: TenantAwareRepository,
    institution_id: str,
    counsellor_id: str,
    new_start: datetime,
    new_end: datetime,
    exclude_appointment_id: Optional[str] = None,
) -> bool:
    """
    Check if the counsellor has any non-cancelled appointment overlapping [new_start, new_end]
    on the same calendar day. exclude_appointment_id skips that appointment (for updates).
    """
    start_of_day = new_start.replace(hour=0, minute=0, second=0, microsecond=0)
    end_of_day = start_of_day + timedelta(days=1)
    busy = await _get_counsellor_busy_ranges(
        repo, institution_id, counsellor_id,
        start_of_day, end_of_day,
        exclude_appointment_id=exclude_appointment_id,
    )
    for ex_start, ex_end in busy:
        if _slots_overlap(new_start, new_end, ex_start, ex_end):
            return True
    return False


async def verify_appointment_access(
    appointment_id: str, 
    tenant: TenantContext,
    database
) -> dict:
    """
    Verify the current user has access to this appointment.
    
    MULTI-TENANCY RULES:
    - Must be in the same institution
    - Students can only access their own appointments
    - Counsellors can access appointments where they are assigned
    - Admins can access all appointments in their institution
    """
    repo = TenantAwareRepository(database, "appointments")
    aid = validate_object_id(appointment_id, "appointment_id")
    apt = await repo.find_one(tenant.institution_id, {"_id": aid})

    if not apt:
        raise HTTPException(status_code=404, detail="Appointment not found")
    
    # Check access based on role
    if tenant.role == UserRole.STUDENT:
        if apt["student_id"] != tenant.user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, 
                detail="Access denied - this is not your appointment"
            )
    elif tenant.role == UserRole.COUNSELLOR:
        if apt["counsellor_id"] != tenant.user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, 
                detail="Access denied - you are not the assigned counsellor"
            )
    # Admins have full access within their institution
    
    return apt


@router.post("/", response_model=AppointmentResponse, status_code=status.HTTP_201_CREATED)
async def create_appointment(
    appointment: AppointmentCreate,
    request: Request,
    tenant: TenantContext = Depends(get_tenant_dependency)
):
    """
    Create a new appointment.
    
    MULTI-TENANCY:
    - Only students can create appointments
    - Counsellor must be in the same institution
    - student_id and institution_id set from tenant context
    """
    if tenant.role != UserRole.STUDENT:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only students can create appointments"
        )
    
    database = await get_database()
    
    cid = validate_object_id(appointment.counsellor_id, "counsellor_id")
    counsellor = await database.users.find_one({
        "_id": cid,
        "role": UserRole.COUNSELLOR,
        "institution_id": tenant.institution_id,
        "is_active": True
    })
    
    if not counsellor:
        raise HTTPException(
            status_code=404, 
            detail="Counsellor not found in your institution"
        )
    
    repo = TenantAwareRepository(database, "appointments")
    
    new_start = appointment.date
    new_end = new_start + timedelta(minutes=appointment.duration_minutes)
    taken = await _counsellor_slot_taken(
        repo, tenant.institution_id, appointment.counsellor_id,
        new_start, new_end, exclude_appointment_id=None
    )
    if taken:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="This time slot is already taken for the counsellor. Please choose another 30-minute slot.",
        )
    
    appointment_dict = appointment.model_dump()
    appointment_dict["student_id"] = tenant.user_id  # From tenant context
    appointment_dict["status"] = AppointmentStatus.PENDING
    appointment_dict["created_at"] = datetime.utcnow()
    appointment_dict["updated_at"] = None
    appointment_dict["notes"] = None
    
    # Repository adds institution_id
    result = await repo.insert_one(tenant.institution_id, appointment_dict)
    
    # Get student name for response
    student = await database.users.find_one({"_id": ObjectId(tenant.user_id)})
    
    # Audit log
    await AuditLogger.log_action(
        institution_id=tenant.institution_id,
        user_id=tenant.user_id,
        action=AuditAction.CREATE,
        resource_type="appointment",
        resource_id=str(result.inserted_id),
        request=request,
        metadata={"counsellor_id": appointment.counsellor_id}
    )
    
    return AppointmentResponse(
        id=str(result.inserted_id),
        student_id=tenant.user_id,
        student_name=student["full_name"] if student else "Unknown",
        counsellor_id=appointment.counsellor_id,
        counsellor_name=counsellor["full_name"],
        date=appointment.date,
        duration_minutes=appointment.duration_minutes,
        appointment_type=appointment.appointment_type,
        status=AppointmentStatus.PENDING,
        title=appointment.title,
        description=appointment.description,
        created_at=appointment_dict["created_at"]
    )


@router.get("/", response_model=List[AppointmentResponse])
async def get_appointments(
    status_filter: Optional[AppointmentStatus] = Query(None, alias="status"),
    request: Request = None,
    tenant: TenantContext = Depends(get_tenant_dependency)
):
    """
    Get appointments.
    
    MULTI-TENANCY:
    - Super admins see all appointments across all institutions
    - Students see ONLY their appointments
    - Counsellors see ONLY appointments where they are assigned
    - Admins see all appointments in their institution
    """
    database = await get_database()
    default_db = get_default_database()
    
    # Super admin: platform-wide appointments
    if is_super_admin(tenant):
        query = {}
        if status_filter:
            query["status"] = status_filter
        cursor = default_db.appointments.find(query).sort("date", -1).limit(500)
        appointments = []
        async for apt in cursor:
            student = await default_db.users.find_one({"_id": ObjectId(apt["student_id"])})
            counsellor = await default_db.users.find_one({"_id": ObjectId(apt["counsellor_id"])})
            appointments.append(AppointmentResponse(
                id=str(apt["_id"]),
                student_id=apt["student_id"],
                student_name=student["full_name"] if student else "Unknown",
                counsellor_id=apt["counsellor_id"],
                counsellor_name=counsellor["full_name"] if counsellor else "Unknown",
                date=apt["date"],
                duration_minutes=apt["duration_minutes"],
                appointment_type=apt["appointment_type"],
                status=apt["status"],
                title=apt["title"],
                description=apt.get("description"),
                notes=apt.get("notes"),
                created_at=apt["created_at"],
                updated_at=apt.get("updated_at")
            ))
        return appointments

    repo = TenantAwareRepository(database, "appointments")
    
    # Build query based on role
    if tenant.role == UserRole.STUDENT:
        query = {"student_id": tenant.user_id}
    elif tenant.role == UserRole.COUNSELLOR:
        query = {"counsellor_id": tenant.user_id}
    else:  # Admin
        query = {}
    
    if status_filter:
        query["status"] = status_filter
    
    cursor = await repo.find(
        tenant.institution_id,
        query,
        sort=[("date", -1)]
    )
    
    appointments = []
    async for apt in cursor:
        student = await database.users.find_one({"_id": ObjectId(apt["student_id"])})
        counsellor = await database.users.find_one({"_id": ObjectId(apt["counsellor_id"])})
        
        appointments.append(AppointmentResponse(
            id=str(apt["_id"]),
            student_id=apt["student_id"],
            student_name=student["full_name"] if student else "Unknown",
            counsellor_id=apt["counsellor_id"],
            counsellor_name=counsellor["full_name"] if counsellor else "Unknown",
            date=apt["date"],
            duration_minutes=apt["duration_minutes"],
            appointment_type=apt["appointment_type"],
            status=apt["status"],
            title=apt["title"],
            description=apt.get("description"),
            notes=apt.get("notes"),
            created_at=apt["created_at"],
            updated_at=apt.get("updated_at")
        ))
    
    # Audit log
    await AuditLogger.log_action(
        institution_id=tenant.institution_id,
        user_id=tenant.user_id,
        action=AuditAction.LIST,
        resource_type="appointment",
        request=request,
        metadata={"count": len(appointments), "status_filter": status_filter}
    )
    
    return appointments


@router.get("/availability")
async def get_availability(
    counsellor_id: str = Query(..., description="Counsellor ID"),
    date: str = Query(..., description="Date YYYY-MM-DD"),
    tenant: TenantContext = Depends(get_tenant_dependency),
):
    """
    Get available 30-minute slots for a counsellor on a given day.
    Working hours 09:00–17:00. Excludes slots overlapping existing appointments.
    """
    database = await get_database()
    cid = validate_object_id(counsellor_id, "counsellor_id")
    counsellor = await database.users.find_one({
        "_id": cid,
        "role": UserRole.COUNSELLOR,
        "institution_id": tenant.institution_id,
        "is_active": True,
    })
    if not counsellor:
        raise HTTPException(status_code=404, detail="Counsellor not found in your institution")

    try:
        parts = date.strip().split("-")
        if len(parts) != 3:
            raise ValueError("invalid")
        y, m, d = int(parts[0]), int(parts[1]), int(parts[2])
        day_start = datetime(y, m, d, 0, 0, 0)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid date; use YYYY-MM-DD")
    day_end = day_start + timedelta(days=1)

    repo = TenantAwareRepository(database, "appointments")
    cid_str = str(cid) if isinstance(cid, ObjectId) else counsellor_id
    busy = await _get_counsellor_busy_ranges(
        repo, tenant.institution_id, cid_str,
        day_start, day_end,
        exclude_appointment_id=None,
    )

    slots = []
    slot_start = day_start + timedelta(hours=AVAILABILITY_START_HOUR)
    end_time = day_start + timedelta(hours=AVAILABILITY_END_HOUR)
    while slot_start + timedelta(minutes=SLOT_MINUTES) <= end_time:
        slot_end = slot_start + timedelta(minutes=SLOT_MINUTES)
        overlap = any(
            _slots_overlap(slot_start, slot_end, bs, be) for bs, be in busy
        )
        if not overlap:
            slots.append({
                "start": slot_start.isoformat(),
                "end": slot_end.isoformat(),
            })
        slot_start = slot_end

    return {
        "date": date,
        "counsellor_id": counsellor_id,
        "available_slots": slots,
    }


@router.get("/{appointment_id}", response_model=AppointmentResponse)
async def get_appointment(
    appointment_id: str,
    request: Request,
    tenant: TenantContext = Depends(get_tenant_dependency)
):
    """Get a specific appointment."""
    database = await get_database()
    
    apt = await verify_appointment_access(appointment_id, tenant, database)
    
    student = await database.users.find_one({"_id": ObjectId(apt["student_id"])})
    counsellor = await database.users.find_one({"_id": ObjectId(apt["counsellor_id"])})
    
    # Audit log
    await AuditLogger.log_action(
        institution_id=tenant.institution_id,
        user_id=tenant.user_id,
        action=AuditAction.READ,
        resource_type="appointment",
        resource_id=appointment_id,
        request=request
    )
    
    return AppointmentResponse(
        id=str(apt["_id"]),
        student_id=apt["student_id"],
        student_name=student["full_name"] if student else "Unknown",
        counsellor_id=apt["counsellor_id"],
        counsellor_name=counsellor["full_name"] if counsellor else "Unknown",
        date=apt["date"],
        duration_minutes=apt["duration_minutes"],
        appointment_type=apt["appointment_type"],
        status=apt["status"],
        title=apt["title"],
        description=apt.get("description"),
        notes=apt.get("notes"),
        created_at=apt["created_at"],
        updated_at=apt.get("updated_at")
    )


@router.put("/{appointment_id}", response_model=AppointmentResponse)
async def update_appointment(
    appointment_id: str,
    update_data: AppointmentUpdate,
    request: Request,
    tenant: TenantContext = Depends(get_tenant_dependency)
):
    """Update an appointment."""
    database = await get_database()
    repo = TenantAwareRepository(database, "appointments")
    
    apt = await verify_appointment_access(appointment_id, tenant, database)
    update_dict = {k: v for k, v in update_data.model_dump().items() if v is not None}
    update_dict["updated_at"] = datetime.utcnow()

    if "date" in update_dict:
        new_date = update_dict["date"]
        duration = apt.get("duration_minutes", 30)
        new_start = new_date
        new_end = new_start + timedelta(minutes=duration)
        counsellor_id = apt["counsellor_id"]
        if isinstance(counsellor_id, ObjectId):
            counsellor_id = str(counsellor_id)
        taken = await _counsellor_slot_taken(
            repo, tenant.institution_id, counsellor_id,
            new_start, new_end, exclude_appointment_id=appointment_id
        )
        if taken:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="This time slot is already taken for the counsellor. Please choose another slot.",
            )

    if tenant.role == UserRole.STUDENT:
        query = {"_id": apt["_id"], "student_id": tenant.user_id}
    elif tenant.role == UserRole.COUNSELLOR:
        query = {"_id": apt["_id"], "counsellor_id": tenant.user_id}
    else:
        query = {"_id": apt["_id"]}
    
    result = await repo.update_one(tenant.institution_id, query, {"$set": update_dict})
    
    if result.matched_count == 0:
        raise HTTPException(status_code=403, detail="Access denied")
    
    # Audit log
    await AuditLogger.log_action(
        institution_id=tenant.institution_id,
        user_id=tenant.user_id,
        action=AuditAction.UPDATE,
        resource_type="appointment",
        resource_id=appointment_id,
        request=request,
        metadata={"updated_fields": list(update_dict.keys())}
    )
    
    return await get_appointment(appointment_id, request, tenant)


@router.delete("/{appointment_id}", status_code=status.HTTP_204_NO_CONTENT)
async def cancel_appointment(
    appointment_id: str,
    request: Request,
    tenant: TenantContext = Depends(get_tenant_dependency)
):
    """Cancel an appointment (soft delete - sets status to cancelled)."""
    if tenant.role not in [UserRole.STUDENT, UserRole.ADMIN]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only students or admins can cancel appointments"
        )
    
    database = await get_database()
    repo = TenantAwareRepository(database, "appointments")
    
    apt = await verify_appointment_access(appointment_id, tenant, database)
    if tenant.role == UserRole.STUDENT:
        query = {"_id": apt["_id"], "student_id": tenant.user_id}
    else:
        query = {"_id": apt["_id"]}
    
    result = await repo.update_one(
        tenant.institution_id,
        query,
        {"$set": {"status": AppointmentStatus.CANCELLED, "updated_at": datetime.utcnow()}}
    )
    
    if result.matched_count == 0:
        raise HTTPException(status_code=403, detail="Access denied")
    
    # Audit log
    await AuditLogger.log_action(
        institution_id=tenant.institution_id,
        user_id=tenant.user_id,
        action=AuditAction.DELETE,
        resource_type="appointment",
        resource_id=appointment_id,
        request=request,
        metadata={"action": "cancelled"}
    )
