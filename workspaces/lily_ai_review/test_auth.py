"""
Test script for the auth service.
"""
import os
import sys
import logging
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("test_auth.log")
    ]
)

logger = logging.getLogger("test_auth")

# Test auth service
try:
    from auth.service_simple import AuthService
    auth_service = AuthService()
    logger.info("AuthService initialized successfully")
except Exception as e:
    logger.error(f"Error initializing AuthService: {e}")
    sys.exit(1)

# Test subscription service
try:
    from app.services.billing.subscription_service_simple import SubscriptionService
    subscription_service = SubscriptionService()
    logger.info("SubscriptionService initialized successfully")
except Exception as e:
    logger.error(f"Error initializing SubscriptionService: {e}")
    sys.exit(1)

# Test email service
try:
    from app.services.email.email_service_simple import EmailService
    email_service = EmailService()
    logger.info("EmailService initialized successfully")
except Exception as e:
    logger.error(f"Error initializing EmailService: {e}")
    sys.exit(1)

logger.info("All services initialized successfully")
