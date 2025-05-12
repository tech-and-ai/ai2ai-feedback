-- Jobs table for the queuing system
CREATE TABLE IF NOT EXISTS jobs (
    -- Primary key and identifiers
    job_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL,

    -- Job metadata
    job_type VARCHAR(50) NOT NULL,  -- e.g., 'research_pack', 'diagram', etc.
    status VARCHAR(20) NOT NULL CHECK (status IN ('queued', 'in_progress', 'completed', 'errored')),
    priority SMALLINT NOT NULL DEFAULT 3 CHECK (priority >= 0 AND priority <= 3),

    -- Timestamps for tracking and sorting
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    started_at TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE,

    -- Job details
    parameters JSONB NOT NULL,  -- Topic, question, education level, etc.
    result JSONB,               -- Output file paths, URLs, etc.
    error_message TEXT,         -- Error details if status is 'errored'

    -- Worker tracking
    worker_id VARCHAR(100),     -- ID of the worker processing this job

    -- Indexes for efficient querying
    CONSTRAINT fk_user FOREIGN KEY (user_id) REFERENCES auth.users(id) ON DELETE CASCADE
);

-- Index for efficient queue processing (priority, then created_at)
CREATE INDEX IF NOT EXISTS idx_jobs_queue ON jobs (priority, created_at)
WHERE status = 'queued';

-- Index for finding a user's jobs
CREATE INDEX IF NOT EXISTS idx_jobs_user ON jobs (user_id, created_at DESC);

-- Index for status-based queries
CREATE INDEX IF NOT EXISTS idx_jobs_status ON jobs (status, updated_at DESC);

-- Function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger to automatically update updated_at
CREATE TRIGGER update_jobs_updated_at
BEFORE UPDATE ON jobs
FOR EACH ROW
EXECUTE FUNCTION update_updated_at_column();

-- RLS (Row Level Security) policies
-- Enable RLS
ALTER TABLE jobs ENABLE ROW LEVEL SECURITY;

-- Admin can do anything
CREATE POLICY admin_all ON jobs
    TO authenticated
    USING (
        EXISTS (
            SELECT 1 FROM auth.users
            WHERE auth.users.id = auth.uid()
            AND auth.users.is_admin = true
        )
    );

-- Users can only see their own jobs
CREATE POLICY user_select ON jobs
    FOR SELECT
    TO authenticated
    USING (user_id = auth.uid());

-- Users can only insert their own jobs
CREATE POLICY user_insert ON jobs
    FOR INSERT
    TO authenticated
    WITH CHECK (user_id = auth.uid());

-- Users can only update their own jobs
CREATE POLICY user_update ON jobs
    FOR UPDATE
    TO authenticated
    USING (user_id = auth.uid());

-- Workers need a service role to process any job
-- This will be handled through service role authentication
