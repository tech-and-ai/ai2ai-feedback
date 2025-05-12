#!/usr/bin/env python
"""Test script to verify BASE_URL environment variable."""
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Print environment variables
print(f"BASE_URL: {os.getenv('BASE_URL', 'Not set')}")
print(f"SUPABASE_URL: {os.getenv('SUPABASE_URL', 'Not set')}")
print(f"SUPABASE_PROJECT_URL: {os.getenv('SUPABASE_PROJECT_URL', 'Not set')}") 