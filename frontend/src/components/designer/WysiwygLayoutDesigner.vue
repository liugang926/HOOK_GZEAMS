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
    :class="`render-mode-${renderMode}`"
    data-testid="layout-designer"
  >
    <DesignerToolbar
      :layout-name="layoutName"
      :mode-label="modeLabel"
      :is-default="isDefault"
      :translation-mode="translationMode"
      :view-mode="layoutMode"
      :viewport="viewport"
      :can-undo="canUndo"
      :can-redo="canRedo"
      :render-mode="renderMode"
      :preview-loading="previewLoading"
      :preview-mode="previewMode"
      :publishing="publishing"
      @cancel="handleCancel"
      @undo="undo"
      @redo="redo"
      @update:render-mode="setRenderMode"
      @reset="handleReset"
      @save="handleSave"
      @publish="handlePublish"
      @set-preview-mode="setPreviewMode"
      @update:translation-mode="translationMode = $event"
      @update:view-mode="layoutMode = $event as any"
      @update:viewport="viewport = $event as any"
    />

    <!-- Main Area -->
    <div
      class="designer-main"
      :class="{ 'designer-main--preview': renderMode === 'preview' }"
    >
      <aside
        v-if="renderMode === 'design'"
        class="designer-pane designer-pane--left"
      >
        <DesignerFieldPanel
          ref="fieldPanelRef"
          :render-mode="renderMode"
          :search-query="searchQuery"
          :filtered-field-groups="filteredFieldGroups"
          :section-template-options="sectionTemplateOptions"
          :detail-region-options="filteredDetailRegionOptions"
          :assigned-field-count="assignedFieldCount"
          :total-field-count="totalAvailableFieldCount"
          :is-group-expanded="isGroupExpanded"
          :can-add-field="canAddField"
          :get-disabled-reason="getDisabledReason"
          :is-field-added="isFieldAdded"
          :is-detail-region-added="isDetailRegionAdded"
          @update:search-query="searchQuery = $event"
          @toggle-group="toggleGroup"
          @field-click="handleFieldClick"
          @section-template-click="addSectionTemplate($event)"
          @detail-region-click="addDetailRegion($event)"
          @detail-region-preview="handleDetailRegionPalettePreview"
          @field-drag-start="handleFieldDragStart"
          @section-template-drag-start="handleSectionTemplateDragStart"
          @detail-region-drag-start="handleDetailRegionDragStart"
          @drag-end="handleDragEnd"
        />
      </aside>

      <section class="designer-pane designer-pane--center">
        <DesignerCanvas
          ref="canvasShellRef"
          :class="[`viewport-${viewport}`]"
          :render-mode="renderMode"
          :layout-mode="layoutMode"
          :is-drag-over-canvas="isDragOverCanvas"
          :resize-hint="resizeHint"
          :resize-hint-style="resizeHintStyle"
          :total-fields="canvasFieldCount"
          :required-fields="canvasRequiredFieldCount"
          :section-count="canvasSectionCount"
          :detail-region-options="detailRegionCanvasOptions"
          @canvas-drop="handleCanvasDrop"
          @canvas-drag-over="handleCanvasDragOver"
          @canvas-drag-leave="handleCanvasDragLeave"
          @add-section="addSection"
          @add-detail-region="addDetailRegion"
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
                v-for="renderSection in designerRenderSections"
                :key="`header-${renderSection.id}`"
                #[`section-header-${renderSection.id}`]
              >
                <DesignerSectionHeader
                  :section-id="renderSection.id"
                  :title="String(renderSection.title || '')"
                  :selected="isDesignMode && selectedId === renderSection.id"
                  :interactive="isDesignMode"
                  :select-section="selectSection"
                  @title-update="updateSectionTitle"
                />
              </template>
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
                  :total-section-count="designerRenderSections.length"
                  :is-design-mode="isDesignMode"
                  :selected-id="selectedId"
                  :active-tab-name="activeTabs[renderSection.id]"
                  :active-collapse-names="activeCollapses[renderSection.id] || []"
                  :size-feedback-field-id="sizeFeedbackFieldId"
                  :sample-data="sampleData"
                  :card-titles="designerCardTitles"
                  :section-action-labels="designerSectionActionLabels"
                  :to-canvas-field="toCanvasField"
                  :field-to-design-display-field="fieldToDesignDisplayField"
                  :get-sample-value="getSampleValue"
                  :select-section="selectSection"
                  :maybe-select-section="maybeSelectSection"
                  :maybe-select-field="maybeSelectField"
                  :remove-field="removeField"
                  :update-field-label="updateFieldLabel"
                  :handle-field-size-reset="handleFieldSizeReset"
                  :handle-field-resize-start="handleFieldResizeStart"
                  :toggle-section-collapse="toggleSectionCollapse"
                  :move-section="moveSection"
                  :delete-section="deleteSection"
                  :handle-section-drag-start="handleSectionDragStart"
                  :handle-drag-end="handleDragEnd"
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
              <div
                v-if="isDesignMode"
                class="empty-canvas-actions"
              >
                <el-button
                  type="primary"
                  @click="addSection"
                >
                  {{ t('system.pageLayout.designer.actions.addSection') }}
                </el-button>
                <el-dropdown
                  v-if="detailRegionCanvasOptions.length > 0"
                  trigger="click"
                  @command="handleAddDetailRegionCommand"
                >
                  <el-button plain>
                    {{ detailRegionActionLabel }}
                  </el-button>
                  <template #dropdown>
                    <el-dropdown-menu>
                      <el-dropdown-item
                        v-for="option in detailRegionCanvasOptions"
                        :key="option.value"
                        :command="option.value"
                      >
                        {{ option.label }}
                      </el-dropdown-item>
                    </el-dropdown-menu>
                  </template>
                </el-dropdown>
              </div>
            </el-empty>
          </div>
        </DesignerCanvas>
      </section>

      <aside
        v-if="renderMode === 'design'"
        class="designer-pane designer-pane--right"
      >
        <div class="designer-right-stack">
          <div class="designer-right-stack__properties">
            <DesignerPropertyPanel
              :render-mode="renderMode"
              :selected-item="selectedItem"
              :element-type="elementType"
              :field-props="fieldProps"
              :section-props="sectionProps"
              :detail-region-options="aggregateDetailRegions"
              :detail-region-field-options="detailRegionFieldOptions"
              :available-spans="availableSpans"
              :available-span-columns="availableSpanColumns"
              :visibility-field-options="visibilityFieldOptions"
              :layout-mode="layoutMode"
              :mode="mode"
              :translation-mode="translationMode"
              @update:field-props="fieldProps = $event"
              @update:section-props="sectionProps = $event"
              @field-property-update="handleFieldPropertyUpdate"
              @section-property-update="handleSectionPropertyUpdate"
              @section-property-batch-update="handleSectionPropertyBatchUpdate"
              @section-preview-property="handleSectionPreviewProperty"
            />
          </div>
          <DesignerWorkbenchMetadataPanel
            v-if="props.mode !== 'search'"
            class="designer-right-stack__workbench"
            :metadata="designerWorkbenchMetadata"
            @update:metadata="handleWorkbenchMetadataUpdate"
          />
        </div>
      </aside>
    </div>

    <!-- History Panel Drawer -->
    <DesignerHistoryPanel
      v-model:visible="historyPanelVisible"
      :entries="historyEntries"
      :current-index="historyCurrentIndex"
      @go-to="handleHistoryGoTo"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import { dynamicApi } from '@/api/dynamic'
