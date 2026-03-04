import { test, expect, type Route } from '@playwright/test'

interface FieldStub {
  code: string
  name: string
  fieldType: string
}

interface DetailScenario {
  objectCode: 'Asset' | 'Supplier' | 'Department'
  id: string
  record: Record<string, unknown>
  businessFields: FieldStub[]
  expectedTexts: string[]
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
  // Keep audit fields to verify they do not replace business content.
  { code: 'created_at', name: 'Created At', fieldType: 'datetime' },
  { code: 'updated_at', name: 'Updated At', fieldType: 'datetime' }
]

const scenarios: DetailScenario[] = [
  {
    objectCode: 'Asset',
    id: 'asset-regression-1',
    record: {
      id: 'asset-regression-1',
      assetCode: 'ASSET-REG-001',
      assetName: 'Regression Laptop',
      brand: 'ThinkPad',
      model: 'X1 Carbon',
      createdBy: { username: 'admin' },
      createdAt: '2026-02-24T08:00:00+08:00',
      updatedBy: { username: 'admin' },
      updatedAt: '2026-02-24T08:30:00+08:00'
    },
    businessFields: [
      { code: 'asset_code', name: 'asset code', fieldType: 'text' },
      { code: 'asset_name', name: 'asset name', fieldType: 'text' },
      { code: 'brand', name: 'brand', fieldType: 'text' },
      { code: 'model', name: 'model', fieldType: 'text' }
    ],
    expectedTexts: ['ASSET-REG-001', 'Regression Laptop', 'ThinkPad', 'X1 Carbon']
  },
  {
    objectCode: 'Supplier',
    id: 'supplier-regression-1',
    record: {
      id: 'supplier-regression-1',
      supplierCode: 'SUP-REG-001',
      supplierName: 'Regression Supplies Inc',
      contactPerson: 'Alice Zhang',
      phone: '18800001111',
      createdBy: { username: 'admin' },
      createdAt: '2026-02-24T08:10:00+08:00',
      updatedBy: { username: 'admin' },
      updatedAt: '2026-02-24T08:35:00+08:00'
    },
    businessFields: [
      { code: 'supplier_code', name: 'supplier code', fieldType: 'text' },
      { code: 'supplier_name', name: 'supplier name', fieldType: 'text' },
      { code: 'contact_person', name: 'contact person', fieldType: 'text' },
      { code: 'phone', name: 'phone', fieldType: 'text' }
    ],
    expectedTexts: ['SUP-REG-001', 'Regression Supplies Inc', 'Alice Zhang', '18800001111']
  },
  {
    objectCode: 'Department',
    id: 'department-regression-1',
    record: {
      id: 'department-regression-1',
      departmentCode: 'DEPT-REG-001',
      name: 'Regression Department',
      contactPerson: 'Bob Li',
      createdBy: { username: 'admin' },
      createdAt: '2026-02-24T08:20:00+08:00',
      updatedBy: { username: 'admin' },
      updatedAt: '2026-02-24T08:40:00+08:00'
    },
    businessFields: [
      { code: 'department_code', name: 'department code', fieldType: 'text' },
      { code: 'name', name: 'department name', fieldType: 'text' },
      { code: 'contact_person', name: 'contact person', fieldType: 'text' }
    ],
    expectedTexts: ['DEPT-REG-001', 'Regression Department', 'Bob Li']
  }
]

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

test.describe('Detail Rendering Regression', () => {
  for (const scenario of scenarios) {
    test(`${scenario.objectCode} must render business fields on readonly detail page`, async ({ page }) => {
      await page.addInitScript(() => {
        localStorage.setItem('access_token', 'e2e-regression-token')
        localStorage.setItem('current_org_id', 'org-regression')
      })

      await page.route('**/*', async (route) => {
        const url = new URL(route.request().url())
        const pathname = url.pathname
        if (!pathname.startsWith('/api/')) {
          return route.continue()
        }

        if (pathname.endsWith('/api/system/objects/User/me/')) {
          return fulfillSuccess(route, {
            id: 'user-regression',
            username: 'admin',
            roles: ['admin'],
            permissions: ['*'],
            primaryOrganization: { id: 'org-regression', name: 'Regression Org', code: 'REG' }
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

        if (pathname.endsWith(`/api/system/objects/${scenario.objectCode}/metadata/`)) {
          return fulfillSuccess(route, {
            code: scenario.objectCode,
            name: scenario.objectCode,
            permissions: { view: true, change: true, delete: true }
          })
        }

        if (pathname.endsWith(`/api/system/objects/${scenario.objectCode}/fields/`)) {
          return fulfillSuccess(route, {
            editable_fields: buildEditableFields(scenario.businessFields),
            reverse_relations: [],
            context: 'detail'
          })
        }

        if (pathname.endsWith(`/api/system/objects/${scenario.objectCode}/${scenario.id}/`)) {
          return fulfillSuccess(route, scenario.record)
        }

        // Keep other API calls harmless for this focused regression.
        return fulfillSuccess(route, {})
      })

      await page.goto(`/objects/${scenario.objectCode}/${scenario.id}`, { waitUntil: 'domcontentloaded' })
      await expect(page).toHaveURL(new RegExp(`/objects/${scenario.objectCode}/${scenario.id}`))
      const detailRoot = page.locator('.dynamic-detail-page, .base-detail-page, .object-detail-page').first()
      await expect(detailRoot).toBeVisible({ timeout: 15000 })
      await expect(page.locator('.load-error')).toHaveCount(0)
      await expect(page.locator('.field-item')).toHaveCount(scenario.businessFields.length, { timeout: 15000 })
      for (const text of scenario.expectedTexts) {
        await expect(page.locator('.detail-content')).toContainText(text)
      }
    })
  }
})
