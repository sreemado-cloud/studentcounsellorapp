"""
Authentication API with multi-tenant support.
Users are registered within an institution context.
"""
from fastapi import APIRouter, HTTPException, status, Depends, Request
from fastapi.security import OAuth2PasswordRequestForm
from datetime import datetime, timedelta
from bson import ObjectId
import traceback

from app.core.database import get_database, get_default_database
from app.core.security import (
    get_password_hash,
    verify_password,
    create_access_token,
    get_current_active_user,
    oauth2_scheme,
)
from app.core.audit import AuditLogger, AuditAction
from app.core.tenant import is_email_super_admin
from app.core.validators import validate_object_id
from app.core.rate_limit import (
    limiter,
    LOGIN_RATE_LIMIT,
    REGISTER_RATE_LIMIT,
    FORGOT_PASSWORD_RATE_LIMIT,
    RESET_PASSWORD_RATE_LIMIT
)
from app.core.token_revocation import add_session, delete_session, delete_sessions_for_user
from app.models.user import (
    UserCreate, UserResponse, Token, UserLogin, PasswordResetRequest,
    ForgotPasswordRequest, ResetPasswordWithTokenRequest
)
from app.core.email import send_password_reset_email, send_student_registration_notification
from app.core.config import settings
from jose import JWTError, jwt
import re
import secrets

router = APIRouter(prefix="/api/auth", tags=["Authentication"])


@router.post("/register", status_code=status.HTTP_201_CREATED)
@limiter.limit(REGISTER_RATE_LIMIT)
async def register(user_data: UserCreate, request: Request):
    """
    Register a new user within an institution.
    
    Multi-tenancy: Users must specify their institution_id.
    The institution_id determines which tenant the user belongs to.
    """
    database = await get_database()
    
    # Verify institution exists
    oid = validate_object_id(user_data.institution_id, "institution_id")
    institution = await database.institutions.find_one({
        "_id": oid,
        "is_active": True
    })
    
    if not institution:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Institution not found or inactive"
        )
    
    # Check if user already exists
    existing_user = await database.users.find_one({"email": user_data.email})
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Check institution user limits
    settings = institution.get("settings", {})
    max_students = settings.get("max_students", 100)
    
    # For students: set as inactive (pending admin approval)
    # For counsellors/admins: set as active (they are created by admins)
    is_active = user_data.role != "student"
    
    if user_data.role == "student":
        # Check limits only for active students (pending ones don't count)
        current_students = await database.users.count_documents({
            "institution_id": user_data.institution_id,
            "role": "student",
            "is_active": True
        })
        if current_students >= max_students:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Institution has reached maximum student capacity"
            )
    
    # Create user document with institution_id
    user_dict = user_data.model_dump()
    user_dict["password"] = get_password_hash(user_data.password)
    user_dict["created_at"] = datetime.utcnow()
    user_dict["is_active"] = is_active  # Students need admin approval
    user_dict["profile_image"] = None
    user_dict["password_reset_required"] = True  # Require password reset on first login
    
    # Store approval status for students
    if user_data.role == "student":
        user_dict["approval_status"] = "pending"  # pending, approved, rejected
    
    result = await database.users.insert_one(user_dict)
    user_dict["id"] = str(result.inserted_id)
    
    # Audit log the registration
    await AuditLogger.log_action(
        institution_id=user_data.institution_id,
        user_id=user_dict["id"],
        action=AuditAction.CREATE,
        resource_type="user",
        resource_id=user_dict["id"],
        request=request,
        metadata={"role": user_data.role, "registration": True}
    )
    
    # If student, notify admins and don't create token (they need approval)
    if user_data.role == "student":
        # Find all admins in the institution
        admins = await database.users.find({
            "institution_id": user_data.institution_id,
            "role": "admin",
            "is_active": True
        }).to_list(length=100)
        
        # Send notification email to admins
        from app.core.email import send_email
        student_name = user_dict.get("full_name", "A student")
        student_email = user_dict.get("email", "")
        
        admin_emails = [admin["email"] for admin in admins]
        for admin_email in admin_emails:
            await send_student_registration_notification(
                admin_email=admin_email,
                student_name=student_name,
                student_email=student_email,
                institution_name=institution.get("name", "the institution")
            )
        
        # Remove password from response
        del user_dict["password"]
        if "_id" in user_dict:
            del user_dict["_id"]
        
        # Add institution name to response
        user_dict["institution_name"] = institution["name"]
        
        return {
            "message": "Registration successful. Your account is pending admin approval. You will receive an email once your account is approved.",
            "user": user_dict,
            "requires_approval": True
        }
    
    # For non-students (counsellors/admins created by admins), create token
    access_token, jti, exp = create_access_token(data={"sub": user_dict["id"]})
    await add_session(jti, user_dict["id"], exp)
    
    # Remove password from response
    del user_dict["password"]
    if "_id" in user_dict:
        del user_dict["_id"]
    
    # Add institution name to response
    user_dict["institution_name"] = institution["name"]
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": user_dict,
        "password_reset_required": user_dict.get("password_reset_required", False)
    }


