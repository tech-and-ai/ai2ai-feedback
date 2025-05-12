#!/usr/bin/env python3
"""
Script to check notification template content.
"""

from app.utils.supabase_client import get_supabase_client

def main():
    """Main function to check template content."""
    # Get Supabase client
    supabase = get_supabase_client()
    
    # Get the welcome email template
    response = supabase.table('saas_notification_templates').select('*').eq('name', 'welcome_email').execute()
    
    if response.data and len(response.data) > 0:
        template = response.data[0]
        print(f"Template: {template['name']} (ID: {template['id']})")
        print(f"Subject: {template['subject']}")
        print("\nHTML Content:")
        print(template['html_content'])
        print("\nText Content:")
        print(template['text_content'])
    else:
        print("Welcome email template not found")

if __name__ == '__main__':
    main()
