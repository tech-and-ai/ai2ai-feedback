"""
Autonomous Agent API

This module provides API endpoints for managing autonomous agents and tasks.
"""

import json
import logging
import uuid
from datetime import datetime
from typing import Dict, List, Optional, Any

from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from pydantic import BaseModel, Field

from .database import get_db, Task, TaskContext, TaskUpdate
from .autonomous_agent import agent_manager, AutonomousAgent

# Configure logging
logger = logging.getLogger(__name__)

# Create router
router = APIRouter(prefix="/autonomous", tags=["autonomous"])

# Models
class AgentCreate(BaseModel):
    """Model for creating an agent."""
    name: str = Field(..., description="Agent name")
    role: str = Field(..., description="Agent role description")
    skills: List[str] = Field(..., description="List of agent skills")
    model: str = Field(..., description="AI model to use")
    agent_type: str = Field("standard", description="Agent type (standard or coding)")

class AgentResponse(BaseModel):
    """Model for agent response."""
    agent_id: str = Field(..., description="Agent ID")
    name: str = Field(..., description="Agent name")
    role: str = Field(..., description="Agent role description")
    skills: List[str] = Field(..., description="List of agent skills")
    model: str = Field(..., description="AI model used")
    status: str = Field(..., description="Agent status")
    agent_type: str = Field("standard", description="Agent type (standard or coding)")

class TaskCreate(BaseModel):
    """Model for creating a task."""
    title: str = Field(..., description="Task title")
    description: str = Field(..., description="Task description")
    required_skills: Optional[List[str]] = Field(None, description="Required skills for the task")
    priority: int = Field(1, description="Task priority (higher number = higher priority)")
    parent_task_id: Optional[str] = Field(None, description="Parent task ID for dependencies")
    context: Optional[Dict[str, Any]] = Field(None, description="Additional context for the task")

class TaskResponse(BaseModel):
    """Model for task response."""
    id: str = Field(..., description="Task ID")
    title: str = Field(..., description="Task title")
    description: str = Field(..., description="Task description")
    status: str = Field(..., description="Task status")
    created_by: str = Field(..., description="Creator ID")
    assigned_to: Optional[str] = Field(None, description="Assigned agent ID")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")
    completed_at: Optional[datetime] = Field(None, description="Completion timestamp")
    result: Optional[Dict[str, Any]] = Field(None, description="Task result")
    parent_task_id: Optional[str] = Field(None, description="Parent task ID")
    priority: int = Field(..., description="Task priority")
    required_skills: Optional[List[str]] = Field(None, description="Required skills")
    updates: Optional[List[Dict[str, Any]]] = Field(None, description="Task updates")

    # Custom validator to handle required_skills as string
    @classmethod
    def model_validate(cls, obj, *args, **kwargs):
        if isinstance(obj, dict) and "required_skills" in obj and isinstance(obj["required_skills"], str):
            # Convert comma-separated string to list
            if obj["required_skills"]:
                obj["required_skills"] = [skill.strip() for skill in obj["required_skills"].split(",")]
            else:
                obj["required_skills"] = None
        return super().model_validate(obj, *args, **kwargs)

class TaskUpdateResponse(BaseModel):
    """Model for task update response."""
    id: int = Field(..., description="Update ID")
    task_id: str = Field(..., description="Task ID")
    agent_id: str = Field(..., description="Agent ID")
    content: str = Field(..., description="Update content")
    timestamp: datetime = Field(..., description="Update timestamp")
    level: str = Field(..., description="Update level")

# Routes
@router.post("/agents", response_model=AgentResponse, summary="Create a new autonomous agent")
async def create_agent(agent: AgentCreate):
    """
    Create a new autonomous agent that can select and execute tasks.

    The agent will start running immediately and look for tasks to execute.

    You can create a specialized coding agent by setting agent_type to "coding".
    Coding agents have additional capabilities for working with code, such as
    creating files, running tests, and debugging.
    """
    try:
        agent_id = await agent_manager.create_agent(
            name=agent.name,
            role=agent.role,
            skills=agent.skills,
            model=agent.model,
            agent_type=agent.agent_type
        )

        agent_obj = agent_manager.get_agent(agent_id)

        return {
            "agent_id": agent_id,
            "name": agent_obj.name,
            "role": agent_obj.role,
            "skills": list(agent_obj.skills),
            "model": agent_obj.model,
            "status": agent_obj.status,
            "agent_type": getattr(agent_obj, "agent_type", "standard")
        }
    except Exception as e:
        logger.error(f"Error creating agent: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error creating agent: {str(e)}")

