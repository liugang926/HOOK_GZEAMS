import { expect, test, type Locator, type Page, type Route } from '@playwright/test'
import { gotoDesignerAndWait, setDesignerRenderMode } from '../helpers/page-ready.helpers'

const OBJECT_CODE = 'Asset'
const LAYOUT_ID = 'layout-asset-panel-scroll'
const DESIGNER_URL =
  `/system/page-layouts/designer?layoutId=${LAYOUT_ID}&objectCode=${OBJECT_CODE}&layoutType=edit&layoutName=Asset%20Panel%20Scroll&businessObjectId=bo-asset`

type MockField = {
  code: string
  name: string
  fieldType: string
}

const metadataFields: MockField[] = [
  { code: 'asset_code', name: 'Asset Code', fieldType: 'text' },
  { code: 'asset_name', name: 'Asset Name', fieldType: 'text' },
  { code: 'description', name: 'Description', fieldType: 'textarea' },
  { code: 'brand', name: 'Brand', fieldType: 'text' },
  { code: 'model', name: 'Model', fieldType: 'text' },
  { code: 'serial_number', name: 'Serial Number', fieldType: 'text' },
  { code: 'category', name: 'Category', fieldType: 'select' },
  { code: 'tags', name: 'Tags', fieldType: 'multi_select' },
  { code: 'purchase_price', name: 'Purchase Price', fieldType: 'number' },
  { code: 'current_value', name: 'Current Value', fieldType: 'number' },
  { code: 'purchase_date', name: 'Purchase Date', fieldType: 'date' },
  { code: 'maintenance_time', name: 'Maintenance Time', fieldType: 'datetime' },
  { code: 'owner_email', name: 'Owner Email', fieldType: 'email' },
  { code: 'vendor_url', name: 'Vendor URL', fieldType: 'url' },
  { code: 'supplier_ref', name: 'Supplier Ref', fieldType: 'reference' },
  { code: 'manager', name: 'Manager', fieldType: 'user' },
  { code: 'department', name: 'Department', fieldType: 'department' },
  { code: 'manual_file', name: 'Manual File', fieldType: 'file' },
  { code: 'photo', name: 'Photo', fieldType: 'image' },
  { code: 'is_active', name: 'Is Active', fieldType: 'boolean' },
  { code: 'confirmed', name: 'Confirmed', fieldType: 'checkbox' },
  { code: 'line_items', name: 'Line Items', fieldType: 'sub_table' },
  { code: 'health_score', name: 'Health Score', fieldType: 'formula' },
  { code: 'notes', name: 'Notes', fieldType: 'textarea' },
  { code: 'archive_code', name: 'Archive Code', fieldType: 'text' }
]

const runtimeFields = metadataFields.map((field) => ({
  ...field,
  label: field.name,
  showInDetail: true,
  showInForm: true,
  showInList: true,
  isReadonly: false,
  isRequired: false
}))

