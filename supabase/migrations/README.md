# Database Migrations for AI Agent Template

## MVP v1.0 Setup

For the MVP v1.0 release, use the **consolidated migration file** that sets up the complete database schema in one step.

### Quick Setup (Recommended)

**Use this single file for MVP v1.0:**

```sql
-- File: 000_consolidated_mvp_setup.sql
-- Run this single migration in Supabase SQL Editor
```

### How to Apply the Migration

#### Option 1: Supabase Dashboard (Easiest)

1. Go to your [Supabase Dashboard](https://app.supabase.com)
2. Select your project
3. Navigate to **SQL Editor**
4. Create a new query
5. Copy the entire contents of `000_consolidated_mvp_setup.sql`
6. Paste and run the migration
7. Verify the success message appears

#### Option 2: Supabase CLI

```bash
# Make sure you're linked to your project
supabase link --project-ref YOUR_PROJECT_REF

# Run the consolidated migration
psql -h db.YOUR_PROJECT_REF.supabase.co -p 5432 -d postgres -U postgres -f 000_consolidated_mvp_setup.sql
```

### What Gets Created

The consolidated migration creates:

#### 📊 **Tables**
- `jobs` - Main table for AI agent jobs with all required columns

#### 🚀 **Indexes**
- Performance indexes for common queries
- GIN indexes for JSON and array columns
- Composite indexes for complex queries

#### 🔒 **Security**
- Row Level Security (RLS) enabled
- User-scoped policies (users only see their own jobs)
- Proper permissions for authenticated users

#### ⚙️ **Functions & Triggers**
- Auto-update `updated_at` timestamp trigger
- Helper functions for database operations

#### 📈 **Views**
- `job_stats` - Real-time job statistics and analytics

#### 📝 **Documentation**
- Complete table and column comments
- Inline documentation for all database objects

### Verification

After running the migration, you can verify the setup:

```sql
-- Check table structure
SELECT column_name, data_type, column_default 
FROM information_schema.columns 
WHERE table_name = 'jobs' 
ORDER BY ordinal_position;

-- Check indexes
SELECT indexname, indexdef 
FROM pg_indexes 
WHERE tablename = 'jobs';

-- Check RLS policies
SELECT policyname, cmd, qual 
FROM pg_policies 
WHERE tablename = 'jobs';

-- Test statistics view
SELECT * FROM job_stats;
```

### Schema Overview

```sql
jobs (
    id              UUID PRIMARY KEY,           -- Auto-generated job ID
    user_id         UUID,                       -- User who created the job
    agent_identifier TEXT,                      -- Agent to process the job
    status          TEXT DEFAULT 'pending',    -- Job status
    priority        INTEGER DEFAULT 5,         -- Priority (0-10)
    tags            TEXT[],                     -- Organization tags
    data            JSONB,                      -- Input data
    result          JSONB,                      -- Output results
    error_message   TEXT,                       -- Error details
    created_at      TIMESTAMPTZ DEFAULT NOW(), -- Creation time
    updated_at      TIMESTAMPTZ DEFAULT NOW(), -- Last update (auto)
    completed_at    TIMESTAMPTZ,               -- Completion time
    failed_at       TIMESTAMPTZ                -- Failure time
)
```

## Legacy Migration Files

The following files are **deprecated** for new installations but kept for reference:

- `001_create_jobs_table.sql` - Initial table creation
- `002_update_jobs_table_schema.sql` - Schema updates
- `003_add_priority_and_tags_columns.sql` - Priority and tags
- `004_update_agent_identification_schema.sql` - Agent identifier

**⚠️ Do not use these files for new installations.** They are only needed if you're migrating from an existing development setup.

## Environment Variables

After running the migration, make sure your environment variables are set:

```bash
# Backend (.env)
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-anon-key
SUPABASE_SERVICE_KEY=your-service-key

# Frontend (.env.local)
VITE_SUPABASE_URL=https://your-project.supabase.co
VITE_SUPABASE_ANON_KEY=your-anon-key
```

## Troubleshooting

### Common Issues

**Permission Denied:**
```sql
-- Make sure RLS policies are created correctly
SELECT * FROM pg_policies WHERE tablename = 'jobs';
```

**Indexes Not Created:**
```sql
-- Check if all indexes exist
SELECT indexname FROM pg_indexes WHERE tablename = 'jobs';
```

**Function Errors:**
```sql
-- Verify trigger function exists
SELECT proname FROM pg_proc WHERE proname = 'update_updated_at_column';
```

### Getting Help

1. Check the [Supabase Documentation](https://supabase.com/docs)
2. Review the [project documentation](../../docs/integrations/supabase.md)
3. Check the verification queries in the migration file

## Production Considerations

Before deploying to production:

1. **Remove sample data** - Comment out the test data section
2. **Review permissions** - Adjust RLS policies as needed
3. **Monitor performance** - Check query performance with real data
4. **Backup strategy** - Set up automated backups
5. **Index optimization** - Monitor and add indexes as needed

## Success ✅

If the migration runs successfully, you should see:

```
NOTICE: AI Agent Template MVP v1.0 database setup completed successfully!
NOTICE: Tables created: jobs
NOTICE: Views created: job_stats
NOTICE: RLS enabled with user-scoped policies
NOTICE: All indexes and triggers configured
```

Your database is now ready for the AI Agent Template MVP v1.0! 🚀 