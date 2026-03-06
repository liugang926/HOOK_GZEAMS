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

  it('migrates legacy _record key into explicit scoped key', () => {
    const storage = new MemoryStorage()
    const legacyKey = 'gzeams:detail:related-groups:Asset:_record'
    const scopedKey = 'gzeams:detail:related-groups:Asset:designer-preview:edit:draft'
    storage.setItem(legacyKey, JSON.stringify({ expanded: ['finance'] }))

    expect(loadRelationGroupExpandedPreference('Asset', 'designer-preview:edit:draft', { storage })).toEqual(['finance'])
    expect(storage.getItem(scopedKey)).toContain('"finance"')
    expect(storage.getItem(legacyKey)).toBeNull()
  })

  it('save/clear with explicit scope removes legacy _record key', () => {
    const storage = new MemoryStorage()
    const legacyKey = 'gzeams:detail:related-groups:Asset:_record'
    const scopedKey = 'gzeams:detail:related-groups:Asset:designer-preview:edit:draft'
    storage.setItem(legacyKey, JSON.stringify({ expanded: ['workflow'] }))

    saveRelationGroupExpandedPreference('Asset', 'designer-preview:edit:draft', ['finance'], { storage })
    expect(storage.getItem(scopedKey)).toContain('"finance"')
    expect(storage.getItem(legacyKey)).toBeNull()

    clearRelationGroupExpandedPreference('Asset', 'designer-preview:edit:draft', { storage })
    expect(storage.getItem(scopedKey)).toBeNull()
  })
})
