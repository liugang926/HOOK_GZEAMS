<template>
  <div class="page-container">
    <div
      v-if="loading"
      class="loading-container"
    >
      <el-skeleton
        :rows="8"
        animated
      />
    </div>
    <div
      v-else-if="detail"
      class="detail-wrapper"
    >
      <!-- Header -->
      <div class="page-header">
        <div class="header-left">
          <el-button
            :icon="ArrowLeft"
            @click="router.back()"
          >
            {{ $t('common.actions.back') }}
          </el-button>
          <h2 class="page-title">
            {{ $t('assets.lifecycle.maintenance.detailTitle') }}
          </h2>
          <el-tag
            :type="getStatusType(detail.status)"
            class="ml-2"
          >
            {{ getStatusLabel(detail.status) }}
          </el-tag>
          <el-tag
            :type="getPriorityType(detail.priority)"
            class="ml-1"
            size="small"
          >
            {{ getPriorityLabel(detail.priority) }}
          </el-tag>
        </div>
        <div class="header-actions">
          <el-button
            v-if="detail.status === 'pending'"
            type="primary"
            @click="dialogType = 'assign'; dialogVisible = true"
          >
            {{ $t('assets.lifecycle.maintenance.actions.assign') }}
          </el-button>
          <el-button
            v-if="detail.status === 'assigned'"
            type="primary"
            @click="handleStartWork"
          >
            {{ $t('assets.lifecycle.maintenance.actions.startWork') }}
          </el-button>
          <el-button
            v-if="detail.status === 'in_progress'"
            type="success"
            @click="dialogType = 'complete'; dialogVisible = true"
          >
            {{ $t('assets.lifecycle.maintenance.actions.completeWork') }}
          </el-button>
          <el-button
            v-if="detail.status === 'completed'"
            type="success"
            @click="dialogType = 'verify'; dialogVisible = true"
          >
            {{ $t('assets.lifecycle.maintenance.actions.verify') }}
          </el-button>
          <el-button
            v-if="['pending', 'assigned', 'in_progress'].includes(detail.status)"
            @click="handleCancel"
          >
            {{ $t('assets.lifecycle.maintenance.actions.cancel') }}
          </el-button>
        </div>
      </div>

      <!-- Status Steps -->
      <el-card class="steps-card mb-4">
        <el-steps
          :active="getStepIndex(detail.status)"
          finish-status="success"
        >
          <el-step :title="$t('assets.lifecycle.maintenance.status.pending')" />
          <el-step :title="$t('assets.lifecycle.maintenance.status.assigned')" />
          <el-step :title="$t('assets.lifecycle.maintenance.status.in_progress')" />
          <el-step :title="$t('assets.lifecycle.maintenance.status.completed')" />
          <el-step :title="$t('assets.lifecycle.maintenance.status.verified')" />
        </el-steps>
      </el-card>

      <!-- Basic Info -->
      <el-card class="info-card">
        <el-descriptions
          :column="3"
          border
        >
          <el-descriptions-item :label="$t('assets.lifecycle.maintenance.columns.maintenanceNo')">
            {{ detail.maintenanceNo }}
          </el-descriptions-item>
          <el-descriptions-item :label="$t('assets.lifecycle.maintenance.columns.assetDisplay')">
            {{ detail.assetDisplay || detail.assetCode || '—' }}
          </el-descriptions-item>
          <el-descriptions-item :label="$t('assets.lifecycle.maintenance.columns.technicianDisplay')">
            {{ detail.technicianDisplay || '—' }}
          </el-descriptions-item>
          <el-descriptions-item
            :label="$t('assets.lifecycle.maintenance.form.faultDescription')"
            :span="3"
          >
            {{ detail.faultDescription }}
          </el-descriptions-item>
          <el-descriptions-item
            :label="$t('assets.lifecycle.maintenance.form.remark')"
            :span="3"
          >
            {{ detail.remark || '—' }}
          </el-descriptions-item>
          <el-descriptions-item :label="$t('assets.lifecycle.maintenance.columns.createdAt')">
            {{ detail.createdAt }}
          </el-descriptions-item>
          <el-descriptions-item
            v-if="detail.completionDate"
            label="completionDate"
          >
            {{ detail.completionDate }}
          </el-descriptions-item>
        </el-descriptions>
      </el-card>
    </div>

    <!-- Action Dialogs -->
    <el-dialog
      v-model="dialogVisible"
      :title="dialogTitle"
      width="480px"
      destroy-on-close
    >
      <el-form
        :model="dialogForm"
        label-width="100px"
      >
        <!-- Assign technician -->
        <template v-if="dialogType === 'assign'">
          <el-form-item :label="$t('assets.lifecycle.maintenance.dialog.technicianLabel')">
            <el-input
              v-model="dialogForm.technicianId"
              :placeholder="$t('assets.lifecycle.maintenance.dialog.technicianPlaceholder')"
            />
          </el-form-item>
        </template>
        <!-- Complete work -->
        <template v-if="dialogType === 'complete'">
          <el-form-item :label="$t('assets.lifecycle.maintenance.dialog.resultLabel')">
            <el-input
              v-model="dialogForm.result"
              type="textarea"
              :rows="4"
              :placeholder="$t('assets.lifecycle.maintenance.dialog.resultPlaceholder')"
            />
          </el-form-item>
          <el-form-item :label="$t('assets.lifecycle.maintenance.dialog.costLabel')">
            <el-input-number
              v-model="dialogForm.cost"
              :min="0"
              :precision="2"
              style="width:100%"
            />
          </el-form-item>
        </template>
        <!-- Verify -->
        <template v-if="dialogType === 'verify'">
          <el-form-item :label="$t('assets.lifecycle.maintenance.dialog.resultLabel')">
            <el-input
              v-model="dialogForm.result"
              type="textarea"
              :rows="4"
              :placeholder="$t('assets.lifecycle.maintenance.dialog.verifyResultPlaceholder')"
            />
          </el-form-item>
        </template>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">
          {{ $t('common.actions.cancel') }}
        </el-button>
        <el-button
          type="primary"
          @click="handleDialogConfirm"
        >
          {{ $t('common.actions.confirm') }}
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ArrowLeft } from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { useI18n } from 'vue-i18n'
import { maintenanceApi } from '@/api/lifecycle'

