import { expect, test, type Page, type Route } from '@playwright/test'

const OBJECT_CODE = 'Asset'
const RECORD_ID = 'asset-alignment-regression-1'

const fieldDefs = [
  { code: 'id_short', name: 'ID', fieldType: 'text' },
  {
    code: 'very_long_business_field_label_for_alignment',
    name: 'Very Long Business Field Label For Alignment Regression',
    fieldType: 'text'
  },
  { code: 'owner_department', name: 'Owner Department', fieldType: 'text' }
]

function fulfillSuccess(route: Route, data: unknown) {
  return route.fulfill({
    status: 200,
    contentType: 'application/json',
    body: JSON.stringify({ success: true, data })
  })
}

function buildRuntimeResponse() {
  return {
    runtime_version: 1,
    mode: 'edit',
    context: 'form',
    fields: {
      editable_fields: fieldDefs.map((field, index) => ({
        ...field,
        isHidden: false,
        isRequired: false,
        isReadonly: false,
        isSystem: false,
        showInDetail: true,
        showInForm: true,
        showInList: true,
        showInFilter: false,
        sortOrder: index + 1
      })),
      reverse_relations: []
    },
    layout: {
      layout_type: 'form',
      layout_config: {
        sections: [
          {
            id: 'alignment-section',
            name: 'alignment-section',
            title: 'Alignment Section',
            columns: 1,
            fields: [
              { fieldCode: 'id' },
              ...fieldDefs.map((field) => ({ fieldCode: field.code }))
            ]
          }
        ]
      },
      status: 'published',
      version: '1.0.0'
    },
    permissions: {
      view: true,
      add: true,
      change: true,
      delete: true
    },
    is_default: true
  }
}

async function mockApis(page: Page) {
  await page.addInitScript(() => {
    localStorage.setItem('access_token', 'e2e-detail-edit-alignment-token')
    localStorage.setItem('current_org_id', 'org-detail-edit-alignment')
    localStorage.setItem('locale', 'en-US')
  })

  await page.route('**/*', async (route) => {
    const url = new URL(route.request().url())
    const pathname = url.pathname
    if (!pathname.startsWith('/api/')) return route.continue()

    if (pathname.endsWith('/api/system/objects/User/me/')) {
      return fulfillSuccess(route, {
        id: 'user-detail-edit-alignment',
        username: 'admin',
        roles: ['admin'],
        permissions: ['*'],
        primaryOrganization: {
          id: 'org-detail-edit-alignment',
          name: 'Alignment Org',
          code: 'ALG'
        }
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

    if (pathname.endsWith(`/api/system/objects/${OBJECT_CODE}/metadata/`)) {
      return fulfillSuccess(route, {
        code: OBJECT_CODE,
        name: OBJECT_CODE,
        permissions: { view: true, add: true, change: true, delete: true }
      })
    }

    if (pathname.endsWith(`/api/system/objects/${OBJECT_CODE}/runtime/`)) {
      return fulfillSuccess(route, buildRuntimeResponse())
    }

    if (pathname.endsWith(`/api/system/objects/${OBJECT_CODE}/fields/`)) {
      return fulfillSuccess(route, {
        editable_fields: fieldDefs,
        reverse_relations: [],
        context: 'detail'
      })
    }

    if (pathname.endsWith(`/api/system/objects/${OBJECT_CODE}/${RECORD_ID}/`)) {
      return fulfillSuccess(route, {
        id: RECORD_ID,
        id_short: 'ALN-001',
        very_long_business_field_label_for_alignment:
          'This is a deliberately long field value to verify wrapping does not break alignment.',
        owner_department: 'Global Platform Engineering Department'
      })
    }

    return fulfillSuccess(route, {})
  })
}

async function collectValueLefts(page: Page, expectedCount: number): Promise<number[]> {
  const lefts: number[] = []
  const detailRoot = page.locator('.detail-content')
  const items = detailRoot.locator('.field-item')
  await expect(items).toHaveCount(expectedCount)

  for (let index = 0; index < expectedCount; index += 1) {
    const fieldItem = items.nth(index)
    await expect(fieldItem).toBeVisible()

    const box = await fieldItem.locator('.field-value').first().boundingBox()
    expect(box).not.toBeNull()
    lefts.push((box as { x: number }).x)
  }

  return lefts
}

function assertXAligned(lefts: number[], tolerance = 1) {
  const min = Math.min(...lefts)
  const max = Math.max(...lefts)
  expect(max - min).toBeLessThanOrEqual(tolerance)
}

test.describe('Detail/Edit Label-Value Alignment Regression', () => {
  test('detail and edit should keep identical value start offset with long labels', async ({ page }) => {
    await mockApis(page)
    await page.goto(`/objects/${OBJECT_CODE}/${RECORD_ID}`)

    await expect(page.locator('.load-error')).toHaveCount(0)
    await expect(page.locator('.detail-content .field-item')).toHaveCount(fieldDefs.length)

    const detailLefts = await collectValueLefts(page, fieldDefs.length)
    assertXAligned(detailLefts)

    await page.locator('.header-actions .el-button').first().click()
    await expect(page.getByRole('button', { name: 'Cancel' })).toBeVisible()
    await expect(page.getByRole('button', { name: 'Save' })).toBeVisible()

    const editLefts = await collectValueLefts(page, fieldDefs.length)
    assertXAligned(editLefts)
  })
})
