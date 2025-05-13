import sqlite3
import json
import os
from datetime import datetime

# Connect to the database
conn = sqlite3.connect('ai2ai_feedback.db')
cursor = conn.cursor()

# Create test output directory
test_output_path = '/home/admin/projects/ai2ai-feedback/test_output'
os.makedirs(test_output_path, exist_ok=True)

# Create a test file
with open(os.path.join(test_output_path, 'mockup.txt'), 'w') as f:
    f.write('This is a test mockup file')

# Insert a completed task with the test output path
task_id = 'task2'
cursor.execute('''
    INSERT INTO tasks (
        id, title, description, complexity, status, stage_progress, 
        created_at, updated_at, completed_at, assigned_agent_id, 
        priority, allow_collaboration, human_review_required, 
        output_formats, result_path
    ) VALUES (
        ?, ?, ?, ?, ?, ?, 
        datetime('now'), datetime('now'), datetime('now'), ?, 
        ?, ?, ?, 
        ?, ?
    )
''', (
    task_id,
    'Create UI mockups',
    'Create UI mockups for the new dashboard',
    3,
    'complete',
    100,
    'agent1',
    5,
    0,
    1,
    json.dumps(['zip', 'pdf']),
    test_output_path
))

# Commit and close
conn.commit()
print('Task created successfully')
conn.close()
