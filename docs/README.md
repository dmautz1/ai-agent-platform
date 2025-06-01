# AI Agent Template Documentation

> **Complete Documentation Hub** - Everything you need to build, deploy, and maintain AI agents

## 🚀 Getting Started

Perfect for developers new to the AI Agent Template:

- **[Quick Start Guide](getting-started/quick-start.md)** - Get running in 15 minutes
- **[Environment Setup](getting-started/environment-setup.md)** - Complete configuration guide
- **[Troubleshooting](getting-started/troubleshooting.md)** - Common issues and solutions

## 🔧 Development

For building custom agents and extending functionality:

- **[Agent Development](development/agent-development.md)** - Create custom AI agents
- **[API Reference](development/api-reference.md)** - Complete API documentation
- **[Testing Guide](development/testing.md)** - Testing strategy and commands
- **[Architecture Overview](development/architecture.md)** - System design and patterns

## 🚀 Deployment

Production deployment and DevOps:

- **[Deployment Guide](deployment/deployment-guide.md)** - Deploy to production
- **[DigitalOcean Setup](deployment/digitalocean.md)** - Platform-specific instructions
- **[Deployment Scripts](deployment/deployment-scripts.md)** - Automated deployment tools

## 🔌 Integrations

Third-party service integrations:

- **[Supabase Database](integrations/supabase.md)** - Database setup and management
- **[Google AI Services](integrations/google-ai.md)** - AI/ML service configuration
- **[Authentication](integrations/authentication.md)** - User management and security

## ⚙️ Configuration

Technical configuration references:

- **[Configuration Reference](configuration/README.md)** - All configuration files explained
- **[Environment Variables](configuration/environment-variables.md)** - Complete variable reference

## 📖 Quick Reference

### Essential Commands
```bash
# Start development
npm run dev                    # Start frontend
cd backend && python main.py  # Start backend

# Testing
npm test                       # Run all tests
npm run test:frontend         # Frontend tests only
npm run test:backend          # Backend tests only
npm run test:e2e              # End-to-end tests

# Deployment
npm run build                 # Build for production
./scripts/deploy.sh           # Deploy to DigitalOcean
```

### Key Directories
```
├── backend/           # Python FastAPI backend
├── frontend/          # React TypeScript frontend
├── e2e-tests/         # Playwright end-to-end tests
├── docs/              # Documentation (you are here)
└── scripts/           # Deployment and utility scripts
```

### Support Channels

- **GitHub Issues** - Bug reports and feature requests
- **Documentation Issues** - Use issues tagged with "documentation"
- **API Documentation** - Interactive docs at `http://localhost:8000/docs`

---

**Choose your path above to get started! 👆** 