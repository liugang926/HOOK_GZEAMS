<template>
  <div class="voucher-list-page">
    <BaseListPage
      :title="t('finance.voucherList')"
      :search-fields="searchFields"
      :table-columns="columns"
      :api="fetchVouchers"
      :batch-actions="batchActions"
      :selectable="true"
    >
      <template #toolbar>
        <el-button
          type="primary"
          :icon="Plus"
          @click="handleCreate"
        >
          {{ t('finance.actions.createVoucher') }}
        </el-button>
        <el-button
          :icon="Upload"
          @click="handlePushBatch"
        >
          {{ t('finance.actions.batchPushToERP') }}
        </el-button>
      </template>

      <template #actions="{ row }">
        <el-button
          link
          type="primary"
          @click="handleView(row)"
        >
          {{ t('finance.actions.detail') }}
        </el-button>
        <el-button
          link
          type="info"
          @click="handleShowLogs(row)"
        >
          Integration Logs
        </el-button>
        <el-button
          v-if="row.status === 'approved'"
          link
          type="success"
          :loading="!!posting[row.id]"
          @click="handlePost(row)"
        >
          {{ t('finance.actions.post') }}
        </el-button>
        <el-button
          v-if="['approved', 'posted'].includes(row.status)"
          link
          type="warning"
          :loading="!!retrying[row.id]"
          @click="handleRetry(row)"
        >
          Retry Push
        </el-button>
        <SyncTaskStatusBadge
          v-if="getTaskState(row.id)"
          :sync-task-id="getTaskState(row.id)?.syncTaskId"
          :status="getTaskState(row.id)?.status"
          :status-display="getTaskState(row.id)?.statusDisplay"
          :show-task-id="false"
        />
        <el-button
          v-if="row.status === 'draft'"
          link
          type="danger"
          @click="handleDelete(row)"
        >
          {{ t('common.actions.delete') }}
        </el-button>
      </template>
    </BaseListPage>

    <el-dialog
      v-model="logsDialogVisible"
      :title="`${currentVoucherNo || '-'} Integration Logs`"
      width="980px"
    >
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
      <template #footer>
        <el-button @click="logsDialogVisible = false">
          {{ t('common.actions.close') || 'Close' }}
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { computed, onUnmounted, ref } from 'vue'
import { Plus, Upload } from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { useI18n } from 'vue-i18n'
import { useRouter } from 'vue-router'
import BaseListPage from '@/components/common/BaseListPage.vue'
import SyncTaskStatusBadge from '@/components/finance/SyncTaskStatusBadge.vue'
import { financeApi, integrationApi } from '@/api/finance'
import { runAction, runFlagAction, runRowAction } from '@/composables'
import { useSyncTaskPolling } from '@/composables/useSyncTaskPolling'
import { formatMoney } from '@/utils/numberFormat'
import type { SearchField, TableColumn } from '@/types/common'

const { t } = useI18n()
const router = useRouter()
const logsDialogVisible = ref(false)
const logsLoading = ref(false)
const currentVoucherId = ref('')
const currentVoucherNo = ref('')
const integrationLogs = ref<any[]>([])
const posting = ref<Record<string, boolean>>({})
const retrying = ref<Record<string, boolean>>({})
const batchPushing = ref(false)
const actionNotifier = {
  success: (message: string) => ElMessage.success(message),
  warning: (message: string) => ElMessage.warning(message),
  error: (message: string) => ElMessage.error(message)
}
const {
  stateByKey: _taskStateByVoucher,
  getState: getTaskState,
  start: startTaskPolling,
  stopAll: stopAllTaskPolling,
} = useSyncTaskPolling({
  onError: (error: unknown) => {
    ElMessage.error((error as any)?.message || t('common.messages.operationFailed'))
  }
})

