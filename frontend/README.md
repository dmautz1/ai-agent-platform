# Frontend

> **React TypeScript frontend** - Modern web interface for AI agent management

## Quick Setup

```bash
# Install dependencies
npm install

# Start development server
npm run dev

# Build for production
npm run build
```

## Scripts

```bash
npm run dev                    # Development server (http://localhost:5173)
npm run build                  # Production build
npm run test                   # Run all tests
npm run test:unit              # Unit tests only
npm run test:integration       # Integration tests only
npm run test:watch             # Watch mode
npm run lint                   # Lint code
npm run create-admin           # Create admin user
```

## Environment Setup

Copy the environment template:
```bash
cp env.local.example .env.local
```

Add your configuration:
```bash
VITE_SUPABASE_URL=your-supabase-url
VITE_SUPABASE_ANON_KEY=your-supabase-anon-key
VITE_API_URL=http://localhost:8000
```

## Documentation

For complete setup and development guides, see:

- **[Complete Documentation](../docs/README.md)** - Full documentation hub
- **[Quick Start Guide](../docs/getting-started/quick-start.md)** - 15-minute setup
- **[Environment Setup](../docs/getting-started/environment-setup.md)** - Detailed configuration
- **[Authentication Guide](../docs/integrations/authentication.md)** - User management
- **[Testing Guide](../docs/development/testing.md)** - Testing strategy
