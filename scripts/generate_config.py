#!/usr/bin/env python3
"""
Configuration Generator for AI Agent Platform

This script reads the centralized config.yaml file and generates:
- .env (root level)
- backend/.env
- frontend/.env.local  
- .do/app.yaml (Digital Ocean deployment)

Usage:
    python scripts/generate_config.py [environment]

Arguments:
    environment: development (default) or production
"""

import os
import sys
import yaml
import argparse
from pathlib import Path
from typing import Dict, Any

def load_config(config_path: Path) -> Dict[str, Any]:
    """Load the central configuration file."""
    try:
        with open(config_path, 'r') as f:
            return yaml.safe_load(f)
    except FileNotFoundError:
        print(f"❌ Configuration file not found: {config_path}")
        sys.exit(1)
    except yaml.YAMLError as e:
        print(f"❌ Error parsing YAML configuration: {e}")
        sys.exit(1)

def generate_root_env(config: Dict[str, Any], environment: str) -> str:
    """Generate root-level .env file."""
    env_config = config['environments'][environment]
    
    content = f"""# =============================================================================
# AI Agent Platform - Root Environment Configuration
# =============================================================================
# Auto-generated from config.yaml - DO NOT EDIT MANUALLY
# Run: python scripts/generate_config.py {environment}
# =============================================================================

# Environment
ENVIRONMENT={environment}

# Project
APP_NAME="{config['deployment']['digital_ocean']['app_name']}"
APP_VERSION={config['project']['version']}

# Deployment
FRONTEND_URL={env_config['frontend_url']}
API_BASE_URL={env_config['api_base_url']}

# Database
SUPABASE_URL={config['database']['supabase_url']}
SUPABASE_ANON_KEY={config['database']['supabase_anon_key']}
SUPABASE_SERVICE_KEY={config['database']['supabase_service_key']}

# Security
JWT_SECRET={config['auth']['jwt_secret']}

# AI Providers
GOOGLE_API_KEY={config['ai_providers']['google']['api_key']}
"""
    return content

