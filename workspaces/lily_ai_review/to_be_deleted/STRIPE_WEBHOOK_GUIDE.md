# Stripe Webhook Testing Guide

This guide explains how to test Stripe webhooks using the Stripe CLI.

## Prerequisites

1. Install the Stripe CLI:
   - macOS: `brew install stripe/stripe-cli/stripe`
   - Windows: `scoop install stripe`
   - Linux: Follow the instructions at https://stripe.com/docs/stripe-cli#install

2. Log in to Stripe:
   ```bash
   stripe login
   ```

## Testing Webhooks

### Method 1: Using the Script

We've created a script to simplify webhook testing:

```bash
./stripe_webhook_test.sh
```

This script provides a menu to:
1. Start the webhook listener
2. Trigger various webhook events

### Method 2: Manual Commands

#### Step 1: Start the Webhook Listener

In one terminal window, run:

```bash
stripe listen --forward-to http://localhost:8004/billing/webhook
```

Keep this terminal window open. It will display a webhook signing secret that you can use in your application.

#### Step 2: Trigger Webhook Events

In another terminal window, trigger webhook events:

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

## Troubleshooting

### Webhook Not Received

If your application isn't receiving webhook events:

1. Check that your application is running on the correct port
2. Verify that the webhook endpoint is correctly implemented
3. Check your application logs for errors
4. Ensure the Stripe CLI is properly forwarding events

### Authentication Issues

If you're having trouble with authentication:

1. Run `stripe login` again to refresh your authentication
2. Check that your API keys are correctly set in your application

## Common Issues and Solutions

### Redirect After Payment

If users aren't being redirected after payment:

1. Ensure your success_url in the checkout session includes the session ID:
   ```python
   success_url=f"{base_url}/billing/success?session_id={{CHECKOUT_SESSION_ID}}"
   ```

2. Verify that your success page handler correctly processes the session ID

### Subscription Status Not Updated

If subscription status isn't updating:

1. Check that your webhook handler correctly processes the `checkout.session.completed` event
2. Verify that your database update logic is working correctly
3. Check for errors in your application logs

## Additional Resources

- [Stripe Webhooks Documentation](https://stripe.com/docs/webhooks)
- [Stripe CLI Documentation](https://stripe.com/docs/stripe-cli)
- [Stripe Checkout Documentation](https://stripe.com/docs/checkout)
