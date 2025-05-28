# Supabase Database Setup

This directory contains database migrations and setup files for the AI Agent Template project.

## Database Schema

The main table is `jobs` which stores information about AI agent tasks:

### Jobs Table Schema

| Column | Type | Description |
|--------|------|-------------|
| `id` | UUID | Primary key, auto-generated |
| `status` | TEXT | Job status: 'pending', 'running', 'completed', 'failed' |
| `data` | JSONB | Input data and parameters for the job |
| `result` | TEXT | Job execution result or output |
| `error_message` | TEXT | Error message if job failed |
| `created_at` | TIMESTAMP | When the job was created |
| `updated_at` | TIMESTAMP | When the job was last updated (auto-updated) |

### Indexes

- `idx_jobs_status` - Fast filtering by status
- `idx_jobs_created_at` - Ordering by creation date
- `idx_jobs_updated_at` - Ordering by update date
- `idx_jobs_status_created` - Combined status and date filtering
- `idx_jobs_data_gin` - GIN index for JSON queries on data column

### Views

- `job_stats` - Provides summary statistics for jobs by status

## Setup Instructions

### 1. Create Supabase Project

1. Go to [supabase.com](https://supabase.com)
2. Create a new project
3. Note your project URL and API keys

### 2. Run Migration

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

1. Open your Supabase dashboard
2. Go to SQL Editor
3. Copy and paste the contents of `migrations/001_create_jobs_table.sql`
4. Execute the SQL

### 3. Configure Environment Variables

Copy the example environment file and update with your Supabase credentials:

```bash
cp backend/.env.example backend/.env
```

Update these values in `backend/.env`:
- `SUPABASE_URL` - Your project URL
- `SUPABASE_KEY` - Your anon/public key
- `SUPABASE_SERVICE_KEY` - Your service role key (for server-side operations)

### 4. Test Connection

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

## Security Considerations

- Never commit `.env` files to version control
- Use service role key only on the server side
- Configure Row Level Security (RLS) policies as needed
- Regularly rotate API keys

## Troubleshooting

### Common Issues

1. **Connection Error**: Verify URL and keys in `.env` file
2. **Permission Denied**: Check RLS policies and user permissions
3. **Migration Failed**: Ensure you have admin privileges on the database

### Useful Queries

```sql
-- Check table structure
\d jobs

-- View recent jobs
SELECT * FROM jobs ORDER BY created_at DESC LIMIT 10;

-- Job statistics
SELECT * FROM job_stats;

-- Clear all jobs (development only)
TRUNCATE jobs;
``` 