@router.post("/login", response_model=Token)
@limiter.limit(LOGIN_RATE_LIMIT)
async def login(request: Request, form_data: OAuth2PasswordRequestForm = Depends()):
    """
    Login with email and password.
    
    Multi-tenancy: User's institution_id is included in the response
    and used for all subsequent requests.
    """
    import logging
    logger = logging.getLogger(__name__)
    
    try:
        email_input = (form_data.username or "").strip()
        logger.info(f"Login attempt for email: {email_input}")
        if not email_input:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Email is required",
            )
        default_db = get_default_database()
        pattern = "^" + re.escape(email_input) + "$"
        user = await default_db.users.find_one({"email": {"$regex": pattern, "$options": "i"}})
        if not user or not verify_password(form_data.password, user["password"]):
            logger.warning(f"Login failed: Invalid credentials for {email_input}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect email or password",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        if not user.get("is_active", True):
            logger.warning(f"Login failed: Inactive account for {email_input}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Account is inactive"
            )
        
        institution_name = None
        institution_id = user.get("institution_id")
        if institution_id:
            try:
                institution = await default_db.institutions.find_one({"_id": ObjectId(str(institution_id))})
                if institution:
                    institution_name = institution["name"]
            except Exception as e:
                logger.warning(f"Could not fetch institution name: {e}")
        
        # Create access token and record session for revocation
        access_token, jti, exp = create_access_token(data={"sub": str(user["_id"])})
        await add_session(jti, str(user["_id"]), exp)

        # Audit log the login (fire-and-forget - log_action uses create_task internally)
        if institution_id:
            try:
                # Await it - it returns immediately after creating the background task
                await AuditLogger.log_action(
                    institution_id=institution_id,
                    user_id=str(user["_id"]),
                    action=AuditAction.LOGIN,
                    resource_type="session",
                    request=request
                )
            except Exception as e:
                # Don't fail login if audit logging fails
                logger.warning(f"Audit logging failed for login: {e}")
        
        password_reset_required = user.get("password_reset_required", False)
        super_admin = is_email_super_admin(user.get("email", "") or "")

        # Resolve assigned counsellor for students
        assigned_counsellor_id = user.get("assigned_counsellor_id")
        assigned_counsellor_name = None
        if assigned_counsellor_id:
            assigned_counsellor_id = str(assigned_counsellor_id)
            try:
                counsellor = await default_db.users.find_one({"_id": ObjectId(assigned_counsellor_id)})
                if counsellor:
                    assigned_counsellor_name = counsellor.get("full_name")
            except Exception:
                pass
        
        user_response = UserResponse(
            id=str(user["_id"]),
            email=user["email"],
            full_name=user["full_name"],
            role=user["role"],
            institution_id=institution_id or "default",
            institution_name=institution_name,
            assigned_counsellor_id=assigned_counsellor_id,
            assigned_counsellor_name=assigned_counsellor_name,
            phone=user.get("phone"),
            grade=user.get("grade"),
            major=user.get("major"),
            bio=user.get("bio"),
            profile_image=user.get("profile_image"),
            created_at=user["created_at"],
            is_active=user.get("is_active", True),
            password_reset_required=password_reset_required,
            is_super_admin=super_admin,
        )
        
        logger.info(f"Login successful for user: {user['email']} (ID: {user['_id']})")
        return Token(
            access_token=access_token, 
            user=user_response,
            password_reset_required=password_reset_required
        )
    except HTTPException:
        # Re-raise HTTP exceptions (these are expected)
        raise
    except Exception as e:
        # Log unexpected errors and return the real message so UI/logs can show it
        logger.error(f"Unexpected error during login: {str(e)}", exc_info=True)
        detail = str(e) if settings.DEBUG else "An error occurred during login. Please try again."
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=detail,
        )


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(current_user: dict = Depends(get_current_active_user)):
    """Get current logged-in user information"""
    default_db = get_default_database()
    # Use shared DB for both user and institution so we never mix tenant DB (can have wrong/stale data)
    user_for_inst = await default_db.users.find_one({"_id": ObjectId(current_user["id"])})
    institution_id = (user_for_inst or current_user).get("institution_id")
    institution_name = None
    if institution_id:
        try:
            institution = await default_db.institutions.find_one({"_id": ObjectId(str(institution_id))})
            if institution:
                institution_name = institution.get("name")
        except Exception:
            pass
    
    super_admin = is_email_super_admin(current_user.get("email", "") or "")

    # Resolve assigned counsellor for students
    assigned_counsellor_id = (user_for_inst or current_user).get("assigned_counsellor_id")
    assigned_counsellor_name = None
    if assigned_counsellor_id:
        assigned_counsellor_id = str(assigned_counsellor_id)
        try:
            counsellor = await default_db.users.find_one({"_id": ObjectId(assigned_counsellor_id)})
            if counsellor:
                assigned_counsellor_name = counsellor.get("full_name")
        except Exception:
            pass

    return UserResponse(
        id=current_user["id"],
        email=current_user["email"],
        full_name=current_user["full_name"],
        role=current_user["role"],
        institution_id=institution_id or "default",
        institution_name=institution_name,
        assigned_counsellor_id=assigned_counsellor_id,
        assigned_counsellor_name=assigned_counsellor_name,
        phone=current_user.get("phone"),
        grade=current_user.get("grade"),
        major=current_user.get("major"),
        bio=current_user.get("bio"),
        profile_image=current_user.get("profile_image"),
        created_at=current_user["created_at"],
        is_active=current_user.get("is_active", True),
        password_reset_required=current_user.get("password_reset_required", False),
        is_super_admin=super_admin,
    )


