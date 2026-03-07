import { expect, test, type Page, type Route } from '@playwright/test'
import {
  ensureInlineEditMode,
  getDetailContent,
  getDetailFieldItem,
  getHeaderActionButton,
  waitForDetailPageReady,
  waitForLoadingMaskToClear
} from '../helpers/detail-page.helpers'

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
              { fieldCode: 'asset_name', minHeight: 168 },
              { fieldCode: 'asset_code' }
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
    localStorage.setItem('access_token', 'e2e-detail-min-height-token')
    localStorage.setItem('current_org_id', 'org-detail-min-height')
    localStorage.setItem('locale', 'en-US')
  })

  await page.route('**/*', async (route) => {
    const url = new URL(route.request().url())
    const pathname = url.pathname
    if (!pathname.startsWith('/api/')) return route.continue()

    if (pathname.endsWith('/api/system/objects/User/me/')) {
      return fulfillSuccess(route, {
        id: 'user-detail-min-height',
        username: 'admin',
        roles: ['admin'],
        permissions: ['*'],
        primaryOrganization: {
          id: 'org-detail-min-height',
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
      return fulfillSuccess(route, buildRuntimeLayoutResponse())
    }

    if (pathname.endsWith('/api/system/objects/Asset/fields/')) {
      return fulfillSuccess(route, {
        editable_fields: [],
        reverse_relations: [],
        context: 'form'
      })
    }

    if (pathname.endsWith('/api/system/objects/Asset/asset-min-height-1/')) {
      return fulfillSuccess(route, {
        id: 'asset-min-height-1',
        assetName: 'Min Height Asset',
        assetCode: 'ASSET-MIN-001',
        createdBy: { username: 'admin' },
        createdAt: '2026-03-02T08:00:00+08:00',
        updatedBy: { username: 'admin' },
        updatedAt: '2026-03-02T08:30:00+08:00'
      })
    }

    return fulfillSuccess(route, {})
  })
}

test.describe('Detail MinHeight Rendering Regression', () => {
  test('detail and inline edit should both respect layout minHeight', async ({ page }) => {
    await mockApis(page)
    await page.goto('/objects/Asset/asset-min-height-1')

    await waitForDetailPageReady(page)
    await waitForLoadingMaskToClear(page)
    await expect(getDetailContent(page)).toContainText('Min Height Asset')

    const detailFieldItem = getDetailFieldItem(page, 'Asset Name')
    await expect(detailFieldItem).toHaveCSS('min-height', '168px')

    await getHeaderActionButton(page, /Edit/i).click()
    await ensureInlineEditMode(page)

    const editFieldItem = getDetailFieldItem(page, 'Asset Name')
    await expect(editFieldItem).toHaveCSS('min-height', '168px')
  })
})
