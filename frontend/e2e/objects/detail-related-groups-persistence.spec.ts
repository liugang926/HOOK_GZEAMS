import { expect, test, type Page, type Route } from '@playwright/test'

const OBJECT_CODE = 'Organization'
const RECORD_ID = 'org-related-1'

function fulfillSuccess(route: Route, data: unknown) {
  return route.fulfill({
    status: 200,
    contentType: 'application/json',
    body: JSON.stringify({ success: true, data })
  })
}

function buildRuntimeLayoutResponse() {
  return {
    runtime_version: 1,
    mode: 'edit',
    context: 'form',
    fields: {
      editable_fields: [
        {
          code: 'name',
          name: 'Organization Name',
          label: 'Organization Name',
          fieldType: 'text',
          isHidden: false,
          showInForm: true,
          showInDetail: true,
          sortOrder: 1
        }
      ],
      reverse_relations: []
    },
    layout: {
      layout_type: 'form',
      layout_config: {
        sections: [
          {
            id: 'overview',
            name: 'overview',
            title: 'Overview',
            columns: 1,
            fields: [{ fieldCode: 'name' }]
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
    localStorage.setItem('access_token', 'e2e-related-groups-token')
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
        primaryOrganization: {
          id: 'org-e2e',
          name: 'E2E Org',
          code: 'E2E'
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
      return fulfillSuccess(route, buildRuntimeLayoutResponse())
    }

    if (pathname.endsWith(`/api/system/objects/${OBJECT_CODE}/fields/`)) {
      return fulfillSuccess(route, {
        editable_fields: [],
        reverse_relations: [],
        context: 'detail'
      })
    }

    if (pathname.endsWith(`/api/system/objects/${OBJECT_CODE}/${RECORD_ID}/`) && route.request().method() === 'GET') {
      return fulfillSuccess(route, {
        id: RECORD_ID,
        name: 'Organization E2E',
        createdAt: '2026-03-05T10:00:00Z',
        updatedAt: '2026-03-05T10:00:00Z'
      })
    }

    if (pathname.endsWith(`/api/system/objects/${OBJECT_CODE}/relations/`)) {
      return fulfillSuccess(route, {
        objectCode: OBJECT_CODE,
        locale: 'en-US',
        relations: [
          {
            relationCode: 'workflow_instances',
            relationName: 'Workflow Instances',
            targetObjectCode: 'WorkflowInstance',
            relationKind: 'derived_query',
            displayMode: 'inline_readonly',
            sortOrder: 10,
            groupKey: 'workflow',
            groupName: 'Workflow',
            groupOrder: 20,
            defaultExpanded: true
          },
          {
            relationCode: 'finance_vouchers',
            relationName: 'Finance Vouchers',
            targetObjectCode: 'FinanceVoucher',
            relationKind: 'direct_fk',
            displayMode: 'inline_readonly',
            sortOrder: 20,
            groupKey: 'finance',
            groupName: 'Finance',
            groupOrder: 30,
            defaultExpanded: false
          }
        ]
      })
    }

    if (pathname.endsWith(`/api/system/objects/${OBJECT_CODE}/${RECORD_ID}/related/workflow_instances/`)) {
      return fulfillSuccess(route, {
        count: 1,
        next: null,
        previous: null,
        results: [{ id: 'wf-1', code: 'WF-001', name: 'WF Instance 1' }],
        targetObjectCode: 'WorkflowInstance'
      })
    }

    if (pathname.endsWith(`/api/system/objects/${OBJECT_CODE}/${RECORD_ID}/related/finance_vouchers/`)) {
      return fulfillSuccess(route, {
        count: 1,
        next: null,
        previous: null,
        results: [{ id: 'fv-1', code: 'FV-001', name: 'Voucher 1' }],
        targetObjectCode: 'FinanceVoucher'
      })
    }

    if (pathname.endsWith('/api/system/objects/WorkflowInstance/fields/')) {
      return fulfillSuccess(route, {
        editable_fields: [
          { code: 'code', name: 'Code', showInList: true, sortOrder: 1 },
          { code: 'name', name: 'Name', showInList: true, sortOrder: 2 }
        ]
      })
    }

    if (pathname.endsWith('/api/system/objects/FinanceVoucher/fields/')) {
      return fulfillSuccess(route, {
        editable_fields: [
          { code: 'code', name: 'Code', showInList: true, sortOrder: 1 },
          { code: 'name', name: 'Name', showInList: true, sortOrder: 2 }
        ]
      })
    }

    return fulfillSuccess(route, {})
  })
}

function groupItem(page: Page, title: string) {
  return page.locator('.related-group-item').filter({
    has: page.locator('.group-name', { hasText: title })
  }).first()
}

async function openRelatedObjectsTab(page: Page) {
  const relatedTab = page.getByRole('tab', { name: /Related Objects/i }).first()
  await expect(relatedTab).toBeVisible()
  await relatedTab.click()
  await expect(relatedTab).toHaveAttribute('aria-selected', 'true')
}

async function setGroupExpanded(page: Page, title: string, expanded: boolean) {
  const item = groupItem(page, title)
  await expect(item).toBeVisible()
  const isActive = await item.evaluate((el) => el.classList.contains('is-active'))
  if (isActive !== expanded) {
    await item.locator('.related-group-header').first().click()
  }
  await expect.poll(async () => {
    return item.evaluate((el) => el.classList.contains('is-active'))
  }).toBe(expanded)
}

test.describe('Detail Related Groups Persistence', () => {
  test('should persist related group expanded state across refresh and edit mode', async ({ page }) => {
    await mockApis(page)

    await page.goto(`/objects/${OBJECT_CODE}/${RECORD_ID}`)
    await expect(page.locator('.load-error')).toHaveCount(0)
    await openRelatedObjectsTab(page)
    await expect(page.locator('.related-groups-collapse')).toBeVisible()

    await expect(groupItem(page, 'Workflow')).toHaveClass(/is-active/)
    await expect(groupItem(page, 'Finance')).not.toHaveClass(/is-active/)

    await setGroupExpanded(page, 'Workflow', false)
    await setGroupExpanded(page, 'Finance', true)
    await expect.poll(async () => {
      return await page.evaluate(() => {
        return localStorage.getItem('gzeams:detail:related-groups:Organization:org-related-1')
      })
    }).toContain('"finance"')

    await page.reload()
    await openRelatedObjectsTab(page)
    await expect(page.locator('.related-groups-collapse')).toBeVisible()
    await expect.poll(async () => {
      return await groupItem(page, 'Workflow').evaluate((el) => el.classList.contains('is-active'))
    }).toBe(false)
    await expect.poll(async () => {
      return await groupItem(page, 'Finance').evaluate((el) => el.classList.contains('is-active'))
    }).toBe(true)

    await page.goto(`/objects/${OBJECT_CODE}/${RECORD_ID}/edit`)
    await expect(page.getByRole('button', { name: 'Cancel' })).toBeVisible()
    await expect(page.getByRole('button', { name: 'Save' })).toBeVisible()
    await openRelatedObjectsTab(page)
    await expect.poll(async () => {
      return await groupItem(page, 'Workflow').evaluate((el) => el.classList.contains('is-active'))
    }).toBe(false)
    await expect.poll(async () => {
      return await groupItem(page, 'Finance').evaluate((el) => el.classList.contains('is-active'))
    }).toBe(true)
  })
})
