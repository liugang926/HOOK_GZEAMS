export type DetailRegionColumnPresetCode =
  | 'amount'
  | 'amountSummary'
  | 'date'
  | 'datetime'
  | 'auditDatetime'
  | 'status'
  | 'statusCompact'

export interface DetailRegionColumnPresetDefinition {
  code: DetailRegionColumnPresetCode
  labelKey: string
  fallbackLabel: string
  descriptionKey: string
  fallbackDescription: string
  appliesTo?: string[]
}

interface DetailRegionColumnPresetConfig {
  minWidth?: number
  align?: 'left' | 'center' | 'right'
  fixed?: 'left' | 'right'
  ellipsis?: boolean
  formatter?: 'uppercase' | 'lowercase' | 'number' | 'date' | 'datetime' | 'boolean'
  emptyText?: string
  tooltipTemplate?: string
}

type DetailRegionPresetTarget = Record<string, unknown> & {
  minWidth?: number
  min_width?: number
  align?: 'left' | 'center' | 'right'
  fixed?: 'left' | 'right'
  ellipsis?: boolean
  showOverflowTooltip?: boolean
  show_overflow_tooltip?: boolean
  formatter?: DetailRegionColumnPresetConfig['formatter']
  displayFormatter?: DetailRegionColumnPresetConfig['formatter']
  emptyText?: string
  empty_text?: string
  tooltipTemplate?: string
  tooltip_template?: string
}

const PRESET_DEFINITIONS: DetailRegionColumnPresetDefinition[] = [
  {
    code: 'amount',
    labelKey: 'system.pageLayout.designer.detailRegionConfigurator.presetOptions.amount',
    fallbackLabel: 'Amount',
    descriptionKey: 'system.pageLayout.designer.detailRegionConfigurator.presetDescriptions.amount',
    fallbackDescription: 'Right-aligned amount column for row-level numeric values.',
    appliesTo: ['number', 'currency', 'percent', 'integer', 'float', 'decimal']
  },
  {
    code: 'amountSummary',
    labelKey: 'system.pageLayout.designer.detailRegionConfigurator.presetOptions.amountSummary',
    fallbackLabel: 'Amount Summary',
    descriptionKey: 'system.pageLayout.designer.detailRegionConfigurator.presetDescriptions.amountSummary',
    fallbackDescription: 'Right-aligned summary amount column for totals or rollups.',
    appliesTo: ['number', 'currency', 'percent', 'integer', 'float', 'decimal']
  },
  {
    code: 'date',
    labelKey: 'system.pageLayout.designer.detailRegionConfigurator.presetOptions.date',
    fallbackLabel: 'Date',
    descriptionKey: 'system.pageLayout.designer.detailRegionConfigurator.presetDescriptions.date',
    fallbackDescription: 'Standard date column for planned or effective dates.',
    appliesTo: ['date']
  },
  {
    code: 'datetime',
    labelKey: 'system.pageLayout.designer.detailRegionConfigurator.presetOptions.datetime',
    fallbackLabel: 'DateTime',
    descriptionKey: 'system.pageLayout.designer.detailRegionConfigurator.presetDescriptions.datetime',
    fallbackDescription: 'Timestamp column for detailed event records.',
    appliesTo: ['datetime', 'timestamp']
  },
  {
    code: 'auditDatetime',
    labelKey: 'system.pageLayout.designer.detailRegionConfigurator.presetOptions.auditDatetime',
    fallbackLabel: 'Audit DateTime',
    descriptionKey: 'system.pageLayout.designer.detailRegionConfigurator.presetDescriptions.auditDatetime',
    fallbackDescription: 'Pinned audit timestamp column for update history and traceability.',
    appliesTo: ['datetime', 'timestamp']
  },
  {
    code: 'status',
    labelKey: 'system.pageLayout.designer.detailRegionConfigurator.presetOptions.status',
    fallbackLabel: 'Status',
    descriptionKey: 'system.pageLayout.designer.detailRegionConfigurator.presetDescriptions.status',
    fallbackDescription: 'Centered status column with tooltip support for longer labels.',
    appliesTo: ['select', 'multi_select', 'radio', 'checkbox', 'boolean', 'text']
  },
  {
    code: 'statusCompact',
    labelKey: 'system.pageLayout.designer.detailRegionConfigurator.presetOptions.statusCompact',
    fallbackLabel: 'Compact Status',
    descriptionKey: 'system.pageLayout.designer.detailRegionConfigurator.presetDescriptions.statusCompact',
    fallbackDescription: 'Compact centered status column for dense operational tables.',
    appliesTo: ['select', 'multi_select', 'radio', 'checkbox', 'boolean', 'text']
  }
]

const PRESET_CONFIGS: Record<DetailRegionColumnPresetCode, DetailRegionColumnPresetConfig> = {
  amount: {
    minWidth: 140,
    align: 'right',
    formatter: 'number',
    emptyText: '0'
  },
  amountSummary: {
    minWidth: 160,
    align: 'right',
    fixed: 'right',
    formatter: 'number',
    emptyText: '0'
  },
  date: {
    minWidth: 140,
    formatter: 'date'
  },
  datetime: {
    minWidth: 180,
    formatter: 'datetime'
  },
  auditDatetime: {
    minWidth: 180,
    fixed: 'right',
    formatter: 'datetime',
    tooltipTemplate: '{value}'
  },
  status: {
    minWidth: 120,
    align: 'center',
    ellipsis: true,
    tooltipTemplate: '{value}'
  },
  statusCompact: {
    minWidth: 96,
    align: 'center',
    ellipsis: true
  }
}

const normalizeFieldType = (value: unknown): string => {
  return String(value || '').trim().toLowerCase().replace(/-/g, '_')
}

