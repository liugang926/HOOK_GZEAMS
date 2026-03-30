<template>
  <div class="my-approvals">
    <div class="page-header">
      <h2>{{ $t('workflow.myApprovals.title') }}</h2>
      <div
        v-if="taskSummary"
        class="summary-cards"
      >
        <el-card class="summary-card pending">
          <div class="card-content">
            <div class="card-value">
              {{ taskSummary.pendingCount || 0 }}
            </div>
            <div class="card-label">
              {{ $t('workflow.myApprovals.pending') }}
            </div>
          </div>
        </el-card>
        <el-card class="summary-card overdue">
          <div class="card-content">
            <div class="card-value">
              {{ taskSummary.overdueCount || 0 }}
            </div>
            <div class="card-label">
              {{ $t('workflow.myApprovals.overdue') }}
            </div>
          </div>
        </el-card>
        <el-card class="summary-card completed">
          <div class="card-content">
            <div class="card-value">
              {{ taskSummary.completedTodayCount || 0 }}
            </div>
            <div class="card-label">
              {{ $t('workflow.myApprovals.completedToday') }}
            </div>
          </div>
        </el-card>
      </div>
    </div>

    <el-tabs
      v-model="activeTab"
      class="approval-tabs"
      @tab-click="handleTabClick"
    >
      <el-tab-pane name="pending">
        <template #label>
          <span class="tab-label">
            {{ $t('workflow.myApprovals.pending') }}
            <el-badge
              v-if="taskSummary?.pendingCount"
              :value="taskSummary.pendingCount"
            />
          </span>
        </template>
        <ApprovalList
          ref="pendingListRef"
          :tasks="pendingTasks"
          :loading="loading"
          @approve="handleApprove"
          @reject="handleReject"
          @return="handleReturn"
        />
      </el-tab-pane>

      <el-tab-pane name="overdue">
        <template #label>
          <span class="tab-label">
            {{ $t('workflow.myApprovals.overdue') }}
            <el-badge
              v-if="taskSummary?.overdueCount"
              :value="taskSummary.overdueCount"
              type="danger"
            />
          </span>
        </template>
        <ApprovalList
          ref="overdueListRef"
          :tasks="overdueTasks"
          :loading="loading"
          @approve="handleApprove"
          @reject="handleReject"
          @return="handleReturn"
        />
      </el-tab-pane>

      <el-tab-pane name="completed">
        <template #label>
          <span class="tab-label">
            {{ $t('workflow.myApprovals.completedToday') }}
            <el-badge
              v-if="taskSummary?.completedTodayCount"
              :value="taskSummary.completedTodayCount"
              type="success"
            />
          </span>
        </template>
        <ApprovalList
          :tasks="completedTasks"
          :loading="loading"
          :read-only="true"
        />
      </el-tab-pane>
    </el-tabs>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue'
import { useI18n } from 'vue-i18n'
import { ElMessage, ElMessageBox } from 'element-plus'
import { workflowNodeApi } from '@/api/workflow'
import type { MyTasksResponse, WorkflowTaskListItem } from '@/types/workflow'
import ApprovalList from './components/ApprovalList.vue'

interface TaskSummary {
  pendingCount: number
  overdueCount: number
  completedTodayCount: number
  pending_count?: number
  overdue_count?: number
  completed_today_count?: number
}

const activeTab = ref('pending')
const loading = ref(false)
const pendingTasks = ref<WorkflowTaskListItem[]>([])
const overdueTasks = ref<WorkflowTaskListItem[]>([])
const completedTasks = ref<WorkflowTaskListItem[]>([])
const taskSummary = ref<TaskSummary | null>(null)
const { t } = useI18n()

const pendingListRef = ref()
const overdueListRef = ref()

const normalizeTaskSummary = (summary: Record<string, any> | undefined, fallback: TaskSummary): TaskSummary => {
  const pendingCount = Number(summary?.pendingCount ?? summary?.pending_count ?? fallback.pendingCount)
  const overdueCount = Number(summary?.overdueCount ?? summary?.overdue_count ?? fallback.overdueCount)
  const completedTodayCount = Number(
    summary?.completedTodayCount ??
      summary?.completed_today_count ??
      fallback.completedTodayCount
  )

  return {
    pendingCount,
    overdueCount,
    completedTodayCount,
    pending_count: pendingCount,
    overdue_count: overdueCount,
    completed_today_count: completedTodayCount
  }
}

