import { expect, test, type Route } from '@playwright/test'
import { setDesignerRenderMode, waitForDesignerReady } from '../helpers/page-ready.helpers'

const OBJECT_CODE = 'Asset'
const LAYOUT_ID = 'layout-asset-preview-related-objects'

function fulfillSuccess(route: Route, data: unknown) {
  return route.fulfill({
    status: 200,
    contentType: 'application/json',
    body: JSON.stringify({ success: true, data })
  })
}

const layoutConfig = {
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
          readonly: false
        }
      ]
    }
  ],
  actions: []
}

test.describe('Layout Designer Preview Related Objects Regression', () => {
  test('designer preview should not fetch related records for preview placeholders', async ({ page }) => {
    let relationsEndpointCalls = 0
    let relatedRecordCalls = 0

    await page.addInitScript(() => {
      localStorage.setItem('access_token', 'e2e-designer-preview-related-token')
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
          layoutCode: `${OBJECT_CODE}_preview_related_objects`,
          layoutName: 'Asset Preview Related Objects',
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
                isRequired: false,
                isReadonly: false,
                showInDetail: true,
                showInForm: true,
                showInList: true
              },
              {
                code: 'internalNote',
                name: 'Internal Note',
                label: 'Internal Note',
                fieldType: 'textarea',
                isRequired: false,
                isReadonly: false,
                showInDetail: false,
                showInForm: true,
                showInList: false
              }
            ],
            reverseRelations: [
              {
                code: 'maintenance_records',
                name: 'Maintenance Records',
                label: 'Maintenance Records',
                relationDisplayMode: 'inline_readonly',
                targetObjectCode: 'Maintenance',
                reverseRelationField: 'asset'
              }
            ]
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

      if (pathname.endsWith(`/api/system/objects/${OBJECT_CODE}/metadata/`)) {
        return fulfillSuccess(route, {
          code: OBJECT_CODE,
          name: OBJECT_CODE,
          fields: [
            {
              code: 'assetName',
              name: 'Asset Name',
              label: 'Asset Name',
              fieldType: 'text'
            },
            {
              code: 'internalNote',
              name: 'Internal Note',
              label: 'Internal Note',
              fieldType: 'textarea',
              showInDetail: false,
              showInForm: true
            }
          ],
          permissions: { view: true, change: true, delete: true }
        })
      }

      if (pathname.endsWith('/api/system/objects/Maintenance/fields/')) {
        return fulfillSuccess(route, {
          editable_fields: [
            {
              code: 'code',
              name: 'Code',
              label: 'Code',
              fieldType: 'text',
              showInList: true
            }
          ],
          reverse_relations: [],
          context: 'list'
        })
      }

      if (pathname.endsWith(`/api/system/objects/${OBJECT_CODE}/relations/`)) {
        relationsEndpointCalls += 1
        return fulfillSuccess(route, {
          objectCode: OBJECT_CODE,
          locale: 'en-US',
          relations: []
        })
      }

      if (pathname.includes(`/api/system/objects/${OBJECT_CODE}/`) && pathname.includes('/related/')) {
        relatedRecordCalls += 1
        return fulfillSuccess(route, {
          count: 0,
          next: null,
          previous: null,
          results: []
        })
      }

      return fulfillSuccess(route, {})
    })

    await page.goto(
      `/system/page-layouts/designer?layoutId=${LAYOUT_ID}&objectCode=${OBJECT_CODE}&layoutType=readonly&layoutName=Asset%20Readonly&businessObjectId=bo-asset`
    )

    await waitForDesignerReady(page)
    await expect(page.getByTestId('layout-palette-field-assetName')).toHaveCount(1)
    await expect(page.getByTestId('layout-palette-field-internalNote')).toHaveCount(0)
    await expect(page.getByTestId('layout-palette-field-maintenance_records')).toHaveCount(0)
    await setDesignerRenderMode(page, 'preview')
    await page.locator('.record-main-tabs .el-tabs__item').filter({ hasText: /Related/i }).first().click()

    await expect(page.locator('.el-message--error')).toHaveCount(0)
    await expect.poll(() => relationsEndpointCalls).toBe(0)
    await expect.poll(() => relatedRecordCalls).toBe(0)
  })
})
