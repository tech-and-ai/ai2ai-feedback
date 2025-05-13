"""
Recreate tasks table with new schema

This script drops and recreates the tasks table with the new schema.
"""

import asyncio
import os
import sys
import logging
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("recreate-tasks-table")

# Force use of local SQLite database
DATABASE_URL = "sqlite+aiosqlite:///ai2ai_feedback.db"
print(f"Using database URL: {DATABASE_URL}")

# Create async engine
engine = create_async_engine(DATABASE_URL)

async def recreate_tasks_table():
    """Drop and recreate the tasks table"""
    try:
        logger.info("Starting tasks table recreation...")
        
        async with engine.begin() as conn:
            # Drop the tasks table
            logger.info("Dropping tasks table...")
            await conn.execute(text("DROP TABLE IF EXISTS tasks"))
            logger.info("Tasks table dropped")
            
            # Create the tasks table with new schema
            logger.info("Creating tasks table with new schema...")
            await conn.execute(text("""
                CREATE TABLE tasks (
                    id TEXT PRIMARY KEY,
                    title TEXT NOT NULL,
                    description TEXT NOT NULL,
                    status TEXT NOT NULL,
                    created_by TEXT NOT NULL,
                    assigned_to TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    completed_at TIMESTAMP,
                    result TEXT,
                    parent_task_id TEXT REFERENCES tasks(id) ON DELETE CASCADE,
                    session_id TEXT REFERENCES sessions(id) ON DELETE CASCADE,
                    priority INTEGER DEFAULT 1,
                    required_skills TEXT,
                    project_id TEXT,
                    task_type TEXT,
                    dependencies TEXT DEFAULT '[]',
                    estimated_effort INTEGER,
                    deadline TIMESTAMP,
                    progress INTEGER DEFAULT 0,
                    blockers TEXT DEFAULT '[]'
                )
            """))
            logger.info("Tasks table created with new schema")
        
        logger.info("Tasks table recreation completed successfully")
    except Exception as e:
        logger.error(f"Error recreating tasks table: {e}")
        raise

async def verify_tasks_table():
    """Verify that the tasks table was recreated correctly"""
    try:
        logger.info("Verifying tasks table...")
        
        async with engine.connect() as conn:
            # Check tasks table columns
            result = await conn.execute(text("PRAGMA table_info(tasks)"))
            tasks_columns = [row[1] for row in result.fetchall()]
            logger.info(f"Tasks table columns: {tasks_columns}")
            
            # Verify new columns exist
            required_task_columns = [
                "project_id", "task_type", "dependencies", "estimated_effort", 
                "deadline", "progress", "blockers"
            ]
            
            missing_task_columns = [col for col in required_task_columns if col not in tasks_columns]
            if missing_task_columns:
                logger.error(f"Missing columns in tasks table: {missing_task_columns}")
                return False
            else:
                logger.info("All required columns exist in tasks table")
            
            logger.info("Tasks table verification completed successfully")
            return True
    except Exception as e:
        logger.error(f"Error verifying tasks table: {e}")
        return False

async def main():
    """Main function"""
    try:
        # Recreate tasks table
        await recreate_tasks_table()
        
        # Verify tasks table
        if await verify_tasks_table():
            logger.info("Tasks table recreation and verification completed successfully")
        else:
            logger.error("Tasks table verification failed")
            sys.exit(1)
    except Exception as e:
        logger.error(f"Error in main function: {e}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
