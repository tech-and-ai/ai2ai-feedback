"""
Initialize the database for the AI-to-AI Feedback API.

This script creates the schema and tables required for the application.
"""

import os
import asyncio
from dotenv import load_dotenv
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

# Load environment variables
load_dotenv()

# Get database URL from environment variables
DATABASE_URL = os.getenv("DATABASE_URL")

# Ensure we're using the asyncpg driver
if DATABASE_URL and not DATABASE_URL.startswith("postgresql+asyncpg://"):
    if DATABASE_URL.startswith("postgresql://"):
        DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://")
    else:
        DATABASE_URL = "postgresql+asyncpg://postgres:postgres@db.brxpkhpkitfzecvmwzgz.supabase.co:5432/postgres"

print(f"Using database URL: {DATABASE_URL}")

# Create async engine
engine = create_async_engine(
    DATABASE_URL,
    echo=True,  # Set to True to see SQL queries
    pool_size=5,
    max_overflow=10,
    pool_timeout=30,
    pool_recycle=1800
)

async def create_schema():
    """Create the ai_agent_system schema if it doesn't exist"""
    try:
        async with engine.begin() as conn:
            await conn.execute(text("""
            CREATE SCHEMA IF NOT EXISTS ai_agent_system
            """))
            print("✅ Schema 'ai_agent_system' created or already exists")
            return True
    except Exception as e:
        print(f"❌ Error creating schema: {str(e)}")
        return False

async def create_sessions_table():
    """Create the sessions table"""
    try:
        async with engine.begin() as conn:
            await conn.execute(text("""
            CREATE TABLE IF NOT EXISTS ai_agent_system.sessions (
                id TEXT PRIMARY KEY,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                last_accessed_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                system_prompt TEXT,
                title TEXT,
                tags TEXT,
                is_multi_agent BOOLEAN DEFAULT FALSE
            )
            """))
            print("✅ Table 'sessions' created or already exists")
            return True
    except Exception as e:
        print(f"❌ Error creating sessions table: {str(e)}")
        return False

async def create_agents_table():
    """Create the agents table"""
    try:
        async with engine.begin() as conn:
            await conn.execute(text("""
            CREATE TABLE IF NOT EXISTS ai_agent_system.agents (
                id SERIAL PRIMARY KEY,
                session_id TEXT NOT NULL,
                agent_index INTEGER NOT NULL,
                name TEXT,
                role TEXT,
                model TEXT,
                FOREIGN KEY (session_id) REFERENCES ai_agent_system.sessions(id) ON DELETE CASCADE
            )
            """))
            print("✅ Table 'agents' created or already exists")
            return True
    except Exception as e:
        print(f"❌ Error creating agents table: {str(e)}")
        return False

async def create_messages_table():
    """Create the messages table"""
    try:
        async with engine.begin() as conn:
            await conn.execute(text("""
            CREATE TABLE IF NOT EXISTS ai_agent_system.messages (
                id SERIAL PRIMARY KEY,
                session_id TEXT NOT NULL,
                agent_id INTEGER REFERENCES ai_agent_system.agents(id) ON DELETE CASCADE,
                role TEXT NOT NULL,
                content TEXT NOT NULL,
                timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                initiator TEXT,
                FOREIGN KEY (session_id) REFERENCES ai_agent_system.sessions(id) ON DELETE CASCADE
            )
            """))
            print("✅ Table 'messages' created or already exists")
            return True
    except Exception as e:
        print(f"❌ Error creating messages table: {str(e)}")
        return False

async def create_feedback_table():
    """Create the feedback table"""
    try:
        async with engine.begin() as conn:
            await conn.execute(text("""
            CREATE TABLE IF NOT EXISTS ai_agent_system.feedback (
                id SERIAL PRIMARY KEY,
                message_id INTEGER NOT NULL,
                feedback_text TEXT NOT NULL,
                feedback_summary TEXT,
                reasoning_assessment TEXT,
                knowledge_gaps TEXT,
                suggested_approach TEXT,
                additional_considerations TEXT,
                source_model TEXT NOT NULL,
                timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                FOREIGN KEY (message_id) REFERENCES ai_agent_system.messages(id) ON DELETE CASCADE
            )
            """))
            print("✅ Table 'feedback' created or already exists")
            return True
    except Exception as e:
        print(f"❌ Error creating feedback table: {str(e)}")
        return False

async def create_tasks_table():
    """Create the tasks table"""
    try:
        async with engine.begin() as conn:
            await conn.execute(text("""
            CREATE TABLE IF NOT EXISTS ai_agent_system.tasks (
                id TEXT PRIMARY KEY,
                title TEXT NOT NULL,
                description TEXT NOT NULL,
                status TEXT NOT NULL,
                created_by TEXT NOT NULL,
                assigned_to TEXT,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                completed_at TIMESTAMP WITH TIME ZONE,
                result TEXT,
                parent_task_id TEXT REFERENCES ai_agent_system.tasks(id) ON DELETE CASCADE,
                session_id TEXT REFERENCES ai_agent_system.sessions(id) ON DELETE CASCADE,
                priority INTEGER DEFAULT 1,
                required_skills TEXT
            )
            """))
            print("✅ Table 'tasks' created or already exists")
            return True
    except Exception as e:
        print(f"❌ Error creating tasks table: {str(e)}")
        return False

async def create_task_contexts_table():
    """Create the task_contexts table"""
    try:
        async with engine.begin() as conn:
            await conn.execute(text("""
            CREATE TABLE IF NOT EXISTS ai_agent_system.task_contexts (
                id SERIAL PRIMARY KEY,
                task_id TEXT NOT NULL,
                key TEXT NOT NULL,
                value TEXT NOT NULL,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                FOREIGN KEY (task_id) REFERENCES ai_agent_system.tasks(id) ON DELETE CASCADE
            )
            """))
            print("✅ Table 'task_contexts' created or already exists")
            return True
    except Exception as e:
        print(f"❌ Error creating task_contexts table: {str(e)}")
        return False

async def create_task_updates_table():
    """Create the task_updates table"""
    try:
        async with engine.begin() as conn:
            await conn.execute(text("""
            CREATE TABLE IF NOT EXISTS ai_agent_system.task_updates (
                id SERIAL PRIMARY KEY,
                task_id TEXT NOT NULL,
                agent_id TEXT NOT NULL,
                content TEXT NOT NULL,
                timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                level TEXT DEFAULT 'info',
                FOREIGN KEY (task_id) REFERENCES ai_agent_system.tasks(id) ON DELETE CASCADE
            )
            """))
            print("✅ Table 'task_updates' created or already exists")
            return True
    except Exception as e:
        print(f"❌ Error creating task_updates table: {str(e)}")
        return False

async def main():
    """Main function"""
    print("Initializing database...")
    
    # Create schema
    await create_schema()
    
    # Create tables
    await create_sessions_table()
    await create_agents_table()
    await create_messages_table()
    await create_feedback_table()
    await create_tasks_table()
    await create_task_contexts_table()
    await create_task_updates_table()
    
    print("\nDone!")

if __name__ == "__main__":
    asyncio.run(main())