def generate_backend_env(config: Dict[str, Any], environment: str) -> str:
    """Generate backend/.env file."""
    env_config = config['environments'][environment]
    server_config = config['server']
    auth_config = config['auth']
    ai_config = config['ai_providers']
    jobs_config = config['jobs']
    cors_config = config['cors']
    logging_config = config['logging']
    
    port = server_config['port'].get(environment, server_config['port']['development'])
    secure_cookies = auth_config['secure_cookies'].get(environment, auth_config['secure_cookies']['development'])
    cors_origins = ','.join(env_config['cors_origins'])
    trusted_hosts = ','.join(auth_config['trusted_hosts'])
    
    content = f"""# =============================================================================
# AI Agent Platform - Backend Environment Configuration
# =============================================================================
# Auto-generated from config.yaml - DO NOT EDIT MANUALLY
# Run: python scripts/generate_config.py {environment}
# =============================================================================

# Environment Settings
ENVIRONMENT={environment}
DEBUG={'true' if env_config['debug'] else 'false'}
APP_NAME="{config['project']['name']} API"
APP_VERSION={config['project']['version']}

# Server Configuration
HOST={server_config['host']}
PORT={port}
RELOAD={'true' if environment == 'development' and server_config['reload'] else 'false'}

# Database Configuration (Supabase)
SUPABASE_URL={config['database']['supabase_url']}
SUPABASE_KEY={config['database']['supabase_anon_key']}
SUPABASE_SERVICE_KEY={config['database']['supabase_service_key']}

# Authentication & Security
JWT_SECRET={auth_config['jwt_secret']}
JWT_ALGORITHM={auth_config['jwt_algorithm']}
ACCESS_TOKEN_EXPIRE_MINUTES={auth_config['access_token_expire_minutes']}
API_RATE_LIMIT={auth_config['api_rate_limit']}
TRUSTED_HOSTS={trusted_hosts}
SECURE_COOKIES={'true' if secure_cookies else 'false'}
MAX_REQUEST_SIZE={auth_config['max_request_size']}

# AI & Agent Configuration
DEFAULT_LLM_PROVIDER={ai_config['default_provider']}

# Google AI Configuration
GOOGLE_API_KEY={ai_config['google']['api_key']}
GOOGLE_DEFAULT_MODEL={ai_config['google']['default_model']}
GOOGLE_GENAI_USE_VERTEXAI={'TRUE' if ai_config['google']['use_vertex_ai'] else 'FALSE'}

# OpenAI Configuration
OPENAI_API_KEY={ai_config['openai']['api_key']}
OPENAI_DEFAULT_MODEL={ai_config['openai']['default_model']}

# Anthropic Configuration
ANTHROPIC_API_KEY={ai_config['anthropic']['api_key']}
ANTHROPIC_DEFAULT_MODEL={ai_config['anthropic']['default_model']}

# Grok Configuration
GROK_API_KEY={ai_config['grok']['api_key']}
GROK_DEFAULT_MODEL={ai_config['grok']['default_model']}
GROK_BASE_URL={ai_config['grok']['base_url']}

# DeepSeek Configuration
DEEPSEEK_API_KEY={ai_config['deepseek']['api_key']}
DEEPSEEK_DEFAULT_MODEL={ai_config['deepseek']['default_model']}
DEEPSEEK_BASE_URL={ai_config['deepseek']['base_url']}

# Meta Llama Configuration
LLAMA_API_KEY={ai_config['llama']['api_key']}
LLAMA_DEFAULT_MODEL={ai_config['llama']['default_model']}
LLAMA_BASE_URL={ai_config['llama']['base_url']}
LLAMA_API_PROVIDER={ai_config['llama']['api_provider']}

# Default agent timeout in seconds
DEFAULT_AGENT_TIMEOUT={jobs_config['default_agent_timeout']}

# Job Processing Configuration
MAX_CONCURRENT_JOBS={jobs_config['max_concurrent']}
JOB_TIMEOUT={jobs_config['timeout']}
JOB_RETRY_ATTEMPTS={jobs_config['retry_attempts']}
JOB_QUEUE_MAX_SIZE={jobs_config['queue_max_size']}
CLEANUP_COMPLETED_JOBS_AFTER={jobs_config['cleanup_after_seconds']}

# CORS Configuration
ALLOWED_ORIGINS={cors_origins}
CORS_ALLOW_CREDENTIALS={'true' if cors_config['allow_credentials'] else 'false'}
CORS_MAX_AGE={cors_config['max_age']}

# Logging Configuration
LOG_LEVEL={logging_config['level']}
LOG_FORMAT={logging_config['format']}
LOG_ROTATION={'true' if logging_config['rotation'] else 'false'}
LOG_MAX_SIZE={logging_config['max_size']}
LOG_BACKUP_COUNT={logging_config['backup_count']}
"""
    return content

