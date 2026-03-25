import { test, expect } from '@playwright/test'
import { apiRequest } from '../helpers/api.helpers'

type AnyRecord = Record<string, unknown>

const API_BASE_URL = process.env.API_BASE_URL || 'http://127.0.0.1:8000/api'
const OBJECT_CODES = ['Asset', 'Supplier', 'Department'] as const

const SYSTEM_FIELD_CODES = new Set([
  'id',
  'created_at',
  'updated_at',
  'created_by',
  'updated_by',
  'is_deleted',
  'deleted_at'
])

const toCamelCase = (value: string): string => {
  return value.replace(/_([a-z])/g, (_, ch: string) => ch.toUpperCase())
}

const pickRecordValue = (record: AnyRecord, field: AnyRecord): string => {
  const code = String(field?.code || '').trim()
  const dataKey = String(field?.dataKey || field?.data_key || '').trim()
  const keyCandidates = [code, toCamelCase(code), dataKey, toCamelCase(dataKey)].filter(Boolean)

  for (const key of keyCandidates) {
    const value = record?.[key]
    if (value === undefined || value === null) continue
    if (typeof value === 'string' && value.trim()) return value.trim()
    if (typeof value === 'number') return String(value)
  }
  return ''
}

async function loginForContractTest(): Promise<{ token: string; orgId: string }> {
  const username = process.env.E2E_USERNAME || 'admin'
  const password = process.env.E2E_PASSWORD || 'admin123'

  const response = await fetch(`${API_BASE_URL}/auth/login/`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ username, password })
  })

  if (!response.ok) return { token: '', orgId: '' }

  const payload = (await response.json()) as AnyRecord
  const data = (payload?.data || {}) as AnyRecord
  const token = String(data?.token || '')
  const orgId = String(
    data?.organization?.id ||
    data?.user?.primaryOrganization?.id ||
    data?.user?.currentOrganization ||
    ''
  )

  return { token, orgId }
}

test.describe('Dynamic Object List Search Backend Contract', () => {
  for (const objectCode of OBJECT_CODES) {
    test(`${objectCode}: field filter and global search should match real backend behavior`, async () => {
      const { token, orgId } = await loginForContractTest()
      if (!token) test.skip(true, 'Missing E2E auth token')
      if (!orgId) test.skip(true, 'Missing organization context for dynamic object query')

      const requestOptions = {
        headers: {
          'X-Organization-ID': orgId
        }
      }

      const metadataRes = await apiRequest<AnyRecord>(`/system/objects/${objectCode}/metadata/`, token, requestOptions)
      if (!metadataRes.success) test.skip(true, `${objectCode} metadata endpoint unavailable`)

      const fields = (metadataRes.data?.fields || []) as AnyRecord[]
      const businessFields = fields.filter((field) => {
        const code = String(field?.code || '').trim()
        if (!code || SYSTEM_FIELD_CODES.has(code)) return false
        const fieldType = String(field?.fieldType || field?.field_type || 'text').toLowerCase()
        return ['text', 'textarea', 'email', 'phone', 'url', 'number'].includes(fieldType)
      })

      if (!businessFields.length) test.skip(true, 'No searchable business fields from metadata')

      const listRes = await apiRequest<AnyRecord>(`/system/objects/${objectCode}/?page=1&page_size=50`, token, requestOptions)
      if (!listRes.success) test.skip(true, `${objectCode} list endpoint unavailable`)
      const records = (listRes.data?.results || []) as AnyRecord[]
      if (!records.length) test.skip(true, `No ${objectCode} records available for search contract test`)

      let matchedField: AnyRecord | null = null
      let matchedRecord: AnyRecord | null = null
      let matchedValue = ''

      const preferredSearchable = businessFields.filter((field) => field?.isSearchable === true || field?.is_searchable === true)
      const fallbackFields = businessFields.filter((field) => !(field?.isSearchable === true || field?.is_searchable === true))
      const candidateFields = [...preferredSearchable, ...fallbackFields]

      outer: for (const field of candidateFields) {
        for (const record of records) {
          const value = pickRecordValue(record, field)
          if (!value || value.length < 2) continue
          matchedField = field
          matchedRecord = record
          matchedValue = value
          break outer
        }
      }

      if (!matchedField || !matchedRecord || !matchedValue) {
        test.skip(true, `No suitable ${objectCode} field value found for contract assertion`)
      }

      const fieldCode = String(matchedField.code)
      const recordId = String(matchedRecord.id)

      const fieldFilterRes = await apiRequest<AnyRecord>(
        `/system/objects/${objectCode}/?${encodeURIComponent(fieldCode)}=${encodeURIComponent(matchedValue)}&page=1&page_size=50`,
        token,
        requestOptions
      )

      expect(fieldFilterRes.success).toBeTruthy()
      const fieldFiltered = (fieldFilterRes.data?.results || []) as AnyRecord[]
      expect(
        fieldFiltered.some((item) => String(item?.id) === recordId),
        `Field filter expected record ${recordId} via ${fieldCode}=${matchedValue}, got ${fieldFiltered.length} rows`
      ).toBeTruthy()

      const isSearchable = matchedField?.isSearchable === true || matchedField?.is_searchable === true
      if (!isSearchable) test.skip(true, `Field ${fieldCode} not marked searchable; skip global search assertion`)

      const globalSearchRes = await apiRequest<AnyRecord>(
        `/system/objects/${objectCode}/?search=${encodeURIComponent(matchedValue)}&page=1&page_size=50`,
        token,
        requestOptions
      )

      expect(globalSearchRes.success).toBeTruthy()
      const globalFiltered = (globalSearchRes.data?.results || []) as AnyRecord[]
      expect(
        globalFiltered.some((item) => String(item?.id) === recordId),
        `Global search expected record ${recordId} via search=${matchedValue}, got ${globalFiltered.length} rows`
      ).toBeTruthy()
    })
  }
})
