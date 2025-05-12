"""
Agent task processing loop for AI-to-AI Feedback API

This module implements the agent task processing loop that regularly checks for tasks,
processes them, and updates the task status.
"""

import json
import logging
import asyncio
import re
import os
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from .database import async_session, Task
from .task_management import ContextScaffold, ContextRefresher, TaskManager
from .providers.factory import get_model_provider
from .tools import FileOperations, ShellCommands

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("agent-loop")

def extract_json_from_markdown(text: str, block_type: str) -> Optional[Dict[str, Any]]:
    """Extract JSON from a markdown code block"""
    pattern = rf"```{block_type}\s*\n(.*?)\n\s*```"
    match = re.search(pattern, text, re.DOTALL)

    if match:
        json_str = match.group(1)
        try:
            return json.loads(json_str)
        except json.JSONDecodeError:
            logger.error(f"Failed to parse JSON from {block_type} block")

    return None

def extract_tool_commands(text: str) -> List[Dict[str, Any]]:
    """Extract tool commands from agent response"""
    commands = []

    # Extract file operations
    file_read_pattern = r"```file-read\s*\n(.*?)\n\s*```"
    file_write_pattern = r"```file-write\s*\n(.*?)\n\s*```"
    file_list_pattern = r"```file-list\s*\n(.*?)\n\s*```"

    # Extract shell commands
    shell_pattern = r"```shell\s*\n(.*?)\n\s*```"
    python_pattern = r"```python-run\s*\n(.*?)\n\s*```"

    # Process file read commands
    for match in re.finditer(file_read_pattern, text, re.DOTALL):
        try:
            data = json.loads(match.group(1))
            commands.append({
                "type": "file-read",
                "data": data
            })
        except json.JSONDecodeError:
            logger.error("Failed to parse JSON from file-read block")

    # Process file write commands
    for match in re.finditer(file_write_pattern, text, re.DOTALL):
        try:
            data = json.loads(match.group(1))
            commands.append({
                "type": "file-write",
                "data": data
            })
        except json.JSONDecodeError:
            logger.error("Failed to parse JSON from file-write block")

    # Process file list commands
    for match in re.finditer(file_list_pattern, text, re.DOTALL):
        try:
            data = json.loads(match.group(1))
            commands.append({
                "type": "file-list",
                "data": data
            })
        except json.JSONDecodeError:
            logger.error("Failed to parse JSON from file-list block")

    # Process shell commands
    for match in re.finditer(shell_pattern, text, re.DOTALL):
        try:
            data = json.loads(match.group(1))
            commands.append({
                "type": "shell",
                "data": data
            })
        except json.JSONDecodeError:
            logger.error("Failed to parse JSON from shell block")

    # Process python run commands
    for match in re.finditer(python_pattern, text, re.DOTALL):
        try:
            data = json.loads(match.group(1))
            commands.append({
                "type": "python-run",
                "data": data
            })
        except json.JSONDecodeError:
            logger.error("Failed to parse JSON from python-run block")

    return commands

