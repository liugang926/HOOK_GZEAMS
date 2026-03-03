import { test, expect, type Route, type Page } from '@playwright/test'
import { clickDesignerSaveDraft, gotoDesignerAndWait } from '../helpers/page-ready.helpers'

interface LayoutField {
  fieldCode?: string
  label?: string
  span?: number
  readonly?: boolean
  visible?: boolean
  [key: string]: unknown
}

interface LayoutSection {
  fields?: LayoutField[]
  tabs?: Array<{ fields?: LayoutField[]; [key: string]: unknown }>
  items?: Array<{ fields?: LayoutField[]; [key: string]: unknown }>
  [key: string]: unknown
}

interface LayoutConfig {
  sections?: LayoutSection[]
  [key: string]: unknown
}

const OBJECT_CODE = 'Asset'
const RECORD_ID = 'asset-e2e-multi-field-1'
const LAYOUT_ID = 'layout-asset-readonly-multi-field-session'

const UPDATED_NAME_LABEL = 'Asset Name Session Final'
const UPDATED_CODE_LABEL = 'Asset Code Session Hidden'

const recordPayload = {
  id: RECORD_ID,
  assetName: 'Regression Laptop',
  assetCode: 'ASSET-2026-001',
  createdBy: { username: 'admin' },
  createdAt: '2026-02-25T13:00:00+08:00',
  updatedBy: { username: 'admin' },
  updatedAt: '2026-02-25T13:30:00+08:00'
}

