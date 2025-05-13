"""
Agent API routes.
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional

from app.db.base import get_db
from app.api.models import (
    AgentCreate, AgentUpdate, AgentStatusUpdate, ToolCreate, ToolUpdate,
    AgentResponse, AgentDetailResponse, AgentListResponse, ToolResponse,
    AgentTaskResponse
)
from app.services.agent_service import AgentService

router = APIRouter()

@router.post("", response_model=AgentResponse, status_code=201)
async def create_agent(
    agent_data: AgentCreate,
    db: AsyncSession = Depends(get_db)
):
    """
    Create a new agent.
    """
    agent_service = AgentService(db)
    agent = await agent_service.create_agent(agent_data)
    return agent

@router.get("", response_model=AgentListResponse)
async def list_agents(
    status: Optional[str] = None,
    model: Optional[str] = None,
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db)
):
    """
    List agents with optional filtering.
    """
    agent_service = AgentService(db)
    agents, total = await agent_service.list_agents(status, model, limit, offset)
    return {
        "total": total,
        "limit": limit,
        "offset": offset,
        "agents": agents
    }

@router.get("/{agent_id}", response_model=AgentDetailResponse)
async def get_agent(
    agent_id: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Get detailed information about a specific agent.
    """
    agent_service = AgentService(db)
    agent = await agent_service.get_agent_with_details(agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    return agent

@router.put("/{agent_id}", response_model=AgentResponse)
async def update_agent(
    agent_id: str,
    agent_data: AgentUpdate,
    db: AsyncSession = Depends(get_db)
):
    """
    Update an agent.
    """
    agent_service = AgentService(db)
    agent = await agent_service.update_agent(agent_id, agent_data)
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    return agent

@router.put("/{agent_id}/status", response_model=AgentResponse)
async def update_agent_status(
    agent_id: str,
    status_data: AgentStatusUpdate,
    db: AsyncSession = Depends(get_db)
):
    """
    Update the status of an agent.
    """
    agent_service = AgentService(db)
    agent = await agent_service.update_agent_status(agent_id, status_data.status)
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    return agent

@router.get("/{agent_id}/tasks", response_model=List[AgentTaskResponse])
async def get_agent_tasks(
    agent_id: str,
    status: Optional[str] = None,
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db)
):
    """
    Get tasks assigned to a specific agent.
    """
    agent_service = AgentService(db)
    tasks = await agent_service.get_agent_tasks(agent_id, status, limit, offset)
    if tasks is None:
        raise HTTPException(status_code=404, detail="Agent not found")
    return tasks

@router.post("/tools", response_model=ToolResponse, status_code=201)
async def create_tool(
    tool_data: ToolCreate,
    db: AsyncSession = Depends(get_db)
):
    """
    Create a new tool.
    """
    agent_service = AgentService(db)
    tool = await agent_service.create_tool(tool_data)
    return tool

@router.get("/tools", response_model=List[ToolResponse])
async def list_tools(
    tool_type: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    """
    List tools with optional filtering.
    """
    agent_service = AgentService(db)
    tools = await agent_service.list_tools(tool_type)
    return tools

@router.get("/tools/{tool_id}", response_model=ToolResponse)
async def get_tool(
    tool_id: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Get information about a specific tool.
    """
    agent_service = AgentService(db)
    tool = await agent_service.get_tool(tool_id)
    if not tool:
        raise HTTPException(status_code=404, detail="Tool not found")
    return tool

@router.put("/tools/{tool_id}", response_model=ToolResponse)
async def update_tool(
    tool_id: str,
    tool_data: ToolUpdate,
    db: AsyncSession = Depends(get_db)
):
    """
    Update a tool.
    """
    agent_service = AgentService(db)
    tool = await agent_service.update_tool(tool_id, tool_data)
    if not tool:
        raise HTTPException(status_code=404, detail="Tool not found")
    return tool

@router.post("/{agent_id}/tools/{tool_id}")
async def assign_tool_to_agent(
    agent_id: str,
    tool_id: str,
    permissions: str = "read",
    db: AsyncSession = Depends(get_db)
):
    """
    Assign a tool to an agent.
    """
    agent_service = AgentService(db)
    success = await agent_service.assign_tool_to_agent(agent_id, tool_id, permissions)
    if not success:
        raise HTTPException(status_code=404, detail="Agent or tool not found")
    return {"message": "Tool assigned to agent successfully"}
