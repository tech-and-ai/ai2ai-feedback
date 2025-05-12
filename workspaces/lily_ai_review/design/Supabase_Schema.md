# Supabase Context Tables

This document outlines the database schema for the Lily AI system, implemented in Supabase PostgreSQL.

## Core Tables

### 1. Jobs Table

The `jobs` table is the central table for the queuing system. It tracks all research pack generation jobs and their status.

```sql
CREATE TABLE jobs (
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
    
    -- Foreign key to user
    CONSTRAINT fk_user FOREIGN KEY (user_id) REFERENCES auth.users(id) ON DELETE CASCADE
);

-- Indexes for efficient querying
CREATE INDEX idx_jobs_queue ON jobs (priority, created_at) WHERE status = 'queued';
CREATE INDEX idx_jobs_user ON jobs (user_id, created_at DESC);
CREATE INDEX idx_jobs_status ON jobs (status, updated_at DESC);
```

### 2. Users Table (Supabase Auth)

Supabase provides a built-in `auth.users` table that we use for user authentication and management.

Key fields we use:
- `id`: UUID primary key
- `email`: User's email address
- `created_at`: When the user was created
- `last_sign_in_at`: When the user last signed in
- Custom metadata fields:
  - `subscription_tier`: User's subscription tier (sample, standard, premium)
  - `paper_limit`: Number of papers allowed per billing period
  - `papers_used`: Number of papers used in the current billing period

### 3. Research Pack Sections Table

This table stores the different sections that can be included in a research pack.

```sql
CREATE TABLE research_pack_sections (
    section_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(100) NOT NULL,
    description TEXT,
    is_required BOOLEAN DEFAULT true,
    display_order INTEGER NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

### 4. Lily Callout Types Table

This table stores the different types of callouts that can be added to research packs.

```sql
CREATE TABLE lily_callout_types (
    callout_type_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(50) NOT NULL UNIQUE,
    description TEXT,
    icon VARCHAR(50),
    color VARCHAR(20),
    is_enabled BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

### 5. Prompts Table

This table stores the prompts used by the system for generating content.

```sql
CREATE TABLE prompts (
    prompt_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(100) NOT NULL,
    description TEXT,
    prompt_text TEXT NOT NULL,
    usage_location VARCHAR(100) NOT NULL,
    is_enabled BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

### 6. Citations Table

This table stores citations used in research packs.

```sql
CREATE TABLE citations (
    citation_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    job_id UUID NOT NULL,
    title VARCHAR(255) NOT NULL,
    authors TEXT,
    publication VARCHAR(255),
    year INTEGER,
    url TEXT,
    citation_text TEXT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    CONSTRAINT fk_job FOREIGN KEY (job_id) REFERENCES jobs(job_id) ON DELETE CASCADE
);
```

## Row Level Security (RLS) Policies

Supabase uses Row Level Security to control access to data. Here are the key policies:

### Jobs Table Policies

```sql
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
```

### Citations Table Policies

```sql
-- Enable RLS
ALTER TABLE citations ENABLE ROW LEVEL SECURITY;

-- Admin can do anything
CREATE POLICY admin_all ON citations
    TO authenticated
    USING (
        EXISTS (
            SELECT 1 FROM auth.users
            WHERE auth.users.id = auth.uid()
            AND auth.users.is_admin = true
        )
    );

-- Users can only see citations for their own jobs
CREATE POLICY user_select ON citations
    FOR SELECT
    TO authenticated
    USING (
        EXISTS (
            SELECT 1 FROM jobs
            WHERE jobs.job_id = citations.job_id
            AND jobs.user_id = auth.uid()
        )
    );
```

## Storage Buckets

Supabase Storage is used to store files generated by the system.

### Research Packs Bucket

This bucket stores the DOCX and PDF files for research packs.

```sql
-- Create the bucket
INSERT INTO storage.buckets (id, name, public)
VALUES ('research-packs', 'Research Packs', true);

-- Set up RLS policies
CREATE POLICY "Users can view their own research packs"
ON storage.objects FOR SELECT
TO authenticated
USING (
    bucket_id = 'research-packs' AND
    (storage.foldername(name))[1] = auth.uid()::text
);

CREATE POLICY "Users can upload their own research packs"
ON storage.objects FOR INSERT
TO authenticated
WITH CHECK (
    bucket_id = 'research-packs' AND
    (storage.foldername(name))[1] = auth.uid()::text
);
```

### Diagrams Bucket

This bucket stores diagram images generated for research packs.

```sql
-- Create the bucket
INSERT INTO storage.buckets (id, name, public)
VALUES ('diagrams', 'Diagrams', true);

-- Set up RLS policies
CREATE POLICY "Users can view their own diagrams"
ON storage.objects FOR SELECT
TO authenticated
USING (
    bucket_id = 'diagrams' AND
    (storage.foldername(name))[1] = auth.uid()::text
);

CREATE POLICY "Users can upload their own diagrams"
ON storage.objects FOR INSERT
TO authenticated
WITH CHECK (
    bucket_id = 'diagrams' AND
    (storage.foldername(name))[1] = auth.uid()::text
);
```
