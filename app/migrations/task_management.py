"""
Database migrations for task management system
"""

from sqlalchemy import Column, String, Text, DateTime, ForeignKey, Boolean, Integer, Float, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, backref
from datetime import datetime

Base = declarative_base()

# Create schema if it doesn't exist
async def create_schema(engine):
    """Create the ai_agent_system schema if it doesn't exist"""
    async with engine.begin() as conn:
        await conn.execute(text("""
        CREATE SCHEMA IF NOT EXISTS ai_agent_system
        """))

# Add is_multi_agent column to Session table
async def upgrade_session_table(engine):
    """Add is_multi_agent column to Session table"""
    async with engine.begin() as conn:
        # Check if is_multi_agent column exists
        result = await conn.execute(text("""
        SELECT column_name
        FROM information_schema.columns
        WHERE table_schema = 'ai_agent_system'
        AND table_name = 'sessions'
        AND column_name = 'is_multi_agent'
        """))
        column_exists = result.fetchone() is not None

        if not column_exists:
            await conn.execute(text("""
            ALTER TABLE ai_agent_system.sessions
            ADD COLUMN is_multi_agent BOOLEAN DEFAULT FALSE
            """))

# Create Agent table
async def create_agent_table(engine):
    """Create Agent table"""
    async with engine.begin() as conn:
        await conn.execute(text("""
        CREATE TABLE IF NOT EXISTS ai_agent_system.agents (
            id SERIAL PRIMARY KEY,
            session_id VARCHAR NOT NULL,
            agent_index INTEGER NOT NULL,
            name VARCHAR,
            role VARCHAR,
            model VARCHAR,
            FOREIGN KEY (session_id) REFERENCES ai_agent_system.sessions(id) ON DELETE CASCADE
        )
        """))

# Update Message table
async def update_message_table(engine):
    """Update Message table to support agents"""
    async with engine.begin() as conn:
        # Check if agent_id column exists
        result = await conn.execute(text("""
        SELECT column_name
        FROM information_schema.columns
        WHERE table_schema = 'ai_agent_system'
        AND table_name = 'messages'
        AND column_name = 'agent_id'
        """))
        agent_id_exists = result.fetchone() is not None

        if not agent_id_exists:
            await conn.execute(text("""
            ALTER TABLE ai_agent_system.messages
            ADD COLUMN agent_id INTEGER REFERENCES ai_agent_system.agents(id) ON DELETE CASCADE
            """))

        # Check if initiator column exists
        result = await conn.execute(text("""
        SELECT column_name
        FROM information_schema.columns
        WHERE table_schema = 'ai_agent_system'
        AND table_name = 'messages'
        AND column_name = 'initiator'
        """))
        initiator_exists = result.fetchone() is not None

        if not initiator_exists:
            await conn.execute(text("""
            ALTER TABLE ai_agent_system.messages
            ADD COLUMN initiator VARCHAR
            """))

# Create Task table
async def create_task_table(engine):
    """Create Task table"""
    async with engine.begin() as conn:
        await conn.execute(text("""
        CREATE TABLE IF NOT EXISTS ai_agent_system.tasks (
            id VARCHAR PRIMARY KEY,
            title VARCHAR NOT NULL,
            description TEXT NOT NULL,
            status VARCHAR NOT NULL,
            created_by VARCHAR NOT NULL,
            assigned_to VARCHAR,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            completed_at TIMESTAMP,
            result TEXT,
            parent_task_id VARCHAR REFERENCES ai_agent_system.tasks(id) ON DELETE CASCADE,
            session_id VARCHAR REFERENCES ai_agent_system.sessions(id) ON DELETE CASCADE,
            priority INTEGER DEFAULT 1,
            required_skills VARCHAR
        )
        """))

# Create TaskContext table
async def create_task_context_table(engine):
    """Create TaskContext table"""
    async with engine.begin() as conn:
        await conn.execute(text("""
        CREATE TABLE IF NOT EXISTS ai_agent_system.task_contexts (
            id SERIAL PRIMARY KEY,
            task_id VARCHAR NOT NULL,
            key VARCHAR NOT NULL,
            value TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (task_id) REFERENCES ai_agent_system.tasks(id) ON DELETE CASCADE
        )
        """))

# Create TaskUpdate table
async def create_task_update_table(engine):
    """Create TaskUpdate table"""
    async with engine.begin() as conn:
        await conn.execute(text("""
        CREATE TABLE IF NOT EXISTS ai_agent_system.task_updates (
            id SERIAL PRIMARY KEY,
            task_id VARCHAR NOT NULL,
            agent_id VARCHAR NOT NULL,
            content TEXT NOT NULL,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            level VARCHAR DEFAULT 'info',
            FOREIGN KEY (task_id) REFERENCES ai_agent_system.tasks(id) ON DELETE CASCADE
        )
        """))

async def run_migrations(engine):
    """Run all migrations"""
    # Create schema first
    await create_schema(engine)

    # Add is_multi_agent column to Session table
    await upgrade_session_table(engine)

    # Create Agent table
    await create_agent_table(engine)

    # Update Message table
    await update_message_table(engine)

    # Create Task table
    await create_task_table(engine)

    # Create TaskContext table
    await create_task_context_table(engine)

    # Create TaskUpdate table
    await create_task_update_table(engine)
