-- Create pricing tables for dynamic content management

-- Pricing plans table
CREATE TABLE IF NOT EXISTS public.saas_pricing_plans (
    id SERIAL PRIMARY KEY,
    name VARCHAR(50) NOT NULL,
    display_name VARCHAR(100) NOT NULL,
    price DECIMAL(10,2) NOT NULL,
    currency VARCHAR(3) NOT NULL DEFAULT 'GBP',
    billing_period VARCHAR(20) NOT NULL DEFAULT 'month',
    credits_per_period INTEGER NOT NULL,
    is_highlighted BOOLEAN DEFAULT FALSE,
    highlight_label VARCHAR(50),
    is_active BOOLEAN DEFAULT TRUE,
    display_order INTEGER NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT now()
);

-- Pricing features table
CREATE TABLE IF NOT EXISTS public.saas_pricing_features (
    id SERIAL PRIMARY KEY,
    plan_id INTEGER REFERENCES public.saas_pricing_plans(id) ON DELETE CASCADE,
    feature_text VARCHAR(255) NOT NULL,
    is_highlighted BOOLEAN DEFAULT FALSE,
    is_included BOOLEAN DEFAULT TRUE,
    display_order INTEGER NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT now()
);

-- Pricing add-ons table (for credit packs)
CREATE TABLE IF NOT EXISTS public.saas_pricing_addons (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    display_name VARCHAR(100) NOT NULL,
    description TEXT,
    price DECIMAL(10,2) NOT NULL,
    currency VARCHAR(3) NOT NULL DEFAULT 'GBP',
    credits INTEGER NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    display_order INTEGER NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT now()
);

-- Pricing display content (for marketing copy)
CREATE TABLE IF NOT EXISTS public.saas_pricing_display (
    id SERIAL PRIMARY KEY,
    section VARCHAR(50) NOT NULL,
    title VARCHAR(255),
    subtitle TEXT,
    content TEXT NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    display_order INTEGER NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT now()
);

-- Create triggers for updated_at timestamps
CREATE OR REPLACE FUNCTION update_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = now();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER update_pricing_plans_timestamp
BEFORE UPDATE ON public.saas_pricing_plans
FOR EACH ROW
EXECUTE FUNCTION update_timestamp();

CREATE TRIGGER update_pricing_features_timestamp
BEFORE UPDATE ON public.saas_pricing_features
FOR EACH ROW
EXECUTE FUNCTION update_timestamp();

CREATE TRIGGER update_pricing_addons_timestamp
BEFORE UPDATE ON public.saas_pricing_addons
FOR EACH ROW
EXECUTE FUNCTION update_timestamp();

CREATE TRIGGER update_pricing_display_timestamp
BEFORE UPDATE ON public.saas_pricing_display
FOR EACH ROW
EXECUTE FUNCTION update_timestamp();

-- Insert initial pricing plans
INSERT INTO public.saas_pricing_plans (name, display_name, price, currency, billing_period, credits_per_period, is_highlighted, highlight_label, is_active, display_order)
VALUES
    ('free', 'Free', 0.00, 'GBP', 'month', 0, FALSE, NULL, TRUE, 1),
    ('basic', 'Basic', 9.99, 'GBP', 'month', 3, FALSE, NULL, TRUE, 2),
    ('premium', 'Premium', 20.00, 'GBP', 'month', 10, TRUE, 'RECOMMENDED', TRUE, 3),
    ('pro', 'Pro', 39.99, 'GBP', 'month', 999999, FALSE, NULL, TRUE, 4)
ON CONFLICT DO NOTHING;

