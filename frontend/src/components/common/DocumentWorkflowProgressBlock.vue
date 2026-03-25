<template>
  <el-card
    v-if="progress"
    class="document-workflow-progress-block"
    shadow="never"
  >
    <p class="document-workflow-progress-block__eyebrow">
      {{ resolvedTitle }}
    </p>
    <DocumentWorkflowProgress
      :current-status="progress.currentStatus"
      :steps="progress.steps"
    />
  </el-card>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useI18n } from 'vue-i18n'
import DocumentWorkflowProgress from '@/components/common/DocumentWorkflowProgress.vue'
import type { ResolvedDocumentWorkflowProgress } from '@/platform/workflow/documentWorkflowProgress'

const props = defineProps<{
  progress: ResolvedDocumentWorkflowProgress | null
  title?: string
}>()

const { t } = useI18n()

const resolvedTitle = computed(() => {
  const candidate = String(props.title || '').trim()
  if (candidate) return candidate
  return t('common.documentWorkbench.sections.workflowProgress')
})
</script>

<style scoped lang="scss">
.document-workflow-progress-block {
  width: 100%;
  border: 1px solid var(--el-border-color-lighter);
}

.document-workflow-progress-block__eyebrow {
  margin: 0 0 12px;
  font-size: 12px;
  font-weight: 600;
  color: var(--el-text-color-secondary);
  text-transform: uppercase;
  letter-spacing: 0.08em;
}
</style>
