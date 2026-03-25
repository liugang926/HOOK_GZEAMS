import { describe, expect, it } from 'vitest'
import { getCanvasPlacementAttrs, placeCanvasFields, toCanvasGridStyle } from './canvasLayout'

describe('canvasLayout', () => {
  it('places fields with rowSpan using grid occupancy and keeps deterministic order', () => {
    const placed = placeCanvasFields(
      [
        { code: 'left_tall', span: 1, minHeight: 112 },
        { code: 'right_top', span: 1 },
        { code: 'full', span: 2 }
      ],
      2,
      { baseRowHeight: 56 }
    )

    expect(placed.map((item: any) => item.code)).toEqual(['left_tall', 'right_top', 'full'])
    expect(placed.map((item: any) => item.placement.row)).toEqual([1, 1, 3])
    expect(placed.map((item: any) => item.placement.colStart)).toEqual([1, 2, 1])
    expect(placed.map((item: any) => item.placement.rowSpan)).toEqual([2, 1, 1])
    expect(placed.map((item: any) => item.placement.totalRows)).toEqual([3, 3, 3])
  })

  it('emits canvas ratios and data attributes for debug/stable rendering hooks', () => {
    const [field] = placeCanvasFields([{ code: 'f1', span: 1 }], 2)
    const attrs = getCanvasPlacementAttrs(field.placement)
    const style = toCanvasGridStyle(field.placement)

    expect(field.placement.canvas).toEqual({
      x: 0,
      y: 0,
      width: 0.5,
      height: 1
    })
    expect(attrs['data-canvas-width']).toBe('0.5')
    expect(attrs['data-grid-total-rows']).toBe('1')
    expect(style).toEqual({
      gridColumn: '1 / span 1',
      gridRow: '1 / span 1'
    })
  })

  it('prefers saved placement when configured and valid', () => {
    const placed = placeCanvasFields(
      [
        {
          code: 'right_first',
          span: 1,
          layoutPlacement: { row: 1, colStart: 2, colSpan: 1, rowSpan: 1 }
        },
        {
          code: 'left_second',
          span: 1
        }
      ],
      2,
      { preferSavedPlacement: true }
    )

    expect((placed[0] as any).placement.row).toBe(1)
    expect((placed[0] as any).placement.colStart).toBe(2)
    expect((placed[1] as any).placement.colStart).toBe(1)
  })
})
