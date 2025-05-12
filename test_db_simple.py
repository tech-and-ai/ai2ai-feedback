"""
Simple test script to verify the database connection and basic operations.
"""

import asyncio
import os
from dotenv import load_dotenv
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
import uuid

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

# Create async session
async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

async def test_connection():
    """Test the database connection"""
    try:
        async with engine.begin() as conn:
            result = await conn.execute(text("SELECT 1"))
            value = result.scalar()
            
            if value == 1:
                print("✅ Database connection successful!")
                return True
            else:
                print("❌ Database connection failed: Unexpected result")
                return False
    except Exception as e:
        print(f"❌ Database connection failed: {str(e)}")
        return False

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

async def create_test_session():
    """Create a test session in the database"""
    try:
        session_id = str(uuid.uuid4())
        
        async with async_session() as session:
            await session.execute(
                text("""
                INSERT INTO ai_agent_system.sessions 
                (id, created_at, last_accessed_at, system_prompt, title, tags, is_multi_agent) 
                VALUES (:id, NOW(), NOW(), :system_prompt, :title, :tags, :is_multi_agent)
                """),
                {
                    "id": session_id,
                    "system_prompt": "Test system prompt",
                    "title": "Test Session",
                    "tags": "test,integration",
                    "is_multi_agent": False
                }
            )
            await session.commit()
            
            print(f"✅ Test session created with ID: {session_id}")
            return session_id
    except Exception as e:
        print(f"❌ Error creating test session: {str(e)}")
        return None

async def get_session(session_id):
    """Get a session from the database"""
    try:
        async with async_session() as session:
            result = await session.execute(
                text("""
                SELECT * FROM ai_agent_system.sessions WHERE id = :id
                """),
                {"id": session_id}
            )
            row = result.fetchone()
            
            if row:
                print(f"✅ Session retrieved: {row}")
                return row
            else:
                print(f"❌ Session not found: {session_id}")
                return None
    except Exception as e:
        print(f"❌ Error getting session: {str(e)}")
        return None

async def main():
    """Main function"""
    print("Testing database connection...")
    connection_successful = await test_connection()
    
    if connection_successful:
        print("\nCreating schema...")
        await create_schema()
        
        print("\nCreating test session...")
        session_id = await create_test_session()
        
        if session_id:
            print("\nRetrieving test session...")
            await get_session(session_id)
    
    print("\nDone!")

if __name__ == "__main__":
    asyncio.run(main())
