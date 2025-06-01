# Environment Setup Guide

> **Complete Guide to Environment Configuration** - Step-by-step setup for junior developers

This guide walks you through setting up all environment variables needed for the AI Agent Template. Follow these steps in order for a successful setup.

## Table of Contents

- [Overview](#overview)
- [Quick Setup Checklist](#quick-setup-checklist)
- [Step-by-Step Setup](#step-by-step-setup)
- [Environment Files](#environment-files)
- [Troubleshooting](#troubleshooting)
- [Security Best Practices](#security-best-practices)
- [Different Environments](#different-environments)

## Overview

The AI Agent Template uses environment variables to configure:

- **Database**: Supabase for data storage and authentication
- **AI Services**: Google AI for agent functionality
- **Security**: JWT tokens and API keys
- **Application**: Server settings and feature flags

**Required vs Optional Variables:**
- ✅ **Required**: Must be set for the app to work
- 🔧 **Optional**: Have defaults but can be customized
- 🚨 **Secret**: Never share or commit these values

## Quick Setup Checklist

Before starting, make sure you have:

- [ ] DigitalOcean account (for deployment)
- [ ] Supabase account
- [ ] Google AI Studio account (or Google Cloud)
- [ ] GitHub repository (for deployment)
- [ ] Code editor
- [ ] Terminal/command line access

**Estimated Setup Time**: 20-30 minutes

## Step-by-Step Setup

### Step 1: Create Environment Files

First, create the environment files from templates:

```bash
# Backend environment file
cp backend/env.example backend/.env

# Frontend environment file  
cp frontend/env.local.example frontend/.env.local

# Or if using the project root
cp backend/env.example .env
```

**Important**: The `.env` files are automatically ignored by Git and will not be committed.

### Step 2: Set Up Supabase Database

#### 2.1 Create Supabase Project

1. Go to [supabase.com](https://supabase.com)
2. Sign up or log in
3. Click **"New Project"**
4. Choose your organization
5. Enter project details:
   - **Name**: `ai-agent-template` (or your preferred name)
   - **Database Password**: Generate a strong password
   - **Region**: Choose closest to your users
6. Click **"Create new project"**
7. Wait 2-3 minutes for project creation

#### 2.2 Get Supabase Credentials

Once your project is ready:

1. Go to **Settings** → **API**
2. Copy the following values:

```bash
# Project URL
SUPABASE_URL=https://your-project-id.supabase.co

# Anon (public) key - safe for frontend
SUPABASE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...

# Service role key - keep secret!
SUPABASE_SERVICE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

#### 2.3 Run Database Migrations

Set up the database tables:

1. In Supabase dashboard, go to **SQL Editor**
2. Copy content from `supabase/migrations/001_create_jobs_table.sql`
3. Paste and run the SQL
4. Copy content from `supabase/migrations/002_update_jobs_table_schema.sql`
5. Paste and run the SQL

**Verification**: Go to **Table Editor** and verify you see the `jobs` table.

### Step 3: Set Up Google AI

#### 3.1 Create Google AI Studio Account

1. Go to [Google AI Studio](https://aistudio.google.com)
2. Sign in with your Google account
3. Accept the terms of service

#### 3.2 Generate API Key

1. Click **"Get API Key"** in the top menu
2. Click **"Create API Key"**
3. Choose **"Create API key in new project"** (recommended)
4. Copy the generated API key

```bash
# Google AI API key
GOOGLE_API_KEY=AIzaSyBxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

**Security Note**: This key gives access to Google AI services. Keep it secret!

#### 3.3 Test API Access (Optional)

Test your API key in Google AI Studio:
1. Go to the **Prompt** section
2. Try a simple prompt like "Hello, world!"
3. Verify you get a response

### Step 4: Generate Security Keys

#### 4.1 Generate JWT Secret

The JWT secret secures user sessions. Generate a strong random key:

**Option A - Using OpenSSL (Recommended)**:
```bash
openssl rand -base64 32
```

**Option B - Using Node.js**:
```bash
node -e "console.log(require('crypto').randomBytes(32).toString('base64'))"
```

**Option C - Using Online Generator**:
Go to [passwordsgenerator.net](https://passwordsgenerator.net/) and generate a 32+ character password.

```bash
# Use the generated value
JWT_SECRET=your-generated-32-character-secret
```

### Step 5: Configure Backend Environment

Edit `backend/.env` (or `.env` in project root):

```bash
# =============================================================================
# REQUIRED VARIABLES - Set these first
# =============================================================================

# Environment
ENVIRONMENT=development
DEBUG=true

# Database (from Step 2)
SUPABASE_URL=https://your-project-id.supabase.co
SUPABASE_KEY=your-supabase-anon-key
SUPABASE_SERVICE_KEY=your-supabase-service-key

# AI Services (from Step 3)
GOOGLE_API_KEY=your-google-ai-api-key

# Security (from Step 4)
JWT_SECRET=your-generated-jwt-secret

# =============================================================================
# OPTIONAL VARIABLES - Can customize later
# =============================================================================

# Server settings
HOST=0.0.0.0
PORT=8000

# Job processing
MAX_CONCURRENT_JOBS=10
JOB_TIMEOUT=3600

# CORS (add your frontend URL)
ALLOWED_ORIGINS=http://localhost:3000,http://localhost:5173

# GitHub (for deployment)
GITHUB_REPO=your-username/ai-agent-template
```

### Step 6: Configure Frontend Environment

Edit `frontend/.env.local`:

```bash
# =============================================================================
# REQUIRED VARIABLES
# =============================================================================

# API connection
VITE_API_BASE_URL=http://localhost:8000

# Database (same as backend, but only anon key)
VITE_SUPABASE_URL=https://your-project-id.supabase.co
VITE_SUPABASE_ANON_KEY=your-supabase-anon-key

# =============================================================================
# OPTIONAL VARIABLES
# =============================================================================

# Development settings
NODE_ENV=development
VITE_API_DEBUG=true

# UI settings
VITE_DEFAULT_THEME=system
VITE_JOB_POLLING_INTERVAL=5000
```

### Step 7: Test Configuration

#### 7.1 Test Backend

```bash
# Navigate to backend directory
cd backend

# Install dependencies (if not done)
pip install -r requirements.txt

# Test configuration
python -c "
from config.environment import get_settings
settings = get_settings()
print('✅ Backend configuration loaded successfully')
print(f'Environment: {settings.environment}')
print(f'Supabase URL: {settings.supabase_url}')
"
```

#### 7.2 Test Frontend

```bash
# Navigate to frontend directory
cd frontend

# Install dependencies (if not done)
npm install

# Test configuration
npm run dev
```

Check the browser console for any environment variable errors.

#### 7.3 Run Full Application

```bash
# Terminal 1 - Backend
cd backend
python main.py

# Terminal 2 - Frontend  
cd frontend
npm run dev
```

**Success Indicators**:
- Backend starts without errors on port 8000
- Frontend starts without errors on port 3000
- You can access http://localhost:3000
- No console errors related to environment variables

## Environment Files

### File Locations and Purposes

| File | Purpose | Contains |
|------|---------|----------|
| `backend/.env` | Backend configuration | Database, AI keys, server settings |
| `frontend/.env.local` | Frontend configuration | API URLs, client-safe keys only |
| `backend/test_config_example.env` | Testing configuration | Test database settings |

### Variable Naming Conventions

- **Backend**: Standard names (`SUPABASE_URL`, `GOOGLE_API_KEY`)
- **Frontend**: Must use `VITE_` prefix (`VITE_API_BASE_URL`)
- **Secrets**: Use `_KEY` or `_SECRET` suffix
- **URLs**: Use `_URL` suffix

### Loading Order

**Backend** (Python/FastAPI):
1. `.env` file in backend directory
2. System environment variables
3. Default values

**Frontend** (Vite):
1. `.env.local` (highest priority)
2. `.env.development` (in dev mode)
3. `.env` (lowest priority)

## Troubleshooting

### Common Issues

#### 1. "Supabase URL must start with https://"

**Error**: Configuration validation fails
**Solution**: Ensure your Supabase URL is complete:
```bash
# ❌ Wrong
SUPABASE_URL=xyzabc123.supabase.co

# ✅ Correct  
SUPABASE_URL=https://xyzabc123.supabase.co
```

#### 2. "Failed to authenticate with Supabase"

**Causes**:
- Wrong anon key
- Wrong service key
- Incorrect project URL

**Solution**:
1. Double-check keys in Supabase dashboard: **Settings** → **API**
2. Ensure no extra spaces or characters
3. Verify project URL matches exactly

#### 3. "Google AI API key invalid"

**Causes**:
- API key not properly copied
- API key not activated
- Billing not enabled (for some features)

**Solution**:
1. Regenerate API key in Google AI Studio
2. Test in Google AI Studio first
3. Check for any API restrictions

#### 4. "Environment variables not loading"

**Frontend Issues**:
- Variables must start with `VITE_`
- File must be named `.env.local`
- Restart dev server after changes

**Backend Issues**:
- Check file is named `.env`
- Verify file is in correct directory
- No spaces around `=` in variable definitions

#### 5. "CORS errors in browser"

**Solution**: Update `ALLOWED_ORIGINS` in backend `.env`:
```bash
ALLOWED_ORIGINS=http://localhost:3000,http://localhost:5173,http://127.0.0.1:3000
```

### Debugging Commands

**Check if environment variables are loaded**:

```bash
# Backend
cd backend
python -c "import os; print('SUPABASE_URL:', os.getenv('SUPABASE_URL'))"

# Frontend (in browser console)
console.log('API URL:', import.meta.env.VITE_API_BASE_URL);
```

**Validate configuration**:

```bash
# Use deployment script
./scripts/deploy.sh validate

# Or manual validation
cd backend
python -c "
from config.environment import validate_required_settings
validate_required_settings()
print('✅ All required settings are valid')
"
```

## Security Best Practices

### 🚨 Critical Security Rules

1. **Never commit `.env` files** to version control
2. **Use different keys** for development, staging, and production
3. **Rotate keys regularly** in production
4. **Use strong JWT secrets** (32+ characters)
5. **Limit API key permissions** where possible

### Production Security

**Environment Variables**:
- Use a secrets management service (AWS Secrets Manager, etc.)
- Set environment variables through deployment platform
- Never hardcode secrets in code

**API Keys**:
- Use separate API keys for production
- Enable API key restrictions (IP, domain)
- Monitor API usage for anomalies

**Database**:
- Use Row Level Security (RLS) in Supabase
- Separate databases for different environments
- Regular security updates

### Development Security

**Local Development**:
- Use `.env.local` for frontend (ignored by Git)
- Keep test keys separate from production
- Don't share `.env` files via email/chat

**Team Development**:
- Use shared test/development databases
- Document required environment variables
- Provide example values without real secrets

## Different Environments

### Development Environment

**Purpose**: Local development and testing

```bash
# Backend (.env)
ENVIRONMENT=development
DEBUG=true
SUPABASE_URL=https://dev-project.supabase.co
ALLOWED_ORIGINS=http://localhost:3000,http://localhost:5173

# Frontend (.env.local)
VITE_API_BASE_URL=http://localhost:8000
VITE_API_DEBUG=true
```

### Staging Environment

**Purpose**: Testing before production

```bash
# Backend
ENVIRONMENT=staging
DEBUG=false
SUPABASE_URL=https://staging-project.supabase.co
ALLOWED_ORIGINS=https://staging.yourdomain.com

# Frontend
VITE_API_BASE_URL=https://staging-api.yourdomain.com
VITE_API_DEBUG=false
```

### Production Environment

**Purpose**: Live application

```bash
# Backend
ENVIRONMENT=production
DEBUG=false
SUPABASE_URL=https://prod-project.supabase.co
ALLOWED_ORIGINS=https://yourdomain.com,https://www.yourdomain.com
TRUSTED_HOSTS=yourdomain.com,www.yourdomain.com
SECURE_COOKIES=true

# Frontend  
VITE_API_BASE_URL=https://yourdomain.com
VITE_API_DEBUG=false
VITE_ENABLE_ANALYTICS=true
```

### Environment-Specific Best Practices

| Environment | Database | API Keys | Logging | Security |
|-------------|----------|----------|---------|----------|
| Development | Shared test DB | Development keys | Debug level | Relaxed CORS |
| Staging | Staging DB | Staging keys | Info level | Production-like |
| Production | Production DB | Production keys | Warning level | Full security |

## Next Steps

After completing this setup:

1. **Test the Application**: Run both backend and frontend
2. **Create Your First User**: Use the admin creation script
3. **Deploy to Staging**: Test the deployment process  
4. **Set Up Monitoring**: Configure logging and alerts
5. **Production Deployment**: Deploy with production environment variables

## Getting Help

If you encounter issues:

1. **Check this guide**: Most common issues are covered
2. **Use the deployment script**: `./scripts/deploy.sh validate`
3. **Check logs**: Look for specific error messages
4. **Verify prerequisites**: Ensure all accounts are set up
5. **Test components individually**: Backend, then frontend
6. **Compare with examples**: Use the example values as reference

For additional help:
- [API Documentation](API_DOCUMENTATION.md)
- [Deployment Guide](DEPLOYMENT_GUIDE.md)
- [Troubleshooting Guide](README.md#troubleshooting)

---

**Remember**: Environment setup is crucial for security and functionality. Take time to understand each variable rather than just copying values. 