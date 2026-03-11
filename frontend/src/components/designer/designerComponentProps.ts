export const DESIGNER_COMPONENT_PROP_KEYS = new Set<string>([
  'lookupCompactKeys',
  'lookupColumns',
  'relatedFields',
  'relatedObjectCode',
  'displayMode',
  'pageSize',
  'paginationPageSize',
  'showShortcutHelp',
  'defaultShortcutHelpPinned'
])

export type LookupColumnConfig = {
  key: string
  label?: string
  minWidth?: number
  width?: number
}

export const normalizeLookupCompactKeys = (value: unknown): string[] => {
  if (!Array.isArray(value)) return []
  return value
    .map((item) => String(item || '').trim())
    .filter(Boolean)
}

export const toBooleanConfig = (value: unknown, fallback: boolean): boolean => {
  if (typeof value === 'boolean') return value
  if (typeof value === 'number') return value !== 0
  if (typeof value === 'string') {
    const normalized = value.trim().toLowerCase()
    if (['true', '1', 'yes', 'on'].includes(normalized)) return true
    if (['false', '0', 'no', 'off'].includes(normalized)) return false
  }
  return fallback
}

export const normalizeLookupColumns = (value: unknown): LookupColumnConfig[] => {
  if (!Array.isArray(value)) return []
  const out: LookupColumnConfig[] = []
  const seen = new Set<string>()
  for (const item of value) {
    const key = typeof item === 'string'
      ? String(item || '').trim()
      : String((item as Record<string, any>)?.key || '').trim()
    if (!key || seen.has(key)) continue
    seen.add(key)
    const next: LookupColumnConfig = { key }
    if (typeof item === 'object' && item) {
      const raw = item as Record<string, any>
      const label = String(raw.label || '').trim()
      if (label) next.label = label
      const minWidth = Number(raw.minWidth ?? raw.min_width)
      const width = Number(raw.width)
      if (Number.isFinite(minWidth) && minWidth > 0) next.minWidth = minWidth
      if (Number.isFinite(width) && width > 0) next.width = width
    }
    out.push(next)
  }
  return out
}

export type RelatedFieldConfig = {
  code?: string
  fieldCode?: string
  name?: string
  label?: string
  width?: number
  fieldType?: string
  field_type?: string
  componentProps?: Record<string, any>
  component_props?: Record<string, any>
}

export const normalizeRelatedFields = (value: unknown): RelatedFieldConfig[] => {
  if (!Array.isArray(value)) return []
  return value
    .map((item) => {
      if (!item || typeof item !== 'object') return null
      const raw = item as Record<string, any>
      const code = String(raw.code || raw.fieldCode || '').trim()
      const label = String(raw.label || raw.name || '').trim()
      const fieldType = String(raw.fieldType || raw.field_type || raw.type || '').trim()
      const width = Number(raw.width)
      const componentProps = {
        ...(raw.component_props || {}),
        ...(raw.componentProps || {})
      }

      const next: RelatedFieldConfig = {}
      if (code) {
        next.code = code
        next.fieldCode = code
      }
      if (label) {
        next.label = label
        next.name = label
      }
      if (fieldType) {
        next.fieldType = fieldType
        next.field_type = fieldType
      }
      if (Number.isFinite(width) && width > 0) next.width = width
      if (Object.keys(componentProps).length > 0) {
        next.componentProps = componentProps
        next.component_props = componentProps
      }

      return (next.code || next.fieldCode || next.label || next.name) ? next : null
    })
    .filter((item): item is RelatedFieldConfig => !!item)
}

const resolveComponentProps = (field: Record<string, any>): Record<string, any> => {
  return {
    ...((field.componentProps || {}) as Record<string, any>),
    ...((field as any).component_props || {})
  }
}

