import { computed, type Ref } from 'vue'
import { useLayoutHistory } from '@/composables/useLayoutHistory'
import { cloneLayoutConfig } from '@/utils/layoutValidation'
import type { LayoutConfig } from '@/components/designer/designerTypes'

interface UseDesignerHistoryOptions {
  maxHistory?: number
}

export function useDesignerHistory(
  layoutConfig: Ref<LayoutConfig>,
  options: UseDesignerHistoryOptions = {}
) {
  const history = useLayoutHistory(layoutConfig as unknown as Ref<Record<string, unknown>>, {
    maxHistory: options.maxHistory ?? 50
  })

  const canUndo = computed(() => history.canUndo.value)
  const canRedo = computed(() => history.canRedo.value)

  const commit = (newConfig: LayoutConfig, description: string, previousConfig?: LayoutConfig) => {
    const previous = previousConfig ? cloneLayoutConfig(previousConfig) : cloneLayoutConfig(layoutConfig.value)
    const next = cloneLayoutConfig(newConfig)
    if (JSON.stringify(previous) === JSON.stringify(next)) return
    layoutConfig.value = next
    history.push(next as unknown as Record<string, unknown>, description)
  }

  return {
    ...history,
    canUndo,
    canRedo,
    commit
  }
}
