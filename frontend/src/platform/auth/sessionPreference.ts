import {
  readStorageString,
  removeStorageKey,
  writeStorageString
} from '@/platform/storage/browserStorage'

export const ACCESS_TOKEN_STORAGE_KEY = 'access_token'
export const CURRENT_ORG_ID_STORAGE_KEY = 'current_org_id'

export const getStoredAccessToken = (): string => {
  return readStorageString(ACCESS_TOKEN_STORAGE_KEY)
}

export const setStoredAccessToken = (token: unknown): void => {
  writeStorageString(ACCESS_TOKEN_STORAGE_KEY, token)
}

export const clearStoredAccessToken = (): void => {
  removeStorageKey(ACCESS_TOKEN_STORAGE_KEY)
}

export const getStoredCurrentOrgId = (): string => {
  return readStorageString(CURRENT_ORG_ID_STORAGE_KEY)
}

export const setStoredCurrentOrgId = (orgId: unknown): void => {
  writeStorageString(CURRENT_ORG_ID_STORAGE_KEY, orgId)
}

export const clearStoredCurrentOrgId = (): void => {
  removeStorageKey(CURRENT_ORG_ID_STORAGE_KEY)
}
