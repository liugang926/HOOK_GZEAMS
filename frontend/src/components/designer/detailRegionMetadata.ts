import { resolveTranslatableText } from '@/utils/localeText'
import type { DesignerDetailRegionOption, LayoutSection } from '@/components/designer/designerTypes'
import type { RuntimeAggregateDetailRegion } from '@/types/runtime'

type LocaleCode = 'zh-CN' | 'en-US'

const cloneValue = <T>(value: T): T => {
  if (value === undefined) return value
  return JSON.parse(JSON.stringify(value))
}

const buildTitleI18n = (region: RuntimeAggregateDetailRegion): Record<string, string> | undefined => {
  const titleI18n =
    region.titleI18n && typeof region.titleI18n === 'object'
      ? { ...region.titleI18n }
      : undefined

  const zhTitle = titleI18n?.['zh-CN'] || region.title || ''
  const enTitle = titleI18n?.['en-US'] || region.titleEn || region.title || ''

  if (!zhTitle && !enTitle) return titleI18n

  return {
    ...(titleI18n || {}),
    ...(zhTitle ? { 'zh-CN': zhTitle } : {}),
    ...(enTitle ? { 'en-US': enTitle } : {})
  }
}

export const localizeDetailRegionTitle = (
  region: RuntimeAggregateDetailRegion,
  locale: LocaleCode
): string => {
  return (
    resolveTranslatableText(
      region.titleI18n || {
        'zh-CN': region.title || '',
        'en-US': region.titleEn || region.title || ''
      },
      locale
    ) ||
    region.title ||
    region.relationCode
  )
}

export const localizeDetailRegionTarget = (
  region: RuntimeAggregateDetailRegion,
  locale: LocaleCode
): string => {
  return (
    resolveTranslatableText(
      region.targetObjectLocaleNames || {
        'zh-CN': region.targetObjectName || region.targetObjectCode || '',
        'en-US': region.targetObjectNameEn || region.targetObjectName || region.targetObjectCode || ''
      },
      locale
    ) ||
    region.targetObjectName ||
    region.targetObjectCode
  )
}

export const buildDetailRegionOptionLabel = (
  region: RuntimeAggregateDetailRegion,
  locale: LocaleCode
): string => {
  const title = localizeDetailRegionTitle(region, locale)
  const target = localizeDetailRegionTarget(region, locale)
  if (target && target !== region.targetObjectCode) {
    return `${title} (${region.relationCode} / ${target})`
  }
  return `${title} (${region.relationCode})`
}

export const clearDetailRegionSelection = (section: LayoutSection): void => {
  delete section.relationCode
  delete section.relation_code
  delete section.fieldCode
  delete section.field_code
  delete section.targetObjectCode
  delete section.target_object_code
  delete section.detailEditMode
  delete section.detail_edit_mode
  delete section.toolbarConfig
  delete section.toolbar_config
  delete section.summaryRules
  delete section.summary_rules
  delete section.validationRules
  delete section.validation_rules
  delete section.lookupColumns
  delete section.lookup_columns
  delete section.relatedFields
  delete section.related_fields
}

