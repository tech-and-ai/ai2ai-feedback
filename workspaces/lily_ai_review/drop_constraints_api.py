import os
import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Get Supabase API key
api_key = os.environ.get('SUPABASE_API_KEY')
project_id = 'brxpkhpkitfzecvmwzgz'

# SQL query to drop constraints
sql_query = """
-- Drop foreign key constraints on saas_paper_credits
ALTER TABLE IF EXISTS saas_paper_credits DROP CONSTRAINT IF EXISTS saas_paper_credits_user_id_fkey;

-- Drop foreign key constraints on saas_notification_settings
ALTER TABLE IF EXISTS saas_notification_settings DROP CONSTRAINT IF EXISTS saas_notification_settings_user_id_fkey;

-- Drop foreign key constraints on saas_paper_credit_usage
ALTER TABLE IF EXISTS saas_paper_credit_usage DROP CONSTRAINT IF EXISTS saas_paper_credit_usage_user_id_fkey;

-- Drop foreign key constraints on saas_paper_usage_tracking
ALTER TABLE IF EXISTS saas_paper_usage_tracking DROP CONSTRAINT IF EXISTS saas_paper_usage_tracking_user_id_fkey;

-- Drop foreign key constraints on saas_research_context
ALTER TABLE IF EXISTS saas_research_context DROP CONSTRAINT IF EXISTS saas_research_context_user_id_fkey;

-- Drop foreign key constraints on tool_todo_items
ALTER TABLE IF EXISTS tool_todo_items DROP CONSTRAINT IF EXISTS todo_items_created_by_fkey;

-- Drop foreign key constraints on saas_user_notification_preferences
ALTER TABLE IF EXISTS saas_user_notification_preferences DROP CONSTRAINT IF EXISTS saas_user_notification_preferences_user_id_fkey;

-- Drop foreign key constraints on saas_job_tracking
ALTER TABLE IF EXISTS saas_job_tracking DROP CONSTRAINT IF EXISTS saas_job_tracking_user_id_fkey;

-- Drop foreign key constraints on saas_notification_logs
ALTER TABLE IF EXISTS saas_notification_logs DROP CONSTRAINT IF EXISTS saas_notification_logs_user_id_fkey;

-- Drop foreign key constraints on saas_paper_reviews
ALTER TABLE IF EXISTS saas_paper_reviews DROP CONSTRAINT IF EXISTS saas_paper_reviews_user_id_fkey;

-- Drop foreign key constraints on saas_papers
ALTER TABLE IF EXISTS saas_papers DROP CONSTRAINT IF EXISTS saas_papers_user_id_fkey;

-- Drop foreign key constraints on saas_research_sessions
ALTER TABLE IF EXISTS saas_research_sessions DROP CONSTRAINT IF EXISTS saas_research_sessions_user_id_fkey;
"""

# API endpoint
url = f"https://api.supabase.com/v1/projects/{project_id}/database/query"

# Headers
headers = {
    "Authorization": f"Bearer {api_key}",
    "Content-Type": "application/json"
}

# Request body
data = {
    "query": sql_query
}

# Make the request
print("Sending request to Supabase API...")
response = requests.post(url, headers=headers, json=data)

# Print the response
print(f"Status code: {response.status_code}")
print(f"Response: {response.text}")

if response.status_code == 200:
    print("Constraints dropped successfully!")
else:
    print("Failed to drop constraints.")
