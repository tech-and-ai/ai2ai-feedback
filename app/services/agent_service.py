"""
Agent service module.
"""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import update, func, and_
from typing import List, Optional, Tuple, Dict, Any
from datetime import datetime
import uuid
import os

from app.db.models import Agent, Tool, Task, AgentWorkspace
from app.api.models import AgentCreate, AgentUpdate, ToolCreate, ToolUpdate
from app.core.config import settings

class AgentService:
    """
    Service for agent management.
    """
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_agent(self, agent_data: AgentCreate) -> Agent:
        """
        Create a new agent.
        """
        # Create agent
        agent_id = str(uuid.uuid4())
        workspace_path = os.path.join(settings.AGENT_WORKSPACE_ROOT, agent_id)

        agent = Agent(
            id=agent_id,
            name=agent_data.name,
            model=agent_data.model,
            endpoint=agent_data.endpoint,
            status="available",
            min_complexity=agent_data.min_complexity,
            max_complexity=agent_data.max_complexity,
            workspace_path=workspace_path
        )

        self.db.add(agent)
        await self.db.commit()
        await self.db.refresh(agent)

        # Create agent workspace directory
        os.makedirs(workspace_path, exist_ok=True)
        os.makedirs(os.path.join(workspace_path, "global", "tools"), exist_ok=True)
        os.makedirs(os.path.join(workspace_path, "global", "references"), exist_ok=True)
        os.makedirs(os.path.join(workspace_path, "tasks"), exist_ok=True)

        return agent

    async def get_agent(self, agent_id: str) -> Optional[Agent]:
        """
        Get an agent by ID.
        """
        query = select(Agent).where(Agent.id == agent_id)
        result = await self.db.execute(query)
        return result.scalars().first()

    async def get_agent_with_details(self, agent_id: str) -> Optional[Dict[str, Any]]:
        """
        Get an agent with its current tasks and tools.
        """
        agent = await self.get_agent(agent_id)
        if not agent:
            return None

        # Get current tasks
        task_query = select(Task).where(
            Task.assigned_agent_id == agent_id,
            Task.status != "complete"
        ).order_by(Task.created_at.desc())

        task_result = await self.db.execute(task_query)
        current_tasks = task_result.scalars().all()

        # Get tools
        tool_query = select(Tool).join(
            Agent.tools
        ).where(Agent.id == agent_id)

        tool_result = await self.db.execute(tool_query)
        tools = tool_result.scalars().all()

        # Convert to dict
        agent_dict = {
            "id": agent.id,
            "name": agent.name,
            "model": agent.model,
            "endpoint": agent.endpoint,
            "status": agent.status,
            "min_complexity": agent.min_complexity,
            "max_complexity": agent.max_complexity,
            "workspace_path": agent.workspace_path,
            "created_at": agent.created_at,
            "last_active": agent.last_active,
            "current_tasks": current_tasks,
            "tools": tools
        }

        return agent_dict

    async def list_agents(
        self,
        status: Optional[str] = None,
        model: Optional[str] = None,
        limit: int = 20,
        offset: int = 0
    ) -> Tuple[List[Dict[str, Any]], int]:
        """
        List agents with optional filtering.
        """
        # Build query
        query = select(Agent)
        count_query = select(func.count()).select_from(Agent)

        # Apply filters
        if status:
            query = query.where(Agent.status == status)
            count_query = count_query.where(Agent.status == status)

        if model:
            query = query.where(Agent.model == model)
            count_query = count_query.where(Agent.model == model)

        # Apply pagination
        query = query.order_by(Agent.created_at.desc()).offset(offset).limit(limit)

        # Execute queries
        result = await self.db.execute(query)
        count_result = await self.db.execute(count_query)

        agents = result.scalars().all()
        total = count_result.scalar()

        # Get current tasks for busy agents
        agent_dicts = []
        for agent in agents:
            agent_dict = {
                "id": agent.id,
                "name": agent.name,
                "model": agent.model,
                "endpoint": agent.endpoint,
                "status": agent.status,
                "min_complexity": agent.min_complexity,
                "max_complexity": agent.max_complexity,
                "workspace_path": agent.workspace_path,
                "created_at": agent.created_at,
                "last_active": agent.last_active,
                "current_task": None
            }

            # If agent is busy, get the current task
            if agent.status == "busy":
                task_query = select(Task).where(
                    Task.assigned_agent_id == agent.id,
                    Task.status != "complete"
                ).order_by(Task.created_at.desc()).limit(1)

                task_result = await self.db.execute(task_query)
                current_task = task_result.scalars().first()

                if current_task:
                    agent_dict["current_task"] = {
                        "id": current_task.id,
                        "title": current_task.title,
                        "status": current_task.status,
                        "stage_progress": current_task.stage_progress,
                        "created_at": current_task.created_at,
                        "updated_at": current_task.updated_at
                    }

            agent_dicts.append(agent_dict)

        return agent_dicts, total

    async def update_agent(self, agent_id: str, agent_data: AgentUpdate) -> Optional[Agent]:
        """
        Update an agent.
        """
        agent = await self.get_agent(agent_id)
        if not agent:
            return None

        # Update fields
        if agent_data.name is not None:
            agent.name = agent_data.name

        if agent_data.model is not None:
            agent.model = agent_data.model

        if agent_data.endpoint is not None:
            agent.endpoint = agent_data.endpoint

        if agent_data.min_complexity is not None:
            agent.min_complexity = agent_data.min_complexity

        if agent_data.max_complexity is not None:
            agent.max_complexity = agent_data.max_complexity

        agent.last_active = datetime.utcnow()

        await self.db.commit()
        await self.db.refresh(agent)

        return agent

    async def update_agent_status(self, agent_id: str, status: str) -> Optional[Agent]:
        """
        Update the status of an agent.
        """
        agent = await self.get_agent(agent_id)
        if not agent:
            return None

        # Update status
        agent.status = status
        agent.last_active = datetime.utcnow()

        await self.db.commit()
        await self.db.refresh(agent)

        return agent

    async def get_agent_tasks(
        self,
        agent_id: str,
        status: Optional[str] = None,
        limit: int = 20,
        offset: int = 0
    ) -> Optional[List[Task]]:
        """
        Get tasks assigned to an agent.
        """
        # Check if agent exists
        agent = await self.get_agent(agent_id)
        if not agent:
            return None

        # Build query
        query = select(Task).where(Task.assigned_agent_id == agent_id)

        # Apply filters
        if status:
            query = query.where(Task.status == status)

        # Apply pagination
        query = query.order_by(Task.created_at.desc()).offset(offset).limit(limit)

        # Execute query
        result = await self.db.execute(query)
        tasks = result.scalars().all()

        return tasks

    async def create_tool(self, tool_data: ToolCreate) -> Tool:
        """
        Create a new tool.
        """
        # Create tool
        tool = Tool(
            id=str(uuid.uuid4()),
            name=tool_data.name,
            description=tool_data.description,
            type=tool_data.type,
            config=str(tool_data.config) if tool_data.config else None
        )

        self.db.add(tool)
        await self.db.commit()
        await self.db.refresh(tool)

        return tool

    async def get_tool(self, tool_id: str) -> Optional[Tool]:
        """
        Get a tool by ID.
        """
        query = select(Tool).where(Tool.id == tool_id)
        result = await self.db.execute(query)
        return result.scalars().first()

    async def list_tools(self, tool_type: Optional[str] = None) -> List[Tool]:
        """
        List tools with optional filtering.
        """
        # Build query
        query = select(Tool)

        # Apply filters
        if tool_type:
            query = query.where(Tool.type == tool_type)

        # Execute query
        result = await self.db.execute(query)
        tools = result.scalars().all()

        return tools

    async def update_tool(self, tool_id: str, tool_data: ToolUpdate) -> Optional[Tool]:
        """
        Update a tool.
        """
        tool = await self.get_tool(tool_id)
        if not tool:
            return None

        # Update fields
        if tool_data.name is not None:
            tool.name = tool_data.name

        if tool_data.description is not None:
            tool.description = tool_data.description

        if tool_data.type is not None:
            tool.type = tool_data.type

        if tool_data.config is not None:
            tool.config = str(tool_data.config)

        tool.updated_at = datetime.utcnow()

        await self.db.commit()
        await self.db.refresh(tool)

        return tool

    async def assign_tool_to_agent(
        self,
        agent_id: str,
        tool_id: str,
        permissions: str = "read"
    ) -> bool:
        """
        Assign a tool to an agent.
        """
        # Check if agent and tool exist
        agent = await self.get_agent(agent_id)
        tool = await self.get_tool(tool_id)

        if not agent or not tool:
            return False

        # Check if assignment already exists
        query = select(Agent).join(
            Agent.tools
        ).where(
            and_(Agent.id == agent_id, Tool.id == tool_id)
        )

        result = await self.db.execute(query)
        existing = result.scalars().first()

        if existing:
            # Update permissions
            await self.db.execute(
                update(Agent.tools.local_table).where(
                    and_(
                        Agent.tools.local_table.c.agent_id == agent_id,
                        Agent.tools.local_table.c.tool_id == tool_id
                    )
                ).values(permissions=permissions)
            )
        else:
            # Create new assignment
            stmt = Agent.tools.local_table.insert().values(
                agent_id=agent_id,
                tool_id=tool_id,
                permissions=permissions
            )
            await self.db.execute(stmt)

        await self.db.commit()

        return True
