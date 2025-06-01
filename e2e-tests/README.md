# End-to-End Tests

> **Playwright E2E testing suite** - Comprehensive testing across browsers and devices

## Quick Start

```bash
# Run all E2E tests
npm run test:e2e

# Run with UI (interactive mode)
npm run test:e2e:ui

# Run in headed mode (see browser)
npm run test:e2e:headed

# Debug tests
npm run test:e2e:debug
```

## Test Suites

- **`01-authentication.spec.ts`** - User login, logout, and auth flows
- **`02-job-workflow.spec.ts`** - Job creation, monitoring, and completion
- **`03-mobile-workflow.spec.ts`** - Mobile-responsive functionality
- **`04-api-authentication.spec.ts`** - API authentication and security
- **`05-agent-api-security.spec.ts`** - Agent-specific security testing
- **`06-cross-browser-compatibility.spec.ts`** - Cross-browser compatibility

## Specific Test Commands

```bash
npm run e2e:auth          # Authentication tests only
npm run e2e:workflow      # Job workflow tests only
npm run e2e:mobile        # Mobile workflow tests only
npm run e2e:api           # API-related tests only
```

## Prerequisites

1. **Backend running** on http://localhost:8000
2. **Frontend running** on http://localhost:5173
3. **Test user created** (admin@example.com)

## Browser Support

Tests run on:
- **Chromium** (Chrome, Edge)
- **Firefox**
- **WebKit** (Safari)
- **Mobile Chrome** (responsive testing)
- **Mobile Safari** (responsive testing)

## Configuration

E2E tests are configured in `../playwright.config.ts` with:
- Automatic server startup
- Parallel execution
- Retry logic for flaky tests
- HTML reports
- Screenshots and videos on failure

## Documentation

For complete testing strategy and guides:

- **[Testing Guide](../docs/development/testing.md)** - Complete testing documentation
- **[Troubleshooting](../docs/getting-started/troubleshooting.md)** - Common test issues
- **[Configuration Reference](../docs/configuration/README.md)** - Playwright configuration 