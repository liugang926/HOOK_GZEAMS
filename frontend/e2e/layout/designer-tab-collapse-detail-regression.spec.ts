import { test, expect, type Route } from '@playwright/test'

type AnyRecord = Record<string, any>
type ScenarioType = 'tab' | 'collapse'

interface Scenario {
  type: ScenarioType
  layoutId: string
  baseTitle: string
  updatedTitle: string
  nestedTitle: string
  updatedFieldLabel: string
}

const OBJECT_CODE = 'Asset'
const RECORD_ID = 'asset-e2e-tab-collapse-1'

const recordPayload = {
  id: RECORD_ID,
  assetName: 'Regression Laptop',
  createdBy: { username: 'admin' },
  createdAt: '2026-02-25T13:00:00+08:00',
  updatedBy: { username: 'admin' },
  updatedAt: '2026-02-25T13:30:00+08:00'
}

const scenarios: Scenario[] = [
  {
    type: 'tab',
    layoutId: 'layout-asset-readonly-tab',
    baseTitle: 'Operations',
    updatedTitle: 'Operations Snapshot',
    nestedTitle: 'Overview',
    updatedFieldLabel: 'Asset Display Name Tab'
  },
  {
    type: 'collapse',
    layoutId: 'layout-asset-readonly-collapse',
    baseTitle: 'Lifecycle',
    updatedTitle: 'Lifecycle Snapshot',
    nestedTitle: 'Basic Group',
    updatedFieldLabel: 'Asset Display Name Collapse'
  }
]

function buildLayoutConfig(scenario: Scenario): AnyRecord {
  const baseField = {
    id: 'field-asset-name',
    fieldCode: 'assetName',
    label: 'Asset Name',
    fieldType: 'text',
    span: 1,
    visible: true,
    required: false,
    readonly: true
  }

  if (scenario.type === 'tab') {
    return {
      sections: [
        {
          id: 'section-tab',
          type: 'tab',
          title: scenario.baseTitle,
          columns: 2,
          collapsible: false,
          collapsed: false,
          tabs: [
            {
              id: 'tab-overview',
              title: scenario.nestedTitle,
              fields: [baseField]
            }
          ]
        }
      ],
      actions: []
    }
  }

  return {
    sections: [
      {
        id: 'section-collapse',
        type: 'collapse',
        title: scenario.baseTitle,
        columns: 2,
        collapsible: true,
        collapsed: false,
        items: [
          {
            id: 'collapse-basic',
            title: scenario.nestedTitle,
            fields: [baseField]
          }
        ]
      }
    ],
    actions: []
  }
}

function getFirstSectionTitle(layoutConfig: AnyRecord): string {
  const first = Array.isArray(layoutConfig?.sections) ? layoutConfig.sections[0] : null
  return (first?.title || '') as string
}

function getNestedField(layoutConfig: AnyRecord, scenario: Scenario): AnyRecord {
  const first = Array.isArray(layoutConfig?.sections) ? layoutConfig.sections[0] : null
  if (!first) return {}
  if (scenario.type === 'tab') {
    return (first?.tabs?.[0]?.fields?.[0] || {}) as AnyRecord
  }
  return (first?.items?.[0]?.fields?.[0] || {}) as AnyRecord
}

function fulfillSuccess(route: Route, data: unknown) {
  return route.fulfill({
    status: 200,
    contentType: 'application/json',
    body: JSON.stringify({ success: true, data })
  })
}

