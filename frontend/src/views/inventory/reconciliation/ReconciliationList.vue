<template>
  <div class="reconciliation-list-page">
    <ReconciliationSummaryCard
      :records="summaryRecords"
      :loading="summaryLoading"
    />

    <BaseListPage
      ref="listRef"
      :title="t('inventory.reconciliation.pageTitle')"
      object-code="InventoryReconciliation"
      :search-fields="searchFields"
      :table-columns="columns"
      :api="fetchReconciliations"
      :batch-actions="batchActions"
      :selectable="true"
      @row-click="handleView"
    >
      <template #toolbar>
        <el-button
          type="primary"
          :icon="Plus"
          @click="openCreateDialog"
        >
          {{ t('inventory.reconciliation.actions.create') }}
        </el-button>
      </template>

      <template #actions="{ row }">
        <el-button
          link
          type="primary"
          @click.stop="handleView(row)"
        >
          {{ t('common.actions.detail') }}
        </el-button>
        <el-button
          v-if="canSubmit(row.status)"
          link
          type="warning"
          @click.stop="handleSubmit(row)"
        >
          {{ t('common.actions.submit') }}
        </el-button>
        <el-button
          v-if="row.status === 'submitted'"
          link
          type="success"
          @click.stop="handleApprove(row)"
        >
          {{ t('common.actions.approve') }}
        </el-button>
      </template>
    </BaseListPage>

    <el-dialog
      v-model="createDialogVisible"
      :title="t('inventory.reconciliation.dialogs.createTitle')"
      width="520px"
      destroy-on-close
    >
      <el-form
        ref="createFormRef"
        :model="createForm"
        :rules="createRules"
        label-width="100px"
      >
        <el-form-item
          :label="t('inventory.reconciliation.fields.task')"
          prop="taskId"
        >
          <el-select
            v-model="createForm.taskId"
            filterable
            clearable
            :placeholder="t('inventory.reconciliation.placeholders.taskSelect')"
            style="width: 100%"
          >
            <el-option
              v-for="option in taskOptions"
              :key="String(option.value)"
              :label="option.label"
              :value="option.value"
            />
          </el-select>
        </el-form-item>

        <el-form-item :label="t('common.labels.remark')">
          <el-input
            v-model="createForm.note"
            type="textarea"
            :rows="4"
            :placeholder="t('inventory.reconciliation.placeholders.note')"
          />
        </el-form-item>
      </el-form>

      <template #footer>
        <el-button @click="createDialogVisible = false">
          {{ t('common.actions.cancel') }}
        </el-button>
        <el-button
          type="primary"
          :loading="submittingCreate"
          @click="confirmCreate"
        >
          {{ t('common.actions.confirm') }}
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { Plus } from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import type { FormInstance, FormRules } from 'element-plus'
import BaseListPage from '@/components/common/BaseListPage.vue'
import ReconciliationSummaryCard from './components/ReconciliationSummaryCard.vue'
import { inventoryApi, reconciliationApi } from '@/api/inventory'
import type {
  InventoryReconciliation,
  InventoryTask,
} from '@/types/inventory'
import type { SearchField, SelectOption, TableColumn } from '@/types/common'
import { formatDate } from '@/utils/dateFormat'

interface ReconciliationCreateForm {
  taskId: string
  note: string
}

const router = useRouter()
const { t } = useI18n()

const listRef = ref<InstanceType<typeof BaseListPage> | null>(null)
const createFormRef = ref<FormInstance | null>(null)
const createDialogVisible = ref(false)
const submittingCreate = ref(false)
const taskOptions = ref<SelectOption[]>([])
const summaryLoading = ref(false)
const summaryRecords = ref<InventoryReconciliation[]>([])

const createForm = reactive<ReconciliationCreateForm>({
  taskId: '',
  note: ''
})

const createRules: FormRules<ReconciliationCreateForm> = {
  taskId: [
    {
      required: true,
      message: t('inventory.reconciliation.validation.taskRequired'),
      trigger: 'change'
    }
  ]
}

