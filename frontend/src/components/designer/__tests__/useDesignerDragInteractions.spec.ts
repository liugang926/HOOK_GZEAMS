import { describe, expect, it, vi } from 'vitest'
import {
  applyDesignerInsertIndicator,
  clearDesignerDragMarkers,
  flashDroppedField
} from '@/components/designer/useDesignerDragInteractions'

describe('useDesignerDragInteractions DOM helpers', () => {
  it('marks insertion before and after on field renderers', () => {
    const root = document.createElement('div')
    root.innerHTML = `
      <div class="designer-fields-container">
        <div class="field-renderer" data-field-id="field_1"></div>
        <div class="field-renderer" data-field-id="field_2"></div>
      </div>
    `

    const fieldOne = root.querySelectorAll('.field-renderer')[0]
    const fieldTwo = root.querySelectorAll('.field-renderer')[1]

    applyDesignerInsertIndicator(root, fieldOne, false)
    expect(fieldOne.classList.contains('drag-insert-before')).toBe(true)

    applyDesignerInsertIndicator(root, fieldTwo, true)
    expect(fieldOne.classList.contains('drag-insert-before')).toBe(false)
    expect(fieldTwo.classList.contains('drag-insert-after')).toBe(true)
  })

  it('marks empty containers as active drop zones', () => {
    const root = document.createElement('div')
    root.innerHTML = `<div class="designer-fields-container"></div>`

    const container = root.querySelector('.designer-fields-container')
    applyDesignerInsertIndicator(root, container, false)

    expect(container?.classList.contains('drop-zone-active')).toBe(true)

    clearDesignerDragMarkers(root)
    expect(container?.classList.contains('drop-zone-active')).toBe(false)
  })

  it('flashes dropped field class and clears it after timeout', () => {
    vi.useFakeTimers()

    const root = document.createElement('div')
    root.innerHTML = `<div class="field-renderer" data-field-id="field_9"></div>`
    const field = root.querySelector('.field-renderer') as HTMLElement

    flashDroppedField(root, 'field_9', 200)
    expect(field.classList.contains('field-just-dropped')).toBe(true)

    vi.advanceTimersByTime(250)
    expect(field.classList.contains('field-just-dropped')).toBe(false)

    vi.useRealTimers()
  })
})
