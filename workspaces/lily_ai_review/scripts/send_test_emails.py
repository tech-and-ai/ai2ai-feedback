#!/usr/bin/env python3
"""
Script to send test emails via Supabase Edge Functions.
This script directly calls the Edge Functions to send actual emails.
"""

import os
import sys
import uuid
import json
import time
import logging
import requests
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def send_email(supabase_url, service_key, to_email, subject, html_content, text_content=None):
    """Send an email directly via the send-email Edge Function."""
    url = f"{supabase_url}/functions/v1/send-email"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {service_key}"
    }
    
    payload = {
        "to": to_email,
        "subject": subject,
        "html_content": html_content,
        "text_content": text_content
    }
    
    logger.info(f"Sending email: {subject}")
    response = requests.post(url, headers=headers, json=payload)
    
    if response.status_code == 200:
        logger.info(f"Email sent successfully: {subject}")
        return True
    else:
        logger.error(f"Failed to send email: {response.status_code} - {response.text}")
        return False

def send_welcome_email(supabase_url, service_key, to_email):
    """Send a welcome email."""
    logger.info("Sending welcome email...")
    
    subject = "Welcome to Research Assistant!"
    
    html_content = """
    <div style="font-family: 'Inter', sans-serif; max-width: 600px; margin: 0 auto; padding: 0; background-color: #2b1d3d; color: white; border-radius: 8px; overflow: hidden;">
      <!-- Header with Logo -->
      <div style="text-align: center; padding: 20px; background-image: linear-gradient(135deg, #2b1d3d 0%, #372554 100%);">
        <h1 style="color: white; margin: 0; font-size: 28px;">Welcome to Lily AI Research Assistant!</h1>
      </div>
      
      <!-- Main Content -->
      <div style="padding: 30px 20px; background-color: #2b1d3d;">
        <p style="color: white; font-size: 16px; line-height: 1.5; margin-bottom: 25px;">
          Thank you for verifying your email address. Your account is now fully activated and you can start using all the features of Lily AI Research Assistant.
        </p>
      
        <div style="text-align: center; margin: 30px 0;">
          <a href="https://researchassistant.uk/dashboard" style="background: linear-gradient(90deg, #6366f1, #8b5cf6); color: white; padding: 12px 24px; text-decoration: none; border-radius: 4px; font-weight: bold; display: inline-block;">
            Go to Dashboard
          </a>
        </div>
      
        <p style="color: white; font-size: 16px; line-height: 1.5; margin-bottom: 15px;">
          Here are some things you can do with Lily AI Research Assistant:
        </p>
        
        <ul style="color: white; font-size: 16px; line-height: 1.5; margin-bottom: 25px; padding-left: 20px;">
          <li style="margin-bottom: 8px;">Generate comprehensive research papers on any topic</li>
          <li style="margin-bottom: 8px;">Access high-quality sources and citations</li>
          <li style="margin-bottom: 8px;">Create custom research packs tailored to your needs</li>
          <li style="margin-bottom: 8px;">Get help with academic writing and research</li>
        </ul>
      
        <p style="color: white; font-size: 16px; line-height: 1.5;">
          If you have any questions or need assistance, please do not hesitate to contact our support team.
        </p>
      </div>
      
      <!-- Footer -->
      <div style="margin-top: 0; padding: 20px; border-top: 1px solid rgba(255, 255, 255, 0.1); background-color: #2b1d3d; color: rgba(255, 255, 255, 0.7);">
        <div style="text-align: center; margin-bottom: 15px;">
          <p style="margin-bottom: 15px; font-size: 14px;">
            Powered by Lily AI - Your AI Research Assistant for academic success.
          </p>
          <div>
            <!-- Social Links -->
            <a href="https://x.com/studyassistant" style="display: inline-block; margin: 0 8px; color: white; text-decoration: none;">
              <img src="https://researchassistant.uk/static/images/social/x-logo.png" alt="X" width="24" height="24" style="filter: brightness(0) invert(1);">
            </a>
            <a href="#" style="display: inline-block; margin: 0 8px; color: white; text-decoration: none;">
              <img src="https://researchassistant.uk/static/images/social/linkedin-logo.png" alt="LinkedIn" width="24" height="24" style="filter: brightness(0) invert(1);">
            </a>
            <a href="https://discord.gg/cWNNz8wt" style="display: inline-block; margin: 0 8px; color: white; text-decoration: none;">
              <img src="https://researchassistant.uk/static/images/social/discord-logo.png" alt="Discord" width="24" height="24" style="filter: brightness(0) invert(1);">
            </a>
          </div>
        </div>
        <div style="text-align: center; margin-top: 15px;">
          <p style="font-size: 12px; color: rgba(255, 255, 255, 0.5);">
            © 2025 researchassistant.uk - All rights reserved
          </p>
          <p style="font-size: 12px; margin-top: 5px;">
            <a href="https://researchassistant.uk/privacy" style="color: rgba(255, 255, 255, 0.7); text-decoration: none;">Privacy Policy</a> | 
            <a href="https://researchassistant.uk/terms" style="color: rgba(255, 255, 255, 0.7); text-decoration: none;">Terms of Service</a>
          </p>
        </div>
      </div>
    </div>
    """
    
    text_content = """
    Welcome to Lily AI Research Assistant!

    Thank you for verifying your email address. Your account is now fully activated and you can start using all the features of Lily AI Research Assistant.

    Here are some things you can do with Lily AI Research Assistant:
    - Generate comprehensive research papers on any topic
    - Access high-quality sources and citations
    - Create custom research packs tailored to your needs
    - Get help with academic writing and research

    If you have any questions or need assistance, please do not hesitate to contact our support team.

    © 2025 researchassistant.uk - All rights reserved
    Privacy Policy: https://researchassistant.uk/privacy
    Terms of Service: https://researchassistant.uk/terms
    """
    
    return send_email(supabase_url, service_key, to_email, subject, html_content, text_content)