const columns = computed<TableColumn[]>(() => [
  {
    prop: 'reconciliationNo',
    label: t('inventory.reconciliation.columns.reconciliationNo'),
    width: 180,
    fixed: 'left'
  },
  {
    prop: 'taskName',
    label: t('inventory.reconciliation.columns.taskName'),
    minWidth: 220,
    format: (_value: unknown, row: InventoryReconciliation) => resolveTaskName(row)
  },
  {
    prop: 'normalCount',
    label: t('inventory.reconciliation.columns.normalCount'),
    width: 120,
    align: 'right'
  },
  {
    prop: 'abnormalCount',
    label: t('inventory.reconciliation.columns.abnormalCount'),
    width: 120,
    align: 'right',
    format: (_value: unknown, row: InventoryReconciliation) => {
      return String(Number(row.differenceCount ?? row.abnormalCount ?? 0))
    }
  },
  {
    prop: 'adjustmentCount',
    label: t('inventory.reconciliation.columns.adjustmentCount'),
    width: 130,
    align: 'right'
  },
  {
    prop: 'reconciledByName',
    label: t('inventory.reconciliation.columns.reconciledBy'),
    width: 140,
    format: (_value: unknown, row: InventoryReconciliation) => resolveUserName(row.reconciledBy, row.reconciledByName)
  },
  {
    prop: 'reconciledAt',
    label: t('inventory.reconciliation.columns.reconciledAt'),
    width: 168,
    format: (value: string) => formatDate(value)
  },
  {
    prop: 'status',
    label: t('inventory.reconciliation.columns.status'),
    width: 120,
    tagType: (row: InventoryReconciliation) => getStatusType(String(row.status || '')),
    format: (_value: unknown, row: InventoryReconciliation) => row.statusDisplay || getStatusLabel(String(row.status || '')),
    fixed: 'right'
  }
])

const searchFields = computed<SearchField[]>(() => [
  {
    prop: 'status',
    label: t('inventory.reconciliation.fields.status'),
    type: 'select',
    options: reconciliationStatusOptions.value
  },
  {
    prop: 'taskId',
    label: t('inventory.reconciliation.fields.task'),
    type: 'select',
    options: taskOptions.value
  },
  {
    prop: 'dateRange',
    label: t('inventory.reconciliation.fields.dateRange'),
    type: 'dateRange'
  }
])

const reconciliationStatusOptions = computed<SelectOption[]>(() => [
  { label: t('inventory.reconciliation.status.draft'), value: 'draft' },
  { label: t('inventory.reconciliation.status.submitted'), value: 'submitted' },
  { label: t('inventory.reconciliation.status.approved'), value: 'approved' },
  { label: t('inventory.reconciliation.status.rejected'), value: 'rejected' }
])

const batchActions = computed(() => [
  {
    label: t('inventory.reconciliation.actions.batchSubmit'),
    type: 'warning' as const,
    action: (rows: InventoryReconciliation[]) => handleBatchSubmit(rows),
    confirm: true,
    confirmMessage: t('inventory.reconciliation.messages.batchSubmitConfirm')
  },
  {
    label: t('inventory.reconciliation.actions.batchApprove'),
    type: 'success' as const,
    action: (rows: InventoryReconciliation[]) => handleBatchApprove(rows),
    confirm: true,
    confirmMessage: t('inventory.reconciliation.messages.batchApproveConfirm')
  }
])

const canSubmit = (status: string) => {
  return status === 'draft' || status === 'rejected'
}

const fetchReconciliations = async (params: Record<string, unknown>) => {
  const nextParams = { ...(params || {}) }

  if (Array.isArray(nextParams.dateRange)) {
    nextParams.dateFrom = nextParams.dateRange[0]
    nextParams.dateTo = nextParams.dateRange[1]
    delete nextParams.dateRange
  }

  summaryLoading.value = true
  try {
    const response = await inventoryApi.getReconciliations(nextParams)
    summaryRecords.value = Array.isArray(response.results) ? response.results : []
    return response
  } finally {
    summaryLoading.value = false
  }
}

const openCreateDialog = () => {
  createForm.taskId = ''
  createForm.note = ''
  createDialogVisible.value = true
}

const confirmCreate = async () => {
  const form = createFormRef.value
  if (!form) return

  const valid = await form.validate().catch(() => false)
  if (!valid) return

  try {
    submittingCreate.value = true
    await inventoryApi.createReconciliation({
      taskId: createForm.taskId,
      note: createForm.note.trim() || undefined
    })
    ElMessage.success(t('inventory.reconciliation.messages.createSuccess'))
    createDialogVisible.value = false
    listRef.value?.refresh()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error(t('inventory.reconciliation.messages.createFailed'))
    }
  } finally {
    submittingCreate.value = false
  }
}

const handleView = (row: InventoryReconciliation) => {
  router.push(`/objects/InventoryReconciliation/${row.id}`)
}

