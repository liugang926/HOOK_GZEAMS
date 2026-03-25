import { test, expect, type Route } from '@playwright/test'
import {
  clickDesignerSaveDraft,
  clickDesignerSectionHeader,
  waitForDesignerReady
} from '../helpers/page-ready.helpers'
import { waitForDetailPageReady } from '../helpers/detail-page.helpers'
type AnyRecord = Record<string, any>

const OBJECT_CODE = 'Asset'
const RECORD_ID = 'asset-e2e-section-1'
const LAYOUT_ID = 'layout-asset-readonly-section'
const INITIAL_SECTION_TITLE = 'Basic Information'
const UPDATED_SECTION_TITLE = 'Business Snapshot'

const recordPayload = {
  id: RECORD_ID,
  assetName: 'Regression Laptop',
  createdBy: { username: 'admin' },
  createdAt: '2026-02-25T11:00:00+08:00',
  updatedBy: { username: 'admin' },
  updatedAt: '2026-02-25T11:30:00+08:00'
}

function buildInitialLayoutConfig() {
  return {
    sections: [
      {
        id: 'section-basic',
        type: 'section',
        title: INITIAL_SECTION_TITLE,
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
          }
        ]
      }
    ],
    actions: []
  }
}

function getFirstSectionTitle(layoutConfig: AnyRecord): string {
  const first = Array.isArray(layoutConfig?.sections) ? layoutConfig.sections[0] : null
  return (first?.title || INITIAL_SECTION_TITLE) as string
}

function fulfillSuccess(route: Route, data: unknown) {
  return route.fulfill({
    status: 200,
    contentType: 'application/json',
    body: JSON.stringify({ success: true, data })
  })
}

test.describe('Layout Designer Section Save -> Detail Rendering Regression', () => {
  test('readonly detail page must reflect designer saved section title', async ({ page }) => {
    let activeLayoutConfig = buildInitialLayoutConfig()
    let saveCallCount = 0

    await page.addInitScript(() => {
      localStorage.setItem('access_token', 'e2e-designer-section-token')
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
          layoutCode: `${OBJECT_CODE}_readonly_section_e2e`,
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
                sectionName: getFirstSectionTitle(activeLayoutConfig)
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
        const sectionName = getFirstSectionTitle(activeLayoutConfig)
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
              sectionName,
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

    await clickDesignerSectionHeader(page, { title: INITIAL_SECTION_TITLE })

    const sectionPropertyEditor = page.getByTestId('layout-section-property-editor')
    await expect(sectionPropertyEditor).toBeVisible()

    const titleInput = page.getByTestId('section-prop-title').locator('input').first()
    await expect(titleInput).toBeVisible()
    await titleInput.fill(UPDATED_SECTION_TITLE)
    await titleInput.press('Tab')

    await clickDesignerSaveDraft(page)

    await expect.poll(() => saveCallCount).toBe(1)
    await expect.poll(() => getFirstSectionTitle(activeLayoutConfig)).toBe(UPDATED_SECTION_TITLE)

    await page.goto(`/objects/${OBJECT_CODE}/${RECORD_ID}`)
    await waitForDetailPageReady(page)
    await expect(page.locator('.detail-sections .section-title', { hasText: UPDATED_SECTION_TITLE }).first()).toBeVisible()
    await expect(page.locator('.detail-content')).toContainText(recordPayload.assetName)
  })
})



