# Playwright Browser Automation Testing - Quick Start Guide

## Overview
Comprehensive Playwright test suite for NEWSEAMS project that tests:
- User authentication (login)
- Menu navigation
- Business object list pages
- API metadata endpoints
- CRUD operations
- Error handling

## Prerequisites

### 1. Install Dependencies
Playwright is already installed in the project. If you need to reinstall:

```bash
npm install
```

### 2. Install Playwright Browsers
```bash
npx playwright install
```

### 3. Start Services

#### Backend (Django API)
```bash
cd backend
python manage.py runserver
```
Runs on: `http://localhost:8000`

#### Frontend (Vue3)
```bash
cd frontend
npm run dev
```
Runs on: `http://localhost:5173`

## Test Files

### Main Test File
**File**: `C:\Users\ND\Desktop\Notting_Project\NEWSEAMS\test_all_objects.spec.ts`

This comprehensive test file includes:

1. **Authentication Tests**
   - Login with admin/admin123
   - Token verification

2. **Menu Navigation Tests**
   - Main menu display
   - Navigation to Assets section

3. **Business Object List Pages**
   Tests list page loading for:
   - Asset (Asset Card)
   - AssetCategory
   - Supplier
   - Location
   - AssetPickup
   - InventoryTask

4. **API Metadata Endpoints**
   - Tests metadata endpoints for all business objects
   - Validates response structure and status codes

5. **API List Endpoints**
   - Tests list data retrieval for all objects
   - Validates pagination and data structure

6. **CRUD Operations (Asset)**
   - Navigate to create page
   - Test API endpoints (GET, POST)

7. **Error Handling**
   - Invalid credentials
   - Unauthorized access
   - 404 pages

## Running Tests

### Quick Start (Windows)
Run the setup script first:
```bash
setup-playwright-tests.bat
```

### Run All Tests
```bash
npx playwright test test_all_objects.spec.ts
```

### Run Tests with UI Mode (Recommended)
```bash
npx playwright test test_all_objects.spec.ts --ui
```

### Run Tests in Headed Mode (Watch Browser)
```bash
npx playwright test test_all_objects.spec.ts --headed
```

### Run Specific Test Suite
```bash
# Run only authentication tests
npx playwright test test_all_objects.spec.ts -g "Authentication"

# Run only list page tests
npx playwright test test_all_objects.spec.ts -g "Business Object List Pages"

# Run only API tests
npx playwright test test_all_objects.spec.ts -g "API Metadata Endpoints"
npx playwright test test_all_objects.spec.ts -g "API List Endpoints"

# Run only CRUD tests
npx playwright test test_all_objects.spec.ts -g "CRUD Operations"
```

### Run with Debugging
```bash
npx playwright test test_all_objects.spec.ts --debug
```

### Run Specific Test
```bash
npx playwright test test_all_objects.spec.ts -g "should login successfully"
```

## Test Configuration

### Environment Variables
Create a `.env` file or set environment variables:

```bash
# Frontend URL (default: http://localhost:5173)
BASE_URL=http://localhost:5173

# Backend API URL (default: http://localhost:8000)
API_BASE_URL=http://localhost:8000
```

### Playwright Config
File: `C:\Users\ND\Desktop\Notting_Project\NEWSEAMS\playwright.config.ts`

Key settings:
- Base URL: `http://localhost:5173`
- Browser: Chromium
- Workers: 1 (sequential execution)
- Screenshot: On failure only
- Reporter: HTML

## Test Outputs

### Screenshots
Location: `test-screenshots/`
- `login-success.png`
- `dashboard.png`
- `assets-page.png`
- `{object-code}-list-page.png`
- `asset-create-page.png`
- `login-error.png`
- `not-found.png`

### API Responses
Location: `test-responses/`
- `{object-code}-metadata.json`
- `{object-code}-list.json`

### HTML Report
After running tests, view the HTML report:
```bash
npx playwright show-report
```

