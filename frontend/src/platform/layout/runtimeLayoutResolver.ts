import { dynamicApi } from '@/api/dynamic'
import { businessObjectApi, pageLayoutApi } from '@/api/system'
import { extractLayoutConfig } from '@/adapters/layoutAdapter'
import { normalizeLayoutConfig } from '@/adapters/layoutNormalizer'
import { deriveCompactLayout } from '@/platform/layout/compactLayoutFactory'
import {
  normalizeLayoutType,
  toMetadataContext,
  toRuntimeMode,
  type LayoutTypeValue,
  type MetadataContext,
} from '@/utils/layoutMode'
import type { RuntimeMode } from '@/contracts/runtimeContract'
import { localizeMultilingualObject } from '@/utils/localeText'

type AnyRecord = Record<string, any>
export type RuntimePermissions = {
  view: boolean
  add: boolean
  change: boolean
  delete: boolean
}
type RuntimeLayoutMode = 'edit' | 'readonly' | 'search'
type LayoutFieldOverrides = Record<string, AnyRecord>
type LayoutSectionOverrides = Record<string, AnyRecord>

function normalizePermissions(payload: any): RuntimePermissions | null {
  if (!payload || typeof payload !== 'object') return null
  if (
    typeof payload.view !== 'boolean' ||
    typeof payload.add !== 'boolean' ||
    typeof payload.change !== 'boolean' ||
    typeof payload.delete !== 'boolean'
  ) {
    return null
  }
  return {
    view: payload.view,
    add: payload.add,
    change: payload.change,
    delete: payload.delete
  }
}

export interface RuntimeLayoutResolution {
  source: 'runtime' | 'legacy'
  runtimeMode: RuntimeMode
  metadataContext: MetadataContext
  layoutType: LayoutTypeValue
  viewMode: 'Detail' | 'Compact' | string | null
  layoutConfig: AnyRecord | null
  layoutStatus: string | null
  layoutVersion: string | null
  isDefault: boolean | null
  permissions: RuntimePermissions | null
  fields: AnyRecord[]
  editableFields: AnyRecord[]
  reverseRelations: AnyRecord[]
}

function normalizeFieldsPayload(payload: any): {
  fields: AnyRecord[]
  editableFields: AnyRecord[]
  reverseRelations: AnyRecord[]
} {
  const raw = (payload?.data ?? payload) as AnyRecord
  const nested = (raw?.data ?? raw) as AnyRecord
  const editable = nested?.editableFields || nested?.editable_fields || nested?.fields || []
  const reverse = nested?.reverseRelations || nested?.reverse_relations || []
  const editableFields = Array.isArray(editable)
    ? editable.map((field: AnyRecord) => localizeMultilingualObject(field))
    : []
  const reverseRelations = Array.isArray(reverse)
    ? reverse.map((field: AnyRecord) => localizeMultilingualObject(field))
    : []
  return {
    editableFields,
    reverseRelations,
    fields: [...editableFields, ...reverseRelations]
  }
}

function normalizeMaybeLayoutConfig(layoutPayload: any): AnyRecord | null {
  const raw = extractLayoutConfig(layoutPayload)
  if (!raw || typeof raw !== 'object') return null
  return normalizeLayoutConfig(raw)
}

function cloneConfig<T extends AnyRecord | null>(value: T): T {
  if (!value || typeof value !== 'object') return value
  return JSON.parse(JSON.stringify(value))
}

function toFieldCode(field: any): string {
  if (!field) return ''
  if (typeof field === 'string') return field
  return String(field.fieldCode || field.field_code || field.code || field.field || '').trim()
}

function readFieldList(node: AnyRecord): AnyRecord[] {
  return Array.isArray(node?.fields) ? node.fields : []
}

function applyFieldAndSectionOverrides(
  baseLayout: AnyRecord,
  fieldOverrides: LayoutFieldOverrides,
  sectionOverrides: LayoutSectionOverrides
): AnyRecord {
  const next = cloneConfig(baseLayout) || {}
  const sections = Array.isArray(next.sections) ? next.sections : []

  const patchField = (field: any) => {
    const fieldCode = toFieldCode(field)
    if (!fieldCode || typeof field !== 'object') return
    const overrides = fieldOverrides[fieldCode]
    if (!overrides) return
    Object.assign(field, overrides)
  }

  for (const section of sections) {
    const sectionId = String(section?.id || '').trim()
    if (sectionId && sectionOverrides[sectionId]) {
      Object.assign(section, sectionOverrides[sectionId])
    }

    const sectionType = String(section?.type || 'section')
    if (sectionType === 'tab') {
      for (const tab of Array.isArray(section?.tabs) ? section.tabs : []) {
        for (const field of readFieldList(tab)) patchField(field)
      }
      continue
    }

    if (sectionType === 'collapse') {
      for (const item of Array.isArray(section?.items) ? section.items : []) {
        for (const field of readFieldList(item)) patchField(field)
      }
      continue
    }

    for (const field of readFieldList(section)) patchField(field)
  }

  return normalizeLayoutConfig(next)
}

