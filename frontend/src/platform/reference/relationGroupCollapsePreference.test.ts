import { describe, expect, it } from 'vitest'
import {
  clearRelationGroupExpandedPreference,
  loadRelationGroupExpandedPreference,
  saveRelationGroupExpandedPreference
} from '@/platform/reference/relationGroupCollapsePreference'

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

describe('relationGroupCollapsePreference', () => {
  it('saves and restores expanded groups by object and record', () => {
    const storage = new MemoryStorage()

    saveRelationGroupExpandedPreference('Asset', 'asset-1', ['workflow', 'business', 'workflow'], { storage })
    saveRelationGroupExpandedPreference('Asset', 'asset-2', ['finance'], { storage })

    expect(loadRelationGroupExpandedPreference('Asset', 'asset-1', { storage })).toEqual(['workflow', 'business'])
    expect(loadRelationGroupExpandedPreference('Asset', 'asset-2', { storage })).toEqual(['finance'])
  })

  it('returns null when preference does not exist and supports clear', () => {
    const storage = new MemoryStorage()
    expect(loadRelationGroupExpandedPreference('Asset', 'asset-3', { storage })).toBeNull()

    saveRelationGroupExpandedPreference('Asset', 'asset-3', ['inventory'], { storage })
    clearRelationGroupExpandedPreference('Asset', 'asset-3', { storage })
    expect(loadRelationGroupExpandedPreference('Asset', 'asset-3', { storage })).toBeNull()
  })
})

