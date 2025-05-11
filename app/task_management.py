"""
Task management module for AI-to-AI Feedback API

This module handles task delegation, context scaffolding, and task management
for the multi-agent system.
"""

import json
import logging
import asyncio
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple
from uuid import uuid4

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from .database import Task, TaskContext, TaskUpdate, Agent, Session
from .providers.factory import get_model_provider

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("task-management")

class ContextScaffold:
    """System for managing and retrieving context for agents"""

    @staticmethod
    async def get_task_context(db: AsyncSession, task_id: str) -> Dict[str, Any]:
        """Get the full context for a task"""
        # Get the task
        stmt = select(Task).where(Task.id == task_id)
        result = await db.execute(stmt)
        task = result.scalars().first()

        if not task:
            return {"error": "Task not found"}

        # Get context entries
        stmt = select(TaskContext).where(TaskContext.task_id == task_id)
        result = await db.execute(stmt)
        context_entries = result.scalars().all()

        # Get updates
        stmt = select(TaskUpdate).where(TaskUpdate.task_id == task_id).order_by(TaskUpdate.timestamp)
        result = await db.execute(stmt)
        updates = result.scalars().all()

        # Get parent task if exists
        parent_context = {}
        if task.parent_task_id:
            parent_context = await ContextScaffold.get_task_context(db, task.parent_task_id)
            # Remove some details to avoid context bloat
            if "updates" in parent_context:
                parent_context["updates"] = parent_context["updates"][-3:]  # Only keep last 3 updates

        # Build context
        context = {
            "task": {
                "id": task.id,
                "title": task.title,
                "description": task.description,
                "status": task.status,
                "created_by": task.created_by,
                "assigned_to": task.assigned_to,
                "created_at": task.created_at.isoformat(),
                "updated_at": task.updated_at.isoformat(),
                "completed_at": task.completed_at.isoformat() if task.completed_at else None,
                "result": task.result,
                "parent_task_id": task.parent_task_id
            },
            "context_entries": {entry.key: entry.value for entry in context_entries},
            "updates": [
                {
                    "agent_id": update.agent_id,
                    "content": update.content,
                    "timestamp": update.timestamp.isoformat()
                }
                for update in updates
            ],
            "parent": parent_context.get("task") if parent_context else None,
            "subtasks": []  # Will be filled below
        }

        # Get subtasks
        stmt = select(Task).where(Task.parent_task_id == task_id)
        result = await db.execute(stmt)
        subtasks = result.scalars().all()

        # Add subtask summaries
        for subtask in subtasks:
            context["subtasks"].append({
                "id": subtask.id,
                "title": subtask.title,
                "status": subtask.status,
                "assigned_to": subtask.assigned_to
            })

        return context

    @staticmethod
    async def add_context_entry(db: AsyncSession, task_id: str, key: str, value: str) -> bool:
        """Add a context entry to a task"""
        try:
            # Check if entry with this key already exists
            stmt = select(TaskContext).where(
                TaskContext.task_id == task_id,
                TaskContext.key == key
            )
            result = await db.execute(stmt)
            existing_entry = result.scalars().first()

            if existing_entry:
                # Update existing entry
                existing_entry.value = value
            else:
                # Create new entry
                entry = TaskContext(
                    task_id=task_id,
                    key=key,
                    value=value
                )
                db.add(entry)

            await db.commit()
            return True
        except Exception as e:
            await db.rollback()
            logger.error(f"Error adding context entry: {e}")
            return False

    @staticmethod
    async def add_task_update(db: AsyncSession, task_id: str, agent_id: str, content: str) -> bool:
        """Add an update to a task"""
        try:
            # Create update
            update = TaskUpdate(
                task_id=task_id,
                agent_id=agent_id,
                content=content
            )
            db.add(update)

            # Update task's updated_at timestamp
            stmt = select(Task).where(Task.id == task_id)
            result = await db.execute(stmt)
            task = result.scalars().first()

            if task:
                task.updated_at = datetime.utcnow()

            await db.commit()
            return True
        except Exception as e:
            await db.rollback()
            logger.error(f"Error adding task update: {e}")
            return False

