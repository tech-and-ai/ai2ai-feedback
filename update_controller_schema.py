"""
Update database schema for controller-based architecture

This script updates the database schema to support the controller-based architecture
by adding new fields to the tasks and agents tables.
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
logger = logging.getLogger("schema-update")

# Force use of local SQLite database
DATABASE_URL = "sqlite+aiosqlite:///ai2ai_feedback.db"
print(f"Using database URL: {DATABASE_URL}")

# Create async engine
engine = create_async_engine(DATABASE_URL)

async def column_exists(conn, table, column):
    """Check if a column exists in a table"""
    try:
        result = await conn.execute(text(f"PRAGMA table_info({table})"))
        columns = [row[1] for row in result.fetchall()]
        return column in columns
    except Exception as e:
        logger.error(f"Error checking if column exists: {e}")
        return False

async def add_column_if_not_exists(conn, table, column, definition):
    """Add a column to a table if it doesn't exist"""
    try:
        if not await column_exists(conn, table, column):
            await conn.execute(text(f"ALTER TABLE {table} ADD COLUMN {column} {definition}"))
            logger.info(f"Added {column} column to {table} table")
            return True
        else:
            logger.info(f"Column {column} already exists in {table} table")
            return False
    except Exception as e:
        logger.error(f"Error adding column {column} to {table} table: {e}")
        return False

async def update_schema():
    """Update the database schema with new fields"""
    try:
        logger.info("Starting schema update...")

        async with engine.begin() as conn:
            # Add new columns to tasks table
            logger.info("Updating tasks table...")

            # Add project_id column
            await add_column_if_not_exists(conn, "tasks", "project_id", "TEXT")

            # Add task_type column
            await add_column_if_not_exists(conn, "tasks", "task_type", "TEXT")

            # Add dependencies column
            await add_column_if_not_exists(conn, "tasks", "dependencies", "TEXT DEFAULT '[]'")

            # Add estimated_effort column
            await add_column_if_not_exists(conn, "tasks", "estimated_effort", "INTEGER")

            # Add deadline column
            await add_column_if_not_exists(conn, "tasks", "deadline", "TIMESTAMP")

            # Add progress column
            await add_column_if_not_exists(conn, "tasks", "progress", "INTEGER DEFAULT 0")

            # Add blockers column
            await add_column_if_not_exists(conn, "tasks", "blockers", "TEXT DEFAULT '[]'")

            # Add new columns to agents table
            logger.info("Updating agents table...")

            # Add agent_type column
            await add_column_if_not_exists(conn, "agents", "agent_type", "TEXT DEFAULT 'worker'")

            # Add performance_metrics column
            await add_column_if_not_exists(conn, "agents", "performance_metrics", "TEXT DEFAULT '{}'")

            # Add current_workload column
            await add_column_if_not_exists(conn, "agents", "current_workload", "INTEGER DEFAULT 0")

            # Add max_workload column
            await add_column_if_not_exists(conn, "agents", "max_workload", "INTEGER DEFAULT 3")

        logger.info("Schema update completed successfully")
    except Exception as e:
        logger.error(f"Error updating schema: {e}")
        raise

async def verify_schema():
    """Verify that the schema was updated correctly"""
    try:
        logger.info("Verifying schema updates...")

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

            # Check agents table columns
            result = await conn.execute(text("PRAGMA table_info(agents)"))
            agents_columns = [row[1] for row in result.fetchall()]
            logger.info(f"Agents table columns: {agents_columns}")

            # Verify new columns exist
            required_agent_columns = [
                "agent_type", "performance_metrics", "current_workload", "max_workload"
            ]

            missing_agent_columns = [col for col in required_agent_columns if col not in agents_columns]
            if missing_agent_columns:
                logger.error(f"Missing columns in agents table: {missing_agent_columns}")
                return False
            else:
                logger.info("All required columns exist in agents table")

            logger.info("Schema verification completed successfully")
            return True
    except Exception as e:
        logger.error(f"Error verifying schema: {e}")
        return False

async def main():
    """Main function"""
    try:
        # Update schema
        await update_schema()

        # Verify schema
        if await verify_schema():
            logger.info("Schema update and verification completed successfully")
        else:
            logger.error("Schema verification failed")
            sys.exit(1)
    except Exception as e:
        logger.error(f"Error in main function: {e}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
