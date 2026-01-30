"""
Admin API endpoints for managing users within an institution.
Only accessible by users with admin role.
"""
from fastapi import APIRouter, HTTPException, status, Depends, Request
from datetime import datetime
from bson import ObjectId
from typing import Optional

from app.core.database import get_database, get_default_database
from app.core.security import get_password_hash
from app.core.validators import validate_object_id
from app.core.token_revocation import delete_sessions_for_user
from app.core.tenant import get_tenant_dependency, require_institution_admin, TenantContext, is_super_admin, is_email_super_admin
from app.core.audit import AuditLogger, AuditAction
from app.core.config import settings
from app.models.user import UserResponse
from pydantic import BaseModel, EmailStr, Field

router = APIRouter(prefix="/api/admin", tags=["Admin"])


class AdminUserCreate(BaseModel):
    """Schema for admin creating a new user"""
    email: EmailStr
    password: str = Field(..., min_length=8)
    full_name: str = Field(..., min_length=2, max_length=100)
    role: str = Field(..., pattern="^(student|counsellor|admin)$")
    institution_id: Optional[str] = None  # Optional - will be auto-set to admin's institution
    assigned_counsellor_id: Optional[str] = None  # For students: assign counsellor during creation
    phone: Optional[str] = None
    bio: Optional[str] = None
    grade: Optional[str] = None
    major: Optional[str] = None


class ReassignInstitutionRequest(BaseModel):
    """Schema for reassigning a user to a different institution"""
    new_institution_id: str


class AssignCounsellorRequest(BaseModel):
    """Schema for assigning a student to a counsellor"""
    counsellor_id: Optional[str] = None  # None to unassign


class SetPasswordRequest(BaseModel):
    """Schema for admin setting a user's password"""
    new_password: str = Field(..., min_length=8)


@router.put("/users/{user_id}/set-password", operation_id="admin_set_user_password")
async def set_user_password(
    user_id: str,
    body: SetPasswordRequest,
    request: Request,
    tenant: TenantContext = Depends(require_institution_admin()),
):
    """
    Set a user's password (admin reset). Use when a user cannot login, e.g. typo at creation.
    User must be in the admin's institution.
    """
    database = await get_database()
    uid = validate_object_id(user_id, "user_id")
    user = await database.users.find_one({
        "_id": uid,
        "institution_id": tenant.institution_id,
    })

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found in your institution",
        )

    await database.users.update_one(
        {"_id": uid},
        {
            "$set": {
                "password": get_password_hash(body.new_password),
                "password_reset_required": False,
                "updated_at": datetime.utcnow(),
            }
        },
    )

    await delete_sessions_for_user(user_id)

    await AuditLogger.log_action(
        institution_id=tenant.institution_id,
        user_id=tenant.user_id,
        action=AuditAction.UPDATE,
        resource_type="user",
        resource_id=user_id,
        request=request,
        metadata={"action": "set_password", "target_user_email": user["email"]},
    )

    return {"message": "Password has been set. The user can now login with the new password."}


