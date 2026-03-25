import { computed, nextTick, ref, type CSSProperties, type ComputedRef, type Ref } from 'vue'
import { cloneLayoutConfig } from '@/utils/layoutValidation'
import type {
  ActiveFieldResize,
  LayoutConfig,
  LayoutField,
  LayoutSection,
  ResizeHintState,
  ResizeStartPayload
} from '@/components/designer/designerTypes'

interface UseDesignerResizeInteractionsOptions {
  layoutConfig: Ref<LayoutConfig>
  isDesignMode: ComputedRef<boolean>
  selectedId: Ref<string>
  fieldProps: Ref<Partial<LayoutField>>
  canvasAreaElement: ComputedRef<HTMLElement | null>
  canvasContentElement: ComputedRef<HTMLElement | null>
  findSectionByFieldId: (config: LayoutConfig, fieldId: string) => LayoutSection | null
  findLayoutFieldById: (config: LayoutConfig, fieldId: string) => LayoutField | null
  getColumns: (section: Partial<LayoutSection> | null | undefined) => number
  resolveLayoutFieldMinHeight: (field: LayoutField | null | undefined) => number | undefined
  clampFieldMinHeight: (value: number) => number
  setLayoutFieldMinHeight: (field: LayoutField, value: unknown) => void
  selectField: (field: LayoutField, section: LayoutSection) => void
  commitLayoutChange: (newConfig: LayoutConfig, description: string, previousConfig?: LayoutConfig) => void
}

