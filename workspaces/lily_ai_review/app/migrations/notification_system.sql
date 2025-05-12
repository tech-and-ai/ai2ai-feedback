-- Notification System Database Schema

-- Store email templates
CREATE TABLE IF NOT EXISTS saas_notification_templates (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(100) NOT NULL UNIQUE,
    description TEXT,
    subject VARCHAR(255) NOT NULL,
    html_content TEXT NOT NULL,
    text_content TEXT NOT NULL,
    version INT NOT NULL DEFAULT 1,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Map events to templates
CREATE TABLE IF NOT EXISTS saas_notification_events (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    event_type VARCHAR(100) NOT NULL UNIQUE,
    template_id UUID NOT NULL REFERENCES saas_notification_templates(id),
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Track notification history
CREATE TABLE IF NOT EXISTS saas_notification_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES auth.users(id),
    event_type VARCHAR(100) NOT NULL,
    template_id UUID REFERENCES saas_notification_templates(id),
    recipient_email VARCHAR(255) NOT NULL,
    status VARCHAR(50) NOT NULL, -- 'sent', 'failed', 'delivered', etc.
    error_message TEXT,
    metadata JSONB, -- Additional data like SMTP response, tracking info
    sent_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- User notification preferences
CREATE TABLE IF NOT EXISTS saas_user_notification_preferences (
    user_id UUID REFERENCES auth.users(id),
    notification_type VARCHAR(100) NOT NULL,
    enabled BOOLEAN NOT NULL DEFAULT TRUE,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    PRIMARY KEY (user_id, notification_type)
);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_notification_logs_user_id ON saas_notification_logs(user_id);
CREATE INDEX IF NOT EXISTS idx_notification_logs_event_type ON saas_notification_logs(event_type);
CREATE INDEX IF NOT EXISTS idx_notification_logs_sent_at ON saas_notification_logs(sent_at);