@router.post("/users", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user(
    user_data: AdminUserCreate,
    request: Request,
    tenant: TenantContext = Depends(require_institution_admin())
):
    """
    Create a new user within the admin's institution.
    Only admins can create users with any role (student, counsellor, admin).
    """
    database = await get_database()
    
    # Automatically assign to the admin's institution (security: ignore frontend value)
    # This ensures users are always created in the admin's institution (store as string)
    institution_id = str(tenant.institution_id) if tenant.institution_id and tenant.institution_id != "default" else tenant.institution_id
    
    # Check if email already exists
    existing_user = await database.users.find_one({"email": user_data.email})
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Get institution to check limits
    institution = await database.institutions.find_one({
        "_id": ObjectId(institution_id)
    })
    
    if not institution:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Institution not found"
        )
    
    settings = institution.get("settings", {})
    
    # Check user limits based on role
    if user_data.role == "student":
        max_students = settings.get("max_students", 100)
        current_students = await database.users.count_documents({
            "institution_id": institution_id,
            "role": "student",
            "is_active": True
        })
        if current_students >= max_students:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Institution has reached maximum student capacity ({max_students})"
            )
        
        # Validate assigned counsellor if provided
        if user_data.assigned_counsellor_id:
            cid = validate_object_id(user_data.assigned_counsellor_id, "assigned_counsellor_id")
            counsellor = await database.users.find_one({
                "_id": cid,
                "institution_id": institution_id,
                "role": "counsellor",
                "is_active": True
            })
            if not counsellor:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Assigned counsellor not found or not in your institution"
                )
    elif user_data.role == "counsellor":
        max_counsellors = settings.get("max_counsellors", 5)
        current_counsellors = await database.users.count_documents({
            "institution_id": institution_id,
            "role": "counsellor",
            "is_active": True
        })
        if current_counsellors >= max_counsellors:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Institution has reached maximum counsellor capacity ({max_counsellors})"
            )
    
    # Create user document
    user_dict = {
        "email": user_data.email,
        "password": get_password_hash(user_data.password),
        "full_name": user_data.full_name,
        "role": user_data.role,
        "institution_id": institution_id,  # Always use admin's institution
        "assigned_counsellor_id": user_data.assigned_counsellor_id if user_data.role == "student" else None,
        "phone": user_data.phone,
        "bio": user_data.bio,
        "grade": user_data.grade,
        "major": user_data.major,
        "created_at": datetime.utcnow(),
        "is_active": True,
        "profile_image": None,
        "password_reset_required": True,  # Require password reset on first login
    }
    
    result = await database.users.insert_one(user_dict)
    user_dict["id"] = str(result.inserted_id)
    
    # Audit log the creation
    await AuditLogger.log_action(
        institution_id=tenant.institution_id,
        user_id=tenant.user_id,
        action=AuditAction.CREATE,
        resource_type="user",
        resource_id=user_dict["id"],
        request=request,
        metadata={
            "created_role": user_data.role,
            "created_by_admin": True,
            "created_user_email": user_data.email
        }
    )
    
    # Get institution name and counsellor name for response
    institution_name = institution.get("name", "")
    assigned_counsellor_name = None
    if user_dict.get("assigned_counsellor_id"):
        counsellor = await database.users.find_one({
            "_id": validate_object_id(user_dict["assigned_counsellor_id"], "assigned_counsellor_id")
        })
        if counsellor:
            assigned_counsellor_name = counsellor.get("full_name")
    
    return UserResponse(
        id=user_dict["id"],
        email=user_dict["email"],
        full_name=user_dict["full_name"],
        role=user_dict["role"],
        institution_id=user_dict["institution_id"],
        institution_name=institution_name,
        assigned_counsellor_id=user_dict.get("assigned_counsellor_id"),
        assigned_counsellor_name=assigned_counsellor_name,
        phone=user_dict.get("phone"),
        grade=user_dict.get("grade"),
        major=user_dict.get("major"),
        bio=user_dict.get("bio"),
        profile_image=user_dict.get("profile_image"),
        created_at=user_dict["created_at"],
        is_active=user_dict["is_active"],
        password_reset_required=user_dict.get("password_reset_required", True)
    )


@router.put("/users/{user_id}/status")
async def update_user_status(
    user_id: str,
    is_active: bool,
    request: Request,
    tenant: TenantContext = Depends(require_institution_admin())
):
    """
    Activate or deactivate a user within the admin's institution.
    Only super admins can disable other admins.
    """
    database = await get_database()
    
    uid = validate_object_id(user_id, "user_id")
    user = await database.users.find_one({
        "_id": uid,
        "institution_id": tenant.institution_id
    })

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found in your institution"
        )

    # Prevent admin from deactivating themselves
    if user_id == tenant.user_id and not is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot deactivate your own account"
        )
    
    # Only super admins can disable (deactivate) other admins
    if user.get("role") == "admin" and not is_active and not is_super_admin(tenant):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only super admins can disable admin accounts. Contact a super admin."
        )
    # Nobody can disable a super admin
    if is_email_super_admin(user.get("email", "") or "") and not is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Super admin accounts cannot be disabled."
        )
    
    await database.users.update_one(
        {"_id": uid},
        {"$set": {"is_active": is_active, "updated_at": datetime.utcnow()}}
    )

    if not is_active:
        await delete_sessions_for_user(user_id)

    await AuditLogger.log_action(
        institution_id=tenant.institution_id,
        user_id=tenant.user_id,
        action=AuditAction.UPDATE,
        resource_type="user",
        resource_id=user_id,
        request=request,
        metadata={
            "status_change": "activated" if is_active else "deactivated",
            "target_user_email": user["email"]
        }
    )

    return {"message": f"User {'activated' if is_active else 'deactivated'} successfully"}


