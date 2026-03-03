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
    <!-- Toolbar -->
    <div class="designer-toolbar">
      <div class="toolbar-left">
        <el-button
          link
          @click="handleCancel"
        >
          <el-icon><ArrowLeft /></el-icon>
          {{ t('common.actions.back') }}
        </el-button>
        <el-divider direction="vertical" />
        <span class="layout-info">{{ layoutName }} ({{ modeLabel }})</span>
        <el-tag
          v-if="!isDefault"
          type="warning"
          size="small"
        >
          {{ t('system.pageLayout.designer.badges.customLayout') }}
        </el-tag>
      </div>
      <div class="toolbar-center">
        <el-button-group>
          <el-button
            data-testid="layout-undo-button"
            :disabled="!canUndo"
            @click="undo"
          >
            <el-icon><RefreshLeft /></el-icon>
            {{ t('system.pageLayout.designer.actions.undo') }}
          </el-button>
          <el-button
            data-testid="layout-redo-button"
            :disabled="!canRedo"
            @click="redo"
          >
            <el-icon><RefreshRight /></el-icon>
            {{ t('system.pageLayout.designer.actions.redo') }}
          </el-button>
        </el-button-group>
      </div>
      <div class="toolbar-right">
        <el-button
          data-testid="layout-reset-button"
          @click="handleReset"
        >
          {{ t('system.pageLayout.designer.actions.reset') }}
        </el-button>
        <el-button-group>
          <el-button
            size="small"
            data-testid="layout-preview-current-button"
            :disabled="previewLoading"
            :type="previewMode === 'current' ? 'primary' : 'default'"
            @click="setPreviewMode('current')"
          >
            {{ t('system.pageLayout.designer.actions.custom') }}
          </el-button>
          <el-button
            size="small"
            data-testid="layout-preview-active-button"
            :loading="previewLoading && previewMode === 'active'"
            :disabled="previewLoading"
            :type="previewMode === 'active' ? 'primary' : 'default'"
            @click="setPreviewMode('active')"
          >
            {{ t('system.pageLayout.designer.actions.preview') }}
          </el-button>
        </el-button-group>
        <el-tag
          size="small"
          effect="plain"
        >
          {{ previewMode === 'active' ? t('system.pageLayout.designer.status.previewMode') : t('system.pageLayout.designer.status.customMode') }}
        </el-tag>
        <el-button
          :disabled="previewMode === 'active'"
          data-testid="layout-save-button"
          @click="handleSave"
        >
          {{ t('system.pageLayout.designer.actions.saveDraft') }}
        </el-button>
        <el-button
          type="success"
          :loading="publishing"
          :disabled="previewMode === 'active'"
          data-testid="layout-publish-button"
          @click="handlePublish"
        >
          {{ t('system.pageLayout.designer.actions.publish') }}
        </el-button>
      </div>
    </div>

    <!-- Main Area -->
    <div class="designer-main">
      <!-- Left Panel - Field List -->
      <div
        v-if="renderMode === 'design'"
        class="field-panel"
        data-testid="layout-field-panel"
      >
        <div class="panel-header">
          <el-input
            v-model="searchQuery"
            :placeholder="t('system.pageLayout.designer.placeholders.searchField')"
            :prefix-icon="Search"
            size="small"
            clearable
          />
        </div>
        <div class="panel-content">
          <div
            v-for="group in filteredFieldGroups"
            :key="group.type"
            class="field-group"
          >
            <div
              class="group-header"
              @click="toggleGroup(group.type)"
            >
              <el-icon>
                <component :is="group.icon" />
              </el-icon>
              <span>{{ group.label }}</span>
              <el-tag size="small">
                {{ group.fields.length }}
              </el-tag>
              <el-icon
                class="expand-icon"
                :class="{ expanded: isGroupExpanded(group.type) }"
              >
                <ArrowRight />
              </el-icon>
            </div>
            <div
              v-show="isGroupExpanded(group.type)"
              class="group-fields"
            >
              <div
                v-for="field in group.fields"
                :key="field.code"
                class="palette-field-item"
                :data-testid="`layout-palette-field-${field.code}`"
                :draggable="canAddField(field)"
                :title="getDisabledReason(field) || ''"
                :class="{
                  'is-selected': isFieldAdded(field.code),
                  'is-disabled': !canAddField(field)
                }"
                @dragstart="handleFieldDragStart($event, field)"
                @dragend="handleDragEnd"
                @click="handleFieldClick(field)"
              >
                <el-icon class="field-icon">
                  <Edit />
                </el-icon>
                <span class="field-label">{{ field.name }}</span>
                <span class="field-code">{{ field.code }}</span>
                <el-icon
                  v-if="isFieldAdded(field.code)"
                  class="added-icon"
                >
                  <Check />
                </el-icon>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Center Canvas - Real-time Preview Area -->
      <div
        class="canvas-area"
        data-testid="layout-canvas"
        :class="{ 'drag-over': isDragOverCanvas }"
        @drop="handleCanvasDrop"
        @dragover="handleCanvasDragOver"
        @dragleave="handleCanvasDragLeave"
      >
        <div class="canvas-header">
          <div class="canvas-header-left">
            <span v-if="renderMode === 'design'">{{ t('system.pageLayout.designer.hints.designCanvas') }}</span>
            <span v-else>{{ t('system.pageLayout.designer.hints.previewCanvas') }}</span>
          </div>
          <div class="canvas-header-right">
            <el-radio-group
              :model-value="renderMode"
              size="small"
              @update:model-value="setRenderMode"
            >
              <el-radio-button label="design">
                <span data-testid="layout-render-design-button">
                {{ t('system.pageLayout.designer.status.designState') }}
                </span>
              </el-radio-button>
              <el-radio-button label="preview">
                <span data-testid="layout-render-preview-button">
                {{ t('system.pageLayout.designer.status.previewState') }}
                </span>
              </el-radio-button>
            </el-radio-group>
            <el-button
              v-if="renderMode === 'design'"
              size="small"
              text
              @click="addSection"
            >
              <el-icon><Plus /></el-icon>
              {{ t('system.pageLayout.designer.actions.addSection') }}
            </el-button>
          </div>
        </div>
        <div
          ref="canvasContentRef"
          class="canvas-content"
        >
          <div class="canvas-render-shell">
            <!-- Render the actual form using real components -->
            <div
              v-if="layoutConfig.sections && layoutConfig.sections.length > 0"
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
                :object-code="objectCode"
                :object-name="previewObjectName"
                :reverse-relations="previewReverseRelations"
                @section-click="maybeSelectSection"
              >
                <template
                  v-for="(section, sectionIndex) in (layoutConfig.sections || [])"
                  :key="`slot-${section.id}`"
                  #[`section-${section.id}`]
                >
                  <div
                    class="designer-section-slot layout-section"
                    data-testid="layout-section"
                    :class="{ 'is-selected': isDesignMode && selectedId === section.id }"
                    :data-section-id="section.id"
                    :data-section-position="section.position"
                    @click.stop="maybeSelectSection(section.id)"
                  >
                    <div
                      v-if="isDesignMode && selectedId === section.id"
                      class="designer-section-toolbar"
                      @click.stop
                    >
                      <el-button
                        size="small"
                        text
                        @click="selectSection(section.id)"
                      >
                        {{ t('system.pageLayout.designer.actions.editSection') }}
                      </el-button>
                      <el-button
                        v-if="section.collapsible"
                        size="small"
                        text
                        @click="toggleSectionCollapse(section.id)"
                      >
                        {{ section.collapsed ? t('common.actions.expand') : t('common.actions.collapse') }}
                      </el-button>
                      <el-button
                        size="small"
                        text
                        type="danger"
                        @click="deleteSection(section.id)"
                      >
                        {{ t('system.pageLayout.designer.actions.deleteSection') }}
                      </el-button>
                    </div>

                    <template v-if="section.type === 'tab'">
                      <el-tabs
                        v-model="activeTabs[section.id]"
                        type="card"
                      >
                        <el-tab-pane
                          v-for="tab in section.tabs"
                          :key="tab.id"
                          :label="tab.title"
                          :name="tab.id"
                          class="tab-pane-content"
                          :data-tab-id="tab.id"
                          :data-section-id="section.id"
                          @drop="handleTabDrop"
                          @dragover="handleSectionDragOver"
                          @dragleave="handleSectionDragLeave"
                        >
                          <el-row
                            :gutter="24"
                            class="tab-fields designer-fields-container dynamic-form-section__fields"
                            data-container-kind="tab"
                            :data-section-id="section.id"
                            :data-tab-id="tab.id"
                          >
                            <el-col
                              v-for="field in tab.fields"
                              :key="field.id"
                              class="field-renderer field-col"
                              :span="getDetailSpan(field, section)"
                              :data-field-id="field.id"
                              :data-field-code="field.fieldCode"
                            >
                              <DesignerFieldCard
                                :field="field"
                                :display-field="fieldToDesignDisplayField(field)"
                                :value="sampleData[field.fieldCode] ?? getSampleValue(field)"
                                :selected="isDesignMode && selectedId === field.id"
                                :interactive="isDesignMode"
                                :section-id="section.id"
                                :section-index="sectionIndex"
                                @select="maybeSelectField(field, section)"
                                @remove="removeField"
                              />
                            </el-col>
                            <el-col
                              v-if="!tab.fields || tab.fields.length === 0"
                              :span="24"
                              class="empty-column-placeholder compact"
                            >
                              {{ t('system.pageLayout.designer.hints.dropToTab') }}
                            </el-col>
                          </el-row>
                        </el-tab-pane>
                      </el-tabs>
                    </template>

                    <template v-else-if="section.type === 'collapse'">
                      <el-collapse
                        v-model="activeCollapses[section.id]"
                        :accordion="false"
                      >
                        <el-collapse-item
                          v-for="item in section.items"
                          :key="item.id"
                          :name="item.id"
                          :data-collapse-id="item.id"
                        >
                          <template #title>
                            <span>{{ item.title }}</span>
                          </template>
                          <div
                            class="collapse-fields dynamic-form-section__fields"
                            data-container-kind="collapse"
                            :data-section-id="section.id"
                            :data-collapse-id="item.id"
                            @drop="handleCollapseDrop"
                            @dragover="handleSectionDragOver"
                            @dragleave="handleSectionDragLeave"
                          >
                            <el-row
                              :gutter="24"
                              class="designer-fields-container"
                              data-container-kind="collapse"
                              :data-section-id="section.id"
                              :data-collapse-id="item.id"
                            >
                              <el-col
                                v-for="field in item.fields"
                                :key="field.id"
                                class="field-renderer field-col"
                                :span="getDetailSpan(field, section)"
                                :data-field-id="field.id"
                                :data-field-code="field.fieldCode"
                              >
                                <DesignerFieldCard
                                  :field="field"
                                  :display-field="fieldToDesignDisplayField(field)"
                                  :value="sampleData[field.fieldCode] ?? getSampleValue(field)"
                                  :selected="isDesignMode && selectedId === field.id"
                                  :interactive="isDesignMode"
                                  :section-id="section.id"
                                  :section-index="sectionIndex"
                                  @select="maybeSelectField(field, section)"
                                  @remove="removeField"
                                />
                              </el-col>
                            </el-row>
                            <el-col
                              v-if="!item.fields || item.fields.length === 0"
                              :span="24"
                              class="empty-column-placeholder compact"
                            >
                              {{ t('system.pageLayout.designer.hints.dropToCollapse') }}
                            </el-col>
                          </div>
                        </el-collapse-item>
                      </el-collapse>
                    </template>

                    <template v-else>
                      <div
                        class="designer-section-body"
                        :data-section-id="section.id"
                        @drop="handleSectionDrop"
                        @dragover="handleSectionDragOver"
                        @dragleave="handleSectionDragLeave"
                      >
                        <template v-if="section.position === 'sidebar'">
                          <div
                            class="section-fields-sidebar designer-fields-container dynamic-form-section__fields"
                            data-container-kind="section"
                            :data-section-id="section.id"
                          >
                            <div
                              v-for="field in section.fields"
                              :key="field.id"
                              class="field-renderer field-col sidebar-field-col"
                              :data-field-id="field.id"
                              :data-field-code="field.fieldCode"
                            >
                              <DesignerFieldCard
                                :field="field"
                                :display-field="fieldToDesignDisplayField(field)"
                                :value="sampleData[field.fieldCode] ?? getSampleValue(field)"
                                :selected="isDesignMode && selectedId === field.id"
                                :interactive="isDesignMode"
                                :sidebar="true"
                                :section-id="section.id"
                                :section-index="sectionIndex"
                                @select="maybeSelectField(field, section)"
                                @remove="removeField"
                              />
                            </div>
                            <el-col
                              v-if="!section.fields || section.fields.length === 0"
                              :span="24"
                              class="empty-column-placeholder compact"
                            >
                              {{ t('system.pageLayout.designer.hints.dropToSection') }}
                            </el-col>
                          </div>
                        </template>
                        <template v-else>
                          <el-row
                            :gutter="24"
                            class="section-fields designer-fields-container dynamic-form-section__fields"
                            data-container-kind="section"
                            :data-section-id="section.id"
                          >
                            <el-col
                              v-for="field in section.fields"
                              :key="field.id"
                              class="field-renderer field-col"
                              :span="getDetailSpan(field, section)"
                              :data-field-id="field.id"
                              :data-field-code="field.fieldCode"
                            >
                              <DesignerFieldCard
                                :field="field"
                                :display-field="fieldToDesignDisplayField(field)"
                                :value="sampleData[field.fieldCode] ?? getSampleValue(field)"
                                :selected="isDesignMode && selectedId === field.id"
                                :interactive="isDesignMode"
                                :section-id="section.id"
                                :section-index="sectionIndex"
                                @select="maybeSelectField(field, section)"
                                @remove="removeField"
                              />
                            </el-col>
                            <div
                              v-if="!section.fields || section.fields.length === 0"
                              class="empty-column-placeholder compact"
                            >
                              {{ t('system.pageLayout.designer.hints.dropToSection') }}
                            </div>
                          </el-row>
                        </template>
                      </div>
                    </template>
                  </div>
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
          </div>
        </div>
      </div>

      <!-- Right Panel - Property Editor -->
      <div
        v-if="renderMode === 'design'"
        class="property-panel"
        data-testid="layout-property-panel"
      >
        <div class="panel-header">
          <span>{{ t('system.pageLayout.designer.panel.properties') }}</span>
        </div>
        <div class="panel-content">
          <!-- No Selection -->
          <div
            v-if="!selectedItem"
            class="no-selection"
          >
            <el-empty
              :description="t('system.pageLayout.designer.empty.selectTarget')"
              :image-size="80"
            />
          </div>

          <!-- Field Properties -->
          <div
            v-else-if="elementType === 'field'"
            class="property-form"
          >
            <div class="property-header">
              <el-icon><Edit /></el-icon>
              <span>{{ t('system.pageLayout.designer.panel.fieldProperties') }}</span>
              <el-tag size="small">
                {{ selectedItem.fieldCode }}
              </el-tag>
            </div>
            <FieldPropertyEditor
              v-model="fieldProps"
              data-testid="layout-field-property-editor"
              :field-type="fieldProps.fieldType"
              :mode="mode"
              :available-spans="availableSpans"
              :available-span-columns="availableSpanColumns"
              @update-property="handleFieldPropertyUpdate"
            />
          </div>

          <!-- Section Properties -->
          <div
            v-else-if="elementType === 'section'"
            class="property-form"
          >
            <div class="property-header">
              <el-icon><Grid /></el-icon>
              <span>{{ t('system.pageLayout.designer.panel.sectionProperties') }}</span>
            </div>
            <SectionPropertyEditor
              v-model="sectionProps"
              data-testid="layout-section-property-editor"
              :section-type="sectionProps.type || 'section'"
              @update-property="handleSectionPropertyUpdate"
            />
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted, watch, nextTick } from 'vue'
import { useI18n } from 'vue-i18n'
import { ElMessage, ElMessageBox } from 'element-plus'
import Sortable from 'sortablejs'
import {
  ArrowLeft, ArrowRight, Search, Plus, Check, RefreshLeft, RefreshRight,
  Edit, Grid, Document, Histogram, Calendar, Timer,
  Message, Link, Connection, User, OfficeBuilding, Folder, Picture, Select,
  CircleCheck, Ticket, FolderOpened
} from '@element-plus/icons-vue'
import FieldPropertyEditor from '@/components/designer/FieldPropertyEditor.vue'
import SectionPropertyEditor from '@/components/designer/SectionPropertyEditor.vue'
import DesignerFieldCard from '@/components/designer/DesignerFieldCard.vue'
import BaseDetailPage, { type DetailSection, type DetailField, type ReverseRelationField } from '@/components/common/BaseDetailPage.vue'
import { dynamicApi } from '@/api/dynamic'
import { pageLayoutApi } from '@/api/system'
import { useLayoutHistory } from '@/composables/useLayoutHistory'
import { normalizeFieldType } from '@/utils/fieldType'
import { resolveRuntimeLayout } from '@/platform/layout/runtimeLayoutResolver'
import { normalizeDetailSpan, toUnifiedDetailField } from '@/platform/layout/unifiedDetailField'
import { toRuntimeFieldFromLayout } from '@/platform/layout/unifiedRuntimeField'
import { canAddFieldInDesigner, getFieldDisabledReason } from '@/platform/layout/designerFieldGuard'
import { ensureLayoutConfigIds as ensurePersistLayoutConfigIds, preparePersistLayoutConfig } from '@/platform/layout/layoutPersistGuard'
import { mergeFieldSources } from '@/platform/layout/unifiedFieldOrder'
import {
  getDefaultLayoutConfig,
  cloneLayoutConfig,
  generateId,
  type LayoutType
} from '@/utils/layoutValidation'
import { normalizeLayoutType } from '@/utils/layoutMode'
import type { LayoutFieldConfig } from '@/types/metadata'
import type { LayoutMode } from '@/types/layout'
import type { FieldDefinition as RuntimeFieldDefinition } from '@/types'

