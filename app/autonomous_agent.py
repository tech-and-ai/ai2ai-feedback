"""
Autonomous Agent System

This module implements autonomous agents that can:
1. Select tasks from a plan
2. Execute tasks independently
3. Provide regular progress updates
4. Collaborate with other agents when needed
5. Handle errors and recovery
"""

import os
import json
import uuid
import asyncio
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple, Set

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import or_, and_, func, desc

from .database import get_db, Session, Agent, Task, TaskContext, TaskUpdate
from .providers.factory import get_model_provider
from .utils.feedback_parser import extract_structured_feedback
from .coding_agent import CodingAgent

# Configure logging
logger = logging.getLogger(__name__)

class AutonomousAgent:
    """
    Autonomous agent that can select and execute tasks independently.

    The agent continuously monitors the task queue for tasks that match its skills,
    executes them, and provides regular updates on progress.
    """

    def __init__(self, agent_id: str, name: str, role: str, skills: List[str], model: str):
        """
        Initialize an autonomous agent.

        Args:
            agent_id: Unique identifier for the agent
            name: Display name for the agent
            role: Role description
            skills: List of skills the agent possesses
            model: AI model to use for this agent
        """
        self.agent_id = agent_id
        self.name = name
        self.role = role
        self.skills = set(skills)
        # Use the model passed in, defaulting to google/gemini-2.0-flash-001
        self.model = model or "google/gemini-2.0-flash-001"
        self.current_task = None
        self.status = "idle"
        # Get the provider for the model
        self.provider = get_model_provider("ollama", self.model)
        self.running = False

    async def start(self):
        """Start the agent's task processing loop."""
        self.running = True
        self.status = "running"
        logger.info(f"Agent {self.name} (ID: {self.agent_id}) started")

        # Start the task processing loop in the background
        asyncio.create_task(self._task_loop())

    async def _task_loop(self):
        """Task processing loop that runs in the background."""
        while self.running:
            if self.status == "running" or self.status == "idle":
                # Look for a task to work on
                task = await self._select_task()
                if task:
                    self.current_task = task
                    self.status = "working"
                    # Process the task
                    await self._process_task(task)
                    # Reset status after processing
                    self.status = "running"
                else:
                    # No suitable tasks found, wait before checking again
                    await asyncio.sleep(5)
            else:
                # Already working on a task, wait for it to complete
                await asyncio.sleep(5)

    async def stop(self):
        """Stop the agent's task processing loop."""
        self.running = False
        logger.info(f"Agent {self.name} (ID: {self.agent_id}) stopped")

    async def _select_task(self) -> Optional[Dict[str, Any]]:
        """
        Select a task that matches the agent's skills.

        Returns:
            Optional[Dict]: Selected task or None if no suitable task found
        """
        async with AsyncSession() as db:
            # Find pending tasks that match agent skills and have no dependencies or completed dependencies
            query = select(Task).where(
                Task.status == "pending",
                Task.assigned_to.is_(None)  # Not already assigned
            ).order_by(desc(Task.priority))  # Higher priority first

            result = await db.execute(query)
            tasks = result.scalars().all()

            for task in tasks:
                # Check if agent has the required skills
                required_skills = await self._get_task_required_skills(db, task.id)
                if not required_skills or self.skills.intersection(required_skills):
                    # Check if dependencies are met
                    if await self._dependencies_met(db, task.id):
                        # Claim the task
                        task.status = "in_progress"
                        task.assigned_to = self.agent_id
                        task.updated_at = datetime.utcnow()
                        await db.commit()

                        # Log task assignment
                        await self._log_update(db, task.id, f"Task assigned to agent {self.name}", "info")

                        return {
                            "id": task.id,
                            "title": task.title,
                            "description": task.description,
                            "context": await self._get_task_context(db, task.id)
                        }

            return None

    async def _get_task_required_skills(self, db: AsyncSession, task_id: str) -> Set[str]:
        """Get the required skills for a task."""
        query = select(Task).where(Task.id == task_id)
        result = await db.execute(query)
        task = result.scalars().first()

        if not task or not task.required_skills:
            return set()

        # For SQLite, required_skills is stored as a comma-separated string
        return set(skill.strip() for skill in task.required_skills.split(","))

    async def _dependencies_met(self, db: AsyncSession, task_id: str) -> bool:
        """Check if all dependencies for a task are completed."""
        query = select(Task).where(Task.id == task_id)
        result = await db.execute(query)
        task = result.scalars().first()

        if not task or not task.parent_task_id:
            return True  # No dependencies

        # Check parent task
        query = select(Task).where(Task.id == task.parent_task_id)
        result = await db.execute(query)
        parent_task = result.scalars().first()

        return parent_task and parent_task.status == "completed"

    async def _get_task_context(self, db: AsyncSession, task_id: str) -> Dict[str, Any]:
        """Get the context for a task."""
        query = select(TaskContext).where(TaskContext.task_id == task_id)
        result = await db.execute(query)
        contexts = result.scalars().all()

        context_dict = {}
        for ctx in contexts:
            context_dict[ctx.key] = ctx.value

        return context_dict

    async def _process_task(self, task: Dict[str, Any]):
        """
        Process a task and update its status.

        Args:
            task: Task to process
        """
        task_id = task["id"]

        try:
            # Log start of processing
            async with AsyncSession() as db:
                await self._log_update(db, task_id, f"Started processing task: {task['title']}", "info")

            # Prepare the prompt for the AI model
            prompt = self._prepare_task_prompt(task)

            # Get response from AI model
            response = await self.provider.generate_text(prompt)

            # Extract structured information from response
            result = self._parse_response(response)

            # Update task status
            async with AsyncSession() as db:
                await self._complete_task(db, task_id, result)

            # Reset agent status
            self.current_task = None
            self.status = "idle"

        except Exception as e:
            logger.error(f"Error processing task {task_id}: {str(e)}")

            # Log error
            async with AsyncSession() as db:
                await self._log_update(db, task_id, f"Error: {str(e)}", "error")

                # Mark task as failed
                await self._fail_task(db, task_id, str(e))

            # Reset agent status
            self.current_task = None
            self.status = "idle"

    def _prepare_task_prompt(self, task: Dict[str, Any]) -> str:
        """
        Prepare a prompt for the AI model based on the task.

        Args:
            task: Task information

        Returns:
            str: Prompt for the AI model
        """
        context_str = ""
        if task.get("context"):
            context_str = "Task Context:\n"
            for key, value in task["context"].items():
                context_str += f"- {key}: {value}\n"

        prompt = f"""
You are {self.name}, an autonomous AI agent with the role: {self.role}
Your skills include: {', '.join(self.skills)}

TASK:
Title: {task['title']}
Description: {task['description']}

{context_str}

Please complete this task to the best of your ability. Provide a detailed response that includes:
1. Your analysis of the task
2. Your approach to solving it
3. The actual solution or implementation
4. Any recommendations or next steps

FORMAT YOUR RESPONSE AS FOLLOWS:
ANALYSIS: [Your analysis of the task]
APPROACH: [Your approach to solving it]
SOLUTION: [The actual solution or implementation]
RECOMMENDATIONS: [Any recommendations or next steps]
"""
        return prompt

    def _parse_response(self, response: str) -> Dict[str, Any]:
        """
        Parse the AI model's response into structured data.

        Args:
            response: Raw response from the AI model

        Returns:
            Dict: Structured response data
        """
        # Extract sections using simple parsing
        sections = {
            "analysis": "",
            "approach": "",
            "solution": "",
            "recommendations": ""
        }

        current_section = None

        for line in response.split('\n'):
            if line.startswith("ANALYSIS:"):
                current_section = "analysis"
                sections[current_section] = line.replace("ANALYSIS:", "").strip()
            elif line.startswith("APPROACH:"):
                current_section = "approach"
                sections[current_section] = line.replace("APPROACH:", "").strip()
            elif line.startswith("SOLUTION:"):
                current_section = "solution"
                sections[current_section] = line.replace("SOLUTION:", "").strip()
            elif line.startswith("RECOMMENDATIONS:"):
                current_section = "recommendations"
                sections[current_section] = line.replace("RECOMMENDATIONS:", "").strip()
            elif current_section:
                sections[current_section] += "\n" + line

        # Clean up and trim whitespace
        for key in sections:
            sections[key] = sections[key].strip()

        return {
            "full_response": response,
            "structured": sections
        }

    async def _complete_task(self, db: AsyncSession, task_id: str, result: Dict[str, Any]):
        """
        Mark a task as completed with results.

        Args:
            db: Database session
            task_id: Task ID
            result: Task result
        """
        query = select(Task).where(Task.id == task_id)
        result_db = await db.execute(query)
        task = result_db.scalars().first()

        if task:
            task.status = "completed"
            task.result = json.dumps(result)
            task.completed_at = datetime.utcnow()
            task.updated_at = datetime.utcnow()

            await db.commit()

            # Log completion
            await self._log_update(db, task_id, "Task completed successfully", "info")

    async def _fail_task(self, db: AsyncSession, task_id: str, error: str):
        """
        Mark a task as failed with error information.

        Args:
            db: Database session
            task_id: Task ID
            error: Error message
        """
        query = select(Task).where(Task.id == task_id)
        result = await db.execute(query)
        task = result.scalars().first()

        if task:
            task.status = "failed"
            task.result = json.dumps({"error": error})
            task.updated_at = datetime.utcnow()

            await db.commit()

            # Log failure
            await self._log_update(db, task_id, f"Task failed: {error}", "error")

    async def _log_update(self, db: AsyncSession, task_id: str, content: str, level: str = "info"):
        """
        Log a task update.

        Args:
            db: Database session
            task_id: Task ID
            content: Update content
            level: Update level (info, warning, error)
        """
        update = TaskUpdate(
            task_id=task_id,
            agent_id=self.agent_id,
            content=content,
            timestamp=datetime.utcnow(),
            level=level
        )

        db.add(update)
        await db.commit()


