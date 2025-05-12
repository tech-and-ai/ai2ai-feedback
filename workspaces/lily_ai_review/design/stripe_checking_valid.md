# Stripe Subscription Verification Design

## Overview

This document outlines the implementation of a hybrid approach for verifying subscription status with Stripe in the Lily AI application. The goal is to ensure that users only have access to premium features when they have a valid subscription, while balancing performance and security.

## Current Issues

1. **Reliance on Database Status**: The application currently relies solely on the local database for subscription status, without verifying with Stripe.
2. **End Date Not Utilized**: The `end_date` field is set but not used to check if subscriptions have expired.
3. **Multiple Active Subscriptions**: Users can have multiple active subscriptions, which shouldn't happen.
4. **Webhook Dependency**: The system heavily depends on webhooks working correctly to maintain subscription status.

## Implementation Strategy

We'll implement a hybrid approach that balances performance and security:

### 1. Session-Based Verification

- Verify subscription status with Stripe when the user logs in
- Store the verification result in the user's session
- Use this cached result for most feature access checks

### 2. Periodic Re-verification

- Re-verify with Stripe if the last verification was more than 24 hours ago
- This catches any missed webhook events
- Update the database status if it differs from Stripe

### 3. Feature-Specific Checks

- For high-value features (like generating a new research paper), verify with Stripe if the last verification was more than 1 hour ago
- This ensures that users can't access premium features after cancellation

### 4. End Date Utilization

- Use the `end_date` field to check if subscriptions have expired
- Update the subscription status to "expired" if the end date has passed
- Sync the end date with Stripe's subscription period end

### 5. Prevent Multiple Active Subscriptions

- Implement application logic to ensure a user can only have one active subscription
- When creating a new subscription, cancel any existing active subscriptions

## Code Changes

The following files will be modified:

1. `app/services/billing/subscription_service.py`:
   - Add `verify_subscription_with_stripe` method
   - Update `can_create_paper` method to use verification
   - Add logic to check end date
   - Add logic to prevent multiple active subscriptions

2. `auth/dependencies.py`:
   - Update to verify subscription status on login
   - Store verification timestamp in session

3. `routes/research_paper.py`:
   - Add verification check before allowing paper creation

## Future Considerations

### Review Papers Feature

When the Review Papers feature is implemented, the same verification approach should be applied:

1. Verify subscription status before allowing access to review paper creation
2. Use the same hybrid approach (session-based with periodic verification)
3. Implement specific limits for review papers based on subscription tier
4. Track review paper usage separately from research papers

### Subscription Synchronization Job

Consider implementing a background job to periodically sync all subscription statuses with Stripe:

1. Run daily to catch any missed webhook events
2. Update subscription status, end date, and other relevant fields
3. Log discrepancies for manual review

## Implementation Timeline

1. Implement subscription verification methods in `subscription_service.py`
2. Update login flow to verify subscription status
3. Update research paper creation to verify subscription status
4. Test with various subscription scenarios (active, canceled, expired)
5. Monitor for any issues after deployment

## Conclusion

This hybrid approach provides a good balance between performance and security, and is in line with industry standards for SaaS applications. It ensures that users only have access to premium features when they have a valid subscription, while minimizing the performance impact of frequent Stripe API calls.
