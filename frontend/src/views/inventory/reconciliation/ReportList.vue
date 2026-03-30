<template>
  <div class="inventory-report-list-page">
    <BaseListPage
      ref="listRef"
      :title="t('inventory.report.pageTitle')"
      object-code="InventoryReport"
      :search-fields="searchFields"
      :table-columns="columns"
      :api="fetchReports"
      :batch-actions="batchActions"
      :selectable="true"
      @row-click="handleView"
    >
      <template #toolbar>
        <el-button
          type="primary"
          :icon="DocumentAdd"
          @click="openGenerateDialog"
        >
          {{ t('inventory.report.actions.generate') }}
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
          link
          type="success"
          @click.stop="handleExport(row, 'pdf')"
        >
          {{ t('inventory.report.actions.exportPdf') }}
        </el-button>
        <el-button
          link
          type="info"
          @click.stop="handleExport(row, 'excel')"
        >
          {{ t('inventory.report.actions.exportExcel') }}
        </el-button>
      </template>
    </BaseListPage>

    <el-dialog
      v-model="generateDialogVisible"
      :title="t('inventory.report.dialogs.generateTitle')"
      width="520px"
      destroy-on-close
    >
      <el-form
        ref="generateFormRef"
        :model="generateForm"
        :rules="generateRules"
        label-width="110px"
      >
        <el-form-item
          :label="t('inventory.report.fields.task')"
          prop="taskId"
        >
          <el-select
            v-model="generateForm.taskId"
            filterable
            clearable
            :placeholder="t('inventory.report.placeholders.taskSelect')"
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

        <el-form-item :label="t('inventory.report.fields.templateId')">
          <el-input
            v-model="generateForm.templateId"
            :placeholder="t('inventory.report.placeholders.templateId')"
          />
        </el-form-item>
      </el-form>

      <template #footer>
        <el-button @click="generateDialogVisible = false">
          {{ t('common.actions.cancel') }}
        </el-button>
        <el-button
          type="primary"
          :loading="generating"
          @click="confirmGenerate"
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
import { DocumentAdd } from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import type { FormInstance, FormRules } from 'element-plus'
import BaseListPage from '@/components/common/BaseListPage.vue'
import { inventoryApi } from '@/api/inventory'
import type {
  GenerateInventoryReportPayload,
  InventoryReport,
  InventoryTask,
} from '@/types/inventory'
import type { SearchField, SelectOption, TableColumn } from '@/types/common'
import { formatDate } from '@/utils/dateFormat'

interface ReportGenerateForm {
  taskId: string
  templateId: string
}

type ExportFormat = 'pdf' | 'excel'

const router = useRouter()
const { t } = useI18n()

const listRef = ref<InstanceType<typeof BaseListPage> | null>(null)
const generateFormRef = ref<FormInstance | null>(null)
const generateDialogVisible = ref(false)
const generating = ref(false)
const taskOptions = ref<SelectOption[]>([])

const generateForm = reactive<ReportGenerateForm>({
  taskId: '',
  templateId: ''
})

const generateRules: FormRules<ReportGenerateForm> = {
  taskId: [
    {
      required: true,
      message: t('inventory.report.validation.taskRequired'),
      trigger: 'change'
    }
  ]
}

const columns = computed<TableColumn[]>(() => [
  {
    prop: 'reportNo',
    label: t('inventory.report.columns.reportNo'),
    width: 180,
    fixed: 'left'
  },
  {
    prop: 'taskName',
    label: t('inventory.report.columns.taskName'),
    minWidth: 220,
    format: (_value: unknown, row: InventoryReport) => resolveTaskName(row)
  },
  {
    prop: 'differenceCount',
    label: t('inventory.report.columns.differenceCount'),
    width: 140,
    align: 'right',
    format: (_value: unknown, row: InventoryReport) => String(resolveDifferenceCount(row))
  },
  {
    prop: 'generatedBy',
    label: t('inventory.report.columns.generatedBy'),
    width: 140,
    format: (_value: unknown, row: InventoryReport) => resolveUserName(row.generatedBy)
  },
  {
    prop: 'generatedAt',
    label: t('inventory.report.columns.generatedAt'),
    width: 168,
    format: (value: string) => formatDate(value)
  },
  {
    prop: 'currentApproverName',
    label: t('inventory.report.columns.currentApprover'),
    width: 160,
    format: (_value: unknown, row: InventoryReport) => row.currentApproverName || resolveUserName(row.currentApprover)
  },
  {
    prop: 'status',
    label: t('inventory.report.columns.status'),
    width: 140,
    tagType: (row: InventoryReport) => getStatusType(String(row.status || '')),
    format: (_value: unknown, row: InventoryReport) => row.statusDisplay || getStatusLabel(String(row.status || '')),
    fixed: 'right'
  }
])

const searchFields = computed<SearchField[]>(() => [
  {
    prop: 'status',
    label: t('inventory.report.fields.status'),
    type: 'select',
    options: reportStatusOptions.value
  },
  {
    prop: 'taskId',
    label: t('inventory.report.fields.task'),
    type: 'select',
    options: taskOptions.value
  },
  {
    prop: 'dateRange',
    label: t('inventory.report.fields.dateRange'),
    type: 'dateRange'
  }
])

const reportStatusOptions = computed<SelectOption[]>(() => [
  { label: t('inventory.report.status.draft'), value: 'draft' },
  { label: t('inventory.report.status.pendingApproval'), value: 'pending_approval' },
  { label: t('inventory.report.status.approved'), value: 'approved' },
  { label: t('inventory.report.status.rejected'), value: 'rejected' }
])

