"""
Admin API endpoints for managing users within an institution.
Only accessible by users with admin role.
"""
from fastapi import APIRouter, HTTPException, status, Depends, Request
from datetime import datetime
from bson import ObjectId
from typing import Optional

from app.core.database import get_database
from app.core.security import get_password_hash
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
    try:
        user = await database.users.find_one({
            "_id": ObjectId(user_id),
            "institution_id": tenant.institution_id,
        })
    except Exception:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid user ID")

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found in your institution",
        )

    await database.users.update_one(
        {"_id": ObjectId(user_id)},
        {
            "$set": {
                "password": get_password_hash(body.new_password),
                "password_reset_required": False,
                "updated_at": datetime.utcnow(),
            }
        },
    )

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
    # This ensures users are always created in the admin's institution
    institution_id = tenant.institution_id
    
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
            try:
                counsellor = await database.users.find_one({
                    "_id": ObjectId(user_data.assigned_counsellor_id),
                    "institution_id": institution_id,
                    "role": "counsellor",
                    "is_active": True
                })
                if not counsellor:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="Assigned counsellor not found or not in your institution"
                    )
            except:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid counsellor ID"
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
            "_id": ObjectId(user_dict["assigned_counsellor_id"])
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
    
    # Find user and verify they're in the same institution
    try:
        user = await database.users.find_one({
            "_id": ObjectId(user_id),
            "institution_id": tenant.institution_id
        })
    except:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid user ID"
        )
    
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
    
    # Update user status
    await database.users.update_one(
        {"_id": ObjectId(user_id)},
        {"$set": {"is_active": is_active, "updated_at": datetime.utcnow()}}
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
            "status_change": "activated" if is_active else "deactivated",
            "target_user_email": user["email"]
        }
    )
    
    return {"message": f"User {'activated' if is_active else 'deactivated'} successfully"}


@router.put("/users/{student_id}/assign-counsellor")
async def assign_student_to_counsellor(
    student_id: str,
    counsellor_id: Optional[str] = None,  # None to unassign
    request: Request = None,
    tenant: TenantContext = Depends(require_institution_admin())
):
    """
    Assign or reassign a student to a counsellor within the admin's institution.
    Pass counsellor_id=None to unassign the student.
    """
    database = await get_database()
    
    # Find student and verify they're in the same institution
    try:
        student = await database.users.find_one({
            "_id": ObjectId(student_id),
            "institution_id": tenant.institution_id,
            "role": "student"
        })
    except:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid student ID"
        )
    
    if not student:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Student not found in your institution"
        )
    
    # Validate counsellor if provided
    counsellor_name = None
    if counsellor_id:
        try:
            counsellor = await database.users.find_one({
                "_id": ObjectId(counsellor_id),
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
            current_student_count = await database.users.count_documents({
                "institution_id": tenant.institution_id,
                "assigned_counsellor_id": counsellor_id,
                "role": "student",
                "is_active": True
            })
            
            # If reassigning to a different counsellor, don't count the current student
            if student.get("assigned_counsellor_id") == counsellor_id:
                # Already assigned to this counsellor, no change needed
                pass
            elif current_student_count >= MAX_STUDENTS_PER_COUNSELLOR:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Counsellor has reached maximum capacity ({MAX_STUDENTS_PER_COUNSELLOR} students). Please assign this student to another counsellor."
                )
        except HTTPException:
            raise
        except:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid counsellor ID"
            )
    
    # Track previous counsellor for history preservation
    previous_counsellor_id = student.get("assigned_counsellor_id")
    
    # Update student assignment
    update_data = {
        "assigned_counsellor_id": counsellor_id,
        "updated_at": datetime.utcnow()
    }
    
    # Track assignment history for conversation history preservation
    if previous_counsellor_id and previous_counsellor_id != counsellor_id:
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
        {"_id": ObjectId(student_id)},
        {"$set": update_data}
    )
    
    # Update all messages to mark previous counsellor for masking
    # This ensures new counsellor can see full history but previous counsellor names are masked
    if previous_counsellor_id and previous_counsellor_id != counsellor_id:
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
    Reassign a user (counsellor or student) to a different institution.
    Note: This should be used carefully as it moves the user to a different tenant.
    """
    database = await get_database()
    
    # Find user and verify they're in the admin's institution
    try:
        user = await database.users.find_one({
            "_id": ObjectId(user_id),
            "institution_id": tenant.institution_id
        })
    except:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid user ID"
        )
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found in your institution"
        )
    
    # Restrict counsellor reassignment to super admins only
    if user["role"] == "counsellor" and not is_super_admin(tenant):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only super admins can reassign counsellors between institutions. Regular institution admins can only reassign students."
        )
    
    # Verify new institution exists
    new_institution_id = request_data.new_institution_id
    try:
        new_institution = await database.institutions.find_one({
            "_id": ObjectId(new_institution_id),
            "is_active": True
        })
    except:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid new institution ID"
        )
    
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
    
    await database.users.update_one(
        {"_id": ObjectId(user_id)},
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
    
    # Find user and verify they're in the same institution
    try:
        user = await database.users.find_one({
            "_id": ObjectId(user_id),
            "institution_id": tenant.institution_id,
            "role": "student"
        })
    except:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid user ID"
        )
    
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
        {"_id": ObjectId(user_id)},
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
    
    # Find user and verify they're in the same institution
    try:
        user = await database.users.find_one({
            "_id": ObjectId(user_id),
            "institution_id": tenant.institution_id,
            "role": "student"
        })
    except:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid user ID"
        )
    
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
        {"_id": ObjectId(user_id)},
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
