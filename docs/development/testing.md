# Testing Guide

## Overview

The AI Agent Platform uses a comprehensive testing strategy with two main test suites:

```
tests/
├── backend/                     # Backend tests (Python/pytest)
│   ├── unit/                    # Unit tests
│   ├── integration/             # Integration tests
│   └── agents/                  # Agent-specific tests
└── frontend/src/test/           # Frontend tests (Jest/React Testing Library)
    ├── components/              # Component tests
    ├── hooks/                   # Hook tests
    └── utils/                   # Utility tests
```

## Quick Start

```bash
# Run all tests
npm run test

# Individual test suites
npm run test:frontend            # Frontend unit/integration tests
npm run test:backend             # Backend tests
npm run test:backend:unit        # Backend unit tests only
npm run test:backend:integration # Backend integration tests only
npm run test:backend:agents      # Agent-specific tests
```

### CI/CD Integration

```bash
npm run test:ci                  # CI pipeline with coverage
npm run test:backend:coverage    # Backend coverage report
npm run test:frontend -- --coverage  # Frontend coverage report
```

## Testing Tools

### Backend (Python)
- **Framework**: pytest
- **Async Support**: pytest-asyncio
- **Mocking**: unittest.mock, pytest fixtures
- **Coverage**: pytest-cov
- **Database**: SQLite in-memory for tests

### Frontend (TypeScript/React)
- **Framework**: Jest
- **Testing Library**: React Testing Library
- **Mocking**: Jest mocks, MSW (Mock Service Worker)
- **Coverage**: Built-in Jest coverage

## Configuration

### Backend Testing
- **Config**: `backend/pytest.ini`
- **Async Settings**: asyncio mode enabled
- **Coverage**: HTML reports in `backend/htmlcov/`

### Frontend Testing
- **Config**: `frontend/jest.config.js`
- **Setup**: `frontend/src/setupTests.ts`
- **Coverage**: Reports in `frontend/coverage/`

## Test Categories

1. **Unit Tests**: Test individual functions and classes
2. **Integration Tests**: Test API endpoints and component interactions
3. **Agent Tests**: Test custom agent implementations

## Debugging Tests

### Backend
```bash
pytest --pdb                     # Drop into debugger on failure
pytest -v                       # Verbose output
pytest -s                       # Don't capture output
pytest -k "test_name"            # Run specific test
```

### Frontend
```bash
npm run test:frontend:watch      # Watch mode for development
npm run test:frontend -- --verbose  # Verbose output
``` 