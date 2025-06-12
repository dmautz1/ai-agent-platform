# Configuration Management

This project uses a centralized configuration system to manage environment variables across multiple components and deployment targets.

## Overview

Instead of maintaining separate `.env` files for each component, all configuration is managed from a single `config.yaml` file. This eliminates duplication and ensures consistency across:

- Root `.env` file (used by deployment scripts)
- Backend `.env` file (FastAPI application)  
- Frontend `.env.local` file (React/Vite application)
- `.do/app.yaml` file (Digital Ocean deployment)

## Quick Start

### 1. Install Dependencies

```bash
# Install Python dependencies for config generation
pip install -r requirements.txt
```

### 2. Configure Your Settings

Edit `config.yaml` with your specific values:

```yaml
# Database configuration
database:
  supabase_url: "https://your-project.supabase.co"
  supabase_anon_key: "your-anon-key"
  supabase_service_key: "your-service-key"

# AI provider keys
ai_providers:
  google:
    api_key: "your-google-api-key"
  # ... other providers
```

### 3. Generate Configuration Files

```bash
# For development
make config-dev
# OR
python scripts/generate_config.py development

# For production  
make config-prod
# OR
python scripts/generate_config.py production
```

### 4. Deploy (automatically generates production config)

```bash
make deploy
# OR
./scripts/deploy.sh
```

## Configuration File Structure

The `config.yaml` file is organized into logical sections:

### Project Metadata
```yaml
project:
  name: "AI Agent Platform"
  version: "1.0.0"
  description: "Production-ready AI Agent Development Platform"
```

### Environment-Specific Settings
```yaml
environments:
  development:
    debug: true
    cors_origins:
      - "http://localhost:3000"
      - "http://localhost:5173"
    api_base_url: "http://localhost:8000"
    
  production:
    debug: false
    cors_origins:
      - "https://yourdomain.com"
    api_base_url: "https://yourdomain.com"
```

### Database Configuration
```yaml
database:
  supabase_url: "https://your-project.supabase.co"
  supabase_anon_key: "your-anon-key"
  supabase_service_key: "your-service-key"
```

### AI Provider Configuration
```yaml
ai_providers:
  default_provider: "google"
  
  google:
    api_key: "your-api-key"
    default_model: "gemini-2.0-flash"
    use_vertex_ai: false
    
  openai:
    api_key: "your-api-key"
    default_model: "gpt-4o-mini"
    
  # ... other providers
```

### Security & Authentication
```yaml
auth:
  jwt_secret: "your-jwt-secret"
  jwt_algorithm: "HS256"
  access_token_expire_minutes: 30
  trusted_hosts:
    - "localhost"
    - "yourdomain.com"
```

### Job Processing
```yaml
jobs:
  max_concurrent: 10
  timeout: 3600
  retry_attempts: 3
  queue_max_size: 1000
```

### Frontend Configuration
```yaml
frontend:
  features:
    dev_tools: true
    analytics: false
  ui:
    default_theme: "system"
  polling:
    job_status_interval: 5000
```

### Deployment Settings
```yaml
deployment:
  digital_ocean:
    app_name: "your-app-name"
    region: "nyc"
    domain: "yourdomain.com"
    backend_instance: "basic-xxs"
    frontend_instance: "basic-xxs"
```

## Available Commands

### Make Commands
```bash
make help           # Show available commands
make setup-dev      # Install deps and generate dev config
make config-dev     # Generate development config files
make config-prod    # Generate production config files  
make config-check   # Validate config without generating files
make deploy         # Deploy to production (generates prod config)
make clean          # Remove generated config files
make status         # Show which config files exist
```

### Direct Script Usage
```bash
# Generate for specific environment
python scripts/generate_config.py development
python scripts/generate_config.py production

# Dry run (show what would be generated)
python scripts/generate_config.py development --dry-run

# Help
python scripts/generate_config.py --help
```

## Generated Files

### Root `.env`
Contains essential variables for deployment scripts:
- Environment settings
- Database URLs
- Basic authentication keys

### Backend `.env` 
Complete FastAPI configuration:
- All AI provider settings
- Database configuration
- Job processing settings  
- CORS and security settings
- Logging configuration

### Frontend `.env.local`
Vite/React configuration with `VITE_` prefixed variables:
- API endpoint URLs
- Supabase client configuration
- Feature flags
- UI settings
- Build configuration

### `.do/app.yaml`
Digital Ocean App Platform configuration:
- Complete service definitions
- Environment variables for both services
- Health check settings
- Domain and routing configuration

## Security Considerations

1. **Sensitive Data**: The `config.yaml` file contains sensitive information and should:
   - Be added to `.gitignore` (already configured)
   - Have restricted file permissions (`chmod 600`)
   - Be stored securely in production environments

