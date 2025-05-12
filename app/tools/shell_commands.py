"""
Shell command execution tools for autonomous agents

This module provides tools for agents to execute shell commands
in a controlled environment.
"""

import os
import subprocess
import logging
import shlex
from typing import Dict, List, Optional, Any, Tuple

from .file_operations import FileOperations

# Configure logging
logger = logging.getLogger("agent-tools")

# List of allowed commands for security
ALLOWED_COMMANDS = [
    "ls", "mkdir", "touch", "cat", "echo", "grep", "find",
    "python", "python3", "pip", "pip3", "pytest", "pytest3",
    "npm", "node", "yarn", "git", "cp", "mv"
]

# List of disallowed command arguments for security
DISALLOWED_ARGS = [
    "--help", "-h", "sudo", "rm -rf", "rm -r", "rm", "rmdir",
    "/etc", "/var", "/usr", "/bin", "/sbin", "/dev", "/proc", "/sys",
    "../", "..", "~", "$HOME", "${HOME}", "$USER", "${USER}"
]

class ShellCommands:
    """Tools for executing shell commands"""
    
    @staticmethod
    def execute_command(agent_id: str, command: str) -> Tuple[bool, str, str]:
        """
        Execute a shell command in the agent's workspace
        
        Args:
            agent_id: Agent ID
            command: Shell command to execute
            
        Returns:
            Tuple[bool, str, str]: (Success, stdout, stderr)
        """
        try:
            # Security checks
            command_parts = shlex.split(command)
            base_command = command_parts[0]
            
            if base_command not in ALLOWED_COMMANDS:
                return False, "", f"Security error: Command '{base_command}' is not allowed"
            
            for arg in command_parts:
                for disallowed in DISALLOWED_ARGS:
                    if disallowed in arg:
                        return False, "", f"Security error: Argument '{arg}' contains disallowed pattern '{disallowed}'"
            
            # Get workspace directory
            workspace = FileOperations.get_agent_workspace(agent_id)
            
            # Execute command in workspace
            process = subprocess.Popen(
                command,
                shell=True,
                cwd=workspace,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            stdout, stderr = process.communicate(timeout=60)  # 60 second timeout
            success = process.returncode == 0
            
            return success, stdout, stderr
        except subprocess.TimeoutExpired:
            return False, "", "Command execution timed out after 60 seconds"
        except Exception as e:
            logger.error(f"Error executing command: {e}")
            return False, "", f"Error executing command: {str(e)}"
    
    @staticmethod
    def run_python_script(agent_id: str, script_path: str, args: List[str] = None) -> Tuple[bool, str, str]:
        """
        Run a Python script
        
        Args:
            agent_id: Agent ID
            script_path: Path to script (relative to agent workspace)
            args: Command line arguments
            
        Returns:
            Tuple[bool, str, str]: (Success, stdout, stderr)
        """
        try:
            workspace = FileOperations.get_agent_workspace(agent_id)
            full_path = os.path.join(workspace, script_path)
            
            # Security check - ensure the path is within the workspace
            if not os.path.abspath(full_path).startswith(os.path.abspath(workspace)):
                return False, "", "Security error: Attempted to access file outside of workspace"
            
            if not os.path.exists(full_path):
                return False, "", f"Script not found: {script_path}"
            
            # Build command
            command = ["python3", script_path]
            if args:
                command.extend(args)
            
            # Execute command
            process = subprocess.Popen(
                command,
                cwd=workspace,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            stdout, stderr = process.communicate(timeout=60)  # 60 second timeout
            success = process.returncode == 0
            
            return success, stdout, stderr
        except subprocess.TimeoutExpired:
            return False, "", "Script execution timed out after 60 seconds"
        except Exception as e:
            logger.error(f"Error running Python script: {e}")
            return False, "", f"Error running Python script: {str(e)}"
