import { test, expect, type Route } from '@playwright/test'

const OBJECT_CODE = 'Asset'
const LAYOUT_ID = 'layout-asset-entry-stability'
const DESIGNER_URL =
  `/system/page-layouts/designer?layoutId=${LAYOUT_ID}&objectCode=${OBJECT_CODE}&layoutType=readonly&layoutName=Asset%20Readonly&businessObjectId=bo-asset`

const layoutConfig = {
  sections: [
    {
      id: 'section-basic',
      type: 'section',
      title: 'Basic',
      columns: 1,
      collapsible: false,
      collapsed: false,
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

const delay = (ms: number) => new Promise((resolve) => setTimeout(resolve, ms))

function fulfillSuccess(route: Route, data: unknown) {
  return route.fulfill({
    status: 200,
    contentType: 'application/json',
    body: JSON.stringify({ success: true, data })
  })
}

test.describe('Layout Designer Entry Stability Regression', () => {
  test('designer should render reliably after repeated entries under delayed API responses', async ({ page }) => {
    let runtimeCallCount = 0
    let layoutDetailCallCount = 0

    await page.addInitScript(() => {
      localStorage.setItem('access_token', 'e2e-designer-entry-stability-token')
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
        layoutDetailCallCount += 1
        await delay(60 + (layoutDetailCallCount % 3) * 40)
        return fulfillSuccess(route, {
          id: LAYOUT_ID,
          layoutCode: `${OBJECT_CODE}_readonly_entry_stability`,
          layoutName: 'Asset Readonly Layout',
          mode: 'readonly',
          status: 'draft',
          version: 1,
          isDefault: false,
          layoutConfig
        })
      }

      if (pathname.endsWith(`/api/system/page-layouts/default/${OBJECT_CODE}/edit/`)) {
        return fulfillSuccess(route, {
          layoutConfig
        })
      }

      if (pathname.endsWith(`/api/system/objects/${OBJECT_CODE}/runtime/`)) {
        runtimeCallCount += 1
        await delay(90 + (runtimeCallCount % 4) * 35)
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
                showInList: true,
                isReadonly: false,
                isRequired: false,
                sectionName: 'basic',
                span: 12
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
              showInForm: true,
              showInList: true,
              isSystem: false
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

    for (let round = 0; round < 4; round += 1) {
      await page.goto('/dashboard')
      await page.goto(DESIGNER_URL)

      await expect(page.getByTestId('layout-designer')).toBeVisible()
      await expect(page.getByTestId('layout-preview-current-button').first()).toBeVisible()
      await expect(page.locator('[data-testid="layout-canvas-field"]').first()).toBeVisible()
    }

    await expect.poll(() => layoutDetailCallCount).toBeGreaterThanOrEqual(4)
    await expect.poll(() => runtimeCallCount).toBeGreaterThanOrEqual(4)
  })
})

