import { computed, type Ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { isPlainObject, isEmptyValue, resolveFieldValue } from '@/utils/fieldKey'
import { resolveTranslatableText } from '@/utils/localeText'
import { normalizeColumnSpan } from '@/platform/layout/semanticGrid'
import { getCanvasPlacementAttrs, toCanvasGridStyle, type CanvasPlacement } from '@/platform/layout/canvasLayout'

interface DetailFieldLike {
  prop: string
  label: string
  hidden?: boolean
  readonly?: boolean
  type?: string
  editorType?: string
  options?: { label: string; value: any; color?: string }[]
  span?: number
  minHeight?: number
  labelClass?: string
  valueClass?: string
  referenceObject?: string
  referenceDisplayField?: string
  referenceSecondaryField?: string
  componentProps?: Record<string, any>
  placement?: {
    row: number
    colStart: number
    colSpan: number
    rowSpan: number
    columns: number
    totalRows: number
    order: number
    canvas?: {
      x: number
      y: number
      width: number
      height: number
    }
  }
}

interface DetailTabLike {
  id: string
  fields: DetailFieldLike[]
}

interface DetailSectionLike {
  name: string
  type?: string
  position?: 'main' | 'sidebar'
  fields: DetailFieldLike[]
  tabs?: DetailTabLike[]
}

interface UseBaseDetailPageFieldsOptions {
  props: {
    sections: DetailSectionLike[]
    data: Record<string, any>
    formData: Record<string, any>
    fieldSpan: number
  }
  activeTabs: Ref<Record<string, string>>
}

export function useBaseDetailPageFields(options: UseBaseDetailPageFieldsOptions) {
  const { locale } = useI18n()

  const getDisplayText = (value: any): string => {
    return resolveTranslatableText(value, locale.value as 'zh-CN' | 'en-US')
  }

  const editDrawerProxyFields = computed<DetailFieldLike[]>(() => {
    const out: DetailFieldLike[] = []

    for (const section of options.props.sections || []) {
      if (section.type === 'tab' && Array.isArray(section.tabs) && section.tabs.length > 0) {
        const activeId = options.activeTabs.value[section.name] || section.tabs[0].id
        const activeTab = section.tabs.find((tab) => tab.id === activeId) || section.tabs[0]
        for (const field of activeTab.fields || []) {
          if (!field.hidden) out.push(field)
        }
        continue
      }

      for (const field of section.fields || []) {
        if (!field.hidden) out.push(field)
      }
    }

    return out
  })

  const resolveFromObjectPath = (obj: any, prop: string): any => {
    const parts = prop.split('.')
    let current = obj

    for (const part of parts) {
      if (!isPlainObject(current)) return undefined

      if (part in current) {
        current = current[part]
        continue
      }

      const camelKey = part.replace(/_([a-z])/g, (_, char: string) => char.toUpperCase())
      if (camelKey in current) {
        current = current[camelKey]
        continue
      }

      const snakeKey = part.replace(/[A-Z]/g, (char: string) => `_${char.toLowerCase()}`)
      if (snakeKey in current) {
        current = current[snakeKey]
        continue
      }

      return undefined
    }

    return current
  }

  const resolveValue = (data: any, prop?: string, allowWrapped = true): any => {
    if (!data || !prop) return undefined

    if (!prop.includes('.')) {
      return resolveFieldValue(data, {
        fieldCode: prop,
        includeWrappedData: allowWrapped,
        includeCustomBags: true,
        treatEmptyAsMissing: true,
        returnEmptyMatch: true
      })
    }

    const directValue = resolveFromObjectPath(data, prop)
    if (!isEmptyValue(directValue)) return directValue

    if (allowWrapped && isPlainObject((data as any).data)) {
      const wrappedValue = resolveFromObjectPath((data as any).data, prop)
      if (!isEmptyValue(wrappedValue)) return wrappedValue
    }

    return directValue
  }

  const getFieldValue = (field: DetailFieldLike) => {
    const value = resolveValue(options.props.data, field.prop)
    return value !== undefined && value !== null ? value : '-'
  }

  const getEditFieldValue = (field: DetailFieldLike) => {
    const value = resolveValue(options.props.formData, field.prop, false)
    return value !== undefined ? value : null
  }

  const resolveEditFieldType = (field: DetailFieldLike): string => {
    const explicitType = String(field.editorType || '').trim()
    if (explicitType) return explicitType

    const fallbackType = String(field.type || 'text').trim()
    if (fallbackType === 'tag') return 'select'
    if (fallbackType === 'link') return 'text'
    return fallbackType || 'text'
  }

  const toInlineEditRuntimeField = (field: DetailFieldLike): Record<string, any> => {
    return {
      code: field.prop,
      name: field.label,
      label: field.label,
      fieldType: resolveEditFieldType(field),
      options: field.options,
      referenceObject: field.referenceObject,
      referenceDisplayField: field.referenceDisplayField,
      referenceSecondaryField: field.referenceSecondaryField,
      componentProps: field.componentProps || {}
    }
  }

  const getFieldItemStyle = (field: DetailFieldLike): Record<string, string> => {
    const minHeight = Number(field?.minHeight)
    if (!Number.isFinite(minHeight) || minHeight <= 0) return {}
    return { minHeight: `${Math.round(minHeight)}px` }
  }

  const getDetailSectionColumns = (section: DetailSectionLike): number => {
    if (section.position === 'sidebar') return 1

    const candidates: DetailFieldLike[] = []
    candidates.push(...(section.fields || []))
    for (const tab of section.tabs || []) candidates.push(...(tab.fields || []))

    for (const field of candidates) {
      const placement = field?.placement
      const columns = Number(placement?.columns)
      if (Number.isFinite(columns) && columns > 0) {
        return Math.round(columns)
      }
    }
    return 2
  }

  const getSectionCanvasStyle = (section: DetailSectionLike): Record<string, string> => {
    return {
      '--detail-section-columns': String(getDetailSectionColumns(section))
    }
  }

  const getFieldColStyle = (
    field: DetailFieldLike,
    section: DetailSectionLike
  ): Record<string, string> => {
    const placement = field?.placement as CanvasPlacement | undefined
    if (placement) {
      return toCanvasGridStyle(placement)
    }

    const columns = getDetailSectionColumns(section)
    const colSpan =
      section.position === 'sidebar'
        ? 1
        : normalizeColumnSpan(field?.span ?? options.props.fieldSpan, columns)
    return {
      gridColumn: `span ${colSpan}`
    }
  }

  const getFieldPlacementAttrs = (field: DetailFieldLike): Record<string, string> => {
    return getCanvasPlacementAttrs(field?.placement as CanvasPlacement | undefined)
  }

  return {
    getDisplayText,
    editDrawerProxyFields,
    getFieldValue,
    getEditFieldValue,
    toInlineEditRuntimeField,
    getFieldItemStyle,
    getSectionCanvasStyle,
    getFieldColStyle,
    getFieldPlacementAttrs
  }
}
