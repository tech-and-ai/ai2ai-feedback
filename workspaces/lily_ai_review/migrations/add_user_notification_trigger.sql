-- Create a function to send welcome emails to new users
CREATE OR REPLACE FUNCTION public.handle_new_user_notification()
RETURNS TRIGGER AS $$
DECLARE
    webhook_url TEXT;
    payload JSONB;
    response JSONB;
BEGIN
    -- Get the webhook URL from the config table
    SELECT value INTO webhook_url FROM public.saas_config WHERE key = 'notification_webhook_url';
    
    -- If no webhook URL is configured, exit
    IF webhook_url IS NULL THEN
        RETURN NEW;
    END IF;
    
    -- Create the payload
    payload := jsonb_build_object(
        'event', 'user.created',
        'user_id', NEW.id,
        'email', NEW.email,
        'created_at', NEW.created_at
    );
    
    -- Send the webhook
    BEGIN
        SELECT
            content::jsonb
        INTO response
        FROM
            http((
                'POST',
                webhook_url,
                ARRAY[http_header('Content-Type', 'application/json')],
                payload::text,
                NULL
            )::http_request);
        
        -- Log the response
        INSERT INTO public.saas_notification_logs (
            event_type,
            user_id,
            recipient_email,
            status,
            metadata,
            sent_at
        ) VALUES (
            'user.created',
            NEW.id,
            NEW.email,
            'sent',
            jsonb_build_object('response', response),
            NOW()
        );
    EXCEPTION WHEN OTHERS THEN
        -- Log the error
        INSERT INTO public.saas_notification_logs (
            event_type,
            user_id,
            recipient_email,
            status,
            error_message,
            sent_at
        ) VALUES (
            'user.created',
            NEW.id,
            NEW.email,
            'failed',
            SQLERRM,
            NOW()
        );
    END;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Create a trigger to call the function when a new user is created
DROP TRIGGER IF EXISTS user_notification_trigger ON auth.users;
CREATE TRIGGER user_notification_trigger
AFTER INSERT ON auth.users
FOR EACH ROW
EXECUTE FUNCTION public.handle_new_user_notification();

-- Create a function to send notifications when a subscription changes
CREATE OR REPLACE FUNCTION public.handle_subscription_notification()
RETURNS TRIGGER AS $$
DECLARE
    webhook_url TEXT;
    payload JSONB;
    response JSONB;
    old_data JSONB;
    new_data JSONB;
BEGIN
    -- Get the webhook URL from the config table
    SELECT value INTO webhook_url FROM public.saas_config WHERE key = 'notification_webhook_url';
    
    -- If no webhook URL is configured, exit
    IF webhook_url IS NULL THEN
        RETURN NEW;
    END IF;
    
    -- Create the payload
    IF TG_OP = 'INSERT' THEN
        old_data := NULL;
    ELSE
        old_data := row_to_json(OLD)::jsonb;
    END IF;
    
    new_data := row_to_json(NEW)::jsonb;
    
    payload := jsonb_build_object(
        'event', 'subscription.changed',
        'user_id', NEW.user_id,
        'old_data', old_data,
        'new_data', new_data,
        'timestamp', NOW()
    );
    
    -- Send the webhook
    BEGIN
        SELECT
            content::jsonb
        INTO response
        FROM
            http((
                'POST',
                webhook_url,
                ARRAY[http_header('Content-Type', 'application/json')],
                payload::text,
                NULL
            )::http_request);
        
        -- Log the response
        INSERT INTO public.saas_notification_logs (
            event_type,
            user_id,
            status,
            metadata,
            sent_at
        ) VALUES (
            'subscription.changed',
            NEW.user_id,
            'sent',
            jsonb_build_object('response', response),
            NOW()
        );
    EXCEPTION WHEN OTHERS THEN
        -- Log the error
        INSERT INTO public.saas_notification_logs (
            event_type,
            user_id,
            status,
            error_message,
            sent_at
        ) VALUES (
            'subscription.changed',
            NEW.user_id,
            'failed',
            SQLERRM,
            NOW()
        );
    END;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Create a trigger to call the function when a subscription changes
DROP TRIGGER IF EXISTS subscription_notification_trigger ON public.saas_user_subscriptions;
CREATE TRIGGER subscription_notification_trigger
AFTER INSERT OR UPDATE ON public.saas_user_subscriptions
FOR EACH ROW
EXECUTE FUNCTION public.handle_subscription_notification();

-- Create a config entry for the notification webhook URL
INSERT INTO public.saas_config (key, value, description)
VALUES (
    'notification_webhook_url',
    'http://localhost:8004/api/notifications/webhook',
    'URL for the notification webhook'
) ON CONFLICT (key) DO UPDATE SET value = EXCLUDED.value;
