/**
 * Runtime rendering types for dynamic layouts.
 * These types represent the normalized structure used by both
 * runtime pages and the layout designer preview.
 */

export type RuntimeFieldType =
  | 'text'
  | 'textarea'
  | 'rich_text'
  | 'richtext'
  | 'number'
  | 'currency'
  | 'percent'
  | 'date'
  | 'datetime'
  | 'time'
  | 'boolean'
  | 'switch'
  | 'select'
  | 'multi_select'
  | 'radio'
  | 'checkbox'
  | 'reference'
  | 'user'
  | 'department'
  | 'file'
  | 'image'
  | 'attachment'
  | 'qr_code'
  | 'barcode'
  | 'formula'
  | 'sub_table'
  | 'subtable'
  | 'location'
  | 'organization'
  | string

export interface RuntimeFieldOption {
  label: string
  value: unknown
  disabled?: boolean
  [key: string]: unknown
}

export interface RuntimeField {
  code: string
  // Key used to read/write values from record payloads (typically camelCase from API).
  // Engine still uses `code` for validation/props; value access should prefer dataKey when present.
  dataKey?: string
  label: string
  fieldType: RuntimeFieldType
  required?: boolean
  readonly?: boolean
  hidden?: boolean
  visible?: boolean
  span?: number
  minHeight?: number
  placeholder?: string
  helpText?: string
  defaultValue?: unknown
  options?: RuntimeFieldOption[]
  referenceObject?: string
  referenceDisplayField?: string
  referenceSecondaryField?: string
  componentProps?: Record<string, unknown>
  objectCode?: string
  instanceId?: string | null
  placement?: {
    row: number
    colStart: number
    colSpan: number
    rowSpan: number
    columns: number
    totalRows: number
    order: number
    canvas: {
      x: number
      y: number
      width: number
      height: number
    }
  }
  layoutPlacement?: {
    row?: number
    colStart?: number
    colSpan?: number
    rowSpan?: number
    columns?: number
    totalRows?: number
    order?: number
    canvas?: {
      x?: number
      y?: number
      width?: number
      height?: number
    }
  }
  metadata?: Record<string, unknown>
}

export type RuntimeSectionType = 'section' | 'card' | 'tab' | 'collapse'

export interface RuntimeTab {
  id: string
  name?: string
  title?: any
  fields: RuntimeField[]
}

export interface RuntimeCollapseItem {
  id: string
  name?: string
  title?: any
  collapsed?: boolean
  fields: RuntimeField[]
}

export interface RuntimeSection {
  id: string
  name?: string
  title?: any
  type?: RuntimeSectionType
  position?: 'main' | 'sidebar'
  columns?: number
  visible?: boolean
  collapsed?: boolean
  collapsible?: boolean
  renderAsCard?: boolean
  showTitle?: boolean
  shadow?: string
  border?: boolean
  icon?: string
  fields?: RuntimeField[]
  tabs?: RuntimeTab[]
  items?: RuntimeCollapseItem[]
}

export interface RuntimeLayoutConfig {
  sections: RuntimeSection[]
}
