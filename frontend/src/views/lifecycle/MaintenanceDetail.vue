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
            {{ detail.maintenanceNo || $t('assets.lifecycle.maintenance.detailTitle') }}
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
      </div>

      <!-- Workflow Actions -->
      <StatusActionBar
        :status="detail.status"
        :actions="workflowActions"
        @action-success="handleRefresh"
      />

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
            :label="$t('assets.lifecycle.maintenance.form.completionDate')"
          >
            {{ detail.completionDate }}
          </el-descriptions-item>
        </el-descriptions>
      </el-card>

      <!-- Cost Breakdown (visible after completion) -->
      <el-card
        v-if="detail.laborCost || detail.materialCost || detail.otherCost || detail.totalCost"
        class="info-card mt-4"
      >
        <template #header>
          <span>{{ $t('assets.lifecycle.maintenance.form.costBreakdown') }}</span>
        </template>
        <el-descriptions :column="4" border>
          <el-descriptions-item :label="$t('assets.lifecycle.maintenance.form.laborCost')">
            ¥ {{ detail.laborCost || 0 }}
          </el-descriptions-item>
          <el-descriptions-item :label="$t('assets.lifecycle.maintenance.form.materialCost')">
            ¥ {{ detail.materialCost || 0 }}
          </el-descriptions-item>
          <el-descriptions-item :label="$t('assets.lifecycle.maintenance.form.otherCost')">
            ¥ {{ detail.otherCost || 0 }}
          </el-descriptions-item>
          <el-descriptions-item :label="$t('assets.lifecycle.maintenance.form.totalCost')">
            <span class="cost-total">¥ {{ detail.totalCost || 0 }}</span>
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
import { ElMessage } from 'element-plus'
import { useI18n } from 'vue-i18n'
import { maintenanceApi } from '@/api/lifecycle'
import StatusActionBar, { type StatusAction } from '@/components/common/StatusActionBar.vue'

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

const workflowActions = computed<StatusAction[]>(() => [
  {
    key: 'assign',
    label: t('assets.lifecycle.maintenance.actions.assign'),
    type: 'primary',
    apiCall: async () => { dialogType.value = 'assign'; dialogVisible.value = true },
    visibleWhen: (s: string) => s === 'pending' || s === 'reported',
  },
  {
    key: 'startWork',
    label: t('assets.lifecycle.maintenance.actions.startWork'),
    type: 'primary',
    confirmMessage: t('assets.lifecycle.maintenance.actions.startWork') + '?',
    apiCall: () => maintenanceApi.startWork(id),
    visibleWhen: (s: string) => s === 'assigned',
  },
  {
    key: 'complete',
    label: t('assets.lifecycle.maintenance.actions.completeWork'),
    type: 'success',
    apiCall: async () => { dialogType.value = 'complete'; dialogVisible.value = true },
    visibleWhen: (s: string) => s === 'in_progress' || s === 'processing',
  },
  {
    key: 'verify',
    label: t('assets.lifecycle.maintenance.actions.verify'),
    type: 'success',
    apiCall: async () => { dialogType.value = 'verify'; dialogVisible.value = true },
    visibleWhen: (s: string) => s === 'completed',
  },
  {
    key: 'cancel',
    label: t('assets.lifecycle.maintenance.actions.cancel'),
    type: 'default',
    confirmMessage: t('assets.lifecycle.maintenance.messages.cancelConfirm'),
    confirmType: 'warning',
    apiCall: () => maintenanceApi.cancel(id),
    visibleWhen: (s: string) => ['pending', 'reported', 'assigned', 'in_progress', 'processing'].includes(s),
  },
])

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
const getStepIndex = (status: string) => {
  const idx = statusSteps.indexOf(status)
  return idx >= 0 ? idx : (status === 'reported' ? 0 : (status === 'processing' ? 2 : 0))
}

const getStatusType = (s: string) => {
  const map: Record<string, string> = {
    pending: 'info', reported: 'info', assigned: 'warning', in_progress: 'primary',
    processing: 'primary', completed: 'warning', verified: 'success', cancelled: 'info'
  }
  return map[s] || 'info'
}
const getStatusLabel = (s: string) => t(`assets.lifecycle.maintenance.status.${s}`) || s

const getPriorityType = (p: string) => {
  const map: Record<string, string> = { low: 'info', normal: '', high: 'warning', urgent: 'danger' }
  return map[p] || ''
}
const getPriorityLabel = (p: string) => t(`assets.lifecycle.maintenance.priority.${p}`) || p

const handleRefresh = async () => {
  try { detail.value = await maintenanceApi.detail(id) } catch { /* ignore */ }
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
</script>

<style scoped lang="scss">
.detail-wrapper {
  .page-header {
    display: flex; align-items: center; justify-content: space-between; margin-bottom: 8px;
    .header-left { display: flex; align-items: center; gap: 12px; .page-title { margin: 0; font-size: 18px; } }
  }
  .mb-4 { margin-bottom: 16px; }
  .mt-4 { margin-top: 16px; }
  .ml-2 { margin-left: 8px; }
  .ml-1 { margin-left: 4px; }
  .cost-total { font-weight: 700; color: var(--el-color-danger); font-size: 15px; }
}
</style>
