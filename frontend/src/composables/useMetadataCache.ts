/**
 * useMetadataCache — SWR-cached metadata & runtime fetching composable.
 *
 * Wraps `dynamicApi.getMetadata()` and `dynamicApi.getRuntime()` with
 * `withSWR` from `@/utils/cacheWrapper`, providing:
 *   - In-memory + IndexedDB persistence
 *   - Stale-While-Revalidate background refresh
 *   - Request deduplication (identical keys share one in-flight promise)
 *
 * Usage:
 *   const { fetchMetadata, fetchRuntime, invalidateMetadata } = useMetadataCache()
 *   const meta = await fetchMetadata('Asset')            // cached 10 min
 *   const rt   = await fetchRuntime('Asset', 'edit')     // cached 5 min
 */

import { withSWR, invalidateSWR } from '@/utils/cacheWrapper'
import { dynamicApi } from '@/api/dynamic'
import type { RuntimeMode } from '@/contracts/runtimeContract'
import type { ObjectMetadata } from '@/types'

/** Default TTLs */
const METADATA_STALE_TIME = 1000 * 60 * 10 // 10 minutes — schema rarely changes
const RUNTIME_STALE_TIME = 1000 * 60 * 5   // 5 minutes — layout may be edited more often

export function useMetadataCache() {
  /**
   * Fetch object metadata with SWR caching + IndexedDB persistence.
   * Identical concurrent calls for the same `code` will share one network request.
   */
  async function fetchMetadata(code: string): Promise<ObjectMetadata> {
    return withSWR<ObjectMetadata>(
      `meta_${code}`,
      () => dynamicApi.getMetadata(code),
      { staleTime: METADATA_STALE_TIME, persist: true }
    )
  }

  /**
   * Fetch runtime data (fields + active layout) with SWR caching.
   * Key is scoped by `code + mode` so different modes don't collide.
   */
  async function fetchRuntime(code: string, mode: RuntimeMode = 'edit', params?: Record<string, any>): Promise<any> {
    const key = `runtime_${code}_${mode}`
    return withSWR(
      key,
      () => dynamicApi.getRuntime(code, mode, params),
      { staleTime: RUNTIME_STALE_TIME, persist: true }
    )
  }

  /**
   * Invalidate all cached metadata and runtime entries for a given object code.
   * Call this after saving a layout or editing field definitions.
   */
  async function invalidateMetadata(code: string): Promise<void> {
    await invalidateSWR(new RegExp(`^(meta|runtime)_${code}`))
  }

  /** Invalidate all metadata caches (e.g. on locale switch). */
  async function invalidateAllMetadata(): Promise<void> {
    await invalidateSWR(/^(meta|runtime)_/)
  }

  return {
    fetchMetadata,
    fetchRuntime,
    invalidateMetadata,
    invalidateAllMetadata
  }
}
