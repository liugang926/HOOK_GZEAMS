import { expect, test, type Locator, type Page, type Route, type TestInfo } from '@playwright/test'
import {
  getDetailFieldItem,
  getHeaderActionButton,
  waitForDetailPageReady
} from '../helpers/detail-page.helpers'
import { waitForDesignerReady } from '../helpers/page-ready.helpers'

type AnyRecord = Record<string, unknown>
type ScenarioKind = 'section' | 'tab' | 'collapse' | 'sidebar'

interface FieldExpectation {
  code: string
  label: string
  colStart: number
  row: number
  value: string
}

interface Scenario {
  kind: ScenarioKind
  layoutId: string
  recordId: string
  designerLayoutConfig: AnyRecord
  runtimeLayoutConfig: AnyRecord
  mainFields: [FieldExpectation, FieldExpectation]
  sidebarField?: FieldExpectation
  containerTitle?: string
}

const OBJECT_CODE = 'Asset'
const RUNTIME_SHADOW_LABEL = 'Runtime Shadow Field'

const fulfillSuccess = (route: Route, data: unknown) => {
  return route.fulfill({
    status: 200,
    contentType: 'application/json',
    body: JSON.stringify({ success: true, data })
  })
}

const placement = (row: number, colStart: number, columns: number, order: number, colSpan = 1) => ({
  row,
  colStart,
  colSpan,
  rowSpan: 1,
  columns,
  totalRows: 1,
  order,
  canvas: {
    x: (colStart - 1) / columns,
    y: 0,
    width: colSpan / columns,
    height: 1
  }
})

const placementSnake = (row: number, colStart: number, columns: number, order: number, colSpan = 1) => ({
  row,
  col_start: colStart,
  col_span: colSpan,
  row_span: 1,
  columns,
  total_rows: 1,
  order,
  canvas: {
    x: (colStart - 1) / columns,
    y: 0,
    width: colSpan / columns,
    height: 1
  }
})

const layoutField = (field: FieldExpectation, columns: number, order: number) => ({
  id: `field-${field.code}`,
  fieldCode: field.code,
  label: field.label,
  fieldType: 'text',
  span: 1,
  visible: true,
  required: false,
  readonly: false,
  layoutPlacement: placement(field.row, field.colStart, columns, order)
})

const layoutFieldSnakePlacement = (field: FieldExpectation, columns: number, order: number) => ({
  id: `field-${field.code}`,
  fieldCode: field.code,
  label: field.label,
  fieldType: 'text',
  span: 1,
  visible: true,
  required: false,
  readonly: false,
  layout_placement: placementSnake(field.row, field.colStart, columns, order)
})

const unknownRuntimeField = (code: string, label: string) => ({
  fieldCode: code,
  label,
  fieldType: 'text',
  span: 1,
  visible: true,
  readonly: true
})

const mainLeft: FieldExpectation = {
  code: 'left_field',
  label: 'Left Field',
  colStart: 1,
  row: 1,
  value: 'L-001'
}

const mainRight: FieldExpectation = {
  code: 'right_field',
  label: 'Right Field',
  colStart: 2,
  row: 1,
  value: 'R-001'
}

const sidebarNote: FieldExpectation = {
  code: 'sidebar_note',
  label: 'Sidebar Note',
  colStart: 1,
  row: 1,
  value: 'SIDEBAR-001'
}

const buildSectionScenario = (): Scenario => ({
  kind: 'section',
  layoutId: 'layout-asset-placement-section',
  recordId: 'asset-placement-section-1',
  designerLayoutConfig: {
    sections: [
      {
        id: 'section-basic',
        type: 'section',
        title: 'Basic',
        columns: 2,
        fields: [layoutField(mainLeft, 2, 1), layoutField(mainRight, 2, 2)]
      }
    ],
    actions: []
  },
  runtimeLayoutConfig: {
    sections: [
      {
        id: 'section-basic',
        type: 'section',
        title: 'Basic',
        columns: 2,
        fields: [
          layoutField(mainLeft, 2, 1),
          unknownRuntimeField('id', 'ID'),
          unknownRuntimeField('runtime_shadow_field', RUNTIME_SHADOW_LABEL),
          layoutFieldSnakePlacement(mainRight, 2, 2)
        ]
      }
    ],
    actions: []
  },
  mainFields: [mainLeft, mainRight]
})

