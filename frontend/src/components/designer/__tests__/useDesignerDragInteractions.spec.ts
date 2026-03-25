import { computed, ref } from 'vue'
import { describe, expect, it, vi } from 'vitest'
import {
  applyDesignerSectionInsertIndicator,
  applyDesignerInsertIndicator,
  clearDesignerDragMarkers,
  flashDroppedField,
  useDesignerDragInteractions
} from '@/components/designer/useDesignerDragInteractions'
import type { DesignerDetailRegionOption, LayoutConfig } from '@/components/designer/designerTypes'

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

  it('marks section insert indicators for detail-region placement', () => {
    const root = document.createElement('div')
    root.innerHTML = `
      <div class="designer-section-slot" data-section-id="section_1"></div>
      <div class="designer-section-slot" data-section-id="section_2"></div>
    `

    const sectionOne = root.querySelectorAll('.designer-section-slot')[0]
    const sectionTwo = root.querySelectorAll('.designer-section-slot')[1]

    applyDesignerSectionInsertIndicator(root, sectionOne, false)
    expect(sectionOne.classList.contains('drag-section-insert-before')).toBe(true)

    applyDesignerSectionInsertIndicator(root, sectionTwo, true)
    expect(sectionOne.classList.contains('drag-section-insert-before')).toBe(false)
    expect(sectionTwo.classList.contains('drag-section-insert-after')).toBe(true)
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

  it('inserts detail-region before the hovered section when dropped in the upper half', () => {
    const layoutConfig = ref<LayoutConfig>({
      sections: [
        { id: 'section_1', type: 'section', fields: [] },
        { id: 'section_2', type: 'section', fields: [] }
      ]
    })
    const draggedField = ref(null)
    const draggedDetailRegion = ref<DesignerDetailRegionOption | null>(null)
    const draggedSectionId = ref<string | null>(null)
    const isDragOverCanvas = ref(false)
    const dragOverSection = ref<string | null>(null)
    const addDetailRegion = vi.fn()

    const { handleSectionDrop } = useDesignerDragInteractions({
      layoutConfig,
      renderMode: ref('design'),
      draggedField,
      draggedDetailRegion,
      draggedSectionId,
      isDragOverCanvas,
      dragOverSection,
      canvasContentElement: computed(() => document.createElement('div')),
      canAddField: () => true,
      notifyUnsupportedField: vi.fn(),
      handleFieldClick: vi.fn(),
      addSectionTemplate: vi.fn(),
      addDetailRegion,
      moveSectionToIndex: vi.fn(),
      addFieldToContainer: vi.fn(),
      commitLayoutChange: vi.fn()
    })

    const sectionSlot = document.createElement('div')
    sectionSlot.className = 'designer-section-slot'
    sectionSlot.dataset.sectionId = 'section_2'
    sectionSlot.getBoundingClientRect = () =>
      ({
        top: 100,
        height: 80
      } as DOMRect)

    const event = {
      currentTarget: sectionSlot,
      target: sectionSlot,
      clientY: 110,
      dataTransfer: {
        types: ['detail-region'],
        getData: (type: string) =>
          type === 'detail-region'
            ? JSON.stringify({
                templateCode: 'pickup_items:default',
                relationCode: 'pickup_items',
                fieldCode: 'items',
                title: 'Pickup Items',
                targetObjectCode: 'PickupItem',
                targetObjectLabel: 'Pickup Item',
                preset: {
                  detailEditMode: 'inline_table',
                  collapsible: true
                }
              })
            : ''
      },
      preventDefault: vi.fn(),
      stopPropagation: vi.fn()
    } as unknown as DragEvent

    handleSectionDrop(event)

    expect(addDetailRegion).toHaveBeenCalledWith(
      expect.objectContaining({
        templateCode: 'pickup_items:default',
        relationCode: 'pickup_items',
        preset: {
          detailEditMode: 'inline_table',
          collapsible: true
        }
      }),
      { insertIndex: 1 }
    )
  })

  it('moves a dragged section before the hovered section when dropped in the upper half', () => {
    const layoutConfig = ref<LayoutConfig>({
      sections: [
        { id: 'section_1', type: 'section', fields: [] },
        { id: 'section_2', type: 'section', fields: [] },
        { id: 'section_3', type: 'section', fields: [] }
      ]
    })
    const draggedField = ref(null)
    const draggedDetailRegion = ref<DesignerDetailRegionOption | null>(null)
    const draggedSectionId = ref<string | null>(null)
    const isDragOverCanvas = ref(false)
    const dragOverSection = ref<string | null>(null)
    const moveSectionToIndex = vi.fn()

    const { handleSectionDrop } = useDesignerDragInteractions({
      layoutConfig,
      renderMode: ref('design'),
      draggedField,
      draggedDetailRegion,
      draggedSectionId,
      isDragOverCanvas,
      dragOverSection,
      canvasContentElement: computed(() => document.createElement('div')),
      canAddField: () => true,
      notifyUnsupportedField: vi.fn(),
      handleFieldClick: vi.fn(),
      addSectionTemplate: vi.fn(),
      addDetailRegion: vi.fn(),
      moveSectionToIndex,
      addFieldToContainer: vi.fn(),
      commitLayoutChange: vi.fn()
    })

    const sectionSlot = document.createElement('div')
    sectionSlot.className = 'designer-section-slot'
    sectionSlot.dataset.sectionId = 'section_3'
    sectionSlot.getBoundingClientRect = () =>
      ({
        top: 200,
        height: 80
      } as DOMRect)

    const event = {
      currentTarget: sectionSlot,
      target: sectionSlot,
      clientY: 210,
      dataTransfer: {
        types: ['layout-section'],
        getData: (type: string) => (type === 'layout-section' ? 'section_1' : '')
      },
      preventDefault: vi.fn(),
      stopPropagation: vi.fn()
    } as unknown as DragEvent

    handleSectionDrop(event)

    expect(moveSectionToIndex).toHaveBeenCalledWith('section_1', { insertIndex: 2 })
  })

  it('moves a dragged section to the end when dropped on the canvas shell', () => {
    const layoutConfig = ref<LayoutConfig>({
      sections: [
        { id: 'section_1', type: 'section', fields: [] },
        { id: 'section_2', type: 'section', fields: [] }
      ]
    })
    const draggedField = ref(null)
    const draggedDetailRegion = ref<DesignerDetailRegionOption | null>(null)
    const draggedSectionId = ref<string | null>(null)
    const isDragOverCanvas = ref(false)
    const dragOverSection = ref<string | null>(null)
    const moveSectionToIndex = vi.fn()

    const { handleCanvasDrop } = useDesignerDragInteractions({
      layoutConfig,
      renderMode: ref('design'),
      draggedField,
      draggedDetailRegion,
      draggedSectionId,
      isDragOverCanvas,
      dragOverSection,
      canvasContentElement: computed(() => document.createElement('div')),
      canAddField: () => true,
      notifyUnsupportedField: vi.fn(),
      handleFieldClick: vi.fn(),
      addSectionTemplate: vi.fn(),
      addDetailRegion: vi.fn(),
      moveSectionToIndex,
      addFieldToContainer: vi.fn(),
      commitLayoutChange: vi.fn()
    })

    const event = {
      dataTransfer: {
        getData: (type: string) => (type === 'layout-section' ? 'section_1' : '')
      },
      preventDefault: vi.fn()
    } as unknown as DragEvent

    handleCanvasDrop(event)

    expect(moveSectionToIndex).toHaveBeenCalledWith('section_1', { insertIndex: 2 })
  })

  it('inserts a section template before the hovered section when dropped in the upper half', () => {
    const layoutConfig = ref<LayoutConfig>({
      sections: [
        { id: 'section_1', type: 'section', fields: [] },
        { id: 'section_2', type: 'section', fields: [] }
      ]
    })
    const draggedField = ref(null)
    const draggedDetailRegion = ref<DesignerDetailRegionOption | null>(null)
    const draggedSectionId = ref<string | null>(null)
    const isDragOverCanvas = ref(false)
    const dragOverSection = ref<string | null>(null)
    const addSectionTemplate = vi.fn()

    const { handleSectionDrop } = useDesignerDragInteractions({
      layoutConfig,
      renderMode: ref('design'),
      draggedField,
      draggedDetailRegion,
      draggedSectionId,
      isDragOverCanvas,
      dragOverSection,
      canvasContentElement: computed(() => document.createElement('div')),
      canAddField: () => true,
      notifyUnsupportedField: vi.fn(),
      handleFieldClick: vi.fn(),
      addSectionTemplate,
      addDetailRegion: vi.fn(),
      moveSectionToIndex: vi.fn(),
      addFieldToContainer: vi.fn(),
      commitLayoutChange: vi.fn()
    })

    const sectionSlot = document.createElement('div')
    sectionSlot.className = 'designer-section-slot'
    sectionSlot.dataset.sectionId = 'section_2'
    sectionSlot.getBoundingClientRect = () =>
      ({
        top: 100,
        height: 80
      } as DOMRect)

    const event = {
      currentTarget: sectionSlot,
      target: sectionSlot,
      clientY: 110,
      dataTransfer: {
        types: ['layout-section-template'],
        getData: (type: string) =>
          type === 'layout-section-template'
            ? JSON.stringify({
                templateCode: 'collapse-main',
                templateType: 'collapse',
                title: 'Collapsible Group',
                icon: 'collapse',
                preset: {
                  position: 'main',
                  columns: 2,
                  collapsible: true
                }
              })
            : ''
      },
      preventDefault: vi.fn(),
      stopPropagation: vi.fn()
    } as unknown as DragEvent

    handleSectionDrop(event)

    expect(addSectionTemplate).toHaveBeenCalledWith(
      expect.objectContaining({
        templateCode: 'collapse-main',
        templateType: 'collapse',
        preset: {
          position: 'main',
          columns: 2,
          collapsible: true
        }
      }),
      { insertIndex: 1 }
    )
  })
})
