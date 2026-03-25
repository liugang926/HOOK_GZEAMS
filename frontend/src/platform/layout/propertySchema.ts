import { normalizeFieldType } from '@/utils/fieldType'

export type PropertyInputType = 'text' | 'number' | 'switch' | 'select' | 'textarea' | 'json' | 'tabs'

export type FieldPropertySection = 'basic' | 'display' | 'validation' | 'advanced'
export interface FieldPropertySchemaItem {
  key: string
  label: string
  labelKey?: string
  inputType: PropertyInputType
  section: FieldPropertySection
  options?: Array<{ label: string; labelKey?: string; value: unknown }>
  appliesTo?: string[]
  hiddenFor?: string[]
}

export type SectionPropertySection = 'basic' | 'display' | 'advanced'
export interface SectionPropertySchemaItem {
  key: string
  label: string
  labelKey?: string
  inputType: PropertyInputType
  section: SectionPropertySection
  options?: Array<{ label: string; labelKey?: string; value: unknown }>
  appliesTo?: string[]
  hiddenFor?: string[]
}

const FIELD_COMMON_SCHEMA: FieldPropertySchemaItem[] = [
  { key: 'fieldType', label: 'Field Type', inputType: 'select', section: 'basic' },
  { key: 'label', label: 'Label', inputType: 'text', section: 'basic' },
  {
    key: 'placeholder',
    label: 'Placeholder',
    inputType: 'text',
    section: 'basic',
    hiddenFor: ['boolean', 'switch', 'checkbox', 'radio', 'tag', 'image', 'file', 'attachment', 'related_object', 'sub_table', 'qr_code', 'barcode']
  },
  {
    key: 'defaultValue',
    label: 'Default Value',
    inputType: 'text',
    section: 'basic',
    hiddenFor: ['file', 'image', 'attachment', 'related_object', 'sub_table', 'qr_code', 'barcode']
  },
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
  { key: 'required', label: 'Required', inputType: 'switch', section: 'basic' },
  { key: 'readonly', label: 'Readonly', inputType: 'switch', section: 'basic' },
  { key: 'visible', label: 'Visible', inputType: 'switch', section: 'display' },
  { key: 'visibilityRule', label: 'Visibility Rule', inputType: 'json', section: 'display', hiddenFor: ['sub_table', 'related_object'] },
]

