import { describe, expect, it, vi, beforeEach } from 'vitest'
import { useMetadataCache } from '../useMetadataCache'

// Mock the SWR cache wrapper
vi.mock('@/utils/cacheWrapper', () => {
  const store = new Map<string, any>()
  return {
    withSWR: vi.fn(async (key: string, fetcher: () => Promise<any>, _opts: any) => {
      if (store.has(key)) return store.get(key)
      const data = await fetcher()
      store.set(key, data)
      return data
    }),
    invalidateSWR: vi.fn(async (matcher: string | RegExp) => {
      if (typeof matcher === 'string') {
        store.delete(matcher)
      } else {
        for (const key of store.keys()) {
          if (matcher.test(key)) store.delete(key)
        }
      }
    }),
    __store: store
  }
})

// Mock the dynamic API
vi.mock('@/api/dynamic', () => ({
  dynamicApi: {
    getMetadata: vi.fn(async (code: string) => ({
      objectCode: code,
      fields: [{ code: 'name', type: 'text' }]
    })),
    getRuntime: vi.fn(async (code: string, mode: string) => ({
      objectCode: code,
      mode,
      layout: { sections: [] }
    }))
  }
}))

describe('useMetadataCache', () => {
  let withSWRMock: ReturnType<typeof vi.fn>
  let invalidateSWRMock: ReturnType<typeof vi.fn>

  beforeEach(async () => {
    vi.clearAllMocks()
    const cacheModule = await import('@/utils/cacheWrapper')
    withSWRMock = cacheModule.withSWR as ReturnType<typeof vi.fn>
    invalidateSWRMock = cacheModule.invalidateSWR as ReturnType<typeof vi.fn>
  })

  it('calls withSWR with correct key and stale time for metadata', async () => {
    const { fetchMetadata } = useMetadataCache()
    await fetchMetadata('Asset')

    expect(withSWRMock).toHaveBeenCalledWith(
      'meta_Asset',
      expect.any(Function),
      { staleTime: 600000, persist: true }
    )
  })

  it('calls withSWR with mode-scoped key for runtime', async () => {
    const { fetchRuntime } = useMetadataCache()
    await fetchRuntime('Asset', 'edit')

    expect(withSWRMock).toHaveBeenCalledWith(
      'runtime_Asset_edit',
      expect.any(Function),
      { staleTime: 300000, persist: true }
    )
  })

  it('invalidates both meta and runtime entries for a given code', async () => {
    const { invalidateMetadata } = useMetadataCache()
    await invalidateMetadata('Asset')

    expect(invalidateSWRMock).toHaveBeenCalledTimes(1)
    const arg = invalidateSWRMock.mock.calls[0][0]
    expect(arg).toBeInstanceOf(RegExp)
    expect(arg.test('meta_Asset')).toBe(true)
    expect(arg.test('runtime_Asset_edit')).toBe(true)
    expect(arg.test('meta_Department')).toBe(false)
  })

  it('returns metadata shape from the fetcher', async () => {
    const { fetchMetadata } = useMetadataCache()
    const result = await fetchMetadata('Department')

    expect(result).toEqual({
      objectCode: 'Department',
      fields: [{ code: 'name', type: 'text' }]
    })
  })
})
