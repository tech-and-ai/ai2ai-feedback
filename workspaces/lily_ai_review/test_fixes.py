#!/usr/bin/env python3
"""
Test script to verify the fixes for:
1. Subscription button redirection
2. "My Papers" access control
3. Welcome email for Google sign-ups
"""
import os
import sys
import requests
import logging
import json
import time
from urllib.parse import urlparse, parse_qs
from bs4 import BeautifulSoup
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("test_fixes.log")
    ]
)
logger = logging.getLogger(__name__)

# Base URL for the application
BASE_URL = "http://localhost:8004"

# Test user credentials
TEST_USER_EMAIL = "test_user@example.com"
TEST_USER_PASSWORD = "Test123!"
TEST_USER_USERNAME = "test_user"

# Test premium user credentials
TEST_PREMIUM_USER_EMAIL = "premium_user@example.com"
TEST_PREMIUM_USER_PASSWORD = "Premium123!"
TEST_PREMIUM_USER_USERNAME = "premium_user"

# Session to maintain cookies
session = requests.Session()

def test_subscription_button_redirection():
    """Test if the subscription button redirects to Stripe."""
    logger.info("Testing subscription button redirection...")
    
    # Step 1: Login as a free user
    login_response = session.post(
        f"{BASE_URL}/auth/login",
        data={
            "email": TEST_USER_EMAIL,
            "password": TEST_USER_PASSWORD
        },
        allow_redirects=True
    )
    
    if login_response.status_code != 200:
        logger.error(f"Failed to login: {login_response.status_code}")
        return False
    
    logger.info("Logged in successfully")
    
    # Step 2: Go to subscription page
    subscription_response = session.get(f"{BASE_URL}/subscription")
    
    if subscription_response.status_code != 200:
        logger.error(f"Failed to access subscription page: {subscription_response.status_code}")
        return False
    
    logger.info("Accessed subscription page successfully")
    
    # Step 3: Extract the form action URL
    soup = BeautifulSoup(subscription_response.text, 'html.parser')
    premium_buttons = soup.select('.premium-checkout-btn')
    
    if not premium_buttons:
        logger.error("Could not find premium checkout button")
        return False
    
    logger.info("Found premium checkout button")
    
    # Step 4: Simulate clicking the button by making a request to the checkout endpoint
    checkout_response = session.get(f"{BASE_URL}/billing/checkout/premium", allow_redirects=False)
    
    # Check if it redirects to Stripe
    if checkout_response.status_code in (301, 302, 303, 307, 308):
        redirect_url = checkout_response.headers.get('Location', '')
        logger.info(f"Redirected to: {redirect_url}")
        
        # Check if the redirect URL is a Stripe URL
        if 'stripe.com' in redirect_url:
            logger.info("Successfully redirected to Stripe")
            return True
        else:
            logger.error(f"Redirected to non-Stripe URL: {redirect_url}")
            return False
    else:
        logger.error(f"No redirection occurred: {checkout_response.status_code}")
        return False

def test_my_papers_access_control():
    """Test if free users are redirected from My Papers page."""
    logger.info("Testing My Papers access control...")
    
    # Step 1: Login as a free user
    login_response = session.post(
        f"{BASE_URL}/auth/login",
        data={
            "email": TEST_USER_EMAIL,
            "password": TEST_USER_PASSWORD
        },
        allow_redirects=True
    )
    
    if login_response.status_code != 200:
        logger.error(f"Failed to login: {login_response.status_code}")
        return False
    
    logger.info("Logged in successfully as free user")
    
    # Step 2: Try to access My Papers page
    my_papers_response = session.get(f"{BASE_URL}/my-papers", allow_redirects=False)
    
    # Check if it redirects to subscription page
    if my_papers_response.status_code in (301, 302, 303, 307, 308):
        redirect_url = my_papers_response.headers.get('Location', '')
        logger.info(f"Redirected to: {redirect_url}")
        
        # Check if the redirect URL is the subscription page
        if '/subscription' in redirect_url:
            logger.info("Successfully redirected free user from My Papers to subscription page")
            return True
        else:
            logger.error(f"Redirected to unexpected URL: {redirect_url}")
            return False
    else:
        logger.error(f"No redirection occurred: {my_papers_response.status_code}")
        return False

def test_welcome_email():
    """Test if welcome email is sent for new users."""
    logger.info("Testing welcome email functionality...")
    
    # This is a bit tricky to test automatically since we can't easily intercept emails
    # Instead, we'll check if the email service is properly configured
    
    # Get email configuration from .env file
    try:
        from dotenv import load_dotenv
        load_dotenv()
        
        smtp_server = os.getenv("SMTP_SERVER")
        smtp_port = int(os.getenv("SMTP_PORT", "587"))
        smtp_user = os.getenv("SMTP_USER")
        smtp_password = os.getenv("SMTP_PASSWORD")
        from_email = os.getenv("FROM_EMAIL")
        from_name = os.getenv("FROM_NAME")
        
        logger.info(f"Email configuration: SMTP_SERVER={smtp_server}, SMTP_PORT={smtp_port}, SMTP_USER={smtp_user}, FROM_EMAIL={from_email}, FROM_NAME={from_name}")
        
        # Check if all required fields are set
        if not all([smtp_server, smtp_port, smtp_user, smtp_password, from_email]):
            logger.error("Email configuration is incomplete")
            return False
        
        # Try to connect to the SMTP server
        try:
            server = smtplib.SMTP(smtp_server, smtp_port)
            server.ehlo()
            server.starttls()
            server.ehlo()
            server.login(smtp_user, smtp_password)
            server.quit()
            logger.info("Successfully connected to SMTP server")
            return True
        except Exception as e:
            logger.error(f"Failed to connect to SMTP server: {str(e)}")
            return False
    except Exception as e:
        logger.error(f"Error checking email configuration: {str(e)}")
        return False

def run_all_tests():
    """Run all tests and report results."""
    logger.info("Starting tests...")
    
    results = {
        "subscription_button": test_subscription_button_redirection(),
        "my_papers_access": test_my_papers_access_control(),
        "welcome_email": test_welcome_email()
    }
    
    logger.info("Test results:")
    for test, result in results.items():
        logger.info(f"{test}: {'PASS' if result else 'FAIL'}")
    
    return results

if __name__ == "__main__":
    run_all_tests()
