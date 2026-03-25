import { test, expect, type Route } from '@playwright/test'
import { waitForDesignerReady } from '../helpers/page-ready.helpers'

const OBJECT_CODE = 'Asset'

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
        title: 'Basic',
        columns: 1,
        fields: [
          {
            id: 'field-asset-name',
            fieldCode: 'assetName',
            label: 'Asset Name',
            fieldType: 'text',
            span: 1,
            visible: true,
            required: false,
            readonly: false
          }
        ]
      }
    ],
    actions: []
  }
}

test.describe('Page Layout System Preview Save Regression', () => {
  test('system preview entry should not pass virtual layoutId and save should create a persisted layout', async ({ page }) => {
    const layoutConfig = buildLayoutConfig()
    let createCallCount = 0
    let patchCallCount = 0
    let invalidVirtualPatch = false

    await page.addInitScript(() => {
      localStorage.setItem('access_token', 'e2e-layout-system-preview-save-token')
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

      if (pathname.endsWith(`/api/system/business-objects/by-code/${OBJECT_CODE}/`)) {
        return fulfillSuccess(route, {
          id: 'bo-asset',
          code: OBJECT_CODE,
          name: 'Asset',
          isHardcoded: true
        })
      }

      if (pathname.endsWith('/api/system/business-objects/fields/')) {
        return fulfillSuccess(route, {
          object_code: OBJECT_CODE,
          fields: [
            {
              fieldName: 'assetName',
              displayName: 'Asset Name',
              fieldType: 'text',
              isRequired: false,
              isEditable: true,
              sortOrder: 1,
              showInList: true,
              showInForm: true,
              showInDetail: true
            }
          ]
        })
      }

      if (pathname.endsWith(`/api/system/page-layouts/by-object/${OBJECT_CODE}/`)) {
        return fulfillSuccess(route, [])
      }

      if (pathname.endsWith(`/api/system/page-layouts/default/${OBJECT_CODE}/edit/`)) {
        return fulfillSuccess(route, { layoutConfig })
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
                showInList: true,
                isReadonly: false,
                isRequired: false,
                span: 12
              }
            ],
            reverseRelations: []
          },
          layout: {
            id: 'layout-active-asset',
            mode: 'edit',
            status: 'published',
            version: 3,
            layoutConfig
          }
        })
      }

      if (pathname.endsWith(`/api/system/objects/${OBJECT_CODE}/metadata/`)) {
        return fulfillSuccess(route, {
          code: OBJECT_CODE,
          name: 'Asset',
          fields: [
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
          permissions: { view: true, change: true, delete: true }
        })
      }

      if (pathname === '/api/system/page-layouts/' && route.request().method() === 'POST') {
        createCallCount += 1
        return fulfillSuccess(route, {
          id: `layout-created-${createCallCount}`,
          layoutCode: `${OBJECT_CODE.toLowerCase()}_edit_${Date.now()}`,
          layoutName: 'Asset Edit',
          mode: 'edit',
          status: 'draft',
          version: '0.1.0',
          businessObject: 'bo-asset',
          layoutConfig
        })
      }

      if (pathname.startsWith('/api/system/page-layouts/') && route.request().method() === 'PATCH') {
        patchCallCount += 1
        if (pathname.includes('/system_')) {
          invalidVirtualPatch = true
        }
        return fulfillSuccess(route, {})
      }

      return fulfillSuccess(route, {})
    })

    await page.goto(`/system/page-layouts?objectCode=${OBJECT_CODE}&objectName=Asset`)
    await expect(page.getByText('Preview').first()).toBeVisible()
    await page.getByText('Preview').first().click()

    await expect(page).toHaveURL(/\/system\/page-layouts\/designer/)
    const currentUrl = new URL(page.url())
    expect(currentUrl.searchParams.get('layoutId')).toBeNull()
    expect(currentUrl.searchParams.get('previewMode')).toBe('active')

    await waitForDesignerReady(page)

    const saveButton = page.getByTestId('layout-save-button').first()
    const previewCurrentButton = page.getByTestId('layout-preview-current-button').first()
    await expect(saveButton).toBeDisabled()

    await previewCurrentButton.click()
    await expect(saveButton).toBeEnabled()
    await saveButton.click()

    await expect.poll(() => createCallCount).toBe(1)
    expect(patchCallCount).toBe(0)
    expect(invalidVirtualPatch).toBeFalsy()
  })
})
