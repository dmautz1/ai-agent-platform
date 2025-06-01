# Scripts

> **Deployment automation** - Quick setup guide for deployment scripts

## Quick Setup

```bash
# Install DigitalOcean CLI
brew install doctl  # macOS
# or snap install doctl  # Linux

# Authenticate
doctl auth init

# Deploy to production
./scripts/deploy.sh deploy --env production --domain yourdomain.com
```

## Scripts Available

- **`deploy.sh`** - Automated DigitalOcean App Platform deployment

## Documentation

For complete deployment script documentation, see:

**[Deployment Scripts Guide](../docs/deployment/deployment-scripts.md)** - Complete usage, options, and troubleshooting 