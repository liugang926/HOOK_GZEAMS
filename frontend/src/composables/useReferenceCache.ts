import { ref } from 'vue'
import { dynamicApi } from '@/api/dynamic'
import type { CompactDetailField } from '@/api/dynamic'

interface CacheEntry {
  fields: CompactDetailField[]
  timestamp: number
}

const MAX_CACHE_SIZE = 100
const CACHE_TTL_MS = 5 * 60 * 1000 // 5 minutes

const cache = ref<Map<string, CacheEntry>>(new Map())

function makeCacheKey(objectCode: string, recordId: string): string {
  return `${objectCode}:${recordId}`
}

function evictOldest() {
  if (cache.value.size <= MAX_CACHE_SIZE) return
  const oldest = cache.value.keys().next().value
  if (oldest) cache.value.delete(oldest)
}

function isExpired(entry: CacheEntry): boolean {
  return Date.now() - entry.timestamp > CACHE_TTL_MS
}

/**
 * LRU cache for compact detail hover card data.
 * Shared across all ReferenceRecordPill instances in the same session.
 */
export function useReferenceCache() {
  const getCompactDetail = async (
    objectCode: string,
    recordId: string
  ): Promise<CompactDetailField[]> => {
    const key = makeCacheKey(objectCode, recordId)

    const cached = cache.value.get(key)
    if (cached && !isExpired(cached)) {
      // Move to end (LRU refresh)
      cache.value.delete(key)
      cache.value.set(key, cached)
      return cached.fields
    }

    try {
      const resp = await dynamicApi.getCompactDetail(objectCode, recordId)
      const data = (resp as any)?.data ?? resp
      const fields: CompactDetailField[] = Array.isArray(data?.fields) ? data.fields : []

      evictOldest()
      cache.value.set(key, { fields, timestamp: Date.now() })

      return fields
    } catch {
      return []
    }
  }

  const invalidate = (objectCode: string, recordId: string) => {
    cache.value.delete(makeCacheKey(objectCode, recordId))
  }

  const clearAll = () => {
    cache.value.clear()
  }

  return {
    getCompactDetail,
    invalidate,
    clearAll
  }
}
