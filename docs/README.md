# AI Agent Platform Documentation

> **Complete documentation for AI Agent Platform** - Your comprehensive guide to building, deploying, and scaling AI agent applications

Welcome to the AI Agent Platform documentation! This platform provides a complete solution for creating, managing, and deploying AI-powered agents with support for multiple AI providers.

## 📚 Getting Started

### Prerequisites
- **Node.js 20+** - JavaScript runtime and package manager
- **Python 3.8+** - Backend development language
- **Supabase account** - Database and authentication service
- **AI Provider account** - Choose from 6 supported providers

### Quick Links
- **[30-Minute Quick Start](getting-started/quick-start.md)** - Get running immediately
- **[Environment Setup Guide](getting-started/environment-setup.md)** - Complete configuration
- **[Troubleshooting Guide](getting-started/troubleshooting.md)** - Common issues and fixes

## 🚀 Core Features

### Agent Framework
- **Self-Contained Architecture** - Each agent includes models, endpoints, and logic
- **Automatic Discovery** - Drop Python files in `agents/`, they're auto-registered
- **Type-Safe Development** - Full Pydantic validation for inputs and outputs
- **Dynamic Form Generation** - Frontend automatically creates forms from schemas

### Multi-Provider AI Support
- **6 AI Providers** - Google AI, OpenAI, Anthropic, Grok, DeepSeek, Meta Llama
- **Intelligent Fallbacks** - Automatic provider switching on failures
- **Cost Optimization** - Smart provider selection based on requirements
- **Unified Interface** - Single API for all providers

### Production Ready
- **Real-Time Updates** - Live job status without page refresh
- **Secure Authentication** - Supabase Auth with JWT tokens  
- **Comprehensive Testing** - 95.3% backend, 98.6% frontend test coverage
- **Deployment Ready** - Docker, DigitalOcean, Vercel support

## 🤖 AI Provider Integration

### Primary Providers

| Provider | Documentation | Best For | Pricing |
|----------|---------------|----------|---------|
| **Google AI** | [Setup Guide](integrations/google-ai.md) | General purpose, free tier | Free → $0.075/1M tokens |
| **OpenAI** | [Setup Guide](integrations/openai.md) | Industry standard, GPT models | $0.50-$20/1M tokens |
| **Anthropic** | [Setup Guide](integrations/anthropic.md) | Advanced reasoning, large context | $3-$75/1M tokens |

### Specialized Providers

| Provider | Documentation | Best For | Pricing |
|----------|---------------|----------|---------|
| **Grok** | [Setup Guide](integrations/grok.md) | Real-time data, current events | Subscription-based |
| **DeepSeek** | [Setup Guide](integrations/deepseek.md) | Cost-effective, bulk processing | $0.14-$0.28/1M tokens |
| **Meta Llama** | [Setup Guide](integrations/meta-llama.md) | Open-source, customizable | $0.20-$0.90/1M tokens |

### Multi-Provider Setup
- **[Multi-Provider Guide](integrations/ai-providers.md)** - Configure multiple providers
- **[Provider Selection](integrations/additional-providers.md)** - Choose the right provider for your needs

## 📖 Development Guides

### Backend Development
- **[Agent Creation](development/creating-agents.md)** - Build custom agents
- **[Database Operations](development/database-guide.md)** - Work with Supabase
- **[API Development](development/api-development.md)** - Extend the API
- **[Testing Guide](development/testing.md)** - Write comprehensive tests

### Frontend Development  
- **[Component Development](development/frontend-development.md)** - Build UI components
- **[State Management](development/state-management.md)** - Handle application state
- **[Form Development](development/forms.md)** - Create dynamic forms

### Architecture
- **[Platform Architecture](architecture/agent-architecture.md)** - Understanding the dual-agent system  
- **[System Architecture](architecture/system-overview.md)** - High-level system design
- **[Agent Framework](architecture/agent-platform.md)** - Agent system architecture
- **[Job Processing](architecture/job-result-handling.md)** - Job execution and results
- **[Database Schema](architecture/database-schema.md)** - Database design