export const setDesignerComponentProp = (field: Record<string, any>, key: string, value: unknown): boolean => {
  if (!DESIGNER_COMPONENT_PROP_KEYS.has(key)) return false
  const componentProps = resolveComponentProps(field)

  if (key === 'lookupCompactKeys') {
    componentProps.lookupCompactKeys = normalizeLookupCompactKeys(value)
    componentProps.lookup_compact_keys = [...componentProps.lookupCompactKeys]
  } else if (key === 'lookupColumns') {
    componentProps.lookupColumns = normalizeLookupColumns(value)
    componentProps.lookup_columns = [...componentProps.lookupColumns]
  } else if (key === 'relatedFields') {
    componentProps.relatedFields = normalizeRelatedFields(value)
    componentProps.related_fields = [...componentProps.relatedFields]
  } else if (key === 'relatedObjectCode') {
    const next = String(value || '').trim()
    if (next) {
      componentProps.relatedObjectCode = next
      componentProps.related_object_code = next
      componentProps.targetObjectCode = next
      componentProps.target_object_code = next
    }
  } else if (key === 'displayMode') {
    const next = String(value || '').trim()
    if (next) {
      componentProps.displayMode = next
      componentProps.display_mode = next
    }
  } else if (key === 'pageSize') {
    const pageSize = Number(value)
    if (Number.isFinite(pageSize) && pageSize > 0) {
      componentProps.pageSize = Math.floor(pageSize)
      componentProps.page_size = Math.floor(pageSize)
    }
  } else if (key === 'paginationPageSize') {
    const pageSize = Number(value)
    if (Number.isFinite(pageSize) && pageSize > 0) {
      componentProps.paginationPageSize = Math.floor(pageSize)
      componentProps.pagination_page_size = Math.floor(pageSize)
    }
  } else if (key === 'showShortcutHelp') {
    const next = toBooleanConfig(value, true)
    componentProps.showShortcutHelp = next
    componentProps.show_shortcut_help = next
  } else if (key === 'defaultShortcutHelpPinned') {
    const next = toBooleanConfig(value, false)
    componentProps.defaultShortcutHelpPinned = next
    componentProps.default_shortcut_help_pinned = next
    componentProps.shortcutHelpDefaultPinned = next
    componentProps.shortcut_help_default_pinned = next
  } else {
    componentProps[key] = value
  }

  field.componentProps = componentProps
  ;(field as any).component_props = componentProps
  delete field[key]
  return true
}

export const resolveDesignerFieldProps = (field: Record<string, any>) => {
  const componentProps = resolveComponentProps(field)
  return {
    lookupCompactKeys: normalizeLookupCompactKeys(
      field.lookupCompactKeys ??
      componentProps.lookupCompactKeys ??
      componentProps.lookup_compact_keys
    ),
    lookupColumns: normalizeLookupColumns(
      field.lookupColumns ??
      field.lookup_columns ??
      componentProps.lookupColumns ??
      componentProps.lookup_columns
    ),
    relatedFields: normalizeRelatedFields(
      field.relatedFields ??
      field.related_fields ??
      componentProps.relatedFields ??
      componentProps.related_fields
    ),
    paginationPageSize:
      field.paginationPageSize ??
      field.pagination_page_size ??
      componentProps.paginationPageSize ??
      componentProps.pagination_page_size,
    relatedObjectCode:
      field.relatedObjectCode ??
      field.related_object_code ??
      field.targetObjectCode ??
      field.target_object_code ??
      componentProps.relatedObjectCode ??
      componentProps.related_object_code ??
      componentProps.targetObjectCode ??
      componentProps.target_object_code,
    displayMode:
      field.displayMode ??
      field.display_mode ??
      componentProps.displayMode ??
      componentProps.display_mode,
    pageSize:
      field.pageSize ??
      field.page_size ??
      componentProps.pageSize ??
      componentProps.page_size,
    showShortcutHelp: toBooleanConfig(
      field.showShortcutHelp ??
      field.show_shortcut_help ??
      componentProps.showShortcutHelp ??
      componentProps.show_shortcut_help,
      true
    ),
    defaultShortcutHelpPinned: toBooleanConfig(
      field.defaultShortcutHelpPinned ??
      field.default_shortcut_help_pinned ??
      field.shortcutHelpDefaultPinned ??
      field.shortcut_help_default_pinned ??
      componentProps.defaultShortcutHelpPinned ??
      componentProps.default_shortcut_help_pinned ??
      componentProps.shortcutHelpDefaultPinned ??
      componentProps.shortcut_help_default_pinned,
      false
    )
  }
}
