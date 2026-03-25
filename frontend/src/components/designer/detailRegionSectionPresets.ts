import type { LayoutSection } from '@/components/designer/designerTypes'
import type { RuntimeAggregateDetailRegion } from '@/types/runtime'

export type DetailRegionSectionPresetCode =
  | 'editableDetail'
  | 'reviewTable'
  | 'sidebarSummary'

export interface DetailRegionSectionPresetDefinition {
  code: DetailRegionSectionPresetCode
  labelKey: string
  fallbackLabel: string
  descriptionKey: string
  fallbackDescription: string
}

const PRESET_DEFINITIONS: DetailRegionSectionPresetDefinition[] = [
  {
    code: 'editableDetail',
    labelKey: 'system.pageLayout.designer.detailRegionConfigurator.sectionPresetOptions.editableDetail',
    fallbackLabel: 'Editable Detail',
    descriptionKey: 'system.pageLayout.designer.detailRegionConfigurator.sectionPresetDescriptions.editableDetail',
    fallbackDescription: 'Main-area editable child table with metadata-backed detail columns and toolbar actions.'
  },
  {
    code: 'reviewTable',
    labelKey: 'system.pageLayout.designer.detailRegionConfigurator.sectionPresetOptions.reviewTable',
    fallbackLabel: 'Review Table',
    descriptionKey: 'system.pageLayout.designer.detailRegionConfigurator.sectionPresetDescriptions.reviewTable',
    fallbackDescription: 'Readonly review table that prefers lookup columns for quick checking.'
  },
  {
    code: 'sidebarSummary',
    labelKey: 'system.pageLayout.designer.detailRegionConfigurator.sectionPresetOptions.sidebarSummary',
    fallbackLabel: 'Sidebar Summary',
    descriptionKey: 'system.pageLayout.designer.detailRegionConfigurator.sectionPresetDescriptions.sidebarSummary',
    fallbackDescription: 'Compact sidebar summary with a focused subset of child columns.'
  }
]

const cloneValue = <T>(value: T): T => {
  if (value === undefined) return value
  return JSON.parse(JSON.stringify(value))
}

const cloneArray = (value: unknown): Array<Record<string, unknown>> | undefined => {
  return Array.isArray(value)
    ? cloneValue(value.filter((item): item is Record<string, unknown> => !!item && typeof item === 'object'))
    : undefined
}

const buildCompactColumns = (
  columns: Array<Record<string, unknown>> | undefined
): Array<Record<string, unknown>> | undefined => {
  if (!Array.isArray(columns) || columns.length === 0) return undefined
  return cloneValue(columns.slice(0, Math.min(columns.length, 3)))
}

const normalizeColumns = (value: unknown): string => {
  if (!Array.isArray(value)) return ''

  return JSON.stringify(
    value.map((item) => {
      const record = (item || {}) as Record<string, unknown>
      return {
        code: String(record.code || record.fieldCode || record.field_code || record.key || '').trim(),
        label: String(record.label || record.name || '').trim(),
        fieldType: String(record.fieldType || record.field_type || '').trim(),
        width: Number.isFinite(Number(record.width)) ? Number(record.width) : undefined,
        minWidth: Number.isFinite(Number(record.minWidth ?? record.min_width))
          ? Number(record.minWidth ?? record.min_width)
          : undefined,
        align: String(record.align || '').trim(),
        fixed: String(record.fixed || '').trim(),
        formatter: String(record.formatter || record.displayFormatter || '').trim(),
        emptyText: String(record.emptyText ?? record.empty_text ?? '').trim(),
        tooltipTemplate: String(record.tooltipTemplate ?? record.tooltip_template ?? '').trim(),
        ellipsis:
          record.ellipsis === true ||
          record.showOverflowTooltip === true ||
          record.show_overflow_tooltip === true
      }
    })
  )
}

const normalizeObject = (value: unknown): string => {
  if (!value || typeof value !== 'object' || Array.isArray(value)) return ''
  return JSON.stringify(value)
}

const normalizePresetComparableState = (value: Partial<LayoutSection>) => ({
  position: String(value.position || '').trim(),
  collapsible: Boolean(value.collapsible),
  collapsed: Boolean(value.collapsed),
  detailEditMode: String(value.detailEditMode || value.detail_edit_mode || '').trim(),
  toolbarConfig: normalizeObject(value.toolbarConfig || value.toolbar_config),
  summaryRules: JSON.stringify(value.summaryRules || value.summary_rules || []),
  validationRules: JSON.stringify(value.validationRules || value.validation_rules || []),
  relatedFields: normalizeColumns(value.relatedFields || value.related_fields),
  lookupColumns: normalizeColumns(value.lookupColumns || value.lookup_columns)
})

