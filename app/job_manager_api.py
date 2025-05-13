"""
API endpoints for the job manager UI
"""

import logging
import requests
import json
import os
from datetime import datetime
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from .database import get_db, Agent, Task, TaskUpdate

# Configure logging
logger = logging.getLogger("job-manager-api")

# Create router
router = APIRouter()

@router.get("/api/agents", response_model=List[Dict[str, Any]])
async def get_agents(db: AsyncSession = Depends(get_db)):
    """
    Get all agents

    Returns:
        List[Dict[str, Any]]: List of agents
    """
    try:
        # Get all agents
        query = select(Agent)
        result = await db.execute(query)
        agents = result.scalars().all()

        # Convert to dict
        agents_list = []
        for agent in agents:
            agent_dict = {
                "agent_id": agent.agent_id,
                "name": agent.name,
                "role": agent.role,
                "skills": agent.skills.split(",") if agent.skills else [],
                "model": agent.model,
                "status": agent.status,
                "agent_type": agent.agent_type,
                "current_workload": agent.current_workload,
                "max_workload": agent.max_workload
            }
            agents_list.append(agent_dict)

        return agents_list
    except Exception as e:
        logger.error(f"Error getting agents: {e}")
        raise HTTPException(status_code=500, detail=f"Error getting agents: {str(e)}")

@router.get("/api/projects", response_model=List[Dict[str, Any]])
async def get_projects(db: AsyncSession = Depends(get_db)):
    """
    Get all projects

    Returns:
        List[Dict[str, Any]]: List of projects
    """
    try:
        # Get all projects
        query = select(Task).where(Task.task_type == "project")
        result = await db.execute(query)
        projects = result.scalars().all()

        # Convert to dict
        projects_list = []
        for project in projects:
            project_dict = {
                "id": project.id,
                "title": project.title,
                "description": project.description,
                "status": project.status,
                "created_at": project.created_at.isoformat() if project.created_at else None,
                "updated_at": project.updated_at.isoformat() if project.updated_at else None,
                "required_skills": project.required_skills.split(",") if project.required_skills else [],
                "priority": project.priority,
                "assigned_to": project.assigned_to
            }
            projects_list.append(project_dict)

        return projects_list
    except Exception as e:
        logger.error(f"Error getting projects: {e}")
        raise HTTPException(status_code=500, detail=f"Error getting projects: {str(e)}")

@router.post("/api/projects", response_model=Dict[str, Any])
async def create_project(project_data: Dict[str, Any], db: AsyncSession = Depends(get_db)):
    """
    Create a new project

    Args:
        project_data: Project data

    Returns:
        Dict[str, Any]: Created project
    """
    try:
        # Forward the request to the projects API
        import requests

        # Use the same port as the current server
        port = os.environ.get("PORT", "8005")

        # The project API is mounted at /projects in main.py
        response = requests.post(
            f"http://localhost:{port}/projects",
            json=project_data,
            headers={"Content-Type": "application/json"}
        )

        if response.status_code != 200:
            raise HTTPException(status_code=response.status_code, detail=response.text)

        return response.json()
    except Exception as e:
        logger.error(f"Error creating project: {e}")
        raise HTTPException(status_code=500, detail=f"Error creating project: {str(e)}")

@router.get("/api/projects/{project_id}/tasks", response_model=List[Dict[str, Any]])
async def get_project_tasks(project_id: str, db: AsyncSession = Depends(get_db)):
    """
    Get all tasks for a project

    Args:
        project_id: Project ID

    Returns:
        List[Dict[str, Any]]: List of tasks
    """
    try:
        # First check if the project exists
        project_query = select(Task).where(
            Task.id == project_id,
            Task.task_type == "project"
        )
        project_result = await db.execute(project_query)
        project = project_result.scalars().first()

        if not project:
            logger.warning(f"Project {project_id} not found")
            raise HTTPException(status_code=404, detail=f"Project {project_id} not found")

        # Get all tasks for the project
        query = select(Task).where(Task.project_id == project_id)
        result = await db.execute(query)
        tasks = result.scalars().all()

        # Convert to dict
        tasks_list = []
        for task in tasks:
            task_dict = {
                "id": task.id,
                "title": task.title,
                "description": task.description,
                "status": task.status,
                "created_at": task.created_at.isoformat() if task.created_at else None,
                "updated_at": task.updated_at.isoformat() if task.updated_at else None,
                "required_skills": task.required_skills.split(",") if task.required_skills else [],
                "task_type": task.task_type,
                "assigned_to": task.assigned_to,
                "estimated_effort": task.estimated_effort,
                "progress": task.progress,
                "project_id": task.project_id,
                "priority": task.priority
            }
            tasks_list.append(task_dict)

        logger.info(f"Successfully retrieved {len(tasks_list)} tasks for project {project_id}")
        return tasks_list
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        logger.error(f"Error getting tasks for project {project_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Error getting tasks: {str(e)}")

