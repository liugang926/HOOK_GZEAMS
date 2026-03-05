import localforage from 'localforage'

localforage.config({
    name: 'GZEAMS',
    storeName: 'frontend_cache',
    description: 'GZEAMS Application Local IndexedDB Cache'
})

/**
 * Universal async storage wrapper (IndexedDB fallback to WebSQL/localStorage).
 * Use for heavy payloads (Layout Drafts, Dictionary Data) to prevent main-thread blocking.
 */
export const storage = {
    /**
     * Set a key-value pair asynchronously.
     */
    async set<T>(key: string, value: T): Promise<T> {
        return localforage.setItem(key, value)
    },

    /**
     * Get a value asynchronously by key. Returns null if not found.
     */
    async get<T>(key: string): Promise<T | null> {
        return localforage.getItem<T>(key)
    },

    /**
     * Remove a value asynchronously by key.
     */
    async remove(key: string): Promise<void> {
        return localforage.removeItem(key)
    },

    /**
     * Clear entire storage instance.
     */
    async clear(): Promise<void> {
        return localforage.clear()
    }
}

export default storage