2. **Environment Separation**: 
   - Development and production settings are clearly separated
   - Different security settings for each environment
   - Production automatically disables debug features

3. **Secret Management**:
   - All secrets are marked as `type: SECRET` in Digital Ocean config
   - API keys and tokens are properly protected
   - JWT secrets use strong encryption

## Troubleshooting

### Missing Dependencies
```bash
pip install PyYAML python-dotenv
```

### Configuration Validation
```bash
# Check what would be generated
python scripts/generate_config.py development --dry-run

# Validate YAML syntax
python -c "import yaml; yaml.safe_load(open('config.yaml'))"
```

### File Permissions
```bash
# Secure the config file
chmod 600 config.yaml

# Make script executable
chmod +x scripts/generate_config.py
```

### Deployment Issues
```bash
# Generate fresh production config
make config-prod

# Check deployment script
./scripts/deploy.sh --dry-run
```

## Migration from Old System

If you have existing `.env` files:

1. Copy values from existing files into `config.yaml`
2. Run `make config-check` to validate
3. Generate new files with `make config-dev`
4. Compare and verify the generated files
5. Remove old `.env` files after verification

## Best Practices

1. **Version Control**: Only commit `config.yaml.example`, never the real `config.yaml`
2. **Environment Variables**: Use environment variables to override sensitive values in CI/CD
3. **Validation**: Always run `config-check` before deploying
4. **Backups**: Keep backups of working configurations
5. **Documentation**: Update this file when adding new configuration sections

## Example Workflow

```bash
# 1. Clone repository
git clone your-repo

# 2. Copy example config
cp config.yaml.example config.yaml

# 3. Edit configuration
nano config.yaml

# 4. Setup development environment
make setup-dev

# 5. Start development
cd backend && source venv/bin/activate && python main.py
cd frontend && npm run dev

# 6. Deploy to production
make deploy
```

This centralized approach ensures consistency, reduces errors, and makes it much easier to manage configuration across your entire application stack.

## DigitalOcean Project Management

The deployment system automatically manages DigitalOcean projects for better resource organization and follows the correct deployment flow:

### Automatic Project-First Deployment Flow

The deployment script follows this optimized sequence:

1. **Check/Create Project First**: Ensures the target project exists before creating any resources
2. **Create App in Project**: Apps are created directly in the specified project using `--project-id`
3. **Automatic Assignment**: No separate assignment step needed - apps are automatically organized

### Project Configuration

Configure your DigitalOcean project in `config.yaml`:

```yaml
deployment:
  digital_ocean:
    app_name: "ai-agent-platform"
    region: "nyc"
    domain: "yourdomain.com"
    
    # Source control configuration
    repository:
      url: "your-github-username/your-repo-name"  # GitHub repository (username/repo)
      branch: "main"                    # Git branch to deploy from
      deploy_on_push: true             # Auto-deploy on git push
    
    project:
      name: "AI Agent Platform"
      description: "Production-ready AI Agent Development Platform deployment"
      purpose: "Web Application"
      environment: "Production"
```

### Repository Configuration

The `repository` section allows you to configure which Git repository and branch to deploy from:

- **`url`**: GitHub repository in format `username/repository-name`
- **`branch`**: Git branch to deploy from (e.g., `main`, `production`, `develop`)
- **`deploy_on_push`**: Whether to automatically trigger deployments when code is pushed to the specified branch

This configuration applies to both backend and frontend services, ensuring they deploy from the same repository and branch for consistency.

### Deployment Flow

When you run `make deploy`, the system:

1. ✅ **Validates Configuration**: Checks all required environment variables and settings
2. ✅ **Builds Frontend**: Compiles and optimizes the React application  
3. ✅ **Manages Project**: Checks if the configured project exists, creates it if needed
4. ✅ **Creates App**: Deploys the app directly into the target project
5. ✅ **Monitors Deployment**: Waits for successful deployment and provides status updates

### Project Management Commands

Use these make commands for project management:

```bash
# Show project and app status
make project-status

# Check deployment status
make deploy-status

# View deployment logs
make deploy-logs
```

### Manual Project Operations

You can also use the deployment script directly:

```bash
# Deploy with automatic project management
./scripts/deploy.sh deploy

# Check deployment status
./scripts/deploy.sh status

# View logs
./scripts/deploy.sh logs
```

### Benefits

- **Organization**: Apps are automatically organized under projects from creation
- **Billing**: Better cost tracking and resource management
- **Teams**: Easier collaboration and access control
- **Automation**: No manual project setup or assignment required
- **Efficiency**: Single-step deployment with automatic project management
- **Reliability**: Project-first flow prevents orphaned resources 