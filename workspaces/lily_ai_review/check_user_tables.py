#!/usr/bin/env python3
"""
Script to check tables with user_id columns.
"""

from app.utils.supabase_client import get_supabase_client

def main():
    """Main function to check tables with user_id columns."""
    # Get Supabase client
    supabase = get_supabase_client()
    
    # Check saas_users table
    print("Checking saas_users table...")
    try:
        response = supabase.table("saas_users").select("*").execute()
        print(f"Found {len(response.data)} rows in saas_users table")
    except Exception as e:
        print(f"Error checking saas_users table: {str(e)}")
    
    # Check saas_user_subscriptions table
    print("\nChecking saas_user_subscriptions table...")
    try:
        response = supabase.table("saas_user_subscriptions").select("*").execute()
        print(f"Found {len(response.data)} rows in saas_user_subscriptions table")
    except Exception as e:
        print(f"Error checking saas_user_subscriptions table: {str(e)}")
    
    # Check saas_papers table
    print("\nChecking saas_papers table...")
    try:
        response = supabase.table("saas_papers").select("*").execute()
        print(f"Found {len(response.data)} rows in saas_papers table")
    except Exception as e:
        print(f"Error checking saas_papers table: {str(e)}")
    
    # Check saas_paper_credits table
    print("\nChecking saas_paper_credits table...")
    try:
        response = supabase.table("saas_paper_credits").select("*").execute()
        print(f"Found {len(response.data)} rows in saas_paper_credits table")
    except Exception as e:
        print(f"Error checking saas_paper_credits table: {str(e)}")
    
    # Check saas_paper_credit_usage table
    print("\nChecking saas_paper_credit_usage table...")
    try:
        response = supabase.table("saas_paper_credit_usage").select("*").execute()
        print(f"Found {len(response.data)} rows in saas_paper_credit_usage table")
    except Exception as e:
        print(f"Error checking saas_paper_credit_usage table: {str(e)}")
    
    # Check saas_notification_logs table
    print("\nChecking saas_notification_logs table...")
    try:
        response = supabase.table("saas_notification_logs").select("*").execute()
        print(f"Found {len(response.data)} rows in saas_notification_logs table")
    except Exception as e:
        print(f"Error checking saas_notification_logs table: {str(e)}")
    
    # Check saas_job_tracking table
    print("\nChecking saas_job_tracking table...")
    try:
        response = supabase.table("saas_job_tracking").select("*").execute()
        print(f"Found {len(response.data)} rows in saas_job_tracking table")
    except Exception as e:
        print(f"Error checking saas_job_tracking table: {str(e)}")

if __name__ == '__main__':
    main()
