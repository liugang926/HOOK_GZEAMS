<template>
  <div class="approval-list">
    <el-table
      v-loading="loading"
      :data="tasks"
      :loading="loading"
      stripe
      border
      :empty-text="t('workflow.approvalList.noTasks')"
    >
      <el-table-column
        prop="instanceNo"
        :label="t('workflow.approvalList.businessNo')"
        width="160"
      />
      <el-table-column
        prop="nodeName"
        :label="t('workflow.columns.receiveTime')"
        width="140"
      />
      <el-table-column
        :label="t('workflow.approvalList.businessType')"
        width="110"
      >
        <template #default="{ row }">
          <el-tag
            :type="getBusinessTypeTag(row.businessObjectCode)"
            size="small"
          >
            {{ getBusinessType(row.businessObjectCode) }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column
        :label="t('workflow.columns.taskTitle')"
        min-width="180"
      >
        <template #default="{ row }">
          {{ row.instanceTitle || '-' }}
        </template>
      </el-table-column>
      <el-table-column
        :label="t('workflow.columns.receiveTime')"
        width="170"
      >
        <template #default="{ row }">
          {{ formatDate(row.createdAt) }}
        </template>
      </el-table-column>
      <el-table-column
        :label="t('workflow.approvalList.priority')"
        width="90"
      >
        <template #default="{ row }">
          <el-tag
            :type="getPriorityTagType(row.priority)"
            size="small"
          >
            {{ getPriorityLabel(row.priority) }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column
        v-if="!readOnly"
        :label="t('workflow.columns.operation')"
        width="200"
        fixed="right"
      >
        <template #default="{ row }">
          <el-button
            type="primary"
            link
            :loading="actionLoading === row.id"
            @click="$emit('approve', row.id, '')"
          >
            {{ t('workflow.actions.approve') }}
          </el-button>
          <el-button
            type="danger"
            link
            :loading="actionLoading === row.id"
            @click="$emit('reject', row.id)"
          >
            {{ t('workflow.actions.reject') }}
          </el-button>
          <el-button
            link
            :loading="actionLoading === row.id"
            @click="$emit('return', row.id)"
          >
            {{ t('workflow.actions.return') }}
          </el-button>
        </template>
      </el-table-column>
      <el-table-column
        v-if="readOnly"
        :label="t('workflow.approvalList.result')"
        width="100"
      >
        <template #default="{ row }">
          <el-tag
            :type="getStatusTagType(row.status)"
            size="small"
          >
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
      <el-form
        :model="dialogForm"
        :label-width="locale === 'zh-CN' ? '80px' : '120px'"
      >
        <el-form-item :label="t('workflow.task.approvalComment')">
          <el-input
            v-model="dialogForm.comment"
            type="textarea"
            :rows="4"
            :placeholder="t('workflow.approvalList.commentPlaceholder')"
            maxlength="500"
            show-word-limit
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">
          {{ t('common.actions.cancel') }}
        </el-button>
        <el-button
          type="primary"
          :loading="confirmLoading"
          @click="handleConfirm"
        >
          {{ t('common.actions.confirm') }}
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { useI18n } from 'vue-i18n'

const { t } = useI18n()

interface WorkflowTask {
  id: string
  instanceNo?: string
  instanceTitle?: string | null
  nodeName?: string
  status: string
  priority?: string
  createdAt?: string
  businessObjectCode?: string
}

interface Props {
  tasks: WorkflowTask[]
  loading: boolean
  readOnly?: boolean
}

withDefaults(defineProps<Props>(), {
  readOnly: false
})

const emit = defineEmits(['approve', 'reject', 'return'])

const locale = computed(() => t('locale'))

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
  return t(`workflow.businessTypes.${code || 'unknown'}`)
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
  return t(`workflow.priority.${priority}`)
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
  return t(`workflow.approvalStatus.${status}`)
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
const formatDate = (dateStr?: string): string => {
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
const handleApproveWithDialog = (_taskId: string, comment?: string) => {
  dialogAction.value = 'approve'
  dialogTitle.value = t('workflow.approvalList.approveApproval')
  dialogForm.value.comment = comment || ''
  dialogVisible.value = true
}

const handleRejectWithDialog = (_taskId: string) => {
  dialogAction.value = 'reject'
  dialogTitle.value = t('workflow.myApprovals.rejectApproval')
  dialogForm.value.comment = ''
  dialogVisible.value = true
}

const handleReturnWithDialog = (_taskId: string) => {
  dialogAction.value = 'return'
  dialogTitle.value = t('workflow.myApprovals.returnApproval')
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
