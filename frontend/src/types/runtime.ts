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

export interface RuntimeAggregateDetailRegion {
  relationCode: string
  fieldCode?: string
  title: string
  titleEn?: string
  titleI18n?: Record<string, string>
  translationKey?: string
  targetObjectCode: string
  targetObjectName?: string
  targetObjectNameEn?: string
  targetObjectLocaleNames?: Record<string, string>
  targetObjectRole?: 'root' | 'detail' | 'reference' | 'log' | string
  relationKind?: string
  relationType?: 'lookup' | 'master_detail' | 'derived' | string
  displayMode?: string
  displayTier?: string
  targetFkField?: string
  detailEditMode?: 'inline_table' | 'nested_form' | 'readonly_table' | string
  cascadeSoftDelete?: boolean
  toolbarConfig?: Record<string, unknown>
  summaryRules?: Array<Record<string, unknown>>
  validationRules?: Array<Record<string, unknown>>
  lookupColumns?: Array<Record<string, unknown>>
  relatedFields?: Array<Record<string, unknown>>
  showInForm?: boolean
  showInDetail?: boolean
  allowStandaloneQuery?: boolean
  allowStandaloneRoute?: boolean
  inheritPermissions?: boolean
  inheritWorkflow?: boolean
  inheritStatus?: boolean
  inheritLifecycle?: boolean
}

export interface RuntimeAggregate {
  objectCode: string
  objectRole: 'root' | 'detail' | 'reference' | 'log' | string
  isAggregateRoot: boolean
  isDetailObject: boolean
  detailRegions: RuntimeAggregateDetailRegion[]
}

export interface RuntimeWorkbenchToolbar {
  primaryActions: Array<Record<string, unknown>>
  secondaryActions: Array<Record<string, unknown>>
}

export interface RuntimeWorkbenchDetailPanel {
  code: string
  title?: string
  component?: string
  dataSource?: Record<string, unknown>
  props?: Record<string, unknown>
  [key: string]: unknown
}

export interface RuntimeWorkbenchAsyncIndicator {
  code: string
  type: string
  taskIdField?: string
  statusField?: string
  label?: string
  props?: Record<string, unknown>
  [key: string]: unknown
}

export interface RuntimeWorkbench {
  workspaceMode: string
  primaryEntryRoute: string
  legacyAliases: string[]
  toolbar: RuntimeWorkbenchToolbar
  detailPanels: RuntimeWorkbenchDetailPanel[]
  asyncIndicators: RuntimeWorkbenchAsyncIndicator[]
}

export type AggregateDocumentPageMode = 'create' | 'edit' | 'readonly'

export interface AggregateDocumentContext {
  objectCode: string
  recordId: string
  pageMode: AggregateDocumentPageMode | string
  recordLabel?: string
}

export interface AggregateDocumentCapabilities {
  canEditMaster: boolean
  canEditDetails: boolean
  canSave: boolean
  canSubmit: boolean
  canDelete: boolean
  canApprove: boolean
  readOnly: boolean
}

export interface AggregateDocumentWorkflowDefinition {
  id: string
  code: string
  name: string
  version?: number | string | null
  status?: string
  publishedAt?: string | null
}

export interface AggregateDocumentWorkflowInstance {
  id?: string
  title?: string
  status?: string
  businessObjectCode?: string
  businessId?: string
  [key: string]: unknown
}

export interface AggregateDocumentTimelineChange {
  fieldCode: string
  fieldLabel?: string
  oldValue: unknown
  newValue: unknown
}

export interface AggregateDocumentTimelineEntry {
  id: string
  source: string
  createdAt?: string | null
  title?: string
  description?: string
  action?: string
  actionDisplay?: string
  actorName?: string
  taskName?: string
  comment?: string
  operationType?: string
  operationTypeDisplay?: string
  result?: string
  resultDisplay?: string
  changes?: AggregateDocumentTimelineChange[]
  [key: string]: unknown
}

export interface AggregateDocumentWorkflowSection {
  businessObjectCode: string
  hasPublishedDefinition: boolean
  definition: AggregateDocumentWorkflowDefinition | null
  hasInstance: boolean
  isActive: boolean
  instance: AggregateDocumentWorkflowInstance | null
  timeline: AggregateDocumentTimelineEntry[]
}

export interface AggregateDocumentAuditCounts {
  activityLogs: number
  workflowApprovals: number
  workflowOperationLogs: number
}

export interface AggregateDocumentAuditSection {
  counts: AggregateDocumentAuditCounts
  activityLogs: Array<Record<string, unknown>>
  workflowApprovals: Array<Record<string, unknown>>
  workflowOperationLogs: Array<Record<string, unknown>>
}

export interface AggregateDocumentDetailSection extends RuntimeAggregateDetailRegion {
  rows: Array<Record<string, unknown>>
  rowCount: number
  editable: boolean
}

export interface AggregateDocumentResponse {
  documentVersion: number
  context: AggregateDocumentContext
  aggregate: RuntimeAggregate
  master: Record<string, unknown>
  details: Record<string, AggregateDocumentDetailSection>
  capabilities: AggregateDocumentCapabilities
  workflow: AggregateDocumentWorkflowSection
  timeline: AggregateDocumentTimelineEntry[]
  audit: AggregateDocumentAuditSection
}

export interface RuntimeTab {
  id: string
  name?: string
  title?: unknown
  fields: RuntimeField[]
}

export interface RuntimeCollapseItem {
  id: string
  name?: string
  title?: unknown
  collapsed?: boolean
  fields: RuntimeField[]
}

export interface RuntimeSection {
  id: string
  name?: string
  title?: unknown
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
