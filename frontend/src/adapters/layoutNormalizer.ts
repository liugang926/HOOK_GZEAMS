import { normalizeFieldType } from '@/utils/fieldType'

type AnyRecord = Record<string, any>

const generateLabelFromCode = (code: string): string => {
  if (!code) return ''
  return code
    .split('_')
    .filter(Boolean)
    .map(word => word.charAt(0).toUpperCase() + word.slice(1))
    .join(' ')
}

export const normalizeSpan = (span: any, columns: number): number => {
  const colCount = Number(columns) || 2
  const value = Number(span)

  if (!Number.isFinite(value) || value <= 0) return 1

  // If already within column count, treat as grid-based span.
  if (value <= colCount) return Math.max(1, Math.floor(value))

  // Otherwise, map legacy 24-grid spans to column-based spans.
  if (value <= 24) {
    const unit = 24 / colCount
    const normalized = Math.ceil(value / unit)
    return Math.min(colCount, Math.max(1, normalized))
  }

  return colCount
}

const normalizeField = (field: any): AnyRecord => {
  if (!field) return field

  if (typeof field === 'string') {
    const code = field
    return {
      id: `field_${code}_${Date.now()}`,
      fieldCode: code,
      label: generateLabelFromCode(code),
      span: 1,
      readonly: false,
      visible: true,
      required: false
    }
  }

  if (field.fieldCode) {
    const fieldCode = String(field.fieldCode || '')
    return {
      ...field,
      id: field.id || (fieldCode ? `field_${fieldCode}_${Date.now()}` : field.id),
      label: field.label || field.name || generateLabelFromCode(field.fieldCode),
      span: field.span ?? 1,
      visible: field.visible !== false,
      fieldType: field.fieldType ? normalizeFieldType(field.fieldType) : field.fieldType
    }
  }

  const fieldCode = field.field || field.code || field.prop || field.name || ''
  const label = field.label || field.name || generateLabelFromCode(fieldCode)
  const rawType = field.fieldType || field.type || field.field_type

  return {
    ...field,
    id: field.id || (fieldCode ? `field_${fieldCode}_${Date.now()}` : field.id),
    fieldCode,
    label,
    span: field.span ?? 1,
    readonly: field.readonly || false,
    visible: field.visible !== false,
    required: field.required || false,
    placeholder: field.placeholder,
    defaultValue: field.defaultValue,
    helpText: field.helpText,
    fieldType: rawType ? normalizeFieldType(rawType) : field.fieldType
  }
}

const normalizeSectionColumns = (section: AnyRecord): number => {
  return Number(section.columns || section.columnCount || section.column || 2) || 2
}

const normalizeFieldWithColumns = (field: any, columns: number): AnyRecord => {
  const normalized = normalizeField(field)
  return {
    ...normalized,
    span: normalizeSpan(normalized?.span ?? 1, columns)
  }
}

export const normalizeLayoutConfig = <T extends AnyRecord>(config: T): T => {
  if (!config || !config.sections) return config

  const sections = (config.sections || []).map((section: AnyRecord) => {
    const sectionType = section.type || 'section'
    const columns = sectionType === 'detail-region' ? 1 : normalizeSectionColumns(section)

    if (sectionType === 'tab') {
      return {
        ...section,
        type: sectionType,
        columns,
        tabs: (section.tabs || []).map((tab: AnyRecord) => ({
          ...tab,
          fields: (tab.fields || []).map((field: AnyRecord) => normalizeFieldWithColumns(field, columns))
        }))
      }
    }

    if (sectionType === 'collapse') {
      return {
        ...section,
        type: sectionType,
        columns,
        items: (section.items || []).map((item: AnyRecord) => ({
          ...item,
          fields: (item.fields || []).map((field: AnyRecord) => normalizeFieldWithColumns(field, columns))
        }))
      }
    }

    if (sectionType === 'detail-region') {
      return {
        ...section,
        type: sectionType,
        columns,
        relationCode: section.relationCode || section.relation_code,
        relation_code: section.relationCode || section.relation_code,
        fieldCode: section.fieldCode || section.field_code,
        field_code: section.fieldCode || section.field_code,
        targetObjectCode: section.targetObjectCode || section.target_object_code,
        target_object_code: section.targetObjectCode || section.target_object_code,
        detailEditMode: section.detailEditMode || section.detail_edit_mode,
        detail_edit_mode: section.detailEditMode || section.detail_edit_mode,
        toolbarConfig: section.toolbarConfig || section.toolbar_config,
        toolbar_config: section.toolbarConfig || section.toolbar_config,
        summaryRules: section.summaryRules || section.summary_rules,
        summary_rules: section.summaryRules || section.summary_rules,
        validationRules: section.validationRules || section.validation_rules,
        validation_rules: section.validationRules || section.validation_rules
      }
    }

    return {
      ...section,
      type: sectionType,
      columns,
      fields: (section.fields || []).map((field: AnyRecord) => normalizeFieldWithColumns(field, columns))
    }
  })

  return {
    ...config,
    sections
  }
}
