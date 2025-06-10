-- ============================================================================
-- AI Agent Template MVP v1.0 - Quick Database Setup Script
-- ============================================================================
-- This script sets up the complete database schema for the MVP v1.0
-- Run this in your Supabase SQL Editor for instant setup
-- ============================================================================

-- Import the consolidated migration
\i '../supabase/migrations/000_consolidated_mvp_setup.sql'

-- Additional setup for production environments
-- (Uncomment as needed)

-- Create additional admin views for monitoring
/*
CREATE OR REPLACE VIEW admin_job_overview AS
SELECT 
    DATE_TRUNC('day', created_at) as date,
    agent_identifier,
    status,
    COUNT(*) as job_count,
    AVG(priority) as avg_priority,
    COUNT(*) FILTER (WHERE tags && ARRAY['urgent']) as urgent_jobs
FROM jobs 
WHERE created_at >= NOW() - INTERVAL '30 days'
GROUP BY DATE_TRUNC('day', created_at), agent_identifier, status
ORDER BY date DESC, agent_identifier;

COMMENT ON VIEW admin_job_overview IS 'Admin view for job monitoring and analytics over the last 30 days';
*/

-- Create performance monitoring function
/*
CREATE OR REPLACE FUNCTION get_database_stats()
RETURNS TABLE (
    table_name TEXT,
    row_count BIGINT,
    table_size TEXT,
    index_size TEXT,
    total_size TEXT
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        schemaname||'.'||tablename as table_name,
        n_tup_ins - n_tup_del as row_count,
        pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as table_size,
        pg_size_pretty(pg_indexes_size(schemaname||'.'||tablename)) as index_size,
        pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename) + pg_indexes_size(schemaname||'.'||tablename)) as total_size
    FROM pg_stat_user_tables 
    WHERE schemaname = 'public'
    ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION get_database_stats() IS 'Get database statistics for monitoring table sizes and performance';
*/

-- Verify setup completion
DO $$
DECLARE
    table_exists boolean;
    view_exists boolean;
    policies_count integer;
BEGIN
    -- Check if jobs table exists
    SELECT EXISTS (
        SELECT FROM information_schema.tables 
        WHERE table_schema = 'public' 
        AND table_name = 'jobs'
    ) INTO table_exists;
    
    -- Check if job_stats view exists
    SELECT EXISTS (
        SELECT FROM information_schema.views 
        WHERE table_schema = 'public' 
        AND table_name = 'job_stats'
    ) INTO view_exists;
    
    -- Check if RLS policies exist
    SELECT COUNT(*) 
    FROM pg_policies 
    WHERE tablename = 'jobs' 
    INTO policies_count;
    
    -- Report status
    IF table_exists AND view_exists AND policies_count > 0 THEN
        RAISE NOTICE '✅ Database setup completed successfully!';
        RAISE NOTICE '📊 Tables: jobs (created)';
        RAISE NOTICE '📈 Views: job_stats (created)';
        RAISE NOTICE '🔒 Security: % RLS policies active', policies_count;
        RAISE NOTICE '🚀 Ready for AI Agent Template MVP v1.0!';
    ELSE
        RAISE WARNING '⚠️ Setup incomplete - please check for errors above';
        IF NOT table_exists THEN
            RAISE WARNING '❌ jobs table not found';
        END IF;
        IF NOT view_exists THEN
            RAISE WARNING '❌ job_stats view not found';
        END IF;
        IF policies_count = 0 THEN
            RAISE WARNING '❌ RLS policies not found';
        END IF;
    END IF;
END $$; 