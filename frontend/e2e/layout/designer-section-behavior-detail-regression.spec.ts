import { test, expect, type Route } from '@playwright/test'
import {
  clickDesignerSaveDraft,
  clickDesignerSectionHeader,
  waitForDesignerReady
} from '../helpers/page-ready.helpers'
type AnyRecord = Record<string, any>

const OBJECT_CODE = 'Asset'
const RECORD_ID = 'asset-e2e-section-behavior-1'
const LAYOUT_ID = 'layout-asset-readonly-section-behavior'

const recordPayload = {
  id: RECORD_ID,
  assetName: 'Regression Laptop',
  createdBy: { username: 'admin' },
  createdAt: '2026-02-25T12:00:00+08:00',
  updatedBy: { username: 'admin' },
  updatedAt: '2026-02-25T12:30:00+08:00'
}

function buildInitialLayoutConfig() {
  return {
    sections: [
      {
        id: 'section-basic',
        type: 'section',
        title: 'Basic Information',
        columns: 2,
        collapsible: false,
        collapsed: false,
        fields: [
          {
            id: 'field-asset-name',
            fieldCode: 'assetName',
            label: 'Asset Name',
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

function getFirstSection(layoutConfig: AnyRecord): AnyRecord {
  const first = Array.isArray(layoutConfig?.sections) ? layoutConfig.sections[0] : null
  return first || {}
}

function fulfillSuccess(route: Route, data: unknown) {
  return route.fulfill({
    status: 200,
    contentType: 'application/json',
    body: JSON.stringify({ success: true, data })
  })
}

test.describe('Layout Designer Section Behavior -> Detail Regression', () => {
  test('readonly detail page must reflect saved section columns/collapsible/collapsed', async ({ page }) => {
    let activeLayoutConfig = buildInitialLayoutConfig()
    let saveCallCount = 0

    await page.addInitScript(() => {
      localStorage.setItem('access_token', 'e2e-designer-section-behavior-token')
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

      if (pathname.endsWith(`/api/system/page-layouts/${LAYOUT_ID}/`)) {
        if (route.request().method() === 'PATCH') {
          saveCallCount += 1
          const body = route.request().postDataJSON() as AnyRecord
          const nextConfig = (body?.layoutConfig || body?.layout_config) as AnyRecord
          if (nextConfig?.sections?.length) activeLayoutConfig = nextConfig
        }

        return fulfillSuccess(route, {
          id: LAYOUT_ID,
          layoutCode: `${OBJECT_CODE}_readonly_section_behavior_e2e`,
          layoutName: 'Asset Readonly Layout',
          mode: 'readonly',
          status: 'draft',
          version: 1,
          isDefault: false,
          layoutConfig: activeLayoutConfig
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
            status: 'draft',
            version: 1,
            layoutConfig: activeLayoutConfig
          }
        })
      }

      if (pathname.endsWith(`/api/system/objects/${OBJECT_CODE}/metadata/`)) {
        return fulfillSuccess(route, {
          code: OBJECT_CODE,
          name: OBJECT_CODE,
          permissions: { view: true, change: true, delete: true }
        })
      }

      if (pathname.endsWith(`/api/system/objects/${OBJECT_CODE}/fields/`)) {
        const context = url.searchParams.get('context') || 'detail'
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

      if (pathname.endsWith(`/api/system/objects/${OBJECT_CODE}/${RECORD_ID}/`)) {
        return fulfillSuccess(route, recordPayload)
      }

      return fulfillSuccess(route, {})
    })

    await page.goto(
      `/system/page-layouts/designer?layoutId=${LAYOUT_ID}&objectCode=${OBJECT_CODE}&layoutType=readonly&layoutName=Asset%20Readonly&businessObjectId=bo-asset`
    )

    await waitForDesignerReady(page)

    await clickDesignerSectionHeader(page)
    await expect(page.getByTestId('layout-section-property-editor')).toBeVisible()

    const columnsProp = page.getByTestId('section-prop-columns').first()
    await expect(columnsProp).toBeVisible()
    await columnsProp.click({ force: true })
    await page.locator('.el-select-dropdown__item').filter({ hasText: /^1$/ }).first().click()

    const collapsibleSwitch = page.getByTestId('section-prop-collapsible').locator('.el-switch').first()
    await expect(collapsibleSwitch).toBeVisible()
    await collapsibleSwitch.click({ force: true })

    const collapsedSwitch = page.getByTestId('section-prop-collapsed').locator('.el-switch').first()
    await expect(collapsedSwitch).toBeVisible()
    await collapsedSwitch.click({ force: true })

    await clickDesignerSaveDraft(page)

    await expect.poll(() => saveCallCount).toBe(1)
    await expect.poll(() => Number(getFirstSection(activeLayoutConfig).columns || 0)).toBe(1)
    await expect.poll(() => Boolean(getFirstSection(activeLayoutConfig).collapsible)).toBe(true)
    await expect.poll(() => Boolean(getFirstSection(activeLayoutConfig).collapsed)).toBe(true)

    await page.goto(`/objects/${OBJECT_CODE}/${RECORD_ID}`)
    await expect(page.locator('.dynamic-detail-page').first()).toBeVisible()
    await expect(page.locator('.load-error')).toHaveCount(0)

    const firstSection = page.locator('.detail-sections .detail-section').first()
    await expect(firstSection).toHaveClass(/is-collapsed/)
    await expect(firstSection.locator('.field-col.el-col-24')).toHaveCount(1)
  })
})


