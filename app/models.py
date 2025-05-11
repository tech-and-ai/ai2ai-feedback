"""
Pydantic models for AI-to-AI Feedback API
"""

from datetime import datetime
from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field, validator

# Request models
class FeedbackRequest(BaseModel):
    """Request model for getting feedback"""
    context: str = Field(..., description="Current context or reasoning")
    question: str = Field(..., description="Specific question or area of uncertainty")

class SessionCreateRequest(BaseModel):
    """Request model for creating a session"""
    system_prompt: Optional[str] = Field(None, description="Optional system prompt for the session")
    title: Optional[str] = Field(None, description="Optional title for the session")
    tags: Optional[List[str]] = Field(None, description="Optional list of tags for categorization")

class SessionFeedbackRequest(BaseModel):
    """Request model for getting feedback with session context"""
    session_id: str = Field(..., description="ID of the session to use")
    context: str = Field(..., description="Current context or reasoning")
    question: str = Field(..., description="Specific question or area of uncertainty")

class SessionProcessRequest(BaseModel):
    """Request model for processing text with potential feedback"""
    session_id: str = Field(..., description="ID of the session to use")
    text: str = Field(..., description="Text to process")

class SessionEndRequest(BaseModel):
    """Request model for ending a session"""
    session_id: str = Field(..., description="ID of the session to end")

# Multi-agent models
class UnifiedDiscussionCreateRequest(BaseModel):
    """Request model for creating a discussion session with any number of agents"""
    num_agents: int = Field(1, description="Number of AI agents to participate (default: 1, max: 10)")
    system_prompt: Optional[str] = Field(None, description="Optional system prompt for the session")
    title: Optional[str] = Field(None, description="Optional title for the session")
    tags: Optional[List[str]] = Field(None, description="Optional list of tags for categorization")
    agent_names: Optional[List[str]] = Field(None, description="Optional names for the agents")
    agent_roles: Optional[List[str]] = Field(None, description="Optional roles for the agents")
    agent_models: Optional[List[str]] = Field(None, description="Optional models for the agents")
    chair_role: Optional[str] = Field("Claude", description="The name of the chair (default: Claude)")

    @validator('num_agents')
    def validate_num_agents(cls, v):
        if v < 1:
            raise ValueError('num_agents must be at least 1')
        if v > 10:
            raise ValueError('num_agents must be at most 10')
        return v

    @validator('agent_names')
    def validate_agent_names(cls, v, values):
        if v is not None and len(v) != values.get('num_agents', 0):
            raise ValueError('agent_names must have the same length as num_agents')
        return v

    @validator('agent_roles')
    def validate_agent_roles(cls, v, values):
        if v is not None and len(v) != values.get('num_agents', 0):
            raise ValueError('agent_roles must have the same length as num_agents')
        return v

    @validator('agent_models')
    def validate_agent_models(cls, v, values):
        if v is not None and len(v) != values.get('num_agents', 0):
            raise ValueError('agent_models must have the same length as num_agents')
        return v

# For backward compatibility
class MultiAgentSessionCreateRequest(UnifiedDiscussionCreateRequest):
    """Request model for creating a multi-agent session (legacy)"""

    @validator('num_agents')
    def validate_num_agents(cls, v):
        if v < 2:
            raise ValueError('num_agents must be at least 2')
        if v > 10:
            raise ValueError('num_agents must be at most 10')
        return v

class UnifiedDiscussionMessageRequest(BaseModel):
    """Request model for sending a message to any discussion session"""
    session_id: str = Field(..., description="ID of the session to use")
    message: str = Field(..., description="Message to send to the agents")
    target_agents: Optional[List[int]] = Field(None, description="Optional list of agent indices to target (0-based)")
    initiator: Optional[str] = Field("user", description="Who is initiating this message (user or agent index)")
    context: Optional[str] = Field(None, description="Optional context for the message (used in one-to-one feedback)")
    question: Optional[str] = Field(None, description="Optional specific question (used in one-to-one feedback)")

# For backward compatibility
class MultiAgentMessageRequest(BaseModel):
    """Request model for sending a message to a multi-agent session (legacy)"""
    session_id: str = Field(..., description="ID of the session to use")
    message: str = Field(..., description="Message to send to the agents")
    target_agents: Optional[List[int]] = Field(None, description="Optional list of agent indices to target (0-based)")
    initiator: Optional[str] = Field("user", description="Who is initiating this message (user or agent index)")

