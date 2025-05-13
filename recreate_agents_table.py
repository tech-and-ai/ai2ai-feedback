"""
Recreate agents table with new schema

This script drops and recreates the agents table with the new schema.
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
logger = logging.getLogger("recreate-agents-table")

# Force use of local SQLite database
DATABASE_URL = "sqlite+aiosqlite:///ai2ai_feedback.db"
print(f"Using database URL: {DATABASE_URL}")

# Create async engine
engine = create_async_engine(DATABASE_URL)

async def recreate_agents_table():
    """Drop and recreate the agents table"""
    try:
        logger.info("Starting agents table recreation...")
        
        async with engine.begin() as conn:
            # Drop the agents table
            logger.info("Dropping agents table...")
            await conn.execute(text("DROP TABLE IF EXISTS agents"))
            logger.info("Agents table dropped")
            
            # Create the agents table with new schema
            logger.info("Creating agents table with new schema...")
            await conn.execute(text("""
                CREATE TABLE agents (
                    id INTEGER PRIMARY KEY,
                    session_id TEXT REFERENCES sessions(id) ON DELETE CASCADE,
                    agent_index INTEGER NOT NULL,
                    name TEXT,
                    role TEXT,
                    model TEXT,
                    agent_id TEXT,
                    agent_type TEXT DEFAULT 'worker',
                    skills TEXT,
                    status TEXT DEFAULT 'idle',
                    performance_metrics TEXT DEFAULT '{}',
                    current_workload INTEGER DEFAULT 0,
                    max_workload INTEGER DEFAULT 3
                )
            """))
            logger.info("Agents table created with new schema")
        
        logger.info("Agents table recreation completed successfully")
    except Exception as e:
        logger.error(f"Error recreating agents table: {e}")
        raise

async def verify_agents_table():
    """Verify that the agents table was recreated correctly"""
    try:
        logger.info("Verifying agents table...")
        
        async with engine.connect() as conn:
            # Check agents table columns
            result = await conn.execute(text("PRAGMA table_info(agents)"))
            agents_columns = [row[1] for row in result.fetchall()]
            logger.info(f"Agents table columns: {agents_columns}")
            
            # Verify new columns exist
            required_agent_columns = [
                "agent_id", "agent_type", "skills", "status", 
                "performance_metrics", "current_workload", "max_workload"
            ]
            
            missing_agent_columns = [col for col in required_agent_columns if col not in agents_columns]
            if missing_agent_columns:
                logger.error(f"Missing columns in agents table: {missing_agent_columns}")
                return False
            else:
                logger.info("All required columns exist in agents table")
            
            logger.info("Agents table verification completed successfully")
            return True
    except Exception as e:
        logger.error(f"Error verifying agents table: {e}")
        return False

async def main():
    """Main function"""
    try:
        # Recreate agents table
        await recreate_agents_table()
        
        # Verify agents table
        if await verify_agents_table():
            logger.info("Agents table recreation and verification completed successfully")
        else:
            logger.error("Agents table verification failed")
            sys.exit(1)
    except Exception as e:
        logger.error(f"Error in main function: {e}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