const FIELD_TYPE_SPECIFIC_SCHEMA: Record<string, FieldPropertySchemaItem[]> = {
  text: [
    { key: 'min_length', label: 'Min Length', inputType: 'number', section: 'validation' },
    { key: 'max_length', label: 'Max Length', inputType: 'number', section: 'validation' },
    { key: 'regex_pattern', label: 'Regex', inputType: 'text', section: 'validation' },
    { key: 'validation_message', label: 'Error Message', inputType: 'text', section: 'validation' },
  ],
  textarea: [
    { key: 'rows', label: 'Rows', inputType: 'number', section: 'display' },
    { key: 'min_length', label: 'Min Length', inputType: 'number', section: 'validation' },
    { key: 'max_length', label: 'Max Length', inputType: 'number', section: 'validation' },
    { key: 'validation_message', label: 'Error Message', inputType: 'text', section: 'validation' },
  ],
  rich_text: [{ key: 'toolbar', label: 'Toolbar', inputType: 'select', section: 'advanced' }],
  number: [
    { key: 'min_value', label: 'Min Value', inputType: 'number', section: 'validation' },
    { key: 'max_value', label: 'Max Value', inputType: 'number', section: 'validation' },
    { key: 'precision', label: 'Precision', inputType: 'number', section: 'validation' },
    { key: 'validation_message', label: 'Error Message', inputType: 'text', section: 'validation' },
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
    { key: 'lookupCompactKeys', label: 'Lookup Compact Keys', inputType: 'json', section: 'advanced' },
    { key: 'lookupColumns', label: 'Lookup Columns', inputType: 'json', section: 'advanced' }
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
  { key: 'title', label: 'Title', labelKey: 'system.pageLayout.designer.sectionProperties.fields.title', inputType: 'text', section: 'basic' },
  { key: 'titleEn', label: 'English Title', labelKey: 'system.pageLayout.designer.sectionProperties.fields.titleEn', inputType: 'text', section: 'basic', appliesTo: ['detail-region'] },
  { key: 'translationKey', label: 'Translation Key', labelKey: 'system.pageLayout.designer.sectionProperties.fields.translationKey', inputType: 'text', section: 'advanced', appliesTo: ['detail-region'] },
  {
    key: 'type',
    label: 'Section Type',
    labelKey: 'system.pageLayout.designer.sectionProperties.fields.type',
    inputType: 'select',
    section: 'basic',
    options: [
      { label: 'Standard', labelKey: 'system.pageLayout.designer.sectionProperties.options.types.section', value: 'section' },
      { label: 'Tab Pages', labelKey: 'system.pageLayout.designer.sectionProperties.options.types.tab', value: 'tab' },
      { label: 'Collapsible Group', labelKey: 'system.pageLayout.designer.sectionProperties.options.types.collapse', value: 'collapse' },
      { label: 'Detail Region', labelKey: 'system.pageLayout.designer.sectionProperties.options.types.detailRegion', value: 'detail-region' },
    ],
  },
  {
    key: 'relationCode',
    label: 'Relation Code',
    labelKey: 'system.pageLayout.designer.sectionProperties.fields.relationCode',
    inputType: 'text',
    section: 'basic',
    appliesTo: ['detail-region']
  },
  {
    key: 'fieldCode',
    label: 'Field Code',
    labelKey: 'system.pageLayout.designer.sectionProperties.fields.fieldCode',
    inputType: 'text',
    section: 'basic',
    appliesTo: ['detail-region']
  },
  {
    key: 'targetObjectCode',
    label: 'Target Object Code',
    labelKey: 'system.pageLayout.designer.sectionProperties.fields.targetObjectCode',
    inputType: 'text',
    section: 'basic',
    appliesTo: ['detail-region']
  },
  {
    key: 'detailEditMode',
    label: 'Detail Edit Mode',
    labelKey: 'system.pageLayout.designer.sectionProperties.fields.detailEditMode',
    inputType: 'select',
    section: 'display',
    appliesTo: ['detail-region'],
    options: [
      { label: 'Inline Table', labelKey: 'system.pageLayout.designer.sectionProperties.options.detailEditMode.inlineTable', value: 'inline_table' },
      { label: 'Nested Form', labelKey: 'system.pageLayout.designer.sectionProperties.options.detailEditMode.nestedForm', value: 'nested_form' },
      { label: 'Readonly Table', labelKey: 'system.pageLayout.designer.sectionProperties.options.detailEditMode.readonlyTable', value: 'readonly_table' }
    ]
  },
  {
    key: 'position',
    label: 'Position',
    labelKey: 'system.pageLayout.designer.sectionProperties.fields.position',
    inputType: 'select',
    section: 'display',
    options: [
      { label: 'Main Activity', labelKey: 'system.pageLayout.designer.sectionProperties.options.position.main', value: 'main' },
      { label: 'Sidebar (Right)', labelKey: 'system.pageLayout.designer.sectionProperties.options.position.sidebar', value: 'sidebar' },
    ],
  },
  {
    key: 'columns',
    label: 'Columns',
    labelKey: 'system.pageLayout.designer.sectionProperties.fields.columns',
    inputType: 'select',
    section: 'basic',
    hiddenFor: ['detail-region'],
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
    labelKey: 'system.pageLayout.designer.sectionProperties.fields.labelPosition',
    inputType: 'select',
    section: 'display',
    hiddenFor: ['detail-region'],
    options: [
      { label: 'Left Aligned', labelKey: 'system.pageLayout.designer.sectionProperties.options.labelPosition.left', value: 'left' },
      { label: 'Top Aligned', labelKey: 'system.pageLayout.designer.sectionProperties.options.labelPosition.top', value: 'top' },
    ]
  },
  { key: 'labelWidth', label: 'Custom Label Width (e.g. 150px)', labelKey: 'system.pageLayout.designer.sectionProperties.fields.labelWidth', inputType: 'text', section: 'display', hiddenFor: ['detail-region'] },
  { key: 'border', label: 'Border', labelKey: 'system.pageLayout.designer.sectionProperties.fields.border', inputType: 'switch', section: 'display', appliesTo: ['section'] },
  { key: 'collapsible', label: 'Collapsible', labelKey: 'system.pageLayout.designer.sectionProperties.fields.collapsible', inputType: 'switch', section: 'display' },
  { key: 'collapsed', label: 'Collapsed', labelKey: 'system.pageLayout.designer.sectionProperties.fields.collapsed', inputType: 'switch', section: 'display' },
  { key: 'tabs', label: 'Tab Pages', labelKey: 'system.pageLayout.designer.sectionProperties.fields.tabs', inputType: 'tabs', section: 'advanced', appliesTo: ['tab'] },
  {
    key: 'relatedFields',
    label: 'Related Fields',
    labelKey: 'system.pageLayout.designer.sectionProperties.fields.relatedFields',
    inputType: 'json',
    section: 'advanced',
    appliesTo: ['detail-region']
  },
  {
    key: 'lookupColumns',
    label: 'Lookup Columns',
    labelKey: 'system.pageLayout.designer.sectionProperties.fields.lookupColumns',
    inputType: 'json',
    section: 'advanced',
    appliesTo: ['detail-region']
  },
  {
    key: 'toolbarConfig',
    label: 'Toolbar Config',
    labelKey: 'system.pageLayout.designer.sectionProperties.fields.toolbarConfig',
    inputType: 'json',
    section: 'advanced',
    appliesTo: ['detail-region']
  },
  {
    key: 'summaryRules',
    label: 'Summary Rules',
    labelKey: 'system.pageLayout.designer.sectionProperties.fields.summaryRules',
    inputType: 'json',
    section: 'advanced',
    appliesTo: ['detail-region']
  },
  {
    key: 'validationRules',
    label: 'Validation Rules',
    labelKey: 'system.pageLayout.designer.sectionProperties.fields.validationRules',
    inputType: 'json',
    section: 'advanced',
    appliesTo: ['detail-region']
  }
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
  return dedupeByKey([...FIELD_COMMON_SCHEMA, ...typeSchema]).filter((item) => {
    if (item.appliesTo && !item.appliesTo.includes(fieldType)) return false
    if (item.hiddenFor && item.hiddenFor.includes(fieldType)) return false
    return true
  })
}

export const getFieldPropertyKeys = (rawFieldType?: string): string[] =>
  getFieldPropertySchema(rawFieldType).map((item) => item.key)

export const getSectionPropertySchema = (sectionType = 'section'): SectionPropertySchemaItem[] =>
  SECTION_COMMON_SCHEMA.filter((item) => {
    if (item.appliesTo && !item.appliesTo.includes(sectionType)) return false
    if (item.hiddenFor && item.hiddenFor.includes(sectionType)) return false
    return true
  })

export const getSectionPropertyKeys = (sectionType = 'section'): string[] =>
  getSectionPropertySchema(sectionType).map((item) => item.key)
