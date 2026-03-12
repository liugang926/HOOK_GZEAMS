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
          <div class="property-header__title">
            <el-icon><Edit /></el-icon>
            <span>{{ t('system.pageLayout.designer.panel.fieldProperties') }}</span>
          </div>
          <el-tag
            size="small"
            effect="plain"
            class="property-header__tag"
          >
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
          <div class="property-header__title">
            <el-icon><Grid /></el-icon>
            <span>{{ t('system.pageLayout.designer.panel.sectionProperties') }}</span>
          </div>
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

<style scoped lang="scss">
.property-panel {
  width: 100%;
  height: 100%;
  min-height: 0;
  min-width: 0;
  display: flex;
  flex-direction: column;
  background: linear-gradient(180deg, #ffffff 0%, #fbfcfe 100%);
}

.panel-header {
  padding: 12px 14px 10px;
  border-bottom: 1px solid #e4e7ed;
  font-size: 11px;
  font-weight: 700;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  color: #4b5563;
  flex-shrink: 0;
  background: rgba(255, 255, 255, 0.94);
}

.panel-content {
  flex: 1;
  min-height: 0;
  overflow-y: auto;
  padding: 14px 14px 40px;
  overscroll-behavior: contain;
}

.panel-content::-webkit-scrollbar {
  width: 6px;
}

.panel-content::-webkit-scrollbar-thumb {
  background: rgba(15, 23, 42, 0.14);
  border-radius: 999px;
}

.property-form {
  min-width: 0;
  display: flex;
  flex-direction: column;
}

.property-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
  margin-bottom: 14px;
  padding: 0 2px 12px;
  border-bottom: 1px solid #ebeef5;
}

.property-header__title {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  min-width: 0;
  font-size: 13px;
  font-weight: 700;
  color: #1f2937;
}

.property-header__title :deep(.el-icon) {
  color: #2563eb;
}

.property-header__tag {
  flex-shrink: 0;
  border-radius: 999px;
}

.no-selection {
  min-height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
}
</style>
