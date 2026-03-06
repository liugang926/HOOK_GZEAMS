import { beforeEach, describe, expect, it, vi } from 'vitest'
import {
  clearStoredAccessToken,
  clearStoredCurrentOrgId,
  getStoredAccessToken,
  getStoredCurrentOrgId,
  setStoredAccessToken,
  setStoredCurrentOrgId
} from '@/platform/auth/sessionPreference'

const storageState = new Map<string, string>()

describe('sessionPreference', () => {
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

  it('reads and writes access token', () => {
    expect(getStoredAccessToken()).toBe('')
    setStoredAccessToken('token-1')
    expect(getStoredAccessToken()).toBe('token-1')
    clearStoredAccessToken()
    expect(getStoredAccessToken()).toBe('')
  })

  it('ignores empty access token writes', () => {
    setStoredAccessToken('token-1')
    setStoredAccessToken(' ')
    expect(getStoredAccessToken()).toBe('token-1')
  })

  it('reads and writes current organization id', () => {
    expect(getStoredCurrentOrgId()).toBe('')
    setStoredCurrentOrgId('org-1')
    expect(getStoredCurrentOrgId()).toBe('org-1')
    clearStoredCurrentOrgId()
    expect(getStoredCurrentOrgId()).toBe('')
  })
})
