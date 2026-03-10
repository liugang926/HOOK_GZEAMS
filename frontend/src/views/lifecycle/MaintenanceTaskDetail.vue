<template>
  <div class="page-container">
    <div v-if="loading">
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
            {{ detail.taskNo || $t('assets.lifecycle.maintenanceTask.detailTitle') }}
          </h2>
          <el-tag
            :type="getStatusType(detail.status)"
            class="ml-2"
          >
            {{ getStatusLabel(detail.status) }}
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
          <el-step :title="$t('assets.lifecycle.maintenanceTask.status.pending')" />
          <el-step :title="$t('assets.lifecycle.maintenanceTask.status.in_progress')" />
          <el-step :title="$t('assets.lifecycle.maintenanceTask.status.completed')" />
          <el-step :title="$t('assets.lifecycle.maintenanceTask.status.verified')" />
        </el-steps>
      </el-card>

      <!-- Basic Info -->
      <el-card class="info-card">
        <el-descriptions
          :column="3"
          border
        >
          <el-descriptions-item :label="$t('assets.lifecycle.maintenanceTask.columns.taskNo')">
            {{ detail.taskNo }}
          </el-descriptions-item>
          <el-descriptions-item :label="$t('assets.lifecycle.maintenanceTask.columns.asset')">
            {{ detail.assetDisplay || '—' }}
          </el-descriptions-item>
          <el-descriptions-item :label="$t('assets.lifecycle.maintenanceTask.columns.scheduledDate')">
            {{ detail.scheduledDate }}
          </el-descriptions-item>
          <el-descriptions-item
            :label="$t('assets.lifecycle.maintenanceTask.columns.maintenanceContent')"
            :span="3"
          >
            {{ detail.maintenanceContent }}
          </el-descriptions-item>
          <el-descriptions-item
            v-if="detail.executionResult"
            :label="$t('assets.lifecycle.maintenanceTask.form.executionResult')"
            :span="3"
          >
            {{ detail.executionResult }}
          </el-descriptions-item>
          <el-descriptions-item
            v-if="detail.verifyResult"
            :label="$t('assets.lifecycle.maintenanceTask.form.verifyResult')"
            :span="3"
          >
            {{ detail.verifyResult }}
          </el-descriptions-item>
        </el-descriptions>
      </el-card>
    </div>

    <!-- Execute Dialog -->
    <el-dialog
      v-model="executeDialog"
      :title="$t('assets.lifecycle.maintenanceTask.dialog.executeTitle')"
      width="480px"
      destroy-on-close
    >
      <el-form
        :model="executeForm"
        label-width="120px"
      >
        <el-form-item :label="$t('assets.lifecycle.maintenanceTask.form.executionResult')">
          <el-input
            v-model="executeForm.result"
            type="textarea"
            :rows="4"
            :placeholder="$t('assets.lifecycle.maintenanceTask.dialog.executionResultPlaceholder')"
          />
        </el-form-item>
        <el-form-item :label="$t('assets.lifecycle.maintenanceTask.form.actualHours')">
          <el-input-number
            v-model="executeForm.actualHours"
            :min="0"
            :precision="1"
            style="width:100%"
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="executeDialog = false">
          {{ $t('common.actions.cancel') }}
        </el-button>
        <el-button
          type="primary"
          @click="handleExecute"
        >
          {{ $t('common.actions.confirm') }}
        </el-button>
      </template>
    </el-dialog>

    <!-- Verify Dialog -->
    <el-dialog
      v-model="verifyDialog"
      :title="$t('assets.lifecycle.maintenanceTask.dialog.verifyTitle')"
      width="480px"
      destroy-on-close
    >
      <el-form
        :model="verifyForm"
        label-width="120px"
      >
        <el-form-item :label="$t('assets.lifecycle.maintenanceTask.form.verifyResult')">
          <el-input
            v-model="verifyForm.result"
            type="textarea"
            :rows="4"
            :placeholder="$t('assets.lifecycle.maintenanceTask.dialog.verifyResultPlaceholder')"
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="verifyDialog = false">
          {{ $t('common.actions.cancel') }}
        </el-button>
        <el-button
          type="primary"
          @click="handleVerify"
        >
          {{ $t('common.actions.confirm') }}
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, reactive } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ArrowLeft } from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { useI18n } from 'vue-i18n'
import { maintenanceTaskApi } from '@/api/lifecycle'
import StatusActionBar, { type StatusAction } from '@/components/common/StatusActionBar.vue'

