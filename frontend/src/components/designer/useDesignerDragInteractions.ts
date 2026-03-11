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
  related?: Element | null
  willInsertAfter?: boolean
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

const INSERT_BEFORE_CLASS = 'drag-insert-before'
const INSERT_AFTER_CLASS = 'drag-insert-after'
const JUST_DROPPED_CLASS = 'field-just-dropped'
const DROP_ZONE_CLASS = 'drop-zone-active'

const removeClasses = (root: ParentNode | null | undefined, selectors: string[]) => {
  if (!root) return
  for (const selector of selectors) {
    root.querySelectorAll<HTMLElement>(selector).forEach((node) => node.classList.remove(selector.slice(1)))
  }
}

export const clearDesignerDragMarkers = (root: ParentNode | null | undefined) => {
  if (!root) return
  removeClasses(root, [
    `.${INSERT_BEFORE_CLASS}`,
    `.${INSERT_AFTER_CLASS}`,
    `.${DROP_ZONE_CLASS}`
  ])
}

export const applyDesignerInsertIndicator = (
  root: ParentNode | null | undefined,
  target: Element | null | undefined,
  willInsertAfter: boolean
) => {
  if (!root) return
  clearDesignerDragMarkers(root)
  const targetField = target instanceof HTMLElement ? target.closest('.field-renderer') as HTMLElement | null : null
  if (targetField) {
    targetField.classList.add(willInsertAfter ? INSERT_AFTER_CLASS : INSERT_BEFORE_CLASS)
    return
  }

  const targetContainer = target instanceof HTMLElement ? target.closest('.designer-fields-container') as HTMLElement | null : null
  targetContainer?.classList.add(DROP_ZONE_CLASS)
}

export const flashDroppedField = (
  root: ParentNode | null | undefined,
  fieldId: string | null | undefined,
  durationMs = 650
) => {
  if (!root || !fieldId) return
  const target = root.querySelector<HTMLElement>(`.field-renderer[data-field-id="${fieldId}"]`)
  if (!target) return
  target.classList.remove(JUST_DROPPED_CLASS)
  void target.offsetWidth
  target.classList.add(JUST_DROPPED_CLASS)
  window.setTimeout(() => {
    target.classList.remove(JUST_DROPPED_CLASS)
  }, durationMs)
}

export function useDesignerDragInteractions(options: UseDesignerDragInteractionsOptions) {
  let sortableInstances: Sortable[] = []

  const destroySortables = () => {
    for (const inst of sortableInstances) inst.destroy()
    sortableInstances = []
  }

  const getCanvasRoot = () => options.canvasContentElement.value

  const clearDragMarkers = () => {
    clearDesignerDragMarkers(getCanvasRoot())
  }

  const showDroppedFeedback = async (fieldId: string | null | undefined) => {
    await nextTick()
    flashDroppedField(getCanvasRoot(), fieldId)
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
    void showDroppedFeedback(moved.id)
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
        ghostClass: 'sortable-ghost',
        chosenClass: 'sortable-chosen',
        dragClass: 'sortable-drag',
        filter: 'input, textarea, button, select, option, .el-input, .el-textarea, .el-select, .el-date-editor, .field-resize-handle',
        preventOnFilter: true,
        onMove: (evt) => {
          applyDesignerInsertIndicator(getCanvasRoot(), evt.related, Boolean(evt.willInsertAfter))
          return true
        },
        onStart: () => {
          clearDragMarkers()
        },
        onEnd: (evt) => {
          clearDragMarkers()
          applySortableMove(evt as SortableMoveEvent)
        }
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
    clearDragMarkers()
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
    // FP-3.4: highlight target section during cross-section drag
    const sectionEl = (event.currentTarget as HTMLElement)?.closest('.designer-section-slot')
    sectionEl?.classList.add('drag-over-target')
  }

  function handleSectionDragLeave(event: DragEvent) {
    if (options.renderMode.value !== 'design') return
    event.stopPropagation()
    // FP-3.4: remove highlight when leaving section
    const sectionEl = (event.currentTarget as HTMLElement)?.closest('.designer-section-slot')
    sectionEl?.classList.remove('drag-over-target')
  }

  function handleSectionDrop(event: DragEvent) {
    if (options.renderMode.value !== 'design') return
    event.preventDefault()
    event.stopPropagation()
    // FP-3.4: remove highlight on drop
    const sectionEl = (event.currentTarget as HTMLElement)?.closest('.designer-section-slot')
    sectionEl?.classList.remove('drag-over-target')

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
    void nextTick().then(() => {
      const root = getCanvasRoot()
      const target = Array.from(root?.querySelectorAll<HTMLElement>('.field-renderer[data-field-code]') || [])
        .find((node) => node.dataset.fieldCode === field.code)
      flashDroppedField(root, target?.dataset.fieldId || null)
    })
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
    void nextTick().then(() => {
      const root = getCanvasRoot()
      const target = Array.from(root?.querySelectorAll<HTMLElement>('.field-renderer[data-field-code]') || [])
        .find((node) => node.dataset.fieldCode === field.code)
      flashDroppedField(root, target?.dataset.fieldId || null)
    })
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
    void nextTick().then(() => {
      const root = getCanvasRoot()
      const target = Array.from(root?.querySelectorAll<HTMLElement>('.field-renderer[data-field-code]') || [])
        .find((node) => node.dataset.fieldCode === field.code)
      flashDroppedField(root, target?.dataset.fieldId || null)
    })
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
