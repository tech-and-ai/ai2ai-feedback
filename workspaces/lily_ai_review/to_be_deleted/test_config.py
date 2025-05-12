#!/usr/bin/env python3
"""
Configuration module for Stripe testing.

This module loads environment variables and provides configuration for Stripe tests.
"""

import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class StripeConfig:
    """Configuration for Stripe tests."""
    
    def __init__(self):
        """Initialize the configuration."""
        # API keys
        self.api_key = os.getenv("STRIPE_SECRET_KEY") or os.getenv("STRIPE_API_KEY")
        self.publishable_key = os.getenv("STRIPE_PUBLISHABLE_KEY")
        self.webhook_secret = os.getenv("STRIPE_WEBHOOK_SECRET")
        
        # Product and price IDs
        self.premium_product_id = os.getenv("STRIPE_PREMIUM_PRODUCT_ID")
        self.premium_price_id = os.getenv("STRIPE_PREMIUM_PRICE_ID")
        
        # Paper credits price IDs
        self.credits_5_price_id = os.getenv("STRIPE_PRICE_ID_CREDITS_5")
        self.credits_10_price_id = os.getenv("STRIPE_PRICE_ID_CREDITS_10")
        self.credits_25_price_id = os.getenv("STRIPE_PRICE_ID_CREDITS_25")
        
        # Payment links
        self.premium_payment_link = os.getenv("STRIPE_PAYMENT_LINK_PREMIUM")
        self.credits_5_payment_link = os.getenv("STRIPE_PAYMENT_LINK_CREDITS_5")
        self.credits_10_payment_link = os.getenv("STRIPE_PAYMENT_LINK_CREDITS_10")
        self.credits_25_payment_link = os.getenv("STRIPE_PAYMENT_LINK_CREDITS_25")
        
        # Application URLs
        self.base_url = os.getenv("BASE_URL", "http://localhost:8004")
        self.success_url = f"{self.base_url}/billing/success?session_id={{CHECKOUT_SESSION_ID}}"
        self.cancel_url = f"{self.base_url}/billing/cancel"
        self.webhook_url = f"{self.base_url}/billing/webhook"
        
    def validate(self):
        """Validate the configuration."""
        errors = []
        
        # Check API keys
        if not self.api_key:
            errors.append("STRIPE_SECRET_KEY or STRIPE_API_KEY not set")
        elif not self.api_key.startswith("sk_test_"):
            errors.append("Not using a test API key. Please check your .env file.")
            
        # Check product and price IDs
        if not self.premium_product_id:
            errors.append("STRIPE_PREMIUM_PRODUCT_ID not set")
        if not self.premium_price_id:
            errors.append("STRIPE_PREMIUM_PRICE_ID not set")
            
        return errors
    
    def is_valid(self):
        """Check if the configuration is valid."""
        return len(self.validate()) == 0
    
    def __str__(self):
        """Return a string representation of the configuration."""
        return f"""Stripe Configuration:
- API Key: {self.api_key[:4]}...{self.api_key[-4:] if self.api_key else 'None'}
- Premium Product ID: {self.premium_product_id}
- Premium Price ID: {self.premium_price_id}
- Base URL: {self.base_url}
- Webhook URL: {self.webhook_url}
"""

# Create a global instance
config = StripeConfig()

if __name__ == "__main__":
    # Print the configuration if run directly
    print(config)
    
    # Validate the configuration
    errors = config.validate()
    if errors:
        print("\nConfiguration errors:")
        for error in errors:
            print(f"- {error}")
    else:
        print("\nConfiguration is valid.")
