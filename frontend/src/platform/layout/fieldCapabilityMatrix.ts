import { normalizeFieldType } from '@/utils/fieldType'

export type FieldRenderMode = 'edit' | 'readonly' | 'list' | 'search'

export interface FieldCapability {
  type: string
  componentType: string
  core: boolean
  modes: Record<FieldRenderMode, boolean>
  filterable: boolean
  sortable: boolean
  designerConfigurable: boolean
}

const CORE_FIELD_TYPES = [
  'text',
  'textarea',
  'number',
  'currency',
  'percent',
  'date',
  'datetime',
  'time',
  'select',
  'multi_select',
  'radio',
  'checkbox',
  'boolean',
  'user',
  'department',
  'reference',
  'asset',
  'location',
  'file',
  'image',
  'rich_text',
  'qr_code',
  'barcode',
  'sub_table',
  'formula',
] as const

const DEFAULT_MODES: Record<FieldRenderMode, boolean> = {
  edit: true,
  readonly: true,
  list: true,
  search: true,
}

const cap = (
  type: string,
  componentType: string,
  options?: Partial<Omit<FieldCapability, 'type' | 'componentType' | 'core' | 'modes'>> & {
    core?: boolean
    modes?: Partial<Record<FieldRenderMode, boolean>>
  }
): FieldCapability => ({
  type,
  componentType,
  core: options?.core ?? false,
  modes: { ...DEFAULT_MODES, ...(options?.modes || {}) },
  filterable: options?.filterable ?? true,
  sortable: options?.sortable ?? true,
  designerConfigurable: options?.designerConfigurable ?? true,
})

const MATRIX: Record<string, FieldCapability> = {
  text: cap('text', 'text', { core: true }),
  textarea: cap('textarea', 'textarea', { core: true, modes: { list: false } }),
  number: cap('number', 'number', { core: true }),
  currency: cap('currency', 'currency', { core: true }),
  percent: cap('percent', 'percent', { core: true }),
  date: cap('date', 'date', { core: true }),
  datetime: cap('datetime', 'datetime', { core: true }),
  time: cap('time', 'time', { core: true }),
  select: cap('select', 'select', { core: true }),
  multi_select: cap('multi_select', 'multi_select', { core: true }),
  radio: cap('radio', 'radio', { core: true }),
  checkbox: cap('checkbox', 'checkbox', { core: true }),
  boolean: cap('boolean', 'boolean', { core: true }),
  user: cap('user', 'user', { core: true }),
  department: cap('department', 'department', { core: true }),
  reference: cap('reference', 'reference', { core: true }),
  asset: cap('asset', 'asset', { core: true }),
  location: cap('location', 'location', { core: true }),
  file: cap('file', 'file', { core: true, modes: { search: false } }),
  image: cap('image', 'image', { core: true, modes: { search: false } }),
  rich_text: cap('rich_text', 'rich_text', { core: true, modes: { list: false, search: false } }),
  qr_code: cap('qr_code', 'qr_code', { core: true, modes: { search: false } }),
  barcode: cap('barcode', 'barcode', { core: true, modes: { search: false } }),
  sub_table: cap('sub_table', 'sub_table', { core: true, modes: { list: false, search: false }, sortable: false }),
  formula: cap('formula', 'formula', { core: true, modes: { search: false } }),
  related_object: cap('related_object', 'related_object', {
    modes: { search: false, list: false },
    sortable: false,
    designerConfigurable: false,
  }),
  workflow_progress: cap('workflow_progress', 'workflow_progress', {
    modes: { search: false, list: false },
    filterable: false,
    sortable: false,
    designerConfigurable: false,
  }),

  // Non-core but supported by current engine
  switch: cap('switch', 'switch', { modes: { list: false } }),
  dictionary: cap('dictionary', 'dictionary'),
  json: cap('json', 'json', { modes: { search: false }, sortable: false }),
  object: cap('object', 'object', { modes: { search: false }, sortable: false }),
  attachment: cap('attachment', 'attachment', { modes: { search: false } }),
  code: cap('code', 'code'),
  color: cap('color', 'color'),
  rate: cap('rate', 'rate'),
  slider: cap('slider', 'slider'),
  email: cap('email', 'text'),
  url: cap('url', 'text'),
  phone: cap('phone', 'text'),
  password: cap('password', 'text', { modes: { list: false, readonly: false, search: false }, filterable: false }),
  daterange: cap('daterange', 'date'),
  year: cap('year', 'date'),
  month: cap('month', 'date'),
  organization: cap('organization', 'reference'),
}

const KNOWN_COMPONENT_TYPES = new Set<string>([
  'text',
  'textarea',
  'number',
  'date',
  'select',
  'checkbox',
  'boolean',
  'reference',
  'user',
  'department',
  'location',
  'asset',
  'dictionary',
  'json',
  'sub_table',
  'formula',
  'related_object',
  'workflow_progress',
  'file',
  'image',
  'attachment',
  'qr_code',
  'barcode',
  'rich_text',
  'code',
  'color',
  'rate',
  'slider',
  'switch',
  'object',
  'currency',
  'percent',
  'radio',
  'multi_select',
  'datetime',
  'time',
  'daterange',
  'year',
  'month',
  'email',
  'url',
  'phone',
  'password',
])

export const getCoreFieldTypes = (): string[] => [...CORE_FIELD_TYPES]

export const normalizeCapabilityType = (raw?: string): string => normalizeFieldType(raw || 'text')

export const getFieldCapability = (raw?: string): FieldCapability => {
  const type = normalizeCapabilityType(raw)
  return MATRIX[type] || cap(type, KNOWN_COMPONENT_TYPES.has(type) ? type : 'text')
}

export const isFieldSupportedInMode = (raw: string | undefined, mode: FieldRenderMode): boolean =>
  Boolean(getFieldCapability(raw).modes[mode])

