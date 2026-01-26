import { defineConfig, devices } from '@playwright/test'

/**
 * Playwright E2E Test Configuration for NEWSEAMS
 *
 * This configuration supports:
 * - Cross-browser testing (Chrome, Firefox, Safari)
 * - API mocking for offline testing
 * - Screenshot and video capture on failure
 * - Test isolation with authentication fixtures
 */
export default defineConfig({
  // Test directory
  testDir: './e2e',

  // Test files matching pattern
  testMatch: '**/*.spec.ts',

  // Timeout per test
  timeout: 30 * 1000,

  // Expect timeout for assertions
  expect: {
    timeout: 5 * 1000
  },

  // Fully parallelize tests across all files
  fullyParallel: true,

  // Fail the build on CI if you accidentally left test.only in the source code
  forbidOnly: !!process.env.CI,

  // Retry on CI only
  retries: process.env.CI ? 2 : 0,

  // Opt out of parallel tests on CI
  workers: process.env.CI ? 1 : undefined,

  // Reporter to use
  reporter: [
    ['html', { outputFolder: 'playwright-report' }],
    ['list']
  ],

  // Shared settings for all tests
  use: {
    // Base URL for tests - uses dev server by default
    baseURL: process.env.BASE_URL || 'http://localhost:5173',

    // Collect trace when retrying the failed test
    trace: 'on-first-retry',

    // Screenshot on failure
    screenshot: 'only-on-failure',

    // Video on failure
    video: 'retain-on-failure',

    // Action timeout
    actionTimeout: 10 * 1000,

    // Navigation timeout
    navigationTimeout: 30 * 1000
  },

  // Configure projects for major browsers
  projects: [
    {
      name: 'chromium',
      use: { ...devices['Desktop Chrome'] },
    },

    // The following projects are disabled on CI for speed
    ...(process.env.CI !== 'true' ? [
      {
        name: 'firefox',
        use: { ...devices['Desktop Firefox'] },
      },
      {
        name: 'webkit',
        use: { ...devices['Desktop Safari'] },
      },
      // Mobile tests
      {
        name: 'Mobile Chrome',
        use: { ...devices['Pixel 5'] },
      },
      {
        name: 'Mobile Safari',
        use: { ...devices['iPhone 12'] },
      },
    ] : []),
  ],

  // Run your local dev server before starting the tests
  // Note: Set PLAYWRIGHT_WEB_SERVER=1 to enable auto-start
  // Otherwise assumes server is already running
  ...(process.env.PLAYWRIGHT_WEB_SERVER === '1' ? {
    webServer: {
      command: 'npm run dev',
      url: 'http://localhost:5173',
      reuseExistingServer: true,
      timeout: 120 * 1000,
    }
  } : {}),
})
