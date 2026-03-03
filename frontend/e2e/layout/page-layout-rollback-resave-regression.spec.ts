import { test, expect, type Route } from '@playwright/test'
import { waitForDesignerReady } from '../helpers/page-ready.helpers'
type AnyRecord = Record<string, any>

const OBJECT_CODE = 'Asset'
const LAYOUT_ID = 'layout-asset-rollback-resave'
const LAYOUT_NAME = 'Asset Form Layout'

function buildLayoutConfigWithIds(label: string): AnyRecord {
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
            label,
            fieldType: 'text',
            span: 1,
            visible: true,
            required: false,
            readonly: false
          }
        ]
      }
    ],
    actions: []
  }
}

function buildLegacyLayoutWithoutIds(label: string): AnyRecord {
  return {
    sections: [
      {
        type: 'section',
        title: 'Basic Legacy',
        columns: 1,
        fields: [
          {
            fieldCode: 'assetName',
            label,
            fieldType: 'text',
            span: 1,
            visible: true,
            required: false,
            readonly: false
          }
        ]
      }
    ],
    actions: []
  }
}

function fulfillSuccess(route: Route, data: unknown) {
  return route.fulfill({
    status: 200,
    contentType: 'application/json',
    body: JSON.stringify({ success: true, data })
  })
}

test.describe('Page Layout Rollback -> Re-save Regression', () => {
  test('rolled back legacy layout should be normalized and remain editable in designer', async ({ page }) => {
    let currentVersion = '2'
    let activeLayoutConfig = buildLayoutConfigWithIds('Asset Name V2')
    let rollbackCallCount = 0
    const patchBodies: AnyRecord[] = []

    await page.addInitScript(() => {
      localStorage.setItem('access_token', 'e2e-page-layout-rollback-resave-token')
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

      if (pathname.endsWith(`/api/system/page-layouts/by-object/${OBJECT_CODE}/`)) {
        return fulfillSuccess(route, [
          {
            id: LAYOUT_ID,
            layoutCode: `${OBJECT_CODE}_form_rollback_resave_e2e`,
            layoutName: LAYOUT_NAME,
            mode: 'edit',
            description: 'Rollback re-save regression',
            status: 'published',
            version: currentVersion,
            isDefault: true,
            isActive: true,
            isSystem: false,
            layoutConfig: activeLayoutConfig
          }
        ])
      }

      if (pathname.endsWith(`/api/system/page-layouts/${LAYOUT_ID}/history/`)) {
        return fulfillSuccess(route, [
          { version: '2', status: 'published' },
          { version: '1', status: 'published' }
        ])
      }

      if (pathname.endsWith(`/api/system/page-layouts/${LAYOUT_ID}/rollback/1/`)) {
        rollbackCallCount += 1
        currentVersion = '1'
        activeLayoutConfig = buildLegacyLayoutWithoutIds('Asset Name V1 Legacy')
        return fulfillSuccess(route, {
          id: LAYOUT_ID,
          version: '1',
          status: 'published'
        })
      }

      if (pathname.endsWith(`/api/system/page-layouts/${LAYOUT_ID}/`)) {
        if (route.request().method() === 'PATCH') {
          const body = route.request().postDataJSON() as AnyRecord
          patchBodies.push(body)
          const nextConfig = (body?.layoutConfig || body?.layout_config) as AnyRecord | undefined
          if (nextConfig) activeLayoutConfig = JSON.parse(JSON.stringify(nextConfig))
          return fulfillSuccess(route, {
            id: LAYOUT_ID,
            layoutName: LAYOUT_NAME,
            mode: 'edit',
            status: body?.status || 'draft',
            version: currentVersion,
            layoutConfig: activeLayoutConfig
          })
        }
        return fulfillSuccess(route, {
          id: LAYOUT_ID,
          layoutCode: `${OBJECT_CODE}_form_rollback_resave_e2e`,
          layoutName: LAYOUT_NAME,
          mode: 'edit',
          status: 'published',
          version: currentVersion,
          isDefault: true,
          isActive: true,
          layoutConfig: activeLayoutConfig
        })
      }

      if (pathname.endsWith(`/api/system/objects/${OBJECT_CODE}/runtime/`)) {
        return fulfillSuccess(route, {
          runtimeVersion: Number(currentVersion),
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
              }
            ],
            reverseRelations: []
          },
          layout: {
            id: LAYOUT_ID,
            mode: 'edit',
            status: 'published',
            version: Number(currentVersion),
            layoutConfig: activeLayoutConfig
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
              isSystem: false,
              showInDetail: true,
              showInForm: true,
              sectionName: 'basic',
              span: 12
            }
          ],
          reverse_relations: [],
          context: url.searchParams.get('context') || 'form'
        })
      }

      if (pathname.endsWith(`/api/system/objects/${OBJECT_CODE}/metadata/`)) {
        return fulfillSuccess(route, {
          code: OBJECT_CODE,
          name: OBJECT_CODE,
          permissions: { view: true, change: true, delete: true }
        })
      }

      if (pathname.endsWith(`/api/system/objects/${OBJECT_CODE}/`)) {
        return fulfillSuccess(route, {
          code: OBJECT_CODE,
          id: 'bo-asset',
          name: OBJECT_CODE
        })
      }

      return fulfillSuccess(route, {})
    })

    await page.goto(`/system/page-layouts?objectCode=${OBJECT_CODE}&objectName=Asset`)
    await expect(page.locator('.page-layout-list').first()).toBeVisible()

    const rollbackButton = page.getByTestId('layout-list-rollback-button').first()
    await expect(rollbackButton).toBeVisible()
    await rollbackButton.click()
    await expect(page.locator('.el-message-box')).toBeVisible()
    await page.locator('.el-message-box__btns .el-button--primary').click()

    await expect.poll(() => rollbackCallCount).toBe(1)
    const patchCountAfterRollback = patchBodies.length

    await page.goto(
      `/system/page-layouts/designer?layoutId=${LAYOUT_ID}&objectCode=${OBJECT_CODE}&layoutType=edit&layoutName=Asset%20Form&businessObjectId=bo-asset`
    )

    await waitForDesignerReady(page)
    await expect(page.locator('[data-testid="layout-canvas-field"]').first()).toBeVisible()

    await page.getByTestId('layout-save-button').first().click()

    await expect.poll(() => patchBodies.length).toBeGreaterThan(patchCountAfterRollback)
    const latestPatch = patchBodies[patchBodies.length - 1] || {}
    const latestConfig = (latestPatch.layoutConfig || latestPatch.layout_config) as AnyRecord

    expect(latestConfig?.sections?.[0]?.id).toBeTruthy()
    expect(latestConfig?.sections?.[0]?.fields?.[0]?.id).toBeTruthy()
    expect(latestConfig?.sections?.[0]?.fields?.[0]?.fieldCode).toBe('assetName')
  })
})