test.describe('Layout Designer Tab/Collapse -> Detail Regression', () => {
  for (const scenario of scenarios) {
    test(`${scenario.type} section title save must reflect on readonly detail`, async ({ page }) => {
      let activeLayoutConfig = buildLayoutConfig(scenario)
      let saveCallCount = 0

      await page.addInitScript(() => {
        localStorage.setItem('access_token', 'e2e-designer-tab-collapse-token')
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

        if (pathname.endsWith(`/api/system/page-layouts/${scenario.layoutId}/`)) {
          if (route.request().method() === 'PATCH') {
            saveCallCount += 1
            const body = route.request().postDataJSON() as AnyRecord
            const nextConfig = (body?.layoutConfig || body?.layout_config) as AnyRecord
            if (nextConfig?.sections?.length) activeLayoutConfig = nextConfig
          }

          return fulfillSuccess(route, {
            id: scenario.layoutId,
            layoutCode: `${OBJECT_CODE}_readonly_${scenario.type}_e2e`,
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
              id: scenario.layoutId,
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
        `/system/page-layouts/designer?layoutId=${scenario.layoutId}&objectCode=${OBJECT_CODE}&layoutType=readonly&layoutName=Asset%20Readonly&businessObjectId=bo-asset`
      )

      await expect(page.getByTestId('layout-designer')).toBeVisible()
      await page.getByTestId('layout-section-header').first().click()
      await expect(page.getByTestId('layout-section-property-editor')).toBeVisible()

      const titleInput = page.getByTestId('section-prop-title').locator('input').first()
      await expect(titleInput).toBeVisible()
      await titleInput.fill(scenario.updatedTitle)
      await titleInput.press('Tab')

      const saveButton = page.getByTestId('layout-save-button').first()
      await expect(saveButton).toBeVisible()
      await saveButton.click()

      await expect.poll(() => saveCallCount).toBe(1)
      await expect.poll(() => getFirstSectionTitle(activeLayoutConfig)).toBe(scenario.updatedTitle)

      await page.goto(`/objects/${OBJECT_CODE}/${RECORD_ID}`)
      await expect(page.locator('.dynamic-detail-page').first()).toBeVisible()
      await expect(page.locator('.load-error')).toHaveCount(0)

      const expectedTitle = `${scenario.updatedTitle} / ${scenario.nestedTitle}`
      await expect(page.locator('.detail-sections .section-title', { hasText: expectedTitle }).first()).toBeVisible()
      await expect(page.locator('.detail-content')).toContainText(recordPayload.assetName)
    })

    test(`${scenario.type} field props save must reflect on readonly detail`, async ({ page }) => {
      let activeLayoutConfig = buildLayoutConfig(scenario)
      let saveCallCount = 0

      await page.addInitScript(() => {
        localStorage.setItem('access_token', 'e2e-designer-tab-collapse-token')
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

        if (pathname.endsWith(`/api/system/page-layouts/${scenario.layoutId}/`)) {
          if (route.request().method() === 'PATCH') {
            saveCallCount += 1
            const body = route.request().postDataJSON() as AnyRecord
            const nextConfig = (body?.layoutConfig || body?.layout_config) as AnyRecord
            if (nextConfig?.sections?.length) activeLayoutConfig = nextConfig
          }

          return fulfillSuccess(route, {
            id: scenario.layoutId,
            layoutCode: `${OBJECT_CODE}_readonly_${scenario.type}_e2e`,
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
              id: scenario.layoutId,
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
        `/system/page-layouts/designer?layoutId=${scenario.layoutId}&objectCode=${OBJECT_CODE}&layoutType=readonly&layoutName=Asset%20Readonly&businessObjectId=bo-asset`
      )

      await expect(page.getByTestId('layout-designer')).toBeVisible()

      const fieldCard = page
        .locator('[data-testid="layout-canvas-field"][data-field-code="assetName"]')
        .first()

      if (!(await fieldCard.isVisible()) && scenario.type === 'collapse') {
        await page.locator('.el-collapse-item__header', { hasText: scenario.nestedTitle }).first().click({ force: true })
      }

      await expect(fieldCard).toBeVisible()
      await fieldCard.click({ position: { x: 4, y: 4 }, force: true })

      const fieldPropertyEditor = page.getByTestId('layout-field-property-editor')
      if (!(await fieldPropertyEditor.count())) {
        await page.locator('.canvas-content .el-form-item__label').first().click({ force: true })
      }
      await expect(fieldPropertyEditor).toBeVisible()

      const labelInput = page.getByTestId('field-prop-label').locator('input').first()
      await expect(labelInput).toBeVisible()
      await labelInput.fill(scenario.updatedFieldLabel)
      await labelInput.press('Tab')

      const spanSelect = page.getByTestId('field-prop-span').first()
      await expect(spanSelect).toBeVisible()
      await spanSelect.click({ force: true })
      await page.locator('.el-select-dropdown__item').filter({ hasText: /^2\s*\/\s*2$/ }).first().click()

      const readonlySwitch = page.getByTestId('field-prop-readonly').locator('.el-switch').first()
      await expect(readonlySwitch).toBeVisible()
      if ((await readonlySwitch.getAttribute('aria-checked')) !== 'false') {
        await readonlySwitch.click({ force: true })
      }

      const saveButton = page.getByTestId('layout-save-button').first()
      await expect(saveButton).toBeVisible()
      await saveButton.click()

      await expect.poll(() => saveCallCount).toBe(1)
      await expect.poll(() => getNestedField(activeLayoutConfig, scenario).label).toBe(scenario.updatedFieldLabel)
      await expect.poll(() => Number(getNestedField(activeLayoutConfig, scenario).span || 0)).toBe(2)
      await expect.poll(() => Boolean(getNestedField(activeLayoutConfig, scenario).readonly)).toBe(false)

      await page.goto(`/objects/${OBJECT_CODE}/${RECORD_ID}`)
      await expect(page.locator('.dynamic-detail-page').first()).toBeVisible()
      await expect(page.locator('.load-error')).toHaveCount(0)

      await expect(page.locator('.detail-content')).toContainText(recordPayload.assetName)
      const fieldLabel = page.locator('.detail-sections .field-label', { hasText: scenario.updatedFieldLabel }).first()
      await expect(fieldLabel).toBeVisible()

      const fieldCol = fieldLabel.locator('xpath=ancestor::div[contains(@class,"field-col")]').first()
      await expect(fieldCol).toHaveClass(/el-col-24/)
    })

    test(`${scenario.type} field visible=false must hide on readonly detail`, async ({ page }) => {
      let activeLayoutConfig = buildLayoutConfig(scenario)
      let saveCallCount = 0

      await page.addInitScript(() => {
        localStorage.setItem('access_token', 'e2e-designer-tab-collapse-token')
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

        if (pathname.endsWith(`/api/system/page-layouts/${scenario.layoutId}/`)) {
          if (route.request().method() === 'PATCH') {
            saveCallCount += 1
            const body = route.request().postDataJSON() as AnyRecord
            const nextConfig = (body?.layoutConfig || body?.layout_config) as AnyRecord
            if (nextConfig?.sections?.length) activeLayoutConfig = nextConfig
          }

          return fulfillSuccess(route, {
            id: scenario.layoutId,
            layoutCode: `${OBJECT_CODE}_readonly_${scenario.type}_e2e`,
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
              id: scenario.layoutId,
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
        `/system/page-layouts/designer?layoutId=${scenario.layoutId}&objectCode=${OBJECT_CODE}&layoutType=readonly&layoutName=Asset%20Readonly&businessObjectId=bo-asset`
      )

      await expect(page.getByTestId('layout-designer')).toBeVisible()

      const fieldCard = page
        .locator('[data-testid="layout-canvas-field"][data-field-code="assetName"]')
        .first()

      if (!(await fieldCard.isVisible()) && scenario.type === 'collapse') {
        await page.locator('.el-collapse-item__header', { hasText: scenario.nestedTitle }).first().click({ force: true })
      }

      await expect(fieldCard).toBeVisible()
      await fieldCard.click({ position: { x: 4, y: 4 }, force: true })

      const fieldPropertyEditor = page.getByTestId('layout-field-property-editor')
      if (!(await fieldPropertyEditor.count())) {
        await page.locator('.canvas-content .el-form-item__label').first().click({ force: true })
      }
      await expect(fieldPropertyEditor).toBeVisible()

      const visibleSwitch = page.getByTestId('field-prop-visible').locator('.el-switch').first()
      await expect(visibleSwitch).toBeVisible()
      if ((await visibleSwitch.getAttribute('aria-checked')) !== 'false') {
        await visibleSwitch.click({ force: true })
      }

      const saveButton = page.getByTestId('layout-save-button').first()
      await expect(saveButton).toBeVisible()
      await saveButton.click()

      await expect.poll(() => saveCallCount).toBe(1)
      await expect.poll(() => Boolean(getNestedField(activeLayoutConfig, scenario).visible)).toBe(false)

      await page.goto(`/objects/${OBJECT_CODE}/${RECORD_ID}`)
      await expect(page.locator('.dynamic-detail-page').first()).toBeVisible()
      await expect(page.locator('.load-error')).toHaveCount(0)

      await expect(page.locator('.detail-sections .field-col')).toHaveCount(0)
      await expect(page.locator('.detail-sections .field-label', { hasText: 'Asset Name' })).toHaveCount(0)
    })
  }
})