const columns = computed<TableColumn[]>(() => [
  { prop: 'voucherNo', label: t('finance.columns.voucherNo'), width: 140, fixed: 'left' as const },
  { prop: 'businessType', label: t('finance.columns.businessType'), width: 120 },
  { prop: 'voucherDate', label: t('finance.columns.voucherDate'), width: 120 },
  { prop: 'summary', label: t('finance.columns.summary'), minWidth: 200 },
  { prop: 'amount', label: t('finance.columns.totalAmount'), width: 120, align: 'right', format: (_value: any, row: any) => {
      const raw = row?.totalAmount ?? row?.amount ?? row?.totalDebit ?? row?.totalCredit
      if (raw === null || raw === undefined) return '-'
      return formatMoney(Number(raw))
    }
  },
  { prop: 'status', label: t('finance.columns.status'), width: 100, tagType: (row: any) => getStatusType(row.status), format: (value: any, row: any) => row?.statusLabel || getStatusLabel(value), fixed: 'right' }
])

const searchFields = computed<SearchField[]>(() => [
  { prop: 'voucherNo', label: t('finance.columns.voucherNo'), type: 'input' as const },
  {
    prop: 'businessType',
    label: t('finance.columns.businessType'),
    type: 'select' as const,
    options: [
      { label: t('finance.businessType.purchase'), value: 'purchase' },
      { label: t('finance.businessType.depreciation'), value: 'depreciation' },
      { label: t('finance.businessType.disposal'), value: 'disposal' },
      { label: t('finance.businessType.inventory'), value: 'inventory' },
      { label: t('finance.businessType.other'), value: 'other' }
    ]
  },
  {
    prop: 'status',
    label: t('finance.columns.status'),
    type: 'select' as const,
    options: [
      { label: t('finance.status.draft'), value: 'draft' },
      { label: t('finance.status.submitted'), value: 'submitted' },
      { label: t('finance.status.approved'), value: 'approved' },
      { label: t('finance.status.posted'), value: 'posted' }
    ]
  },
  { prop: 'voucherDateRange', label: t('finance.columns.voucherDate'), type: 'dateRange' as const }
])

const batchActions = computed(() => [
  {
    label: t('finance.actions.batchPush'),
    type: 'primary' as const,
    action: (rows: any[]) => handleBatchPush(rows)
  }
])

const fetchVouchers = async (params: any) => {
  if (params.voucherDateRange) {
    params.voucherDateFrom = params.voucherDateRange[0]
    params.voucherDateTo = params.voucherDateRange[1]
    delete params.voucherDateRange
  }
  return await financeApi.listVouchers(params)
}

const getStatusType = (status: string) => {
  const map: Record<string, string> = {
    draft: 'info',
    submitted: 'warning',
    approved: 'primary',
    posted: 'success',
    rejected: 'danger'
  }
  return map[status] || 'info'
}

const getStatusLabel = (status: string) => {
  const map: Record<string, string> = {
    draft: t('finance.status.draft'),
    submitted: t('finance.status.submitted'),
    approved: t('finance.status.approved'),
    posted: t('finance.status.posted'),
    rejected: t('finance.status.rejected')
  }
  return map[status] || status
}

const resolveSyncTaskId = (payload: any) => {
  if (!payload) return ''
  return String(payload?.syncTaskId || payload?.sync_task_id || '')
}

const dispatchListRefresh = () => {
  window.dispatchEvent(new CustomEvent('refresh-base-list'))
}

const refreshLogsIfOpen = async (voucherId: string) => {
  if (logsDialogVisible.value && currentVoucherId.value === voucherId) {
    await loadIntegrationLogs(voucherId)
  }
}

const handleCreate = () => {
  ElMessage.info(t('common.messages.functionUnderDevelopment') || 'Feature under development')
}

const handleView = (row: any) => {
  router.push(`/finance/vouchers/${row.id}`)
}