def create_agent_task_prompt(agent_role: str, task: Dict[str, Any], context: Dict[str, Any]) -> str:
    """Create a prompt for an agent to start a task"""
    # Format parent task info if available
    parent_info = ""
    if context.get("parent"):
        parent = context["parent"]
        parent_info = f"""
This task is part of a larger task:
Title: {parent['title']}
Description: {parent['description']}
"""

    # Format subtasks if available
    subtasks_info = ""
    if context["subtasks"]:
        subtasks = context["subtasks"]
        subtasks_list = "\n".join([
            f"- {subtask['title']} (Status: {subtask['status']}, Assigned to: {subtask['assigned_to'] or 'Unassigned'})"
            for subtask in subtasks
        ])
        subtasks_info = f"""
This task has the following subtasks:
{subtasks_list}
"""

    # Format context entries if available
    context_info = ""
    if context["context_entries"]:
        entries = context["context_entries"]
        entries_list = "\n".join([
            f"- {key}: {value}"
            for key, value in entries.items()
        ])
        context_info = f"""
Additional context for this task:
{entries_list}
"""

    # Format recent updates if available
    updates_info = ""
    if context["updates"]:
        updates = context["updates"][-5:]  # Only show last 5 updates
        updates_list = "\n".join([
            f"- {update['timestamp'][:19]} - {update['agent_id']}: {update['content'][:100]}..."
            if len(update['content']) > 100 else
            f"- {update['timestamp'][:19]} - {update['agent_id']}: {update['content']}"
            for update in updates
        ])
        updates_info = f"""
Recent updates:
{updates_list}
"""

    # Create the prompt
    prompt = f"""
You are an AI assistant with the role: {agent_role}.
You have been assigned the following task:

Title: {task['title']}
Description: {task['description']}
Status: {task['status']}
Created by: {task['created_by']}

{parent_info}
{subtasks_info}
{context_info}
{updates_info}

You can:
1. Complete the task by providing a result
2. Delegate subtasks to other agents
3. Add context entries to store information
4. Provide an update on your progress
5. Use tools to interact with the environment

To complete the task:
```complete
{{
  "result": "Your detailed task result here"
}}
```

To delegate a subtask:
```delegate
{{
  "task": {{
    "title": "Subtask title",
    "description": "Detailed subtask description"
  }},
  "delegate_to": "Agent name, role, or ID"
}}
```

To add a context entry:
```context
{{
  "key": "entry_key",
  "value": "entry_value"
}}
```

AVAILABLE TOOLS:

1. Read a file:
```file-read
{{
  "path": "path/to/file.txt"
}}
```

2. Write to a file:
```file-write
{{
  "path": "path/to/file.txt",
  "content": "File content goes here"
}}
```

3. List directory contents:
```file-list
{{
  "directory": "path/to/directory"
}}
```

4. Execute a shell command:
```shell
{{
  "command": "mkdir -p new_directory"
}}
```

5. Run a Python script:
```python-run
{{
  "script": "path/to/script.py",
  "args": ["arg1", "arg2"]
}}
```

You have a dedicated workspace where you can create and manipulate files. All file paths are relative to your workspace.
You can create Python scripts, run tests, and execute shell commands to accomplish your task.

Please start working on this task now. If you need more information, you can use the available tools.
"""

    return prompt

def create_agent_continue_prompt(agent_role: str, task: Dict[str, Any], context: Dict[str, Any]) -> str:
    """Create a prompt for an agent to continue a task"""
    # Format recent updates if available
    updates_info = ""
    if context["updates"]:
        updates = context["updates"][-10:]  # Show last 10 updates
        updates_list = "\n".join([
            f"- {update['timestamp'][:19]} - {update['agent_id']}: {update['content'][:100]}..."
            if len(update['content']) > 100 else
            f"- {update['timestamp'][:19]} - {update['agent_id']}: {update['content']}"
            for update in updates
        ])
        updates_info = f"""
Recent updates:
{updates_list}
"""

    # Format context entries if available
    context_info = ""
    if context["context_entries"]:
        entries = context["context_entries"]
        entries_list = "\n".join([
            f"- {key}: {value}"
            for key, value in entries.items()
        ])
        context_info = f"""
Current context for this task:
{entries_list}
"""

    # Create the prompt
    prompt = f"""
You are an AI assistant with the role: {agent_role}.
You are continuing work on the following task:

Title: {task['title']}
Description: {task['description']}
Status: {task['status']}

{context_info}
{updates_info}

Please continue working on this task. Provide an update on your progress or complete the task if you're ready.

To complete the task:
```complete
{{
  "result": "Your detailed task result here"
}}
```

To delegate a subtask:
```delegate
{{
  "task": {{
    "title": "Subtask title",
    "description": "Detailed subtask description"
  }},
  "delegate_to": "Agent name, role, or ID"
}}
```

To add a context entry:
```context
{{
  "key": "entry_key",
  "value": "entry_value"
}}
```

AVAILABLE TOOLS:

1. Read a file:
```file-read
{{
  "path": "path/to/file.txt"
}}
```

2. Write to a file:
```file-write
{{
  "path": "path/to/file.txt",
  "content": "File content goes here"
}}
```

3. List directory contents:
```file-list
{{
  "directory": "path/to/directory"
}}
```

4. Execute a shell command:
```shell
{{
  "command": "mkdir -p new_directory"
}}
```

5. Run a Python script:
```python-run
{{
  "script": "path/to/script.py",
  "args": ["arg1", "arg2"]
}}
```

You have a dedicated workspace where you can create and manipulate files. All file paths are relative to your workspace.
You can create Python scripts, run tests, and execute shell commands to accomplish your task.
"""

    return prompt

