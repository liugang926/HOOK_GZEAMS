import { beforeEach, describe, expect, it, vi } from 'vitest'
import {
  readStorageJson,
  readStorageString,
  removeStorageKey,
  writeStorageJson,
  writeStorageString
} from '@/platform/storage/browserStorage'

const storageState = new Map<string, string>()

describe('browserStorage', () => {
  beforeEach(() => {
    storageState.clear()
    vi.mocked(localStorage.getItem).mockImplementation((key: string) => {
      return storageState.has(key) ? storageState.get(key)! : null
    })
    vi.mocked(localStorage.setItem).mockImplementation((key: string, value: string) => {
      storageState.set(key, String(value))
    })
    vi.mocked(localStorage.removeItem).mockImplementation((key: string) => {
      storageState.delete(key)
    })
  })

  it('reads and writes normalized string values', () => {
    expect(readStorageString('k1', 'fallback')).toBe('fallback')
    writeStorageString(' k1 ', ' value-1 ')
    expect(readStorageString('k1')).toBe('value-1')
  })

  it('removes keys safely', () => {
    writeStorageString('k2', 'value-2')
    expect(readStorageString('k2')).toBe('value-2')
    removeStorageKey('k2')
    expect(readStorageString('k2')).toBe('')
  })

  it('reads and writes json payloads with fallback', () => {
    expect(readStorageJson('k3', { count: 0 })).toEqual({ count: 0 })
    writeStorageJson('k3', { count: 2 })
    expect(readStorageJson('k3', { count: 0 })).toEqual({ count: 2 })
    storageState.set('k3', '{broken-json')
    expect(readStorageJson('k3', { count: 0 })).toEqual({ count: 0 })
  })
})
