import { debounce } from 'lodash-es'
import { storage } from '@/utils/storage'
import { cloneLayoutConfig } from '@/utils/layoutValidation'
import type { Ref } from 'vue'
import type { LayoutConfig } from '@/components/designer/designerTypes'

interface UseDesignerChangePipelineOptions {
  objectCode?: string
  mode?: string
  layoutConfig: Ref<LayoutConfig>
  historyLength: Ref<number>
  pushHistory: (snapshot: Record<string, unknown>, description: string) => void
}

export function useDesignerChangePipeline(options: UseDesignerChangePipelineOptions) {
  const debouncedSaveLayoutState = debounce(async (key: string, config: LayoutConfig) => {
    try {
      await storage.set(key, config)
    } catch {
      // Ignore background autosave failure; explicit save/publish remains available.
    }
  }, 800)

  function commitLayoutChange(newConfig: LayoutConfig, description: string, previousConfig?: LayoutConfig) {
    if (options.historyLength.value === 0) {
      const baseline = cloneLayoutConfig(previousConfig || options.layoutConfig.value) as Record<string, unknown>
      options.pushHistory(baseline, 'Initial state')
    }
    options.layoutConfig.value = newConfig
    options.pushHistory(newConfig as unknown as Record<string, unknown>, description)

    if (options.objectCode && options.mode) {
      const autoSaveKey = `layout_autosave_${options.objectCode}_${options.mode}`
      void debouncedSaveLayoutState(autoSaveKey, newConfig)
    }
  }

  return {
    commitLayoutChange
  }
}
