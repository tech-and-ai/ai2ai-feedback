"""
Task API routes.
"""
from fastapi import APIRouter, Depends, HTTPException, Query, Response
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
import os
import shutil
from datetime import datetime

from app.db.base import get_db
from app.api.models import (
    TaskCreate, TaskUpdate, TaskStatusUpdate, TaskUpdateCreate,
    TaskResponse, TaskDetailResponse, TaskListResponse, TaskUpdateResponse
)
from app.services.task_service import TaskService

router = APIRouter()

@router.post("", response_model=TaskResponse, status_code=201)
async def create_task(
    task_data: TaskCreate,
    db: AsyncSession = Depends(get_db)
):
    """
    Create a new task.
    """
    task_service = TaskService(db)
    task = await task_service.create_task(task_data)
    return task

@router.get("", response_model=TaskListResponse)
async def list_tasks(
    status: Optional[str] = None,
    agent_id: Optional[str] = None,
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db)
):
    """
    List tasks with optional filtering.
    """
    task_service = TaskService(db)
    tasks, total = await task_service.list_tasks(status, agent_id, limit, offset)
    return {
        "total": total,
        "limit": limit,
        "offset": offset,
        "tasks": tasks
    }

@router.get("/{task_id}", response_model=TaskDetailResponse)
async def get_task(
    task_id: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Get detailed information about a specific task.
    """
    task_service = TaskService(db)
    task = await task_service.get_task_with_updates(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return task

@router.put("/{task_id}", response_model=TaskResponse)
async def update_task(
    task_id: str,
    task_data: TaskUpdate,
    db: AsyncSession = Depends(get_db)
):
    """
    Update a task.
    """
    task_service = TaskService(db)
    task = await task_service.update_task(task_id, task_data)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return task

@router.put("/{task_id}/status", response_model=TaskResponse)
async def update_task_status(
    task_id: str,
    status_data: TaskStatusUpdate,
    db: AsyncSession = Depends(get_db)
):
    """
    Update the status of a task.
    """
    task_service = TaskService(db)
    task = await task_service.update_task_status(
        task_id,
        status_data.status,
        status_data.stage_progress,
        status_data.update_message
    )
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return task

@router.get("/{task_id}/updates", response_model=List[TaskUpdateResponse])
async def get_task_updates(
    task_id: str,
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db)
):
    """
    Get updates for a specific task.
    """
    task_service = TaskService(db)
    updates = await task_service.get_task_updates(task_id, limit, offset)
    if updates is None:
        raise HTTPException(status_code=404, detail="Task not found")
    return updates

@router.post("/{task_id}/updates", response_model=TaskUpdateResponse)
async def create_task_update(
    task_id: str,
    update_data: TaskUpdateCreate,
    db: AsyncSession = Depends(get_db)
):
    """
    Create a new update for a task.
    """
    task_service = TaskService(db)
    update = await task_service.create_task_update(
        task_id,
        update_data.update_type,
        update_data.content
    )
    if not update:
        raise HTTPException(status_code=404, detail="Task not found")
    return update

@router.get("/{task_id}/download")
async def download_task_output(
    task_id: str,
    format: str = "zip",
    db: AsyncSession = Depends(get_db)
):
    """
    Download task output in the specified format.
    """
    task_service = TaskService(db)
    task = await task_service.get_task(task_id)

    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    if not task.result_path or not os.path.exists(task.result_path):
        raise HTTPException(status_code=404, detail="Task output not found")

    # Check if the task is complete
    if task.status != "complete":
        raise HTTPException(status_code=400, detail="Task is not complete yet")

    # Create a temporary zip file if needed
    if format == "zip" and os.path.isdir(task.result_path):
        # Create a temporary zip file
        zip_path = f"{task.result_path}.zip"

        # Create the zip file if it doesn't exist
        if not os.path.exists(zip_path):
            shutil.make_archive(task.result_path, 'zip', task.result_path)

        return FileResponse(
            zip_path,
            media_type="application/zip",
            filename=f"task_{task_id}_output.zip"
        )

    # If it's a single file, return it directly
    if os.path.isfile(task.result_path):
        filename = os.path.basename(task.result_path)
        return FileResponse(
            task.result_path,
            filename=filename
        )

    # If it's a directory but format is not zip, return an error
    raise HTTPException(status_code=400, detail="Invalid format for task output")
