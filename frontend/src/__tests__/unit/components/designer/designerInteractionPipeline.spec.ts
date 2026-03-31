import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { nextTick, ref, computed } from 'vue'

const mocks = vi.hoisted(() => ({
  sortableCreate: vi.fn(),
  storageSet: vi.fn()
}))

vi.mock('sortablejs', () => ({
  default: {
    create: mocks.sortableCreate
  }
}))

vi.mock('@/utils/storage', () => ({
  storage: {
    set: mocks.storageSet
  }
}))

describe('designer interaction pipeline', () => {
  beforeEach(() => {
    mocks.sortableCreate.mockReset()
    mocks.storageSet.mockReset()
    document.body.innerHTML = ''
  })

  afterEach(() => {
    vi.useRealTimers()
    document.body.innerHTML = ''
  })

  it('autosaves after commitLayoutChange and seeds initial history baseline', async () => {
    vi.useFakeTimers()
    const { useDesignerChangePipeline } = await import('@/components/designer/useDesignerChangePipeline')

    const layoutConfig = ref({
      sections: [{ id: 'section-1', type: 'section', fields: [] }]
    })
    const historyLength = ref(0)
    const pushHistory = vi.fn((_snapshot, _description) => {
      historyLength.value += 1
    })

    const { commitLayoutChange } = useDesignerChangePipeline({
      objectCode: 'Asset',
      mode: 'edit',
      layoutConfig,
      historyLength,
      pushHistory
    })

    const nextConfig = {
      sections: [
        {
          id: 'section-1',
          type: 'section',
          fields: [{ id: 'field-1', fieldCode: 'asset_name', label: 'Asset name', span: 1 }]
        }
      ]
    }

    commitLayoutChange(nextConfig as any, 'Add asset_name')

    expect(pushHistory).toHaveBeenNthCalledWith(1, { sections: [{ id: 'section-1', type: 'section', fields: [] }] }, 'Initial state')
    expect(pushHistory).toHaveBeenNthCalledWith(2, nextConfig, 'Add asset_name')
    expect(layoutConfig.value).toEqual(nextConfig)

    await vi.advanceTimersByTimeAsync(800)

    expect(mocks.storageSet).toHaveBeenCalledWith('layout_autosave_Asset_edit', nextConfig)
  })

  it('commits moved fields when sortable ends across containers', async () => {
    const { useDesignerDragInteractions } = await import('@/components/designer/useDesignerDragInteractions')

    const root = document.createElement('div')
    const fromContainer = document.createElement('div')
    fromContainer.className = 'designer-fields-container'
    fromContainer.dataset.containerKind = 'section'
    fromContainer.dataset.sectionId = 'section-a'
    const toContainer = document.createElement('div')
    toContainer.className = 'designer-fields-container'
    toContainer.dataset.containerKind = 'section'
    toContainer.dataset.sectionId = 'section-b'
    root.appendChild(fromContainer)
    root.appendChild(toContainer)
    document.body.appendChild(root)

    const layoutConfig = ref({
      sections: [
        {
          id: 'section-a',
          type: 'section',
          fields: [{ id: 'field-1', fieldCode: 'asset_code', label: 'Asset code', span: 1 }]
        },
        {
          id: 'section-b',
          type: 'section',
          fields: [{ id: 'field-2', fieldCode: 'asset_name', label: 'Asset name', span: 1 }]
        }
      ]
    })

    const commitLayoutChange = vi.fn()
    const instances: Array<{ options: Record<string, any> }> = []
    mocks.sortableCreate.mockImplementation((_element, options) => {
      instances.push({ options })
      return { destroy: vi.fn() }
    })

    const interactions = useDesignerDragInteractions({
      layoutConfig: layoutConfig as any,
      renderMode: ref('design'),
      draggedField: ref(null),
      isDragOverCanvas: ref(false),
      dragOverSection: ref(null),
      canvasContentElement: computed(() => root) as any,
      canAddField: () => true,
      notifyUnsupportedField: vi.fn(),
      handleFieldClick: vi.fn(),
      addFieldToContainer: vi.fn(),
      commitLayoutChange
    } as any)

    await interactions.initSortables()

    expect(mocks.sortableCreate).toHaveBeenCalledTimes(2)

    const item = document.createElement('div')
    item.dataset.fieldId = 'field-1'

    instances[0].options.onEnd({
      from: fromContainer,
      to: toContainer,
      oldIndex: 0,
      newIndex: 1,
      item
    })

    expect(commitLayoutChange).toHaveBeenCalledTimes(1)
    const [newConfig, description, previousConfig] = commitLayoutChange.mock.calls[0]
    expect(description).toBe('Move field asset_code')
    expect(previousConfig.sections[0].fields).toHaveLength(1)
    expect(newConfig.sections[0].fields).toHaveLength(0)
    expect(newConfig.sections[1].fields.map((field: any) => field.fieldCode)).toEqual(['asset_name', 'asset_code'])
  })

  it('commits resized field span changes through the resize interaction pipeline', async () => {
    const { useDesignerResizeInteractions } = await import('@/components/designer/useDesignerResizeInteractions')

    const canvasArea = document.createElement('div')
    Object.defineProperty(canvasArea, 'getBoundingClientRect', {
      value: () => ({ left: 0, top: 0, width: 1200, height: 800 })
    })

    const canvasContent = document.createElement('div')
    const fieldCard = document.createElement('div')
    fieldCard.dataset.testid = 'layout-canvas-field'
    fieldCard.dataset.fieldId = 'field-1'
    Object.defineProperty(fieldCard, 'getBoundingClientRect', {
      value: () => ({ left: 10, top: 20, width: 200, height: 48 })
    })
    canvasContent.appendChild(fieldCard)
    document.body.appendChild(canvasArea)
    document.body.appendChild(canvasContent)

    const layoutConfig = ref({
      sections: [
        {
          id: 'section-1',
          type: 'section',
          columns: 2,
          position: 'main',
          fields: [{ id: 'field-1', fieldCode: 'asset_name', label: 'Asset name', span: 1 }]
        }
      ]
    })
    const selectedId = ref('')
    const fieldProps = ref<Record<string, unknown>>({})
    const commitLayoutChange = vi.fn()

    const interactions = useDesignerResizeInteractions({
      layoutConfig: layoutConfig as any,
      isDesignMode: computed(() => true) as any,
      selectedId,
      fieldProps: fieldProps as any,
      canvasAreaElement: computed(() => canvasArea) as any,
      canvasContentElement: computed(() => canvasContent) as any,
      findSectionByFieldId: (config, fieldId) =>
        (config.sections || []).find((section: any) => (section.fields || []).some((field: any) => field.id === fieldId)) || null,
      findLayoutFieldById: (config, fieldId) => {
        for (const section of config.sections || []) {
          const found = (section.fields || []).find((field: any) => field.id === fieldId)
          if (found) return found as any
        }
        return null
      },
      getColumns: (section) => Number(section?.columns || 1),
      resolveLayoutFieldMinHeight: (field) => Number(field?.minHeight || field?.min_height || 44),
      clampFieldMinHeight: (value) => Math.max(44, Math.min(720, Math.round(value))),
      setLayoutFieldMinHeight: (field, value) => {
        field.minHeight = Number(value)
      },
      selectField: (_field, _section) => {
        selectedId.value = 'field-1'
        void nextTick()
      },
      commitLayoutChange
    })

    interactions.handleFieldResizeStart({
      fieldId: 'field-1',
      axis: 'x',
      startX: 0,
      startY: 0,
      cardWidth: 200,
      cardHeight: 48
    })

    window.dispatchEvent(new PointerEvent('pointermove', { clientX: 220, clientY: 0 }))
    window.dispatchEvent(new PointerEvent('pointerup', { clientX: 220, clientY: 0 }))

    const resizedField = layoutConfig.value.sections[0].fields[0]
    expect(resizedField.span).toBe(2)
    expect(fieldProps.value.span).toBe(2)
    expect(commitLayoutChange).toHaveBeenCalledTimes(1)
    expect(commitLayoutChange.mock.calls[0][1]).toBe('Resize field asset_name')
  })
})
