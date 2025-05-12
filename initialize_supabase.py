"""
Initialize the database for the AI-to-AI Feedback API using the Supabase REST API.

This script creates the schema and tables required for the application.
"""

import os
import json
import asyncio
import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Get Supabase URL and key from environment variables
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

# Check if Supabase URL and key are set
if not SUPABASE_URL or not SUPABASE_KEY:
    print("❌ Supabase URL or key not set in environment variables")
    exit(1)

# Set up headers for Supabase REST API
headers = {
    "Content-Type": "application/json",
    "Authorization": f"Bearer {SUPABASE_KEY}",
    "apikey": SUPABASE_KEY
}

def run_query(query):
    """Run a query on the Supabase database"""
    url = f"{SUPABASE_URL}/rest/v1/rpc/execute_sql"
    response = requests.post(url, headers=headers, json={"query": query})

    if response.status_code != 200:
        print(f"❌ Error running query: {response.text}")
        return None

    return response.json()

def check_schema_exists():
    """Check if the ai_agent_system schema exists"""
    query = """
    SELECT schema_name
    FROM information_schema.schemata
    WHERE schema_name = 'ai_agent_system'
    """
    result = run_query(query)

    if result and len(result) > 0:
        print("✅ Schema 'ai_agent_system' exists")
        return True
    else:
        print("❓ Schema 'ai_agent_system' does not exist")
        return False

def create_schema():
    """Create the ai_agent_system schema"""
    query = "CREATE SCHEMA IF NOT EXISTS ai_agent_system"
    result = run_query(query)

    if result is not None:
        print("✅ Schema 'ai_agent_system' created")
        return True
    else:
        print("❌ Failed to create schema 'ai_agent_system'")
        return False

def check_table_exists(table_name):
    """Check if a table exists in the ai_agent_system schema"""
    query = f"""
    SELECT table_name
    FROM information_schema.tables
    WHERE table_schema = 'ai_agent_system'
    AND table_name = '{table_name}'
    """
    result = run_query(query)

    if result and len(result) > 0:
        print(f"✅ Table '{table_name}' exists")
        return True
    else:
        print(f"❓ Table '{table_name}' does not exist")
        return False

def create_sessions_table():
    """Create the sessions table"""
    if check_table_exists("sessions"):
        return True

    query = """
    CREATE TABLE IF NOT EXISTS ai_agent_system.sessions (
        id TEXT PRIMARY KEY,
        created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
        last_accessed_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
        system_prompt TEXT,
        title TEXT,
        tags TEXT,
        is_multi_agent BOOLEAN DEFAULT FALSE
    )
    """
    result = run_query(query)

    if result is not None:
        print("✅ Table 'sessions' created")
        return True
    else:
        print("❌ Failed to create table 'sessions'")
        return False

def create_agents_table():
    """Create the agents table"""
    if check_table_exists("agents"):
        return True

    query = """
    CREATE TABLE IF NOT EXISTS ai_agent_system.agents (
        id SERIAL PRIMARY KEY,
        session_id TEXT NOT NULL,
        agent_index INTEGER NOT NULL,
        name TEXT,
        role TEXT,
        model TEXT,
        FOREIGN KEY (session_id) REFERENCES ai_agent_system.sessions(id) ON DELETE CASCADE
    )
    """
    result = run_query(query)

    if result is not None:
        print("✅ Table 'agents' created")
        return True
    else:
        print("❌ Failed to create table 'agents'")
        return False

def create_messages_table():
    """Create the messages table"""
    if check_table_exists("messages"):
        return True

    query = """
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
    """
    result = run_query(query)

    if result is not None:
        print("✅ Table 'messages' created")
        return True
    else:
        print("❌ Failed to create table 'messages'")
        return False

def create_feedback_table():
    """Create the feedback table"""
    if check_table_exists("feedback"):
        return True

    query = """
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
    """
    result = run_query(query)

    if result is not None:
        print("✅ Table 'feedback' created")
        return True
    else:
        print("❌ Failed to create table 'feedback'")
        return False

def create_tasks_table():
    """Create the tasks table"""
    if check_table_exists("tasks"):
        return True

    query = """
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
    """
    result = run_query(query)

    if result is not None:
        print("✅ Table 'tasks' created")
        return True
    else:
        print("❌ Failed to create table 'tasks'")
        return False

def create_task_contexts_table():
    """Create the task_contexts table"""
    if check_table_exists("task_contexts"):
        return True

    query = """
    CREATE TABLE IF NOT EXISTS ai_agent_system.task_contexts (
        id SERIAL PRIMARY KEY,
        task_id TEXT NOT NULL,
        key TEXT NOT NULL,
        value TEXT NOT NULL,
        created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
        FOREIGN KEY (task_id) REFERENCES ai_agent_system.tasks(id) ON DELETE CASCADE
    )
    """
    result = run_query(query)

    if result is not None:
        print("✅ Table 'task_contexts' created")
        return True
    else:
        print("❌ Failed to create table 'task_contexts'")
        return False

def create_task_updates_table():
    """Create the task_updates table"""
    if check_table_exists("task_updates"):
        return True

    query = """
    CREATE TABLE IF NOT EXISTS ai_agent_system.task_updates (
        id SERIAL PRIMARY KEY,
        task_id TEXT NOT NULL,
        agent_id TEXT NOT NULL,
        content TEXT NOT NULL,
        timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
        level TEXT DEFAULT 'info',
        FOREIGN KEY (task_id) REFERENCES ai_agent_system.tasks(id) ON DELETE CASCADE
    )
    """
    result = run_query(query)

    if result is not None:
        print("✅ Table 'task_updates' created")
        return True
    else:
        print("❌ Failed to create table 'task_updates'")
        return False

def main():
    """Main function"""
    print("Initializing database...")

    # Check if schema exists, create if not
    if not check_schema_exists():
        if not create_schema():
            return

    # Create tables
    create_sessions_table()
    create_agents_table()
    create_messages_table()
    create_feedback_table()
    create_tasks_table()
    create_task_contexts_table()
    create_task_updates_table()

    print("\nDone!")

if __name__ == "__main__":
    main()
