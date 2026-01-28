from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from enum import Enum


class NoteCategory(str, Enum):
    GENERAL = "general"
    ACADEMIC = "academic"
    CAREER = "career"
    PERSONAL = "personal"
    GOALS = "goals"
    RESOURCES = "resources"


class NoteCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    content: str = Field(..., min_length=1)
    category: NoteCategory = NoteCategory.GENERAL
    tags: Optional[List[str]] = []
    is_private: bool = True  # Private notes only visible to student


class NoteUpdate(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None
    category: Optional[NoteCategory] = None
    tags: Optional[List[str]] = None
    is_private: Optional[bool] = None


class NoteResponse(BaseModel):
    id: str
    student_id: str
    title: str
    content: str
    category: NoteCategory
    tags: List[str] = []
    is_private: bool
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True
