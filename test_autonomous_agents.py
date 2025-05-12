"""
Test script for autonomous agents.

This script creates agents and tasks to test the autonomous agent system.
"""

import asyncio
import json
import sys
import os
import requests
from datetime import datetime

# API endpoints
API_BASE = "http://localhost:8001"
AGENTS_ENDPOINT = f"{API_BASE}/autonomous/agents"
TASKS_ENDPOINT = f"{API_BASE}/autonomous/tasks"

async def create_agent(name, role, skills, model):
    """Create an autonomous agent."""
    print(f"Creating agent: {name}")

    try:
        response = requests.post(
            AGENTS_ENDPOINT,
            json={
                "name": name,
                "role": role,
                "skills": skills,
                "model": model
            }
        )

        response.raise_for_status()
        result = response.json()

        print(f"Agent created successfully: {result['agent_id']}")
        return result
    except Exception as e:
        print(f"Error creating agent: {str(e)}")
        return None

async def create_task(title, description, required_skills=None, priority=1, parent_task_id=None, context=None):
    """Create a task for autonomous agents."""
    print(f"Creating task: {title}")

    try:
        response = requests.post(
            TASKS_ENDPOINT,
            json={
                "title": title,
                "description": description,
                "required_skills": required_skills,
                "priority": priority,
                "parent_task_id": parent_task_id,
                "context": context
            }
        )

        response.raise_for_status()
        result = response.json()

        print(f"Task created successfully: {result['id']}")
        return result
    except Exception as e:
        print(f"Error creating task: {str(e)}")
        return None

async def get_tasks(status=None):
    """Get all tasks, optionally filtered by status."""
    try:
        url = TASKS_ENDPOINT
        if status:
            url += f"?status={status}"

        response = requests.get(url)
        response.raise_for_status()

        return response.json()
    except Exception as e:
        print(f"Error getting tasks: {str(e)}")
        return []

async def get_agents():
    """Get all agents."""
    try:
        response = requests.get(AGENTS_ENDPOINT)
        response.raise_for_status()

        return response.json()
    except Exception as e:
        print(f"Error getting agents: {str(e)}")
        return []

async def monitor_tasks(interval=5, max_time=300):
    """Monitor tasks and print updates."""
    start_time = datetime.now()
    elapsed_time = 0

    while elapsed_time < max_time:
        # Get tasks
        tasks = await get_tasks()

        # Print task status
        print("\n--- Task Status ---")
        for task in tasks:
            print(f"Task: {task['title']} - Status: {task['status']}")

            # Print latest update if available
            if task.get("updates") and len(task["updates"]) > 0:
                latest_update = task["updates"][-1]
                print(f"  Latest update: {latest_update['content']}")

        # Check if all tasks are completed or failed
        all_done = all(task["status"] in ["completed", "failed"] for task in tasks)
        if all_done and tasks:
            print("\nAll tasks completed or failed!")
            break

        # Wait for next check
        await asyncio.sleep(interval)

        # Update elapsed time
        elapsed_time = (datetime.now() - start_time).total_seconds()

    # Print final results
    print("\n--- Final Results ---")
    tasks = await get_tasks()

    for task in tasks:
        print(f"\nTask: {task['title']}")
        print(f"Status: {task['status']}")

        if task["status"] == "completed" and task.get("result"):
            result = task["result"]
            if isinstance(result, dict) and result.get("structured"):
                print("\nAnalysis:")
                print(result["structured"]["analysis"])

                print("\nApproach:")
                print(result["structured"]["approach"])

                print("\nSolution:")
                print(result["structured"]["solution"])

                print("\nRecommendations:")
                print(result["structured"]["recommendations"])
            else:
                print("\nResult:")
                print(json.dumps(result, indent=2))

async def main():
    """Main function to test autonomous agents."""
    # Create agents
    researcher = await create_agent(
        name="Research Specialist",
        role="Research and analyze information",
        skills=["research", "analysis", "summarization"],
        model="google/gemini-2.0-flash-001"
    )

    developer = await create_agent(
        name="Code Developer",
        role="Write and optimize code",
        skills=["coding", "debugging", "optimization"],
        model="google/gemini-2.0-flash-001"
    )

    # Create tasks
    research_task = await create_task(
        title="Research PostgreSQL performance optimization",
        description="Research best practices for optimizing PostgreSQL performance for a web application with high read/write operations. Focus on indexing strategies, query optimization, and connection pooling.",
        required_skills=["research", "analysis"],
        priority=2
    )

    if research_task:
        coding_task = await create_task(
            title="Implement database connection pooling",
            description="Implement database connection pooling for a Python application using SQLAlchemy. The implementation should handle concurrent requests efficiently and prevent connection leaks.",
            required_skills=["coding", "optimization"],
            priority=1,
            parent_task_id=research_task["id"]  # This task depends on the research task
        )

    # Monitor task execution
    print("\nMonitoring task execution...")
    await monitor_tasks(interval=10, max_time=600)  # Check every 10 seconds for up to 10 minutes

    # Print final agent status
    agents = await get_agents()
    print("\n--- Agent Status ---")
    for agent in agents:
        print(f"Agent: {agent['name']} - Status: {agent['status']}")

if __name__ == "__main__":
    asyncio.run(main())