const layoutConfig = {
  sections: [
    {
      id: 'section-basic',
      type: 'section',
      title: 'Basic Information',
      columns: 2,
      fields: [
        { id: 'field-asset-code', fieldCode: 'asset_code', label: 'Asset Code', fieldType: 'text', span: 1, visible: true },
        { id: 'field-asset-name', fieldCode: 'asset_name', label: 'Asset Name', fieldType: 'text', span: 1, visible: true },
        { id: 'field-description', fieldCode: 'description', label: 'Description', fieldType: 'textarea', span: 1, visible: true },
        { id: 'field-brand', fieldCode: 'brand', label: 'Brand', fieldType: 'text', span: 1, visible: true }
      ]
    },
    {
      id: 'section-category',
      type: 'section',
      title: 'Category',
      columns: 2,
      fields: [
        { id: 'field-category', fieldCode: 'category', label: 'Category', fieldType: 'select', span: 1, visible: true },
        { id: 'field-tags', fieldCode: 'tags', label: 'Tags', fieldType: 'multi_select', span: 1, visible: true },
        { id: 'field-model', fieldCode: 'model', label: 'Model', fieldType: 'text', span: 1, visible: true },
        { id: 'field-serial-number', fieldCode: 'serial_number', label: 'Serial Number', fieldType: 'text', span: 1, visible: true }
      ]
    },
    {
      id: 'section-financial',
      type: 'section',
      title: 'Financial',
      columns: 2,
      fields: [
        { id: 'field-purchase-price', fieldCode: 'purchase_price', label: 'Purchase Price', fieldType: 'number', span: 1, visible: true },
        { id: 'field-current-value', fieldCode: 'current_value', label: 'Current Value', fieldType: 'number', span: 1, visible: true },
        { id: 'field-purchase-date', fieldCode: 'purchase_date', label: 'Purchase Date', fieldType: 'date', span: 1, visible: true },
        { id: 'field-maintenance-time', fieldCode: 'maintenance_time', label: 'Maintenance Time', fieldType: 'datetime', span: 1, visible: true }
      ]
    },
    {
      id: 'section-ownership',
      type: 'section',
      title: 'Ownership',
      columns: 2,
      fields: [
        { id: 'field-manager', fieldCode: 'manager', label: 'Manager', fieldType: 'user', span: 1, visible: true },
        { id: 'field-department', fieldCode: 'department', label: 'Department', fieldType: 'department', span: 1, visible: true },
        { id: 'field-owner-email', fieldCode: 'owner_email', label: 'Owner Email', fieldType: 'email', span: 1, visible: true },
        { id: 'field-vendor-url', fieldCode: 'vendor_url', label: 'Vendor URL', fieldType: 'url', span: 1, visible: true }
      ]
    },
    {
      id: 'section-media',
      type: 'section',
      title: 'Media',
      columns: 2,
      fields: [
        { id: 'field-manual-file', fieldCode: 'manual_file', label: 'Manual File', fieldType: 'file', span: 1, visible: true },
        { id: 'field-photo', fieldCode: 'photo', label: 'Photo', fieldType: 'image', span: 1, visible: true },
        { id: 'field-is-active', fieldCode: 'is_active', label: 'Is Active', fieldType: 'boolean', span: 1, visible: true },
        { id: 'field-confirmed', fieldCode: 'confirmed', label: 'Confirmed', fieldType: 'checkbox', span: 1, visible: true }
      ]
    },
    {
      id: 'section-archive',
      type: 'section',
      title: 'Archive',
      columns: 2,
      fields: [
        { id: 'field-notes', fieldCode: 'notes', label: 'Notes', fieldType: 'textarea', span: 1, visible: true },
        { id: 'field-archive-code', fieldCode: 'archive_code', label: 'Archive Code', fieldType: 'text', span: 1, visible: true }
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

async function expectScrollableToBottom(locator: Locator) {
  await expect.poll(async () => {
    return locator.evaluate((el) => {
      const node = el as HTMLElement
      return node.scrollHeight - node.clientHeight
    })
  }).toBeGreaterThan(32)

  await locator.evaluate((el) => {
    const node = el as HTMLElement
    node.scrollTop = node.scrollHeight
  })

  await expect.poll(async () => {
    return locator.evaluate((el) => {
      const node = el as HTMLElement
      const maxScrollTop = Math.max(0, node.scrollHeight - node.clientHeight)
      return Math.abs(maxScrollTop - node.scrollTop)
    })
  }).toBeLessThanOrEqual(2)
}

async function expandAllPaletteGroups(page: Page) {
  const headers = page.locator('[data-testid="layout-field-panel"] .field-group .group-header')
  const count = await headers.count()

  for (let index = 0; index < count; index += 1) {
    const header = headers.nth(index)
    const icon = header.locator('.expand-icon').first()
    const expanded = await icon.evaluate((el) => el.classList.contains('expanded'))
    if (!expanded) {
      await header.click()
    }
  }
}

test.describe('Layout Designer Panel Scroll Regression', () => {
  test.setTimeout(120000)

  test('designer shell should keep page fixed while each pane can scroll to bottom', async ({ page }) => {
    await page.addInitScript(() => {
      localStorage.setItem('access_token', 'e2e-designer-panel-scroll-token')
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
          layoutCode: `${OBJECT_CODE}_panel_scroll`,
          layoutName: 'Asset Panel Scroll',
          mode: 'edit',
          status: 'draft',
          version: 1,
          isDefault: false,
          layoutConfig
        })
      }

      if (pathname.endsWith(`/api/system/page-layouts/default/${OBJECT_CODE}/edit/`)) {
        return fulfillSuccess(route, {
          layoutConfig
        })
      }

      if (pathname.endsWith(`/api/system/objects/${OBJECT_CODE}/runtime/`)) {
        return fulfillSuccess(route, {
          runtimeVersion: 1,
          mode: 'edit',
          context: 'form',
          fields: {
            editableFields: runtimeFields,
            reverseRelations: []
          },
          layout: {
            id: LAYOUT_ID,
            mode: 'edit',
            status: 'draft',
            version: 1,
            layoutConfig
          },
          permissions: { view: true, add: true, change: true, delete: true },
          isDefault: false
        })
      }

      if (pathname.endsWith(`/api/system/objects/${OBJECT_CODE}/fields/`)) {
        return fulfillSuccess(route, {
          editable_fields: runtimeFields,
          reverse_relations: [],
          context: 'form'
        })
      }

      if (pathname.endsWith(`/api/system/objects/${OBJECT_CODE}/metadata/`)) {
        return fulfillSuccess(route, {
          code: OBJECT_CODE,
          name: OBJECT_CODE,
          fields: metadataFields,
          permissions: { view: true, change: true, delete: true }
        })
      }

      return fulfillSuccess(route, {})
    })

    await gotoDesignerAndWait(page, DESIGNER_URL, { requiredFieldCode: 'asset_code' })
    await setDesignerRenderMode(page, 'design')

    await expect.poll(async () => {
      return page.evaluate(() => {
        const scroller = document.scrollingElement
        return Math.max(0, (scroller?.scrollHeight ?? 0) - (scroller?.clientHeight ?? 0))
      })
    }).toBeLessThanOrEqual(4)

    await expandAllPaletteGroups(page)

    const fieldPanelContent = page.locator('[data-testid="layout-field-panel"] .panel-content').first()
    await expectScrollableToBottom(fieldPanelContent)
    await expect(
      page.locator('[data-testid="layout-field-panel"] .group-header').filter({ hasText: /^Layout$/ }).first()
    ).toBeVisible()

    const canvasContent = page.locator('[data-testid="layout-canvas"] .canvas-content').first()
    await expectScrollableToBottom(canvasContent)
    await expect(page.getByTestId('layout-section-header').filter({ hasText: 'Archive' }).first()).toBeVisible()

    await page.locator('[data-testid="layout-canvas-field"][data-field-code="asset_code"]').first().click()
    await expect(page.getByTestId('layout-field-property-editor')).toBeVisible()

    const propertyPanelContent = page.locator('[data-testid="layout-property-panel"] .panel-content').first()
    await expectScrollableToBottom(propertyPanelContent)
    await expect.poll(async () => {
      return propertyPanelContent.evaluate((el) => (el as HTMLElement).scrollTop)
    }).toBeGreaterThan(32)
  })
})