@router.get("/debug-institution")
async def debug_institution(current_user: dict = Depends(get_current_active_user)):
    """[DEBUG] Return institution_id and resolved institution_name for current user. 404 when DEBUG=false."""
    if not settings.DEBUG:
        raise HTTPException(status_code=404, detail="Not found")
    default_db = get_default_database()
    user = await default_db.users.find_one({"_id": ObjectId(current_user["id"])})
    institution_id = (user or current_user).get("institution_id")
    institution_name = None
    if institution_id:
        try:
            inst = await default_db.institutions.find_one({"_id": ObjectId(str(institution_id))})
            if inst:
                institution_name = inst.get("name")
        except Exception:
            pass
    return {
        "email": current_user.get("email"),
        "institution_id": institution_id,
        "institution_name": institution_name,
    }


@router.post("/logout")
async def logout(
    request: Request,
    token: str = Depends(oauth2_scheme),
    current_user: dict = Depends(get_current_active_user),
):
    """
    Logout the current user. Revokes the current token (C3).
    Client should discard the token.
    """
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        jti = payload.get("jti")
        if jti:
            await delete_session(jti)
    except (JWTError, Exception):
        pass

    institution_id = current_user.get("institution_id")
    if institution_id:
        await AuditLogger.log_action(
            institution_id=institution_id,
            user_id=current_user["id"],
            action=AuditAction.LOGOUT,
            resource_type="session",
            request=request
        )

    return {"message": "Logged out successfully"}


