#!/bin/bash

# Stripe Webhook Testing Script
# This script helps set up and test Stripe webhooks using the Stripe CLI

# Load environment variables from .env file if it exists
if [ -f .env ]; then
    echo "Loading environment variables from .env file..."
    export $(grep -v '^#' .env | xargs)
fi

# Default values if not set in environment
WEBHOOK_PORT=${WEBHOOK_PORT:-8004}
WEBHOOK_PATH=${WEBHOOK_PATH:-"/billing/webhook"}
WEBHOOK_URL="http://localhost:${WEBHOOK_PORT}${WEBHOOK_PATH}"

# Product and price IDs from environment
PREMIUM_PRODUCT_ID=${STRIPE_PREMIUM_PRODUCT_ID:-"prod_SH8CIB1TV5s5my"}
PREMIUM_PRICE_ID=${STRIPE_PREMIUM_PRICE_ID:-"price_1RMZvsC1xrrQSUhiewLnwuxq"}

# Check if Stripe CLI is installed
if ! command -v stripe &> /dev/null; then
    echo "Stripe CLI is not installed. Please install it first:"
    echo "For macOS: brew install stripe/stripe-cli/stripe"
    echo "For Windows: scoop install stripe"
    echo "For Linux: https://stripe.com/docs/stripe-cli#install"
    exit 1
fi

# Check if we're logged in to Stripe
echo "Checking Stripe CLI login status..."
if ! stripe whoami &> /dev/null; then
    echo "You need to log in to Stripe CLI first:"
    echo "Run: stripe login"
    exit 1
fi

# Function to start the webhook listener
start_listener() {
    echo "Starting webhook listener..."
    echo "This will forward Stripe webhook events to your local server at ${WEBHOOK_URL}"
    echo "Keep this terminal window open while testing."
    echo ""

    # Start the webhook listener
    stripe listen --forward-to "${WEBHOOK_URL}"
}

# Function to trigger a test event
trigger_event() {
    local event_type=$1
    local additional_args=$2

    echo "Triggering test event: $event_type"
    if [ -z "$additional_args" ]; then
        stripe trigger $event_type
    else
        stripe trigger $event_type $additional_args
    fi

    echo "Event triggered. Check your application logs for the webhook response."
}

# Main menu
show_menu() {
    echo "=== Stripe Webhook Testing ==="
    echo "Current configuration:"
    echo "- Webhook URL: ${WEBHOOK_URL}"
    echo "- Premium Product ID: ${PREMIUM_PRODUCT_ID}"
    echo "- Premium Price ID: ${PREMIUM_PRICE_ID}"
    echo ""
    echo "1. Start webhook listener"
    echo "2. Trigger checkout.session.completed event"
    echo "3. Trigger customer.subscription.created event"
    echo "4. Trigger customer.subscription.updated event"
    echo "5. Trigger customer.subscription.deleted event"
    echo "6. Trigger checkout.session.completed with Premium Membership"
    echo "7. Exit"
    echo "Enter your choice: "
    read choice

    case $choice in
        1) start_listener ;;
        2) trigger_event "checkout.session.completed" ;;
        3) trigger_event "customer.subscription.created" ;;
        4) trigger_event "customer.subscription.updated" ;;
        5) trigger_event "customer.subscription.deleted" ;;
        6)
            # Premium membership checkout with metadata
            trigger_event "checkout.session.completed" "--metadata user_id=test_user_123 --metadata product_id=${PREMIUM_PRODUCT_ID} --metadata price_id=${PREMIUM_PRICE_ID}"
            ;;
        7) exit 0 ;;
        *) echo "Invalid choice. Please try again." ;;
    esac
}

# Show the menu
show_menu
