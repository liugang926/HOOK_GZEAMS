import { describe, expect, it } from 'vitest'
import {
  hasLookupColumnsPreference,
  loadLastLookupProfile,
  loadLookupColumnsPreference,
  loadLookupHiddenColumns,
  saveLastLookupProfile,
  saveLookupColumnsPreference,
  saveLookupHiddenColumns
} from './referenceLookupColumnsPreference'

const createStorage = () => {
  const map = new Map<string, string>()
  return {
    getItem: (key: string) => map.get(key) ?? null,
    setItem: (key: string, value: string) => map.set(key, value),
    removeItem: (key: string) => map.delete(key)
  }
}

describe('referenceLookupColumnsPreference', () => {
  it('should persist hidden columns by object and preference key', () => {
    const storage = createStorage()
    saveLookupHiddenColumns('User', ['code', 'email'], { preferenceKey: 'owner', userScope: 'u1', storage })

    const hidden = loadLookupHiddenColumns('User', { preferenceKey: 'owner', userScope: 'u1', storage })
    expect(Array.from(hidden).sort()).toEqual(['code', 'email'])
  })

  it('should isolate preferences by key and user scope', () => {
    const storage = createStorage()
    saveLookupHiddenColumns('User', ['code'], { preferenceKey: 'owner', userScope: 'u1', storage })
    saveLookupHiddenColumns('User', ['email'], { preferenceKey: 'owner', userScope: 'u2', storage })

    const owner = loadLookupHiddenColumns('User', { preferenceKey: 'owner', userScope: 'u1', storage })
    const assignee = loadLookupHiddenColumns('User', { preferenceKey: 'owner', userScope: 'u2', storage })
    expect(Array.from(owner)).toEqual(['code'])
    expect(Array.from(assignee)).toEqual(['email'])
  })

  it('should persist column order together with hidden columns', () => {
    const storage = createStorage()
    saveLookupColumnsPreference(
      'User',
      { hidden: ['email'], order: ['name', 'id', 'code'], widths: { name: 320, code: 180 }, profile: 'compact' },
      { preferenceKey: 'owner', userScope: 'u1', storage }
    )

    const preference = loadLookupColumnsPreference('User', { preferenceKey: 'owner', userScope: 'u1', storage })
    expect(Array.from(preference.hidden)).toEqual(['email'])
    expect(preference.order).toEqual(['name', 'id', 'code'])
    expect(preference.widths).toEqual({ name: 320, code: 180 })
    expect(preference.profile).toBe('compact')
  })

  it('should preserve order and widths when saving hidden columns via compatibility wrapper', () => {
    const storage = createStorage()
    saveLookupColumnsPreference(
      'User',
      { hidden: [], order: ['name', 'id', 'code'], widths: { name: 300 }, profile: 'custom' },
      { preferenceKey: 'owner', userScope: 'u1', storage }
    )

    saveLookupHiddenColumns('User', ['code'], { preferenceKey: 'owner', userScope: 'u1', storage })
    const preference = loadLookupColumnsPreference('User', { preferenceKey: 'owner', userScope: 'u1', storage })
    expect(Array.from(preference.hidden)).toEqual(['code'])
    expect(preference.order).toEqual(['name', 'id', 'code'])
    expect(preference.widths).toEqual({ name: 300 })
    expect(preference.profile).toBe('custom')
  })

  it('should support preference existence checks by user scope', () => {
    const storage = createStorage()
    expect(hasLookupColumnsPreference('User', { preferenceKey: 'owner', userScope: 'u1', storage })).toBe(false)
    saveLookupColumnsPreference(
      'User',
      { hidden: ['email'], profile: 'compact' },
      { preferenceKey: 'owner', userScope: 'u1', storage }
    )
    expect(hasLookupColumnsPreference('User', { preferenceKey: 'owner', userScope: 'u1', storage })).toBe(true)
    expect(hasLookupColumnsPreference('User', { preferenceKey: 'owner', userScope: 'u2', storage })).toBe(false)
  })

  it('should persist and load last profile per object and user scope', () => {
    const storage = createStorage()
    expect(loadLastLookupProfile('User', { userScope: 'u1', storage })).toBe('standard')

    saveLastLookupProfile('User', 'compact', { userScope: 'u1', storage })
    saveLastLookupProfile('User', 'custom', { userScope: 'u2', storage })

    expect(loadLastLookupProfile('User', { userScope: 'u1', storage })).toBe('compact')
    expect(loadLastLookupProfile('User', { userScope: 'u2', storage })).toBe('custom')
  })
})