@router.get("/agents", response_model=List[AgentResponse], summary="Get all agents")
async def get_agents():
    """Get all running autonomous agents."""
    try:
        agents = agent_manager.get_all_agents()

        return [
            {
                "agent_id": agent_id,
                "name": agent.name,
                "role": agent.role,
                "skills": list(agent.skills),
                "model": agent.model,
                "status": agent.status,
                "agent_type": getattr(agent, "agent_type", "standard")
            }
            for agent_id, agent in agents.items()
        ]
    except Exception as e:
        logger.error(f"Error getting agents: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error getting agents: {str(e)}")

@router.delete("/agents/{agent_id}", response_model=dict, summary="Stop an agent")
async def stop_agent(agent_id: str):
    """Stop an autonomous agent."""
    try:
        success = await agent_manager.stop_agent(agent_id)

        if not success:
            raise HTTPException(status_code=404, detail=f"Agent {agent_id} not found")

        return {"message": f"Agent {agent_id} stopped successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error stopping agent: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error stopping agent: {str(e)}")

@router.post("/tasks", response_model=TaskResponse, summary="Create a new task")
async def create_task(task: TaskCreate, db: AsyncSession = Depends(get_db)):
    """
    Create a new task for autonomous agents to execute.

    The task will be picked up by an agent with matching skills.
    """
    try:
        # Generate task ID
        task_id = str(uuid.uuid4())

        # Create task
        # Convert required_skills list to comma-separated string for SQLite
        required_skills_str = None
        if task.required_skills:
            required_skills_str = ",".join(task.required_skills)

        db_task = Task(
            id=task_id,
            title=task.title,
            description=task.description,
            status="pending",
            created_by="user",  # Could be user ID or agent ID
            priority=task.priority,
            parent_task_id=task.parent_task_id,
            required_skills=required_skills_str
        )

        db.add(db_task)
        await db.commit()
        await db.refresh(db_task)

        # Add context if provided
        if task.context:
            for key, value in task.context.items():
                context = TaskContext(
                    task_id=task_id,
                    key=key,
                    value=str(value)
                )

                db.add(context)

            await db.commit()

        # Get task with updates
        return await _get_task_with_updates(db, task_id)
    except Exception as e:
        await db.rollback()
        logger.error(f"Error creating task: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error creating task: {str(e)}")

@router.get("/tasks", response_model=List[TaskResponse], summary="Get all tasks")
async def get_tasks(status: Optional[str] = None, db: AsyncSession = Depends(get_db)):
    """
    Get all tasks, optionally filtered by status.

    Status can be: pending, in_progress, completed, failed
    """
    try:
        # Build query
        query = select(Task)

        if status:
            query = query.where(Task.status == status)

        # Execute query
        result = await db.execute(query)
        tasks = result.scalars().all()

        # Get tasks with updates
        task_responses = []
        for task in tasks:
            try:
                task_response = await _get_task_with_updates(db, task.id)
                if task_response:
                    task_responses.append(task_response)
            except Exception as task_error:
                logger.error(f"Error processing task {task.id}: {task_error}")
                # Continue with other tasks
                continue

        return task_responses
    except Exception as e:
        logger.error(f"Error getting tasks: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error getting tasks: {str(e)}")

@router.get("/tasks/{task_id}", response_model=TaskResponse, summary="Get a task by ID")
async def get_task(task_id: str, db: AsyncSession = Depends(get_db)):
    """Get a task by ID with its updates."""
    try:
        task_response = await _get_task_with_updates(db, task_id)

        if not task_response:
            raise HTTPException(status_code=404, detail=f"Task {task_id} not found")

        return task_response
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting task: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error getting task: {str(e)}")

