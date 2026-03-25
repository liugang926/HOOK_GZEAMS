<template>
  <div
    v-if="steps.length > 0"
    class="document-workflow-progress"
  >
    <el-steps
      :active="activeIndex"
      finish-status="success"
      align-center
    >
      <el-step
        v-for="step in steps"
        :key="step.key"
        :title="step.label"
      />
    </el-steps>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import type { ResolvedDocumentWorkflowProgressStep } from '@/platform/workflow/documentWorkflowProgress'

const props = defineProps<{
  currentStatus: string
  steps: ResolvedDocumentWorkflowProgressStep[]
}>()

const activeIndex = computed(() => {
  const index = props.steps.findIndex(step => step.key === props.currentStatus)
  return index >= 0 ? index : 0
})
</script>

<style scoped lang="scss">
.document-workflow-progress {
  width: 100%;
}
</style>