## 🚀 Deployment

### Deployment Options
- **[DigitalOcean](deployment/digitalocean.md)** - Full-stack deployment
- **[Vercel + Railway](deployment/vercel-railway.md)** - Serverless option
- **[Docker](deployment/docker.md)** - Containerized deployment
- **[AWS](deployment/aws.md)** - Enterprise deployment

### Deployment Guides
- **[Complete Deployment Guide](deployment/deployment-guide.md)** - Step-by-step deployment
- **[Environment Variables](deployment/environment-variables.md)** - Production configuration
- **[Security](deployment/security.md)** - Security best practices

## ⚙️ Configuration

### Core Configuration
- **[Environment Variables](configuration/environment-variables.md)** - Complete variable reference
- **[Configuration Guide](configuration/README.md)** - Configuration overview
- **[Security Settings](configuration/security.md)** - Secure your application

### Provider Configuration
- **[AI Provider Settings](configuration/ai-providers.md)** - Configure AI providers
- **[Database Settings](configuration/database.md)** - Database configuration
- **[Authentication](configuration/authentication.md)** - Auth configuration

## 📊 Monitoring & Maintenance

### Monitoring
- **[Application Monitoring](monitoring/application.md)** - Monitor your application
- **[Performance Monitoring](monitoring/performance.md)** - Track performance metrics
- **[Error Tracking](monitoring/errors.md)** - Handle and track errors

### Maintenance
- **[Updates & Upgrades](maintenance/updates.md)** - Keep your platform current
- **[Backup & Recovery](maintenance/backup.md)** - Protect your data
- **[Scaling](maintenance/scaling.md)** - Scale your application

## 🔧 API Reference

### Backend API
- **[REST API](api/rest-api.md)** - Complete REST API reference
- **[Authentication](api/authentication.md)** - API authentication
- **[Error Handling](api/error-handling.md)** - API error responses

### Agent API
- **[Agent Framework API](api/agent-platform.md)** - Agent development API
- **[Job Management](api/job-management.md)** - Job execution API
- **[Provider Integration](api/provider-integration.md)** - AI provider API

## 🤝 Community & Support

### Getting Help
- **[GitHub Issues](https://github.com/dmautz1/ai-agent-platform/issues)** - Bug reports and feature requests
- **[GitHub Discussions](https://github.com/dmautz1/ai-agent-platform/discussions)** - Community Q&A
- **[Security Advisories](https://github.com/dmautz1/ai-agent-platform/security/advisories)** - Security reporting

### Contributing
- **[Contributing Guide](../CONTRIBUTING.md)** - How to contribute
- **[Code of Conduct](../CODE_OF_CONDUCT.md)** - Community standards
- **[Development Setup](development/development-setup.md)** - Set up for contributing

### Resources
- **[Examples](examples/)** - Example agents and use cases
- **[Tutorials](tutorials/)** - Step-by-step tutorials
- **[FAQ](faq.md)** - Frequently asked questions
- **[Changelog](../CHANGELOG.md)** - Version history

## 📋 Quick Reference

### Essential Commands
```bash
# Development setup
npm install && cd frontend && npm install && cd ../backend && pip install -r requirements.txt

# Start development
cd backend && python main.py  # Terminal 1
cd frontend && npm run dev     # Terminal 2

# Run tests
npm test                       # All tests
npm run test:backend          # Backend only
npm run test:frontend         # Frontend only
```

### Key Files
- `backend/.env` - Backend environment variables
- `frontend/.env.local` - Frontend environment variables
- `backend/agents/` - Custom agents directory
- `supabase/migrations/` - Database migrations

### Default Ports
- **Frontend**: http://localhost:5173 (Vite dev server)
- **Backend**: http://localhost:8000 (FastAPI server)
- **API Docs**: http://localhost:8000/docs (Swagger UI)

---

**Need help?** Check our [Troubleshooting Guide](getting-started/troubleshooting.md) or [create an issue](https://github.com/dmautz1/ai-agent-platform/issues/new/choose).