// ============================================================================
// Types
// ============================================================================

interface FieldDefinition {
  code: string
  name: string
  fieldType: string
  isRequired?: boolean
  isReadonly?: boolean
  isSystem?: boolean
  isSearchable?: boolean
  showInList?: boolean
  showInForm?: boolean
  showInDetail?: boolean
  // Field metadata for proper rendering
  options?: Array<{ value: any; label: string }>
  referenceObject?: string
  relatedObject?: string
  componentProps?: Record<string, any>
  dictionaryType?: string
  defaultValue?: any
  placeholder?: string
  helpText?: string
}

// Use LayoutFieldConfig from @/types/metadata for fields with full metadata
// This local interface is kept for backward compatibility but extends the concept
interface LayoutField extends Omit<LayoutFieldConfig, 'fieldType'> {
  fieldType?: string // Make fieldType optional for backward compatibility
  // Additional properties that may come from legacy layouts
  min_length?: number
  max_length?: number
  min_value?: number
  max_value?: number
  regex_pattern?: string
}

interface LayoutSection {
  id: string
  type: string
  title?: string
  collapsible?: boolean
  collapsed?: boolean
  border?: boolean
  columns?: number
  position?: 'main' | 'sidebar'
  fields?: LayoutField[]
  tabs?: LayoutTab[]
  items?: LayoutCollapseItem[]
}

interface LayoutTab {
  id: string
  title: string
  fields?: LayoutField[]
}

interface LayoutCollapseItem {
  id: string
  title: string
  fields?: LayoutField[]
}

interface LayoutConfig {
  sections?: LayoutSection[]
  columns?: any[]
  actions?: any[]
  modeOverrides?: Record<string, any>
  layoutOverrides?: Record<string, any>
}

