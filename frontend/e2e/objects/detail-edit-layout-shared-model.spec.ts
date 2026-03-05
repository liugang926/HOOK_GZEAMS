import { expect, test, type Page, type Route } from '@playwright/test'

function fulfillSuccess(route: Route, data: unknown) {
  return route.fulfill({
    status: 200,
    contentType: 'application/json',
    body: JSON.stringify({ success: true, data })
  })
}

function buildRuntimeLayoutResponse() {
  return {
    runtime_version: 1,
    mode: 'edit',
    context: 'form',
    fields: {
      editable_fields: [
        {
          code: 'asset_name',
          name: 'Asset Name',
          fieldType: 'text',
          isHidden: false,
          showInForm: true,
          showInDetail: true,
          sortOrder: 1
        },
        {
          code: 'asset_code',
          name: 'Asset Code',
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
            id: 'overview',
            name: 'overview',
            title: 'Overview',
            columns: 2,
            fields: [
              { fieldCode: 'asset_name' },
              { fieldCode: 'asset_code', readonly: true },
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

async function mockApis(page: Page, state: { readonlyCalls: number }) {
  await page.addInitScript(() => {
    localStorage.setItem('access_token', 'e2e-detail-edit-shared-layout-token')
    localStorage.setItem('current_org_id', 'org-detail-edit-shared-layout')
    localStorage.setItem('locale', 'en-US')
  })

  await page.route('**/*', async (route) => {
    const url = new URL(route.request().url())
    const pathname = url.pathname
    if (!pathname.startsWith('/api/')) return route.continue()

    if (pathname.endsWith('/api/system/objects/User/me/')) {
      return fulfillSuccess(route, {
        id: 'user-detail-edit-shared-layout',
        username: 'admin',
        roles: ['admin'],
        permissions: ['*'],
        primaryOrganization: {
          id: 'org-detail-edit-shared-layout',
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
      const mode = url.searchParams.get('mode') || 'edit'
      if (mode === 'readonly') {
        state.readonlyCalls += 1
        return fulfillSuccess(route, {
          runtime_version: 1,
          mode: 'readonly',
          context: 'detail',
          fields: { editable_fields: [], reverse_relations: [] },
          layout: { layout_type: 'detail', layout_config: { sections: [] } },
          permissions: { view: true, add: true, change: true, delete: true },
          is_default: true
        })
      }
      return fulfillSuccess(route, buildRuntimeLayoutResponse())
    }

    if (pathname.endsWith('/api/system/objects/Asset/fields/')) {
      return fulfillSuccess(route, {
        editable_fields: [
          {
            code: 'created_at',
            name: 'Created At',
            fieldType: 'datetime',
            isHidden: false,
            showInForm: true,
            showInDetail: true,
            isSystem: true
          }
        ],
        reverse_relations: [],
        context: 'form'
      })
    }

    if (pathname.endsWith('/api/system/objects/Asset/asset-shared-layout-1/')) {
      return fulfillSuccess(route, {
        id: 'asset-shared-layout-1',
        asset_code: '',
        assetName: 'Shared Layout Asset',
        assetCode: 'ASSET-SHARED-001',
        purchaseDate: '2026-02-26',
        status: 'active',
        createdBy: { username: 'admin' },
        createdAt: '2026-02-26T08:00:00+08:00',
        updatedBy: { username: 'admin' },
        updatedAt: '2026-02-26T08:30:00+08:00'
      })
    }

    return fulfillSuccess(route, {})
  })
}

function normalizeLabels(values: string[]) {
  return values
    .map((item) => item.replace(/[:\s]/g, '').trim())
    .filter(Boolean)
}

async function hasInputWithValue(page: Page, value: string) {
  return page.evaluate((v) => {
    const inputs = Array.from(document.querySelectorAll('input, textarea')) as Array<
      HTMLInputElement | HTMLTextAreaElement
    >
    return inputs.some((el) => el.value === v || el.value.includes(v))
  }, value)
}

test.describe('Detail/Edit Shared Layout Model', () => {
  test('detail view and inline edit should follow the same edit layout field order', async ({ page }) => {
    const state = { readonlyCalls: 0 }
    await mockApis(page, state)

    await page.goto('/objects/Asset/asset-shared-layout-1')

    await expect(page.locator('.load-error')).toHaveCount(0)
    await expect(page.getByRole('button', { name: 'Edit' })).toBeVisible({ timeout: 15000 })
    const detailSurface = page.locator('body')
    await expect(detailSurface).toContainText('Shared Layout Asset')
    await expect(detailSurface).toContainText('ASSET-SHARED-001')

    const detailLabels = normalizeLabels(
      await detailSurface.locator('.field-label').allTextContents()
    )
    expect(detailLabels.slice(0, 3)).toEqual(['AssetName', 'AssetCode', 'PurchaseDate'])

    await page.locator('.header-actions .el-button').first().click()
    await expect(page.getByRole('button', { name: 'Cancel' })).toBeVisible()
    await expect(page.getByRole('button', { name: 'Save' })).toBeVisible()
    const editSurface = detailSurface

    const drawerLabels = normalizeLabels(
      await editSurface.locator('.el-form-item__label').allTextContents()
    )
    expect(drawerLabels.slice(0, 3)).toEqual(['AssetName', 'AssetCode', 'PurchaseDate'])
    await expect.poll(async () => hasInputWithValue(page, 'ASSET-SHARED-001')).toBe(true)
    await expect.poll(async () => hasInputWithValue(page, 'Shared Layout Asset')).toBe(true)
    const purchaseDateField = editSurface.locator('.field-item').filter({
      has: page.locator('.field-label', { hasText: 'Purchase Date' })
    }).first()
    const assetCodeField = editSurface.locator('.field-item').filter({
      has: page.locator('.field-label', { hasText: 'Asset Code' })
    }).first()
    const statusField = editSurface.locator('.field-item').filter({
      has: page.locator('.field-label', { hasText: 'Status' })
    }).first()
    await expect(assetCodeField.locator('input')).toHaveValue('ASSET-SHARED-001')
    await expect(assetCodeField.locator('input')).toBeDisabled()
    await expect(purchaseDateField.locator('.el-date-editor')).toHaveCount(1)
    await expect(statusField.locator('.el-select')).toHaveCount(1)

    expect(state.readonlyCalls).toBe(0)
  })
})