class ContextRefresher:
    """System for regularly refreshing agent context"""

    @staticmethod
    async def get_agent_tasks(db: AsyncSession, agent_id: str) -> List[Dict[str, Any]]:
        """Get all tasks assigned to an agent"""
        stmt = select(Task).where(
            Task.assigned_to == agent_id,
            Task.status.in_(["pending", "in_progress"])
        ).order_by(Task.updated_at.desc())
        result = await db.execute(stmt)
        tasks = result.scalars().all()

        return [
            {
                "id": task.id,
                "title": task.title,
                "description": task.description,
                "status": task.status,
                "created_by": task.created_by,
                "created_at": task.created_at.isoformat(),
                "updated_at": task.updated_at.isoformat()
            }
            for task in tasks
        ]

    @staticmethod
    async def refresh_agent_context(db: AsyncSession, agent_id: str) -> Dict[str, Any]:
        """Refresh the context for an agent"""
        # Get agent's active tasks
        tasks = await ContextRefresher.get_agent_tasks(db, agent_id)

        # Get full context for the most recently updated task
        current_task_context = {}
        if tasks:
            current_task_context = await ContextScaffold.get_task_context(db, tasks[0]["id"])

        # Build agent context
        agent_context = {
            "agent_id": agent_id,
            "active_tasks": tasks,
            "current_task": current_task_context,
            "timestamp": datetime.utcnow().isoformat()
        }

        return agent_context

class TaskManager:
    """System for managing tasks and delegation"""

    @staticmethod
    async def get_agent_by_name_or_role(
        db: AsyncSession,
        session_id: str,
        name_or_role: str
    ) -> Optional[str]:
        """
        Get agent ID by name or role

        Args:
            db: Database session
            session_id: Session ID
            name_or_role: Agent name or role

        Returns:
            Optional[str]: Agent ID if found, None otherwise
        """
        try:
            # Try exact match on name or role
            stmt = select(Agent).where(
                Agent.session_id == session_id,
                (Agent.name == name_or_role) | (Agent.role == name_or_role)
            )
            result = await db.execute(stmt)
            agent = result.scalars().first()

            if agent:
                return f"{session_id}_{agent.agent_index}"

            # Try partial match if exact match fails
            stmt = select(Agent).where(
                Agent.session_id == session_id,
                (Agent.name.ilike(f"%{name_or_role}%")) | (Agent.role.ilike(f"%{name_or_role}%"))
            )
            result = await db.execute(stmt)
            agent = result.scalars().first()

            if agent:
                return f"{session_id}_{agent.agent_index}"

            return None
        except Exception as e:
            logger.error(f"Error finding agent by name or role: {e}")
            return None

    @staticmethod
    async def create_task(
        db: AsyncSession,
        title: str,
        description: str,
        created_by: str,
        assigned_to: Optional[str] = None,
        parent_task_id: Optional[str] = None,
        session_id: Optional[str] = None
    ) -> Optional[str]:
        """Create a new task"""
        try:
            task_id = str(uuid4())

            task = Task(
                id=task_id,
                title=title,
                description=description,
                status="pending" if assigned_to else "unassigned",
                created_by=created_by,
                assigned_to=assigned_to,
                parent_task_id=parent_task_id,
                session_id=session_id
            )

            db.add(task)
            await db.commit()

            # Add initial update
            if assigned_to:
                await ContextScaffold.add_task_update(
                    db,
                    task_id,
                    created_by,
                    f"Task created and assigned to {assigned_to}"
                )
            else:
                await ContextScaffold.add_task_update(
                    db,
                    task_id,
                    created_by,
                    "Task created"
                )

            return task_id
        except Exception as e:
            await db.rollback()
            logger.error(f"Error creating task: {e}")
            return None

    @staticmethod
    async def delegate_task(
        db: AsyncSession,
        task_id: str,
        delegator_id: str,
        delegatee_id: str
    ) -> bool:
        """Delegate a task from one agent to another"""
        try:
            # Get the task
            stmt = select(Task).where(Task.id == task_id)
            result = await db.execute(stmt)
            task = result.scalars().first()

            if not task:
                return False

            # Update task
            task.assigned_to = delegatee_id
            task.status = "pending"
            task.updated_at = datetime.utcnow()

            # Add update
            await ContextScaffold.add_task_update(
                db,
                task_id,
                delegator_id,
                f"Task delegated to {delegatee_id}"
            )

            await db.commit()
            return True
        except Exception as e:
            await db.rollback()
            logger.error(f"Error delegating task: {e}")
            return False

    @staticmethod
    async def complete_task(
        db: AsyncSession,
        task_id: str,
        agent_id: str,
        result: str
    ) -> bool:
        """Mark a task as completed"""
        try:
            # Get the task
            stmt = select(Task).where(Task.id == task_id)
            result_query = await db.execute(stmt)
            task = result_query.scalars().first()

            if not task or task.assigned_to != agent_id:
                return False

            # Update task
            task.status = "completed"
            task.completed_at = datetime.utcnow()
            task.result = result
            task.updated_at = datetime.utcnow()

            # Add update
            await ContextScaffold.add_task_update(
                db,
                task_id,
                agent_id,
                "Task completed"
            )

            await db.commit()
            return True
        except Exception as e:
            await db.rollback()
            logger.error(f"Error completing task: {e}")
            return False
