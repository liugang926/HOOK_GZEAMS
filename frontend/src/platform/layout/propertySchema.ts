import { normalizeFieldType } from '@/utils/fieldType'

export type PropertyInputType = 'text' | 'number' | 'switch' | 'select' | 'textarea' | 'json' | 'tabs'

export type FieldPropertySection = 'basic' | 'display' | 'validation' | 'advanced'
export interface FieldPropertySchemaItem {
  key: string
  label: string
  inputType: PropertyInputType
  section: FieldPropertySection
  options?: Array<{ label: string; value: unknown }>
}

export type SectionPropertySection = 'basic' | 'display' | 'advanced'
export interface SectionPropertySchemaItem {
  key: string
  label: string
  inputType: PropertyInputType
  section: SectionPropertySection
  options?: Array<{ label: string; value: unknown }>
  appliesTo?: string[]
}

const FIELD_COMMON_SCHEMA: FieldPropertySchemaItem[] = [
  { key: 'fieldType', label: 'Field Type', inputType: 'select', section: 'basic' },
  { key: 'label', label: 'Label', inputType: 'text', section: 'basic' },
  { key: 'placeholder', label: 'Placeholder', inputType: 'text', section: 'basic' },
  { key: 'defaultValue', label: 'Default Value', inputType: 'text', section: 'basic' },
  { key: 'helpText', label: 'Help Text', inputType: 'textarea', section: 'basic' },
  { key: 'span', label: 'Span', inputType: 'number', section: 'display' },
  { key: 'fullWidth', label: 'Full Width', inputType: 'switch', section: 'display' },
  { key: 'minHeight', label: 'Min Height', inputType: 'number', section: 'display' },
  {
    key: 'labelPosition',
    label: 'Label Position',
    inputType: 'select',
    section: 'display',
    options: [
      { label: 'Inherit/Left', value: '' },
      { label: 'Left Aligned', value: 'left' },
      { label: 'Top Aligned', value: 'top' },
    ]
  },
  { key: 'labelWidth', label: 'Custom Label Width (e.g. 150px)', inputType: 'text', section: 'display' },
  { key: 'required', label: 'Required', inputType: 'switch', section: 'display' },
  { key: 'readonly', label: 'Readonly', inputType: 'switch', section: 'display' },
  { key: 'visible', label: 'Visible', inputType: 'switch', section: 'display' },
]

const FIELD_TYPE_SPECIFIC_SCHEMA: Record<string, FieldPropertySchemaItem[]> = {
  text: [
    { key: 'min_length', label: 'Min Length', inputType: 'number', section: 'validation' },
    { key: 'max_length', label: 'Max Length', inputType: 'number', section: 'validation' },
    { key: 'regex_pattern', label: 'Regex', inputType: 'text', section: 'validation' },
  ],
  textarea: [
    { key: 'rows', label: 'Rows', inputType: 'number', section: 'display' },
    { key: 'min_length', label: 'Min Length', inputType: 'number', section: 'validation' },
    { key: 'max_length', label: 'Max Length', inputType: 'number', section: 'validation' },
  ],
  rich_text: [{ key: 'toolbar', label: 'Toolbar', inputType: 'select', section: 'advanced' }],
  number: [
    { key: 'min_value', label: 'Min Value', inputType: 'number', section: 'validation' },
    { key: 'max_value', label: 'Max Value', inputType: 'number', section: 'validation' },
    { key: 'precision', label: 'Precision', inputType: 'number', section: 'validation' },
  ],
  currency: [
    { key: 'min_value', label: 'Min Value', inputType: 'number', section: 'validation' },
    { key: 'max_value', label: 'Max Value', inputType: 'number', section: 'validation' },
    { key: 'precision', label: 'Precision', inputType: 'number', section: 'validation' },
  ],
  percent: [
    { key: 'min_value', label: 'Min Value', inputType: 'number', section: 'validation' },
    { key: 'max_value', label: 'Max Value', inputType: 'number', section: 'validation' },
    { key: 'precision', label: 'Precision', inputType: 'number', section: 'validation' },
  ],
  date: [
    { key: 'format', label: 'Format', inputType: 'text', section: 'advanced' },
    { key: 'valueFormat', label: 'Value Format', inputType: 'text', section: 'advanced' },
  ],
  datetime: [
    { key: 'format', label: 'Format', inputType: 'text', section: 'advanced' },
    { key: 'valueFormat', label: 'Value Format', inputType: 'text', section: 'advanced' },
  ],
  time: [
    { key: 'format', label: 'Format', inputType: 'text', section: 'advanced' },
    { key: 'valueFormat', label: 'Value Format', inputType: 'text', section: 'advanced' },
  ],
  select: [{ key: 'options', label: 'Options', inputType: 'json', section: 'advanced' }],
  multi_select: [{ key: 'options', label: 'Options', inputType: 'json', section: 'advanced' }],
  radio: [{ key: 'options', label: 'Options', inputType: 'json', section: 'advanced' }],
  checkbox: [{ key: 'options', label: 'Options', inputType: 'json', section: 'advanced' }],
  dictionary: [{ key: 'dictionaryType', label: 'Dictionary Type', inputType: 'text', section: 'advanced' }],
  reference: [
    { key: 'referenceObject', label: 'Reference Object', inputType: 'text', section: 'advanced' },
    { key: 'lookupCompactKeys', label: 'Lookup Compact Keys', inputType: 'json', section: 'advanced' }
  ],
  sub_table: [
    { key: 'relatedFields', label: 'Related Fields', inputType: 'json', section: 'advanced' },
    { key: 'paginationPageSize', label: 'Pagination Page Size', inputType: 'number', section: 'display' },
    { key: 'showShortcutHelp', label: 'Show Shortcut Help', inputType: 'switch', section: 'advanced' },
    { key: 'defaultShortcutHelpPinned', label: 'Default Shortcut Help Pinned', inputType: 'switch', section: 'advanced' }
  ],
  file: [
    { key: 'accept', label: 'Accept', inputType: 'text', section: 'advanced' },
    { key: 'maxSize', label: 'Max Size', inputType: 'number', section: 'validation' },
    { key: 'maxCount', label: 'Max Count', inputType: 'number', section: 'validation' },
  ],
  image: [
    { key: 'accept', label: 'Accept', inputType: 'text', section: 'advanced' },
    { key: 'maxSize', label: 'Max Size', inputType: 'number', section: 'validation' },
    { key: 'maxCount', label: 'Max Count', inputType: 'number', section: 'validation' },
  ],
  attachment: [
    { key: 'accept', label: 'Accept', inputType: 'text', section: 'advanced' },
    { key: 'maxSize', label: 'Max Size', inputType: 'number', section: 'validation' },
    { key: 'maxCount', label: 'Max Count', inputType: 'number', section: 'validation' },
  ],
  related_object: [
    { key: 'relationCode', label: 'Relation Code', inputType: 'text', section: 'advanced' },
    { key: 'relatedObjectCode', label: 'Target Object', inputType: 'text', section: 'advanced' },
    { key: 'pageSize', label: 'Max Rows', inputType: 'number', section: 'display' },
    {
      key: 'displayMode',
      label: 'Display Mode',
      inputType: 'select',
      section: 'display',
      options: [
        { label: 'Inline Editable', value: 'inline_editable' },
        { label: 'Inline Readonly', value: 'inline_readonly' },
        { label: 'Hidden', value: 'hidden' }
      ]
    }
  ],
}