@router.post("/tasks/{task_id}/update", response_model=TaskResponse, summary="Update a task")
async def update_task(task_id: str, update_data: dict, db: AsyncSession = Depends(get_db)):
    """Update a task with new data."""
    try:
        # Get task
        query = select(Task).where(Task.id == task_id)
        result = await db.execute(query)
        task = result.scalars().first()

        if not task:
            raise HTTPException(status_code=404, detail=f"Task {task_id} not found")

        # Update task fields
        for key, value in update_data.items():
            if hasattr(task, key):
                setattr(task, key, value)

        # Update timestamp
        task.updated_at = datetime.utcnow()

        # Commit changes
        await db.commit()
        await db.refresh(task)

        # Log update if status changed
        if "status" in update_data:
            # Create a task update
            update = TaskUpdate(
                task_id=task_id,
                agent_id="system",
                content=f"Task status changed to {update_data['status']}",
                timestamp=datetime.utcnow(),
                level="info"
            )

            db.add(update)
            await db.commit()

        # Get task with updates
        return await _get_task_with_updates(db, task_id)
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"Error updating task: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error updating task: {str(e)}")

class AssignTaskRequest(BaseModel):
    """Model for assigning a task to an agent."""
    agent_id: str = Field(..., description="Agent ID to assign the task to")

@router.post("/tasks/{task_id}/assign", response_model=TaskResponse, summary="Assign a task to an agent")
async def assign_task(task_id: str, assign_data: AssignTaskRequest, db: AsyncSession = Depends(get_db)):
    """Assign a task to a specific agent."""
    try:
        # Get task
        query = select(Task).where(Task.id == task_id)
        result = await db.execute(query)
        task = result.scalars().first()

        if not task:
            raise HTTPException(status_code=404, detail=f"Task {task_id} not found")

        # Check if agent exists
        agent = agent_manager.get_agent(assign_data.agent_id)
        if not agent:
            raise HTTPException(status_code=404, detail=f"Agent {assign_data.agent_id} not found")

        # Update task
        task.assigned_to = assign_data.agent_id
        task.status = "in_progress"
        task.updated_at = datetime.utcnow()

        # Commit changes
        await db.commit()
        await db.refresh(task)

        # Create a task update
        update = TaskUpdate(
            task_id=task_id,
            agent_id="system",
            content=f"Task assigned to agent {assign_data.agent_id} ({agent.name})",
            timestamp=datetime.utcnow(),
            level="info"
        )

        db.add(update)
        await db.commit()

        # Get task with updates
        return await _get_task_with_updates(db, task_id)
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"Error assigning task: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error assigning task: {str(e)}")

async def _get_task_with_updates(db: AsyncSession, task_id: str) -> Optional[Dict[str, Any]]:
    """
    Get a task with its updates.

    Args:
        db: Database session
        task_id: Task ID

    Returns:
        Optional[Dict]: Task with updates or None if not found
    """
    # Get task
    query = select(Task).where(Task.id == task_id)
    result = await db.execute(query)
    task = result.scalars().first()

    if not task:
        return None

    # Get updates
    query = select(TaskUpdate).where(TaskUpdate.task_id == task_id).order_by(TaskUpdate.timestamp)
    result = await db.execute(query)
    updates = result.scalars().all()

    # Get context
    query = select(TaskContext).where(TaskContext.task_id == task_id)
    result = await db.execute(query)
    contexts = result.scalars().all()

    # Convert required_skills from string to list if needed
    required_skills = None
    if task.required_skills:
        required_skills = [skill.strip() for skill in task.required_skills.split(",")]

    # Build response
    task_dict = {
        "id": task.id,
        "title": task.title,
        "description": task.description,
        "status": task.status,
        "created_by": task.created_by,
        "assigned_to": task.assigned_to,
        "created_at": task.created_at,
        "updated_at": task.updated_at,
        "completed_at": task.completed_at,
        "result": json.loads(task.result) if task.result and task.result.strip() else None,
        "parent_task_id": task.parent_task_id,
        "priority": task.priority,
        "required_skills": required_skills,
        "updates": [
            {
                "id": update.id,
                "task_id": update.task_id,
                "agent_id": update.agent_id,
                "content": update.content,
                "timestamp": update.timestamp,
                "level": update.level
            }
            for update in updates
        ],
        "context": {
            context.key: context.value
            for context in contexts
        }
    }

    return task_dict