class AgentResponse(BaseModel):
    """Response model for an individual agent's response"""
    agent_index: int = Field(..., description="Index of the agent")
    agent_name: Optional[str] = Field(None, description="Name of the agent")
    agent_role: Optional[str] = Field(None, description="Role of the agent")
    response: str = Field(..., description="Response from the agent")
    model: str = Field(..., description="Model used by the agent")

class UnifiedDiscussionMessageResponse(BaseModel):
    """Response model for any discussion message"""
    session_id: str = Field(..., description="ID of the session")
    message: str = Field(..., description="Original message")
    responses: List[AgentResponse] = Field(..., description="Responses from the agents")
    metadata: Dict[str, Any] = Field(..., description="Metadata about the response")
    structured: Optional[Dict[str, str]] = Field(None, description="Optional structured feedback (for one-to-one feedback)")

# For backward compatibility
class MultiAgentMessageResponse(BaseModel):
    """Response model for a multi-agent message (legacy)"""
    session_id: str = Field(..., description="ID of the session")
    message: str = Field(..., description="Original message")
    responses: List[AgentResponse] = Field(..., description="Responses from the agents")
    metadata: Dict[str, Any] = Field(..., description="Metadata about the response")

# Response models
class FeedbackResponse(BaseModel):
    """Response model for feedback"""
    feedback: str = Field(..., description="Feedback from the larger model")
    structured: Dict[str, str] = Field(..., description="Structured feedback components")
    metadata: Dict[str, Any] = Field(..., description="Metadata about the feedback")

class SessionCreateResponse(BaseModel):
    """Response model for session creation"""
    session_id: str = Field(..., description="ID of the created session")

class ProcessResponse(BaseModel):
    """Response model for text processing"""
    response: str = Field(..., description="Response from the model")
    metadata: Dict[str, Any] = Field(..., description="Metadata about the response")

class SessionEndResponse(BaseModel):
    """Response model for session ending"""
    success: bool = Field(..., description="Whether the session was successfully ended")

# Memory models
class MemoryCreateRequest(BaseModel):
    """Request model for creating a memory"""
    content: str = Field(..., description="Memory content")
    source: Optional[str] = Field(None, description="Source of the memory")
    importance: float = Field(0.5, description="Importance rating (0-1)")
    tags: Optional[List[str]] = Field(None, description="Optional list of tags")

class MemoryResponse(BaseModel):
    """Response model for memory"""
    id: int = Field(..., description="Memory ID")
    content: str = Field(..., description="Memory content")
    source: Optional[str] = Field(None, description="Source of the memory")
    importance: float = Field(..., description="Importance rating (0-1)")
    tags: Optional[List[str]] = Field(None, description="List of tags")
    timestamp: datetime = Field(..., description="Timestamp of creation")
    similarity: Optional[float] = Field(None, description="Similarity score if from search")

class MemorySearchRequest(BaseModel):
    """Request model for searching memories"""
    query: str = Field(..., description="Search query")
    limit: int = Field(5, description="Maximum number of results")

# Code snippet models
class CodeSnippetCreateRequest(BaseModel):
    """Request model for creating a code snippet"""
    title: str = Field(..., description="Title of the snippet")
    language: str = Field(..., description="Programming language")
    code: str = Field(..., description="Code content")
    description: Optional[str] = Field(None, description="Optional description")
    tags: Optional[List[str]] = Field(None, description="Optional list of tags")

class CodeSnippetResponse(BaseModel):
    """Response model for code snippet"""
    id: int = Field(..., description="Snippet ID")
    title: str = Field(..., description="Title of the snippet")
    language: str = Field(..., description="Programming language")
    code: str = Field(..., description="Code content")
    description: Optional[str] = Field(None, description="Description")
    tags: Optional[List[str]] = Field(None, description="List of tags")
    created_at: datetime = Field(..., description="Timestamp of creation")
    last_used: datetime = Field(..., description="Timestamp of last use")
    usage_count: int = Field(..., description="Number of times used")
    similarity: Optional[float] = Field(None, description="Similarity score if from search")

class CodeSnippetSearchRequest(BaseModel):
    """Request model for searching code snippets"""
    query: str = Field(..., description="Search query")
    language: Optional[str] = Field(None, description="Optional language filter")
    limit: int = Field(5, description="Maximum number of results")
