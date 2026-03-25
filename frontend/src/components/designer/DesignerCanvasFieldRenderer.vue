<script setup lang="ts">
import { computed } from 'vue'
import type { DetailField } from '@/components/common/BaseDetailPage.vue'
import DesignerFieldCard from '@/components/designer/DesignerFieldCard.vue'
import { useDetailGridPlacement } from '@/composables/useDetailGridPlacement'
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
  selectField: (field: LayoutField, section: LayoutSection) => void
  removeFieldFromSection: (fieldId: string, sectionId: string, sectionIndex?: number) => void
  resetFieldSize: (fieldId: string) => void
  startFieldResize: (payload: ResizeStartPayload) => void
  updateFieldLabel: (fieldId: string, label: string) => void
}>()

const emit = defineEmits<{
  select: []
}>()

const { getFieldColStyle } = useDetailGridPlacement({
  fieldSpan: computed(() => 1)
})

function handleSelect() {
  props.selectField(props.renderField.field, props.section)
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
      @remove="removeFieldFromSection"
      @reset-size="resetFieldSize"
      @resize-start="startFieldResize"
      @label-update="updateFieldLabel"
    />
  </div>

  <div
    v-else
    class="field-renderer field-col"
    :style="getFieldColStyle(toCanvasField(renderField.field), section)"
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
      @remove="removeFieldFromSection"
      @reset-size="resetFieldSize"
      @resize-start="startFieldResize"
      @label-update="updateFieldLabel"
    />
  </div>
</template>

<style scoped lang="scss">
.field-renderer {
  cursor: move;
}

.sidebar-field-col {
  margin-bottom: 12px;
}
</style>
