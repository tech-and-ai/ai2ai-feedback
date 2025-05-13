"""
Message Model

This module defines the Message model.
"""

from typing import Dict, Optional, Any
from pydantic import BaseModel, Field

class Message(BaseModel):
    """Message model."""
    id: str
    discussion_id: str
    agent_id: str
    content: str
    created_at: str
    parent_message_id: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
