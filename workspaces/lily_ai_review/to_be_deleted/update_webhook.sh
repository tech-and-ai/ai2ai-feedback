#!/bin/bash
# Script to update Stripe webhook URL

# Check if API key is provided
if [ $# -lt 1 ]; then
    echo "Usage: $0 YOUR_STRIPE_API_KEY"
    exit 1
fi

API_KEY=$1
OLD_URL="https://academicresearch.uk/api/membership/webhook"
NEW_URL="https://researchassistant.uk/billing/webhook"

echo "Listing current webhooks..."
WEBHOOKS=$(stripe webhook list --api-key $API_KEY --format json)

# Check if the command was successful
if [ $? -ne 0 ]; then
    echo "Error listing webhooks. Make sure your API key is correct."
    exit 1
fi

echo "Current webhooks:"
echo "$WEBHOOKS" | jq -r '.data[] | "ID: \(.id), URL: \(.url), Status: \(.status)"'

# Find webhook with old URL
WEBHOOK_ID=$(echo "$WEBHOOKS" | jq -r ".data[] | select(.url == \"$OLD_URL\") | .id")

if [ -n "$WEBHOOK_ID" ]; then
    echo "Found webhook with old URL: $WEBHOOK_ID"
    echo "Updating webhook to new URL: $NEW_URL"
    
    # Update the webhook
    stripe webhook update $WEBHOOK_ID --url $NEW_URL --api-key $API_KEY
    
    if [ $? -eq 0 ]; then
        echo "Successfully updated webhook!"
    else
        echo "Error updating webhook."
    fi
else
    echo "No webhook found with URL: $OLD_URL"
    
    # Check if webhook with new URL already exists
    NEW_WEBHOOK_ID=$(echo "$WEBHOOKS" | jq -r ".data[] | select(.url == \"$NEW_URL\") | .id")
    
    if [ -n "$NEW_WEBHOOK_ID" ]; then
        echo "Webhook with new URL already exists: $NEW_WEBHOOK_ID"
    else
        echo "Creating new webhook with URL: $NEW_URL"
        
        # Create new webhook
        RESULT=$(stripe webhook create --url $NEW_URL --events "*" --api-key $API_KEY)
        
        if [ $? -eq 0 ]; then
            echo "Successfully created new webhook!"
            echo "Webhook secret: $(echo "$RESULT" | grep -o 'whsec_[a-zA-Z0-9]*')"
            echo "IMPORTANT: Update your STRIPE_WEBHOOK_SECRET in .env with this value!"
        else
            echo "Error creating webhook."
        fi
    fi
fi
