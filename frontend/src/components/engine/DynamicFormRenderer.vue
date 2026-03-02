<template>
  <div class="dynamic-form-renderer">
    <div
      v-if="visibleSections.length === 0 || !hasRenderableFields"
      class="dynamic-form-renderer__empty"
    >
      <el-empty :description="emptyText" />
    </div>

    <template
      v-for="section in visibleSections"
      v-else
      :key="sectionKey(section)"
    >
      <el-card
        v-if="shouldRenderSectionCard(section)"
        :shadow="section.shadow || 'never'"
        class="dynamic-form-renderer__section-card"
      >
        <template
          v-if="showSectionTitle(section)"
          #header
        >
          <span>{{ section.title }}</span>
        </template>
        <div class="dynamic-form-renderer__section-body">
          <DynamicFormSection
            :section="section"
            :model-value="modelValue"
            :readonly="readonly"
            :field-permissions="fieldPermissions"
            :business-object="businessObject"
            :instance-id="instanceId"
            :use-form-item="useFormItem"
            :label-width="labelWidth"
            :label-position="labelPosition"
            @update:model-value="(val) => emit('update:modelValue', val)"
          />
        </div>
      </el-card>

      <div
        v-else
        class="dynamic-form-renderer__section"
      >
        <div
          v-if="showSectionTitle(section)"
          class="dynamic-form-renderer__section-title"
        >
          {{ section.title }}
        </div>
        <DynamicFormSection
          :section="section"
          :model-value="modelValue"
          :readonly="readonly"
          :field-permissions="fieldPermissions"
          :business-object="businessObject"
          :instance-id="instanceId"
          :use-form-item="useFormItem"
          :label-width="labelWidth"
          :label-position="labelPosition"
          @update:model-value="(val) => emit('update:modelValue', val)"
        />
      </div>
    </template>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import DynamicFormSection from '@/components/engine/DynamicFormSection.vue'
import type { RuntimeLayoutConfig, RuntimeSection } from '@/types/runtime'
import type { RenderSchema } from '@/platform/layout/renderSchema'
import { projectRuntimeLayoutFromRenderSchema } from '@/platform/layout/renderSchemaProjector'

interface Props {
  layout?: RuntimeLayoutConfig
  schema?: RenderSchema | null
  modelValue: Record<string, any>
  readonly?: boolean
  fieldPermissions?: Record<string, { readonly?: boolean; visible?: boolean; hidden?: boolean }>
  businessObject?: string
  instanceId?: string | null
  useFormItem?: boolean
  labelWidth?: string | number
  labelPosition?: 'left' | 'right' | 'top'
  emptyText?: string
}

const props = withDefaults(defineProps<Props>(), {
  layout: () => ({ sections: [] }),
  schema: null,
  readonly: false,
  fieldPermissions: () => ({}),
  useFormItem: true,
  labelWidth: '120px',
  labelPosition: 'right',
  emptyText: '���޿��ò���'
})

const emit = defineEmits<{
  (e: 'update:modelValue', value: Record<string, any>): void
}>()

const effectiveLayout = computed<RuntimeLayoutConfig>(() => {
  if (props.schema) {
    return projectRuntimeLayoutFromRenderSchema(props.schema)
  }
  return props.layout || { sections: [] }
})

const visibleSections = computed<RuntimeSection[]>(() => {
  const sections = effectiveLayout.value.sections || []
  return sections.filter((section) => section.visible !== false)
})

const hasRenderableFields = computed(() => {
  return visibleSections.value.some((section) => {
    if (section.type === 'tab') {
      return (section.tabs || []).some((tab) => (tab.fields || []).length > 0)
    }
    if (section.type === 'collapse') {
      return (section.items || []).some((item) => (item.fields || []).length > 0)
    }
    return (section.fields || []).length > 0
  })
})

const sectionKey = (section: RuntimeSection) => section.id || section.name || ''

const showSectionTitle = (section: RuntimeSection) => {
  return section.showTitle !== false && !!section.title
}

const shouldRenderSectionCard = (section: RuntimeSection) => {
  return section.type === 'card' || section.renderAsCard === true
}
</script>

<style scoped lang="scss">
.dynamic-form-renderer {
  width: 100%;

  &__section {
    margin-bottom: 20px;
  }

  &__section-title {
    font-weight: 600;
    margin-bottom: 12px;
  }

  &__section-card {
    margin-bottom: 20px;
  }

  &__section-body {
    padding-top: 4px;
  }

  &__empty {
    padding: 32px 0;
  }
}
</style>
