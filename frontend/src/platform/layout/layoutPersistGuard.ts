import { normalizeLayoutConfig } from '@/adapters/layoutNormalizer'
import { validateAndSanitizeLayoutConfig, type LayoutType } from '@/utils/layoutValidation'

type AnyRecord = Record<string, any>

type PreparePersistOptions = {
  layoutType?: LayoutType
  availableFieldCodes?: string[]
  dropFieldCode?: (code: string) => boolean
}

const generateLayoutElementId = (prefix: string): string => {
  return `${prefix}-${Date.now()}-${Math.random().toString(36).slice(2, 8)}`
}

const normalizePlacementSnapshot = (rawPlacement: any) => {
  if (!rawPlacement || typeof rawPlacement !== 'object') return undefined

  const toInt = (value: unknown): number | undefined => {
    const num = Number(value)
    if (!Number.isFinite(num) || num <= 0) return undefined
    return Math.round(num)
  }

  const toRatio = (value: unknown): number | undefined => {
    const num = Number(value)
    if (!Number.isFinite(num) || num < 0) return undefined
    return Math.round(num * 1000000) / 1000000
  }

  const normalized = {
    row: toInt(rawPlacement.row),
    colStart: toInt(rawPlacement.colStart ?? rawPlacement.col_start),
    colSpan: toInt(rawPlacement.colSpan ?? rawPlacement.col_span),
    rowSpan: toInt(rawPlacement.rowSpan ?? rawPlacement.row_span),
    columns: toInt(rawPlacement.columns),
    totalRows: toInt(rawPlacement.totalRows ?? rawPlacement.total_rows),
    order: toInt(rawPlacement.order),
    canvas: {
      x: toRatio(rawPlacement.canvas?.x),
      y: toRatio(rawPlacement.canvas?.y),
      width: toRatio(rawPlacement.canvas?.width),
      height: toRatio(rawPlacement.canvas?.height)
    }
  }

  if (!normalized.row || !normalized.colStart || !normalized.colSpan || !normalized.columns) {
    return undefined
  }

  if (!normalized.rowSpan) normalized.rowSpan = 1
  if (!normalized.totalRows) normalized.totalRows = normalized.row
  if (!normalized.order) normalized.order = 1
  if (!normalized.canvas.width) normalized.canvas.width = Math.round((normalized.colSpan / normalized.columns) * 1000000) / 1000000
  if (!normalized.canvas.height) normalized.canvas.height = 1
  if (normalized.canvas.x === undefined) normalized.canvas.x = Math.round(((normalized.colStart - 1) / normalized.columns) * 1000000) / 1000000
  if (normalized.canvas.y === undefined) normalized.canvas.y = Math.round(((normalized.row - 1) / normalized.totalRows) * 1000000) / 1000000

  return normalized
}

const normalizeFieldForPersist = (rawField: any, dropFieldCode?: (code: string) => boolean) => {
  const field = { ...(rawField || {}) }
  const fieldCode = String(
    field.fieldCode || field.field_code || field.code || field.prop || field.name || ''
  ).trim()
  if (!fieldCode) return null
  if (dropFieldCode && dropFieldCode(fieldCode)) return null

  const componentProps = {
    ...(field.component_props || {}),
    ...(field.componentProps || {})
  }
  const rawMinHeight = field.minHeight ?? field.min_height ?? componentProps.minHeight ?? componentProps.min_height
  const normalizedMinHeight = rawMinHeight === undefined
    ? undefined
    : (Number.isFinite(Number(rawMinHeight)) ? Math.round(Number(rawMinHeight)) : rawMinHeight)

  if (normalizedMinHeight === undefined) {
    delete componentProps.minHeight
    delete componentProps.min_height
  } else {
    componentProps.minHeight = normalizedMinHeight
    delete componentProps.min_height
  }

  const normalizedField = {
    ...field,
    id: field.id || generateLayoutElementId('field'),
    fieldCode,
    label: field.label || field.name || fieldCode,
    span: Number.isFinite(Number(field.span)) ? Number(field.span) : 1,
    minHeight: normalizedMinHeight,
    componentProps,
    component_props: componentProps
  }
  const normalizedPlacement = normalizePlacementSnapshot(
    field.layoutPlacement ||
    field.layout_placement ||
    field.placement ||
    field.canvasPlacement
  )
  if (normalizedPlacement) {
    ;(normalizedField as any).layoutPlacement = normalizedPlacement
    ;(normalizedField as any).layout_placement = {
      row: normalizedPlacement.row,
      col_start: normalizedPlacement.colStart,
      col_span: normalizedPlacement.colSpan,
      row_span: normalizedPlacement.rowSpan,
      columns: normalizedPlacement.columns,
      total_rows: normalizedPlacement.totalRows,
      order: normalizedPlacement.order
    }
  } else {
    delete (normalizedField as any).layoutPlacement
    delete (normalizedField as any).layout_placement
  }
  delete (normalizedField as any).min_height
  return normalizedField
}

