import { nextTick, type ComputedRef, type Ref } from 'vue'
import Sortable from 'sortablejs'
import { cloneLayoutConfig } from '@/utils/layoutValidation'
import type {
  ContainerMeta,
  DesignerFieldDefinition,
  LayoutConfig
} from '@/components/designer/designerTypes'
import {
  getDesignerFieldArrayRef,
  parseDesignerContainerMeta
} from '@/components/designer/designerContainerUtils'

type SortableMoveEvent = {
  from?: Element | null
  to?: Element | null
  oldIndex?: number
  newIndex?: number
  item?: Element | null
}

interface UseDesignerDragInteractionsOptions {
  layoutConfig: Ref<LayoutConfig>
  renderMode: Ref<'design' | 'preview'>
  draggedField: Ref<DesignerFieldDefinition | null>
  isDragOverCanvas: Ref<boolean>
  dragOverSection: Ref<string | null>
  canvasContentElement: ComputedRef<HTMLElement | null>
  canAddField: (field: DesignerFieldDefinition) => boolean
  notifyUnsupportedField: (field: DesignerFieldDefinition) => void
  handleFieldClick: (field: DesignerFieldDefinition) => void
  addFieldToContainer: (field: DesignerFieldDefinition, meta: ContainerMeta) => void
  commitLayoutChange: (newConfig: LayoutConfig, description: string, previousConfig?: LayoutConfig) => void
}

