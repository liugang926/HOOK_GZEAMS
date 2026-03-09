<!--
  WysiwygLayoutDesigner.vue - WYSIWYG Layout Designer
  What You See Is What You Get layout editor with real-time preview

  Key Features:
  - Left panel: Draggable field list organized by type
  - Center canvas: Real-time rendered form that IS the preview
  - Right panel: Property editor for selected elements
  - Inline editing: Click fields to select, drag to reorder
  - No separate preview mode - the design area IS the preview
-->

<template>
  <div
    class="wysiwyg-layout-designer"
    data-testid="layout-designer"
  >
    <DesignerToolbar
      :layout-name="layoutName"
      :mode-label="modeLabel"
      :is-default="isDefault"
      :translation-mode="translationMode"
      :can-undo="canUndo"
      :can-redo="canRedo"
      :preview-loading="previewLoading"
      :preview-mode="previewMode"
      :publishing="publishing"
      @cancel="handleCancel"
      @undo="undo"
      @redo="redo"
      @reset="handleReset"
      @save="handleSave"
      @publish="handlePublish"
      @set-preview-mode="setPreviewMode"
      @update:translation-mode="translationMode = $event"
    />

    <!-- Main Area -->
    <div class="designer-main">
      <DesignerFieldPanel
        ref="fieldPanelRef"
        :render-mode="renderMode"
        :search-query="searchQuery"
        :filtered-field-groups="filteredFieldGroups"
        :is-group-expanded="isGroupExpanded"
        :can-add-field="canAddField"
        :get-disabled-reason="getDisabledReason"
        :is-field-added="isFieldAdded"
        @update:search-query="searchQuery = $event"
        @toggle-group="toggleGroup"
        @field-click="handleFieldClick"
        @field-drag-start="handleFieldDragStart"
        @drag-end="handleDragEnd"
      />

      <DesignerCanvas
        ref="canvasShellRef"
        :render-mode="renderMode"
        :layout-mode="layoutMode"
        :is-drag-over-canvas="isDragOverCanvas"
        :resize-hint="resizeHint"
        :resize-hint-style="resizeHintStyle"
        @canvas-drop="handleCanvasDrop"
        @canvas-drag-over="handleCanvasDragOver"
        @canvas-drag-leave="handleCanvasDragLeave"
        @set-render-mode="setRenderMode"
        @update:layout-mode="layoutMode = $event"
        @add-section="addSection"
      >
            <!-- Render the actual form using real components -->
            <div
              v-if="designerRenderSections.length > 0"
              class="runtime-preview-card detail-mode-preview dynamic-detail-page"
            >
              <BaseDetailPage
                :title="previewPageTitle"
                :sections="designerCanvasSections"
                :data="sampleData"
                :audit-info="previewAuditInfo"
                :show-back="false"
                :show-edit="false"
                :show-delete="false"
                section-header-test-id="layout-section-header"
                :show-related-objects="true"
                :resolve-runtime-relations="false"
                :disable-related-object-fetch="true"
                :object-code="objectCode"
                :object-name="previewObjectName"
                :reverse-relations="previewReverseRelations"
                :relation-group-scope-id="previewRelationGroupScopeId"
                @section-click="maybeSelectSection"
              >
                <template
                  v-for="(renderSection, sectionIndex) in designerRenderSections"
                  :key="`slot-${renderSection.id}`"
                  #[`section-${renderSection.id}`]
                >
                  <DesignerCanvasSectionRenderer
                    class="designer-section-slot"
                    :data-section-id="renderSection.id"
                    :data-section-position="renderSection.position"
                    :render-section="renderSection"
                    :section-index="sectionIndex"
                    :is-design-mode="isDesignMode"
                    :selected-id="selectedId"
                    :active-tab-name="activeTabs[renderSection.id]"
                    :active-collapse-names="activeCollapses[renderSection.id] || []"
                    :size-feedback-field-id="sizeFeedbackFieldId"
                    :sample-data="sampleData"
                    :card-titles="designerCardTitles"
                    :to-canvas-field="toCanvasField"
                    :field-to-design-display-field="fieldToDesignDisplayField"
                    :get-sample-value="getSampleValue"
                    :select-section="selectSection"
                    :maybe-select-section="maybeSelectSection"
                    :maybe-select-field="maybeSelectField"
                    :remove-field="removeField"
                    :handle-field-size-reset="handleFieldSizeReset"
                    :handle-field-resize-start="handleFieldResizeStart"
                    :toggle-section-collapse="toggleSectionCollapse"
                    :delete-section="deleteSection"
                    :handle-tab-drop="handleTabDrop"
                    :handle-collapse-drop="handleCollapseDrop"
                    :handle-section-drop="handleSectionDrop"
                    :handle-section-drag-over="handleSectionDragOver"
                    :handle-section-drag-leave="handleSectionDragLeave"
                    :t="t"
                    @update:active-tab-name="activeTabs[renderSection.id] = $event"
                    @update:active-collapse-names="activeCollapses[renderSection.id] = $event"
                  />
                </template>
              </BaseDetailPage>
            </div>

            <!-- Empty State -->
            <div
              v-else
              class="empty-canvas"
            >
              <el-empty :description="t('system.pageLayout.designer.empty.layoutEmpty')">
                <el-button
                  v-if="isDesignMode"
                  type="primary"
                  @click="addSection"
                >
                  {{ t('system.pageLayout.designer.actions.addSection') }}
                </el-button>
              </el-empty>
            </div>
      </DesignerCanvas>

      <DesignerPropertyPanel
        :render-mode="renderMode"
        :selected-item="selectedItem"
        :element-type="elementType"
        :field-props="fieldProps"
        :section-props="sectionProps"
        :available-spans="availableSpans"
        :available-span-columns="availableSpanColumns"
        :layout-mode="layoutMode"
        :mode="mode"
        :translation-mode="translationMode"
        @update:field-props="fieldProps = $event"
        @update:section-props="sectionProps = $event"
        @field-property-update="handleFieldPropertyUpdate"
        @section-property-update="handleSectionPropertyUpdate"
      />
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { useI18n } from 'vue-i18n'
import { ElMessage } from 'element-plus'
import DesignerToolbar from '@/components/designer/DesignerToolbar.vue'
import DesignerFieldPanel from '@/components/designer/DesignerFieldPanel.vue'
import DesignerPropertyPanel from '@/components/designer/DesignerPropertyPanel.vue'
import DesignerCanvas from '@/components/designer/DesignerCanvas.vue'
import DesignerCanvasSectionRenderer from '@/components/designer/DesignerCanvasSectionRenderer.vue'
import BaseDetailPage, { type ReverseRelationField } from '@/components/common/BaseDetailPage.vue'
import { canAddFieldInDesigner, getFieldDisabledReason } from '@/platform/layout/designerFieldGuard'
import { useDesignerState } from '@/components/designer/useDesignerState'
import { useDesignerHistory } from '@/components/designer/useDesignerHistory'
import { useDesignerCanvasInteractions } from '@/components/designer/useDesignerCanvasInteractions'
import { useDesignerPalette } from '@/components/designer/useDesignerPalette'
import { useDesignerSelection } from '@/components/designer/useDesignerSelection'
import { useDesignerFieldEditing } from '@/components/designer/useDesignerFieldEditing'
import { useDesignerPersistence } from '@/components/designer/useDesignerPersistence'
import { useDesignerLifecycle } from '@/components/designer/useDesignerLifecycle'
import { useDesignerPreview } from '@/components/designer/useDesignerPreview'
import { useDesignerChangePipeline } from '@/components/designer/useDesignerChangePipeline'
import {
  buildLayoutConfigWithPlacementSnapshot,
  clampFieldMinHeight,
  getColumns,
  getRenderColumns,
  readComponentProps,
  readErrorMessage,
  readLayoutPlacement,
  resolveLayoutFieldMinHeight,
  setLayoutFieldMinHeight,
  toCanvasField,
  unwrapData
} from '@/components/designer/designerLayoutAdapters'
import {
  findDesignerNodeById,
  findLayoutFieldById,
  findSectionByFieldId
} from '@/components/designer/designerTreeUtils'
import { useDesignerFieldCatalog } from '@/components/designer/useDesignerFieldCatalog'
import type {
  ContainerMeta,
  DesignerAnyRecord,
  DesignerFieldDefinition,
  LayoutConfig,
  LayoutField,
  LayoutSection,
  WysiwygDesignerProps
} from '@/components/designer/designerTypes'
import type { LayoutMode } from '@/types/layout'

