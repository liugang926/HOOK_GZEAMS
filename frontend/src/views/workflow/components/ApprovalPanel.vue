<template>
  <div class="approval-panel">
    <!-- Header -->
    <div class="panel-header">
      <div class="header-info">
        <h3 class="task-title">
          <el-icon class="title-icon">
            <Document />
          </el-icon>
          {{ task?.nodeName || task?.instance?.title || $t('workflow.task.processTask') }}
        </h3>
        <div class="header-meta">
          <span class="workflow-name">{{ workflowName }}</span>
          <el-tag
            v-if="task?.priority"
            :type="task.priority === 'high' ? 'danger' : task.priority === 'medium' ? 'warning' : 'info'"
            size="small"
            effect="dark"
          >
            {{ task.priority }}
          </el-tag>
          <span
            v-if="task?.createdAt"
            class="date-text"
          >{{ formatDate(task.createdAt) }}</span>
        </div>
      </div>
      <el-tag
        :type="statusType"
        size="default"
      >
        {{ statusText }}
      </el-tag>
    </div>

    <!-- Business Data Form -->
    <div
      v-loading="loading"
      class="panel-section"
    >
      <div class="section-title">
        <el-icon><EditPen /></el-icon>
        {{ $t('workflow.task.formInfo') }}
      </div>
      <div
        v-if="businessData && Object.keys(businessData).length"
        class="business-form"
      >
        <el-form
          :label-width="120"
          label-position="left"
        >
          <template
            v-for="(value, key) in businessData"
            :key="key"
          >
            <!-- Hidden fields are not rendered -->
            <el-form-item
              v-if="fieldPerms.isVisible(String(key))"
              :label="String(key)"
              :class="{
                'field-readonly': fieldPerms.isReadOnly(String(key)),
                'field-editable': fieldPerms.isEditable(String(key)),
              }"
            >
              <template v-if="fieldPerms.isEditable(String(key))">
                <el-input
                  v-model="editableData[String(key)]"
                  :placeholder="`${$t('common.actions.edit')} ${key}`"
                />
              </template>
              <template v-else>
                <span class="readonly-value">{{ value ?? '-' }}</span>
                <el-tag
                  v-if="fieldPerms.hasPermissions.value"
                  type="info"
                  size="small"
                  class="perm-badge"
                >
                  {{ $t('workflow.fields.readOnly') }}
                </el-tag>
              </template>
            </el-form-item>
          </template>
        </el-form>
      </div>
      <el-empty
        v-else-if="!loading"
        :description="$t('common.messages.noData')"
        :image-size="80"
      />
    </div>

    <!-- Approval Timeline -->
    <div
      v-if="task?.timeline?.length"
      class="panel-section"
    >
      <div class="section-title">
        <el-icon><Timer /></el-icon>
        {{ $t('workflow.task.approvalProcess') }}
      </div>
      <el-timeline class="timeline">
        <el-timeline-item
          v-for="(item, idx) in task.timeline"
          :key="idx"
          :type="getTimelineItemType(item.action)"
          :timestamp="formatDate(item.createdAt)"
          placement="top"
        >
          <div class="timeline-content">
            <strong>{{ item.nodeName }}</strong>
            <span class="timeline-operator">{{ item.operator || '-' }}</span>
            <el-tag
              :type="getTimelineItemType(item.action)"
              size="small"
            >
              {{ item.action }}
            </el-tag>
            <p
              v-if="item.comment"
              class="timeline-comment"
            >
              {{ item.comment }}
            </p>
          </div>
        </el-timeline-item>
      </el-timeline>
    </div>

    <!-- Action Bar -->
    <div
      v-if="isPending"
      class="panel-actions"
    >
      <el-form-item
        :label="$t('workflow.task.approvalComment')"
        class="comment-input"
      >
        <el-input
          v-model="comment"
          type="textarea"
          :rows="3"
          :placeholder="$t('workflow.myApprovals.enterRejectReason')"
        />
      </el-form-item>

      <div class="action-buttons">
        <el-button
          type="warning"
          :loading="actionLoading"
          :icon="RefreshLeft"
          @click="handleReturn"
        >
          {{ $t('workflow.actions.return') }}
        </el-button>
        <el-button
          type="danger"
          :loading="actionLoading"
          :icon="CircleClose"
          @click="handleReject"
        >
          {{ $t('workflow.actions.reject') }}
        </el-button>
        <el-button
          type="success"
          :loading="actionLoading"
          :icon="CircleCheck"
          @click="handleApprove"
        >
          {{ $t('workflow.actions.approve') }}
        </el-button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Document, EditPen, Timer, CircleCheck, CircleClose, RefreshLeft } from '@element-plus/icons-vue'
import { useFieldPermissions } from '@/composables/useFieldPermissions'
import type { NodeFormPermissions, TaskDetailWithPermissions } from '@/types/workflow'

const props = defineProps<{
  task: TaskDetailWithPermissions | null
  loading?: boolean
  actionLoading?: boolean
}>()

const emit = defineEmits<{
  approve: [taskId: string, comment: string, editedData?: Record<string, any>]
  reject: [taskId: string, comment: string]
  return: [taskId: string, comment: string]
}>()

