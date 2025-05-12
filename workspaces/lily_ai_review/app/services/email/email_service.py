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
        <div style="font-family: 'Inter', sans-serif; max-width: 600px; margin: 0 auto; padding: 0; background-color: #2b1d3d; color: white; border-radius: 8px; overflow: hidden;">
          <!-- Header with Logo -->
          <div style="text-align: center; padding: 20px; background-image: linear-gradient(135deg, #2b1d3d 0%, #372554 100%);">
            <h1 style="color: white; margin: 0; font-size: 28px;">Welcome to Lily AI Research Assistant!</h1>
          </div>

          <!-- Main Content -->
          <div style="padding: 30px 20px; background-color: #2b1d3d;">
            <p style="color: white; font-size: 16px; line-height: 1.5; margin-bottom: 25px;">
              Thank you for joining Research Assistant. Your account is now active and you can start using all the features of Lily AI Research Assistant.
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
        <div style="font-family: 'Inter', sans-serif; max-width: 600px; margin: 0 auto; padding: 0; background-color: #2b1d3d; color: white; border-radius: 8px; overflow: hidden;">
          <!-- Header with Logo -->
          <div style="text-align: center; padding: 20px; background-image: linear-gradient(135deg, #2b1d3d 0%, #372554 100%);">
            <h1 style="color: white; margin: 0; font-size: 28px;">Thank You for Subscribing!</h1>
          </div>

          <!-- Main Content -->
          <div style="padding: 30px 20px; background-color: #2b1d3d;">
            <p style="color: white; font-size: 16px; line-height: 1.5; margin-bottom: 25px;">
              Dear Premium Member,
            </p>

            <p style="color: white; font-size: 16px; line-height: 1.5; margin-bottom: 25px;">
              Thank you for subscribing to Research Assistant's Premium plan. Your subscription is now active!
            </p>

            <div style="background: rgba(255, 255, 255, 0.1); border-radius: 8px; padding: 20px; margin-bottom: 25px;">
              <h3 style="color: white; margin-top: 0; margin-bottom: 15px; font-size: 18px;">Subscription Details:</h3>
              <p style="color: white; font-size: 16px; line-height: 1.5; margin: 0 0 10px 0;">
                <strong>Plan:</strong> Premium
              </p>
              <p style="color: white; font-size: 16px; line-height: 1.5; margin: 0 0 10px 0;">
                <strong>Paper Credits:</strong> 10 per month
              </p>
            </div>

            <div style="text-align: center; margin: 30px 0;">
              <a href="https://researchassistant.uk/dashboard" style="background: linear-gradient(90deg, #6366f1, #8b5cf6); color: white; padding: 12px 24px; text-decoration: none; border-radius: 4px; font-weight: bold; display: inline-block;">
                Go to Dashboard
              </a>
            </div>

            <p style="color: white; font-size: 16px; line-height: 1.5;">
              You can now start generating research papers right away. Just log in to your account and click on "New Research Paper" to get started.
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
        <div style="font-family: 'Inter', sans-serif; max-width: 600px; margin: 0 auto; padding: 0; background-color: #2b1d3d; color: white; border-radius: 8px; overflow: hidden;">
          <!-- Header with Logo -->
          <div style="text-align: center; padding: 20px; background-image: linear-gradient(135deg, #2b1d3d 0%, #372554 100%);">
            <h1 style="color: white; margin: 0; font-size: 28px;">Paper Credits Added!</h1>
          </div>

          <!-- Main Content -->
          <div style="padding: 30px 20px; background-color: #2b1d3d;">
            <p style="color: white; font-size: 16px; line-height: 1.5; margin-bottom: 25px;">
              Dear Researcher,
            </p>

            <p style="color: white; font-size: 16px; line-height: 1.5; margin-bottom: 25px;">
              Thank you for your purchase. We've added <strong>{credit_count}</strong> paper credits to your account.
            </p>

            <div style="background: rgba(255, 255, 255, 0.1); border-radius: 8px; padding: 20px; margin-bottom: 25px;">
              <h3 style="color: white; margin-top: 0; margin-bottom: 15px; font-size: 18px;">Credit Details:</h3>
              <p style="color: white; font-size: 16px; line-height: 1.5; margin: 0 0 10px 0;">
                <strong>Credits Added:</strong> {credit_count}
              </p>
              <p style="color: white; font-size: 16px; line-height: 1.5; margin: 0 0 10px 0;">
                <strong>Expiration:</strong> Never (these credits never expire)
              </p>
            </div>

            <div style="text-align: center; margin: 30px 0;">
              <a href="https://researchassistant.uk/dashboard" style="background: linear-gradient(90deg, #6366f1, #8b5cf6); color: white; padding: 12px 24px; text-decoration: none; border-radius: 4px; font-weight: bold; display: inline-block;">
                Go to Dashboard
              </a>
            </div>

            <p style="color: white; font-size: 16px; line-height: 1.5;">
              These credits will be used after your monthly allocation is exhausted.
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

        return self.send_email(email, subject, html_content)
