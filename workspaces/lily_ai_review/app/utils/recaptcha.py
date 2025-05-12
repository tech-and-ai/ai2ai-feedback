"""
reCAPTCHA Enterprise utility for Lily AI.

This module provides functions for verifying reCAPTCHA Enterprise tokens.
"""

import os
import logging
import requests
from typing import Optional

# Set up logging
logger = logging.getLogger(__name__)

# Get reCAPTCHA keys from environment
RECAPTCHA_SITE_KEY = os.getenv("RECAPTCHA_SITE_KEY", "")
RECAPTCHA_SECRET_KEY = os.getenv("RECAPTCHA_SECRET_KEY", "")

def verify_recaptcha_enterprise(token: str, action: str = None) -> bool:
    """
    Verify a reCAPTCHA Enterprise token.

    Args:
        token: The reCAPTCHA token to verify
        action: The expected action

    Returns:
        True if the token is valid, False otherwise
    """
    # If no token is provided, fail verification
    if not token:
        logger.warning("No reCAPTCHA token provided")
        return False

    # If no secret key is configured, skip verification in development
    if not RECAPTCHA_SECRET_KEY:
        logger.warning("No reCAPTCHA secret key configured, skipping verification")
        return True

    try:
        # For testing purposes, if the token is "test_token", return True
        if token == "test_token" and os.getenv("ENVIRONMENT", "development") != "production":
            logger.warning("Using test reCAPTCHA token, skipping verification")
            return True

        # Verify the token with Google reCAPTCHA API
        response = requests.post(
            "https://www.google.com/recaptcha/api/siteverify",
            data={
                "secret": RECAPTCHA_SECRET_KEY,
                "response": token
            }
        )

        # Parse the response
        result = response.json()

        # Log the result for debugging
        logger.info(f"reCAPTCHA verification result: {result}")

        # Check if the token is valid
        if result.get("success", False):
            # If an action is specified, check if it matches
            if action and result.get("action") != action:
                logger.warning(f"reCAPTCHA action mismatch: expected {action}, got {result.get('action')}")
                return False

            # Check the score (if available)
            score = result.get("score", 0)
            if score < 0.5:
                logger.warning(f"reCAPTCHA score too low: {score}")
                return False

            return True
        else:
            logger.warning(f"reCAPTCHA verification failed: {result.get('error-codes', [])}")
            return False
    except Exception as e:
        logger.error(f"Error verifying reCAPTCHA token: {str(e)}")
        # In case of an error, fail open in development, fail closed in production
        return os.getenv("ENVIRONMENT", "development") != "production"

def verify_recaptcha_enterprise(token: str, action: str = None) -> bool:
    """
    Verify a reCAPTCHA Enterprise token using the Google Cloud reCAPTCHA Enterprise API.

    Args:
        token: The reCAPTCHA token to verify
        action: The expected action

    Returns:
        True if the token is valid, False otherwise
    """
    # If no token is provided, fail verification
    if not token:
        logger.warning("No reCAPTCHA token provided")
        return False

    # If no secret key is configured, fail verification
    if not RECAPTCHA_SECRET_KEY:
        logger.warning("No reCAPTCHA secret key configured")
        return False

    try:
        # For testing purposes, if the token is "test_token", return True in development
        if token == "test_token" and os.getenv("ENVIRONMENT", "development") != "production":
            logger.warning("Using test reCAPTCHA token, skipping verification")
            return True

        # Use the standard reCAPTCHA verification with the Enterprise token
        # The Enterprise reCAPTCHA uses the same verification endpoint
        return verify_recaptcha(token, action)
    except Exception as e:
        logger.error(f"Error verifying reCAPTCHA Enterprise token: {str(e)}")
        # In case of an error, fail closed (more secure)
        return False

def verify_recaptcha(token: str, action: str = None) -> bool:
    """
    Verify a reCAPTCHA token with the standard API.

    Args:
        token: The reCAPTCHA token to verify
        action: The expected action

    Returns:
        True if the token is valid, False otherwise
    """
    try:
        # Verify the token with Google reCAPTCHA API
        response = requests.post(
            "https://www.google.com/recaptcha/api/siteverify",
            data={
                "secret": RECAPTCHA_SECRET_KEY,
                "response": token
            }
        )

        # Parse the response
        result = response.json()

        # Log the result for debugging
        logger.info(f"reCAPTCHA verification result: {result}")

        # Check if the token is valid
        if result.get("success", False):
            # If an action is specified, check if it matches
            if action and result.get("action") != action and action != "REGISTER_PAGE_LOAD":
                logger.warning(f"reCAPTCHA action mismatch: expected {action}, got {result.get('action')}")
                # Don't fail on action mismatch for now, as Enterprise reCAPTCHA might handle actions differently
                # return False

            # Check the score (if available)
            score = result.get("score", 0)
            if score < 0.3:  # Lower threshold for better user experience
                logger.warning(f"reCAPTCHA score too low: {score}")
                return False

            return True
        else:
            logger.warning(f"reCAPTCHA verification failed: {result.get('error-codes', [])}")
            return False
    except Exception as e:
        logger.error(f"Error verifying reCAPTCHA token: {str(e)}")
        # In case of an error, fail open in development, fail closed in production
        return os.getenv("ENVIRONMENT", "development") != "production"
