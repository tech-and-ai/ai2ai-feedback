"""
Discussion Model

This module defines the Discussion model and related enums.
"""

from enum import Enum
from typing import Dict, Any
from pydantic import BaseModel, Field

class DiscussionStatus(str, Enum):
    """Discussion status enum."""
    ACTIVE = "active"
    RESOLVED = "resolved"
    ARCHIVED = "archived"

class Discussion(BaseModel):
    """Discussion model."""
    id: str
    task_id: str
    title: str
    status: DiscussionStatus
    created_at: str
    updated_at: str
    metadata: Dict[str, Any] = Field(default_factory=dict)
    
    class Config:
        """Pydantic config."""
        use_enum_values = True