const buildTabScenario = (): Scenario => ({
  kind: 'tab',
  layoutId: 'layout-asset-placement-tab',
  recordId: 'asset-placement-tab-1',
  containerTitle: 'Overview',
  designerLayoutConfig: {
    sections: [
      {
        id: 'section-tab',
        type: 'tab',
        title: 'Operations',
        columns: 2,
        tabs: [
          {
            id: 'tab-overview',
            title: 'Overview',
            fields: [layoutField(mainLeft, 2, 1), layoutField(mainRight, 2, 2)]
          }
        ]
      }
    ],
    actions: []
  },
  runtimeLayoutConfig: {
    sections: [
      {
        id: 'section-tab',
        type: 'tab',
        title: 'Operations',
        columns: 2,
        tabs: [
          {
            id: 'tab-overview',
            title: 'Overview',
            fields: [
              layoutField(mainLeft, 2, 1),
              unknownRuntimeField('id', 'ID'),
              unknownRuntimeField('runtime_shadow_field', RUNTIME_SHADOW_LABEL),
              layoutFieldSnakePlacement(mainRight, 2, 2)
            ]
          }
        ]
      }
    ],
    actions: []
  },
  mainFields: [mainLeft, mainRight]
})

const buildCollapseScenario = (): Scenario => ({
  kind: 'collapse',
  layoutId: 'layout-asset-placement-collapse',
  recordId: 'asset-placement-collapse-1',
  containerTitle: 'Basic Group',
  designerLayoutConfig: {
    sections: [
      {
        id: 'section-collapse',
        type: 'collapse',
        title: 'Lifecycle',
        columns: 2,
        collapsible: true,
        collapsed: false,
        items: [
          {
            id: 'item-basic',
            title: 'Basic Group',
            collapsed: false,
            fields: [layoutField(mainLeft, 2, 1), layoutField(mainRight, 2, 2)]
          }
        ]
      }
    ],
    actions: []
  },
  runtimeLayoutConfig: {
    sections: [
      {
        id: 'section-collapse',
        type: 'collapse',
        title: 'Lifecycle',
        columns: 2,
        collapsible: true,
        collapsed: false,
        items: [
          {
            id: 'item-basic',
            title: 'Basic Group',
            collapsed: false,
            fields: [
              layoutField(mainLeft, 2, 1),
              unknownRuntimeField('id', 'ID'),
              unknownRuntimeField('runtime_shadow_field', RUNTIME_SHADOW_LABEL),
              layoutFieldSnakePlacement(mainRight, 2, 2)
            ]
          }
        ]
      }
    ],
    actions: []
  },
  mainFields: [mainLeft, mainRight]
})

const buildSidebarScenario = (): Scenario => ({
  kind: 'sidebar',
  layoutId: 'layout-asset-placement-sidebar',
  recordId: 'asset-placement-sidebar-1',
  designerLayoutConfig: {
    sections: [
      {
        id: 'section-main',
        type: 'section',
        title: 'Main Info',
        position: 'main',
        columns: 2,
        fields: [layoutField(mainLeft, 2, 1), layoutField(mainRight, 2, 2)]
      },
      {
        id: 'section-sidebar',
        type: 'section',
        title: 'Sidebar Info',
        position: 'sidebar',
        columns: 1,
        fields: [layoutField(sidebarNote, 1, 1)]
      }
    ],
    actions: []
  },
  runtimeLayoutConfig: {
    sections: [
      {
        id: 'section-main',
        type: 'section',
        title: 'Main Info',
        position: 'main',
        columns: 2,
        fields: [
          layoutField(mainLeft, 2, 1),
          unknownRuntimeField('id', 'ID'),
          unknownRuntimeField('runtime_shadow_field', RUNTIME_SHADOW_LABEL),
          layoutFieldSnakePlacement(mainRight, 2, 2)
        ]
      },
      {
        id: 'section-sidebar',
        type: 'section',
        title: 'Sidebar Info',
        position: 'sidebar',
        columns: 1,
        fields: [layoutFieldSnakePlacement(sidebarNote, 1, 1)]
      }
    ],
    actions: []
  },
  mainFields: [mainLeft, mainRight],
  sidebarField: sidebarNote
})

const scenarios: Scenario[] = [
  buildSectionScenario(),
  buildTabScenario(),
  buildCollapseScenario(),
  buildSidebarScenario()
]

const toRuntimeFieldMeta = (field: FieldExpectation) => ({
  code: field.code,
  name: field.label,
  label: field.label,
  fieldType: 'text',
  isSystem: false,
  showInDetail: true,
  showInForm: true,
  showInList: true,
  sectionName: 'basic',
  span: 12
})

const getScenarioKnownFields = (scenario: Scenario): FieldExpectation[] => {
  const fields = [...scenario.mainFields]
  if (scenario.sidebarField) fields.push(scenario.sidebarField)
  return fields
}

