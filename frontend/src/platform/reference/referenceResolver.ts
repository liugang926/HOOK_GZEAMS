import request from '@/utils/request'

export type ReferenceObjectCode = string

export interface ResolveRefInput {
  objectCode: ReferenceObjectCode
  id: string
}

type CacheEntry = {
  expiresAt: number
  value: any
}

const DEFAULT_TTL_MS = 5 * 60 * 1000
const MAX_CACHE_SIZE = 2000

const cache = new Map<string, CacheEntry>()
const inFlight = new Map<string, Promise<any>>()

const makeKey = (objectCode: string, id: string) => `${objectCode}:${id}`

const trimCacheIfNeeded = () => {
  if (cache.size <= MAX_CACHE_SIZE) return
  // Drop the oldest-ish entries by iterating insertion order.
  const target = Math.floor(MAX_CACHE_SIZE * 0.9)
  for (const key of cache.keys()) {
    cache.delete(key)
    if (cache.size <= target) break
  }
}

const fetchById = async (objectCode: string, id: string): Promise<any> => {
  // Unified object router only (engine/runtime should not depend on legacy /auth/users).
  return await request.get(`/system/objects/${objectCode}/${id}/`, { silent: true })
}

export const referenceResolver = {
  async resolve(input: ResolveRefInput, options?: { ttlMs?: number; force?: boolean }): Promise<any | null> {
    const objectCode = String(input.objectCode || '').trim()
    const id = String(input.id || '').trim()
    if (!objectCode || !id) return null

    const ttlMs = options?.ttlMs ?? DEFAULT_TTL_MS
    const key = makeKey(objectCode, id)

    if (!options?.force) {
      const cached = cache.get(key)
      if (cached && cached.expiresAt > Date.now()) return cached.value
    }

    const existing = inFlight.get(key)
    if (existing) return existing

    const p = (async () => {
      try {
        const value = await fetchById(objectCode, id)
        cache.set(key, { value, expiresAt: Date.now() + ttlMs })
        trimCacheIfNeeded()
        return value
      } catch {
        // Cache null briefly to avoid hot loops when backend returns 404/500.
        cache.set(key, { value: null, expiresAt: Date.now() + Math.min(ttlMs, 15_000) })
        trimCacheIfNeeded()
        return null
      } finally {
        inFlight.delete(key)
      }
    })()

    inFlight.set(key, p)
    return p
  },

  async resolveMany(
    objectCode: ReferenceObjectCode,
    ids: string[],
    options?: { ttlMs?: number; force?: boolean; concurrency?: number }
  ): Promise<Record<string, any | null>> {
    const code = String(objectCode || '').trim()
    const uniqueIds = Array.from(new Set((ids || []).map((id) => String(id || '').trim()).filter(Boolean)))
    const out: Record<string, any | null> = {}
    if (!code || uniqueIds.length === 0) return out

    const ttlMs = options?.ttlMs ?? DEFAULT_TTL_MS

    // Prefer backend batch endpoint to reduce request storms in readonly/detail pages.
    const now = Date.now()
    const needsFetch = uniqueIds.filter((id) => {
      if (options?.force) return true
      const cached = cache.get(makeKey(code, id))
      return !cached || cached.expiresAt <= now
    })

    if (needsFetch.length > 0) {
      try {
        const res: any = await request.post(
          `/system/objects/${code}/batch-get/`,
          { ids: needsFetch },
          { silent: true }
        )

        const results: any[] = res?.results || res?.data?.results || []
        const missing: string[] = res?.missingIds || res?.missing_ids || res?.data?.missingIds || []

        for (const item of results) {
          const id = String(item?.id || item?.pk || '').trim()
          if (!id) continue
          cache.set(makeKey(code, id), { value: item, expiresAt: Date.now() + ttlMs })
        }

        for (const id of missing) {
          const key = makeKey(code, String(id))
          cache.set(key, { value: null, expiresAt: Date.now() + Math.min(ttlMs, 15_000) })
        }

        trimCacheIfNeeded()
      } catch {
        // Fall through to per-id resolves.
      }
    }

    const concurrency = Math.max(1, Math.min(options?.concurrency ?? 6, 12))
    let idx = 0
    const worker = async () => {
      while (idx < uniqueIds.length) {
        const current = uniqueIds[idx++]
        const cached = cache.get(makeKey(code, current))
        if (cached && cached.expiresAt > Date.now()) out[current] = cached.value
        else out[current] = await this.resolve({ objectCode: code, id: current }, options)
      }
    }
    await Promise.all(Array.from({ length: Math.min(concurrency, uniqueIds.length) }, () => worker()))
    return out
  },

  clear() {
    cache.clear()
    inFlight.clear()
  }
}
