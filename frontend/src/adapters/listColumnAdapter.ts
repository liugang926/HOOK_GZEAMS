import type { TableColumn } from '@/types/common'
import { normalizeFieldType } from '@/utils/fieldType'
import { buildFieldKeyCandidates } from '@/utils/fieldKey'

const resolveFieldCode = (entry: any): string => {
  return entry?.fieldCode || entry?.field_code || entry?.prop || entry?.code || entry?.field || ''
}

export const buildColumnsFromLayout = (columns: any[], fields: any[] = []): TableColumn[] => {
  const fieldMap = new Map<string, any>()
  fields.forEach((field) => {
    const code = field.code || field.fieldName || field.fieldCode || field.field_code
    if (!code) return
    buildFieldKeyCandidates(String(code)).forEach((key) => fieldMap.set(key, field))
  })

  return (columns || [])
    .map((col: any) => {
      const fieldCode = resolveFieldCode(col)
      if (!fieldCode) return null

      const fieldMeta = buildFieldKeyCandidates(fieldCode)
        .map((key) => fieldMap.get(key))
        .find(Boolean)
      const label = col.label || col.title || fieldMeta?.name || fieldMeta?.label || fieldCode
      const type = normalizeFieldType(col.type || col.fieldType || fieldMeta?.fieldType || 'text')
      const options = col.options || fieldMeta?.options || fieldMeta?.choices || []
      const slotName = col.slot || (col.requiresSlot ? fieldCode : null)

      return {
        prop: fieldCode,
        fieldCode,
        label,
        type,
        fieldType: type,
        options,
        width: col.width,
        minWidth: col.minWidth,
        align: col.align,
        fixed: col.fixed,
        sortable: col.sortable !== false,
        visible: col.visible !== false,
        slot: slotName
      } as TableColumn
    })
    .filter(Boolean) as TableColumn[]
}
