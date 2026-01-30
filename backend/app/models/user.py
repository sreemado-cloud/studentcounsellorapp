import re
from typing import Annotated, Optional

from pydantic import BaseModel, EmailStr, Field, BeforeValidator
from datetime import datetime
from enum import Enum


def _validate_email_permissive(v: str) -> str:
    """Accept any user@domain.tld-style string for output (UserResponse). Allows .local, .example, etc."""
    if not isinstance(v, str):
        raise ValueError("Email must be a string")
    v = v.strip()
    if not v or "@" not in v:
        raise ValueError("Invalid email format")
    if not re.match(r"^[^\s@]+@[^\s@]+\.[^\s@]+$", v):
        raise ValueError("Invalid email format")
    return v


# Use in output models (e.g. UserResponse) so .local / .example emails from DB don't fail validation.
EmailStrPermissive = Annotated[str, BeforeValidator(_validate_email_permissive)]


class UserRole(str, Enum):
    STUDENT = "student"
    COUNSELLOR = "counsellor"
    ADMIN = "admin"


class UserBase(BaseModel):
    email: EmailStr
    full_name: str = Field(..., min_length=2, max_length=100)
    role: UserRole = UserRole.STUDENT


class UserCreate(UserBase):
    password: str = Field(..., min_length=8)
    institution_id: str = Field(..., description="Institution the user belongs to")
    assigned_counsellor_id: Optional[str] = Field(None, description="Counsellor assigned to this student")
    phone: Optional[str] = None
    grade: Optional[str] = None  # For students
    major: Optional[str] = None  # For students
    bio: Optional[str] = None


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserResponse(BaseModel):
    id: str
    email: EmailStrPermissive
    full_name: str
    role: UserRole
    institution_id: str
    institution_name: Optional[str] = None  # Populated when needed
    assigned_counsellor_id: Optional[str] = None  # For students: their assigned counsellor
    assigned_counsellor_name: Optional[str] = None  # Populated when needed
    phone: Optional[str] = None
    grade: Optional[str] = None
    major: Optional[str] = None
    bio: Optional[str] = None
    profile_image: Optional[str] = None
    created_at: datetime
    is_active: bool = True
    password_reset_required: bool = False  # True if user must reset password on first login
    is_super_admin: bool = False  # True if user email is in SUPER_ADMIN_EMAILS

    class Config:
        from_attributes = True


class UserUpdate(BaseModel):
    full_name: Optional[str] = None
    phone: Optional[str] = None
    grade: Optional[str] = None
    major: Optional[str] = None
    bio: Optional[str] = None
    profile_image: Optional[str] = None
    assigned_counsellor_id: Optional[str] = None  # For students: assign/reassign counsellor
    institution_id: Optional[str] = None  # For reassigning users to different institution


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse
    password_reset_required: bool = False  # Flag indicating if password reset is required


class PasswordResetRequest(BaseModel):
    """Schema for password reset"""
    current_password: str
    new_password: str = Field(..., min_length=8)


class ForgotPasswordRequest(BaseModel):
    """Schema for forgot password request"""
    email: EmailStr


class ResetPasswordWithTokenRequest(BaseModel):
    """Schema for resetting password with token from email"""
    token: str
    new_password: str = Field(..., min_length=8)


class UserInvite(BaseModel):
    """Model for inviting a user to an institution"""
    email: EmailStr
    full_name: str
    role: UserRole = UserRole.STUDENT
