"""
Database module for AI-to-AI Feedback API

This module handles database operations for the AI-to-AI Feedback API,
including session management, message storage, and feedback storage.
"""

import os
from datetime import datetime
from typing import List, Optional, Dict, Any

from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, ForeignKey, Boolean, Float
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship, backref
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy.future import select

from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Get database URL from environment variables
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./ai2ai_feedback.db")
# Convert to async URL for SQLite
if DATABASE_URL.startswith("sqlite:///"):
    DATABASE_URL = DATABASE_URL.replace("sqlite:///", "sqlite+aiosqlite:///")

# Create async engine
engine = create_async_engine(DATABASE_URL, echo=os.getenv("DEBUG", "False").lower() == "true")

# Create async session
async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

# Create base class for models
Base = declarative_base()

class Session(Base):
    """Session model for storing conversation sessions"""
    __tablename__ = "sessions"

    id = Column(String, primary_key=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_accessed_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    system_prompt = Column(Text, nullable=True)
    title = Column(String, nullable=True)
    tags = Column(String, nullable=True)
    is_multi_agent = Column(Boolean, default=False)  # Flag for multi-agent sessions

    # Relationships
    messages = relationship("Message", back_populates="session", cascade="all, delete-orphan")
    agents = relationship("Agent", back_populates="session", cascade="all, delete-orphan")
    tasks = relationship("Task", back_populates="session", cascade="all, delete-orphan")

class Agent(Base):
    """Agent model for storing information about AI agents in a multi-agent session"""
    __tablename__ = "agents"

    id = Column(Integer, primary_key=True)
    session_id = Column(String, ForeignKey("sessions.id", ondelete="CASCADE"))
    agent_index = Column(Integer, nullable=False)  # 0-based index
    name = Column(String, nullable=True)
    role = Column(String, nullable=True)
    model = Column(String, nullable=True)

    # Relationships
    session = relationship("Session", back_populates="agents")
    messages = relationship("Message", back_populates="agent")

class Message(Base):
    """Message model for storing conversation messages"""
    __tablename__ = "messages"

    id = Column(Integer, primary_key=True)
    session_id = Column(String, ForeignKey("sessions.id", ondelete="CASCADE"))
    agent_id = Column(Integer, ForeignKey("agents.id", ondelete="CASCADE"), nullable=True)
    role = Column(String, nullable=False)  # system, user, assistant, agent
    content = Column(Text, nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow)
    initiator = Column(String, nullable=True)  # For multi-agent: user or agent index

    # Relationships
    session = relationship("Session", back_populates="messages")
    agent = relationship("Agent", back_populates="messages")
    feedback = relationship("Feedback", back_populates="message", cascade="all, delete-orphan")

class Feedback(Base):
    """Feedback model for storing structured feedback"""
    __tablename__ = "feedback"

    id = Column(Integer, primary_key=True)
    message_id = Column(Integer, ForeignKey("messages.id", ondelete="CASCADE"))
    feedback_text = Column(Text, nullable=False)
    feedback_summary = Column(Text, nullable=True)
    reasoning_assessment = Column(Text, nullable=True)
    knowledge_gaps = Column(Text, nullable=True)
    suggested_approach = Column(Text, nullable=True)
    additional_considerations = Column(Text, nullable=True)
    source_model = Column(String, nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow)

    # Relationships
    message = relationship("Message", back_populates="feedback")

class Memory(Base):
    """Memory model for storing agent memories"""
    __tablename__ = "memories"

    id = Column(Integer, primary_key=True)
    content = Column(Text, nullable=False)
    embedding = Column(Text, nullable=True)  # JSON string of embedding vector
    timestamp = Column(DateTime, default=datetime.utcnow)
    source = Column(String, nullable=True)
    importance = Column(Float, default=0.5)
    tags = Column(String, nullable=True)

class CodeSnippet(Base):
    """Code snippet model for storing reusable code snippets"""
    __tablename__ = "code_snippets"

    id = Column(Integer, primary_key=True)
    title = Column(String, nullable=False)
    language = Column(String, nullable=False)
    code = Column(Text, nullable=False)
    description = Column(Text, nullable=True)
    embedding = Column(Text, nullable=True)  # JSON string of embedding vector
    created_at = Column(DateTime, default=datetime.utcnow)
    last_used = Column(DateTime, default=datetime.utcnow)
    usage_count = Column(Integer, default=0)
    tags = Column(String, nullable=True)

class Reference(Base):
    """Reference model for storing external references and documentation"""
    __tablename__ = "references"

    id = Column(Integer, primary_key=True)
    title = Column(String, nullable=False)
    content = Column(Text, nullable=False)
    url = Column(String, nullable=True)
    embedding = Column(Text, nullable=True)  # JSON string of embedding vector
    created_at = Column(DateTime, default=datetime.utcnow)
    last_accessed = Column(DateTime, default=datetime.utcnow)
    access_count = Column(Integer, default=0)
    tags = Column(String, nullable=True)

class Task(Base):
    """Task model for storing delegated tasks"""
    __tablename__ = "tasks"

    id = Column(String, primary_key=True)
    title = Column(String, nullable=False)
    description = Column(Text, nullable=False)
    status = Column(String, nullable=False)  # "pending", "in_progress", "completed", "failed"
    created_by = Column(String, nullable=False)  # Agent ID or "user"
    assigned_to = Column(String, nullable=True)  # Agent ID
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)
    result = Column(Text, nullable=True)
    parent_task_id = Column(String, ForeignKey("tasks.id", ondelete="CASCADE"), nullable=True)
    session_id = Column(String, ForeignKey("sessions.id", ondelete="CASCADE"), nullable=True)

    # Relationships
    subtasks = relationship("Task", backref=backref("parent", remote_side=[id]))
    session = relationship("Session", back_populates="tasks")
    context_entries = relationship("TaskContext", back_populates="task", cascade="all, delete-orphan")
    updates = relationship("TaskUpdate", back_populates="task", cascade="all, delete-orphan")