def generate_frontend_env(config: Dict[str, Any], environment: str) -> str:
    """Generate frontend/.env.local file."""
    env_config = config['environments'][environment]
    frontend_config = config['frontend']
    
    content = f"""# =============================================================================
# AI Agent Platform - Frontend Environment Configuration
# =============================================================================
# Auto-generated from config.yaml - DO NOT EDIT MANUALLY
# Run: python scripts/generate_config.py {environment}
# =============================================================================

# Node.js environment
NODE_ENV={environment}

# API Configuration
VITE_API_BASE_URL={env_config['api_base_url']}
VITE_API_TIMEOUT=30000
VITE_API_DEBUG={'true' if environment == 'development' else 'false'}

# Supabase Configuration (Frontend)
VITE_SUPABASE_URL={config['database']['supabase_url']}
VITE_SUPABASE_ANON_KEY={config['database']['supabase_anon_key']}
VITE_SUPABASE_REDIRECT_URL={env_config['frontend_url']}/auth/callback

# Application Settings
VITE_APP_TITLE="{config['project']['name']}"
VITE_APP_VERSION={config['project']['version']}
VITE_APP_DESCRIPTION="{config['project']['description']}"

# Feature Flags
VITE_ENABLE_DEV_TOOLS={'true' if frontend_config['features']['dev_tools'] and environment == 'development' else 'false'}
VITE_ENABLE_PERFORMANCE_MONITORING={'true' if frontend_config['features']['performance_monitoring'] else 'false'}
VITE_ENABLE_ERROR_DETAILS={'true' if frontend_config['features']['error_details'] else 'false'}
VITE_ENABLE_API_MOCKING={'true' if frontend_config['features']['api_mocking'] else 'false'}
VITE_ENABLE_ANALYTICS={'true' if frontend_config['features']['analytics'] else 'false'}

# UI Configuration
VITE_DEFAULT_THEME={frontend_config['ui']['default_theme']}
VITE_PERSIST_THEME={'true' if frontend_config['ui']['persist_theme'] else 'false'}
VITE_DEFAULT_LOCALE={frontend_config['ui']['default_locale']}

# Polling & Real-time Configuration
VITE_JOB_POLLING_INTERVAL={frontend_config['polling']['job_status_interval']}
VITE_MAX_POLLING_ATTEMPTS={frontend_config['polling']['max_attempts']}
VITE_ENABLE_REALTIME={'true' if frontend_config['polling']['enable_realtime'] else 'false'}

# Caching Configuration
VITE_CACHE_DURATION={frontend_config['caching']['duration']}
VITE_ENABLE_SERVICE_WORKER={'true' if frontend_config['caching']['enable_service_worker'] else 'false'}

# Build Configuration
VITE_BUILD_TARGET={frontend_config['build']['target']}
VITE_BUILD_SOURCEMAP={'true' if frontend_config['build']['sourcemap'].get(environment, False) else 'false'}
VITE_ANALYZE_BUNDLE={'true' if frontend_config['build']['analyze_bundle'] else 'false'}
VITE_PUBLIC_PATH=/

# Development Configuration
VITE_DEV_PORT={frontend_config['dev']['port']}
VITE_HMR={'true' if frontend_config['dev']['hmr'] else 'false'}
VITE_OPEN_BROWSER={'true' if frontend_config['dev']['open_browser'] and environment == 'development' else 'false'}
VITE_HTTPS={'true' if frontend_config['dev']['https'] else 'false'}

# Security Configuration
VITE_CSP_ENABLED=false
"""
    return content

