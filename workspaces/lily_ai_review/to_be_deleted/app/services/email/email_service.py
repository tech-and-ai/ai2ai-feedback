"""
Email service for sending emails to users.

This service provides methods for sending various types of emails to users.
"""

import os
import logging
from datetime import datetime
from typing import Optional
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import smtplib

# Configure logging
logger = logging.getLogger(__name__)

class EmailService:
    """Service for sending emails to users."""

    def __init__(self):
        """Initialize the email service."""
        # Get email configuration from environment variables
        self.smtp_server = os.getenv("SMTP_SERVER", "smtp.gmail.com")
        self.smtp_port = int(os.getenv("SMTP_PORT", "587"))
        self.smtp_username = os.getenv("SMTP_USER", os.getenv("SMTP_USERNAME", ""))
        self.smtp_password = os.getenv("SMTP_PASSWORD", "")
        self.from_email = os.getenv("FROM_EMAIL", "noreply@researchassistant.uk")
        self.from_name = os.getenv("FROM_NAME", "Research Assistant")

        # Check if email is configured
        self.is_configured = (
            self.smtp_server and
            self.smtp_port and
            self.smtp_username and
            self.smtp_password
        )

        if not self.is_configured:
            logger.warning("Email service is not fully configured. Emails will be logged but not sent.")

    def send_email(self, to_email: str, subject: str, html_content: str, text_content: Optional[str] = None) -> bool:
        """
        Send an email to a user.

        Args:
            to_email: The recipient's email address
            subject: The email subject
            html_content: The HTML content of the email
            text_content: The plain text content of the email (optional)

        Returns:
            True if the email was sent successfully, False otherwise
        """
        if not self.is_configured:
            logger.info(f"Email would be sent to {to_email} with subject: {subject}")
            logger.info(f"HTML content: {html_content}")
            return True

        try:
            # Create message
            msg = MIMEMultipart("alternative")
            msg["Subject"] = subject
            msg["From"] = f"{self.from_name} <{self.from_email}>"
            msg["To"] = to_email

            # Add text content if provided, otherwise use a simple version of the HTML
            if text_content:
                msg.attach(MIMEText(text_content, "plain"))
            else:
                # Create a simple text version from the HTML
                simple_text = html_content.replace("<br>", "\n").replace("<p>", "").replace("</p>", "\n\n")
                msg.attach(MIMEText(simple_text, "plain"))

            # Add HTML content
            msg.attach(MIMEText(html_content, "html"))

            # Send email
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.smtp_username, self.smtp_password)
                server.send_message(msg)

            logger.info(f"Email sent to {to_email} with subject: {subject}")
            return True

        except Exception as e:
            logger.error(f"Error sending email to {to_email}: {str(e)}")
            return False

    def send_subscription_confirmation(self, email: str, tier: str, papers_limit: int, end_date: Optional[str] = None) -> bool:
        """
        Send a subscription confirmation email to a user.

        Args:
            email: The user's email address
            tier: The subscription tier
            papers_limit: The number of papers included in the subscription
            end_date: The subscription end date (optional)

        Returns:
            True if the email was sent successfully, False otherwise
        """
        try:
            # Format the end date if provided
            end_date_formatted = "N/A"
            if end_date:
                try:
                    end_date_dt = datetime.fromisoformat(end_date.replace("Z", "+00:00"))
                    end_date_formatted = end_date_dt.strftime("%d %B %Y")
                except (ValueError, TypeError):
                    end_date_formatted = end_date

            # Create email subject
            subject = f"Welcome to Research Assistant {tier.capitalize()} Subscription"

            # Create email content
            html_content = f"""
            <html>
            <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
                <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                    <h1 style="color: #6c5ce7; text-align: center;">Thank You for Subscribing!</h1>

                    <p>Dear Researcher,</p>

                    <p>Thank you for subscribing to Research Assistant's <strong>{tier.capitalize()}</strong> plan. Your subscription is now active!</p>

                    <div style="background-color: #f5f5f5; border-radius: 5px; padding: 15px; margin: 20px 0;">
                        <h2 style="color: #6c5ce7; margin-top: 0;">Subscription Details</h2>
                        <p><strong>Plan:</strong> {tier.capitalize()}</p>
                        <p><strong>Paper Credits:</strong> {papers_limit}</p>
                        <p><strong>Valid Until:</strong> {end_date_formatted}</p>
                    </div>

                    <p>You can now start generating research papers right away. Just log in to your account and click on "New Research Paper" to get started.</p>

                    <p>If you have any questions or need assistance, please don't hesitate to contact our support team at <a href="mailto:support@researchassistant.uk">support@researchassistant.uk</a>.</p>

                    <p>Happy researching!</p>

                    <p>Best regards,<br>
                    The Research Assistant Team</p>

                    <div style="border-top: 1px solid #ddd; margin-top: 20px; padding-top: 20px; font-size: 12px; color: #777; text-align: center;">
                        <p>This email was sent to {email}. If you did not subscribe to Research Assistant, please contact us immediately.</p>
                    </div>
                </div>
            </body>
            </html>
            """

            # Send the email
            return self.send_email(email, subject, html_content)

        except Exception as e:
            logger.error(f"Error sending subscription confirmation email: {str(e)}")
            return False
