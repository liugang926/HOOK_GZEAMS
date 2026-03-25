<template>
  <DocumentWorkflowProgressBlock
    :progress="progress"
    :title="resolvedTitle"
  />
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useI18n } from 'vue-i18n'
import DocumentWorkflowProgressBlock from '@/components/common/DocumentWorkflowProgressBlock.vue'
import {
  resolveDocumentWorkflowProgress,
  type DocumentWorkflowProgressStepDefinition,
} from '@/platform/workflow/documentWorkflowProgress'

const props = defineProps<{
  field: Record<string, any>
  modelValue: any
  formData?: Record<string, any>
}>()

const { t } = useI18n()

const componentProps = computed<Record<string, any>>(() => ({
  ...(props.field?.component_props || {}),
  ...(props.field?.componentProps || {}),
}))

const statusFieldCode = computed(() => {
  const candidate = String(
    componentProps.value.statusFieldCode ||
    componentProps.value.status_field_code ||
    'status'
  ).trim()
  return candidate || 'status'
})

const currentStatus = computed(() => {
  const source = props.formData || {}
  const direct = source?.[statusFieldCode.value]
  if (direct !== undefined && direct !== null && String(direct).trim()) {
    return String(direct).trim()
  }
  if (props.modelValue !== undefined && props.modelValue !== null && String(props.modelValue).trim()) {
    return String(props.modelValue).trim()
  }
  return ''
})

const workflowSteps = computed<DocumentWorkflowProgressStepDefinition[] | null>(() => {
  return Array.isArray(componentProps.value.steps)
    ? componentProps.value.steps as DocumentWorkflowProgressStepDefinition[]
    : null
})

const resolvedTitle = computed(() => {
  const candidate = String(props.field?.label || '').trim()
  if (candidate) return candidate
  return t('common.documentWorkbench.sections.workflowProgress')
})

const progress = computed(() => {
  return resolveDocumentWorkflowProgress({
    objectCode: String(props.field?.objectCode || componentProps.value.objectCode || '').trim(),
    currentStatus: currentStatus.value,
    steps: workflowSteps.value,
    t: t as (key: string) => string,
  })
})
</script>
