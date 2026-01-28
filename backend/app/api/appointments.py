"""
Appointments API with multi-tenant isolation.
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
from app.models.appointment import (
    AppointmentCreate, 
    AppointmentResponse, 
    AppointmentUpdate,
    AppointmentStatus
)
from app.models.user import UserRole

router = APIRouter(prefix="/api/appointments", tags=["Appointments"])


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
    
    try:
        apt = await repo.find_one(tenant.institution_id, {"_id": ObjectId(appointment_id)})
    except:
        raise HTTPException(status_code=404, detail="Appointment not found")
    
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
    
    # Verify counsellor exists in the same institution
    counsellor = await database.users.find_one({
        "_id": ObjectId(appointment.counsellor_id),
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
    - Automatically filtered by institution_id
    - Students see ONLY their appointments
    - Counsellors see ONLY appointments where they are assigned
    - Admins see all appointments in their institution
    """
    database = await get_database()
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
    
    # Verify access first
    await verify_appointment_access(appointment_id, tenant, database)
    
    update_dict = {k: v for k, v in update_data.model_dump().items() if v is not None}
    update_dict["updated_at"] = datetime.utcnow()
    
    # Build query based on role
    if tenant.role == UserRole.STUDENT:
        query = {"_id": ObjectId(appointment_id), "student_id": tenant.user_id}
    elif tenant.role == UserRole.COUNSELLOR:
        query = {"_id": ObjectId(appointment_id), "counsellor_id": tenant.user_id}
    else:
        query = {"_id": ObjectId(appointment_id)}
    
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
    
    # Verify ownership
    await verify_appointment_access(appointment_id, tenant, database)
    
    # Build query
    if tenant.role == UserRole.STUDENT:
        query = {"_id": ObjectId(appointment_id), "student_id": tenant.user_id}
    else:
        query = {"_id": ObjectId(appointment_id)}
    
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
