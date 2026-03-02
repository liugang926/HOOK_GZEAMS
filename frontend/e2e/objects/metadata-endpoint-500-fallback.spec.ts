import { test, expect, type Route } from '@playwright/test'

const assetId = 'asset-500-1'
const assetRecord = {
  id: assetId,
  assetCode: 'ASSET-500-001',
  assetName: 'Metadata Failure Regression Asset',
  createdAt: '2026-02-26T09:00:00+08:00',
  updatedAt: '2026-02-26T09:30:00+08:00',
  createdBy: { username: 'admin' },
  updatedBy: { username: 'admin' }
}

const fields = [
  {
    code: 'asset_code',
    name: 'Asset Code',
    fieldType: 'text',
    showInDetail: true,
    showInForm: true,
    showInList: true
  },
  {
    code: 'asset_name',
    name: 'Asset Name',
    fieldType: 'text',
    showInDetail: true,
    showInForm: true,
    showInList: true
  }
]

function fulfill(route: Route, data: unknown, status = 200) {
  return route.fulfill({
    status,
    contentType: 'application/json',
    body: JSON.stringify({ success: status < 400, data })
  })
}

test.describe('Metadata 500 Fallback Regression', () => {
  test('Asset list/detail/form should still render business content when metadata endpoint returns 500', async ({ page }) => {
    let metadataCallCount = 0

    await page.addInitScript(() => {
      localStorage.setItem('access_token', 'e2e-metadata-500-token')
      localStorage.setItem('current_org_id', 'org-metadata-500')
    })

    await page.route('**/*', async (route) => {
      const url = new URL(route.request().url())
      const pathname = url.pathname
      if (!pathname.startsWith('/api/')) return route.continue()

      if (pathname.endsWith('/api/system/objects/User/me/')) {
        return fulfill(route, {
          id: 'user-metadata-500',
          username: 'admin',
          roles: ['admin'],
          permissions: ['*'],
          primaryOrganization: { id: 'org-metadata-500', name: 'Regression Org', code: 'REG' }
        })
      }

      if (pathname.endsWith('/api/system/menu/')) {
        return route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({ groups: [], items: [] })
        })
      }
      if (pathname.endsWith('/api/system/menu/flat/')) return fulfill(route, [])
      if (pathname.endsWith('/api/system/menu/config/')) {
        return route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({ schema: {}, common_groups: [], common_icons: [] })
        })
      }

      if (pathname.endsWith('/api/system/objects/Asset/metadata/')) {
        metadataCallCount += 1
        return route.fulfill({
          status: 500,
          contentType: 'application/json',
          body: JSON.stringify({
            success: false,
            error: {
              code: 'INTERNAL_SERVER_ERROR',
              message: 'e2e injected metadata failure'
            }
          })
        })
      }

      if (pathname.endsWith('/api/system/objects/Asset/runtime/')) {
        const mode = url.searchParams.get('mode') || 'edit'
        if (mode === 'list') {
          return fulfill(route, {
            runtime_version: 1,
            mode,
            context: 'list',
            fields: {
              editable_fields: fields,
              reverse_relations: []
            },
            layout: {
              layout_type: 'list',
              layout_config: {
                columns: [
                  { fieldCode: 'asset_code', label: 'Asset Code', visible: true },
                  { fieldCode: 'asset_name', label: 'Asset Name', visible: true }
                ]
              },
              status: 'published',
              version: '1.0.0'
            },
            is_default: false
          })
        }

        return fulfill(route, {
          runtime_version: 1,
          mode,
          context: mode === 'readonly' ? 'detail' : 'form',
          fields: {
            editable_fields: fields,
            reverse_relations: []
          },
          layout: {
            layout_type: mode === 'readonly' ? 'detail' : 'form',
            layout_config: {
              sections: [
                {
                  id: 'basic',
                  type: 'section',
                  title: 'Basic',
                  columns: 2,
                  fields: [
                    { id: 'f1', fieldCode: 'asset_code', label: 'Asset Code', span: 1 },
                    { id: 'f2', fieldCode: 'asset_name', label: 'Asset Name', span: 1 }
                  ]
                }
              ]
            },
            status: 'published',
            version: '1.0.0'
          },
          is_default: false
        })
      }

      if (pathname.endsWith('/api/system/objects/Asset/fields/')) {
        return fulfill(route, {
          editable_fields: fields,
          reverse_relations: [],
          context: 'detail'
        })
      }

      if (pathname.endsWith('/api/system/objects/Asset/')) {
        return fulfill(route, {
          count: 1,
          next: null,
          previous: null,
          results: [assetRecord]
        })
      }

      if (pathname.endsWith(`/api/system/objects/Asset/${assetId}/`)) {
        return fulfill(route, assetRecord)
      }

      return fulfill(route, {})
    })

    await page.goto('/objects/Asset')
    await page.locator('.el-loading-mask').first().waitFor({ state: 'detached' }).catch(() => {})
    await expect(page.locator('.load-error')).toHaveCount(0)
    await expect(page.locator('.dynamic-list-page .el-table')).toBeVisible()
    await expect(page.locator('.dynamic-list-page')).toContainText('ASSET-500-001')

    await page.goto(`/objects/Asset/${assetId}`)
    await page.locator('.el-loading-mask').first().waitFor({ state: 'detached' }).catch(() => {})
    await expect(page.locator('.load-error')).toHaveCount(0)
    await expect(page.locator('.dynamic-detail-page .field-item')).toHaveCount(2)
    await expect(page.locator('.detail-content').first()).toContainText('ASSET-500-001')
    await expect(page.locator('.detail-content').first()).toContainText('Metadata Failure Regression Asset')

    await page.goto(`/objects/Asset/${assetId}/edit`)
    await page.locator('.el-loading-mask').first().waitFor({ state: 'detached' }).catch(() => {})
    await expect(page.locator('.load-error')).toHaveCount(0)
    await expect(page.locator('.dynamic-form .el-form-item')).toHaveCount(2)
    await expect(page.locator('.dynamic-form')).toContainText('Asset Code')
    await expect(page.locator('.dynamic-form')).toContainText('Asset Name')

    expect(metadataCallCount).toBeGreaterThanOrEqual(3)
  })
})
