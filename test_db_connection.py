"""
Test the database connection and run migrations for the AI-to-AI Feedback API.
"""

import asyncio
import os
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

async def test_connection():
    """Test the database connection"""
    try:
        # Try to connect to the database
        async with engine.begin() as conn:
            # Execute a simple query
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

async def check_schema_exists():
    """Check if the ai_agent_system schema exists"""
    try:
        async with engine.begin() as conn:
            result = await conn.execute(text("""
            SELECT schema_name
            FROM information_schema.schemata
            WHERE schema_name = 'ai_agent_system'
            """))
            schema_exists = result.fetchone() is not None

            if schema_exists:
                print("✅ Schema 'ai_agent_system' exists")
            else:
                print("❓ Schema 'ai_agent_system' does not exist (will be created during migrations)")

            return schema_exists
    except Exception as e:
        print(f"❌ Error checking schema: {str(e)}")
        return False

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
                    print(f"❓ Table '{table}' does not exist (will be created during migrations)")
    except Exception as e:
        print(f"❌ Error checking tables: {str(e)}")

async def main():
    """Main function"""
    print("Testing database connection...")
    connection_successful = await test_connection()

    if connection_successful:
        print("\nChecking schema...")
        await check_schema_exists()

        print("\nChecking tables...")
        await check_tables()

        print("\nRun migrations? (y/n)")
        choice = input().lower()

        if choice == 'y':
            print("\nRunning migrations...")
            # Import and run migrations
            from app.run_migrations import run_migrations
            await run_migrations()

            print("\nChecking schema after migrations...")
            await check_schema_exists()

            print("\nChecking tables after migrations...")
            await check_tables()

    print("\nDone!")

if __name__ == "__main__":
    asyncio.run(main())
