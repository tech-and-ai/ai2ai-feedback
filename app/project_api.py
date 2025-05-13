"""
Project API for AI-to-AI Feedback API

This module implements API endpoints for project management:
1. Create a new project
2. Get project status
3. Get project tasks
"""

import logging
import uuid
from typing import List, Optional, Dict, Any
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from .database import Task, Agent, TaskUpdate, get_db
from .task_management import ContextScaffold

# Configure logging
logger = logging.getLogger("project-api")

# Create router
router = APIRouter()

# Define models
class ProjectCreate(BaseModel):
    """Model for creating a new project"""
    title: str
    description: str
    required_skills: List[str] = []
    priority: int = 5

class ProjectResponse(BaseModel):
    """Model for project response"""
    id: str
    title: str
    description: str
    status: str
    created_at: datetime
    updated_at: datetime
    required_skills: List[str]
    priority: int
    assigned_to: Optional[str] = None

class TaskResponse(BaseModel):
    """Model for task response"""
    id: str
    title: str
    description: str
    status: str
    created_at: datetime
    updated_at: datetime
    required_skills: List[str]
    task_type: Optional[str] = None
    assigned_to: Optional[str] = None
    estimated_effort: Optional[int] = None
    progress: Optional[int] = None

@router.post("/", response_model=ProjectResponse)
async def create_project(
    project: ProjectCreate,
    db: AsyncSession = Depends(get_db)
):
    """Create a new project"""
    try:
        # Create a project task
        task = Task(
            id=str(uuid.uuid4()),
            title=project.title,
            description=project.description,
            status="pending",
            created_by="user",
            task_type="project",
            required_skills=",".join(project.required_skills),  # Convert list to comma-separated string
            priority=project.priority
        )
        db.add(task)
        await db.commit()

        # Find a controller agent
        query = select(Agent).where(
            Agent.agent_type == "controller",
            Agent.status == "running"
        )
        result = await db.execute(query)
        controller = result.scalars().first()

        if controller:
            # Assign to controller
            task.assigned_to = controller.agent_id
            task.status = "in_progress"
            await db.commit()

            # Add update about assignment
            await ContextScaffold.add_task_update(
                db,
                task.id,
                "system",
                f"Project assigned to controller agent {controller.name} ({controller.agent_id})"
            )

            logger.info(f"Project {task.id} assigned to controller {controller.agent_id}")
        else:
            logger.warning(f"No controller agent available for project {task.id}")

            # Add update about no controller
            await ContextScaffold.add_task_update(
                db,
                task.id,
                "system",
                "No controller agent available. Project will be processed when a controller becomes available."
            )

        # Convert comma-separated string back to list
        required_skills = task.required_skills.split(",") if task.required_skills else []

        return ProjectResponse(
            id=task.id,
            title=task.title,
            description=task.description,
            status=task.status,
            created_at=task.created_at,
            updated_at=task.updated_at,
            required_skills=required_skills,
            priority=task.priority,
            assigned_to=task.assigned_to
        )
    except Exception as e:
        logger.error(f"Error creating project: {e}")
        raise HTTPException(status_code=500, detail=f"Error creating project: {str(e)}")

