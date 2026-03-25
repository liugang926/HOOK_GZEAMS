<script setup lang="ts">
import { computed } from 'vue'
import { DCaret } from '@element-plus/icons-vue'
import type { DetailField } from '@/components/common/BaseDetailPage.vue'
import FieldDisplay from '@/components/common/FieldDisplay.vue'
import DesignerCanvasFieldRenderer from '@/components/designer/DesignerCanvasFieldRenderer.vue'
import { useDetailGridPlacement } from '@/composables/useDetailGridPlacement'
import type {
  DesignerRenderSection,
  DesignerAnyRecord,
  LayoutField,
  LayoutSection,
  ResizeStartPayload
} from '@/components/designer/designerTypes'

type DetailRegionPreviewColumn = DesignerAnyRecord & {
  key: string
  label: string
}

interface DesignerCardTitles {
  remove: string
  resize: string
  reset: string
  sidebarOnlyHeight: string
}

interface DesignerSectionActionLabels {
  moveUp: string
  moveDown: string
  reorder: string
}

const props = defineProps<{
  renderSection: DesignerRenderSection
  sectionIndex: number
  totalSectionCount: number
  isDesignMode: boolean
  selectedId: string
  activeTabName?: string
  activeCollapseNames?: string[]
  sizeFeedbackFieldId: string
  sampleData: Record<string, unknown>
  cardTitles: DesignerCardTitles
  sectionActionLabels: DesignerSectionActionLabels
  toCanvasField: (field: LayoutField) => LayoutField
  fieldToDesignDisplayField: (field: LayoutField) => DetailField
  getSampleValue: (field: LayoutField) => unknown
  selectSection: (sectionId: string) => void
  maybeSelectSection: (sectionId: string) => void
  maybeSelectField: (field: LayoutField, section: LayoutSection) => void
  removeField: (fieldId: string, sectionId: string, sectionIndex?: number) => void
  updateFieldLabel: (fieldId: string, label: string) => void
  handleFieldSizeReset: (fieldId: string) => void
  handleFieldResizeStart: (payload: ResizeStartPayload) => void
  toggleSectionCollapse: (sectionId: string) => void
  moveSection: (sectionId: string, direction: 'up' | 'down') => void
  deleteSection: (sectionId: string) => void
  handleSectionDragStart: (event: DragEvent, sectionId: string) => void
  handleDragEnd: () => void
  handleTabDrop: (event: DragEvent) => void
  handleCollapseDrop: (event: DragEvent) => void
  handleSectionDrop: (event: DragEvent) => void
  handleSectionDragOver: (event: DragEvent) => void
  handleSectionDragLeave: (event: DragEvent) => void
  t: (key: string) => string
}>()

const emit = defineEmits<{
  'update:active-tab-name': [value: string]
  'update:active-collapse-names': [value: string[]]
}>()

const { getSectionCanvasStyle } = useDetailGridPlacement({
  fieldSpan: computed(() => 1) // default field span is 1 column in grid
})

const activeTabModel = computed({
  get: () => props.activeTabName || '',
  set: (value: string) => emit('update:active-tab-name', value)
})

const activeCollapseModel = computed({
  get: () => props.activeCollapseNames || [],
  set: (value: string[]) => emit('update:active-collapse-names', value)
})

const detailRegionFieldCode = computed(() => {
  return String(
    props.renderSection.section.fieldCode ||
    props.renderSection.section.field_code ||
    ''
  ).trim()
})

const detailRegionPreviewColumns = computed<DetailRegionPreviewColumn[]>(() => {
  const section = props.renderSection.section || {}
  const relatedFields = Array.isArray(section.relatedFields)
    ? section.relatedFields
    : Array.isArray(section.related_fields)
      ? section.related_fields
      : []
  const lookupColumns = Array.isArray(section.lookupColumns)
    ? section.lookupColumns
    : Array.isArray(section.lookup_columns)
      ? section.lookup_columns
      : []
  const source = relatedFields.length > 0 ? relatedFields : lookupColumns

  return source.reduce<DetailRegionPreviewColumn[]>((columns, column) => {
      const record = (column || {}) as DesignerAnyRecord
      const key = String(record.code || record.fieldCode || record.field_code || record.key || '').trim()
      if (!key) return columns
      columns.push({
        ...record,
        key,
        label: String(record.label || record.name || key).trim() || key
      })
      return columns
    }, [])
})

