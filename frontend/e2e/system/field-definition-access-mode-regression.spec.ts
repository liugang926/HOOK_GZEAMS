import { expect, test, type Page, type Route } from '@playwright/test'

function fulfillSuccess(route: Route, data: unknown) {
  return route.fulfill({
    status: 200,
    contentType: 'application/json',
    body: JSON.stringify({ success: true, data })
  })
}

async function mockShellApis(page: Page) {
  await page.addInitScript(() => {
    localStorage.setItem('access_token', 'e2e-field-definition-access-mode-token')
    localStorage.setItem('current_org_id', 'org-e2e')
    localStorage.setItem('locale', 'en-US')
  })
}

async function mockCustomObjectScenario(page: Page) {
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

    if (pathname.endsWith('/api/system/business-objects/by-code/CustomAsset/')) {
      return fulfillSuccess(route, {
        id: 'bo-custom-asset',
        code: 'CustomAsset',
        name: 'Custom Asset',
        isHardcoded: false
      })
    }

    if (pathname.endsWith('/api/system/field-definitions/by-object/CustomAsset/')) {
      return fulfillSuccess(route, [
        {
          id: 'fd-updated-at',
          code: 'updated_at',
          name: 'Updated At',
          fieldType: 'datetime',
          isRequired: false,
          isReadonly: true,
          isSystem: true,
          sortOrder: 1
        },
        {
          id: 'fd-asset-name',
          code: 'asset_name',
          name: 'Asset Name',
          fieldType: 'text',
          isRequired: true,
          isReadonly: false,
          isSystem: false,
          sortOrder: 2
        }
      ])
    }

    return fulfillSuccess(route, {})
  })
}

async function mockHardcodedObjectScenario(page: Page) {
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

    if (pathname.endsWith('/api/system/business-objects/by-code/Asset/')) {
      return fulfillSuccess(route, {
        id: 'bo-asset',
        code: 'Asset',
        name: 'Asset',
        isHardcoded: true
      })
    }

    if (pathname.endsWith('/api/system/objects/Asset/fields/')) {
      return fulfillSuccess(route, {
        object_code: 'Asset',
        object_name: 'Asset',
        is_hardcoded: true,
        fields: [
          {
            fieldName: 'asset_code',
            displayName: 'Asset Code',
            fieldType: 'text',
            isRequired: true,
            isReadonly: false,
            isEditable: true,
            sortOrder: 1
          }
        ]
      })
    }

    if (pathname.endsWith('/api/system/business-objects/fields/')) {
      return fulfillSuccess(route, {
        object_code: 'Asset',
        object_name: 'Asset',
        is_hardcoded: true,
        fields: []
      })
    }

    return fulfillSuccess(route, {})
  })
}

test.describe('Field Definition Access Mode Regression', () => {
  test.describe.configure({ mode: 'serial' })
  test.setTimeout(60000)

  test('custom object allows edit/delete for business fields but keeps system fields read-only', async ({ page }) => {
    await mockShellApis(page)
    await mockCustomObjectScenario(page)

    await page.goto('/system/field-definitions?objectCode=CustomAsset&objectName=Custom%20Asset')
    await expect(page.getByRole('button', { name: 'Add Field' })).toBeEnabled()

    const systemRow = page.locator('.el-table__row', { hasText: 'updated_at' }).first()
    await expect(systemRow).toBeVisible()
    await expect(systemRow.getByRole('button', { name: 'Edit' })).toBeDisabled()
    await expect(systemRow.getByRole('button', { name: 'Delete' })).toBeDisabled()
    await systemRow.locator('.action-disabled-wrapper').first().hover()
    await expect(page.getByText('System fields cannot be edited or deleted.')).toBeVisible()

    const businessRow = page.locator('.el-table__row', { hasText: 'asset_name' }).first()
    await expect(businessRow).toBeVisible()
    await expect(businessRow.getByRole('button', { name: 'Edit' })).toBeEnabled()
    await expect(businessRow.getByRole('button', { name: 'Delete' })).toHaveCount(1)
  })

  test('hardcoded object remains fully read-only in field management page', async ({ page }) => {
    await mockShellApis(page)
    await mockHardcodedObjectScenario(page)

    await page.goto('/system/field-definitions?objectCode=Asset&objectName=Asset')

    const addButton = page.getByRole('button', { name: 'Add Field' })
    await expect(addButton).toBeDisabled()
    await page.locator('.page-header .action-disabled-wrapper').first().hover()
    await expect(page.getByText('Hardcoded object fields are read-only.')).toBeVisible()

    const assetRow = page.locator('.el-table__row', { hasText: 'asset_code' }).first()
    await expect(assetRow).toBeVisible()
    await expect(assetRow.getByRole('button', { name: 'Edit' })).toBeDisabled()
    await expect(page.locator('.el-table').first().getByRole('button', { name: 'Delete' })).toBeDisabled()
  })
})
