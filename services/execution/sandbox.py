"""
Execution Sandbox

This module provides a sandbox for executing code safely.
"""

import logging
import os
import tempfile
import subprocess
import asyncio
import shutil
from typing import Dict, Optional, Any, Tuple

logger = logging.getLogger(__name__)

class ExecutionSandbox:
    """Execution sandbox class."""
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the execution sandbox.
        
        Args:
            config: Sandbox configuration
        """
        self.timeout = config.get('timeout', 30)
        self.max_memory = config.get('max_memory', '256m')
        self.base_dir = config.get('base_dir', 'sandbox')
        
        # Create base directory if it doesn't exist
        os.makedirs(self.base_dir, exist_ok=True)
        
        logger.info(f"Initialized execution sandbox with base directory: {self.base_dir}")
    
    async def execute_code(self, 
                          code: str, 
                          language: str, 
                          inputs: Optional[str] = None) -> Dict[str, Any]:
        """
        Execute code in a sandbox.
        
        Args:
            code: Code to execute
            language: Programming language
            inputs: Optional inputs to the code
            
        Returns:
            Execution results
        """
        # Create a temporary directory for the execution
        with tempfile.TemporaryDirectory(dir=self.base_dir) as temp_dir:
            # Write code to a file
            file_path = self._write_code_to_file(temp_dir, code, language)
            
            # Write inputs to a file if provided
            input_path = None
            if inputs:
                input_path = os.path.join(temp_dir, 'input.txt')
                with open(input_path, 'w') as f:
                    f.write(inputs)
            
            # Execute the code
            stdout, stderr, exit_code = await self._execute_file(file_path, language, input_path)
            
            return {
                'stdout': stdout,
                'stderr': stderr,
                'exit_code': exit_code
            }
    
    def _write_code_to_file(self, directory: str, code: str, language: str) -> str:
        """
        Write code to a file.
        
        Args:
            directory: Directory to write the file to
            code: Code to write
            language: Programming language
            
        Returns:
            File path
        """
        # Determine file extension
        extension = self._get_file_extension(language)
        
        # Create file path
        file_path = os.path.join(directory, f'code{extension}')
        
        # Write code to file
        with open(file_path, 'w') as f:
            f.write(code)
        
        return file_path
    
    async def _execute_file(self, 
                           file_path: str, 
                           language: str, 
                           input_path: Optional[str] = None) -> Tuple[str, str, int]:
        """
        Execute a file.
        
        Args:
            file_path: Path to the file to execute
            language: Programming language
            input_path: Path to the input file
            
        Returns:
            Tuple of (stdout, stderr, exit_code)
        """
        # Get command to execute the file
        command = self._get_execution_command(file_path, language)
        
        if not command:
            return '', f"Unsupported language: {language}", 1
        
        # Prepare input
        stdin = None
        if input_path:
            with open(input_path, 'r') as f:
                stdin = f.read()
        
        # Execute the command
        try:
            process = await asyncio.create_subprocess_shell(
                command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                stdin=asyncio.subprocess.PIPE if stdin else None,
                cwd=os.path.dirname(file_path)
            )
            
            # Set timeout
            try:
                stdout, stderr = await asyncio.wait_for(
                    process.communicate(input=stdin.encode() if stdin else None),
                    timeout=self.timeout
                )
                
                return stdout.decode(), stderr.decode(), process.returncode
            except asyncio.TimeoutError:
                # Kill the process if it times out
                process.kill()
                return '', f"Execution timed out after {self.timeout} seconds", 1
        except Exception as e:
            logger.error(f"Error executing file: {e}")
            return '', f"Error executing file: {e}", 1
    
    def _get_file_extension(self, language: str) -> str:
        """
        Get file extension for a language.
        
        Args:
            language: Programming language
            
        Returns:
            File extension
        """
        extensions = {
            'python': '.py',
            'javascript': '.js',
            'typescript': '.ts',
            'java': '.java',
            'c': '.c',
            'cpp': '.cpp',
            'csharp': '.cs',
            'go': '.go',
            'ruby': '.rb',
            'php': '.php',
            'rust': '.rs',
            'swift': '.swift',
            'kotlin': '.kt',
            'scala': '.scala',
            'bash': '.sh',
            'html': '.html',
            'css': '.css',
            'sql': '.sql'
        }
        
        return extensions.get(language.lower(), '.txt')
    
    def _get_execution_command(self, file_path: str, language: str) -> Optional[str]:
        """
        Get command to execute a file.
        
        Args:
            file_path: Path to the file to execute
            language: Programming language
            
        Returns:
            Execution command
        """
        commands = {
            'python': f"python {file_path}",
            'javascript': f"node {file_path}",
            'typescript': f"ts-node {file_path}",
            'java': f"javac {file_path} && java {os.path.splitext(os.path.basename(file_path))[0]}",
            'c': f"gcc {file_path} -o {os.path.splitext(file_path)[0]} && {os.path.splitext(file_path)[0]}",
            'cpp': f"g++ {file_path} -o {os.path.splitext(file_path)[0]} && {os.path.splitext(file_path)[0]}",
            'go': f"go run {file_path}",
            'ruby': f"ruby {file_path}",
            'php': f"php {file_path}",
            'rust': f"rustc {file_path} && {os.path.splitext(file_path)[0]}",
            'bash': f"bash {file_path}"
        }
        
        return commands.get(language.lower())
