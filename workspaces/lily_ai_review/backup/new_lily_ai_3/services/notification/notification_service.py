"""
Notification Service

This module provides the main service for sending notifications based on events.
"""

import logging
import smtplib
import os
import json
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
from typing import Dict, Any, List, Optional, Union
import asyncio

from app.services.notification.template_manager import TemplateManager
from app.services.notification.user_preference_manager import UserPreferenceManager

logger = logging.getLogger(__name__)

class NotificationService:
    """
    Central service for sending notifications based on events.
    """

    def __init__(self, db_client, smtp_config: Dict[str, Any] = None):
        """
        Initialize with database client and SMTP configuration.

        Args:
            db_client: Supabase client or other database client
            smtp_config: SMTP configuration dictionary
        """
        self.db = db_client
        self.smtp_config = smtp_config or self._get_default_smtp_config()
        self.template_manager = TemplateManager(db_client)
        self.preference_manager = UserPreferenceManager(db_client)

    async def notify(self, event_type: str, user_id: str, data: Dict[str, Any] = None,
                    background_tasks = None) -> Dict[str, Any]:
        """
        Send a notification based on an event type.

        Args:
            event_type: Type of event (e.g., 'user.signup', 'paper.completed')
            user_id: ID of the user to notify
            data: Dictionary of data to include in the template
            background_tasks: Optional FastAPI BackgroundTasks for async processing

        Returns:
            Dictionary with notification status
        """
        try:
            # Check if user has opted out of this notification type
            can_notify = await self.preference_manager.can_notify(user_id, event_type)
            if not can_notify:
                logger.info(f"User {user_id} has opted out of {event_type} notifications")
                return {
                    "success": False,
                    "message": "User has opted out of this notification type",
                    "event_type": event_type,
                    "user_id": user_id
                }

            # Get user email
            user_data = await self._get_user_data(user_id)
            if not user_data or not user_data.get('email'):
                logger.error(f"Failed to get email for user {user_id}")
                return {
                    "success": False,
                    "message": "User email not found",
                    "event_type": event_type,
                    "user_id": user_id
                }

            recipient_email = user_data['email']

            # Get template for this event type
            template = await self.template_manager.get_template_for_event(event_type)
            if not template:
                logger.error(f"No template found for event type {event_type}")
                return {
                    "success": False,
                    "message": "No template found for this event type",
                    "event_type": event_type,
                    "user_id": user_id
                }

            # Prepare data for template rendering
            template_data = {
                "user": user_data,
                **(data or {})
            }

            # Render the template
            rendered = await self.template_manager.render_template(template, template_data)

            # Send the email
            if background_tasks:
                # Add to background tasks if provided
                background_tasks.add_task(
                    self.send_email,
                    recipient_email=recipient_email,
                    subject=rendered['subject'],
                    html_content=rendered['html_content'],
                    text_content=rendered['text_content']
                )

                # Log the notification
                await self.log_notification(
                    user_id=user_id,
                    event_type=event_type,
                    template_id=template['id'],
                    recipient_email=recipient_email,
                    status='queued'
                )

                return {
                    "success": True,
                    "message": "Notification queued for delivery",
                    "event_type": event_type,
                    "user_id": user_id,
                    "recipient_email": recipient_email
                }
            else:
                # Send immediately
                result = await self.send_email(
                    recipient_email=recipient_email,
                    subject=rendered['subject'],
                    html_content=rendered['html_content'],
                    text_content=rendered['text_content']
                )

                # Log the notification
                await self.log_notification(
                    user_id=user_id,
                    event_type=event_type,
                    template_id=template['id'],
                    recipient_email=recipient_email,
                    status='sent' if result.get('success') else 'failed',
                    error_message=result.get('error')
                )

                return {
                    "success": result.get('success', False),
                    "message": result.get('message', 'Unknown error'),
                    "event_type": event_type,
                    "user_id": user_id,
                    "recipient_email": recipient_email
                }

        except Exception as e:
            logger.exception(f"Error sending notification: {str(e)}")
            return {
                "success": False,
                "message": f"Error sending notification: {str(e)}",
                "event_type": event_type,
                "user_id": user_id
            }

    async def send_email(self, recipient_email: str, subject: str, html_content: str,
                        text_content: str = None) -> Dict[str, Any]:
        """
        Send an email using the configured SMTP provider.

        Args:
            recipient_email: Email address of the recipient
            subject: Email subject
            html_content: HTML content of the email
            text_content: Plain text content (auto-generated from HTML if None)

        Returns:
            Dictionary with email sending status
        """
        try:
            # Validate email format
            if not self._is_valid_email(recipient_email):
                return {
                    "success": False,
                    "message": f"Invalid email address: {recipient_email}",
                    "error": "Invalid email format"
                }

            # Create message container
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = self.smtp_config['sender_email']
            msg['To'] = recipient_email

            # Add plain text part if provided, otherwise create from HTML
            if text_content is None:
                # Simple conversion from HTML to text
                text_content = html_content.replace('<br>', '\n').replace('</p>', '\n\n').replace('<li>', '\n- ')
                # Remove HTML tags
                import re
                text_content = re.sub('<[^<]+?>', '', text_content)

            # Attach parts to message
            part1 = MIMEText(text_content, 'plain')
            part2 = MIMEText(html_content, 'html')
            msg.attach(part1)
            msg.attach(part2)

            # Check if we're in development mode
            if self.smtp_config.get('dev_mode', False):
                # Save to file instead of sending
                return await self._save_email_to_file(recipient_email, subject, html_content, text_content)

            # Connect to SMTP server
            logger.info(f"Connecting to SMTP server {self.smtp_config['server']}:{self.smtp_config['port']}")
            server = smtplib.SMTP(self.smtp_config['server'], self.smtp_config['port'], timeout=10)

            # Enable debug output if configured
            if self.smtp_config.get('debug', False):
                server.set_debuglevel(1)

            # Identify ourselves to the server
            server.ehlo()

            # If TLS is enabled, start TLS
            if self.smtp_config.get('use_tls', True):
                server.starttls()
                server.ehlo()  # Re-identify ourselves over TLS connection

            # If authentication is required
            if self.smtp_config.get('username') and self.smtp_config.get('password'):
                server.login(self.smtp_config['username'], self.smtp_config['password'])

            # Send the message
            server.sendmail(self.smtp_config['sender_email'], recipient_email, msg.as_string())
            server.quit()

            logger.info(f"Email sent to {recipient_email}")
            return {
                "success": True,
                "message": f"Email sent to {recipient_email}"
            }

        except Exception as e:
            logger.error(f"Failed to send email: {str(e)}")

            # Try to save to file as fallback
            if not self.smtp_config.get('dev_mode', False):
                logger.info(f"Falling back to saving email to file for {recipient_email}")
                return await self._save_email_to_file(recipient_email, subject, html_content, text_content)

            return {
                "success": False,
                "message": f"Failed to send email to {recipient_email}",
                "error": str(e)
            }

    async def log_notification(self, user_id: str, event_type: str, template_id: str,
                              recipient_email: str, status: str, error_message: str = None,
                              metadata: Dict[str, Any] = None) -> str:
        """
        Log a notification attempt to the database.

        Args:
            user_id: ID of the user
            event_type: Type of event
            template_id: ID of the template used
            recipient_email: Email address of the recipient
            status: Status of the notification ('sent', 'failed', etc.)
            error_message: Error message if any
            metadata: Additional data to store

        Returns:
            ID of the created log entry
        """
        try:
            log_data = {
                'user_id': user_id,
                'event_type': event_type,
                'template_id': template_id,
                'recipient_email': recipient_email,
                'status': status,
                'error_message': error_message,
                'metadata': json.dumps(metadata) if metadata else None,
                'sent_at': datetime.now().isoformat()
            }

            response = self.db.table('saas_notification_logs').insert(log_data).execute()

            if response.data and len(response.data) > 0:
                logger.debug(f"Logged notification: {event_type} to {recipient_email}")
                return response.data[0]['id']
            else:
                logger.error(f"Failed to log notification: {event_type} to {recipient_email}")
                return None

        except Exception as e:
            logger.error(f"Error logging notification: {str(e)}")
            return None

    async def _get_user_data(self, user_id: str) -> Dict[str, Any]:
        """
        Get user data from the database.

        Args:
            user_id: ID of the user

        Returns:
            User data dictionary
        """
        try:
            # Get user from auth.users table
            response = self.db.from_('auth.users').select('*').eq('id', user_id).execute()

            if response.data and len(response.data) > 0:
                user = response.data[0]

                # Format user data
                return {
                    'id': user['id'],
                    'email': user['email'],
                    'username': user.get('user_metadata', {}).get('username', user['email'].split('@')[0]),
                    'first_name': user.get('user_metadata', {}).get('first_name', ''),
                    'last_name': user.get('user_metadata', {}).get('last_name', ''),
                    'full_name': f"{user.get('user_metadata', {}).get('first_name', '')} {user.get('user_metadata', {}).get('last_name', '')}".strip(),
                    'created_at': user['created_at'],
                    'last_sign_in_at': user['last_sign_in_at']
                }
            else:
                logger.error(f"User not found: {user_id}")
                return None

        except Exception as e:
            logger.error(f"Error getting user data: {str(e)}")
            return None

    async def _save_email_to_file(self, recipient_email: str, subject: str,
                                 html_content: str, text_content: str) -> Dict[str, Any]:
        """
        Save email content to a file for development/debugging purposes.

        Args:
            recipient_email: Email address of the recipient
            subject: Email subject
            html_content: HTML content of the email
            text_content: Plain text content

        Returns:
            Dictionary with save status
        """
        try:
            # Create dev_emails directory if it doesn't exist
            dev_email_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))), 'dev_emails')
            os.makedirs(dev_email_dir, exist_ok=True)

            # Create a unique filename
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            safe_email = recipient_email.replace('@', '_at_').replace('.', '_dot_')
            filename = f"{timestamp}_{safe_email}.html"
            filepath = os.path.join(dev_email_dir, filename)

            # Extract verification link if present
            verification_link = None
            import re
            link_match = re.search(r'href="([^"]*verify[^"]*?)"', html_content)
            if link_match:
                verification_link = link_match.group(1)

            # Create a wrapper HTML with metadata
            wrapper_html = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Email to: {recipient_email}</title>
    <style>
        .metadata {{ background: #f0f0f0; padding: 10px; margin-bottom: 20px; border: 1px solid #ccc; }}
        .email-content {{ border: 1px solid #ddd; padding: 20px; }}
        .text-version {{ background: #f8f8f8; padding: 10px; margin-top: 20px; white-space: pre-wrap; }}
    </style>
</head>
<body>
    <div class="metadata">
        <h2>Email Metadata</h2>
        <p><strong>To:</strong> {recipient_email}</p>
        <p><strong>Subject:</strong> {subject}</p>
        <p><strong>Date:</strong> {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}</p>
        {f'<p><strong>Verification Link:</strong> <a href="{verification_link}">{verification_link}</a></p>' if verification_link else ''}
    </div>

    <h2>HTML Version</h2>
    <div class="email-content">
        {html_content}
    </div>

    <h2>Text Version</h2>
    <div class="text-version">
        {text_content}
    </div>
</body>
</html>"""

            # Write to file
            with open(filepath, 'w') as f:
                f.write(wrapper_html)

            logger.info(f"Email saved to file: {filepath}")
            return {
                "success": True,
                "message": f"Email saved to file: {filepath}",
                "filepath": filepath
            }

        except Exception as e:
            logger.error(f"Error saving email to file: {str(e)}")
            return {
                "success": False,
                "message": f"Error saving email to file: {str(e)}",
                "error": str(e)
            }

    def _is_valid_email(self, email: str) -> bool:
        """
        Validate email format using regex pattern.

        Args:
            email: Email address to validate

        Returns:
            True if the email is valid, False otherwise
        """
        import re
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return bool(re.match(pattern, email))

    def _get_default_smtp_config(self) -> Dict[str, Any]:
        """
        Get default SMTP configuration from environment variables.

        Returns:
            SMTP configuration dictionary
        """
        return {
            'server': os.environ.get('SMTP_SERVER', 'mail.privateemail.com'),
            'port': int(os.environ.get('SMTP_PORT', '587')),
            'username': os.environ.get('SMTP_USER', 'lily@lilyai.uk'),
            'password': os.environ.get('SMTP_PASSWORD', ''),
            'sender_email': os.environ.get('EMAIL_SENDER', 'lily@lilyai.uk'),
            'use_tls': os.environ.get('SMTP_TLS', 'True').lower() in ('true', '1', 't'),
            'debug': os.environ.get('SMTP_DEBUG', 'False').lower() in ('true', '1', 't'),
            'dev_mode': os.environ.get('EMAIL_DEV_MODE', 'False').lower() in ('true', '1', 't')
        }
