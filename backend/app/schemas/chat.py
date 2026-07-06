from pydantic import BaseModel, Field, field_validator
from typing import Optional, List
from datetime import datetime


class SessionCreate(BaseModel):
    title: Optional[str] = "新会话"


class SessionUpdate(BaseModel):
    title: Optional[str] = None
    status: Optional[str] = None


class SessionResponse(BaseModel):
    id: int
    user_id: int
    title: str
    status: str
    message_count: int = 0
    last_message: Optional[str] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None

    class Config:
        from_attributes = True

    @field_validator("created_at", "updated_at", mode="before")
    @classmethod
    def datetime_to_str(cls, v):
        if isinstance(v, datetime):
            return v.isoformat()
        return v


class MessageRequest(BaseModel):
    content: str = Field(..., min_length=1, max_length=10000)


class CitationItem(BaseModel):
    chunk_id: int
    content: str
    document_name: str
    score: float = 0.0


class MessageResponse(BaseModel):
    id: int
    session_id: int
    role: str
    content: str
    citations: Optional[List[CitationItem]] = None
    token_count: int = 0
    created_at: Optional[str] = None

    class Config:
        from_attributes = True

    @field_validator("created_at", mode="before")
    @classmethod
    def msg_datetime_to_str(cls, v):
        if isinstance(v, datetime):
            return v.isoformat()
        return v


class ChatHistoryResponse(BaseModel):
    messages: List[MessageResponse]
    total: int
    page: int
    page_size: int