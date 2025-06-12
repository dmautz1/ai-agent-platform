# Deployment Scripts Documentation

> **Automated Deployment Tools** - Streamlined deployment with centralized configuration

This document covers the deployment automation tools and scripts included with the AI Agent Platform.

## 🚀 Overview

The platform includes a comprehensive deployment system with:

- **Centralized Configuration** - Single `config.yaml` file for all settings
- **Automated Deployment** - One-command deployment to DigitalOcean
- **Environment Management** - Separate dev/production configurations
- **Configuration Generation** - Auto-generates all necessary files
- **Health Monitoring** - Built-in deployment monitoring and logging

## 📋 Available Tools

### 1. Configuration Generator (`scripts/generate_config.py`)

Generates all configuration files from the centralized `config.yaml`:

```bash
# Generate development configuration
python scripts/generate_config.py development

# Generate production configuration  
python scripts/generate_config.py production

# Validate configuration without generating files
python scripts/generate_config.py development --dry-run

# Show help
python scripts/generate_config.py --help
```

**Generated Files:**
- `.env` - Root environment variables for deployment scripts
- `backend/.env` - FastAPI application configuration
- `frontend/.env.local` - React/Vite application configuration
- `.do/app.yaml` - DigitalOcean App Platform deployment specification

### 2. Deployment Script (`scripts/deploy.sh`)

Unified deployment script with comprehensive automation:

```bash
# Deploy with automatic configuration generation
./scripts/deploy.sh deploy --env production --domain yourdomain.com

# Create new app (force creation)
./scripts/deploy.sh create --name my-app --env production

# Update existing app
./scripts/deploy.sh update

# Check deployment status
./scripts/deploy.sh status

# View application logs
./scripts/deploy.sh logs backend
./scripts/deploy.sh logs frontend

# Rollback deployment (manual process)
./scripts/deploy.sh rollback

# Destroy application (with confirmation)
./scripts/deploy.sh destroy

# Validate configuration
./scripts/deploy.sh validate --env production
```

### 3. Makefile Commands

Convenient shortcuts for common operations:

```bash
# Show available commands
make help

# Setup development environment
make setup-dev

# Configuration management
make config-dev     # Generate development config
make config-prod    # Generate production config
make config-check   # Validate configuration
make status         # Show config file status
make clean          # Remove generated files

# Deployment
make deploy         # Deploy to production (auto-generates config)
```

## ⚙️ Configuration System

### Centralized Configuration (`config.yaml`)

All project configuration is managed from a single YAML file:

```yaml
# Project metadata
project:
  name: "AI Agent Platform"
  version: "1.0.0"

# Environment-specific settings
environments:
  development:
    debug: true
    api_base_url: "http://localhost:8000"
  production:
    debug: false
    api_base_url: "https://yourdomain.com"

# Database configuration
database:
  supabase_url: "https://your-project.supabase.co"
  supabase_anon_key: "your-anon-key"
  supabase_service_key: "your-service-key"

# AI providers
ai_providers:
  default_provider: "google"
  google:
    api_key: "your-google-api-key"
    default_model: "gemini-2.0-flash"

# Deployment settings
deployment:
  digital_ocean:
    app_name: "your-app-name"
    domain: "yourdomain.com"
    region: "nyc"
```

### Benefits

- **No Duplication** - Define variables once, use everywhere
- **Environment Separation** - Clear development vs production settings
- **Type Safety** - YAML validation prevents configuration errors
- **Version Control** - Real config.yaml is gitignored for security
- **Deployment Ready** - Auto-generates all deployment files

## 🛠️ Deployment Workflow

### Standard Deployment Process

1. **Setup Configuration**:
   ```bash
   cp config.yaml.example config.yaml
   # Edit config.yaml with your values
   ```

2. **Generate Configuration Files**:
   ```bash
   make config-prod
   ```

3. **Deploy Application**:
   ```bash
   make deploy
   ```

4. **Monitor Deployment**:
   ```bash
   ./scripts/deploy.sh status
   ```

### Automated Deployment Features

The deployment script automatically:

- **Validates Prerequisites** - Checks for required tools (doctl, python, etc.)
- **Generates Configuration** - Creates production config from config.yaml
- **Builds Frontend** - Compiles and optimizes React application
- **Deploys Services** - Creates or updates DigitalOcean app
- **Monitors Progress** - Tracks deployment status with real-time updates
- **Validates Health** - Tests health endpoints after deployment

## 📊 Script Options

### Configuration Generator Options