@router.post("/reset-password")
async def reset_password(
    reset_data: PasswordResetRequest,
    current_user: dict = Depends(get_current_active_user),
    request: Request = None
):
    """
    Reset password for the current user.
    Requires current password for verification.
    """
    database = await get_database()
    
    # Verify current password
    user = await database.users.find_one({"_id": ObjectId(current_user["id"])})
    if not user or not verify_password(reset_data.current_password, user["password"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Current password is incorrect"
        )
    
    # Update password and clear password_reset_required flag
    await database.users.update_one(
        {"_id": ObjectId(current_user["id"])},
        {
            "$set": {
                "password": get_password_hash(reset_data.new_password),
                "password_reset_required": False,
                "updated_at": datetime.utcnow()
            }
        }
    )
    
    # Revoke all tokens for this user (C3)
    await delete_sessions_for_user(current_user["id"])

    institution_id = current_user.get("institution_id")
    if institution_id:
        await AuditLogger.log_action(
            institution_id=institution_id,
            user_id=current_user["id"],
            action=AuditAction.UPDATE,
            resource_type="user",
            resource_id=current_user["id"],
            request=request,
            metadata={"action": "password_reset"}
        )

    return {"message": "Password reset successfully"}


@router.post("/forgot-password")
@limiter.limit(FORGOT_PASSWORD_RATE_LIMIT)
async def forgot_password(
    request_data: ForgotPasswordRequest,
    request: Request
):
    """
    Request password reset via email.
    Sends a password reset link to the user's email if the email exists.
    Always returns success to prevent email enumeration attacks.
    """
    import logging
    logger = logging.getLogger(__name__)
    
    import asyncio
    
    # Return success immediately - process everything in background
    logger.info(f"Forgot password request received for: {request_data.email.lower()}")
    
    # Process the request in background - don't block the response
    async def process_forgot_password_background():
        try:
            database = await get_database()
            
            # Find user by email with timeout
            try:
                user = await asyncio.wait_for(
                    database.users.find_one({"email": request_data.email.lower()}),
                    timeout=10.0  # 10 second timeout for database query
                )
            except asyncio.TimeoutError:
                logger.error(f"Database query timed out for forgot password: {request_data.email.lower()}")
                return
            
            # Only send email if user exists and is active
            if user and user.get("is_active", True):
                try:
                    logger.info(f"User found, generating reset token for: {request_data.email.lower()}")
                    # Generate secure reset token
                    reset_token = secrets.token_urlsafe(32)
                    
                    # Store reset token with expiration (1 hour) - with timeout
                    reset_token_expiry = datetime.utcnow() + timedelta(hours=1)
                    
                    try:
                        await asyncio.wait_for(
                            database.password_reset_tokens.insert_one({
                                "user_id": str(user["_id"]),
                                "token": reset_token,
                                "email": request_data.email.lower(),
                                "expires_at": reset_token_expiry,
                                "used": False,
                                "created_at": datetime.utcnow()
                            }),
                            timeout=5.0  # 5 second timeout for database insert
                        )
                        logger.info(f"Reset token stored for user: {request_data.email.lower()}")
                    except asyncio.TimeoutError:
                        logger.error(f"Database insert timed out for forgot password: {request_data.email.lower()}")
                        # Continue anyway - return success
                    
                    # Send password reset email in background (non-blocking - don't wait for it)
                    # Only attempt if SMTP is configured
                    from app.core.config import settings
                    
                    if settings.SMTP_USER and settings.SMTP_PASSWORD:
                        user_name = user.get("full_name", "User")
                        logger.info(f"Scheduling password reset email to be sent to: {request_data.email.lower()}")
                        
                        # Use asyncio.create_task to send email in background without blocking
                        async def send_email_background():
                            try:
                                email_sent = await asyncio.wait_for(
                                    send_password_reset_email(
                                        email=request_data.email.lower(),
                                        reset_token=reset_token,
                                        user_name=user_name
                                    ),
                                    timeout=10.0  # 10 second timeout for email sending
                                )
                                if email_sent:
                                    logger.info(f"Password reset email sent successfully to: {request_data.email.lower()}")
                                else:
                                    logger.warning(f"Failed to send password reset email to {request_data.email.lower()}")
                            except asyncio.TimeoutError:
                                logger.warning(f"Email sending timed out for {request_data.email.lower()}")
                            except Exception as e:
                                logger.error(f"Error sending password reset email to {request_data.email.lower()}: {str(e)}", exc_info=True)
                        
                        # Fire and forget - don't await
                        asyncio.create_task(send_email_background())
                    else:
                        logger.warning(f"SMTP not configured - skipping email send for {request_data.email.lower()}. Token stored: {reset_token}")
                    
                    # Audit log in background (non-blocking - log_action already uses create_task internally)
                    institution_id = user.get("institution_id")
                    if institution_id:
                        # This is already fire-and-forget (log_action uses asyncio.create_task internally)
                        # Don't await - it's non-blocking
                        AuditLogger.log_action(
                            institution_id=institution_id,
                            user_id=str(user["_id"]),
                            action=AuditAction.UPDATE,
                            resource_type="user",
                            resource_id=str(user["_id"]),
                            request=request,
                            metadata={"action": "forgot_password_requested"}
                        )
                except Exception as e:
                    # Log error but continue
                    logger.error(f"Error processing forgot password request for {request_data.email.lower()}: {str(e)}", exc_info=True)
            else:
                logger.info(f"User not found or inactive for: {request_data.email.lower()}")
        except Exception as e:
            # Log any errors in background processing
            logger.error(f"Error in background forgot password processing: {str(e)}", exc_info=True)
    
    # Start background processing - don't await
    asyncio.create_task(process_forgot_password_background())
    
    # Return success immediately (security best practice)
    logger.info(f"Returning immediate success response for forgot password request: {request_data.email.lower()}")
    return {
        "message": "If an account with that email exists, a password reset link has been sent."
    }


@router.post("/reset-password-with-token")
@limiter.limit(RESET_PASSWORD_RATE_LIMIT)
async def reset_password_with_token(
    reset_data: ResetPasswordWithTokenRequest,
    request: Request = None
):
    """
    Reset password using token from email.
    """
    database = await get_database()
    
    # Find reset token
    reset_token_doc = await database.password_reset_tokens.find_one({
        "token": reset_data.token,
        "used": False
    })
    
    if not reset_token_doc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired reset token"
        )
    
    # Check if token has expired
    if reset_token_doc["expires_at"] < datetime.utcnow():
        # Mark as used even though expired
        await database.password_reset_tokens.update_one(
            {"_id": reset_token_doc["_id"]},
            {"$set": {"used": True}}
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Reset token has expired. Please request a new one."
        )
    
    # Get user
    user = await database.users.find_one({
        "_id": ObjectId(reset_token_doc["user_id"])
    })
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    if not user.get("is_active", True):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Account is inactive"
        )
    
    # Update password
    await database.users.update_one(
        {"_id": ObjectId(reset_token_doc["user_id"])},
        {
            "$set": {
                "password": get_password_hash(reset_data.new_password),
                "password_reset_required": False,  # Clear first login flag too
                "updated_at": datetime.utcnow()
            }
        }
    )
    
    await database.password_reset_tokens.update_one(
        {"_id": reset_token_doc["_id"]},
        {"$set": {"used": True, "used_at": datetime.utcnow()}}
    )

    await delete_sessions_for_user(str(user["_id"]))

    institution_id = user.get("institution_id")
    if institution_id:
        await AuditLogger.log_action(
            institution_id=institution_id,
            user_id=str(user["_id"]),
            action=AuditAction.UPDATE,
            resource_type="user",
            resource_id=str(user["_id"]),
            request=request,
            metadata={"action": "password_reset_with_token"}
        )
    
    return {"message": "Password has been reset successfully. You can now login with your new password."}
