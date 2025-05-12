"""
Configuration management for the application.

This module provides a centralized way to access configuration values from
environment variables and other sources.
"""
import os
import logging
from typing import Dict
from enum import Enum
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Configure logging
logger = logging.getLogger(__name__)


class Environment(str, Enum):
    """Application environment."""
    DEVELOPMENT = "development"
    TESTING = "testing"
    PRODUCTION = "production"


class Config:
    """Base configuration class."""

    # Application settings
    APP_NAME: str = "Lily AI Research Pack Generator"
    APP_VERSION: str = "1.0.0"
    APP_DESCRIPTION: str = "AI-powered research paper generator"

    # Environment
    ENV: Environment = Environment(os.getenv("APP_ENV", "development").lower())
    DEBUG: bool = os.getenv("DEBUG", "false").lower() == "true"
    TESTING: bool = os.getenv("TESTING", "false").lower() == "true"

    # Paths
    BASE_DIR: str = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    STATIC_DIR: str = os.getenv("STATIC_DIR", os.path.join(BASE_DIR, "static"))
    TEMPLATES_DIR: str = os.getenv("TEMPLATES_DIR", os.path.join(BASE_DIR, "templates"))

    # Server
    HOST: str = os.getenv("HOST", "0.0.0.0")
    PORT: int = int(os.getenv("PORT", "8004"))

    # Base URL for the application
    # Always use researchassistant.uk as the base URL
    BASE_URL: str = os.getenv("BASE_URL", "https://researchassistant.uk")

    # Session
    SESSION_SECRET_KEY: str = os.getenv("SESSION_SECRET_KEY", "supersecretkey")
    SESSION_MAX_AGE: int = int(os.getenv("SESSION_MAX_AGE", str(3600 * 24 * 7)))  # 7 days
    SESSION_SAME_SITE: str = os.getenv("SESSION_SAME_SITE", "lax")
    SESSION_HTTPS_ONLY: bool = os.getenv("SESSION_HTTPS_ONLY", "false").lower() == "true"

    # Stripe
    STRIPE_API_KEY: str = os.getenv("STRIPE_API_KEY", "")
    STRIPE_SECRET_KEY: str = os.getenv("STRIPE_SECRET_KEY", "")
    STRIPE_PUBLISHABLE_KEY: str = os.getenv("STRIPE_PUBLISHABLE_KEY", "")
    STRIPE_WEBHOOK_SECRET: str = os.getenv("STRIPE_WEBHOOK_SECRET", "")

    # Stripe Products and Prices
    STRIPE_PREMIUM_PRODUCT_ID: str = os.getenv("STRIPE_PREMIUM_PRODUCT_ID", "")
    STRIPE_PREMIUM_PRICE_ID: str = os.getenv("STRIPE_PREMIUM_PRICE_ID", "")

    STRIPE_CREDITS_5_PRODUCT_ID: str = os.getenv("STRIPE_CREDITS_5_PRODUCT_ID", "")
    STRIPE_CREDITS_5_PRICE_ID: str = os.getenv("STRIPE_CREDITS_5_PRICE_ID", "")

    STRIPE_CREDITS_10_PRODUCT_ID: str = os.getenv("STRIPE_CREDITS_10_PRODUCT_ID", "")
    STRIPE_CREDITS_10_PRICE_ID: str = os.getenv("STRIPE_CREDITS_10_PRICE_ID", "")

    STRIPE_CREDITS_25_PRODUCT_ID: str = os.getenv("STRIPE_CREDITS_25_PRODUCT_ID", "")
    STRIPE_CREDITS_25_PRICE_ID: str = os.getenv("STRIPE_CREDITS_25_PRICE_ID", "")

    # Stripe Payment Links
    STRIPE_PAYMENT_LINK_PREMIUM: str = os.getenv("STRIPE_PAYMENT_LINK_PREMIUM", "")
    STRIPE_PAYMENT_LINK_CREDITS_5: str = os.getenv("STRIPE_PAYMENT_LINK_CREDITS_5", "")
    STRIPE_PAYMENT_LINK_CREDITS_10: str = os.getenv("STRIPE_PAYMENT_LINK_CREDITS_10", "")
    STRIPE_PAYMENT_LINK_CREDITS_25: str = os.getenv("STRIPE_PAYMENT_LINK_CREDITS_25", "")

    # Supabase
    SUPABASE_URL: str = os.getenv("SUPABASE_URL", "")
    SUPABASE_KEY: str = os.getenv("SUPABASE_KEY", "")

    # Development mode
    DEV_MODE: bool = os.getenv("PAPER_GEN_DEV_MODE", "false").lower() == "true"

    @classmethod
    def is_development(cls) -> bool:
        """Check if the application is running in development mode."""
        return cls.ENV == Environment.DEVELOPMENT or cls.DEV_MODE

    @classmethod
    def is_testing(cls) -> bool:
        """Check if the application is running in testing mode."""
        return cls.ENV == Environment.TESTING or cls.TESTING

    @classmethod
    def is_production(cls) -> bool:
        """Check if the application is running in production mode."""
        return cls.ENV == Environment.PRODUCTION and not cls.DEV_MODE and not cls.TESTING

    @classmethod
    def get_stripe_mode(cls) -> str:
        """Get the Stripe mode (test or live)."""
        if cls.STRIPE_API_KEY and "test" in cls.STRIPE_API_KEY.lower():
            return "test"
        return "live"

    @classmethod
    def is_stripe_test_mode(cls) -> bool:
        """Check if Stripe is in test mode."""
        return cls.get_stripe_mode() == "test"

    @classmethod
    def get_stripe_products(cls) -> Dict[str, str]:
        """Get Stripe product IDs."""
        return {
            "premium": cls.STRIPE_PREMIUM_PRODUCT_ID,
            "credits_5": cls.STRIPE_CREDITS_5_PRODUCT_ID,
            "credits_10": cls.STRIPE_CREDITS_10_PRODUCT_ID,
            "credits_25": cls.STRIPE_CREDITS_25_PRODUCT_ID
        }

    @classmethod
    def get_stripe_prices(cls) -> Dict[str, str]:
        """Get Stripe price IDs."""
        return {
            "premium": cls.STRIPE_PREMIUM_PRICE_ID,
            "credits_5": cls.STRIPE_CREDITS_5_PRICE_ID,
            "credits_10": cls.STRIPE_CREDITS_10_PRICE_ID,
            "credits_25": cls.STRIPE_CREDITS_25_PRICE_ID
        }

    @classmethod
    def get_stripe_payment_links(cls) -> Dict[str, str]:
        """Get Stripe payment links."""
        # Use hardcoded test links if in test mode and no links are configured
        if cls.is_stripe_test_mode():
            return {
                "premium": cls.STRIPE_PAYMENT_LINK_PREMIUM or "https://buy.stripe.com/test_4gwbLh9xB84G2icdQS",
                "credits_5": cls.STRIPE_PAYMENT_LINK_CREDITS_5 or "https://buy.stripe.com/test_4gweXt6lp70C1e85kq",
                "credits_10": cls.STRIPE_PAYMENT_LINK_CREDITS_10 or "https://buy.stripe.com/test_4gwaHd9xB2Km2ic28d",
                "credits_25": cls.STRIPE_PAYMENT_LINK_CREDITS_25 or "https://buy.stripe.com/test_bIY3eL39d0Ce0a4004"
            }

        # Use configured links for production
        return {
            "premium": cls.STRIPE_PAYMENT_LINK_PREMIUM,
            "credits_5": cls.STRIPE_PAYMENT_LINK_CREDITS_5,
            "credits_10": cls.STRIPE_PAYMENT_LINK_CREDITS_10,
            "credits_25": cls.STRIPE_PAYMENT_LINK_CREDITS_25
        }

    @classmethod
    def validate(cls) -> None:
        """Validate the configuration."""
        # Check required configuration values
        required_values = [
            ("SESSION_SECRET_KEY", cls.SESSION_SECRET_KEY),
            ("SUPABASE_URL", cls.SUPABASE_URL),
            ("SUPABASE_KEY", cls.SUPABASE_KEY),
        ]

        # In production, check for Stripe keys
        if cls.is_production():
            required_values.extend([
                ("STRIPE_API_KEY", cls.STRIPE_API_KEY),
                ("STRIPE_SECRET_KEY", cls.STRIPE_SECRET_KEY),
                ("STRIPE_PUBLISHABLE_KEY", cls.STRIPE_PUBLISHABLE_KEY),
                ("STRIPE_WEBHOOK_SECRET", cls.STRIPE_WEBHOOK_SECRET),
            ])

        # Log warnings for missing values
        for name, value in required_values:
            if not value:
                logger.warning(f"Missing required configuration value: {name}")


# Create a singleton instance
config = Config()

# Validate the configuration
config.validate()
