"""
Task Manager

This module is responsible for managing the lifecycle of tasks,
including creation, updating, querying, and deletion.
"""

import logging
import uuid
from datetime import datetime
from typing import Dict, List, Optional, Any

from models.task import Task, TaskStatus, TaskPriority

logger = logging.getLogger(__name__)

class TaskManager:
    """
    Task Manager class for managing task lifecycle.
    """
    
    def __init__(self, db_connection):
        """
        Initialize the Task Manager.
        
        Args:
            db_connection: Database connection
        """
        self.db = db_connection
        logger.info("Task Manager initialized")
    
    async def create_task(self, 
                         title: str, 
                         description: str, 
                         priority: TaskPriority = TaskPriority.MEDIUM,
                         assigned_agent_id: Optional[str] = None,
                         parent_task_id: Optional[str] = None,
                         metadata: Optional[Dict[str, Any]] = None) -> Task:
        """
        Create a new task.
        
        Args:
            title: Task title
            description: Task description
            priority: Task priority
            assigned_agent_id: ID of assigned agent (if any)
            parent_task_id: ID of parent task (if any)
            metadata: Additional task metadata
            
        Returns:
            Created task
        """
        task_id = str(uuid.uuid4())
        now = datetime.utcnow().isoformat()
        
        task = Task(
            id=task_id,
            title=title,
            description=description,
            status=TaskStatus.NOT_STARTED,
            priority=priority,
            created_at=now,
            updated_at=now,
            assigned_agent_id=assigned_agent_id,
            parent_task_id=parent_task_id,
            metadata=metadata or {}
        )
        
        # Save task to database
        await self.db.tasks.create(task)
        
        logger.info(f"Created task {task_id}: {title}")
        return task
    
    async def get_task(self, task_id: str) -> Optional[Task]:
        """
        Get a task by ID.
        
        Args:
            task_id: Task ID
            
        Returns:
            Task if found, None otherwise
        """
        task = await self.db.tasks.get(task_id)
        return task
    
    async def update_task(self, task_id: str, **kwargs) -> Optional[Task]:
        """
        Update a task.
        
        Args:
            task_id: Task ID
            **kwargs: Fields to update
            
        Returns:
            Updated task if found, None otherwise
        """
        # Ensure updated_at is set
        kwargs['updated_at'] = datetime.utcnow().isoformat()
        
        # Update task in database
        task = await self.db.tasks.update(task_id, **kwargs)
        
        if task:
            logger.info(f"Updated task {task_id}")
        else:
            logger.warning(f"Failed to update task {task_id}: not found")
            
        return task
    
    async def delete_task(self, task_id: str) -> bool:
        """
        Delete a task.
        
        Args:
            task_id: Task ID
            
        Returns:
            True if task was deleted, False otherwise
        """
        result = await self.db.tasks.delete(task_id)
        
        if result:
            logger.info(f"Deleted task {task_id}")
        else:
            logger.warning(f"Failed to delete task {task_id}: not found")
            
        return result
    
    async def list_tasks(self, 
                        status: Optional[TaskStatus] = None,
                        priority: Optional[TaskPriority] = None,
                        assigned_agent_id: Optional[str] = None,
                        parent_task_id: Optional[str] = None,
                        limit: int = 100,
                        offset: int = 0) -> List[Task]:
        """
        List tasks with optional filtering.
        
        Args:
            status: Filter by status
            priority: Filter by priority
            assigned_agent_id: Filter by assigned agent ID
            parent_task_id: Filter by parent task ID
            limit: Maximum number of tasks to return
            offset: Offset for pagination
            
        Returns:
            List of tasks
        """
        filters = {}
        
        if status is not None:
            filters['status'] = status
            
        if priority is not None:
            filters['priority'] = priority
            
        if assigned_agent_id is not None:
            filters['assigned_agent_id'] = assigned_agent_id
            
        if parent_task_id is not None:
            filters['parent_task_id'] = parent_task_id
            
        tasks = await self.db.tasks.list(filters, limit, offset)
        return tasks
    
    async def assign_task(self, task_id: str, agent_id: str) -> Optional[Task]:
        """
        Assign a task to an agent.
        
        Args:
            task_id: Task ID
            agent_id: Agent ID
            
        Returns:
            Updated task if found, None otherwise
        """
        return await self.update_task(task_id, assigned_agent_id=agent_id)
    
    async def update_task_status(self, task_id: str, status: TaskStatus) -> Optional[Task]:
        """
        Update a task's status.
        
        Args:
            task_id: Task ID
            status: New status
            
        Returns:
            Updated task if found, None otherwise
        """
        return await self.update_task(task_id, status=status)
    
    async def get_next_task(self, agent_id: Optional[str] = None) -> Optional[Task]:
        """
        Get the next task to process.
        
        Args:
            agent_id: Agent ID to get tasks for (if any)
            
        Returns:
            Next task if available, None otherwise
        """
        filters = {'status': TaskStatus.NOT_STARTED}
        
        if agent_id is not None:
            filters['assigned_agent_id'] = agent_id
            
        tasks = await self.db.tasks.list(filters, limit=1, order_by=[('priority', 'desc'), ('created_at', 'asc')])
        
        if tasks:
            return tasks[0]
        
        return None
