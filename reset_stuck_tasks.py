import sqlite3
from datetime import datetime

# Connect to the database
conn = sqlite3.connect('ai2ai_feedback.db')
conn.row_factory = sqlite3.Row
cursor = conn.cursor()

print("=== Resetting stuck tasks and agents ===")

# Get all busy agents
cursor.execute('SELECT * FROM agents WHERE status = "busy"')
busy_agents = cursor.fetchall()

for agent in busy_agents:
    print(f"Resetting agent: {agent['name']} (ID: {agent['id']})")

    # Get tasks assigned to this agent
    cursor.execute('SELECT * FROM tasks WHERE assigned_agent_id = ?', (agent['id'],))
    tasks = cursor.fetchall()

    for task in tasks:
        if task['status'] != 'complete':
            print(f"  Resetting task: {task['title']} (ID: {task['id']})")

            # Reset task to not_started
            cursor.execute(
                'UPDATE tasks SET status = "not_started", stage_progress = 0, assigned_agent_id = NULL, updated_at = ? WHERE id = ?',
                (datetime.now().isoformat(), task['id'])
            )

            # Add task update with a unique ID
            import uuid
            update_id = str(uuid.uuid4())
            cursor.execute(
                'INSERT INTO task_updates (id, task_id, agent_id, update_type, content, timestamp) VALUES (?, ?, ?, ?, ?, ?)',
                (update_id, task['id'], agent['id'], "status_change", "Task reset due to being stuck", datetime.now().isoformat())
            )

    # Reset agent to available
    cursor.execute(
        'UPDATE agents SET status = "available", last_active = ? WHERE id = ?',
        (datetime.now().isoformat(), agent['id'])
    )

# Commit changes
conn.commit()

# Verify changes
cursor.execute('SELECT * FROM agents')
agents = cursor.fetchall()
print("\nAgent statuses after reset:")
for agent in agents:
    print(f"- {agent['name']}: {agent['status']}")

cursor.execute('SELECT * FROM tasks WHERE status != "complete"')
tasks = cursor.fetchall()
print("\nTask statuses after reset:")
for task in tasks:
    print(f"- {task['title']}: {task['status']}, Assigned to: {task['assigned_agent_id'] or 'None'}")

# Close connection
conn.close()

print("\nReset complete. All stuck tasks and agents have been reset.")
