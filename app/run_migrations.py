"""
Run database migrations for AI-to-AI Feedback API
"""

import asyncio
import os
import sys
from pathlib import Path

# Add the parent directory to the path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.database import engine
from app.migrations.task_management import (
    upgrade_session_table,
    create_agent_table,
    update_message_table,
    create_task_table,
    create_task_context_table,
    create_task_update_table
)

async def run_migrations():
    """Run all migrations"""
    print("Running migrations...")
    
    # Add is_multi_agent column to Session table
    print("Upgrading session table...")
    await upgrade_session_table(engine)
    
    # Create Agent table
    print("Creating agent table...")
    await create_agent_table(engine)
    
    # Update Message table
    print("Updating message table...")
    await update_message_table(engine)
    
    # Create Task table
    print("Creating task table...")
    await create_task_table(engine)
    
    # Create TaskContext table
    print("Creating task context table...")
    await create_task_context_table(engine)
    
    # Create TaskUpdate table
    print("Creating task update table...")
    await create_task_update_table(engine)
    
    print("Migrations completed successfully!")

if __name__ == "__main__":
    asyncio.run(run_migrations())
