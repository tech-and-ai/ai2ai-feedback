# SaaS Framework

A modular, reusable SaaS framework with authentication, subscription management, and payment processing.

## Features

- User authentication (email/password and Google OAuth)
- Email verification
- User profile management
- Subscription management with Stripe
- Paper credits system
- reCAPTCHA integration for security
- Responsive UI with Bootstrap

## Prerequisites

- Python 3.9+
- Supabase account
- Stripe account
- Google OAuth credentials (optional)
- reCAPTCHA Enterprise API keys

## Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/saas-framework.git
   cd saas-framework
   ```

2. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Copy the example environment file:
   ```bash
   cp .env.example .env
   ```

5. Update the `.env` file with your credentials:
   - Supabase credentials
   - Stripe API keys
   - reCAPTCHA keys
   - Application settings

## Stripe Setup

Before running the application, you need to set up the following in your Stripe account:

1. Create products and prices:
   - Premium subscription product
   - Paper credits products (5, 10, 25 credits)

2. Create payment links for each product

3. Update the `.env` file with the product IDs, price IDs, and payment links

## Supabase Setup

1. Create a new Supabase project

2. Set up the following tables:
   - `lily_subscriptions`
   - `lily_payments`
   - `lily_papers`
   - `lily_settings`
   - `saas_notification_templates`
   - `saas_notification_logs`

3. Configure authentication:
   - Enable email/password authentication
   - Set up Google OAuth (optional)
   - Configure email templates

## Running the Application

1. Start the application:
   ```bash
   python run.py
   ```

2. Access the application at http://localhost:8004

## Customization

### Branding

1. Update the application name and contact email in the `.env` file

2. Replace the logo in `static/images/logo.svg`

3. Customize the color scheme in `static/css/styles.css`

### Email Templates

Email templates are stored in the Supabase database in the `saas_notification_templates` table. You can customize them by updating the HTML and text content.

### Subscription Tiers

To modify the subscription tiers:

1. Update the subscription plans in the Stripe dashboard

2. Update the product and price IDs in the `.env` file

3. Modify the subscription page template in `templates/subscription.html`

## Integrating with Your Core Engine

This SaaS framework is designed to be modular and can be integrated with any core engine. To integrate with your core engine:

1. Create a new module in the `app` directory for your core engine

2. Update the routes in `main.py` to include your core engine's endpoints

3. Add any necessary templates to the `templates` directory

4. Update the dashboard to include links to your core engine's features

## Webhook Setup

To handle Stripe webhooks:

1. Set up a webhook endpoint in the Stripe dashboard pointing to `https://yourdomain.com/billing/webhook`

2. Update the `STRIPE_WEBHOOK_SECRET` in the `.env` file

## License

This project is licensed under the MIT License - see the LICENSE file for details.
