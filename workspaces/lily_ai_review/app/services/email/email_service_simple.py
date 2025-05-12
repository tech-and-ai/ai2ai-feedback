"""
Email service for sending emails to users.
"""
import os
import logging
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional

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
    
    def send_email(self, to_email: str, subject: str, html_content: str) -> bool:
        """
        Send an email to a user.
        
        Args:
            to_email: The recipient's email address
            subject: The email subject
            html_content: The HTML content of the email
            
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
    
    def send_welcome_email(self, email: str, is_oauth: bool = False) -> bool:
        """
        Send a welcome email to a new user.
        
        Args:
            email: The user's email address
            is_oauth: Whether the user signed up with OAuth
            
        Returns:
            True if the email was sent successfully, False otherwise
        """
        subject = "Welcome to Research Assistant!"
        
        html_content = f"""
        <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                <h1 style="color: #6c5ce7; text-align: center;">Welcome to Research Assistant!</h1>
                
                <p>Dear Researcher,</p>
                
                <p>Thank you for signing up with Research Assistant. We're excited to have you on board!</p>
                
                <p>You now have access to our powerful research tools that will help you create amazing papers.</p>
                
                <div style="background-color: #f5f5f5; border-radius: 5px; padding: 15px; margin: 20px 0;">
                    <h2 style="color: #6c5ce7; margin-top: 0;">Getting Started</h2>
                    <p>1. Log in to your account</p>
                    <p>2. Go to your dashboard</p>
                    <p>3. Click on "New Research Paper" to begin</p>
                </div>
                
                <p>If you have any questions or need assistance, please don't hesitate to contact our support team.</p>
                
                <p>Happy researching!</p>
                
                <p>Best regards,<br>
                The Research Assistant Team</p>
            </div>
        </body>
        </html>
        """
        
        return self.send_email(email, subject, html_content)
    
    def send_subscription_confirmation_email(self, email: str) -> bool:
        """
        Send a subscription confirmation email to a user.
        
        Args:
            email: The user's email address
            
        Returns:
            True if the email was sent successfully, False otherwise
        """
        subject = "Thank You for Your Premium Subscription!"
        
        html_content = f"""
        <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                <h1 style="color: #6c5ce7; text-align: center;">Thank You for Subscribing!</h1>
                
                <p>Dear Premium Member,</p>
                
                <p>Thank you for subscribing to Research Assistant's Premium plan. Your subscription is now active!</p>
                
                <div style="background-color: #f5f5f5; border-radius: 5px; padding: 15px; margin: 20px 0;">
                    <h2 style="color: #6c5ce7; margin-top: 0;">Subscription Details</h2>
                    <p><strong>Plan:</strong> Premium</p>
                    <p><strong>Paper Credits:</strong> 10 per month</p>
                </div>
                
                <p>You can now start generating research papers right away. Just log in to your account and click on "New Research Paper" to get started.</p>
                
                <p>Best regards,<br>
                The Research Assistant Team</p>
            </div>
        </body>
        </html>
        """
        
        return self.send_email(email, subject, html_content)
    
    def send_credits_confirmation_email(self, email: str, credit_count: int) -> bool:
        """
        Send a confirmation email for paper credit purchases.
        
        Args:
            email: The user's email address
            credit_count: The number of credits purchased
            
        Returns:
            True if the email was sent successfully, False otherwise
        """
        subject = "Your Paper Credits Purchase"
        
        html_content = f"""
        <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                <h1 style="color: #6c5ce7; text-align: center;">Paper Credits Added!</h1>
                
                <p>Dear Researcher,</p>
                
                <p>Thank you for your purchase. We've added <strong>{credit_count}</strong> paper credits to your account.</p>
                
                <div style="background-color: #f5f5f5; border-radius: 5px; padding: 15px; margin: 20px 0;">
                    <h2 style="color: #6c5ce7; margin-top: 0;">Credit Details</h2>
                    <p><strong>Credits Added:</strong> {credit_count}</p>
                    <p><strong>Expiration:</strong> Never (these credits never expire)</p>
                </div>
                
                <p>These credits will be used after your monthly allocation is exhausted.</p>
                
                <p>Best regards,<br>
                The Research Assistant Team</p>
            </div>
        </body>
        </html>
        """
        
        return self.send_email(email, subject, html_content)
