"""
Database migrations for task management system
"""

from sqlalchemy import Column, String, Text, DateTime, ForeignKey, Boolean, Integer, Float, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, backref
from datetime import datetime

Base = declarative_base()

# Add is_multi_agent column to Session table
async def upgrade_session_table(engine):
    """Add is_multi_agent column to Session table"""
    async with engine.begin() as conn:
        # Check if is_multi_agent column exists
        result = await conn.execute(text("""
        PRAGMA table_info(sessions)
        """))
        rows = result.fetchall()  # No await here for SQLAlchemy 1.4
        columns = [row[1] for row in rows]

        if 'is_multi_agent' not in columns:
            await conn.execute(text("""
            ALTER TABLE sessions
            ADD COLUMN is_multi_agent BOOLEAN DEFAULT FALSE
            """))

# Create Agent table
async def create_agent_table(engine):
    """Create Agent table"""
    async with engine.begin() as conn:
        await conn.execute(text("""
        CREATE TABLE IF NOT EXISTS agents (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id VARCHAR NOT NULL,
            agent_index INTEGER NOT NULL,
            name VARCHAR,
            role VARCHAR,
            model VARCHAR,
            FOREIGN KEY (session_id) REFERENCES sessions(id) ON DELETE CASCADE
        )
        """))

# Update Message table
async def update_message_table(engine):
    """Update Message table to support agents"""
    async with engine.begin() as conn:
        # Check if agent_id column exists
        result = await conn.execute(text("""
        PRAGMA table_info(messages)
        """))
        rows = result.fetchall()  # No await here for SQLAlchemy 1.4
        columns = [row[1] for row in rows]

        if 'agent_id' not in columns:
            await conn.execute(text("""
            ALTER TABLE messages
            ADD COLUMN agent_id INTEGER REFERENCES agents(id) ON DELETE CASCADE
            """))

        if 'initiator' not in columns:
            await conn.execute(text("""
            ALTER TABLE messages
            ADD COLUMN initiator VARCHAR
            """))

# Create Task table
async def create_task_table(engine):
    """Create Task table"""
    async with engine.begin() as conn:
        await conn.execute(text("""
        CREATE TABLE IF NOT EXISTS tasks (
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
            parent_task_id VARCHAR REFERENCES tasks(id) ON DELETE CASCADE,
            session_id VARCHAR REFERENCES sessions(id) ON DELETE CASCADE
        )
        """))

# Create TaskContext table
async def create_task_context_table(engine):
    """Create TaskContext table"""
    async with engine.begin() as conn:
        await conn.execute(text("""
        CREATE TABLE IF NOT EXISTS task_contexts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            task_id VARCHAR NOT NULL,
            key VARCHAR NOT NULL,
            value TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (task_id) REFERENCES tasks(id) ON DELETE CASCADE
        )
        """))

# Create TaskUpdate table
async def create_task_update_table(engine):
    """Create TaskUpdate table"""
    async with engine.begin() as conn:
        await conn.execute(text("""
        CREATE TABLE IF NOT EXISTS task_updates (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            task_id VARCHAR NOT NULL,
            agent_id VARCHAR NOT NULL,
            content TEXT NOT NULL,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (task_id) REFERENCES tasks(id) ON DELETE CASCADE
        )
        """))

async def run_migrations(engine):
    """Run all migrations"""
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
