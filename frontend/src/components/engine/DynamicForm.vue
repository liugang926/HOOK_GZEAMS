<template>
  <div
    v-loading="loading"
    class="dynamic-form"
  >
    <el-form
      ref="formRef"
      :model="activeFormData"
      :rules="activeFormRules"
      label-width="120px"
      label-position="right"
      class="dynamic-form__form"
    >
      <DynamicFormRenderer
        :layout="activeLayout"
        :schema="activeRenderSchema"
        :model-value="activeFormData"
        :readonly="readonly"
        :field-permissions="fieldPermissions"
        :business-object="businessObject"
        :instance-id="instanceId"
        :use-form-item="true"
        label-width="120px"
        label-position="right"
        @update:model-value="handleModelUpdate"
        @request-save="emit('request-save')"
      />
    </el-form>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import DynamicFormRenderer from '@/components/engine/DynamicFormRenderer.vue'
import { useDynamicForm } from '@/components/engine/hooks'
import type { RuntimeLayoutConfig, RuntimeField } from '@/types/runtime'
import { buildSubmitPayload, getFieldValue } from '@/components/engine/valueAccessor'
import { snakeToCamel } from '@/utils/case'
import { referenceResolver } from '@/platform/reference/referenceResolver'
import { normalizeLayoutConfig } from '@/adapters/layoutNormalizer'
import { mergeRuntimeField } from '@/adapters/fieldAdapter'
import { normalizeFieldType } from '@/utils/fieldType'

interface Props {
  businessObject?: string
  layoutCode?: string
  modelValue?: Record<string, any>
  readonly?: boolean
  showActions?: boolean
  instanceId?: string | null
  fieldPermissions?: Record<string, { readonly?: boolean; visible?: boolean; hidden?: boolean }>
  schema?: Record<string, any> | null
  data?: Record<string, any> | null
}

const props = withDefaults(defineProps<Props>(), {
  layoutCode: 'form',
  readonly: false,
  showActions: true,
  instanceId: null,
  schema: null,
  data: null
})

const emit = defineEmits<{
  (e: 'update:modelValue', value: Record<string, any>): void
  (e: 'dirty-change', isDirty: boolean): void
  (e: 'request-save'): void
}>()

const isSchemaMode = computed(() => !!props.schema)

const schemaFormData = ref<Record<string, any>>({})
const schemaLayout = ref<RuntimeLayoutConfig>({ sections: [] })

const {
  formData,
  formRules,
  runtimeLayout,
  renderSchema,
  loading,
  loadMetadata,
  validate,
  resetFields,
  clearValidation
} = useDynamicForm(
  props.businessObject || '',
  props.layoutCode,
  null,
  null,
  props.instanceId
)

const activeFormData = computed(() => (isSchemaMode.value ? schemaFormData.value : formData.value))
const activeFormRules = computed(() => (isSchemaMode.value ? {} : formRules.value))

const activeRenderSchema = computed(() => {
  if (isSchemaMode.value) return null
  return renderSchema.value
})

const activeLayout = computed<RuntimeLayoutConfig>(() => {
  if (isSchemaMode.value) return schemaLayout.value
  return runtimeLayout.value
})

const fieldPermissions = computed(() => props.fieldPermissions || {})