const normalizeMinWidth = (value: unknown): number | undefined => {
  const numeric = Number(value)
  return Number.isFinite(numeric) && numeric > 0 ? Math.round(numeric) : undefined
}

const normalizeAlign = (value: unknown): 'left' | 'center' | 'right' | undefined => {
  const normalized = String(value || '').trim().toLowerCase()
  return ['left', 'center', 'right'].includes(normalized)
    ? (normalized as 'left' | 'center' | 'right')
    : undefined
}

const normalizeFixed = (value: unknown): 'left' | 'right' | undefined => {
  const normalized = String(value || '').trim().toLowerCase()
  return ['left', 'right'].includes(normalized)
    ? (normalized as 'left' | 'right')
    : undefined
}

const normalizeFormatter = (
  value: unknown
): DetailRegionColumnPresetConfig['formatter'] | undefined => {
  const normalized = String(value || '').trim().toLowerCase()
  return ['uppercase', 'lowercase', 'number', 'date', 'datetime', 'boolean'].includes(normalized)
    ? (normalized as DetailRegionColumnPresetConfig['formatter'])
    : undefined
}

const normalizeString = (value: unknown): string | undefined => {
  const normalized = String(value ?? '').trim()
  return normalized || undefined
}

const normalizeEllipsis = (value: Record<string, unknown>): boolean | undefined => {
  return (
    value.ellipsis === true ||
    value.showOverflowTooltip === true ||
    value.show_overflow_tooltip === true
  )
    ? true
    : undefined
}

const toPresetState = (value: Record<string, unknown>): DetailRegionColumnPresetConfig => ({
  minWidth: normalizeMinWidth(value.minWidth ?? value.min_width),
  align: normalizeAlign(value.align),
  fixed: normalizeFixed(value.fixed),
  ellipsis: normalizeEllipsis(value),
  formatter: normalizeFormatter(value.formatter ?? value.displayFormatter),
  emptyText: normalizeString(value.emptyText ?? value.empty_text),
  tooltipTemplate: normalizeString(value.tooltipTemplate ?? value.tooltip_template)
})

const PRESET_STATE_KEYS: Array<keyof DetailRegionColumnPresetConfig> = [
  'minWidth',
  'align',
  'fixed',
  'ellipsis',
  'formatter',
  'emptyText',
  'tooltipTemplate'
]

const clearPresetManagedKeys = <T extends DetailRegionPresetTarget>(value: T): T => {
  const next = { ...value }
  delete next.minWidth
  delete next.min_width
  delete next.align
  delete next.fixed
  delete next.ellipsis
  delete next.showOverflowTooltip
  delete next.show_overflow_tooltip
  delete next.formatter
  delete next.displayFormatter
  delete next.emptyText
  delete next.empty_text
  delete next.tooltipTemplate
  delete next.tooltip_template
  return next
}

const isPresetCode = (value: unknown): value is DetailRegionColumnPresetCode => {
  return PRESET_DEFINITIONS.some((preset) => preset.code === value)
}

export const getDetailRegionColumnPresetDefinition = (
  presetCode: unknown
): DetailRegionColumnPresetDefinition | null => {
  if (!isPresetCode(presetCode)) return null
  return PRESET_DEFINITIONS.find((preset) => preset.code === presetCode) || null
}

export const getDetailRegionColumnPresetDefinitions = (
  fieldType?: unknown
): DetailRegionColumnPresetDefinition[] => {
  const normalizedFieldType = normalizeFieldType(fieldType)
  if (!normalizedFieldType) return PRESET_DEFINITIONS.slice()

  const matched = PRESET_DEFINITIONS.filter((preset) => {
    return Array.isArray(preset.appliesTo) && preset.appliesTo.includes(normalizedFieldType)
  })

  return matched.length > 0 ? matched : PRESET_DEFINITIONS.slice()
}

export const getDetailRegionColumnPresetConfig = (
  presetCode: unknown
): DetailRegionColumnPresetConfig | null => {
  if (!isPresetCode(presetCode)) return null
  return { ...PRESET_CONFIGS[presetCode] }
}

export const resolveDetailRegionColumnPreset = (value: unknown): DetailRegionColumnPresetCode | '' => {
  if (!value || typeof value !== 'object') return ''
  const state = toPresetState(value as Record<string, unknown>)

  for (const preset of PRESET_DEFINITIONS) {
    const presetState = PRESET_CONFIGS[preset.code]
    const matches = PRESET_STATE_KEYS.every((key) => {
      const expected = presetState[key]
      const actual = state[key]
      if (expected === undefined) return actual === undefined
      return actual === expected
    })
    if (matches) return preset.code
  }

  return ''
}

export const applyDetailRegionColumnPreset = <T extends Record<string, any>>(
  value: T,
  presetCode: unknown
): T => {
  const next = clearPresetManagedKeys(value as T & DetailRegionPresetTarget) as T & DetailRegionPresetTarget
  if (!isPresetCode(presetCode)) return next

  const preset = PRESET_CONFIGS[presetCode]
  if (typeof preset.minWidth === 'number' && preset.minWidth > 0) {
    next.minWidth = preset.minWidth
  }
  if (preset.align) {
    next.align = preset.align
  }
  if (preset.fixed) {
    next.fixed = preset.fixed
  }
  if (preset.ellipsis) {
    next.ellipsis = true
    next.showOverflowTooltip = true
    next.show_overflow_tooltip = true
  }
  if (preset.formatter) {
    next.formatter = preset.formatter
  }
  if (preset.emptyText) {
    next.emptyText = preset.emptyText
  }
  if (preset.tooltipTemplate) {
    next.tooltipTemplate = preset.tooltipTemplate
  }

  return next
}
