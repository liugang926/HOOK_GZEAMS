import { test, expect, type Route } from '@playwright/test'

const OBJECT_CODE = 'Asset'

function buildRows(size: number) {
  return Array.from({ length: size }).map((_, index) => ({
    line_no: index + 1,
    item_code: `ITEM-${String(index + 1).padStart(3, '0')}`,
    quantity: index + 1
  }))
}

function fulfillSuccess(route: Route, data: unknown) {
  return route.fulfill({
    status: 200,
    contentType: 'application/json',
    body: JSON.stringify({ success: true, data })
  })
}

test.describe('SubTable First Render Performance', () => {
  test('collects sub-table first screen render telemetry for 200 rows', async ({ page }, testInfo) => {
    const rows = buildRows(200)
    const pageSize = 20
    let runtimeResponseAt = 0

    await page.addInitScript(() => {
      localStorage.setItem('access_token', 'e2e-subtable-perf-token')
      localStorage.setItem('current_org_id', 'org-subtable-perf')
      localStorage.setItem('locale', 'en-US')
    })

    await page.route('**/*', async (route) => {
      const url = new URL(route.request().url())
      const pathname = url.pathname
      if (!pathname.startsWith('/api/')) return route.continue()

      if (pathname.endsWith('/api/system/objects/User/me/')) {
        return fulfillSuccess(route, {
          id: 'user-subtable-perf',
          username: 'admin',
          roles: ['admin'],
          permissions: ['*'],
          primaryOrganization: { id: 'org-subtable-perf', name: 'SubTable Perf Org', code: 'PERF' }
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
          permissions: { view: true, add: true, change: true, delete: true }
        })
      }

      if (pathname.endsWith(`/api/system/objects/${OBJECT_CODE}/runtime/`)) {
        runtimeResponseAt = Date.now()
        return fulfillSuccess(route, {
          runtimeVersion: 1,
          context: 'form',
          fields: {
            editableFields: [
              {
                code: 'asset_code',
                name: 'Asset Code',
                label: 'Asset Code',
                fieldType: 'text',
                showInForm: true,
                sortOrder: 1
              },
              {
                code: 'lineItems',
                name: 'Line Items',
                label: 'Line Items',
                fieldType: 'sub_table',
                field_type: 'sub_table',
                showInForm: true,
                sortOrder: 2,
                defaultValue: rows,
                relatedFields: [
                  { code: 'line_no', name: 'Line No', fieldType: 'number' },
                  { code: 'item_code', name: 'Item Code', fieldType: 'text' },
                  { code: 'quantity', name: 'Quantity', fieldType: 'number' }
                ],
                componentProps: {
                  relatedFields: [
                    { code: 'line_no', name: 'Line No', fieldType: 'number' },
                    { code: 'item_code', name: 'Item Code', fieldType: 'text' },
                    { code: 'quantity', name: 'Quantity', fieldType: 'number' }
                  ]
                }
              }
            ],
            reverseRelations: []
          },
          layout: {
            layoutType: 'form',
            layoutConfig: {
              sections: [
                {
                  id: 'basic',
                  name: 'basic',
                  title: 'Basic',
                  columns: 1,
                  fields: [
                    { fieldCode: 'asset_code', label: 'Asset Code', span: 24 },
                    { fieldCode: 'lineItems', label: 'Line Items', span: 24 }
                  ]
                }
              ]
            }
          },
          isDefault: true
        })
      }

      return fulfillSuccess(route, {})
    })

    await page.goto(`/objects/${OBJECT_CODE}/create`)
    await expect(page.locator('.dynamic-form-page')).toBeVisible()
    await expect(page.locator('.sub-table-field')).toBeVisible({ timeout: 10000 })
    await expect
      .poll(() => page.locator('.sub-table-field .el-table__row').count(), { timeout: 10000 })
      .toBeGreaterThan(0)

    const renderedRowCount = await page.locator('.sub-table-field .el-table__row').count()
    const elapsedMs = Date.now() - runtimeResponseAt
    const targetMs = 1500

    await testInfo.attach('subtable-perf-metrics', {
      body: JSON.stringify(
        {
          objectCode: OBJECT_CODE,
          page: 'create',
          rowCount: rows.length,
          pageSize,
          renderedRowCount,
          elapsedMs,
          targetMs,
          withinTarget: elapsedMs < targetMs
        },
        null,
        2
      ),
      contentType: 'application/json'
    })

    expect(runtimeResponseAt).toBeGreaterThan(0)
    expect(renderedRowCount).toBeGreaterThan(0)
    expect(renderedRowCount).toBeLessThanOrEqual(pageSize)
    await expect(page.locator('.sub-table-field .el-pagination')).toContainText('200')
    expect(elapsedMs).toBeLessThan(targetMs)
  })
})
