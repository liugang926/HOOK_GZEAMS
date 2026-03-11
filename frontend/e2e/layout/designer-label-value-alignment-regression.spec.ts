import { expect, test, type Page, type Route } from '@playwright/test'
import { getDetailFieldItem } from '../helpers/detail-page.helpers'
import { setDesignerRenderMode, waitForDesignerReady } from '../helpers/page-ready.helpers'

const OBJECT_CODE = 'Asset'
const LAYOUT_ID = 'layout-asset-label-value-alignment'

const fields = [
  { code: 'id_short', label: 'ID', fieldType: 'text' },
  {
    code: 'very_long_business_field_label_for_alignment',
    label: 'Very Long Business Field Label For Alignment Regression',
    fieldType: 'text'
  },
  { code: 'owner_department', label: 'Owner Department', fieldType: 'text' }
]

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
        id: 'alignment-section',
        type: 'section',
        title: 'Alignment Section',
        columns: 2,
        fields: fields.map((field) => ({
          id: `field-${field.code}`,
          fieldCode: field.code,
          label: field.label,
          fieldType: field.fieldType,
          span: 2,
          visible: true,
          required: false,
          readonly: false
        }))
      }
    ],
    actions: []
  }
}

async function mockApis(page: Page) {
  const layoutConfig = buildLayoutConfig()

  await page.addInitScript(() => {
    localStorage.setItem('access_token', 'e2e-designer-label-alignment-token')
    localStorage.setItem('current_org_id', 'org-designer-label-alignment')
    localStorage.setItem('locale', 'en-US')
  })

  await page.route('**/*', async (route) => {
    const url = new URL(route.request().url())
    const pathname = url.pathname

    if (!pathname.startsWith('/api/')) return route.continue()

    if (pathname.endsWith('/api/system/objects/User/me/')) {
      return fulfillSuccess(route, {
        id: 'user-designer-label-alignment',
        username: 'admin',
        roles: ['admin'],
        permissions: ['*'],
        primaryOrganization: { id: 'org-designer-label-alignment', name: 'Alignment Org', code: 'ALG' }
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
        layoutCode: `${OBJECT_CODE}_label_alignment`,
        layoutName: 'Asset Label Alignment',
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
          editableFields: fields.map((field) => ({
            code: field.code,
            name: field.label,
            label: field.label,
            fieldType: field.fieldType,
            isRequired: false,
            isReadonly: false,
            showInDetail: true,
            showInForm: true,
            showInList: true
          })),
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
        editable_fields: fields.map((field) => ({
          code: field.code,
          name: field.label,
          label: field.label,
          fieldType: field.fieldType,
          showInDetail: true,
          showInForm: true
        })),
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
}

function assertXAligned(lefts: number[], tolerance = 1) {
  const min = Math.min(...lefts)
  const max = Math.max(...lefts)
  expect(max - min).toBeLessThanOrEqual(tolerance)
}

async function collectCanvasDesignLeftsByLabels(page: Page, labels: string[]): Promise<number[]> {
  const lefts: number[] = []
  const canvas = page.getByTestId('layout-canvas').first()

  for (const label of labels) {
    const card = canvas.locator('[data-testid="layout-canvas-field"]').filter({
      has: page.locator('.field-label', { hasText: label })
    }).first()
    await expect(card).toBeVisible()

    const box = await card.locator('.field-value').first().boundingBox()
    expect(box).not.toBeNull()
    lefts.push((box as { x: number }).x)
  }

  return lefts
}

async function collectCanvasPreviewLeftsByLabels(page: Page, labels: string[]): Promise<number[]> {
  const lefts: number[] = []
  const previewRoot = page.locator('.runtime-preview-card').first()

  for (const label of labels) {
    const fieldItem = getDetailFieldItem(previewRoot, label)
    await expect(fieldItem).toBeVisible()

    const box = await fieldItem.locator('.field-value').first().boundingBox()
    expect(box).not.toBeNull()
    lefts.push((box as { x: number }).x)
  }

  return lefts
}

test.describe('Layout Designer Label-Value Alignment Regression', () => {
  test('design and preview mode should keep value start aligned for long labels', async ({ page }) => {
    await mockApis(page)

    await page.goto(
      `/system/page-layouts/designer?layoutId=${LAYOUT_ID}&objectCode=${OBJECT_CODE}&layoutType=readonly&layoutName=Asset%20Readonly&businessObjectId=bo-asset`
    )

    await waitForDesignerReady(page)
    await setDesignerRenderMode(page, 'design')

    const labels = fields.map((field) => field.label)
    const designLefts = await collectCanvasDesignLeftsByLabels(page, labels)
    assertXAligned(designLefts)

    await setDesignerRenderMode(page, 'preview')
    const previewLefts = await collectCanvasPreviewLeftsByLabels(page, labels)
    assertXAligned(previewLefts)
  })
})