import DesignerToolbar from '@/components/designer/DesignerToolbar.vue'
import DesignerFieldPanel from '@/components/designer/DesignerFieldPanel.vue'
import DesignerPropertyPanel from '@/components/designer/DesignerPropertyPanel.vue'
import DesignerWorkbenchMetadataPanel from '@/components/designer/DesignerWorkbenchMetadataPanel.vue'
import DesignerCanvas from '@/components/designer/DesignerCanvas.vue'
import DesignerCanvasSectionRenderer from '@/components/designer/DesignerCanvasSectionRenderer.vue'
import DesignerSectionHeader from '@/components/designer/DesignerSectionHeader.vue'
import DesignerHistoryPanel from '@/components/designer/DesignerHistoryPanel.vue'
import BaseDetailPage from '@/components/common/BaseDetailPage.vue'
import { canAddFieldInDesigner, getFieldDisabledReason } from '@/platform/layout/designerFieldGuard'
import { buildDetailRegionPaletteOptions } from '@/components/designer/detailRegionPaletteOptions'
import {
  extractDetailRegionFieldOptions,
  type DetailRegionFieldOption
} from '@/components/designer/detailRegionFieldOptions'
import { useDesignerState } from '@/components/designer/useDesignerState'
import { useDesignerHistory } from '@/components/designer/useDesignerHistory'
import { useDesignerCanvasInteractions } from '@/components/designer/useDesignerCanvasInteractions'
import { useDesignerPalette } from '@/components/designer/useDesignerPalette'
import { useDesignerSelection } from '@/components/designer/useDesignerSelection'
import { useDesignerFieldEditing } from '@/components/designer/useDesignerFieldEditing'
import { useDesignerPersistence } from '@/components/designer/useDesignerPersistence'
import { useDesignerLifecycle } from '@/components/designer/useDesignerLifecycle'
import { useDesignerPreview } from '@/components/designer/useDesignerPreview'
import {
  applyDesignerSectionPreviewOverlay,
  resolveDetailRegionPreviewSectionId,
  type DesignerSectionPreviewOverlay
} from '@/components/designer/designerPreviewOverlay'
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
import {
  normalizeDesignerWorkbenchMetadata,
  serializeDesignerWorkbenchMetadata,
} from '@/components/designer/designerWorkbenchMetadata'
import type {
  DesignerAnyRecord,
  DesignerDetailRegionOption,
  DesignerFieldDefinition,
  DesignerSectionTemplateOption,
  LayoutConfig,
  LayoutField,
  LayoutSection,
  WysiwygDesignerProps
} from '@/components/designer/designerTypes'
import type { LayoutMode } from '@/types/layout'

