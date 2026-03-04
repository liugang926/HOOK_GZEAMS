import { normalizeColumnSpan, normalizeGridColumns } from '@/platform/layout/semanticGrid'

export interface CanvasRatio {
  x: number
  y: number
  width: number
  height: number
}

export interface CanvasRatioInput {
  x?: number
  y?: number
  width?: number
  height?: number
}

export interface CanvasPlacement {
  row: number
  colStart: number
  colSpan: number
  rowSpan: number
  columns: number
  totalRows: number
  order: number
  canvas: CanvasRatio
}

export interface CanvasPlacementInput {
  row?: number
  colStart?: number
  colSpan?: number
  rowSpan?: number
  columns?: number
  totalRows?: number
  order?: number
  canvas?: CanvasRatioInput
}

export interface CanvasFieldLike {
  span?: number
  minHeight?: number
  rowSpan?: number
  min_row_span?: number
  placement?: CanvasPlacementInput | null
  layoutPlacement?: CanvasPlacementInput | null
}

export interface PlaceCanvasOptions {
  baseRowHeight?: number
  maxRowSpan?: number
  preferSavedPlacement?: boolean
}

const DEFAULT_BASE_ROW_HEIGHT = 56
const DEFAULT_MAX_ROW_SPAN = 12

const normalizeRatio = (value: number): number => {
  if (!Number.isFinite(value)) return 0
  return Math.round(value * 1000000) / 1000000
}

const resolveRowSpan = (
  field: CanvasFieldLike,
  options: Required<PlaceCanvasOptions>
): number => {
  const explicitSpan = Number(field?.rowSpan ?? field?.min_row_span)
  if (Number.isFinite(explicitSpan) && explicitSpan > 0) {
    return Math.max(1, Math.min(options.maxRowSpan, Math.round(explicitSpan)))
  }

  const minHeight = Number(field?.minHeight)
  if (Number.isFinite(minHeight) && minHeight > 0) {
    return Math.max(1, Math.min(options.maxRowSpan, Math.ceil(minHeight / options.baseRowHeight)))
  }

  return 1
}

const ensureRow = (occupied: boolean[][], row: number, columns: number) => {
  if (!occupied[row]) {
    occupied[row] = new Array(columns + 1).fill(false)
  }
}

const canPlaceAt = (
  occupied: boolean[][],
  row: number,
  colStart: number,
  colSpan: number,
  rowSpan: number,
  columns: number
): boolean => {
  if (colStart <= 0 || colStart + colSpan - 1 > columns) return false

  for (let r = row; r < row + rowSpan; r += 1) {
    ensureRow(occupied, r, columns)
    for (let c = colStart; c < colStart + colSpan; c += 1) {
      if (occupied[r][c]) return false
    }
  }
  return true
}

const markPlacement = (
  occupied: boolean[][],
  row: number,
  colStart: number,
  colSpan: number,
  rowSpan: number,
  columns: number
) => {
  for (let r = row; r < row + rowSpan; r += 1) {
    ensureRow(occupied, r, columns)
    for (let c = colStart; c < colStart + colSpan; c += 1) {
      occupied[r][c] = true
    }
  }
}