@router.get("/api/tasks", response_model=List[Dict[str, Any]])
async def get_all_tasks(db: AsyncSession = Depends(get_db)):
    """
    Get all tasks

    Returns:
        List[Dict[str, Any]]: List of tasks
    """
    try:
        # Get all tasks
        query = select(Task).where(Task.task_type != "project")
        result = await db.execute(query)
        tasks = result.scalars().all()

        # Convert to dict
        tasks_list = []
        for task in tasks:
            task_dict = {
                "id": task.id,
                "title": task.title,
                "description": task.description,
                "status": task.status,
                "created_at": task.created_at.isoformat() if task.created_at else None,
                "updated_at": task.updated_at.isoformat() if task.updated_at else None,
                "required_skills": task.required_skills.split(",") if task.required_skills else [],
                "task_type": task.task_type,
                "assigned_to": task.assigned_to,
                "estimated_effort": task.estimated_effort,
                "progress": task.progress,
                "project_id": task.project_id,
                "has_result": task.result is not None and len(task.result) > 0
            }
            tasks_list.append(task_dict)

        return tasks_list
    except Exception as e:
        logger.error(f"Error getting all tasks: {e}")
        raise HTTPException(status_code=500, detail=f"Error getting tasks: {str(e)}")

@router.put("/api/agents/{agent_id}/config", response_model=Dict[str, Any])
async def update_agent_config(agent_id: str, config_data: Dict[str, Any], db: AsyncSession = Depends(get_db)):
    """
    Update agent configuration

    Args:
        agent_id: Agent ID
        config_data: Configuration data

    Returns:
        Dict[str, Any]: Updated agent
    """
    try:
        # Get agent
        query = select(Agent).where(Agent.agent_id == agent_id)
        result = await db.execute(query)
        agent = result.scalars().first()

        if not agent:
            raise HTTPException(status_code=404, detail=f"Agent {agent_id} not found")

        # Update agent configuration
        agent.model = config_data.get("model", agent.model)

        # Store the endpoint in the agent's performance_metrics JSON field
        # First, parse the existing performance_metrics
        try:
            performance_metrics = json.loads(agent.performance_metrics) if agent.performance_metrics else {}
        except:
            performance_metrics = {}

        # Update the endpoint
        performance_metrics["endpoint"] = config_data.get("endpoint", performance_metrics.get("endpoint", "localhost:11434"))

        # Save back to the agent
        agent.performance_metrics = json.dumps(performance_metrics)

        # Commit changes
        await db.commit()
        await db.refresh(agent)

        # Convert to dict
        agent_dict = {
            "agent_id": agent.agent_id,
            "name": agent.name,
            "role": agent.role,
            "skills": agent.skills.split(",") if agent.skills else [],
            "model": agent.model,
            "status": agent.status,
            "agent_type": agent.agent_type,
            "current_workload": agent.current_workload,
            "max_workload": agent.max_workload,
            "endpoint": performance_metrics.get("endpoint", "localhost:11434")
        }

        return agent_dict
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating agent configuration: {e}")
        raise HTTPException(status_code=500, detail=f"Error updating agent configuration: {str(e)}")

