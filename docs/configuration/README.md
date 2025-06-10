# Configuration Reference

> **All configuration files explained** - Complete reference for project configuration

## Configuration Overview

The AI Agent Platform uses multiple configuration files for different aspects of the system:

```
├── Root Level Configuration
│   ├── package.json                    # Root dependencies and scripts
│   ├── playwright.config.ts            # E2E testing configuration
│   └── .gitignore                      # Git ignore patterns
├── Frontend Configuration
│   ├── package.json                    # Frontend dependencies
│   ├── vite.config.ts                  # Build tool configuration
│   ├── vitest.config.ts                # Testing configuration
│   ├── tsconfig.*.json                 # TypeScript configuration
│   ├── eslint.config.js                # Linting rules
│   ├── components.json                 # UI component configuration
│   └── .env.local                      # Environment variables
├── Backend Configuration
│   ├── requirements.txt                # Python dependencies
│   ├── pytest.ini                     # Testing configuration
│   └── .env                           # Environment variables
└── Deployment Configuration
    └── .do/app.yaml                    # DigitalOcean deployment
```

## Root Level Configuration

### package.json
**Purpose**: Root-level dependencies and orchestration scripts

```json
{
  "name": "ai-agent-platform",
  "version": "1.0.0",
  "scripts": {
    "test": "npm run test:frontend && npm run test:backend && npm run test:e2e",
    "test:frontend": "cd frontend && npm run test",
    "test:backend": "cd backend && python -m pytest",
    "test:e2e": "playwright test"
  },
  "devDependencies": {
    "@playwright/test": "^1.52.0",
    "playwright": "^1.52.0"
  }
}
```

**Key sections**:
- `scripts`: Orchestration commands for the entire project
- `devDependencies`: Tools for testing and development

### playwright.config.ts
**Purpose**: End-to-end testing configuration

```typescript
export default defineConfig({
  testDir: './e2e-tests',
  fullyParallel: true,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 2 : 0,
  workers: process.env.CI ? 1 : undefined,
  reporter: 'html',
  use: {
    baseURL: 'http://localhost:5173',
    trace: 'on-first-retry',
  },
  projects: [
    { name: 'chromium', use: { ...devices['Desktop Chrome'] } },
    { name: 'firefox', use: { ...devices['Desktop Firefox'] } },
    { name: 'webkit', use: { ...devices['Desktop Safari'] } }
  ],
  webServer: {
    command: 'cd frontend && npm run dev',
    url: 'http://localhost:5173',
    reuseExistingServer: !process.env.CI,
  }
})
```

**Key sections**:
- `testDir`: Location of E2E test files
- `projects`: Browser configurations for cross-browser testing
- `webServer`: Automatic server startup for testing

## Frontend Configuration

### package.json
**Purpose**: Frontend dependencies and build scripts

```json
{
  "name": "frontend",
  "type": "module",
  "scripts": {
    "dev": "vite",
    "build": "tsc -b && vite build",
    "test": "vitest run",
    "test:unit": "vitest run src/test/",
    "test:integration": "vitest run tests/integration/"
  },
  "dependencies": {
    "react": "^19.1.0",
    "react-dom": "^19.1.0",
    "@supabase/supabase-js": "^2.49.8",
    "axios": "^1.9.0"
  },
  "devDependencies": {
    "@vitejs/plugin-react": "^4.4.1",
    "typescript": "~5.8.3",
    "vitest": "^3.1.4"
  }
}
```

**Key sections**:
- `scripts`: Build, development, and testing commands
- `dependencies`: Runtime dependencies for the React app
- `devDependencies`: Build tools and development utilities

### vite.config.ts
**Purpose**: Build tool and development server configuration

```typescript
export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      '@': '/src',
    },
  },
  server: {
    port: 5173,
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/api/, '')
      }
    }
  }
})
```

**Key sections**:
- `plugins`: Vite plugins for React support
- `resolve.alias`: Path aliases for imports
- `server.proxy`: API proxying for development

