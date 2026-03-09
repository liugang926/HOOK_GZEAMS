<template>
  <div>
    <template v-if="section.type === 'tab'">
      <el-tabs
        v-model="activeTabs[sectionKey]"
        type="card"
      >
        <el-tab-pane
          v-for="tab in section.tabs || []"
          :key="tab.id || tab.name"
          :name="tab.id || tab.name"
          :label="getDisplayText(tab.title) || tab.name"
        >
          <div
            class="dynamic-form-section__fields"
            :class="getColumnClass(section)"
          >
            <div
              v-for="item in getFieldItems(tab.fields || [])"
              :key="item.code"
              class="dynamic-form-section__field"
              :style="getGridStyle(item, section)"
            >
              <template v-if="item.visible">
                <el-form-item
                  v-if="useFormItem"
                  :label="item.label"
                  :prop="item.code"
                  :required="item.required"
                  :label-width="labelWidth"
                  :label-position="labelPosition"
                >
                  <RuntimeFieldControl
                    :field="item.field"
                    :model-value="item.value"
                    :form-data="modelValue"
                    :disabled="item.readonly"
                    @update:model-value="(val) => handleFieldChange(item.field, val)"
                    @request-save="emit('request-save')"
                  />
                </el-form-item>
                <RuntimeFieldControl
                  v-else
                  :field="item.field"
                  :model-value="item.value"
                  :form-data="modelValue"
                  :disabled="item.readonly"
                  @update:model-value="(val) => handleFieldChange(item.field, val)"
                  @request-save="emit('request-save')"
                />
              </template>
            </div>
          </div>
        </el-tab-pane>
      </el-tabs>
    </template>

    <template v-else-if="section.type === 'collapse'">
      <el-collapse v-model="activeCollapses[sectionKey]">
        <el-collapse-item
          v-for="item in section.items || []"
          :key="item.id || item.name"
          :name="item.id || item.name"
          :title="getDisplayText(item.title) || item.name"
        >
          <div
            class="dynamic-form-section__fields"
            :class="getColumnClass(section)"
          >
            <div
              v-for="fieldItem in getFieldItems(item.fields || [])"
              :key="fieldItem.code"
              class="dynamic-form-section__field"
              :style="getGridStyle(fieldItem, section)"
            >
              <template v-if="fieldItem.visible">
                <el-form-item
                  v-if="useFormItem"
                  :label="fieldItem.label"
                  :prop="fieldItem.code"
                  :required="fieldItem.required"
                  :label-width="labelWidth"
                  :label-position="labelPosition"
                >
                  <RuntimeFieldControl
                    :field="fieldItem.field"
                    :model-value="fieldItem.value"
                    :form-data="modelValue"
                    :disabled="fieldItem.readonly"
                    @update:model-value="(val) => handleFieldChange(fieldItem.field, val)"
                    @request-save="emit('request-save')"
                  />
                </el-form-item>
                <RuntimeFieldControl
                  v-else
                  :field="fieldItem.field"
                  :model-value="fieldItem.value"
                  :form-data="modelValue"
                  :disabled="fieldItem.readonly"
                  @update:model-value="(val) => handleFieldChange(fieldItem.field, val)"
                  @request-save="emit('request-save')"
                />
              </template>
            </div>
          </div>
        </el-collapse-item>
      </el-collapse>
    </template>

    <template v-else>
      <div
        class="dynamic-form-section__fields"
        :class="getColumnClass(section)"
      >
        <div
          v-for="item in getFieldItems(section.fields || [])"
          :key="item.code"
          class="dynamic-form-section__field"
          :style="getGridStyle(item, section)"
        >
          <template v-if="item.visible">
            <el-form-item
              v-if="useFormItem"
              :label="item.label"
              :prop="item.code"
              :required="item.required"
              :label-width="labelWidth"
              :label-position="labelPosition"
            >
              <RuntimeFieldControl
                :field="item.field"
                :model-value="item.value"
                :form-data="modelValue"
                :disabled="item.readonly"
                @update:model-value="(val) => handleFieldChange(item.field, val)"
                @request-save="emit('request-save')"
              />
            </el-form-item>
            <RuntimeFieldControl
              v-else
              :field="item.field"
              :model-value="item.value"
              :form-data="modelValue"
              :disabled="item.readonly"
              @update:model-value="(val) => handleFieldChange(item.field, val)"
              @request-save="emit('request-save')"
            />
          </template>
        </div>
      </div>
    </template>
  </div>
</template>

<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import RuntimeFieldControl from '@/components/engine/RuntimeFieldControl.vue'
import type { RuntimeField, RuntimeSection } from '@/types/runtime'
import { getFieldValue, setFieldValue } from '@/components/engine/valueAccessor'
import { normalizeSpan } from '@/adapters/layoutNormalizer'
import { placeCanvasFields, toCanvasGridStyle, type CanvasPlacement } from '@/platform/layout/canvasLayout'
import { resolveTranslatableText } from '@/utils/localeText'

