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
import { localizeMultilingualObject, localizeMultilingualTree } from '@/utils/localeText'
import type { RuntimeAggregate, RuntimeWorkbench } from '@/types/runtime'

type AnyRecord = Record<string, unknown>
export type RuntimePermissions = {
  view: boolean
  add: boolean
  change: boolean
  delete: boolean
}
type RuntimeLayoutMode = 'edit' | 'readonly' | 'search'
type LayoutFieldOverrides = Record<string, AnyRecord>
type LayoutSectionOverrides = Record<string, AnyRecord>

function toRecord(value: unknown): AnyRecord | null {
  if (!value || typeof value !== 'object' || Array.isArray(value)) return null
  return value as AnyRecord
}

function readString(value: unknown): string | null {
  if (typeof value !== 'string') return null
  const normalized = value.trim()
  return normalized || null
}

function readBoolean(value: unknown): boolean | null {
  return typeof value === 'boolean' ? value : null
}

function normalizePermissions(payload: unknown): RuntimePermissions | null {
  if (!payload || typeof payload !== 'object') return null
  const candidate = payload as Record<string, unknown>
  if (
    typeof candidate.view !== 'boolean' ||
    typeof candidate.add !== 'boolean' ||
    typeof candidate.change !== 'boolean' ||
    typeof candidate.delete !== 'boolean'
  ) {
    return null
  }
  return {
    view: candidate.view,
    add: candidate.add,
    change: candidate.change,
    delete: candidate.delete
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
  aggregate: RuntimeAggregate | null
  workbench: RuntimeWorkbench
}

const EMPTY_RUNTIME_WORKBENCH = Object.freeze<RuntimeWorkbench>({
  workspaceMode: 'standard',
  primaryEntryRoute: '',
  legacyAliases: [],
  toolbar: {
    primaryActions: [],
    secondaryActions: [],
  },
  detailPanels: [],
  asyncIndicators: [],
  summaryCards: [],
  queuePanels: [],
  exceptionPanels: [],
  closurePanel: null,
  slaIndicators: [],
  recommendedActions: [],
})

function normalizeFieldsPayload(payload: unknown): {
  fields: AnyRecord[]
  editableFields: AnyRecord[]
  reverseRelations: AnyRecord[]
} {
  const payloadRecord = toRecord(payload)
  const raw = toRecord(payloadRecord?.data) || payloadRecord || {}
  const nested = toRecord(raw.data) || raw
  const editable = nested.editableFields || nested.editable_fields || nested.fields || []
  const reverse = nested.reverseRelations || nested.reverse_relations || []
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

function normalizeMaybeLayoutConfig(layoutPayload: unknown): AnyRecord | null {
  const raw = extractLayoutConfig(toRecord(layoutPayload) || undefined)
  if (!raw || typeof raw !== 'object') return null
  return normalizeLayoutConfig(raw as AnyRecord)
}

function normalizeAggregatePayload(payload: unknown): RuntimeAggregate | null {
  if (!payload || typeof payload !== 'object') return null
  return localizeMultilingualTree(payload) as RuntimeAggregate
}

function normalizeStringList(value: unknown): string[] {
  if (!Array.isArray(value)) return []
  return value
    .map((item) => String(item || '').trim())
    .filter(Boolean)
}

function normalizeWorkbench(payload: unknown, objectCode: string): RuntimeWorkbench {
  if (!payload || typeof payload !== 'object') {
    return {
      ...EMPTY_RUNTIME_WORKBENCH,
      primaryEntryRoute: objectCode ? `/objects/${objectCode}` : '',
      toolbar: {
        primaryActions: [],
        secondaryActions: [],
      },
      detailPanels: [],
      asyncIndicators: [],
      summaryCards: [],
      queuePanels: [],
      exceptionPanels: [],
      closurePanel: null,
      slaIndicators: [],
      recommendedActions: [],
      legacyAliases: [],
    }
  }

  const candidate = payload as AnyRecord
  const toolbar = (candidate.toolbar || {}) as AnyRecord
  const primaryActions = Array.isArray(toolbar.primaryActions || toolbar.primary_actions)
    ? [...((toolbar.primaryActions || toolbar.primary_actions) as Array<Record<string, unknown>>)]
    : []
  const secondaryActions = Array.isArray(toolbar.secondaryActions || toolbar.secondary_actions)
    ? [...((toolbar.secondaryActions || toolbar.secondary_actions) as Array<Record<string, unknown>>)]
    : []
  const detailPanels = Array.isArray(candidate.detailPanels || candidate.detail_panels)
    ? [...((candidate.detailPanels || candidate.detail_panels) as Array<Record<string, unknown>>)]
    : []
  const asyncIndicators = Array.isArray(candidate.asyncIndicators || candidate.async_indicators)
    ? [...((candidate.asyncIndicators || candidate.async_indicators) as Array<Record<string, unknown>>)]
    : []
  const summaryCards = Array.isArray(candidate.summaryCards || candidate.summary_cards)
    ? [...((candidate.summaryCards || candidate.summary_cards) as Array<Record<string, unknown>>)]
    : []
  const queuePanels = Array.isArray(candidate.queuePanels || candidate.queue_panels)
    ? [...((candidate.queuePanels || candidate.queue_panels) as Array<Record<string, unknown>>)]
    : []
  const exceptionPanels = Array.isArray(candidate.exceptionPanels || candidate.exception_panels)
    ? [...((candidate.exceptionPanels || candidate.exception_panels) as Array<Record<string, unknown>>)]
    : []
  const rawClosurePanel = toRecord(candidate.closurePanel || candidate.closure_panel)
  const closurePanel = rawClosurePanel && Object.keys(rawClosurePanel).length > 0 ? rawClosurePanel : null
  const slaIndicators = Array.isArray(candidate.slaIndicators || candidate.sla_indicators)
    ? [...((candidate.slaIndicators || candidate.sla_indicators) as Array<Record<string, unknown>>)]
    : []
  const recommendedActions = Array.isArray(candidate.recommendedActions || candidate.recommended_actions)
    ? [...((candidate.recommendedActions || candidate.recommended_actions) as Array<Record<string, unknown>>)]
    : []

  return {
    workspaceMode: String(candidate.workspaceMode || candidate.workspace_mode || 'standard'),
    primaryEntryRoute: String(
      candidate.primaryEntryRoute ||
      candidate.primary_entry_route ||
      (objectCode ? `/objects/${objectCode}` : '')
    ),
    legacyAliases: normalizeStringList(candidate.legacyAliases || candidate.legacy_aliases),
    toolbar: {
      primaryActions,
      secondaryActions,
    },
    detailPanels: detailPanels as RuntimeWorkbench['detailPanels'],
    asyncIndicators: asyncIndicators as RuntimeWorkbench['asyncIndicators'],
    summaryCards: summaryCards as RuntimeWorkbench['summaryCards'],
    queuePanels: queuePanels as RuntimeWorkbench['queuePanels'],
    exceptionPanels: exceptionPanels as RuntimeWorkbench['exceptionPanels'],
    closurePanel: closurePanel as RuntimeWorkbench['closurePanel'],
    slaIndicators: slaIndicators as RuntimeWorkbench['slaIndicators'],
    recommendedActions: recommendedActions as RuntimeWorkbench['recommendedActions'],
  }
}

function cloneConfig<T extends AnyRecord | null>(value: T): T {
  if (!value || typeof value !== 'object') return value
  return JSON.parse(JSON.stringify(value)) as T
}

function toFieldCode(field: unknown): string {
  if (!field) return ''
  if (typeof field === 'string') return field
  if (typeof field !== 'object') return ''
  const candidate = field as AnyRecord
  return String(candidate.fieldCode || candidate.field_code || candidate.code || candidate.field || '').trim()
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

  const patchField = (field: unknown) => {
    const fieldCode = toFieldCode(field)
    if (!fieldCode || !field || typeof field !== 'object') return
    const overrides = fieldOverrides[fieldCode]
    if (!overrides) return
    Object.assign(field as AnyRecord, overrides)
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

function normalizeRuntimeContext(value: unknown, fallback: MetadataContext): MetadataContext {
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
    const runtimePayload = toRecord(runtime) || {}
    const metadataContext = normalizeRuntimeContext(runtimePayload.context, inputContext)
    const layoutPayload = toRecord(runtimePayload.layout) || {}
    const layoutConfigPayload =
      toRecord(layoutPayload.layoutConfig) ||
      toRecord(layoutPayload.layout_config)
    const normalizedFields = normalizeFieldsPayload(runtimePayload.fields || {})
    let layoutConfig = normalizeMaybeLayoutConfig(layoutPayload)
    if (runtimeMode === 'edit' || runtimeMode === 'search') {
      layoutConfig = applyModeOverridesFromLayout(layoutConfig, runtimeMode)
    }
    const permissions = normalizePermissions(runtimePayload.permissions)
    const aggregate = normalizeAggregatePayload(runtimePayload.aggregate)
    const workbench = normalizeWorkbench(
      runtimePayload.workbench ||
      layoutPayload.workbench ||
      layoutConfigPayload?.workbench,
      objectCode
    )
    // Apply compact derivation if preferred and backend returned a Detail layout
    const resolvedViewMode = readString(layoutPayload.view_mode) || readString(layoutPayload.viewMode) || 'Detail'
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
      layoutStatus: readString(layoutPayload.status),
      layoutVersion: readString(layoutPayload.version),
      isDefault:
        readBoolean(runtimePayload.isDefault) ??
        readBoolean(runtimePayload.is_default) ??
        readBoolean(layoutPayload.isDefault) ??
        readBoolean(layoutPayload.is_default),
      permissions,
      aggregate,
      workbench,
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
    const layoutResponseRecord = toRecord(layoutResponse)
    const layoutPayload = toRecord(layoutResponseRecord?.data) || layoutResponseRecord || {}
    const layoutConfigPayload =
      toRecord(layoutPayload.layoutConfig) ||
      toRecord(layoutPayload.layout_config)
    let layoutConfig = normalizeMaybeLayoutConfig(layoutResponse)
    if (runtimeMode === 'edit' || runtimeMode === 'search') {
      layoutConfig = applyModeOverridesFromLayout(layoutConfig, runtimeMode)
    }
    const workbench = normalizeWorkbench(
      layoutPayload.workbench || layoutConfigPayload?.workbench,
      objectCode
    )

    return {
      source: 'legacy',
      runtimeMode,
      metadataContext: fallbackContext,
      layoutType: fallbackLayoutType,
      viewMode: readString(layoutPayload.view_mode) || readString(layoutPayload.viewMode) || 'Detail',
      layoutConfig,
      layoutStatus: readString(layoutPayload.status),
      layoutVersion: readString(layoutPayload.version),
      isDefault: readBoolean(layoutPayload.isDefault) ?? readBoolean(layoutPayload.is_default) ?? true,
      permissions: null,
      aggregate: null,
      workbench,
      ...normalizedFields,
    }
  }
}