async def execute_tool_command(agent_id: str, command: Dict[str, Any]) -> Dict[str, Any]:
    """
    Execute a tool command and return the result

    Args:
        agent_id: Agent ID
        command: Tool command

    Returns:
        Dict: Command result
    """
    command_type = command["type"]
    data = command["data"]

    if command_type == "file-read":
        if "path" not in data:
            return {"success": False, "error": "Missing 'path' in file-read command"}

        success, result = FileOperations.read_file(agent_id, data["path"])
        return {"success": success, "result": result}

    elif command_type == "file-write":
        if "path" not in data or "content" not in data:
            return {"success": False, "error": "Missing 'path' or 'content' in file-write command"}

        success, result = FileOperations.write_file(agent_id, data["path"], data["content"])
        return {"success": success, "result": result}

    elif command_type == "file-list":
        directory = data.get("directory", "")
        success, result = FileOperations.list_directory(agent_id, directory)
        return {"success": success, "result": result}

    elif command_type == "shell":
        if "command" not in data:
            return {"success": False, "error": "Missing 'command' in shell command"}

        success, stdout, stderr = ShellCommands.execute_command(agent_id, data["command"])
        return {"success": success, "stdout": stdout, "stderr": stderr}

    elif command_type == "python-run":
        if "script" not in data:
            return {"success": False, "error": "Missing 'script' in python-run command"}

        args = data.get("args", [])
        success, stdout, stderr = ShellCommands.run_python_script(agent_id, data["script"], args)
        return {"success": success, "stdout": stdout, "stderr": stderr}

    return {"success": False, "error": f"Unknown command type: {command_type}"}

async def process_agent_response(db: AsyncSession, agent_id: str, task_id: str, response: str) -> None:
    """Process a response from an agent"""
    # Check for tool commands
    tool_commands = extract_tool_commands(response)
    tool_results = []

    for command in tool_commands:
        result = await execute_tool_command(agent_id, command)
        tool_results.append({
            "command": command,
            "result": result
        })

    # If tool commands were executed, add the results to the context
    if tool_results:
        # Add tool results to context
        await ContextScaffold.add_context_entry(
            db,
            task_id,
            f"tool_results_{datetime.utcnow().isoformat()}",
            json.dumps(tool_results)
        )

        # Add update about tool usage
        await ContextScaffold.add_task_update(
            db,
            task_id,
            agent_id,
            f"Executed {len(tool_results)} tool commands"
        )

    # Check for special commands in the response
    if "```complete" in response:
        # Extract completion data
        completion_data = extract_json_from_markdown(response, "complete")
        if completion_data and "result" in completion_data:
            # Complete the task
            await TaskManager.complete_task(db, task_id, agent_id, completion_data["result"])
            logger.info(f"Agent {agent_id} completed task {task_id}")
            return

    if "```delegate" in response:
        # Extract delegation data
        delegation_data = extract_json_from_markdown(response, "delegate")
        if delegation_data and "task" in delegation_data and "delegate_to" in delegation_data:
            # Get the session ID from the agent ID
            session_id = agent_id.split('_')[0] if '_' in agent_id else None

            if not session_id:
                logger.error(f"Invalid agent ID format: {agent_id}")
                return

            # Check if delegate_to is a name/role or an agent ID
            delegatee_id = delegation_data["delegate_to"]
            if not delegatee_id.startswith(f"{session_id}_"):
                # Try to resolve by name or role
                resolved_id = await TaskManager.get_agent_by_name_or_role(
                    db,
                    session_id,
                    delegation_data["delegate_to"]
                )

                if resolved_id:
                    delegatee_id = resolved_id
                    logger.info(f"Resolved '{delegation_data['delegate_to']}' to agent ID: {delegatee_id}")
                else:
                    logger.error(f"Could not resolve agent '{delegation_data['delegate_to']}' to a valid agent ID")
                    # Add update about the error
                    await ContextScaffold.add_task_update(
                        db,
                        task_id,
                        agent_id,
                        f"Failed to delegate task: Could not find agent '{delegation_data['delegate_to']}'"
                    )
                    return

            # Create and delegate a new task
            new_task_id = await TaskManager.create_task(
                db,
                delegation_data["task"]["title"],
                delegation_data["task"]["description"],
                agent_id,
                delegatee_id,
                parent_task_id=task_id,
                session_id=session_id
            )

            # Add context entry about delegation
            if new_task_id:
                # Get the delegatee's name or role for a more human-readable message
                delegatee_index = int(delegatee_id.split('_')[-1]) if '_' in delegatee_id else None
                delegatee_info = "unknown agent"

                if delegatee_index is not None:
                    from .database import Agent
                    stmt = select(Agent).where(
                        Agent.session_id == session_id,
                        Agent.agent_index == delegatee_index
                    )
                    result = await db.execute(stmt)
                    agent = result.scalars().first()

                    if agent:
                        delegatee_info = f"{agent.name} ({agent.role})"

                await ContextScaffold.add_context_entry(
                    db,
                    task_id,
                    f"delegated_task_{new_task_id}",
                    f"Delegated subtask: {delegation_data['task']['title']} to {delegatee_info}"
                )
                logger.info(f"Agent {agent_id} delegated subtask {new_task_id} to {delegatee_id}")
            return

    if "```context" in response:
        # Extract context data
        context_data = extract_json_from_markdown(response, "context")
        if context_data and "key" in context_data and "value" in context_data:
            # Add context entry
            await ContextScaffold.add_context_entry(
                db,
                task_id,
                context_data["key"],
                context_data["value"]
            )
            logger.info(f"Agent {agent_id} added context entry '{context_data['key']}' to task {task_id}")
            return

    # If no special command, treat as a regular update
    await ContextScaffold.add_task_update(db, task_id, agent_id, response)
    logger.info(f"Agent {agent_id} provided an update for task {task_id}")

