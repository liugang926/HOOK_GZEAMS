import type { LayoutFieldConfig } from '@/types/metadata'
import type { LayoutMode } from '@/types/layout'

export interface DesignerFieldDefinition {
  code: string
  name: string
  fieldType: string
  field_type?: string
  type?: string
  displayName?: string
  isRequired?: boolean
  isReadonly?: boolean
  isSystem?: boolean
  isSearchable?: boolean
  showInList?: boolean
  showInForm?: boolean
  showInDetail?: boolean
  options?: Array<{ value: unknown; label: string }>
  referenceObject?: string
  relatedObject?: string
  componentProps?: Record<string, unknown>
  component_props?: Record<string, unknown>
  dictionaryType?: string
  defaultValue?: unknown
  placeholder?: string
  helpText?: string
}

export type DesignerAnyRecord = Record<string, unknown>

export interface LayoutField extends Omit<LayoutFieldConfig, 'fieldType'> {
  fieldType?: string
  field_type?: string
  minHeight?: number
  min_height?: number
  component_props?: DesignerAnyRecord
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
  layout_placement?: {
    row?: number
    col_start?: number
    col_span?: number
    row_span?: number
    columns?: number
    total_rows?: number
    order?: number
  }
  min_length?: number
  max_length?: number
  min_value?: number
  max_value?: number
  regex_pattern?: string
}

export interface LayoutTab {
  id: string
  name?: string
  title?: any
  fields?: LayoutField[]
}

export interface LayoutCollapseItem {
  id: string
  name?: string
  title?: any
  fields?: LayoutField[]
}

export interface LayoutSection {
  id: string
  name?: string
  type: string
  title?: any
  collapsible?: boolean
  collapsed?: boolean
  border?: boolean
  columns?: number
  columnCount?: number
  column?: number
  position?: 'main' | 'sidebar'
  fields?: LayoutField[]
  tabs?: LayoutTab[]
  items?: LayoutCollapseItem[]
}

export interface LayoutConfig {
  sections?: LayoutSection[]
  columns?: unknown[]
  actions?: unknown[]
  modeOverrides?: DesignerAnyRecord
  layoutOverrides?: DesignerAnyRecord
  layoutType?: 'Detail' | 'Compact'
}

export type DesignerConfigNode = LayoutSection | LayoutTab | LayoutCollapseItem | LayoutField

export interface FieldGroup {
  type: string
  label: string
  icon: unknown
  color?: string
  fields: DesignerFieldDefinition[]
}

export interface DesignerRenderField {
  field: LayoutField
  span24: number
  semanticSpan: number
  placement: DesignerFieldPlacement | null
  placementAttrs: Record<string, string>
}

export interface DesignerRenderTab {
  id: string
  title: string
  fields: DesignerRenderField[]
}

export interface DesignerRenderCollapseItem {
  id: string
  title: string
  fields: DesignerRenderField[]
}

export interface DesignerRenderSection {
  id: string
  title: string
  type: string
  position?: 'main' | 'sidebar'
  collapsible?: boolean
  collapsed?: boolean
  section: LayoutSection
  fields: DesignerRenderField[]
  tabs: DesignerRenderTab[]
  items: DesignerRenderCollapseItem[]
}

export type ContainerKind = 'section' | 'tab' | 'collapse'

export interface ContainerMeta {
  kind: ContainerKind
  sectionId: string
  tabId?: string
  collapseId?: string
}

export interface DesignerFieldPlacement {
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

export type ResizeAxis = 'x' | 'y' | 'xy'

export interface ResizeStartPayload {
  fieldId: string
  axis: ResizeAxis
  startX: number
  startY: number
  cardWidth: number
  cardHeight: number
}

export interface ActiveFieldResize {
  fieldId: string
  fieldCode: string
  axis: ResizeAxis
  startX: number
  startY: number
  startSpan: number
  startMinHeight: number
  spanUnitPx: number
  columns: number
  allowHorizontal: boolean
  allowVertical: boolean
  initialConfig: LayoutConfig
  previousUserSelect: string
  previousCursor: string
}

export interface ResizeHintState {
  span: number
  columns: number
  minHeight: number
  clientX: number
  clientY: number
}

export interface WysiwygDesignerProps {
  layoutId?: string
  mode?: LayoutMode
  objectCode?: string
  layoutName?: string
  businessObjectId?: string
  initialPreviewMode?: 'current' | 'active'
  layoutConfig?: LayoutConfig
}
