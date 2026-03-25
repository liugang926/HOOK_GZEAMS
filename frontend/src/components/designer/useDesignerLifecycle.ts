import { computed, onMounted, onUnmounted, watch, type Ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { ElMessageBox } from 'element-plus'
import { getDefaultLayoutConfig } from '@/utils/layoutValidation'
import { normalizeLayoutType } from '@/utils/layoutMode'
import { storage } from '@/utils/storage'
import type { LayoutConfig } from '@/components/designer/designerTypes'

interface UseDesignerLifecycleOptions {
  props: {
    objectCode?: string
    mode?: string
    initialPreviewMode?: 'current' | 'active'
  }
  layoutConfig: Ref<LayoutConfig>
  renderMode: Ref<string>
  previewMode: Ref<'current' | 'active'>
  activeTabs: Ref<Record<string, string>>
  activeCollapses: Ref<Record<string, string[]>>
  expandedGroups: Ref<Set<string>>
  selectedId: Ref<string>
  isDragOverCanvas: Ref<boolean>
  dragOverSection: Ref<string | null>
  resizeHint: Ref<unknown>
  activeFieldResize: Ref<unknown>
  normalizeAndEnsureLayoutConfig: (config: LayoutConfig) => LayoutConfig
  populateSampleData: () => void
  loadLayout: () => Promise<unknown>
  setPreviewMode: (mode: 'current' | 'active') => Promise<unknown>
  initSortables: () => Promise<unknown>
  destroySortables: () => void
  clearPropertySizeFeedback: () => void
  handleFieldResizeEnd: () => void
  deselect: () => void
  pushHistory: (snapshot: Record<string, unknown>, description: string) => void
}

export function useDesignerLifecycle(options: UseDesignerLifecycleOptions) {
  const { t } = useI18n()

  const dndSignature = computed(() => {
    const sections = options.layoutConfig.value.sections || []
    return JSON.stringify({
      renderMode: options.renderMode.value,
      sections: sections.map((section) => ({
        id: section.id,
        type: section.type,
        tabs: section.type === 'tab' ? (section.tabs || []).map((tab) => tab.id) : [],
        items: section.type === 'collapse' ? (section.items || []).map((item) => item.id) : []
      }))
    })
  })

  function syncContainerStates() {
    const sections = options.layoutConfig.value.sections || []
    const nextTabs = { ...(options.activeTabs.value || {}) }
    const nextCollapses = { ...(options.activeCollapses.value || {}) }
    let tabsChanged = false
    let collapsesChanged = false

    for (const section of sections) {
      const sectionId = section.id
      if (!sectionId) continue

      if (section.type === 'tab') {
        const tabIds = (section.tabs || []).map((tab) => tab.id).filter(Boolean) as string[]
        if (tabIds.length === 0) {
          if (nextTabs[sectionId] !== undefined) {
            delete nextTabs[sectionId]
            tabsChanged = true
          }
        } else {
          const current = nextTabs[sectionId]
          if (!current || !tabIds.includes(current)) {
            nextTabs[sectionId] = tabIds[0]
            tabsChanged = true
          }
        }
      }

      if (section.type === 'collapse') {
        const itemIds = (section.items || []).map((item) => item.id).filter(Boolean) as string[]
        if (itemIds.length === 0) {
          if (nextCollapses[sectionId] !== undefined) {
            delete nextCollapses[sectionId]
            collapsesChanged = true
          }
        } else {
          const current = Array.isArray(nextCollapses[sectionId]) ? nextCollapses[sectionId] : []
          const filtered = current.filter((id) => itemIds.includes(id))
          const target = filtered.length > 0 ? filtered : [itemIds[0]]
          if (JSON.stringify(current) !== JSON.stringify(target)) {
            nextCollapses[sectionId] = target
            collapsesChanged = true
          }
        }
      }
    }

    if (tabsChanged) {
      options.activeTabs.value = nextTabs
    }
    if (collapsesChanged) {
      options.activeCollapses.value = nextCollapses
    }
  }

  const proceedWithNormalLoad = () => {
    void options.loadLayout().finally(() => {
      if (options.props.initialPreviewMode === 'active') {
        void options.setPreviewMode('active')
      }
    })
    options.expandedGroups.value.add('text')
  }

  watch(
    dndSignature,
    async () => {
      syncContainerStates()
      await options.initSortables()
    },
    { immediate: true }
  )

  watch(options.renderMode, (mode) => {
    if (mode !== 'design') {
      options.clearPropertySizeFeedback()
      if (options.activeFieldResize.value) {
        options.handleFieldResizeEnd()
      }
      options.resizeHint.value = null
      options.deselect()
      options.isDragOverCanvas.value = false
      options.dragOverSection.value = null
    }
  })

  onMounted(() => {
    const autoSaveKey =
      options.props.objectCode && options.props.mode
        ? `layout_autosave_${options.props.objectCode}_${options.props.mode}`
        : null

    if (!autoSaveKey) {
      proceedWithNormalLoad()
      return
    }

    storage
      .get<LayoutConfig>(autoSaveKey)
      .then((savedState) => {
        if (!savedState) {
          proceedWithNormalLoad()
          return
        }

        ElMessageBox.confirm(
          t(
            'system.pageLayout.designer.messages.recoverDirtySchema',
            'An unsaved layout state was found. Do you want to recover it?'
          ),
          t('system.pageLayout.designer.messages.recoverTitle', 'Recover Layout'),
          {
            type: 'info',
            confirmButtonText: t('common.actions.confirm', 'Recover'),
            cancelButtonText: t('common.actions.cancel', 'Discard')
          }
        )
          .then(() => {
            try {
              options.layoutConfig.value = options.normalizeAndEnsureLayoutConfig(savedState)
              options.populateSampleData()
              options.pushHistory(options.layoutConfig.value as Record<string, unknown>, 'Recovered state')
            } catch {
              void storage.remove(autoSaveKey)
              proceedWithNormalLoad()
            }
          })
          .catch(() => {
            void storage.remove(autoSaveKey)
            proceedWithNormalLoad()
          })
      })
      .catch(() => {
        proceedWithNormalLoad()
      })
  })

  onUnmounted(() => {
    options.clearPropertySizeFeedback()
    if (options.activeFieldResize.value) {
      options.handleFieldResizeEnd()
    }
    options.destroySortables()
  })

  watch(
    () => options.props.mode,
    (newMode) => {
      options.layoutConfig.value = options.normalizeAndEnsureLayoutConfig(
        getDefaultLayoutConfig(normalizeLayoutType(newMode)) as LayoutConfig
      )
      void options.loadLayout()
    }
  )
}