const batchActions = computed(() => [
  {
    label: t('inventory.report.actions.batchExportPdf'),
    type: 'success' as const,
    action: (rows: InventoryReport[]) => handleBatchExport(rows, 'pdf')
  },
  {
    label: t('inventory.report.actions.batchExportExcel'),
    type: 'primary' as const,
    action: (rows: InventoryReport[]) => handleBatchExport(rows, 'excel')
  }
])

const canSubmit = (status: string) => {
  return status === 'draft' || status === 'rejected'
}

const fetchReports = async (params: Record<string, unknown>) => {
  const nextParams = { ...(params || {}) }

  if (Array.isArray(nextParams.dateRange)) {
    nextParams.dateFrom = nextParams.dateRange[0]
    nextParams.dateTo = nextParams.dateRange[1]
    delete nextParams.dateRange
  }

  return inventoryApi.getReports(nextParams)
}

const openGenerateDialog = () => {
  generateForm.taskId = ''
  generateForm.templateId = ''
  generateDialogVisible.value = true
}

const confirmGenerate = async () => {
  const form = generateFormRef.value
  if (!form) return

  const valid = await form.validate().catch(() => false)
  if (!valid) return

  try {
    generating.value = true
    const payload: GenerateInventoryReportPayload = {
      taskId: generateForm.taskId,
      templateId: generateForm.templateId.trim() || undefined
    }
    await inventoryApi.generateReport(payload)
    ElMessage.success(t('inventory.report.messages.generateSuccess'))
    generateDialogVisible.value = false
    listRef.value?.refresh()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error(t('inventory.report.messages.generateFailed'))
    }
  } finally {
    generating.value = false
  }
}

const handleView = (row: InventoryReport) => {
  router.push(`/objects/InventoryReport/${row.id}`)
}

const handleSubmit = async (row: InventoryReport) => {
  try {
    await ElMessageBox.confirm(
      t('inventory.report.messages.submitConfirm'),
      t('common.messages.confirmTitle'),
      {
        type: 'warning',
        confirmButtonText: t('common.actions.confirm'),
        cancelButtonText: t('common.actions.cancel')
      }
    )

    await inventoryApi.submitReport(row.id)
    ElMessage.success(t('inventory.report.messages.submitSuccess'))
    listRef.value?.refresh()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error(t('inventory.report.messages.submitFailed'))
    }
  }
}

const handleExport = async (row: InventoryReport, format: ExportFormat, notify = true) => {
  try {
    const blob = await inventoryApi.exportReport(row.id, format)
    const fileName = buildReportFileName(row, format)
    downloadBlob(blob, fileName)

    if (notify) {
      ElMessage.success(t('inventory.report.messages.exportSuccess', { fileName }))
    }
  } catch (error) {
    ElMessage.error(t('inventory.report.messages.exportFailed'))
    if (!notify) {
      throw error
    }
  }
}

const handleBatchExport = async (rows: InventoryReport[], format: ExportFormat) => {
  if (rows.length === 0) {
    ElMessage.warning(t('inventory.report.messages.batchExportEmpty'))
    return
  }

  for (const row of rows) {
    await handleExport(row, format, false)
  }

  ElMessage.success(
    t('inventory.report.messages.batchExportSuccess', {
      count: rows.length,
      format: format === 'pdf'
        ? t('inventory.report.actions.exportPdf')
        : t('inventory.report.actions.exportExcel')
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
    ElMessage.error(t('inventory.report.messages.loadTasksFailed'))
    taskOptions.value = []
  }
}

const resolveTaskName = (row: InventoryReport) => {
  if (row.task && typeof row.task === 'object') {
    return row.task.taskName || row.task.name || row.task.taskNo || '--'
  }
  return '--'
}

const resolveDifferenceCount = (row: InventoryReport) => {
  return Number(
    row.summary?.differenceCount
      ?? row.reportData?.summary?.differenceCount
      ?? 0
  )
}

const resolveUserName = (user: InventoryReport['generatedBy'] | InventoryReport['currentApprover']) => {
  if (user && typeof user === 'object') {
    return user.fullName || user.username || user.email || '--'
  }
  return typeof user === 'string' && user ? user : '--'
}

const getStatusType = (status: string) => {
  const map: Record<string, 'info' | 'warning' | 'success' | 'danger'> = {
    draft: 'info',
    pending_approval: 'warning',
    approved: 'success',
    rejected: 'danger'
  }
  return map[status] || 'info'
}

const getStatusLabel = (status: string) => {
  const map: Record<string, string> = {
    draft: t('inventory.report.status.draft'),
    pending_approval: t('inventory.report.status.pendingApproval'),
    approved: t('inventory.report.status.approved'),
    rejected: t('inventory.report.status.rejected')
  }
  return map[status] || status
}

const buildReportFileName = (row: InventoryReport, format: ExportFormat) => {
  const baseName = row.reportNo || (row.task && typeof row.task === 'object' ? row.task.taskNo : '') || row.id
  const extension = format === 'pdf' ? 'pdf' : 'xlsx'
  return `${baseName}.${extension}`
}

const downloadBlob = (blob: Blob, fileName: string) => {
  const url = window.URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  link.download = fileName
  document.body.appendChild(link)
  link.click()
  document.body.removeChild(link)
  window.URL.revokeObjectURL(url)
}

onMounted(() => {
  loadTaskOptions()
})
</script>

<style scoped lang="scss">
.inventory-report-list-page {
  display: flex;
  flex-direction: column;
  gap: 16px;
}
</style>
