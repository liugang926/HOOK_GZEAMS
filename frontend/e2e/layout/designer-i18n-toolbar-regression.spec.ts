import { test, expect, type Page, type Route } from '@playwright/test'
import { waitForDesignerReady } from '../helpers/page-ready.helpers'

const OBJECT_CODE = 'Asset'
const LAYOUT_ID = 'layout-asset-i18n-toolbar'

function fulfillSuccess(route: Route, data: unknown) {
  return route.fulfill({
    status: 200,
    contentType: 'application/json',
    body: JSON.stringify({ success: true, data })
  })
}

function buildLayoutConfig() {
  return {
    sections: [
      {
        id: 'section-basic',
        type: 'section',
        title: '基本信息',
        columns: 2,
        fields: [
          {
            id: 'field-asset-name',
            fieldCode: 'assetName',
            label: '资产名称',
            fieldType: 'text',
            span: 1,
            visible: true,
            readonly: true
          }
        ]
      }
    ],
    actions: []
  }
}

async function mockApis(page: Page) {
  const layoutConfig = buildLayoutConfig()

  await page.addInitScript(() => {
    localStorage.setItem('access_token', 'e2e-designer-i18n-toolbar-token')
    localStorage.setItem('current_org_id', 'org-e2e')
    localStorage.setItem('locale', 'zh-CN')
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

    if (pathname.endsWith(`/api/system/page-layouts/${LAYOUT_ID}/`)) {
      return fulfillSuccess(route, {
        id: LAYOUT_ID,
        layoutCode: `${OBJECT_CODE}_i18n_toolbar`,
        layoutName: '资产布局',
        mode: 'readonly',
        status: 'draft',
        version: 1,
        isDefault: false,
        layoutConfig
      })
    }

    if (pathname.endsWith(`/api/system/objects/${OBJECT_CODE}/runtime/`)) {
      return fulfillSuccess(route, {
        runtimeVersion: 1,
        fields: {
          editableFields: [
            {
              code: 'assetName',
              name: '资产名称',
              label: '资产名称',
              fieldType: 'text',
              showInDetail: true,
              showInForm: true
            }
          ],
          reverseRelations: []
        },
        layout: {
          id: LAYOUT_ID,
          mode: 'readonly',
          status: 'draft',
          version: 1,
          layoutConfig
        }
      })
    }

    if (pathname.endsWith(`/api/system/objects/${OBJECT_CODE}/fields/`)) {
      return fulfillSuccess(route, {
        editable_fields: [
          {
            code: 'assetName',
            name: '资产名称',
            label: '资产名称',
            fieldType: 'text',
            showInDetail: true,
            showInForm: true
          }
        ],
        reverse_relations: [],
        context: 'detail'
      })
    }

    if (pathname.endsWith(`/api/system/objects/${OBJECT_CODE}/metadata/`)) {
      return fulfillSuccess(route, {
        code: OBJECT_CODE,
        name: '资产',
        permissions: { view: true, change: true, delete: true }
      })
    }

    return fulfillSuccess(route, {})
  })
}

test.describe('Layout Designer i18n Toolbar Regression', () => {
  test('zh-CN toolbar/buttons should not show question-mark placeholders', async ({ page }) => {
    await mockApis(page)

    await page.goto(
      `/system/page-layouts/designer?layoutId=${LAYOUT_ID}&objectCode=${OBJECT_CODE}&layoutType=readonly&layoutName=Asset%20Readonly&businessObjectId=bo-asset`
    )
    await waitForDesignerReady(page)

    const toolbar = page.locator('.designer-toolbar')
    await expect(page.getByTestId('layout-undo-button')).toHaveAttribute('aria-label', '撤销')
    await expect(page.getByTestId('layout-redo-button')).toHaveAttribute('aria-label', '重做')
    await expect(toolbar).toContainText('保存草稿')
    await expect(toolbar).toContainText('发布')

    await page.getByTestId('layout-more-button').click()
    await expect(page.locator('.el-dropdown-menu__item:visible').filter({ hasText: '翻译模式' }).first()).toBeVisible()
    await expect(page.locator('.el-dropdown-menu__item:visible').filter({ hasText: '恢复默认' }).first()).toBeVisible()

    const text = await page.locator('.page-layout-designer').innerText()
    expect(text).not.toContain('???')
  })
})
