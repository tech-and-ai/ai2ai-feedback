#!/usr/bin/env python3
"""
Script to check notification templates in the database.
"""

from app.utils.supabase_client import get_supabase_client

def main():
    """Main function to check templates."""
    # Get Supabase client
    supabase = get_supabase_client()
    
    # Get all templates
    response = supabase.table('saas_notification_templates').select('*').execute()
    
    print('Templates:')
    for template in response.data:
        print(f"- {template['name']} (ID: {template['id']})")
    
    # Get all event mappings
    response = supabase.table('saas_notification_events').select('*').execute()
    
    print('\nEvent Mappings:')
    for event in response.data:
        print(f"- {event['event_type']} -> Template ID: {event['template_id']}")

if __name__ == '__main__':
    main()
