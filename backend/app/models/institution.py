"""
Institution model for multi-tenant architecture.
An institution (school/university) is the top-level tenant.
"""
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from datetime import datetime
from enum import Enum


class SubscriptionTier(str, Enum):
    FREE = "free"
    BASIC = "basic"
    PROFESSIONAL = "professional"
    ENTERPRISE = "enterprise"


class InstitutionSettings(BaseModel):
    """Configurable settings per institution"""
    branding_color: Optional[str] = "#3B82F6"
    logo_url: Optional[str] = None
    max_counsellors: int = 5
    max_students: int = 100
    features_enabled: list[str] = ["appointments", "messages", "notes"]
    custom_domain: Optional[str] = None


class InstitutionBase(BaseModel):
    name: str = Field(..., min_length=2, max_length=200)
    domain: Optional[str] = Field(None, description="Email domain for auto-assignment, e.g., 'university.edu'")
    subscription_tier: SubscriptionTier = SubscriptionTier.FREE


class InstitutionCreate(InstitutionBase):
    settings: Optional[InstitutionSettings] = None


class InstitutionUpdate(BaseModel):
    name: Optional[str] = None
    domain: Optional[str] = None
    subscription_tier: Optional[SubscriptionTier] = None
    settings: Optional[InstitutionSettings] = None
    is_active: Optional[bool] = None


class InstitutionResponse(InstitutionBase):
    id: str
    settings: InstitutionSettings
    is_active: bool = True
    created_at: datetime
    updated_at: Optional[datetime] = None
    user_count: Optional[int] = None
    
    class Config:
        from_attributes = True


class InstitutionStats(BaseModel):
    """Statistics for an institution"""
    institution_id: str
    total_students: int = 0
    total_counsellors: int = 0
    total_appointments: int = 0
    total_messages: int = 0
    active_users_30d: int = 0
