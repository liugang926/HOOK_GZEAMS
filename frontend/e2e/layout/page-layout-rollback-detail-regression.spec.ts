import { test, expect, type Route } from '@playwright/test'
import { confirmDialogPrimary } from '../helpers/page-ready.helpers'
import {
  getDetailContent,
  waitForDetailPageReady
} from '../helpers/detail-page.helpers'

type AnyRecord = Record<string, any>

const OBJECT_CODE = 'Asset'
const LAYOUT_ID = 'layout-asset-readonly-rollback'
const RECORD_ID = 'asset-e2e-rollback-1'
const LAYOUT_NAME = 'Asset Form Layout'

const LABEL_V2 = 'Asset Name V2'
const LABEL_V1 = 'Asset Name V1'

const recordPayload = {
  id: RECORD_ID,
  assetName: 'Regression Laptop',
  createdBy: { username: 'admin' },
  createdAt: '2026-02-25T13:00:00+08:00',
  updatedBy: { username: 'admin' },
  updatedAt: '2026-02-25T13:30:00+08:00'
}

function buildLayoutConfig(label: string): AnyRecord {
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
            readonly: true
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

test.describe('Page Layout Rollback -> Detail Regression', () => {
  test('rollback to previous version should reflect on readonly detail page', async ({ page }) => {
    let runtimeLayoutConfig = buildLayoutConfig(LABEL_V2)
    let currentVersion = '2'
    let rollbackCallCount = 0

    await page.addInitScript(() => {
      localStorage.setItem('access_token', 'e2e-page-layout-rollback-token')
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

      if (pathname.endsWith('/api/system/menu/flat/')) {
        return fulfillSuccess(route, [])
      }

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
            layoutCode: `${OBJECT_CODE}_form_rollback_e2e`,
            layoutName: LAYOUT_NAME,
            mode: 'edit',
            description: 'Shared form layout for rollback test',
            status: 'published',
            version: currentVersion,
            isDefault: true,
            isActive: true,
            isSystem: false,
            layoutConfig: runtimeLayoutConfig
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
        runtimeLayoutConfig = buildLayoutConfig(LABEL_V1)
        return fulfillSuccess(route, {
          id: LAYOUT_ID,
          version: '1',
          status: 'published'
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
            mode: 'readonly',
            status: 'published',
            version: Number(currentVersion),
            layoutConfig: runtimeLayoutConfig
          }
        })
      }

      if (pathname.endsWith(`/api/system/objects/${OBJECT_CODE}/fields/`)) {
        const context = url.searchParams.get('context') || 'form'
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
          context
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
        return fulfillSuccess(route, recordPayload)
      }

      return fulfillSuccess(route, {})
    })

    await page.goto(`/system/page-layouts?objectCode=${OBJECT_CODE}&objectName=Asset`)

    await expect(page.locator('.page-layout-list').first()).toBeVisible()
    await expect(page.locator('tbody tr')).toHaveCount(1)
    await expect(page.locator('.version-badge').first()).toContainText('2')

    const rollbackButton = page.getByTestId('layout-list-rollback-button').first()
    await expect(rollbackButton).toBeVisible()
    await rollbackButton.click()

    await confirmDialogPrimary(page)

    await expect.poll(() => rollbackCallCount).toBe(1)
    await expect(page.locator('.version-badge').first()).toContainText('1')

    await page.goto(`/objects/${OBJECT_CODE}/${RECORD_ID}`)
    await waitForDetailPageReady(page)
    await expect(page.locator('.detail-sections .field-label', { hasText: LABEL_V1 }).first()).toBeVisible()
    await expect(page.locator('.detail-sections .field-label', { hasText: LABEL_V2 })).toHaveCount(0)
    await expect(getDetailContent(page)).toContainText(recordPayload.assetName)
  })
})