interface FieldGroup {
  type: string
  label: string
  icon: string
  color?: string
  fields: FieldDefinition[]
}

// ============================================================================
// Props & Emits
// ============================================================================

interface Props {
  layoutId?: string
  mode?: LayoutMode
  objectCode?: string
  layoutName?: string
  businessObjectId?: string
  initialPreviewMode?: 'current' | 'active'
  layoutConfig?: LayoutConfig
}

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
const { t } = useI18n()

// ============================================================================
// State
// ============================================================================

const layoutConfig = ref<LayoutConfig>(
  normalizeAndEnsureLayoutConfig(getDefaultLayoutConfig(props.mode) as LayoutConfig)
)
const selectedId = ref<string>('')
const renderMode = ref<'design' | 'preview'>('design')
const isDesignMode = computed(() => renderMode.value === 'design')
const previewMode = ref<'current' | 'active'>('current')
const currentLayoutSnapshot = ref<LayoutConfig | null>(null)
const previewLoading = ref(false)
const selectedSection = ref<LayoutSection | null>(null)
const saving = ref(false)
const publishing = ref(false)
const searchQuery = ref('')
const expandedGroups = ref<Set<string>>(new Set(['text', 'number', 'select']))

const isDefault = ref(false)
const isPublished = ref(false)
const layoutVersion = ref('1.0.0')
const sharedEditLayoutId = ref('')

// Track field drag source
const draggedField = ref<FieldDefinition | null>(null)
const isDragOverCanvas = ref(false)
const dragOverSection = ref<string | null>(null)

// Available fields
const availableFields = ref<FieldDefinition[]>([])
const previewReverseRelations = ref<ReverseRelationField[]>([])

// Sample data for preview
const sampleData = ref<Record<string, any>>({})
const canvasContentRef = ref<HTMLElement | null>(null)

type ContainerKind = 'section' | 'tab' | 'collapse'
type ContainerMeta = {
  kind: ContainerKind
  sectionId: string
  tabId?: string
  collapseId?: string
}

let sortableInstances: Sortable[] = []

const destroySortables = () => {
  for (const inst of sortableInstances) inst.destroy()
  sortableInstances = []
}

const parseContainerMeta = (el: HTMLElement | null): ContainerMeta | null => {
  if (!el) return null
  const kind = (el.dataset.containerKind || '') as ContainerKind
  const sectionId = el.dataset.sectionId || ''

  if (!kind || !sectionId) return null
  if (kind === 'tab') {
    const tabId = el.dataset.tabId || ''
    if (!tabId) return null
    return { kind, sectionId, tabId }
  }
  if (kind === 'collapse') {
    const collapseId = el.dataset.collapseId || ''
    if (!collapseId) return null
    return { kind, sectionId, collapseId }
  }
  return { kind: 'section', sectionId }
}

const getFieldArrayRef = (config: LayoutConfig, meta: ContainerMeta): LayoutField[] | null => {
  const section = (config.sections || []).find((s) => s.id === meta.sectionId)
  if (!section) return null

  if (meta.kind === 'section') {
    section.fields = section.fields || []
    return section.fields
  }

  if (meta.kind === 'tab') {
    section.tabs = section.tabs || []
    const tab = (section.tabs || []).find((t) => t.id === meta.tabId)
    if (!tab) return null
    tab.fields = tab.fields || []
    return tab.fields
  }

  if (meta.kind === 'collapse') {
    section.items = section.items || []
    const item = (section.items || []).find((i) => i.id === meta.collapseId)
    if (!item) return null
    item.fields = item.fields || []
    return item.fields
  }

  return null
}

const applySortableMove = (evt: any) => {
  const fromMeta = parseContainerMeta(evt?.from as HTMLElement)
  const toMeta = parseContainerMeta(evt?.to as HTMLElement)
  const oldIndex = typeof evt?.oldIndex === 'number' ? evt.oldIndex : null
  const newIndex = typeof evt?.newIndex === 'number' ? evt.newIndex : null

  if (!fromMeta || !toMeta) return
  if (oldIndex === null || newIndex === null) return

  const previousConfig = cloneLayoutConfig(layoutConfig.value)
  const newConfig = cloneLayoutConfig(layoutConfig.value) as LayoutConfig
  const fromArr = getFieldArrayRef(newConfig, fromMeta)
  const toArr = getFieldArrayRef(newConfig, toMeta)
  if (!fromArr || !toArr) return

  // Prefer index-based move (matches DOM order), fallback to id match for safety.
  const moved =
    fromArr[oldIndex] ||
    fromArr.find((f) => f?.id && (evt?.item as HTMLElement | undefined)?.dataset?.fieldId === f.id)

  if (!moved) return

  const removeIndex = fromArr.indexOf(moved)
  if (removeIndex >= 0) fromArr.splice(removeIndex, 1)

  const insertIndex = Math.max(0, Math.min(newIndex, toArr.length))
  toArr.splice(insertIndex, 0, moved)

  commitLayoutChange(newConfig, `Move field ${moved.fieldCode || moved.id}`, previousConfig)
}

const initSortables = async () => {
  if (renderMode.value !== 'design') {
    destroySortables()
    return
  }

  await nextTick()
  destroySortables()

  const root = canvasContentRef.value
  if (!root) return

  const containers = Array.from(root.querySelectorAll<HTMLElement>('.designer-fields-container'))
  for (const container of containers) {
    const inst = Sortable.create(container, {
      group: { name: 'layout-fields', pull: true, put: true },
      animation: 180,
      draggable: '.field-renderer',
      // Avoid grabbing from inputs; drag from labels/empty area instead.
      filter: 'input, textarea, button, select, option, .el-input, .el-textarea, .el-select, .el-date-editor',
      preventOnFilter: true,
      onEnd: applySortableMove
    })
    sortableInstances.push(inst)
  }
}

function getColumns(section: any): number {
  return Number(section?.columns || section?.columnCount || section?.column || 2) || 2
}

function getDetailSpan(field: any, section: any): number {
  return normalizeDetailSpan(field?.span ?? 1, getColumns(section))
}

// Active tabs and collapses state
const activeTabs = ref<Record<string, string>>({})
const activeCollapses = ref<Record<string, string[]>>({})

// History management
const history = useLayoutHistory(layoutConfig, { maxHistory: 50 })
const { canUndo, canRedo, undo, redo, historyLength } = history

function commitLayoutChange(newConfig: LayoutConfig, description: string, previousConfig?: LayoutConfig) {
  if (historyLength.value === 0) {
    const baseline = cloneLayoutConfig(previousConfig || layoutConfig.value) as Record<string, unknown>
    history.push(baseline, 'Initial state')
  }
  layoutConfig.value = newConfig
  history.push(newConfig as unknown as Record<string, unknown>, description)
}

// Property form state
const fieldProps = ref<Partial<LayoutField>>({})
const sectionProps = ref<Partial<LayoutSection>>({})

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

const selectedItem = computed(() => {
  if (!selectedId.value) return null
  return findItemById(layoutConfig.value, selectedId.value)
})

const elementType = computed(() => {
  if (!selectedItem.value) return null
  if ('fieldCode' in selectedItem.value) return 'field'
  // Treat all non-field nodes in the canvas as section-like for property editing.
  // This covers regular sections as well as tab/collapse container sections.
  if ('columns' in selectedItem.value || 'fields' in selectedItem.value || 'tabs' in selectedItem.value || 'items' in selectedItem.value) return 'section'
  return 'section'
})

const availableSpanColumns = computed(() => {
  return selectedSection.value ? getColumns(selectedSection.value) : 2
})

const availableSpans = computed(() => {
  const columns = availableSpanColumns.value
  return Array.from({ length: columns }, (_, index) => index + 1)
})

const addedFieldCodes = computed(() => {
  const codes: string[] = []
  for (const section of layoutConfig.value.sections || []) {
    if (section.type === 'tab') {
      for (const tab of section.tabs || []) {
        for (const field of tab.fields || []) {
          codes.push(field.fieldCode)
        }
      }
    } else if (section.type === 'collapse') {
      for (const item of section.items || []) {
        for (const field of item.fields || []) {
          codes.push(field.fieldCode)
        }
      }
    } else {
      for (const field of section.fields || []) {
        codes.push(field.fieldCode)
      }
    }
  }
  return codes
})

// Group metadata for field types
const groupMetadata: Record<string, { label: string; icon: any; color: string }> = {
  text: { label: 'Text', icon: Edit, color: '#409eff' },
  textarea: { label: 'Textarea', icon: Document, color: '#409eff' },
  rich_text: { label: 'Rich Text', icon: Document, color: '#409eff' },
  number: { label: 'Number', icon: Histogram, color: '#67c23a' },
  boolean: { label: 'Boolean', icon: CircleCheck, color: '#67c23a' },
  date: { label: 'Date', icon: Calendar, color: '#e6a23c' },
  datetime: { label: 'DateTime', icon: Timer, color: '#e6a23c' },
  email: { label: 'Email', icon: Message, color: '#409eff' },
  url: { label: 'URL', icon: Link, color: '#409eff' },
  reference: { label: 'Reference', icon: Connection, color: '#909399' },
  user: { label: 'User', icon: User, color: '#f56c6c' },
  department: { label: 'Department', icon: OfficeBuilding, color: '#f56c6c' },
  file: { label: 'File', icon: Folder, color: '#e6a23c' },
  image: { label: 'Image', icon: Picture, color: '#e6a23c' },
  select: { label: 'Select', icon: Select, color: '#67c23a' },
  multi_select: { label: 'Multi Select', icon: Select, color: '#67c23a' },
  radio: { label: 'Radio', icon: CircleCheck, color: '#67c23a' },
  checkbox: { label: 'Checkbox', icon: Check, color: '#67c23a' },
  sub_table: { label: 'Sub Table', icon: FolderOpened, color: '#909399' },
  formula: { label: 'Formula', icon: Ticket, color: '#9c27b0' }
}

