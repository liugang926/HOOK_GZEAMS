import { test, expect, type Route } from '@playwright/test'
import { waitForDesignerReady } from '../helpers/page-ready.helpers'
type AnyRecord = Record<string, any>

const OBJECT_CODE = 'Asset'
const OBJECT_ID = 'bo-asset'
const SOURCE_LAYOUT_ID = 'layout-asset-source-duplicate'
const CREATED_LAYOUT_ID = 'layout-asset-created-duplicate'

function buildLegacySourceLayout(): AnyRecord {
  return {
    sections: [
      {
        type: 'section',
        title: 'Basic Legacy',
        columns: 1,
        fields: [
          {
            fieldCode: 'assetName',
            label: 'Asset Name',
            fieldType: 'text',
            span: 1,
            visible: true,
            required: false
          },
          {
            fieldCode: 'created_at',
            label: 'Created At',
            fieldType: 'datetime',
            span: 1,
            visible: true,
            required: false
          }
        ]
      }
    ],
    actions: []
  }
}

function fulfillSuccess(route: Route, data: unknown) {
  return route.fulfill({
    status: 200,
    contentType: 'application/json',
    body: JSON.stringify({ success: true, data })
  })
}

test.describe('Page Layout Duplicate Regression', () => {
  test('duplicate should sanitize layout config and open designer with duplicated draft', async ({ page }) => {
    let createCallCount = 0
    let createdPayload: AnyRecord | null = null
    let createdLayoutConfig: AnyRecord = buildLegacySourceLayout()

    await page.addInitScript(() => {
      localStorage.setItem('access_token', 'e2e-page-layout-duplicate-token')
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
          id: OBJECT_ID,
          code: OBJECT_CODE,
          name: OBJECT_CODE
        })
      }

      if (pathname.endsWith(`/api/system/page-layouts/by-object/${OBJECT_CODE}/`)) {
        return fulfillSuccess(route, [
          {
            id: SOURCE_LAYOUT_ID,
            layoutCode: `${OBJECT_CODE}_form_source`,
            layoutName: 'Asset Form Source',
            mode: 'edit',
            description: 'Source layout for duplicate regression',
            status: 'draft',
            version: '2',
            isDefault: false,
            isActive: true,
            isSystem: false,
            businessObject: OBJECT_ID,
            layoutConfig: buildLegacySourceLayout()
          }
        ])
      }

      if (/\/api\/system\/page-layouts\/?$/.test(pathname) && route.request().method() === 'POST') {
        createCallCount += 1
        createdPayload = route.request().postDataJSON() as AnyRecord
        createdLayoutConfig = (createdPayload?.layoutConfig || createdPayload?.layout_config || {}) as AnyRecord
        return fulfillSuccess(route, {
          id: CREATED_LAYOUT_ID,
          layoutCode: createdPayload?.layoutCode,
          layoutName: createdPayload?.layoutName,
          mode: 'edit',
          status: 'draft',
          version: '0.1.0',
          isDefault: false,
          isActive: true,
          businessObject: OBJECT_ID,
          layoutConfig: createdLayoutConfig
        })
      }

      if (pathname.endsWith(`/api/system/page-layouts/${CREATED_LAYOUT_ID}/`)) {
        return fulfillSuccess(route, {
          id: CREATED_LAYOUT_ID,
          layoutCode: 'asset_form_duplicate',
          layoutName: 'Asset Form Source - Duplicate',
          mode: 'edit',
          status: 'draft',
          version: '0.1.0',
          isDefault: false,
          isActive: true,
          businessObject: OBJECT_ID,
          layoutConfig: createdLayoutConfig
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
                showInList: true,
                sectionName: 'basic',
                span: 12
              }
            ],
            reverseRelations: []
          },
          layout: {
            id: CREATED_LAYOUT_ID,
            mode: 'edit',
            status: 'draft',
            version: 1,
            layoutConfig: createdLayoutConfig
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
              isSystem: false,
              showInDetail: true,
              showInForm: true,
              showInList: true,
              span: 12
            }
          ],
          reverse_relations: [],
          context: url.searchParams.get('context') || 'form'
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

    await page.goto(`/system/page-layouts?objectCode=${OBJECT_CODE}&objectName=Asset`)
    await expect(page.locator('.page-layout-list').first()).toBeVisible()
    await expect(page.locator('tbody tr')).toHaveCount(1)

    const duplicateButton = page.locator('tbody tr').first().getByRole('button', { name: 'Duplicate' })
    await expect(duplicateButton).toBeVisible()
    await duplicateButton.click()
    await expect.poll(() => createCallCount).toBe(1)

    const payload = createdPayload || {}
    const config = (payload.layoutConfig || payload.layout_config || {}) as AnyRecord
    expect(config?.sections?.[0]?.id).toBeTruthy()
    expect(config?.sections?.[0]?.fields?.[0]?.id).toBeTruthy()

    const fieldCodes = (config?.sections?.[0]?.fields || []).map((field: AnyRecord) => String(field.fieldCode || ''))
    expect(fieldCodes).toContain('assetName')
    expect(fieldCodes).not.toContain('created_at')

    await expect(page).toHaveURL(/\/system\/page-layouts\/designer/)
    await waitForDesignerReady(page)
    await expect(page.locator('[data-testid="layout-canvas-field"]').first()).toBeVisible()
  })
})


