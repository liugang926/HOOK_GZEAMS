import { test, expect, type Route } from '@playwright/test'
import { waitForDesignerReady } from '../helpers/page-ready.helpers'
type AnyRecord = Record<string, any>

const OBJECT_CODE = 'Asset'
const LAYOUT_ID = 'layout-asset-locale-persistence'
const UPDATED_LABEL = 'Asset Name Unsaved'

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

test.describe('Layout Designer Locale Switch Persistence Regression', () => {
  test('unsaved designer state should persist after locale switch', async ({ page }) => {
    let activeLayoutConfig = buildLayoutConfig()

    await page.addInitScript(() => {
      localStorage.setItem('access_token', 'e2e-designer-locale-switch-token')
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
        if (route.request().method() === 'PATCH') {
          const body = route.request().postDataJSON() as AnyRecord
          const next = (body?.layoutConfig || body?.layout_config) as AnyRecord
          if (next?.sections?.length) activeLayoutConfig = next
        }

        return fulfillSuccess(route, {
          id: LAYOUT_ID,
          layoutCode: `${OBJECT_CODE}_readonly_locale_persistence`,
          layoutName: 'Asset Readonly Layout',
          mode: 'readonly',
          status: 'draft',
          version: 1,
          isDefault: false,
          layoutConfig: activeLayoutConfig
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
              }
            ],
            reverseRelations: []
          },
          layout: {
            id: LAYOUT_ID,
            mode: 'readonly',
            status: 'draft',
            version: 1,
            layoutConfig: activeLayoutConfig
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

    const previewField = page.locator('[data-testid="layout-canvas-field"][data-field-code="assetName"]').first()
    await previewField.click({ position: { x: 4, y: 4 } })
    await expect(page.getByTestId('layout-field-property-editor')).toBeVisible()

    const labelInput = page.getByTestId('field-prop-label').locator('input').first()
    await labelInput.fill(UPDATED_LABEL)
    await labelInput.press('Tab')
    await expect(page.locator('[data-testid="layout-canvas-field"][data-field-code="assetName"] .el-form-item__label')).toContainText(UPDATED_LABEL)

    const localeTrigger = page.locator('.locale-trigger').first()
    await expect(localeTrigger).toBeVisible()
    await localeTrigger.click()
    await page.locator('.el-dropdown-menu__item:not(.is-disabled)').first().click()

    await waitForDesignerReady(page)
    await expect(labelInput).toHaveValue(UPDATED_LABEL)
    await expect(page.locator('[data-testid="layout-canvas-field"][data-field-code="assetName"] .el-form-item__label')).toContainText(UPDATED_LABEL)
    await expect(page.getByTestId('layout-save-button').first()).toBeEnabled()
  })
})


