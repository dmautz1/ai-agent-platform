# DigitalOcean App Platform Deployment Guide

> **Complete Guide to Deploying AI Agent Platform** - From setup to production

This guide walks you through deploying the AI Agent Platform to DigitalOcean App Platform using the **centralized configuration system**.

## 🚀 Quick Start with Centralized Configuration

**⚡ The platform uses a single `config.yaml` file for all configuration:**

```bash
# 1. Set up centralized configuration
cp config.yaml.example config.yaml
# Edit config.yaml with your credentials

# 2. Install configuration dependencies  
pip install -r requirements.txt

# 3. Install and authenticate doctl
brew install doctl  # or appropriate installation for your OS
doctl auth init

# 4. Deploy to production (automatically generates config)
make deploy
# OR
./scripts/deploy.sh deploy --env production --domain yourdomain.com

# 5. Check status
./scripts/deploy.sh status
```

## 🔧 Configuration Management

### Centralized Configuration Benefits

- **Single Source of Truth** - All variables defined once in `config.yaml`
- **No Duplication** - Variables automatically generated for each component
- **Environment Separation** - Clear development vs production settings
- **Automatic Generation** - Script generates all necessary files
- **Deployment Integration** - Deploy script automatically generates production config

### Configuration Files Generated

From `config.yaml`, the system generates:
- **Root `.env`** - Used by deployment scripts
- **`backend/.env`** - FastAPI application configuration
- **`frontend/.env.local`** - React/Vite application configuration  
- `.do/app.yaml` - Digital Ocean deployment configuration

### Available Commands

```bash
make help           # Show available configuration commands
make config-dev     # Generate development configuration files
make config-prod    # Generate production configuration files  
make config-check   # Validate configuration without generating files
make deploy         # Deploy to production (auto-generates prod config)
make clean          # Remove generated configuration files
make status         # Show which configuration files exist
```

---

## Manual Deployment Guide

For manual deployment or advanced configuration, follow the detailed steps below.

## Table of Contents

- [Prerequisites](#prerequisites)
- [Pre-Deployment Setup](#pre-deployment-setup)
- [Configuration Setup](#configuration-setup)
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
- **AI Provider Account** (Google AI Studio, OpenAI, Anthropic, etc.)

### Required Tools
- **Python 3.8+** for configuration generation
- **Node.js 20+** for frontend build
- **Git** for repository management
- **doctl CLI** for DigitalOcean deployment

### Cost Estimate
- **Backend Service**: ~$5/month (Basic plan)
- **Frontend Service**: ~$5/month (Basic plan)
- **Total**: ~$10/month for production-ready deployment

## Pre-Deployment Setup

### 1. Prepare Your Repository

1. **Fork or Clone the Repository**:
   ```bash
   git clone https://github.com/your-username/ai-agent-platform.git
   cd ai-agent-platform
   ```

2. **Install Configuration Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Push to Your GitHub Repository**:
   ```bash
   git remote set-url origin https://github.com/your-username/ai-agent-platform.git
   git push -u origin main
   ```

### 2. Set Up Supabase Database

1. **Create Supabase Project**:
   - Go to [supabase.com](https://supabase.com)
   - Create a new project
   - Wait for project initialization (~2 minutes)

2. **Run Database Migrations**:
   - Go to **SQL Editor** in Supabase dashboard
   - Copy content from `supabase/migrations/supabase_setup.sql`
   - Run the SQL to create tables

3. **Get Database Credentials**:
   - Go to **Settings** → **API**
   - Copy **Project URL**
   - Copy **anon public key**
   - Copy **service_role key**

### 3. Set Up AI Providers

Choose one or more AI providers:

#### Google AI Studio (Recommended)
1. Visit [Google AI Studio](https://aistudio.google.com)
2. Create an API key
3. Copy the API key

#### Other Providers
- **OpenAI**: [Platform](https://platform.openai.com) - GPT models
- **Anthropic**: [Console](https://console.anthropic.com) - Claude models
- **Grok**: [Console](https://console.x.ai) - Grok models with real-time data
- **DeepSeek**: [Platform](https://platform.deepseek.com) - Cost-effective models
- **Meta Llama**: [Together AI](https://api.together.xyz) - Open-source models

## Configuration Setup

### 1. Create Configuration File

```bash
# Copy the example configuration
cp config.yaml.example config.yaml
```

### 2. Edit Centralized Configuration

Edit `config.yaml` with your specific values:

#### Project Settings
```yaml
project:
  name: "Your App Name"
  version: "1.0.0"

deployment:
  digital_ocean:
    app_name: "your-app-name"
    domain: "yourdomain.com"  # Optional: remove for DigitalOcean subdomain
    region: "nyc"  # Choose: nyc1, nyc3, ams3, sfo3, sgp1, lon1, fra1, tor1, blr1
```

#### Database Configuration
```yaml
database:
  supabase_url: "https://your-project-id.supabase.co"
  supabase_anon_key: "your-supabase-anon-key"
  supabase_service_key: "your-supabase-service-role-key"
```

#### Security Configuration
```yaml
auth:
  jwt_secret: "your-32-character-random-jwt-secret"  # Generate with: openssl rand -base64 32
```

#### AI Provider Configuration
```yaml
ai_providers:
  default_provider: "google"  # Choose your primary provider
  
  google:
    api_key: "your-google-ai-api-key"
  openai:
    api_key: "your-openai-api-key"  # Optional
  anthropic:
    api_key: "your-anthropic-api-key"  # Optional
  # ... configure other providers as needed
```

#### Environment-Specific Settings
```yaml
environments:
  production:
    debug: false
    cors_origins:
      - "https://yourdomain.com"
      - "https://www.yourdomain.com"
    api_base_url: "https://yourdomain.com"
    frontend_url: "https://yourdomain.com"
```

### 3. Generate Deployment Configuration

```bash
# Generate production configuration files
make config-prod

# Verify generated files
make status
```

This creates:
- `.env` - Root environment variables
- `backend/.env` - Backend configuration
- `frontend/.env.local` - Frontend configuration  
- `.do/app.yaml` - DigitalOcean deployment configuration

### 4. Validate Configuration

```bash
# Check configuration without generating files
make config-check

# Validate specific environment
python scripts/generate_config.py production --dry-run
```

## Deployment Process

### Option 1: Automated Deployment (Recommended)

```bash
# Deploy with automatic configuration generation
make deploy

# Or with specific options
./scripts/deploy.sh deploy --env production --domain yourdomain.com
```

### Option 2: Manual Deployment

1. **Install DigitalOcean CLI**:
   ```bash
   # macOS
   brew install doctl
   
   # Linux
   snap install doctl
   
   # Windows
   # Download from: https://github.com/digitalocean/doctl/releases
   ```

2. **Authenticate with DigitalOcean**:
   ```bash
   doctl auth init
   ```

3. **Deploy the Application**:
   ```bash
   # Create new app
   doctl apps create --spec .do/app.yaml
   
   # Or update existing app
   doctl apps update YOUR_APP_ID --spec .do/app.yaml
   ```

### 3. Monitor Deployment

```bash
# Check deployment status
./scripts/deploy.sh status

# View logs
./scripts/deploy.sh logs backend
./scripts/deploy.sh logs frontend
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