"""
Agent Model

This module defines the Agent model and related enums.
"""

from enum import Enum
from typing import Dict, Any
from pydantic import BaseModel, Field

class AgentStatus(str, Enum):
    """Agent status enum."""
    AVAILABLE = "available"
    BUSY = "busy"
    OFFLINE = "offline"

class Agent(BaseModel):
    """Agent model."""
    id: str
    name: str
    description: str
    model: str
    capabilities: Dict[str, Any] = Field(default_factory=dict)
    status: AgentStatus
    last_active: str
    configuration: Dict[str, Any] = Field(default_factory=dict)
    
    class Config:
        """Pydantic config."""
        use_enum_values = True
