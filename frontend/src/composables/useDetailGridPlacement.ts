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
    const styles: Record<string, string> = {
      '--detail-section-columns': String(getDetailSectionColumns(section))
    }
    if ((section as any).labelPosition === 'top') {
      styles['--section-label-position'] = 'top'
    }
    if ((section as any).labelWidth) {
      const width = (section as any).labelWidth
      styles['--section-label-width'] = typeof width === 'number' ? `${width}px` : width
    }
    return styles
  }

  const getFieldColStyle = (
    field: DetailField,
    section: DetailSection
  ): Record<string, string> => {
    if ((field as any).fullWidth) {
      return { gridColumn: '1 / -1' }
    }

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
    const styles: Record<string, string> = {}
    const minHeight = Number(field?.minHeight)
    if (Number.isFinite(minHeight) && minHeight > 0) {
      styles.minHeight = `${Math.round(minHeight)}px`
    }
    
    if ((field as any).labelWidth) {
      const width = (field as any).labelWidth
      styles['--field-label-width'] = typeof width === 'number' ? `${width}px` : width
    } else {
      styles['--field-label-width'] = 'var(--section-label-width, var(--detail-label-width))'
    }
    return styles
  }

  const getFieldItemClass = (field: DetailField, section?: DetailSection): string[] => {
    const classes = []
    const fieldPos = (field as any).labelPosition
    const sectionPos = section ? (section as any).labelPosition : undefined
    
    if (fieldPos === 'top' || (!fieldPos && sectionPos === 'top')) {
      classes.push('label-position-top')
    }
    return classes
  }

  const getFieldPlacementAttrs = (field: DetailField): Record<string, string> => {
    return getCanvasPlacementAttrs(field?.placement as CanvasPlacement | undefined)
  }

  return {
    getSectionCanvasStyle,
    getFieldColStyle,
    getFieldItemStyle,
    getFieldItemClass,
    getFieldPlacementAttrs
  }
}

