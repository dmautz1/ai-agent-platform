-- ============================================================================
-- AI Agent Platform MVP v1.0 - Complete Database Setup
-- ============================================================================
-- Description: Consolidated migration that creates the complete database schema
--              from scratch for the MVP v1.0. This includes all tables, indexes,
--              functions, triggers, and views needed for the application.
-- 
-- Created: 2024-12-XX
-- Version: 1.0.0
-- Compatibility: Supabase/PostgreSQL
-- ============================================================================

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ============================================================================
-- MAIN TABLES
-- ============================================================================

-- Create the jobs table with all required columns
CREATE TABLE IF NOT EXISTS jobs (
    -- Core identification and metadata
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID,
    agent_identifier TEXT,
    title TEXT,
    
    -- Job status and lifecycle
    status TEXT NOT NULL DEFAULT 'pending' CHECK (status IN ('pending', 'running', 'completed', 'failed')),
    priority INTEGER DEFAULT 5 CHECK (priority >= 0 AND priority <= 10),
    tags TEXT[] DEFAULT '{}',
    
    -- Job data and results
    data JSONB,
    result JSONB,
    result_format TEXT,
    error_message TEXT,
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    completed_at TIMESTAMP WITH TIME ZONE,
    failed_at TIMESTAMP WITH TIME ZONE
);

-- ============================================================================
-- INDEXES FOR PERFORMANCE
-- ============================================================================

-- Single column indexes
CREATE INDEX IF NOT EXISTS idx_jobs_status ON jobs(status);
CREATE INDEX IF NOT EXISTS idx_jobs_user_id ON jobs(user_id);
CREATE INDEX IF NOT EXISTS idx_jobs_agent_identifier ON jobs(agent_identifier);
CREATE INDEX IF NOT EXISTS idx_jobs_priority ON jobs(priority DESC);
CREATE INDEX IF NOT EXISTS idx_jobs_created_at ON jobs(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_jobs_updated_at ON jobs(updated_at DESC);
CREATE INDEX IF NOT EXISTS idx_jobs_completed_at ON jobs(completed_at DESC);
CREATE INDEX IF NOT EXISTS idx_jobs_failed_at ON jobs(failed_at DESC);

-- Composite indexes for common query patterns
CREATE INDEX IF NOT EXISTS idx_jobs_status_created ON jobs(status, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_jobs_user_status ON jobs(user_id, status);
CREATE INDEX IF NOT EXISTS idx_jobs_priority_status ON jobs(priority DESC, status);

-- Specialized indexes
CREATE INDEX IF NOT EXISTS idx_jobs_data_gin ON jobs USING GIN(data);
CREATE INDEX IF NOT EXISTS idx_jobs_tags ON jobs USING GIN(tags);

-- ============================================================================
-- FUNCTIONS AND TRIGGERS
-- ============================================================================

-- Function to automatically update the updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Trigger to automatically update updated_at when a row is modified
CREATE TRIGGER update_jobs_updated_at 
    BEFORE UPDATE ON jobs 
    FOR EACH ROW 
    EXECUTE FUNCTION update_updated_at_column();

-- ============================================================================
-- VIEWS AND STATISTICS
-- ============================================================================

-- Job statistics view for monitoring and analytics
CREATE OR REPLACE VIEW job_stats AS
SELECT 
    status,
    agent_identifier,
    priority,
    COUNT(*) as count,
    MIN(created_at) as first_job,
    MAX(created_at) as last_job,
    AVG(EXTRACT(EPOCH FROM (
        CASE 
            WHEN status = 'completed' THEN completed_at - created_at
            WHEN status = 'failed' THEN failed_at - created_at
            ELSE updated_at - created_at
        END
    ))) as avg_duration_seconds
FROM jobs 
GROUP BY status, agent_identifier, priority
ORDER BY priority DESC, status;

-- ============================================================================
-- SECURITY AND PERMISSIONS
-- ============================================================================

-- Enable Row Level Security (RLS) on jobs table
ALTER TABLE jobs ENABLE ROW LEVEL SECURITY;

-- Policy: Users can only see their own jobs
CREATE POLICY "Users can view own jobs" ON jobs
    FOR SELECT USING (auth.uid() = user_id);

-- Policy: Users can insert their own jobs
CREATE POLICY "Users can insert own jobs" ON jobs
    FOR INSERT WITH CHECK (auth.uid() = user_id);

-- Policy: Users can update their own jobs
CREATE POLICY "Users can update own jobs" ON jobs
    FOR UPDATE USING (auth.uid() = user_id);

-- Policy: Users can delete their own jobs
CREATE POLICY "Users can delete own jobs" ON jobs
    FOR DELETE USING (auth.uid() = user_id);

-- Grant permissions to authenticated users
GRANT USAGE ON SCHEMA public TO anon, authenticated;
GRANT SELECT, INSERT, UPDATE, DELETE ON jobs TO authenticated;
GRANT SELECT ON job_stats TO authenticated;

-- ============================================================================
-- DOCUMENTATION AND COMMENTS
-- ============================================================================

-- Table documentation
COMMENT ON TABLE jobs IS 'Stores AI agent job information including status, input data, and results';

-- Column documentation
COMMENT ON COLUMN jobs.id IS 'Unique identifier for each job (UUID)';
COMMENT ON COLUMN jobs.user_id IS 'ID of the user who created the job (references auth.users)';
COMMENT ON COLUMN jobs.agent_identifier IS 'Generic string identifier for the agent that will process this job (e.g., simple_prompt, custom_research)';
COMMENT ON COLUMN jobs.title IS 'Human-readable title for the job for identification and organization';
COMMENT ON COLUMN jobs.status IS 'Current status of the job (pending, running, completed, failed)';
COMMENT ON COLUMN jobs.priority IS 'Job priority level (0=low, 5=normal, 8=high, 10=critical)';
COMMENT ON COLUMN jobs.tags IS 'Array of tags for job organization and filtering';
COMMENT ON COLUMN jobs.data IS 'Input data and parameters for the job stored as JSON';
COMMENT ON COLUMN jobs.result IS 'Job execution result or output stored as JSON';
COMMENT ON COLUMN jobs.result_format IS 'Format of the result data';
COMMENT ON COLUMN jobs.error_message IS 'Error message if job failed';
COMMENT ON COLUMN jobs.created_at IS 'Timestamp when the job was created';
COMMENT ON COLUMN jobs.updated_at IS 'Timestamp when the job was last updated (auto-updated via trigger)';
COMMENT ON COLUMN jobs.completed_at IS 'Timestamp when the job completed successfully';
COMMENT ON COLUMN jobs.failed_at IS 'Timestamp when the job failed';

-- View documentation
COMMENT ON VIEW job_stats IS 'Provides summary statistics for jobs by status, agent_identifier, and priority';
