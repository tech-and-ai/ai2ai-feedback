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
    def get_agent_workspace(agent_id: str, agent_name: str = None, agent_role: str = None) -> str:
        """
        Get the workspace directory for an agent

        Args:
            agent_id: Agent ID
            agent_name: Agent name (optional)
            agent_role: Agent role (optional)

        Returns:
            str: Path to agent workspace
        """
        # Base workspaces directory
        workspaces_base = os.path.join(os.getcwd(), "workspaces")

        # If agent_name and agent_role are provided, use a more user-friendly structure
        if agent_name and agent_role:
            # Sanitize name and role for use in file paths
            safe_name = "".join(c if c.isalnum() else "_" for c in agent_name).lower()
            safe_role = "".join(c if c.isalnum() else "_" for c in agent_role).lower()

            # Create a directory structure: workspaces/role/name_id
            workspace_dir = os.path.join(workspaces_base, safe_role, f"{safe_name}_{agent_id[:8]}")

            # Create a symlink from the UUID to the named directory for backward compatibility
            uuid_dir = os.path.join(workspaces_base, agent_id)

            # Create the named directory
            os.makedirs(workspace_dir, exist_ok=True)

            # Create a symlink if it doesn't exist
            if not os.path.exists(uuid_dir):
                # Ensure the parent directory exists
                os.makedirs(os.path.dirname(uuid_dir), exist_ok=True)

                try:
                    # Create relative symlink
                    rel_path = os.path.relpath(workspace_dir, os.path.dirname(uuid_dir))
                    os.symlink(rel_path, uuid_dir, target_is_directory=True)
                except (OSError, FileExistsError):
                    # If symlink creation fails, just use the UUID directory
                    pass
        else:
            # Fallback to the old UUID-based structure
            workspace_dir = os.path.join(workspaces_base, agent_id)
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

    @staticmethod
    def list_workspaces() -> List[Dict[str, Any]]:
        """
        List all agent workspaces in a user-friendly format

        Returns:
            List[Dict]: List of workspace info
        """
        try:
            workspaces_base = os.path.join(os.getcwd(), "workspaces")
            if not os.path.exists(workspaces_base):
                return []

            workspaces = []

            # First, scan for role-based directories
            for role in os.listdir(workspaces_base):
                role_path = os.path.join(workspaces_base, role)

                # Skip files and UUID directories
                if not os.path.isdir(role_path) or len(role) == 36:
                    continue

                # Look for agent directories within each role
                for agent_dir in os.listdir(role_path):
                    agent_path = os.path.join(role_path, agent_dir)
                    if os.path.isdir(agent_path):
                        # Extract agent name and ID from directory name
                        parts = agent_dir.split('_')
                        if len(parts) > 1:
                            agent_name = '_'.join(parts[:-1])
                            agent_id_prefix = parts[-1]

                            workspaces.append({
                                "path": agent_path,
                                "role": role,
                                "name": agent_name,
                                "id_prefix": agent_id_prefix,
                                "type": "named"
                            })

            # Then, scan for UUID-based directories (for backward compatibility)
            for item in os.listdir(workspaces_base):
                item_path = os.path.join(workspaces_base, item)

                # Only process directories that look like UUIDs
                if os.path.isdir(item_path) and len(item) == 36 and '-' in item:
                    # Check if it's a symlink
                    if os.path.islink(item_path):
                        # This is a symlink to a named workspace, skip it
                        continue
                    else:
                        # This is a legacy UUID workspace
                        workspaces.append({
                            "path": item_path,
                            "id": item,
                            "type": "uuid"
                        })

            return workspaces
        except Exception as e:
            logger.error(f"Error listing workspaces: {e}")
            return []