export const placeCanvasFields = <T extends CanvasFieldLike>(
  fields: T[],
  rawColumns: unknown,
  options: PlaceCanvasOptions = {}
): Array<T & { placement: CanvasPlacement }> => {
  const columns = normalizeGridColumns(rawColumns)
  const normalizedOptions: Required<PlaceCanvasOptions> = {
    baseRowHeight: Number(options.baseRowHeight) > 0 ? Number(options.baseRowHeight) : DEFAULT_BASE_ROW_HEIGHT,
    maxRowSpan: Number(options.maxRowSpan) > 0 ? Math.round(Number(options.maxRowSpan)) : DEFAULT_MAX_ROW_SPAN,
    preferSavedPlacement: options.preferSavedPlacement === true
  }

  const occupied: boolean[][] = []
  const draft: Array<T & { __placement: Omit<CanvasPlacement, 'totalRows' | 'canvas'> }> = []
  let totalRows = 1

  for (let index = 0; index < (fields || []).length; index += 1) {
    const field = fields[index]
    const colSpan = normalizeColumnSpan(field?.span ?? 1, columns)
    const rowSpan = resolveRowSpan(field, normalizedOptions)

    let placed = false
    let row = 1
    let colStart = 1

    if (normalizedOptions.preferSavedPlacement) {
      const saved = (field?.layoutPlacement || field?.placement || null) as CanvasPlacementInput | null
      const savedRow = Number(saved?.row)
      const savedColStart = Number((saved as any)?.colStart ?? (saved as any)?.col_start)
      const savedColSpan = Number((saved as any)?.colSpan ?? (saved as any)?.col_span)
      const savedRowSpan = Number((saved as any)?.rowSpan ?? (saved as any)?.row_span)
      const normalizedSavedColSpan = Number.isFinite(savedColSpan)
        ? normalizeColumnSpan(savedColSpan, columns)
        : colSpan
      const normalizedSavedRowSpan = Number.isFinite(savedRowSpan) && savedRowSpan > 0
        ? Math.max(1, Math.min(normalizedOptions.maxRowSpan, Math.round(savedRowSpan)))
        : rowSpan

      if (
        Number.isFinite(savedRow) &&
        Number.isFinite(savedColStart) &&
        savedRow > 0 &&
        savedColStart > 0 &&
        canPlaceAt(
          occupied,
          Math.round(savedRow),
          Math.round(savedColStart),
          normalizedSavedColSpan,
          normalizedSavedRowSpan,
          columns
        )
      ) {
        row = Math.round(savedRow)
        colStart = Math.round(savedColStart)
        placed = true
        markPlacement(occupied, row, colStart, normalizedSavedColSpan, normalizedSavedRowSpan, columns)
        totalRows = Math.max(totalRows, row + normalizedSavedRowSpan - 1)

        draft.push({
          ...field,
          __placement: {
            row,
            colStart,
            colSpan: normalizedSavedColSpan,
            rowSpan: normalizedSavedRowSpan,
            columns,
            order: index + 1
          }
        })
      }
    }

    if (placed) continue

    while (!placed) {
      for (let col = 1; col <= columns - colSpan + 1; col += 1) {
        if (canPlaceAt(occupied, row, col, colSpan, rowSpan, columns)) {
          colStart = col
          placed = true
          break
        }
      }
      if (!placed) row += 1
    }

    markPlacement(occupied, row, colStart, colSpan, rowSpan, columns)
    totalRows = Math.max(totalRows, row + rowSpan - 1)

    draft.push({
      ...field,
      __placement: {
        row,
        colStart,
        colSpan,
        rowSpan,
        columns,
        order: index + 1
      }
    })
  }

  return draft.map((item) => {
    const p = item.__placement
    const placement: CanvasPlacement = {
      ...p,
      totalRows,
      canvas: {
        x: normalizeRatio((p.colStart - 1) / p.columns),
        y: normalizeRatio((p.row - 1) / totalRows),
        width: normalizeRatio(p.colSpan / p.columns),
        height: normalizeRatio(p.rowSpan / totalRows)
      }
    }

    const { __placement: _placement, ...rest } = item
    return {
      ...(rest as unknown as T),
      placement
    }
  })
}

export const getCanvasPlacementAttrs = (
  placement: CanvasPlacement | null | undefined
): Record<string, string> => {
  if (!placement) return {}
  return {
    'data-grid-row': String(placement.row),
    'data-grid-col-start': String(placement.colStart),
    'data-grid-col-span': String(placement.colSpan),
    'data-grid-row-span': String(placement.rowSpan),
    'data-grid-columns': String(placement.columns),
    'data-grid-total-rows': String(placement.totalRows),
    'data-grid-order': String(placement.order),
    'data-canvas-x': String(placement.canvas.x),
    'data-canvas-y': String(placement.canvas.y),
    'data-canvas-width': String(placement.canvas.width),
    'data-canvas-height': String(placement.canvas.height)
  }
}

export const toCanvasGridStyle = (
  placement: CanvasPlacement | null | undefined
): Record<string, string> => {
  if (!placement) return {}
  return {
    gridColumn: `${placement.colStart} / span ${placement.colSpan}`,
    gridRow: `${placement.row} / span ${placement.rowSpan}`
  }
}
