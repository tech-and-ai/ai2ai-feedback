#!/bin/bash
# Script to test Stripe webhook by triggering events

# Check if API key is provided
if [ $# -lt 1 ]; then
    echo "Usage: $0 YOUR_STRIPE_API_KEY [EVENT_TYPE]"
    echo "Example: $0 sk_test_123456 payment_intent.succeeded"
    exit 1
fi

API_KEY="$1"
EVENT_TYPE=${2:-payment_intent.succeeded}  # Default to payment_intent.succeeded if not provided

echo "Starting webhook listener..."
echo "In a new terminal, run: stripe listen --forward-to https://researchassistant.uk/billing/webhook --api-key \"$API_KEY\""
echo ""
echo "Triggering $EVENT_TYPE event..."

# Trigger the event
stripe trigger "$EVENT_TYPE" --api-key "$API_KEY"

# Check if the command was successful
if [ $? -eq 0 ]; then
    echo "Successfully triggered $EVENT_TYPE event!"
    echo "Check your application logs to see if the webhook was received and processed correctly."
else
    echo "Error triggering $EVENT_TYPE event. Make sure your API key is correct."
fi
