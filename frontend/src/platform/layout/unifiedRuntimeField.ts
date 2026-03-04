import { adaptFieldDefinition, mergeRuntimeField } from '@/adapters/fieldAdapter'
import { normalizeFieldType } from '@/utils/fieldType'
import type { RuntimeField } from '@/types/runtime'

export interface LayoutRuntimeFieldInput {
  fieldCode?: string
  label?: string
  fieldType?: string
  required?: boolean
  readonly?: boolean
  visible?: boolean
  span?: number
  minHeight?: number
  placeholder?: string
  defaultValue?: any
  helpText?: string
  options?: Array<{ value: any; label: string }>
  referenceObject?: string
  relatedObject?: string
  componentProps?: Record<string, any>
  [key: string]: any
}

export interface CatalogRuntimeFieldInput {
  code?: string
  [key: string]: any
}

const resolveMinHeight = (field: LayoutRuntimeFieldInput | null | undefined): number | undefined => {
  if (!field) return undefined
  const raw = (field?.componentProps as any)?.minHeight ??
    (field?.componentProps as any)?.min_height ??
    (field as any)?.component_props?.minHeight ??
    (field as any)?.component_props?.min_height ??
    field?.minHeight ??
    (field as any)?.min_height
  const normalized = Number(raw)
  return Number.isFinite(normalized) && normalized > 0 ? Math.round(normalized) : undefined
}

/**
 * Build runtime field payload from layout field + optional catalog field metadata.
 * This is shared by runtime-aligned previews (designer) and runtime pages.
 */
export function toRuntimeFieldFromLayout(
  layoutField: LayoutRuntimeFieldInput,
  catalogFields: CatalogRuntimeFieldInput[] = []
): RuntimeField {
  const code = String(layoutField?.fieldCode || '').trim()
  const fullField = catalogFields.find((field) => String(field?.code || '').trim() === code)
  const base = fullField ? adaptFieldDefinition(fullField as any) : null

  const normalizedType = normalizeFieldType(layoutField?.fieldType || 'text')
  const mergedComponentProps = {
    ...(layoutField?.componentProps || {}),
    ...(layoutField as any)?.component_props || {}
  }
  const minHeight = resolveMinHeight(layoutField)
  if (minHeight !== undefined) {
    (mergedComponentProps as any).minHeight = minHeight
    delete (mergedComponentProps as any).min_height
  }

  const override = {
    code,
    label: layoutField?.label,
    fieldType: normalizedType,
    field_type: normalizedType,
    required: layoutField?.required,
    readonly: layoutField?.readonly,
    hidden: layoutField?.visible === false,
    span: layoutField?.span,
    minHeight,
    placeholder: layoutField?.placeholder,
    defaultValue: layoutField?.defaultValue,
    helpText: layoutField?.helpText,
    options: layoutField?.options,
    referenceObject: layoutField?.referenceObject || layoutField?.relatedObject,
    componentProps: mergedComponentProps,
    component_props: mergedComponentProps
  }

  if (base) {
    return mergeRuntimeField(base, override as any) as RuntimeField
  }

  return {
    code,
    label: layoutField?.label || code,
    fieldType: normalizedType,
    required: layoutField?.required,
    readonly: layoutField?.readonly,
    hidden: layoutField?.visible === false,
    span: layoutField?.span,
    minHeight,
    placeholder: layoutField?.placeholder,
    defaultValue: layoutField?.defaultValue,
    helpText: layoutField?.helpText,
    options: layoutField?.options as any,
    referenceObject: layoutField?.referenceObject || layoutField?.relatedObject,
    componentProps: mergedComponentProps,
    metadata: layoutField as any
  }
}
