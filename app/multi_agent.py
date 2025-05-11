"""
Multi-agent API endpoints for AI-to-AI Feedback API

This module implements the API endpoints for the multi-agent system,
including session creation, message sending, and task management.
"""

import json
import logging
import asyncio
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple
from uuid import uuid4

from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from .database import get_db, Session, Agent, Task
from .models import (
    MultiAgentSessionCreateRequest, MultiAgentMessageRequest,
    MultiAgentMessageResponse, AgentResponse, SessionCreateResponse
)
from .task_management import TaskManager, ContextScaffold
from .agent_loop import agent_task_loop
from .providers.factory import get_model_provider

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("multi-agent")

# Create router
router = APIRouter(prefix="/multi-agent", tags=["multi-agent"])

# Dictionary to store agent task loops
agent_loops = {}

@router.post("/create", response_model=SessionCreateResponse)
async def create_multi_agent_session(
    request: MultiAgentSessionCreateRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db)
):
    """
    Create a new multi-agent session with the specified number of agents.
    """
    try:
        # Create session ID
        session_id = str(uuid4())

        # Create session
        session = Session(
            id=session_id,
            system_prompt=request.system_prompt,
            title=request.title,
            tags=",".join(request.tags) if request.tags else "",
            is_multi_agent=True
        )

        db.add(session)
        await db.commit()

        # Create agents
        for i in range(request.num_agents):
            agent_name = request.agent_names[i] if request.agent_names else f"Agent {i+1}"
            agent_role = request.agent_roles[i] if request.agent_roles else f"Assistant {i+1}"
            agent_model = request.agent_models[i] if request.agent_models else None

            agent = Agent(
                session_id=session_id,
                agent_index=i,
                name=agent_name,
                role=agent_role,
                model=agent_model
            )

            db.add(agent)

        await db.commit()

        # Start agent task loops
        for i in range(request.num_agents):
            agent_id = f"{session_id}_{i}"
            agent_name = request.agent_names[i] if request.agent_names else f"Agent {i+1}"
            agent_role = request.agent_roles[i] if request.agent_roles else f"Assistant {i+1}"
            agent_model = request.agent_models[i] if request.agent_models else None

            # Start agent task loop in background
            background_tasks.add_task(
                start_agent_loop,
                agent_id,
                agent_model,
                agent_role
            )

        logger.info(f"Created multi-agent session {session_id} with {request.num_agents} agents")
        return {"session_id": session_id}
    except Exception as e:
        logger.error(f"Error creating multi-agent session: {e}")
        raise HTTPException(status_code=500, detail=f"Error creating multi-agent session: {str(e)}")

