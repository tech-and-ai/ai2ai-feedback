-- Create subscription tables for Stripe integration

-- User subscriptions table to track subscriptions
CREATE TABLE IF NOT EXISTS public.saas_user_subscriptions (
    id SERIAL PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    subscription_tier VARCHAR(20) NOT NULL DEFAULT 'sample', -- sample, basic, premium, pro
    status VARCHAR(20) NOT NULL DEFAULT 'active', -- active, past_due, canceled, etc.
    papers_limit INTEGER NOT NULL DEFAULT 1,
    papers_used INTEGER NOT NULL DEFAULT 0,
    current_period_end TIMESTAMP WITH TIME ZONE,
    stripe_subscription_id VARCHAR(100),
    stripe_customer_id VARCHAR(100),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
    UNIQUE(user_id)
);

-- Create RLS policies for user subscriptions
ALTER TABLE public.saas_user_subscriptions ENABLE ROW LEVEL SECURITY;

-- Allow users to read their own subscriptions
CREATE POLICY "Users can read their own subscriptions" ON public.saas_user_subscriptions
    FOR SELECT
    USING (auth.uid() = user_id);

-- Only allow service role to insert, update, or delete subscriptions
CREATE POLICY "Service role can manage all subscriptions" ON public.saas_user_subscriptions
    USING (auth.role() = 'service_role');

-- Create trigger for updated_at timestamp
CREATE OR REPLACE FUNCTION update_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = now();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER update_subscription_timestamp
BEFORE UPDATE ON public.saas_user_subscriptions
FOR EACH ROW
EXECUTE FUNCTION update_timestamp();

-- Initialize sample subscriptions for existing users
INSERT INTO public.saas_user_subscriptions (user_id, subscription_tier, status, papers_limit, papers_used, current_period_end)
SELECT id, 'sample', 'active', 1, 0, now() + interval '30 days'
FROM auth.users
WHERE id NOT IN (SELECT user_id FROM public.saas_user_subscriptions)
ON CONFLICT (user_id) DO NOTHING; 