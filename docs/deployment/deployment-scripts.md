# Deployment Scripts

> **Automated deployment tools** - Scripts for deploying to DigitalOcean and other platforms

## Overview

The `scripts/` directory contains automated deployment tools for the AI Agent Template:

- **`deploy.sh`** - Unified deployment script for DigitalOcean App Platform with comprehensive automation, error handling, and monitoring

## Quick Start

### Prerequisites

1. **Install doctl CLI**:
   ```bash
   # macOS
   brew install doctl
   
   # Linux
   snap install doctl
   
   # Or download from: https://github.com/digitalocean/doctl/releases
   ```

2. **Authenticate with DigitalOcean**:
   ```bash
   doctl auth init
   ```

3. **Set up environment variables** (create `.env` file in project root):
   ```bash
   SUPABASE_URL=https://your-project.supabase.co
   SUPABASE_KEY=your-supabase-anon-key
   SUPABASE_SERVICE_KEY=your-supabase-service-key
   GOOGLE_API_KEY=your-google-ai-api-key
   JWT_SECRET=your-32-character-secret
   GITHUB_REPO=your-username/ai-agent-template
   ```

### Basic Deployment

```bash
# Deploy to production with custom domain
./scripts/deploy.sh deploy --env production --domain yourdomain.com

# Deploy to staging
./scripts/deploy.sh deploy --env staging

# Create new app (force creation)
./scripts/deploy.sh create --name my-ai-agent --env production
```

## Deployment Script Usage

### Commands

| Command | Description | Example |
|---------|-------------|---------|
| `deploy` | Deploy or update application (default) | `./scripts/deploy.sh deploy` |
| `create` | Force create new app | `./scripts/deploy.sh create --name new-app` |
| `update` | Update existing app only | `./scripts/deploy.sh update` |
| `status` | Check deployment status | `./scripts/deploy.sh status` |
| `logs` | View application logs | `./scripts/deploy.sh logs backend` |
| `rollback` | Rollback deployment | `./scripts/deploy.sh rollback` |
| `destroy` | Destroy application | `./scripts/deploy.sh destroy` |
| `validate` | Validate configuration | `./scripts/deploy.sh validate` |

### Options

| Option | Description | Example |
|--------|-------------|---------|
| `-n, --name NAME` | App name | `--name my-app` |
| `-e, --env ENV` | Environment (development\|staging\|production) | `--env production` |
| `-d, --domain DOMAIN` | Custom domain | `--domain yourdomain.com` |
| `--force-create` | Force create new app | `--force-create` |
| `--skip-build` | Skip frontend build | `--skip-build` |
| `--skip-env-check` | Skip environment validation | `--skip-env-check` |
| `--dry-run` | Show actions without executing | `--dry-run` |
| `-v, --verbose` | Enable verbose logging | `--verbose` |
| `-h, --help` | Show help message | `--help` |

## Deployment Workflows

### Production Deployment

```bash
# Full production deployment with custom domain
./scripts/deploy.sh deploy \
  --env production \
  --domain yourdomain.com \
  --verbose

# Check deployment status
./scripts/deploy.sh status

# View logs if needed
./scripts/deploy.sh logs backend
```

### Development/Testing

```bash
# Quick development deployment
./scripts/deploy.sh deploy --env development --skip-env-check

# Validate configuration without deploying
./scripts/deploy.sh validate --env production

# Dry run to see what would happen
./scripts/deploy.sh deploy --env production --dry-run
```

### Maintenance Operations

```bash
# View recent logs
./scripts/deploy.sh logs backend
./scripts/deploy.sh logs frontend

# Check app status and health
./scripts/deploy.sh status

# Destroy app (with confirmation)
./scripts/deploy.sh destroy
```

## Environment Variables

### Required Variables

The deployment script requires these environment variables to be set:

```bash
# Supabase Configuration
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-supabase-anon-key
SUPABASE_SERVICE_KEY=your-supabase-service-role-key

# Google AI Configuration
GOOGLE_API_KEY=your-google-ai-api-key

# Security Configuration
JWT_SECRET=your-32-character-random-secret
```

### Optional Variables

```bash
# GitHub Configuration
GITHUB_REPO=your-username/ai-agent-template

# Security Configuration
TRUSTED_HOSTS=yourdomain.com,www.yourdomain.com
ALLOWED_ORIGINS=https://yourdomain.com,https://www.yourdomain.com

# Performance Configuration
MAX_CONCURRENT_JOBS=10
JOB_TIMEOUT=3600
```

### Environment Files

Create a `.env` file in the project root:

```bash
# Copy example file
cp .env.example .env

# Edit with your values
nano .env
```

## Configuration Files

### DigitalOcean App Spec

The deployment script uses `.do/app.yaml` for DigitalOcean App Platform configuration. Key placeholders that get replaced:

- `your-domain.com` → Your custom domain
- `your-github-username/ai-agent-template` → Your GitHub repository
- Environment-specific values based on `--env` flag

### Automatic Configuration Updates

The script automatically updates the app.yaml configuration based on command line options:

```bash
# Updates domain in app.yaml
--domain yourdomain.com

# Updates environment variables
--env production

# Uses GitHub repo from environment variable
GITHUB_REPO=myuser/my-ai-agent
```

## Error Handling and Troubleshooting

### Common Issues

**Environment Variable Missing:**
```bash
Error: SUPABASE_URL not set
Solution: Set required environment variables in .env file
```

**DigitalOcean Authentication Failed:**
```bash
Error: doctl authentication failed
Solution: Run 'doctl auth init' and provide your API token
```

**App Creation Failed:**
```bash
Error: App with name 'ai-agent-template' already exists
Solution: Use --name option to specify different name or --force-create to overwrite
```

**Domain Configuration Failed:**
```bash
Error: Domain verification failed
Solution: Ensure DNS records are properly configured
```

### Debug Mode

Enable verbose logging for troubleshooting:

```bash
./scripts/deploy.sh deploy --verbose --dry-run
```

### Script Validation

Validate your configuration before deployment:

```bash
# Check environment variables
./scripts/deploy.sh validate

# Test with dry run
./scripts/deploy.sh deploy --env production --dry-run
```

## Advanced Usage

### Multiple Environments

Deploy to different environments with environment-specific configurations:

```bash
# Development
./scripts/deploy.sh deploy --env development --name ai-agent-dev

# Staging
./scripts/deploy.sh deploy --env staging --name ai-agent-staging

# Production
./scripts/deploy.sh deploy --env production --name ai-agent-prod --domain yourdomain.com
```

### Automated CI/CD

Use in GitHub Actions:

```yaml
- name: Deploy to DigitalOcean
  run: |
    ./scripts/deploy.sh deploy --env production --skip-env-check
  env:
    SUPABASE_URL: ${{ secrets.SUPABASE_URL }}
    GOOGLE_API_KEY: ${{ secrets.GOOGLE_API_KEY }}
    # ... other secrets
```

---

**Related Documentation:**
- **[Deployment Guide](deployment-guide.md)** - General deployment concepts
- **[DigitalOcean Setup](digitalocean.md)** - Platform-specific setup
- **[Configuration Reference](../configuration/README.md)** - Environment variables 