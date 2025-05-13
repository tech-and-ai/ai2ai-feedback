import sqlite3
from datetime import datetime

# Connect to the database
conn = sqlite3.connect('ai2ai_feedback.db')
conn.row_factory = sqlite3.Row
cursor = conn.cursor()

# Check tasks in queue (not started)
print("=== TASKS IN QUEUE (NOT STARTED) ===")
cursor.execute('SELECT * FROM tasks WHERE status = "not_started" ORDER BY created_at DESC')
queued_tasks = cursor.fetchall()

if not queued_tasks:
    print("No tasks in queue.")
else:
    for task in queued_tasks:
        print(f"\nTask ID: {task['id']}")
        print(f"Title: {task['title']}")
        print(f"Description: {task['description']}")
        print(f"Complexity: {task['complexity']}")
        print(f"Priority: {task['priority']}")
        print(f"Created at: {task['created_at']}")
        
        if task['assigned_agent_id']:
            print(f"Assigned to: {task['assigned_agent_id']}")
        else:
            print("Not assigned to any agent")
    
    print(f"\nTotal tasks in queue: {len(queued_tasks)}")

# Check in-progress tasks
print("\n\n=== IN-PROGRESS TASKS ===")
cursor.execute('SELECT * FROM tasks WHERE status != "not_started" AND status != "complete" ORDER BY updated_at DESC')
in_progress_tasks = cursor.fetchall()

if not in_progress_tasks:
    print("No in-progress tasks.")
else:
    for task in in_progress_tasks:
        print(f"\nTask ID: {task['id']}")
        print(f"Title: {task['title']}")
        print(f"Status: {task['status']}")
        print(f"Progress: {task['stage_progress']}%")
        print(f"Created at: {task['created_at']}")
        print(f"Updated at: {task['updated_at']}")
        
        if task['assigned_agent_id']:
            print(f"Assigned to: {task['assigned_agent_id']}")
        else:
            print("Not assigned to any agent")
    
    print(f"\nTotal in-progress tasks: {len(in_progress_tasks)}")

# Close connection
conn.close()