async function mockApis(page: Page, scenario: Scenario) {
  const knownFields = getScenarioKnownFields(scenario)
  const runtimeFields = knownFields.map(toRuntimeFieldMeta)
  const recordPayload = knownFields.reduce<AnyRecord>((acc, field) => {
    acc[field.code] = field.value
    return acc
  }, {
    id: scenario.recordId,
    createdBy: { username: 'admin' },
    createdAt: '2026-03-01T08:00:00+08:00',
    updatedBy: { username: 'admin' },
    updatedAt: '2026-03-01T09:00:00+08:00'
  })

  await page.addInitScript(() => {
    localStorage.setItem('access_token', 'e2e-placement-baseline-token')
    localStorage.setItem('current_org_id', 'org-placement-baseline')
    localStorage.setItem('locale', 'en-US')
  })

  await page.route('**/*', async (route) => {
    const url = new URL(route.request().url())
    const pathname = url.pathname

    if (!pathname.startsWith('/api/')) return route.continue()

    if (pathname.endsWith('/api/system/objects/User/me/')) {
      return fulfillSuccess(route, {
        id: 'user-placement-baseline',
        username: 'admin',
        roles: ['admin'],
        permissions: ['*'],
        primaryOrganization: {
          id: 'org-placement-baseline',
          name: 'Placement Baseline Org',
          code: 'PBO'
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

    if (pathname.endsWith(`/api/system/page-layouts/${scenario.layoutId}/`)) {
      return fulfillSuccess(route, {
        id: scenario.layoutId,
        layoutCode: `${OBJECT_CODE}_${scenario.kind}_placement`,
        layoutName: `Asset ${scenario.kind} placement`,
        mode: 'readonly',
        status: 'draft',
        version: 1,
        isDefault: false,
        layoutConfig: scenario.designerLayoutConfig
      })
    }

    if (pathname.endsWith(`/api/system/objects/${OBJECT_CODE}/runtime/`)) {
      return fulfillSuccess(route, {
        runtimeVersion: 1,
        fields: {
          editableFields: runtimeFields,
          reverseRelations: []
        },
        layout: {
          id: scenario.layoutId,
          mode: 'readonly',
          status: 'draft',
          version: 1,
          layoutConfig: scenario.runtimeLayoutConfig
        }
      })
    }

    if (pathname.endsWith(`/api/system/objects/${OBJECT_CODE}/fields/`)) {
      const context = url.searchParams.get('context') || 'detail'
      return fulfillSuccess(route, {
        editable_fields: runtimeFields.map((field) => ({
          ...field,
          show_in_detail: field.showInDetail,
          show_in_form: field.showInForm
        })),
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

    if (pathname.endsWith(`/api/system/objects/${OBJECT_CODE}/${scenario.recordId}/`)) {
      return fulfillSuccess(route, recordPayload)
    }

    return fulfillSuccess(route, {})
  })
}

const designerFieldByCode = (page: Page, code: string) => {
  return page.locator(`.field-renderer[data-field-code="${code}"]`).first()
}

const detailFieldByLabel = (page: Page, label: string) => getDetailFieldItem(page, label)

const expectRightOfOnSameRow = async (left: Locator, right: Locator) => {
  const [leftBox, rightBox] = await Promise.all([left.boundingBox(), right.boundingBox()])
  expect(leftBox).not.toBeNull()
  expect(rightBox).not.toBeNull()
  expect((rightBox as { x: number }).x).toBeGreaterThan((leftBox as { x: number }).x)
  expect(Math.abs((rightBox as { y: number }).y - (leftBox as { y: number }).y)).toBeLessThanOrEqual(8)
}

const expectRightOf = async (left: Locator, right: Locator) => {
  const [leftBox, rightBox] = await Promise.all([left.boundingBox(), right.boundingBox()])
  expect(leftBox).not.toBeNull()
  expect(rightBox).not.toBeNull()
  expect((rightBox as { x: number }).x).toBeGreaterThan((leftBox as { x: number }).x)
}

const ensureDesignerFieldVisible = async (page: Page, scenario: Scenario, code: string) => {
  let locator = designerFieldByCode(page, code)
  if (await locator.isVisible()) return

  if (scenario.kind === 'tab' && scenario.containerTitle) {
    const tab = page.getByRole('tab', { name: scenario.containerTitle }).first()
    if (await tab.count()) await tab.click({ force: true })
  }

  if (scenario.kind === 'collapse' && scenario.containerTitle) {
    const collapseHeader = page.locator('.el-collapse-item__header', { hasText: scenario.containerTitle }).first()
    if (await collapseHeader.count()) await collapseHeader.click({ force: true })
  }

  locator = designerFieldByCode(page, code)
  await expect(locator).toBeVisible({ timeout: 10000 })
}

const assertMainFieldPair = async (
  page: Page,
  fields: [FieldExpectation, FieldExpectation],
  context: 'designer' | 'detail'
) => {
  const [leftField, rightField] = fields
  const leftLocator = context === 'designer'
    ? designerFieldByCode(page, leftField.code)
    : detailFieldByLabel(page, leftField.label)
  const rightLocator = context === 'designer'
    ? designerFieldByCode(page, rightField.code)
    : detailFieldByLabel(page, rightField.label)

  await expect(leftLocator).toBeVisible()
  await expect(rightLocator).toBeVisible()

  await expect(leftLocator).toHaveAttribute('data-grid-col-start', String(leftField.colStart))
  await expect(rightLocator).toHaveAttribute('data-grid-col-start', String(rightField.colStart))
  await expect(leftLocator).toHaveAttribute('data-grid-row', String(leftField.row))
  await expect(rightLocator).toHaveAttribute('data-grid-row', String(rightField.row))

  await expectRightOfOnSameRow(leftLocator, rightLocator)
}

const attachLayoutSnapshot = async (
  page: Page,
  testInfo: TestInfo,
  scenarioKind: ScenarioKind,
  phase: 'designer' | 'detail' | 'edit'
) => {
  const target = phase === 'designer'
    ? page.locator('.canvas-render-shell').first()
    : page.locator('.detail-layout-container').first()
  await expect(target).toBeVisible({ timeout: 10000 })
  const screenshot = await target.screenshot({ animations: 'disabled' })
  await testInfo.attach(`layout-${scenarioKind}-${phase}`, {
    body: screenshot,
    contentType: 'image/png'
  })
}

test.describe('Layout Placement Baseline Regression (Designer/Detail/Edit)', () => {
  test.setTimeout(120000)

  for (const scenario of scenarios) {
    test(`${scenario.kind} should keep persisted field placement across designer, detail and edit`, async ({ page }, testInfo) => {
      await mockApis(page, scenario)

      await page.goto(
        `/system/page-layouts/designer?layoutId=${scenario.layoutId}&objectCode=${OBJECT_CODE}&layoutType=readonly&layoutName=Asset%20Readonly&businessObjectId=bo-asset`
      )

      await waitForDesignerReady(page, {
        timeout: 30000,
        requiredFieldCode: scenario.mainFields[0].code
      })

      await ensureDesignerFieldVisible(page, scenario, scenario.mainFields[0].code)
      await ensureDesignerFieldVisible(page, scenario, scenario.mainFields[1].code)
      await assertMainFieldPair(page, scenario.mainFields, 'designer')

      if (scenario.sidebarField) {
        await ensureDesignerFieldVisible(page, scenario, scenario.sidebarField.code)
        const mainRight = designerFieldByCode(page, scenario.mainFields[1].code)
        const sidebar = designerFieldByCode(page, scenario.sidebarField.code)
        await expect(sidebar).toBeVisible()
        await expectRightOf(mainRight, sidebar)
      }
      await attachLayoutSnapshot(page, testInfo, scenario.kind, 'designer')

      await page.goto(`/objects/${OBJECT_CODE}/${scenario.recordId}`, { waitUntil: 'domcontentloaded' })
      await expect(page).toHaveURL(new RegExp(`/objects/${OBJECT_CODE}/${scenario.recordId}`))
      await waitForDetailPageReady(page, { timeout: 30_000 })
      await expect(page.locator('.detail-content').first()).toBeVisible({ timeout: 15000 })

      await assertMainFieldPair(page, scenario.mainFields, 'detail')
      await expect(page.locator('.detail-content .field-label', { hasText: RUNTIME_SHADOW_LABEL })).toHaveCount(0)

      if (scenario.sidebarField) {
        const mainRight = detailFieldByLabel(page, scenario.mainFields[1].label)
        const sidebar = detailFieldByLabel(page, scenario.sidebarField.label)
        await expect(sidebar).toBeVisible()
        await expectRightOf(mainRight, sidebar)
      }
      await attachLayoutSnapshot(page, testInfo, scenario.kind, 'detail')

      await getHeaderActionButton(page, /Edit/i).click()
      await expect(page.locator('.drawer-compat-proxy')).toBeVisible({ timeout: 10000 })

      await assertMainFieldPair(page, scenario.mainFields, 'detail')

      if (scenario.sidebarField) {
        const mainRight = detailFieldByLabel(page, scenario.mainFields[1].label)
        const sidebar = detailFieldByLabel(page, scenario.sidebarField.label)
        await expect(sidebar).toBeVisible()
        await expectRightOf(mainRight, sidebar)
      }

      await expect(page.locator('.detail-content .field-label', { hasText: RUNTIME_SHADOW_LABEL })).toHaveCount(0)
      await attachLayoutSnapshot(page, testInfo, scenario.kind, 'edit')
    })
  }
})
