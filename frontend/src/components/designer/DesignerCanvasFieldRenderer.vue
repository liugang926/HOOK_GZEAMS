<script setup lang="ts">
import type { DetailField } from '@/components/common/BaseDetailPage.vue'
import DesignerFieldCard from '@/components/designer/DesignerFieldCard.vue'
import type {
  DesignerRenderField,
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
  renderField: DesignerRenderField
  section: LayoutSection
  sectionId: string
  sectionIndex: number
  isDesignMode: boolean
  selectedId: string
  sizeFeedbackFieldId: string
  sampleData: Record<string, unknown>
  sidebar?: boolean
  allowHorizontalResize: boolean
  allowVerticalResize: boolean
  cardTitles: DesignerCardTitles
  toCanvasField: (field: LayoutField) => LayoutField
  fieldToDesignDisplayField: (field: LayoutField) => DetailField
  getSampleValue: (field: LayoutField) => unknown
  onSelect: (field: LayoutField, section: LayoutSection) => void
  onRemove: (fieldId: string, sectionId: string, sectionIndex?: number) => void
  onResetSize: (fieldId: string) => void
  onResizeStart: (payload: ResizeStartPayload) => void
}>()

const emit = defineEmits<{
  select: []
}>()

function handleSelect() {
  props.onSelect(props.renderField.field, props.section)
  emit('select')
}
</script>

<template>
  <div
    v-if="sidebar"
    class="field-renderer field-col sidebar-field-col"
    :data-field-id="renderField.field.id"
    :data-field-code="renderField.field.fieldCode"
    :data-field-span="renderField.semanticSpan"
    v-bind="renderField.placementAttrs"
  >
    <DesignerFieldCard
      :field="toCanvasField(renderField.field)"
      :display-field="fieldToDesignDisplayField(renderField.field)"
      :value="sampleData[renderField.field.fieldCode] ?? getSampleValue(renderField.field)"
      :selected="isDesignMode && selectedId === renderField.field.id"
      :interactive="isDesignMode"
      :sidebar="true"
      :resizable="isDesignMode"
      :allow-horizontal-resize="allowHorizontalResize"
      :allow-vertical-resize="allowVerticalResize"
      :size-feedback-active="sizeFeedbackFieldId === renderField.field.id"
      :remove-title="cardTitles.remove"
      :resize-title="cardTitles.resize"
      :reset-size-title="cardTitles.reset"
      :sidebar-resize-hint="cardTitles.sidebarOnlyHeight"
      :section-id="sectionId"
      :section-index="sectionIndex"
      @select="handleSelect"
      @remove="onRemove"
      @reset-size="onResetSize"
      @resize-start="onResizeStart"
    />
  </div>

  <el-col
    v-else
    class="field-renderer field-col"
    :span="renderField.span24"
    :data-field-id="renderField.field.id"
    :data-field-code="renderField.field.fieldCode"
    :data-field-span="renderField.semanticSpan"
    v-bind="renderField.placementAttrs"
  >
    <DesignerFieldCard
      :field="toCanvasField(renderField.field)"
      :display-field="fieldToDesignDisplayField(renderField.field)"
      :value="sampleData[renderField.field.fieldCode] ?? getSampleValue(renderField.field)"
      :selected="isDesignMode && selectedId === renderField.field.id"
      :interactive="isDesignMode"
      :resizable="isDesignMode"
      :allow-horizontal-resize="allowHorizontalResize"
      :allow-vertical-resize="allowVerticalResize"
      :size-feedback-active="sizeFeedbackFieldId === renderField.field.id"
      :remove-title="cardTitles.remove"
      :resize-title="cardTitles.resize"
      :reset-size-title="cardTitles.reset"
      :sidebar-resize-hint="cardTitles.sidebarOnlyHeight"
      :section-id="sectionId"
      :section-index="sectionIndex"
      @select="handleSelect"
      @remove="onRemove"
      @reset-size="onResetSize"
      @resize-start="onResizeStart"
    />
  </el-col>
</template>

<style scoped lang="scss">
.field-renderer {
  cursor: move;
}

.sidebar-field-col {
  margin-bottom: 12px;
}
</style>