const fieldGroups = computed<FieldGroup[]>(() => {
  const groups: Record<string, FieldGroup> = {}

  availableFields.value.forEach(field => {
    let groupType = normalizeFieldType(field.fieldType || 'text')

    if (groupType === 'currency' || groupType === 'percent' || groupType === 'slider' || groupType === 'rate') {
      groupType = 'number'
    }
    if (groupType === 'year' || groupType === 'month' || groupType === 'time' || groupType === 'daterange') {
      groupType = 'date'
    }
    if (groupType === 'location' || groupType === 'asset') {
      groupType = 'reference'
    }

    const metadata = groupMetadata[groupType] || { label: groupType, icon: Edit, color: '#909399' }

    if (!groups[groupType]) {
      groups[groupType] = {
        type: groupType,
        label: metadata.label,
        icon: metadata.icon,
        color: metadata.color,
        fields: []
      }
    }
    groups[groupType].fields.push(field)
  })

  return Object.values(groups)
})

// Filter groups by search query
const filteredFieldGroups = computed(() => {
  if (!searchQuery.value) return fieldGroups.value

  const query = searchQuery.value.toLowerCase()
  return fieldGroups.value
    .map(group => ({
      ...group,
      fields: group.fields.filter(f =>
        f.name?.toLowerCase().includes(query) ||
        f.code?.toLowerCase().includes(query)
      )
    }))
    .filter(group => group.fields.length > 0)
})

// ============================================================================
// Methods
// ============================================================================

function findItemById(config: LayoutConfig, id: string): any {
  for (const section of config.sections || []) {
    if (section.id === id) return section
    if (section.type === 'tab') {
      for (const tab of section.tabs || []) {
        if (tab.id === id) return tab
        for (const field of tab.fields || []) {
          if (field.id === id) return field
        }
      }
    } else if (section.type === 'collapse') {
      for (const item of section.items || []) {
        if (item.id === id) return item
        for (const field of item.fields || []) {
          if (field.id === id) return field
        }
      }
    } else {
      for (const field of section.fields || []) {
        if (field.id === id) return field
      }
    }
  }
  return null
}

function fieldToDesignDisplayField(field: LayoutField): DetailField {
  const runtimeField = toRuntimeFieldFromLayout(field as any, availableFields.value as any[])
  const detailField = toUnifiedDetailField(runtimeField as any) as DetailField
  detailField.prop = field.fieldCode
  detailField.label = field.label || detailField.label || field.fieldCode
  return detailField
}

/**
 * Generate a sample value by canonical field type.
 */
function getSampleValue(field: LayoutField): any {
  const type = normalizeFieldType(field.fieldType || 'text')
  const label = field.label || ''
  const code = field.fieldCode || ''

  if (field.defaultValue !== undefined) return field.defaultValue

  const labelLower = label.toLowerCase()
  const codeLower = code.toLowerCase()

  if (codeLower.includes('name') || labelLower.includes('name')) {
    return 'Sample Name'
  }
  if (codeLower.includes('code') || labelLower.includes('code')) {
    return 'CODE001'
  }

  const sampleValues: Record<string, any> = {
    text: label || 'Sample Text',
    textarea: `${label || 'Sample'} details`,
    rich_text: `<p>${label || 'Sample rich text'}</p>`,
    number: 100,
    percent: 15.5,
    currency: 9999.99,
    boolean: true,
    date: '2024-01-15',
    datetime: '2024-01-15 14:30:00',
    time: '14:30:00',
    year: '2024',
    month: '2024-01',
    select: 'option-1',
    multi_select: ['option-1', 'option-2'],
    radio: 'option-1',
    checkbox: true,
    reference: null,
    user: null,
    department: null,
    location: null,
    asset: null,
    image: null,
    file: null,
    attachment: null,
    formula: 0,
    sub_table: []
  }

  return sampleValues[type] !== undefined ? sampleValues[type] : label || ''
}

const iterateLayoutFields = (config: LayoutConfig): LayoutField[] => {
  const out: LayoutField[] = []
  for (const section of config.sections || []) {
    if (section.type === 'tab') {
      for (const tab of section.tabs || []) out.push(...(tab.fields || []))
      continue
    }
    if (section.type === 'collapse') {
      for (const item of section.items || []) out.push(...(item.fields || []))
      continue
    }
    out.push(...(section.fields || []))
  }
  return out.filter((field) => !!field?.fieldCode)
}

const previewFieldDefinitions = computed<RuntimeFieldDefinition[]>(() => {
  const map = new Map<string, RuntimeFieldDefinition>()

  const register = (code: string, seed: Partial<RuntimeFieldDefinition>) => {
    const normalizedCode = String(code || '').trim()
    if (!normalizedCode) return
    const current = map.get(normalizedCode)
    const next: RuntimeFieldDefinition = {
      code: normalizedCode,
      name: seed.name || seed.label || normalizedCode,
      label: seed.label || seed.name || normalizedCode,
      fieldType: normalizeFieldType((seed.fieldType as string) || 'text') as RuntimeFieldDefinition['fieldType'],
      isRequired: seed.isRequired ?? false,
      isReadonly: seed.isReadonly ?? false,
      isHidden: seed.isHidden ?? false,
      showInForm: seed.showInForm ?? true,
      showInDetail: seed.showInDetail ?? true,
      options: seed.options || [],
      span: seed.span,
      defaultValue: seed.defaultValue,
      placeholder: seed.placeholder,
      helpText: seed.helpText,
      referenceObject: seed.referenceObject,
      componentProps: seed.componentProps || {},
      ...(current || {})
    }
    map.set(normalizedCode, { ...next, ...(seed as RuntimeFieldDefinition) })
  }

  for (const field of availableFields.value) {
    register(field.code, {
      name: field.name,
      label: field.name,
      fieldType: field.fieldType as RuntimeFieldDefinition['fieldType'],
      isRequired: field.isRequired,
      isReadonly: field.isReadonly,
      showInForm: field.showInForm ?? true,
      showInDetail: field.showInDetail ?? true,
      options: field.options as any,
      defaultValue: field.defaultValue,
      placeholder: field.placeholder,
      helpText: field.helpText,
      referenceObject: field.referenceObject || field.relatedObject,
      componentProps: field.componentProps || {}
    })
  }

  for (const field of iterateLayoutFields(layoutConfig.value)) {
    register(field.fieldCode, {
      name: field.label || field.fieldCode,
      label: field.label || field.fieldCode,
      fieldType: normalizeFieldType(field.fieldType || 'text') as RuntimeFieldDefinition['fieldType'],
      isRequired: !!field.required,
      isReadonly: !!field.readonly,
      isHidden: field.visible === false,
      showInForm: field.visible !== false,
      showInDetail: field.visible !== false,
      options: (field.options || []) as any,
      span: field.span,
      defaultValue: field.defaultValue,
      placeholder: field.placeholder,
      helpText: field.helpText,
      referenceObject: field.referenceObject || field.relatedObject,
      componentProps: {
        ...(field.componentProps || {}),
        ...(field as any).component_props || {}
      }
    })
  }

  return Array.from(map.values())
})

const designerCanvasSections = computed<DetailSection[]>(() => {
  return (layoutConfig.value.sections || []).map((section: LayoutSection) => ({
    name: section.id,
    title: section.title || 'Untitled Section',
    type: section.type || 'section',
    position: section.position,
    fields: [],
    collapsible: section.collapsible === true,
    collapsed: section.collapsed === true
  }))
})

const previewAuditInfo = computed(() => ({
  createdBy: sampleData.value.createdBy || sampleData.value.created_by || 'System',
  createdAt: sampleData.value.createdAt || sampleData.value.created_at || '2026-03-01 10:00:00',
  updatedBy: sampleData.value.updatedBy || sampleData.value.updated_by || 'System',
  updatedAt: sampleData.value.updatedAt || sampleData.value.updated_at || '2026-03-01 12:30:00'
}))

const previewObjectName = computed(() => {
  return props.objectCode || props.layoutName || 'Record'
})

