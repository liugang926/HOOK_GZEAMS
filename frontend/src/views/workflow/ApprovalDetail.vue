<template>
  <div class="approval-detail-page">
    <el-page-header
      :content="task?.nodeName || $t('workflow.task.processTask')"
      class="page-header"
      @back="$router.back()"
    />

    <div class="detail-content">
      <ApprovalPanel
        :task="task"
        :loading="store.loading"
        :action-loading="store.actionLoading"
        @approve="handleApprove"
        @reject="handleReject"
        @return="handleReturn"
      />
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, onUnmounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { ElMessage } from 'element-plus'
import { useWorkflowStore } from '@/stores/workflow'
import ApprovalPanel from './components/ApprovalPanel.vue'

const { t } = useI18n()
const route = useRoute()
const router = useRouter()
const store = useWorkflowStore()

const taskId = computed(() => route.params.taskId as string)
const task = computed(() => store.currentTask)

// Load task detail on mount
onMounted(async () => {
  if (taskId.value) {
    try {
      await store.fetchTaskDetail(taskId.value)
    } catch (e: any) {
      console.error('Failed to load task detail:', e)
      ElMessage.error(e.message || t('workflow.messages.loadFailed'))
    }
  }
})

// Clear current task on unmount
onUnmounted(() => {
  store.clearCurrentTask()
})

// Action handlers
const handleApprove = async (id: string, comment: string) => {
  try {
    await store.approveCurrentTask(id, comment)
    ElMessage.success(t('workflow.messages.approveSuccess'))
    router.back()
  } catch (e: any) {
    ElMessage.error(e.message || t('workflow.messages.approveFailed'))
  }
}

const handleReject = async (id: string, comment: string) => {
  try {
    await store.rejectCurrentTask(id, comment)
    ElMessage.success(t('workflow.messages.rejected'))
    router.back()
  } catch (e: any) {
    ElMessage.error(e.message || t('workflow.messages.rejectFailed'))
  }
}

const handleReturn = async (id: string, comment: string) => {
  try {
    await store.returnCurrentTask(id, comment)
    ElMessage.success(t('workflow.messages.returned'))
    router.back()
  } catch (e: any) {
    ElMessage.error(e.message || t('workflow.messages.rejectFailed'))
  }
}
</script>

<style scoped>
.approval-detail-page {
  padding: 20px;
  background-color: #f5f7fa;
  min-height: 100%;
}

.page-header {
  margin-bottom: 20px;
}

.detail-content {
  max-width: 900px;
  margin: 0 auto;
}
</style>
