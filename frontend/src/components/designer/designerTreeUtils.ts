import type {
  DesignerConfigNode,
  LayoutConfig,
  LayoutField,
  LayoutSection
} from '@/components/designer/designerTypes'

export function findDesignerNodeById(config: LayoutConfig, id: string): DesignerConfigNode | null {
  for (const section of config.sections || []) {
    if (section.id === id) return section
    if (section.type === 'tab') {
      for (const tab of section.tabs || []) {
        if (tab.id === id) return tab
        for (const field of tab.fields || []) {
          if (field.id === id) return field
        }
      }
    } else if (section.type === 'collapse') {
      for (const item of section.items || []) {
        if (item.id === id) return item
        for (const field of item.fields || []) {
          if (field.id === id) return field
        }
      }
    } else {
      for (const field of section.fields || []) {
        if (field.id === id) return field
      }
    }
  }
  return null
}

export function findSectionByFieldId(config: LayoutConfig, fieldId: string): LayoutSection | null {
  for (const section of config.sections || []) {
    if (section.type === 'tab') {
      for (const tab of section.tabs || []) {
        if ((tab.fields || []).some((field) => field?.id === fieldId)) return section
      }
      continue
    }
    if (section.type === 'collapse') {
      for (const item of section.items || []) {
        if ((item.fields || []).some((field) => field?.id === fieldId)) return section
      }
      continue
    }
    if ((section.fields || []).some((field) => field?.id === fieldId)) return section
  }
  return null
}

export function findLayoutFieldById(config: LayoutConfig, fieldId: string): LayoutField | null {
  const item = findDesignerNodeById(config, fieldId)
  if (!item || !('fieldCode' in item)) return null
  return item as LayoutField
}

export function collectAddedFieldCodes(config: LayoutConfig): string[] {
  const codes: string[] = []
  for (const section of config.sections || []) {
    if (section.type === 'tab') {
      for (const tab of section.tabs || []) {
        for (const field of tab.fields || []) {
          codes.push(field.fieldCode)
        }
      }
    } else if (section.type === 'collapse') {
      for (const item of section.items || []) {
        for (const field of item.fields || []) {
          codes.push(field.fieldCode)
        }
      }
    } else if (section.type === 'detail-region') {
      const code = String(section.fieldCode || section.field_code || '').trim()
      if (code) codes.push(code)
    } else {
      for (const field of section.fields || []) {
        codes.push(field.fieldCode)
      }
    }
  }
  return codes
}
