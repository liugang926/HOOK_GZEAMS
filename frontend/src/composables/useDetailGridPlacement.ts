import { unref, type MaybeRef } from 'vue'
import { getCanvasPlacementAttrs, toCanvasGridStyle, type CanvasPlacement } from '@/platform/layout/canvasLayout'
import { normalizeColumnSpan } from '@/platform/layout/semanticGrid'

interface GridPlacementCanvas {
  x?: number
  y?: number
  width?: number
  height?: number
}

interface GridPlacementPosition {
  row?: number
  colStart?: number
  colSpan?: number
  rowSpan?: number
  columns?: number
  totalRows?: number
  order?: number
  canvas?: GridPlacementCanvas
}

interface GridPlacementField {
  span?: number
  fullWidth?: boolean
  minHeight?: number
  labelWidth?: string | number
  labelPosition?: 'left' | 'top'
  placement?: GridPlacementPosition | null
}

interface GridPlacementTab {
  fields?: GridPlacementField[]
}

interface GridPlacementSection {
  position?: 'main' | 'sidebar'
  fields?: GridPlacementField[]
  tabs?: GridPlacementTab[]
  labelWidth?: string | number
  labelPosition?: 'left' | 'top'
}

export function useDetailGridPlacement(props: { fieldSpan?: MaybeRef<number | undefined> }) {
  const getDetailSectionColumns = (section: GridPlacementSection): number => {
    if (section.position === 'sidebar') return 1

    const candidates: GridPlacementField[] = []
    candidates.push(...(section.fields || []))
    for (const tab of section.tabs || []) candidates.push(...(tab.fields || []))

    for (const field of candidates) {
      const placement = field?.placement as GridPlacementPosition | undefined
      const columns = Number(placement?.columns)
      if (Number.isFinite(columns) && columns > 0) {
        return Math.round(columns)
      }
    }
    return 2
  }

  const getSectionCanvasStyle = (section: GridPlacementSection): Record<string, string> => {
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
    field: GridPlacementField,
    section: GridPlacementSection
  ): Record<string, string> => {
    if ((field as any).fullWidth) {
      return { gridColumn: '1 / -1' }
    }

    if (field?.placement) {
      const placement = field.placement as CanvasPlacement
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

  const getFieldItemStyle = (field: GridPlacementField): Record<string, string> => {
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

  const getFieldItemClass = (field: GridPlacementField, section?: GridPlacementSection): string[] => {
    const classes = []
    const fieldPos = (field as any).labelPosition
    const sectionPos = section ? (section as any).labelPosition : undefined
    
    if (fieldPos === 'top' || (!fieldPos && sectionPos === 'top')) {
      classes.push('label-position-top')
    }
    return classes
  }

  const getFieldPlacementAttrs = (field: GridPlacementField): Record<string, string> => {
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

