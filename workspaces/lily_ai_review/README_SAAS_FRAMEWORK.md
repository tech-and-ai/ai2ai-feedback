# SaaS Framework

A complete, production-ready SaaS framework built with FastAPI, Supabase, and Stripe. This framework provides all the essential components needed to quickly build and deploy a SaaS application.

## Features

### Authentication
- Email/password registration with verification
- Google OAuth integration
- Session management
- CSRF protection
- Rate limiting

### Subscription Management
- Stripe integration for payments
- Tiered subscription plans (free/premium)
- Usage tracking and credits system
- Webhook handling for subscription events

### Email Notifications
- Welcome emails
- Subscription confirmation emails
- Credit purchase confirmation emails
- Consistent email templates

### User Management
- User profiles
- Account management
- Subscription management
- Usage analytics

### UI Components
- Responsive dashboard
- Account management pages
- Subscription and billing pages
- Error pages

## Architecture

The framework follows a modular architecture with clear separation of concerns:

### Services
- `auth/service.py`: Authentication service
- `app/services/billing/stripe_service.py`: Stripe integration
- `app/services/billing/subscription_service.py`: Subscription management
- `app/services/email/email_service.py`: Email notifications
- `app/services/supabase_service.py`: Supabase integration

### Routes
- `routes/auth.py`: Authentication routes
- `routes/billing.py`: Billing and subscription routes
- `routes/billing_webhook.py`: Stripe webhook handling

### Configuration
- `app/config.py`: Application configuration
- `.env`: Environment variables

## Getting Started

1. Clone the repository
2. Create a `.env` file with your configuration
3. Install dependencies: `pip install -r requirements.txt`
4. Run the application: `python run.py`

## Environment Variables

```
# Application
APP_NAME=Your SaaS App
APP_DESCRIPTION=Your SaaS App Description
APP_VERSION=1.0.0
ENV=development
DEBUG=True
PORT=8004
BASE_URL=http://localhost:8004

# Supabase
SUPABASE_URL=your-supabase-url
SUPABASE_KEY=your-supabase-key
SUPABASE_SERVICE_KEY=your-supabase-service-key

# Stripe
STRIPE_API_KEY=your-stripe-api-key
STRIPE_WEBHOOK_SECRET=your-stripe-webhook-secret
STRIPE_PREMIUM_PRICE_ID=your-stripe-premium-price-id
STRIPE_CREDITS_5_PRICE_ID=your-stripe-credits-5-price-id
STRIPE_CREDITS_10_PRICE_ID=your-stripe-credits-10-price-id
STRIPE_CREDITS_25_PRICE_ID=your-stripe-credits-25-price-id

# Email
SMTP_SERVER=your-smtp-server
SMTP_PORT=587
SMTP_USER=your-smtp-user
SMTP_PASSWORD=your-smtp-password
EMAIL_FROM=noreply@yourdomain.com

# Session
SESSION_SECRET_KEY=your-session-secret-key
SESSION_MAX_AGE=86400
SESSION_SAME_SITE=lax
SESSION_HTTPS_ONLY=False
```

## Customization

To customize the framework for your own SaaS application:

1. Update the branding in templates
2. Configure your Stripe products and prices
3. Set up your Supabase project
4. Add your specific business logic
5. Customize the UI to match your brand

## Extension Points

The framework is designed to be easily extended:

1. Add new services in `app/services/`
2. Add new routes in `routes/`
3. Add new templates in `templates/`
4. Add new static files in `static/`

## Best Practices

1. Keep files under 1000 lines
2. Follow the existing error handling patterns
3. Add comprehensive logging
4. Document all functions and methods
5. Add tests for new functionality

## License

MIT License