const flattenLayoutFields = (layout: RuntimeLayoutConfig | null | undefined): RuntimeField[] => {
  if (!layout?.sections) return []

  const out: RuntimeField[] = []
  for (const section of layout.sections) {
    if (!section) continue
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
  return out.filter((f) => !!f?.code)
}

const resolveObjectCode = (refValue: any) => {
  if (!refValue) return ''
  const raw = String(refValue).trim()
  if (!raw) return ''
  const noQuery = raw.split('?')[0].replace(/\/+$/, '')
  const lastDot = noQuery.split('.').pop() || noQuery
  const lastPath = lastDot.split('/').filter(Boolean).pop() || lastDot
  return String(lastPath || '').trim()
}

let lastPrefetchKey = ''
const prefetchReadonlyReferences = async (layout: RuntimeLayoutConfig, model: Record<string, any>) => {
  if (!props.readonly) return
  if (isSchemaMode.value) return
  if (!layout?.sections || !model) return

  const refsByObject = new Map<string, string[]>()

  for (const field of flattenLayoutFields(layout)) {
    if (!field?.code) continue

    const type = field.fieldType
    const isRel =
      type === 'reference' ||
      type === 'user' ||
      type === 'department' ||
      type === 'location' ||
      type === 'organization' ||
      type === 'asset'

    if (!isRel) continue

    const value = getFieldValue(field, model)
    if (value === null || value === undefined || value === '') continue

    const ids: string[] = []
    const pushId = (v: any) => {
      if (!v) return
      if (typeof v === 'object' && v.id) ids.push(String(v.id))
      else if (typeof v === 'string' || typeof v === 'number') ids.push(String(v))
    }

    if (Array.isArray(value)) value.forEach(pushId)
    else pushId(value)

    if (ids.length === 0) continue

    let objectCode = ''
    if (type === 'user') objectCode = 'User'
    else if (type === 'department') objectCode = 'Department'
    else if (type === 'location') objectCode = 'Location'
    else if (type === 'organization') objectCode = 'Organization'
    else if (type === 'asset') objectCode = 'Asset'
    else objectCode = resolveObjectCode((field as any).referenceObject)

    if (!objectCode) continue

    const bucket = refsByObject.get(objectCode) || []
    bucket.push(...ids)
    refsByObject.set(objectCode, bucket)
  }

  const key = Array.from(refsByObject.entries())
    .sort(([a], [b]) => a.localeCompare(b))
    .map(([obj, ids]) => `${obj}=${Array.from(new Set(ids)).sort().join(',')}`)
    .join('|')

  if (!key || key === lastPrefetchKey) return
  lastPrefetchKey = key

  await Promise.all(
    Array.from(refsByObject.entries()).map(([objectCode, ids]) =>
      referenceResolver.resolveMany(objectCode, ids, { concurrency: 6 })
    )
  )
}

const ensureCanonicalKeys = (model: Record<string, any>, layout: RuntimeLayoutConfig) => {
  // Element Plus validation uses `prop=field.code`, so make sure the canonical keys exist.
  const next = { ...(model || {}) }
  for (const field of flattenLayoutFields(layout)) {
    const hasKey = Object.prototype.hasOwnProperty.call(next, field.code)
    const current = hasKey ? next[field.code] : undefined
    const isEmpty = current === undefined || current === null || current === ''
    if (!isEmpty) continue

    const dataKey = field.dataKey || (field.code.includes('_') ? snakeToCamel(field.code) : field.code)
    if (dataKey && Object.prototype.hasOwnProperty.call(next, dataKey)) {
      const candidate = next[dataKey]
      if (candidate !== undefined) next[field.code] = candidate
      continue
    }

    // Fallback (covers legacy alias keys and customFields)
    const value = getFieldValue(field, next)
    if (value !== undefined) next[field.code] = value
  }
  return next
}

// Keep a snapshot of original data to check dirty state
const originalSnapshot = ref<string>('{}')
const isDirty = ref(false)

const getSubmitData = () => {
  if (isSchemaMode.value) return { ...(schemaFormData.value || {}) }
  return buildSubmitPayload(flattenLayoutFields(activeLayout.value), activeFormData.value || {})
}

const checkDirtyState = (currentData: Record<string, any>) => {
  // Simple JSON stringify comparison for deep objects. In a production app with Dates/Functions, 
  // a deepEqual from lodash would be safer, but this is sufficient for standard JSON forms.
  const currentSnapshot = JSON.stringify(currentData || {})
  const dirty = currentSnapshot !== originalSnapshot.value
  if (dirty !== isDirty.value) {
    isDirty.value = dirty
    emit('dirty-change', dirty)
  }
}

const handleModelUpdate = (value: Record<string, any>) => {
  let nextVal
  if (isSchemaMode.value) {
    nextVal = { ...schemaFormData.value, ...value }
    schemaFormData.value = nextVal
  } else {
    nextVal = ensureCanonicalKeys({ ...formData.value, ...value }, activeLayout.value)
    formData.value = nextVal
  }
  emit('update:modelValue', { ...activeFormData.value })
  checkDirtyState(nextVal)
}

const buildFieldsFromSchema = (schema: Record<string, any>): RuntimeField[] => {
  if (!schema) return []

  if (Array.isArray(schema.fields)) {
    return schema.fields.map((field: any) => {
      const code = field.code || field.fieldCode || field.name || field.prop
      const label = field.name || field.label || field.title || field.code || field.fieldCode || field.prop
      return {
        code,
        label,
        fieldType: normalizeFieldType(field.fieldType || field.type || field.field_type || 'text'),
        required: field.isRequired ?? field.required ?? false,
        readonly: field.isReadonly ?? field.readonly ?? false,
        hidden: field.isHidden ?? field.hidden ?? false,
        visible: field.isVisible ?? (field.hidden ? false : true),
        span: field.span,
        placeholder: field.placeholder,
        helpText: field.helpText,
        defaultValue: field.defaultValue,
        options: field.options || field.enum || [],
        referenceObject: field.referenceObject || field.relatedObject,
        componentProps: field.componentProps || field.component_props || {},
        metadata: { ...(field || {}) }
      }
    })
  }

  if (schema.properties && typeof schema.properties === 'object') {
    const required = new Set<string>(schema.required || [])
    return Object.entries(schema.properties).map(([key, prop]: [string, any]) => {
      let fieldType = 'text'

      if (prop.enum) {
        fieldType = 'select'
      } else if (prop.type === 'boolean') {
        fieldType = 'boolean'
      } else if (prop.type === 'number' || prop.type === 'integer') {
        fieldType = 'number'
      } else if (prop.type === 'array') {
        fieldType = prop.items?.enum ? 'multi_select' : 'text'
      } else if (prop.format === 'date') {
        fieldType = 'date'
      } else if (prop.format === 'date-time') {
        fieldType = 'datetime'
      } else if (prop.format === 'time') {
        fieldType = 'time'
      }

      const options = Array.isArray(prop.enum)
        ? prop.enum.map((value: any) => ({ label: String(value), value }))
        : []

      return {
        code: key,
        label: prop.title || key,
        fieldType: normalizeFieldType(fieldType),
        required: required.has(key),
        readonly: !!prop.readOnly,
        hidden: false,
        visible: true,
        options,
        componentProps: {},
        metadata: { ...(prop || {}) }
      }
    })
  }

  return []
}

const buildSectionsFromSchema = (schema: Record<string, any>, fields: RuntimeField[]) => {
  if (schema?.sections && Array.isArray(schema.sections)) {
    const fieldMap = new Map(fields.map((field) => [field.code, field]))
    const normalized = normalizeLayoutConfig(schema)
    return (normalized.sections || []).map((section: any, index: number) => ({
      id: section.id || section.name || `section-${index}`,
      name: section.name || `section-${index}`,
      title: section.title || '',
      fields: (section.fields || []).map((entry: any) => {
        if (typeof entry === 'string') {
          return fieldMap.get(entry) || { code: entry, label: entry, fieldType: 'text' }
        }
        const code = entry.code || entry.fieldCode || entry.field || entry.name
        if (code && fieldMap.has(code)) {
          const base = fieldMap.get(code)!
          const override = {
            label: entry.label || entry.name || base.label,
            fieldType: entry.fieldType ? normalizeFieldType(entry.fieldType) : undefined,
            span: entry.span,
            required: entry.required,
            readonly: entry.readonly,
            hidden: entry.hidden,
            visible: entry.visible,
            options: entry.options,
            referenceObject: entry.referenceObject || entry.relatedObject,
            componentProps: entry.componentProps || entry.component_props,
            placeholder: entry.placeholder,
            helpText: entry.helpText,
            defaultValue: entry.defaultValue
          }
          const merged = mergeRuntimeField(base, override)
          return {
            ...merged,
            metadata: { ...(merged.metadata || {}), ...(entry || {}) }
          }
        }
        return {
          code: code || entry.name || `field-${index}`,
          label: entry.label || entry.name || code || `field-${index}`,
          fieldType: normalizeFieldType(entry.fieldType || entry.type || 'text'),
          required: entry.required ?? false,
          readonly: entry.readonly ?? false,
          hidden: entry.hidden ?? false,
          visible: entry.visible ?? true,
          span: entry.span,
          placeholder: entry.placeholder,
          helpText: entry.helpText,
          defaultValue: entry.defaultValue,
          options: entry.options,
          referenceObject: entry.referenceObject || entry.relatedObject,
          componentProps: entry.componentProps || entry.component_props,
          metadata: { ...(entry || {}) }
        }
      }),
      columns: section.columns || section.columnCount || section.column || 2,
      visible: section.visible !== false,
      renderAsCard: section.renderAsCard || false,
      showTitle: section.showTitle !== false
    }))
  }

  if (fields.length === 0) return []

  return [{
    id: 'default',
    name: 'default',
    title: '',
    fields,
    columns: 2,
    visible: true,
    showTitle: false
  }]
}

const applyExternalModel = (value: Record<string, any> | null | undefined, isInitial = false) => {
  if (!value || typeof value !== 'object') return
  const target = isSchemaMode.value ? schemaFormData : formData
  const merged = { ...target.value, ...value }
  const finalVal = isSchemaMode.value ? merged : ensureCanonicalKeys(merged, activeLayout.value)
  target.value = finalVal
  
  if (isInitial) {
    originalSnapshot.value = JSON.stringify(finalVal)
    isDirty.value = false
    emit('dirty-change', false)
  } else {
    checkDirtyState(finalVal)
  }
}

watch(
  () => props.schema,
  (schema) => {
    if (!schema) {
      schemaLayout.value = { sections: [] }
      return
    }

    const fields = buildFieldsFromSchema(schema).filter((field) => !!field.code)
    const sections = buildSectionsFromSchema(schema, fields)
    schemaLayout.value = {
      sections
    }
  },
  { immediate: true, deep: true }
)

watch(
  () => props.modelValue,
  (value) => {
    // Only treat as initial if original doesn't exist yet
    const isInitial = originalSnapshot.value === '{}' || Boolean(props.instanceId && !loading.value && Object.keys(value || {}).length > 0)
    if (value) applyExternalModel(value, isInitial)
  },
  { immediate: true, deep: true }
)

watch(
  () => props.data,
  (value) => {
    const isInitial = originalSnapshot.value === '{}'
    if (value) applyExternalModel(value, isInitial)
  },
  { immediate: true, deep: true }
)

// Emit updates only on user-driven changes to avoid recursive update loops.


watch(
  () => [props.businessObject, props.layoutCode],
  async ([businessObject]) => {
    if (businessObject && !isSchemaMode.value) {
      await loadMetadata()
    }
  },
  { immediate: true }
)

watch(
  () => [props.readonly, activeLayout.value, activeFormData.value],
  async ([readonly, layout, model]) => {
    if (!readonly) return
    if (!layout || !model) return
    await prefetchReadonlyReferences(layout as RuntimeLayoutConfig, model as Record<string, any>)
  },
  { immediate: true, deep: true }
)

defineExpose({
  validate,
  resetFields,
  clearValidation,
  formData: activeFormData,
  getSubmitData,
  isDirty
})
</script>

<style scoped lang="scss">
.dynamic-form {
  width: 100%;

  &__form {
    width: 100%;
  }
}
</style>
