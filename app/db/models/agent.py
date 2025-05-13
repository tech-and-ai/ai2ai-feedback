"""
Agent database models.
"""
from sqlalchemy import Column, String, Integer, DateTime, ForeignKey, Table
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid

from app.db.base import Base

# Association table for agent-tool many-to-many relationship
agent_tools = Table(
    "agent_tools",
    Base.metadata,
    Column("agent_id", String, ForeignKey("agents.id"), primary_key=True),
    Column("tool_id", String, ForeignKey("tools.id"), primary_key=True),
    Column("permissions", String, nullable=False, default="read"),
)

class Agent(Base):
    """
    Agent model representing an AI agent in the system.
    """
    __tablename__ = "agents"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String, nullable=False)
    model = Column(String, nullable=False)
    endpoint = Column(String, nullable=False)
    status = Column(String, nullable=False, default="available")
    min_complexity = Column(Integer, nullable=False)
    max_complexity = Column(Integer, nullable=False)
    workspace_path = Column(String, nullable=False)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    last_active = Column(DateTime, nullable=False, default=datetime.utcnow)

    # Relationships
    tasks = relationship("Task", back_populates="assigned_agent")
    workspaces = relationship("AgentWorkspace", back_populates="agent")
    task_updates = relationship("TaskUpdate", back_populates="agent")
    tools = relationship("Tool", secondary=agent_tools, back_populates="agents")

    def __repr__(self):
        return f"<Agent {self.name} ({self.model})>"


class Tool(Base):
    """
    Tool model representing a tool available to agents.
    """
    __tablename__ = "tools"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String, nullable=False)
    description = Column(String, nullable=False)
    type = Column(String, nullable=False)
    config = Column(String, nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    # Relationships
    agents = relationship("Agent", secondary=agent_tools, back_populates="tools")

    def __repr__(self):
        return f"<Tool {self.name} ({self.type})>"


class AgentWorkspace(Base):
    """
    AgentWorkspace model representing a workspace for an agent-task pair.
    """
    __tablename__ = "agent_workspaces"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    agent_id = Column(String, ForeignKey("agents.id"), nullable=False)
    task_id = Column(String, ForeignKey("tasks.id"), nullable=False)
    workspace_path = Column(String, nullable=False)
    venv_path = Column(String, nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    last_accessed = Column(DateTime, nullable=False, default=datetime.utcnow)

    # Relationships
    agent = relationship("Agent", back_populates="workspaces")
    task = relationship("Task", back_populates="workspace")

    def __repr__(self):
        return f"<AgentWorkspace {self.agent_id} - {self.task_id}>"