@router.post("/message", response_model=MultiAgentMessageResponse)
async def send_multi_agent_message(
    request: MultiAgentMessageRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Send a message to a multi-agent session and get responses from all agents.
    """
    try:
        # Get session
        stmt = select(Session).where(Session.id == request.session_id)
        result = await db.execute(stmt)
        session = result.scalars().first()

        if not session or not session.is_multi_agent:
            raise HTTPException(status_code=404, detail="Multi-agent session not found")

        # Get agents
        stmt = select(Agent).where(Agent.session_id == request.session_id)
        if request.target_agents:
            stmt = stmt.where(Agent.agent_index.in_(request.target_agents))

        result = await db.execute(stmt)
        agents = result.scalars().all()

        if not agents:
            raise HTTPException(status_code=404, detail="No agents found in session")

        # Create a task for each agent
        responses = []
        for agent in agents:
            agent_id = f"{request.session_id}_{agent.agent_index}"

            # Create a task for the agent
            task_id = await TaskManager.create_task(
                db,
                f"Process message: {request.message[:50]}...",
                request.message,
                request.initiator,
                agent_id,
                session_id=request.session_id
            )

            if not task_id:
                logger.error(f"Failed to create task for agent {agent_id}")
                continue

            # Add initial context
            await ContextScaffold.add_context_entry(
                db,
                task_id,
                "message_type",
                "user_message"
            )

            # Get agent model
            agent_model = agent.model or get_model_provider().get_model_name()

            # Create response placeholder
            responses.append(
                AgentResponse(
                    agent_index=agent.agent_index,
                    agent_name=agent.name,
                    agent_role=agent.role,
                    response="Task created, processing...",
                    model=agent_model
                )
            )

        logger.info(f"Created tasks for {len(responses)} agents in session {request.session_id}")

        return MultiAgentMessageResponse(
            session_id=request.session_id,
            message=request.message,
            responses=responses,
            metadata={
                "timestamp": datetime.utcnow().isoformat(),
                "target_agents": request.target_agents
            }
        )
    except Exception as e:
        logger.error(f"Error sending multi-agent message: {e}")
        raise HTTPException(status_code=500, detail=f"Error sending multi-agent message: {str(e)}")

@router.get("/tasks/{session_id}")
async def get_session_tasks(
    session_id: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Get all tasks for a multi-agent session.
    """
    try:
        # Get session
        stmt = select(Session).where(Session.id == session_id)
        result = await db.execute(stmt)
        session = result.scalars().first()

        if not session or not session.is_multi_agent:
            raise HTTPException(status_code=404, detail="Multi-agent session not found")

        # Get tasks
        stmt = select(Task).where(Task.session_id == session_id)
        result = await db.execute(stmt)
        tasks = result.scalars().all()

        # Format tasks
        formatted_tasks = []
        for task in tasks:
            formatted_tasks.append({
                "id": task.id,
                "title": task.title,
                "description": task.description,
                "status": task.status,
                "created_by": task.created_by,
                "assigned_to": task.assigned_to,
                "created_at": task.created_at.isoformat(),
                "updated_at": task.updated_at.isoformat(),
                "completed_at": task.completed_at.isoformat() if task.completed_at else None,
                "parent_task_id": task.parent_task_id
            })

        return {
            "session_id": session_id,
            "tasks": formatted_tasks
        }
    except Exception as e:
        logger.error(f"Error getting session tasks: {e}")
        raise HTTPException(status_code=500, detail=f"Error getting session tasks: {str(e)}")

@router.get("/agents/{session_id}")
async def get_session_agents(
    session_id: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Get all agents for a multi-agent session.
    """
    try:
        # Get session
        stmt = select(Session).where(Session.id == session_id)
        result = await db.execute(stmt)
        session = result.scalars().first()

        if not session or not session.is_multi_agent:
            raise HTTPException(status_code=404, detail="Multi-agent session not found")

        # Get agents
        stmt = select(Agent).where(Agent.session_id == session_id).order_by(Agent.agent_index)
        result = await db.execute(stmt)
        agents = result.scalars().all()

        # Format agents
        formatted_agents = []
        for agent in agents:
            agent_id = f"{session_id}_{agent.agent_index}"
            formatted_agents.append({
                "index": agent.agent_index,
                "name": agent.name,
                "role": agent.role,
                "model": agent.model,
                "is_active": agent_id in agent_loops
            })

        return {
            "session_id": session_id,
            "agents": formatted_agents
        }
    except Exception as e:
        logger.error(f"Error getting session agents: {e}")
        raise HTTPException(status_code=500, detail=f"Error getting session agents: {str(e)}")

@router.post("/agents/{session_id}/restart/{agent_index}")
async def restart_agent(
    session_id: str,
    agent_index: int,
    db: AsyncSession = Depends(get_db)
):
    """
    Restart an agent's task loop.
    """
    try:
        # Get agent
        stmt = select(Agent).where(
            Agent.session_id == session_id,
            Agent.agent_index == agent_index
        )
        result = await db.execute(stmt)
        agent = result.scalars().first()

        if not agent:
            raise HTTPException(status_code=404, detail="Agent not found")

        # Create agent ID
        agent_id = f"{session_id}_{agent_index}"

        # Cancel existing task if running
        if agent_id in agent_loops:
            agent_loops[agent_id].cancel()
            # Wait a moment for the task to be cancelled
            await asyncio.sleep(0.5)

        # Start new agent loop
        await start_agent_loop(agent_id, agent.model, agent.role)

        return {"success": True, "message": f"Agent {agent_index} restarted"}
    except Exception as e:
        logger.error(f"Error restarting agent: {e}")
        raise HTTPException(status_code=500, detail=f"Error restarting agent: {str(e)}")

@router.post("/agents/{session_id}/start_all")
async def start_all_agents(
    session_id: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Start all agent loops for a session.
    """
    try:
        # Get session
        stmt = select(Session).where(Session.id == session_id)
        result = await db.execute(stmt)
        session = result.scalars().first()

        if not session or not session.is_multi_agent:
            raise HTTPException(status_code=404, detail="Multi-agent session not found")

        # Get agents
        stmt = select(Agent).where(Agent.session_id == session_id).order_by(Agent.agent_index)
        result = await db.execute(stmt)
        agents = result.scalars().all()

        # Start agent loops
        started_count = 0
        for agent in agents:
            agent_id = f"{session_id}_{agent.agent_index}"

            # Skip if already running
            if agent_id in agent_loops:
                continue

            # Start agent loop
            await start_agent_loop(agent_id, agent.model, agent.role)
            started_count += 1

        return {
            "success": True,
            "message": f"Started {started_count} agent loops for session {session_id}"
        }
    except Exception as e:
        logger.error(f"Error starting all agents: {e}")
        raise HTTPException(status_code=500, detail=f"Error starting all agents: {str(e)}")

@router.get("/responses/{session_id}")
async def get_session_responses(
    session_id: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Get all completed task responses for a session.
    """
    try:
        # Get session
        stmt = select(Session).where(Session.id == session_id)
        result = await db.execute(stmt)
        session = result.scalars().first()

        if not session or not session.is_multi_agent:
            raise HTTPException(status_code=404, detail="Multi-agent session not found")

        # Get completed tasks
        stmt = select(Task).where(
            Task.session_id == session_id,
            Task.status == "completed"
        ).order_by(Task.completed_at.desc())
        result = await db.execute(stmt)
        tasks = result.scalars().all()

        # Format responses
        responses = []
        for task in tasks:
            # Get agent info
            agent_id = task.assigned_to
            agent_index = int(agent_id.split('_')[-1]) if agent_id else None

            agent_info = {}
            if agent_index is not None:
                stmt = select(Agent).where(
                    Agent.session_id == session_id,
                    Agent.agent_index == agent_index
                )
                agent_result = await db.execute(stmt)
                agent = agent_result.scalars().first()

                if agent:
                    agent_info = {
                        "index": agent.agent_index,
                        "name": agent.name,
                        "role": agent.role,
                        "model": agent.model
                    }

            responses.append({
                "task_id": task.id,
                "title": task.title,
                "description": task.description,
                "result": task.result,
                "completed_at": task.completed_at.isoformat(),
                "agent": agent_info
            })

        return {
            "session_id": session_id,
            "responses": responses
        }
    except Exception as e:
        logger.error(f"Error getting session responses: {e}")
        raise HTTPException(status_code=500, detail=f"Error getting session responses: {str(e)}")

async def start_agent_loop(agent_id: str, agent_model: str, agent_role: str) -> None:
    """Start an agent task loop"""
    # Check if agent loop is already running
    if agent_id in agent_loops:
        logger.warning(f"Agent loop for {agent_id} is already running")
        return

    # Create task for agent loop
    task = asyncio.create_task(agent_task_loop(agent_id, agent_model, agent_role))

    # Store task
    agent_loops[agent_id] = task

    logger.info(f"Started agent loop for {agent_id}")

    # Set up a callback for when the task completes
    def task_done_callback(t):
        try:
            # Handle any exceptions
            if t.exception():
                logger.error(f"Agent loop for {agent_id} failed: {t.exception()}")
            else:
                logger.info(f"Agent loop for {agent_id} completed normally")
        except asyncio.CancelledError:
            logger.info(f"Agent loop for {agent_id} was cancelled")
        finally:
            # Remove task from dictionary
            agent_loops.pop(agent_id, None)

    # Add the callback
    task.add_done_callback(task_done_callback)