const buildDetailRegionPreviewCell = (column: DetailRegionPreviewColumn, rowIndex: number): unknown => {
  const fieldCode = String(column.key || '').trim()
  const fieldType = String(column.fieldType || column.field_type || 'text').trim() || 'text'
  const label = String(column.label || column.name || fieldCode).trim() || fieldCode
  const baseValue = props.getSampleValue({
    id: `detail_region_preview_${fieldCode}`,
    fieldCode,
    label,
    fieldType,
    span: 1
  } as LayoutField)

  if (typeof baseValue === 'number' && Number.isFinite(baseValue)) {
    return baseValue + rowIndex
  }
  if (typeof baseValue === 'boolean') {
    return rowIndex % 2 === 0 ? baseValue : !baseValue
  }
  if (typeof baseValue === 'string' && baseValue) {
    if (fieldType === 'date' || fieldType === 'datetime' || fieldType === 'time' || fieldType === 'year' || fieldType === 'month') {
      return baseValue
    }
    return `${baseValue} ${rowIndex + 1}`
  }

  return baseValue
}

const detailRegionPreviewRows = computed<Record<string, unknown>[]>(() => {
  const fieldCode = detailRegionFieldCode.value
  const rawRows = fieldCode ? props.sampleData[fieldCode] : undefined
  if (Array.isArray(rawRows) && rawRows.length > 0) {
    return rawRows
      .filter((row): row is Record<string, unknown> => !!row && typeof row === 'object' && !Array.isArray(row))
      .slice(0, 5)
  }

  if (detailRegionPreviewColumns.value.length === 0) return []

  return Array.from({ length: 3 }, (_, rowIndex) => {
    const row: Record<string, unknown> = {}
    detailRegionPreviewColumns.value.forEach((column) => {
      row[String(column.key || '')] = buildDetailRegionPreviewCell(column, rowIndex)
    })
    return row
  })
})

const detailRegionPreviewField = computed(() => ({
  type: 'sub_table',
  fieldType: 'sub_table',
  componentProps: {
    columns: detailRegionPreviewColumns.value
  }
}))

const detailRegionPreviewModeLabel = computed(() => {
  const detailEditMode = String(
    props.renderSection.section.detailEditMode ||
    props.renderSection.section.detail_edit_mode ||
    ''
  ).trim()

  if (detailEditMode === 'readonly_table') {
    return props.t('system.pageLayout.designer.sectionProperties.options.detailEditMode.readonlyTable')
  }
  if (detailEditMode === 'nested_form') {
    return props.t('system.pageLayout.designer.sectionProperties.options.detailEditMode.nestedForm')
  }
  return props.t('system.pageLayout.designer.sectionProperties.options.detailEditMode.inlineTable')
})

const isSelected = computed(() => props.isDesignMode && props.selectedId === props.renderSection.id)
const canMoveUp = computed(() => props.sectionIndex > 0)
const canMoveDown = computed(() => props.sectionIndex < props.totalSectionCount - 1)
</script>

