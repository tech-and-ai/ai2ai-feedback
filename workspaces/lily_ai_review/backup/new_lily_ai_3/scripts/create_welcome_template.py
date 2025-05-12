#!/usr/bin/env python3
"""
Script to create or update the welcome email template in the database.
"""

import os
import sys
import logging
from pathlib import Path

# Add the parent directory to the path so we can import from the app
sys.path.append(str(Path(__file__).parent.parent))

from new_lily_ai.services.database.supabase_client import get_supabase_client

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def create_welcome_template():
    """Create or update the welcome email template."""
    # Get Supabase client
    supabase = get_supabase_client()
    
    # Check if the template already exists
    response = supabase.table('saas_notification_templates').select('*').eq('name', 'welcome_email').execute()
    
    # HTML content for the welcome email
    html_content = """
    <div style="font-family: 'Inter', sans-serif; max-width: 600px; margin: 0 auto; padding: 20px; color: #333;">
        <div style="text-align: center; padding: 20px; background-color: #f8f9fa; border-radius: 8px; margin-bottom: 20px;">
            <h1 style="color: #4a6cf7; margin: 0; font-size: 28px;">Welcome to Lily AI Research Assistant!</h1>
        </div>
        
        <div style="padding: 20px; background-color: #fff; border-radius: 8px; border: 1px solid #e9ecef; margin-bottom: 20px;">
            <h2 style="color: #333; margin-top: 0;">Thank you for joining us!</h2>
            
            <p>Dear {{ user.name or user.username }},</p>
            
            <p>We're thrilled to welcome you to Lily AI Research Assistant! Your account has been successfully created and verified.</p>
            
            <p>With Lily AI, you can:</p>
            
            <ul style="padding-left: 20px;">
                <li>Conduct in-depth research on various topics</li>
                <li>Generate comprehensive research papers</li>
                <li>Receive AI guidance throughout your research process</li>
                <li>Access a wealth of knowledge across multiple disciplines</li>
            </ul>
            
            <div style="text-align: center; margin: 30px 0;">
                <a href="https://researchassistant.uk/dashboard" style="background-color: #4a6cf7; color: white; padding: 12px 24px; text-decoration: none; border-radius: 4px; font-weight: bold;">Go to Dashboard</a>
            </div>
            
            <p>If you have any questions or need assistance, please don't hesitate to contact our support team.</p>
            
            <p>Best regards,<br>The Lily AI Team</p>
        </div>
        
        <div style="text-align: center; padding: 20px; color: #6c757d; font-size: 14px;">
            <p>Follow us on social media:</p>
            <div style="margin-bottom: 15px;">
                <a href="#" style="margin: 0 10px; text-decoration: none;">
                    <img src="https://researchassistant.uk/static/images/social/x-logo.png" alt="X" width="24" height="24" style="vertical-align: middle;">
                </a>
                <a href="#" style="margin: 0 10px; text-decoration: none;">
                    <img src="https://researchassistant.uk/static/images/social/linkedin-logo.png" alt="LinkedIn" width="24" height="24" style="vertical-align: middle;">
                </a>
                <a href="#" style="margin: 0 10px; text-decoration: none;">
                    <img src="https://researchassistant.uk/static/images/social/discord-logo.png" alt="Discord" width="24" height="24" style="vertical-align: middle;">
                </a>
            </div>
            <p>&copy; 2025 Lily AI Research Assistant. All rights reserved.</p>
        </div>
    </div>
    """
    
    # Plain text content for the welcome email
    text_content = """
    Welcome to Lily AI Research Assistant!
    
    Dear {{ user.name or user.username }},
    
    We're thrilled to welcome you to Lily AI Research Assistant! Your account has been successfully created and verified.
    
    With Lily AI, you can:
    - Conduct in-depth research on various topics
    - Generate comprehensive research papers
    - Receive AI guidance throughout your research process
    - Access a wealth of knowledge across multiple disciplines
    
    Visit your dashboard: https://researchassistant.uk/dashboard
    
    If you have any questions or need assistance, please don't hesitate to contact our support team.
    
    Best regards,
    The Lily AI Team
    
    © 2025 Lily AI Research Assistant. All rights reserved.
    """
    
    # Template data
    template_data = {
        'name': 'welcome_email',
        'description': 'Email sent to users after they verify their email address',
        'subject': 'Welcome to Lily AI Research Assistant!',
        'html_content': html_content,
        'text_content': text_content,
        'is_active': True
    }
    
    if response.data and len(response.data) > 0:
        # Update existing template
        template = response.data[0]
        logger.info(f"Updating existing welcome email template (ID: {template['id']})")
        
        # Update with new version
        template_data['version'] = template['version'] + 1
        supabase.table('saas_notification_templates').update(template_data).eq('id', template['id']).execute()
        logger.info("Welcome email template updated successfully")
    else:
        # Create new template
        logger.info("Creating new welcome email template")
        template_data['version'] = 1
        response = supabase.table('saas_notification_templates').insert(template_data).execute()
        
        if response.data and len(response.data) > 0:
            logger.info(f"Welcome email template created successfully (ID: {response.data[0]['id']})")
        else:
            logger.error("Failed to create welcome email template")

if __name__ == '__main__':
    create_welcome_template()
