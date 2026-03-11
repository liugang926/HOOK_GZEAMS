<template>
  <div
    v-if="renderMode === 'design'"
    class="property-panel"
    data-testid="layout-property-panel"
  >
    <div class="panel-header">
      <span>{{ t('system.pageLayout.designer.panel.properties') }}</span>
    </div>
    <div class="panel-content">
      <div
        v-if="!selectedItem"
        class="no-selection"
      >
        <el-empty
          :description="t('system.pageLayout.designer.empty.selectTarget')"
          :image-size="80"
        />
      </div>

      <div
        v-else-if="elementType === 'field'"
        class="property-form"
      >
        <div class="property-header">
          <el-icon><Edit /></el-icon>
          <span>{{ t('system.pageLayout.designer.panel.fieldProperties') }}</span>
          <el-tag size="small">
            {{ selectedFieldCode }}
          </el-tag>
        </div>
        <FieldPropertyEditor
          :model-value="fieldProps"
          data-testid="layout-field-property-editor"
          :field-type="fieldProps.fieldType"
          :mode="mode"
          :translation-mode="translationMode"
          :available-spans="availableSpans"
          :available-span-columns="availableSpanColumns"
          :visibility-field-options="visibilityFieldOptions"
          @update:model-value="$emit('update:fieldProps', $event)"
          @update-property="$emit('fieldPropertyUpdate', $event)"
        />
      </div>

      <div
        v-else
        class="property-form"
      >
        <div class="property-header">
          <el-icon><Grid /></el-icon>
          <span>{{ t('system.pageLayout.designer.panel.sectionProperties') }}</span>
        </div>
        <SectionPropertyEditor
          :model-value="sectionProps"
          data-testid="layout-section-property-editor"
          :section-type="sectionProps.type || 'section'"
          :is-compact-mode="layoutMode === 'Compact'"
          @update:model-value="$emit('update:sectionProps', $event)"
          @update-property="$emit('sectionPropertyUpdate', $event)"
        />
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useI18n } from 'vue-i18n'
import { Edit, Grid } from '@element-plus/icons-vue'
import FieldPropertyEditor from '@/components/designer/FieldPropertyEditor.vue'
import SectionPropertyEditor from '@/components/designer/SectionPropertyEditor.vue'
import type { DesignerConfigNode, LayoutField, LayoutSection } from '@/components/designer/designerTypes'
import type { LayoutMode } from '@/types/layout'

const props = defineProps<{
  renderMode: 'design' | 'preview'
  selectedItem: DesignerConfigNode | null
  elementType: 'field' | 'section' | null
  fieldProps: Partial<LayoutField>
  sectionProps: Partial<LayoutSection>
  availableSpans: number[]
  availableSpanColumns: number
  visibilityFieldOptions: Array<{ label: string; value: string }>
  layoutMode: 'Detail' | 'Compact'
  mode: LayoutMode
  translationMode: boolean
}>()

defineEmits<{
  (e: 'update:fieldProps', value: Partial<LayoutField>): void
  (e: 'update:sectionProps', value: Partial<LayoutSection>): void
  (e: 'fieldPropertyUpdate', payload: { key: string; value: unknown }): void
  (e: 'sectionPropertyUpdate', payload: { key: string; value: unknown }): void
}>()

const { t } = useI18n()

const selectedFieldCode = computed(() => {
  if (!props.selectedItem || props.elementType !== 'field') return ''
  return String((props.selectedItem as LayoutField).fieldCode || '')
})
</script>
