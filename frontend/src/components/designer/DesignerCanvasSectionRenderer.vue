<script setup lang="ts">
import { computed } from 'vue'
import type { DetailField } from '@/components/common/BaseDetailPage.vue'
import DesignerCanvasFieldRenderer from '@/components/designer/DesignerCanvasFieldRenderer.vue'
import { useDetailGridPlacement } from '@/composables/useDetailGridPlacement'
import type {
  DesignerRenderSection,
  LayoutField,
  LayoutSection,
  ResizeStartPayload
} from '@/components/designer/designerTypes'

interface DesignerCardTitles {
  remove: string
  resize: string
  reset: string
  sidebarOnlyHeight: string
}

const props = defineProps<{
  renderSection: DesignerRenderSection
  sectionIndex: number
  isDesignMode: boolean
  selectedId: string
  activeTabName?: string
  activeCollapseNames?: string[]
  sizeFeedbackFieldId: string
  sampleData: Record<string, unknown>
  cardTitles: DesignerCardTitles
  toCanvasField: (field: LayoutField) => LayoutField
  fieldToDesignDisplayField: (field: LayoutField) => DetailField
  getSampleValue: (field: LayoutField) => unknown
  selectSection: (sectionId: string) => void
  maybeSelectSection: (sectionId: string) => void
  maybeSelectField: (field: LayoutField, section: LayoutSection) => void
  removeField: (fieldId: string, sectionId: string, sectionIndex?: number) => void
  handleFieldSizeReset: (fieldId: string) => void
  handleFieldResizeStart: (payload: ResizeStartPayload) => void
  toggleSectionCollapse: (sectionId: string) => void
  deleteSection: (sectionId: string) => void
  handleTabDrop: (event: DragEvent) => void
  handleCollapseDrop: (event: DragEvent) => void
  handleSectionDrop: (event: DragEvent) => void
  handleSectionDragOver: (event: DragEvent) => void
  handleSectionDragLeave: () => void
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

const isSelected = computed(() => props.isDesignMode && props.selectedId === props.renderSection.id)
</script>

<template>
  <div
    class="designer-section-slot layout-section"
    data-testid="layout-section"
    :class="{ 'is-selected': isSelected }"
    :data-section-id="renderSection.id"
    :data-section-position="renderSection.position"
    @click.stop="maybeSelectSection(renderSection.id)"
  >
    <div
      v-if="isSelected"
      class="designer-section-toolbar"
      @click.stop
    >
      <el-button
        size="small"
        text
        @click="selectSection(renderSection.id)"
      >
        {{ t('system.pageLayout.designer.actions.editSection') }}
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
              :on-select="maybeSelectField"
              :on-remove="removeField"
              :on-reset-size="handleFieldSizeReset"
              :on-resize-start="handleFieldResizeStart"
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
                :on-select="maybeSelectField"
                :on-remove="removeField"
                :on-reset-size="handleFieldSizeReset"
                :on-resize-start="handleFieldResizeStart"
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
              :on-select="maybeSelectField"
              :on-remove="removeField"
              :on-reset-size="handleFieldSizeReset"
              :on-resize-start="handleFieldResizeStart"
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
              :on-select="maybeSelectField"
              :on-remove="removeField"
              :on-reset-size="handleFieldSizeReset"
              :on-resize-start="handleFieldResizeStart"
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

.designer-section-body,
.designer-fields-container {
  min-height: 24px;
}

.designer-fields-container.el-row {
  row-gap: 12px;
}
</style>