export const resolveRawLayoutConfig = (raw: any): AnyRecord => {
  const payload = (raw?.data ?? raw) as AnyRecord
  if (
    Array.isArray(payload?.sections) ||
    Array.isArray(payload?.columns) ||
    Array.isArray(payload?.fields) ||
    payload?.modeOverrides ||
    payload?.mode_overrides
  ) {
    return payload
  }
  return (
    payload?.layoutConfig ||
    payload?.layout_config ||
    payload?.layout ||
    { sections: [] }
  ) as AnyRecord
}

export const ensureLayoutConfigIds = (rawConfig: any, options?: Pick<PreparePersistOptions, 'dropFieldCode'>): AnyRecord => {
  const normalized = normalizeLayoutConfig((rawConfig || { sections: [] }) as AnyRecord) as AnyRecord
  const next = JSON.parse(JSON.stringify(normalized || {})) as AnyRecord

  if (!Array.isArray(next.sections)) return next

  next.sections = next.sections.map((rawSection: AnyRecord) => {
    const section = { ...(rawSection || {}) }
    const sectionType = section.type || 'section'
    section.id = section.id || generateLayoutElementId('section')
    section.type = sectionType

    if (sectionType === 'tab') {
      section.tabs = (Array.isArray(section.tabs) ? section.tabs : []).map((rawTab: AnyRecord) => ({
        ...(rawTab || {}),
        id: rawTab?.id || generateLayoutElementId('tab'),
        title: rawTab?.title || 'Tab',
        fields: (Array.isArray(rawTab?.fields) ? rawTab.fields : [])
          .map((field: AnyRecord) => normalizeFieldForPersist(field, options?.dropFieldCode))
          .filter(Boolean)
      }))
      return section
    }

    if (sectionType === 'collapse') {
      section.items = (Array.isArray(section.items) ? section.items : []).map((rawItem: AnyRecord) => ({
        ...(rawItem || {}),
        id: rawItem?.id || generateLayoutElementId('collapse'),
        title: rawItem?.title || 'Item',
        fields: (Array.isArray(rawItem?.fields) ? rawItem.fields : [])
          .map((field: AnyRecord) => normalizeFieldForPersist(field, options?.dropFieldCode))
          .filter(Boolean)
      }))
      return section
    }

    section.fields = (Array.isArray(section.fields) ? section.fields : [])
      .map((field: AnyRecord) => normalizeFieldForPersist(field, options?.dropFieldCode))
      .filter(Boolean)
    return section
  })

  return next
}

const collectReferencedFieldCodes = (config: AnyRecord): string[] => {
  const codes = new Set<string>()

  for (const section of config.sections || []) {
    if (section.type === 'tab') {
      for (const tab of section.tabs || []) {
        for (const field of tab.fields || []) {
          const code = String(field?.fieldCode || '').trim()
          if (code) codes.add(code)
        }
      }
      continue
    }

    if (section.type === 'collapse') {
      for (const item of section.items || []) {
        for (const field of item.fields || []) {
          const code = String(field?.fieldCode || '').trim()
          if (code) codes.add(code)
        }
      }
      continue
    }

    for (const field of section.fields || []) {
      const code = String(field?.fieldCode || '').trim()
      if (code) codes.add(code)
    }
  }

  return [...codes]
}

export const preparePersistLayoutConfig = (rawConfig: any, options: PreparePersistOptions = {}): AnyRecord => {
  const layoutType = options.layoutType || 'form'
  const withIds = ensureLayoutConfigIds(resolveRawLayoutConfig(rawConfig), {
    dropFieldCode: options.dropFieldCode
  })
  const validation = validateAndSanitizeLayoutConfig(withIds, layoutType)
  if (!validation.valid) {
    const first = validation.errors?.[0]
    const prefix = first?.path ? `${first.path}: ` : ''
    throw new Error(first ? `${prefix}${first.message}` : 'Layout configuration is invalid')
  }

  const sanitizedWithIds = ensureLayoutConfigIds((validation.sanitized || withIds) as AnyRecord, {
    dropFieldCode: options.dropFieldCode
  })

  if (Array.isArray(options.availableFieldCodes) && options.availableFieldCodes.length > 0) {
    const knownCodes = new Set(options.availableFieldCodes.map((code) => String(code || '').trim()).filter(Boolean))
    const referenced = collectReferencedFieldCodes(sanitizedWithIds)
    const unknown = referenced.filter((code) => !knownCodes.has(code))
    if (unknown.length > 0) {
      throw new Error(`Layout contains unknown fields: ${unknown.join(', ')}`)
    }
  }

  return sanitizedWithIds
}
