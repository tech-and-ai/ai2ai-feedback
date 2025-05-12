"""
Script to manually process a task using the OpenRouter API.
"""

import os
import json
import asyncio
import requests
import uuid
from datetime import datetime

# API endpoints
API_BASE = "http://localhost:8001"
TASKS_ENDPOINT = f"{API_BASE}/autonomous/tasks"
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "")

async def get_pending_tasks():
    """Get all pending tasks."""
    try:
        response = requests.get(f"{TASKS_ENDPOINT}?status=pending")
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"Error getting pending tasks: {str(e)}")
        return []

async def process_task(task_id: str):
    """Process a task using the OpenRouter API."""
    try:
        # Get task details
        response = requests.get(f"{TASKS_ENDPOINT}/{task_id}")
        response.raise_for_status()
        task = response.json()
        
        print(f"Processing task: {task['title']}")
        
        # Update task status to in_progress
        update_response = requests.post(
            f"{API_BASE}/autonomous/tasks/{task_id}/update",
            json={"status": "in_progress", "assigned_to": "manual_processor"}
        )
        
        # Prepare the prompt
        prompt = f"""
You are an autonomous AI agent tasked with solving the following problem:

TASK:
Title: {task['title']}
Description: {task['description']}

Please complete this task to the best of your ability. Provide a detailed response that includes:
1. Your analysis of the task
2. Your approach to solving it
3. The actual solution or implementation
4. Any recommendations or next steps

FORMAT YOUR RESPONSE AS FOLLOWS:
ANALYSIS: [Your analysis of the task]
APPROACH: [Your approach to solving it]
SOLUTION: [The actual solution or implementation]
RECOMMENDATIONS: [Any recommendations or next steps]
"""
        
        # Call OpenRouter API
        headers = {
            "Authorization": f"Bearer {OPENROUTER_API_KEY}",
            "Content-Type": "application/json"
        }
        
        openrouter_response = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers=headers,
            json={
                "model": "google/gemini-2.0-flash-001",
                "messages": [
                    {"role": "user", "content": prompt}
                ]
            }
        )
        
        if openrouter_response.status_code != 200:
            print(f"Error from OpenRouter: {openrouter_response.text}")
            return
        
        result = openrouter_response.json()
        response_text = result["choices"][0]["message"]["content"]
        
        print("\nResponse from OpenRouter:")
        print(response_text)
        
        # Parse the response
        sections = {
            "analysis": "",
            "approach": "",
            "solution": "",
            "recommendations": ""
        }
        
        current_section = None
        
        for line in response_text.split('\n'):
            if line.startswith("ANALYSIS:"):
                current_section = "analysis"
                sections[current_section] = line.replace("ANALYSIS:", "").strip()
            elif line.startswith("APPROACH:"):
                current_section = "approach"
                sections[current_section] = line.replace("APPROACH:", "").strip()
            elif line.startswith("SOLUTION:"):
                current_section = "solution"
                sections[current_section] = line.replace("SOLUTION:", "").strip()
            elif line.startswith("RECOMMENDATIONS:"):
                current_section = "recommendations"
                sections[current_section] = line.replace("RECOMMENDATIONS:", "").strip()
            elif current_section:
                sections[current_section] += "\n" + line
        
        # Clean up and trim whitespace
        for key in sections:
            sections[key] = sections[key].strip()
        
        # Update task with result
        result_data = {
            "full_response": response_text,
            "structured": sections
        }
        
        # Mark task as completed
        update_response = requests.post(
            f"{API_BASE}/autonomous/tasks/{task_id}/update",
            json={
                "status": "completed",
                "result": json.dumps(result_data),
                "completed_at": datetime.utcnow().isoformat()
            }
        )
        
        print(f"\nTask {task_id} completed successfully!")
        
    except Exception as e:
        print(f"Error processing task: {str(e)}")

async def main():
    """Main function."""
    # Get pending tasks
    tasks = await get_pending_tasks()
    
    if not tasks:
        print("No pending tasks found.")
        return
    
    # Process the first pending task
    await process_task(tasks[0]["id"])

if __name__ == "__main__":
    asyncio.run(main())
