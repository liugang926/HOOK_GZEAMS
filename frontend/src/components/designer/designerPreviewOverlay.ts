import { cloneLayoutConfig } from '@/utils/layoutValidation'
import type { DesignerDetailRegionOption, LayoutConfig, LayoutSection } from '@/components/designer/designerTypes'

export interface DesignerSectionPreviewOverlay {
  sectionId: string
  value: Partial<LayoutSection>
}

export const applyDesignerSectionPreviewOverlay = (
  layoutConfig: LayoutConfig,
  overlay: DesignerSectionPreviewOverlay | null | undefined
): LayoutConfig => {
  if (!overlay?.sectionId || !overlay.value) return layoutConfig

  const sections = layoutConfig.sections || []
  if (!sections.some((section) => section.id === overlay.sectionId)) {
    return layoutConfig
  }

  const next = cloneLayoutConfig(layoutConfig || { sections: [] }) as LayoutConfig
  next.sections = (next.sections || []).map((section) => {
    if (section.id !== overlay.sectionId) return section
    return {
      ...section,
      ...overlay.value,
      id: section.id
    }
  })
  return next
}

export const resolveDetailRegionPreviewSectionId = (
  layoutConfig: LayoutConfig,
  region: Pick<DesignerDetailRegionOption, 'relationCode' | 'fieldCode'>,
  preferredSectionId?: string | null
): string | null => {
  const sections = layoutConfig.sections || []
  const relationCode = String(region.relationCode || '').trim()
  const fieldCode = String(region.fieldCode || '').trim()

  const matchesRegion = (section: LayoutSection): boolean => {
    if (String(section.type || '') !== 'detail-region') return false

    const sectionRelationCode = String(section.relationCode || section.relation_code || '').trim()
    const sectionFieldCode = String(section.fieldCode || section.field_code || '').trim()

    if (relationCode && sectionRelationCode === relationCode) return true
    if (fieldCode && sectionFieldCode === fieldCode) return true
    return false
  }

  if (preferredSectionId) {
    const preferred = sections.find((section) => section.id === preferredSectionId)
    if (preferred && matchesRegion(preferred)) {
      return preferred.id
    }
  }

  return sections.find(matchesRegion)?.id || null
}
