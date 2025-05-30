-- Migration: Create jobs table for AI Agent Template
-- Created: 2024-12-XX
-- Description: Creates the main jobs table with proper indexing for job scheduling and monitoring

-- Enable UUID extension if not already enabled
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Create the jobs table
CREATE TABLE IF NOT EXISTS jobs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    status TEXT NOT NULL CHECK (status IN ('pending', 'running', 'completed', 'failed')),
    data JSONB,
    result TEXT,
    error_message TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create indexes for better query performance
CREATE INDEX IF NOT EXISTS idx_jobs_status ON jobs(status);
CREATE INDEX IF NOT EXISTS idx_jobs_created_at ON jobs(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_jobs_updated_at ON jobs(updated_at DESC);
CREATE INDEX IF NOT EXISTS idx_jobs_status_created ON jobs(status, created_at DESC);

-- Create a GIN index on the JSONB data column for efficient JSON queries
CREATE INDEX IF NOT EXISTS idx_jobs_data_gin ON jobs USING GIN(data);

-- Create a function to automatically update the updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Create trigger to automatically update updated_at when a row is modified
CREATE TRIGGER update_jobs_updated_at 
    BEFORE UPDATE ON jobs 
    FOR EACH ROW 
    EXECUTE FUNCTION update_updated_at_column();

-- Add comments for documentation
COMMENT ON TABLE jobs IS 'Stores AI agent job information including status, input data, and results';
COMMENT ON COLUMN jobs.id IS 'Unique identifier for each job (UUID)';
COMMENT ON COLUMN jobs.status IS 'Current status of the job (pending, running, completed, failed)';
COMMENT ON COLUMN jobs.data IS 'Input data and parameters for the job stored as JSON';
COMMENT ON COLUMN jobs.result IS 'Job execution result or output';
COMMENT ON COLUMN jobs.error_message IS 'Error message if job failed';
COMMENT ON COLUMN jobs.created_at IS 'Timestamp when the job was created';
COMMENT ON COLUMN jobs.updated_at IS 'Timestamp when the job was last updated';

-- Grant permissions (adjust as needed for your setup)
-- These grants assume you have a service role for the application
-- ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO service_role;
-- GRANT ALL ON jobs TO service_role;
-- GRANT USAGE ON SCHEMA public TO anon, authenticated;
-- GRANT SELECT, INSERT, UPDATE ON jobs TO authenticated;

-- Optional: Create a view for job statistics
CREATE OR REPLACE VIEW job_stats AS
SELECT 
    status,
    COUNT(*) as count,
    MIN(created_at) as first_job,
    MAX(created_at) as last_job,
    AVG(EXTRACT(EPOCH FROM (updated_at - created_at))) as avg_duration_seconds
FROM jobs 
GROUP BY status;

COMMENT ON VIEW job_stats IS 'Provides summary statistics for jobs by status';

-- Insert sample data for testing (can be removed in production)
-- INSERT INTO jobs (status, data, result) VALUES 
-- ('completed', '{"task": "sample", "input": "test"}', 'Sample job completed successfully'),
-- ('pending', '{"task": "pending_sample", "input": "waiting"}', NULL),
-- ('failed', '{"task": "failed_sample", "input": "error"}', NULL);

-- Verify the table was created successfully
-- SELECT table_name, column_name, data_type, is_nullable 
-- FROM information_schema.columns 
-- WHERE table_name = 'jobs' 
-- ORDER BY ordinal_position; 