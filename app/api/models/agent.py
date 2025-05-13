"""
Agent API models.
"""
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum


class AgentStatus(str, Enum):
    """
    Agent status enum.
    """
    AVAILABLE = "available"
    BUSY = "busy"
    OFFLINE = "offline"


class ToolType(str, Enum):
    """
    Tool type enum.
    """
    TERMINAL = "terminal"
    PYTHON = "python"
    SEARCH = "search"
    GITHUB = "github"
    EMAIL = "email"
    FILE = "file"
    OTHER = "other"


class AgentCreate(BaseModel):
    """
    Agent creation model.
    """
    name: str = Field(..., min_length=1, max_length=100)
    model: str = Field(..., min_length=1)
    endpoint: str = Field(..., min_length=1)
    min_complexity: int = Field(..., ge=1, le=10)
    max_complexity: int = Field(..., ge=1, le=10)


class AgentUpdate(BaseModel):
    """
    Agent update model.
    """
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    model: Optional[str] = Field(None, min_length=1)
    endpoint: Optional[str] = Field(None, min_length=1)
    min_complexity: Optional[int] = Field(None, ge=1, le=10)
    max_complexity: Optional[int] = Field(None, ge=1, le=10)


class AgentStatusUpdate(BaseModel):
    """
    Agent status update model.
    """
    status: AgentStatus


class ToolCreate(BaseModel):
    """
    Tool creation model.
    """
    name: str = Field(..., min_length=1, max_length=100)
    description: str = Field(..., min_length=1)
    type: ToolType
    config: Optional[Dict[str, Any]] = None


class ToolUpdate(BaseModel):
    """
    Tool update model.
    """
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = Field(None, min_length=1)
    type: Optional[ToolType] = None
    config: Optional[Dict[str, Any]] = None


class ToolResponse(BaseModel):
    """
    Tool response model.
    """
    id: str
    name: str
    description: str
    type: str
    config: Optional[Dict[str, Any]] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True


class AgentTaskResponse(BaseModel):
    """
    Agent task response model.
    """
    id: str
    title: str
    status: str
    stage_progress: int
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True


class AgentResponse(BaseModel):
    """
    Agent response model.
    """
    id: str
    name: str
    model: str
    endpoint: str
    status: str
    min_complexity: int
    max_complexity: int
    created_at: datetime
    last_active: datetime
    current_task: Optional[AgentTaskResponse] = None

    class Config:
        orm_mode = True


class AgentDetailResponse(AgentResponse):
    """
    Agent detail response model with current tasks and tools.
    """
    current_tasks: List[AgentTaskResponse] = []
    tools: List[ToolResponse] = []

    class Config:
        orm_mode = True


class AgentListResponse(BaseModel):
    """
    Agent list response model.
    """
    total: int
    limit: int
    offset: int
    agents: List[AgentResponse]