const previewPageTitle = computed(() => {
  const fields = previewFieldDefinitions.value || []
  const identifier = fields.find((field: any) => field?.isIdentifier || field?.is_identifier || field?.code === 'name')
  const candidateKeys = [
    identifier?.code,
    'name',
    'title',
    'code'
  ].filter(Boolean) as string[]

  for (const key of candidateKeys) {
    const value = sampleData.value?.[key]
    if (value !== undefined && value !== null && String(value).trim()) {
      return String(value)
    }
  }

  return props.layoutName || previewObjectName.value
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

function isFieldAdded(code: string): boolean {
  return addedFieldCodes.value.includes(code)
}

function getDisabledReason(field: FieldDefinition): string | null {
  return getFieldDisabledReason(field.fieldType, props.mode)
}

function canAddField(field: FieldDefinition): boolean {
  return canAddFieldInDesigner(field.fieldType, props.mode)
}

function notifyUnsupportedField(field: FieldDefinition): void {
  const reason = getDisabledReason(field)
  if (!reason) return
  ElMessage.warning(t('system.pageLayout.designer.messages.cannotAddField', { name: field.name, reason }))
}

function extractRelatedObjectCode(field: Record<string, any>): string {
  const direct = field.relatedObjectCode || field.related_object_code || field.referenceObject
  if (direct) return String(direct)
  if (field.reverseRelationModel || field.reverse_relation_model) {
    const model = String(field.reverseRelationModel || field.reverse_relation_model)
    const parts = model.split('.')
    return parts[parts.length - 1]
  }
  return String(field.code || '').replace(/(_?record|_?items|s?)$/, '')
}

function mapPreviewReverseRelations(fields: any[]): ReverseRelationField[] {
  return (fields || []).map((rel: any) => ({
    code: rel.code,
    label: rel.label || rel.name || rel.code,
    displayMode: rel.relationDisplayMode || rel.relation_display_mode || 'inline_readonly',
    relatedObjectCode: extractRelatedObjectCode(rel),
    reverseRelationField: rel.reverseRelationField || rel.reverse_relation_field,
    reverseRelationModel: rel.reverseRelationModel || rel.reverse_relation_model,
    title: rel.label || rel.name || rel.code,
    showCreate: (rel.relationDisplayMode || rel.relation_display_mode) === 'inline_editable',
    position: rel.position
  })) as ReverseRelationField[]
}

function buildLayoutField(field: FieldDefinition): LayoutField {
  const fieldType = normalizeFieldType(field.fieldType || 'text')
  const componentProps = {
    ...(field.componentProps || {}),
    ...(field as any).component_props || {}
  }

  return {
    id: generateId('field'),
    fieldCode: field.code,
    label: field.name,
    span: 1,
    readonly: field.isReadonly || props.mode === 'readonly',
    visible: true,
    required: field.isRequired,
    fieldType,
    // Preserve complete metadata for proper rendering
    options: field.options,
    referenceObject: field.referenceObject || field.relatedObject,
    componentProps,
    dictionaryType: field.dictionaryType,
    defaultValue: field.defaultValue,
    placeholder: field.placeholder,
    helpText: field.helpText
  }
}

function addFieldToContainer(field: FieldDefinition, meta: ContainerMeta) {
  if (!canAddField(field)) {
    notifyUnsupportedField(field)
    return
  }

  if (isFieldAdded(field.code)) {
    ElMessage.warning(t('system.pageLayout.designer.messages.fieldAlreadyAdded'))
    return
  }

  const previousConfig = cloneLayoutConfig(layoutConfig.value)
  const newConfig = cloneLayoutConfig(layoutConfig.value) as LayoutConfig
  const targetArr = getFieldArrayRef(newConfig, meta)
  if (!targetArr) return

  const newField = buildLayoutField(field)
  targetArr.push(newField)
  commitLayoutChange(newConfig, `Add field ${field.code}`, previousConfig)

  // Seed sample value so WYSIWYG preview is never blank.
  if (newField.fieldCode && sampleData.value[newField.fieldCode] === undefined) {
    sampleData.value[newField.fieldCode] = getSampleValue(newField)
  }

}

// Field selection from panel
function handleFieldClick(field: FieldDefinition) {
  if (!canAddField(field)) {
    notifyUnsupportedField(field)
    return
  }

  // Add to first section or create one if none exists
  if (!layoutConfig.value.sections || layoutConfig.value.sections.length === 0) {
    addSection()
  }

  // Check if already added
  if (isFieldAdded(field.code)) {
    ElMessage.warning(t('system.pageLayout.designer.messages.fieldAlreadyAdded'))
    return
  }

  const previousConfig = cloneLayoutConfig(layoutConfig.value)
  const newConfig = cloneLayoutConfig(layoutConfig.value) as LayoutConfig
  const firstSection = newConfig.sections![0]
  if (!firstSection.fields) {
    firstSection.fields = []
  }

  const newField = buildLayoutField(field)
  firstSection.fields!.push(newField)
  if (newField.fieldCode && sampleData.value[newField.fieldCode] === undefined) {
    sampleData.value[newField.fieldCode] = getSampleValue(newField)
  }
  commitLayoutChange(newConfig, `Add field ${field.code}`, previousConfig)
}

function selectField(field: LayoutField, section: LayoutSection) {
  selectedId.value = field.id
  selectedSection.value = section
  fieldProps.value = { ...field }
}

function maybeSelectField(field: LayoutField, section: LayoutSection) {
  if (!isDesignMode.value) return
  selectField(field, section)
}

function selectSection(id: string) {
  selectedId.value = id
  const section = findItemById(layoutConfig.value, id)
  selectedSection.value = section
  sectionProps.value = { ...section }
}

function maybeSelectSection(id: string) {
  if (!isDesignMode.value) return
  selectSection(id)
}

function deselect() {
  selectedId.value = ''
  selectedSection.value = null
  fieldProps.value = {}
  sectionProps.value = {}
}

// Drag handlers
function handleFieldDragStart(e: DragEvent, field: FieldDefinition) {
  if (!canAddField(field)) {
    e.preventDefault()
    notifyUnsupportedField(field)
    return
  }

  draggedField.value = field
  e.dataTransfer!.effectAllowed = 'copy'
  e.dataTransfer!.setData('field', JSON.stringify(field))
}

function handleDragEnd() {
  draggedField.value = null
  isDragOverCanvas.value = false
  dragOverSection.value = null
}

function handleCanvasDragOver(e: DragEvent) {
  if (renderMode.value !== 'design') return
  e.preventDefault()
  isDragOverCanvas.value = true
}

function handleCanvasDragLeave(_e: DragEvent) {
  if (renderMode.value !== 'design') return
  isDragOverCanvas.value = false
}

function handleCanvasDrop(e: DragEvent) {
  if (renderMode.value !== 'design') return
  e.preventDefault()
  isDragOverCanvas.value = false

  const data = e.dataTransfer!.getData('field')
  if (!data) return

  const field: FieldDefinition = JSON.parse(data)
  handleFieldClick(field)
}

function handleSectionDragOver(e: DragEvent) {
  if (renderMode.value !== 'design') return
  e.preventDefault()
  e.stopPropagation()
}

function handleSectionDragLeave(e: DragEvent) {
  if (renderMode.value !== 'design') return
  e.stopPropagation()
}

function handleSectionDrop(e: DragEvent) {
  if (renderMode.value !== 'design') return
  e.preventDefault()
  e.stopPropagation()

  const data = e.dataTransfer?.getData('field')
  if (!data) return

  const sectionId = (e.currentTarget as HTMLElement | null)?.dataset?.sectionId || ''
  if (!sectionId) return

  const field: FieldDefinition = JSON.parse(data)
  if (!canAddField(field)) {
    notifyUnsupportedField(field)
    return
  }
  addFieldToContainer(field, { kind: 'section', sectionId })
}

function handleTabDrop(e: DragEvent) {
  if (renderMode.value !== 'design') return
  e.preventDefault()
  e.stopPropagation()

  const data = e.dataTransfer?.getData('field')
  if (!data) return

  const tabId = (e.currentTarget as HTMLElement | null)?.dataset?.tabId || ''
  const sectionId = (e.currentTarget as HTMLElement | null)?.dataset?.sectionId || ''
  if (!sectionId || !tabId) return

  const field: FieldDefinition = JSON.parse(data)
  if (!canAddField(field)) {
    notifyUnsupportedField(field)
    return
  }
  addFieldToContainer(field, { kind: 'tab', sectionId, tabId })
}

function handleCollapseDrop(e: DragEvent) {
  if (renderMode.value !== 'design') return
  e.preventDefault()
  e.stopPropagation()

  const data = e.dataTransfer?.getData('field')
  if (!data) return

  const sectionId = (e.currentTarget as HTMLElement | null)?.dataset?.sectionId || ''
  const collapseId = (e.currentTarget as HTMLElement | null)?.dataset?.collapseId || ''
  if (!sectionId || !collapseId) return

  const field: FieldDefinition = JSON.parse(data)
  if (!canAddField(field)) {
    notifyUnsupportedField(field)
    return
  }
  addFieldToContainer(field, { kind: 'collapse', sectionId, collapseId })
}

// Field update
function updateField(key: string, value: any) {
  if (!selectedId.value || elementType.value !== 'field') return

  if (key === 'fieldType') {
    const nextType = normalizeFieldType(value || 'text')
    const reason = getFieldDisabledReason(nextType, props.mode)
    if (reason) {
      ElMessage.warning(t('system.pageLayout.designer.messages.cannotSwitchFieldType', { reason }))
      const current = findItemById(layoutConfig.value, selectedId.value)
      if (current) {
        fieldProps.value = {
          ...fieldProps.value,
          fieldType: normalizeFieldType(current.fieldType || 'text')
        }
      }
      return
    }
  }

  const previousConfig = cloneLayoutConfig(layoutConfig.value)
  const newConfig = cloneLayoutConfig(layoutConfig.value) as LayoutConfig
  const item = findItemById(newConfig, selectedId.value)
  if (item) {
    item[key] = key === 'fieldType' ? normalizeFieldType(value || 'text') : value
    commitLayoutChange(newConfig, `Update field ${key}`, previousConfig)
  }
}

function handleFieldPropertyUpdate(payload: { key: string; value: any }) {
  updateField(payload.key, payload.value)
}

function updateSection(key: string, value: any) {
  if (!selectedId.value || elementType.value !== 'section') return

  const previousConfig = cloneLayoutConfig(layoutConfig.value)
  const newConfig = cloneLayoutConfig(layoutConfig.value) as LayoutConfig
  const item = findItemById(newConfig, selectedId.value)
  if (item) {
    item[key] = value

    // Auto-bootstrap tabs array if switching to tab mode and empty
    if (key === 'type' && value === 'tab') {
      if (!Array.isArray(item.tabs) || item.tabs.length === 0) {
        const tabId = `tab_${Date.now()}`
        item.tabs = [{
          id: tabId,
          title: t('system.pageLayout.designer.defaults.tabTitle', { index: 1 }),
          name: tabId,
          fields: []
        }]
        // Initialize the v-model as well
        activeTabs.value[item.id] = tabId
      }
    }

    commitLayoutChange(newConfig, `Update section ${key}`, previousConfig)
  }
}

function handleSectionPropertyUpdate(payload: { key: string; value: any }) {
  updateSection(payload.key, payload.value)
}

function removeField(fieldId: string, sectionId: string, _sectionIndex?: number) {
  const previousConfig = cloneLayoutConfig(layoutConfig.value)
  const newConfig = cloneLayoutConfig(layoutConfig.value) as LayoutConfig
  
  const section = newConfig.sections?.find(s => s.id === sectionId)
  if (!section) return

  if (section.type === 'tab') {
    // Find in tabs
    for (const tab of section.tabs || []) {
      tab.fields = tab.fields?.filter(f => f.id !== fieldId) || []
    }
  } else if (section.type === 'collapse') {
    for (const item of section.items || []) {
      item.fields = item.fields?.filter(f => f.id !== fieldId) || []
    }
  } else {
    section.fields = section.fields?.filter(f => f.id !== fieldId) || []
  }

  commitLayoutChange(newConfig, `Remove field ${fieldId}`, previousConfig)
  selectedId.value = ''
}

function deleteSection(sectionId: string) {
  ElMessageBox.confirm(
    t('system.pageLayout.designer.messages.deleteSectionConfirm'),
    t('system.pageLayout.designer.messages.deleteSectionTitle'),
    {
    type: 'warning'
  }).then(() => {
    const previousConfig = cloneLayoutConfig(layoutConfig.value)
    const newConfig = cloneLayoutConfig(layoutConfig.value) as LayoutConfig
    newConfig.sections = newConfig.sections?.filter(s => s.id !== sectionId) || []
    commitLayoutChange(newConfig, `Delete section ${sectionId}`, previousConfig)
    selectedId.value = ''
    ElMessage.success(t('system.pageLayout.designer.messages.sectionDeleted'))
  }).catch(() => {})
}

function addSection() {
  const newSection: LayoutSection = {
    id: generateId('section'),
    type: 'section',
    title: t('system.pageLayout.designer.defaults.newSection'),
    collapsible: true,
    collapsed: false,
    columns: 2,
    border: true,
    fields: []
  }

  const previousConfig = cloneLayoutConfig(layoutConfig.value)
  const newConfig = cloneLayoutConfig(layoutConfig.value) as LayoutConfig
  if (!newConfig.sections) {
    newConfig.sections = []
  }

  newConfig.sections.push(newSection)
  commitLayoutChange(newConfig, 'Add section', previousConfig)
  selectedId.value = newSection.id
}

function toggleSectionCollapse(sectionId: string) {
  const section = findItemById(layoutConfig.value, sectionId)
  if (section && section.collapsible !== undefined) {
    section.collapsed = !section.collapsed
  }
}

const resolveLayoutType = (): LayoutType => {
  return normalizeLayoutType(props.mode) as LayoutType
}

const isReadonlyMode = computed(() => props.mode === 'readonly')

function normalizeAndEnsureLayoutConfig(rawConfig: LayoutConfig): LayoutConfig {
  return ensurePersistLayoutConfigIds(rawConfig || { sections: [] }) as LayoutConfig
}

function extractConfigPayload(raw: any): LayoutConfig {
  const payload = (raw?.data ?? raw) as any
  const config = payload?.layoutConfig || payload?.layout_config || payload?.layout || { sections: [] }
  return normalizeAndEnsureLayoutConfig(config as LayoutConfig)
}

function buildReadonlyModeOverride(sharedBase: LayoutConfig, readonlyConfig: LayoutConfig): LayoutConfig {
  const next = cloneLayoutConfig(normalizeAndEnsureLayoutConfig(sharedBase || { sections: [] })) as any
  const normalizedReadonly = normalizeAndEnsureLayoutConfig(readonlyConfig || { sections: [] })
  const existingOverrides = (next.modeOverrides || next.mode_overrides || {}) as Record<string, any>

  next.modeOverrides = {
    ...existingOverrides,
    readonly: {
      sections: normalizedReadonly.sections || [],
      actions: normalizedReadonly.actions || []
    }
  }

  return next as LayoutConfig
}

async function resolveSharedEditLayout(readonlySeed?: LayoutConfig): Promise<any> {
  if (!props.objectCode) {
    throw new Error('Missing objectCode')
  }

  // Reuse resolved target when possible to avoid redundant queries.
  if (sharedEditLayoutId.value) {
    const existing = await pageLayoutApi.detail(sharedEditLayoutId.value)
    if ((existing as any)?.id) return existing
  }

  let activeEdit: any = null
  try {
    activeEdit = await pageLayoutApi.byObjectAndMode(props.objectCode, 'edit')
  } catch {
    activeEdit = null
  }

  const normalizedEdit = ((activeEdit as any)?.data ?? activeEdit) as any
  if (normalizedEdit?.id && !normalizedEdit?.isDefault) {
    sharedEditLayoutId.value = String(normalizedEdit.id)
    return normalizedEdit
  }

  // If current active edit layout is system default, create a custom edit layout
  // and store readonly override in that custom shared layout.
  const sourceBusinessObject =
    normalizedEdit?.businessObject ||
    normalizedEdit?.business_object ||
    props.businessObjectId

  let baseLayoutConfig: LayoutConfig | null = null
  if (normalizedEdit?.layoutConfig || normalizedEdit?.layout_config) {
    baseLayoutConfig = extractConfigPayload(normalizedEdit)
  } else {
    try {
      const defaultEdit = await pageLayoutApi.getDefault(props.objectCode, 'edit')
      baseLayoutConfig = extractConfigPayload(defaultEdit)
    } catch {
      baseLayoutConfig = null
    }
  }

  const fallbackSeed = normalizeAndEnsureLayoutConfig(readonlySeed || { sections: [] })
  const createPayload = {
    layoutCode: `${props.objectCode}_edit_shared_${Date.now()}`,
    layoutName: `${props.objectCode} Edit Shared`,
    mode: 'edit',
    business_object: sourceBusinessObject || props.businessObjectId,
    status: 'draft',
    isDefault: false,
    layoutConfig: baseLayoutConfig || fallbackSeed
  }

  const created = await pageLayoutApi.create(createPayload as any)
  const normalizedCreated = ((created as any)?.data ?? created) as any
  if (!normalizedCreated?.id) {
    if (props.layoutId) {
      const legacy = await pageLayoutApi.detail(props.layoutId)
      const normalizedLegacy = ((legacy as any)?.data ?? legacy) as any
      if (normalizedLegacy?.id) {
        sharedEditLayoutId.value = String(normalizedLegacy.id)
        return normalizedLegacy
      }
    }
    throw new Error('Failed to resolve shared edit layout')
  }
  sharedEditLayoutId.value = String(normalizedCreated.id)
  return normalizedCreated
}

async function saveReadonlyToSharedLayout(readonlyConfig: LayoutConfig, publish = false) {
  const targetLayout = await resolveSharedEditLayout(readonlyConfig)
  const targetLayoutId = String(targetLayout.id)
  const targetMode = String(targetLayout?.mode || '').toLowerCase()
  const targetType = String(targetLayout?.layoutType || targetLayout?.layout_type || '').toLowerCase()
  const isEditTarget = targetMode === 'edit' || targetType === 'form'
  const mergedConfig = isEditTarget
    ? buildReadonlyModeOverride(extractConfigPayload(targetLayout), readonlyConfig)
    : normalizeAndEnsureLayoutConfig(readonlyConfig)

  await pageLayoutApi.partialUpdate(targetLayoutId, {
    layoutConfig: mergedConfig,
    status: 'draft'
  })

  if (publish) {
    await pageLayoutApi.publish(targetLayoutId, {
      change_summary: 'Publish readonly override on shared edit layout'
    })
  }

  sharedEditLayoutId.value = targetLayoutId
  return {
    id: targetLayoutId,
    layoutConfig: mergedConfig
  }
}

const prepareLayoutConfig = (): LayoutConfig | null => {
  try {
    const availableFieldCodes = availableFields.value.map((item) => String(item.code || '').trim()).filter(Boolean)
    const prepared = preparePersistLayoutConfig(layoutConfig.value || { sections: [] }, {
      layoutType: resolveLayoutType(),
      availableFieldCodes
    }) as LayoutConfig
    layoutConfig.value = prepared
    return prepared
  } catch (error: any) {
    ElMessage.error(error?.message || t('system.pageLayout.designer.messages.invalidLayoutConfig'))
    return null
  }
}

// Save and publish
async function handleSave() {
  saving.value = true
  try {
    const sanitizedConfig = prepareLayoutConfig()
    if (!sanitizedConfig) return
    const data: Record<string, any> = {
      layoutConfig: sanitizedConfig,
      status: 'draft'
    }

    if (isReadonlyMode.value && props.objectCode) {
      const result = await saveReadonlyToSharedLayout(sanitizedConfig, false)
      data.sharedLayoutId = result.id
      // Compatibility sync: keep legacy readonly layout snapshot updated when editing from a readonly layout row.
      if (props.layoutId && props.layoutId !== result.id) {
        try {
          await pageLayoutApi.partialUpdate(props.layoutId, {
            layoutConfig: sanitizedConfig,
            status: 'draft'
          } as any)
        } catch {
          // ignore legacy sync failure; shared edit layout is source of truth.
        }
      }
    } else if (props.layoutId) {
      await pageLayoutApi.partialUpdate(props.layoutId, data as any)
    } else {
      await pageLayoutApi.create({
        ...data,
        layoutCode: `${props.objectCode}_${props.mode}_${Date.now()}`,
        layoutName: props.layoutName,
        mode: props.mode,
        business_object: props.businessObjectId
      } as any)
    }

    ElMessage.success(t('system.pageLayout.designer.messages.layoutSaved'))
    emit('save', data)
  } catch (error: any) {
    console.error('Save failed:', error)
    ElMessage.error(error.response?.data?.message || t('system.pageLayout.designer.messages.saveFailed'))
  } finally {
    saving.value = false
  }
}

async function handlePublish() {
  publishing.value = true
  try {
    const sanitizedConfig = prepareLayoutConfig()
    if (!sanitizedConfig) return

    if (isReadonlyMode.value && props.objectCode) {
      const result = await saveReadonlyToSharedLayout(sanitizedConfig, true)
      // Compatibility sync for legacy readonly layout records.
      if (props.layoutId && props.layoutId !== result.id) {
        try {
          await pageLayoutApi.partialUpdate(props.layoutId, {
            layoutConfig: sanitizedConfig,
            status: 'draft'
          } as any)
          await pageLayoutApi.publish(props.layoutId, {
            change_summary: 'Sync readonly snapshot from shared edit layout'
          })
        } catch {
          // ignore legacy sync failure; shared edit layout is source of truth.
        }
      }
    } else if (props.layoutId) {
      // Persist latest draft before publish to avoid publishing stale server-side config.
      await pageLayoutApi.partialUpdate(props.layoutId, {
        layoutConfig: sanitizedConfig,
        status: 'draft'
      })
      await pageLayoutApi.publish(props.layoutId, {
        change_summary: 'Publish layout'
      })
    } else {
      // Create as draft first, then publish to keep lifecycle consistent.
      const createResult = await pageLayoutApi.create({
        layoutConfig: sanitizedConfig,
        layoutCode: `${props.objectCode}_${props.mode}_${Date.now()}`,
        layoutName: props.layoutName,
        mode: props.mode,
        business_object: props.businessObjectId,
        status: 'draft'
      } as any)
      const createdPayload = ((createResult as any)?.data ?? createResult) as { id: string }
      await pageLayoutApi.publish(createdPayload.id, {
        change_summary: 'Publish layout',
        set_as_default: true
      })
    }

    isPublished.value = true
    ElMessage.success(t('system.pageLayout.designer.messages.layoutPublished'))
    emit('published', layoutConfig.value)
  } catch (error: any) {
    console.error('Publish failed:', error)
    ElMessage.error(error.response?.data?.message || t('system.pageLayout.designer.messages.publishFailed'))
  } finally {
    publishing.value = false
  }
}

/**
 * Reset layout to system default
 * Fetches the auto-generated default layout from backend which includes all fields
 */
async function handleReset() {
  try {
    await ElMessageBox.confirm(
      t('system.pageLayout.designer.messages.resetConfirm'),
      t('system.pageLayout.designer.messages.resetConfirmTitle'),
      { type: 'warning' }
    )
  } catch {
    return // User cancelled
  }

  try {
    if (!props.objectCode) throw new Error('Missing objectCode')

    // Single source of truth: default layout endpoint (supports mode/type normalization).
    const layoutType = normalizeLayoutType(props.mode)
    const result = await pageLayoutApi.getDefault(props.objectCode, layoutType)
    const payload = ((result as any)?.data ?? result) as any
    const backendConfig =
      payload?.layoutConfig ||
      payload?.layout_config ||
      payload?.layout ||
      null

    if (
      backendConfig &&
      (
        (Array.isArray(backendConfig.sections) && backendConfig.sections.length > 0) ||
        (Array.isArray(backendConfig.columns) && backendConfig.columns.length > 0) ||
        Object.keys(backendConfig).length > 0
      )
    ) {
      // Normalize and use the backend-generated default layout
      layoutConfig.value = normalizeAndEnsureLayoutConfig(backendConfig as LayoutConfig)
      await loadAvailableFields()
      populateSampleData()
      console.log('[LayoutDesigner Reset] Applied normalized layout:', layoutConfig.value)
    } else {
      // Fallback: generate a layout with all available fields
      console.warn('[LayoutDesigner Reset] No default layout from backend, generating from available fields')
      await loadAvailableFields()
      
      const defaultSection = {
        id: `section-${Date.now()}`,
        type: 'section',
        title: t('system.pageLayout.designer.defaults.basicInformation'),
        collapsible: true,
        collapsed: false,
        columns: 2,
        border: false,
        fields: availableFields.value.map((field, index) => ({
          id: `field-${Date.now()}-${index}`,
          fieldCode: field.code,
          label: field.name || (field as any).displayName || field.code,
          fieldType: normalizeFieldType((field as any).fieldType || (field as any).field_type || (field as any).type || 'text'),
          span: 12,
          required: field.isRequired || false,
          options: field.options,
          referenceObject: field.referenceObject || field.relatedObject,
          componentProps: field.componentProps,
          dictionaryType: field.dictionaryType
        }))
      }
      
      layoutConfig.value = {
        sections: [defaultSection],
        actions: [
          { code: 'submit', label: 'Submit', type: 'primary', position: 'bottom-right' },
          { code: 'cancel', label: 'Cancel', type: 'default', position: 'bottom-right' }
        ]
      }
      populateSampleData()
    }
    
    selectedId.value = ''
    history.clear()
    ElMessage.success(t('system.pageLayout.designer.messages.resetToDefaultSuccess'))
  } catch (error) {
    console.error('[LayoutDesigner Reset] Failed:', error)
    ElMessage.error(t('system.pageLayout.designer.messages.resetFailedRefresh'))
  }
}

function handleCancel() {
  emit('cancel')
}

/**
 * Populate sampleData with sample values for all fields in the layout
 * This ensures the canvas preview displays sample text instead of empty fields
 */
function populateSampleData() {
  const data: Record<string, any> = {}

  // Iterate through all sections and fields to collect field codes
  for (const section of layoutConfig.value.sections || []) {
    if (section.type === 'tab') {
      // Tab section - iterate through tabs
      for (const tab of section.tabs || []) {
        for (const field of tab.fields || []) {
          data[field.fieldCode] = getSampleValue(field)
        }
      }
    } else if (section.type === 'collapse') {
      // Collapse section - iterate through items
      for (const item of section.items || []) {
        for (const field of item.fields || []) {
          data[field.fieldCode] = getSampleValue(field)
        }
      }
    } else {
      // Regular section
      for (const field of section.fields || []) {
        data[field.fieldCode] = getSampleValue(field)
      }
    }
  }

  sampleData.value = data
}

function normalizeAvailableFields(fields: any[]): FieldDefinition[] {
  return (fields || []).map((field: any) => ({
    ...field,
    code: String(field.code || field.fieldCode || field.field_code || field.fieldName || '').trim(),
    name: String(field.name || field.label || field.displayName || field.display_name || field.code || field.fieldName || '').trim(),
    fieldType: normalizeFieldType(field.fieldType || field.field_type || field.type || 'text')
  }))
}

function applyResolvedLayoutToDesigner(resolved: any): boolean {
  const combinedFields = Array.isArray(resolved?.fields) ? resolved.fields : []
  if (combinedFields.length > 0 && availableFields.value.length === 0) {
    availableFields.value = normalizeAvailableFields(combinedFields)
  }

  const activeConfig = resolved?.layoutConfig || null
  if (!activeConfig) return false

  if (!(activeConfig.sections?.length || activeConfig.columns?.length)) return false

  layoutConfig.value = normalizeAndEnsureLayoutConfig({ ...activeConfig } as LayoutConfig)
  return true
}

async function loadActiveLayoutPreview(): Promise<boolean> {
  if (!props.objectCode) return false
  try {
    const resolved = await resolveRuntimeLayout(props.objectCode, props.mode || 'edit', {
      includeRelations: true
    })
    if (applyResolvedLayoutToDesigner(resolved)) {
      populateSampleData()
      return true
    }
  } catch (error) {
    // ignore and keep current canvas
  }
  return false
}

async function setPreviewMode(mode: 'current' | 'active') {
  if (previewLoading.value) return
  if (previewMode.value === mode) return

  if (mode === 'current') {
    previewMode.value = mode
    if (currentLayoutSnapshot.value) {
      layoutConfig.value = cloneLayoutConfig(currentLayoutSnapshot.value)
      populateSampleData()
    }
    ElMessage.info(t('system.pageLayout.designer.messages.switchedToCustomMode'))
    return
  }

  previewLoading.value = true
  currentLayoutSnapshot.value = cloneLayoutConfig(layoutConfig.value)

  try {
    previewMode.value = mode
    const ok = await loadActiveLayoutPreview()
    if (!ok) {
      previewMode.value = 'current'
      if (currentLayoutSnapshot.value) {
        layoutConfig.value = cloneLayoutConfig(currentLayoutSnapshot.value)
        populateSampleData()
      }
      ElMessage.warning(t('system.pageLayout.designer.messages.noPreviewLayoutFallback'))
      return
    }
    ElMessage.success(t('system.pageLayout.designer.messages.switchedToPreviewMode'))
  } finally {
    previewLoading.value = false
  }
}

async function loadLayout() {

  previewMode.value = 'current'
  currentLayoutSnapshot.value = null
  previewLoading.value = false

  // Otherwise, load from API if layoutId is provided
  if (props.layoutId && !isReadonlyMode.value) {
    try {
      const layoutRaw = await pageLayoutApi.detail(props.layoutId)
      const layout = ((layoutRaw as any)?.data ?? layoutRaw) as any
      const rawConfig = layout.layoutConfig || layout.layout_config || getDefaultLayoutConfig(props.mode)
      // Normalize the layout config to handle backend API format (field -> fieldCode)
      layoutConfig.value = normalizeAndEnsureLayoutConfig(rawConfig as LayoutConfig)
      isDefault.value = Boolean(layout.isDefault ?? layout.is_default)
      isPublished.value = String(layout.status || '') === 'published'
      layoutVersion.value = String(layout.version || layoutVersion.value)
      // Populate sample data with values from the loaded layout
      await loadAvailableFields()
      populateSampleData()
      return
    } catch (error) {
      console.error('Failed to load layout:', error)
    }
  }

  // If no specific layoutId, load the active layout to match the real detail page
  if (props.objectCode) {
    try {
      const resolved = await resolveRuntimeLayout(props.objectCode, props.mode || 'edit', {
        includeRelations: true
      })
      applyResolvedLayoutToDesigner(resolved)
      await loadAvailableFields()
      isDefault.value = !!resolved?.isDefault
      isPublished.value = resolved?.layoutStatus === 'published'
      layoutVersion.value = resolved?.layoutVersion || layoutVersion.value

      populateSampleData()
      return
    } catch (error) {
      // Ignore and fall back to default
    }
  }

  // Fall back to layoutConfig prop if provided
  if (props.layoutConfig && (props.layoutConfig.sections?.length || props.layoutConfig.columns?.length)) {
    layoutConfig.value = normalizeAndEnsureLayoutConfig({ ...props.layoutConfig } as LayoutConfig)
    populateSampleData()
    return
  }

  // Final fallback: backend default layout for this object/mode
  if (props.objectCode) {
    try {
      const defaultLayout = await pageLayoutApi.getDefault(props.objectCode, normalizeLayoutType(props.mode))
      const defaultData: any = (defaultLayout as any)?.data ?? defaultLayout
      const backendConfig = defaultData?.layoutConfig || defaultData?.layout_config
      if (backendConfig && (backendConfig.sections?.length || backendConfig.columns?.length)) {
        layoutConfig.value = normalizeAndEnsureLayoutConfig({ ...backendConfig } as LayoutConfig)
        populateSampleData()
        return
      }
    } catch (error) {
      // fall through
    }
  }

  return
}

/**
 * Load available fields using businessObjectApi for authenticated requests
 * Refactored to use unified API layer instead of native fetch()
 */
async function loadAvailableFields() {
  if (!props.objectCode) {
    console.warn('[LayoutDesigner] No objectCode provided, cannot load fields')
    previewReverseRelations.value = []
    return
  }

  try {
    const [runtimeResult, metadataResult] = await Promise.allSettled([
      resolveRuntimeLayout(props.objectCode, props.mode || 'edit', {
        includeRelations: true
      }),
      dynamicApi.getMetadata(props.objectCode)
    ])

    const runtimeFields =
      runtimeResult.status === 'fulfilled' && Array.isArray(runtimeResult.value?.fields)
        ? runtimeResult.value.fields
        : []
    const runtimeReverseRelations =
      runtimeResult.status === 'fulfilled' && Array.isArray((runtimeResult.value as any)?.reverseRelations)
        ? (runtimeResult.value as any).reverseRelations
        : []
    previewReverseRelations.value = mapPreviewReverseRelations(runtimeReverseRelations)

    const metadataPayload =
      metadataResult.status === 'fulfilled'
        ? ((metadataResult.value as any)?.data ?? metadataResult.value)
        : null
    const metadataFields = Array.isArray(metadataPayload?.fields) ? metadataPayload.fields : []

    // Runtime fields preserve active layout semantics; metadata fills gaps for full designer palette.
    const combined = mergeFieldSources(runtimeFields, metadataFields)
    if (combined.length > 0) {
      availableFields.value = normalizeAvailableFields(combined)
      return
    }

    console.warn('[LayoutDesigner] No fields returned from runtime/metadata endpoints, keeping current fields')
  } catch (error) {
    console.error('Failed to load fields:', error)
    previewReverseRelations.value = []
    // Only set fallback mock data if availableFields is empty
    if (availableFields.value.length === 0) {
      console.log('[LayoutDesigner] Using fallback mock data')
      availableFields.value = [
        { code: 'name', name: 'Name', fieldType: 'text', isRequired: true },
        { code: 'code', name: 'Code', fieldType: 'text', isRequired: true },
        { code: 'status', name: 'Status', fieldType: 'select', isRequired: false },
        { code: 'description', name: 'Description', fieldType: 'textarea', isRequired: false }
      ]
    }
  }
}

// Update properties when selection changes
watch(selectedId, () => {
  const item = selectedItem.value
  if (!item) {
    fieldProps.value = {}
    sectionProps.value = {}
    return
  }

  if (elementType.value === 'field') {
    fieldProps.value = {
      ...item,
      fieldType: normalizeFieldType((item as any).fieldType || (item as any).field_type || 'text')
    }
  } else if (elementType.value === 'section') {
    sectionProps.value = { ...item }
  }
})

const dndSignature = computed(() => {
  const sections = layoutConfig.value.sections || []
  return JSON.stringify(
    {
      renderMode: renderMode.value,
      sections: sections.map((s) => ({
        id: s.id,
        type: s.type,
        tabs: s.type === 'tab' ? (s.tabs || []).map((t) => t.id) : [],
        items: s.type === 'collapse' ? (s.items || []).map((i) => i.id) : []
      }))
    }
  )
})

function syncContainerStates() {
  const sections = layoutConfig.value.sections || []
  const nextTabs = { ...(activeTabs.value || {}) }
  const nextCollapses = { ...(activeCollapses.value || {}) }
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
    activeTabs.value = nextTabs
  }
  if (collapsesChanged) {
    activeCollapses.value = nextCollapses
  }
}

watch(
  dndSignature,
  async () => {
    syncContainerStates()
    await initSortables()
  },
  { immediate: true }
)

watch(renderMode, (mode) => {
  if (mode !== 'design') {
    deselect()
    isDragOverCanvas.value = false
    dragOverSection.value = null
  }
})

// Lifecycle
onMounted(() => {
  loadLayout().finally(() => {
    if (props.initialPreviewMode === 'active') {
      void setPreviewMode('active')
    }
  })
  // Expand first group by default
  expandedGroups.value.add('text')
})

onUnmounted(() => {
  destroySortables()
})

// Watch for prop changes
watch(() => props.mode, (newType) => {
  layoutConfig.value = normalizeAndEnsureLayoutConfig(getDefaultLayoutConfig(newType) as LayoutConfig)
  loadLayout()
})
</script>

<style scoped lang="scss">
.wysiwyg-layout-designer {
  display: flex;
  flex-direction: column;
  height: 100vh;
  background: #f5f7fa;
}

.designer-toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  flex-wrap: wrap;
  row-gap: 8px;
  padding: 12px 20px;
  background: white;
  border-bottom: 1px solid #e4e7ed;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);

  .toolbar-left {
    display: flex;
    align-items: center;
    gap: 12px;
    min-width: 0;
    flex: 1 1 auto;

    .layout-info {
      display: inline-block;
      max-width: 420px;
      overflow: hidden;
      text-overflow: ellipsis;
      white-space: nowrap;
      font-size: 16px;
      font-weight: 500;
      color: #303133;
    }
  }

  .toolbar-center {
    flex: 0 0 auto;
  }

  .toolbar-right {
    display: flex;
    align-items: center;
    justify-content: flex-end;
    flex-wrap: wrap;
    gap: 8px;
    flex: 0 0 auto;
  }
}

