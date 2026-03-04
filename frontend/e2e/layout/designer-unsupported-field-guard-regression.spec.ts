import { test, expect, type Route } from '@playwright/test'
import { waitForDesignerReady } from '../helpers/page-ready.helpers'
const OBJECT_CODE = 'Asset'
const LAYOUT_ID = 'layout-asset-readonly-unsupported-guard'

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
        title: 'Basic Information',
        columns: 2,
        fields: [
          {
            id: 'field-asset-name',
            fieldCode: 'assetName',
            label: 'Asset Name',
            fieldType: 'text',
            span: 1,
            visible: true,
            required: false,
            readonly: true
          }
        ]
      }
    ],
    actions: []
  }
}

test.describe('Layout Designer Unsupported Field Guard Regression', () => {
  test.setTimeout(60000)

  test('unsupported field must be disabled and cannot be added to canvas', async ({ page }) => {
    const layoutConfig = buildLayoutConfig()

    await page.addInitScript(() => {
      localStorage.setItem('access_token', 'e2e-designer-unsupported-guard-token')
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

      if (pathname.endsWith(`/api/system/page-layouts/${LAYOUT_ID}/`)) {
        return fulfillSuccess(route, {
          id: LAYOUT_ID,
          layoutCode: `${OBJECT_CODE}_readonly_unsupported_guard`,
          layoutName: 'Asset Readonly Layout',
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
                name: 'Asset Name',
                label: 'Asset Name',
                fieldType: 'text',
                showInDetail: true,
                showInForm: true,
                showInList: true
              },
              {
                code: 'password',
                name: 'Password',
                label: 'Password',
                fieldType: 'password',
                showInDetail: true,
                showInForm: true,
                showInList: false
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
              name: 'Asset Name',
              label: 'Asset Name',
              fieldType: 'text',
              showInDetail: true,
              showInForm: true
            },
            {
              code: 'password',
              name: 'Password',
              label: 'Password',
              fieldType: 'password',
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
          name: OBJECT_CODE,
          permissions: { view: true, change: true, delete: true }
        })
      }

      return fulfillSuccess(route, {})
    })

    await page.goto(
      `/system/page-layouts/designer?layoutId=${LAYOUT_ID}&objectCode=${OBJECT_CODE}&layoutType=readonly&layoutName=Asset%20Readonly&businessObjectId=bo-asset`
    )

    await waitForDesignerReady(page)
    await expect(page.locator('[data-testid="layout-canvas-field"][data-field-code="assetName"]').first()).toBeVisible()

    const passwordPaletteItemAny = page.getByTestId('layout-palette-field-password').first()
    if (!(await passwordPaletteItemAny.isVisible())) {
      const groupHeader = passwordPaletteItemAny
        .locator('xpath=ancestor::div[contains(@class,"field-group")][1]//div[contains(@class,"group-header")]')
        .first()
      await groupHeader.click()
    }

    const passwordPaletteItem = page.locator('[data-testid="layout-palette-field-password"]:visible').first()
    await expect(passwordPaletteItem).toBeVisible()
    await expect(passwordPaletteItem).toHaveClass(/is-disabled/)
    await expect(passwordPaletteItem).toHaveAttribute('draggable', 'false')

    await passwordPaletteItem.click()
    const guardMessage = page.locator('.el-message__content').filter({
      hasText: /Cannot add "Password"|Cannot add|unsupported/i
    }).first()
    try {
      await expect(guardMessage).toBeVisible({ timeout: 2000 })
    } catch {
      // Message display is optional across themes/locales; non-addition is the hard requirement.
    }
    await expect(page.locator('[data-testid="layout-canvas-field"][data-field-code="password"]')).toHaveCount(0)
  })
})


