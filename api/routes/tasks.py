"""
Task Routes

This module defines the API routes for tasks.
"""

import logging
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from pydantic import BaseModel

from models.task import Task, TaskStatus, TaskPriority

router = APIRouter()
logger = logging.getLogger(__name__)

class TaskCreate(BaseModel):
    """Task creation model."""
    title: str
    description: str
    priority: TaskPriority = TaskPriority.MEDIUM
    assigned_agent_id: Optional[str] = None
    parent_task_id: Optional[str] = None
    metadata: dict = {}

class TaskUpdate(BaseModel):
    """Task update model."""
    title: Optional[str] = None
    description: Optional[str] = None
    status: Optional[TaskStatus] = None
    priority: Optional[TaskPriority] = None
    assigned_agent_id: Optional[str] = None
    metadata: Optional[dict] = None

@router.post("/", response_model=Task, status_code=201)
async def create_task(task_create: TaskCreate, request: Request):
    """
    Create a new task.
    
    Args:
        task_create: Task creation data
        request: Request object
        
    Returns:
        Created task
    """
    task_manager = request.app.state.task_manager
    
    task = await task_manager.create_task(
        title=task_create.title,
        description=task_create.description,
        priority=task_create.priority,
        assigned_agent_id=task_create.assigned_agent_id,
        parent_task_id=task_create.parent_task_id,
        metadata=task_create.metadata
    )
    
    return task

@router.get("/{task_id}", response_model=Task)
async def get_task(task_id: str, request: Request):
    """
    Get a task by ID.
    
    Args:
        task_id: Task ID
        request: Request object
        
    Returns:
        Task if found
    """
    task_manager = request.app.state.task_manager
    
    task = await task_manager.get_task(task_id)
    
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    return task

@router.put("/{task_id}", response_model=Task)
async def update_task(task_id: str, task_update: TaskUpdate, request: Request):
    """
    Update a task.
    
    Args:
        task_id: Task ID
        task_update: Task update data
        request: Request object
        
    Returns:
        Updated task
    """
    task_manager = request.app.state.task_manager
    
    # Filter out None values
    update_data = {k: v for k, v in task_update.dict().items() if v is not None}
    
    task = await task_manager.update_task(task_id, **update_data)
    
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    return task

@router.delete("/{task_id}", status_code=204)
async def delete_task(task_id: str, request: Request):
    """
    Delete a task.
    
    Args:
        task_id: Task ID
        request: Request object
    """
    task_manager = request.app.state.task_manager
    
    result = await task_manager.delete_task(task_id)
    
    if not result:
        raise HTTPException(status_code=404, detail="Task not found")

@router.get("/", response_model=List[Task])
async def list_tasks(
    request: Request,
    status: Optional[TaskStatus] = None,
    priority: Optional[TaskPriority] = None,
    assigned_agent_id: Optional[str] = None,
    parent_task_id: Optional[str] = None,
    limit: int = Query(100, ge=1, le=100),
    offset: int = Query(0, ge=0)
):
    """
    List tasks with optional filtering.
    
    Args:
        request: Request object
        status: Filter by status
        priority: Filter by priority
        assigned_agent_id: Filter by assigned agent ID
        parent_task_id: Filter by parent task ID
        limit: Maximum number of tasks to return
        offset: Offset for pagination
        
    Returns:
        List of tasks
    """
    task_manager = request.app.state.task_manager
    
    tasks = await task_manager.list_tasks(
        status=status,
        priority=priority,
        assigned_agent_id=assigned_agent_id,
        parent_task_id=parent_task_id,
        limit=limit,
        offset=offset
    )
    
    return tasks

@router.post("/{task_id}/assign/{agent_id}", response_model=Task)
async def assign_task(task_id: str, agent_id: str, request: Request):
    """
    Assign a task to an agent.
    
    Args:
        task_id: Task ID
        agent_id: Agent ID
        request: Request object
        
    Returns:
        Updated task
    """
    task_manager = request.app.state.task_manager
    
    task = await task_manager.assign_task(task_id, agent_id)
    
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    return task
