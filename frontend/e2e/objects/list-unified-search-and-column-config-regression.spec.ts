import { test, expect, type Route, type Page } from '@playwright/test'

const OBJECT_CODE = 'Asset'

const metadataFields = [
  {
    code: 'asset_name',
    name: 'Asset Name',
    fieldType: 'text',
    isSearchable: true,
    showInList: true
  },
  {
    code: 'asset_code',
    name: 'Asset Code',
    fieldType: 'text',
    isSearchable: false,
    showInList: true
  },
  {
    code: 'serial_number',
    name: 'Serial Number',
    fieldType: 'text',
    isSearchable: false,
    showInList: true
  }
]

const runtimeListFields = [
  {
    code: 'asset_name',
    name: 'Asset Name',
    fieldType: 'text',
    isSearchable: true,
    showInList: true
  }
]

const listRecords = [
  {
    id: 'asset-list-reg-1',
    assetName: 'Unified Search Regression Asset',
    assetCode: 'ASSET-SEARCH-001',
    serialNumber: 'SN-REG-001'
  }
]

function fulfillSuccess(route: Route, data: unknown) {
  return route.fulfill({
    status: 200,
    contentType: 'application/json',
    body: JSON.stringify({ success: true, data })
  })
}

async function mockListPageApis(page: Page, requestQueries: Array<Record<string, string>>) {
  await page.addInitScript(() => {
    localStorage.setItem('access_token', 'e2e-list-unified-search-token')
    localStorage.setItem('current_org_id', 'org-list-regression')
    localStorage.setItem('locale', 'zh-CN')
  })

  await page.route('**/*', async (route) => {
    const url = new URL(route.request().url())
    const pathname = url.pathname
    if (!pathname.startsWith('/api/')) return route.continue()

    if (pathname.endsWith('/api/system/objects/User/me/')) {
      return fulfillSuccess(route, {
        id: 'user-list-regression',
        username: 'admin',
        roles: ['admin'],
        permissions: ['*'],
        primaryOrganization: { id: 'org-list-regression', name: 'Regression Org', code: 'REG' }
      })
    }

    if (pathname.endsWith('/api/system/menu/')) {
      return route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ groups: [], items: [] })
      })
    }
    if (pathname.endsWith('/api/system/menu/flat/')) return fulfillSuccess(route, [])
    if (pathname.endsWith('/api/system/menu/config/')) {
      return route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ schema: {}, common_groups: [], common_icons: [] })
      })
    }

    if (pathname.endsWith(`/api/system/objects/${OBJECT_CODE}/metadata/`)) {
      return fulfillSuccess(route, {
        code: OBJECT_CODE,
        name: OBJECT_CODE,
        fields: metadataFields,
        permissions: { view: true, add: true, change: true, delete: true },
        layouts: {
          list: {
            columns: [{ fieldCode: 'asset_name', label: 'Asset Name', visible: true }]
          }
        }
      })
    }

    if (pathname.endsWith(`/api/system/objects/${OBJECT_CODE}/runtime/`)) {
      const mode = url.searchParams.get('mode') || 'list'
      if (mode === 'list') {
        return fulfillSuccess(route, {
          runtime_version: 1,
          mode: 'list',
          context: 'list',
          fields: {
            editable_fields: runtimeListFields,
            reverse_relations: []
          },
          layout: {
            layout_type: 'list',
            layout_config: {
              columns: [{ fieldCode: 'asset_name', label: 'Asset Name', visible: true }]
            },
            status: 'published',
            version: '1.0.0'
          },
          is_default: false
        })
      }
      return fulfillSuccess(route, {})
    }

    if (pathname.endsWith(`/api/system/objects/${OBJECT_CODE}/`)) {
      const query: Record<string, string> = {}
      url.searchParams.forEach((value, key) => {
        query[key] = value
      })
      requestQueries.push(query)
      return fulfillSuccess(route, {
        count: listRecords.length,
        next: null,
        previous: null,
        results: listRecords
      })
    }

    return fulfillSuccess(route, {})
  })
}

test.describe('List Unified Search And Column Config Regression', () => {
  test('should map unified search to field query or global search query', async ({ page }) => {
    const requestQueries: Array<Record<string, string>> = []
    await mockListPageApis(page, requestQueries)

    await page.goto(`/objects/${OBJECT_CODE}`)
    await expect(page.locator('.dynamic-list-page .el-table')).toBeVisible()
    await expect(page.locator('.dynamic-list-page')).toContainText('Unified Search Regression Asset')

    // Remove initial load query, keep only search-triggered requests.
    requestQueries.length = 0

    await page.locator('.unified-search-field').click()
    await page.getByRole('option', { name: 'Asset Code' }).click()
    await page.getByPlaceholder('请输入关键词').fill('ASSET-SEARCH-001')
    await page.locator('.search-form-container .el-button--primary').click()

    await expect.poll(() => requestQueries.at(-1)?.asset_code || '').toBe('ASSET-SEARCH-001')
    await expect.poll(() => requestQueries.at(-1)?.search || '').toBe('')

    await page.locator('.unified-search-field').click()
    await page.getByRole('option', { name: '全部字段' }).click()
    await page.getByPlaceholder('请输入关键词').fill('Regression')
    await page.locator('.search-form-container .el-button--primary').click()

    await expect.poll(() => requestQueries.at(-1)?.search || '').toBe('Regression')
    await expect.poll(() => requestQueries.at(-1)?.asset_code || '').toBe('')
  })

  test('column manager should include fields outside runtime layout columns', async ({ page }) => {
    const requestQueries: Array<Record<string, string>> = []
    await mockListPageApis(page, requestQueries)

    await page.goto(`/objects/${OBJECT_CODE}`)
    await expect(page.locator('.dynamic-list-page .el-table')).toBeVisible()

    await page.locator('.column-manager-trigger .el-button').click()
    const manager = page.locator('.column-manager')
    await expect(manager).toBeVisible()
    await expect(manager).toContainText('Asset Name')
    await expect(manager).toContainText('Asset Code')
    await expect(manager).toContainText('Serial Number')
  })
})
