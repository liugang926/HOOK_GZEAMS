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

    // Fill in login credentials (Element Plus inputs; no name attributes)
    const username = process.env.E2E_USERNAME || 'admin'
    const password = process.env.E2E_PASSWORD || 'admin123'

    const inputs = page.locator('.login-page .el-input__inner')
    await inputs.nth(0).fill(username)
    await inputs.nth(1).fill(password)

    // Submit login form
    await page.locator('.login-page button.el-button--primary').click()

    // Wait for navigation to complete (should redirect to dashboard)
    await page.waitForURL(/\/(dashboard)?$/, { timeout: 10000 })

    // Use the authenticated page
    await use(page)

    // Cleanup: logout after test
    // Note: This runs in reverse order due to how fixtures work
    // The page will be automatically closed by Playwright
  },
})

// Re-export expect
export const expect = test.expect
