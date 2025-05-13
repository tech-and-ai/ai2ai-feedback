import sqlite3
from datetime import datetime
import os

# Connect to the database
conn = sqlite3.connect('ai2ai_feedback.db')
conn.row_factory = sqlite3.Row
cursor = conn.cursor()

# Check completed tasks and their outputs
print("=== COMPLETED TASKS AND THEIR OUTPUTS ===")
cursor.execute('SELECT * FROM tasks WHERE status = "complete" ORDER BY completed_at DESC')
completed_tasks = cursor.fetchall()

if not completed_tasks:
    print("No completed tasks found.")
else:
    for task in completed_tasks:
        print(f"\nTask ID: {task['id']}")
        print(f"Title: {task['title']}")
        print(f"Description: {task['description']}")
        print(f"Result path: {task['result_path']}")
        
        # Check if the result path exists
        if task['result_path']:
            if os.path.exists(task['result_path']):
                if os.path.isdir(task['result_path']):
                    print(f"Output directory exists: {task['result_path']}")
                    # List files in the directory
                    files = os.listdir(task['result_path'])
                    if files:
                        print("Files in output directory:")
                        for file in files:
                            file_path = os.path.join(task['result_path'], file)
                            file_size = os.path.getsize(file_path)
                            print(f"  - {file} ({file_size} bytes)")
                    else:
                        print("Output directory is empty")
                else:
                    print(f"Output file exists: {task['result_path']}")
                    file_size = os.path.getsize(task['result_path'])
                    print(f"File size: {file_size} bytes")
                    
                    # If it's a text file, show the content
                    if task['result_path'].endswith('.txt') or task['result_path'].endswith('.md'):
                        try:
                            with open(task['result_path'], 'r') as f:
                                content = f.read()
                                print(f"Content: {content}")
                        except Exception as e:
                            print(f"Error reading file: {e}")
            else:
                print(f"Output path does not exist: {task['result_path']}")
        else:
            print("No result path specified")
    
    print(f"\nTotal completed tasks: {len(completed_tasks)}")

# Close connection
conn.close()
