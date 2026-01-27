# E2E Tests

Playwright-based end-to-end testing for NEWSEAMS frontend.

## Setup

Install dependencies and browsers:

```bash
npm install
npm run test:e2e:install
```

## Running Tests

```bash
# Run all tests (Chromium only by default)
npm run test:e2e

# Run with UI mode (interactive)
npm run test:e2e:ui

# Run with visible browser
npm run test:e2e:headed

# Debug mode
npm run test:e2e:debug
```

## Test Structure

```
e2e/
├── fixtures/
│   └── auth.fixture.ts      # Authentication fixture
├── helpers/
│   └── api.helpers.ts        # API helper functions
├── auth/
│   └── auth.spec.ts         # Authentication tests (7 tests)
├── assets/
│   └── assets-crud.spec.ts  # Asset CRUD tests (8 tests)
├── forms/
│   └── form-validation.spec.ts  # Form validation tests (8 tests)
├── navigation/
│   └── navigation.spec.ts  # Navigation tests (10 tests)
└── inventory/
    └── inventory-workflow.spec.ts  # Inventory tests (9 tests)
```

## Environment Variables

Create a `.env` file or set environment variables:

```bash
E2E_USERNAME=admin
E2E_PASSWORD=admin123
API_BASE_URL=http://127.0.0.1:8000/api
```

## Test Coverage

| Suite | Tests | Coverage |
|-------|-------|----------|
| Authentication | 7 | Login, logout, validation, session persistence |
| Asset CRUD | 8 | List, create, edit, delete, search |
| Form Validation | 8 | Required fields, email, number, date, phone |
| Navigation | 10 | Menu navigation, breadcrumbs, browser nav |
| Inventory | 9 | Task creation, execution, scanning, submission |

**Total: 42 test scenarios × 5 browser projects = 210 tests**

## Writing New Tests

1. Create a new spec file in the appropriate directory
2. Import test utilities:

```typescript
import { test, expect } from '@playwright/test'
import { getTestUserToken } from '../helpers/api.helpers'
```

3. Use the auth pattern:

```typescript
test.beforeEach(async ({ page }) => {
  const token = await getTestUserToken()
  await page.goto('/login')
  await page.evaluate((token) => {
    localStorage.setItem('auth_token', token)
  }, token)
})
```

## CI/CD Integration

For CI, set up a test user and run:

```bash
npm run test:e2e
```

The test configuration automatically handles:
- Starting the dev server
- Running tests in parallel
- Retrying on failure (CI only)
- Generating HTML reports
