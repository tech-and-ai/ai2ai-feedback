# Manual Test Plan for Lily AI Fixes

This document outlines the steps to manually test the fixes we've made to the Lily AI application.

## Prerequisites

1. Restart the application by:
   - Killing any existing processes on port 8004:
     ```bash
     sudo lsof -i :8004 | grep LISTEN | awk '{print $2}' | xargs kill -9
     ```
   - Starting the application:
     ```bash
     cd /home/admin/projects/lily_ai && source venv/bin/activate && python run.py
     ```

## Test 1: Subscription Button Redirection

### Objective
Verify that clicking the "Upgrade Now" button on the subscription page redirects to Stripe.

### Steps
1. Login as a free user
2. Navigate to `/subscription`
3. Click the "Upgrade Now" button
4. Observe where you are redirected

### Expected Result
You should be redirected to a Stripe checkout page.

### Technical Details
- The JavaScript in `templates/subscription.html` now uses `window.location.href` for navigation
- The route in `routes/billing_simple.py` has been updated to `/checkout/premium` to match the prefix in main.py

## Test 2: "My Papers" Access Control

### Objective
Verify that free users are redirected from the "My Papers" page to the subscription page.

### Steps
1. Login as a free user
2. Try to navigate to `/my-papers`
3. Observe where you are redirected

### Expected Result
You should be redirected to the subscription page.

### Technical Details
- The `/my-papers` route in `main.py` now checks the user's subscription tier
- Free/sample tier users are redirected to the subscription page

## Test 3: Individual Paper View Access Control

### Objective
Verify that free users are redirected from individual paper view pages to the subscription page.

### Steps
1. Login as a free user
2. Try to navigate to `/my-papers/1` (or any paper ID)
3. Observe where you are redirected

### Expected Result
You should be redirected to the subscription page.

### Technical Details
- The `/my-papers/{paper_id}` route in `main.py` now checks the user's subscription tier
- Free/sample tier users are redirected to the subscription page

## Test 4: Welcome Email for Google Sign-ups

### Objective
Verify that welcome emails are sent when users sign up with Google.

### Steps
1. Sign up with a new Google account
2. Check the email inbox for the welcome email

### Expected Result
You should receive a welcome email from "Lily AI <noreply@lilyai.uk>".

### Technical Details
- The email configuration in `.env` has been updated:
  - `FROM_EMAIL=noreply@lilyai.uk`
  - `FROM_NAME=Lily AI`
  - `SMTP_USER=noreply@lilyai.uk`
- Detailed logging has been added to help diagnose any issues

## Troubleshooting

### Subscription Button Not Redirecting
- Check the browser console for any JavaScript errors
- Verify that the route in `routes/billing_simple.py` is correctly defined as `/checkout/premium`
- Check the application logs for any errors related to the checkout process

### "My Papers" Access Control Not Working
- Check if the user's subscription tier is correctly set in the session
- Verify that the context in `main.py` includes the subscription tier
- Check the application logs for any errors related to the access control

### Welcome Email Not Sent
- Check the application logs for any errors related to the email service
- Verify that the SMTP configuration in `.env` is correct
- Check if the email service is properly initialized in the auth service

## Additional Notes

- The application needs to be restarted for these changes to take effect
- The port 8004 needs to be available for the application to start properly
- If you encounter any issues, check the application logs for more information
