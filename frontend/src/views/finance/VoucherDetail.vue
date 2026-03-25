<template>
  <div class="voucher-detail-page">
    <BaseDetailPage
      :title="`${t('finance.voucherList')} - ${voucherData.voucherNo || ''}`"
      :sections="sections"
      :data="voucherData"
      :loading="loading"
      :audit-info="auditInfo"
      :relation-group-scope-id="relationGroupScopeId"
      :show-edit="false"
      :show-delete="false"
      :extra-actions="detailActions"
      @back="goBack"
    >
      <template #section-entries>
        <el-table
          :data="voucherEntries"
          border
          stripe
        >
          <el-table-column
            prop="lineNo"
            label="#"
            width="80"
          />
          <el-table-column
            prop="accountCode"
            label="Account Code"
            width="140"
          />
          <el-table-column
            prop="accountName"
            label="Account Name"
            width="180"
          />
          <el-table-column
            prop="debitAmount"
            label="Debit"
            width="130"
            align="right"
          >
            <template #default="{ row }">
              {{ formatMoney(Number(row.debitAmount || 0)) }}
            </template>
          </el-table-column>
          <el-table-column
            prop="creditAmount"
            label="Credit"
            width="130"
            align="right"
          >
            <template #default="{ row }">
              {{ formatMoney(Number(row.creditAmount || 0)) }}
            </template>
          </el-table-column>
          <el-table-column
            prop="description"
            label="Description"
            min-width="220"
          />
        </el-table>
      </template>

      <template #section-integration>
        <div class="integration-section-header">
          <SyncTaskStatusBadge
            v-if="currentTask.syncTaskId"
            :sync-task-id="currentTask.syncTaskId"
            :status="currentTask.status"
            :status-display="currentTask.statusDisplay"
          />
          <el-button
            size="small"
            @click="loadIntegrationLogs"
          >
            {{ t('common.actions.refresh') }}
          </el-button>
        </div>
        <el-table
          v-loading="logsLoading"
          :data="integrationLogs"
          border
          stripe
        >
          <el-table-column
            prop="createdAt"
            :label="t('common.columns.createdAt')"
            width="180"
          />
          <el-table-column
            prop="requestMethod"
            label="Method"
            width="100"
          />
          <el-table-column
            prop="statusCode"
            label="HTTP"
            width="90"
          />
          <el-table-column
            :label="t('common.columns.status')"
            width="100"
          >
            <template #default="{ row }">
              <el-tag :type="row.success ? 'success' : 'danger'">
                {{ row.success ? 'Success' : 'Failed' }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column
            prop="integrationType"
            label="Type"
            width="180"
          />
          <el-table-column
            prop="errorMessage"
            label="Error"
            min-width="220"
            show-overflow-tooltip
          />
          <el-table-column
            prop="durationSeconds"
            label="Duration(ms)"
            width="130"
          />
        </el-table>
      </template>
    </BaseDetailPage>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { ElMessage, ElMessageBox } from 'element-plus'
import BaseDetailPage from '@/components/common/BaseDetailPage.vue'
import SyncTaskStatusBadge from '@/components/finance/SyncTaskStatusBadge.vue'
import { financeApi, integrationApi } from '@/api/finance'
import { runAction } from '@/composables'
import { useSyncTaskPolling } from '@/composables/useSyncTaskPolling'
import { formatMoney } from '@/utils/numberFormat'
import { buildRecordRelationGroupScopeId } from '@/platform/reference/relationGroupScope'

const route = useRoute()
const router = useRouter()
const { t } = useI18n()
const actionNotifier = {
  success: (message: string) => ElMessage.success(message),
  warning: (message: string) => ElMessage.warning(message),
  error: (message: string) => ElMessage.error(message)
}

const loading = ref(false)
const logsLoading = ref(false)
const voucherData = ref<any>({})
const integrationLogs = ref<any[]>([])
const {
  getState: getTaskState,
  start: startTaskPolling,
  stopAll: stopAllTaskPolling,
} = useSyncTaskPolling({
  onError: (error: unknown) => {
    ElMessage.error((error as any)?.message || t('common.messages.operationFailed'))
  }
})

const voucherId = computed(() => String(route.params.id || ''))
const relationGroupScopeId = computed(() => {
  return buildRecordRelationGroupScopeId(voucherId.value, voucherData.value?.voucherNo)
})
const taskStateKey = computed(() => `voucher:${voucherId.value}`)
const currentTask = computed(() => (
  getTaskState(taskStateKey.value) || {
    syncTaskId: '',
    status: '',
    statusDisplay: '',
    done: false,
  }
))

const voucherEntries = computed(() => {
  const entries = voucherData.value?.entries
  return Array.isArray(entries) ? entries : []
})

const auditInfo = computed(() => ({
  createdBy: voucherData.value?.createdByName || voucherData.value?.createdBy?.username || '-',
  createdAt: voucherData.value?.createdAt,
  updatedBy: voucherData.value?.updatedByName || voucherData.value?.updatedBy?.username || '-',
  updatedAt: voucherData.value?.updatedAt,
}))

const statusTagType = {
  draft: 'info',
  submitted: 'warning',
  approved: 'primary',
  posted: 'success',
  rejected: 'danger'
} as const

const resolveSyncTaskId = (payload: any) => {
  if (!payload) return ''
  return String(payload?.syncTaskId || payload?.sync_task_id || '')
}

const sections = computed(() => [
  {
    name: 'basic',
    title: 'Basic Info',
    fields: [
      { prop: 'voucherNo', label: t('finance.columns.voucherNo'), span: 8 },
      { prop: 'businessType', label: t('finance.columns.businessType'), span: 8 },
      { prop: 'voucherDate', label: t('finance.columns.voucherDate'), type: 'date', span: 8 },
      {
        prop: 'totalAmount',
        label: t('finance.columns.totalAmount'),
        type: 'currency',
        span: 8,
        formatter: (value: any) => formatMoney(Number(value || 0))
      },
      {
        prop: 'status',
        label: t('finance.columns.status'),
        type: 'tag',
        span: 8,
        tagType: statusTagType as any,
      },
      { prop: 'summary', label: t('finance.columns.summary'), span: 24 },
      { prop: 'notes', label: 'Notes', span: 24 },
    ]
  },
  {
    name: 'posting',
    title: 'Posting Info',
    fields: [
      { prop: 'erpVoucherNo', label: 'ERP Voucher No', span: 8 },
      { prop: 'postedAt', label: 'Posted At', type: 'datetime', span: 8 },
      { prop: 'postedByName', label: 'Posted By', span: 8 },
      { prop: 'entryCount', label: 'Entry Count', span: 8 },
      {
        prop: 'isBalanced',
        label: 'Balanced',
        span: 8,
        formatter: (value: any) => (value ? 'Yes' : 'No')
      },
    ]
  },
  {
    name: 'entries',
    title: 'Voucher Entries',
    fields: []
  },
  {
    name: 'integration',
    title: 'Integration Logs',
    fields: []
  }
])

const detailActions = computed(() => {
  const actions: Array<{ label: string; type?: string; action: () => void | Promise<void> }> = []

  if (voucherData.value?.status === 'approved') {
    actions.push({
      label: t('finance.actions.post'),
      type: 'success',
      action: handlePost
    })
  }

  if (['approved', 'posted'].includes(voucherData.value?.status)) {
    actions.push({
      label: 'Retry Push',
      type: 'warning',
      action: handleRetry
    })
  }

  return actions
})

const fetchVoucher = async () => {
  if (!voucherId.value) return
  loading.value = true
  try {
    voucherData.value = await financeApi.getVoucher(voucherId.value)
  } catch (e: any) {
    ElMessage.error(e?.message || t('common.messages.loadFailed') || 'Load failed')
  } finally {
    loading.value = false
  }
}

const loadIntegrationLogs = async () => {
  if (!voucherId.value) return
  logsLoading.value = true
  try {
    const data = await integrationApi.getLogs(voucherId.value)
    if (Array.isArray(data)) {
      integrationLogs.value = data
    } else if (data && Array.isArray((data as any).results)) {
      integrationLogs.value = (data as any).results
    } else {
      integrationLogs.value = []
    }
  } catch (e: any) {
    integrationLogs.value = []
    ElMessage.error(e?.message || t('common.messages.operationFailed'))
  } finally {
    logsLoading.value = false
  }
}

const handlePost = async () => {
  try {
    await ElMessageBox.confirm(
      `${t('finance.actions.post')} ${voucherData.value?.voucherNo || ''}?`,
      t('common.messages.tips'),
      { type: 'warning' }
    )
  } catch {
    return
  }

  await runAction({
    notifier: actionNotifier,
    messages: {
      successFallback: t('common.messages.operationSuccess'),
      failureFallback: t('common.messages.operationFailed'),
      errorFallback: t('common.messages.operationFailed')
    },
    invoke: async () => {
      await financeApi.postVoucher(voucherId.value)
      return { success: true as const }
    },
    onSuccess: async () => {
      await fetchVoucher()
      await loadIntegrationLogs()
    }
  })
}

const handleRetry = async () => {
  try {
    await ElMessageBox.confirm(
      `Retry push ${voucherData.value?.voucherNo || ''}?`,
      t('common.messages.tips'),
      { type: 'warning' }
    )
  } catch {
    return
  }

  await runAction({
    notifier: actionNotifier,
    messages: {
      successFallback: t('common.messages.operationSuccess'),
      failureFallback: t('common.messages.operationFailed'),
      errorFallback: t('common.messages.operationFailed')
    },
    invoke: async () => {
      const result = await integrationApi.retry(voucherId.value)
      return {
        ...result,
        success: result?.success !== false
      }
    },
    onSuccess: async (result) => {
      const syncTaskId = resolveSyncTaskId(result)
      if (syncTaskId) {
        startTaskPolling(taskStateKey.value, syncTaskId, {
          onDone: async () => {
            await fetchVoucher()
            await loadIntegrationLogs()
          }
        })
      }
      await fetchVoucher()
      await loadIntegrationLogs()
    },
    onFailure: async () => {
      await fetchVoucher()
      await loadIntegrationLogs()
    }
  })
}

const goBack = () => {
  router.push('/finance/vouchers')
}

onMounted(async () => {
  await fetchVoucher()
  await loadIntegrationLogs()
})

onUnmounted(() => {
  stopAllTaskPolling()
})
</script>

<style scoped>
.voucher-detail-page {
  height: 100%;
}

.integration-section-header {
  margin-bottom: 12px;
  display: flex;
  justify-content: space-between;
  align-items: center;
}
</style>