.designer-main {
  display: flex;
  flex: 1;
  overflow: hidden;
}

// Left Panel - Field List
.field-panel {
  width: 260px;
  background: white;
  border-right: 1px solid #e4e7ed;
  display: flex;
  flex-direction: column;

  .panel-header {
    padding: 12px 16px;
    border-bottom: 1px solid #e4e7ed;
  }

  .panel-content {
    flex: 1;
    overflow-y: auto;
    padding: 8px 0;
  }
}

.field-group {
  margin-bottom: 8px;

  .group-header {
    display: flex;
    align-items: center;
    gap: 8px;
    padding: 8px 12px;
    cursor: pointer;
    border-radius: 6px;
    transition: background 0.2s;

    &:hover {
      background: #f5f7fa;
    }

    .expand-icon {
      margin-left: auto;
      transition: transform 0.2s;

      &.expanded {
        transform: rotate(90deg);
      }
    }
  }

  .group-fields {
    padding: 0 8px 8px;
  }
}

.palette-field-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 12px;
  margin-bottom: 4px;
  border-radius: 6px;
  cursor: pointer;
  transition: all 0.2s;
  border: 1px solid transparent;

  .field-icon {
    color: #909399;
  }

  .field-label {
    flex: 1;
    font-size: 14px;
    color: #303133;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }

  .field-code {
    font-size: 12px;
    color: #909399;
  }

  .added-icon {
    margin-left: auto;
    color: #67c23a;
  }

  &:hover {
    background: #f0f9ff;
    border-color: #409eff;
  }

  &.is-selected {
    background: #ecf5ff;
    border-color: #409eff;
  }

  &.is-disabled {
    opacity: 0.5;
    cursor: not-allowed;
  }
}

