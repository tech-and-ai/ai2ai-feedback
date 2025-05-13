"""
Task API models.
"""
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum


class TaskStatus(str, Enum):
    """
    Task status enum.
    """
    NOT_STARTED = "not_started"
    DESIGN = "design"
    BUILD = "build"
    TEST = "test"
    REVIEW = "review"
    COMPLETE = "complete"


class UpdateType(str, Enum):
    """
    Task update type enum.
    """
    STATUS_CHANGE = "status_change"
    PROGRESS_UPDATE = "progress_update"
    NOTE = "note"


class ResearchLikelihood(str, Enum):
    """
    Research likelihood enum.
    """
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class OutputFormat(str, Enum):
    """
    Output format enum.
    """
    ZIP = "zip"
    PDF = "pdf"
    DOCX = "docx"
    JPG = "jpg"
    MARKDOWN = "markdown"
    HTML = "html"
    JSON = "json"
    CSV = "csv"


class TaskCreate(BaseModel):
    """
    Task creation model.
    """
    title: str = Field(..., min_length=1, max_length=100)
    description: str = Field(..., min_length=1)
    complexity: int = Field(..., ge=1, le=10)
    priority: Optional[int] = Field(5, ge=1, le=10)

    # New fields
    research_likelihood: Optional[ResearchLikelihood] = None
    allowed_tools: Optional[List[str]] = None
    output_formats: Optional[List[OutputFormat]] = None
    max_token_usage: Optional[int] = None
    allow_collaboration: Optional[bool] = Field(False)
    max_collaborators: Optional[int] = Field(None, ge=1, le=5)
    human_review_required: Optional[bool] = Field(True)
    deadline: Optional[datetime] = None


class TaskUpdate(BaseModel):
    """
    Task update model.
    """
    title: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = Field(None, min_length=1)
    complexity: Optional[int] = Field(None, ge=1, le=10)
    priority: Optional[int] = Field(None, ge=1, le=10)

    # New fields
    research_likelihood: Optional[ResearchLikelihood] = None
    allowed_tools: Optional[List[str]] = None
    output_formats: Optional[List[OutputFormat]] = None
    max_token_usage: Optional[int] = None
    allow_collaboration: Optional[bool] = None
    max_collaborators: Optional[int] = Field(None, ge=1, le=5)
    human_review_required: Optional[bool] = None
    deadline: Optional[datetime] = None


class TaskStatusUpdate(BaseModel):
    """
    Task status update model.
    """
    status: TaskStatus
    stage_progress: int = Field(..., ge=0, le=100)
    update_message: Optional[str] = None


class TaskUpdateCreate(BaseModel):
    """
    Task update creation model.
    """
    update_type: UpdateType
    content: str


class TaskUpdateResponse(BaseModel):
    """
    Task update response model.
    """
    id: str
    task_id: str
    agent_id: str
    update_type: str
    content: str
    timestamp: datetime

    class Config:
        orm_mode = True


class TaskResponse(BaseModel):
    """
    Task response model.
    """
    id: str
    title: str
    description: str
    complexity: int
    status: str
    stage_progress: int
    created_at: datetime
    updated_at: datetime
    completed_at: Optional[datetime] = None
    assigned_agent_id: Optional[str] = None
    assigned_agent_name: Optional[str] = None
    result_path: Optional[str] = None
    priority: int

    # New fields
    research_likelihood: Optional[str] = None
    allowed_tools: Optional[List[str]] = None
    output_formats: Optional[List[str]] = None
    max_token_usage: Optional[int] = None
    allow_collaboration: Optional[bool] = None
    max_collaborators: Optional[int] = None
    human_review_required: Optional[bool] = None
    deadline: Optional[datetime] = None

    class Config:
        orm_mode = True


class TaskDetailResponse(TaskResponse):
    """
    Task detail response model with updates.
    """
    updates: List[TaskUpdateResponse] = []

    class Config:
        orm_mode = True


class TaskListResponse(BaseModel):
    """
    Task list response model.
    """
    total: int
    limit: int
    offset: int
    tasks: List[TaskResponse]
