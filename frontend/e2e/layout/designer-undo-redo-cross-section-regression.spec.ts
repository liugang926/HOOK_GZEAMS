import { test, expect, type Route } from '@playwright/test'
import {
  clickDesignerSaveDraft,
  clickDesignerSectionHeader,
  waitForDesignerReady
} from '../helpers/page-ready.helpers'
interface LayoutField {
  id: string
  fieldCode: string
  label: string
  fieldType: string
  span: number
  visible: boolean
  required: boolean
  readonly: boolean
}

interface LayoutSection {
  id: string
  type: 'section'
  title: string
  columns: number
  collapsible: boolean
  collapsed: boolean
  fields: LayoutField[]
}

interface LayoutConfig {
  sections: LayoutSection[]
  actions: Array<Record<string, unknown>>
}

const OBJECT_CODE = 'Asset'
const RECORD_ID = 'asset-e2e-undo-redo-cross-section-1'
const LAYOUT_ID = 'layout-asset-readonly-undo-redo-cross-section'

const INITIAL_TITLE_A = 'Operations'
const INITIAL_TITLE_B = 'Lifecycle'
const UPDATED_TITLE_A = 'Operations Undo Redo A'
const UPDATED_TITLE_B = 'Lifecycle Undo Redo B'

const recordPayload = {
  id: RECORD_ID,
  assetName: 'Regression Laptop',
  assetCode: 'ASSET-2026-009',
  createdBy: { username: 'admin' },
  createdAt: '2026-02-25T13:00:00+08:00',
  updatedBy: { username: 'admin' },
  updatedAt: '2026-02-25T13:30:00+08:00'
}

function buildLayoutConfig(): LayoutConfig {
  return {
    sections: [
      {
        id: 'section-operations',
        type: 'section',
        title: INITIAL_TITLE_A,
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
      },
      {
        id: 'section-lifecycle',
        type: 'section',
        title: INITIAL_TITLE_B,
        columns: 2,
        collapsible: false,
        collapsed: false,
        fields: [
          {
            id: 'field-asset-code',
            fieldCode: 'assetCode',
            label: 'Asset Code',
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

function sectionTitle(layoutConfig: LayoutConfig, index: number): string {
  return String(layoutConfig?.sections?.[index]?.title || '')
}

function fulfillSuccess(route: Route, data: unknown) {
  return route.fulfill({
    status: 200,
    contentType: 'application/json',
    body: JSON.stringify({ success: true, data })
  })
}

test.describe('Layout Designer Undo/Redo Cross-section Regression', () => {
  test('cross-section title edits should persist correctly after undo/redo and save', async ({ page }) => {
    let activeLayoutConfig = buildLayoutConfig()
    let saveCallCount = 0

    await page.addInitScript(() => {
      localStorage.setItem('access_token', 'e2e-designer-undo-redo-cross-token')
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
          const body = route.request().postDataJSON() as { layoutConfig?: LayoutConfig; layout_config?: LayoutConfig }
          const nextConfig = body?.layoutConfig || body?.layout_config
          if (nextConfig?.sections?.length) activeLayoutConfig = nextConfig
        }

        return fulfillSuccess(route, {
          id: LAYOUT_ID,
          layoutCode: `${OBJECT_CODE}_readonly_undo_redo_cross_section_e2e`,
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
                code: 'assetCode',
                name: 'Asset Code',
                label: 'Asset Code',
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
              code: 'assetCode',
              name: 'Asset Code',
              label: 'Asset Code',
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

    await clickDesignerSectionHeader(page, { title: INITIAL_TITLE_A })
    await expect(page.getByTestId('layout-section-property-editor')).toBeVisible()
    const titleInputA = page.getByTestId('section-prop-title').locator('input').first()
    await titleInputA.fill(UPDATED_TITLE_A)
    await titleInputA.press('Tab')

    await clickDesignerSectionHeader(page, { title: INITIAL_TITLE_B })
    const titleInputB = page.getByTestId('section-prop-title').locator('input').first()
    await titleInputB.fill(UPDATED_TITLE_B)
    await titleInputB.press('Tab')

    const undoButton = page.getByTestId('layout-undo-button')
    const redoButton = page.getByTestId('layout-redo-button')

    await expect(undoButton).toBeEnabled()
    await undoButton.click()

    await clickDesignerSaveDraft(page)
    await expect.poll(() => saveCallCount).toBe(1)
    await expect.poll(() => sectionTitle(activeLayoutConfig, 0)).toBe(UPDATED_TITLE_A)
    await expect.poll(() => sectionTitle(activeLayoutConfig, 1)).toBe(INITIAL_TITLE_B)

    await expect(redoButton).toBeEnabled()
    await redoButton.click()

    await clickDesignerSaveDraft(page)
    await expect.poll(() => saveCallCount).toBe(2)
    await expect.poll(() => sectionTitle(activeLayoutConfig, 0)).toBe(UPDATED_TITLE_A)
    await expect.poll(() => sectionTitle(activeLayoutConfig, 1)).toBe(UPDATED_TITLE_B)

    await page.goto(`/objects/${OBJECT_CODE}/${RECORD_ID}`)
    await expect(page.locator('.dynamic-detail-page').first()).toBeVisible()
    await expect(page.locator('.load-error')).toHaveCount(0)
    await expect(page.locator('.detail-sections .section-title', { hasText: UPDATED_TITLE_A }).first()).toBeVisible()
    await expect(page.locator('.detail-sections .section-title', { hasText: UPDATED_TITLE_B }).first()).toBeVisible()
    await expect(page.locator('.detail-content')).toContainText(recordPayload.assetName)
    await expect(page.locator('.detail-content')).toContainText(recordPayload.assetCode)
  })
})