const { t } = useI18n()
const comment = ref('')
const editableData = ref<Record<string, any>>({})

// Field permissions
const formPermissions = computed<NodeFormPermissions>(
  () => props.task?.formPermissions ?? {}
)
const fieldPerms = useFieldPermissions(formPermissions)

// Business data
const businessData = computed(() => props.task?.businessData ?? {})
const workflowName = computed(
  () => props.task?.instance?.definition?.name ?? props.task?.instance?.definitionCode ?? '-'
)

// Initialize editable data when business data changes
watch(businessData, (data) => {
  const editable: Record<string, any> = {}
  for (const [key, value] of Object.entries(data)) {
    if (fieldPerms.isEditable(key)) {
      editable[key] = value
    }
  }
  editableData.value = editable
}, { immediate: true })

// Status helpers
const isPending = computed(() => {
  const s = props.task?.status
  return s === 'pending' || s === 'in_progress'
})

const statusType = computed(() => {
  const map: Record<string, string> = {
    pending: 'warning',
    in_progress: 'warning',
    approved: 'success',
    completed: 'success',
    rejected: 'danger',
    cancelled: 'info',
  }
  return map[props.task?.status || ''] || 'info'
})

const statusText = computed(() => {
  const status = props.task?.status || 'unknown'
  return t(`workflow.status.${status}`)
})

// Date formatting
const formatDate = (date?: string) => {
  if (!date) return '-'
  return new Date(date).toLocaleString('zh-CN')
}

// Timeline helpers
const getTimelineItemType = (action: string) => {
  const map: Record<string, string> = {
    approve: 'success',
    approved: 'success',
    submit: 'primary',
    reject: 'danger',
    rejected: 'danger',
    return: 'warning',
    pending: 'warning',
  }
  return map[action] || 'info'
}

// Action handlers
const handleApprove = async () => {
  try {
    await ElMessageBox.confirm(
      t('workflow.task.confirmApprove'),
      t('common.actions.confirm'),
      { type: 'success' }
    )
    emit('approve', props.task!.id, comment.value, editableData.value)
    comment.value = ''
  } catch {
    // User cancelled
  }
}

const handleReject = async () => {
  if (!comment.value.trim()) {
    ElMessage.warning(t('workflow.myApprovals.reasonRequired'))
    return
  }
  try {
    await ElMessageBox.confirm(
      t('workflow.task.confirmReject'),
      t('common.actions.confirm'),
      { type: 'warning' }
    )
    emit('reject', props.task!.id, comment.value)
    comment.value = ''
  } catch {
    // User cancelled
  }
}

const handleReturn = async () => {
  if (!comment.value.trim()) {
    ElMessage.warning(t('workflow.myApprovals.returnReasonRequired'))
    return
  }
  try {
    await ElMessageBox.confirm(
      t('workflow.task.confirmReturn') || t('common.actions.confirm'),
      t('common.actions.confirm'),
      { type: 'warning' }
    )
    emit('return', props.task!.id, comment.value)
    comment.value = ''
  } catch {
    // User cancelled
  }
}
</script>

<style scoped>
.approval-panel {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.panel-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  padding: 16px 20px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border-radius: 8px;
  color: #fff;
}

.task-title {
  margin: 0 0 6px 0;
  font-size: 18px;
  font-weight: 600;
  display: flex;
  align-items: center;
  gap: 8px;
  color: #fff;
}

.title-icon {
  font-size: 20px;
}

.header-meta {
  display: flex;
  align-items: center;
  gap: 10px;
  font-size: 13px;
  opacity: 0.9;
}

.workflow-name {
  color: rgba(255, 255, 255, 0.85);
}

.date-text {
  color: rgba(255, 255, 255, 0.7);
}

.panel-section {
  background: #fff;
  border-radius: 8px;
  padding: 16px 20px;
  border: 1px solid #ebeef5;
}

.section-title {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 15px;
  font-weight: 600;
  color: #303133;
  margin-bottom: 16px;
  padding-bottom: 8px;
  border-bottom: 1px solid #f0f2f5;
}

.business-form :deep(.el-form-item) {
  margin-bottom: 12px;
}

.field-readonly :deep(.el-form-item__label) {
  color: #909399;
}

.field-editable :deep(.el-form-item__label) {
  color: #303133;
  font-weight: 500;
}

.readonly-value {
  color: #606266;
}

.perm-badge {
  margin-left: 8px;
}

.timeline {
  padding-left: 0;
}

.timeline-content {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
}

.timeline-operator {
  color: #909399;
  font-size: 13px;
}

.timeline-comment {
  width: 100%;
  margin: 4px 0 0;
  font-size: 13px;
  color: #606266;
  font-style: italic;
}

.panel-actions {
  background: #fff;
  border-radius: 8px;
  padding: 16px 20px;
  border: 1px solid #ebeef5;
}

.comment-input {
  margin-bottom: 16px;
}

.comment-input :deep(.el-form-item__label) {
  font-weight: 600;
}

.action-buttons {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
}

.action-buttons .el-button {
  min-width: 100px;
}
</style>