type FieldDefinition = DesignerFieldDefinition

// ============================================================================
// Props & Emits
// ============================================================================

type Props = WysiwygDesignerProps

const translationMode = ref(false)
const viewport = ref<'desktop' | 'mobile'>('desktop')

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
  published: [data: LayoutConfig | Record<string, unknown>]
}>()
const { t, locale } = useI18n()
const tr = (key: string, fallback: string) => {
  const text = t(key, {})
  return text === key ? fallback : text
}

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
const sectionPreviewOverlay = ref<DesignerSectionPreviewOverlay | null>(null)

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
  aggregateDetailRegions,
  draggedDetailRegion,
  draggedSectionId,
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

// History panel state
const historyPanelVisible = ref(false)
const historyEntries = computed(() => history.entries.value)
const historyCurrentIndex = computed(() => history.currentIndex.value)
const handleHistoryGoTo = (index: number) => {
  history.goTo(index)
}
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

const designerSectionActionLabels = computed(() => ({
  moveUp: fallbackText('system.pageLayout.designer.actions.moveSectionUp', 'Move up'),
  moveDown: fallbackText('system.pageLayout.designer.actions.moveSectionDown', 'Move down'),
  reorder: fallbackText('system.pageLayout.designer.hints.dragToReorderSection', 'Drag to reorder section')
}))

const { filteredFieldGroups, normalizeAvailableFields } = useDesignerPalette({
  mode: computed(() => props.mode),
  availableFields,
  searchQuery
})

const detailRegionFieldOptionsByTarget = ref<Record<string, DetailRegionFieldOption[]>>({})
const detailRegionFieldLoadingTargets = new Set<string>()