@router.post("/api/tasks/{task_id}/assign", response_model=Dict[str, Any])
async def assign_task(task_id: str, assign_data: Dict[str, Any], db: AsyncSession = Depends(get_db)):
    """
    Assign a task to a specific agent

    Args:
        task_id: Task ID
        assign_data: Assignment data with agent_id

    Returns:
        Dict[str, Any]: Updated task
    """
    try:
        # Get task
        query = select(Task).where(Task.id == task_id)
        result = await db.execute(query)
        task = result.scalars().first()

        if not task:
            raise HTTPException(status_code=404, detail=f"Task {task_id} not found")

        # Update task
        agent_id = assign_data.get("agent_id")

        # If agent_id is empty string, set to None (unassign)
        if agent_id == "":
            agent_id = None

        # Check if agent exists if agent_id is provided
        if agent_id:
            agent_query = select(Agent).where(Agent.agent_id == agent_id)
            agent_result = await db.execute(agent_query)
            agent = agent_result.scalars().first()

            if not agent:
                raise HTTPException(status_code=404, detail=f"Agent {agent_id} not found")

        # Update task
        task.assigned_to = agent_id

        # If task is pending and being assigned, set to in_progress
        if task.status == "pending" and agent_id:
            task.status = "in_progress"

        # If task is in_progress and being unassigned, set to pending
        if task.status == "in_progress" and not agent_id:
            task.status = "pending"

        # Update timestamp
        task.updated_at = datetime.utcnow()

        # Add task update
        task_update = TaskUpdate(
            task_id=task.id,
            agent_id=agent_id if agent_id else "system",
            content=f"Task assigned to {'agent ' + agent_id if agent_id else 'no agent'}"
        )
        db.add(task_update)

        # Commit changes
        await db.commit()
        await db.refresh(task)

        # Convert to dict
        task_dict = {
            "id": task.id,
            "title": task.title,
            "description": task.description,
            "status": task.status,
            "created_at": task.created_at.isoformat() if task.created_at else None,
            "updated_at": task.updated_at.isoformat() if task.updated_at else None,
            "assigned_to": task.assigned_to,
            "project_id": task.project_id,
            "task_type": task.task_type,
            "progress": task.progress,
            "priority": task.priority
        }

        return task_dict
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error assigning task: {e}")
        raise HTTPException(status_code=500, detail=f"Error assigning task: {str(e)}")

@router.post("/api/tasks/{task_id}/type", response_model=Dict[str, Any])
async def update_task_type(task_id: str, type_data: Dict[str, str], db: AsyncSession = Depends(get_db)):
    """
    Update a task's type

    Args:
        task_id: Task ID
        type_data: Type data with task_type

    Returns:
        Dict[str, Any]: Updated task
    """
    try:
        # Get task
        query = select(Task).where(Task.id == task_id)
        result = await db.execute(query)
        task = result.scalars().first()

        if not task:
            raise HTTPException(status_code=404, detail=f"Task {task_id} not found")

        # Update task type
        task.task_type = type_data.get("task_type")

        # Update timestamp
        task.updated_at = datetime.utcnow()

        # Add task update
        task_update = TaskUpdate(
            task_id=task.id,
            agent_id="system",
            content=f"Task type updated to {task.task_type}"
        )
        db.add(task_update)

        # Commit changes
        await db.commit()
        await db.refresh(task)

        # Convert to dict
        task_dict = {
            "id": task.id,
            "title": task.title,
            "description": task.description,
            "status": task.status,
            "created_at": task.created_at.isoformat() if task.created_at else None,
            "updated_at": task.updated_at.isoformat() if task.updated_at else None,
            "assigned_to": task.assigned_to,
            "project_id": task.project_id,
            "task_type": task.task_type,
            "progress": task.progress,
            "priority": task.priority
        }

        return task_dict
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating task type: {e}")
        raise HTTPException(status_code=500, detail=f"Error updating task type: {str(e)}")

