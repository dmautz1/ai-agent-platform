# Testing Guide

This document outlines the testing strategy and structure for the Agent Template application.

## Test Organization

The application follows a **distributed testing approach** that aligns with the monorepo structure:

```
├── e2e-tests/                    # End-to-end tests (Playwright)
│   ├── 01-authentication.spec.ts
│   ├── 02-job-workflow.spec.ts
│   ├── 03-mobile-workflow.spec.ts
│   ├── 04-api-authentication.spec.ts
│   ├── 05-agent-api-security.spec.ts
│   ├── 06-cross-browser-compatibility.spec.ts
│   ├── helpers/
│   └── fixtures/
├── frontend/
│   ├── src/test/                 # Unit & Component tests
│   │   ├── setup.ts             # Test environment setup
│   │   ├── utils.tsx            # Test utilities
│   │   ├── components/          # Component tests
│   │   ├── contexts/            # Context tests
│   │   ├── lib/                 # Library function tests
│   │   └── pages/               # Page component tests
│   └── tests/
│       └── integration/         # Frontend integration tests
│           ├── api-communication.test.ts
│           ├── api-error-scenarios.test.ts
│           └── polling-validation-simplified.test.ts
└── backend/
    └── tests/
        ├── unit/                # Backend unit tests
        ├── integration/         # Backend integration tests
        └── agents/              # Agent-specific tests
```

## Test Types

### 1. Unit Tests
- **Frontend**: Component and utility function tests in `frontend/src/test/`
- **Backend**: Function and class tests in `backend/tests/unit/`
- **Purpose**: Test individual components/functions in isolation
- **Tools**: Vitest (frontend), pytest (backend)

### 2. Integration Tests
- **Frontend**: API communication tests in `frontend/tests/integration/`
- **Backend**: Database and service integration tests in `backend/tests/integration/`
- **Purpose**: Test component interactions and external service integrations
- **Tools**: Vitest (frontend), pytest (backend)

### 3. End-to-End Tests
- **Location**: `e2e-tests/`
- **Purpose**: Test complete user workflows across the entire application
- **Tools**: Playwright

## Available Commands

### Root Level Commands

Run all tests:
```bash
npm test
```

Run specific test suites:
```bash
npm run test:frontend          # All frontend tests
npm run test:backend           # All backend tests
npm run test:e2e              # End-to-end tests
```

Granular frontend testing:
```bash
npm run test:frontend:unit        # Component/unit tests only
npm run test:frontend:integration # Frontend integration tests only
npm run test:frontend:watch       # Watch mode for development
```

Granular backend testing:
```bash
npm run test:backend:unit         # Backend unit tests only
npm run test:backend:integration  # Backend integration tests only
npm run test:backend:agents       # Agent-specific tests only
npm run test:backend:coverage     # Run with coverage report
```

Granular e2e testing:
```bash
npm run test:e2e:ui              # Run with Playwright UI
npm run test:e2e:headed          # Run in headed browser mode
npm run test:e2e:debug           # Run in debug mode
npm run test:e2e:report          # Show test report
```

Specific e2e test suites:
```bash
npm run e2e:auth                 # Authentication tests only
npm run e2e:workflow             # Job workflow tests only
npm run e2e:mobile               # Mobile workflow tests only
npm run e2e:api                  # API-related tests only
```

CI/CD optimized:
```bash
npm run test:ci                  # Run all tests with coverage
```

### Frontend-Specific Commands

When working in the `frontend/` directory:
```bash
npm run test                     # Run all frontend tests
npm run test:unit               # Component tests in src/test/
npm run test:integration        # Integration tests in tests/integration/
npm run test:api                # API-related integration tests
npm run test:polling            # Polling validation tests
npm run test:watch              # Watch mode for all tests
npm run test:watch:unit         # Watch mode for unit tests only
npm run test:watch:integration  # Watch mode for integration tests only
npm run test:coverage           # Run with coverage report
npm run test:ui                 # Run with Vitest UI
npm run test:debug              # Run in debug mode
```

### Backend-Specific Commands

When working in the `backend/` directory:
```bash
python -m pytest                # Run all backend tests
python -m pytest tests/unit/    # Unit tests only
python -m pytest tests/integration/  # Integration tests only
python -m pytest tests/agents/  # Agent tests only
python -m pytest --cov=. --cov-report=html  # With coverage
```

## Test Configuration

### Frontend (Vitest)
- **Config**: `frontend/vitest.config.ts`
- **Environment**: jsdom
- **Setup**: `frontend/src/test/setup.ts`
- **Coverage**: HTML, JSON, and text reports

### Backend (pytest)
- **Config**: `backend/pytest.ini`
- **Test Discovery**: Automatic for `test_*.py` files
- **Coverage**: Available with `--cov` flag

### E2E (Playwright)
- **Config**: `playwright.config.ts`
- **Browsers**: Chromium, Firefox, WebKit
- **Reports**: HTML reports in `playwright-report/`
- **Results**: JSON/XML results in `test-results/`

## Best Practices

1. **Unit Tests**: Focus on testing individual components and functions
2. **Integration Tests**: Test API communications and service integrations
3. **E2E Tests**: Test complete user workflows and critical paths
4. **Test Isolation**: Each test should be independent and not rely on others
5. **Descriptive Names**: Use clear, descriptive test names
6. **Mocking**: Mock external dependencies in unit tests
7. **Coverage**: Aim for high coverage but prioritize meaningful tests

## Development Workflow

1. **During Development**: Use watch mode (`npm run test:watch`)
2. **Before Commit**: Run relevant test suites
3. **Before Push**: Run full test suite (`npm test`)
4. **CI/CD**: Use `npm run test:ci` for comprehensive testing with coverage

## Debugging Tests

### Frontend
```bash
npm run test:debug              # Debug mode
npm run test:ui                 # Visual test runner
```

### Backend
```bash
python -m pytest -v            # Verbose output
python -m pytest -s            # Print statements
python -m pytest --pdb         # Python debugger
```

### E2E
```bash
npm run test:e2e:debug          # Step-by-step debugging
npm run test:e2e:headed         # See browser actions
npm run test:e2e:ui             # Interactive test runner
``` 