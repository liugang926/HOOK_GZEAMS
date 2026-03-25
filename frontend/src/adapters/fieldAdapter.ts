import type { FieldDefinition } from '@/types'
import type { RuntimeField, RuntimeFieldType } from '@/types/runtime'
import { snakeToCamel } from '@/utils/case'
import { normalizeFieldType } from '@/utils/fieldType'
import { getLocalizedLabel, getLocalizedPlaceholder, getLocalizedHelpText } from '@/utils/getLocalizedLabel'

type AnyField = FieldDefinition & Record<string, any>

const getFieldCode = (field: AnyField): string => {
  return field.code || field.fieldCode || field.field || field.field_name || field.name || ''
}

const getFieldLabel = (field: AnyField): string => {
  // First try locale-aware multilingual fields (label_zh, label_en etc.)
  const localized = getLocalizedLabel(field)
  if (localized) return localized
  // Fallback chain for legacy fields without multilingual variants
  return field.label || field.name || field.displayName || field.title || getFieldCode(field)
}

const getFieldType = (field: AnyField): RuntimeFieldType => {
  return normalizeFieldType(field.fieldType || field.type || field.field_type || 'text') as RuntimeFieldType
}

const deriveDataKey = (code: string) => {
  if (!code) return code
  return code.includes('_') ? snakeToCamel(code) : code
}

export function adaptFieldDefinition(field: AnyField): RuntimeField {
  const code = getFieldCode(field)
  return {
    code,
    dataKey: field.dataKey || field.data_key || deriveDataKey(code),
    label: getFieldLabel(field),
    fieldType: getFieldType(field),
    required: field.isRequired ?? field.required ?? false,
    readonly: field.isReadonly ?? field.readonly ?? false,
    hidden: field.isHidden ?? field.hidden ?? false,
    visible: field.isVisible ?? (field.visible !== undefined ? field.visible : true),
    span: field.span ?? field.componentProps?.span ?? field.component_props?.span,
    minHeight: field.minHeight ?? field.min_height ?? field.componentProps?.minHeight ?? field.component_props?.min_height,
    placeholder: getLocalizedPlaceholder(field),
    helpText: getLocalizedHelpText(field),
    defaultValue: field.defaultValue ?? field.default_value,
    options: field.options || field.enum,
    referenceObject: field.referenceObject || field.reference_model_path || field.relatedObject,
    referenceDisplayField: field.referenceDisplayField || field.reference_display_field || field.displayField || field.display_field,
    referenceSecondaryField: field.referenceSecondaryField || field.reference_secondary_field,
    componentProps: field.componentProps || field.component_props || {},
    metadata: field
  }
}

export function mergeRuntimeField(
  baseField: RuntimeField,
  override: Partial<RuntimeField>
): RuntimeField {
  // Layout configs often omit many keys (e.g. no `fieldType/referenceObject`),
  // so we must NOT let `undefined` in overrides wipe the base field definition.
  const next: RuntimeField = { ...(baseField as any) }
  for (const [key, value] of Object.entries(override || {})) {
    if (value === undefined) continue
      ; (next as any)[key] = value
  }

  next.componentProps = {
    ...(baseField.componentProps || {}),
    ...(override.componentProps || {})
  }

  return next
}
