-- Add footer copyright text configuration to saas_lily_ai_config table

-- Check if the table exists, create it if it doesn't
CREATE TABLE IF NOT EXISTS saas_lily_ai_config (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(100) NOT NULL,
    config_key VARCHAR(100) NOT NULL UNIQUE,
    config_value TEXT NOT NULL,
    description TEXT,
    enabled BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Insert footer copyright text configuration
INSERT INTO saas_lily_ai_config (name, config_key, config_value, description, enabled)
VALUES (
    'Footer Copyright Text',
    'footer_copyright_text',
    '© 2025 researchassistant.uk - All rights reserved',
    'Copyright text displayed in the footer of the website and documents',
    TRUE
)
ON CONFLICT (config_key)
DO UPDATE SET
    name = EXCLUDED.name,
    config_value = EXCLUDED.config_value,
    description = EXCLUDED.description,
    updated_at = NOW();

-- Create an index on config_key for faster lookups
CREATE INDEX IF NOT EXISTS idx_saas_lily_ai_config_key ON saas_lily_ai_config(config_key);
