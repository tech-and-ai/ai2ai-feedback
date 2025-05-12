# Stripe Integration Testing Guide

This guide provides comprehensive instructions for testing the Stripe integration in the Research Assistant application.

## Prerequisites

1. Make sure your application is running:
   ```bash
   python run.py
   ```

2. Make sure you have the Stripe CLI installed:
   ```bash
   # Check if installed
   stripe --version
   
   # Install if needed (macOS)
   brew install stripe/stripe-cli/stripe
   ```

3. Log in to Stripe CLI:
   ```bash
   stripe login
   ```

## Testing Methods

### Method 1: Using the Test Scripts

We've created several scripts to simplify testing:

#### 1. Test the Stripe API

```bash
python test_stripe_api.py
```

This script:
- Verifies your Stripe API keys are working
- Lists customers, products, and prices
- Creates a test checkout session
- Provides a URL for testing the payment flow

#### 2. Test Webhooks

```bash
./stripe_webhook_test.sh
```

This script provides a menu to:
1. Start the webhook listener
2. Trigger various webhook events
3. Test specific scenarios like Premium Membership checkout

### Method 2: Manual Testing

#### 1. Start the Webhook Listener

In one terminal window, run:

```bash
stripe listen --forward-to http://localhost:8004/billing/webhook
```

Keep this terminal window open. It will display a webhook signing secret.

#### 2. Trigger Webhook Events

In another terminal window, trigger webhook events:

```bash
# Simulate a completed checkout session
stripe trigger checkout.session.completed

# With specific metadata for Premium Membership
stripe trigger checkout.session.completed --metadata user_id=test_user_123 --metadata product_id=prod_SH8CIB1TV5s5my --metadata price_id=price_1RMZvsC1xrrQSUhiewLnwuxq
```

#### 3. Create a Real Checkout Session

```bash
python -c "
import stripe, os
from dotenv import load_dotenv
load_dotenv()
stripe.api_key = os.getenv('STRIPE_SECRET_KEY')
session = stripe.checkout.Session.create(
    payment_method_types=['card'],
    line_items=[{'price': 'price_1RMZvsC1xrrQSUhiewLnwuxq', 'quantity': 1}],
    mode='subscription',
    success_url='http://localhost:8004/billing/success?session_id={CHECKOUT_SESSION_ID}',
    cancel_url='http://localhost:8004/billing/cancel',
    metadata={'user_id': 'test_user_123'}
)
print(f'Checkout URL: {session.url}')
"
```

## Test Scenarios

### 1. Premium Membership Subscription

**Test Steps:**
1. Create a checkout session for the Premium Membership
2. Complete the payment using test card 4242 4242 4242 4242
3. Verify you're redirected to the success page
4. Check that the subscription is created in the database
5. Verify the user's session is updated with the new subscription tier

**Expected Results:**
- User is redirected to success page
- Subscription is created in the database
- User session shows Premium tier
- Dashboard displays Premium features

### 2. Additional Paper Credits Purchase

**Test Steps:**
1. Create a checkout session for Additional Paper Credits
2. Complete the payment using test card 4242 4242 4242 4242
3. Verify you're redirected to the success page
4. Check that the credits are added to the user's account

**Expected Results:**
- User is redirected to success page
- Paper credits are added to the user's account
- Dashboard displays updated paper credit count

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
2. Check that your API keys are correctly set in your .env file
3. Make sure you're using test keys for testing

### Redirect After Payment Not Working

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

## Test Cards

| Card Number | Description |
|-------------|-------------|
| 4242 4242 4242 4242 | Succeeds and immediately processes the payment |
| 4000 0025 0000 3155 | Requires authentication (3D Secure) |
| 4000 0000 0000 9995 | Declined (insufficient funds) |

## Additional Resources

- [Stripe Testing Documentation](https://stripe.com/docs/testing)
- [Stripe CLI Documentation](https://stripe.com/docs/stripe-cli)
- [Stripe Webhook Documentation](https://stripe.com/docs/webhooks)
- [Stripe Checkout Documentation](https://stripe.com/docs/checkout)