class TaskContext(Base):
    """Model for storing context information for tasks"""
    __tablename__ = "task_contexts"

    id = Column(Integer, primary_key=True)
    task_id = Column(String, ForeignKey("tasks.id", ondelete="CASCADE"))
    key = Column(String, nullable=False)  # Context key (e.g., "research_findings", "code_snippet")
    value = Column(Text, nullable=False)  # Context value
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    task = relationship("Task", back_populates="context_entries")

class TaskUpdate(Base):
    """Model for storing task progress updates"""
    __tablename__ = "task_updates"

    id = Column(Integer, primary_key=True)
    task_id = Column(String, ForeignKey("tasks.id", ondelete="CASCADE"))
    agent_id = Column(String, nullable=False)  # Agent that provided the update
    content = Column(Text, nullable=False)  # Update content
    timestamp = Column(DateTime, default=datetime.utcnow)

    # Relationships
    task = relationship("Task", back_populates="updates")

# Database initialization
async def init_db():
    """Initialize the database"""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

# Database session context manager
async def get_db():
    """Get database session"""
    async with async_session() as session:
        try:
            yield session
        finally:
            await session.close()

# Session management functions
async def create_session(db: AsyncSession, session_id: str, system_prompt: Optional[str] = None,
                         title: Optional[str] = None, tags: Optional[List[str]] = None) -> bool:
    """
    Create a new session

    Args:
        db: Database session
        session_id: Session ID
        system_prompt: Optional system prompt
        title: Optional title
        tags: Optional list of tags

    Returns:
        bool: True if successful
    """
    try:
        tags_str = ",".join(tags) if tags else ""

        session = Session(
            id=session_id,
            system_prompt=system_prompt,
            title=title,
            tags=tags_str
        )

        db.add(session)
        await db.commit()

        return True
    except Exception as e:
        await db.rollback()
        print(f"Error creating session: {e}")
        return False

