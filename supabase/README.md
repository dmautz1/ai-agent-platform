# Supabase

> **Database migrations and setup** - Quick database setup guide

## Quick Setup

```bash
# 1. Create Supabase project at supabase.com
# 2. Copy your credentials from Settings → API

# 3. Add to backend/.env:
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-anon-key
SUPABASE_SERVICE_KEY=your-service-key

# 4. Run migrations in Supabase SQL Editor:
# Copy content from migrations/001_create_jobs_table.sql
# Copy content from migrations/002_update_jobs_table_schema.sql
```

## Files in this Directory

- **`migrations/`** - Database schema migrations
- **`001_create_jobs_table.sql`** - Initial jobs table setup
- **`002_update_jobs_table_schema.sql`** - Schema updates

## Documentation

For complete database setup, schema details, and troubleshooting:

**[Supabase Integration Guide](../docs/integrations/supabase.md)** - Complete setup, migrations, security, and usage 