const route = useRoute()
const router = useRouter()
const { t } = useI18n()
const id = route.params.id as string
const loading = ref(true)
const detail = ref<any>(null)
const executeDialog = ref(false)
const verifyDialog = ref(false)
const executeForm = reactive({ result: '', actualHours: 0 })
const verifyForm = reactive({ result: '' })

const workflowActions = computed<StatusAction[]>(() => [
  {
    key: 'execute',
    label: t('assets.lifecycle.maintenanceTask.actions.execute'),
    type: 'success',
    apiCall: async () => { executeDialog.value = true },
    visibleWhen: (s: string) => ['pending', 'in_progress'].includes(s),
  },
  {
    key: 'verify',
    label: t('assets.lifecycle.maintenanceTask.actions.verify'),
    type: 'primary',
    apiCall: async () => { verifyDialog.value = true },
    visibleWhen: (s: string) => s === 'completed',
  },
  {
    key: 'skip',
    label: t('assets.lifecycle.maintenanceTask.actions.skip'),
    type: 'default',
    apiCall: async () => {
      const { value: reason } = await ElMessageBox.prompt(
        t('assets.lifecycle.maintenanceTask.dialog.skipReasonPlaceholder'),
        t('assets.lifecycle.maintenanceTask.actions.skip'),
        { inputType: 'textarea', confirmButtonText: t('common.actions.confirm'), cancelButtonText: t('common.actions.cancel') }
      )
      await maintenanceTaskApi.skip(id, reason)
    },
    visibleWhen: (s: string) => s === 'pending',
  },
])

const statusSteps = ['pending', 'in_progress', 'completed', 'verified']
const getStepIndex = (s: string) => Math.max(0, statusSteps.indexOf(s))
const getStatusType = (s: string) => {
  const map: Record<string, string> = {
    pending: 'warning', in_progress: 'primary', completed: 'success', verified: '', skipped: 'info'
  }
  return map[s] || 'info'
}
const getStatusLabel = (s: string) => t(`assets.lifecycle.maintenanceTask.status.${s}`) || s

const handleRefresh = async () => {
  try { detail.value = await maintenanceTaskApi.detail(id) } catch { /* ignore */ }
}

const handleExecute = async () => {
  try {
    await maintenanceTaskApi.execute(id, { execution_result: executeForm.result, actual_hours: executeForm.actualHours })
    ElMessage.success(t('assets.lifecycle.maintenanceTask.messages.executeSuccess'))
    executeDialog.value = false
    detail.value = await maintenanceTaskApi.detail(id)
  } catch (e: any) { ElMessage.error(e?.message) }
}

const handleVerify = async () => {
  try {
    await maintenanceTaskApi.verify(id, verifyForm.result)
    ElMessage.success(t('assets.lifecycle.maintenanceTask.messages.verifySuccess'))
    verifyDialog.value = false
    detail.value = await maintenanceTaskApi.detail(id)
  } catch (e: any) { ElMessage.error(e?.message) }
}

onMounted(async () => {
  try { detail.value = await maintenanceTaskApi.detail(id) }
  catch { ElMessage.error(t('assets.lifecycle.maintenanceTask.messages.loadFailed')) }
  finally { loading.value = false }
})
</script>

<style scoped lang="scss">
.detail-wrapper {
  .page-header {
    display: flex; align-items: center; justify-content: space-between; margin-bottom: 8px;
    .header-left { display: flex; align-items: center; gap: 12px; .page-title { margin: 0; font-size: 18px; } }
  }
  .mb-4 { margin-bottom: 16px; }
  .ml-2 { margin-left: 8px; }
}
</style>