const buildSectionColumns = (
  region: RuntimeAggregateDetailRegion
): {
  detailColumns: Array<Record<string, unknown>> | undefined
  reviewColumns: Array<Record<string, unknown>> | undefined
  summaryColumns: Array<Record<string, unknown>> | undefined
} => {
  const detailColumns = cloneArray(region.relatedFields) || cloneArray(region.lookupColumns)
  const reviewColumns = cloneArray(region.lookupColumns) || cloneArray(region.relatedFields)
  const summaryColumns = buildCompactColumns(reviewColumns || detailColumns) || reviewColumns || detailColumns

  return {
    detailColumns,
    reviewColumns,
    summaryColumns
  }
}

export const getDetailRegionSectionPresetDefinitions = (): DetailRegionSectionPresetDefinition[] => {
  return PRESET_DEFINITIONS.slice()
}

export const getDetailRegionSectionPresetDefinition = (
  presetCode: unknown
): DetailRegionSectionPresetDefinition | null => {
  const normalized = String(presetCode || '').trim()
  return PRESET_DEFINITIONS.find((preset) => preset.code === normalized) || null
}

export const buildDetailRegionSectionPresetPatch = (
  region: RuntimeAggregateDetailRegion,
  presetCode: unknown
): Partial<LayoutSection> | null => {
  const normalized = String(presetCode || '').trim() as DetailRegionSectionPresetCode
  if (!getDetailRegionSectionPresetDefinition(normalized)) return null

  const { detailColumns, reviewColumns, summaryColumns } = buildSectionColumns(region)
  const detailEditMode = String(region.detailEditMode || 'inline_table').trim() || 'inline_table'
  const toolbarConfig = cloneValue(region.toolbarConfig || {})
  const summaryRules = cloneArray(region.summaryRules)
  const validationRules = cloneArray(region.validationRules)

  if (normalized === 'editableDetail') {
    return {
      position: 'main',
      collapsible: true,
      collapsed: false,
      detailEditMode,
      detail_edit_mode: detailEditMode,
      toolbarConfig,
      toolbar_config: cloneValue(toolbarConfig),
      summaryRules,
      summary_rules: cloneValue(summaryRules),
      validationRules,
      validation_rules: cloneValue(validationRules),
      relatedFields: detailColumns,
      related_fields: cloneValue(detailColumns),
      lookupColumns: reviewColumns,
      lookup_columns: cloneValue(reviewColumns)
    }
  }

  if (normalized === 'reviewTable') {
    return {
      position: 'main',
      collapsible: true,
      collapsed: false,
      detailEditMode: 'readonly_table',
      detail_edit_mode: 'readonly_table',
      toolbarConfig: {},
      toolbar_config: {},
      summaryRules,
      summary_rules: cloneValue(summaryRules),
      validationRules,
      validation_rules: cloneValue(validationRules),
      relatedFields: reviewColumns,
      related_fields: cloneValue(reviewColumns),
      lookupColumns: reviewColumns,
      lookup_columns: cloneValue(reviewColumns)
    }
  }

  return {
    position: 'sidebar',
    collapsible: true,
    collapsed: false,
    detailEditMode: 'readonly_table',
    detail_edit_mode: 'readonly_table',
    toolbarConfig: {},
    toolbar_config: {},
    summaryRules,
    summary_rules: cloneValue(summaryRules),
    validationRules,
    validation_rules: cloneValue(validationRules),
    relatedFields: summaryColumns,
    related_fields: cloneValue(summaryColumns),
    lookupColumns: summaryColumns,
    lookup_columns: cloneValue(summaryColumns)
  }
}

export const resolveDetailRegionSectionPreset = (
  section: Partial<LayoutSection> | null | undefined,
  region: RuntimeAggregateDetailRegion | null | undefined
): DetailRegionSectionPresetCode | '' => {
  if (!section || !region) return ''

  const currentState = normalizePresetComparableState(section)

  for (const preset of PRESET_DEFINITIONS) {
    const patch = buildDetailRegionSectionPresetPatch(region, preset.code)
    if (!patch) continue
    const expectedState = normalizePresetComparableState(patch)
    const matches = Object.entries(expectedState).every(([key, value]) => {
      return currentState[key as keyof typeof currentState] === value
    })
    if (matches) return preset.code
  }

  return ''
}
