"""
reCAPTCHA utility for Lily AI.

This module provides reCAPTCHA verification functionality.
"""

import os
import logging
import requests
from typing import Dict, Any, Optional

# Set up logging
logger = logging.getLogger(__name__)

class RecaptchaVerifier:
    """reCAPTCHA verifier for Lily AI."""

    _instance = None

    def __new__(cls):
        """Create a new instance of the RecaptchaVerifier if one doesn't exist."""
        if cls._instance is None:
            cls._instance = super(RecaptchaVerifier, cls).__new__(cls)
            cls._instance._initialize()
        return cls._instance

    def _initialize(self):
        """Initialize the RecaptchaVerifier."""
        self.site_key = os.getenv("RECAPTCHA_SITE_KEY")
        self.secret_key = os.getenv("RECAPTCHA_SECRET_KEY")
        self.verify_url = "https://www.google.com/recaptcha/api/siteverify"

        logger.info(f"Initializing reCAPTCHA verifier with site_key: {self.site_key}")

        # Check if keys are placeholders or not set
        if not self.site_key or not self.secret_key or self.site_key == "your-recaptcha-site-key" or self.secret_key == "your-recaptcha-secret-key":
            logger.warning("reCAPTCHA keys are not set or are placeholders. Verification will be skipped.")
            self.site_key = None
            self.secret_key = None

    def verify(self, token: str, action: str, remote_ip: Optional[str] = None) -> Dict[str, Any]:
        """
        Verify a reCAPTCHA token.

        Args:
            token: The reCAPTCHA token from the client
            action: The expected action
            remote_ip: The remote IP address (optional)

        Returns:
            A dictionary containing the verification result
        """
        # If keys are not set or are placeholders, skip verification
        if not self.site_key or not self.secret_key or self.site_key == "your-recaptcha-site-key" or self.secret_key == "your-recaptcha-secret-key":
            logger.warning("reCAPTCHA verification skipped: keys not set or are placeholders")
            return {"success": True, "score": 1.0, "action": action}

        # For development environment with the specific test key, skip verification
        if self.site_key == "6LcgczQrAAAAAAvXas3rgYE7nit-OmSMZE0_Iv-a":
            logger.warning("reCAPTCHA verification skipped: using test key")
            return {"success": True, "score": 1.0, "action": action}

        # If token is not provided but we're requiring verification, fail
        if not token:
            logger.warning("reCAPTCHA verification failed: no token provided")
            return {"success": False, "error": "No token provided"}

        try:
            # Set up verification data
            data = {
                "secret": self.secret_key,
                "response": token
            }

            # Add remote IP if provided
            if remote_ip:
                data["remoteip"] = remote_ip

            # Send verification request
            response = requests.post(self.verify_url, data=data)
            result = response.json()

            # Log verification result
            logger.info(f"reCAPTCHA verification result: {result}")

            # Check if verification was successful
            if result.get("success"):
                # Check action
                if result.get("action") != action:
                    logger.warning(f"reCAPTCHA action mismatch: expected {action}, got {result.get('action')}")
                    result["warning"] = f"Action mismatch: expected {action}, got {result.get('action')}"

                # Check score
                score = result.get("score", 0)
                if score < 0.5:
                    logger.warning(f"reCAPTCHA score too low: {score}")
                    result["warning"] = f"Score too low: {score}"

            return result
        except Exception as e:
            logger.error(f"reCAPTCHA verification error: {str(e)}")
            return {"success": False, "error": str(e)}

    def get_site_key(self) -> str:
        """
        Get the reCAPTCHA site key.

        Returns:
            The reCAPTCHA site key
        """
        return self.site_key or ""

# Create a singleton instance
recaptcha_verifier = RecaptchaVerifier()

def get_recaptcha_verifier() -> RecaptchaVerifier:
    """
    Get the reCAPTCHA verifier singleton.

    Returns:
        The reCAPTCHA verifier
    """
    return recaptcha_verifier
