import { test, expect } from '../fixtures/auth.fixture'

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

test.describe('Dynamic List Unified Search Backend E2E', () => {
  for (const objectCode of OBJECT_CODES) {
    test(`${objectCode} unified search should send field query and global search query`, async ({ authenticatedPage: page }) => {
      const token = await page.evaluate(() => localStorage.getItem('access_token') || '')
      const orgId = await page.evaluate(() => localStorage.getItem('current_org_id') || '')
      if (!token || !orgId) test.skip(true, 'Missing auth token or org context in browser session')

      const headers = {
        Authorization: `Bearer ${token}`,
        'X-Organization-ID': orgId
      }

      const metadataRes = await page.request.get(`${API_BASE_URL}/system/objects/${objectCode}/metadata/`, { headers })
      if (!metadataRes.ok()) test.skip(true, `${objectCode} metadata endpoint unavailable`)
      const metadataPayload = (await metadataRes.json()) as AnyRecord
      const fields = ((metadataPayload?.data as AnyRecord)?.fields || []) as AnyRecord[]

      const candidateFields = fields.filter((field) => {
        const code = String(field?.code || '').trim()
        if (!code || SYSTEM_FIELD_CODES.has(code)) return false
        const fieldType = String(field?.fieldType || field?.field_type || 'text').toLowerCase()
        const searchable = field?.isSearchable === true || field?.is_searchable === true
        return searchable && ['text', 'textarea', 'email', 'phone', 'url', 'number'].includes(fieldType)
      })
      if (!candidateFields.length) test.skip(true, `No searchable business fields in ${objectCode} metadata`)

      const listRes = await page.request.get(`${API_BASE_URL}/system/objects/${objectCode}/?page=1&page_size=50`, { headers })
      if (!listRes.ok()) test.skip(true, `${objectCode} list endpoint unavailable`)
      const listPayload = (await listRes.json()) as AnyRecord
      const records = (((listPayload?.data as AnyRecord)?.results || []) as AnyRecord[])
      if (!records.length) test.skip(true, `No ${objectCode} records available for backend UI search test`)

      let matchedField: AnyRecord | null = null
      let matchedValue = ''
      outer: for (const field of candidateFields) {
        for (const record of records) {
          const value = pickRecordValue(record, field)
          if (!value || value.length < 2) continue
          matchedField = field
          matchedValue = value
          break outer
        }
      }
      if (!matchedField || !matchedValue) test.skip(true, `No suitable ${objectCode} field value for unified search assertion`)

      const fieldCode = String(matchedField.code)
      const fieldLabel = String(matchedField.name || matchedField.label || fieldCode)

      await page.goto(`/objects/${objectCode}`)
      await expect(page.locator('.dynamic-list-page .el-table')).toBeVisible()

      const fieldSearchResponsePromise = page.waitForResponse((res) => {
        if (!res.url().includes(`/api/system/objects/${objectCode}/`)) return false
        if (res.request().method() !== 'GET') return false
        const url = new URL(res.url())
        return url.searchParams.get(fieldCode) === matchedValue
      })

      await page.locator('.unified-search-field').click()
      await page.getByRole('option', { name: fieldLabel }).click()
      await page.getByPlaceholder('请输入关键词').fill(matchedValue)
      await page.locator('.search-form-container .el-button--primary').click()

      const fieldSearchResponse = await fieldSearchResponsePromise
      expect(fieldSearchResponse.ok()).toBeTruthy()

      const globalKeyword = matchedValue.slice(0, Math.max(2, Math.min(8, matchedValue.length)))
      const globalSearchResponsePromise = page.waitForResponse((res) => {
        if (!res.url().includes(`/api/system/objects/${objectCode}/`)) return false
        if (res.request().method() !== 'GET') return false
        const url = new URL(res.url())
        return url.searchParams.get('search') === globalKeyword
      })

      await page.locator('.unified-search-field').click()
      await page.locator('.el-select-dropdown:visible .el-select-dropdown__item').first().click()
      await page.getByPlaceholder('请输入关键词').fill(globalKeyword)
      await page.locator('.search-form-container .el-button--primary').click()

      const globalSearchResponse = await globalSearchResponsePromise
      expect(globalSearchResponse.ok()).toBeTruthy()
    })
  }
})
