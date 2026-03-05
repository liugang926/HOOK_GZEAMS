import { describe, expect, it } from 'vitest'
import {
  clearRecentReferenceIds,
  loadRecentReferenceIds,
  saveRecentReferenceIds
} from '@/platform/reference/referenceLookupRecent'

class MemoryStorage {
  private map = new Map<string, string>()

  getItem(key: string): string | null {
    return this.map.has(key) ? this.map.get(key)! : null
  }

  setItem(key: string, value: string): void {
    this.map.set(key, String(value))
  }

  removeItem(key: string): void {
    this.map.delete(key)
  }
}

describe('referenceLookupRecent', () => {
  it('saves and loads recent ids in insertion order with dedupe', () => {
    const storage = new MemoryStorage()
    saveRecentReferenceIds('Asset', ['a-1', 'a-2'], { storage })
    saveRecentReferenceIds('Asset', ['a-2', 'a-3'], { storage })

    expect(loadRecentReferenceIds('Asset', { storage, limit: 10 })).toEqual(['a-2', 'a-3', 'a-1'])
  })

  it('applies limit and supports clear', () => {
    const storage = new MemoryStorage()
    saveRecentReferenceIds('User', ['u-1', 'u-2', 'u-3', 'u-4'], { storage, limit: 3 })
    expect(loadRecentReferenceIds('User', { storage, limit: 10 })).toEqual(['u-1', 'u-2', 'u-3'])

    clearRecentReferenceIds('User', { storage })
    expect(loadRecentReferenceIds('User', { storage })).toEqual([])
  })
})

