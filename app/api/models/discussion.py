"""
Discussion API models.
"""
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum


class SessionStatus(str, Enum):
    """
    Session status enum.
    """
    ACTIVE = "active"
    ARCHIVED = "archived"
    DELETED = "deleted"


class MessageRole(str, Enum):
    """
    Message role enum.
    """
    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"
    TOOL = "tool"


class SessionCreate(BaseModel):
    """
    Session creation model.
    """
    title: str = Field(..., min_length=1, max_length=100)
    system_prompt: Optional[str] = None
    tags: Optional[List[str]] = None


class SessionUpdate(BaseModel):
    """
    Session update model.
    """
    title: Optional[str] = Field(None, min_length=1, max_length=100)
    system_prompt: Optional[str] = None
    status: Optional[SessionStatus] = None
    tags: Optional[List[str]] = None


class MessageCreate(BaseModel):
    """
    Message creation model.
    """
    role: MessageRole
    content: str
    metadata: Optional[Dict[str, Any]] = None


class MessageResponse(BaseModel):
    """
    Message response model.
    """
    id: str
    role: str
    content: str
    timestamp: datetime
    metadata: Optional[Dict[str, Any]] = None

    class Config:
        orm_mode = True


class SessionResponse(BaseModel):
    """
    Session response model.
    """
    id: str
    title: str
    system_prompt: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    status: str
    tags: Optional[List[str]] = None

    class Config:
        orm_mode = True


class SessionDetailResponse(SessionResponse):
    """
    Session detail response model with messages.
    """
    messages: List[MessageResponse] = []

    class Config:
        orm_mode = True


class SessionListResponse(BaseModel):
    """
    Session list response model.
    """
    total: int
    limit: int
    offset: int
    sessions: List[SessionResponse]


class MessageListResponse(BaseModel):
    """
    Message list response model.
    """
    session_id: str
    messages: List[MessageResponse]