class AgentManager:
    """
    Manager for autonomous agents.

    Handles agent creation, starting, stopping, and monitoring.
    """

    def __init__(self):
        """Initialize the agent manager."""
        self.agents = {}  # agent_id -> AutonomousAgent

    async def create_agent(self, name: str, role: str, skills: List[str], model: str, agent_type: str = "standard") -> str:
        """
        Create a new autonomous agent.

        Args:
            name: Agent name
            role: Agent role
            skills: List of agent skills
            model: AI model to use
            agent_type: Agent type (standard or coding)

        Returns:
            str: Agent ID
        """
        agent_id = str(uuid.uuid4())

        if agent_type == "coding":
            # Create a coding agent
            agent = CodingAgent(
                agent_id=agent_id,
                name=name,
                role=role,
                skills=skills,
                model=model
            )
            # Set agent type
            agent.agent_type = "coding"

            # Set up workspace
            await agent.setup_workspace()

            # Start the agent
            await agent.start()
        else:
            # Create a standard agent
            agent = AutonomousAgent(
                agent_id=agent_id,
                name=name,
                role=role,
                skills=skills,
                model=model
            )
            # Set agent type
            agent.agent_type = "standard"

            # Start the agent
            await agent.start()

        self.agents[agent_id] = agent
        return agent_id

    async def stop_agent(self, agent_id: str) -> bool:
        """
        Stop an autonomous agent.

        Args:
            agent_id: Agent ID

        Returns:
            bool: True if successful, False otherwise
        """
        if agent_id in self.agents:
            await self.agents[agent_id].stop()
            del self.agents[agent_id]
            return True

        return False

    def get_agent(self, agent_id: str) -> Optional[AutonomousAgent]:
        """
        Get an agent by ID.

        Args:
            agent_id: Agent ID

        Returns:
            Optional[AutonomousAgent]: Agent or None if not found
        """
        return self.agents.get(agent_id)

    def get_all_agents(self) -> Dict[str, AutonomousAgent]:
        """
        Get all agents.

        Returns:
            Dict[str, AutonomousAgent]: Dictionary of agent_id -> agent
        """
        return self.agents

    async def stop_all_agents(self):
        """Stop all agents."""
        for agent_id in list(self.agents.keys()):
            await self.stop_agent(agent_id)


# Create a global agent manager
agent_manager = AgentManager()
