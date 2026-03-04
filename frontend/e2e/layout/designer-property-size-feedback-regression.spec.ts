import { test, expect, type Route } from '@playwright/test'
import { setDesignerRenderMode, waitForDesignerReady } from '../helpers/page-ready.helpers'

const OBJECT_CODE = 'Asset'
const LAYOUT_ID = 'layout-asset-property-size-feedback'

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
            visible: true
          },
          {
            id: 'field-asset-code',
            fieldCode: 'assetCode',
            label: 'Asset Code',
            fieldType: 'text',
            span: 1,
            visible: true
          }
        ]
      }
    ],
    actions: []
  }
}

test.describe('Layout Designer Property Size Feedback Regression', () => {
  test('property panel span/minHeight updates should show visual feedback on canvas field', async ({ page }) => {
    const layoutConfig = buildLayoutConfig()

    await page.addInitScript(() => {
      localStorage.setItem('access_token', 'e2e-designer-property-size-feedback-token')
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
          layoutCode: `${OBJECT_CODE}_property_size_feedback`,
          layoutName: 'Asset Property Size Feedback',
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
                showInForm: true
              },
              {
                code: 'assetCode',
                name: 'Asset Code',
                label: 'Asset Code',
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
              name: 'Asset Name',
              label: 'Asset Name',
              fieldType: 'text',
              showInDetail: true,
              showInForm: true
            },
            {
              code: 'assetCode',
              name: 'Asset Code',
              label: 'Asset Code',
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
    await setDesignerRenderMode(page, 'design')

    const fieldCard = page.locator('[data-testid="layout-canvas-field"][data-field-id="field-asset-name"]').first()
    await fieldCard.click()

    await page.locator('[data-testid="field-prop-span"] .el-select').first().click()
    await page.locator('.el-select-dropdown__item').filter({ hasText: '2 / 2' }).first().click()

    await expect(page.getByTestId('layout-field-resize-hint')).toBeVisible()
    await expect(page.getByTestId('layout-field-resize-hint-span')).toContainText('2 / 2')
    await expect.poll(async () => Number(await page.locator('.field-renderer[data-field-id="field-asset-name"]').first().getAttribute('data-field-span') || '0')).toBe(2)
    await expect(fieldCard).toHaveClass(/is-size-feedback/)

    const minHeightInput = page.locator('[data-testid="field-prop-minHeight"] input').first()
    await minHeightInput.click()
    await minHeightInput.press('Control+a')
    await minHeightInput.type('184')
    await minHeightInput.press('Enter')

    await expect(page.getByTestId('layout-field-resize-hint-height')).toContainText('184px')
    await expect.poll(async () => await fieldCard.getAttribute('data-field-min-height')).toBe('184')
    await expect(fieldCard).toHaveClass(/is-size-feedback/)
  })
})

