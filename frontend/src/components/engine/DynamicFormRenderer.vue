<template>
  <div class="dynamic-form-renderer">
    <div
      v-if="visibleSections.length === 0 || !hasRenderableFields"
      class="dynamic-form-renderer__empty"
    >
      <el-empty :description="emptyText" />
    </div>

    <div
      v-else
      class="dynamic-form-renderer__layout"
      :class="{ 'has-sidebar': sidebarSections.length > 0 }"
    >
      <div class="dynamic-form-renderer__main">
        <template
          v-for="section in mainSections"
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
                @request-save="emit('request-save')"
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
              @request-save="emit('request-save')"
            />
          </div>
        </template>
      </div>

      <div
        v-if="sidebarSections.length > 0"
        class="dynamic-form-renderer__sidebar"
      >
        <template
          v-for="section in sidebarSections"
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
                @request-save="emit('request-save')"
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
              @request-save="emit('request-save')"
            />
          </div>
        </template>
      </div>
    </div>
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
  emptyText: 'No layout fields available'
})

const emit = defineEmits<{
  (e: 'update:modelValue', value: Record<string, any>): void
  (e: 'request-save'): void
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

const mainSections = computed<RuntimeSection[]>(() => {
  return visibleSections.value.filter((section) => section.position !== 'sidebar')
})

const sidebarSections = computed<RuntimeSection[]>(() => {
  return visibleSections.value.filter((section) => section.position === 'sidebar')
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

  &__layout {
    display: block;

    &.has-sidebar {
      display: grid;
      grid-template-columns: minmax(0, 1fr) 320px;
      gap: 20px;
      align-items: start;
    }
  }

  &__main {
    min-width: 0;
  }

  &__sidebar {
    min-width: 0;
  }

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

@media (max-width: 1200px) {
  .dynamic-form-renderer {
    &__layout {
      &.has-sidebar {
        grid-template-columns: minmax(0, 1fr);
      }
    }
  }
}
</style>
