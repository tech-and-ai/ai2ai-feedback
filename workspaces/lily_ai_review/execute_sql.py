import os
import psycopg2
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Get database connection details from environment variables
db_url = os.environ.get('SUPABASE_DATABASE_URL')

if not db_url:
    # Try to construct the URL from individual components
    db_host = os.environ.get('SUPABASE_DB_HOST', 'brxpkhpkitfzecvmwzgz.supabase.co')
    db_port = os.environ.get('SUPABASE_DB_PORT', '5432')
    db_name = os.environ.get('SUPABASE_DB_NAME', 'postgres')
    db_user = os.environ.get('SUPABASE_DB_USER', 'postgres')
    db_password = os.environ.get('SUPABASE_DB_PASSWORD', 'postgres')
    
    db_url = f"postgresql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"

try:
    # Connect to the database
    print(f"Connecting to database: {db_url}")
    conn = psycopg2.connect(db_url)
    
    # Create a cursor
    cur = conn.cursor()
    
    # Read the SQL file
    with open('drop_constraints.sql', 'r') as f:
        sql = f.read()
    
    # Execute the SQL
    print("Executing SQL...")
    cur.execute(sql)
    
    # Commit the changes
    conn.commit()
    
    print("SQL executed successfully!")
    
    # Close the cursor and connection
    cur.close()
    conn.close()
    
except Exception as e:
    print(f"Error: {e}")
