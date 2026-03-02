import { test, expect, type Page, type Route } from '@playwright/test'

type AnyRecord = Record<string, any>

const OBJECT_CODE = 'Asset'
const LAYOUT_ID = 'layout-asset-readonly-rollback-failure'
const LAYOUT_NAME = 'Asset Form Layout'
const LATEST_VERSION = '2'
const LABEL_V2 = 'Asset Name V2'

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

async function setupMock(
  page: Page,
  options: {
    historyEntries: Array<Record<string, any>>
    handleRollback: (route: Route, version: string) => Promise<void>
  }
) {
  await page.addInitScript(() => {
    localStorage.setItem('access_token', 'e2e-page-layout-rollback-failure-token')
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
          layoutCode: `${OBJECT_CODE}_form_rollback_failure_e2e`,
          layoutName: LAYOUT_NAME,
          mode: 'edit',
          description: 'Shared form layout for rollback failure regression',
          status: 'published',
          version: LATEST_VERSION,
          isDefault: true,
          isActive: true,
          isSystem: false,
          layoutConfig: buildLayoutConfig(LABEL_V2)
        }
      ])
    }

    if (pathname.endsWith(`/api/system/page-layouts/${LAYOUT_ID}/history/`)) {
      return fulfillSuccess(route, options.historyEntries)
    }

    const rollbackMatch = pathname.match(new RegExp(`/api/system/page-layouts/${LAYOUT_ID}/rollback/([^/]+)/$`))
    if (rollbackMatch) {
      const version = rollbackMatch[1]
      return options.handleRollback(route, version)
    }

    if (pathname.endsWith(`/api/system/objects/${OBJECT_CODE}/runtime/`)) {
      return fulfillSuccess(route, {
        runtimeVersion: Number(LATEST_VERSION),
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
          version: Number(LATEST_VERSION),
          layoutConfig: buildLayoutConfig(LABEL_V2)
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

    return fulfillSuccess(route, {})
  })
}

test.describe('Page Layout Rollback Failure Regression', () => {
  test('should warn and skip rollback when no previous version exists', async ({ page }) => {
    let rollbackCallCount = 0

    await setupMock(page, {
      historyEntries: [{ version: LATEST_VERSION, status: 'published' }],
      handleRollback: async (route) => {
        rollbackCallCount += 1
        await fulfillSuccess(route, { id: LAYOUT_ID, version: LATEST_VERSION, status: 'published' })
      }
    })

    await page.goto(`/system/page-layouts?objectCode=${OBJECT_CODE}&objectName=Asset`)
    await expect(page.locator('.page-layout-list').first()).toBeVisible()

    await expect(page.locator('tbody tr')).toHaveCount(1)
    await expect(page.locator('.version-badge').first()).toContainText(LATEST_VERSION)

    await page.getByTestId('layout-list-rollback-button').first().click()
    await expect(page.locator('.el-message-box')).toBeVisible()
    await page.locator('.el-message-box__btns .el-button--primary').click()

    await expect(
      page.locator('.el-message .el-message__content', {
        hasText: 'No previous version available for rollback'
      }).first()
    ).toBeVisible()
    await expect.poll(() => rollbackCallCount).toBe(0)
    await expect(page.locator('.version-badge').first()).toContainText(LATEST_VERSION)

  })

  test('should surface backend message when rollback returns success=false', async ({ page }) => {
    let rollbackCallCount = 0
    const rollbackMessage = 'Rollback target missing'

    await setupMock(page, {
      historyEntries: [
        { version: LATEST_VERSION, status: 'published' },
        { version: '1', status: 'published' }
      ],
      handleRollback: async (route, version) => {
        rollbackCallCount += 1
        expect(version).toBe('1')
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            success: false,
            error: {
              code: 'ROLLBACK_ERROR',
              message: rollbackMessage
            }
          })
        })
      }
    })

    await page.goto(`/system/page-layouts?objectCode=${OBJECT_CODE}&objectName=Asset`)
    await expect(page.locator('.page-layout-list').first()).toBeVisible()

    await expect(page.locator('tbody tr')).toHaveCount(1)
    await expect(page.locator('.version-badge').first()).toContainText(LATEST_VERSION)

    await page.getByTestId('layout-list-rollback-button').first().click()
    await expect(page.locator('.el-message-box')).toBeVisible()
    await page.locator('.el-message-box__btns .el-button--primary').click()

    await expect.poll(() => rollbackCallCount).toBe(1)
    await expect(page.locator('.el-message .el-message__content', { hasText: rollbackMessage }).first()).toBeVisible()
    await expect(page.locator('.version-badge').first()).toContainText(LATEST_VERSION)

  })

  test('should not show duplicate fallback message when rollback returns HTTP 500 unified error', async ({ page }) => {
    let rollbackCallCount = 0
    const rollbackMessage = 'Rollback service unavailable'

    await setupMock(page, {
      historyEntries: [
        { version: LATEST_VERSION, status: 'published' },
        { version: '1', status: 'published' }
      ],
      handleRollback: async (route, version) => {
        rollbackCallCount += 1
        expect(version).toBe('1')
        await route.fulfill({
          status: 500,
          contentType: 'application/json',
          body: JSON.stringify({
            success: false,
            error: {
              code: 'ROLLBACK_ERROR',
              message: rollbackMessage
            }
          })
        })
      }
    })

    await page.goto(`/system/page-layouts?objectCode=${OBJECT_CODE}&objectName=Asset`)
    await expect(page.locator('.page-layout-list').first()).toBeVisible()

    await expect(page.locator('tbody tr')).toHaveCount(1)
    await expect(page.locator('.version-badge').first()).toContainText(LATEST_VERSION)

    await page.getByTestId('layout-list-rollback-button').first().click()
    await expect(page.locator('.el-message-box')).toBeVisible()
    await page.locator('.el-message-box__btns .el-button--primary').click()

    const backendMessageLocator = page.locator('.el-message .el-message__content', { hasText: rollbackMessage })
    await expect.poll(() => rollbackCallCount).toBe(1)
    await expect(backendMessageLocator.first()).toBeVisible()
    await expect(backendMessageLocator).toHaveCount(1)
    await expect(page.locator('.el-message .el-message__content', { hasText: 'Rollback failed' })).toHaveCount(0)
    await expect(page.locator('.version-badge').first()).toContainText(LATEST_VERSION)
  })
})
