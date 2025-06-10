# Supabase Database Integration

> **Complete database setup and management** - From initial setup to advanced features

## Overview

The AI Agent Template uses [Supabase](https://supabase.com) as its primary database, providing:

- **PostgreSQL Database** - Robust relational database
- **Real-time Subscriptions** - Live data updates
- **Built-in Authentication** - User management out of the box
- **Row Level Security (RLS)** - Secure data access
- **REST API** - Auto-generated database API

## Quick Setup

### 1. Create Supabase Project

1. Go to [supabase.com](https://supabase.com) and sign up
2. Click **"New Project"**
3. Choose organization and enter project details:
   - **Name**: `ai-agent-template`
   - **Database Password**: Generate strong password
   - **Region**: Choose closest to your users
4. Wait 2-3 minutes for project creation

### 2. Get Database Credentials

From your Supabase dashboard:

1. Go to **Settings** → **API**
2. Copy these values:

```bash
# Project URL
SUPABASE_URL=https://your-project-id.supabase.co

# Anonymous (public) key - safe for frontend
SUPABASE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...

# Service role key - backend only, keep secret!
SUPABASE_SERVICE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

### 3. Run Database Migrations

Set up the required database schema using one of these methods:

#### Option A: Using Supabase CLI (Recommended)

```bash
# Install Supabase CLI
npm install -g @supabase/cli

# Login to Supabase
supabase login

# Initialize project (if not already done)
supabase init

# Link to your project
supabase link --project-ref YOUR_PROJECT_REF

# Run migration
supabase db push
```

#### Option B: Manual SQL Execution

1. In Supabase dashboard, go to **SQL Editor**
2. Copy and run the migration files in order:

**Migration 1: Create Jobs Table**
```sql
-- Copy content from supabase/migrations/001_create_jobs_table.sql
-- Run in Supabase SQL Editor
```

**Migration 2: Update Jobs Schema**  
```sql
-- Copy content from supabase/migrations/002_update_jobs_table_schema.sql
-- Run in Supabase SQL Editor
```

### 4. Configure Environment

Add credentials to your environment files:

**Backend** (`backend/.env`):
```bash
SUPABASE_URL=your-project-url
SUPABASE_KEY=your-anon-key
SUPABASE_SERVICE_KEY=your-service-key
```

**Frontend** (`frontend/.env.local`):
```bash
VITE_SUPABASE_URL=your-project-url
VITE_SUPABASE_ANON_KEY=your-anon-key
```

### 5. Test Connection

```bash
cd backend
python -c "
import os
from dotenv import load_dotenv
load_dotenv()
from database import DatabaseClient
client = DatabaseClient()
print('Database connection successful!')
"
```

## Database Schema

### Core Tables

#### Jobs Table
```sql
CREATE TABLE jobs (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE,
    agent_identifier TEXT NOT NULL,
    status job_status NOT NULL DEFAULT 'pending',
    job_data JSONB,
    result JSONB,
    error_message TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    started_at TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE
);

-- Job status enum
CREATE TYPE job_status AS ENUM (
    'pending',
    'running', 
    'completed',
    'failed',
    'cancelled'
);
```

**Schema Details:**

| Column | Type | Description |
|--------|------|-------------|
| `id` | UUID | Primary key, auto-generated |
| `user_id` | UUID | References auth.users, user who created the job |
| `agent_identifier` | TEXT | Identifier of agent processing the job |
| `status` | job_status | Job status: 'pending', 'running', 'completed', 'failed', 'cancelled' |
| `job_data` | JSONB | Input data and parameters for the job |
| `result` | JSONB | Job execution result or output |
| `error_message` | TEXT | Error message if job failed |
| `created_at` | TIMESTAMP | When the job was created |
| `updated_at` | TIMESTAMP | When the job was last updated (auto-updated) |
| `started_at` | TIMESTAMP | When job processing began |
| `completed_at` | TIMESTAMP | When job processing finished |

#### Built-in Auth Tables
Supabase provides these automatically:
```sql
-- User authentication
auth.users (
    id UUID PRIMARY KEY,
    email TEXT UNIQUE,
    encrypted_password TEXT,
    email_confirmed_at TIMESTAMP,
    created_at TIMESTAMP,
    updated_at TIMESTAMP,
    -- ... other auth fields
)
```

### Indexes and Performance

```sql
-- Performance indexes
CREATE INDEX idx_jobs_user_id ON jobs(user_id);
CREATE INDEX idx_jobs_status ON jobs(status);
CREATE INDEX idx_jobs_created_at ON jobs(created_at DESC);
CREATE INDEX idx_jobs_agent_identifier ON jobs(agent_identifier);
CREATE INDEX idx_jobs_updated_at ON jobs(updated_at DESC);

-- Composite indexes for common queries
CREATE INDEX idx_jobs_user_status ON jobs(user_id, status);
CREATE INDEX idx_jobs_user_created ON jobs(user_id, created_at DESC);
CREATE INDEX idx_jobs_status_created ON jobs(status, created_at DESC);

-- GIN index for JSON queries on job_data column
CREATE INDEX idx_jobs_data_gin ON jobs USING GIN (job_data);
```

### Database Views

```sql
-- Job statistics view
CREATE VIEW job_stats AS
SELECT 
    COUNT(*) as total_jobs,
    COUNT(*) FILTER (WHERE status = 'pending') as pending_jobs,
    COUNT(*) FILTER (WHERE status = 'running') as running_jobs,
    COUNT(*) FILTER (WHERE status = 'completed') as completed_jobs,
    COUNT(*) FILTER (WHERE status = 'failed') as failed_jobs,
    COUNT(*) FILTER (WHERE status = 'cancelled') as cancelled_jobs,
    AVG(EXTRACT(EPOCH FROM (completed_at - started_at))) FILTER (WHERE status = 'completed') as avg_processing_time
FROM jobs;
```

## Security Configuration

### Row Level Security (RLS)

Enable RLS to ensure users can only access their own data:

```sql
-- Enable RLS on jobs table
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
```

### Service Role Access

For backend operations requiring elevated privileges:

```sql
-- Policy: Service role can access all jobs
CREATE POLICY "Service role full access" ON jobs
    FOR ALL USING (auth.role() = 'service_role');
```

## Backend Integration

### Database Client Setup

The backend uses the Supabase client for database operations:

```python
# backend/database.py
from supabase import create_client, Client
import os

def get_supabase_client() -> Client:
    """Get authenticated Supabase client"""
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_SERVICE_KEY")  # Service role for backend
    
    if not url or not key:
        raise ValueError("Supabase credentials not configured")
    
    return create_client(url, key)

# Usage in application
supabase = get_supabase_client()
```

### Common Database Operations

#### Creating Jobs
```python
async def create_job(user_id: str, agent_identifier: str, job_data: dict) -> dict:
    """Create a new job in the database"""
    result = supabase.table("jobs").insert({
        "user_id": user_id,
        "agent_identifier": agent_identifier,
        "status": "pending",
        "job_data": job_data,
        "created_at": "NOW()"
    }).execute()
    
    return result.data[0]
```

#### Updating Job Status
```python
async def update_job_status(job_id: str, status: str, result: dict = None):
    """Update job status and result"""
    update_data = {
        "status": status,
        "updated_at": "NOW()"
    }
    
    if status == "running":
        update_data["started_at"] = "NOW()"
    elif status in ["completed", "failed"]:
        update_data["completed_at"] = "NOW()"
        if result:
            update_data["result"] = result
    
    supabase.table("jobs").update(update_data).eq("id", job_id).execute()
```

#### Querying Jobs
```python
async def get_user_jobs(user_id: str, limit: int = 50) -> list:
    """Get user's jobs with pagination"""
    result = supabase.table("jobs")\
        .select("*")\
        .eq("user_id", user_id)\
        .order("created_at", desc=True)\
        .limit(limit)\
        .execute()
    
    return result.data
```

## Frontend Integration

### Supabase Client Setup

```typescript
// frontend/src/lib/supabase.ts
import { createClient } from '@supabase/supabase-js'

const supabaseUrl = import.meta.env.VITE_SUPABASE_URL
const supabaseAnonKey = import.meta.env.VITE_SUPABASE_ANON_KEY

export const supabase = createClient(supabaseUrl, supabaseAnonKey)
```

### Authentication Integration

```typescript
// Sign in
const { data, error } = await supabase.auth.signInWithPassword({
  email: 'user@example.com',
  password: 'password'
})

// Get current user
const { data: { user } } = await supabase.auth.getUser()

// Sign out
await supabase.auth.signOut()
```

### Real-time Subscriptions

```typescript
// Subscribe to job updates
const subscription = supabase
  .channel('jobs')
  .on('postgres_changes', 
    { 
      event: '*', 
      schema: 'public', 
      table: 'jobs',
      filter: `user_id=eq.${userId}`
    }, 
    (payload) => {
      console.log('Job updated:', payload)
      // Update UI with new job data
    }
  )
  .subscribe()

// Cleanup
subscription.unsubscribe()
```

## Advanced Features

### Database Functions

Create reusable database functions for complex operations:

```sql
-- Function to get job statistics
CREATE OR REPLACE FUNCTION get_job_stats(p_user_id UUID)
RETURNS JSON AS $$
BEGIN
    RETURN (
        SELECT json_build_object(
            'total', COUNT(*),
            'pending', COUNT(*) FILTER (WHERE status = 'pending'),
            'running', COUNT(*) FILTER (WHERE status = 'running'),
            'completed', COUNT(*) FILTER (WHERE status = 'completed'),
            'failed', COUNT(*) FILTER (WHERE status = 'failed')
        )
        FROM jobs 
        WHERE user_id = p_user_id
    );
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;
```

### Backup and Recovery

Supabase provides automatic backups, but you can also:

1. **Manual Exports**: Use the Supabase dashboard
2. **pg_dump**: Connect directly to PostgreSQL
3. **API Exports**: Use Supabase REST API

```bash
# Export data via API
curl -X GET "https://your-project.supabase.co/rest/v1/jobs" \
     -H "apikey: your-anon-key" \
     -H "Authorization: Bearer your-jwt-token" > jobs_backup.json
```

### Performance Monitoring

Monitor database performance through:

1. **Supabase Dashboard** - Query performance insights
2. **Application Logs** - Log slow queries
3. **Custom Metrics** - Track query timing

```python
# Log slow queries
import time
import logging

def log_query_performance(func):
    def wrapper(*args, **kwargs):
        start_time = time.time()
        result = func(*args, **kwargs)
        execution_time = time.time() - start_time
        
        if execution_time > 1.0:  # Log queries taking > 1 second
            logging.warning(f"Slow query: {func.__name__} took {execution_time:.2f}s")
        
        return result
    return wrapper
```

## Troubleshooting

### Common Issues

**Connection Errors:**
```bash
# Check environment variables
echo $SUPABASE_URL
echo $SUPABASE_KEY

# Verify credentials in Supabase dashboard
# Settings → API → Project URL and API keys
```

**RLS Policy Issues:**
```sql
-- Check if RLS is enabled
SELECT schemaname, tablename, rowsecurity 
FROM pg_tables 
WHERE tablename = 'jobs';

-- View policies
SELECT * FROM pg_policies WHERE tablename = 'jobs';

-- Test policy with specific user
SELECT * FROM jobs WHERE auth.uid() = 'user-uuid';
```

**Performance Issues:**
```sql
-- Check query performance
EXPLAIN ANALYZE SELECT * FROM jobs WHERE user_id = 'uuid';

-- Check index usage
SELECT * FROM pg_stat_user_indexes WHERE relname = 'jobs';

-- View recent jobs
SELECT * FROM jobs ORDER BY created_at DESC LIMIT 10;

-- Get job statistics
SELECT * FROM job_stats;
```

**Migration Issues:**
```bash
# Clear all jobs (development only)
TRUNCATE jobs CASCADE;

# Reset sequences
SELECT setval('jobs_id_seq', 1, false);

# Check table structure
\d jobs
```

### Migration Best Practices

1. **Test migrations locally** before production
2. **Backup before major changes**
3. **Use transactions** for multi-step migrations
4. **Document schema changes**

```sql
-- Example migration with transaction
BEGIN;

-- Add new column
ALTER TABLE jobs ADD COLUMN priority INTEGER DEFAULT 0;

-- Create index
CREATE INDEX idx_jobs_priority ON jobs(priority);

-- Update existing data
UPDATE jobs SET priority = 1 WHERE status = 'pending';

COMMIT;
```

### Security Considerations

1. **Never commit `.env` files** to version control
2. **Use service role key only** on the server side
3. **Configure Row Level Security (RLS)** policies as needed
4. **Regularly rotate API keys**
5. **Monitor access patterns** for suspicious activity

### Useful Database Queries

```sql
-- Check table structure
\d jobs

-- View recent jobs
SELECT * FROM jobs ORDER BY created_at DESC LIMIT 10;

-- Job statistics
SELECT * FROM job_stats;

-- Find long-running jobs
SELECT id, agent_identifier, started_at, 
       NOW() - started_at as duration
FROM jobs 
WHERE status = 'running' 
AND started_at < NOW() - INTERVAL '1 hour';

-- Clear all jobs (development only)
TRUNCATE jobs;
```

---

**Next Steps:**
- **[Authentication Setup](authentication.md)** - User management integration
- **[Google AI Integration](google-ai.md)** - AI service setup
- **[API Reference](../development/api-reference.md)** - Database API endpoints 