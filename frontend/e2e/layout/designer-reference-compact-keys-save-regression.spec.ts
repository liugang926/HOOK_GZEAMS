import { test, expect } from '@playwright/test'
import { clickDesignerSaveDraft, waitForDesignerReady } from '../helpers/page-ready.helpers'
import {
  ensureInlineEditMode,
  openLookupColumnSettings,
  openReferenceAdvancedLookup,
  selectLookupProfile
} from '../helpers/reference-lookup.helpers'
import { fulfillSuccess, mockReferenceLookupApis } from '../helpers/reference-lookup.api'

type AnyRecord = Record<string, unknown>

const OBJECT_CODE = 'Asset'
const RECORD_ID = 'asset-ref-compact-1'
const LAYOUT_ID = 'layout-asset-reference-compact'

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

test.describe('Layout Designer Reference Compact Keys Save Regression', () => {
  test('designer saved lookupCompactKeys should take effect in runtime compact profile', async ({ page }) => {
    let activeLayoutConfig = buildInitialLayoutConfig()
    let saveCallCount = 0

    await mockReferenceLookupApis(page, {
      accessToken: 'e2e-designer-reference-compact-token',
      orgId: 'org-e2e',
      currentUser: {
        id: 'user-e2e',
        username: 'admin',
        roles: ['admin'],
        permissions: ['*'],
        primaryOrganization: { id: 'org-e2e', name: 'E2E Org', code: 'E2E' }
      },
      searchKeys: ['fullName', 'username', 'email', 'mobile'],
      handleApiRoute: async ({ route, pathname }) => {
        if (pathname.endsWith(`/api/system/page-layouts/${LAYOUT_ID}/`)) {
          if (route.request().method() === 'PATCH') {
            saveCallCount += 1
            const body = route.request().postDataJSON() as AnyRecord
            const nextConfig = (body?.layoutConfig || body?.layout_config) as AnyRecord
            if (nextConfig?.sections?.length) activeLayoutConfig = nextConfig
          }

          await fulfillSuccess(route, {
            id: LAYOUT_ID,
            layoutCode: `${OBJECT_CODE}_reference_compact`,
            layoutName: 'Asset Reference Compact Layout',
            mode: 'edit',
            status: 'draft',
            version: 1,
            isDefault: false,
            layoutConfig: activeLayoutConfig
          })
          return true
        }

        if (pathname.endsWith(`/api/system/objects/${OBJECT_CODE}/runtime/`)) {
          await fulfillSuccess(route, {
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
          return true
        }

        if (pathname.endsWith(`/api/system/objects/${OBJECT_CODE}/fields/`)) {
          const editableFields = buildEditableFields(activeLayoutConfig).map((field) => ({
            ...field,
            field_type: field.fieldType,
            reference_object: field.referenceObject,
            reference_display_field: field.referenceDisplayField,
            reference_secondary_field: field.referenceSecondaryField
          }))
          await fulfillSuccess(route, {
            editable_fields: editableFields,
            reverse_relations: [],
            context: 'form'
          })
          return true
        }

        if (pathname.endsWith(`/api/system/objects/${OBJECT_CODE}/metadata/`)) {
          await fulfillSuccess(route, {
            code: OBJECT_CODE,
            name: OBJECT_CODE,
            permissions: { view: true, add: true, change: true, delete: true }
          })
          return true
        }

        if (pathname.endsWith(`/api/system/objects/${OBJECT_CODE}/${RECORD_ID}/`) && route.request().method() === 'GET') {
          await fulfillSuccess(route, {
            id: RECORD_ID,
            assetName: 'Compact Config Asset',
            owner: 'user-alice'
          })
          return true
        }

        if (pathname.endsWith(`/api/system/objects/${OBJECT_CODE}/${RECORD_ID}/`) && route.request().method() === 'PUT') {
          const body = route.request().postDataJSON() as AnyRecord
          await fulfillSuccess(route, { id: RECORD_ID, ...body })
          return true
        }

        return false
      }
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
    await ensureInlineEditMode(page, { timeout: 20_000 })

    const dialog = await openReferenceAdvancedLookup(page, { fieldLabel: 'Owner' })
    const settings = await openLookupColumnSettings(page, dialog)
    await selectLookupProfile(settings, 'Compact')
    await expect(dialog.locator('.el-table__header-wrapper')).toContainText('email')
    await expect(dialog.locator('.el-table__header-wrapper')).not.toContainText('mobile')
  })
})
