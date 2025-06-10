# DigitalOcean App Platform Deployment Guide

> **Complete Guide to Deploying AI Agent Platform** - From setup to production

This guide walks you through deploying the AI Agent Platform to DigitalOcean App Platform using the included configuration file.

## Quick Start with Deployment Script

**⚡ For automated deployment, use our unified deployment script:**

```bash
# 1. Set up environment variables
cp .env.example .env
# Edit .env with your credentials

# 2. Install and authenticate doctl
brew install doctl  # or appropriate installation for your OS
doctl auth init

# 3. Deploy to production
./scripts/deploy.sh deploy --env production --domain yourdomain.com

# 4. Check status
./scripts/deploy.sh status
```

For detailed script usage, see: [scripts/README.md](scripts/README.md)

---

## Manual Deployment Guide

For manual deployment or advanced configuration, follow the detailed steps below.

## Table of Contents

- [Prerequisites](#prerequisites)
- [Pre-Deployment Setup](#pre-deployment-setup)
- [Deployment Configuration](#deployment-configuration)
- [Environment Variables Setup](#environment-variables-setup)
- [Deployment Process](#deployment-process)
- [Post-Deployment Configuration](#post-deployment-configuration)
- [Monitoring and Maintenance](#monitoring-and-maintenance)
- [Troubleshooting](#troubleshooting)
- [Cost Optimization](#cost-optimization)

## Prerequisites

### Required Accounts
- **DigitalOcean Account** with App Platform access
- **GitHub Account** with your repository
- **Supabase Account** with your database project
- **Google AI Studio Account** (or Google Cloud) for AI functionality

### Required Knowledge
- Basic understanding of environment variables
- Familiarity with GitHub repositories
- Basic knowledge of domain management (if using custom domain)

### Cost Estimate
- **Backend Service**: ~$5/month (Basic plan)
- **Frontend Service**: ~$5/month (Basic plan)
- **Worker Service**: ~$5/month (Basic plan)
- **Domain/SSL**: Free with DigitalOcean
- **Total**: ~$15/month for production-ready deployment

## Pre-Deployment Setup

### 1. Prepare Your Repository

1. **Fork or Clone the Repository**:
   ```bash
   git clone https://github.com/your-username/ai-agent-platform.git
   cd ai-agent-platform
   ```

2. **Push to Your GitHub Repository**:
   ```bash
   git remote set-url origin https://github.com/your-username/ai-agent-framwwork.git
   git push -u origin main
   ```

### 2. Set Up Supabase Database

1. **Create Supabase Project**:
   - Go to [supabase.com](https://supabase.com)
   - Create a new project
   - Wait for project initialization (~2 minutes)

2. **Run Database Migrations**:
   - Go to **SQL Editor** in Supabase dashboard
   - Copy content from `supabase/migrations/001_create_jobs_table.sql`
   - Run the SQL to create tables

3. **Get Database Credentials**:
   - Go to **Settings** → **API**
   - Copy **Project URL**
   - Copy **anon public key**
   - Copy **service_role key**

### 3. Set Up Google AI

Choose one option:

#### Option A: Google AI Studio (Recommended)
1. Visit [Google AI Studio](https://aistudio.google.com)
2. Create an API key
3. Copy the API key

#### Option B: Google Cloud Vertex AI
1. Create Google Cloud project
2. Enable Vertex AI API
3. Set up service account
4. Download credentials

### 4. Prepare Domain (Optional)

If using a custom domain:
1. Register domain or use existing domain
2. Update DNS to point to DigitalOcean (done after deployment)

## Deployment Configuration

The deployment uses the provided `.do/app.yaml` configuration file. Update the following placeholders:

### 1. Update Repository Information

Replace in `.do/app.yaml`:
```yaml
github:
  repo: your-github-username/ai-agent-platform  # Replace with your repo
  branch: main
```

### 2. Update Domain Configuration

Replace in `.do/app.yaml`:
```yaml
domains:
- domain: your-domain.com  # Replace with your domain
  type: PRIMARY
  wildcard: false
  zone: your-domain.com    # Replace with your domain
```

If you don't have a domain, remove the `domains` section entirely to use the default DigitalOcean URL.

## Environment Variables Setup

### Backend Environment Variables

Update these in the DigitalOcean App Platform dashboard or in `.do/app.yaml`:

#### Required Variables
```yaml
# Database (Replace with your Supabase credentials)
- key: SUPABASE_URL
  value: "https://your-project-id.supabase.co"
  type: SECRET
- key: SUPABASE_KEY
  value: "your-supabase-anon-key"
  type: SECRET
- key: SUPABASE_SERVICE_KEY
  value: "your-supabase-service-key"
  type: SECRET

# Authentication (Generate a strong secret)
- key: JWT_SECRET
  value: "your-32-character-random-string"
  type: SECRET

# Google AI (Your API key)
- key: GOOGLE_API_KEY
  value: "your-google-ai-api-key"
  type: SECRET
```

#### Optional Variables (can keep defaults)
```yaml
# Application Settings
- key: APP_NAME
  value: "AI Agent Platform API"
- key: ENVIRONMENT
  value: "production"
- key: LOG_LEVEL
  value: "INFO"

# Performance Settings
- key: MAX_CONCURRENT_JOBS
  value: "10"
- key: JOB_TIMEOUT
  value: "3600"
```

### Frontend Environment Variables

```yaml
# API Configuration
- key: VITE_API_BASE_URL
  value: "https://your-domain.com"  # Or your DigitalOcean app URL

# Database (Same as backend)
- key: VITE_SUPABASE_URL
  value: "https://your-project-id.supabase.co"
  type: SECRET
- key: VITE_SUPABASE_ANON_KEY
  value: "your-supabase-anon-key"
  type: SECRET
```

## Deployment Process

### Method 1: Using DigitalOcean Dashboard

1. **Create App**:
   - Go to [DigitalOcean Apps](https://cloud.digitalocean.com/apps)
   - Click "Create App"
   - Choose "GitHub" as source

2. **Connect Repository**:
   - Authorize DigitalOcean to access your GitHub
   - Select your repository: `your-username/ai-agent-platform`
   - Choose branch: `main`

3. **Upload Configuration**:
   - In the app creation flow, choose "Use existing app spec"
   - Upload the `.do/app.yaml` file
   - Review the configuration

4. **Configure Environment Variables**:
   - Go to each service (backend, frontend, worker)
   - Add environment variables as specified above
   - Mark sensitive variables as "SECRET"

5. **Deploy**:
   - Click "Create Resources"
   - Wait for deployment (~5-10 minutes)

### Method 2: Using doctl CLI

1. **Install doctl**:
   ```bash
   # macOS
   brew install doctl
   
   # Linux
   snap install doctl
   
   # Or download from: https://github.com/digitalocean/doctl/releases
   ```

2. **Authenticate**:
   ```bash
   doctl auth init
   ```

3. **Deploy App**:
   ```bash
   doctl apps create --spec .do/app.yaml
   ```

4. **Update Environment Variables**:
   ```bash
   doctl apps update YOUR_APP_ID --spec .do/app.yaml
   ```

## Post-Deployment Configuration

### 1. Verify Deployment

1. **Check App Status**:
   - Go to DigitalOcean Apps dashboard
   - Verify all services are "Running"
   - Check build and runtime logs for errors

2. **Test Health Endpoints**:
   ```bash
   # Test backend health
   curl https://your-app-url.ondigitalocean.app/health
   
   # Test frontend
   curl https://your-app-url.ondigitalocean.app/
   ```

### 2. Set Up Domain (If Using Custom Domain)

1. **Update DNS Records**:
   ```
   Type: CNAME
   Name: @ (or www)
   Value: your-app-url.ondigitalocean.app
   ```

2. **Configure SSL**:
   - DigitalOcean automatically provisions SSL certificates
   - Verify HTTPS is working

### 3. Create Initial User

Run the admin user creation script:
```bash
# Locally, pointing to production API
cd frontend
VITE_API_BASE_URL=https://your-app-url.ondigitalocean.app npm run create-admin admin@yourdomain.com secure-password "Admin User"
```

### 4. Configure CORS

Update CORS origins in the backend environment variables:
```yaml
- key: ALLOWED_ORIGINS
  value: "https://your-domain.com,https://www.your-domain.com,https://your-app-url.ondigitalocean.app"
```

## Monitoring and Maintenance

### 1. Monitor Application Health

1. **DigitalOcean Monitoring**:
   - Check CPU, memory, and request metrics
   - Set up alerts for high resource usage
   - Monitor deployment status

2. **Application Logs**:
   ```bash
   # View backend logs
   doctl apps logs YOUR_APP_ID --component backend --follow
   
   # View frontend logs
   doctl apps logs YOUR_APP_ID --component frontend --follow
   ```

3. **Health Check Endpoints**:
   - Backend: `https://your-app/health`
   - Pipeline status: `https://your-app/pipeline/status`
   - Agent status: `https://your-app/agents`

### 2. Database Maintenance

1. **Monitor Supabase**:
   - Check database performance in Supabase dashboard
   - Monitor API usage and quotas
   - Set up database backups

2. **Clean Up Jobs**:
   - The system automatically cleans up completed jobs after 24 hours
   - Adjust `CLEANUP_COMPLETED_JOBS_AFTER` environment variable if needed

### 3. Performance Optimization

1. **Scale Services**:
   ```yaml
   # In .do/app.yaml, increase instance count
   instance_count: 2  # For backend
   instance_size_slug: basic-xs  # Upgrade size if needed
   ```

2. **Optimize Workers**:
   ```yaml
   # Adjust concurrent job processing
   - key: MAX_CONCURRENT_JOBS
     value: "20"  # Increase based on load
   ```

### 4. Security Updates

1. **Regular Deployments**:
   - Keep dependencies updated
   - Deploy security patches promptly

2. **Environment Variable Rotation**:
   ```bash
   # Update sensitive keys periodically
   doctl apps update YOUR_APP_ID --spec .do/app.yaml
   ```

## Troubleshooting

### Common Deployment Issues

#### 1. Build Failures

**Backend Build Issues**:
```bash
# Check Python version compatibility
python --version  # Should be 3.8+

# Verify requirements.txt
pip install -r backend/requirements.txt
```

**Frontend Build Issues**:
```bash
# Check Node.js version
node --version  # Should be 18+

# Clear dependencies and rebuild
rm -rf frontend/node_modules frontend/package-lock.json
cd frontend && npm install && npm run build
```

#### 2. Environment Variable Issues

**Missing Variables**:
- Check all required environment variables are set
- Verify variable names match exactly (case-sensitive)
- Ensure SECRET variables are properly marked

**Supabase Connection Issues**:
```bash
# Test Supabase connection
curl -H "Authorization: Bearer YOUR_SERVICE_KEY" \
     -H "Content-Type: application/json" \
     "https://your-project.supabase.co/rest/v1/jobs"
```

#### 3. Authentication Issues

**JWT Secret Issues**:
- Generate a strong, random JWT secret
- Ensure it's consistent across backend and worker services

**Supabase Auth Issues**:
- Verify Supabase URL and keys are correct
- Check that authentication is enabled in Supabase

#### 4. CORS Issues

**Frontend Can't Connect to Backend**:
```yaml
# Update CORS origins
- key: ALLOWED_ORIGINS
  value: "https://your-frontend-url,https://your-domain.com"
```

### Performance Issues

#### 1. High CPU/Memory Usage

**Backend Optimization**:
```yaml
# Reduce concurrent jobs
- key: MAX_CONCURRENT_JOBS
  value: "5"

# Increase timeout for heavy operations
- key: JOB_TIMEOUT
  value: "1800"
```

**Scaling Options**:
```yaml
# Increase instance size
instance_size_slug: basic-s  # or basic-m

# Increase instance count
instance_count: 2
```

#### 2. Slow Response Times

**Database Optimization**:
- Add indexes in Supabase for frequently queried fields
- Optimize SQL queries
- Consider database connection pooling

**Caching**:
```yaml
# Enable agent result caching
- key: ENABLE_RESULT_CACHING
  value: "true"
```

### Debugging Commands

```bash
# Get app info
doctl apps get YOUR_APP_ID

# View logs in real-time
doctl apps logs YOUR_APP_ID --component backend --follow

# Get deployment history
doctl apps list-deployments YOUR_APP_ID

# View app spec
doctl apps spec get YOUR_APP_ID

# Update app configuration
doctl apps update YOUR_APP_ID --spec .do/app.yaml
```

**💡 Tip: Use the deployment script for easier management:**
```bash
# All the above commands simplified:
./scripts/deploy.sh status
./scripts/deploy.sh logs backend
```

## Cost Optimization

### 1. Resource Right-Sizing

**Development/Staging**:
```yaml
# Use smaller instances for non-production
instance_size_slug: basic-xxs
instance_count: 1
```

**Production Scaling**:
```yaml
# Scale based on actual usage
instance_size_slug: basic-xs  # Start small
instance_count: 1              # Scale up as needed
```

### 2. Worker Optimization

```yaml
# Adjust worker count based on job volume
- key: MAX_CONCURRENT_JOBS
  value: "3"  # Reduce for lower job volumes

# Optimize cleanup frequency
- key: CLEANUP_COMPLETED_JOBS_AFTER
  value: "43200"  # 12 hours instead of 24
```

### 3. Monitoring Costs

1. **DigitalOcean Usage Dashboard**:
   - Monitor monthly spending
   - Set up billing alerts
   - Review resource utilization

2. **Resource Optimization**:
   - Remove unused workers if job volume is low
   - Scale down during off-peak hours
   - Use basic instance sizes unless performance requires more

### 4. Development vs Production

**Development Environment**:
```yaml
# Minimal configuration for development
instance_count: 1
instance_size_slug: basic-xxs
- key: MAX_CONCURRENT_JOBS
  value: "2"
```

**Production Environment**:
```yaml
# Production-ready configuration
instance_count: 2  # For redundancy
instance_size_slug: basic-xs
- key: MAX_CONCURRENT_JOBS
  value: "10"
```

## Using the Deployment Script

For ongoing maintenance and updates, use the unified deployment script:

### Quick Commands

```bash
# Check application status
./scripts/deploy.sh status

# View logs
./scripts/deploy.sh logs backend
./scripts/deploy.sh logs frontend

# Update application
./scripts/deploy.sh update --env production

# Validate configuration
./scripts/deploy.sh validate --env production
```

### Automated Deployment

```bash
# Production deployment with monitoring
./scripts/deploy.sh deploy \
  --env production \
  --domain yourdomain.com \
  --verbose

# Development deployment (quick)
./scripts/deploy.sh deploy --env development --skip-env-check
```

For complete script documentation, see: [scripts/README.md](scripts/README.md)

## Next Steps

### 1. Custom Domain Setup
- Configure your domain DNS
- Set up SSL certificates  
- Update CORS configurations

### 2. Monitoring and Alerting
- Set up DigitalOcean monitoring
- Configure log aggregation
- Create custom dashboards

### 3. CI/CD Pipeline
- Set up automated testing
- Configure deployment hooks with the deployment script
- Implement staging environment

### 4. Advanced Features
- Set up CDN for static assets
- Configure database connection pooling
- Implement rate limiting

---

## Summary

**Deployment Options:**
- **Automated**: Use `./scripts/deploy.sh` for quick, reliable deployments
- **Manual**: Follow this guide for detailed control and understanding

**Estimated Deployment Time**: 
- With script: 5-15 minutes
- Manual setup: 30-60 minutes

**Monthly Cost**: ~$15/month for production-ready deployment
**Uptime**: 99.9% with DigitalOcean App Platform SLA

For additional help, refer to:
- [scripts/README.md](scripts/README.md) - Deployment script documentation
- [DigitalOcean App Platform documentation](https://docs.digitalocean.com/products/app-platform/)
- Create an issue in the repository for specific problems