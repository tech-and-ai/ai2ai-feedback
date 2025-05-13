"""
Controller Agent for AI-to-AI Feedback API

This module implements a specialized controller agent that:
1. Breaks down projects into tasks
2. Assigns tasks to appropriate specialized agents
3. Monitors progress and handles blockers
4. Ensures integration of components
5. Delivers final results
"""

import os
import json
import logging
import asyncio
import re
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple, Set

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import or_, and_, func, desc, text

from .database import Task, Agent, TaskContext, TaskUpdate, async_session, get_db
from .providers.factory import get_model_provider
from .tools import FileOperations, ShellCommands
from .task_management import ContextScaffold

# Configure logging
logger = logging.getLogger("controller-agent")

class ControllerAgent:
    """
    Project Manager agent that allocates and coordinates tasks
    """

    def __init__(self, agent_id: str, name: str, role: str, model: str, endpoint: str = None):
        """
        Initialize a controller agent

        Args:
            agent_id: Agent ID
            name: Agent name
            role: Agent role
            model: AI model to use
            endpoint: Ollama endpoint URL
        """
        self.agent_id = agent_id
        self.name = name
        self.role = role
        self.model = model
        self.status = "idle"
        self.endpoint = endpoint
        self.provider = get_model_provider("ollama", self.model)

        # If endpoint is provided, update the provider's endpoint
        if self.endpoint:
            self.provider.endpoint = self.endpoint if self.endpoint.startswith("http") else f"http://{self.endpoint}"

        # Create workspace
        self.workspace = FileOperations.get_agent_workspace(agent_id, self.name, self.role)

    async def start(self):
        """Start the controller agent"""
        self.running = True
        self.status = "running"
        logger.info(f"Controller Agent {self.name} ({self.agent_id}) started")

        # Start the project monitoring loop
        asyncio.create_task(self._project_loop())
        return True

    async def stop(self):
        """Stop the controller agent"""
        self.running = False
        self.status = "stopped"
        logger.info(f"Controller Agent {self.name} ({self.agent_id}) stopped")
        return True

    async def _project_loop(self):
        """Monitor projects and coordinate tasks"""
        while self.running:
            try:
                # Get database session
                db_gen = get_db()
                db = await anext(db_gen)

                # Look for new projects without a plan
                await self._process_new_projects(db)

                # Check for completed tasks and handle next steps
                await self._process_completed_tasks(db)

                # Check for blocked tasks
                await self._process_blocked_tasks(db)

                # Check for completed projects
                await self._check_completed_projects(db)

                # Sleep before next check
                await asyncio.sleep(30)
            except Exception as e:
                logger.error(f"Error in controller loop: {e}")
                await asyncio.sleep(30)

    async def _process_new_projects(self, db: AsyncSession):
        """Process new projects by delegating to a designer"""
        try:
            # Find projects assigned to the controller
            query = select(Task).where(
                Task.status == "in_progress",
                Task.assigned_to == self.agent_id,
                Task.task_type == "project"
            )

            result = await db.execute(query)
            projects = result.scalars().all()

            for project in projects:
                # Check if this project already has a design task
                subquery = select(Task).where(
                    Task.project_id == project.id,
                    Task.task_type == "design"
                )
                subresult = await db.execute(subquery)
                existing_design_tasks = subresult.scalars().all()

                if not existing_design_tasks:
                    # Create a design task and assign it to a designer
                    logger.info(f"Creating design task for project: {project.id} - {project.title}")

                    # Create a design task
                    design_task = Task(
                        id=str(uuid.uuid4()),
                        title=f"Design for {project.title}",
                        description=f"Analyze requirements and create design specifications for: {project.description}",
                        status="pending",
                        created_by=self.agent_id,
                        project_id=project.id,
                        task_type="design",
                        required_skills="design,requirements,analysis,architecture",
                        priority=project.priority,
                        estimated_effort=8
                    )
                    db.add(design_task)
                    await db.commit()

                    # Assign the design task to a designer
                    await self._assign_task(db, design_task)

                    # Add update about task creation
                    await ContextScaffold.add_task_update(
                        db,
                        project.id,
                        self.agent_id,
                        f"Created design task and assigned it to a designer. The design phase has begun."
                    )
        except Exception as e:
            logger.error(f"Error processing new projects: {e}")

    async def _create_project_plan(self, db: AsyncSession, project: Task):
        """Create a plan for a project following Design-Build-Test methodology"""
        try:
            # Create a plan following proper software engineering practices
            plan = {
                "tasks": [
                    # PHASE 1: REQUIREMENTS & DESIGN
                    {
                        "title": "Requirements Analysis",
                        "description": f"Analyze and document requirements for {project.title}",
                        "required_skills": ["requirements", "analysis", "design"],
                        "task_type": "design",
                        "dependencies": [],
                        "estimated_effort": 4
                    },
                    {
                        "title": "Architecture Design",
                        "description": f"Create high-level architecture design for {project.title}",
                        "required_skills": ["architecture", "design"],
                        "task_type": "design",
                        "dependencies": ["Requirements Analysis"],
                        "estimated_effort": 4
                    },
                    {
                        "title": "Database Schema Design",
                        "description": f"Design the database schema for {project.title}",
                        "required_skills": ["database", "design"],
                        "task_type": "design",
                        "dependencies": ["Architecture Design"],
                        "estimated_effort": 3
                    },
                    {
                        "title": "API Design",
                        "description": f"Design the API interfaces for {project.title}",
                        "required_skills": ["api", "design"],
                        "task_type": "design",
                        "dependencies": ["Architecture Design"],
                        "estimated_effort": 3
                    },
                    {
                        "title": "UI/UX Design",
                        "description": f"Create UI/UX mockups and user flows for {project.title}",
                        "required_skills": ["ui", "ux", "design"],
                        "task_type": "design",
                        "dependencies": ["Requirements Analysis"],
                        "estimated_effort": 4
                    },
                    {
                        "title": "Test Plan Design",
                        "description": f"Create test plan and test cases for {project.title}",
                        "required_skills": ["testing", "quality", "design"],
                        "task_type": "design",
                        "dependencies": ["Architecture Design", "API Design", "UI/UX Design"],
                        "estimated_effort": 3
                    },

                    # PHASE 2: IMPLEMENTATION
                    {
                        "title": "Backend Implementation",
                        "description": f"Implement the backend services for {project.title} based on the design",
                        "required_skills": ["python", "backend", "development"],
                        "task_type": "development",
                        "dependencies": ["Database Schema Design", "API Design"],
                        "estimated_effort": 8
                    },
                    {
                        "title": "Frontend Implementation",
                        "description": f"Implement the frontend UI for {project.title} based on the UI/UX design",
                        "required_skills": ["javascript", "frontend", "development"],
                        "task_type": "development",
                        "dependencies": ["UI/UX Design", "API Design"],
                        "estimated_effort": 8
                    },
                    {
                        "title": "Integration Implementation",
                        "description": f"Integrate frontend and backend components for {project.title}",
                        "required_skills": ["integration", "fullstack", "development"],
                        "task_type": "development",
                        "dependencies": ["Backend Implementation", "Frontend Implementation"],
                        "estimated_effort": 5
                    },

                    # PHASE 3: TESTING
                    {
                        "title": "Unit Testing",
                        "description": f"Implement and execute unit tests for {project.title}",
                        "required_skills": ["testing", "quality", "python"],
                        "task_type": "testing",
                        "dependencies": ["Backend Implementation", "Frontend Implementation", "Test Plan Design"],
                        "estimated_effort": 5
                    },
                    {
                        "title": "Integration Testing",
                        "description": f"Execute integration tests for {project.title}",
                        "required_skills": ["testing", "integration", "quality"],
                        "task_type": "testing",
                        "dependencies": ["Integration Implementation", "Test Plan Design"],
                        "estimated_effort": 4
                    },
                    {
                        "title": "User Acceptance Testing",
                        "description": f"Conduct user acceptance testing for {project.title}",
                        "required_skills": ["testing", "quality", "ux"],
                        "task_type": "testing",
                        "dependencies": ["Integration Testing"],
                        "estimated_effort": 3
                    },

                    # PHASE 4: DOCUMENTATION & DELIVERY
                    {
                        "title": "Technical Documentation",
                        "description": f"Create technical documentation for {project.title}",
                        "required_skills": ["documentation", "technical", "writing"],
                        "task_type": "documentation",
                        "dependencies": ["Integration Implementation"],
                        "estimated_effort": 4
                    },
                    {
                        "title": "User Documentation",
                        "description": f"Create user documentation and guides for {project.title}",
                        "required_skills": ["documentation", "writing", "ux"],
                        "task_type": "documentation",
                        "dependencies": ["Integration Implementation"],
                        "estimated_effort": 3
                    },
                    {
                        "title": "Deployment Planning",
                        "description": f"Create deployment plan for {project.title}",
                        "required_skills": ["deployment", "operations", "devops"],
                        "task_type": "deployment",
                        "dependencies": ["User Acceptance Testing"],
                        "estimated_effort": 2
                    }
                ]
            }

            # Create tasks based on the plan
            await self._create_tasks_from_plan(db, project, plan)

            # Add update about plan creation
            await ContextScaffold.add_task_update(
                db,
                project.id,
                self.agent_id,
                f"Created project plan with {len(plan['tasks'])} tasks"
            )

            logger.info(f"Created plan for project {project.id} with {len(plan['tasks'])} tasks")
        except Exception as e:
            logger.error(f"Error creating project plan: {e}")
            await ContextScaffold.add_task_update(
                db,
                project.id,
                self.agent_id,
                f"Error creating project plan: {str(e)}"
            )

    async def _create_tasks_from_plan(self, db: AsyncSession, project: Task, plan: Dict[str, Any]):
        """Create tasks based on the project plan"""
        try:
            # Track task IDs for dependency mapping
            task_ids = {}

            # First pass: Create all tasks
            for task_data in plan["tasks"]:
                # Generate a unique ID for the task
                task_id = str(uuid.uuid4())

                task = Task(
                    id=task_id,  # Set the ID explicitly
                    title=task_data["title"],
                    description=task_data["description"],
                    status="pending",
                    created_by=self.agent_id,
                    project_id=project.id,
                    task_type=task_data["task_type"],
                    required_skills=",".join(task_data["required_skills"]),  # Convert list to comma-separated string
                    estimated_effort=task_data["estimated_effort"],
                    dependencies="[]"  # Will update in second pass
                )
                db.add(task)
                await db.flush()

                # Store the task ID for dependency mapping
                task_ids[task_data["title"]] = task.id

            # Second pass: Update dependencies
            for task_data in plan["tasks"]:
                if task_data.get("dependencies"):
                    # Get the task
                    task_id = task_ids[task_data["title"]]
                    stmt = select(Task).where(Task.id == task_id)
                    result = await db.execute(stmt)
                    task = result.scalars().first()

                    if task:
                        # Update dependencies
                        task.dependencies = json.dumps([
                            task_ids[dep_title]
                            for dep_title in task_data["dependencies"]
                            if dep_title in task_ids
                        ])

            await db.commit()

            # Assign tasks that have no dependencies
            for task_id, task_title in task_ids.items():
                stmt = select(Task).where(Task.id == task_id)
                result = await db.execute(stmt)
                task = result.scalars().first()

                if task and (not task.dependencies or task.dependencies == '[]'):
                    await self._assign_task(db, task)
        except Exception as e:
            logger.error(f"Error creating tasks from plan: {e}")
            await db.rollback()
            raise

    async def _process_completed_tasks(self, db: AsyncSession):
        """Process completed tasks and assign next tasks"""
        try:
            # Find completed tasks
            query = select(Task).where(
                Task.status == "completed",
                Task.project_id != None
            )

            result = await db.execute(query)
            completed_tasks = result.scalars().all()

            for task in completed_tasks:
                # Get all pending tasks for this project
                query = select(Task).where(
                    Task.project_id == task.project_id,
                    Task.status == "pending"
                )

                result = await db.execute(query)
                pending_tasks = result.scalars().all()

                for pending_task in pending_tasks:
                    # Skip tasks without dependencies
                    if not pending_task.dependencies or pending_task.dependencies == '[]':
                        continue

                    # Check if this task depends on the completed task
                    try:
                        dependencies = json.loads(pending_task.dependencies)
                        if task.id not in dependencies:
                            continue

                        # Check if all dependencies are completed
                        all_deps_completed = True
                        for dep_id in dependencies:
                            stmt = select(Task).where(Task.id == dep_id)
                            result = await db.execute(stmt)
                            dep = result.scalars().first()
                            if dep and dep.status != "completed":
                                all_deps_completed = False
                                break

                        if all_deps_completed:
                            # Assign the task to an appropriate agent
                            await self._assign_task(db, pending_task)
                    except json.JSONDecodeError:
                        logger.error(f"Invalid dependencies JSON for task {pending_task.id}: {pending_task.dependencies}")
                        continue

                # Mark this task as processed
                task.status = "archived"

            await db.commit()
        except Exception as e:
            logger.error(f"Error processing completed tasks: {e}")

    async def _assign_task(self, db: AsyncSession, task: Task):
        """Assign a task to an appropriate agent based on role-specific model requirements"""
        try:
            # Get required skills as a list
            required_skills = task.required_skills.split(",") if task.required_skills else []

            # Determine the required model based on task type
            required_model = None
            if task.task_type == "design":
                # Designer/Architect tasks require Gemma 3 4B
                required_model = "gemma3:4b"
            elif task.task_type == "development":
                # Development tasks require DeepSeek Coder v2
                required_model = "deepseek-coder-v2:16b"
            elif task.task_type == "testing":
                # Testing tasks require DeepSeek Coder v2
                required_model = "deepseek-coder-v2:16b"
            elif task.task_type == "review":
                # Review tasks require Gemma 3 4B
                required_model = "gemma3:4b"
            elif task.task_type == "documentation":
                # Documentation tasks require Gemma 3 1B
                required_model = "gemma3:1b"

            # Find available agents with matching skills and the required model
            query = select(Agent).where(
                Agent.status == "running",
                Agent.current_workload < Agent.max_workload,
                Agent.agent_type == "worker"
            )

            if required_model:
                query = query.where(Agent.model == required_model)

            result = await db.execute(query)
            agents = result.scalars().all()

            if agents:
                # Select the best agent based on skill match and workload
                best_agent = None
                best_score = -1

                for agent in agents:
                    # Get agent skills as a list
                    agent_skills = agent.skills.split(",") if agent.skills else []

                    # Calculate skill match score
                    skill_match = sum(1 for skill in required_skills if skill in agent_skills)
                    skill_score = skill_match / len(required_skills) if required_skills else 0

                    # Calculate workload score (lower is better)
                    workload_score = 1 - (agent.current_workload / agent.max_workload)

                    # Combined score
                    score = (skill_score * 0.7) + (workload_score * 0.3)

                    if score > best_score:
                        best_score = score
                        best_agent = agent

                if best_agent:
                    # Assign the task
                    task.assigned_to = best_agent.agent_id
                    task.status = "in_progress"

                    # Update agent workload
                    best_agent.current_workload += 1

                    await db.commit()

                    # Add update about assignment
                    await ContextScaffold.add_task_update(
                        db,
                        task.id,
                        self.agent_id,
                        f"Task assigned to agent {best_agent.name} ({best_agent.agent_id})"
                    )

                    logger.info(f"Assigned task {task.id} to agent {best_agent.agent_id}")
                    return True

            # No suitable agent found
            await ContextScaffold.add_task_update(
                db,
                task.id,
                self.agent_id,
                "No suitable agent found for this task"
            )
            logger.warning(f"No suitable agent found for task {task.id}")
            return False
        except Exception as e:
            logger.error(f"Error assigning task: {e}")
            return False

    async def _process_blocked_tasks(self, db: AsyncSession):
        """Check for blocked tasks and try to resolve issues"""
        try:
            # Find tasks that have been in progress for too long
            one_hour_ago = datetime.utcnow() - timedelta(hours=1)
            query = select(Task).where(
                Task.status == "in_progress",
                Task.updated_at < one_hour_ago
            )

            result = await db.execute(query)
            blocked_tasks = result.scalars().all()

            for task in blocked_tasks:
                # Check if the assigned agent is still active
                query = select(Agent).where(Agent.agent_id == task.assigned_to)
                result = await db.execute(query)
                agent = result.scalars().first()

                if not agent or agent.status != "running":
                    # Agent is no longer available, reassign the task
                    task.status = "pending"
                    task.assigned_to = None

                    await ContextScaffold.add_task_update(
                        db,
                        task.id,
                        self.agent_id,
                        f"Task reassigned because agent {task.assigned_to} is no longer available"
                    )

                    logger.info(f"Reassigned task {task.id} because agent {task.assigned_to} is no longer available")
                else:
                    # Agent is still active but task might be blocked
                    await ContextScaffold.add_task_update(
                        db,
                        task.id,
                        self.agent_id,
                        "Task appears to be blocked. Please provide an update on your progress."
                    )

                    logger.info(f"Task {task.id} appears to be blocked")

            await db.commit()
        except Exception as e:
            logger.error(f"Error processing blocked tasks: {e}")

    async def _check_completed_projects(self, db: AsyncSession):
        """Check for projects that have all tasks completed"""
        try:
            # Find in-progress projects assigned to the controller
            query = select(Task).where(
                Task.status == "in_progress",
                Task.assigned_to == self.agent_id,
                Task.task_type == "project"
            )

            result = await db.execute(query)
            projects = result.scalars().all()

            for project in projects:
                # Get all tasks for this project
                query = select(Task).where(
                    Task.project_id == project.id,
                    Task.task_type != "project"  # Exclude the project task itself
                )

                result = await db.execute(query)
                tasks = result.scalars().all()

                if not tasks:
                    # No tasks found, project might be new
                    continue

                # Check if all tasks are completed or archived
                all_completed = True
                for task in tasks:
                    if task.status not in ["completed", "archived"]:
                        all_completed = False
                        break

                if all_completed:
                    # All tasks are completed, mark the project as completed
                    project.status = "completed"
                    project.completed_at = datetime.utcnow()

                    # Add update about project completion
                    await ContextScaffold.add_task_update(
                        db,
                        project.id,
                        self.agent_id,
                        f"Project {project.title} has been completed successfully. All tasks have been completed."
                    )

                    logger.info(f"Project {project.id} - {project.title} has been completed")

            await db.commit()
        except Exception as e:
            logger.error(f"Error checking completed projects: {e}")
