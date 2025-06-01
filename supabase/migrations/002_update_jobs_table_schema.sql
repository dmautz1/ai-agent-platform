-- Migration: Update jobs table schema to match application requirements
-- Created: 2024-12-XX
-- Description: Adds missing columns and updates schema to match DatabaseOperations class

-- Add missing columns to jobs table
ALTER TABLE jobs 
ADD COLUMN IF NOT EXISTS user_id UUID,
ADD COLUMN IF NOT EXISTS type TEXT,
ADD COLUMN IF NOT EXISTS completed_at TIMESTAMP WITH TIME ZONE,
ADD COLUMN IF NOT EXISTS failed_at TIMESTAMP WITH TIME ZONE;

-- Update status constraint to ensure consistency
ALTER TABLE jobs DROP CONSTRAINT IF EXISTS jobs_status_check;
ALTER TABLE jobs ADD CONSTRAINT jobs_status_check 
CHECK (status IN ('pending', 'running', 'completed', 'failed'));

-- Update result column to be JSONB for structured data
ALTER TABLE jobs ALTER COLUMN result TYPE JSONB USING result::jsonb;

-- Create additional indexes for performance
CREATE INDEX IF NOT EXISTS idx_jobs_user_id ON jobs(user_id);
CREATE INDEX IF NOT EXISTS idx_jobs_type ON jobs(type);
CREATE INDEX IF NOT EXISTS idx_jobs_user_status ON jobs(user_id, status);
CREATE INDEX IF NOT EXISTS idx_jobs_completed_at ON jobs(completed_at DESC);
CREATE INDEX IF NOT EXISTS idx_jobs_failed_at ON jobs(failed_at DESC);

-- Add foreign key constraint for user_id if auth.users table exists
-- Note: This assumes Supabase auth is enabled
-- ALTER TABLE jobs ADD CONSTRAINT fk_jobs_user_id 
-- FOREIGN KEY (user_id) REFERENCES auth.users(id) ON DELETE CASCADE;

-- Update comments
COMMENT ON COLUMN jobs.user_id IS 'ID of the user who created the job';
COMMENT ON COLUMN jobs.type IS 'Type of agent/job being executed';
COMMENT ON COLUMN jobs.completed_at IS 'Timestamp when the job completed successfully';
COMMENT ON COLUMN jobs.failed_at IS 'Timestamp when the job failed';

-- Update the job_stats view to include new columns
DROP VIEW IF EXISTS job_stats;
CREATE OR REPLACE VIEW job_stats AS
SELECT 
    status,
    type,
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
GROUP BY status, type;

COMMENT ON VIEW job_stats IS 'Provides summary statistics for jobs by status and type'; 