<template>
  <div
    class="designer-section-slot layout-section"
    data-testid="layout-section"
    :class="{ 'is-selected': isSelected }"
    :data-section-id="renderSection.id"
    :data-section-position="renderSection.position"
    @click.stop="maybeSelectSection(renderSection.id)"
    @drop="handleSectionDrop"
    @dragover="handleSectionDragOver"
    @dragleave="handleSectionDragLeave"
  >
    <div
      v-if="isSelected"
      class="designer-section-toolbar"
      @click.stop
    >
      <el-button
        size="small"
        text
        class="designer-section-drag-handle"
        draggable="true"
        :title="sectionActionLabels.reorder"
        :aria-label="sectionActionLabels.reorder"
        @dragstart="handleSectionDragStart($event, renderSection.id)"
        @dragend="handleDragEnd"
      >
        <el-icon><DCaret /></el-icon>
      </el-button>
      <el-button
        size="small"
        text
        @click="selectSection(renderSection.id)"
      >
        {{ t('system.pageLayout.designer.actions.editSection') }}
      </el-button>
      <el-button
        size="small"
        text
        :disabled="!canMoveUp"
        @click="moveSection(renderSection.id, 'up')"
      >
        {{ sectionActionLabels.moveUp }}
      </el-button>
      <el-button
        size="small"
        text
        :disabled="!canMoveDown"
        @click="moveSection(renderSection.id, 'down')"
      >
        {{ sectionActionLabels.moveDown }}
      </el-button>
      <el-button
        v-if="renderSection.collapsible"
        size="small"
        text
        @click="toggleSectionCollapse(renderSection.id)"
      >
        {{ renderSection.collapsed ? t('common.actions.expand') : t('common.actions.collapse') }}
      </el-button>
      <el-button
        size="small"
        text
        type="danger"
        @click="deleteSection(renderSection.id)"
      >
        {{ t('system.pageLayout.designer.actions.deleteSection') }}
      </el-button>
    </div>

    <template v-if="renderSection.type === 'tab'">
      <el-tabs
        v-model="activeTabModel"
        type="card"
      >
        <el-tab-pane
          v-for="tab in renderSection.tabs"
          :key="tab.id"
          :label="tab.title"
          :name="tab.id"
          class="tab-pane-content"
          :data-tab-id="tab.id"
          :data-section-id="renderSection.id"
          @drop="handleTabDrop"
          @dragover="handleSectionDragOver"
          @dragleave="handleSectionDragLeave"
        >
          <div
            class="tab-fields designer-fields-container detail-canvas-grid dynamic-form-section__fields"
            :style="getSectionCanvasStyle(renderSection.section)"
            data-container-kind="tab"
            :data-section-id="renderSection.id"
            :data-tab-id="tab.id"
          >
            <DesignerCanvasFieldRenderer
              v-for="tabField in tab.fields"
              :key="tabField.field.id"
              :render-field="tabField"
              :section="renderSection.section"
              :section-id="renderSection.id"
              :section-index="sectionIndex"
              :is-design-mode="isDesignMode"
              :selected-id="selectedId"
              :size-feedback-field-id="sizeFeedbackFieldId"
              :sample-data="sampleData"
              :allow-horizontal-resize="true"
              :allow-vertical-resize="true"
              :card-titles="cardTitles"
              :to-canvas-field="toCanvasField"
              :field-to-design-display-field="fieldToDesignDisplayField"
              :get-sample-value="getSampleValue"
              :select-field="maybeSelectField"
              :remove-field-from-section="removeField"
              :update-field-label="updateFieldLabel"
              :reset-field-size="handleFieldSizeReset"
              :start-field-resize="handleFieldResizeStart"
            />
            <div
              v-if="tab.fields.length === 0"
              class="empty-column-placeholder compact"
              style="grid-column: 1 / -1;"
            >
              {{ t('system.pageLayout.designer.hints.dropToTab') }}
            </div>
          </div>
        </el-tab-pane>
      </el-tabs>
    </template>

    <template v-else-if="renderSection.type === 'collapse'">
      <el-collapse
        v-model="activeCollapseModel"
        :accordion="false"
      >
        <el-collapse-item
          v-for="item in renderSection.items"
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
            :data-section-id="renderSection.id"
            :data-collapse-id="item.id"
            @drop="handleCollapseDrop"
            @dragover="handleSectionDragOver"
            @dragleave="handleSectionDragLeave"
          >
            <div
              class="designer-fields-container detail-canvas-grid"
              :style="getSectionCanvasStyle(renderSection.section)"
              data-container-kind="collapse"
              :data-section-id="renderSection.id"
              :data-collapse-id="item.id"
            >
              <DesignerCanvasFieldRenderer
                v-for="itemField in item.fields"
                :key="itemField.field.id"
                :render-field="itemField"
                :section="renderSection.section"
                :section-id="renderSection.id"
                :section-index="sectionIndex"
                :is-design-mode="isDesignMode"
                :selected-id="selectedId"
                :size-feedback-field-id="sizeFeedbackFieldId"
                :sample-data="sampleData"
                :allow-horizontal-resize="renderSection.position !== 'sidebar'"
                :allow-vertical-resize="true"
                :card-titles="cardTitles"
                :to-canvas-field="toCanvasField"
                :field-to-design-display-field="fieldToDesignDisplayField"
                :get-sample-value="getSampleValue"
                :select-field="maybeSelectField"
                :remove-field-from-section="removeField"
                :update-field-label="updateFieldLabel"
                :reset-field-size="handleFieldSizeReset"
                :start-field-resize="handleFieldResizeStart"
              />
              <div
                v-if="item.fields.length === 0"
                class="empty-column-placeholder compact"
                style="grid-column: 1 / -1;"
              >
                {{ t('system.pageLayout.designer.hints.dropToCollapse') }}
              </div>
            </div>
          </div>
        </el-collapse-item>
      </el-collapse>
    </template>

    <template v-else-if="renderSection.type === 'detail-region'">
      <div class="designer-section-body">
        <div class="detail-region-placeholder">
          <div class="detail-region-placeholder__title">
            {{ renderSection.title }}
          </div>
          <div class="detail-region-placeholder__meta">
            <span>{{ t('system.pageLayout.designer.hints.detailRegionRelation') }}: {{ renderSection.section.relationCode || renderSection.section.relation_code || '-' }}</span>
            <span>{{ t('system.pageLayout.designer.hints.detailRegionField') }}: {{ renderSection.section.fieldCode || renderSection.section.field_code || '-' }}</span>
            <span>{{ t('system.pageLayout.designer.hints.detailRegionTarget') }}: {{ renderSection.section.targetObjectCode || renderSection.section.target_object_code || '-' }}</span>
            <span>{{ t('system.pageLayout.designer.hints.detailRegionMode') }}: {{ detailRegionPreviewModeLabel }}</span>
            <span>{{ t('system.pageLayout.designer.hints.detailRegionColumns') }}: {{ detailRegionPreviewColumns.length }}</span>
          </div>
          <div
            v-if="detailRegionPreviewColumns.length > 0 && detailRegionPreviewRows.length > 0"
            class="detail-region-placeholder__preview"
            data-testid="detail-region-live-preview"
          >
            <FieldDisplay
              :field="detailRegionPreviewField"
              :value="detailRegionPreviewRows"
              :defer-reference-resolve="true"
            />
          </div>
          <div
            v-else
            class="detail-region-placeholder__summary"
          >
            {{ t('system.pageLayout.designer.hints.detailRegionSummary') }}
          </div>
        </div>
      </div>
    </template>

    <template v-else>
      <div
        class="designer-section-body"
        :data-section-id="renderSection.id"
        @drop="handleSectionDrop"
        @dragover="handleSectionDragOver"
        @dragleave="handleSectionDragLeave"
      >
        <template v-if="renderSection.position === 'sidebar'">
          <div
            class="section-fields-sidebar designer-fields-container detail-canvas-grid sidebar-canvas-grid dynamic-form-section__fields"
            :style="getSectionCanvasStyle(renderSection.section)"
            data-container-kind="section"
            :data-section-id="renderSection.id"
          >
            <DesignerCanvasFieldRenderer
              v-for="sectionField in renderSection.fields"
              :key="sectionField.field.id"
              :render-field="sectionField"
              :section="renderSection.section"
              :section-id="renderSection.id"
              :section-index="sectionIndex"
              :is-design-mode="isDesignMode"
              :selected-id="selectedId"
              :size-feedback-field-id="sizeFeedbackFieldId"
              :sample-data="sampleData"
              :sidebar="true"
              :allow-horizontal-resize="false"
              :allow-vertical-resize="true"
              :card-titles="cardTitles"
              :to-canvas-field="toCanvasField"
              :field-to-design-display-field="fieldToDesignDisplayField"
              :get-sample-value="getSampleValue"
              :select-field="maybeSelectField"
              :remove-field-from-section="removeField"
              :update-field-label="updateFieldLabel"
              :reset-field-size="handleFieldSizeReset"
              :start-field-resize="handleFieldResizeStart"
            />
            <div
              v-if="renderSection.fields.length === 0"
              class="empty-column-placeholder compact"
              style="grid-column: 1 / -1;"
            >
              {{ t('system.pageLayout.designer.hints.dropToSection') }}
            </div>
          </div>
        </template>
        <template v-else>
          <div
            class="section-fields designer-fields-container detail-canvas-grid dynamic-form-section__fields"
            :style="getSectionCanvasStyle(renderSection.section)"
            data-container-kind="section"
            :data-section-id="renderSection.id"
          >
            <DesignerCanvasFieldRenderer
              v-for="sectionField in renderSection.fields"
              :key="sectionField.field.id"
              :render-field="sectionField"
              :section="renderSection.section"
              :section-id="renderSection.id"
              :section-index="sectionIndex"
              :is-design-mode="isDesignMode"
              :selected-id="selectedId"
              :size-feedback-field-id="sizeFeedbackFieldId"
              :sample-data="sampleData"
              :allow-horizontal-resize="true"
              :allow-vertical-resize="true"
              :card-titles="cardTitles"
              :to-canvas-field="toCanvasField"
              :field-to-design-display-field="fieldToDesignDisplayField"
              :get-sample-value="getSampleValue"
              :select-field="maybeSelectField"
              :remove-field-from-section="removeField"
              :update-field-label="updateFieldLabel"
              :reset-field-size="handleFieldSizeReset"
              :start-field-resize="handleFieldResizeStart"
            />
            <div
              v-if="renderSection.fields.length === 0"
              class="empty-column-placeholder compact"
              style="grid-column: 1 / -1;"
            >
              {{ t('system.pageLayout.designer.hints.dropToSection') }}
            </div>
          </div>
        </template>
      </div>
    </template>
  </div>