interface Props {
  section: RuntimeSection
  modelValue: Record<string, any>
  readonly?: boolean
  fieldPermissions?: Record<string, { readonly?: boolean; visible?: boolean; hidden?: boolean }>
  businessObject?: string
  instanceId?: string | null
  useFormItem?: boolean
  labelWidth?: string | number
  labelPosition?: 'left' | 'right' | 'top'
}

const props = withDefaults(defineProps<Props>(), {
  readonly: false,
  fieldPermissions: () => ({}),
  useFormItem: true,
  labelWidth: '120px',
  labelPosition: 'right'
})

const { locale } = useI18n()

const getDisplayText = (value: any): string => {
  return resolveTranslatableText(value, locale.value as 'zh-CN' | 'en-US')
}

const emit = defineEmits<{
  (e: 'update:modelValue', value: Record<string, any>): void
  (e: 'request-save'): void
}>()

const sectionKey = computed(() => props.section.id || props.section.name || 'section')

const getSectionColumns = (section: RuntimeSection) => {
  if ((section as any).position === 'sidebar') return 1
  return Number((section as any).columns || (section as any).columnCount || (section as any).column || 2) || 2
}

const resolveFieldVisibility = (field: RuntimeField) => {
  const perm = props.fieldPermissions[field.code]
  if (perm?.hidden === true) return false
  if (perm?.visible === false) return false
  if (field.hidden === true) return false
  if (field.visible === false) return false
  return true
}

const resolveFieldReadonly = (field: RuntimeField) => {
  if (props.readonly) return true
  const perm = props.fieldPermissions[field.code]
  if (perm?.readonly === true) return true
  if (field.readonly === true) return true
  return false
}

const enrichField = (field: RuntimeField): RuntimeField => {
  const next = { ...field }
  if (props.businessObject) next.objectCode = props.businessObject
  if (props.instanceId !== undefined) next.instanceId = props.instanceId
  return next
}

const getFieldItems = (fields: RuntimeField[] = []) => {
  const columns = getSectionColumns(props.section)
  const placedFields = placeCanvasFields(
    fields.map((field) => ({
      ...field,
      span: field.span ?? 1,
      minHeight: field.minHeight
    })),
    columns,
    { preferSavedPlacement: true }
  )

  return placedFields.map((field) => {
    const enriched = enrichField(field as RuntimeField)
    const placement = ((enriched as any).placement || (field as any).placement || null) as CanvasPlacement | null
    return {
      code: enriched.code,
      field: enriched,
      label: enriched.label || enriched.code,
      required: !!enriched.required,
      visible: resolveFieldVisibility(enriched),
      readonly: resolveFieldReadonly(enriched),
      span: enriched.span || 1,
      placement,
      value: getFieldValue(enriched, props.modelValue)
    }
  })
}

const getGridStyle = (item: { span?: number; placement?: CanvasPlacement | null }, section: RuntimeSection) => {
  if (item.placement) {
    return toCanvasGridStyle(item.placement)
  }

  const columns = getSectionColumns(section)
  const span = normalizeSpan(item.span ?? 1, columns)
  return {
    gridColumn: `span ${span}`
  }
}

const getColumnClass = (section: RuntimeSection) => {
  const columns = getSectionColumns(section)
  return `columns-${columns}`
}

const handleFieldChange = (field: RuntimeField, value: any) => {
  emit('update:modelValue', setFieldValue(field, props.modelValue, value))
}

const activeTabs = ref<Record<string, string>>({})
const activeCollapses = ref<Record<string, string[]>>({})

watch(
  () => props.section,
  (section) => {
    if (!section) return
    if (section.type === 'tab') {
      const tabs = section.tabs || []
      if (!activeTabs.value[sectionKey.value] && tabs.length > 0) {
        activeTabs.value[sectionKey.value] = tabs[0].id || tabs[0].name || ''
      }
    }

    if (section.type === 'collapse') {
      const items = section.items || []
      if (!activeCollapses.value[sectionKey.value]) {
        activeCollapses.value[sectionKey.value] = items
          .filter((item) => item.collapsed !== true)
          .map((item) => item.id || item.name || '')
      }
    }
  },
  { immediate: true, deep: true }
)
</script>

<style scoped lang="scss">
.dynamic-form-section__fields {
  display: grid;
  gap: 12px;
  grid-auto-flow: row dense;
  grid-auto-rows: minmax(56px, auto);
}

.dynamic-form-section__field {
  min-width: 0;
}

.dynamic-form-section__fields.columns-1 {
  grid-template-columns: 1fr;
}

.dynamic-form-section__fields.columns-2 {
  grid-template-columns: repeat(2, 1fr);
}

.dynamic-form-section__fields.columns-3 {
  grid-template-columns: repeat(3, 1fr);
}

.dynamic-form-section__fields.columns-4 {
  grid-template-columns: repeat(4, 1fr);
}
</style>
