"""
Agent Routes

This module defines the API routes for agents.
"""

import logging
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from pydantic import BaseModel

from models.agent import Agent, AgentStatus

router = APIRouter()
logger = logging.getLogger(__name__)

class AgentCreate(BaseModel):
    """Agent creation model."""
    name: str
    description: str
    model: str
    capabilities: dict = {}
    configuration: dict = {}

class AgentUpdate(BaseModel):
    """Agent update model."""
    name: Optional[str] = None
    description: Optional[str] = None
    model: Optional[str] = None
    capabilities: Optional[dict] = None
    status: Optional[AgentStatus] = None
    configuration: Optional[dict] = None

@router.post("/", response_model=Agent, status_code=201)
async def create_agent(agent_create: AgentCreate, request: Request):
    """
    Create a new agent.
    
    Args:
        agent_create: Agent creation data
        request: Request object
        
    Returns:
        Created agent
    """
    agent_manager = request.app.state.agent_manager
    
    agent = await agent_manager.create_agent(
        name=agent_create.name,
        description=agent_create.description,
        model=agent_create.model,
        capabilities=agent_create.capabilities,
        configuration=agent_create.configuration
    )
    
    return agent

@router.get("/{agent_id}", response_model=Agent)
async def get_agent(agent_id: str, request: Request):
    """
    Get an agent by ID.
    
    Args:
        agent_id: Agent ID
        request: Request object
        
    Returns:
        Agent if found
    """
    agent_manager = request.app.state.agent_manager
    
    agent = await agent_manager.get_agent(agent_id)
    
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    
    return agent

@router.put("/{agent_id}", response_model=Agent)
async def update_agent(agent_id: str, agent_update: AgentUpdate, request: Request):
    """
    Update an agent.
    
    Args:
        agent_id: Agent ID
        agent_update: Agent update data
        request: Request object
        
    Returns:
        Updated agent
    """
    agent_manager = request.app.state.agent_manager
    
    # Filter out None values
    update_data = {k: v for k, v in agent_update.dict().items() if v is not None}
    
    agent = await agent_manager.update_agent(agent_id, **update_data)
    
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    
    return agent

@router.delete("/{agent_id}", status_code=204)
async def delete_agent(agent_id: str, request: Request):
    """
    Delete an agent.
    
    Args:
        agent_id: Agent ID
        request: Request object
    """
    agent_manager = request.app.state.agent_manager
    
    result = await agent_manager.delete_agent(agent_id)
    
    if not result:
        raise HTTPException(status_code=404, detail="Agent not found")

@router.get("/", response_model=List[Agent])
async def list_agents(
    request: Request,
    status: Optional[AgentStatus] = None,
    model: Optional[str] = None,
    limit: int = Query(100, ge=1, le=100),
    offset: int = Query(0, ge=0)
):
    """
    List agents with optional filtering.
    
    Args:
        request: Request object
        status: Filter by status
        model: Filter by model
        limit: Maximum number of agents to return
        offset: Offset for pagination
        
    Returns:
        List of agents
    """
    agent_manager = request.app.state.agent_manager
    
    agents = await agent_manager.list_agents(
        status=status,
        model=model,
        limit=limit,
        offset=offset
    )
    
    return agents

@router.post("/{agent_id}/status/{status}", response_model=Agent)
async def update_agent_status(agent_id: str, status: AgentStatus, request: Request):
    """
    Update an agent's status.
    
    Args:
        agent_id: Agent ID
        status: New status
        request: Request object
        
    Returns:
        Updated agent
    """
    agent_manager = request.app.state.agent_manager
    
    agent = await agent_manager.update_agent_status(agent_id, status)
    
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    
    return agent
