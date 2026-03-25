export interface GridPlacement {
  row: number
  colStart: number
  colSpan: number
  columns: number
  order: number
}

export interface GridFieldLike {
  span?: number
}

export const normalizeGridColumns = (rawColumns: unknown): number => {
  const columns = Number(rawColumns)
  if (!Number.isFinite(columns) || columns <= 0) return 2
  return Math.max(1, Math.round(columns))
}

/**
 * Normalize field span to semantic column units (1..columns).
 * Supports both semantic spans (<= columns) and legacy 24-grid spans.
 */
export const normalizeColumnSpan = (rawSpan: unknown, rawColumns: unknown): number => {
  const columns = normalizeGridColumns(rawColumns)
  const span = Number(rawSpan)

  if (!Number.isFinite(span) || span <= 0) return 1
  if (span <= columns) return Math.max(1, Math.min(columns, Math.round(span)))
  if (span <= 24) {
    const unit = 24 / columns
    return Math.max(1, Math.min(columns, Math.ceil(span / unit)))
  }
  return columns
}

/**
 * Convert semantic/legacy span to ElementPlus 24-grid span.
 */
export const normalizeGridSpan24 = (rawSpan: unknown, rawColumns: unknown): number => {
  const columns = normalizeGridColumns(rawColumns)
  const colSpan = normalizeColumnSpan(rawSpan, columns)
  return Math.max(1, Math.min(24, Math.round((24 / columns) * colSpan)))
}

/**
 * Deterministically place fields on a semantic grid for diagnostics and consistency checks.
 */
export const placeGridFields = <T extends GridFieldLike>(
  fields: T[],
  rawColumns: unknown
): Array<T & { placement: GridPlacement }> => {
  const columns = normalizeGridColumns(rawColumns)
  const out: Array<T & { placement: GridPlacement }> = []
  let row = 1
  let colCursor = 1

  for (let index = 0; index < (fields || []).length; index += 1) {
    const field = fields[index]
    const colSpan = normalizeColumnSpan(field?.span ?? 1, columns)
    if (colCursor + colSpan - 1 > columns) {
      row += 1
      colCursor = 1
    }

    const placement: GridPlacement = {
      row,
      colStart: colCursor,
      colSpan,
      columns,
      order: index + 1
    }

    out.push({
      ...field,
      placement
    })

    colCursor += colSpan
    if (colCursor > columns) {
      row += 1
      colCursor = 1
    }
  }

  return out
}