function buildLayoutConfig(): LayoutConfig {
  return {
    sections: [
      {
        id: 'section-tab',
        type: 'tab',
        title: 'Operations',
        columns: 2,
        collapsible: false,
        collapsed: false,
        tabs: [
          {
            id: 'tab-overview',
            title: 'Overview',
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
        ]
      },
      {
        id: 'section-collapse',
        type: 'collapse',
        title: 'Lifecycle',
        columns: 2,
        collapsible: true,
        collapsed: false,
        items: [
          {
            id: 'collapse-basic',
            title: 'Basic Group',
            fields: [
              {
                id: 'field-asset-code',
                fieldCode: 'assetCode',
                label: 'Asset Code',
                fieldType: 'text',
                span: 1,
                visible: true,
                required: false,
                readonly: true
              }
            ]
          }
        ]
      }
    ],
    actions: []
  }
}

function findField(layoutConfig: LayoutConfig, fieldCode: string): LayoutField | null {
  for (const section of layoutConfig?.sections || []) {
    for (const field of section?.fields || []) {
      if (field?.fieldCode === fieldCode) return field
    }
    for (const tab of section?.tabs || []) {
      for (const field of tab?.fields || []) {
        if (field?.fieldCode === fieldCode) return field
      }
    }
    for (const item of section?.items || []) {
      for (const field of item?.fields || []) {
        if (field?.fieldCode === fieldCode) return field
      }
    }
  }
  return null
}

function fulfillSuccess(route: Route, data: unknown) {
  return route.fulfill({
    status: 200,
    contentType: 'application/json',
    body: JSON.stringify({ success: true, data })
  })
}

async function selectCanvasField(page: Page, fieldCode: string) {
  const visibleCard = page.locator(`[data-testid="layout-canvas-field"][data-field-code="${fieldCode}"]:visible`).first()
  const card = (await visibleCard.count()) ? visibleCard : page.locator(`[data-testid="layout-canvas-field"][data-field-code="${fieldCode}"]`).first()
  await expect(card).toBeVisible()
  await card.click({ position: { x: 4, y: 4 }, force: true })

  const editor = page.getByTestId('layout-field-property-editor')
  const labelInput = page.getByTestId('field-prop-label').locator('input').first()
  const isExpectedFieldSelected = async () => {
    if (!(await labelInput.count())) return false
    const value = await labelInput.inputValue()
    if (fieldCode === 'assetName') return value.includes('Asset Name')
    if (fieldCode === 'assetCode') return value.includes('Asset Code')
    return value.length > 0
  }

  if (!(await editor.count()) || !(await isExpectedFieldSelected())) {
    await card.click({ position: { x: 4, y: 4 }, force: true })
  }

  if (!(await isExpectedFieldSelected())) {
    await page
      .locator(`[data-testid="layout-canvas-field"][data-field-code="${fieldCode}"]:visible .el-form-item__label`)
      .first()
      .click({ force: true })
  }

  await expect(editor).toBeVisible()
  await expect.poll(async () => isExpectedFieldSelected(), { timeout: 10000 }).toBe(true)
}

test.describe('Layout Designer Multi-field Session Regression', () => {
  test('continuous cross-container field edits must persist and render correctly', async ({ page }) => {
    let activeLayoutConfig = buildLayoutConfig()
    let saveCallCount = 0

    await page.addInitScript(() => {
      localStorage.setItem('access_token', 'e2e-designer-multi-field-token')
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
          const body = route.request().postDataJSON() as { layoutConfig?: LayoutConfig; layout_config?: LayoutConfig }
          const nextConfig = body?.layoutConfig || body?.layout_config
          if (nextConfig?.sections?.length) activeLayoutConfig = nextConfig
        }

        return fulfillSuccess(route, {
          id: LAYOUT_ID,
          layoutCode: `${OBJECT_CODE}_readonly_multi_field_session_e2e`,
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
              },
              {
                code: 'assetCode',
                name: 'Asset Code',
                label: 'Asset Code',
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
            },
            {
              code: 'assetCode',
              name: 'Asset Code',
              label: 'Asset Code',
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

    await gotoDesignerAndWait(
      page,
      `/system/page-layouts/designer?layoutId=${LAYOUT_ID}&objectCode=${OBJECT_CODE}&layoutType=readonly&layoutName=Asset%20Readonly&businessObjectId=bo-asset`,
      { requiredFieldCode: 'assetName' }
    )

    await selectCanvasField(page, 'assetName')
    const labelInput = page.getByTestId('field-prop-label').locator('input').first()
    await labelInput.fill('Asset Name Session Step 1')
    await labelInput.press('Tab')

    const spanSelect = page.getByTestId('field-prop-span').first()
    await spanSelect.click({ force: true })
    await page.locator('.el-select-dropdown__item').filter({ hasText: /^2\s*\/\s*2$/ }).first().click()

    const readonlySwitch = page.getByTestId('field-prop-readonly').locator('.el-switch').first()
    if ((await readonlySwitch.getAttribute('aria-checked')) !== 'false') {
      await readonlySwitch.click({ force: true })
    }

    const collapseHeader = page.locator('.el-collapse-item__header', { hasText: 'Basic Group' }).first()
    const collapseItem = page.locator('.el-collapse-item', { has: collapseHeader }).first()
    const isCollapsed = ((await collapseItem.getAttribute('class')) || '').includes('is-active') === false
    if (await collapseHeader.isVisible() && isCollapsed) {
      await collapseHeader.click({ force: true })
    }
    await selectCanvasField(page, 'assetCode')

    const codeLabelInput = page.getByTestId('field-prop-label').locator('input').first()
    await codeLabelInput.fill(UPDATED_CODE_LABEL)
    await codeLabelInput.press('Tab')

    const visibleSwitch = page.getByTestId('field-prop-visible').locator('.el-switch').first()
    if ((await visibleSwitch.getAttribute('aria-checked')) !== 'false') {
      await visibleSwitch.click({ force: true })
    }

    await selectCanvasField(page, 'assetName')
    const finalLabelInput = page.getByTestId('field-prop-label').locator('input').first()
    await finalLabelInput.fill(UPDATED_NAME_LABEL)
    await finalLabelInput.press('Tab')

    await clickDesignerSaveDraft(page)

    await expect.poll(() => saveCallCount).toBe(1)
    await expect.poll(() => findField(activeLayoutConfig, 'assetName')?.label).toBe(UPDATED_NAME_LABEL)
    await expect.poll(() => Number(findField(activeLayoutConfig, 'assetName')?.span || 0)).toBe(2)
    await expect.poll(() => Boolean(findField(activeLayoutConfig, 'assetName')?.readonly)).toBe(false)
    await expect.poll(() => findField(activeLayoutConfig, 'assetCode')?.label).toBe(UPDATED_CODE_LABEL)
    await expect.poll(() => Boolean(findField(activeLayoutConfig, 'assetCode')?.visible)).toBe(false)

    await page.goto(`/objects/${OBJECT_CODE}/${RECORD_ID}`)
    await expect(page.locator('.dynamic-detail-page').first()).toBeVisible()
    await expect(page.locator('.load-error')).toHaveCount(0)

    await expect(page.locator('.detail-sections .field-label', { hasText: UPDATED_NAME_LABEL }).first()).toBeVisible()
    await expect(page.locator('.detail-sections .field-label', { hasText: UPDATED_CODE_LABEL })).toHaveCount(0)
  })
})
