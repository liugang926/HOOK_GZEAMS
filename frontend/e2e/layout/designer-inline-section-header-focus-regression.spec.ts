import { expect, test, type Route } from '@playwright/test'
import { clickDesignerSaveDraft, waitForDesignerReady } from '../helpers/page-ready.helpers'
import { waitForDetailPageReady } from '../helpers/detail-page.helpers'

type AnyRecord = Record<string, any>

const OBJECT_CODE = 'Asset'
const RECORD_ID = 'asset-e2e-inline-section-focus-1'
const LAYOUT_ID = 'layout-asset-readonly-inline-section-focus'
const UPDATED_SECTION_TITLE = 'Overview'

const recordPayload = {
  id: RECORD_ID,
  assetName: 'Regression Laptop',
  status: 'Draft',
  createdBy: { username: 'admin' },
  createdAt: '2026-02-25T10:00:00+08:00',
  updatedBy: { username: 'admin' },
  updatedAt: '2026-02-25T10:30:00+08:00'
}

function buildInitialLayoutConfig() {
  return {
    sections: [
      {
        id: 'section-basic',
        type: 'section',
        title: 'Basic Information',
        columns: 2,
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
          },
          {
            id: 'field-status',
            fieldCode: 'status',
            label: 'Status',
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

function getFirstSection(layoutConfig: AnyRecord): AnyRecord {
  const first = Array.isArray(layoutConfig?.sections) ? layoutConfig.sections[0] : null
  return first || {}
}

function countSectionFields(layoutConfig: AnyRecord): number {
  const firstSection = getFirstSection(layoutConfig)
  return Array.isArray(firstSection?.fields) ? firstSection.fields.length : 0
}

function fulfillSuccess(route: Route, data: unknown) {
  return route.fulfill({
    status: 200,
    contentType: 'application/json',
    body: JSON.stringify({ success: true, data })
  })
}

test.describe('Layout Designer Inline Section Header + Focus Regression', () => {
  test('inline section rename and selected field delete should preserve section editing flow', async ({ page }) => {
    let activeLayoutConfig = buildInitialLayoutConfig()
    let saveCallCount = 0

    await page.addInitScript(() => {
      localStorage.setItem('access_token', 'e2e-inline-section-focus-token')
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

      if (pathname.endsWith(`/api/system/page-layouts/${LAYOUT_ID}/`)) {
        if (route.request().method() === 'PATCH') {
          saveCallCount += 1
          const body = route.request().postDataJSON() as AnyRecord
          const nextConfig = (body?.layoutConfig || body?.layout_config) as AnyRecord
          if (nextConfig?.sections?.length) activeLayoutConfig = nextConfig
        }

        return fulfillSuccess(route, {
          id: LAYOUT_ID,
          layoutCode: `${OBJECT_CODE}_readonly_inline_section_focus_e2e`,
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
              },
              {
                code: 'status',
                name: 'Status',
                label: 'Status',
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
            status: 'draft',
            version: 1,
            layoutConfig: activeLayoutConfig
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
            },
            {
              code: 'status',
              name: 'Status',
              label: 'Status',
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

    await waitForDesignerReady(page, { requiredFieldCode: 'assetName' })

    const sectionTitle = page.getByTestId('designer-section-title').first()
    await expect(sectionTitle).toBeVisible()
    await sectionTitle.dblclick()

    const sectionTitleInput = page.getByTestId('designer-section-title-input').first()
    await expect(sectionTitleInput).toBeVisible()
    await sectionTitleInput.fill(UPDATED_SECTION_TITLE)
    await sectionTitleInput.press('Enter')

    await clickDesignerSaveDraft(page)

    await expect.poll(() => saveCallCount).toBe(1)
    await expect.poll(() => String(getFirstSection(activeLayoutConfig).title || '')).toBe(UPDATED_SECTION_TITLE)

    const assetField = page.locator('[data-testid="layout-canvas-field"][data-field-code="assetName"]').first()
    await expect(assetField).toBeVisible()
    await assetField.click({ position: { x: 8, y: 8 } })

    await expect(page.getByTestId('layout-field-property-editor')).toBeVisible()
    await assetField.getByTestId('layout-remove-field-button').click({ force: true })

    await expect(page.getByTestId('layout-section-property-editor')).toBeVisible()
    await expect(page.getByTestId('layout-field-property-editor')).toHaveCount(0)
    await expect(page.getByTestId('section-prop-title').locator('input').first()).toHaveValue(UPDATED_SECTION_TITLE)

    await clickDesignerSaveDraft(page)

    await expect.poll(() => saveCallCount).toBe(2)
    await expect.poll(() => countSectionFields(activeLayoutConfig)).toBe(1)

    await page.goto(`/objects/${OBJECT_CODE}/${RECORD_ID}`)
    await waitForDetailPageReady(page)

    await expect(page.locator('.detail-section .section-header', { hasText: UPDATED_SECTION_TITLE }).first()).toBeVisible()
    await expect(page.locator('.field-label', { hasText: 'Asset Name' })).toHaveCount(0)
    await expect(page.locator('.field-label', { hasText: 'Status' }).first()).toBeVisible()
  })
})
