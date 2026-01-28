from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class MessageCreate(BaseModel):
    recipient_id: str
    content: str = Field(..., min_length=1, max_length=5000)
    subject: Optional[str] = Field(None, max_length=200)


class MessageResponse(BaseModel):
    id: str
    sender_id: str
    sender_name: str
    recipient_id: str
    recipient_name: str
    subject: Optional[str] = None
    content: str
    is_read: bool = False
    created_at: datetime
    read_at: Optional[datetime] = None
    
    # For multi-tenancy: student_id links to the student this conversation belongs to
    student_id: str

    class Config:
        from_attributes = True


class ConversationResponse(BaseModel):
    """Groups messages into conversations"""
    participant_id: str
    participant_name: str
    participant_role: str
    last_message: str
    last_message_time: datetime
    unread_count: int
