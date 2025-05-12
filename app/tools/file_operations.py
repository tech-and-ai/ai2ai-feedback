"""
File operation tools for autonomous agents

This module provides tools for agents to interact with the file system,
including reading, writing, and executing code.
"""

import os
import subprocess
import logging
from typing import Dict, List, Optional, Any, Tuple

# Configure logging
logger = logging.getLogger("agent-tools")

class FileOperations:
    """Tools for file operations"""
    
    @staticmethod
    def get_agent_workspace(agent_id: str) -> str:
        """
        Get the workspace directory for an agent
        
        Args:
            agent_id: Agent ID
            
        Returns:
            str: Path to agent workspace
        """
        # Create a workspace directory for the agent if it doesn't exist
        workspace_dir = os.path.join(os.getcwd(), "workspaces", agent_id)
        os.makedirs(workspace_dir, exist_ok=True)
        return workspace_dir
    
    @staticmethod
    def read_file(agent_id: str, file_path: str) -> Tuple[bool, str]:
        """
        Read a file
        
        Args:
            agent_id: Agent ID
            file_path: Path to file (relative to agent workspace)
            
        Returns:
            Tuple[bool, str]: (Success, Content or error message)
        """
        try:
            workspace = FileOperations.get_agent_workspace(agent_id)
            full_path = os.path.join(workspace, file_path)
            
            # Security check - ensure the path is within the workspace
            if not os.path.abspath(full_path).startswith(os.path.abspath(workspace)):
                return False, "Security error: Attempted to access file outside of workspace"
            
            if not os.path.exists(full_path):
                return False, f"File not found: {file_path}"
                
            with open(full_path, 'r') as f:
                content = f.read()
            
            return True, content
        except Exception as e:
            logger.error(f"Error reading file: {e}")
            return False, f"Error reading file: {str(e)}"
    
    @staticmethod
    def write_file(agent_id: str, file_path: str, content: str) -> Tuple[bool, str]:
        """
        Write to a file
        
        Args:
            agent_id: Agent ID
            file_path: Path to file (relative to agent workspace)
            content: File content
            
        Returns:
            Tuple[bool, str]: (Success, Message)
        """
        try:
            workspace = FileOperations.get_agent_workspace(agent_id)
            full_path = os.path.join(workspace, file_path)
            
            # Security check - ensure the path is within the workspace
            if not os.path.abspath(full_path).startswith(os.path.abspath(workspace)):
                return False, "Security error: Attempted to write file outside of workspace"
            
            # Create directories if they don't exist
            os.makedirs(os.path.dirname(os.path.abspath(full_path)), exist_ok=True)
                
            with open(full_path, 'w') as f:
                f.write(content)
            
            return True, f"File written successfully: {file_path}"
        except Exception as e:
            logger.error(f"Error writing file: {e}")
            return False, f"Error writing file: {str(e)}"
    
    @staticmethod
    def list_directory(agent_id: str, directory_path: str = "") -> Tuple[bool, List[Dict[str, Any]]]:
        """
        List files in a directory
        
        Args:
            agent_id: Agent ID
            directory_path: Path to directory (relative to agent workspace)
            
        Returns:
            Tuple[bool, List[Dict]]: (Success, List of file info)
        """
        try:
            workspace = FileOperations.get_agent_workspace(agent_id)
            full_path = os.path.join(workspace, directory_path)
            
            # Security check - ensure the path is within the workspace
            if not os.path.abspath(full_path).startswith(os.path.abspath(workspace)):
                return False, [{"error": "Security error: Attempted to access directory outside of workspace"}]
            
            if not os.path.exists(full_path):
                return False, [{"error": f"Directory not found: {directory_path}"}]
                
            files = []
            for item in os.listdir(full_path):
                item_path = os.path.join(full_path, item)
                files.append({
                    "name": item,
                    "type": "directory" if os.path.isdir(item_path) else "file",
                    "size": os.path.getsize(item_path) if os.path.isfile(item_path) else None
                })
            
            return True, files
        except Exception as e:
            logger.error(f"Error listing directory: {e}")
            return False, [{"error": f"Error listing directory: {str(e)}"}]
