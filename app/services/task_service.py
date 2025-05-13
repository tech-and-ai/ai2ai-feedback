"""
Task service module.
"""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import update, func
from typing import List, Optional, Tuple, Dict, Any
from datetime import datetime
import uuid
import json
import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv

from app.db.models import Task, TaskUpdate, Agent

# Load environment variables
load_dotenv()
from app.api.models import TaskCreate, TaskUpdate as TaskUpdateModel

class TaskService:
    """
    Service for task management.
    """
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_task(self, task_data: TaskCreate) -> Task:
        """
        Create a new task.
        """
        # Create task with basic fields
        task = Task(
            id=str(uuid.uuid4()),
            title=task_data.title,
            description=task_data.description,
            complexity=task_data.complexity,
            status="not_started",
            stage_progress=0,
            priority=task_data.priority
        )

        # Add new fields if provided
        if task_data.research_likelihood:
            task.research_likelihood = task_data.research_likelihood.value

        if task_data.allowed_tools:
            task.allowed_tools = json.dumps(task_data.allowed_tools)

        if task_data.output_formats:
            task.output_formats = json.dumps([fmt.value for fmt in task_data.output_formats])

        if task_data.max_token_usage is not None:
            task.max_token_usage = task_data.max_token_usage

        if task_data.allow_collaboration is not None:
            task.allow_collaboration = task_data.allow_collaboration

        if task_data.max_collaborators is not None:
            task.max_collaborators = task_data.max_collaborators

        if task_data.human_review_required is not None:
            task.human_review_required = task_data.human_review_required

        if task_data.deadline:
            task.deadline = task_data.deadline

        self.db.add(task)
        await self.db.commit()
        await self.db.refresh(task)

        # Try to assign the task to an agent
        await self.assign_task(task.id)

        return task

    async def assign_task(self, task_id: str) -> Optional[str]:
        """
        Assign a task to an available agent.
        """
        # Get the task
        task = await self.get_task(task_id)
        if not task:
            return None

        # Find available agents that can handle this complexity
        query = select(Agent).where(
            Agent.status == "available",
            Agent.min_complexity <= task.complexity,
            Agent.max_complexity >= task.complexity
        ).order_by(Agent.last_active)

        result = await self.db.execute(query)
        agent = result.scalars().first()

        if not agent:
            # No suitable agent available
            return None

        # Update task assignment
        task.assigned_agent_id = agent.id
        task.status = "design"
        task.updated_at = datetime.utcnow()

        # Update agent status
        agent.status = "busy"
        agent.last_active = datetime.utcnow()

        # Create task update
        task_update = TaskUpdate(
            id=str(uuid.uuid4()),
            task_id=task.id,
            agent_id=agent.id,
            update_type="status_change",
            content=f"Task assigned to agent {agent.name}"
        )

        self.db.add(task_update)
        await self.db.commit()

        # Return the agent ID
        return agent.id

    async def get_task(self, task_id: str) -> Optional[Task]:
        """
        Get a task by ID.
        """
        query = select(Task).where(Task.id == task_id)
        result = await self.db.execute(query)
        return result.scalars().first()

    async def get_task_with_updates(self, task_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a task with its updates.
        """
        task = await self.get_task(task_id)
        if not task:
            return None

        # Get task updates
        query = select(TaskUpdate).where(TaskUpdate.task_id == task_id).order_by(TaskUpdate.timestamp)
        result = await self.db.execute(query)
        updates = result.scalars().all()

        # Convert to dict
        task_dict = {
            "id": task.id,
            "title": task.title,
            "description": task.description,
            "complexity": task.complexity,
            "status": task.status,
            "stage_progress": task.stage_progress,
            "created_at": task.created_at,
            "updated_at": task.updated_at,
            "completed_at": task.completed_at,
            "assigned_agent_id": task.assigned_agent_id,
            "result_path": task.result_path,
            "priority": task.priority,

            # New fields
            "research_likelihood": task.research_likelihood,
            "allowed_tools": json.loads(task.allowed_tools) if task.allowed_tools else None,
            "output_formats": json.loads(task.output_formats) if task.output_formats else None,
            "max_token_usage": task.max_token_usage,
            "allow_collaboration": task.allow_collaboration,
            "max_collaborators": task.max_collaborators,
            "human_review_required": task.human_review_required,
            "deadline": task.deadline,

            "updates": updates
        }

        return task_dict

    async def list_tasks(
        self,
        status: Optional[str] = None,
        agent_id: Optional[str] = None,
        limit: int = 20,
        offset: int = 0
    ) -> Tuple[List[Dict[str, Any]], int]:
        """
        List tasks with optional filtering.
        """
        # Build query
        query = select(Task)
        count_query = select(func.count()).select_from(Task)

        # Apply filters
        if status:
            query = query.where(Task.status == status)
            count_query = count_query.where(Task.status == status)

        if agent_id:
            query = query.where(Task.assigned_agent_id == agent_id)
            count_query = count_query.where(Task.assigned_agent_id == agent_id)

        # Apply pagination
        query = query.order_by(Task.created_at.desc()).offset(offset).limit(limit)

        # Execute queries
        result = await self.db.execute(query)
        count_result = await self.db.execute(count_query)

        tasks = result.scalars().all()
        total = count_result.scalar()

        # Enhance tasks with agent names
        task_dicts = []
        for task in tasks:
            task_dict = {
                "id": task.id,
                "title": task.title,
                "description": task.description,
                "complexity": task.complexity,
                "status": task.status,
                "stage_progress": task.stage_progress,
                "created_at": task.created_at,
                "updated_at": task.updated_at,
                "completed_at": task.completed_at,
                "assigned_agent_id": task.assigned_agent_id,
                "result_path": task.result_path,
                "priority": task.priority,
                "research_likelihood": task.research_likelihood,
                "allowed_tools": json.loads(task.allowed_tools) if task.allowed_tools else None,
                "output_formats": json.loads(task.output_formats) if task.output_formats else None,
                "max_token_usage": task.max_token_usage,
                "allow_collaboration": task.allow_collaboration,
                "max_collaborators": task.max_collaborators,
                "human_review_required": task.human_review_required,
                "deadline": task.deadline,
                "assigned_agent_name": None
            }

            # Get agent name if assigned
            if task.assigned_agent_id:
                agent_query = select(Agent).where(Agent.id == task.assigned_agent_id)
                agent_result = await self.db.execute(agent_query)
                agent = agent_result.scalars().first()
                if agent:
                    task_dict["assigned_agent_name"] = agent.name

            task_dicts.append(task_dict)

        return task_dicts, total

    async def update_task(self, task_id: str, task_data: TaskUpdateModel) -> Optional[Task]:
        """
        Update a task.
        """
        task = await self.get_task(task_id)
        if not task:
            return None

        # Update basic fields
        if task_data.title is not None:
            task.title = task_data.title

        if task_data.description is not None:
            task.description = task_data.description

        if task_data.complexity is not None:
            task.complexity = task_data.complexity

        if task_data.priority is not None:
            task.priority = task_data.priority

        # Update new fields
        if task_data.research_likelihood is not None:
            task.research_likelihood = task_data.research_likelihood.value

        if task_data.allowed_tools is not None:
            task.allowed_tools = json.dumps(task_data.allowed_tools)

        if task_data.output_formats is not None:
            task.output_formats = json.dumps([fmt.value for fmt in task_data.output_formats])

        if task_data.max_token_usage is not None:
            task.max_token_usage = task_data.max_token_usage

        if task_data.allow_collaboration is not None:
            task.allow_collaboration = task_data.allow_collaboration

        if task_data.max_collaborators is not None:
            task.max_collaborators = task_data.max_collaborators

        if task_data.human_review_required is not None:
            task.human_review_required = task_data.human_review_required

        if task_data.deadline is not None:
            task.deadline = task_data.deadline

        task.updated_at = datetime.utcnow()

        await self.db.commit()
        await self.db.refresh(task)

        return task

    async def update_task_status(
        self,
        task_id: str,
        status: str,
        stage_progress: int,
        update_message: Optional[str] = None
    ) -> Optional[Task]:
        """
        Update the status of a task.
        """
        task = await self.get_task(task_id)
        if not task:
            return None

        # Update status
        task.status = status
        task.stage_progress = stage_progress
        task.updated_at = datetime.utcnow()

        # If status is complete, set completed_at
        if status == "complete":
            task.completed_at = datetime.utcnow()

            # If task has an assigned agent, set agent status to available
            if task.assigned_agent_id:
                agent_query = select(Agent).where(Agent.id == task.assigned_agent_id)
                agent_result = await self.db.execute(agent_query)
                agent = agent_result.scalars().first()

                if agent:
                    agent.status = "available"
                    agent.last_active = datetime.utcnow()

            # Send email notification
            await self.send_task_completion_email(task.id)

        # Create task update
        if task.assigned_agent_id:
            content = update_message or f"Task status updated to {status} with progress {stage_progress}%"
            task_update = TaskUpdate(
                id=str(uuid.uuid4()),
                task_id=task.id,
                agent_id=task.assigned_agent_id,
                update_type="status_change",
                content=content
            )

            self.db.add(task_update)

        await self.db.commit()
        await self.db.refresh(task)

        return task

    async def get_task_updates(
        self,
        task_id: str,
        limit: int = 20,
        offset: int = 0
    ) -> Optional[List[TaskUpdate]]:
        """
        Get updates for a task.
        """
        # Check if task exists
        task = await self.get_task(task_id)
        if not task:
            return None

        # Get updates
        query = select(TaskUpdate).where(TaskUpdate.task_id == task_id).order_by(
            TaskUpdate.timestamp.desc()
        ).offset(offset).limit(limit)

        result = await self.db.execute(query)
        updates = result.scalars().all()

        return updates

    async def create_task_update(
        self,
        task_id: str,
        update_type: str,
        content: str
    ) -> Optional[TaskUpdate]:
        """
        Create a new update for a task.
        """
        # Check if task exists
        task = await self.get_task(task_id)
        if not task:
            return None

        # Create update
        task_update = TaskUpdate(
            id=str(uuid.uuid4()),
            task_id=task_id,
            agent_id=task.assigned_agent_id or "system",
            update_type=update_type,
            content=content
        )

        self.db.add(task_update)
        await self.db.commit()
        await self.db.refresh(task_update)

        return task_update

    async def send_task_completion_email(self, task_id: str) -> bool:
        """
        Send an email notification when a task is completed.
        """
        # Get task details
        task = await self.get_task(task_id)
        if not task or task.status != "complete":
            return False

        # Get email configuration from environment variables
        smtp_server = os.getenv("SMTP_SERVER")
        smtp_port = int(os.getenv("SMTP_PORT", "587"))
        smtp_username = os.getenv("SMTP_USERNAME")
        smtp_password = os.getenv("SMTP_PASSWORD")
        sender_email = os.getenv("SENDER_EMAIL")
        recipient_email = os.getenv("RECIPIENT_EMAIL")

        # Check if email configuration is available
        if not all([smtp_server, smtp_port, smtp_username, smtp_password, sender_email, recipient_email]):
            print("Email configuration not complete. Skipping email notification.")
            return False

        try:
            # Create message
            message = MIMEMultipart()
            message["From"] = sender_email
            message["To"] = recipient_email
            message["Subject"] = f"Task Completed: {task.title}"

            # Create email body
            body = f"""
            <html>
            <body>
                <h2>Task Completed</h2>
                <p><strong>Title:</strong> {task.title}</p>
                <p><strong>Description:</strong> {task.description}</p>
                <p><strong>Completed at:</strong> {task.completed_at}</p>

                <p>You can download the task output by clicking the link below:</p>
                <p><a href="http://localhost:8001/api/v1/tasks/{task.id}/download">Download Task Output</a></p>

                <p>Or view the task details in the dashboard:</p>
                <p><a href="http://localhost:8001/api/v1/dashboard">Open Dashboard</a></p>
            </body>
            </html>
            """

            # Attach body to message
            message.attach(MIMEText(body, "html"))

            # Send email
            with smtplib.SMTP(smtp_server, smtp_port) as server:
                server.starttls()
                server.login(smtp_username, smtp_password)
                server.send_message(message)

            print(f"Task completion email sent for task {task_id}")
            return True

        except Exception as e:
            print(f"Error sending task completion email: {e}")
            return False