### vitest.config.ts
**Purpose**: Frontend testing configuration

```typescript
export default defineConfig({
  plugins: [react()],
  test: {
    globals: true,
    environment: 'jsdom',
    setupFiles: ['./src/test/setup.ts'],
    include: [
      'src/test/**/*.{test,spec}.{js,mjs,cjs,ts,mts,cts,jsx,tsx}',
      'tests/**/*.{test,spec}.{js,mjs,cjs,ts,mts,cts,jsx,tsx}'
    ]
  }
})
```

**Key sections**:
- `test.environment`: Testing environment (jsdom for React)
- `test.setupFiles`: Test setup and configuration
- `test.include`: Test file patterns

### TypeScript Configuration

#### tsconfig.json
**Purpose**: Main TypeScript configuration

```json
{
  "compilerOptions": {
    "target": "ES2020",
    "lib": ["ES2020", "DOM", "DOM.Iterable"],
    "module": "ESNext",
    "skipLibCheck": true,
    "moduleResolution": "bundler",
    "allowImportingTsExtensions": true,
    "resolveJsonModule": true,
    "isolatedModules": true,
    "noEmit": true,
    "jsx": "react-jsx",
    "strict": true,
    "noUnusedLocals": true,
    "noUnusedParameters": true,
    "noFallthroughCasesInSwitch": true,
    "baseUrl": ".",
    "paths": {
      "@/*": ["./src/*"]
    }
  },
  "include": ["src"],
  "references": [
    { "path": "./tsconfig.app.json" },
    { "path": "./tsconfig.node.json" }
  ]
}
```

#### tsconfig.app.json
**Purpose**: Application-specific TypeScript settings

```json
{
  "extends": "./tsconfig.json",
  "compilerOptions": {
    "composite": true,
    "tsBuildInfoFile": "./node_modules/.tmp/tsconfig.app.tsbuildinfo"
  },
  "include": ["src"]
}
```

### eslint.config.js
**Purpose**: Code linting and style enforcement

```javascript
export default [
  { ignores: ['dist'] },
  {
    extends: [eslint.configs.recommended, ...tseslint.configs.recommended],
    files: ['**/*.{ts,tsx}'],
    languageOptions: {
      ecmaVersion: 2020,
      globals: globals.browser,
    },
    plugins: {
      'react-hooks': reactHooks,
      'react-refresh': reactRefresh,
    },
    rules: {
      ...reactHooks.configs.recommended.rules,
      'react-refresh/only-export-components': ['warn', { allowConstantExport: true }],
    },
  },
]
```

### components.json
**Purpose**: shadcn/ui component configuration

```json
{
  "$schema": "https://ui.shadcn.com/schema.json",
  "style": "default",
  "rsc": false,
  "tsx": true,
  "tailwind": {
    "config": "tailwind.config.js",
    "css": "src/index.css",
    "baseColor": "slate",
    "cssVariables": true,
    "prefix": ""
  },
  "aliases": {
    "components": "@/components",
    "utils": "@/lib/utils"
  }
}
```

## Backend Configuration

### requirements.txt
**Purpose**: Python dependencies

```txt
fastapi==0.115.6
uvicorn==0.34.0
pydantic==2.10.4
supabase==2.10.0
google-generativeai==0.8.3
pytest==8.3.4
python-jose[cryptography]==3.3.0
python-multipart==0.0.20
requests==2.32.3
python-dotenv==1.0.1
```

**Categories**:
- **Web Framework**: FastAPI, Uvicorn
- **Data Validation**: Pydantic
- **Database**: Supabase client
- **AI Services**: Google Generative AI
- **Testing**: pytest
- **Authentication**: python-jose
- **Utilities**: requests, python-dotenv

### pytest.ini
**Purpose**: Python testing configuration

```ini
[tool:pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
addopts = -v --tb=short
markers =
    unit: Unit tests
    integration: Integration tests
    slow: Slow tests
```

**Key sections**:
- `testpaths`: Directory containing tests
- `python_*`: Test file and function naming patterns
- `addopts`: Default pytest options
- `markers`: Custom test markers for categorization

