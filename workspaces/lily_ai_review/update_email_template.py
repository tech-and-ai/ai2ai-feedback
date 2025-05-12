#!/usr/bin/env python3
"""
Script to update email templates with embedded images.
"""

from app.utils.supabase_client import get_supabase_client
import base64
import os

def get_image_as_base64(image_path):
    """Convert an image to base64."""
    try:
        with open(image_path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode('utf-8')
    except Exception as e:
        print(f"Error reading image {image_path}: {str(e)}")
        return None

def update_welcome_email_template():
    """Update the welcome email template with embedded images."""
    # Get Supabase client
    supabase = get_supabase_client()
    
    # Get the welcome email template
    response = supabase.table('saas_notification_templates').select('*').eq('name', 'welcome_email').execute()
    
    if not response.data or len(response.data) == 0:
        print("Welcome email template not found")
        return
    
    template = response.data[0]
    html_content = template['html_content']
    
    # Get base64 encoded images
    static_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static', 'images', 'social')
    
    x_logo_path = os.path.join(static_dir, 'x-logo.png')
    linkedin_logo_path = os.path.join(static_dir, 'linkedin-logo.png')
    discord_logo_path = os.path.join(static_dir, 'discord-logo.png')
    
    x_logo_base64 = get_image_as_base64(x_logo_path)
    linkedin_logo_base64 = get_image_as_base64(linkedin_logo_path)
    discord_logo_base64 = get_image_as_base64(discord_logo_path)
    
    if not x_logo_base64 or not linkedin_logo_base64 or not discord_logo_base64:
        print("Failed to load one or more images")
        return
    
    # Replace image URLs with embedded base64 images
    html_content = html_content.replace(
        'src="https://researchassistant.uk/static/images/social/x-logo.png"',
        f'src="data:image/png;base64,{x_logo_base64}"'
    )
    
    html_content = html_content.replace(
        'src="https://researchassistant.uk/static/images/social/linkedin-logo.png"',
        f'src="data:image/png;base64,{linkedin_logo_base64}"'
    )
    
    html_content = html_content.replace(
        'src="https://researchassistant.uk/static/images/social/discord-logo.png"',
        f'src="data:image/png;base64,{discord_logo_base64}"'
    )
    
    # Update the template
    supabase.table('saas_notification_templates').update({
        'html_content': html_content,
        'version': template['version'] + 1
    }).eq('id', template['id']).execute()
    
    print("Welcome email template updated with embedded images")

if __name__ == '__main__':
    update_welcome_email_template()
