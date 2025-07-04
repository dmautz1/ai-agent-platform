-- ============================================================================
-- AI Agent Platform - Complete Database Setup (Consolidated)
-- ============================================================================
-- Description: Consolidated migration that creates the complete database schema
--              from scratch including jobs table, schedules table, and all
--              extensions. This replaces all individual migration files.
-- 
-- Created: 2024-12-16
-- Version: 2.0.0 (Consolidated)
-- Compatibility: Supabase/PostgreSQL
-- Features: Jobs system, Agent scheduling, Statistics, Security
-- ============================================================================

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ============================================================================
-- UTILITY FUNCTIONS (Create first to avoid dependency issues)
-- ============================================================================

-- Function to automatically update the updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- ============================================================================
-- MAIN TABLES
-- ============================================================================

-- Jobs table with complete schema including scheduling extensions
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
    
    -- Scheduling fields (added for agent scheduling functionality)
    schedule_id UUID,
    execution_source TEXT NOT NULL DEFAULT 'manual' CHECK (execution_source IN ('manual', 'scheduled')),
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    completed_at TIMESTAMP WITH TIME ZONE,
    failed_at TIMESTAMP WITH TIME ZONE
);

-- Schedules table for agent scheduling system
CREATE TABLE IF NOT EXISTS schedules (
    -- Core identification and metadata
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL,
    agent_name TEXT NOT NULL,
    title TEXT NOT NULL,
    description TEXT,
    
    -- Agent configuration and scheduling
    agent_config_data JSONB NOT NULL,
    cron_expression TEXT NOT NULL,
    enabled BOOLEAN NOT NULL DEFAULT TRUE,
    timezone VARCHAR(100), -- User timezone for cron expression (e.g., 'America/New_York')
    
    -- Scheduling timestamps
    next_run TIMESTAMP WITH TIME ZONE,
    last_run TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Constraints
    CONSTRAINT schedules_user_id_fkey FOREIGN KEY (user_id) REFERENCES auth.users(id) ON DELETE CASCADE,
    CONSTRAINT schedules_cron_expression_check CHECK (length(cron_expression) > 0),
    CONSTRAINT schedules_title_check CHECK (length(title) > 0),
    CONSTRAINT schedules_agent_name_check CHECK (length(agent_name) > 0)
);

-- ============================================================================
-- FOREIGN KEY RELATIONSHIPS
-- ============================================================================

-- Link jobs to their source schedules (after both tables exist)
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.table_constraints 
        WHERE constraint_name = 'jobs_schedule_id_fkey'
        AND table_name = 'jobs'
        AND constraint_type = 'FOREIGN KEY'
    ) THEN
        ALTER TABLE jobs ADD CONSTRAINT jobs_schedule_id_fkey 
            FOREIGN KEY (schedule_id) REFERENCES schedules(id) ON DELETE SET NULL;
    END IF;
END $$;

-- ============================================================================
-- INDEXES FOR PERFORMANCE
-- ============================================================================