@router.get("/{project_id}", response_model=ProjectResponse)
async def get_project(
    project_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Get project status"""
    try:
        # Get project
        query = select(Task).where(
            Task.id == project_id,
            Task.task_type == "project"
        )
        result = await db.execute(query)
        project = result.scalars().first()

        if not project:
            raise HTTPException(status_code=404, detail=f"Project {project_id} not found")

        # Convert comma-separated string back to list
        required_skills = project.required_skills.split(",") if project.required_skills else []

        return ProjectResponse(
            id=project.id,
            title=project.title,
            description=project.description,
            status=project.status,
            created_at=project.created_at,
            updated_at=project.updated_at,
            required_skills=required_skills,
            priority=project.priority,
            assigned_to=project.assigned_to
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting project: {e}")
        raise HTTPException(status_code=500, detail=f"Error getting project: {str(e)}")

@router.get("/{project_id}/tasks", response_model=List[TaskResponse])
async def get_project_tasks(
    project_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Get project tasks"""
    try:
        # Get project
        query = select(Task).where(
            Task.id == project_id,
            Task.task_type == "project"
        )
        result = await db.execute(query)
        project = result.scalars().first()

        if not project:
            raise HTTPException(status_code=404, detail=f"Project {project_id} not found")

        # Get tasks
        query = select(Task).where(
            Task.project_id == project_id
        )
        result = await db.execute(query)
        tasks = result.scalars().all()

        return [
            TaskResponse(
                id=task.id,
                title=task.title,
                description=task.description,
                status=task.status,
                created_at=task.created_at,
                updated_at=task.updated_at,
                required_skills=task.required_skills.split(",") if task.required_skills else [],
                task_type=task.task_type,
                assigned_to=task.assigned_to,
                estimated_effort=task.estimated_effort,
                progress=task.progress
            )
            for task in tasks
        ]
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting project tasks: {e}")
        raise HTTPException(status_code=500, detail=f"Error getting project tasks: {str(e)}")

class TaskAssignRequest(BaseModel):
    """Model for assigning a task to an agent"""
    agent_id: str

class TaskUpdateResponse(BaseModel):
    """Model for task update response"""
    agent_id: str
    content: str
    timestamp: datetime

@router.post("/tasks/{task_id}/assign", response_model=TaskResponse)
async def assign_task(
    task_id: str,
    request: TaskAssignRequest,
    db: AsyncSession = Depends(get_db)
):
    """Assign a task to an agent"""
    try:
        # Get task
        query = select(Task).where(
            Task.id == task_id
        )
        result = await db.execute(query)
        task = result.scalars().first()

        if not task:
            raise HTTPException(status_code=404, detail=f"Task {task_id} not found")

        # Get agent
        query = select(Agent).where(
            Agent.agent_id == request.agent_id
        )
        result = await db.execute(query)
        agent = result.scalars().first()

        if not agent:
            raise HTTPException(status_code=404, detail=f"Agent {request.agent_id} not found")

        # Assign task to agent
        task.assigned_to = agent.agent_id
        task.status = "in_progress"

        # Update agent workload
        agent.current_workload += 1

        await db.commit()

        # Add update about assignment
        await ContextScaffold.add_task_update(
            db,
            task.id,
            "system",
            f"Task assigned to agent {agent.name} ({agent.agent_id})"
        )

        logger.info(f"Task {task.id} assigned to agent {agent.agent_id}")

        return TaskResponse(
            id=task.id,
            title=task.title,
            description=task.description,
            status=task.status,
            created_at=task.created_at,
            updated_at=task.updated_at,
            required_skills=task.required_skills.split(",") if task.required_skills else [],
            task_type=task.task_type,
            assigned_to=task.assigned_to,
            estimated_effort=task.estimated_effort,
            progress=task.progress
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error assigning task: {e}")
        raise HTTPException(status_code=500, detail=f"Error assigning task: {str(e)}")

@router.get("/tasks/{task_id}/updates", response_model=List[TaskUpdateResponse])
async def get_task_updates(
    task_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Get updates for a task"""
    try:
        # Get task
        query = select(Task).where(
            Task.id == task_id
        )
        result = await db.execute(query)
        task = result.scalars().first()

        if not task:
            raise HTTPException(status_code=404, detail=f"Task {task_id} not found")

        # Get updates
        query = select(TaskUpdate).where(
            TaskUpdate.task_id == task_id
        ).order_by(TaskUpdate.timestamp)
        result = await db.execute(query)
        updates = result.scalars().all()

        return [
            TaskUpdateResponse(
                agent_id=update.agent_id,
                content=update.content,
                timestamp=update.timestamp
            )
            for update in updates
        ]
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting task updates: {e}")
        raise HTTPException(status_code=500, detail=f"Error getting task updates: {str(e)}")

@router.get("/{project_id}/updates", response_model=List[TaskUpdateResponse])
async def get_project_updates(
    project_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Get all updates for a project and its tasks"""
    try:
        # Get project
        query = select(Task).where(
            Task.id == project_id,
            Task.task_type == "project"
        )
        result = await db.execute(query)
        project = result.scalars().first()

        if not project:
            raise HTTPException(status_code=404, detail=f"Project {project_id} not found")

        # Get project updates
        query = select(TaskUpdate).where(
            TaskUpdate.task_id == project_id
        )
        result = await db.execute(query)
        project_updates = result.scalars().all()

        # Get all tasks for this project
        query = select(Task).where(
            Task.project_id == project_id
        )
        result = await db.execute(query)
        tasks = result.scalars().all()

        # Get updates for all tasks
        all_updates = project_updates
        for task in tasks:
            query = select(TaskUpdate).where(
                TaskUpdate.task_id == task.id
            )
            result = await db.execute(query)
            task_updates = result.scalars().all()
            all_updates.extend(task_updates)

        # Sort updates by timestamp
        all_updates.sort(key=lambda x: x.timestamp)

        return [
            TaskUpdateResponse(
                agent_id=update.agent_id,
                content=update.content,
                timestamp=update.timestamp
            )
            for update in all_updates
        ]
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting project updates: {e}")
        raise HTTPException(status_code=500, detail=f"Error getting project updates: {str(e)}")