async def get_session(db: AsyncSession, session_id: str) -> Optional[Dict[str, Any]]:
    """
    Get a session by ID

    Args:
        db: Database session
        session_id: Session ID

    Returns:
        Optional[Dict]: Session data or None if not found
    """
    try:
        # Update last accessed time
        stmt = select(Session).where(Session.id == session_id)
        result = await db.execute(stmt)
        session = result.scalars().first()

        if not session:
            return None

        # Update last accessed time
        session.last_accessed_at = datetime.utcnow()
        await db.commit()

        # Get messages for this session
        stmt = select(Message).where(Message.session_id == session_id).order_by(Message.timestamp)
        result = await db.execute(stmt)
        messages = result.scalars().all()

        # Convert to dict
        session_dict = {
            "id": session.id,
            "created_at": session.created_at,
            "last_accessed_at": session.last_accessed_at,
            "system_prompt": session.system_prompt,
            "title": session.title,
            "tags": session.tags,
            "history": [
                {
                    "id": message.id,
                    "role": message.role,
                    "content": message.content,
                    "timestamp": message.timestamp
                }
                for message in messages
            ]
        }

        return session_dict
    except Exception as e:
        print(f"Error getting session: {e}")
        return None

async def add_message(db: AsyncSession, session_id: str, role: str, content: str) -> Optional[int]:
    """
    Add a message to a session

    Args:
        db: Database session
        session_id: Session ID
        role: Message role (system, user, assistant)
        content: Message content

    Returns:
        Optional[int]: Message ID or None if failed
    """
    try:
        # Check if session exists
        stmt = select(Session).where(Session.id == session_id)
        result = await db.execute(stmt)
        session = result.scalars().first()

        if not session:
            return None

        # Update last accessed time
        session.last_accessed_at = datetime.utcnow()

        # Create message
        message = Message(
            session_id=session_id,
            role=role,
            content=content
        )

        db.add(message)
        await db.commit()
        await db.refresh(message)

        return message.id
    except Exception as e:
        await db.rollback()
        print(f"Error adding message: {e}")
        return None

async def add_feedback(db: AsyncSession, message_id: int, feedback_text: str,
                      structured: Dict[str, str], source_model: str) -> Optional[int]:
    """
    Add feedback for a message

    Args:
        db: Database session
        message_id: Message ID
        feedback_text: Full feedback text
        structured: Structured feedback components
        source_model: Source model

    Returns:
        Optional[int]: Feedback ID or None if failed
    """
    try:
        # Check if message exists
        stmt = select(Message).where(Message.id == message_id)
        result = await db.execute(stmt)
        message = result.scalars().first()

        if not message:
            return None

        # Create feedback
        feedback = Feedback(
            message_id=message_id,
            feedback_text=feedback_text,
            feedback_summary=structured.get("FEEDBACK_SUMMARY", ""),
            reasoning_assessment=structured.get("REASONING_ASSESSMENT", ""),
            knowledge_gaps=structured.get("KNOWLEDGE_GAPS", ""),
            suggested_approach=structured.get("SUGGESTED_APPROACH", ""),
            additional_considerations=structured.get("ADDITIONAL_CONSIDERATIONS", ""),
            source_model=source_model
        )

        db.add(feedback)
        await db.commit()
        await db.refresh(feedback)

        return feedback.id
    except Exception as e:
        await db.rollback()
        print(f"Error adding feedback: {e}")
        return None

async def cleanup_old_sessions(db: AsyncSession, hours: int = 24) -> int:
    """
    Clean up sessions that haven't been accessed in the specified number of hours

    Args:
        db: Database session
        hours: Number of hours of inactivity before cleanup

    Returns:
        int: Number of sessions cleaned up
    """
    try:
        # Find sessions to clean up
        cutoff_time = datetime.utcnow() - datetime.timedelta(hours=hours)
        stmt = select(Session).where(Session.last_accessed_at < cutoff_time)
        result = await db.execute(stmt)
        old_sessions = result.scalars().all()

        if not old_sessions:
            return 0

        # Delete sessions
        for session in old_sessions:
            await db.delete(session)

        await db.commit()

        return len(old_sessions)
    except Exception as e:
        await db.rollback()
        print(f"Error cleaning up sessions: {e}")
        return 0
