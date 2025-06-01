# Troubleshooting Guide

> **Common issues and solutions** - Quick fixes for the most frequent problems

## Quick Diagnostics

### System Health Check

Run these commands to quickly diagnose issues:

```bash
# Check if services are running
curl http://localhost:8000/health        # Backend health
curl http://localhost:5173               # Frontend (should show HTML)

# Check environment variables
echo $SUPABASE_URL
echo $GOOGLE_API_KEY

# Check dependencies
node --version && npm --version          # Node.js/npm
python --version && pip --version       # Python/pip
```

### Common Error Patterns

| Error Message | Quick Fix |
|---------------|-----------|
| `Connection refused` | Service not running - check terminals |
| `ModuleNotFoundError` | Missing dependencies - run `pip install -r requirements.txt` |
| `CORS error` | Check CORS configuration in backend |
| `Invalid token` | Check JWT secret configuration |
| `Supabase error` | Verify Supabase credentials |

## Environment and Setup Issues

### 1. Missing Dependencies

**Problem**: `ModuleNotFoundError` or package not found errors

**Solutions**:
```bash
# Backend dependencies
cd backend
pip install -r requirements.txt

# If using virtual environment
source .venv/bin/activate  # Linux/Mac
# or .venv\Scripts\activate  # Windows
pip install -r requirements.txt

# Frontend dependencies
cd frontend
npm install

# Clear cache if issues persist
npm cache clean --force
rm -rf node_modules package-lock.json
npm install
```

### 2. Environment Variable Issues

**Problem**: Configuration not loading properly

**Solutions**:
```bash
# Check if .env files exist
ls -la backend/.env
ls -la frontend/.env.local

# Verify format (no spaces around =)
# Correct: SUPABASE_URL=https://example.supabase.co
# Wrong:   SUPABASE_URL = https://example.supabase.co

# Check for hidden characters
cat -A backend/.env | head -5

# Test environment loading
cd backend && python -c "import os; print(os.getenv('SUPABASE_URL'))"
```

### 3. Port Conflicts

**Problem**: "Port already in use" errors

**Solutions**:
```bash
# Find what's using the port
lsof -i :8000    # Backend port
lsof -i :5173    # Frontend port

# Kill process using port
kill -9 $(lsof -t -i:8000)

# Use different ports
# Backend: python main.py --port 8001
# Frontend: npm run dev -- --port 5174
```

## Database Issues

### 1. Supabase Connection Problems

**Problem**: Cannot connect to database

**Solutions**:
```bash
# Test Supabase connection
curl "$SUPABASE_URL/rest/v1/" \
     -H "apikey: $SUPABASE_ANON_KEY"

# Check credentials in Supabase dashboard
# Settings → API → Project URL and API keys

# Verify RLS policies
# Dashboard → Authentication → Policies
```

**Common fixes**:
- Ensure Supabase URL doesn't have trailing slash
- Check that service role key has correct permissions
- Verify project is not paused (free tier limitation)

### 2. Migration Issues

**Problem**: Database schema not set up correctly

**Solutions**:
```sql
-- Check if tables exist
SELECT table_name FROM information_schema.tables 
WHERE table_schema = 'public';

-- Re-run migrations in Supabase SQL Editor
-- Copy and paste from supabase/migrations/ files

-- Check RLS is enabled
SELECT schemaname, tablename, rowsecurity 
FROM pg_tables 
WHERE tablename = 'jobs';
```

### 3. Row Level Security Problems

**Problem**: Users can't access their own data

**Solutions**:
```sql
-- Check current policies
SELECT * FROM pg_policies WHERE tablename = 'jobs';

-- Test RLS bypass (should work for service role)
SELECT * FROM jobs;

-- Enable RLS if disabled
ALTER TABLE jobs ENABLE ROW LEVEL SECURITY;

-- Recreate basic policies
DROP POLICY IF EXISTS "Users can view own jobs" ON jobs;
CREATE POLICY "Users can view own jobs" ON jobs
    FOR SELECT USING (auth.uid() = user_id);
```

## Authentication Issues

### 1. JWT Token Problems

**Problem**: "Invalid token" or "Token expired" errors

**Solutions**:
```bash
# Check JWT secret configuration
echo $JWT_SECRET
# Should be 32+ character string

# Generate new JWT secret if needed
openssl rand -base64 32

# Test token validation
curl -H "Authorization: Bearer $TOKEN" \
     http://localhost:8000/auth/me
```

### 2. User Creation Issues

**Problem**: Cannot create first user

**Solutions**:
```bash
# Use the admin creation script
cd frontend
npm run create-admin admin@example.com password123 "Admin User"

# If script fails, create manually in Supabase dashboard
# Authentication → Users → Add user

# Check email confirmation settings
# Authentication → Settings → Email confirmations
```

### 3. Login/Logout Problems

**Problem**: Authentication not working in frontend

**Solutions**:
```typescript
// Debug authentication state
const debugAuth = async () => {
  const { data: { session } } = await supabase.auth.getSession()
  console.log('Session:', session)
  
  const { data: { user } } = await supabase.auth.getUser()
  console.log('User:', user)
}

// Clear auth storage
localStorage.clear()
sessionStorage.clear()
```

## API and CORS Issues

### 1. CORS Errors

**Problem**: "Access blocked by CORS policy"

**Solutions**:
```python
# Backend: Update CORS configuration
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://localhost:3000",
        "https://your-domain.com"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### 2. API Endpoint Not Found

**Problem**: 404 errors on API calls

**Solutions**:
```bash
# Check if agent is registered
curl http://localhost:8000/agents