def generate_do_app_yaml(config: Dict[str, Any]) -> str:
    """Generate .do/app.yaml file for Digital Ocean deployment."""
    deployment_config = config['deployment']['digital_ocean']
    ai_config = config['ai_providers']
    prod_env = config['environments']['production']
    auth_config = config['auth']
    jobs_config = config['jobs']
    cors_config = config['cors']
    logging_config = config['logging']
    
    cors_origins = ','.join(prod_env['cors_origins'])
    trusted_hosts = ','.join(auth_config['trusted_hosts'])
    
    content = f"""# =============================================================================
# Digital Ocean App Platform Configuration
# =============================================================================
# Auto-generated from config.yaml - DO NOT EDIT MANUALLY
# Run: python scripts/generate_config.py production
# =============================================================================

name: {deployment_config['app_name']}
region: {deployment_config['region']}
# Temporarily commented out custom domain due to SSL certificate issues
# domains:
# - domain: {deployment_config['domain']}
#   type: PRIMARY
#   wildcard: false
#   zone: {deployment_config['domain']}

# Ingress configuration for routing
ingress:
  rules:
  - match:
      path:
        prefix: /api/
    component:
      name: backend
  - match:
      path:
        prefix: /
    component:
      name: frontend

services:
- name: backend
  source_dir: /backend
  github:
    repo: {deployment_config['repository']['url']}
    branch: {deployment_config['repository']['branch']}
    deploy_on_push: {'true' if deployment_config['repository']['deploy_on_push'] else 'false'}
  run_command: python -m uvicorn main:app --host 0.0.0.0 --port $PORT
  environment_slug: python
  instance_count: 1
  instance_size_slug: {deployment_config['backend_instance']}
  health_check:
    http_path: {deployment_config['health_check']['path']}
    initial_delay_seconds: {deployment_config['health_check']['initial_delay']}
    period_seconds: {deployment_config['health_check']['period']}
    timeout_seconds: {deployment_config['health_check']['timeout']}
    success_threshold: {deployment_config['health_check']['success_threshold']}
    failure_threshold: {deployment_config['health_check']['failure_threshold']}
  http_port: 8080
  envs:
  # Application Configuration
  - key: APP_NAME
    value: "{config['project']['name']} API"
  - key: APP_VERSION
    value: "{config['project']['version']}"
  - key: ENVIRONMENT
    value: "production"
  - key: DEBUG
    value: "false"
  - key: HOST
    value: "0.0.0.0"
  - key: PORT
    value: "8080"
  
  # Database Configuration (Supabase)
  - key: SUPABASE_URL
    value: "{config['database']['supabase_url']}"
    type: SECRET
  - key: SUPABASE_KEY
    value: "{config['database']['supabase_anon_key']}"
    type: SECRET
  - key: SUPABASE_SERVICE_KEY
    value: "{config['database']['supabase_service_key']}"
    type: SECRET
  
  # Authentication Configuration
  - key: JWT_SECRET
    value: "{auth_config['jwt_secret']}"
    type: SECRET
  - key: JWT_ALGORITHM
    value: "{auth_config['jwt_algorithm']}"
  - key: ACCESS_TOKEN_EXPIRE_MINUTES
    value: "{auth_config['access_token_expire_minutes']}"
  
  # Google AI Configuration
  - key: GOOGLE_API_KEY
    value: "{ai_config['google']['api_key']}"
    type: SECRET
  - key: GOOGLE_DEFAULT_MODEL
    value: "{ai_config['google']['default_model']}"
  - key: GOOGLE_GENAI_USE_VERTEXAI
    value: "{'TRUE' if ai_config['google']['use_vertex_ai'] else 'FALSE'}"
  
  # OpenAI Configuration
  - key: OPENAI_API_KEY
    value: "{ai_config['openai']['api_key']}"
    type: SECRET
  - key: OPENAI_DEFAULT_MODEL
    value: "{ai_config['openai']['default_model']}"
  
  # Anthropic Configuration
  - key: ANTHROPIC_API_KEY
    value: "{ai_config['anthropic']['api_key']}"
    type: SECRET
  - key: ANTHROPIC_DEFAULT_MODEL
    value: "{ai_config['anthropic']['default_model']}"
  
  # Grok Configuration
  - key: GROK_API_KEY
    value: "{ai_config['grok']['api_key']}"
    type: SECRET
  - key: GROK_DEFAULT_MODEL
    value: "{ai_config['grok']['default_model']}"
  
  # DeepSeek Configuration
  - key: DEEPSEEK_API_KEY
    value: "{ai_config['deepseek']['api_key']}"
    type: SECRET
  - key: DEEPSEEK_DEFAULT_MODEL
    value: "{ai_config['deepseek']['default_model']}"
  
  # Meta Llama Configuration
  - key: LLAMA_API_KEY
    value: "{ai_config['llama']['api_key']}"
    type: SECRET
  - key: LLAMA_DEFAULT_MODEL
    value: "{ai_config['llama']['default_model']}"
  
  # CORS Configuration
  - key: ALLOWED_ORIGINS
    value: "{cors_origins}"
  - key: CORS_ALLOW_CREDENTIALS
    value: "{'true' if cors_config['allow_credentials'] else 'false'}"
  - key: CORS_MAX_AGE
    value: "{cors_config['max_age']}"
  
  # Logging Configuration
  - key: LOG_LEVEL
    value: "{logging_config['level']}"
  - key: LOG_FORMAT
    value: "{logging_config['format']}"
  - key: LOG_ROTATION
    value: "{'true' if logging_config['rotation'] else 'false'}"
  - key: LOG_MAX_SIZE
    value: "{logging_config['max_size']}"
  - key: LOG_BACKUP_COUNT
    value: "{logging_config['backup_count']}"
  
  # Performance and Resource Configuration
  - key: MAX_CONCURRENT_JOBS
    value: "{jobs_config['max_concurrent']}"
  - key: DEFAULT_AGENT_TIMEOUT
    value: "{jobs_config['default_agent_timeout']}"
  - key: JOB_TIMEOUT
    value: "{jobs_config['timeout']}"
  - key: JOB_RETRY_ATTEMPTS
    value: "{jobs_config['retry_attempts']}"
  - key: JOB_QUEUE_MAX_SIZE
    value: "{jobs_config['queue_max_size']}"
  - key: CLEANUP_COMPLETED_JOBS_AFTER
    value: "{jobs_config['cleanup_after_seconds']}"
  
  # Security Configuration
  - key: API_RATE_LIMIT
    value: "{auth_config['api_rate_limit']}"
  - key: TRUSTED_HOSTS
    value: "{trusted_hosts}"
  - key: SECURE_COOKIES
    value: "true"
  - key: MAX_REQUEST_SIZE
    value: "{auth_config['max_request_size']}"

static_sites:
- name: frontend
  source_dir: /frontend
  github:
    repo: {deployment_config['repository']['url']}
    branch: {deployment_config['repository']['branch']}
    deploy_on_push: {'true' if deployment_config['repository']['deploy_on_push'] else 'false'}
  build_command: npm run build
  output_dir: /dist
  environment_slug: node-js
  envs:
  # Frontend Configuration
  - key: NODE_ENV
    value: "production"
  - key: VITE_API_BASE_URL
    value: "{prod_env['api_base_url']}"
  - key: VITE_SUPABASE_URL
    value: "{config['database']['supabase_url']}"
    type: SECRET
  - key: VITE_SUPABASE_ANON_KEY
    value: "{config['database']['supabase_anon_key']}"
    type: SECRET
"""
    return content

