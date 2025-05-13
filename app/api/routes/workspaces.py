"""
Workspace API routes.
"""
from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File, Form
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
import os

from app.db.base import get_db
from app.api.models import (
    WorkspaceCreate, WorkspaceResponse, FileListResponse,
    FileUploadResponse, CommandExecutionRequest, CommandExecutionResponse
)
from app.services.workspace_service import WorkspaceService

router = APIRouter()

@router.post("", response_model=WorkspaceResponse, status_code=201)
async def create_workspace(
    workspace_data: WorkspaceCreate,
    db: AsyncSession = Depends(get_db)
):
    """
    Create a new workspace.
    """
    workspace_service = WorkspaceService(db)
    workspace = await workspace_service.create_workspace(
        workspace_data.agent_id,
        workspace_data.task_id
    )
    return workspace

@router.get("/{workspace_id}", response_model=WorkspaceResponse)
async def get_workspace(
    workspace_id: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Get information about a specific workspace.
    """
    workspace_service = WorkspaceService(db)
    workspace = await workspace_service.get_workspace(workspace_id)
    if not workspace:
        raise HTTPException(status_code=404, detail="Workspace not found")
    return workspace

@router.get("/{workspace_id}/files", response_model=FileListResponse)
async def list_files(
    workspace_id: str,
    path: Optional[str] = "",
    db: AsyncSession = Depends(get_db)
):
    """
    List files in a workspace.
    """
    workspace_service = WorkspaceService(db)
    files = await workspace_service.list_files(workspace_id, path)
    if files is None:
        raise HTTPException(status_code=404, detail="Workspace not found")
    return files

@router.get("/{workspace_id}/files/{file_path:path}")
async def get_file_content(
    workspace_id: str,
    file_path: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Get the content of a file in a workspace.
    """
    workspace_service = WorkspaceService(db)
    file_content, content_type = await workspace_service.get_file_content(workspace_id, file_path)
    if file_content is None:
        raise HTTPException(status_code=404, detail="File not found")
    
    return StreamingResponse(
        iter([file_content]),
        media_type=content_type
    )

@router.post("/{workspace_id}/files", response_model=FileUploadResponse)
async def upload_file(
    workspace_id: str,
    file: UploadFile = File(...),
    path: str = Form(""),
    db: AsyncSession = Depends(get_db)
):
    """
    Upload a file to a workspace.
    """
    workspace_service = WorkspaceService(db)
    file_info = await workspace_service.upload_file(workspace_id, file, path)
    if file_info is None:
        raise HTTPException(status_code=404, detail="Workspace not found")
    return file_info

@router.post("/{workspace_id}/execute", response_model=CommandExecutionResponse)
async def execute_command(
    workspace_id: str,
    command_data: CommandExecutionRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Execute a command in a workspace.
    """
    workspace_service = WorkspaceService(db)
    result = await workspace_service.execute_command(
        workspace_id,
        command_data.command,
        command_data.timeout
    )
    if result is None:
        raise HTTPException(status_code=404, detail="Workspace not found")
    return result

@router.post("/{workspace_id}/python", response_model=CommandExecutionResponse)
async def execute_python(
    workspace_id: str,
    code: str,
    timeout: Optional[int] = 30,
    db: AsyncSession = Depends(get_db)
):
    """
    Execute Python code in a workspace.
    """
    workspace_service = WorkspaceService(db)
    result = await workspace_service.execute_python(workspace_id, code, timeout)
    if result is None:
        raise HTTPException(status_code=404, detail="Workspace not found")
    return result