@router.put("/users/{student_id}/assign-counsellor")
async def assign_student_to_counsellor(
    student_id: str,
    body: AssignCounsellorRequest,
    request: Request = None,
    tenant: TenantContext = Depends(require_institution_admin())
):
    """
    Assign or reassign a student to a counsellor within the admin's institution.
    Send {"counsellor_id": "..."} in JSON body; omit or null to unassign.
    """
    database = await get_database()
    counsellor_id = body.counsellor_id

    sid = validate_object_id(student_id, "student_id")
    student = await database.users.find_one({
        "_id": sid,
        "institution_id": tenant.institution_id,
        "role": "student"
    })

    if not student:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Student not found in your institution"
        )
    
    previous_counsellor_id = student.get("assigned_counsellor_id")
    prev_cid_str = str(previous_counsellor_id) if previous_counsellor_id else None

    # Validate counsellor if provided
    counsellor_name = None
    if counsellor_id:
        cid = validate_object_id(counsellor_id, "counsellor_id")
        counsellor = await database.users.find_one({
            "_id": cid,
            "institution_id": tenant.institution_id,
            "role": "counsellor",
            "is_active": True
        })
        if not counsellor:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Counsellor not found or not in your institution"
            )
        counsellor_name = counsellor.get("full_name")

        # Check max students per counsellor (max 10)
        MAX_STUDENTS_PER_COUNSELLOR = 10
        # Match both str and ObjectId (existing docs may use either)
        q = {
            "institution_id": tenant.institution_id,
            "role": "student",
            "is_active": True,
            "$or": [
                {"assigned_counsellor_id": counsellor_id},
                {"assigned_counsellor_id": cid},
            ],
        }
        current_student_count = await database.users.count_documents(q)
        if prev_cid_str != counsellor_id and current_student_count >= MAX_STUDENTS_PER_COUNSELLOR:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Counsellor has reached maximum capacity ({MAX_STUDENTS_PER_COUNSELLOR} students). Please assign this student to another counsellor."
            )

    update_data = {
        "assigned_counsellor_id": counsellor_id,
        "updated_at": datetime.utcnow()
    }
    
    if previous_counsellor_id and prev_cid_str != counsellor_id:
        # Add to assignment history
        assignment_history = student.get("counsellor_assignment_history", [])
        assignment_history.append({
            "counsellor_id": previous_counsellor_id,
            "assigned_at": student.get("counsellor_assigned_at", student.get("created_at")),
            "reassigned_at": datetime.utcnow(),
            "reassigned_by": tenant.user_id
        })
        update_data["counsellor_assignment_history"] = assignment_history
        update_data["counsellor_assigned_at"] = datetime.utcnow()
    elif counsellor_id and not previous_counsellor_id:
        # First assignment
        update_data["counsellor_assigned_at"] = datetime.utcnow()
    
    await database.users.update_one(
        {"_id": sid},
        {"$set": update_data}
    )

    # Update all messages to mark previous counsellor for masking
    # This ensures new counsellor can see full history but previous counsellor names are masked
    if previous_counsellor_id and prev_cid_str != counsellor_id:
        from app.core.tenant_strategy import TenantAwareRepository
        repo = TenantAwareRepository(database, "messages")
        
        # Mark messages from previous counsellor for masking
        await repo.update_one(
            tenant.institution_id,
            {
                "student_id": student_id,
                "sender_id": previous_counsellor_id
            },
            {
                "$set": {
                    "previous_counsellor_masked": True,
                    "masked_counsellor_id": previous_counsellor_id
                }
            }
        )
    
    # Audit log
    await AuditLogger.log_action(
        institution_id=tenant.institution_id,
        user_id=tenant.user_id,
        action=AuditAction.UPDATE,
        resource_type="user",
        resource_id=student_id,
        request=request,
        metadata={
            "assignment_action": "assigned" if counsellor_id else "unassigned",
            "previous_counsellor_id": previous_counsellor_id,
            "new_counsellor_id": counsellor_id,
            "student_email": student["email"]
        }
    )
    
    action = "assigned" if counsellor_id else "unassigned"
    return {
        "message": f"Student {action} to counsellor successfully",
        "assigned_counsellor_id": counsellor_id,
        "assigned_counsellor_name": counsellor_name
    }


