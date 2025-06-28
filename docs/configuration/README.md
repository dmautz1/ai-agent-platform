# Configuration Guide

This document outlines the configuration files and settings used throughout the AI Agent Platform.

## Overview

The project uses multiple configuration files for different environments and components:

```
├── backend/
│   ├── .env                         # Backend environment variables
│   └── pytest.ini                  # Backend testing configuration
├── frontend/
│   ├── .env.local                   # Frontend environment variables
│   ├── jest.config.js               # Frontend testing configuration
│   ├── vite.config.ts               # Build configuration
│   └── tailwind.config.js           # Styling configuration
├── package.json                     # Project scripts and dependencies
└── .gitignore                       # Git ignore rules
```

## Core Configuration Files

### package.json
Main project configuration with npm scripts:

```json
{
  "scripts": {
    "test": "npm run test:frontend && npm run test:backend",
    "test:frontend": "npm run test --workspace=frontend",
    "test:backend": "cd backend && python -m pytest"
  },
  "devDependencies": {
    "@types/node": "^22.15.29",
    "autoprefixer": "^10.4.21",
    "postcss": "^8.5.4",
    "tailwindcss": "^4.1.8"
  }
}
```

## Environment Variables

### Backend (.env)
```env
# Database Configuration
SUPABASE_URL=your_supabase_url
SUPABASE_ANON_KEY=your_supabase_anon_key
SUPABASE_SERVICE_KEY=your_supabase_service_key

# AI Provider Configuration
OPENAI_API_KEY=your_openai_api_key
ANTHROPIC_API_KEY=your_anthropic_api_key
GOOGLE_AI_API_KEY=your_google_ai_api_key

# Security
JWT_SECRET=your_jwt_secret_key

# Application Settings
DEBUG=False
LOG_LEVEL=INFO
CORS_ORIGINS=http://localhost:3000,http://localhost:5173
```

### Frontend (.env.local)
```env
# API Configuration
VITE_API_BASE_URL=http://localhost:8000
VITE_SUPABASE_URL=your_supabase_url
VITE_SUPABASE_ANON_KEY=your_supabase_anon_key
```

## Testing Configuration

### Backend Testing (pytest.ini)
```ini
[tool:pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
addopts = 
    -v
    --tb=short
    --strict-markers
    --disable-warnings
    --asyncio-mode=auto
asyncio_mode = auto
```

### Frontend Testing (jest.config.js)
```javascript
module.exports = {
  preset: 'ts-jest',
  testEnvironment: 'jsdom',
  setupFilesAfterEnv: ['<rootDir>/src/setupTests.ts'],
  moduleNameMapping: {
    '^@/(.*)$': '<rootDir>/src/$1'
  },
  collectCoverageFrom: [
    'src/**/*.{ts,tsx}',
    '!src/**/*.d.ts'
  ]
};
```

## Build Configuration

### Vite Configuration (vite.config.ts)
```typescript
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import path from 'path'

export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src')
    }
  },
  server: {
    port: 3000,
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true
      }
    }
  }
})
```

## Configuration Best Practices

1. **Environment Separation**: Use different configuration files for development and production
2. **Secret Management**: Never commit sensitive data to version control
3. **Default Values**: Provide sensible defaults for optional configuration
4. **Validation**: Validate configuration on application startup
5. **Documentation**: Document all configuration options and their purposes

---

**Next Steps**:
- **[Environment Variables Reference](environment-variables.md)** - Complete variable documentation
- **[Environment Setup Guide](../getting-started/environment-setup.md)** - Step-by-step configuration
- **[Deployment Guide](../deployment/deployment-guide.md)** - Production configuration 