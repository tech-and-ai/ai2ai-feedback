import sqlite3

# Connect to the database
conn = sqlite3.connect('ai2ai_feedback.db')
conn.row_factory = sqlite3.Row
cursor = conn.cursor()

# Check agent status
cursor.execute('SELECT * FROM agents WHERE model = "gemma3:4b"')
agent = cursor.fetchone()
print(f'Agent: {agent["name"]}, Status: {agent["status"]}, Model: {agent["model"]}')

# Check what task the agent is working on
cursor.execute('SELECT * FROM tasks WHERE assigned_agent_id = "agent1"')
task = cursor.fetchone()
if task:
    print(f'Working on: {task["title"]}, Status: {task["status"]}, Progress: {task["stage_progress"]}%')
else:
    print("Not working on any task")

# Close connection
conn.close()