@router.put("/users/{user_id}/reassign-institution")
async def reassign_user_institution(
    user_id: str,
    request_data: ReassignInstitutionRequest,
    request: Request = None,
    tenant: TenantContext = Depends(require_institution_admin())
):
    """
    Reassign a user (admin, counsellor, or student) to a different institution.
    Note: This should be used carefully as it moves the user to a different tenant.
    """
    database = await get_database()
    default_db = get_default_database()

    uid = validate_object_id(user_id, "user_id")
    user = await database.users.find_one({
        "_id": uid,
        "institution_id": tenant.institution_id
    })
    # Super admin can reassign users with no institution (they appear in the merged list)
    if not user and is_super_admin(tenant):
        user = await default_db.users.find_one({"_id": uid})
        if user and user.get("institution_id") not in (None, ""):
            user = None  # They have an institution but not ours - don't allow
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found in your institution"
        )

    # Restrict counsellor and admin reassignment to super admins only
    if user["role"] in ("counsellor", "admin") and not is_super_admin(tenant):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only super admins can reassign admins or counsellors between institutions. Regular institution admins can only reassign students."
        )
    
    new_institution_id = request_data.new_institution_id
    new_inst_oid = validate_object_id(new_institution_id, "new_institution_id")
    new_institution = await database.institutions.find_one({
        "_id": new_inst_oid,
        "is_active": True
    })

    if not new_institution:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="New institution not found or inactive"
        )
    
    # Check limits in new institution
    settings = new_institution.get("settings", {})
    if user["role"] == "student":
        max_students = settings.get("max_students", 100)
        current_students = await database.users.count_documents({
            "institution_id": new_institution_id,
            "role": "student",
            "is_active": True
        })
        if current_students >= max_students:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"New institution has reached maximum student capacity ({max_students})"
            )
    elif user["role"] == "counsellor":
        max_counsellors = settings.get("max_counsellors", 5)
        current_counsellors = await database.users.count_documents({
            "institution_id": new_institution_id,
            "role": "counsellor",
            "is_active": True
        })
        if current_counsellors >= max_counsellors:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"New institution has reached maximum counsellor capacity ({max_counsellors})"
            )
    
    # If student, unassign from current counsellor (counsellors are institution-specific)
    update_data = {
        "institution_id": new_institution_id,
        "updated_at": datetime.utcnow()
    }
    
    if user["role"] == "student":
        update_data["assigned_counsellor_id"] = None  # Unassign when moving institutions

    # Update in the DB where the user lives (default_db if they had no institution)
    update_db = default_db if user.get("institution_id") in (None, "") else database
    await update_db.users.update_one(
        {"_id": uid},
        {"$set": update_data}
    )

    # Audit log
    await AuditLogger.log_action(
        institution_id=tenant.institution_id,
        user_id=tenant.user_id,
        action=AuditAction.UPDATE,
        resource_type="user",
        resource_id=user_id,
        request=request,
        metadata={
            "reassignment": "institution",
            "old_institution_id": tenant.institution_id,
            "new_institution_id": new_institution_id,
            "user_email": user["email"]
        }
    )
    
    return {
        "message": f"User reassigned to {new_institution.get('name', 'new institution')} successfully",
        "new_institution_id": new_institution_id,
        "new_institution_name": new_institution.get("name")
    }


