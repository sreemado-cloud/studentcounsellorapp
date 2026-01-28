from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from enum import Enum


class AppointmentStatus(str, Enum):
    PENDING = "pending"
    CONFIRMED = "confirmed"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class AppointmentType(str, Enum):
    ACADEMIC = "academic"
    CAREER = "career"
    PERSONAL = "personal"
    MENTAL_HEALTH = "mental_health"
    OTHER = "other"


class AppointmentCreate(BaseModel):
    counsellor_id: str
    date: datetime
    duration_minutes: int = Field(default=30, ge=15, le=120)
    appointment_type: AppointmentType
    title: str = Field(..., min_length=3, max_length=200)
    description: Optional[str] = None


class AppointmentUpdate(BaseModel):
    date: Optional[datetime] = None
    status: Optional[AppointmentStatus] = None
    title: Optional[str] = None
    description: Optional[str] = None
    notes: Optional[str] = None  # Counsellor notes after session


class AppointmentResponse(BaseModel):
    id: str
    student_id: str
    student_name: Optional[str] = None
    counsellor_id: str
    counsellor_name: Optional[str] = None
    date: datetime
    duration_minutes: int
    appointment_type: AppointmentType
    status: AppointmentStatus
    title: str
    description: Optional[str] = None
    notes: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True
