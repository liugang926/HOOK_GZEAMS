import { test, expect, type Route } from '@playwright/test'
import { waitForDetailPageReady } from '../helpers/detail-page.helpers'

interface FieldStub {
  code: string
  name: string
  fieldType: string
}

const baseField = {
  isRequired: false,
  isReadonly: false,
  isSystem: false,
  isSearchable: true,
  sortable: true,
  showInFilter: false,
  showInList: false,
  showInDetail: true,
  showInForm: true,
  sortOrder: 0,
  columnWidth: null,
  minColumnWidth: null,
  fixed: false,
  options: null,
  placeholder: null,
  defaultValue: null,
  referenceObject: null,
  isReverseRelation: false,
  reverseRelationModel: '',
  reverseRelationField: '',
  relationDisplayMode: 'tab_readonly'
}

const auditFields: FieldStub[] = [
  { code: 'created_at', name: 'Created At', fieldType: 'datetime' },
  { code: 'updated_at', name: 'Updated At', fieldType: 'datetime' }
]

const specialFields: FieldStub[] = [
  { code: 'qr_code', name: 'QR Code', fieldType: 'qr_code' },
  { code: 'website', name: 'Website', fieldType: 'url' },
  { code: 'contact_email', name: 'Email', fieldType: 'email' },
  { code: 'contact_phone', name: 'Phone', fieldType: 'phone' },
  { code: 'is_active', name: 'Active', fieldType: 'boolean' },
  { code: 'theme_color', name: 'Theme Color', fieldType: 'color' },
  { code: 'rating', name: 'Rating', fieldType: 'rate' },
  { code: 'description', name: 'Description', fieldType: 'rich_text' },
  { code: 'attachments', name: 'Attachments', fieldType: 'attachment' },
  { code: 'lines', name: 'Lines', fieldType: 'sub_table' },
  { code: 'payload', name: 'Payload', fieldType: 'json' }
]

const specialRecord = {
  id: 'asset-special-regression-1',
  qr_code: 'QR-DETAIL-001',
  website: 'https://example.com/assets/1',
  contact_email: 'asset@example.com',
  contact_phone: '13800138000',
  is_active: true,
  theme_color: '#22c55e',
  rating: 4,
  description: '<p><strong>Rich Content</strong> for detail</p><script>window.__xss = true</script>',
  attachments: [
    { fileName: 'manual.pdf', url: 'https://example.com/files/manual.pdf' },
    { fileName: 'invoice.pdf', url: 'https://example.com/files/invoice.pdf' }
  ],
  lines: [
    { item: 'Row A', qty: 1, remark: 'ok' },
    { item: 'Row B', qty: 2, remark: 'done' }
  ],
  payload: {
    assetType: 'Laptop',
    owner: 'QA Team'
  },
  createdBy: { username: 'admin' },
  createdAt: '2026-02-24T08:00:00+08:00',
  updatedBy: { username: 'admin' },
  updatedAt: '2026-02-24T08:30:00+08:00'
}

function buildEditableFields(fields: FieldStub[]) {
  return [...fields, ...auditFields].map((field, index) => ({
    ...baseField,
    ...field,
    sortOrder: index
  }))
}

function fulfillSuccess(route: Route, data: unknown) {
  return route.fulfill({
    status: 200,
    contentType: 'application/json',
    body: JSON.stringify({ success: true, data })
  })
}

test.describe('Detail Special Field Rendering Regression', () => {
  test('renders special field types with semantic display instead of plain text fallback', async ({ page }) => {
    await page.addInitScript(() => {
      localStorage.setItem('access_token', 'e2e-special-token')
      localStorage.setItem('current_org_id', 'org-special')
    })

    await page.route('**/*', async (route) => {
      const url = new URL(route.request().url())
      const pathname = url.pathname
      if (!pathname.startsWith('/api/')) {
        return route.continue()
      }

      if (pathname.endsWith('/api/system/objects/User/me/')) {
        return fulfillSuccess(route, {
          id: 'user-special',
          username: 'admin',
          roles: ['admin'],
          permissions: ['*'],
          primaryOrganization: { id: 'org-special', name: 'Special Org', code: 'SPL' }
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
          body: JSON.stringify({
            schema: {},
            common_groups: [],
            common_icons: []
          })
        })
      }

      if (pathname.endsWith('/api/system/objects/Asset/metadata/')) {
        return fulfillSuccess(route, {
          code: 'Asset',
          name: 'Asset',
          permissions: { view: true, change: true, delete: true }
        })
      }

      if (pathname.endsWith('/api/system/objects/Asset/fields/')) {
        return fulfillSuccess(route, {
          editable_fields: buildEditableFields(specialFields),
          reverse_relations: [],
          context: 'detail'
        })
      }

      if (pathname.endsWith('/api/system/objects/Asset/asset-special-regression-1/')) {
        return fulfillSuccess(route, specialRecord)
      }

      return fulfillSuccess(route, {})
    })

    await page.goto('/objects/Asset/asset-special-regression-1')
    await waitForDetailPageReady(page)

    await expect(page.locator('.qr-code-image')).toHaveCount(1)
    await expect(page.locator('a[href="https://example.com/assets/1"]')).toHaveCount(1)
    await expect(page.locator('a[href="mailto:asset@example.com"]')).toHaveCount(1)
    await expect(page.locator('a[href="tel:13800138000"]')).toHaveCount(1)
    await expect(page.locator('.color-swatch')).toHaveCount(1)
    await expect(page.locator('.el-rate')).toHaveCount(1)
    await expect(page.locator('.rich-text-display')).toContainText('Rich Content')
    await expect(page.locator('.rich-text-display script')).toHaveCount(0)
    await expect(page.locator('a[href="https://example.com/files/manual.pdf"]')).toHaveCount(1)
    await expect(page.locator('a[href="https://example.com/files/invoice.pdf"]')).toHaveCount(1)
    await expect(page.locator('.subtable-table')).toHaveCount(1)
    await expect(page.locator('.subtable-display')).toContainText('Row A')
    await expect(page.locator('.subtable-display')).toContainText('Row B')
    await expect(page.locator('.json-display')).toContainText('"assetType": "Laptop"')
  })
})
