import { beforeEach, describe, expect, it, vi } from 'vitest'
import {
  clearStoredLocaleSource,
  getStoredLocale,
  getStoredLocaleSource,
  setStoredLocale,
  setStoredLocaleSource
} from '@/platform/i18n/localePreference'

const storageState = new Map<string, string>()

describe('localePreference', () => {
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

  it('reads locale with fallback', () => {
    expect(getStoredLocale()).toBe('zh-CN')
    storageState.set('locale', 'en-US')
    expect(getStoredLocale()).toBe('en-US')
  })

  it('writes locale only when non-empty', () => {
    setStoredLocale('en-US')
    expect(storageState.get('locale')).toBe('en-US')

    setStoredLocale('')
    expect(storageState.get('locale')).toBe('en-US')
  })

  it('handles locale source lifecycle', () => {
    expect(getStoredLocaleSource()).toBe('')
    setStoredLocaleSource('local')
    expect(getStoredLocaleSource()).toBe('local')
    setStoredLocaleSource('profile')
    expect(getStoredLocaleSource()).toBe('profile')
    clearStoredLocaleSource()
    expect(getStoredLocaleSource()).toBe('')
  })
})
