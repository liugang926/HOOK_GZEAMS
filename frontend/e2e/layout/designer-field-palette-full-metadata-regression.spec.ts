import { expect, test, type Route } from '@playwright/test'

const OBJECT_CODE = 'Asset'

function fulfillSuccess(route: Route, data: unknown) {
  return route.fulfill({
    status: 200,
    contentType: 'application/json',
    body: JSON.stringify({ success: true, data })
  })
}

test.describe('Layout Designer Field Palette Metadata Merge Regression', () => {
  test('palette should include metadata fields that are missing from runtime layout fields', async ({ page }) => {
    await page.addInitScript(() => {
      localStorage.setItem('access_token', 'e2e-designer-palette-merge-token')
      localStorage.setItem('current_org_id', 'org-e2e')
      localStorage.setItem('locale', 'en-US')
    })

    await page.route('**/*', async (route) => {
      const url = new URL(route.request().url())
      const pathname = url.pathname

      if (!pathname.startsWith('/api/')) return route.continue()

      if (pathname.endsWith('/api/system/objects/User/me/')) {
        return fulfillSuccess(route, {
          id: 'user-e2e',
          username: 'admin',
          roles: ['admin'],
          permissions: ['*'],
          primaryOrganization: { id: 'org-e2e', name: 'E2E Org', code: 'E2E' }
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

      if (pathname.endsWith(`/api/system/objects/${OBJECT_CODE}/runtime/`)) {
        return fulfillSuccess(route, {
          runtimeVersion: 1,
          mode: 'edit',
          context: 'form',
          fields: {
            editableFields: [
              {
                code: 'asset_name',
                name: 'Asset Name',
                label: 'Asset Name',
                fieldType: 'text',
                showInDetail: true,
                showInForm: true,
                showInList: true
              }
            ],
            reverseRelations: []
          },
          layout: {
            id: 'layout-asset-default',
            mode: 'edit',
            status: 'published',
            version: 1,
            layoutConfig: {
              sections: [
                {
                  id: 'section-basic',
                  type: 'section',
                  title: 'Basic Information',
                  columns: 2,
                  fields: [{ fieldCode: 'asset_name', label: 'Asset Name', fieldType: 'text', span: 12 }]
                }
              ]
            }
          },
          permissions: { view: true, add: true, change: true, delete: true },
          isDefault: true
        })
      }

      if (pathname.endsWith(`/api/system/objects/${OBJECT_CODE}/metadata/`)) {
        return fulfillSuccess(route, {
          code: OBJECT_CODE,
          name: OBJECT_CODE,
          fields: [
            { code: 'asset_name', name: 'Asset Name', fieldType: 'text' },
            { code: 'asset_code', name: 'Asset Code', fieldType: 'text' },
            { code: 'purchase_date', name: 'Purchase Date', fieldType: 'date' }
          ],
          permissions: { view: true, change: true, delete: true }
        })
      }

      return fulfillSuccess(route, {})
    })

    await page.goto(
      `/system/page-layouts/designer?objectCode=${OBJECT_CODE}&layoutType=edit&layoutName=Asset%20Layout&businessObjectId=bo-asset`
    )

    const ensurePaletteFieldPresent = async (fieldCode: string) => {
      const allItems = page.locator(`[data-testid="layout-palette-field-${fieldCode}"]`)
      expect(await allItems.count()).toBeGreaterThan(0)

      const itemAny = allItems.first()
      if (!(await itemAny.isVisible())) {
        const groupHeader = itemAny
          .locator('xpath=ancestor::div[contains(@class,"field-group")][1]//div[contains(@class,"group-header")]')
          .first()
        await groupHeader.click()
      }
      await expect(allItems.first()).toBeVisible()
    }

    await expect(page.getByTestId('layout-designer')).toBeVisible()
    await expect(page.locator('[data-testid="layout-canvas-field"][data-field-code="asset_name"]').first()).toBeVisible()
    await ensurePaletteFieldPresent('asset_code')
    await ensurePaletteFieldPresent('purchase_date')
  })
})