export const applyDetailRegionDefinition = (
  section: LayoutSection,
  region: RuntimeAggregateDetailRegion
): void => {
  const relationCode = String(region.relationCode || '').trim()
  if (!relationCode) return

  section.relationCode = relationCode
  section.relation_code = relationCode

  const fieldCode = String(region.fieldCode || '').trim()
  if (fieldCode) {
    section.fieldCode = fieldCode
    section.field_code = fieldCode
  } else {
    delete section.fieldCode
    delete section.field_code
  }

  const targetObjectCode = String(region.targetObjectCode || '').trim()
  if (targetObjectCode) {
    section.targetObjectCode = targetObjectCode
    section.target_object_code = targetObjectCode
  } else {
    delete section.targetObjectCode
    delete section.target_object_code
  }

  const titleI18n = buildTitleI18n(region)
  if (titleI18n && Object.keys(titleI18n).length > 0) {
    section.titleI18n = titleI18n
    section.title_i18n = cloneValue(titleI18n)
    section.title = titleI18n['zh-CN'] || section.title || region.title || relationCode
    section.titleEn = titleI18n['en-US'] || section.titleEn || region.titleEn || region.title || relationCode
    section.title_en = section.titleEn
  } else if (region.title) {
    section.title = region.title
    section.titleEn = region.titleEn || region.title
    section.title_en = section.titleEn
  }

  if (typeof region.translationKey === 'string' && region.translationKey.trim()) {
    section.translationKey = region.translationKey
    section.translation_key = region.translationKey
  }

  const detailEditMode = String(region.detailEditMode || '').trim()
  if (detailEditMode) {
    section.detailEditMode = detailEditMode
    section.detail_edit_mode = detailEditMode
  }

  if (region.toolbarConfig && typeof region.toolbarConfig === 'object') {
    section.toolbarConfig = cloneValue(region.toolbarConfig)
    section.toolbar_config = cloneValue(region.toolbarConfig)
  } else {
    delete section.toolbarConfig
    delete section.toolbar_config
  }

  if (Array.isArray(region.summaryRules)) {
    section.summaryRules = cloneValue(region.summaryRules)
    section.summary_rules = cloneValue(region.summaryRules)
  } else {
    delete section.summaryRules
    delete section.summary_rules
  }

  if (Array.isArray(region.validationRules)) {
    section.validationRules = cloneValue(region.validationRules)
    section.validation_rules = cloneValue(region.validationRules)
  } else {
    delete section.validationRules
    delete section.validation_rules
  }

  if (Array.isArray(region.lookupColumns)) {
    section.lookupColumns = cloneValue(region.lookupColumns)
    section.lookup_columns = cloneValue(region.lookupColumns)
  } else {
    delete section.lookupColumns
    delete section.lookup_columns
  }

  if (Array.isArray(region.relatedFields)) {
    section.relatedFields = cloneValue(region.relatedFields)
    section.related_fields = cloneValue(region.relatedFields)
  } else {
    delete section.relatedFields
    delete section.related_fields
  }
}

export const applyDetailRegionPreset = (
  section: LayoutSection,
  option?: DesignerDetailRegionOption | null
): void => {
  const preset = option?.preset
  if (!preset) return

  if (preset.position) {
    section.position = preset.position
  }
  if (typeof preset.collapsible === 'boolean') {
    section.collapsible = preset.collapsible
  }
  if (typeof preset.collapsed === 'boolean') {
    section.collapsed = preset.collapsed
  }

  const detailEditMode = String(preset.detailEditMode || '').trim()
  if (detailEditMode) {
    section.detailEditMode = detailEditMode
    section.detail_edit_mode = detailEditMode
  }

  if (preset.toolbarConfig && typeof preset.toolbarConfig === 'object') {
    section.toolbarConfig = cloneValue(preset.toolbarConfig)
    section.toolbar_config = cloneValue(preset.toolbarConfig)
  }

  if (Array.isArray(preset.summaryRules)) {
    section.summaryRules = cloneValue(preset.summaryRules)
    section.summary_rules = cloneValue(preset.summaryRules)
  }

  if (Array.isArray(preset.validationRules)) {
    section.validationRules = cloneValue(preset.validationRules)
    section.validation_rules = cloneValue(preset.validationRules)
  }

  if (Array.isArray(preset.lookupColumns)) {
    section.lookupColumns = cloneValue(preset.lookupColumns)
    section.lookup_columns = cloneValue(preset.lookupColumns)
  }

  if (Array.isArray(preset.relatedFields)) {
    section.relatedFields = cloneValue(preset.relatedFields)
    section.related_fields = cloneValue(preset.relatedFields)
  }
}