const SECTION_COMMON_SCHEMA: SectionPropertySchemaItem[] = [
  { key: 'title', label: 'Title', inputType: 'text', section: 'basic' },
  {
    key: 'type',
    label: 'Section Type',
    inputType: 'select',
    section: 'basic',
    options: [
      { label: 'Standard', value: 'section' },
      { label: 'Tab Pages', value: 'tab' },
      { label: 'Collapsible Group', value: 'collapse' },
    ],
  },
  {
    key: 'position',
    label: 'Position',
    inputType: 'select',
    section: 'display',
    options: [
      { label: 'Main Activity', value: 'main' },
      { label: 'Sidebar (Right)', value: 'sidebar' },
    ],
  },
  {
    key: 'columns',
    label: 'Columns',
    inputType: 'select',
    section: 'basic',
    options: [
      { label: '1', value: 1 },
      { label: '2', value: 2 },
      { label: '3', value: 3 },
      { label: '4', value: 4 },
    ],
  },
  {
    key: 'labelPosition',
    label: 'Label Position',
    inputType: 'select',
    section: 'display',
    options: [
      { label: 'Left Aligned', value: 'left' },
      { label: 'Top Aligned', value: 'top' },
    ]
  },
  { key: 'labelWidth', label: 'Custom Label Width (e.g. 150px)', inputType: 'text', section: 'display' },
  { key: 'border', label: 'Border', inputType: 'switch', section: 'display', appliesTo: ['section'] },
  { key: 'collapsible', label: 'Collapsible', inputType: 'switch', section: 'display' },
  { key: 'collapsed', label: 'Collapsed', inputType: 'switch', section: 'display' },
  { key: 'tabs', label: 'Tab Pages', inputType: 'tabs', section: 'advanced', appliesTo: ['tab'] },
]

const dedupeByKey = <T extends { key: string }>(items: T[]): T[] => {
  const map = new Map<string, T>()
  for (const item of items) {
    if (!map.has(item.key)) {
      map.set(item.key, item)
    }
  }
  return Array.from(map.values())
}

export const getFieldPropertySchema = (rawFieldType?: string): FieldPropertySchemaItem[] => {
  const fieldType = normalizeFieldType(rawFieldType || 'text')
  const typeSchema = FIELD_TYPE_SPECIFIC_SCHEMA[fieldType] || []
  return dedupeByKey([...FIELD_COMMON_SCHEMA, ...typeSchema])
}

export const getFieldPropertyKeys = (rawFieldType?: string): string[] =>
  getFieldPropertySchema(rawFieldType).map((item) => item.key)

export const getSectionPropertySchema = (sectionType = 'section'): SectionPropertySchemaItem[] =>
  SECTION_COMMON_SCHEMA.filter((item) => !item.appliesTo || item.appliesTo.includes(sectionType))

export const getSectionPropertyKeys = (sectionType = 'section'): string[] =>
  getSectionPropertySchema(sectionType).map((item) => item.key)