export function useDesignerResizeInteractions(options: UseDesignerResizeInteractionsOptions) {
  let sizeFeedbackTimer: ReturnType<typeof setTimeout> | null = null

  const activeFieldResize = ref<ActiveFieldResize | null>(null)
  const resizeHint = ref<ResizeHintState | null>(null)
  const sizeFeedbackFieldId = ref('')

  const resizeHintStyle = computed<CSSProperties>(() => {
    const canvasArea = options.canvasAreaElement.value
    if (!resizeHint.value || !canvasArea) return { display: 'none' }
    const rect = canvasArea.getBoundingClientRect()
    const left = Math.max(8, Math.min(rect.width - 220, resizeHint.value.clientX - rect.left + 14))
    const top = Math.max(8, Math.min(rect.height - 56, resizeHint.value.clientY - rect.top + 14))
    return {
      left: `${left}px`,
      top: `${top}px`
    }
  })

  function clearPropertySizeFeedback(clearHint = true) {
    if (sizeFeedbackTimer) {
      clearTimeout(sizeFeedbackTimer)
      sizeFeedbackTimer = null
    }
    sizeFeedbackFieldId.value = ''
    if (clearHint && !activeFieldResize.value) {
      resizeHint.value = null
    }
  }

  async function showPropertySizeFeedback(fieldId: string) {
    if (!fieldId || !options.isDesignMode.value || activeFieldResize.value) return
    const field = options.findLayoutFieldById(options.layoutConfig.value, fieldId)
    const section = options.findSectionByFieldId(options.layoutConfig.value, fieldId)
    if (!field || !section) return

    await nextTick()

    const card = options.canvasContentElement.value?.querySelector<HTMLElement>(
      `[data-testid="layout-canvas-field"][data-field-id="${fieldId}"]`
    ) || null
    const cardRect = card?.getBoundingClientRect()
    const span = Math.max(1, Math.min(options.getColumns(section), Number(field.span || 1)))
    const minHeight = options.resolveLayoutFieldMinHeight(field) ?? options.clampFieldMinHeight(cardRect?.height || 44)

    resizeHint.value = {
      span,
      columns: options.getColumns(section),
      minHeight,
      clientX: cardRect ? cardRect.left + cardRect.width / 2 : 0,
      clientY: cardRect ? cardRect.top + cardRect.height / 2 : 0
    }
    sizeFeedbackFieldId.value = fieldId

    if (sizeFeedbackTimer) clearTimeout(sizeFeedbackTimer)
    sizeFeedbackTimer = setTimeout(() => {
      sizeFeedbackFieldId.value = ''
      if (!activeFieldResize.value) {
        resizeHint.value = null
      }
      sizeFeedbackTimer = null
    }, 1100)
  }

  function handleFieldResizeStart(payload: ResizeStartPayload) {
    if (!options.isDesignMode.value) return
    clearPropertySizeFeedback(false)

    const field = options.findLayoutFieldById(options.layoutConfig.value, payload.fieldId)
    const section = options.findSectionByFieldId(options.layoutConfig.value, payload.fieldId)
    if (!field || !section) return

    const columns = options.getColumns(section)
    const allowHorizontal = section.position !== 'sidebar' && payload.axis !== 'y'
    const allowVertical = payload.axis !== 'x'
    if (!allowHorizontal && !allowVertical) return

    if (options.selectedId.value !== payload.fieldId) {
      options.selectField(field, section)
    }

    if (activeFieldResize.value) {
      handleFieldResizeEnd()
    }

    const startSpan = Math.max(1, Math.min(columns, Number(field.span || 1)))
    const inferredHeight = options.resolveLayoutFieldMinHeight(field) ?? options.clampFieldMinHeight(payload.cardHeight || 44)
    const spanUnitPx = payload.cardWidth > 0 ? payload.cardWidth / startSpan : 180

    const bodyStyle = document.body.style
    const previousUserSelect = bodyStyle.userSelect
    const previousCursor = bodyStyle.cursor
    bodyStyle.userSelect = 'none'
    bodyStyle.cursor = payload.axis === 'x' ? 'ew-resize' : payload.axis === 'y' ? 'ns-resize' : 'nwse-resize'

    activeFieldResize.value = {
      fieldId: payload.fieldId,
      fieldCode: field.fieldCode || payload.fieldId,
      axis: payload.axis,
      startX: payload.startX,
      startY: payload.startY,
      startSpan,
      startMinHeight: inferredHeight,
      spanUnitPx: Math.max(24, spanUnitPx),
      columns,
      allowHorizontal,
      allowVertical,
      initialConfig: cloneLayoutConfig(options.layoutConfig.value) as LayoutConfig,
      previousUserSelect,
      previousCursor
    }
    resizeHint.value = {
      span: startSpan,
      columns,
      minHeight: inferredHeight,
      clientX: payload.startX,
      clientY: payload.startY
    }

    window.addEventListener('pointermove', handleFieldResizeMove)
    window.addEventListener('pointerup', handleFieldResizeEnd)
    window.addEventListener('pointercancel', handleFieldResizeEnd)
  }

  function handleFieldResizeMove(event: PointerEvent) {
    const state = activeFieldResize.value
    if (!state) return
    event.preventDefault()

    const field = options.findLayoutFieldById(options.layoutConfig.value, state.fieldId)
    if (!field) return

    let nextSpan = Number(field.span || 1)
    let nextMinHeight = options.resolveLayoutFieldMinHeight(field) ?? state.startMinHeight

    if (state.allowHorizontal) {
      const dx = event.clientX - state.startX
      const delta = Math.round(dx / state.spanUnitPx)
      nextSpan = Math.max(1, Math.min(state.columns, state.startSpan + delta))
    }

    if (state.allowVertical) {
      const dy = event.clientY - state.startY
      nextMinHeight = options.clampFieldMinHeight(state.startMinHeight + dy)
    }

    if (state.allowHorizontal) {
      field.span = nextSpan
    }
    if (state.allowVertical) {
      options.setLayoutFieldMinHeight(field, nextMinHeight)
    }

    if (options.selectedId.value === state.fieldId) {
      options.fieldProps.value = {
        ...options.fieldProps.value,
        span: field.span,
        minHeight: options.resolveLayoutFieldMinHeight(field)
      }
    }

    resizeHint.value = {
      span: nextSpan,
      columns: state.columns,
      minHeight: nextMinHeight,
      clientX: event.clientX,
      clientY: event.clientY
    }
  }

  function handleFieldResizeEnd() {
    const state = activeFieldResize.value
    if (!state) return

    window.removeEventListener('pointermove', handleFieldResizeMove)
    window.removeEventListener('pointerup', handleFieldResizeEnd)
    window.removeEventListener('pointercancel', handleFieldResizeEnd)

    const bodyStyle = document.body.style
    bodyStyle.userSelect = state.previousUserSelect
    bodyStyle.cursor = state.previousCursor

    const currentField = options.findLayoutFieldById(options.layoutConfig.value, state.fieldId)
    const currentSpan = Math.max(1, Number(currentField?.span || 1))
    const currentMinHeight = options.resolveLayoutFieldMinHeight(currentField || undefined) ?? state.startMinHeight
    const spanChanged = state.allowHorizontal && currentSpan !== state.startSpan
    const heightChanged = state.allowVertical && currentMinHeight !== state.startMinHeight

    activeFieldResize.value = null
    resizeHint.value = null

    if (!spanChanged && !heightChanged) return

    const finalConfig = cloneLayoutConfig(options.layoutConfig.value) as LayoutConfig
    options.commitLayoutChange(finalConfig, `Resize field ${state.fieldCode}`, state.initialConfig)
  }

  return {
    activeFieldResize,
    resizeHint,
    resizeHintStyle,
    sizeFeedbackFieldId,
    clearPropertySizeFeedback,
    showPropertySizeFeedback,
    handleFieldResizeStart,
    handleFieldResizeEnd
  }
}
