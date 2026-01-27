import { test as base, Page } from '@playwright/test'

/**
 * Auth fixture for authenticated testing
 *
 * Provides automatic login for tests that require authentication.
 */

// Define test fixtures
export const test = base.extend<{
  authenticatedPage: Page
}>({
  authenticatedPage: async ({ page }, use) => {
    // Navigate to login page
    await page.goto('/login')

    // Fill in login credentials (using test user)
    await page.fill('input[name="username"]', process.env.E2E_USERNAME || 'admin')
    await page.fill('input[name="password"]', process.env.E2E_PASSWORD || 'admin123')

    // Submit login form
    await page.click('button[type="submit"]')

    // Wait for navigation to complete (should redirect to dashboard)
    await page.waitForURL('/', { timeout: 10000 })

    // Use the authenticated page
    await use(page)

    // Cleanup: logout after test
    // Note: This runs in reverse order due to how fixtures work
    // The page will be automatically closed by Playwright
  },
})

// Re-export expect
export const expect = test.expect
