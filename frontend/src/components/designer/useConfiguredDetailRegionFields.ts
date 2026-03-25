import { ref, type ComputedRef } from 'vue'
import { applyDetailRegionColumnPreset } from '@/components/designer/detailRegionColumnPresets'

export type ConfiguredFieldGroup = 'relatedFields' | 'lookupColumns'
export type ConfiguredFieldDropPosition = 'before' | 'after'

type ConfiguredFieldRecord = Record<string, any>

interface UseConfiguredDetailRegionFieldsOptions {
  selectedRelatedFieldConfigs: ComputedRef<ConfiguredFieldRecord[]>
  selectedLookupColumnConfigs: ComputedRef<ConfiguredFieldRecord[]>
  resolveConfiguredFieldKey: (value: unknown) => string
  emitUpdate: (key: ConfiguredFieldGroup, value: ConfiguredFieldRecord[]) => void
}

export function useConfiguredDetailRegionFields(
  options: UseConfiguredDetailRegionFieldsOptions
) {
  const draggingConfiguredField = ref<{ group: ConfiguredFieldGroup; key: string } | null>(null)
  const dragOverConfiguredField = ref<{
    group: ConfiguredFieldGroup
    key: string
    position: ConfiguredFieldDropPosition
  } | null>(null)

  const getConfiguredFieldList = (key: ConfiguredFieldGroup): ConfiguredFieldRecord[] => {
    return key === 'relatedFields'
      ? options.selectedRelatedFieldConfigs.value
      : options.selectedLookupColumnConfigs.value
  }

  const mapConfiguredFieldList = (
    key: ConfiguredFieldGroup,
    configKey: string,
    updater: (value: ConfiguredFieldRecord) => ConfiguredFieldRecord
  ) => {
    const current = getConfiguredFieldList(key).map((item) => {
      if (options.resolveConfiguredFieldKey(item) !== configKey) return item
      return updater({ ...item })
    })

    options.emitUpdate(key, current)
  }

  const reorderConfiguredFields = (
    key: ConfiguredFieldGroup,
    fromKey: string,
    toKey: string,
    position: ConfiguredFieldDropPosition
  ) => {
    if (!fromKey || !toKey || fromKey === toKey) return

    const current = [...getConfiguredFieldList(key)]
    const movingItem = current.find((item) => options.resolveConfiguredFieldKey(item) === fromKey)
    if (!movingItem) return

    const remaining = current.filter((item) => options.resolveConfiguredFieldKey(item) !== fromKey)
    const targetIndex = remaining.findIndex((item) => options.resolveConfiguredFieldKey(item) === toKey)
    if (targetIndex < 0) return

    remaining.splice(position === 'after' ? targetIndex + 1 : targetIndex, 0, movingItem)
    options.emitUpdate(key, remaining)
  }

  const resolveConfiguredFieldElement = (event: DragEvent): HTMLElement | null => {
    if (event.currentTarget instanceof HTMLElement) return event.currentTarget
    if (event.target instanceof HTMLElement) {
      return event.target.closest('.detail-region-configurator__item')
    }
    return null
  }

  const resolveConfiguredFieldDropPosition = (
    event: DragEvent
  ): ConfiguredFieldDropPosition => {
    const element = resolveConfiguredFieldElement(event)
    if (!element) return 'after'

    const rect = element.getBoundingClientRect()
    const midpoint = rect.top + rect.height / 2
    return event.clientY <= midpoint ? 'before' : 'after'
  }

  const configuredFieldItemClasses = (key: ConfiguredFieldGroup, configKey: string) => ({
    'is-dragging':
      draggingConfiguredField.value?.group === key &&
      draggingConfiguredField.value?.key === configKey,
    'is-drag-over-before': (
      dragOverConfiguredField.value?.group === key &&
      dragOverConfiguredField.value?.key === configKey &&
      dragOverConfiguredField.value?.position === 'before' &&
      draggingConfiguredField.value?.key !== configKey
    ),
    'is-drag-over-after': (
      dragOverConfiguredField.value?.group === key &&
      dragOverConfiguredField.value?.key === configKey &&
      dragOverConfiguredField.value?.position === 'after' &&
      draggingConfiguredField.value?.key !== configKey
    )
  })

  const handleConfiguredFieldDragStart = (
    key: ConfiguredFieldGroup,
    configKey: string,
    event: DragEvent
  ) => {
    draggingConfiguredField.value = { group: key, key: configKey }
    dragOverConfiguredField.value = null

    if (event.dataTransfer) {
      event.dataTransfer.effectAllowed = 'move'
      event.dataTransfer.setData('text/plain', configKey)
    }
  }

  const handleConfiguredFieldDragOver = (
    key: ConfiguredFieldGroup,
    configKey: string,
    event: DragEvent
  ) => {
    if (!draggingConfiguredField.value || draggingConfiguredField.value.group !== key) return

    event.preventDefault()
    if (event.dataTransfer) {
      event.dataTransfer.dropEffect = 'move'
    }

    if (draggingConfiguredField.value.key === configKey) {
      dragOverConfiguredField.value = null
      return
    }

    dragOverConfiguredField.value = {
      group: key,
      key: configKey,
      position: resolveConfiguredFieldDropPosition(event)
    }
  }

  const handleConfiguredFieldDragEnd = () => {
    draggingConfiguredField.value = null
    dragOverConfiguredField.value = null
  }

  const handleConfiguredFieldDrop = (
    key: ConfiguredFieldGroup,
    configKey: string,
    event: DragEvent
  ) => {
    event.preventDefault()

    const dragging = draggingConfiguredField.value
    if (!dragging || dragging.group !== key) {
      handleConfiguredFieldDragEnd()
      return
    }

    if (dragging.key === configKey) {
      handleConfiguredFieldDragEnd()
      return
    }

    const position = (
      dragOverConfiguredField.value?.group === key &&
      dragOverConfiguredField.value?.key === configKey
    )
      ? dragOverConfiguredField.value.position
      : resolveConfiguredFieldDropPosition(event)

    reorderConfiguredFields(key, dragging.key, configKey, position)
    handleConfiguredFieldDragEnd()
  }

  const moveConfiguredField = (
    key: ConfiguredFieldGroup,
    configKey: string,
    direction: -1 | 1
  ) => {
    const current = [...getConfiguredFieldList(key)]
    const index = current.findIndex((item) => options.resolveConfiguredFieldKey(item) === configKey)
    if (index < 0) return
    const nextIndex = index + direction
    if (nextIndex < 0 || nextIndex >= current.length) return
    const [item] = current.splice(index, 1)
    current.splice(nextIndex, 0, item)
    options.emitUpdate(key, current)
  }

  const updateConfiguredFieldWidth = (
    key: ConfiguredFieldGroup,
    configKey: string,
    value: unknown
  ) => {
    const raw = String(value ?? '').trim()
    if (raw) {
      const parsed = Number(raw)
      if (!Number.isFinite(parsed) || parsed <= 0) return
    }

    mapConfiguredFieldList(key, configKey, (next) => {
      if (!raw) {
        delete next.width
        return next
      }
      next.width = Math.round(Number(raw))
      return next
    })
  }

  const updateConfiguredFieldMinWidth = (
    key: ConfiguredFieldGroup,
    configKey: string,
    value: unknown
  ) => {
    const raw = String(value ?? '').trim()
    if (raw) {
      const parsed = Number(raw)
      if (!Number.isFinite(parsed) || parsed <= 0) return
    }

    mapConfiguredFieldList(key, configKey, (next) => {
      if (!raw) {
        delete next.minWidth
        delete next.min_width
        return next
      }
      next.minWidth = Math.round(Number(raw))
      delete next.min_width
      return next
    })
  }

  const updateConfiguredFieldAlign = (
    key: ConfiguredFieldGroup,
    configKey: string,
    value: unknown
  ) => {
    const raw = String(value ?? '').trim().toLowerCase()
    const normalized = ['left', 'center', 'right'].includes(raw) ? raw : ''

    mapConfiguredFieldList(key, configKey, (next) => {
      if (!normalized) {
        delete next.align
        return next
      }
      next.align = normalized
      return next
    })
  }

  const updateConfiguredFieldFixed = (
    key: ConfiguredFieldGroup,
    configKey: string,
    value: unknown
  ) => {
    const raw = String(value ?? '').trim().toLowerCase()
    const normalized = ['left', 'right'].includes(raw) ? raw : ''

    mapConfiguredFieldList(key, configKey, (next) => {
      if (!normalized) {
        delete next.fixed
        return next
      }
      next.fixed = normalized
      return next
    })
  }

  const updateConfiguredFieldEllipsis = (
    key: ConfiguredFieldGroup,
    configKey: string,
    value: unknown
  ) => {
    const enabled = value === true

    mapConfiguredFieldList(key, configKey, (next) => {
      if (!enabled) {
        delete next.ellipsis
        delete next.showOverflowTooltip
        delete next.show_overflow_tooltip
        return next
      }
      next.ellipsis = true
      next.showOverflowTooltip = true
      next.show_overflow_tooltip = true
      return next
    })
  }

  const updateConfiguredFieldFormatter = (
    key: ConfiguredFieldGroup,
    configKey: string,
    value: unknown
  ) => {
    const raw = String(value ?? '').trim().toLowerCase()
    const normalized = ['uppercase', 'lowercase', 'number', 'date', 'datetime', 'boolean'].includes(raw)
      ? raw
      : ''

    mapConfiguredFieldList(key, configKey, (next) => {
      if (!normalized) {
        delete next.formatter
        delete next.displayFormatter
        return next
      }
      next.formatter = normalized
      delete next.displayFormatter
      return next
    })
  }

  const updateConfiguredFieldEmptyText = (
    key: ConfiguredFieldGroup,
    configKey: string,
    value: unknown
  ) => {
    const raw = String(value ?? '').trim()

    mapConfiguredFieldList(key, configKey, (next) => {
      if (!raw) {
        delete next.emptyText
        delete next.empty_text
        return next
      }
      next.emptyText = raw
      delete next.empty_text
      return next
    })
  }

  const updateConfiguredFieldTooltipTemplate = (
    key: ConfiguredFieldGroup,
    configKey: string,
    value: unknown
  ) => {
    const raw = String(value ?? '').trim()

    mapConfiguredFieldList(key, configKey, (next) => {
      if (!raw) {
        delete next.tooltipTemplate
        delete next.tooltip_template
        return next
      }
      next.tooltipTemplate = raw
      delete next.tooltip_template
      return next
    })
  }

  const applyConfiguredFieldPreset = (
    key: ConfiguredFieldGroup,
    configKey: string,
    presetCode: unknown
  ) => {
    mapConfiguredFieldList(key, configKey, (next) => {
      return applyDetailRegionColumnPreset(next, presetCode)
    })
  }

  const removeConfiguredField = (key: ConfiguredFieldGroup, configKey: string) => {
    const current = getConfiguredFieldList(key).filter((item) => {
      return options.resolveConfiguredFieldKey(item) !== configKey
    })
    options.emitUpdate(key, current)
  }

  return {
    draggingConfiguredField,
    dragOverConfiguredField,
    getConfiguredFieldList,
    configuredFieldItemClasses,
    handleConfiguredFieldDragStart,
    handleConfiguredFieldDragOver,
    handleConfiguredFieldDragEnd,
    handleConfiguredFieldDrop,
    moveConfiguredField,
    updateConfiguredFieldWidth,
    updateConfiguredFieldMinWidth,
    updateConfiguredFieldAlign,
    updateConfiguredFieldFixed,
    updateConfiguredFieldEllipsis,
    updateConfiguredFieldFormatter,
    updateConfiguredFieldEmptyText,
    updateConfiguredFieldTooltipTemplate,
    applyConfiguredFieldPreset,
    removeConfiguredField,
  }
}