// Load tasks from API
const loadTasks = async () => {
  loading.value = true
  try {
    const data = await workflowNodeApi.getMyTasks() as MyTasksResponse & Record<string, any>

    // Update tasks
    pendingTasks.value = data.pending || data.results || []
    overdueTasks.value = data.overdue || []
    completedTasks.value = data.completedToday || data.completed_today || []
    taskSummary.value = normalizeTaskSummary(data.summary, {
      pendingCount: pendingTasks.value.length,
      overdueCount: overdueTasks.value.length,
      completedTodayCount: completedTasks.value.length
    })
  } catch (e: any) {
    console.error('Failed to load tasks:', e)
    ElMessage.error(e.message || t('workflow.messages.loadFailed'))
  } finally {
    loading.value = false
  }
}

const handleTabClick = () => {
  // Data is already loaded, no need to reload
}

// Handle approve action
const handleApprove = async (taskId: string, comment: string) => {
  try {
    loading.value = true
    await workflowNodeApi.approveNode(taskId, taskId, { action: 'approve', comment })
    ElMessage.success(t('workflow.messages.approveSuccess'))
    await loadTasks()
  } catch (e: any) {
    console.error('Approve failed:', e)
    ElMessage.error(e.message || t('workflow.messages.approveFailed'))
  } finally {
    loading.value = false
  }
}

// Handle reject action
const handleReject = async (taskId: string, comment?: string) => {
  try {
    // Require comment for rejection
    if (!comment) {
      const result = await ElMessageBox.prompt(t('workflow.myApprovals.enterRejectReason'), t('workflow.myApprovals.rejectApproval'), {
        confirmButtonText: t('common.actions.confirm'),
        cancelButtonText: t('common.actions.cancel'),
        inputPattern: /.+/,
        inputErrorMessage: t('workflow.myApprovals.reasonRequired')
      })
      comment = result.value
    }

    loading.value = true
    await workflowNodeApi.approveNode(taskId, taskId, { action: 'reject', comment })
    ElMessage.success(t('workflow.messages.rejected'))
    await loadTasks()
  } catch (e: any) {
    if (e !== 'cancel') {
      console.error('Reject failed:', e)
      ElMessage.error(e.message || t('workflow.messages.rejectFailed'))
    }
  } finally {
    loading.value = false
  }
}

// Handle return action
const handleReturn = async (taskId: string, comment?: string) => {
  try {
    // Require comment for return
    if (!comment) {
      const result = await ElMessageBox.prompt(t('workflow.myApprovals.enterReturnReason'), t('workflow.myApprovals.returnApproval'), {
        confirmButtonText: t('common.actions.confirm'),
        cancelButtonText: t('common.actions.cancel'),
        inputPattern: /.+/,
        inputErrorMessage: t('workflow.myApprovals.returnReasonRequired')
      })
      comment = result.value
    }

    loading.value = true
    // Use taskApi.returnTask or workflowNodeApi with return action
    const { taskApi } = await import('@/api/workflow')
    await taskApi.returnTask(taskId, { comment })
    ElMessage.success(t('workflow.messages.returned'))
    await loadTasks()
  } catch (e: any) {
    if (e !== 'cancel') {
      console.error('Return failed:', e)
      ElMessage.error(e.message || t('workflow.messages.rejectFailed'))
    }
  } finally {
    loading.value = false
  }
}

// Auto-refresh on mount
onMounted(() => {
  loadTasks()
  // Set up auto-refresh every 30 seconds
  const interval = setInterval(() => {
    loadTasks()
  }, 30000)

  // Clean up interval on unmount
  onUnmounted(() => {
    clearInterval(interval)
  })
})
</script>

<style scoped>
.my-approvals {
  padding: 20px;
  background-color: #f5f7fa;
  min-height: 100%;
}

.page-header {
  margin-bottom: 20px;
}

.page-header h2 {
  margin: 0 0 16px 0;
  font-size: 20px;
  font-weight: 500;
  color: #303133;
}

.summary-cards {
  display: flex;
  gap: 16px;
}

.summary-card {
  flex: 1;
  border-radius: 8px;
}

.summary-card :deep(.el-card__body) {
  padding: 16px 20px;
}

.card-content {
  display: flex;
  align-items: center;
  gap: 12px;
}

.card-value {
  font-size: 28px;
  font-weight: 600;
  line-height: 1;
}

.card-label {
  font-size: 14px;
  color: #909399;
}

.summary-card.pending .card-value {
  color: #409eff;
}

.summary-card.overdue .card-value {
  color: #f56c6c;
}

.summary-card.completed .card-value {
  color: #67c23a;
}

.approval-tabs {
  background: white;
  border-radius: 8px;
  padding: 16px;
}

.tab-label {
  display: flex;
  align-items: center;
  gap: 8px;
}

.approval-tabs :deep(.el-tabs__header) {
  margin-bottom: 16px;
}

.approval-tabs :deep(.el-tabs__content) {
  overflow: visible;
}
</style>
