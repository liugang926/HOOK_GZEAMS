import { expect, test, type Page, type Route } from '@playwright/test'
import { waitForDesignerReady } from '../helpers/page-ready.helpers'

const OBJECT_CODE = 'Asset'
const LAYOUT_ID = 'layout-asset-related-groups-preview'
const STORAGE_KEY = `gzeams:detail:related-groups:${OBJECT_CODE}:designer-preview:edit:${LAYOUT_ID}`

function fulfillSuccess(route: Route, data: unknown) {
  return route.fulfill({
    status: 200,
    contentType: 'application/json',
    body: JSON.stringify({ success: true, data })
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

async function mockApis(page: Page) {
  await page.addInitScript(([key]) => {
    localStorage.setItem('access_token', 'e2e-designer-related-groups-token')
    localStorage.setItem('current_org_id', 'org-e2e')
    localStorage.setItem('locale', 'en-US')
    if (!localStorage.getItem(key as string)) {
      localStorage.setItem(key as string, JSON.stringify({ expanded: ['finance'] }))
    }
  }, [STORAGE_KEY])

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
              showInForm: true
            }
          ],
          reverseRelations: [
            {
              code: 'workflow_instances',
              name: 'Workflow Instances',
              label: 'Workflow Instances',
              relationDisplayMode: 'inline_readonly',
              targetObjectCode: 'WorkflowInstance',
              groupKey: 'workflow',
              groupName: 'Workflow',
              groupOrder: 20,
              defaultExpanded: true
            },
            {
              code: 'finance_vouchers',
              name: 'Finance Vouchers',
              label: 'Finance Vouchers',
              relationDisplayMode: 'inline_readonly',
              targetObjectCode: 'FinanceVoucher',
              groupKey: 'finance',
              groupName: 'Finance',
              groupOrder: 30,
              defaultExpanded: false
            }
          ]
        },
        layout: {
          id: LAYOUT_ID,
          mode: 'readonly',
          status: 'draft',
          version: 1,
          layoutConfig: {
            sections: [
              {
                id: 'section-basic',
                type: 'section',
                title: 'Basic Information',
                columns: 1,
                fields: [
                  {
                    id: 'field-asset-name',
                    fieldCode: 'assetName',
                    label: 'Asset Name',
                    fieldType: 'text',
                    span: 1,
                    visible: true,
                    readonly: true
                  }
                ]
              }
            ],
            actions: []
          }
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

test.describe('Layout Designer Related Groups Scope Persistence Regression', () => {
  test('should restore and persist related group expansion with designer scope id', async ({ page }) => {
    await mockApis(page)

    await page.goto(
      `/system/page-layouts/designer?layoutId=${LAYOUT_ID}&objectCode=${OBJECT_CODE}&layoutType=readonly&layoutName=Asset%20Readonly&businessObjectId=bo-asset`
    )
    await waitForDesignerReady(page)
    await openRelatedObjectsTab(page)
    await expect(page.locator('.related-groups-collapse')).toBeVisible()

    await expect(groupItem(page, 'Workflow')).not.toHaveClass(/is-active/)
    await expect(groupItem(page, 'Finance')).toHaveClass(/is-active/)

    await groupItem(page, 'Workflow').locator('.related-group-header').click()
    await expect(groupItem(page, 'Workflow')).toHaveClass(/is-active/)
    await expect.poll(async () => {
      return await page.evaluate((key) => localStorage.getItem(key), STORAGE_KEY)
    }).toContain('"workflow"')

    await page.reload()
    await waitForDesignerReady(page)
    await openRelatedObjectsTab(page)
    await expect(groupItem(page, 'Workflow')).toHaveClass(/is-active/)
    await expect(groupItem(page, 'Finance')).toHaveClass(/is-active/)
  })
})