-- Jobs table indexes
CREATE INDEX IF NOT EXISTS idx_jobs_status ON jobs(status);
CREATE INDEX IF NOT EXISTS idx_jobs_user_id ON jobs(user_id);
CREATE INDEX IF NOT EXISTS idx_jobs_agent_identifier ON jobs(agent_identifier);
CREATE INDEX IF NOT EXISTS idx_jobs_priority ON jobs(priority DESC);
CREATE INDEX IF NOT EXISTS idx_jobs_created_at ON jobs(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_jobs_updated_at ON jobs(updated_at DESC);
CREATE INDEX IF NOT EXISTS idx_jobs_completed_at ON jobs(completed_at DESC);
CREATE INDEX IF NOT EXISTS idx_jobs_failed_at ON jobs(failed_at DESC);

-- Jobs scheduling indexes
CREATE INDEX IF NOT EXISTS idx_jobs_schedule_id ON jobs(schedule_id);
CREATE INDEX IF NOT EXISTS idx_jobs_execution_source ON jobs(execution_source);

-- Composite indexes for common query patterns
CREATE INDEX IF NOT EXISTS idx_jobs_status_created ON jobs(status, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_jobs_user_status ON jobs(user_id, status);
CREATE INDEX IF NOT EXISTS idx_jobs_priority_status ON jobs(priority DESC, status);
CREATE INDEX IF NOT EXISTS idx_jobs_user_execution_source ON jobs(user_id, execution_source);
CREATE INDEX IF NOT EXISTS idx_jobs_schedule_created ON jobs(schedule_id, created_at DESC) WHERE schedule_id IS NOT NULL;

-- Specialized indexes
CREATE INDEX IF NOT EXISTS idx_jobs_data_gin ON jobs USING GIN(data);
CREATE INDEX IF NOT EXISTS idx_jobs_tags ON jobs USING GIN(tags);

-- Schedules table indexes
CREATE INDEX IF NOT EXISTS idx_schedules_user_id ON schedules(user_id);
CREATE INDEX IF NOT EXISTS idx_schedules_agent_name ON schedules(agent_name);
CREATE INDEX IF NOT EXISTS idx_schedules_enabled ON schedules(enabled);
CREATE INDEX IF NOT EXISTS idx_schedules_next_run ON schedules(next_run);
CREATE INDEX IF NOT EXISTS idx_schedules_timezone ON schedules(timezone);
CREATE INDEX IF NOT EXISTS idx_schedules_created_at ON schedules(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_schedules_updated_at ON schedules(updated_at DESC);

-- Composite indexes for scheduler queries
CREATE INDEX IF NOT EXISTS idx_schedules_enabled_next_run ON schedules(enabled, next_run) WHERE enabled = TRUE;
CREATE INDEX IF NOT EXISTS idx_schedules_user_enabled ON schedules(user_id, enabled);

-- Specialized indexes
CREATE INDEX IF NOT EXISTS idx_schedules_agent_config_gin ON schedules USING GIN(agent_config_data);

-- ============================================================================
-- TRIGGERS (Create after tables and functions exist)
-- ============================================================================

-- Trigger to automatically update updated_at when jobs are modified
CREATE TRIGGER update_jobs_updated_at 
    BEFORE UPDATE ON jobs 
    FOR EACH ROW 
    EXECUTE FUNCTION update_updated_at_column();

-- Trigger to automatically update updated_at when schedules are modified
CREATE TRIGGER update_schedules_updated_at 
    BEFORE UPDATE ON schedules 
    FOR EACH ROW 
    EXECUTE FUNCTION update_updated_at_column();

-- ============================================================================
-- VIEWS AND STATISTICS
-- ============================================================================

-- Job statistics view with execution source breakdown
CREATE OR REPLACE VIEW job_stats AS
SELECT 
    status,
    agent_identifier,
    execution_source,
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
GROUP BY status, agent_identifier, execution_source, priority
ORDER BY priority DESC, status, execution_source;

-- Schedule-specific job statistics view
CREATE OR REPLACE VIEW schedule_job_stats AS
SELECT 
    s.id as schedule_id,
    s.title as schedule_title,
    s.agent_name,
    COUNT(j.id) as total_jobs,
    COUNT(CASE WHEN j.status = 'completed' THEN 1 END) as completed_jobs,
    COUNT(CASE WHEN j.status = 'failed' THEN 1 END) as failed_jobs,
    COUNT(CASE WHEN j.status = 'running' THEN 1 END) as running_jobs,
    COUNT(CASE WHEN j.status = 'pending' THEN 1 END) as pending_jobs,
    ROUND(
        (COUNT(CASE WHEN j.status = 'completed' THEN 1 END)::DECIMAL / 
         NULLIF(COUNT(CASE WHEN j.status IN ('completed', 'failed') THEN 1 END), 0)) * 100, 
        2
    ) as success_rate,
    MAX(j.created_at) as last_execution,
    s.next_run
FROM schedules s
LEFT JOIN jobs j ON s.id = j.schedule_id
GROUP BY s.id, s.title, s.agent_name, s.next_run
ORDER BY s.created_at DESC;

-- ============================================================================
-- SECURITY AND PERMISSIONS
-- ============================================================================

-- Enable Row Level Security (RLS) on both tables
ALTER TABLE jobs ENABLE ROW LEVEL SECURITY;
ALTER TABLE schedules ENABLE ROW LEVEL SECURITY;

-- Drop existing policies if they exist to avoid conflicts
DROP POLICY IF EXISTS "Users can view own jobs" ON jobs;
DROP POLICY IF EXISTS "Users can insert own jobs" ON jobs;
DROP POLICY IF EXISTS "Users can update own jobs" ON jobs;
DROP POLICY IF EXISTS "Users can delete own jobs" ON jobs;

DROP POLICY IF EXISTS "Users can view own schedules" ON schedules;
DROP POLICY IF EXISTS "Users can insert own schedules" ON schedules;
DROP POLICY IF EXISTS "Users can update own schedules" ON schedules;
DROP POLICY IF EXISTS "Users can delete own schedules" ON schedules;

-- Jobs table policies
CREATE POLICY "Users can view own jobs" ON jobs
    FOR SELECT USING (auth.uid() = user_id);

CREATE POLICY "Users can insert own jobs" ON jobs
    FOR INSERT WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update own jobs" ON jobs
    FOR UPDATE USING (auth.uid() = user_id);

CREATE POLICY "Users can delete own jobs" ON jobs
    FOR DELETE USING (auth.uid() = user_id);

-- Schedules table policies
CREATE POLICY "Users can view own schedules" ON schedules
    FOR SELECT USING (auth.uid() = user_id);

CREATE POLICY "Users can insert own schedules" ON schedules
    FOR INSERT WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update own schedules" ON schedules
    FOR UPDATE USING (auth.uid() = user_id);

CREATE POLICY "Users can delete own schedules" ON schedules
    FOR DELETE USING (auth.uid() = user_id);

-- Grant permissions to authenticated users
GRANT USAGE ON SCHEMA public TO anon, authenticated;
GRANT SELECT, INSERT, UPDATE, DELETE ON jobs TO authenticated;
GRANT SELECT, INSERT, UPDATE, DELETE ON schedules TO authenticated;
GRANT SELECT ON job_stats TO authenticated;
GRANT SELECT ON schedule_job_stats TO authenticated;

-- ============================================================================
-- DOCUMENTATION AND COMMENTS
-- ============================================================================

-- Jobs table documentation
COMMENT ON TABLE jobs IS 'Stores AI agent job information including status, input data, results, and scheduling information';

-- Jobs column documentation
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
COMMENT ON COLUMN jobs.schedule_id IS 'ID of the schedule that created this job (NULL for manually created jobs)';
COMMENT ON COLUMN jobs.execution_source IS 'Source of job execution: "manual" for user-created jobs, "scheduled" for automatically scheduled jobs';
COMMENT ON COLUMN jobs.created_at IS 'Timestamp when the job was created';
COMMENT ON COLUMN jobs.updated_at IS 'Timestamp when the job was last updated (auto-updated via trigger)';
COMMENT ON COLUMN jobs.completed_at IS 'Timestamp when the job completed successfully';
COMMENT ON COLUMN jobs.failed_at IS 'Timestamp when the job failed';

-- Schedules table documentation
COMMENT ON TABLE schedules IS 'Stores agent scheduling configurations with complete agent parameters for automatic execution';

-- Schedules column documentation
COMMENT ON COLUMN schedules.id IS 'Unique identifier for each schedule (UUID)';
COMMENT ON COLUMN schedules.user_id IS 'ID of the user who created the schedule (references auth.users)';
COMMENT ON COLUMN schedules.agent_name IS 'Name of the agent to be executed (e.g., simple_prompt, custom_research)';
COMMENT ON COLUMN schedules.title IS 'Human-readable title for the schedule (required, defaults to agent name)';
COMMENT ON COLUMN schedules.description IS 'Optional description of what this schedule does';
COMMENT ON COLUMN schedules.agent_config_data IS 'Complete agent configuration including all parameters needed for execution (JSONB)';
COMMENT ON COLUMN schedules.cron_expression IS 'Cron expression defining when the agent should run (e.g., "0 9 * * 1" for every Monday at 9 AM)';
COMMENT ON COLUMN schedules.enabled IS 'Whether this schedule is active and should be executed (defaults to TRUE)';
COMMENT ON COLUMN schedules.timezone IS 'User timezone for cron expression (e.g., America/New_York)';
COMMENT ON COLUMN schedules.next_run IS 'Calculated timestamp for the next scheduled execution';
COMMENT ON COLUMN schedules.last_run IS 'Timestamp of the last execution';
COMMENT ON COLUMN schedules.created_at IS 'Timestamp when the schedule was created';
COMMENT ON COLUMN schedules.updated_at IS 'Timestamp when the schedule was last updated (auto-updated via trigger)';

-- Views documentation
COMMENT ON VIEW job_stats IS 'Provides summary statistics for jobs by status, agent_identifier, execution_source, and priority';
COMMENT ON VIEW schedule_job_stats IS 'Provides execution statistics for each schedule including success rates and job counts';

