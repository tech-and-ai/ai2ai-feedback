"""
Workspace API models.
"""
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum


class FileType(str, Enum):
    """
    File type enum.
    """
    FILE = "file"
    DIRECTORY = "directory"


class FileInfo(BaseModel):
    """
    File information model.
    """
    name: str
    type: FileType
    size: Optional[int] = None
    last_modified: Optional[datetime] = None


class WorkspaceCreate(BaseModel):
    """
    Workspace creation model.
    """
    agent_id: str
    task_id: str


class WorkspaceResponse(BaseModel):
    """
    Workspace response model.
    """
    id: str
    agent_id: str
    task_id: str
    workspace_path: str
    venv_path: Optional[str] = None
    created_at: datetime
    last_accessed: datetime

    class Config:
        orm_mode = True


class FileListResponse(BaseModel):
    """
    File list response model.
    """
    workspace_id: str
    path: str
    files: List[FileInfo]


class FileUploadResponse(BaseModel):
    """
    File upload response model.
    """
    name: str
    path: str
    size: int
    last_modified: datetime


class CommandExecutionRequest(BaseModel):
    """
    Command execution request model.
    """
    command: str
    timeout: Optional[int] = 60


class CommandExecutionResponse(BaseModel):
    """
    Command execution response model.
    """
    stdout: str
    stderr: str
    exit_code: int
    execution_time: float
