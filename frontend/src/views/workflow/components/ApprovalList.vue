<template>
  <div class="approval-list">
    <el-table
      :data="tasks"
      :loading="loading"
      v-loading="loading"
      stripe
      border
      empty-text="暂无审批任务"
    >
      <el-table-column prop="instance.business_no" label="单号" width="160" />
      <el-table-column prop="node_name" label="当前节点" width="140" />
      <el-table-column label="业务类型" width="110">
        <template #default="{ row }">
          <el-tag :type="getBusinessTypeTag(row.instance?.business_object_code)" size="small">
            {{ getBusinessType(row.instance?.business_object_code) }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column label="发起人" width="110">
        <template #default="{ row }">
          {{ row.instance?.initiator?.username || '-' }}
        </template>
      </el-table-column>
      <el-table-column label="发起时间" width="170">
        <template #default="{ row }">
          {{ formatDate(row.created_at) }}
        </template>
      </el-table-column>
      <el-table-column label="优先级" width="90">
        <template #default="{ row }">
          <el-tag :type="getPriorityTagType(row.priority)" size="small">
            {{ getPriorityLabel(row.priority) }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column label="操作" width="200" fixed="right" v-if="!readOnly">
        <template #default="{ row }">
          <el-button
            type="primary"
            link
            @click="$emit('approve', row.id, '')"
            :loading="actionLoading === row.id"
          >
            同意
          </el-button>
          <el-button
            type="danger"
            link
            @click="$emit('reject', row.id)"
            :loading="actionLoading === row.id"
          >
            拒绝
          </el-button>
          <el-button
            link
            @click="$emit('return', row.id)"
            :loading="actionLoading === row.id"
          >
            退回
          </el-button>
        </template>
      </el-table-column>
      <el-table-column label="处理结果" width="100" v-if="readOnly">
        <template #default="{ row }">
          <el-tag :type="getStatusTagType(row.status)" size="small">
            {{ getStatusLabel(row.status) }}
          </el-tag>
        </template>
      </el-table-column>
    </el-table>

    <!-- Comment dialog for approve/reject/return -->
    <el-dialog
      v-model="dialogVisible"
      :title="dialogTitle"
      width="500px"
      @close="handleDialogClose"
    >
      <el-form :model="dialogForm" label-width="80px">
        <el-form-item label="审批意见">
          <el-input
            v-model="dialogForm.comment"
            type="textarea"
            :rows="4"
            placeholder="请输入审批意见（可选）"
            maxlength="500"
            show-word-limit
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleConfirm" :loading="confirmLoading">
          确定
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'

interface WorkflowTask {
  id: string
  node_name: string
  status: string
  priority: string
  created_at: string
  instance?: {
    business_no?: string
    business_object_code?: string
    initiator?: {
      username?: string
    }
  }
}

interface Props {
  tasks: WorkflowTask[]
  loading: boolean
  readOnly?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  readOnly: false
})

const emit = defineEmits(['approve', 'reject', 'return'])

// Dialog state
const dialogVisible = ref(false)
const dialogTitle = ref('')
const dialogAction = ref<'approve' | 'reject' | 'return'>('approve')
const dialogForm = ref({
  comment: ''
})
const confirmLoading = ref(false)
const actionLoading = ref<string | null>(null)

// Business type mapping
const getBusinessType = (code?: string): string => {
  const types: Record<string, string> = {
    'asset_pickup': '资产领用',
    'asset_transfer': '资产调拨',
    'asset_loan': '资产借用',
    'asset_return': '资产退库'
  }
  return types[code || ''] || code || '未知'
}

const getBusinessTypeTag = (code?: string): string => {
  const tags: Record<string, string> = {
    'asset_pickup': 'primary',
    'asset_transfer': 'success',
    'asset_loan': 'warning',
    'asset_return': 'info'
  }
  return tags[code || ''] || ''
}

// Priority mapping
const getPriorityLabel = (priority: string): string => {
  const labels: Record<string, string> = {
    'low': '低',
    'normal': '普通',
    'high': '高',
    'urgent': '紧急'
  }
  return labels[priority] || '普通'
}

const getPriorityTagType = (priority: string): string => {
  const types: Record<string, string> = {
    'low': 'info',
    'normal': '',
    'high': 'warning',
    'urgent': 'danger'
  }
  return types[priority] || ''
}

// Status mapping for completed tasks
const getStatusLabel = (status: string): string => {
  const labels: Record<string, string> = {
    'approved': '已同意',
    'rejected': '已拒绝',
    'returned': '已退回',
    'pending': '待处理'
  }
  return labels[status] || status
}

const getStatusTagType = (status: string): string => {
  const types: Record<string, string> = {
    'approved': 'success',
    'rejected': 'danger',
    'returned': 'warning',
    'pending': 'info'
  }
  return types[status] || ''
}

// Format date
const formatDate = (dateStr: string): string => {
  if (!dateStr) return '-'
  const date = new Date(dateStr)
  const year = date.getFullYear()
  const month = String(date.getMonth() + 1).padStart(2, '0')
  const day = String(date.getDate()).padStart(2, '0')
  const hours = String(date.getHours()).padStart(2, '0')
  const minutes = String(date.getMinutes()).padStart(2, '0')
  return `${year}-${month}-${day} ${hours}:${minutes}`
}

// Handle emit with dialog
const handleApproveWithDialog = (taskId: string, comment?: string) => {
  dialogAction.value = 'approve'
  dialogTitle.value = '同意审批'
  dialogForm.value.comment = comment || ''
  dialogVisible.value = true
}

const handleRejectWithDialog = (taskId: string) => {
  dialogAction.value = 'reject'
  dialogTitle.value = '拒绝审批'
  dialogForm.value.comment = ''
  dialogVisible.value = true
}

const handleReturnWithDialog = (taskId: string) => {
  dialogAction.value = 'return'
  dialogTitle.value = '退回审批'
  dialogForm.value.comment = ''
  dialogVisible.value = true
}

// Confirm dialog action
const handleConfirm = () => {
  confirmLoading.value = true
  const emitEvent = dialogAction.value
  const comment = dialogForm.value.comment

  // Close dialog first
  dialogVisible.value = false

  // Emit the action with comment
  if (emitEvent === 'approve') {
    emit('approve', '', comment)
  } else if (emitEvent === 'reject') {
    emit('reject', comment)
  } else if (emitEvent === 'return') {
    emit('return', comment)
  }

  confirmLoading.value = false
}

const handleDialogClose = () => {
  dialogForm.value.comment = ''
}

// Expose methods for parent to use
defineExpose({
  handleApproveWithDialog,
  handleRejectWithDialog,
  handleReturnWithDialog
})
</script>

<style scoped>
.approval-list {
  width: 100%;
}

.approval-list :deep(.el-table) {
  font-size: 14px;
}

.approval-list :deep(.el-table__cell) {
  padding: 8px 0;
}
</style>
