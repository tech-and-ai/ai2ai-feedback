"""
Workspace service module.
"""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from typing import List, Optional, Dict, Any, Tuple
from datetime import datetime
import uuid
import os
import subprocess
import time
import mimetypes
import shutil
from fastapi import UploadFile

from app.db.models import AgentWorkspace, Agent, Task
from app.core.config import settings
from app.core.security import is_command_allowed, sanitize_command

class WorkspaceService:
    """
    Service for workspace management.
    """
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_workspace(self, agent_id: str, task_id: str) -> Optional[AgentWorkspace]:
        """
        Create a new workspace for an agent-task pair.
        """
        # Check if agent and task exist
        agent_query = select(Agent).where(Agent.id == agent_id)
        task_query = select(Task).where(Task.id == task_id)
        
        agent_result = await self.db.execute(agent_query)
        task_result = await self.db.execute(task_query)
        
        agent = agent_result.scalars().first()
        task = task_result.scalars().first()
        
        if not agent or not task:
            return None
        
        # Check if workspace already exists
        existing_query = select(AgentWorkspace).where(
            AgentWorkspace.agent_id == agent_id,
            AgentWorkspace.task_id == task_id
        )
        
        existing_result = await self.db.execute(existing_query)
        existing = existing_result.scalars().first()
        
        if existing:
            return existing
        
        # Create workspace directories
        task_dir = os.path.join(agent.workspace_path, "tasks", task_id)
        os.makedirs(os.path.join(task_dir, "src"), exist_ok=True)
        os.makedirs(os.path.join(task_dir, "output"), exist_ok=True)
        os.makedirs(os.path.join(task_dir, "research"), exist_ok=True)
        
        # Create virtual environment
        venv_path = os.path.join(task_dir, "venv")
        try:
            subprocess.run(["python", "-m", "venv", venv_path], check=True)
            
            # Install basic packages
            subprocess.run([
                os.path.join(venv_path, "bin", "pip"),
                "install",
                "--upgrade",
                "pip"
            ], check=True)
            
            subprocess.run([
                os.path.join(venv_path, "bin", "pip"),
                "install",
                "requests",
                "beautifulsoup4",
                "pandas",
                "matplotlib"
            ], check=True)
        except subprocess.CalledProcessError as e:
            # Log error but continue
            print(f"Error creating virtual environment: {e}")
        
        # Create README.md
        with open(os.path.join(task_dir, "README.md"), "w") as f:
            f.write(f"# {task.title}\n\n")
            f.write(f"## Description\n\n{task.description}\n\n")
            f.write(f"## Status\n\nTask initialized on {datetime.utcnow().isoformat()}\n\n")
            f.write("## Progress\n\n- [ ] Design\n- [ ] Build\n- [ ] Test\n- [ ] Review\n- [ ] Complete\n")
        
        # Create workspace record
        workspace = AgentWorkspace(
            id=str(uuid.uuid4()),
            agent_id=agent_id,
            task_id=task_id,
            workspace_path=task_dir,
            venv_path=venv_path
        )
        
        self.db.add(workspace)
        await self.db.commit()
        await self.db.refresh(workspace)
        
        return workspace

    async def get_workspace(self, workspace_id: str) -> Optional[AgentWorkspace]:
        """
        Get a workspace by ID.
        """
        query = select(AgentWorkspace).where(AgentWorkspace.id == workspace_id)
        result = await self.db.execute(query)
        return result.scalars().first()

    async def get_workspace_by_agent_task(self, agent_id: str, task_id: str) -> Optional[AgentWorkspace]:
        """
        Get a workspace by agent ID and task ID.
        """
        query = select(AgentWorkspace).where(
            AgentWorkspace.agent_id == agent_id,
            AgentWorkspace.task_id == task_id
        )
        
        result = await self.db.execute(query)
        return result.scalars().first()

    async def list_files(self, workspace_id: str, path: str = "") -> Optional[Dict[str, Any]]:
        """
        List files in a workspace.
        """
        workspace = await self.get_workspace(workspace_id)
        if not workspace:
            return None
        
        # Construct full path
        full_path = os.path.join(workspace.workspace_path, path)
        
        # Check if path exists
        if not os.path.exists(full_path):
            return None
        
        # List files
        files = []
        for item in os.listdir(full_path):
            item_path = os.path.join(full_path, item)
            
            if os.path.isdir(item_path):
                files.append({
                    "name": item,
                    "type": "directory",
                    "last_modified": datetime.fromtimestamp(os.path.getmtime(item_path))
                })
            else:
                files.append({
                    "name": item,
                    "type": "file",
                    "size": os.path.getsize(item_path),
                    "last_modified": datetime.fromtimestamp(os.path.getmtime(item_path))
                })
        
        return {
            "workspace_id": workspace_id,
            "path": path,
            "files": files
        }

    async def get_file_content(self, workspace_id: str, file_path: str) -> Optional[Tuple[bytes, str]]:
        """
        Get the content of a file in a workspace.
        """
        workspace = await self.get_workspace(workspace_id)
        if not workspace:
            return None
        
        # Construct full path
        full_path = os.path.join(workspace.workspace_path, file_path)
        
        # Check if file exists
        if not os.path.exists(full_path) or not os.path.isfile(full_path):
            return None
        
        # Get file content
        with open(full_path, "rb") as f:
            content = f.read()
        
        # Determine content type
        content_type, _ = mimetypes.guess_type(full_path)
        if not content_type:
            content_type = "application/octet-stream"
        
        return content, content_type

    async def upload_file(self, workspace_id: str, file: UploadFile, path: str = "") -> Optional[Dict[str, Any]]:
        """
        Upload a file to a workspace.
        """
        workspace = await self.get_workspace(workspace_id)
        if not workspace:
            return None
        
        # Construct full path
        dir_path = os.path.join(workspace.workspace_path, path)
        
        # Create directory if it doesn't exist
        os.makedirs(dir_path, exist_ok=True)
        
        # Save file
        file_path = os.path.join(dir_path, file.filename)
        with open(file_path, "wb") as f:
            shutil.copyfileobj(file.file, f)
        
        # Get file info
        file_info = {
            "name": file.filename,
            "path": os.path.join(path, file.filename),
            "size": os.path.getsize(file_path),
            "last_modified": datetime.fromtimestamp(os.path.getmtime(file_path))
        }
        
        return file_info

    async def execute_command(
        self, 
        workspace_id: str, 
        command: str, 
        timeout: int = 60
    ) -> Optional[Dict[str, Any]]:
        """
        Execute a command in a workspace.
        """
        workspace = await self.get_workspace(workspace_id)
        if not workspace:
            return None
        
        # Check if command is allowed
        if not is_command_allowed(command):
            return {
                "stdout": "",
                "stderr": "Command not allowed",
                "exit_code": 1,
                "execution_time": 0
            }
        
        # Sanitize command
        sanitized_command = sanitize_command(command)
        
        # Set up execution environment
        env = os.environ.copy()
        env["WORKSPACE"] = workspace.workspace_path
        
        # Execute command
        start_time = time.time()
        try:
            process = subprocess.run(
                sanitized_command,
                shell=True,
                cwd=workspace.workspace_path,
                env=env,
                timeout=timeout,
                capture_output=True,
                text=True
            )
            
            execution_time = time.time() - start_time
            
            return {
                "stdout": process.stdout,
                "stderr": process.stderr,
                "exit_code": process.returncode,
                "execution_time": execution_time
            }
        except subprocess.TimeoutExpired:
            execution_time = time.time() - start_time
            
            return {
                "stdout": "",
                "stderr": f"Command execution timed out after {timeout} seconds",
                "exit_code": 124,  # Standard timeout exit code
                "execution_time": execution_time
            }

    async def execute_python(
        self, 
        workspace_id: str, 
        code: str, 
        timeout: int = 30
    ) -> Optional[Dict[str, Any]]:
        """
        Execute Python code in a workspace.
        """
        workspace = await self.get_workspace(workspace_id)
        if not workspace:
            return None
        
        # Create a temporary file for the code
        import tempfile
        with tempfile.NamedTemporaryFile(suffix='.py', dir=workspace.workspace_path, delete=False) as f:
            f.write(code.encode('utf-8'))
            script_path = f.name
        
        try:
            # Execute the code in the virtual environment
            venv_python = os.path.join(workspace.venv_path, "bin", "python")
            
            # Execute command
            start_time = time.time()
            try:
                process = subprocess.run(
                    [venv_python, script_path],
                    cwd=workspace.workspace_path,
                    timeout=timeout,
                    capture_output=True,
                    text=True
                )
                
                execution_time = time.time() - start_time
                
                return {
                    "stdout": process.stdout,
                    "stderr": process.stderr,
                    "exit_code": process.returncode,
                    "execution_time": execution_time
                }
            except subprocess.TimeoutExpired:
                execution_time = time.time() - start_time
                
                return {
                    "stdout": "",
                    "stderr": f"Python execution timed out after {timeout} seconds",
                    "exit_code": 124,  # Standard timeout exit code
                    "execution_time": execution_time
                }
        finally:
            # Clean up the temporary file
            os.unlink(script_path)
