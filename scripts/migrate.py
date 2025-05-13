#!/usr/bin/env python3
"""
Database Migration Script

This script creates the database schema for the AI2AI Feedback System.
"""

import os
import sys
import sqlite3
import logging
import argparse

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.config import load_config

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

def table_exists(cursor, table_name):
    """
    Check if a table exists in the database.

    Args:
        cursor: Database cursor
        table_name: Table name

    Returns:
        True if the table exists, False otherwise
    """
    cursor.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name=?",
        (table_name,)
    )
    return cursor.fetchone() is not None

def create_tables(conn):
    """
    Create database tables.

    Args:
        conn: Database connection
    """
    cursor = conn.cursor()

    # Drop existing tables if they exist
    tables = ['messages', 'discussions', 'outputs', 'agents', 'tasks']
    for table in tables:
        cursor.execute(f'DROP TABLE IF EXISTS {table}')

    # Create tasks table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS tasks (
        id TEXT PRIMARY KEY,
        title TEXT NOT NULL,
        description TEXT NOT NULL,
        status TEXT NOT NULL,
        priority INTEGER NOT NULL,
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL,
        assigned_agent_id TEXT,
        parent_task_id TEXT,
        metadata TEXT DEFAULT '{}'
    )
    ''')

    # Create agents table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS agents (
        id TEXT PRIMARY KEY,
        name TEXT NOT NULL,
        description TEXT NOT NULL,
        model TEXT NOT NULL,
        capabilities TEXT DEFAULT '{}',
        status TEXT NOT NULL,
        last_active TEXT NOT NULL,
        configuration TEXT DEFAULT '{}'
    )
    ''')

    # Create outputs table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS outputs (
        id TEXT PRIMARY KEY,
        task_id TEXT NOT NULL,
        agent_id TEXT NOT NULL,
        type TEXT NOT NULL,
        content TEXT NOT NULL,
        created_at TEXT NOT NULL,
        metadata TEXT DEFAULT '{}',
        FOREIGN KEY (task_id) REFERENCES tasks (id),
        FOREIGN KEY (agent_id) REFERENCES agents (id)
    )
    ''')

    # Create discussions table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS discussions (
        id TEXT PRIMARY KEY,
        task_id TEXT NOT NULL,
        title TEXT NOT NULL,
        status TEXT NOT NULL,
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL,
        metadata TEXT DEFAULT '{}',
        FOREIGN KEY (task_id) REFERENCES tasks (id)
    )
    ''')

    # Create messages table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS messages (
        id TEXT PRIMARY KEY,
        discussion_id TEXT NOT NULL,
        agent_id TEXT NOT NULL,
        content TEXT NOT NULL,
        created_at TEXT NOT NULL,
        parent_message_id TEXT,
        metadata TEXT DEFAULT '{}',
        FOREIGN KEY (discussion_id) REFERENCES discussions (id),
        FOREIGN KEY (agent_id) REFERENCES agents (id),
        FOREIGN KEY (parent_message_id) REFERENCES messages (id)
    )
    ''')

    # Create indexes
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_tasks_status ON tasks (status)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_tasks_priority ON tasks (priority)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_tasks_assigned_agent_id ON tasks (assigned_agent_id)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_agents_status ON agents (status)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_agents_model ON agents (model)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_outputs_task_id ON outputs (task_id)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_outputs_agent_id ON outputs (agent_id)')

    # Create discussions and messages indexes after tables are created
    if table_exists(cursor, 'discussions'):
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_discussions_task_id ON discussions (task_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_discussions_status ON discussions (status)')

    if table_exists(cursor, 'messages'):
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_messages_discussion_id ON messages (discussion_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_messages_agent_id ON messages (agent_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_messages_parent_message_id ON messages (parent_message_id)')

    conn.commit()
    logger.info("Created database tables")

def main():
    """Main function."""
    parser = argparse.ArgumentParser(description='Database Migration Script')
    parser.add_argument('--config', type=str, default='default', help='Configuration to use')
    args = parser.parse_args()

    # Load configuration
    config = load_config(args.config)

    # Connect to database
    conn = sqlite3.connect(config.database_url)

    try:
        # Create tables
        create_tables(conn)
        logger.info(f"Migration completed successfully: {config.database_url}")
    except Exception as e:
        logger.error(f"Error during migration: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    main()
