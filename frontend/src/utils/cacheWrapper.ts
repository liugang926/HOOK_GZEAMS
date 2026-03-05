/**
 * SWR (Stale-While-Revalidate) Cache Wrapper
 * Provides an in-memory cache mechanism that returns stale data immediately
 * while fetching fresh data in the background. Now supports IndexedDB persistence.
 */

import { storage } from '@/utils/storage'

interface CacheEntry<T> {
    data: T
    fetchTime: number
    promise?: Promise<T>
}

interface SWROptions {
    /** Time in ms before data is considered stale and needs revalidation (default: 5 minutes) */
    staleTime?: number
    /** Whether to persist this cache entry via IndexedDB */
    persist?: boolean
}

const memoryCache = new Map<string, CacheEntry<any>>()

export async function withSWR<T>(
    key: string,
    fetcher: () => Promise<T>,
    options: SWROptions = {}
): Promise<T> {
    const staleTime = options.staleTime ?? 1000 * 60 * 5 // 5 minutes default
    const persist = options.persist ?? false

    const now = Date.now()
    let cached = memoryCache.get(key)

    // 1. Attempt persistent hydrate if not in memory
    if (!cached && persist) {
        try {
            const persisted = await storage.get<CacheEntry<T>>(key)
            if (persisted && persisted.data) {
                cached = { data: persisted.data, fetchTime: persisted.fetchTime || 0 }
                memoryCache.set(key, cached)
            }
        } catch (e) {
            console.warn(`[SWR] Hydration failed for key ${key}`, e)
        }
    }

    // 2. We have cached data
    if (cached && cached.fetchTime > 0) {
        const isStale = now - cached.fetchTime > staleTime

        if (!isStale) {
            // Data is fresh, return immediately
            return cached.data
        }

        // Data is stale. If no background fetch is happening, trigger one
        if (!cached.promise) {
            cached.promise = fetcher()
                .then(async (freshData) => {
                    const entry = { data: freshData, fetchTime: Date.now() }
                    memoryCache.set(key, entry)
                    if (persist) {
                        await storage.set(key, entry).catch(e => console.warn(`[SWR] persist failed for ${key}`, e))
                    }
                    return freshData
                })
                .catch((error) => {
                    console.warn(`[SWR] Background fetch failed for ${key}. Retaining stale data.`, error)
                    // Resolve with stale data to avoid breaking the app (Resilience)
                    return cached!.data
                })
                .finally(() => {
                    const entry = memoryCache.get(key)
                    // Only clear the promise if it hasn't been overwritten by a new fetch
                    if (entry && entry.promise === cached!.promise) {
                        entry.promise = undefined
                    }
                })
        }

        // Return stale data immediately while background fetch continues
        return cached.data
    }

    // 3. No cache exists at all
    if (cached && cached.promise) {
        return cached.promise
    }

    const promise = fetcher()
        .then(async (freshData) => {
            const entry = { data: freshData, fetchTime: Date.now() }
            memoryCache.set(key, entry)
            if (persist) {
                await storage.set(key, entry).catch(e => console.warn(`[SWR] persist failed for ${key}`, e))
            }
            return freshData
        })
        .catch((error) => {
            // Initial fetch failed completely, delete placeholder
            memoryCache.delete(key)
            throw error
        })

    // Set placeholder with active promise
    memoryCache.set(key, { data: null as any, fetchTime: 0, promise })

    try {
        return await promise
    } catch (error) {
        throw error
    }
}

export async function invalidateSWR(keyMatcher: string | RegExp) {
    if (typeof keyMatcher === 'string') {
        memoryCache.delete(keyMatcher)
        await storage.remove(keyMatcher).catch(() => { })
    } else {
        for (const key of memoryCache.keys()) {
            if (keyMatcher.test(key)) {
                memoryCache.delete(key)
                await storage.remove(key).catch(() => { })
            }
        }
    }
}

export async function clearSWR() {
    memoryCache.clear()
    await storage.clear().catch(() => { })
}
