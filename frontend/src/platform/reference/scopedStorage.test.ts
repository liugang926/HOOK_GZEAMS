import { describe, expect, it } from 'vitest'
import {
  buildStorageKey,
  normalizeStorageSegment,
  readWithLegacyMigration,
  removeLegacyKey,
  type StorageLike
} from '@/platform/reference/scopedStorage'

class MemoryStorage implements StorageLike {
  private readonly map = new Map<string, string>()

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

describe('scopedStorage', () => {
  it('normalizes segments and builds storage keys', () => {
    expect(normalizeStorageSegment(' Asset ')).toBe('Asset')
    expect(buildStorageKey('k:', 'A', 'B', 'C')).toBe('k:A:B:C')
  })

  it('reads scoped key directly when present', () => {
    const storage = new MemoryStorage()
    storage.setItem('k:scoped', 'value-1')
    storage.setItem('k:legacy', 'legacy-value')

    expect(readWithLegacyMigration(storage, 'k:scoped', 'k:legacy')).toBe('value-1')
    expect(storage.getItem('k:legacy')).toBe('legacy-value')
  })

  it('migrates legacy key on first scoped read', () => {
    const storage = new MemoryStorage()
    storage.setItem('k:legacy', 'legacy-value')

    expect(readWithLegacyMigration(storage, 'k:scoped', 'k:legacy')).toBe('legacy-value')
    expect(storage.getItem('k:scoped')).toBe('legacy-value')
    expect(storage.getItem('k:legacy')).toBeNull()
  })

  it('removes legacy key only when different from scoped key', () => {
    const storage = new MemoryStorage()
    storage.setItem('k:scoped', 'scoped-value')
    storage.setItem('k:legacy', 'legacy-value')

    removeLegacyKey(storage, 'k:scoped', 'k:legacy')
    expect(storage.getItem('k:legacy')).toBeNull()

    storage.setItem('k:same', 'same')
    removeLegacyKey(storage, 'k:same', 'k:same')
    expect(storage.getItem('k:same')).toBe('same')
  })
})
