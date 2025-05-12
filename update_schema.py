"""
Update the PostgreSQL database schema to include the priority and required_skills fields.
"""

import asyncio
import os
from sqlalchemy import text
from app.database import engine

async def update_schema():
    """Update the PostgreSQL database schema."""
    try:
        async with engine.begin() as conn:
            # Check if the priority column exists
            result = await conn.execute(text("""
            SELECT column_name
            FROM information_schema.columns
            WHERE table_schema = 'ai_agent_system'
            AND table_name = 'tasks'
            AND column_name = 'priority'
            """))
            priority_exists = result.fetchone() is not None

            # Add the priority column if it doesn't exist
            if not priority_exists:
                print("Adding priority column to tasks table...")
                await conn.execute(text("""
                ALTER TABLE ai_agent_system.tasks
                ADD COLUMN priority INTEGER DEFAULT 1
                """))

            # Check if the required_skills column exists
            result = await conn.execute(text("""
            SELECT column_name
            FROM information_schema.columns
            WHERE table_schema = 'ai_agent_system'
            AND table_name = 'tasks'
            AND column_name = 'required_skills'
            """))
            required_skills_exists = result.fetchone() is not None

            # Add the required_skills column if it doesn't exist
            if not required_skills_exists:
                print("Adding required_skills column to tasks table...")
                await conn.execute(text("""
                ALTER TABLE ai_agent_system.tasks
                ADD COLUMN required_skills VARCHAR
                """))

            print("Schema updated successfully!")
    except Exception as e:
        print(f"Error updating schema: {str(e)}")

if __name__ == "__main__":
    asyncio.run(update_schema())
