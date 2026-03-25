import { nextTick, type ComputedRef, type Ref } from 'vue'
import Sortable from 'sortablejs'
import { cloneLayoutConfig } from '@/utils/layoutValidation'
import type {
  ContainerMeta,
  DesignerFieldDefinition,
  DesignerDetailRegionOption,
  DesignerSectionTemplateOption,
  SectionTemplateType,
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
  draggedDetailRegion: Ref<DesignerDetailRegionOption | null>
  draggedSectionId: Ref<string | null>
  isDragOverCanvas: Ref<boolean>
  dragOverSection: Ref<string | null>
  canvasContentElement: ComputedRef<HTMLElement | null>
  canAddField: (field: DesignerFieldDefinition) => boolean
  notifyUnsupportedField: (field: DesignerFieldDefinition) => void
  handleFieldClick: (field: DesignerFieldDefinition) => void
  addSectionTemplate: (
    template?: SectionTemplateType | DesignerSectionTemplateOption,
    options?: { insertIndex?: number | null }
  ) => void
  addDetailRegion: (
    detailRegion?: string | DesignerDetailRegionOption,
    options?: { insertIndex?: number | null }
  ) => void
  moveSectionToIndex: (sectionId: string, options?: { insertIndex?: number | null }) => void
  addFieldToContainer: (field: DesignerFieldDefinition, meta: ContainerMeta) => void
  commitLayoutChange: (newConfig: LayoutConfig, description: string, previousConfig?: LayoutConfig) => void
}

const INSERT_BEFORE_CLASS = 'drag-insert-before'
const INSERT_AFTER_CLASS = 'drag-insert-after'
const SECTION_INSERT_BEFORE_CLASS = 'drag-section-insert-before'
const SECTION_INSERT_AFTER_CLASS = 'drag-section-insert-after'
const JUST_DROPPED_CLASS = 'field-just-dropped'
const DROP_ZONE_CLASS = 'drop-zone-active'
const SECTION_DROP_ZONE_CLASS = 'drag-over-target'

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
    `.${SECTION_INSERT_BEFORE_CLASS}`,
    `.${SECTION_INSERT_AFTER_CLASS}`,
    `.${DROP_ZONE_CLASS}`,
    `.${SECTION_DROP_ZONE_CLASS}`
  ])
}