export function useDesignerDragInteractions(options: UseDesignerDragInteractionsOptions) {
  let sortableInstances: Sortable[] = []

  const destroySortables = () => {
    for (const inst of sortableInstances) inst.destroy()
    sortableInstances = []
  }

  const applySortableMove = (evt: SortableMoveEvent) => {
    const fromMeta = parseDesignerContainerMeta(evt?.from as HTMLElement)
    const toMeta = parseDesignerContainerMeta(evt?.to as HTMLElement)
    const oldIndex = typeof evt?.oldIndex === 'number' ? evt.oldIndex : null
    const newIndex = typeof evt?.newIndex === 'number' ? evt.newIndex : null

    if (!fromMeta || !toMeta) return
    if (oldIndex === null || newIndex === null) return

    const previousConfig = cloneLayoutConfig(options.layoutConfig.value)
    const newConfig = cloneLayoutConfig(options.layoutConfig.value) as LayoutConfig
    const fromArr = getDesignerFieldArrayRef(newConfig, fromMeta)
    const toArr = getDesignerFieldArrayRef(newConfig, toMeta)
    if (!fromArr || !toArr) return

    const moved =
      fromArr[oldIndex] ||
      fromArr.find((field) => field?.id && (evt?.item as HTMLElement | undefined)?.dataset?.fieldId === field.id)

    if (!moved) return

    const removeIndex = fromArr.indexOf(moved)
    if (removeIndex >= 0) fromArr.splice(removeIndex, 1)

    const insertIndex = Math.max(0, Math.min(newIndex, toArr.length))
    toArr.splice(insertIndex, 0, moved)

    options.commitLayoutChange(newConfig, `Move field ${moved.fieldCode || moved.id}`, previousConfig)
  }

  const initSortables = async () => {
    if (options.renderMode.value !== 'design') {
      destroySortables()
      return
    }

    await nextTick()
    destroySortables()

    const root = options.canvasContentElement.value
    if (!root) return

    const containers = Array.from(root.querySelectorAll<HTMLElement>('.designer-fields-container'))
    for (const container of containers) {
      const inst = Sortable.create(container, {
        group: { name: 'layout-fields', pull: true, put: true },
        animation: 180,
        draggable: '.field-renderer',
        filter: 'input, textarea, button, select, option, .el-input, .el-textarea, .el-select, .el-date-editor, .field-resize-handle',
        preventOnFilter: true,
        onEnd: applySortableMove
      })
      sortableInstances.push(inst)
    }
  }

  function handleFieldDragStart(event: DragEvent, field: DesignerFieldDefinition) {
    if (!options.canAddField(field)) {
      event.preventDefault()
      options.notifyUnsupportedField(field)
      return
    }

    options.draggedField.value = field
    event.dataTransfer!.effectAllowed = 'copy'
    event.dataTransfer!.setData('field', JSON.stringify(field))
  }

  function handleDragEnd() {
    options.draggedField.value = null
    options.isDragOverCanvas.value = false
    options.dragOverSection.value = null
  }

  function handleCanvasDragOver(event: DragEvent) {
    if (options.renderMode.value !== 'design') return
    event.preventDefault()
    options.isDragOverCanvas.value = true
  }

  function handleCanvasDragLeave() {
    if (options.renderMode.value !== 'design') return
    options.isDragOverCanvas.value = false
  }

  function handleCanvasDrop(event: DragEvent) {
    if (options.renderMode.value !== 'design') return
    event.preventDefault()
    options.isDragOverCanvas.value = false

    const data = event.dataTransfer?.getData('field')
    if (!data) return

    const field: DesignerFieldDefinition = JSON.parse(data)
    options.handleFieldClick(field)
  }

  function handleSectionDragOver(event: DragEvent) {
    if (options.renderMode.value !== 'design') return
    event.preventDefault()
    event.stopPropagation()
  }

  function handleSectionDragLeave(event: DragEvent) {
    if (options.renderMode.value !== 'design') return
    event.stopPropagation()
  }

  function handleSectionDrop(event: DragEvent) {
    if (options.renderMode.value !== 'design') return
    event.preventDefault()
    event.stopPropagation()

    const data = event.dataTransfer?.getData('field')
    if (!data) return

    const sectionId = (event.currentTarget as HTMLElement | null)?.dataset?.sectionId || ''
    if (!sectionId) return

    const field: DesignerFieldDefinition = JSON.parse(data)
    if (!options.canAddField(field)) {
      options.notifyUnsupportedField(field)
      return
    }
    options.addFieldToContainer(field, { kind: 'section', sectionId })
  }

  function handleTabDrop(event: DragEvent) {
    if (options.renderMode.value !== 'design') return
    event.preventDefault()
    event.stopPropagation()

    const data = event.dataTransfer?.getData('field')
    if (!data) return

    const tabId = (event.currentTarget as HTMLElement | null)?.dataset?.tabId || ''
    const sectionId = (event.currentTarget as HTMLElement | null)?.dataset?.sectionId || ''
    if (!sectionId || !tabId) return

    const field: DesignerFieldDefinition = JSON.parse(data)
    if (!options.canAddField(field)) {
      options.notifyUnsupportedField(field)
      return
    }
    options.addFieldToContainer(field, { kind: 'tab', sectionId, tabId })
  }

  function handleCollapseDrop(event: DragEvent) {
    if (options.renderMode.value !== 'design') return
    event.preventDefault()
    event.stopPropagation()

    const data = event.dataTransfer?.getData('field')
    if (!data) return

    const sectionId = (event.currentTarget as HTMLElement | null)?.dataset?.sectionId || ''
    const collapseId = (event.currentTarget as HTMLElement | null)?.dataset?.collapseId || ''
    if (!sectionId || !collapseId) return

    const field: DesignerFieldDefinition = JSON.parse(data)
    if (!options.canAddField(field)) {
      options.notifyUnsupportedField(field)
      return
    }
    options.addFieldToContainer(field, { kind: 'collapse', sectionId, collapseId })
  }

  return {
    initSortables,
    destroySortables,
    handleFieldDragStart,
    handleDragEnd,
    handleCanvasDragOver,
    handleCanvasDragLeave,
    handleCanvasDrop,
    handleSectionDragOver,
    handleSectionDragLeave,
    handleSectionDrop,
    handleTabDrop,
    handleCollapseDrop
  }
}