const loadIntegrationLogs = async (voucherId: string) => {
  logsLoading.value = true
  try {
    const data = await integrationApi.getLogs(voucherId)
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

const handleShowLogs = async (row: any) => {
  currentVoucherId.value = row.id
  currentVoucherNo.value = row.voucherNo || row.voucher_no || ''
  logsDialogVisible.value = true
  await loadIntegrationLogs(row.id)
}

const handleDelete = async (row: any) => {
  try {
    await ElMessageBox.confirm(
      t('common.messages.confirmDelete', { name: row.voucherNo }),
      t('common.messages.tips'),
      { type: 'warning' }
    )
  } catch {
    return
  }

  await runAction({
    notifier: actionNotifier,
    messages: {
      successFallback: t('common.messages.deleteSuccess'),
      failureFallback: t('common.messages.operationFailed'),
      errorFallback: t('common.messages.operationFailed')
    },
    invoke: async () => {
      await financeApi.deleteVoucher(row.id)
      return { success: true as const }
    },
    onSuccess: () => {
      dispatchListRefresh()
    }
  })
}

const handlePost = async (row: any) => {
  try {
    await ElMessageBox.confirm(
      t('finance.actions.post') + ` ${row.voucherNo}?`,
      t('common.messages.tips'),
      { type: 'warning' }
    )
  } catch {
    return
  }

  await runRowAction({
    loadingMap: posting,
    rowId: String(row.id),
    notifier: actionNotifier,
    messages: {
      successFallback: t('common.messages.operationSuccess'),
      failureFallback: t('common.messages.operationFailed'),
      errorFallback: t('common.messages.operationFailed')
    },
    invoke: async () => {
      await financeApi.postVoucher(row.id)
      return { success: true as const }
    },
    onSuccess: () => {
      dispatchListRefresh()
    }
  })
}

const handleRetry = async (row: any) => {
  try {
    await ElMessageBox.confirm(
      `Retry push ${row.voucherNo}?`,
      t('common.messages.tips'),
      { type: 'warning' }
    )
  } catch {
    return
  }

  await runRowAction({
    loadingMap: retrying,
    rowId: String(row.id),
    notifier: actionNotifier,
    messages: {
      successFallback: t('common.messages.operationSuccess'),
      failureFallback: t('common.messages.operationFailed'),
      errorFallback: t('common.messages.operationFailed')
    },
    invoke: async () => {
      const result = await integrationApi.retry(row.id)
      return {
        ...result,
        success: result?.success !== false
      }
    },
    onSuccess: async (result) => {
      const syncTaskId = resolveSyncTaskId(result)
      if (syncTaskId) {
        startTaskPolling(String(row.id), syncTaskId, {
          onDone: async () => {
            dispatchListRefresh()
            await refreshLogsIfOpen(String(row.id))
          }
        })
      }
      dispatchListRefresh()
      await refreshLogsIfOpen(String(row.id))
    },
    onFailure: async () => {
      dispatchListRefresh()
      await refreshLogsIfOpen(String(row.id))
    }
  })
}

const handlePushBatch = () => {
  ElMessage.info(t('common.messages.pleaseSelectData'))
}

const handleBatchPush = async (rows: any[]) => {
  await runFlagAction({
    loadingFlag: batchPushing,
    notifier: actionNotifier,
    messages: {
      successFallback: t('common.messages.operationSuccess'),
      failureFallback: t('common.messages.operationFailed'),
      errorFallback: t('common.messages.operationFailed')
    },
    invoke: async () => {
      const ids = rows.map(r => r.id)
      const result = await financeApi.batchPushVouchers(ids)
      return {
        ...result,
        success: true as const
      }
    },
    onSuccess: async (result) => {
      const taskRows = Array.isArray(result?.results) ? result.results : []
      taskRows.forEach((item: any) => {
        if (!item?.success) return
        const syncTaskId = resolveSyncTaskId(item)
        if (syncTaskId && item?.id) {
          startTaskPolling(String(item.id), syncTaskId, {
            onDone: async () => {
              dispatchListRefresh()
              await refreshLogsIfOpen(String(item.id))
            }
          })
        }
      })
      dispatchListRefresh()
    }
  })
}

onUnmounted(() => {
  stopAllTaskPolling()
})
</script>

<style scoped>
</style>
