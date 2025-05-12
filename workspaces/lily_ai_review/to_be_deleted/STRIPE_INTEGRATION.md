# Clean Stripe Integration for Lily AI

This document provides an overview of the clean, modular Stripe integration for Lily AI.

## Overview

The Stripe integration consists of several modular components:

1. **Stripe Service** (`app/services/billing/stripe_service_clean.py`): Handles all direct interactions with the Stripe API.
2. **Subscription Service** (`app/services/billing/subscription_service_clean.py`): Manages user subscriptions and handles Stripe webhook events.
3. **Billing Routes** (`routes/billing_clean.py`): Provides API endpoints for subscription management, checkout, and webhook handling.
4. **Main Application** (`app/main_clean.py`): Sets up the FastAPI application with the clean routes.
5. **Run Script** (`run_clean.py`): Starts the application with the clean implementation.

## Features

- **Clean, Modular Architecture**: Each component has a single responsibility and clear interfaces.
- **Comprehensive Error Handling**: All operations include proper error handling and logging.
- **Stripe Checkout Integration**: Uses Stripe Checkout for a seamless payment experience.
- **Webhook Handling**: Properly handles Stripe webhook events for subscription management.
- **Customer Portal**: Provides access to the Stripe Customer Portal for subscription management.

## Setup

### 1. Environment Variables

Ensure the following environment variables are set:

```
STRIPE_SECRET_KEY=sk_test_...
STRIPE_WEBHOOK_SECRET=whsec_...
STRIPE_PREMIUM_PRODUCT_ID=prod_SH8CIB1TV5s5my
STRIPE_PREMIUM_PRICE_ID=price_1RMZvsC1xrrQSUhiewLnwuxq
SESSION_SECRET_KEY=your_session_secret
```

### 2. Stripe Webhook Setup

1. Set up a webhook in the [Stripe Dashboard](https://dashboard.stripe.com/webhooks).
2. Configure it to send the following events:
   - `checkout.session.completed`
   - `customer.subscription.created`
   - `customer.subscription.updated`
   - `customer.subscription.deleted`
3. Set the webhook URL to `https://your-domain.com/billing/webhook`.
4. Copy the webhook signing secret to the `STRIPE_WEBHOOK_SECRET` environment variable.

### 3. Stripe Product and Price Setup

1. Ensure you have a product for the premium subscription in Stripe.
2. Set the product ID in the `STRIPE_PREMIUM_PRODUCT_ID` environment variable.
3. Set the price ID in the `STRIPE_PREMIUM_PRICE_ID` environment variable.

## Usage

### Starting the Application

To start the application with the clean implementation:

```bash
python run_clean.py
```

This will:
1. Terminate any existing processes on port 8004
2. Start the application using uvicorn on port 8004

### Subscription Flow

1. User visits `/billing/subscription` to view subscription options.
2. User clicks "Subscribe" button, which redirects to `/billing/checkout`.
3. The checkout route creates a Stripe Checkout session and redirects to it.
4. User completes payment on the Stripe Checkout page.
5. Stripe sends a `checkout.session.completed` webhook event.
6. The webhook handler updates the user's subscription in the database.
7. User is redirected to `/billing/success` and then to the dashboard.

### Managing Subscriptions

1. User visits `/billing/portal` to access the Stripe Customer Portal.
2. User can update payment methods, cancel subscription, etc.
3. Stripe sends webhook events for subscription changes.
4. The webhook handler updates the user's subscription in the database.

## Testing

### Local Webhook Testing

Use the Stripe CLI to test webhooks locally:

```bash
# Install Stripe CLI
# Then forward webhooks to your local server
stripe listen --forward-to http://localhost:8004/billing/webhook

# Trigger test events
stripe trigger checkout.session.completed
```

### Test Cards

Use Stripe's test cards for testing:

- **Success**: `4242 4242 4242 4242`
- **Requires Authentication**: `4000 0025 0000 3155`
- **Declined**: `4000 0000 0000 0002`

## Troubleshooting

### Webhook Issues

1. Check the webhook logs in the Stripe Dashboard.
2. Verify the webhook secret is correct.
3. Check the application logs for webhook processing errors.

### Subscription Issues

1. Check the user's subscription in the database.
2. Verify the Stripe customer and subscription IDs.
3. Check the Stripe Dashboard for subscription status.

## Migration from Legacy Code

To migrate from the legacy code to the clean implementation:

1. Update the imports in your existing code to use the clean services:
   ```python
   from app.services.billing.stripe_service_clean import StripeService
   from app.services.billing.subscription_service_clean import SubscriptionService
   ```

2. Update the routes in your FastAPI application:
   ```python
   from routes.billing_clean import router as billing_router
   ```

3. Start the application using the clean run script:
   ```bash
   python run_clean.py
   ```
