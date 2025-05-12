"""
Coding Agent for AI-to-AI Feedback API

This module implements a specialized coding agent that can:
1. Create and modify code files
2. Run tests
3. Debug code
4. Implement features
"""

import os
import json
import logging
import asyncio
import re
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple, Set

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import or_, and_, func, desc

from .database import Task, TaskContext, TaskUpdate, async_session, get_db
from .providers.factory import get_model_provider
from .tools import FileOperations, ShellCommands
from .task_management import ContextScaffold

# Configure logging
logger = logging.getLogger("coding-agent")

class CodingAgent:
    """
    Specialized agent for coding tasks

    This agent can create and modify code files, run tests, and debug code.
    """

    def __init__(self, agent_id: str, name: str, role: str, skills: List[str], model: str):
        """
        Initialize a coding agent

        Args:
            agent_id: Agent ID
            name: Agent name
            role: Agent role
            skills: Agent skills
            model: AI model to use
        """
        self.agent_id = agent_id
        self.name = name
        self.role = role
        self.skills = set(skills)
        self.model = model
        self.status = "idle"  # Add status attribute
        self.provider = get_model_provider("openrouter", self.model)

        # Create workspace
        self.workspace = FileOperations.get_agent_workspace(agent_id)

    async def start(self):
        """Start the agent"""
        self.running = True
        self.status = "running"
        logger.info(f"Agent {self.name} ({self.agent_id}) started")

        # Start the task processing loop in the background
        asyncio.create_task(self._task_loop())
        return True

    async def _task_loop(self):
        """Task processing loop that runs in the background."""
        while self.running:
            if self.status == "running" or self.status == "idle":
                try:
                    # Look for a task to work on
                    db_gen = get_db()
                    db = await anext(db_gen)

                    # Find pending tasks that match agent skills and are assigned to this agent
                    query = select(Task).where(
                        Task.status == "in_progress",
                        Task.assigned_to == self.agent_id
                    )

                    result = await db.execute(query)
                    task = result.scalars().first()

                    if task:
                        self.status = "working"
                        logger.info(f"Agent {self.name} ({self.agent_id}) working on task {task.id}")

                        # Process the task
                        await self.process_coding_task(db, task.id, task.description)

                        # Reset status after processing
                        self.status = "running"
                    else:
                        # No tasks assigned, wait before checking again
                        await asyncio.sleep(5)
                except Exception as e:
                    logger.error(f"Error in task loop: {e}")
                    await asyncio.sleep(5)
            else:
                # Already working on a task, wait for it to complete
                await asyncio.sleep(5)

    async def setup_workspace(self):
        """Set up the agent's workspace with necessary files and directories"""
        # Create basic directory structure
        os.makedirs(os.path.join(self.workspace, "src"), exist_ok=True)
        os.makedirs(os.path.join(self.workspace, "tests"), exist_ok=True)
        os.makedirs(os.path.join(self.workspace, "docs"), exist_ok=True)

        # Create a README file
        readme_content = f"""# {self.name} Workspace

This workspace is used by the {self.name} agent to work on coding tasks.

## Agent Information
- Name: {self.name}
- Role: {self.role}
- Skills: {', '.join(self.skills)}

## Directory Structure
- src/: Source code
- tests/: Test files
- docs/: Documentation
"""
        FileOperations.write_file(self.agent_id, "README.md", readme_content)

        # Create a .gitignore file
        gitignore_content = """# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
env/
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
*.egg-info/
.installed.cfg
*.egg

# Virtual Environment
venv/
ENV/

# IDE files
.idea/
.vscode/
*.swp
*.swo
"""
        FileOperations.write_file(self.agent_id, ".gitignore", gitignore_content)

        self.status = "ready"
        return True

    async def process_coding_task(self, db: AsyncSession, task_id: str, task_description: str) -> bool:
        """
        Process a coding task

        Args:
            db: Database session
            task_id: Task ID
            task_description: Task description

        Returns:
            bool: Success
        """
        try:
            # Set up workspace if needed
            await self.setup_workspace()

            # Log start of processing
            await ContextScaffold.add_task_update(
                db,
                task_id,
                self.agent_id,
                f"Started processing coding task: {task_description[:100]}..."
            )

            # Analyze the task
            analysis = await self._analyze_task(task_description)

            # Add analysis to context
            await ContextScaffold.add_context_entry(
                db,
                task_id,
                "task_analysis",
                analysis
            )

            # Log analysis
            await ContextScaffold.add_task_update(
                db,
                task_id,
                self.agent_id,
                "Completed task analysis"
            )

            # Implement the solution
            implementation_result = await self._implement_solution(task_description, analysis)

            # Add implementation result to context
            await ContextScaffold.add_context_entry(
                db,
                task_id,
                "implementation_result",
                json.dumps(implementation_result)
            )

            # Log implementation
            await ContextScaffold.add_task_update(
                db,
                task_id,
                self.agent_id,
                "Completed implementation"
            )

            # Run tests
            test_result = await self._run_tests()

            # Add test result to context
            await ContextScaffold.add_context_entry(
                db,
                task_id,
                "test_result",
                json.dumps(test_result)
            )

            # Log test results
            await ContextScaffold.add_task_update(
                db,
                task_id,
                self.agent_id,
                f"Completed testing: {'Tests passed' if test_result['success'] else 'Tests failed'}"
            )

            # Complete the task
            result = {
                "analysis": analysis,
                "implementation": implementation_result,
                "tests": test_result,
                "workspace_path": self.workspace
            }

            return True
        except Exception as e:
            logger.error(f"Error processing coding task: {e}")
            await ContextScaffold.add_task_update(
                db,
                task_id,
                self.agent_id,
                f"Error processing coding task: {str(e)}"
            )
            return False

    async def _analyze_task(self, task_description: str) -> str:
        """Analyze a coding task"""
        prompt = f"""
You are {self.name}, a coding agent with the role: {self.role}
Your skills include: {', '.join(self.skills)}

TASK DESCRIPTION:
{task_description}

Please analyze this coding task and provide:
1. A clear understanding of the requirements
2. The key components or modules needed
3. Any potential challenges or edge cases
4. A high-level approach to implementing the solution
5. Any libraries or frameworks that would be helpful

FORMAT YOUR RESPONSE AS FOLLOWS:
REQUIREMENTS: [Clear understanding of the requirements]
COMPONENTS: [Key components or modules needed]
CHALLENGES: [Potential challenges or edge cases]
APPROACH: [High-level approach to implementing the solution]
LIBRARIES: [Libraries or frameworks that would be helpful]
"""

        response = await self.provider.generate_completion(
            system_prompt=f"You are {self.name}, a coding agent specialized in software development.",
            user_prompt=prompt
        )

        return response

    async def _implement_solution(self, task_description: str, analysis: str) -> Dict[str, Any]:
        """Implement a solution for a coding task"""
        prompt = f"""
You are {self.name}, a coding agent with the role: {self.role}
Your skills include: {', '.join(self.skills)}

TASK DESCRIPTION:
{task_description}

ANALYSIS:
{analysis}

Please implement a solution for this task. You should:
1. Create the necessary files and directories
2. Write the code for each file
3. Include appropriate comments and documentation
4. Write tests for your implementation

For each file you want to create, use the following format:

```file-write
{{
  "path": "path/to/file.py",
  "content": "# File content goes here\\n..."
}}
```

You can also run shell commands if needed:

```shell
{{
  "command": "mkdir -p src/utils"
}}
```

FORMAT YOUR RESPONSE AS FOLLOWS:
IMPLEMENTATION_PLAN: [Brief description of your implementation plan]
FILES: [List of files you will create]
[File creation commands for each file]
TESTS: [Description of tests]
[Test file creation commands]
"""

        response = await self.provider.generate_completion(
            system_prompt=f"You are {self.name}, a coding agent specialized in software development.",
            user_prompt=prompt
        )

        # Extract and execute file-write commands
        file_write_pattern = r"```file-write\s*\n(.*?)\n\s*```"
        import re

        files_created = []
        for match in re.finditer(file_write_pattern, response, re.DOTALL):
            try:
                json_str = match.group(1)
                logger.info(f"Attempting to parse JSON: {json_str[:100]}...")

                # Try to extract path and content directly using regex if JSON parsing fails
                path_match = re.search(r'"path"\s*:\s*"([^"]+)"', json_str)
                content_match = re.search(r'"content"\s*:\s*"""(.*?)"""', json_str, re.DOTALL)

                if path_match and content_match:
                    path = path_match.group(1)
                    content = content_match.group(1)
                    logger.info(f"Extracted path and content using regex: {path}")
                    success, result = FileOperations.write_file(self.agent_id, path, content)
                    if success:
                        files_created.append(path)
                        logger.info(f"Successfully created file: {path}")
                    else:
                        logger.error(f"Failed to create file: {path} - {result}")
                else:
                    # Try standard JSON parsing as fallback
                    try:
                        data = json.loads(json_str)
                        if "path" in data and "content" in data:
                            logger.info(f"Creating file: {data['path']}")
                            success, result = FileOperations.write_file(self.agent_id, data["path"], data["content"])
                            if success:
                                files_created.append(data["path"])
                                logger.info(f"Successfully created file: {data['path']}")
                            else:
                                logger.error(f"Failed to create file: {data['path']} - {result}")
                        else:
                            logger.error(f"Missing 'path' or 'content' in file-write data: {data}")
                    except json.JSONDecodeError as e:
                        logger.error(f"Failed to parse JSON from file-write block: {e}")
            except Exception as e:
                logger.error(f"Error processing file-write block: {e}")

        # Extract and execute shell commands
        shell_pattern = r"```shell\s*\n(.*?)\n\s*```"
        commands_executed = []
        for match in re.finditer(shell_pattern, response, re.DOTALL):
            try:
                json_str = match.group(1)
                logger.info(f"Attempting to parse shell command JSON: {json_str[:100]}...")
                data = json.loads(json_str)
                if "command" in data:
                    logger.info(f"Executing command: {data['command']}")
                    success, stdout, stderr = ShellCommands.execute_command(self.agent_id, data["command"])
                    commands_executed.append({
                        "command": data["command"],
                        "success": success,
                        "stdout": stdout,
                        "stderr": stderr
                    })
                    logger.info(f"Command execution result: success={success}, stdout={stdout[:100]}...")
                else:
                    logger.error(f"Missing 'command' in shell data: {data}")
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse JSON from shell block: {e}")

        return {
            "response": response,
            "files_created": files_created,
            "commands_executed": commands_executed
        }

    async def _run_tests(self) -> Dict[str, Any]:
        """Run tests for the implementation"""
        # Check if pytest is available
        success, stdout, stderr = ShellCommands.execute_command(self.agent_id, "which pytest")

        if not success:
            # Try to install pytest
            ShellCommands.execute_command(self.agent_id, "pip install pytest")

        # Run tests
        success, stdout, stderr = ShellCommands.execute_command(self.agent_id, "cd tests && python -m pytest -v")

        return {
            "success": success,
            "stdout": stdout,
            "stderr": stderr
        }
