"""
Task Model

This module defines the Task model and related enums.
"""

from enum import Enum
from typing import Dict, Optional, Any
from pydantic import BaseModel, Field

class TaskStatus(str, Enum):
    """Task status enum."""
    NOT_STARTED = "not_started"
    PLANNING = "planning"
    RESEARCHING = "researching"
    EXECUTING = "executing"
    REVIEWING = "reviewing"
    COMPLETED = "completed"
    FAILED = "failed"

class TaskPriority(int, Enum):
    """Task priority enum."""
    LOW = 1
    MEDIUM = 5
    HIGH = 10

class Task(BaseModel):
    """Task model."""
    id: str
    title: str
    description: str
    status: TaskStatus
    priority: TaskPriority
    created_at: str
    updated_at: str
    assigned_agent_id: Optional[str] = None
    parent_task_id: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
    
    class Config:
        """Pydantic config."""
        use_enum_values = True
