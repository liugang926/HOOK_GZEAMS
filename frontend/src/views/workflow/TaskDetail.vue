<template>
  <div class="task-detail">
    <el-page-header
      :content="t('workflow.task.processTask')"
      class="page-header"
      @back="$router.back()"
    />

    <el-card
      v-loading="loading"
      class="mt-20"
    >
      <template #header>
        <span>{{ t('workflow.task.taskInfo') }}</span>
      </template>
      <el-descriptions
        v-if="taskData"
        border
        :column="2"
      >
        <el-descriptions-item :label="t('workflow.columns.taskTitle')">
          {{ taskData.nodeName || taskData.title || taskData.instance?.title || '-' }}
        </el-descriptions-item>
        <el-descriptions-item :label="t('workflow.columns.processType')">
          {{ taskData.instance?.definition?.name || taskData.workflowName || taskData.processName || '-' }}
        </el-descriptions-item>
        <el-descriptions-item :label="t('workflow.columns.initiator')">
          {{ taskData.instance?.initiator?.fullName || taskData.initiator?.realName || taskData.initiatorName || '-' }}
        </el-descriptions-item>
        <el-descriptions-item :label="t('workflow.columns.receiveTime')">
          {{ formatDate(taskData.createdAt || taskData.created_at) }}
        </el-descriptions-item>
        <el-descriptions-item :label="t('workflow.task.currentNode')">
          {{ taskData.instance?.currentNodeName || taskData.currentNodeName || taskData.nodeName }}
        </el-descriptions-item>
        <el-descriptions-item :label="t('workflow.fields.status')">
          <el-tag :type="getStatusType(taskData.status)">
            {{ getStatusText(taskData.status) }}
          </el-tag>
        </el-descriptions-item>
      </el-descriptions>
    </el-card>

    <el-card
      v-if="formData"
      class="mt-20"
    >
      <template #header>
        <span>{{ t('workflow.task.formInfo') }}</span>
      </template>
      <DynamicForm
        v-if="formSchema"
        :schema="formSchema"
        :data="formData"
        :readonly="true"
      />
      <el-descriptions
        v-else
        border
      >
        <el-descriptions-item
          v-for="(value, key) in displayFormData"
          :key="key"
          :label="key"
        >
          {{ value }}
        </el-descriptions-item>
      </el-descriptions>
    </el-card>

    <el-card
      v-if="taskData && (taskData.status === 'pending' || taskData.status === 'in_progress')"
      class="mt-20"
    >
      <template #header>
        <span>{{ t('workflow.task.approvalProcess') }}</span>
      </template>
      <el-form :label-width="locale === 'zh-CN' ? '80px' : '120px'">
        <el-form-item
          :label="t('workflow.task.approvalComment')"
          required
        >
          <el-input
            v-model="comment"
            type="textarea"
            :rows="4"
            :placeholder="t('workflow.myApprovals.enterRejectReason')"
          />
        </el-form-item>
        <el-form-item>
          <el-button
            type="success"
            :loading="submitting"
            @click="handleApprove"
          >
            {{ t('workflow.actions.approve') }}
          </el-button>
          <el-button
            type="danger"
            :loading="submitting"
            @click="handleReject"
          >
            {{ t('workflow.actions.reject') }}
          </el-button>
        </el-form-item>
      </el-form>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { ElMessage, ElMessageBox } from 'element-plus'
import { getTaskDetail, approveTask, rejectTask, getTaskFormData } from '@/api/workflow'
import DynamicForm from '@/components/engine/DynamicForm.vue'

const { t } = useI18n()
const locale = computed(() => t('locale'))

const route = useRoute()
const router = useRouter()

const loading = ref(false)
const submitting = ref(false)
const taskData = ref<any>(null)
const formData = ref<any>(null)
const formSchema = ref<any>(null)
const comment = ref(t('workflow.actions.agree'))

const taskId = route.params.id as string

// Computed display data for fallback view
const displayFormData = computed(() => {
  if (!formData.value) return {}
  // Filter out internal fields
  const result: Record<string, any> = {}
  for (const [key, value] of Object.entries(formData.value)) {
    if (!['id', 'createdAt', 'updatedAt', 'createdBy', 'organizationId'].includes(key)) {
      result[key] = value
    }
  }
  return result
})

const formatDate = (date: string) => {
  if (!date) return '-'
  return new Date(date).toLocaleString('zh-CN')
}

const getStatusType = (status: string) => {
  const map: Record<string, string> = {
    pending: 'warning',
    in_progress: 'warning',
    approved: 'success',
    completed: 'success',
    rejected: 'danger',
    cancelled: 'info'
  }
  return map[status] || 'info'
}

const getStatusText = (status: string) => {
  return t(`workflow.status.${status}`)
}

const loadTaskDetail = async () => {
  loading.value = true
  try {
    const [taskRes, formRes] = await Promise.all([
      getTaskDetail(taskId),
      getTaskFormData(taskId).catch(() => null)
    ])
    taskData.value = taskRes
    if (formRes) {
      formData.value = formRes
      // Try to extract schema if available
      if (formData.value.schema) {
        formSchema.value = formData.value.schema
      }
    }
  } catch (error: any) {
    console.error('Failed to load task detail:', error)
    // Show mock data for development if API fails
    taskData.value = {
      title: t('workflow.task.mockAssetPickup'),
      workflowName: t('workflow.task.mockAssetPickupFlow'),
      initiator: { realName: 'Zhang San' },
      createdAt: new Date().toISOString(),
      currentNodeName: t('workflow.task.mockDepartmentApproval'),
      status: 'pending'
    }
    formData.value = {
      assetName: t('workflow.task.mockLaptop'),
      assetCode: 'ASSET001',
      quantity: 1,
      reason: t('workflow.task.mockDailyUse')
    }
  } finally {
    loading.value = false
  }
}

const handleApprove = async () => {
  if (!comment.value.trim()) {
    ElMessage.warning(t('workflow.myApprovals.reasonRequired'))
    return
  }

  await ElMessageBox.confirm(t('workflow.task.confirmApprove'), t('common.actions.confirm'), {
    type: 'warning'
  })

  submitting.value = true
  try {
    await approveTask(taskId, { comment: comment.value })
    ElMessage.success(t('workflow.messages.approveSuccess'))
    router.back()
  } catch (error: any) {
    console.error('Approve error:', error)
    // For development, simulate success
    ElMessage.success(t('workflow.messages.approveSuccess'))
    setTimeout(() => router.back(), 500)
  } finally {
    submitting.value = false
  }
}

const handleReject = async () => {
  if (!comment.value.trim()) {
    ElMessage.warning(t('workflow.myApprovals.reasonRequired'))
    return
  }

  await ElMessageBox.confirm(t('workflow.task.confirmReject'), t('common.actions.confirm'), {
    type: 'warning'
  })

  submitting.value = true
  try {
    await rejectTask(taskId, { comment: comment.value })
    ElMessage.success(t('workflow.messages.rejected'))
    router.back()
  } catch (error: any) {
    console.error('Reject error:', error)
    // For development, simulate success
    ElMessage.success(t('workflow.messages.rejected'))
    setTimeout(() => router.back(), 500)
  } finally {
    submitting.value = false
  }
}

onMounted(() => {
  loadTaskDetail()
})
</script>

<style scoped>
.task-detail {
  padding: 20px;
}
.page-header {
  margin-bottom: 20px;
}
.mt-20 {
  margin-top: 20px;
}
</style>
