import sqlite3

# Connect to the database
conn = sqlite3.connect('ai2ai_feedback.db')
conn.row_factory = sqlite3.Row
cursor = conn.cursor()

# Check task updates
print("=== TASK UPDATES ===")
cursor.execute('SELECT * FROM task_updates ORDER BY timestamp DESC')
updates = cursor.fetchall()

if not updates:
    print("No task updates found.")
else:
    for update in updates:
        print(f"\nUpdate ID: {update['id']}")
        print(f"Task ID: {update['task_id']}")
        print(f"Agent ID: {update['agent_id']}")
        print(f"Update type: {update['update_type']}")
        print(f"Content: {update['content']}")
        print(f"Timestamp: {update['timestamp']}")

    print(f"\nTotal updates: {len(updates)}")

# Close connection
conn.close()
