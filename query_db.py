import sqlite3
import os

# Connect to the database
db_path = 'ai2ai_feedback.db'
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Get column names for tasks table
cursor.execute("PRAGMA table_info(tasks)")
task_columns = [col[1] for col in cursor.fetchall()]
print("Task table columns:", task_columns)

# Get column names for agents table
cursor.execute("PRAGMA table_info(agents)")
agent_columns = [col[1] for col in cursor.fetchall()]
print("Agent table columns:", agent_columns)

# Query all tasks
cursor.execute("SELECT * FROM tasks")
tasks = cursor.fetchall()

print("\nAll Tasks:")
if not tasks:
    print("No tasks found in the database.")
else:
    for task in tasks:
        print("ID:", task[0])
        print("Title:", task[1])
        print("Description:", task[2])
        print("Status:", task[3])
        print("Stage Progress:", task[4])
        print("Created at:", task[5])
        print("Updated at:", task[6])
        print("Completed at:", task[7])
        print("Assigned to:", task[8])
        print("Result path:", task[9])
        print("Priority:", task[10])
        print("-" * 50)

# Query all agents
cursor.execute("SELECT * FROM agents")
agents = cursor.fetchall()

print("\nAll Agents:")
if not agents:
    print("No agents found in the database.")
else:
    for agent in agents:
        print("ID:", agent[0])
        print("Name:", agent[1])
        print("Model:", agent[2])
        print("Endpoint:", agent[3])
        print("Status:", agent[4])
        print("Min Complexity:", agent[5])
        print("Max Complexity:", agent[6])
        print("Workspace Path:", agent[7])
        print("Created at:", agent[8])
        print("Last active:", agent[9])
        print("-" * 50)

# Get task updates
cursor.execute("SELECT * FROM task_updates")
updates = cursor.fetchall()

print("\nTask Updates:")
if not updates:
    print("No task updates found in the database.")
else:
    # Get column names for task_updates table
    cursor.execute("PRAGMA table_info(task_updates)")
    update_columns = [col[1] for col in cursor.fetchall()]
    print("Task updates columns:", update_columns)

    for update in updates:
        print("ID:", update[0])
        print("Task ID:", update[1])
        print("Agent ID:", update[2])
        print("Update Type:", update[3])
        print("Content:", update[4])
        print("Timestamp:", update[5])
        print("-" * 50)

conn.close()
