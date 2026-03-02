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
              { fieldCode: 'asset_code' },
              { fieldCode: 'purchase_date' }
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
        asset_name: 'Shared Layout Asset',
        asset_code: 'ASSET-SHARED-001',
        purchase_date: '2026-02-26',
        created_by: { username: 'admin' },
        created_at: '2026-02-26T08:00:00+08:00',
        updated_by: { username: 'admin' },
        updated_at: '2026-02-26T08:30:00+08:00'
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

test.describe('Detail/Edit Shared Layout Model', () => {
  test('detail view and edit drawer should follow the same edit layout field order', async ({ page }) => {
    const state = { readonlyCalls: 0 }
    await mockApis(page, state)

    await page.goto('/objects/Asset/asset-shared-layout-1')

    await expect(page.locator('.load-error')).toHaveCount(0)
    await expect(page.locator('.detail-content')).toContainText('Shared Layout Asset')
    await expect(page.locator('.detail-content')).toContainText('ASSET-SHARED-001')

    const detailLabels = normalizeLabels(
      await page.locator('.detail-content .field-label').allTextContents()
    )
    expect(detailLabels.slice(0, 3)).toEqual(['AssetName', 'AssetCode', 'PurchaseDate'])

    await page.locator('.header-actions .el-button').first().click()
    const openedDrawer = page.locator('.el-drawer.open')
    await expect(openedDrawer).toBeVisible()

    const drawerLabels = normalizeLabels(
      await openedDrawer.locator('.el-form-item__label').allTextContents()
    )
    expect(drawerLabels.slice(0, 3)).toEqual(['AssetName', 'AssetCode', 'PurchaseDate'])

    expect(state.readonlyCalls).toBe(0)
  })
})
