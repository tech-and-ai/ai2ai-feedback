#!/usr/bin/env python3
"""
Database Seed Script

This script seeds the database with initial data for the AI2AI Feedback System.
"""

import os
import sys
import sqlite3
import logging
import argparse
import json
import uuid
from datetime import datetime

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.config import load_config

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

def seed_agents(conn):
    """
    Seed agents table.
    
    Args:
        conn: Database connection
    """
    cursor = conn.cursor()
    
    # Check if agents table is empty
    cursor.execute('SELECT COUNT(*) FROM agents')
    count = cursor.fetchone()[0]
    
    if count > 0:
        logger.info("Agents table already seeded")
        return
    
    # Seed agents
    agents = [
        {
            'id': 'agent1',
            'name': 'Gemma 3 4B',
            'description': 'General-purpose agent using Gemma 3 4B model',
            'model': 'gemma3:4b',
            'capabilities': json.dumps({
                'text_generation': True,
                'summarization': True,
                'question_answering': True
            }),
            'status': 'available',
            'last_active': datetime.utcnow().isoformat(),
            'configuration': json.dumps({})
        },
        {
            'id': 'agent2',
            'name': 'DeepSeek Coder',
            'description': 'Code-focused agent using DeepSeek Coder model',
            'model': 'deepseek-coder-v2:16b',
            'capabilities': json.dumps({
                'code_generation': True,
                'code_explanation': True,
                'code_review': True
            }),
            'status': 'available',
            'last_active': datetime.utcnow().isoformat(),
            'configuration': json.dumps({})
        },
        {
            'id': 'agent3',
            'name': 'Gemma 3 1B',
            'description': 'Lightweight agent using Gemma 3 1B model',
            'model': 'gemma3:1b',
            'capabilities': json.dumps({
                'text_generation': True,
                'classification': True
            }),
            'status': 'available',
            'last_active': datetime.utcnow().isoformat(),
            'configuration': json.dumps({})
        }
    ]
    
    for agent in agents:
        cursor.execute('''
        INSERT INTO agents (id, name, description, model, capabilities, status, last_active, configuration)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            agent['id'],
            agent['name'],
            agent['description'],
            agent['model'],
            agent['capabilities'],
            agent['status'],
            agent['last_active'],
            agent['configuration']
        ))
    
    conn.commit()
    logger.info(f"Seeded {len(agents)} agents")

def seed_tasks(conn):
    """
    Seed tasks table.
    
    Args:
        conn: Database connection
    """
    cursor = conn.cursor()
    
    # Check if tasks table is empty
    cursor.execute('SELECT COUNT(*) FROM tasks')
    count = cursor.fetchone()[0]
    
    if count > 0:
        logger.info("Tasks table already seeded")
        return
    
    # Seed tasks
    tasks = [
        {
            'id': str(uuid.uuid4()),
            'title': 'Research quantum computing',
            'description': 'Gather information about recent advances in quantum computing and summarize key findings.',
            'status': 'not_started',
            'priority': 5,
            'created_at': datetime.utcnow().isoformat(),
            'updated_at': datetime.utcnow().isoformat(),
            'assigned_agent_id': None,
            'parent_task_id': None,
            'metadata': json.dumps({
                'expected_output_format': 'markdown',
                'min_words': 500,
                'max_words': 2000
            })
        },
        {
            'id': str(uuid.uuid4()),
            'title': 'Generate landing page HTML',
            'description': 'Create a responsive HTML landing page for a SaaS product with modern design and animations.',
            'status': 'not_started',
            'priority': 8,
            'created_at': datetime.utcnow().isoformat(),
            'updated_at': datetime.utcnow().isoformat(),
            'assigned_agent_id': 'agent2',
            'parent_task_id': None,
            'metadata': json.dumps({
                'expected_output_format': 'html',
                'include_css': True,
                'include_javascript': True
            })
        },
        {
            'id': str(uuid.uuid4()),
            'title': 'Summarize research paper',
            'description': 'Read and summarize the key findings of the research paper "Attention Is All You Need".',
            'status': 'not_started',
            'priority': 3,
            'created_at': datetime.utcnow().isoformat(),
            'updated_at': datetime.utcnow().isoformat(),
            'assigned_agent_id': 'agent1',
            'parent_task_id': None,
            'metadata': json.dumps({
                'expected_output_format': 'markdown',
                'min_words': 300,
                'max_words': 1000
            })
        }
    ]
    
    for task in tasks:
        cursor.execute('''
        INSERT INTO tasks (id, title, description, status, priority, created_at, updated_at, assigned_agent_id, parent_task_id, metadata)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            task['id'],
            task['title'],
            task['description'],
            task['status'],
            task['priority'],
            task['created_at'],
            task['updated_at'],
            task['assigned_agent_id'],
            task['parent_task_id'],
            task['metadata']
        ))
    
    conn.commit()
    logger.info(f"Seeded {len(tasks)} tasks")

def main():
    """Main function."""
    parser = argparse.ArgumentParser(description='Database Seed Script')
    parser.add_argument('--config', type=str, default='default', help='Configuration to use')
    args = parser.parse_args()
    
    # Load configuration
    config = load_config(args.config)
    
    # Connect to database
    conn = sqlite3.connect(config.database_url)
    
    try:
        # Seed database
        seed_agents(conn)
        seed_tasks(conn)
        logger.info(f"Seeding completed successfully: {config.database_url}")
    except Exception as e:
        logger.error(f"Error during seeding: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    main()
