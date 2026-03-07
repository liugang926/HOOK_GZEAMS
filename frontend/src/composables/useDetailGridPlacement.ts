import { unref, type MaybeRef } from 'vue'
import { getCanvasPlacementAttrs, toCanvasGridStyle, type CanvasPlacement } from '@/platform/layout/canvasLayout'
import { normalizeColumnSpan } from '@/platform/layout/semanticGrid'
import type { DetailField, DetailSection } from '../components/common/BaseDetailPage.vue'

export function useDetailGridPlacement(props: { fieldSpan?: MaybeRef<number | undefined> }) {
  const getDetailSectionColumns = (section: DetailSection): number => {
    if (section.position === 'sidebar') return 1

    const candidates: DetailField[] = []
    candidates.push(...(section.fields || []))
    for (const tab of section.tabs || []) candidates.push(...(tab.fields || []))

    for (const field of candidates) {
      const placement = field?.placement as DetailField['placement'] | undefined
      const columns = Number(placement?.columns)
      if (Number.isFinite(columns) && columns > 0) {
        return Math.round(columns)
      }
    }
    return 2
  }

  const getSectionCanvasStyle = (section: DetailSection): Record<string, string> => {
    return {
      '--detail-section-columns': String(getDetailSectionColumns(section))
    }
  }

  const getFieldColStyle = (
    field: DetailField,
    section: DetailSection
  ): Record<string, string> => {
    const placement = field?.placement as CanvasPlacement | undefined
    if (placement) {
      return toCanvasGridStyle(placement)
    }

    const columns = getDetailSectionColumns(section)
    const defaultFieldSpan = unref(props.fieldSpan)
    const colSpan = section.position === 'sidebar'
      ? 1
      : normalizeColumnSpan(field?.span ?? defaultFieldSpan, columns)
    return {
      gridColumn: `span ${colSpan}`
    }
  }

  const getFieldItemStyle = (field: DetailField): Record<string, string> => {
    const minHeight = Number(field?.minHeight)
    if (!Number.isFinite(minHeight) || minHeight <= 0) return {}
    return { minHeight: `${Math.round(minHeight)}px` }
  }

  const getFieldPlacementAttrs = (field: DetailField): Record<string, string> => {
    return getCanvasPlacementAttrs(field?.placement as CanvasPlacement | undefined)
  }

  return {
    getSectionCanvasStyle,
    getFieldColStyle,
    getFieldItemStyle,
    getFieldPlacementAttrs
  }
}