type FieldDefinition = DesignerFieldDefinition
type AnyRecord = DesignerAnyRecord

// ============================================================================
// Props & Emits
// ============================================================================

type Props = WysiwygDesignerProps

const translationMode = ref(false)

const props = withDefaults(defineProps<Props>(), {
  layoutId: '',
  mode: 'edit',
  layoutName: '',
  objectCode: '',
  businessObjectId: '',
  initialPreviewMode: 'current',
  layoutConfig: () => ({ sections: [] })
})

const emit = defineEmits<{
  save: [data: Record<string, unknown>]
  cancel: []
  published: [data: Record<string, unknown>]
}>()
const { t, locale } = useI18n()

// ============================================================================
// State
// ============================================================================

type DesignerFieldPanelExpose = {
  focusSearch: () => void
}

type DesignerCanvasExpose = {
  canvasAreaElement: HTMLElement | null
  canvasContentElement: HTMLElement | null
}

const fieldPanelRef = ref<(InstanceType<typeof DesignerFieldPanel> & DesignerFieldPanelExpose) | null>(null)
const canvasShellRef = ref<(InstanceType<typeof DesignerCanvas> & DesignerCanvasExpose) | null>(null)

const designerState = useDesignerState({
  mode: props.mode,
  initialPreviewMode: props.initialPreviewMode,
  focusSearch: () => fieldPanelRef.value?.focusSearch(),
  saveDraft: () => {
    void handleSave()
  }
})