async def process_new_task(db: AsyncSession, agent_id: str, agent_model: str, agent_role: str, task: Dict[str, Any], context: Dict[str, Any]) -> None:
    """Process a new task"""
    # Update task status
    stmt = select(Task).where(Task.id == task["id"])
    result = await db.execute(stmt)
    db_task = result.scalars().first()

    if db_task:
        db_task.status = "in_progress"
        await db.commit()

    # Add update
    await ContextScaffold.add_task_update(
        db,
        task["id"],
        agent_id,
        "Started working on task"
    )

    # Create prompt for the agent
    prompt = create_agent_task_prompt(agent_role, task, context)

    # Get response from the model
    provider = get_model_provider(model_name=agent_model)
    response = await provider.generate_completion(
        system_prompt=f"You are an AI assistant with the role: {agent_role}. You are working on a delegated task.",
        user_prompt=prompt
    )

    # Process the response
    await process_agent_response(db, agent_id, task["id"], response)

async def continue_task(db: AsyncSession, agent_id: str, agent_model: str, agent_role: str, task: Dict[str, Any], context: Dict[str, Any]) -> None:
    """Continue working on a task"""
    # Check if there are any new updates since last check
    last_update_time = None
    for update in context["updates"]:
        if update["agent_id"] == agent_id:
            last_update_time = datetime.fromisoformat(update["timestamp"])
            break

    if last_update_time and (datetime.utcnow() - last_update_time).total_seconds() < 300:
        # Last update was less than 5 minutes ago, wait longer
        return

    # Create prompt for the agent to continue the task
    prompt = create_agent_continue_prompt(agent_role, task, context)

    # Get response from the model
    provider = get_model_provider(model_name=agent_model)
    response = await provider.generate_completion(
        system_prompt=f"You are an AI assistant with the role: {agent_role}. You are continuing work on a delegated task.",
        user_prompt=prompt
    )

    # Process the response
    await process_agent_response(db, agent_id, task["id"], response)

async def agent_task_loop(agent_id: str, agent_model: str, agent_role: str) -> None:
    """Main processing loop for an agent"""
    logger.info(f"Starting agent task loop for agent {agent_id} with role {agent_role}")

    while True:
        try:
            async with async_session() as db:
                # Refresh context
                context = await ContextRefresher.refresh_agent_context(db, agent_id)

                # Check if there are any active tasks
                if not context["active_tasks"]:
                    # No active tasks, sleep and check again later
                    await asyncio.sleep(60)  # Check every minute
                    continue

                # Get the current task
                current_task = context["current_task"]["task"]

                # Process the task
                if current_task["status"] == "pending":
                    # Task is new, start working on it
                    await process_new_task(db, agent_id, agent_model, agent_role, current_task, context["current_task"])
                elif current_task["status"] == "in_progress":
                    # Task is in progress, continue working
                    await continue_task(db, agent_id, agent_model, agent_role, current_task, context["current_task"])

                # Sleep before checking again
                await asyncio.sleep(30)  # Check every 30 seconds
        except Exception as e:
            logger.error(f"Error in agent task loop for {agent_id}: {e}")
            await asyncio.sleep(60)  # Wait a minute before retrying
