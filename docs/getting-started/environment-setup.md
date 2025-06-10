# Environment Setup Guide

> **Complete Guide to Environment Configuration** - Step-by-step setup for junior developers

This guide walks you through setting up all environment variables needed for the AI Agent Platform. Follow these steps in order for a successful setup.

## Table of Contents

- [Overview](#overview)
- [Quick Setup Checklist](#quick-setup-checklist)
- [Step-by-Step Setup](#step-by-step-setup)
- [Environment Files](#environment-files)
- [Troubleshooting](#troubleshooting)
- [Security Best Practices](#security-best-practices)
- [Different Environments](#different-environments)

## Overview

The AI Agent Platform uses environment variables to configure:

- **Database**: Supabase for data storage and authentication
- **AI Services**: 6 supported AI providers for agent functionality
- **Security**: JWT tokens and API keys
- **Application**: Server settings and feature flags

**Required vs Optional Variables:**
- ✅ **Required**: Must be set for the app to work
- 🔧 **Optional**: Have defaults but can be customized
- 🚨 **Secret**: Never share or commit these values

## Quick Setup Checklist

Before starting, make sure you have accounts for:

- [ ] **Node.js 20+** - JavaScript runtime and package manager
- [ ] **Python 3.8+** - Backend development language  
- [ ] Supabase account (required)
- [ ] At least one AI provider account:
  - [ ] Google AI Studio (recommended - free tier)
  - [ ] OpenAI (industry standard - requires billing)
  - [ ] Anthropic (advanced reasoning - requires billing)
  - [ ] Grok/xAI (real-time data - subscription)
  - [ ] DeepSeek (cost-effective - free tier)
  - [ ] Meta Llama via Together AI (open-source - free tier)
- [ ] GitHub repository (for deployment)
- [ ] Code editor and terminal access

**Estimated Setup Time**: 30-45 minutes

## Step-by-Step Setup

### Step 1: Create Environment Files

First, create the environment files from templates:

```bash
# Backend environment file
cp backend/env.example backend/.env

# Frontend environment file  
cp frontend/env.local.example frontend/.env.local
```

### Step 2: Set Up Python Virtual Environment

Create and activate a Python virtual environment for the backend:

```bash
# Navigate to backend directory
cd backend

# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Linux/Mac:
source venv/bin/activate

# On Windows:
venv\Scripts\activate

# Your terminal prompt should now show (venv) at the beginning

# Install Python dependencies
pip install -r requirements.txt

# Return to project root
cd ..
```

**⚠️ Important**: Always activate the virtual environment before working with the backend:
```bash
cd backend
source venv/bin/activate  # Linux/Mac
# OR
venv\Scripts\activate  # Windows
```

### Step 3: Install Frontend Dependencies

```bash
# Install root dependencies (for testing)
npm install

# Install frontend dependencies
cd frontend
npm install
cd ..
```

### Step 4: Configure Supabase Database

#### 4.1 Create Supabase Account

1. Go to [supabase.com](https://supabase.com)
2. Sign up for free account
3. Create new project (takes 2-3 minutes)
4. Choose region closest to you

#### 4.2 Get Database Credentials

In your Supabase dashboard:

1. Go to **Settings** → **API**
2. Copy these values:
   - **Project URL** (starts with `https://`)
   - **anon public** key (for frontend)
   - **service_role secret** key (for backend)

#### 4.3 Configure Database Connection

Edit `backend/.env` and add:

```bash
# =============================================================================
# REQUIRED VARIABLES
# =============================================================================

# Database Configuration
SUPABASE_URL=https://your-project-id.supabase.co
SUPABASE_KEY=your-supabase-anon-key
SUPABASE_SERVICE_KEY=your-supabase-service-key

# Authentication
JWT_SECRET=your-32-character-secret-key-here
```

#### 4.4 Run Database Migrations

1. In Supabase dashboard, go to **SQL Editor**
2. Copy content from `supabase/migrations/supabase_setup.sql`
3. Paste and run the SQL

### Step 5: Configure AI Providers

Choose and configure at least one AI provider:

#### 5.1 Set Default Provider

Choose your preferred default AI provider by adding to `backend/.env`:

```bash
# Default LLM provider when none is specified
# Options: google|openai|anthropic|grok|deepseek|llama
DEFAULT_LLM_PROVIDER=google
```

**Provider Selection Guide:**
- **google** - Free tier, fast, good for development
- **openai** - Industry standard, reliable, moderate cost
- **anthropic** - Advanced reasoning, higher cost
- **grok** - Real-time data access, subscription-based
- **deepseek** - Most cost-effective, good performance  
- **llama** - Open-source flexibility, various providers

#### 5.2 Google AI (Recommended - Free Tier)

1. Go to [Google AI Studio](https://aistudio.google.com)
2. Create API key
3. Add to `backend/.env`:

```bash
# Google AI Configuration
GOOGLE_API_KEY=your-google-ai-api-key
```

#### 5.3 OpenAI (Industry Standard)

1. Go to [OpenAI Platform](https://platform.openai.com)
2. Create API key (requires billing setup)
3. Add to `backend/.env`:

```bash
# OpenAI Configuration
OPENAI_API_KEY=your-openai-api-key
```

#### 5.4 Additional Providers (Optional)

Add any of these providers for specialized capabilities:

```bash
# Anthropic (Advanced reasoning)
ANTHROPIC_API_KEY=your-anthropic-api-key

# Grok (Real-time data)
GROK_API_KEY=your-grok-api-key

# DeepSeek (Cost-effective)
DEEPSEEK_API_KEY=your-deepseek-api-key

# Meta Llama (Open-source)
LLAMA_API_KEY=your-llama-api-key
```

**Provider Setup Guides:**
- [Google AI Setup](../integrations/google-ai.md)
- [OpenAI Setup](../integrations/openai.md) 
- [Anthropic Setup](../integrations/anthropic.md)
- [Grok Setup](../integrations/grok.md)
- [DeepSeek Setup](../integrations/deepseek.md)
- [Meta Llama Setup](../integrations/meta-llama.md)

### Step 6: Complete Backend Configuration

Your complete `backend/.env` should look like this:

```bash
# =============================================================================
# REQUIRED VARIABLES
# =============================================================================

# Database Configuration
SUPABASE_URL=https://your-project-id.supabase.co
SUPABASE_KEY=your-supabase-anon-key
SUPABASE_SERVICE_KEY=your-supabase-service-key

# Authentication
JWT_SECRET=your-32-character-secret-key-here

# Default LLM Provider
DEFAULT_LLM_PROVIDER=google

# AI Providers (at least one required)
GOOGLE_API_KEY=your-google-ai-api-key
OPENAI_API_KEY=your-openai-api-key
ANTHROPIC_API_KEY=your-anthropic-api-key

# Additional AI Providers (optional)
GROK_API_KEY=your-grok-api-key
DEEPSEEK_API_KEY=your-deepseek-api-key
LLAMA_API_KEY=your-llama-api-key

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

# AI Provider Configuration
AI_FALLBACK_PROVIDERS=google,openai,anthropic  # Fallback order
GOOGLE_AI_MODEL=gemini-2.0-flash
OPENAI_MODEL=gpt-4-turbo-preview
ANTHROPIC_MODEL=claude-3-sonnet-20240229

# GitHub (for deployment)
GITHUB_REPO=your-username/ai-agent-platform
```

### Step 7: Configure Frontend Environment

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

### Step 8: Test Configuration

#### 8.1 Test Backend

```bash
# Navigate to backend directory
cd backend

# Activate virtual environment
source venv/bin/activate  # Linux/Mac
# OR venv\Scripts\activate  # Windows

# Test configuration
python -c "
from config.environment import get_settings
settings = get_settings()
print('✅ Backend configuration loaded successfully')
print(f'Environment: {settings.environment}')
print(f'Supabase URL: {settings.supabase_url}')
"
```

#### 8.2 Test Frontend

```bash
# Navigate to frontend directory
cd frontend

# Test configuration
npm run dev
```

Check the browser console for any environment variable errors.

#### 8.3 Run Full Application

```bash
# Terminal 1 - Backend (with venv activated)
cd backend
source venv/bin/activate  # Linux/Mac
# OR venv\Scripts\activate  # Windows
python main.py

# Terminal 2 - Frontend  
cd frontend
npm run dev
```

**Success Indicators**:
- Backend starts without errors on port 8000
- Frontend starts without errors on port 5173
- You can access http://localhost:5173
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
1. `.env`