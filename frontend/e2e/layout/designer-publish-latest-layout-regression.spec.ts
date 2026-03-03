import { test, expect, type Route } from '@playwright/test'
import { waitForDesignerReady } from '../helpers/page-ready.helpers'
type AnyRecord = Record<string, any>

const OBJECT_CODE = 'Asset'
const RECORD_ID = 'asset-e2e-publish-latest-1'
const LAYOUT_ID = 'layout-asset-readonly-publish-latest'
const INITIAL_LABEL = 'Asset Name'
const UPDATED_LABEL = 'Asset Name Published Latest'

const recordPayload = {
  id: RECORD_ID,
  assetName: 'Regression Laptop',
  createdBy: { username: 'admin' },
  createdAt: '2026-02-25T13:00:00+08:00',
  updatedBy: { username: 'admin' },
  updatedAt: '2026-02-25T13:30:00+08:00'
}

function buildLayoutConfig(label: string): AnyRecord {
  return {
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
            label,
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

function findFieldLabel(layoutConfig: AnyRecord, fieldCode: string): string {
  const sections = Array.isArray(layoutConfig?.sections) ? layoutConfig.sections : []
  for (const section of sections) {
    const fields = Array.isArray(section?.fields) ? section.fields : []
    const found = fields.find((field: AnyRecord) => field?.fieldCode === fieldCode)
    if (found) return String(found.label || '')
  }
  return ''
}

function fulfillSuccess(route: Route, data: unknown) {
  return route.fulfill({
    status: 200,
    contentType: 'application/json',
    body: JSON.stringify({ success: true, data })
  })
}

test.describe('Layout Designer Publish Latest Regression', () => {
  test('publish should include latest unsaved edits and detail should reflect published label', async ({ page }) => {
    let activeLayoutConfig = buildLayoutConfig(INITIAL_LABEL)
    let publishedLayoutConfig = buildLayoutConfig(INITIAL_LABEL)
    let saveCallCount = 0
    let publishCallCount = 0

    await page.addInitScript(() => {
      localStorage.setItem('access_token', 'e2e-designer-publish-latest-token')
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

      if (pathname.endsWith('/api/system/menu/flat/')) {
        return fulfillSuccess(route, [])
      }

      if (pathname.endsWith('/api/system/menu/config/')) {
        return route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({ schema: {}, common_groups: [], common_icons: [] })
        })
      }

      if (pathname.endsWith(`/api/system/page-layouts/${LAYOUT_ID}/publish/`)) {
        publishCallCount += 1
        publishedLayoutConfig = JSON.parse(JSON.stringify(activeLayoutConfig))
        return fulfillSuccess(route, {
          id: LAYOUT_ID,
          status: 'published'
        })
      }

      if (pathname.endsWith(`/api/system/page-layouts/${LAYOUT_ID}/`)) {
        if (route.request().method() === 'PATCH') {
          saveCallCount += 1
          const body = route.request().postDataJSON() as AnyRecord
          const nextConfig = (body?.layoutConfig || body?.layout_config) as AnyRecord
          if (nextConfig?.sections?.length) activeLayoutConfig = nextConfig
        }

        return fulfillSuccess(route, {
          id: LAYOUT_ID,
          layoutCode: `${OBJECT_CODE}_readonly_publish_latest_e2e`,
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
            id: LAYOUT_ID,
            mode: 'readonly',
            status: 'published',
            version: 2,
            layoutConfig: publishedLayoutConfig
          }
        })
      }

      if (pathname.endsWith(`/api/system/objects/${OBJECT_CODE}/metadata/`)) {
        return fulfillSuccess(route, {
          code: OBJECT_CODE,
          name: OBJECT_CODE,
          permissions: { view: true, change: true, delete: true }
        })
      }

      if (pathname.endsWith(`/api/system/objects/${OBJECT_CODE}/fields/`)) {
        const context = url.searchParams.get('context') || 'detail'
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
              sectionName: 'basic',
              span: 12
            }
          ],
          reverse_relations: [],
          context
        })
      }

      if (pathname.endsWith(`/api/system/objects/${OBJECT_CODE}/${RECORD_ID}/`)) {
        return fulfillSuccess(route, recordPayload)
      }

      return fulfillSuccess(route, {})
    })

    await page.goto(
      `/system/page-layouts/designer?layoutId=${LAYOUT_ID}&objectCode=${OBJECT_CODE}&layoutType=readonly&layoutName=Asset%20Readonly&businessObjectId=bo-asset`
    )

    await waitForDesignerReady(page)

    const fieldCard = page.locator('[data-testid="layout-canvas-field"][data-field-code="assetName"]').first()
    await expect(fieldCard).toBeVisible()
    await fieldCard.click({ position: { x: 4, y: 4 }, force: true })

    const fieldPropertyEditor = page.getByTestId('layout-field-property-editor')
    if (!(await fieldPropertyEditor.count())) {
      await page.locator('.canvas-content .el-form-item__label').first().click({ force: true })
    }
    await expect(fieldPropertyEditor).toBeVisible()

    const labelInput = page.getByTestId('field-prop-label').locator('input').first()
    await expect(labelInput).toBeVisible()
    await labelInput.fill(UPDATED_LABEL)
    await labelInput.press('Tab')

    const publishButton = page.getByTestId('layout-publish-button').first()
    await expect(publishButton).toBeVisible()
    await publishButton.click()

    await expect.poll(() => saveCallCount).toBe(1)
    await expect.poll(() => publishCallCount).toBe(1)
    await expect.poll(() => findFieldLabel(activeLayoutConfig, 'assetName')).toBe(UPDATED_LABEL)
    await expect.poll(() => findFieldLabel(publishedLayoutConfig, 'assetName')).toBe(UPDATED_LABEL)

    await page.goto(`/objects/${OBJECT_CODE}/${RECORD_ID}`)
    await expect(page.locator('.dynamic-detail-page').first()).toBeVisible()
    await expect(page.locator('.load-error')).toHaveCount(0)
    await expect(page.locator('.detail-sections .field-label', { hasText: UPDATED_LABEL }).first()).toBeVisible()
    await expect(page.locator('.detail-content')).toContainText(recordPayload.assetName)
  })
})