def send_paper_queued_email(supabase_url, service_key, to_email):
    """Send a paper queued email."""
    logger.info("Sending paper queued email...")
    
    paper_id = str(uuid.uuid4())
    paper_title = f"Test Paper {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
    paper_topic = "Email Notification Testing"
    
    subject = "Your Research Paper is Queued - Lily AI"
    
    html_content = f"""
    <div style="font-family: 'Inter', sans-serif; max-width: 600px; margin: 0 auto; padding: 0; background-color: #2b1d3d; color: white; border-radius: 8px; overflow: hidden;">
      <!-- Header with Logo -->
      <div style="text-align: center; padding: 20px; background-image: linear-gradient(135deg, #2b1d3d 0%, #372554 100%);">
        <img src="https://researchassistant.uk/static/images/logo-lily.png" alt="Lily AI Logo" style="height: 60px; margin-bottom: 15px;">
        <h1 style="color: white; margin: 0; font-size: 24px;">Your Research Paper is Queued</h1>
      </div>
      
      <!-- Main Content -->
      <div style="padding: 30px 20px; background-color: #2b1d3d;">
        <p style="color: white; font-size: 16px; line-height: 1.5; margin-bottom: 25px;">
          Hello,
        </p>
        
        <p style="color: white; font-size: 16px; line-height: 1.5; margin-bottom: 25px;">
          We're excited to let you know that your research paper on <strong>{paper_topic}</strong> has been successfully queued for generation. Your paper will be processed shortly.
        </p>
        
        <div style="background: rgba(255, 255, 255, 0.1); border-radius: 8px; padding: 20px; margin-bottom: 25px;">
          <h3 style="color: white; margin-top: 0; margin-bottom: 15px; font-size: 18px;">Paper Details:</h3>
          <p style="color: white; font-size: 16px; line-height: 1.5; margin: 0 0 10px 0;">
            <strong>Title:</strong> {paper_title}
          </p>
          <p style="color: white; font-size: 16px; line-height: 1.5; margin: 0 0 10px 0;">
            <strong>Topic:</strong> {paper_topic}
          </p>
          <p style="color: white; font-size: 16px; line-height: 1.5; margin: 0 0 10px 0;">
            <strong>Status:</strong> <span style="color: #f59e0b;">Queued</span>
          </p>
          <p style="color: white; font-size: 16px; line-height: 1.5; margin: 0;">
            <strong>Requested:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
          </p>
        </div>
        
        <div style="text-align: center; margin: 30px 0;">
          <a href="https://researchassistant.uk/papers/{paper_id}" style="background: linear-gradient(90deg, #6366f1, #8b5cf6); color: white; padding: 12px 24px; text-decoration: none; border-radius: 4px; font-weight: bold; display: inline-block;">
            View Paper Status
          </a>
        </div>
        
        <p style="color: white; font-size: 16px; line-height: 1.5;">
          We'll notify you when your paper starts processing and when it's ready for download. Thank you for using Lily AI Research Assistant!
        </p>
      </div>
      
      <!-- Footer -->
      <div style="margin-top: 0; padding: 20px; border-top: 1px solid rgba(255, 255, 255, 0.1); background-color: #2b1d3d; color: rgba(255, 255, 255, 0.7);">
        <div style="text-align: center; margin-bottom: 15px;">
          <p style="margin-bottom: 15px; font-size: 14px;">
            Powered by Lily AI - Your AI Research Assistant for academic success.
          </p>
          <div>
            <!-- Social Links -->
            <a href="https://x.com/studyassistant" style="display: inline-block; margin: 0 8px; color: white; text-decoration: none;">
              <img src="https://researchassistant.uk/static/images/social/x-logo.png" alt="X" width="24" height="24" style="filter: brightness(0) invert(1);">
            </a>
            <a href="#" style="display: inline-block; margin: 0 8px; color: white; text-decoration: none;">
              <img src="https://researchassistant.uk/static/images/social/linkedin-logo.png" alt="LinkedIn" width="24" height="24" style="filter: brightness(0) invert(1);">
            </a>
            <a href="https://discord.gg/cWNNz8wt" style="display: inline-block; margin: 0 8px; color: white; text-decoration: none;">
              <img src="https://researchassistant.uk/static/images/social/discord-logo.png" alt="Discord" width="24" height="24" style="filter: brightness(0) invert(1);">
            </a>
          </div>
        </div>
        <div style="text-align: center; margin-top: 15px;">
          <p style="font-size: 12px; color: rgba(255, 255, 255, 0.5);">
            © 2025 researchassistant.uk - All rights reserved
          </p>
          <p style="font-size: 12px; margin-top: 5px;">
            <a href="https://researchassistant.uk/privacy" style="color: rgba(255, 255, 255, 0.7); text-decoration: none;">Privacy Policy</a> | 
            <a href="https://researchassistant.uk/terms" style="color: rgba(255, 255, 255, 0.7); text-decoration: none;">Terms of Service</a>
          </p>
        </div>
      </div>
    </div>
    """
    
    text_content = f"""
    Your Research Paper is Queued - Lily AI

    Hello,

    We're excited to let you know that your research paper on {paper_topic} has been successfully queued for generation. Your paper will be processed shortly.

    Paper Details:
    - Title: {paper_title}
    - Topic: {paper_topic}
    - Status: Queued
    - Requested: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

    You can view your paper status at: https://researchassistant.uk/papers/{paper_id}

    We'll notify you when your paper starts processing and when it's ready for download. Thank you for using Lily AI Research Assistant!

    Powered by Lily AI - Your AI Research Assistant for academic success.

    © 2025 researchassistant.uk - All rights reserved
    Privacy Policy: https://researchassistant.uk/privacy
    Terms of Service: https://researchassistant.uk/terms
    """
    
    return send_email(supabase_url, service_key, to_email, subject, html_content, text_content)

def main():
    """Main function to send test emails."""
    if len(sys.argv) < 3:
        print("Usage: python send_test_emails.py <supabase_url> <service_key> [email]")
        return 1
    
    supabase_url = sys.argv[1]
    service_key = sys.argv[2]
    to_email = sys.argv[3] if len(sys.argv) > 3 else "pantaleone@btinternet.com"
    
    logger.info(f"Sending test emails to {to_email}")
    
    # Send welcome email
    send_welcome_email(supabase_url, service_key, to_email)
    time.sleep(2)
    
    # Send paper queued email
    send_paper_queued_email(supabase_url, service_key, to_email)
    
    logger.info("All test emails have been sent")
    return 0

if __name__ == "__main__":
    sys.exit(main())