</template>

<style scoped lang="scss">
.empty-column-placeholder {
  padding: 28px;
  text-align: center;
  border: 2px dashed #dcdfe6;
  border-radius: 8px;
  color: #909399;
  font-size: 13px;
  background: linear-gradient(135deg, #fafbfc 0%, #f5f7fa 100%);
  transition: all 0.25s ease;

  &:hover {
    border-color: var(--el-color-primary-light-5, #79bbff);
    color: var(--el-color-primary, #409eff);
    background: linear-gradient(135deg, #f0f7ff 0%, #ecf5ff 100%);
  }
}

.empty-column-placeholder.compact {
  padding: 14px;
  font-size: 12px;
}

.designer-section-slot {
  position: relative;
  border-radius: 8px;
  transition: outline 0.2s ease, outline-offset 0.2s ease;
}

.designer-section-slot.is-selected {
  outline: 2px solid var(--el-color-primary, #409eff);
  outline-offset: 4px;
  border-radius: 8px;
}

.designer-section-toolbar {
  display: flex;
  gap: 4px;
  justify-content: flex-end;
  margin-bottom: 8px;
  padding: 4px 8px;
  background: rgba(255, 255, 255, 0.9);
  backdrop-filter: blur(4px);
  border-radius: 6px;
  border: 1px solid #e4e7ed;
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.06);
}

.designer-section-body,
.designer-fields-container {
  min-height: 24px;
}

.detail-region-placeholder__preview {
  margin-top: 12px;
}

.detail-region-placeholder__preview :deep(.subtable-display) {
  margin: 0;
}

.detail-region-placeholder__preview :deep(.subtable-table) {
  border-radius: 10px;
  overflow: hidden;
}

.designer-fields-container.el-row {
  row-gap: 12px;
}

.designer-section-drag-handle {
  cursor: grab;
}

.designer-section-drag-handle:active {
  cursor: grabbing;
}

.detail-region-placeholder {
  display: flex;
  flex-direction: column;
  gap: 10px;
  padding: 18px;
  border: 1px dashed rgba(37, 99, 235, 0.32);
  border-radius: 14px;
  background: linear-gradient(180deg, rgba(239, 246, 255, 0.9) 0%, rgba(255, 255, 255, 0.98) 100%);
}

.detail-region-placeholder__title {
  font-size: 15px;
  font-weight: 700;
  color: #1e3a8a;
}

.detail-region-placeholder__meta {
  display: grid;
  gap: 6px;
  color: #475569;
  font-size: 12px;
}

.detail-region-placeholder__summary {
  color: #64748b;
  font-size: 12px;
  line-height: 1.6;
}
</style>