@router.put("/users/{user_id}/approve")
async def approve_student(
    user_id: str,
    request: Request = None,
    tenant: TenantContext = Depends(require_institution_admin())
):
    """
    Approve a pending student registration.
    Only admins can approve students within their institution.
    """
    database = await get_database()
    
    uid = validate_object_id(user_id, "user_id")
    user = await database.users.find_one({
        "_id": uid,
        "institution_id": tenant.institution_id,
        "role": "student"
    })

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Student not found in your institution"
        )

    if user.get("approval_status") != "pending":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Student is not pending approval. Current status: {user.get('approval_status', 'unknown')}"
        )

    # Update user: approve and activate
    await database.users.update_one(
        {"_id": uid},
        {
            "$set": {
                "is_active": True,
                "approval_status": "approved",
                "approved_at": datetime.utcnow(),
                "approved_by": tenant.user_id,
                "updated_at": datetime.utcnow()
            }
        }
    )
    
    # Audit log
    await AuditLogger.log_action(
        institution_id=tenant.institution_id,
        user_id=tenant.user_id,
        action=AuditAction.UPDATE,
        resource_type="user",
        resource_id=user_id,
        request=request,
        metadata={
            "action": "student_approved",
            "student_email": user["email"]
        }
    )
    
    # Send approval email to student
    from app.core.email import send_email
    student_name = user.get("full_name", "Student")
    student_email = user.get("email", "")
    login_url = f"{settings.FRONTEND_URL}/login"
    
    await send_email(
        to_email=student_email,
        subject="Account Approved - Student Counsellor",
        html_body=f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 30px; text-align: center; border-radius: 10px 10px 0 0; }}
                .content {{ background: #f9f9f9; padding: 30px; border-radius: 0 0 10px 10px; }}
                .button {{ display: inline-block; padding: 12px 30px; background: #667eea; color: white; text-decoration: none; border-radius: 5px; margin: 20px 0; }}
                .footer {{ text-align: center; margin-top: 20px; color: #666; font-size: 12px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>Account Approved!</h1>
                </div>
                <div class="content">
                    <p>Hello {student_name},</p>
                    <p>Great news! Your Student Counsellor account has been approved by an administrator.</p>
                    <p>You can now log in to access your account:</p>
                    <p style="text-align: center;">
                        <a href="{login_url}" class="button">Login Now</a>
                    </p>
                    <p>Or copy and paste this link into your browser:</p>
                    <p style="word-break: break-all; color: #667eea;">{login_url}</p>
                    <p>Best regards,<br>Student Counsellor Team</p>
                </div>
                <div class="footer">
                    <p>This is an automated email. Please do not reply to this message.</p>
                </div>
            </div>
        </body>
        </html>
        """,
        text_body=f"""
        Hello {student_name},
        
        Great news! Your Student Counsellor account has been approved by an administrator.
        
        You can now log in to access your account at:
        {login_url}
        
        Best regards,
        Student Counsellor Team
        """
    )
    
    return {"message": "Student approved successfully. Approval email sent."}


@router.put("/users/{user_id}/reject")
async def reject_student(
    user_id: str,
    reason: Optional[str] = None,
    request: Request = None,
    tenant: TenantContext = Depends(require_institution_admin())
):
    """
    Reject a pending student registration.
    Only admins can reject students within their institution.
    """
    database = await get_database()
    
    uid = validate_object_id(user_id, "user_id")
    user = await database.users.find_one({
        "_id": uid,
        "institution_id": tenant.institution_id,
        "role": "student"
    })

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Student not found in your institution"
        )

    if user.get("approval_status") != "pending":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Student is not pending approval. Current status: {user.get('approval_status', 'unknown')}"
        )

    # Update user: reject and keep inactive
    await database.users.update_one(
        {"_id": uid},
        {
            "$set": {
                "is_active": False,
                "approval_status": "rejected",
                "rejected_at": datetime.utcnow(),
                "rejected_by": tenant.user_id,
                "rejection_reason": reason,
                "updated_at": datetime.utcnow()
            }
        }
    )
    
    # Audit log
    await AuditLogger.log_action(
        institution_id=tenant.institution_id,
        user_id=tenant.user_id,
        action=AuditAction.UPDATE,
        resource_type="user",
        resource_id=user_id,
        request=request,
        metadata={
            "action": "student_rejected",
            "student_email": user["email"],
            "rejection_reason": reason
        }
    )
    
    # Send rejection email to student
    from app.core.email import send_email
    student_name = user.get("full_name", "Student")
    student_email = user.get("email", "")
    
    await send_email(
        to_email=student_email,
        subject="Registration Status - Student Counsellor",
        html_body=f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background: #dc2626; color: white; padding: 30px; text-align: center; border-radius: 10px 10px 0 0; }}
                .content {{ background: #f9f9f9; padding: 30px; border-radius: 0 0 10px 10px; }}
                .footer {{ text-align: center; margin-top: 20px; color: #666; font-size: 12px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>Registration Status</h1>
                </div>
                <div class="content">
                    <p>Hello {student_name},</p>
                    <p>We regret to inform you that your Student Counsellor account registration has been reviewed and was not approved at this time.</p>
                    {f'<p><strong>Reason:</strong> {reason}</p>' if reason else ''}
                    <p>If you believe this is an error or have questions, please contact your institution's administrator.</p>
                    <p>Best regards,<br>Student Counsellor Team</p>
                </div>
                <div class="footer">
                    <p>This is an automated email. Please do not reply to this message.</p>
                </div>
            </div>
        </body>
        </html>
        """,
        text_body=f"""
        Hello {student_name},
        
        We regret to inform you that your Student Counsellor account registration has been reviewed and was not approved at this time.
        
        {f'Reason: {reason}' if reason else ''}
        
        If you believe this is an error or have questions, please contact your institution's administrator.
        
        Best regards,
        Student Counsellor Team
        """
    )
    
    return {"message": "Student registration rejected. Rejection email sent."}
