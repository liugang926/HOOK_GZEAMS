import { test, expect, type Route } from '@playwright/test'
import { clickDesignerSaveDraft, waitForDesignerReady } from '../helpers/page-ready.helpers'

type AnyRecord = Record<string, any>

const OBJECT_CODE = 'Asset'
const RECORD_ID = 'asset-ref-compact-1'
const LAYOUT_ID = 'layout-asset-reference-compact'

const USER_POOL: Array<Record<string, any>> = [
  { id: 'user-alice', fullName: 'Alice Stone', username: 'alice', name: 'Alice Stone', code: 'U-ALICE', email: 'alice@example.com', mobile: '13800000001' },
  { id: 'user-john', fullName: 'John Carter', username: 'john', name: 'John Carter', code: 'U-JOHN', email: 'john@example.com', mobile: '13800000002' },
  { id: 'user-zoe', fullName: 'Zoe Green', username: 'zoe', name: 'Zoe Green', code: 'U-ZOE', email: 'zoe@example.com', mobile: '13800000003' }
]

function fulfillSuccess(route: Route, data: unknown) {
  return route.fulfill({
    status: 200,
    contentType: 'application/json',
    body: JSON.stringify({ success: true, data })
  })
}

function buildLookupColumns() {
  return [
    { key: 'fullName', minWidth: 220 },
    { key: 'username', minWidth: 180 },
    { key: 'id', minWidth: 180 },
    { key: 'email', minWidth: 220 },
    { key: 'mobile', minWidth: 160 }
  ]
}

function buildInitialLayoutConfig() {
  return {
    sections: [
      {
        id: 'section-basic',
        type: 'section',
        title: 'Basic Information',
        columns: 2,
        fields: [
          {
            id: 'field-asset-name',
            fieldCode: 'assetName',
            label: 'Asset Name',
            fieldType: 'text',
            span: 1,
            visible: true,
            required: false,
            readonly: false
          },
          {
            id: 'field-owner',
            fieldCode: 'owner',
            label: 'Owner',
            fieldType: 'reference',
            referenceObject: 'User',
            referenceDisplayField: 'fullName',
            referenceSecondaryField: 'username',
            span: 1,
            visible: true,
            required: false,
            readonly: false,
            componentProps: {
              lookupColumns: buildLookupColumns()
            }
          }
        ]
      }
    ],
    actions: []
  }
}

function findLayoutField(layoutConfig: AnyRecord, fieldCode: string): AnyRecord | null {
  const sections = Array.isArray(layoutConfig?.sections) ? layoutConfig.sections : []
  for (const section of sections) {
    const fields = Array.isArray(section?.fields) ? section.fields : []
    const found = fields.find((field: AnyRecord) => String(field?.fieldCode || '') === fieldCode)
    if (found) return found
  }
  return null
}

function buildEditableFields(layoutConfig: AnyRecord) {
  const ownerLayoutField = findLayoutField(layoutConfig, 'owner') || {}
  const ownerProps = {
    ...((ownerLayoutField.componentProps || {}) as AnyRecord),
    ...((ownerLayoutField.component_props || {}) as AnyRecord)
  }
  return [
    {
      code: 'assetName',
      name: 'Asset Name',
      label: 'Asset Name',
      fieldType: 'text',
      isRequired: false,
      isReadonly: false,
      showInDetail: true,
      showInForm: true,
      showInList: true
    },
    {
      code: 'owner',
      name: 'Owner',
      label: 'Owner',
      fieldType: 'reference',
      referenceObject: 'User',
      referenceDisplayField: 'fullName',
      referenceSecondaryField: 'username',
      componentProps: ownerProps,
      component_props: ownerProps,
      isRequired: false,
      isReadonly: false,
      showInDetail: true,
      showInForm: true,
      showInList: true
    }
  ]
}

function pickUsersBySearch(keyword: string): Array<Record<string, any>> {
  const q = keyword.trim().toLowerCase()
  if (!q) return USER_POOL
  return USER_POOL.filter((user) => {
    return (
      String(user.fullName || '').toLowerCase().includes(q) ||
      String(user.username || '').toLowerCase().includes(q) ||
      String(user.email || '').toLowerCase().includes(q) ||
      String(user.mobile || '').toLowerCase().includes(q)
    )
  })
}