## Business Objects Tested

| Code | Name | URL | API Endpoint |
|------|------|-----|--------------|
| Asset | Asset Card | /objects/Asset | /api/assets/ |
| AssetCategory | Asset Category | /objects/AssetCategory | /api/asset-categories/ |
| Supplier | Supplier | /objects/Supplier | /api/suppliers/ |
| Location | Location | /objects/Location | /api/locations/ |
| AssetPickup | Asset Pickup | /objects/AssetPickup | /api/asset-pickups/ |
| InventoryTask | Inventory Task | /objects/InventoryTask | /api/inventory-tasks/ |

## Test Credentials
- **Username**: admin
- **Password**: admin123

## Troubleshooting

### Issue: Tests fail with "Service not responding"
**Solution**: Ensure both frontend and backend services are running:
```bash
# Terminal 1 - Backend
cd backend
python manage.py runserver

# Terminal 2 - Frontend
cd frontend
npm run dev
```

### Issue: Login fails
**Solution**:
1. Verify backend is running on port 8000
2. Check if admin user exists: `python manage.py createsuperuser`
3. Check test credentials in test file

### Issue: Tests timeout
**Solution**:
1. Increase timeout in `playwright.config.ts`
2. Check if services are slow to respond
3. Run with `--debug` flag to see what's happening

### Issue: Playwright browsers not installed
**Solution**:
```bash
npx playwright install
```

### Issue: Module not found errors
**Solution**:
```bash
npm install
cd frontend && npm install && cd ..
```

## Advanced Usage

### Run All Playwright Tests in Project
```bash
npx playwright test
```

### Run Tests for Specific File Pattern
```bash
# Run all .spec.ts files
npx playwright test

# Run specific test files
npx playwright test test_login.spec.ts
npx playwright test test_business_objects.spec.ts
```

### Generate Code Coverage
```bash
npx playwright test --coverage
```

### Run Tests in CI Mode
```bash
CI=true npx playwright test
```

## Test Structure

The test file is organized into test suites:

```typescript
test.describe('Authentication', () => { ... });
test.describe('Menu Navigation', () => { ... });
test.describe('Business Object List Pages', () => { ... });
test.describe('API Metadata Endpoints', () => { ... });
test.describe('API List Endpoints', () => { ... });
test.describe('CRUD Operations - Asset', () => { ... });
test.describe('Error Handling', () => { ... });
```

Each test suite:
- Runs independently
- Has its own setup (beforeEach/beforeAll)
- Takes screenshots for visual verification
- Logs detailed information to console

## Best Practices

1. **Always ensure services are running** before executing tests
2. **Use UI mode** for development and debugging: `--ui`
3. **Use headed mode** to watch test execution: `--headed`
4. **Check screenshots** in `test-screenshots/` after test runs
5. **Review API responses** in `test-responses/` for debugging
6. **Run specific test suites** during development to save time
7. **Update test data** if business objects change in the system

## Support

For issues or questions:
1. Check the troubleshooting section above
2. Review test logs in console output
3. Examine screenshots and API response files
4. Run with `--debug` flag for detailed execution info

## File Locations Summary

- **Test File**: `C:\Users\ND\Desktop\Notting_Project\NEWSEAMS\test_all_objects.spec.ts`
- **Config**: `C:\Users\ND\Desktop\Notting_Project\NEWSEAMS\playwright.config.ts`
- **Setup Script**: `C:\Users\ND\Desktop\Notting_Project\NEWSEAMS\setup-playwright-tests.bat`
- **Screenshots**: `C:\Users\ND\Desktop\Notting_Project\NEWSEAMS\test-screenshots\`
- **API Responses**: `C:\Users\ND\Desktop\Notting_Project\NEWSEAMS\test-responses\`
- **HTML Report**: `C:\Users\ND\Desktop\Notting_Project\NEWSEAMS\playwright-report\`
