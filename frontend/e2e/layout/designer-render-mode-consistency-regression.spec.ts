import { test, expect, type Route, type Page } from '@playwright/test'
import { setDesignerRenderMode, waitForDesignerReady } from '../helpers/page-ready.helpers'

const OBJECT_CODE = 'Asset'
const LAYOUT_ID = 'layout-asset-render-mode-consistency'
const SECTION_TITLE = 'Basic Information'

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
        title: SECTION_TITLE,
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
          },
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

function normalizeLabel(text: string): string {
  return String(text || '')
    .replace(/\*/g, '')
    .replace(/\s+/g, ' ')
    .trim()
}

async function readCanvasSnapshot(page: Page) {
  const title = normalizeLabel(
    await page.locator('.detail-section .section-title').first().innerText()
  )
  const labels = (await page
    .locator('[data-testid="layout-canvas-field"] .el-form-item__label')
    .allTextContents())
    .map(normalizeLabel)
    .filter(Boolean)

  return { title, labels }
}

async function countReadonlyCards(page: Page) {
  return page.locator('[data-testid="layout-canvas-field"].is-field-readonly').count()
}

test.describe('Layout Designer Render Mode Consistency Regression', () => {
  test('design mode and preview mode should render the same section and field labels', async ({ page }) => {
    const layoutConfig = buildLayoutConfig()

    await page.addInitScript(() => {
      localStorage.setItem('access_token', 'e2e-designer-render-mode-token')
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
          layoutCode: `${OBJECT_CODE}_render_mode_consistency`,
          layoutName: 'Asset Render Mode Consistency',
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
                code: 'assetCode',
                name: 'Asset Code',
                label: 'Asset Code',
                fieldType: 'text',
                isRequired: false,
                isReadonly: false,
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

    const designSnapshot = await readCanvasSnapshot(page)
    expect(designSnapshot.title).toContain(SECTION_TITLE)
    expect(designSnapshot.labels).toEqual(['Asset Name', 'Asset Code'])
    await expect.poll(async () => countReadonlyCards(page)).toBe(2)

    await setDesignerRenderMode(page, 'preview')

    const previewSnapshot = await readCanvasSnapshot(page)
    expect(previewSnapshot).toEqual(designSnapshot)
    await expect.poll(async () => countReadonlyCards(page)).toBe(2)

    await setDesignerRenderMode(page, 'design')
    const designSnapshotAfterBack = await readCanvasSnapshot(page)
    expect(designSnapshotAfterBack).toEqual(designSnapshot)
    await expect.poll(async () => countReadonlyCards(page)).toBe(2)
  })
})