const {
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
  activeTabs,
  activeCollapses,
  isDesignMode
} = designerState

const canvasAreaRef = computed(() => canvasShellRef.value?.canvasAreaElement ?? null)
const canvasContentRef = computed(() => canvasShellRef.value?.canvasContentElement ?? null)


// History management
const history = useDesignerHistory(layoutConfig, { maxHistory: 50 })
const { canUndo, canRedo, undo, redo, historyLength } = history
const { commitLayoutChange } = useDesignerChangePipeline({
  objectCode: props.objectCode,
  mode: props.mode,
  layoutConfig,
  historyLength,
  pushHistory: (snapshot, description) => history.push(snapshot, description)
})

// ============================================================================
// Computed
// ============================================================================

const modeLabel = computed(() => {
  const labels: Record<LayoutMode, string> = {
    edit: t('system.pageLayout.modes.edit'),
    readonly: t('system.pageLayout.modes.readonly'),
    search: t('system.pageLayout.modes.search')
  }
  return labels[props.mode] || String(props.mode)
})

const fallbackText = (key: string, fallback: string): string => {
  const value = t(key)
  return typeof value === 'string' && value !== key ? value : fallback
}

const designerCardTitles = computed(() => ({
  remove: fallbackText('system.pageLayout.designer.actions.removeField', 'Remove field'),
  reset: fallbackText('system.pageLayout.designer.actions.resetSize', 'Reset size'),
  resize: fallbackText('system.pageLayout.designer.hints.dragToResize', 'Drag to resize field size'),
  sidebarOnlyHeight: fallbackText('system.pageLayout.designer.hints.sidebarHeightOnly', 'Sidebar field supports height resize only')
}))

const { filteredFieldGroups, normalizeAvailableFields } = useDesignerPalette({
  mode: computed(() => props.mode),
  availableFields,
  searchQuery
})

// ============================================================================
// Methods
// ============================================================================

const findItemById = findDesignerNodeById

const {
  fieldProps,
  sectionProps,
  selectedItem,
  elementType,
  availableSpanColumns,
  availableSpans,
  selectField,
  maybeSelectField,
  selectSection,
  maybeSelectSection,
  deselect
} = useDesignerSelection({
  layoutConfig,
  selectedId,
  selectedSection,
  isDesignMode,
  locale,
  clearPropertySizeFeedback: () => clearPropertySizeFeedback(),
  findItemById,
  getColumns,
  resolveLayoutFieldMinHeight
})

const {
  fieldToDesignDisplayField,
  getSampleValue,
  designerRenderSections,
  designerCanvasSections,
  previewAuditInfo,
  previewObjectName,
  previewRelationGroupScopeId,
  previewPageTitle
} = useDesignerPreview({
  props,
  availableFields,
  layoutConfig,
  sampleData,
  readComponentProps,
  readLayoutPlacement,
  resolveLayoutFieldMinHeight,
  getRenderColumns
})

function setRenderMode(mode: string | number) {
  const nextMode = mode === 'preview' || mode === 'design'
    ? mode
    : 'design'
  renderMode.value = nextMode
}

function isGroupExpanded(type: string): boolean {
  return expandedGroups.value.has(type)
}

