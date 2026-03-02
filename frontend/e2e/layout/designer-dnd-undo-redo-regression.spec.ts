import { test, expect, type Page, type Route } from '@playwright/test'

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
const RECORD_ID = 'asset-e2e-dnd-undo-redo-1'
const LAYOUT_ID = 'layout-asset-readonly-dnd-undo-redo'

const recordPayload = {
  id: RECORD_ID,
  assetName: 'Regression Laptop',
  assetCode: 'ASSET-2026-101',
  createdBy: { username: 'admin' },
  createdAt: '2026-02-25T13:00:00+08:00',
  updatedBy: { username: 'admin' },
  updatedAt: '2026-02-25T13:30:00+08:00'
}

function buildLayoutConfig(): LayoutConfig {
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

function getFieldOrder(layoutConfig: LayoutConfig): string[] {
  return (layoutConfig?.sections?.[0]?.fields || []).map((f) => f.fieldCode)
}

async function getCanvasFieldOrder(page: Page): Promise<string[]> {
  return page
    .locator('[data-testid="layout-canvas-field"]')
    .evaluateAll((nodes) => nodes.map((node) => String(node.getAttribute('data-field-code') || '')))
}

function fulfillSuccess(route: Route, data: unknown) {
  return route.fulfill({
    status: 200,
    contentType: 'application/json',
    body: JSON.stringify({ success: true, data })
  })
}

async function dragFieldBefore(page: Page, sourceCode: string, targetCode: string) {
  const source = page.locator(`[data-testid="layout-canvas-field"][data-field-code="${sourceCode}"]`).first()
  const target = page.locator(`[data-testid="layout-canvas-field"][data-field-code="${targetCode}"]`).first()

  await expect(source).toBeVisible()
  await expect(target).toBeVisible()

  await source.dragTo(target, {
    sourcePosition: { x: 12, y: 8 },
    targetPosition: { x: 12, y: 2 },
    force: true
  })
}

test.describe('Layout Designer DnD + Undo/Redo Regression', () => {
  test('drag reorder should remain consistent across undo/redo and save', async ({ page }) => {
    let activeLayoutConfig = buildLayoutConfig()
    let saveCallCount = 0

    await page.addInitScript(() => {
      localStorage.setItem('access_token', 'e2e-designer-dnd-undo-redo-token')
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
          layoutCode: `${OBJECT_CODE}_readonly_dnd_undo_redo_e2e`,
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

    await expect(page.getByTestId('layout-designer')).toBeVisible()
    await expect(page.locator('[data-testid="layout-canvas-field"]')).toHaveCount(2)

    await expect.poll(async () => (await getCanvasFieldOrder(page)).join(',')).toBe('assetName,assetCode')

    await dragFieldBefore(page, 'assetCode', 'assetName')
    await expect.poll(async () => (await getCanvasFieldOrder(page)).join(',')).toBe('assetCode,assetName')

    const undoButton = page.getByTestId('layout-undo-button')
    const redoButton = page.getByTestId('layout-redo-button')
    const saveButton = page.getByTestId('layout-save-button').first()

    await expect(undoButton).toBeEnabled()
    await undoButton.click()
    await expect.poll(async () => (await getCanvasFieldOrder(page)).join(',')).toBe('assetName,assetCode')

    await expect(redoButton).toBeEnabled()
    await redoButton.click()
    await expect.poll(async () => (await getCanvasFieldOrder(page)).join(',')).toBe('assetCode,assetName')

    await saveButton.click()
    await expect.poll(() => saveCallCount).toBe(1)
    await expect.poll(() => getFieldOrder(activeLayoutConfig).join(',')).toBe('assetCode,assetName')

    await page.goto(`/objects/${OBJECT_CODE}/${RECORD_ID}`)
    await expect(page.locator('.dynamic-detail-page').first()).toBeVisible()
    await expect(page.locator('.load-error')).toHaveCount(0)

    const labels = page.locator('.detail-sections .field-label')
    await expect(labels).toHaveCount(2)
    await expect(labels.nth(0)).toContainText('Asset Code')
    await expect(labels.nth(1)).toContainText('Asset Name')
    await expect(page.locator('.detail-content')).toContainText(recordPayload.assetCode)
    await expect(page.locator('.detail-content')).toContainText(recordPayload.assetName)
  })
})