test.describe('Layout Designer Reference Compact Keys Save Regression', () => {
  test('designer saved lookupCompactKeys should take effect in runtime compact profile', async ({ page }) => {
    let activeLayoutConfig = buildInitialLayoutConfig()
    let saveCallCount = 0

    await page.addInitScript(() => {
      localStorage.setItem('access_token', 'e2e-designer-reference-compact-token')
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

      if (pathname.endsWith(`/api/system/page-layouts/${LAYOUT_ID}/`)) {
        if (route.request().method() === 'PATCH') {
          saveCallCount += 1
          const body = route.request().postDataJSON() as AnyRecord
          const nextConfig = (body?.layoutConfig || body?.layout_config) as AnyRecord
          if (nextConfig?.sections?.length) activeLayoutConfig = nextConfig
        }

        return fulfillSuccess(route, {
          id: LAYOUT_ID,
          layoutCode: `${OBJECT_CODE}_reference_compact`,
          layoutName: 'Asset Reference Compact Layout',
          mode: 'edit',
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
            editableFields: buildEditableFields(activeLayoutConfig),
            reverseRelations: []
          },
          layout: {
            id: LAYOUT_ID,
            mode: 'edit',
            status: 'draft',
            version: 1,
            layoutConfig: activeLayoutConfig
          }
        })
      }

      if (pathname.endsWith(`/api/system/objects/${OBJECT_CODE}/fields/`)) {
        const editableFields = buildEditableFields(activeLayoutConfig).map((field) => ({
          ...field,
          field_type: field.fieldType,
          reference_object: field.referenceObject,
          reference_display_field: field.referenceDisplayField,
          reference_secondary_field: field.referenceSecondaryField
        }))
        return fulfillSuccess(route, {
          editable_fields: editableFields,
          reverse_relations: [],
          context: 'form'
        })
      }

      if (pathname.endsWith(`/api/system/objects/${OBJECT_CODE}/metadata/`)) {
        return fulfillSuccess(route, {
          code: OBJECT_CODE,
          name: OBJECT_CODE,
          permissions: { view: true, add: true, change: true, delete: true }
        })
      }

      if (pathname.endsWith(`/api/system/objects/${OBJECT_CODE}/${RECORD_ID}/`) && route.request().method() === 'GET') {
        return fulfillSuccess(route, {
          id: RECORD_ID,
          assetName: 'Compact Config Asset',
          owner: 'user-alice'
        })
      }

      if (pathname.endsWith(`/api/system/objects/${OBJECT_CODE}/${RECORD_ID}/`) && route.request().method() === 'PUT') {
        const body = route.request().postDataJSON() as AnyRecord
        return fulfillSuccess(route, { id: RECORD_ID, ...body })
      }

      if (pathname.endsWith('/api/system/objects/User/batch-get/')) {
        const body = route.request().postDataJSON() as { ids?: string[] }
        const ids = Array.isArray(body?.ids) ? body.ids.map((id) => String(id)) : []
        const map = new Map(USER_POOL.map((user) => [String(user.id), user]))
        const results = ids
          .map((id) => map.get(id))
          .filter((item): item is Record<string, any> => !!item)
        const missing_ids = ids.filter((id) => !map.has(id))
        return route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({ success: true, results, missing_ids })
        })
      }

      if (/\/api\/system\/objects\/User\/[^/]+\/$/.test(pathname)) {
        const id = pathname.split('/').filter(Boolean).pop() || ''
        const user = USER_POOL.find((item) => item.id === id)
        if (!user) {
          return route.fulfill({
            status: 404,
            contentType: 'application/json',
            body: JSON.stringify({ success: false, message: 'not found' })
          })
        }
        return fulfillSuccess(route, user)
      }

      if (pathname.endsWith('/api/system/objects/User/')) {
        const search = url.searchParams.get('search') || ''
        const pageNo = Number(url.searchParams.get('page') || '1')
        const pageSize = Number(url.searchParams.get('page_size') || '20')
        const filtered = pickUsersBySearch(search)
        const start = Math.max(0, (pageNo - 1) * pageSize)
        const results = filtered.slice(start, start + pageSize)
        return route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            success: true,
            count: filtered.length,
            results
          })
        })
      }

      return fulfillSuccess(route, {})
    })

    await page.goto(
      `/system/page-layouts/designer?layoutId=${LAYOUT_ID}&objectCode=${OBJECT_CODE}&layoutType=edit&layoutName=Asset%20Reference%20Compact&businessObjectId=bo-asset`
    )

    await waitForDesignerReady(page, { requiredFieldCode: 'owner' })
    const ownerCanvasField = page.locator('[data-testid="layout-canvas-field"][data-field-code="owner"]').first()
    await expect(ownerCanvasField).toBeVisible()
    await ownerCanvasField.click({ position: { x: 4, y: 4 } })

    const compactKeysEditor = page.getByTestId('field-prop-lookupCompactKeys').first()
    await expect(compactKeysEditor).toBeVisible()
    await compactKeysEditor.scrollIntoViewIfNeeded()
    const compactInput = compactKeysEditor.locator('input').first()
    await compactInput.click()
    await compactInput.fill('email')
    await compactInput.press('Enter')
    await expect(compactKeysEditor).toContainText('email')

    await clickDesignerSaveDraft(page)
    await expect.poll(() => saveCallCount).toBeGreaterThan(0)
    await expect.poll(() => {
      const owner = findLayoutField(activeLayoutConfig, 'owner') || {}
      const props = {
        ...((owner as AnyRecord).componentProps || {}),
        ...((owner as AnyRecord).component_props || {})
      }
      return Array.isArray(props.lookupCompactKeys) ? props.lookupCompactKeys.join(',') : ''
    }).toBe('email')

    await page.goto(`/objects/${OBJECT_CODE}/${RECORD_ID}`)
    await expect(page.locator('.load-error')).toHaveCount(0)
    const editButton = page.locator('.header-actions .el-button').filter({ hasText: /Edit|缂栬緫/i }).first()
    await expect(editButton).toBeVisible({ timeout: 20_000 })
    await editButton.click()
    await expect(page.getByRole('button', { name: 'Save' })).toBeVisible()

    const ownerField = page.locator('.field-item').filter({
      has: page.locator('.field-label', { hasText: 'Owner' })
    }).first()
    await expect(ownerField).toBeVisible()
    await ownerField.locator('.el-select').first().click()
    await page.locator('.reference-dropdown-footer').last().getByRole('button', { name: 'Advanced Search' }).click()

    const dialog = page.locator('.el-dialog').filter({
      has: page.locator('.lookup-toolbar')
    }).first()
    await expect(dialog).toBeVisible()
    await dialog.locator('.lookup-toolbar__columns-trigger').click()
    const settings = page.locator('.lookup-column-settings:visible').last()
    await settings.locator('.lookup-column-settings__profiles').getByText('Compact').click()
    await expect(dialog.locator('.el-table__header-wrapper')).toContainText('email')
    await expect(dialog.locator('.el-table__header-wrapper')).not.toContainText('mobile')
  })
})