const detailRegionFieldOptions = computed<Record<string, DetailRegionFieldOption[]>>(() => {
  const byRelation: Record<string, DetailRegionFieldOption[]> = {}
  for (const region of aggregateDetailRegions.value) {
    const relationCode = String(region?.relationCode || '').trim()
    const targetObjectCode = String(region?.targetObjectCode || '').trim()
    if (!relationCode) continue
    byRelation[relationCode] = detailRegionFieldOptionsByTarget.value[targetObjectCode] || []
  }
  return byRelation
})

const loadDetailRegionFieldOptions = async (targetObjectCode: string) => {
  const normalizedCode = String(targetObjectCode || '').trim()
  if (!normalizedCode) return
  if (detailRegionFieldOptionsByTarget.value[normalizedCode]) return
  if (detailRegionFieldLoadingTargets.has(normalizedCode)) return

  detailRegionFieldLoadingTargets.add(normalizedCode)
  try {
    const runtime = await dynamicApi.getRuntime(normalizedCode, 'edit', {
      include_relations: false
    })
    detailRegionFieldOptionsByTarget.value = {
      ...detailRegionFieldOptionsByTarget.value,
      [normalizedCode]: extractDetailRegionFieldOptions(runtime)
    }
  } catch {
    detailRegionFieldOptionsByTarget.value = {
      ...detailRegionFieldOptionsByTarget.value,
      [normalizedCode]: []
    }
  } finally {
    detailRegionFieldLoadingTargets.delete(normalizedCode)
  }
}

watch(
  aggregateDetailRegions,
  (regions) => {
    for (const region of regions || []) {
      const targetObjectCode = String(region?.targetObjectCode || '').trim()
      if (!targetObjectCode) continue
      void loadDetailRegionFieldOptions(targetObjectCode)
    }
  },
  { immediate: true, deep: true }
)

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
  layoutConfig: computed(() => applyDesignerSectionPreviewOverlay(layoutConfig.value, sectionPreviewOverlay.value)),
  sampleData,
  readComponentProps,
  readLayoutPlacement,
  resolveLayoutFieldMinHeight,
  getRenderColumns
})

const handleSectionPreviewProperty = (
  payload: { key: string; value: unknown } | { values: Partial<LayoutSection> } | null
) => {
  if (!payload || elementType.value !== 'section' || !selectedSection.value?.id) {
    sectionPreviewOverlay.value = null
    return
  }

  const overlayValue = 'values' in payload
    ? payload.values
    : ({
        [payload.key]: payload.value
      } as Partial<LayoutSection>)

  sectionPreviewOverlay.value = {
    sectionId: selectedSection.value.id,
    value: overlayValue
  }
}

const handleDetailRegionPalettePreview = (region: DesignerDetailRegionOption | null) => {
  if (!region?.preset) {
    sectionPreviewOverlay.value = null
    return
  }

  const previewSectionId = resolveDetailRegionPreviewSectionId(
    layoutConfig.value,
    region,
    selectedSection.value?.id || null
  )

  if (!previewSectionId) {
    sectionPreviewOverlay.value = null
    return
  }

  sectionPreviewOverlay.value = {
    sectionId: previewSectionId,
    value: region.preset
  }
}