const route = useRoute()
const router = useRouter()
const { t } = useI18n()
const id = route.params.id as string
const loading = ref(true)
const detail = ref<any>(null)

const dialogVisible = ref(false)
const dialogType = ref<'assign' | 'complete' | 'verify'>('assign')
const dialogForm = ref<any>({ technicianId: '', result: '', cost: 0 })

const dialogTitle = computed(() => {
  const map = {
    assign: t('assets.lifecycle.maintenance.dialog.assignTitle'),
    complete: t('assets.lifecycle.maintenance.dialog.completeTitle'),
    verify: t('assets.lifecycle.maintenance.dialog.verifyTitle')
  }
  return map[dialogType.value]
})

onMounted(async () => {
  try {
    detail.value = await maintenanceApi.detail(id)
  } catch {
    ElMessage.error(t('assets.lifecycle.maintenance.messages.loadFailed'))
  } finally {
    loading.value = false
  }
})

const statusSteps = ['pending', 'assigned', 'in_progress', 'completed', 'verified']
const getStepIndex = (status: string) => Math.max(0, statusSteps.indexOf(status))

const getStatusType = (s: string) => {
  const map: Record<string, string> = {
    pending: 'info', assigned: 'warning', in_progress: 'primary',
    completed: 'warning', verified: 'success', cancelled: 'info'
  }
  return map[s] || 'info'
}
const getStatusLabel = (s: string) => t(`assets.lifecycle.maintenance.status.${s}`) || s

const getPriorityType = (p: string) => {
  const map: Record<string, string> = { low: 'info', normal: '', high: 'warning', urgent: 'danger' }
  return map[p] || ''
}
const getPriorityLabel = (p: string) => t(`assets.lifecycle.maintenance.priority.${p}`) || p

const handleStartWork = async () => {
  try {
    await maintenanceApi.startWork(id)
    ElMessage.success(t('assets.lifecycle.maintenance.messages.startWorkSuccess'))
    detail.value = await maintenanceApi.detail(id)
  } catch (e: any) {
    ElMessage.error(e?.message || t('common.messages.operationFailed'))
  }
}

const handleDialogConfirm = async () => {
  try {
    if (dialogType.value === 'assign') {
      await maintenanceApi.assign(id, dialogForm.value.technicianId)
      ElMessage.success(t('assets.lifecycle.maintenance.messages.assignSuccess'))
    } else if (dialogType.value === 'complete') {
      await maintenanceApi.completeWork(id, { maintenance_cost: dialogForm.value.cost, completion_report: dialogForm.value.result })
      ElMessage.success(t('assets.lifecycle.maintenance.messages.completeWorkSuccess'))
    } else if (dialogType.value === 'verify') {
      await maintenanceApi.verify(id, dialogForm.value.result)
      ElMessage.success(t('assets.lifecycle.maintenance.messages.verifySuccess'))
    }
    dialogVisible.value = false
    dialogForm.value = { technicianId: '', result: '', cost: 0 }
    detail.value = await maintenanceApi.detail(id)
  } catch (e: any) {
    ElMessage.error(e?.message || t('common.messages.operationFailed'))
  }
}

const handleCancel = async () => {
  try {
    await ElMessageBox.confirm(t('assets.lifecycle.maintenance.messages.cancelConfirm'), t('common.messages.confirmTitle'), { type: 'warning' })
    await maintenanceApi.cancel(id)
    ElMessage.success(t('assets.lifecycle.maintenance.messages.cancelSuccess'))
    detail.value = await maintenanceApi.detail(id)
  } catch { /* cancelled */ }
}
</script>

<style scoped lang="scss">
.detail-wrapper {
  .page-header {
    display: flex; align-items: center; justify-content: space-between; margin-bottom: 16px;
    .header-left { display: flex; align-items: center; gap: 12px; .page-title { margin: 0; font-size: 18px; } }
    .header-actions { display: flex; gap: 8px; }
  }
  .mb-4 { margin-bottom: 16px; }
  .ml-2 { margin-left: 8px; }
  .ml-1 { margin-left: 4px; }
}
</style>
