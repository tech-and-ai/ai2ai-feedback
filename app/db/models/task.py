"""
Task database models.
"""
from sqlalchemy import Column, String, Integer, DateTime, ForeignKey, Text, Boolean
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid

from app.db.base import Base

class Task(Base):
    """
    Task model representing a task in the system.
    """
    __tablename__ = "tasks"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    title = Column(String, nullable=False)
    description = Column(Text, nullable=False)
    complexity = Column(Integer, nullable=False)
    status = Column(String, nullable=False, default="not_started")
    stage_progress = Column(Integer, nullable=False, default=0)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)
    assigned_agent_id = Column(String, ForeignKey("agents.id"), nullable=True)
    result_path = Column(String, nullable=True)
    priority = Column(Integer, nullable=False, default=5)

    # New fields
    research_likelihood = Column(String, nullable=True)  # Low, Medium, High
    allowed_tools = Column(Text, nullable=True)  # JSON list of tool IDs
    output_formats = Column(Text, nullable=True)  # JSON list of formats (zip, pdf, docx, jpg, etc.)
    max_token_usage = Column(Integer, nullable=True)
    allow_collaboration = Column(Boolean, nullable=False, default=False)
    max_collaborators = Column(Integer, nullable=True)
    human_review_required = Column(Boolean, nullable=False, default=True)
    deadline = Column(DateTime, nullable=True)

    # Relationships
    assigned_agent = relationship("Agent", back_populates="tasks")
    updates = relationship("TaskUpdate", back_populates="task", cascade="all, delete-orphan")
    workspace = relationship("AgentWorkspace", back_populates="task", uselist=False)

    def __repr__(self):
        return f"<Task {self.title} ({self.status})>"


class TaskUpdate(Base):
    """
    TaskUpdate model representing an update to a task.
    """
    __tablename__ = "task_updates"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    task_id = Column(String, ForeignKey("tasks.id"), nullable=False)
    agent_id = Column(String, ForeignKey("agents.id"), nullable=False)
    update_type = Column(String, nullable=False)
    content = Column(Text, nullable=False)
    timestamp = Column(DateTime, nullable=False, default=datetime.utcnow)

    # Relationships
    task = relationship("Task", back_populates="updates")
    agent = relationship("Agent", back_populates="task_updates")

    def __repr__(self):
        return f"<TaskUpdate {self.update_type} for {self.task_id}>"