## Environment Configuration

### Backend Environment (.env)
**Purpose**: Backend environment variables

```bash
# Application Settings
ENVIRONMENT=development
DEBUG=true
HOST=0.0.0.0
PORT=8000

# Database Configuration
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-anon-key
SUPABASE_SERVICE_KEY=your-service-key

# Authentication
JWT_SECRET=your-32-character-secret

# AI Services
GOOGLE_API_KEY=your-google-ai-key
GOOGLE_AI_MODEL=gemini-1.5-flash

# CORS and Security
ALLOWED_ORIGINS=http://localhost:5173,http://localhost:3000

# Job Processing
MAX_CONCURRENT_JOBS=10
JOB_TIMEOUT=3600

# Logging
LOG_LEVEL=INFO
LOG_FORMAT=json
```

### Frontend Environment (.env.local)
**Purpose**: Frontend environment variables

```bash
# Supabase Configuration
VITE_SUPABASE_URL=https://your-project.supabase.co
VITE_SUPABASE_ANON_KEY=your-anon-key

# API Configuration
VITE_API_URL=http://localhost:8000

# Application Settings
VITE_APP_NAME=AI Agent Platform
VITE_APP_VERSION=1.0.0

# Feature Flags
VITE_ENABLE_ANALYTICS=false
VITE_ENABLE_DEBUG=true
```

## Deployment Configuration

### .do/app.yaml
**Purpose**: DigitalOcean App Platform deployment

```yaml
name: ai-agent-platform
services:
- name: backend
  source_dir: /backend
  github:
    repo: your-username/your-repo
    branch: main
  run_command: python main.py
  environment_slug: python
  instance_count: 1
  instance_size_slug: basic-xxs
  routes:
  - path: /
  envs:
  - key: ENVIRONMENT
    value: production
  - key: SUPABASE_URL
    value: ${SUPABASE_URL}
  - key: SUPABASE_SERVICE_KEY
    value: ${SUPABASE_SERVICE_KEY}

- name: frontend
  source_dir: /frontend
  github:
    repo: your-username/your-repo
    branch: main
  build_command: npm run build
  environment_slug: node-js
  instance_count: 1
  instance_size_slug: basic-xxs
  routes:
  - path: /
  envs:
  - key: VITE_SUPABASE_URL
    value: ${SUPABASE_URL}
  - key: VITE_SUPABASE_ANON_KEY
    value: ${SUPABASE_ANON_KEY}
```

## Configuration Best Practices

### Security Guidelines

1. **Never commit secrets** to version control
2. **Use environment variables** for all sensitive data
3. **Validate environment variables** at startup
4. **Use different configurations** for different environments
5. **Rotate secrets regularly** in production

### Environment Management

```bash
# Development
cp backend/env.example backend/.env
cp frontend/env.local.example frontend/.env.local

# Production
# Set environment variables in deployment platform
# Never store production secrets in files
```

### Configuration Validation

```python
# Backend configuration validation
import os
from typing import Optional

class Config:
    def __init__(self):
        self.supabase_url = self._get_required("SUPABASE_URL")
        self.supabase_key = self._get_required("SUPABASE_SERVICE_KEY")
        self.jwt_secret = self._get_required("JWT_SECRET")
        self.google_api_key = self._get_required("GOOGLE_API_KEY")
        
    def _get_required(self, key: str) -> str:
        value = os.getenv(key)
        if not value:
            raise ValueError(f"Required environment variable {key} not set")
        return value
```

### Configuration Documentation

- **Document all environment variables** with descriptions
- **Provide example configurations** for different environments
- **Explain configuration dependencies** between services
- **Include troubleshooting guides** for common configuration issues

---

**Next Steps**:
- **[Environment Variables Reference](environment-variables.md)** - Complete variable documentation
- **[Environment Setup Guide](../getting-started/environment-setup.md)** - Step-by-step configuration
- **[Deployment Guide](../deployment/deployment-guide.md)** - Production configuration 