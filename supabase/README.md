# Supabase Database Setup

> **🚀 MVP v1.0 Ready** - One-click database setup for production

## Quick Setup for MVP v1.0

**Use the consolidated migration for instant setup:**

```bash
# 1. Create Supabase project at supabase.com
# 2. Copy your credentials from Settings → API

# 3. Add to backend/.env:
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-anon-key
SUPABASE_SERVICE_KEY=your-service-key

# 4. Run the consolidated migration:
# Copy content from migrations/000_consolidated_mvp_setup.sql
# Paste and run in Supabase SQL Editor
```

## Migration Files

### 🎯 **For New Installations (MVP v1.0)**
- **`migrations/000_consolidated_mvp_setup.sql`** - Complete database setup in one file
- **`migrations/README.md`** - Detailed setup instructions and troubleshooting

### 📚 **Legacy Files (Reference Only)**
- `migrations/001_create_jobs_table.sql` - Initial jobs table setup  
- `migrations/002_update_jobs_table_schema.sql` - Schema updates
- `migrations/003_add_priority_and_tags_columns.sql` - Priority and tags support
- `migrations/004_update_agent_identification_schema.sql` - Agent identifier updates

**⚠️ New installations should only use `000_consolidated_mvp_setup.sql`**

## What Gets Created

The consolidated migration creates everything needed for the MVP:

- **🗃️ Tables**: `jobs` with all required columns
- **📊 Indexes**: Optimized for performance and JSON queries  
- **🔒 Security**: Row Level Security with user-scoped policies
- **⚙️ Functions**: Auto-update triggers and utilities
- **📈 Views**: `job_stats` for real-time analytics
- **📝 Documentation**: Complete inline documentation

## Complete Documentation

For detailed setup, configuration, and troubleshooting:

**[📖 Complete Supabase Integration Guide](../docs/integrations/supabase.md)**

## Verification

After running the migration, verify success:

```sql
-- Quick verification
SELECT 'Database setup successful!' as status 
WHERE EXISTS (SELECT 1 FROM jobs LIMIT 1 EXCEPT SELECT 1 FROM jobs);

-- Detailed verification  
SELECT * FROM job_stats;
```

## Success Message

If setup completed successfully, you'll see:

```
✅ AI Agent Template MVP v1.0 database setup completed successfully!
📊 Tables created: jobs
📈 Views created: job_stats  
🔒 RLS enabled with user-scoped policies
⚙️ All indexes and triggers configured
```

Ready to build! 🚀 