-- Insert initial pricing features
-- Free plan features
INSERT INTO public.saas_pricing_features (plan_id, feature_text, is_highlighted, is_included, display_order)
VALUES
    ((SELECT id FROM public.saas_pricing_plans WHERE name = 'free'), 'Sample research packs', FALSE, TRUE, 1),
    ((SELECT id FROM public.saas_pricing_plans WHERE name = 'free'), 'Basic research depth', FALSE, TRUE, 2),
    ((SELECT id FROM public.saas_pricing_plans WHERE name = 'free'), 'PDF downloads', FALSE, TRUE, 3),
    ((SELECT id FROM public.saas_pricing_plans WHERE name = 'free'), 'Research paper generation', FALSE, FALSE, 4);

-- Basic plan features
INSERT INTO public.saas_pricing_features (plan_id, feature_text, is_highlighted, is_included, display_order)
VALUES
    ((SELECT id FROM public.saas_pricing_plans WHERE name = 'basic'), '3 papers per month', FALSE, TRUE, 1),
    ((SELECT id FROM public.saas_pricing_plans WHERE name = 'basic'), 'Basic research depth', FALSE, TRUE, 2),
    ((SELECT id FROM public.saas_pricing_plans WHERE name = 'basic'), 'PDF downloads', FALSE, TRUE, 3),
    ((SELECT id FROM public.saas_pricing_plans WHERE name = 'basic'), 'Research paper generation', FALSE, FALSE, 4);

-- Premium plan features
INSERT INTO public.saas_pricing_features (plan_id, feature_text, is_highlighted, is_included, display_order)
VALUES
    ((SELECT id FROM public.saas_pricing_plans WHERE name = 'premium'), '10 papers per month', TRUE, TRUE, 1),
    ((SELECT id FROM public.saas_pricing_plans WHERE name = 'premium'), 'Advanced research depth', FALSE, TRUE, 2),
    ((SELECT id FROM public.saas_pricing_plans WHERE name = 'premium'), 'PDF & DOCX downloads', FALSE, TRUE, 3),
    ((SELECT id FROM public.saas_pricing_plans WHERE name = 'premium'), 'Research paper generation', TRUE, TRUE, 4);

-- Pro plan features
INSERT INTO public.saas_pricing_features (plan_id, feature_text, is_highlighted, is_included, display_order)
VALUES
    ((SELECT id FROM public.saas_pricing_plans WHERE name = 'pro'), 'Unlimited papers', TRUE, TRUE, 1),
    ((SELECT id FROM public.saas_pricing_plans WHERE name = 'pro'), 'Premium research depth', FALSE, TRUE, 2),
    ((SELECT id FROM public.saas_pricing_plans WHERE name = 'pro'), 'All file formats', FALSE, TRUE, 3),
    ((SELECT id FROM public.saas_pricing_plans WHERE name = 'pro'), 'Priority support', FALSE, TRUE, 4);

-- Insert initial pricing add-ons
INSERT INTO public.saas_pricing_addons (name, display_name, description, price, currency, credits, is_active, display_order)
VALUES
    ('credits_5', '5 Credits', '5 additional paper credits', 8.99, 'GBP', 5, TRUE, 1),
    ('credits_10', '10 Credits', '10 additional paper credits', 15.99, 'GBP', 10, TRUE, 2),
    ('credits_25', '25 Credits', '25 additional paper credits', 34.99, 'GBP', 25, TRUE, 3);

-- Insert initial pricing display content
INSERT INTO public.saas_pricing_display (section, title, subtitle, content, is_active, display_order)
VALUES
    ('home_pricing', 'Simple, Transparent Pricing', NULL, 'Choose the plan that works best for you.', TRUE, 1),
    ('home_addon', 'Add-on Credits', 'From £1.40/credit', 'For Premium subscribers who need more than 10 credits per month', TRUE, 2),
    ('home_edu', 'Educational Institutions', 'Bespoke packages for universities and higher education', 'Tailored solutions for universities and higher education institutions worldwide. We support academic development and integrity with flexible options for research support and student learning.', TRUE, 3),
    ('subscription_addon', 'Need More Papers?', 'Buy Additional Paper Credits', 'Need more papers than your subscription allows? Purchase additional paper credits that never expire.', TRUE, 1);
