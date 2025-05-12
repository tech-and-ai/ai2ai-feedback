"""
Initialize the database for the AI-to-AI Feedback API.

This script creates all tables defined in the database.py file.
"""

import asyncio
import os
from dotenv import load_dotenv
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

# Load environment variables
load_dotenv()

# Import the database module
from app.database import init_db, engine

async def create_schema():
    """Create the ai_agent_system schema if it doesn't exist"""
    try:
        async with engine.begin() as conn:
            await conn.execute(text("""
            CREATE SCHEMA IF NOT EXISTS ai_agent_system
            """))
            print("✅ Schema 'ai_agent_system' created or already exists")
    except Exception as e:
        print(f"❌ Error creating schema: {str(e)}")

async def initialize_database():
    """Initialize the database with all tables"""
    try:
        # Create schema first
        await create_schema()
        
        # Initialize the database (create all tables)
        await init_db()
        print("✅ Database initialized successfully")
    except Exception as e:
        print(f"❌ Error initializing database: {str(e)}")

async def check_tables():
    """Check if the required tables exist in the schema"""
    tables = [
        "sessions", "messages", "feedback", "agents", 
        "tasks", "task_contexts", "task_updates",
        "memories", "code_snippets", "references"
    ]
    
    try:
        async with engine.begin() as conn:
            for table in tables:
                result = await conn.execute(text(f"""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'ai_agent_system' 
                AND table_name = '{table}'
                """))
                table_exists = result.fetchone() is not None
                
                if table_exists:
                    print(f"✅ Table '{table}' exists")
                else:
                    print(f"❌ Table '{table}' does not exist")
    except Exception as e:
        print(f"❌ Error checking tables: {str(e)}")

async def main():
    """Main function"""
    print("Initializing database...")
    await initialize_database()
    
    print("\nChecking tables...")
    await check_tables()
    
    print("\nDone!")

if __name__ == "__main__":
    asyncio.run(main())