def write_file(path: Path, content: str, dry_run: bool = False) -> None:
    """Write content to file."""
    if dry_run:
        print(f"📝 Would write to: {path}")
        return
    
    # Create directory if it doesn't exist
    path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(path, 'w') as f:
        f.write(content)
    
    print(f"✅ Generated: {path}")

def main():
    """Main function."""
    parser = argparse.ArgumentParser(description='Generate configuration files from config.yaml')
    parser.add_argument('environment', nargs='?', default='development', 
                       choices=['development', 'production'],
                       help='Environment to generate config for (default: development)')
    parser.add_argument('--dry-run', action='store_true', 
                       help='Show what would be generated without writing files')
    
    args = parser.parse_args()
    
    # Get project root (one level up from scripts directory)
    script_dir = Path(__file__).parent
    project_root = script_dir.parent
    config_path = project_root / 'config.yaml'
    
    print(f"🔧 Generating configuration for {args.environment} environment...")
    print(f"📂 Project root: {project_root}")
    print(f"📄 Config file: {config_path}")
    
    # Load configuration
    config = load_config(config_path)
    
    # Generate files
    files_to_generate = [
        (project_root / '.env', generate_root_env(config, args.environment)),
        (project_root / 'backend' / '.env', generate_backend_env(config, args.environment)),
        (project_root / 'frontend' / '.env.local', generate_frontend_env(config, args.environment)),
    ]
    
    # Always generate the DO app.yaml for production deployment
    files_to_generate.append(
        (project_root / '.do' / 'app.yaml', generate_do_app_yaml(config))
    )
    
    # Write all files
    for file_path, content in files_to_generate:
        write_file(file_path, content, args.dry_run)
    
    if not args.dry_run:
        print(f"\n🎉 Configuration generation complete for {args.environment} environment!")
        print("\n📋 Generated files:")
        for file_path, _ in files_to_generate:
            print(f"   - {file_path}")
    else:
        print(f"\n🎯 Dry run complete - {len(files_to_generate)} files would be generated")

if __name__ == '__main__':
    main() 