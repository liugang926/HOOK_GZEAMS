import { resolveFieldType } from '@/utils/fieldType'
import { getCoreFieldTypes, getFieldCapability, isFieldSupportedInMode, type FieldRenderMode } from '@/platform/layout/fieldCapabilityMatrix'

export type FieldComponentLoader = () => Promise<unknown>

export const FIELD_COMPONENT_LOADERS: Record<string, FieldComponentLoader> = {
  text: () => import('./fields/TextField.vue'),
  textarea: () => import('./fields/TextField.vue'),
  email: () => import('./fields/TextField.vue'),
  url: () => import('./fields/TextField.vue'),
  phone: () => import('./fields/TextField.vue'),
  password: () => import('./fields/TextField.vue'),

  number: () => import('./fields/NumberField.vue'),
  currency: () => import('./fields/NumberField.vue'),
  percent: () => import('./fields/NumberField.vue'),

  date: () => import('./fields/DateField.vue'),
  datetime: () => import('./fields/DateField.vue'),
  time: () => import('./fields/DateField.vue'),
  daterange: () => import('./fields/DateField.vue'),
  year: () => import('./fields/DateField.vue'),
  month: () => import('./fields/DateField.vue'),

  select: () => import('./fields/SelectField.vue'),
  multi_select: () => import('./fields/SelectField.vue'),
  radio: () => import('./fields/SelectField.vue'),
  checkbox: () => import('./fields/BooleanField.vue'),
  boolean: () => import('./fields/BooleanField.vue'),

  reference: () => import('./fields/ReferenceField.vue'),
  user: () => import('./fields/UserSelectField.vue'),
  department: () => import('./fields/DepartmentSelectField.vue'),
  location: () => import('./fields/LocationSelectField.vue'),
  asset: () => import('./fields/AssetSelector.vue'),

  dictionary: () => import('./fields/DictionarySelect.vue'),

  json: () => import('./fields/JsonField.vue'),
  object: () => import('./fields/JsonField.vue'),

  sub_table: () => import('./fields/SubTableField.vue'),
  formula: () => import('./fields/FormulaField.vue'),

  file: () => import('./fields/AttachmentUpload.vue'),
  image: () => import('./fields/ImageField.vue'),
  attachment: () => import('./fields/AttachmentUpload.vue'),

  qr_code: () => import('./fields/QRCodeField.vue'),
  barcode: () => import('./fields/BarcodeField.vue'),
  rich_text: () => import('./fields/RichTextField.vue'),
  code: () => import('./fields/CodeField.vue'),
  color: () => import('./fields/ColorField.vue'),
  rate: () => import('./fields/RateField.vue'),
  slider: () => import('./fields/SliderField.vue'),
  switch: () => import('./fields/SwitchField.vue'),
  related_object: () => import('@/components/common/RelatedObjectTable.vue')
}

const FIELD_TYPE_ALIASES: Record<string, string> = {
  multiselect: 'multi_select',
  multiSelect: 'multi_select',
  subtable: 'sub_table',
  subTable: 'sub_table',
  richtext: 'rich_text'
}

export const normalizeEngineFieldType = (raw?: string): string => {
  if (!raw) return 'text'
  const normalized = resolveFieldType({ fieldType: raw }, 'text')
  return FIELD_TYPE_ALIASES[raw] || FIELD_TYPE_ALIASES[normalized] || normalized
}

export const resolveEngineFieldType = (field: Record<string, unknown>, fallback = 'text'): string => {
  const normalized = resolveFieldType(field || {}, fallback)
  return FIELD_TYPE_ALIASES[normalized] || normalized
}

export const getFieldComponentLoader = (rawType?: string): FieldComponentLoader => {
  const type = normalizeEngineFieldType(rawType || 'text')
  const capability = getFieldCapability(type)
  return FIELD_COMPONENT_LOADERS[capability.componentType] || FIELD_COMPONENT_LOADERS.text
}

export const buildNormalizedRuntimeField = (field: Record<string, unknown> = {}) => {
  const mergedComponentProps = {
    ...(field.component_props || {}),
    ...(field.componentProps || {})
  }
  const fieldType = resolveEngineFieldType(field, 'text')

  return {
    ...field,
    fieldType,
    field_type: fieldType,
    componentProps: mergedComponentProps,
    component_props: mergedComponentProps
  }
}

export const getSupportedEngineFieldTypes = (): string[] => getCoreFieldTypes()

export const isEngineFieldSupportedInMode = (rawType: string | undefined, mode: FieldRenderMode): boolean =>
  isFieldSupportedInMode(rawType, mode)
