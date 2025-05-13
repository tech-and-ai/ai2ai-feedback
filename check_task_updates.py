import sqlite3

# Connect to the database
conn = sqlite3.connect('ai2ai_feedback.db')
conn.row_factory = sqlite3.Row
cursor = conn.cursor()

# Get the task ID for the current task
cursor.execute('SELECT id FROM tasks WHERE assigned_agent_id = "agent1"')
task = cursor.fetchone()

if task:
    task_id = task['id']
    print(f"Task ID: {task_id}")
    
    # Get task updates
    cursor.execute('SELECT * FROM task_updates WHERE task_id = ? ORDER BY timestamp DESC LIMIT 10', (task_id,))
    updates = cursor.fetchall()
    
    if updates:
        print("\nTask Updates:")
        for update in updates:
            print(f"- {update['timestamp']}: {update['update_type']} - {update['content'][:100]}...")
    else:
        print("No updates found for this task")
else:
    print("No task found assigned to agent1")

# Close connection
conn.close()