export const applyDesignerSectionInsertIndicator = (
  root: ParentNode | null | undefined,
  target: Element | null | undefined,
  willInsertAfter: boolean
) => {
  if (!root) return
  clearDesignerDragMarkers(root)
  const targetSection = target instanceof HTMLElement ? target.closest('.designer-section-slot') as HTMLElement | null : null
  if (!targetSection) return
  targetSection.classList.add(willInsertAfter ? SECTION_INSERT_AFTER_CLASS : SECTION_INSERT_BEFORE_CLASS)
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

  const isDetailRegionDragEvent = (event: DragEvent) =>
    Array.from(event.dataTransfer?.types || []).includes('detail-region')

  const isSectionTemplateDragEvent = (event: DragEvent) =>
    Array.from(event.dataTransfer?.types || []).includes('layout-section-template')

  const isSectionDragEvent = (event: DragEvent) =>
    Array.from(event.dataTransfer?.types || []).includes('layout-section')

  const parseSectionTemplatePayload = (
    payload: string | null | undefined
  ): SectionTemplateType | DesignerSectionTemplateOption | null => {
    const raw = String(payload || '').trim()
    if (!raw) return null

    try {
      const parsed = JSON.parse(raw) as Partial<DesignerSectionTemplateOption>
      if (parsed && typeof parsed === 'object' && typeof parsed.templateType === 'string') {
        return {
          templateCode: String(parsed.templateCode || parsed.templateType),
          templateType:
            parsed.templateType === 'tab' || parsed.templateType === 'collapse' ? parsed.templateType : 'section',
          title: String(parsed.title || parsed.templateCode || parsed.templateType),
          description: typeof parsed.description === 'string' ? parsed.description : undefined,
          icon:
            parsed.icon === 'tab' || parsed.icon === 'collapse' || parsed.icon === 'section'
              ? parsed.icon
              : 'section',
          preset: parsed.preset && typeof parsed.preset === 'object' ? parsed.preset : undefined
        }
      }
    } catch {
      // Fallback to legacy string payloads.
    }

    if (raw === 'tab' || raw === 'collapse') return raw
    return 'section'
  }

  const findSectionById = (sectionId: string) =>
    (options.layoutConfig.value.sections || []).find((section) => section.id === sectionId) || null

  const resolveSectionInsertContext = (event: DragEvent) => {
    const sectionEl =
      (
        (event.currentTarget as HTMLElement | null)?.closest('.designer-section-slot') ||
        (event.target as HTMLElement | null)?.closest('.designer-section-slot')
      ) as HTMLElement | null
    const sectionId = String(sectionEl?.dataset?.sectionId || '').trim()
    if (!sectionEl || !sectionId) return null

    const sectionIndex = (options.layoutConfig.value.sections || []).findIndex((section) => section.id === sectionId)
    if (sectionIndex < 0) return null

    const rect = sectionEl.getBoundingClientRect()
    const midpoint = rect.top + rect.height / 2
    const willInsertAfter = event.clientY >= midpoint

    return {
      sectionEl,
      sectionId,
      sectionIndex,
      willInsertAfter,
      insertIndex: willInsertAfter ? sectionIndex + 1 : sectionIndex
    }
  }

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

  function handleDetailRegionDragStart(event: DragEvent, region: DesignerDetailRegionOption) {
    options.draggedDetailRegion.value = region
    event.dataTransfer!.effectAllowed = 'copy'
    event.dataTransfer!.setData('detail-region', JSON.stringify(region))
  }

  function handleSectionTemplateDragStart(event: DragEvent, template: DesignerSectionTemplateOption) {
    event.dataTransfer!.effectAllowed = 'copy'
    event.dataTransfer!.setData('layout-section-template', JSON.stringify(template))
  }

  function handleSectionDragStart(event: DragEvent, sectionId: string) {
    const nextSectionId = String(sectionId || '').trim()
    if (!nextSectionId) {
      event.preventDefault()
      return
    }

    options.draggedSectionId.value = nextSectionId
    event.dataTransfer!.effectAllowed = 'move'
    event.dataTransfer!.setData('layout-section', nextSectionId)
  }

  function handleDragEnd() {
    options.draggedField.value = null
    options.draggedDetailRegion.value = null
    options.draggedSectionId.value = null
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
    clearDragMarkers()
  }

  function handleCanvasDrop(event: DragEvent) {
    if (options.renderMode.value !== 'design') return
    event.preventDefault()
    options.isDragOverCanvas.value = false
    clearDragMarkers()

    const data = event.dataTransfer?.getData('field')
    const detailRegionData = event.dataTransfer?.getData('detail-region')
    const sectionTemplateData = parseSectionTemplatePayload(event.dataTransfer?.getData('layout-section-template'))
    const sectionData = event.dataTransfer?.getData('layout-section')
    if (sectionData) {
      options.moveSectionToIndex(sectionData, {
        insertIndex: (options.layoutConfig.value.sections || []).length
      })
      return
    }
    if (sectionTemplateData) {
      options.addSectionTemplate(sectionTemplateData, {
        insertIndex: (options.layoutConfig.value.sections || []).length
      })
      return
    }
    if (detailRegionData) {
      const region: DesignerDetailRegionOption = JSON.parse(detailRegionData)
      options.addDetailRegion(region)
      return
    }
    if (!data) return

    const field: DesignerFieldDefinition = JSON.parse(data)
    options.handleFieldClick(field)
  }

  function handleSectionDragOver(event: DragEvent) {
    if (options.renderMode.value !== 'design') return
    event.preventDefault()
    event.stopPropagation()
    if (isDetailRegionDragEvent(event)) {
      const insertContext = resolveSectionInsertContext(event)
      applyDesignerSectionInsertIndicator(getCanvasRoot(), insertContext?.sectionEl, Boolean(insertContext?.willInsertAfter))
      return
    }

    if (isSectionTemplateDragEvent(event)) {
      const insertContext = resolveSectionInsertContext(event)
      applyDesignerSectionInsertIndicator(getCanvasRoot(), insertContext?.sectionEl, Boolean(insertContext?.willInsertAfter))
      return
    }

    if (isSectionDragEvent(event)) {
      const insertContext = resolveSectionInsertContext(event)
      applyDesignerSectionInsertIndicator(getCanvasRoot(), insertContext?.sectionEl, Boolean(insertContext?.willInsertAfter))
      return
    }

    const sectionEl = (event.currentTarget as HTMLElement)?.closest('.designer-section-slot')
    clearDragMarkers()
    sectionEl?.classList.add(SECTION_DROP_ZONE_CLASS)
  }

  function handleSectionDragLeave(event: DragEvent) {
    if (options.renderMode.value !== 'design') return
    event.stopPropagation()
    clearDragMarkers()
  }

  function handleSectionDrop(event: DragEvent) {
    if (options.renderMode.value !== 'design') return
    event.preventDefault()
    event.stopPropagation()
    clearDragMarkers()

    const data = event.dataTransfer?.getData('field')
    const detailRegionData = event.dataTransfer?.getData('detail-region')
    const sectionTemplateData = parseSectionTemplatePayload(event.dataTransfer?.getData('layout-section-template'))
    const sectionData = event.dataTransfer?.getData('layout-section')
    if (sectionData) {
      const insertContext = resolveSectionInsertContext(event)
      options.moveSectionToIndex(sectionData, {
        insertIndex: insertContext?.insertIndex ?? null
      })
      return
    }
    if (sectionTemplateData) {
      const insertContext = resolveSectionInsertContext(event)
      options.addSectionTemplate(sectionTemplateData, {
        insertIndex: insertContext?.insertIndex ?? null
      })
      return
    }
    if (detailRegionData) {
      const region: DesignerDetailRegionOption = JSON.parse(detailRegionData)
      const insertContext = resolveSectionInsertContext(event)
      options.addDetailRegion(region, {
        insertIndex: insertContext?.insertIndex ?? null
      })
      return
    }
    if (!data) return

    const sectionId = (event.currentTarget as HTMLElement | null)?.dataset?.sectionId || ''
    if (!sectionId) return
    const targetSection = findSectionById(sectionId)
    if (String(targetSection?.type || '') === 'detail-region') {
      return
    }

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
    clearDragMarkers()

    const data = event.dataTransfer?.getData('field')
    const detailRegionData = event.dataTransfer?.getData('detail-region')
    const sectionTemplateData = parseSectionTemplatePayload(event.dataTransfer?.getData('layout-section-template'))
    const sectionData = event.dataTransfer?.getData('layout-section')
    if (sectionData) {
      const insertContext = resolveSectionInsertContext(event)
      options.moveSectionToIndex(sectionData, {
        insertIndex: insertContext?.insertIndex ?? null
      })
      return
    }
    if (sectionTemplateData) {
      const insertContext = resolveSectionInsertContext(event)
      options.addSectionTemplate(sectionTemplateData, {
        insertIndex: insertContext?.insertIndex ?? null
      })
      return
    }
    if (detailRegionData) {
      const region: DesignerDetailRegionOption = JSON.parse(detailRegionData)
      const insertContext = resolveSectionInsertContext(event)
      options.addDetailRegion(region, {
        insertIndex: insertContext?.insertIndex ?? null
      })
      return
    }
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
    clearDragMarkers()

    const data = event.dataTransfer?.getData('field')
    const detailRegionData = event.dataTransfer?.getData('detail-region')
    const sectionTemplateData = parseSectionTemplatePayload(event.dataTransfer?.getData('layout-section-template'))
    const sectionData = event.dataTransfer?.getData('layout-section')
    if (sectionData) {
      const insertContext = resolveSectionInsertContext(event)
      options.moveSectionToIndex(sectionData, {
        insertIndex: insertContext?.insertIndex ?? null
      })
      return
    }
    if (sectionTemplateData) {
      const insertContext = resolveSectionInsertContext(event)
      options.addSectionTemplate(sectionTemplateData, {
        insertIndex: insertContext?.insertIndex ?? null
      })
      return
    }
    if (detailRegionData) {
      const region: DesignerDetailRegionOption = JSON.parse(detailRegionData)
      const insertContext = resolveSectionInsertContext(event)
      options.addDetailRegion(region, {
        insertIndex: insertContext?.insertIndex ?? null
      })
      return
    }
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
    handleDetailRegionDragStart,
    handleSectionTemplateDragStart,
    handleSectionDragStart,
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