watch([selectedId, elementType], () => {
  sectionPreviewOverlay.value = null
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
  addedFieldCodes,
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

const totalAvailableFieldCount = computed(() =>
  availableFields.value.filter((field) => canAddField(field) && field.code !== '$empty_space$').length
)
const assignedFieldCount = computed(() =>
  [...new Set(addedFieldCodes.value)].filter((code) => code !== '$empty_space$').length
)

const sectionTemplateOptions = computed<DesignerSectionTemplateOption[]>(() => {
  const query = searchQuery.value.trim().toLowerCase()
  const templates: DesignerSectionTemplateOption[] = [
    {
      templateCode: 'section-main',
      templateType: 'section',
      title: t('system.pageLayout.designer.templates.sectionMain.title'),
      description: t('system.pageLayout.designer.templates.sectionMain.description'),
      icon: 'section',
      preset: {
        position: 'main',
        columns: 2,
        collapsible: true,
        collapsed: false,
        border: true
      }
    },
    {
      templateCode: 'section-sidebar',
      templateType: 'section',
      title: t('system.pageLayout.designer.templates.sectionSidebar.title'),
      description: t('system.pageLayout.designer.templates.sectionSidebar.description'),
      icon: 'section',
      preset: {
        position: 'sidebar',
        columns: 1,
        collapsible: false,
        collapsed: false,
        border: false,
        labelPosition: 'top'
      }
    },
    {
      templateCode: 'tab-main',
      templateType: 'tab',
      title: t('system.pageLayout.designer.templates.tabMain.title'),
      description: t('system.pageLayout.designer.templates.tabMain.description'),
      icon: 'tab',
      preset: {
        position: 'main',
        columns: 2,
        collapsible: false,
        collapsed: false
      }
    },
    {
      templateCode: 'collapse-main',
      templateType: 'collapse',
      title: t('system.pageLayout.designer.templates.collapseMain.title'),
      description: t('system.pageLayout.designer.templates.collapseMain.description'),
      icon: 'collapse',
      preset: {
        position: 'main',
        columns: 2,
        collapsible: true,
        collapsed: false
      }
    }
  ]

  if (!query) return templates

  return templates.filter((template) =>
    template.title.toLowerCase().includes(query) ||
    String(template.description || '').toLowerCase().includes(query) ||
    template.templateCode.toLowerCase().includes(query) ||
    template.templateType.toLowerCase().includes(query)
  )
})

const countSectionFields = (config: LayoutConfig): { total: number; required: number } => {
  const countFields = (fields: LayoutField[] | undefined) =>
    (fields || []).reduce(
      (acc, field) => {
        if (!field || field.fieldType === 'empty' || field.fieldCode === '$empty_space$') return acc
        acc.total += 1
        if (field.required) acc.required += 1
        return acc
      },
      { total: 0, required: 0 }
    )

  return (config.sections || []).reduce(
    (acc, section) => {
      if (section.type === 'tab') {
        for (const tab of section.tabs || []) {
          const counts = countFields(tab.fields)
          acc.total += counts.total
          acc.required += counts.required
        }
        return acc
      }

      if (section.type === 'collapse') {
        for (const item of section.items || []) {
          const counts = countFields(item.fields)
          acc.total += counts.total
          acc.required += counts.required
        }
        return acc
      }

      const counts = countFields(section.fields)
      acc.total += counts.total
      acc.required += counts.required
      return acc
    },
    { total: 0, required: 0 }
  )
}

const canvasFieldStats = computed(() => countSectionFields(layoutConfig.value))
const canvasFieldCount = computed(() => canvasFieldStats.value.total)
const canvasRequiredFieldCount = computed(() => canvasFieldStats.value.required)
const canvasSectionCount = computed(() => (layoutConfig.value.sections || []).length)
const visibilityFieldOptions = computed(() =>
  availableFields.value
    .filter((field) => field.code !== '$empty_space$' && field.code !== fieldProps.value.fieldCode)
    .map((field) => ({
      label: String(field.name || field.displayName || field.code),
      value: String(field.code)
    }))
    .sort((a, b) => a.label.localeCompare(b.label))
)

const designerWorkbenchMetadata = computed(() => {
  const currentConfig = layoutConfig.value as LayoutConfig & {
    workbench?: DesignerAnyRecord
  }
  const workbench = currentConfig.workbench

  return normalizeDesignerWorkbenchMetadata(workbench)
})

const normalizedLocale = computed<'zh-CN' | 'en-US'>(() => {
  const raw = String(locale.value || 'zh-CN').toLowerCase()
  return raw.startsWith('en') ? 'en-US' : 'zh-CN'
})

const detailRegionCanvasOptions = computed(() =>
  buildDetailRegionPaletteOptions(
    aggregateDetailRegions.value,
    normalizedLocale.value,
    tr
  ).map((option) => ({
    label: option.title,
    value: option
  }))
)

const filteredDetailRegionOptions = computed<DesignerDetailRegionOption[]>(() => {
  const query = searchQuery.value.trim().toLowerCase()
  const options = buildDetailRegionPaletteOptions(
    aggregateDetailRegions.value,
    normalizedLocale.value,
    tr
  )

  if (!query) return options

  return options.filter((option) =>
    option.title.toLowerCase().includes(query) ||
    String(option.templateCode || '').toLowerCase().includes(query) ||
    option.relationCode.toLowerCase().includes(query) ||
    option.targetObjectCode.toLowerCase().includes(query) ||
    option.targetObjectLabel.toLowerCase().includes(query) ||
    String(option.description || '').toLowerCase().includes(query)
  )
})

const isDetailRegionAdded = (relationCode: string, fieldCode?: string) => {
  return (layoutConfig.value.sections || []).some((section) => {
    if (String(section?.type || '') !== 'detail-region') return false
    const sectionRelationCode = String(section?.relationCode || section?.relation_code || '').trim()
    const sectionFieldCode = String(section?.fieldCode || section?.field_code || '').trim()
    if (sectionRelationCode && sectionRelationCode === relationCode) return true
    if (fieldCode && sectionFieldCode === String(fieldCode || '').trim()) return true
    return false
  })
}

const detailRegionActionLabel = computed(() => `${t('common.actions.add')} ${t('system.pageLayout.designer.defaults.detailRegion')}`)

let showPropertySizeFeedbackFromCanvas: (fieldId: string) => Promise<void> | void = () => {}

const {
  addSection,
  addSectionTemplate,
  addDetailRegion,
  handleFieldClick,
  handleFieldPropertyUpdate,
  updateFieldLabel,
  updateSectionTitle,
  handleFieldSizeReset,
  handleSectionPropertyUpdate,
  handleSectionPropertyBatchUpdate,
  moveSection,
  moveSectionToIndex,
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
  sectionProps,
  detailRegionDefinitions: aggregateDetailRegions,
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

const handleAddDetailRegionCommand = (payload: string | number | object) => {
  if (payload && typeof payload === 'object' && 'relationCode' in payload) {
    addDetailRegion(payload as DesignerDetailRegionOption)
    return
  }
  if (typeof payload !== 'string' || !payload.trim()) return
  addDetailRegion(payload)
}

const handleWorkbenchMetadataUpdate = (metadata: unknown) => {
  const nextConfig = JSON.parse(JSON.stringify(layoutConfig.value || { sections: [] })) as LayoutConfig & {
    workbench?: DesignerAnyRecord
  }
  const workbench = (
    nextConfig.workbench &&
    typeof nextConfig.workbench === 'object' &&
    !Array.isArray(nextConfig.workbench)
  )
    ? { ...nextConfig.workbench }
    : {}

  nextConfig.workbench = {
    ...workbench,
    ...serializeDesignerWorkbenchMetadata(metadata),
  }

  commitLayoutChange(
    nextConfig,
    t('system.pageLayout.designer.messages.workbenchMetadataUpdated'),
  )
}

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
  handleSectionTemplateDragStart,
  handleDetailRegionDragStart,
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
} = useDesignerCanvasInteractions({
  layoutConfig,
  renderMode,
  isDesignMode,
  selectedId,
  fieldProps,
  draggedField,
  draggedDetailRegion,
  draggedSectionId,
  isDragOverCanvas,
  dragOverSection,
  canvasAreaElement: canvasAreaRef,
  canvasContentElement: canvasContentRef,
  canAddField,
  notifyUnsupportedField,
  handleFieldClick,
  addSectionTemplate,
  addDetailRegion,
  moveSectionToIndex,
  addFieldToContainer,
  commitLayoutChange,
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
  normalizeAndEnsureLayoutConfig,
  populateSampleData,
  loadLayout,
  setPreviewMode,
  handleSave,
  handlePublish,
  handleReset
} = useDesignerPersistence({
  props,
  availableFields,
  aggregateDetailRegions,
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
