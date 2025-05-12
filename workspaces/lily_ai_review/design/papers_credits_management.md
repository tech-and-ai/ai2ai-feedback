# Papers and Credits Management System

## Overview

This document outlines the credit management system for Lily AI, detailing how monthly subscription papers and add-on credits are tracked, displayed, and used within the application.

## Credit Types

### Monthly Subscription Papers

- **Quantity**: 10 papers per month with Premium subscription (£20/month)
- **Expiration**: Reset at the end of each billing cycle
- **Usage Priority**: Used first before any add-on credits
- **Purpose**: Core offering of the Premium subscription

### Add-on Credits

- **Quantity**: Varies based on purchase (5, 10, or 25 credits)
- **Expiration**: Never expire
- **Usage Priority**: Used only after monthly papers are depleted
- **Purpose**: Supplement for users who need more than 10 papers per month

## User Interface Implementation

### Dashboard Display

- **Monthly Papers Counter**: "Monthly Papers: 7/10 remaining (reset on [date])"
- **Add-on Credits Counter**: "Add-on Credits: 40 available"
- **Visual Distinction**:
  - Different colors for each type (e.g., blue for monthly, purple for add-on)
  - Simple icons to distinguish types (calendar for monthly, plus/star for add-on)

### My Papers Screen

- **Credit Summary**: Displayed prominently at the top of the page
  - "7 monthly papers remaining this month + 40 additional credits"
- **Buy More Credits Button**: For premium and pro users
- **Upgrade to Premium Button**: For free and basic users

### Research Generator Screen

- **Credit Usage Indicator**: "This will use 1 paper/credit"
- **Credit Source Information**: "We'll automatically use your monthly papers first, then your add-on credits"
- **Current Balance Display**: Show current credit balances before submission

## Technical Implementation

### Database Structure

```sql
-- Users table (existing)
-- Contains user_id, subscription status, etc.

-- Monthly papers tracking (integrated into saas_user_subscriptions)
-- The saas_user_subscriptions table includes:
--   user_id UUID REFERENCES auth.users(id)
--   subscription_tier VARCHAR(20) NOT NULL
--   papers_limit INTEGER NOT NULL
--   papers_used INTEGER NOT NULL DEFAULT 0
--   current_period_end TIMESTAMP WITH TIME ZONE
--   status VARCHAR(20) NOT NULL
--   stripe_subscription_id VARCHAR(100)
--   stripe_customer_id VARCHAR(100)

-- Add-on credits tracking
CREATE TABLE saas_paper_credits (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES auth.users(id),
    credits_remaining INTEGER NOT NULL DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Paper credit usage tracking
CREATE TABLE saas_paper_credit_usage (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    paper_id UUID,
    user_id UUID NOT NULL REFERENCES auth.users(id),
    credit_type VARCHAR(20) NOT NULL, -- 'monthly' or 'addon'
    used_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

### Credit Management Logic

1. **Subscription Activation**:
   - When user subscribes to Premium, update entry in `saas_user_subscriptions`
   - Set `papers_limit = 10` and `papers_used = 0`
   - Set `current_period_end` to one month from subscription date

2. **Monthly Reset Process**:
   - Stripe webhook handles subscription renewal events
   - Reset `papers_used = 0` when subscription renews
   - Update `current_period_end` to next billing date

3. **Add-on Credit Purchase**:
   - When user purchases add-on credits, update `saas_paper_credits`
   - Increment `credits_remaining` by purchased amount

4. **Paper Creation Logic**:
   ```python
   def increment_papers_used(user_id):
       # Get subscription and additional credits
       subscription = get_user_subscription(user_id)

       # Check if user has monthly papers remaining
       if subscription.get("papers_remaining", 0) > 0:
           # Use a monthly paper
           new_count = subscription.get("papers_used", 0) + 1

           # Update subscription
           update_subscription_papers_used(user_id, new_count)

           # Record usage
           record_paper_credit_usage(user_id, "monthly")

           return True

       # Check if user has additional credits
       if subscription.get("additional_credits", 0) > 0:
           # Use an additional credit
           new_credits = subscription.get("additional_credits", 0) - 1

           # Update credits
           update_paper_credits(user_id, new_credits)

           # Record usage
           record_paper_credit_usage(user_id, "addon")

           return True

       # No credits available
       return False
   ```

5. **Credit Usage Tracking**:
   - When a paper is created, record in `saas_paper_credit_usage` which type was used
   - This enables reporting and filtering by credit type

## User Notifications

1. **Low Monthly Papers**:
   - Notify when user has 2 or fewer monthly papers remaining
   - Include reset date information

2. **Monthly Papers Reset**:
   - Notify when monthly papers have been reset
   - "Your 10 monthly papers are now available"

3. **Add-on Credits Purchase**:
   - Confirm successful purchase
   - Show updated total add-on credits

## Reporting and Analytics

Track the following metrics:

1. **Usage Patterns**:
   - Ratio of monthly papers to add-on credits used
   - Average papers used per user per month
   - Percentage of users who exhaust monthly papers

2. **Purchase Behavior**:
   - Frequency of add-on credit purchases
   - Average add-on credit purchase size
   - Correlation between usage and purchases

3. **Retention Impact**:
   - How credit usage correlates with subscription retention
   - Whether add-on credit purchases predict longer retention

## Implementation Status

1. ✅ **Core Credit Tracking** - Implemented accurate tracking of both credit types
2. ✅ **Automatic Usage Logic** - Implemented the priority system (monthly first, then add-on)
3. ✅ **Clear UI Indicators** - Added clear credit balances and usage indicators
4. ✅ **Purchase Flow** - Implemented streamlined process for buying add-on credits
5. ⏳ **Reporting** - Analytics tracking to be implemented in future updates

## Future Enhancements

1. **Enhanced Notifications** - Add more proactive notifications for low credits
2. **Usage Analytics** - Implement detailed analytics dashboard for credit usage
3. **Filtering Options** - Add ability to filter papers by credit type used