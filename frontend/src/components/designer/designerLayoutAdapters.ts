import { placeCanvasFields, type CanvasPlacement } from '@/platform/layout/canvasLayout'
import { cloneLayoutConfig } from '@/utils/layoutValidation'
import type {
  DesignerAnyRecord,
  DesignerFieldDefinition,
  LayoutConfig,
  LayoutField,
  LayoutSection
} from '@/components/designer/designerTypes'

export type ApiDataEnvelope<T> = { data?: T }

export const isRecord = (value: unknown): value is DesignerAnyRecord => {
  return value !== null && typeof value === 'object' && !Array.isArray(value)
}

export function unwrapData<T>(raw: T | ApiDataEnvelope<T>): T {
  if (isRecord(raw) && 'data' in raw) {
    const value = (raw as ApiDataEnvelope<T>).data
    return (value ?? raw) as T
  }
  return raw
}

export const readErrorMessage = (error: unknown): string | null => {
  if (!isRecord(error)) return null
  const response = error.response
  if (!isRecord(response)) return null
  const data = response.data
  if (!isRecord(data)) return null
  const message = data.message
  return typeof message === 'string' && message.trim() ? message : null
}

export const readComponentProps = (
  field: Partial<DesignerFieldDefinition & LayoutField> | null | undefined
): DesignerAnyRecord => {
  return {
    ...((isRecord(field?.componentProps) ? field.componentProps : {}) as DesignerAnyRecord),
    ...((isRecord(field?.component_props) ? field.component_props : {}) as DesignerAnyRecord)
  }
}

export const readLayoutPlacement = (
  field: LayoutField | null | undefined
): LayoutField['layoutPlacement'] | LayoutField['layout_placement'] | null => {
  if (!field) return null
  return field.layoutPlacement || field.layout_placement || null
}

export const FIELD_MIN_HEIGHT_MIN = 44
export const FIELD_MIN_HEIGHT_MAX = 720
export const FIELD_MIN_HEIGHT_STEP = 8

export const normalizeFieldMinHeight = (value: unknown): number | undefined => {
  const raw = Number(value)
  if (!Number.isFinite(raw) || raw <= 0) return undefined
  return Math.round(raw)
}

export const clampFieldMinHeight = (value: number): number => {
  if (!Number.isFinite(value)) return FIELD_MIN_HEIGHT_MIN
  const rounded = Math.round(value / FIELD_MIN_HEIGHT_STEP) * FIELD_MIN_HEIGHT_STEP
  return Math.max(FIELD_MIN_HEIGHT_MIN, Math.min(FIELD_MIN_HEIGHT_MAX, rounded))
}

export const resolveLayoutFieldMinHeight = (field: LayoutField | null | undefined): number | undefined => {
  if (!field) return undefined
  const componentProps = readComponentProps(field)
  const componentMinHeight = componentProps.minHeight
  const legacyComponentMinHeight = componentProps.min_height
  const raw = componentMinHeight ?? legacyComponentMinHeight ?? field.minHeight ?? field.min_height
  const normalized = normalizeFieldMinHeight(raw)
  return normalized ? clampFieldMinHeight(normalized) : undefined
}

export const setLayoutFieldMinHeight = (field: LayoutField, value: unknown) => {
  const normalized = normalizeFieldMinHeight(value)
  const next = normalized ? clampFieldMinHeight(normalized) : undefined

  const componentProps = readComponentProps(field)

  if (next === undefined) {
    delete componentProps.minHeight
    delete componentProps.min_height
  } else {
    componentProps.minHeight = next
    delete componentProps.min_height
  }

  field.componentProps = componentProps
  field.component_props = componentProps
  if (next === undefined) {
    delete field.minHeight
    delete field.min_height
  } else {
    field.minHeight = next
    field.min_height = next
  }
}

export const toCanvasField = (field: LayoutField): LayoutField => {
  const minHeight = resolveLayoutFieldMinHeight(field)
  return {
    ...field,
    minHeight,
    min_height: minHeight
  }
}

export function getColumns(section: Partial<LayoutSection> | null | undefined): number {
  return Number(section?.columns || section?.columnCount || section?.column || 2) || 2
}

export function getRenderColumns(section: Partial<LayoutSection> | null | undefined): number {
  if (section?.position === 'sidebar') return 1
  return getColumns(section)
}

const writeLegacyLayoutPlacement = (
  field: LayoutField,
  placement: LayoutField['layoutPlacement'] | undefined
): void => {
  if (!placement) {
    delete field.layoutPlacement
    delete field.layout_placement
    return
  }

  field.layoutPlacement = placement
  field.layout_placement = {
    row: placement.row,
    col_start: placement.colStart,
    col_span: placement.colSpan,
    row_span: placement.rowSpan,
    columns: placement.columns,
    total_rows: placement.totalRows,
    order: placement.order
  }
}

const toPersistedLayoutPlacement = (placement: CanvasPlacement | null): LayoutField['layoutPlacement'] | undefined => {
  if (!placement) return undefined
  return {
    row: placement.row,
    colStart: placement.colStart,
    colSpan: placement.colSpan,
    rowSpan: placement.rowSpan,
    columns: placement.columns,
    totalRows: placement.totalRows,
    order: placement.order,
    canvas: {
      x: placement.canvas.x,
      y: placement.canvas.y,
      width: placement.canvas.width,
      height: placement.canvas.height
    }
  }
}

const applyPlacementSnapshotToFieldList = (
  fields: LayoutField[],
  columns: number
): LayoutField[] => {
  const placementSeed = (fields || []).map((field) => ({
    span: field?.span ?? 1,
    minHeight: resolveLayoutFieldMinHeight(field)
  }))
  const placed = placeCanvasFields(placementSeed, columns, {
    preferSavedPlacement: false
  })

  return (fields || []).map((field, index) => {
    const next = { ...field }
    setLayoutFieldMinHeight(next, resolveLayoutFieldMinHeight(next))
    const placement = (placed[index]?.placement || null) as CanvasPlacement | null
    const persisted = toPersistedLayoutPlacement(placement)
    if (persisted) {
      writeLegacyLayoutPlacement(next, persisted)
    } else {
      writeLegacyLayoutPlacement(next, undefined)
    }
    return next
  })
}

export const buildLayoutConfigWithPlacementSnapshot = (rawConfig: LayoutConfig): LayoutConfig => {
  const next = cloneLayoutConfig(rawConfig || { sections: [] }) as LayoutConfig
  next.sections = (next.sections || []).map((rawSection) => {
    const section = { ...(rawSection || {}) }
    const columns = getRenderColumns(section)
    if (section.type === 'tab') {
      section.tabs = (section.tabs || []).map((tab) => ({
        ...(tab || {}),
        fields: applyPlacementSnapshotToFieldList(tab.fields || [], columns)
      }))
      return section
    }

    if (section.type === 'collapse') {
      section.items = (section.items || []).map((item) => ({
        ...(item || {}),
        fields: applyPlacementSnapshotToFieldList(item.fields || [], columns)
      }))
      return section
    }

    section.fields = applyPlacementSnapshotToFieldList(section.fields || [], columns)
    return section
  })
  return next
}