// Center Canvas
.canvas-area {
  flex: 1;
  background: #f5f7fa;
  display: flex;
  flex-direction: column;
  overflow: hidden;

  .canvas-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 12px;
    padding: 12px 20px;
    background: white;
    border-bottom: 1px solid #e4e7ed;
    font-size: 14px;
    color: #606266;

    .canvas-header-left {
      min-width: 0;
      flex: 1;
    }

    .canvas-header-right {
      display: flex;
      align-items: center;
      gap: 8px;
      flex-shrink: 0;
    }
  }

  .canvas-content {
    flex: 1;
    overflow-y: auto;
    padding: 20px;
  }

  &.drag-over {
    background: #ecf5ff;
  }
}

.empty-column-placeholder {
  padding: 30px;
  text-align: center;
  border: 2px dashed #dcdfe6;
  border-radius: 8px;
  color: #909399;
  font-size: 14px;
}

.empty-column-placeholder.compact {
  padding: 14px;
  font-size: 12px;
}

.designer-section-slot {
  position: relative;
}

.designer-section-slot.is-selected {
  outline: 2px dashed #409eff;
  outline-offset: 6px;
  border-radius: 6px;
}

.designer-section-toolbar {
  display: flex;
  gap: 6px;
  justify-content: flex-end;
  margin-bottom: 12px;
}