@router.post("/api/tasks/{task_id}/prioritize", response_model=Dict[str, Any])
async def prioritize_task(task_id: str, db: AsyncSession = Depends(get_db)):
    """
    Prioritize a task

    Args:
        task_id: Task ID

    Returns:
        Dict[str, Any]: Updated task
    """
    try:
        # Get task
        query = select(Task).where(Task.id == task_id)
        result = await db.execute(query)
        task = result.scalars().first()

        if not task:
            raise HTTPException(status_code=404, detail=f"Task {task_id} not found")

        # Update task priority
        task.priority = 1  # Set to highest priority

        # Update timestamp
        task.updated_at = datetime.utcnow()

        # Add task update
        task_update = TaskUpdate(
            task_id=task.id,
            agent_id="system",
            content="Task prioritized to highest level"
        )
        db.add(task_update)

        # Commit changes
        await db.commit()
        await db.refresh(task)

        # Convert to dict
        task_dict = {
            "id": task.id,
            "title": task.title,
            "description": task.description,
            "status": task.status,
            "created_at": task.created_at.isoformat() if task.created_at else None,
            "updated_at": task.updated_at.isoformat() if task.updated_at else None,
            "assigned_to": task.assigned_to,
            "project_id": task.project_id,
            "task_type": task.task_type,
            "progress": task.progress,
            "priority": task.priority
        }

        return task_dict
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error prioritizing task: {e}")
        raise HTTPException(status_code=500, detail=f"Error prioritizing task: {str(e)}")

@router.delete("/api/tasks/{task_id}", response_model=Dict[str, Any])
async def delete_task(task_id: str, db: AsyncSession = Depends(get_db)):
    """
    Delete a task

    Args:
        task_id: Task ID

    Returns:
        Dict[str, Any]: Success message
    """
    try:
        # Get task
        query = select(Task).where(Task.id == task_id)
        result = await db.execute(query)
        task = result.scalars().first()

        if not task:
            raise HTTPException(status_code=404, detail=f"Task {task_id} not found")

        # Delete task
        await db.delete(task)

        # Commit changes
        await db.commit()

        return {"success": True, "message": f"Task {task_id} deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting task: {e}")
        raise HTTPException(status_code=500, detail=f"Error deleting task: {str(e)}")

@router.delete("/api/projects/{project_id}/tasks", response_model=Dict[str, Any])
async def delete_project_tasks(project_id: str, db: AsyncSession = Depends(get_db)):
    """
    Delete all tasks for a project

    Args:
        project_id: Project ID

    Returns:
        Dict[str, Any]: Success message with count of deleted tasks
    """
    try:
        # Get all tasks for the project
        query = select(Task).where(Task.project_id == project_id)
        result = await db.execute(query)
        tasks = result.scalars().all()

        if not tasks:
            return {"success": True, "message": "No tasks found for this project", "count": 0}

        # Count tasks
        task_count = len(tasks)

        # Delete all tasks
        for task in tasks:
            await db.delete(task)

        # Commit changes
        await db.commit()

        return {
            "success": True,
            "message": f"Successfully deleted {task_count} tasks for project {project_id}",
            "count": task_count
        }
    except Exception as e:
        logger.error(f"Error deleting project tasks: {e}")
        raise HTTPException(status_code=500, detail=f"Error deleting project tasks: {str(e)}")

@router.get("/api/tasks/{task_id}/result", response_model=Dict[str, Any])
async def get_task_result(task_id: str, db: AsyncSession = Depends(get_db)):
    """
    Get the result of a task

    Args:
        task_id: Task ID

    Returns:
        Dict[str, Any]: Task result
    """
    try:
        # Get the task
        query = select(Task).where(Task.id == task_id)
        result = await db.execute(query)
        task = result.scalars().first()

        if not task:
            raise HTTPException(status_code=404, detail=f"Task {task_id} not found")

        # Get task updates
        updates_query = select(TaskUpdate).where(TaskUpdate.task_id == task_id).order_by(TaskUpdate.timestamp)
        updates_result = await db.execute(updates_query)
        updates = updates_result.scalars().all()

        updates_list = []
        for update in updates:
            update_dict = {
                "id": update.id,
                "agent_id": update.agent_id,
                "content": update.content,
                "timestamp": update.timestamp.isoformat() if update.timestamp else None,
                "level": update.level
            }
            updates_list.append(update_dict)

        # Return task result and updates
        return {
            "id": task.id,
            "title": task.title,
            "status": task.status,
            "result": task.result or "",
            "updates": updates_list,
            "created_at": task.created_at.isoformat() if task.created_at else None,
            "updated_at": task.updated_at.isoformat() if task.updated_at else None,
            "completed_at": task.completed_at.isoformat() if task.completed_at else None,
            "progress": task.progress
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting task result: {e}")
        raise HTTPException(status_code=500, detail=f"Error getting task result: {str(e)}")
