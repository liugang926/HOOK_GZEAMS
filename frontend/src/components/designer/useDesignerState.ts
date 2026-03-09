import { computed, ref } from 'vue'
import { useHotkey } from '@/composables/useHotkeys'
import type {
  DesignerFieldDefinition,
  LayoutConfig,
  LayoutSection
} from '@/components/designer/designerTypes'
import type { LayoutMode } from '@/types/layout'

type FocusTarget = { focus: () => void } | null

interface UseDesignerStateOptions {
  mode: LayoutMode
  initialPreviewMode: 'current' | 'active'
  focusSearch: () => void
  saveDraft: () => void
}

export function useDesignerState(options: UseDesignerStateOptions) {
  const availableFields = ref<DesignerFieldDefinition[]>([])
  const previewReverseRelations = ref<any[]>([])
  const layoutConfig = ref<LayoutConfig>({ sections: [] })
  const selectedId = ref('')
  const renderMode = ref<'design' | 'preview'>('design')
  const layoutMode = ref<'Detail' | 'Compact'>('Detail')
  const previewMode = ref<'current' | 'active'>(options.initialPreviewMode)
  const currentLayoutSnapshot = ref<LayoutConfig | null>(null)
  const previewLoading = ref(false)
  const selectedSection = ref<LayoutSection | null>(null)
  const saving = ref(false)
  const publishing = ref(false)
  const searchInputRef = ref<FocusTarget>(null)
  const searchQuery = ref('')
  const expandedGroups = ref<Set<string>>(new Set())
  const isDefault = ref(false)
  const isPublished = ref(false)
  const layoutVersion = ref('1.0.0')
  const sharedEditLayoutId = ref('')
  const draggedField = ref<DesignerFieldDefinition | null>(null)
  const isDragOverCanvas = ref(false)
  const dragOverSection = ref<string | null>(null)
  const sampleData = ref<Record<string, unknown>>({})
  const canvasAreaRef = ref<HTMLElement | null>(null)
  const canvasContentRef = ref<HTMLElement | null>(null)
  const activeTabs = ref<Record<string, string>>({})
  const activeCollapses = ref<Record<string, string[]>>({})

  const isDesignMode = computed(() => renderMode.value === 'design')

  useHotkey('ctrl+s', () => {
    if (previewMode.value !== 'active') {
      options.saveDraft()
    }
  }, { preventDefault: true, allowInInputs: true })

  useHotkey('ctrl+f', () => {
    if (renderMode.value === 'design') {
      options.focusSearch()
    }
  }, { preventDefault: true })

  return {
    availableFields,
    previewReverseRelations,
    layoutConfig,
    selectedId,
    renderMode,
    layoutMode,
    previewMode,
    currentLayoutSnapshot,
    previewLoading,
    selectedSection,
    saving,
    publishing,
    searchInputRef,
    searchQuery,
    expandedGroups,
    isDefault,
    isPublished,
    layoutVersion,
    sharedEditLayoutId,
    draggedField,
    isDragOverCanvas,
    dragOverSection,
    sampleData,
    canvasAreaRef,
    canvasContentRef,
    activeTabs,
    activeCollapses,
    isDesignMode
  }
}
