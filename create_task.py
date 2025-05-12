"""
Simple script to create a task and agent for autonomous agents.
"""

import requests
import json

# API endpoint
API_BASE = "http://localhost:8001"
TASKS_ENDPOINT = f"{API_BASE}/autonomous/tasks"
AGENTS_ENDPOINT = f"{API_BASE}/autonomous/agents"

def create_agent():
    """Create an autonomous agent."""
    agent_data = {
        "name": "Research Specialist",
        "role": "Research and analyze information",
        "skills": ["research", "analysis", "summarization"],
        "model": "google/gemini-2.0-flash-001"
    }

    try:
        response = requests.post(
            AGENTS_ENDPOINT,
            json=agent_data
        )

        response.raise_for_status()
        result = response.json()

        print(f"Agent created successfully: {result['agent_id']}")
        print(json.dumps(result, indent=2))

        return result
    except Exception as e:
        print(f"Error creating agent: {str(e)}")
        return None

def create_task():
    """Create a task for autonomous agents."""
    task_data = {
        "title": "Research PostgreSQL performance optimization",
        "description": "Research best practices for optimizing PostgreSQL performance for a web application with high read/write operations. Focus on indexing strategies, query optimization, and connection pooling.",
        "required_skills": ["research", "analysis"],
        "priority": 2
    }

    try:
        response = requests.post(
            TASKS_ENDPOINT,
            json=task_data
        )

        response.raise_for_status()
        result = response.json()

        print(f"Task created successfully: {result['id']}")
        print(json.dumps(result, indent=2))

        return result
    except Exception as e:
        print(f"Error creating task: {str(e)}")
        return None

if __name__ == "__main__":
    # First create an agent
    agent = create_agent()

    # Then create a task
    if agent:
        task = create_task()
    else:
        print("Skipping task creation since agent creation failed.")
