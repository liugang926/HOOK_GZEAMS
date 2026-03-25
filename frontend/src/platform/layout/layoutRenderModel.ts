import { normalizeFieldType } from '@/utils/fieldType'

type AnyRecord = Record<string, any>

export type RenderMetadataContext = 'form' | 'detail'

export interface ModePolicy {
  metadataContext: RenderMetadataContext
  strictVisibility: boolean
  source: 'runtime' | 'designer' | 'test'
}

export interface FieldViewModel extends AnyRecord {
  code: string
  name: string
  label: string
  fieldType: string
  isHidden?: boolean
  showInForm?: boolean
  showInDetail?: boolean
}

export interface LayoutRenderModel {
  sections: AnyRecord[]
  fields: FieldViewModel[]
  modePolicy: ModePolicy
}

export type ModePolicyContext = 'detail-runtime' | 'detail-strict' | 'designer-preview'

export const createModePolicyForContext = (
  context: ModePolicyContext,
  overrides: Partial<ModePolicy> = {}
): ModePolicy => {
  const base: ModePolicy = (() => {
    if (context === 'detail-strict') {
      return { metadataContext: 'detail', strictVisibility: true, source: 'runtime' }
    }
    if (context === 'designer-preview') {
      return { metadataContext: 'form', strictVisibility: false, source: 'designer' }
    }
    return { metadataContext: 'form', strictVisibility: false, source: 'runtime' }
  })()

  return {
    ...base,
    ...(overrides || {})
  }
}

export const toFieldViewModel = (field: AnyRecord): FieldViewModel => {
  const code = String(field?.code || field?.fieldCode || field?.field_code || '').trim()
  const name = String(field?.name || field?.label || code).trim()
  const label = String(field?.label || field?.name || code).trim()
  const fieldType = normalizeFieldType(String(field?.fieldType || field?.field_type || field?.type || 'text'))
  const showInForm = field?.showInForm ?? field?.show_in_form
  const showInDetail = field?.showInDetail ?? field?.show_in_detail
  const isHidden = field?.isHidden ?? field?.is_hidden

  return {
    ...field,
    code,
    name: name || code,
    label: label || name || code,
    fieldType,
    showInForm,
    showInDetail,
    isHidden
  } as FieldViewModel
}

export const toFieldViewModels = (fields: AnyRecord[]): FieldViewModel[] => {
  const list = Array.isArray(fields) ? fields : []
  return list
    .map((field) => toFieldViewModel(field || {}))
    .filter((field) => !!field.code)
}

export const buildLayoutRenderModel = (input: {
  sections: AnyRecord[]
  fields: AnyRecord[]
  modePolicy: ModePolicy
}): LayoutRenderModel => {
  return {
    sections: Array.isArray(input.sections) ? input.sections : [],
    fields: toFieldViewModels(input.fields || []),
    modePolicy: input.modePolicy
  }
}