function toggleGroup(type: string) {
  if (expandedGroups.value.has(type)) {
    expandedGroups.value.delete(type)
  } else {
    expandedGroups.value.add(type)
  }
}

function getDisabledReason(field: FieldDefinition): string | null {
  return getFieldDisabledReason(field.fieldType, props.mode)
}

function canAddField(field: FieldDefinition): boolean {
  return canAddFieldInDesigner(field.fieldType, props.mode)
}

const {
  isFieldAdded,
  notifyUnsupportedField,
  buildLayoutField,
  addFieldToContainer,
  mapPreviewReverseRelations
} = useDesignerFieldCatalog({
  mode: props.mode,
  layoutConfig,
  sampleData,
  readComponentProps,
  canAddField,
  getDisabledReason,
  commitLayoutChange,
  getSampleValue,
  t
})

let showPropertySizeFeedbackFromCanvas: (fieldId: string) => Promise<void> | void = () => {}

const {
  addSection,
  handleFieldClick,
  handleFieldPropertyUpdate,
  handleFieldSizeReset,
  handleSectionPropertyUpdate,
  removeField,
  deleteSection,
  toggleSectionCollapse
} = useDesignerFieldEditing({
  mode: props.mode,
  layoutConfig,
  layoutMode,
  sampleData,
  selectedId,
  selectedSection,
  elementType,
  fieldProps,
  activeTabs,
  canAddField,
  notifyUnsupportedField,
  isFieldAdded,
  buildLayoutField,
  getSampleValue,
  commitLayoutChange,
  findItemById,
  getColumns,
  setLayoutFieldMinHeight,
  showPropertySizeFeedback: (fieldId) => showPropertySizeFeedbackFromCanvas(fieldId),
  t
})

const {
  activeFieldResize,
  resizeHint,
  resizeHintStyle,
  sizeFeedbackFieldId,
  clearPropertySizeFeedback,
  showPropertySizeFeedback,
  initSortables,
  destroySortables,
  handleFieldResizeStart,
  handleFieldResizeEnd,
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
} = useDesignerCanvasInteractions({
  layoutConfig,
  renderMode,
  isDesignMode,
  selectedId,
  fieldProps,
  draggedField,
  isDragOverCanvas,
  dragOverSection,
  canvasAreaElement: canvasAreaRef,
  canvasContentElement: canvasContentRef,
  canAddField,
  notifyUnsupportedField,
  handleFieldClick,
  addFieldToContainer,
  commitLayoutChange,
  findItemById,
  findSectionByFieldId,
  findLayoutFieldById,
  getColumns,
  resolveLayoutFieldMinHeight,
  clampFieldMinHeight,
  setLayoutFieldMinHeight,
  selectField
})
showPropertySizeFeedbackFromCanvas = showPropertySizeFeedback

const {
  isReadonlyMode,
  normalizeAndEnsureLayoutConfig,
  populateSampleData,
  loadLayout,
  loadAvailableFields,
  setPreviewMode,
  handleSave,
  handlePublish,
  handleReset
} = useDesignerPersistence({
  props,
  availableFields,
  previewReverseRelations,
  layoutConfig,
  layoutMode,
  previewMode,
  currentLayoutSnapshot,
  previewLoading,
  isDefault,
  isPublished,
  layoutVersion,
  sharedEditLayoutId,
  sampleData,
  saving,
  publishing,
  selectedId,
  history: {
    clear: () => history.clear(),
    push: (snapshot, description) => history.push(snapshot, description)
  },
  normalizeAvailableFields,
  mapPreviewReverseRelations,
  buildLayoutConfigWithPlacementSnapshot,
  previewObjectName,
  unwrapData,
  readErrorMessage,
  emitSave: (data) => emit('save', data),
  emitPublished: (data) => emit('published', data)
})

function handleCancel() {
  emit('cancel')
}

useDesignerLifecycle({
  props,
  layoutConfig,
  renderMode,
  previewMode,
  activeTabs,
  activeCollapses,
  expandedGroups,
  selectedId,
  isDragOverCanvas,
  dragOverSection,
  resizeHint,
  activeFieldResize,
  normalizeAndEnsureLayoutConfig,
  populateSampleData,
  loadLayout,
  setPreviewMode,
  initSortables,
  destroySortables,
  clearPropertySizeFeedback,
  handleFieldResizeEnd,
  deselect,
  pushHistory: (snapshot, description) => history.push(snapshot, description)
})
</script>

<style scoped lang="scss" src="./WysiwygLayoutDesigner.scss"></style>
