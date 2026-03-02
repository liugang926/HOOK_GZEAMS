import { test, expect, type Page, type Route } from '@playwright/test'

const OBJECT_CASES = [
  { code: 'Asset', expectedTitle: 'Asset List' },
  { code: 'FinanceVoucher', expectedTitle: 'Finance Voucher' },
  { code: 'ITAsset', expectedTitle: 'IT Asset' }
]

function fulfillSuccess(route: Route, data: unknown) {
  return route.fulfill({
    status: 200,
    contentType: 'application/json',
    body: JSON.stringify({ success: true, data })
  })
}

async function mockApis(page: Page) {
  await page.addInitScript(() => {
    localStorage.setItem('access_token', 'e2e-object-display-name-token')
    localStorage.setItem('current_org_id', 'org-object-display-name')
    localStorage.setItem('locale', 'en-US')
  })

  await page.route('**/*', async (route) => {
    const url = new URL(route.request().url())
    const pathname = url.pathname
    if (!pathname.startsWith('/api/')) return route.continue()

    if (pathname.endsWith('/api/system/objects/User/me/')) {
      return fulfillSuccess(route, {
        id: 'user-object-display-name',
        username: 'admin',
        roles: ['admin'],
        permissions: ['*'],
        primaryOrganization: { id: 'org-object-display-name', name: 'Regression Org', code: 'REG' }
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

    if (pathname.endsWith('/api/system/business-objects/')) {
      return fulfillSuccess(route, {
        hardcoded: OBJECT_CASES.map((item) => ({
          id: item.code,
          code: item.code,
          name: item.code,
          type: 'hardcoded',
          isHardcoded: true
        })),
        custom: []
      })
    }

    if (/\/api\/system\/business-objects\/by-code\/[^/]+\/$/.test(pathname)) {
      const code = decodeURIComponent(pathname.split('/').slice(-2, -1)[0] || '')
      return fulfillSuccess(route, {
        id: code,
        code,
        name: code,
        isHardcoded: true
      })
    }

    if (pathname.endsWith('/api/system/business-objects/fields/')) {
      return fulfillSuccess(route, {
        object_code: url.searchParams.get('object_code') || 'Unknown',
        fields: [
          {
            fieldName: 'name',
            displayName: 'Name',
            fieldType: 'text',
            isRequired: false,
            isEditable: true,
            sortOrder: 1,
            showInList: true,
            showInForm: true,
            showInDetail: true
          }
        ]
      })
    }

    if (/\/api\/system\/page-layouts\/by-object\/[^/]+\/$/.test(pathname)) {
      const code = decodeURIComponent(pathname.split('/').slice(-2, -1)[0] || '')
      return fulfillSuccess(route, [
        {
          id: `${code}-layout-edit`,
          layoutCode: `${code.toLowerCase()}_form_default`,
          layoutName: `${code} Edit Layout`,
          layoutType: 'form',
          mode: 'edit',
          description: '',
          isDefault: true,
          isActive: true,
          isSystem: false,
          status: 'published',
          version: '1.0.0',
          layoutConfig: { sections: [] }
        }
      ])
    }

    if (/\/api\/system\/objects\/[^/]+\/metadata\/$/.test(pathname)) {
      const code = decodeURIComponent(pathname.split('/').slice(-2, -1)[0] || '')
      return fulfillSuccess(route, {
        code,
        name: code,
        fields: [
          {
            code: 'name',
            name: 'Name',
            fieldType: 'text',
            isSearchable: true,
            showInList: true
          }
        ],
        permissions: { view: true, add: true, change: true, delete: true },
        layouts: {
          list: {
            columns: [{ fieldCode: 'name', label: 'Name', visible: true }]
          }
        }
      })
    }

    if (/\/api\/system\/objects\/[^/]+\/runtime\/$/.test(pathname)) {
      const code = decodeURIComponent(pathname.split('/').slice(-2, -1)[0] || '')
      const mode = url.searchParams.get('mode') || 'list'
      return fulfillSuccess(route, {
        runtime_version: 1,
        mode,
        context: mode,
        fields: {
          editable_fields: [
            {
              code: 'name',
              name: 'Name',
              fieldType: 'text',
              isSearchable: true,
              showInList: true
            }
          ],
          reverse_relations: []
        },
        layout: {
          layout_type: mode === 'list' ? 'list' : 'form',
          layout_config: {
            columns: [{ fieldCode: 'name', label: 'Name', visible: true }],
            sections: []
          },
          status: 'published',
          version: '1.0.0'
        },
        is_default: true,
        code
      })
    }

    if (/\/api\/system\/objects\/[^/]+\/$/.test(pathname)) {
      return fulfillSuccess(route, {
        count: 1,
        next: null,
        previous: null,
        results: [{ id: 'record-1', name: 'Record 1' }]
      })
    }

    return fulfillSuccess(route, {})
  })
}

test.describe('Object Display Name Consistency', () => {
  test('should keep list page title and layout page title consistent for core object modules', async ({ page }) => {
    await mockApis(page)

    for (const entry of OBJECT_CASES) {
      await page.goto(`/objects/${entry.code}`)
      await expect(page.locator('.base-list-page .page-title')).toHaveText(entry.expectedTitle)

      await page.goto(`/system/page-layouts?objectCode=${entry.code}&objectName=${entry.code}`)
      await expect(page.locator('.page-layout-list .page-header h3')).toContainText(entry.expectedTitle)
    }
  })
})