function applyModeOverridesFromLayout(layout: AnyRecord | null, mode: RuntimeLayoutMode): AnyRecord | null {
  if (!layout || typeof layout !== 'object') return layout
  const modeOverrides = (layout.modeOverrides || layout.mode_overrides || {}) as AnyRecord
  const override = modeOverrides?.[mode] as AnyRecord
  if (!override || typeof override !== 'object') return layout

  const baseConfig = cloneConfig(layout) || {}
  delete (baseConfig as AnyRecord).modeOverrides
  delete (baseConfig as AnyRecord).mode_overrides

  if (Array.isArray(override.sections) && override.sections.length > 0) {
    baseConfig.sections = override.sections
  }
  if (Array.isArray(override.columns) && override.columns.length > 0) {
    baseConfig.columns = override.columns
  }
  if (Array.isArray(override.actions)) {
    baseConfig.actions = override.actions
  }

  const fieldOverrides = (override.fieldOverrides || override.field_overrides || {}) as LayoutFieldOverrides
  const sectionOverrides = (override.sectionOverrides || override.section_overrides || {}) as LayoutSectionOverrides

  return applyFieldAndSectionOverrides(baseConfig, fieldOverrides, sectionOverrides)
}

function normalizeRuntimeContext(value: any, fallback: MetadataContext): MetadataContext {
  const raw = String(value || '').toLowerCase()
  if (raw === 'form' || raw === 'detail' || raw === 'list') {
    return raw
  }
  return fallback
}

/**
 * Resolve layout + fields through runtime first, with legacy fallback.
 * This keeps detail/form/list pages on a single data contract.
 */
export async function resolveRuntimeLayout(
  objectCode: string,
  modeInput: string,
  options: { includeRelations?: boolean; preferredViewMode?: 'Detail' | 'Compact' } = {}
): Promise<RuntimeLayoutResolution> {
  const runtimeMode = toRuntimeMode(modeInput)
  const inputContext = toMetadataContext(modeInput)
  const layoutType = normalizeLayoutType(modeInput)
  const includeRelations = options.includeRelations !== false

  try {
    const runtime = await dynamicApi.getRuntime(objectCode, runtimeMode, {
      include_relations: includeRelations,
      ...(options.preferredViewMode ? { view_mode: options.preferredViewMode } : {}),
    })
    const metadataContext = normalizeRuntimeContext(runtime?.context, inputContext)
    const layoutPayload = (runtime?.layout || {}) as AnyRecord
    const normalizedFields = normalizeFieldsPayload(runtime?.fields || {})
    let layoutConfig = normalizeMaybeLayoutConfig(layoutPayload)
    if (runtimeMode === 'edit' || runtimeMode === 'search') {
      layoutConfig = applyModeOverridesFromLayout(layoutConfig, runtimeMode)
    }
    const permissions = normalizePermissions(runtime?.permissions)
    // Apply compact derivation if preferred and backend returned a Detail layout
    const resolvedViewMode = (layoutPayload?.view_mode || layoutPayload?.viewMode || 'Detail') as string
    if (options.preferredViewMode === 'Compact' && resolvedViewMode !== 'Compact' && layoutConfig) {
      layoutConfig = deriveCompactLayout(layoutConfig, normalizedFields.editableFields)
    }
    return {
      source: 'runtime',
      runtimeMode,
      metadataContext,
      layoutType,
      viewMode: options.preferredViewMode === 'Compact' ? 'Compact' : resolvedViewMode,
      layoutConfig,
      layoutStatus: layoutPayload?.status ?? null,
      layoutVersion: layoutPayload?.version ?? null,
      isDefault: (runtime?.isDefault ?? runtime?.is_default ?? layoutPayload?.isDefault ?? layoutPayload?.is_default ?? null) as boolean | null,
      permissions,
      ...normalizedFields,
    }
  } catch (runtimeError) {
    const fallbackContext = runtimeMode === 'readonly' ? 'form' : inputContext
    const fallbackLayoutType: LayoutTypeValue = runtimeMode === 'readonly' ? 'form' : layoutType
    const fieldsResponse = await businessObjectApi.getFieldsWithContext(
      objectCode,
      fallbackContext,
      { includeRelations }
    )
    const normalizedFields = normalizeFieldsPayload(fieldsResponse)
    const layoutResponse = await pageLayoutApi.getDefault(objectCode, fallbackLayoutType)
    const layoutPayload = ((layoutResponse as AnyRecord)?.data ?? layoutResponse ?? {}) as AnyRecord
    let layoutConfig = normalizeMaybeLayoutConfig(layoutResponse)
    if (runtimeMode === 'edit' || runtimeMode === 'search') {
      layoutConfig = applyModeOverridesFromLayout(layoutConfig, runtimeMode)
    }

    return {
      source: 'legacy',
      runtimeMode,
      metadataContext: fallbackContext,
      layoutType: fallbackLayoutType,
      viewMode: (layoutPayload?.view_mode || layoutPayload?.viewMode || 'Detail') as string,
      layoutConfig,
      layoutStatus: (layoutPayload?.status ?? null) as string | null,
      layoutVersion: (layoutPayload?.version ?? null) as string | null,
      isDefault: (layoutPayload?.isDefault ?? layoutPayload?.is_default ?? true) as boolean | null,
      permissions: null,
      ...normalizedFields,
    }
  }
}