const handleSubmit = async (row: InventoryReconciliation) => {
  try {
    await ElMessageBox.confirm(
      t('inventory.reconciliation.messages.submitConfirm'),
      t('common.messages.confirmTitle'),
      {
        type: 'warning',
        confirmButtonText: t('common.actions.confirm'),
        cancelButtonText: t('common.actions.cancel')
      }
    )

    await reconciliationApi.submit(row.id)
    ElMessage.success(t('inventory.reconciliation.messages.submitSuccess'))
    listRef.value?.refresh()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error(t('inventory.reconciliation.messages.submitFailed'))
    }
  }
}

const handleApprove = async (row: InventoryReconciliation) => {
  try {
    await ElMessageBox.confirm(
      t('inventory.reconciliation.messages.approveConfirm'),
      t('common.messages.confirmTitle'),
      {
        type: 'warning',
        confirmButtonText: t('common.actions.confirm'),
        cancelButtonText: t('common.actions.cancel')
      }
    )

    await reconciliationApi.approve(row.id)
    ElMessage.success(t('inventory.reconciliation.messages.approveSuccess'))
    listRef.value?.refresh()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error(t('inventory.reconciliation.messages.approveFailed'))
    }
  }
}

const handleBatchSubmit = async (rows: InventoryReconciliation[]) => {
  const targets = rows.filter((row) => canSubmit(String(row.status || '')))
  if (targets.length === 0) {
    ElMessage.warning(t('inventory.reconciliation.messages.noEligibleRecords'))
    return
  }

  const settled = await Promise.allSettled(targets.map((row) => reconciliationApi.submit(row.id)))
  notifyBatchResult(settled, 'submit')
}

const handleBatchApprove = async (rows: InventoryReconciliation[]) => {
  const targets = rows.filter((row) => row.status === 'submitted')
  if (targets.length === 0) {
    ElMessage.warning(t('inventory.reconciliation.messages.noEligibleRecords'))
    return
  }

  const settled = await Promise.allSettled(targets.map((row) => reconciliationApi.approve(row.id)))
  notifyBatchResult(settled, 'approve')
}

const notifyBatchResult = (
  settled: PromiseSettledResult<void>[],
  action: 'submit' | 'approve'
) => {
  const failed = settled.filter((item) => item.status === 'rejected').length
  const succeeded = settled.length - failed

  if (failed === 0) {
    ElMessage.success(action === 'submit'
      ? t('inventory.reconciliation.messages.batchSubmitSuccess', { count: succeeded })
      : t('inventory.reconciliation.messages.batchApproveSuccess', { count: succeeded }))
    return
  }

  ElMessage.warning(
    t('inventory.reconciliation.messages.batchPartialSuccess', {
      succeeded,
      failed,
      total: settled.length
    })
  )
}

const loadTaskOptions = async () => {
  try {
    const response = await inventoryApi.listTasks({ pageSize: 100 })
    const rows = Array.isArray(response?.results) ? response.results as InventoryTask[] : []
    taskOptions.value = rows.map((task) => ({
      label: [task.taskNo, task.taskName || task.name].filter(Boolean).join(' / '),
      value: task.id
    }))
  } catch (error) {
    console.error('Failed to load inventory task options:', error)
    ElMessage.error(t('inventory.reconciliation.messages.loadTasksFailed'))
    taskOptions.value = []
  }
}

const resolveTaskName = (row: InventoryReconciliation) => {
  if (row.taskName) return row.taskName
  if (row.task && typeof row.task === 'object') {
    return row.task.taskName || row.task.name || row.task.taskNo || '--'
  }
  return row.taskNo || '--'
}

const resolveUserName = (user: InventoryReconciliation['reconciledBy'], fallback?: string) => {
  if (fallback) return fallback
  if (user && typeof user === 'object') {
    return user.fullName || user.username || user.email || '--'
  }
  return typeof user === 'string' && user ? user : '--'
}

const getStatusType = (status: string) => {
  const map: Record<string, 'info' | 'warning' | 'success' | 'danger'> = {
    draft: 'info',
    submitted: 'warning',
    approved: 'success',
    rejected: 'danger'
  }
  return map[status] || 'info'
}

const getStatusLabel = (status: string) => {
  const map: Record<string, string> = {
    draft: t('inventory.reconciliation.status.draft'),
    submitted: t('inventory.reconciliation.status.submitted'),
    approved: t('inventory.reconciliation.status.approved'),
    rejected: t('inventory.reconciliation.status.rejected')
  }
  return map[status] || status
}

onMounted(() => {
  loadTaskOptions()
})
</script>

<style scoped lang="scss">
.reconciliation-list-page {
  display: flex;
  flex-direction: column;
  gap: 16px;
}
</style>
