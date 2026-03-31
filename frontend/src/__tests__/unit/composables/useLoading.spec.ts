/**
 * useLoading composable tests
 */

import { describe, it, expect } from 'vitest'
import { useLoading } from '@/composables/useLoading'

describe('useLoading', () => {
  it('should initialize with default loading state', () => {
    const { loading } = useLoading()

    expect(loading.value).toBe(false)
  })

  it('should initialize with custom loading state', () => {
    const { loading } = useLoading(true)

    expect(loading.value).toBe(true)
  })

  it('should set loading to true during async operation', async () => {
    const { loading, withLoading } = useLoading()
    let operationRan = false

    const operation = async () => {
      operationRan = true
      await new Promise(resolve => setTimeout(resolve, 10))
    }

    await withLoading(operation)

    expect(operationRan).toBe(true)
    expect(loading.value).toBe(false)
  })

  it('should set loading to false after async operation completes', async () => {
    const { loading, withLoading } = useLoading()

    await withLoading(async () => {
      expect(loading.value).toBe(true)
      await new Promise(resolve => setTimeout(resolve, 10))
    })

    expect(loading.value).toBe(false)
  })

  it('should set loading to false even if operation throws', async () => {
    const { loading, withLoading } = useLoading()

    try {
      await withLoading(async () => {
        throw new Error('Test error')
      })
    } catch {
      // Expected error
    }

    expect(loading.value).toBe(false)
  })
})
