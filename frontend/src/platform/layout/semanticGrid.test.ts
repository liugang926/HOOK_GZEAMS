import { describe, expect, it } from 'vitest'
import { normalizeColumnSpan, normalizeGridColumns, normalizeGridSpan24, placeGridFields } from './semanticGrid'

describe('semanticGrid', () => {
  it('normalizes columns and spans from semantic/legacy values', () => {
    expect(normalizeGridColumns(undefined)).toBe(2)
    expect(normalizeGridColumns(3)).toBe(3)

    expect(normalizeColumnSpan(1, 2)).toBe(1)
    expect(normalizeColumnSpan(2, 2)).toBe(2)
    expect(normalizeColumnSpan(12, 2)).toBe(1)
    expect(normalizeColumnSpan(24, 2)).toBe(2)

    expect(normalizeGridSpan24(1, 2)).toBe(12)
    expect(normalizeGridSpan24(2, 2)).toBe(24)
    expect(normalizeGridSpan24(12, 2)).toBe(12)
  })

  it('places fields deterministically by row and column', () => {
    const placed = placeGridFields(
      [
        { span: 1, code: 'left' },
        { span: 1, code: 'right' },
        { span: 2, code: 'full' },
        { span: 1, code: 'next' }
      ],
      2
    )

    expect(placed.map((item) => item.code)).toEqual(['left', 'right', 'full', 'next'])
    expect(placed.map((item) => item.placement)).toEqual([
      { row: 1, colStart: 1, colSpan: 1, columns: 2, order: 1 },
      { row: 1, colStart: 2, colSpan: 1, columns: 2, order: 2 },
      { row: 2, colStart: 1, colSpan: 2, columns: 2, order: 3 },
      { row: 3, colStart: 1, colSpan: 1, columns: 2, order: 4 }
    ])
  })
})