```bash
python scripts/generate_config.py [ENVIRONMENT] [OPTIONS]

ENVIRONMENTS:
  development    Generate development configuration (default)
  production     Generate production configuration

OPTIONS:
  --dry-run      Show what would be generated without writing files
  --help         Show help message
```

### Deployment Script Options

```bash
./scripts/deploy.sh [COMMAND] [OPTIONS]

COMMANDS:
  deploy         Deploy or update application (default)
  create         Create new app (force creation)
  update         Update existing app
  status         Check deployment status
  logs           View application logs
  rollback       Rollback to previous deployment
  destroy        Destroy application
  validate       Validate configuration

OPTIONS:
  -n, --name NAME         App name (default: from config.yaml)
  -e, --env ENV          Environment (development|production)
  -d, --domain DOMAIN    Custom domain
  --force-create         Force create new app
  --skip-build          Skip frontend build
  --skip-env-check      Skip environment validation
  --dry-run             Show what would be done
  -v, --verbose         Enable verbose logging
  -h, --help            Show help
```

## 🔍 Monitoring and Debugging

### Health Checks

The deployment includes automatic health monitoring:

```bash
# Check overall application status
./scripts/deploy.sh status

# View real-time logs
./scripts/deploy.sh logs backend
./scripts/deploy.sh logs frontend

# Test health endpoints manually
curl https://yourdomain.com/health
curl https://yourdomain.com/
```

### Common Deployment Issues

1. **Configuration Errors**:
   ```bash
   # Validate configuration
   make config-check
   python scripts/generate_config.py production --dry-run
   ```

2. **Build Failures**:
   ```bash
   # Check frontend build locally
   cd frontend && npm run build
   
   # Deploy with build logs
   ./scripts/deploy.sh deploy --verbose
   ```

3. **Environment Variable Issues**:
   ```bash
   # Regenerate configuration
   make config-prod
   
   # Check generated files
   make status
   ```

4. **Deployment Timeouts**:
   ```bash
   # Check deployment logs
   ./scripts/deploy.sh logs backend
   
   # Manual deployment monitoring
   doctl apps list-deployments YOUR_APP_ID
   ```

## 🔐 Security Considerations

### Environment Variables

- **Sensitive Data**: All secrets marked as `type: SECRET` in DigitalOcean
- **Local Security**: config.yaml is gitignored and should have restricted permissions
- **Production Secrets**: Use strong, randomly generated keys

### Best Practices

1. **Configuration Security**:
   ```bash
   # Secure the config file
   chmod 600 config.yaml
   
   # Generate strong JWT secret
   openssl rand -base64 32
   ```

2. **Deployment Security**:
   - Use environment-specific configurations
   - Enable secure cookies in production
   - Configure proper CORS origins
   - Use HTTPS for all production traffic

3. **Access Control**:
   - Limit doctl access to deployment-only permissions
   - Use separate Supabase projects for dev/prod
   - Rotate API keys regularly

## 🚀 Advanced Usage

### Custom Deployment Targets

Modify `config.yaml` for different deployment scenarios:

```yaml
deployment:
  digital_ocean:
    app_name: "staging-app"        # Different app for staging
    region: "fra1"                 # European deployment
    backend_instance: "basic-s"    # Larger instance for production
    frontend_instance: "basic-s"
```

### Multi-Environment Setup

```bash
# Development deployment
python scripts/generate_config.py development
./scripts/deploy.sh deploy --env development --name dev-app

# Staging deployment  
python scripts/generate_config.py production
# Edit config.yaml for staging settings
./scripts/deploy.sh deploy --env production --name staging-app

# Production deployment
./scripts/deploy.sh deploy --env production --name prod-app
```

### CI/CD Integration

The scripts are designed for CI/CD integration:

```yaml
# GitHub Actions example
- name: Deploy to Production
  run: |
    echo "$CONFIG_YAML" > config.yaml
    make config-prod
    ./scripts/deploy.sh deploy --env production
  env:
    CONFIG_YAML: ${{ secrets.CONFIG_YAML }}
    DIGITALOCEAN_ACCESS_TOKEN: ${{ secrets.DO_TOKEN }}
```

## 📚 Related Documentation

- **[Configuration Guide](../../CONFIG.md)** - Complete configuration system documentation
- **[Deployment Guide](deployment-guide.md)** - Step-by-step deployment instructions
- **[DigitalOcean Guide](digitalocean.md)** - DigitalOcean-specific configuration
- **[Security Guide](../security/deployment-security.md)** - Security best practices 