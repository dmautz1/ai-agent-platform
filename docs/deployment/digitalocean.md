# DigitalOcean Deployment

> **Deploy to DigitalOcean App Platform** - Production deployment in under 30 minutes

## Overview

DigitalOcean App Platform provides a managed deployment solution perfect for the AI Agent Template:

- **Automatic builds** from GitHub
- **Managed databases** via Supabase
- **SSL certificates** included
- **Auto-scaling** based on demand
- **Cost-effective** starting at ~$12/month

## Quick Deployment

### Prerequisites

1. **GitHub repository** with your code
2. **DigitalOcean account** ([signup here](https://cloud.digitalocean.com))
3. **Supabase project** configured and running
4. **Google AI API key** ready

### Step 1: Prepare Repository

Ensure your repository has the deployment configuration:

```bash
# Check if deployment config exists
ls -la .do/app.yaml
```

If missing, create `.do/app.yaml`:

```yaml
name: ai-agent-template
services:
- name: backend
  source_dir: /backend
  github:
    repo: your-username/your-repo
    branch: main
  run_command: python main.py
  environment_slug: python
  instance_count: 1
  instance_size_slug: basic-xxs
  routes:
  - path: /api
  envs:
  - key: ENVIRONMENT
    value: production
  - key: HOST
    value: 0.0.0.0
  - key: PORT
    value: "8080"

- name: frontend
  source_dir: /frontend
  github:
    repo: your-username/your-repo
    branch: main
  build_command: npm run build
  environment_slug: node-js
  instance_count: 1
  instance_size_slug: basic-xxs
  routes:
  - path: /
  envs:
  - key: NODE_ENV
    value: production
```

### Step 2: Create DigitalOcean App

1. **Login to DigitalOcean** console
2. Go to **Apps** → **Create App**
3. Connect your **GitHub repository**
4. Choose **branch** (usually `main`)
5. **Auto-detect** will find your app.yaml configuration

### Step 3: Configure Environment Variables

In the DigitalOcean Apps console, add these environment variables:

#### Backend Environment Variables

| Variable | Value | Description |
|----------|-------|-------------|
| `SUPABASE_URL` | `https://xxx.supabase.co` | Your Supabase project URL |
| `SUPABASE_KEY` | `eyJhbG...` | Supabase anon key |
| `SUPABASE_SERVICE_KEY` | `eyJhbG...` | Supabase service role key |
| `GOOGLE_API_KEY` | `AIzaSy...` | Google AI Studio API key |
| `JWT_SECRET` | `your-32-char-secret` | JWT signing secret |
| `ENVIRONMENT` | `production` | Application environment |
| `DEBUG` | `false` | Disable debug mode |

#### Frontend Environment Variables

| Variable | Value | Description |
|----------|-------|-------------|
| `VITE_SUPABASE_URL` | `https://xxx.supabase.co` | Supabase URL for frontend |
| `VITE_SUPABASE_ANON_KEY` | `eyJhbG...` | Supabase anon key |
| `VITE_API_URL` | `https://your-app-backend.ondigitalocean.app` | Backend API URL |

### Step 4: Deploy

1. **Review configuration** in the DigitalOcean console
2. Click **Create Resources**
3. Wait for deployment (5-10 minutes)
4. **Verify deployment** at the provided URLs

## Post-Deployment Setup

### Update CORS Configuration

Update your backend to allow your frontend domain:

```python
# backend/main.py
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://your-app-frontend.ondigitalocean.app",
        "http://localhost:5173"  # Keep for local development
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### Create Production Admin User

```bash
# SSH into your backend app or use DigitalOcean console
curl -X POST https://your-app-backend.ondigitalocean.app/auth/create-admin \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@yourdomain.com","password":"secure-password","name":"Admin"}'
```

### Configure Custom Domain (Optional)

1. In DigitalOcean Apps console, go to **Settings** → **Domains**
2. Add your custom domain
3. Update DNS records as instructed
4. SSL certificate will be automatically provisioned

## Production Optimization

### Performance Tuning

1. **Scale backend instances** based on usage:
   ```yaml
   # .do/app.yaml
   - name: backend
     instance_count: 2  # Scale horizontally
     instance_size_slug: basic-xs  # Scale vertically
   ```

2. **Enable caching** in your backend:
   ```python
   from fastapi_cache import FastAPICache
   from fastapi_cache.backends.redis import RedisBackend
   
   # Add Redis caching
   FastAPICache.init(RedisBackend(), prefix="fastapi-cache")
   ```

3. **Optimize frontend build**:
   ```bash
   # Build with optimizations
   npm run build -- --minify --sourcemap=false
   ```

### Monitoring and Logging

1. **Enable monitoring** in DigitalOcean console:
   - Go to **Insights** tab
   - Monitor CPU, memory, and request metrics
   - Set up alerts for high resource usage

2. **Structured logging** is automatically configured:
   ```python
   # Backend logs are collected automatically
   logger.info("Job completed", extra={"job_id": job.id, "duration": duration})
   ```

3. **View logs** in DigitalOcean console:
   - **Runtime logs** - Application output
   - **Build logs** - Deployment process
   - **Access logs** - HTTP requests

### Security Hardening

1. **Rotate secrets regularly**:
   ```bash
   # Generate new JWT secret
   openssl rand -base64 32
   # Update in DigitalOcean environment variables
   ```

2. **Update Supabase RLS policies** for production:
   ```sql
   -- Ensure strict user isolation
   CREATE POLICY "Production user isolation" ON jobs
     FOR ALL USING (auth.uid() = user_id);
   ```

3. **Configure rate limiting**:
   ```python
   from slowapi import Limiter, _rate_limit_exceeded_handler
   from slowapi.util import get_remote_address
   
   limiter = Limiter(key_func=get_remote_address)
   app.add_exception_handler(429, _rate_limit_exceeded_handler)
   
   @app.post("/api/agents/process")
   @limiter.limit("5/minute")
   async def process_job(request: Request):
       # Rate limited endpoint
   ```

## Cost Optimization

### Instance Sizing

Start small and scale based on actual usage:

| Size | vCPU | Memory | Price/month | Best For |
|------|------|--------|-------------|----------|
| `basic-xxs` | 0.5 | 0.5GB | $5 | Development, low traffic |
| `basic-xs` | 1 | 1GB | $12 | Production start |
| `basic-s` | 1 | 2GB | $25 | Higher traffic |
| `basic-m` | 2 | 4GB | $50 | High performance |

### Database Costs

Using Supabase (external to DigitalOcean):

- **Free tier**: 500MB storage, 50MB database size
- **Pro tier**: $25/month for production features
- **Pay-as-you-grow**: Additional storage and transfer

### Total Monthly Cost Estimate

| Component | Cost | Notes |
|-----------|------|-------|
| Frontend (basic-xxs) | $5 | Static site hosting |
| Backend (basic-xs) | $12 | API server |
| Database (Supabase Pro) | $25 | Production database |
| **Total** | **$42/month** | For moderate usage |

## Troubleshooting

### Common Deployment Issues

**Build failures:**
```bash
# Check build logs in DigitalOcean console
# Common fixes:
npm install --production  # Frontend dependency issues
pip install -r requirements.txt  # Backend dependency issues
```

**Environment variable issues:**
```bash
# Verify all required variables are set
# Check for typos in variable names
# Ensure secrets are properly escaped
```

**Database connection errors:**
```bash
# Verify Supabase credentials
# Check if Supabase project is active
# Confirm RLS policies are correct
```

### Health Checks

Set up health check endpoints:

```python
@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow(),
        "version": "1.0.0"
    }

@app.get("/health/deep")
async def deep_health_check():
    # Check database connection
    # Check external APIs
    # Return detailed status
```

### Rollback Strategy

If deployment fails:

1. **Use DigitalOcean console** to rollback to previous deployment
2. **Check logs** for error details
3. **Fix issues locally** and redeploy
4. **Keep staging environment** for testing changes

## Continuous Deployment

### GitHub Actions Integration

Create `.github/workflows/deploy.yml`:

```yaml
name: Deploy to DigitalOcean
on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Deploy to DigitalOcean
        uses: digitalocean/app_action@v1
        with:
          app_name: ai-agent-template
          token: ${{ secrets.DIGITALOCEAN_ACCESS_TOKEN }}
```

### Automated Testing

Run tests before deployment:

```yaml
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Run tests
        run: |
          npm test
          cd backend && python -m pytest
```

## Scaling Strategies

### Horizontal Scaling

```yaml
# .do/app.yaml - Multiple instances
- name: backend
  instance_count: 3  # Auto-load balanced
  autoscaling:
    min_instance_count: 2
    max_instance_count: 5
    metrics:
      cpu:
        percent: 80
```

### Database Scaling

1. **Connection pooling** - Built into Supabase
2. **Read replicas** - For read-heavy workloads
3. **Caching layer** - Redis for frequently accessed data

---

**Next Steps:**
- **[Deployment Guide](deployment-guide.md)** - General deployment concepts
- **[Configuration Reference](../configuration/README.md)** - Production configuration
- **[Troubleshooting](../getting-started/troubleshooting.md)** - Deployment issues 