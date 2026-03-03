import { expect, test, type Page, type Route } from '@playwright/test'

function fulfillSuccess(route: Route, data: unknown) {
  return route.fulfill({
    status: 200,
    contentType: 'application/json',
    body: JSON.stringify({ success: true, data })
  })
}

function buildRuntimeResponse() {
  return {
    runtime_version: 1,
    mode: 'edit',
    context: 'form',
    fields: {
      editable_fields: [
        {
          code: 'asset_code',
          name: 'Asset Code',
          fieldType: 'text',
          isHidden: false,
          showInForm: true,
          showInDetail: true,
          sortOrder: 1
        },
        {
          code: 'asset_name',
          name: 'Asset Name',
          fieldType: 'text',
          isHidden: false,
          showInForm: true,
          showInDetail: true,
          sortOrder: 2
        },
        {
          code: 'purchase_date',
          name: 'Purchase Date',
          fieldType: 'date',
          isHidden: false,
          showInForm: true,
          showInDetail: true,
          sortOrder: 3
        },
        {
          code: 'status',
          name: 'Status',
          fieldType: 'select',
          isHidden: false,
          showInForm: true,
          showInDetail: true,
          sortOrder: 4,
          options: [
            { label: 'Active', value: 'active' },
            { label: 'Inactive', value: 'inactive' }
          ]
        }
      ],
      reverse_relations: []
    },
    layout: {
      layout_type: 'form',
      layout_config: {
        sections: [
          {
            id: 'basic',
            title: 'Basic',
            columns: 2,
            fields: [
              { fieldCode: 'asset_code', readonly: true },
              { fieldCode: 'asset_name' },
              { fieldCode: 'purchase_date' },
              { fieldCode: 'status' }
            ]
          }
        ]
      },
      status: 'published',
      version: '1.0.0'
    },
    permissions: {
      view: true,
      add: true,
      change: true,
      delete: true
    },
    is_default: true
  }
}

async function mockApis(page: Page) {
  await page.addInitScript(() => {
    localStorage.setItem('access_token', 'e2e-edit-page-field-render-token')
    localStorage.setItem('current_org_id', 'org-edit-page-field-render')
    localStorage.setItem('locale', 'en-US')
  })

  await page.route('**/*', async (route) => {
    const url = new URL(route.request().url())
    const pathname = url.pathname
    if (!pathname.startsWith('/api/')) return route.continue()

    if (pathname.endsWith('/api/system/objects/User/me/')) {
      return fulfillSuccess(route, {
        id: 'user-edit-page-field-render',
        username: 'admin',
        roles: ['admin'],
        permissions: ['*'],
        primaryOrganization: {
          id: 'org-edit-page-field-render',
          name: 'Regression Org',
          code: 'REG'
        }
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

    if (pathname.endsWith('/api/system/objects/Asset/metadata/')) {
      return fulfillSuccess(route, {
        code: 'Asset',
        name: 'Asset',
        permissions: { view: true, add: true, change: true, delete: true }
      })
    }

    if (pathname.endsWith('/api/system/objects/Asset/runtime/')) {
      return fulfillSuccess(route, buildRuntimeResponse())
    }

    if (pathname.endsWith('/api/system/objects/Asset/asset-edit-page-1/')) {
      return fulfillSuccess(route, {
        id: 'asset-edit-page-1',
        asset_code: '',
        assetCode: 'ASSET-EDIT-001',
        assetName: 'Edit Page Asset',
        purchaseDate: '2026-02-27',
        status: 'active'
      })
    }

    return fulfillSuccess(route, {})
  })
}

async function hasInputWithValue(page: Page, value: string) {
  return page.evaluate((v) => {
    const inputs = Array.from(document.querySelectorAll('input, textarea')) as Array<
      HTMLInputElement | HTMLTextAreaElement
    >
    return inputs.some((el) => el.value === v || el.value.includes(v))
  }, value)
}

test.describe('Edit Page Field Rendering Regression', () => {
  test('edit page should render value/type/readonly correctly with snake-camel mixed payload', async ({ page }) => {
    await mockApis(page)

    await page.goto('/objects/Asset/asset-edit-page-1/edit')

    await expect(page.locator('.load-error')).toHaveCount(0)
    await expect(page).toHaveURL(/\/objects\/Asset\/asset-edit-page-1\?action=edit/)
    await expect(page.locator('.dynamic-detail-page').first()).toBeVisible()
    await expect.poll(async () => hasInputWithValue(page, 'ASSET-EDIT-001')).toBe(true)
    await expect.poll(async () => hasInputWithValue(page, 'Edit Page Asset')).toBe(true)

    const formRoot = page.locator('.detail-content')
    const codeField = formRoot.locator('.field-item').filter({
      has: page.locator('.field-label', { hasText: 'Asset Code' })
    }).first()
    const dateField = formRoot.locator('.field-item').filter({
      has: page.locator('.field-label', { hasText: 'Purchase Date' })
    }).first()
    const statusField = formRoot.locator('.field-item').filter({
      has: page.locator('.field-label', { hasText: 'Status' })
    }).first()

    await expect(codeField.locator('input')).toHaveValue('ASSET-EDIT-001')
    await expect(codeField.locator('input')).toBeDisabled()
    await expect(dateField.locator('.el-date-editor')).toHaveCount(1)
    await expect(statusField.locator('.el-select')).toHaveCount(1)
  })
})
