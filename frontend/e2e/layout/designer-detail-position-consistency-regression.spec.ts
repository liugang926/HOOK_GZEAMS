import { expect, test, type Page, type Route } from '@playwright/test'
import { waitForDesignerReady } from '../helpers/page-ready.helpers'

const OBJECT_CODE = 'Asset'
const LAYOUT_ID = 'layout-asset-detail-position-consistency'
const RECORD_ID = 'asset-position-consistency-1'

const DESIGNER_LAYOUT_CONFIG = {
  sections: [
    {
      id: 'section-basic',
      type: 'section',
      title: 'Basic',
      columns: 2,
      fields: [
        {
          id: 'field-left',
          fieldCode: 'left_field',
          label: 'Left Field',
          fieldType: 'text',
          span: 1,
          visible: true,
          required: false,
          readonly: true
        },
        {
          id: 'field-right',
          fieldCode: 'right_field',
          label: 'Right Field',
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

const RUNTIME_LAYOUT_CONFIG_WITH_SYSTEM_INSERTION = {
  sections: [
    {
      id: 'section-basic',
      type: 'section',
      title: 'Basic',
      columns: 2,
      fields: [
        { fieldCode: 'left_field', label: 'Left Field', fieldType: 'text', span: 1, visible: true, readonly: true },
        { fieldCode: 'id', label: 'ID', fieldType: 'text', span: 1, visible: true, readonly: true },
        { fieldCode: 'runtime_shadow_field', label: 'Runtime Shadow Field', fieldType: 'text', span: 1, visible: true, readonly: true },
        { fieldCode: 'right_field', label: 'Right Field', fieldType: 'text', span: 1, visible: true, readonly: true }
      ]
    }
  ],
  actions: []
}

function fulfillSuccess(route: Route, data: unknown) {
  return route.fulfill({
    status: 200,
    contentType: 'application/json',
    body: JSON.stringify({ success: true, data })
  })
}

async function mockApis(page: Page) {
  await page.addInitScript(() => {
    localStorage.setItem('access_token', 'e2e-position-consistency-token')
    localStorage.setItem('current_org_id', 'org-position-consistency')
    localStorage.setItem('locale', 'en-US')
  })

  await page.route('**/*', async (route) => {
    const url = new URL(route.request().url())
    const pathname = url.pathname
    if (!pathname.startsWith('/api/')) return route.continue()

    if (pathname.endsWith('/api/system/objects/User/me/')) {
      return fulfillSuccess(route, {
        id: 'user-position-consistency',
        username: 'admin',
        roles: ['admin'],
        permissions: ['*'],
        primaryOrganization: { id: 'org-position-consistency', name: 'Position Org', code: 'POS' }
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
        layoutCode: `${OBJECT_CODE}_position_consistency`,
        layoutName: 'Asset Position Consistency',
        mode: 'readonly',
        status: 'draft',
        version: 1,
        isDefault: false,
        layoutConfig: DESIGNER_LAYOUT_CONFIG
      })
    }

    if (pathname.endsWith(`/api/system/objects/${OBJECT_CODE}/runtime/`)) {
      return fulfillSuccess(route, {
        runtimeVersion: 1,
        fields: {
          editableFields: [
            {
              code: 'left_field',
              name: 'Left Field',
              label: 'Left Field',
              fieldType: 'text',
              showInDetail: true,
              showInForm: true,
              showInList: true
            },
            {
              code: 'right_field',
              name: 'Right Field',
              label: 'Right Field',
              fieldType: 'text',
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
          layoutConfig: RUNTIME_LAYOUT_CONFIG_WITH_SYSTEM_INSERTION
        }
      })
    }

    if (pathname.endsWith(`/api/system/objects/${OBJECT_CODE}/fields/`)) {
      return fulfillSuccess(route, {
        editable_fields: [
          { code: 'left_field', name: 'Left Field', label: 'Left Field', fieldType: 'text', showInDetail: true, showInForm: true },
          { code: 'right_field', name: 'Right Field', label: 'Right Field', fieldType: 'text', showInDetail: true, showInForm: true }
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

    if (pathname.endsWith(`/api/system/objects/${OBJECT_CODE}/${RECORD_ID}/`)) {
      return fulfillSuccess(route, {
        id: RECORD_ID,
        left_field: 'L-001',
        right_field: 'R-001'
      })
    }

    return fulfillSuccess(route, {})
  })
}

function assertSameRowAndLeftRight(leftBox: { x: number; y: number }, rightBox: { x: number; y: number }) {
  expect(rightBox.x).toBeGreaterThan(leftBox.x)
  expect(Math.abs(rightBox.y - leftBox.y)).toBeLessThanOrEqual(8)
}

test.describe('Designer/Detail Position Consistency Regression', () => {
  test('runtime system-field insertion must not change left/right position mapping in detail page', async ({ page }) => {
    await mockApis(page)

    await page.goto(
      `/system/page-layouts/designer?layoutId=${LAYOUT_ID}&objectCode=${OBJECT_CODE}&layoutType=readonly&layoutName=Asset%20Readonly&businessObjectId=bo-asset`
    )
    await waitForDesignerReady(page)

    const leftCard = page.locator('[data-testid="layout-canvas-field"][data-field-code="left_field"]').first()
    const rightCard = page.locator('[data-testid="layout-canvas-field"][data-field-code="right_field"]').first()
    const leftGridItem = page.locator('.field-renderer[data-field-code="left_field"]').first()
    const rightGridItem = page.locator('.field-renderer[data-field-code="right_field"]').first()

    await expect(leftCard).toBeVisible()
    await expect(rightCard).toBeVisible()
    await expect(leftGridItem).toHaveAttribute('data-grid-col-start', '1')
    await expect(rightGridItem).toHaveAttribute('data-grid-col-start', '2')
    await expect(leftGridItem).toHaveAttribute('data-grid-row', '1')
    await expect(rightGridItem).toHaveAttribute('data-grid-row', '1')

    const leftCardBox = await leftCard.boundingBox()
    const rightCardBox = await rightCard.boundingBox()
    expect(leftCardBox).not.toBeNull()
    expect(rightCardBox).not.toBeNull()
    assertSameRowAndLeftRight(leftCardBox as { x: number; y: number }, rightCardBox as { x: number; y: number })

    await page.goto(`/objects/${OBJECT_CODE}/${RECORD_ID}`, { waitUntil: 'domcontentloaded' })
    await expect(page).toHaveURL(new RegExp(`/objects/${OBJECT_CODE}/${RECORD_ID}`))
    const detailRoot = page.locator('.dynamic-detail-page, .base-detail-page, .object-detail-page').first()
    await expect(detailRoot).toBeVisible({ timeout: 15000 })
    await expect(page.locator('.load-error')).toHaveCount(0)

    const leftItem = page.locator('.field-item').filter({
      has: page.locator('.field-label', { hasText: 'Left Field' })
    }).first()
    const rightItem = page.locator('.field-item').filter({
      has: page.locator('.field-label', { hasText: 'Right Field' })
    }).first()

    await expect(leftItem).toBeVisible()
    await expect(rightItem).toBeVisible()
    await expect(page.locator('.field-label', { hasText: 'ID' })).toHaveCount(0)
    await expect(page.locator('.field-label', { hasText: 'Runtime Shadow Field' })).toHaveCount(0)
    await expect(leftItem).toHaveAttribute('data-grid-col-start', '1')
    await expect(rightItem).toHaveAttribute('data-grid-col-start', '2')
    await expect(leftItem).toHaveAttribute('data-grid-row', '1')
    await expect(rightItem).toHaveAttribute('data-grid-row', '1')

    const leftItemBox = await leftItem.boundingBox()
    const rightItemBox = await rightItem.boundingBox()
    expect(leftItemBox).not.toBeNull()
    expect(rightItemBox).not.toBeNull()
    assertSameRowAndLeftRight(leftItemBox as { x: number; y: number }, rightItemBox as { x: number; y: number })
  })
})
