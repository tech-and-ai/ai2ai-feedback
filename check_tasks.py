import sqlite3
import json
from datetime import datetime

# Connect to the database
conn = sqlite3.connect('ai2ai_feedback.db')
conn.row_factory = sqlite3.Row
cursor = conn.cursor()

# Check completed tasks
print("=== COMPLETED TASKS ===")
cursor.execute('SELECT * FROM tasks WHERE status = "complete"')
completed_tasks = cursor.fetchall()

if not completed_tasks:
    print("No completed tasks found.")
else:
    for task in completed_tasks:
        print(f"\nTask ID: {task['id']}")
        print(f"Title: {task['title']}")
        print(f"Description: {task['description']}")
        print(f"Status: {task['status']}")
        print(f"Progress: {task['stage_progress']}%")
        print(f"Created at: {task['created_at']}")
        print(f"Completed at: {task['completed_at']}")
        print(f"Assigned agent: {task['assigned_agent_id']}")
        print(f"Result path: {task['result_path']}")
        
        if task['output_formats']:
            formats = json.loads(task['output_formats'])
            print(f"Output formats: {', '.join(formats)}")
        
        # Check task updates
        cursor.execute('SELECT * FROM task_updates WHERE task_id = ? ORDER BY timestamp', (task['id'],))
        updates = cursor.fetchall()
        
        if updates:
            print("\nTask Updates:")
            for update in updates:
                print(f"- {update['timestamp']}: {update['update_type']} - {update['content']}")

# Check in-progress tasks
print("\n\n=== IN-PROGRESS TASKS ===")
cursor.execute('SELECT * FROM tasks WHERE status != "complete" AND status != "not_started"')
in_progress_tasks = cursor.fetchall()

if not in_progress_tasks:
    print("No in-progress tasks found.")
else:
    for task in in_progress_tasks:
        print(f"\nTask ID: {task['id']}")
        print(f"Title: {task['title']}")
        print(f"Status: {task['status']}")
        print(f"Progress: {task['stage_progress']}%")
        print(f"Created at: {task['created_at']}")
        print(f"Assigned agent: {task['assigned_agent_id']}")

# Check agents
print("\n\n=== AGENTS ===")
cursor.execute('SELECT * FROM agents')
agents = cursor.fetchall()

if not agents:
    print("No agents found.")
else:
    for agent in agents:
        print(f"\nAgent ID: {agent['id']}")
        print(f"Name: {agent['name']}")
        print(f"Model: {agent['model']}")
        print(f"Status: {agent['status']}")
        print(f"Complexity range: {agent['min_complexity']}-{agent['max_complexity']}")
        print(f"Last active: {agent['last_active']}")

# Close connection
conn.close()
