<template>
  <div class="my-approvals">
    <div class="page-header">
      <h2>我的审批</h2>
      <div
        v-if="taskSummary"
        class="summary-cards"
      >
        <el-card class="summary-card pending">
          <div class="card-content">
            <div class="card-value">
              {{ taskSummary.pending_count || 0 }}
            </div>
            <div class="card-label">
              待审批
            </div>
          </div>
        </el-card>
        <el-card class="summary-card overdue">
          <div class="card-content">
            <div class="card-value">
              {{ taskSummary.overdue_count || 0 }}
            </div>
            <div class="card-label">
              已逾期
            </div>
          </div>
        </el-card>
        <el-card class="summary-card completed">
          <div class="card-content">
            <div class="card-value">
              {{ taskSummary.completed_today_count || 0 }}
            </div>
            <div class="card-label">
              今日已处理
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
            待审批
            <el-badge
              v-if="taskSummary?.pending_count"
              :value="taskSummary.pending_count"
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
            已逾期
            <el-badge
              v-if="taskSummary?.overdue_count"
              :value="taskSummary.overdue_count"
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
            今日已处理
            <el-badge
              v-if="taskSummary?.completed_today_count"
              :value="taskSummary.completed_today_count"
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
import { ref, onMounted, computed } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { workflowNodeApi } from '@/api/workflow'
import ApprovalList from './components/ApprovalList.vue'

interface TaskSummary {
  pending_count: number
  overdue_count: number
  completed_today_count: number
}

const activeTab = ref('pending')
const loading = ref(false)
const pendingTasks = ref([])
const overdueTasks = ref([])
const completedTasks = ref([])
const taskSummary = ref<TaskSummary | null>(null)

const pendingListRef = ref()
const overdueListRef = ref()

// Load tasks from API
const loadTasks = async () => {
  loading.value = true
  try {
    const data = await workflowNodeApi.getMyTasks() as any

    // Update tasks
    pendingTasks.value = data.pending || []
    overdueTasks.value = data.overdue || []
    completedTasks.value = data.completed_today || []
    taskSummary.value = data.summary || {
      pending_count: (data.pending || []).length,
      overdue_count: (data.overdue || []).length,
      completed_today_count: (data.completed_today || []).length
    }
  } catch (e: any) {
    console.error('Failed to load tasks:', e)
    ElMessage.error(e.message || '加载失败')
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
    await workflowNodeApi.approveNode(taskId, taskId, { comment })
    ElMessage.success('审批成功')
    await loadTasks()
  } catch (e: any) {
    console.error('Approve failed:', e)
    ElMessage.error(e.message || '审批失败')
  } finally {
    loading.value = false
  }
}

// Handle reject action
const handleReject = async (taskId: string, comment?: string) => {
  try {
    // Require comment for rejection
    if (!comment) {
      const result = await ElMessageBox.prompt('请输入拒绝原因', '拒绝审批', {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        inputPattern: /.+/,
        inputErrorMessage: '请输入拒绝原因'
      })
      comment = result.value
    }

    loading.value = true
    await workflowNodeApi.approveNode(taskId, taskId, { action: 'reject', comment })
    ElMessage.success('已拒绝')
    await loadTasks()
  } catch (e: any) {
    if (e !== 'cancel') {
      console.error('Reject failed:', e)
      ElMessage.error(e.message || '操作失败')
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
      const result = await ElMessageBox.prompt('请输入退回原因', '退回审批', {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        inputPattern: /.+/,
        inputErrorMessage: '请输入退回原因'
      })
      comment = result.value
    }

    loading.value = true
    // Use taskApi.returnTask or workflowNodeApi with return action
    const { taskApi } = await import('@/api/workflow')
    await taskApi.returnTask(taskId, { comment })
    ElMessage.success('已退回')
    await loadTasks()
  } catch (e: any) {
    if (e !== 'cancel') {
      console.error('Return failed:', e)
      ElMessage.error(e.message || '操作失败')
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

import { onUnmounted } from 'vue'
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
