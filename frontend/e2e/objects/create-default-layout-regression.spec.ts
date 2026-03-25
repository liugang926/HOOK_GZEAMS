import { test, expect, type Route } from '@playwright/test'

const OBJECT_CODE = 'Asset'

function fulfillSuccess(route: Route, data: unknown) {
  return route.fulfill({
    status: 200,
    contentType: 'application/json',
    body: JSON.stringify({ success: true, data })
  })
}

test.describe('Create Page Default Layout Regression', () => {
  test('create page should render sorted fields and apply create defaults when layout is missing', async ({ page }) => {
    await page.addInitScript(() => {
      localStorage.setItem('access_token', 'e2e-create-default-layout-token')
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

      if (pathname.endsWith(`/api/system/objects/${OBJECT_CODE}/metadata/`)) {
        return fulfillSuccess(route, {
          code: OBJECT_CODE,
          name: OBJECT_CODE,
          permissions: { view: true, add: true, change: true, delete: true }
        })
      }

      if (pathname.endsWith(`/api/system/objects/${OBJECT_CODE}/runtime/`)) {
        return fulfillSuccess(route, {
          runtimeVersion: 1,
          context: 'form',
          fields: {
            editableFields: [
              {
                code: 'assetCode',
                name: 'Asset Code',
                label: 'Asset Code',
                fieldType: 'text',
                sortOrder: 2,
                defaultValue: 'ASSET-NEW-001',
                showInForm: true
              },
              {
                code: 'assetName',
                name: 'Asset Name',
                label: 'Asset Name',
                fieldType: 'text',
                sortOrder: 1,
                showInForm: true
              },
              {
                code: 'purchaseDate',
                name: 'Purchase Date',
                label: 'Purchase Date',
                fieldType: 'date',
                sortOrder: 3,
                showInForm: true
              }
            ],
            reverseRelations: []
          },
          // Simulate missing layout: engine should fallback to default section + sorted fields
          layout: {},
          isDefault: true
        })
      }

      return fulfillSuccess(route, {})
    })

    await page.goto(`/objects/${OBJECT_CODE}/create`)
    await expect(page.locator('.dynamic-form-page')).toBeVisible()
    await expect(page.locator('.load-error')).toHaveCount(0)

    const labels = (await page.locator('.dynamic-form .el-form-item__label').allTextContents())
      .map((text) => text.replace(/\*/g, '').replace(/:/g, '').trim())
      .filter(Boolean)
    expect(labels.slice(0, 3)).toEqual(['Asset Name', 'Asset Code', 'Purchase Date'])

    const assetCodeInput = page
      .locator('.dynamic-form .el-form-item')
      .filter({ has: page.locator('.el-form-item__label', { hasText: 'Asset Code' }) })
      .locator('input')
      .first()
    await expect(assetCodeInput).toHaveValue('ASSET-NEW-001')
  })
})