.designer-section-body {
  min-height: 24px;
}

.designer-fields-container {
  min-height: 24px;
}

.designer-fields-container.el-row {
  row-gap: 12px;
}

.section-fields-sidebar .field-col {
  margin-bottom: 12px;
}

.field-renderer {
  cursor: move;
}

// Right Panel - Property Editor
.property-panel {
  width: 280px;
  background: white;
  border-left: 1px solid #e4e7ed;
  display: flex;
  flex-direction: column;

  .panel-header {
    padding: 12px 16px;
    border-bottom: 1px solid #e4e7ed;
    font-weight: 500;
    color: #303133;
  }

  .panel-content {
    flex: 1;
    overflow-y: auto;
    padding: 16px;
  }
}

.property-form {
  .property-header {
    display: flex;
    align-items: center;
    gap: 8px;
    margin-bottom: 16px;
    padding-bottom: 12px;
    border-bottom: 1px solid #e4e7ed;

    .el-icon {
      color: #409eff;
    }
  }
}

.no-selection {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 200px;
}

.empty-canvas {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 100%;
  min-height: 400px;
}

.runtime-preview-card {
  width: 100%;
  margin: 0;
  padding: 0;
}

.detail-mode-preview {
  min-height: 100%;

  :deep(.base-detail-page) {
    background: transparent;
  }
}
</style>


