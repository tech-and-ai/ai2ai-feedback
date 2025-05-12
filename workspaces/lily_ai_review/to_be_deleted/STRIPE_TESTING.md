# Stripe Integration Testing

This document provides instructions for testing and troubleshooting the Stripe integration.

## Prerequisites

Before running the tests, make sure you have the following:

1. Python 3.7+ installed
2. Required Python packages:
   ```
   pip install stripe requests python-dotenv supabase
   ```
3. Environment variables set in `.env` file:
   ```
   STRIPE_SECRET_KEY=sk_test_...
   STRIPE_WEBHOOK_SECRET=whsec_...
   SUPABASE_URL=https://your-project-id.supabase.co
   SUPABASE_KEY=your-supabase-key
   APP_URL=http://localhost:8004
   ADMIN_TOKEN=admin-token
   ```

## Testing Scripts

### 1. Complete Integration Test

The `test_stripe_integration_flow.py` script tests the complete Stripe subscription flow:

1. Creates a test customer in Stripe
2. Creates a test subscription
3. Verifies webhook processing
4. Checks database updates

```bash
python test_stripe_integration_flow.py
```

### 2. Webhook Processing Test

The `test_webhook_processing.py` script tests the webhook processing functionality:

```bash
python test_webhook_processing.py
```

If the API endpoint for processing webhooks is not working, you can use the `--manual` flag to manually mark events as processed:

```bash
python test_webhook_processing.py --manual
```

### 3. Manual Event Processing

The `mark_events_processed.py` script manually marks unprocessed Stripe webhook events as processed in the database:

```bash
# List all unprocessed events
python mark_events_processed.py --list-only

# Mark all unprocessed events as processed
python mark_events_processed.py

# Mark specific event types as processed
python mark_events_processed.py --event-types customer.subscription.created,customer.subscription.updated
```

## Troubleshooting

### Common Issues

1. **Webhook Events Not Being Processed**

   If webhook events are being received but not processed, check:
   
   - The webhook endpoint is correctly configured in Stripe
   - The webhook secret is correctly set in the environment variables
   - The webhook endpoint is returning a 200 OK response
   - The event processing logic in `handle_subscription_created` and `handle_subscription_updated` is working correctly

   You can manually process events using:
   
   ```bash
   python mark_events_processed.py
   ```

2. **Subscription Not Being Updated**

   If the subscription is not being updated in the database, check:
   
   - The webhook events are being received and processed
   - The `handle_subscription_updated` function is correctly updating all fields
   - The user ID in the webhook event matches a user in the database

3. **Authentication Issues with Process-Pending-Webhooks Endpoint**

   If you're having trouble accessing the `/billing/process-pending-webhooks` endpoint, check:
   
   - The endpoint is correctly registered in the router
   - The authentication logic is working correctly
   - You're using the correct admin token

## Manual Testing

You can also test the Stripe integration manually:

1. Create a test customer in the Stripe Dashboard
2. Create a test subscription for the customer
3. Check the webhook events in the Stripe Dashboard
4. Verify that the subscription is updated in the database

## Verifying Webhook Events

To verify that webhook events are being received and processed:

1. Check the Stripe Dashboard for webhook events
2. Check the `stripe_events` table in the database
3. Check the application logs for webhook processing messages

## Checking Subscription Status

To check the subscription status in the database:

```bash
python -c "
import os
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()
supabase = create_client(os.getenv('SUPABASE_URL'), os.getenv('SUPABASE_KEY'))
response = supabase.table('saas_user_subscriptions').select('*').order('created_at', desc=True).limit(5).execute()
for sub in response.data:
    print(f\"User: {sub['user_id']}, Tier: {sub['subscription_tier']}, Status: {sub['status']}\")
"
```

## Conclusion

By using these testing scripts and troubleshooting steps, you can ensure that the Stripe integration is working correctly and fix any issues that arise.