# Verify endpoint URL format
# Correct: http://localhost:8000/text-processing/analyze
# Wrong:   http://localhost:8000/api/text-processing/analyze

# Check agent file naming
# Should end with _agent.py
# Should be in backend/agents/ directory
```

### 3. Request/Response Issues

**Problem**: Malformed requests or unexpected responses

**Solutions**:
```bash
# Check API documentation
open http://localhost:8000/docs

# Test with curl
curl -X POST http://localhost:8000/text-processing/analyze \
     -H "Content-Type: application/json" \
     -H "Authorization: Bearer $TOKEN" \
     -d '{"text": "test"}'

# Enable debug logging
DEBUG=true python main.py
```

## Google AI Integration Issues

### 1. API Key Problems

**Problem**: Google AI requests failing

**Solutions**:
```bash
# Test API key
curl -H "Authorization: Bearer $GOOGLE_API_KEY" \
     "https://generativelanguage.googleapis.com/v1/models"

# Check quota and billing
# Visit Google AI Studio → API usage

# Test connection endpoint
curl http://localhost:8000/adk/connection-test
```

### 2. Model Access Issues

**Problem**: Specific models not available

**Solutions**:
```python
# List available models
import google.generativeai as genai
genai.configure(api_key="your-key")

for model in genai.list_models():
    print(f"Model: {model.name}")
    print(f"Methods: {model.supported_generation_methods}")
```

### 3. Content Safety Blocks

**Problem**: AI responses blocked by safety filters

**Solutions**:
```python
# Check safety ratings
if response.prompt_feedback.block_reason:
    print(f"Blocked: {response.prompt_feedback.block_reason}")
    print(f"Safety: {response.prompt_feedback.safety_ratings}")

# Adjust safety settings
safety_settings = [
    {
        "category": "HARM_CATEGORY_HARASSMENT",
        "threshold": "BLOCK_ONLY_HIGH"  # Less restrictive
    }
]
```

## Frontend Issues

### 1. Build/Development Issues

**Problem**: Frontend won't start or build

**Solutions**:
```bash
# Clear cache and reinstall
rm -rf node_modules package-lock.json
npm cache clean --force
npm install

# Check for TypeScript errors
npm run build

# Update dependencies
npm update

# Check Node.js version (should be 18+)
node --version
```

### 2. UI Component Issues

**Problem**: Components not rendering correctly

**Solutions**:
```bash
# Check CSS imports
# Ensure Tailwind CSS is properly configured

# Verify component imports
# Check for circular dependencies

# Clear browser cache
# Try incognito/private mode
```

### 3. State Management Issues

**Problem**: Application state not updating

**Solutions**:
```typescript
// Check React DevTools
// Verify context providers are wrapping components

// Debug state updates
useEffect(() => {
  console.log('State changed:', state)
}, [state])

// Check for stale closures
// Use functional updates: setState(prev => ...)
```

## Performance Issues

### 1. Slow API Responses

**Problem**: API calls taking too long

**Solutions**:
```bash
# Check backend logs for slow queries
tail -f backend/logs/app.log

# Enable query logging in Supabase
# Database → Settings → Logs

# Add database indexes for common queries
CREATE INDEX idx_jobs_user_created ON jobs(user_id, created_at DESC);

# Monitor connection pool
# Check for connection leaks
```

### 2. High Memory Usage

**Problem**: Application using too much memory

**Solutions**:
```bash
# Monitor Python memory usage
pip install memory-profiler
python -m memory_profiler main.py

# Check for memory leaks
# Monitor with htop or Activity Monitor

# Optimize database queries
# Use pagination for large result sets
```

### 3. Slow Frontend Performance

**Problem**: Frontend feels sluggish

**Solutions**:
```bash
# Build production version
npm run build
npm run preview

# Check bundle size
npm run build -- --analyze

# Optimize images and assets
# Use React.memo for expensive components
# Implement virtualization for long lists
```

## Network and Deployment Issues

### 1. Localhost Access Issues

**Problem**: Can't access services on localhost

**Solutions**:
```bash
# Check firewall settings
# Try 127.0.0.1 instead of localhost

# Check if bound to correct interface
# Backend should bind to 0.0.0.0:8000

# Try different browsers
# Check for browser extensions blocking requests
```

### 2. Production Deployment Issues

**Problem**: Works locally but fails in production

**Solutions**:
```bash
# Check environment variables in production
# Verify all required secrets are set

# Check production URLs
# Ensure HTTPS in production

# Monitor production logs
# Check for rate limiting or quota issues
```

## Getting Further Help

### Debugging Tools

1. **Browser DevTools** - Network tab for API requests
2. **React DevTools** - Component state and props
3. **Supabase Dashboard** - Database logs and monitoring
4. **Backend Logs** - Detailed error information

### Log Locations

```bash
# Backend logs
tail -f backend/logs/app.log

# Frontend console
# Open browser DevTools → Console

# Supabase logs
# Dashboard → Logs → API/Database
```

### Community Support

- **GitHub Issues** - Report bugs and get help
- **Documentation** - Check other docs sections
- **API Docs** - Interactive documentation at `/docs`

### Before Reporting Issues

1. Check this troubleshooting guide
2. Search existing GitHub issues
3. Provide error messages and logs
4. Include system information and versions
5. List steps to reproduce the problem

---

**Still having issues?** Check the specific integration guides:
- **[Environment Setup](environment-setup.md)** - Detailed setup instructions
- **[Supabase Integration](../integrations/supabase.md)** - Database issues
- **[Google AI Integration](../integrations/google-ai.md)** - AI service problems
- **[Authentication](../integrations/authentication.md)** - User management issues 