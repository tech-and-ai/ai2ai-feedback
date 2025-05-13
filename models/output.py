"""
Output Model

This module defines the Output model and related enums.
"""

from enum import Enum
from typing import Dict, Any
from pydantic import BaseModel, Field

class OutputType(str, Enum):
    """Output type enum."""
    TEXT = "text"
    CODE = "code"
    HTML = "html"
    JSON = "json"
    MARKDOWN = "markdown"

class Output(BaseModel):
    """Output model."""
    id: str
    task_id: str
    agent_id: str
    type: OutputType
    content: str
    created_at: str
    metadata: Dict[str, Any] = Field(default_factory=dict)
    
    class Config:
        """Pydantic config."""
        use_enum_values = True
