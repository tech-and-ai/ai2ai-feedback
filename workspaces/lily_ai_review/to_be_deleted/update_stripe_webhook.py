#!/usr/bin/env python
"""
Script to update Stripe webhook URL.

Usage:
    python update_stripe_webhook.py YOUR_STRIPE_API_KEY

Example:
    python update_stripe_webhook.py sk_test_123456789
"""
import sys
import stripe

# Check if API key is provided
if len(sys.argv) < 2:
    print("Usage: python update_stripe_webhook.py YOUR_STRIPE_API_KEY")
    exit(1)

# Get API key from command line
stripe_api_key = sys.argv[1]

# Configure Stripe with API key
stripe.api_key = stripe_api_key

# New webhook URL
new_webhook_url = "https://researchassistant.uk/billing/webhook"

def list_webhooks():
    """List all webhooks in the Stripe account."""
    try:
        webhooks = stripe.WebhookEndpoint.list()
        print("\nCurrent webhooks:")
        if not webhooks.data:
            print("No webhooks found")
        for webhook in webhooks.data:
            print(f"ID: {webhook.id}")
            print(f"URL: {webhook.url}")
            print(f"Status: {webhook.status}")
            print(f"Events: {', '.join(webhook.enabled_events)}")
            print("-" * 50)
        return webhooks.data
    except Exception as e:
        print(f"Error listing webhooks: {str(e)}")
        return []

def update_webhook(webhook_id, new_url):
    """Update an existing webhook URL."""
    try:
        webhook = stripe.WebhookEndpoint.modify(
            webhook_id,
            url=new_url
        )
        print(f"Successfully updated webhook {webhook_id} to URL: {new_url}")
        return webhook
    except Exception as e:
        print(f"Error updating webhook: {str(e)}")
        return None

def create_webhook(url):
    """Create a new webhook endpoint."""
    try:
        webhook = stripe.WebhookEndpoint.create(
            url=url,
            enabled_events=["*"],  # Subscribe to all events
            description="Lily AI Research Assistant webhook"
        )
        print(f"Successfully created new webhook with ID: {webhook.id}")
        print(f"Secret: {webhook.secret}")
        print("IMPORTANT: Update your STRIPE_WEBHOOK_SECRET in .env with this value!")
        return webhook
    except Exception as e:
        print(f"Error creating webhook: {str(e)}")
        return None

def main():
    """Main function to update or create webhook."""
    print("Stripe Webhook Updater")
    print("=" * 50)

    # List current webhooks
    webhooks = list_webhooks()

    # Check if there are any webhooks with the old URL
    old_webhook_url = "https://academicresearch.uk/api/membership/webhook"
    old_domain_webhooks = [w for w in webhooks if old_webhook_url == w.url]

    if old_domain_webhooks:
        print("\nFound webhooks with old domain:")
        for webhook in old_domain_webhooks:
            print(f"ID: {webhook.id}, URL: {webhook.url}")

        # Ask to update
        webhook_id = old_domain_webhooks[0].id
        print(f"\nUpdating webhook {webhook_id} to {new_webhook_url}")
        update_webhook(webhook_id, new_webhook_url)
    else:
        # Check if there's already a webhook with the new URL
        existing_webhooks = [w for w in webhooks if new_webhook_url == w.url]

        if existing_webhooks:
            print(f"\nWebhook with URL {new_webhook_url} already exists:")
            for webhook in existing_webhooks:
                print(f"ID: {webhook.id}, Status: {webhook.status}")
        else:
            # Create new webhook
            print(f"\nCreating new webhook with URL: {new_webhook_url}")
            create_webhook(new_webhook_url)

if __name__ == "__main__":
    main()
