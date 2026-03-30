/**
 * MSW server setup and lifecycle management
 */

import { afterAll, afterEach, beforeAll } from 'vitest'
import { setupServer } from 'msw/node'
import { handlers } from './handlers'

export const mswServer = setupServer(...handlers)

// Setup before all tests
beforeAll(() => {
  mswServer.listen({ onUnhandledRequest: 'error' })
})

// Reset handlers after each test
afterEach(() => {
  mswServer.resetHandlers()
})

// Cleanup after all tests
afterAll(() => {
  mswServer.close()
})
