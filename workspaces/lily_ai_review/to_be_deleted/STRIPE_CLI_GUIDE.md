# Stripe CLI Guide for Lily AI

This guide explains how to use the Stripe CLI to test and debug Stripe integration in Lily AI.

## Installation

### macOS
```bash
brew install stripe/stripe-cli/stripe
```

### Windows
```bash
scoop install stripe
```

### Linux
Follow the instructions at https://stripe.com/docs/stripe-cli#install

## Setup

1. Log in to Stripe CLI:
```bash
stripe login
```

2. Verify login:
```bash
stripe whoami
```

## Testing Webhooks

### Start Webhook Forwarding

Run the included script to start forwarding webhooks to your local server:
```bash
chmod +x stripe_cli_setup.sh
./stripe_cli_setup.sh
```

Or run the command directly:
```bash
stripe listen --forward-to http://localhost:8004/billing/webhook
```

Keep this terminal window open while testing.

### Trigger Test Events

In a new terminal window, you can trigger test events:

```bash
# Simulate a completed checkout session
stripe trigger checkout.session.completed

# Simulate a subscription creation
stripe trigger customer.subscription.created

# Simulate a subscription update
stripe trigger customer.subscription.updated

# Simulate a subscription cancellation
stripe trigger customer.subscription.deleted
```

## Testing Checkout

You can test the checkout flow using Stripe's test cards:

- **Success**: `4242 4242 4242 4242`
- **Requires Authentication**: `4000 0025 0000 3155`
- **Declined**: `4000 0000 0000 0002`

## Debugging Tips

### View Webhook Events

You can view recent webhook events in the Stripe Dashboard:
https://dashboard.stripe.com/test/webhooks

### Check Logs

Check the application logs for webhook processing:
```bash
tail -f logs/app.log
```

### Verify Webhook Signatures

The application will verify webhook signatures in production mode. In development mode, it will bypass signature verification for easier testing.

## Environment Variables

Make sure these environment variables are set in your `.env` file:

```
STRIPE_API_KEY=sk_test_...
STRIPE_WEBHOOK_SECRET=whsec_...
STRIPE_PUBLISHABLE_KEY=pk_test_...
ENVIRONMENT=development
```

## Common Issues

### Webhook Signature Verification Failed

If you see "Webhook signature verification failed" in the logs, check:
1. The webhook secret in your `.env` file
2. That you're using the correct webhook endpoint URL
3. That the webhook is being forwarded correctly by the Stripe CLI

### Subscription Not Updated

If a user's subscription isn't updated after checkout:
1. Check that the webhook event was received
2. Verify that the user ID was correctly extracted from the event
3. Check for errors in the subscription service

## Additional Resources

- [Stripe CLI Documentation](https://stripe.com/docs/stripe-cli)
- [Stripe Webhook Documentation](https://stripe.com/docs/webhooks)
- [Stripe Testing Documentation](https://stripe.com/docs/testing)
