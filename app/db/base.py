"""
Database base module.
"""
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os

# Use SQLite database
DATABASE_URL = "sqlite+aiosqlite:///ai2ai_feedback.db"

# Create async engine
engine = create_async_engine(
    DATABASE_URL,
    echo=True,
    future=True,
)

# Create async session factory
async_session = sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False
)

# Create declarative base
Base = declarative_base()

# Dependency to get DB session
async def get_db():
    """
    Dependency for getting async DB session.
    """
    async with async_session() as session:
        try:
            yield session
        finally:
            await session.close()

# Initialize database
async def init_db():
    """
    Initialize database by creating all tables.
    """
    # Import models to ensure they are registered with Base
    from app.db.models import Agent, Tool, AgentWorkspace, Task, TaskUpdate, Session, Message

    # Create tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
