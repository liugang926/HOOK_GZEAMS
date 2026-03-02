/**
 * Test helper utilities
 */

import { VueWrapper, DOMWrapper } from '@vue/test-utils'
import { vi } from 'vitest'

/**
 * Wait for async updates to complete
 */
export async function flushPromises(): Promise<void> {
  return new Promise(resolve => setTimeout(resolve, 0))
}

/**
 * Wait for next tick
 */
export async function nextTick(): Promise<void> {
  return await new Promise(resolve => setTimeout(resolve, 10))
}

/**
 * Find element by test id
 */
export function findByTestId(
  wrapper: VueWrapper<any> | DOMWrapper<any>,
  id: string
): DOMWrapper<any> | null {
  return wrapper.find(`[data-testid="${id}"]`)
}

/**
 * Find all elements by test id
 */
export function findAllByTestId(
  wrapper: VueWrapper<any>,
  id: string
): DOMWrapper<any>[] {
  return wrapper.findAll(`[data-testid="${id}"]`)
}

/**
 * Mock console methods to reduce noise in tests
 */
export function mockConsole(): { restore: () => void } {
  const originalError = console.error
  const originalWarn = console.warn

  console.error = vi.fn()
  console.warn = vi.fn()

  return {
    restore: () => {
      console.error = originalError
      console.warn = originalWarn
    }
  }
}

/**
 * Create a mock file for upload testing
 */
export function createMockFile(
  name: string = 'test.pdf',
  size: number = 1024,
  type: string = 'application/pdf'
): File {
  const file = new File(['mock content'], name, { type })
  Object.defineProperty(file, 'size', { value: size })
  return file
}

/**
 * Wait for element to appear
 */
export async function waitFor(
  callback: () => boolean,
  timeout: number = 5000
): Promise<void> {
  const startTime = Date.now()
  while (!callback()) {
    if (Date.now() - startTime > timeout) {
      throw new Error(`Timeout waiting for condition`)
    }
    await new Promise(resolve => setTimeout(resolve, 50))
  }
}
