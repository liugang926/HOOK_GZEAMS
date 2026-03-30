<template>
  <div class="depreciation-list-page">
    <el-row
      :gutter="16"
      class="summary-grid"
    >
      <el-col
        :xs="24"
        :sm="12"
        :xl="6"
      >
        <el-card shadow="hover">
          <div class="summary-card">
            <span class="summary-card__label">{{ t('finance.depreciation.summary.assetCount') }}</span>
            <strong class="summary-card__value">{{ reportSummary.assetCount }}</strong>
          </div>
        </el-card>
      </el-col>
      <el-col
        :xs="24"
        :sm="12"
        :xl="6"
      >
        <el-card shadow="hover">
          <div class="summary-card">
            <span class="summary-card__label">{{ t('finance.depreciation.summary.originalValue') }}</span>
            <strong class="summary-card__value">{{ formatAmount(reportSummary.originalValue) }}</strong>
          </div>
        </el-card>
      </el-col>
      <el-col
        :xs="24"
        :sm="12"
        :xl="6"
      >
        <el-card shadow="hover">
          <div class="summary-card">
            <span class="summary-card__label">{{ t('finance.depreciation.summary.currentAmount') }}</span>
            <strong class="summary-card__value">{{ formatAmount(reportSummary.currentAmount) }}</strong>
          </div>
        </el-card>
      </el-col>
      <el-col
        :xs="24"
        :sm="12"
        :xl="6"
      >
        <el-card shadow="hover">
          <div class="summary-card">
            <span class="summary-card__label">{{ t('finance.depreciation.summary.netValue') }}</span>
            <strong class="summary-card__value">{{ formatAmount(reportSummary.netValue) }}</strong>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <el-card
      shadow="never"
      class="filter-card"
    >
      <el-form
        :model="filters"
        inline
      >
        <el-form-item :label="t('finance.depreciation.filters.assetKeyword')">
          <el-input
            v-model="filters.assetKeyword"
            :placeholder="t('finance.depreciation.placeholders.assetKeyword')"
            clearable
            style="width: 220px"
          />
        </el-form-item>

        <el-form-item :label="t('finance.depreciation.filters.period')">
          <el-date-picker
            v-model="filters.period"
            type="month"
            value-format="YYYY-MM"
            :placeholder="t('finance.depreciation.placeholders.period')"
            style="width: 180px"
          />
        </el-form-item>

        <el-form-item :label="t('finance.depreciation.filters.status')">
          <el-select
            v-model="filters.status"
            clearable
            :placeholder="t('finance.depreciation.placeholders.status')"
            style="width: 180px"
          >
            <el-option
              v-for="option in statusOptions"
              :key="option.value"
              :label="option.label"
              :value="option.value"
            />
          </el-select>
        </el-form-item>

        <el-form-item>
          <el-button
            type="primary"
            @click="handleSearch"
          >
            {{ t('common.actions.search') }}
          </el-button>
          <el-button @click="handleReset">
            {{ t('common.actions.reset') }}
          </el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <el-card shadow="never">
      <template #header>
        <div class="table-header">
          <div>
            <h3>{{ t('finance.depreciation.title') }}</h3>
            <p>{{ t('finance.depreciation.subtitle', { period: activePeriod }) }}</p>
          </div>
          <el-space wrap>
            <el-button
              type="primary"
              :icon="Refresh"
              @click="showGenerator = true"
            >
              {{ t('finance.actions.calculateDepreciation') }}
            </el-button>
            <el-button
              type="warning"
              :loading="posting"
              @click="handleBatchPost"
            >
              {{ t('finance.actions.batchPost') }}
            </el-button>
            <el-button
              :icon="Document"
              :loading="reportLoading"
              @click="openReportDrawer"
            >
              {{ t('finance.actions.previewReport') }}
            </el-button>
            <el-button
              :icon="Download"
              :loading="exporting"
              @click="handleExport"
            >
              {{ t('common.actions.export') }}
            </el-button>
          </el-space>
        </div>
      </template>

      <el-table
        v-loading="loading"
        :data="records"
        border
        stripe
        style="width: 100%"
        @selection-change="handleSelectionChange"
      >
        <el-table-column
          type="selection"
          width="48"
        />
        <el-table-column
          :label="t('finance.columns.assetCode')"
          min-width="140"
        >
          <template #default="{ row }">
            {{ getAssetCode(row) }}
          </template>
        </el-table-column>
        <el-table-column
          :label="t('finance.columns.assetName')"
          min-width="180"
        >
          <template #default="{ row }">
            {{ getAssetName(row) }}
          </template>
        </el-table-column>
        <el-table-column
          prop="period"
          :label="t('finance.columns.period')"
          width="120"
        />
        <el-table-column
          :label="t('finance.depreciation.columns.method')"
          width="160"
        >
          <template #default="{ row }">
            <el-tag
              size="small"
              effect="plain"
            >
              {{ getMethodLabel(row.depreciationMethod) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column
          :label="t('finance.depreciation.columns.purchasePrice')"
          min-width="150"
          align="right"
        >
          <template #default="{ row }">
            {{ formatAmount(row.purchasePrice) }}
          </template>
        </el-table-column>
        <el-table-column
          :label="t('finance.depreciation.columns.depreciationAmount')"
          min-width="150"
          align="right"
        >
          <template #default="{ row }">
            {{ formatAmount(row.depreciationAmount) }}
          </template>
        </el-table-column>
        <el-table-column
          :label="t('finance.columns.accumulatedDepreciation')"
          min-width="150"
          align="right"
        >
          <template #default="{ row }">
            {{ formatAmount(row.accumulatedDepreciation) }}
          </template>
        </el-table-column>
        <el-table-column
          :label="t('finance.columns.netValue')"
          min-width="150"
          align="right"
        >
          <template #default="{ row }">
            {{ formatAmount(row.netValue) }}
          </template>
        </el-table-column>
        <el-table-column
          :label="t('common.columns.status')"
          width="130"
        >
          <template #default="{ row }">
            <el-tag :type="getStatusTagType(row.status)">
              {{ getStatusLabel(row) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column
          :label="t('common.columns.actions')"
          width="180"
          fixed="right"
        >
          <template #default="{ row }">
            <el-button
              link
              type="primary"
              @click="handleViewDetail(row)"
            >
              {{ t('common.actions.view') }}
            </el-button>
            <el-button
              v-if="canPost(row)"
              link
              type="warning"
              @click="handlePostRecord(row)"
            >
              {{ t('finance.actions.post') }}
            </el-button>
          </template>
        </el-table-column>
      </el-table>

      <div class="table-footer">
        <el-pagination
          :current-page="pagination.page"
          :page-size="pagination.pageSize"
          :total="pagination.total"
          :page-sizes="[10, 20, 50, 100]"
          layout="total, sizes, prev, pager, next, jumper"
          @current-change="handlePageChange"
          @size-change="handlePageSizeChange"
        />
      </div>
    </el-card>

    <el-drawer
      v-model="reportDrawerVisible"
      :title="t('finance.depreciation.report.title', { period: activePeriod })"
      size="720px"
    >
      <div v-loading="reportLoading">
        <el-descriptions
          :column="2"
          border
          class="report-summary"
        >
          <el-descriptions-item :label="t('finance.depreciation.summary.assetCount')">
            {{ reportSummary.assetCount }}
          </el-descriptions-item>
          <el-descriptions-item :label="t('finance.depreciation.summary.originalValue')">
            {{ formatAmount(reportSummary.originalValue) }}
          </el-descriptions-item>
          <el-descriptions-item :label="t('finance.depreciation.summary.currentAmount')">
            {{ formatAmount(reportSummary.currentAmount) }}
          </el-descriptions-item>
          <el-descriptions-item :label="t('finance.depreciation.summary.accumulatedAmount')">
            {{ formatAmount(reportSummary.accumulatedAmount) }}
          </el-descriptions-item>
          <el-descriptions-item :label="t('finance.depreciation.summary.netValue')">
            {{ formatAmount(reportSummary.netValue) }}
          </el-descriptions-item>
        </el-descriptions>

        <el-divider>{{ t('finance.depreciation.report.byCategory') }}</el-divider>
        <el-table
          :data="reportData?.byCategory || []"
          border
          size="small"
        >
          <el-table-column
            prop="categoryName"
            :label="t('finance.depreciation.report.columns.category')"
            min-width="160"
          />
          <el-table-column
            prop="assetCount"
            :label="t('finance.depreciation.summary.assetCount')"
            width="100"
          />
          <el-table-column
            :label="t('finance.depreciation.summary.currentAmount')"
            min-width="140"
            align="right"
          >
            <template #default="{ row }">
              {{ formatAmount(row.currentDepreciation) }}
            </template>
          </el-table-column>
          <el-table-column
            :label="t('finance.depreciation.summary.accumulatedAmount')"
            min-width="140"
            align="right"
          >
            <template #default="{ row }">
              {{ formatAmount(row.accumulatedDepreciation) }}
            </template>
          </el-table-column>
          <el-table-column
            :label="t('finance.depreciation.summary.netValue')"
            min-width="140"
            align="right"
          >
            <template #default="{ row }">
              {{ formatAmount(row.netValue) }}
            </template>
          </el-table-column>
        </el-table>

        <el-divider>{{ t('finance.depreciation.report.byAsset') }}</el-divider>
        <el-table
          :data="reportData?.byAsset || []"
          border
          size="small"
        >
          <el-table-column
            prop="assetCode"
            :label="t('finance.columns.assetCode')"
            min-width="140"
          />
          <el-table-column
            prop="assetName"
            :label="t('finance.columns.assetName')"
            min-width="180"
          />
          <el-table-column
            prop="categoryName"
            :label="t('finance.depreciation.report.columns.category')"
            min-width="160"
          />
          <el-table-column
            :label="t('finance.depreciation.summary.currentAmount')"
            min-width="140"
            align="right"
          >
            <template #default="{ row }">
              {{ formatAmount(row.currentDepreciation) }}
            </template>
          </el-table-column>
          <el-table-column
            :label="t('finance.depreciation.summary.accumulatedAmount')"
            min-width="140"
            align="right"
          >
            <template #default="{ row }">
              {{ formatAmount(row.accumulatedDepreciation) }}
            </template>
          </el-table-column>
          <el-table-column
            :label="t('finance.depreciation.summary.netValue')"
            min-width="140"
            align="right"
          >
            <template #default="{ row }">
              {{ formatAmount(row.netValue) }}
            </template>
          </el-table-column>
        </el-table>
      </div>
    </el-drawer>

    <DepreciationGenerator
      v-model="showGenerator"
      @success="handleGeneratorSuccess"
    />
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { Document, Download, Refresh } from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox } from 'element-plus'

import { depreciationApi } from '@/api/depreciation'
import type {
  DepreciationMethod,
  DepreciationReport,
  DepreciationStatus,
} from '@/types/depreciation'
import DepreciationGenerator from './components/DepreciationGenerator.vue'

interface DepreciationTableRow {
  id: string
  asset?: {
    code?: string
    name?: string
  }
  assetCode?: string
  assetName?: string
  statusDisplay?: string
  depreciationMethod?: DepreciationMethod | string
  status?: DepreciationStatus | string
  period?: string
  purchasePrice?: number
  depreciationAmount?: number
  accumulatedDepreciation?: number
  netValue?: number
}

const { t } = useI18n()
const router = useRouter()

const currentMonth = new Date().toISOString().slice(0, 7)

const filters = reactive({
  assetKeyword: '',
  period: currentMonth,
  status: '',
})

const pagination = reactive({
  page: 1,
  pageSize: 20,
  total: 0,
})

const loading = ref(false)
const exporting = ref(false)
const posting = ref(false)
const reportLoading = ref(false)
const showGenerator = ref(false)
const reportDrawerVisible = ref(false)

const records = ref<DepreciationTableRow[]>([])
const selectedRows = ref<DepreciationTableRow[]>([])
const reportData = ref<DepreciationReport | null>(null)

const activePeriod = computed(() => filters.period || currentMonth)

const statusOptions = computed(() => ([
  { value: 'calculated', label: t('finance.status.calculated') },
  { value: 'posted', label: t('finance.status.posted') },
  { value: 'rejected', label: t('finance.status.rejected') },
]))

const reportSummary = computed(() => reportData.value?.summary || {
  assetCount: 0,
  originalValue: 0,
  currentAmount: 0,
  accumulatedAmount: 0,
  netValue: 0,
})

const formatAmount = (value?: number | null) => {
  return Number(value || 0).toLocaleString(undefined, {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  })
}

const getAssetCode = (row: DepreciationTableRow) => row.assetCode || row.asset?.code || '-'
const getAssetName = (row: DepreciationTableRow) => row.assetName || row.asset?.name || '-'

const getMethodLabel = (method?: string) => {
  const keyMap: Record<string, string> = {
    straight_line: 'finance.depreciation.methods.straightLine',
    double_declining: 'finance.depreciation.methods.doubleDeclining',
    sum_of_years: 'finance.depreciation.methods.sumOfYears',
    units_of_production: 'finance.depreciation.methods.unitsOfProduction',
  }

  if (!method) {
    return '-'
  }

  return t(keyMap[method] || method)
}

const getStatusTagType = (status?: string) => {
  const tagTypeMap: Record<string, string> = {
    calculated: 'warning',
    draft: 'info',
    submitted: 'warning',
    approved: 'success',
    posted: '',
    rejected: 'danger',
  }

  return tagTypeMap[status || ''] || 'info'
}

const getStatusLabel = (row: DepreciationTableRow) => {
  if (row.statusDisplay) {
    return row.statusDisplay
  }

  const statusMap: Record<string, string> = {
    calculated: t('finance.status.calculated'),
    draft: t('finance.status.draft'),
    submitted: t('finance.status.submitted'),
    approved: t('finance.status.approved'),
    posted: t('finance.status.posted'),
    rejected: t('finance.status.rejected'),
  }

  return statusMap[row.status || ''] || (row.status || '-')
}

const loadRecords = async () => {
  loading.value = true
  try {
    const response = await depreciationApi.listRecords({
      page: pagination.page,
      pageSize: pagination.pageSize,
      assetKeyword: filters.assetKeyword || undefined,
      period: filters.period || undefined,
      status: filters.status || undefined,
    })
    records.value = response.results as DepreciationTableRow[]
    pagination.total = response.count
  } finally {
    loading.value = false
  }
}

const loadReport = async (openDrawer = false) => {
  reportLoading.value = true
  try {
    reportData.value = await depreciationApi.getReport({
      period: activePeriod.value,
    })
    if (openDrawer) {
      reportDrawerVisible.value = true
    }
  } catch (error: any) {
    ElMessage.error(error?.message || t('finance.depreciation.messages.reportLoadFailed'))
  } finally {
    reportLoading.value = false
  }
}

const refreshPage = async () => {
  await Promise.all([
    loadRecords(),
    loadReport(),
  ])
}

const handleSearch = async () => {
  pagination.page = 1
  await refreshPage()
}

const handleReset = async () => {
  filters.assetKeyword = ''
  filters.period = currentMonth
  filters.status = ''
  pagination.page = 1
  await refreshPage()
}

const handlePageChange = async (page: number) => {
  pagination.page = page
  await loadRecords()
}

const handlePageSizeChange = async (pageSize: number) => {
  pagination.pageSize = pageSize
  pagination.page = 1
  await loadRecords()
}

const handleSelectionChange = (rows: DepreciationTableRow[]) => {
  selectedRows.value = rows
}

const canPost = (row: DepreciationTableRow) => ['calculated', 'approved'].includes(String(row.status || ''))

const handleViewDetail = (row: DepreciationTableRow) => {
  void router.push(`/objects/DepreciationRecord/${row.id}`)
}

const handlePostRecord = async (row: DepreciationTableRow) => {
  try {
    await ElMessageBox.confirm(
      t('finance.depreciation.messages.confirmPost'),
      t('common.actions.confirm'),
      { type: 'warning' }
    )
  } catch {
    return
  }

  posting.value = true
  try {
    await depreciationApi.postRecord(row.id)
    ElMessage.success(t('common.messages.operationSuccess'))
    await refreshPage()
  } catch (error: any) {
    ElMessage.error(error?.message || t('common.messages.operationFailed'))
  } finally {
    posting.value = false
  }
}

const handleBatchPost = async () => {
  const postableIds = selectedRows.value
    .filter(canPost)
    .map((row) => row.id)

  if (postableIds.length === 0) {
    ElMessage.warning(t('finance.depreciation.messages.noPostableSelected'))
    return
  }

  try {
    await ElMessageBox.confirm(
      t('finance.depreciation.messages.confirmBatchPost', { count: postableIds.length }),
      t('common.actions.confirm'),
      { type: 'warning' }
    )
  } catch {
    return
  }

  posting.value = true
  try {
    const result = await depreciationApi.batchPost(postableIds)
    if (result.failed > 0) {
      ElMessage.warning(
        t('finance.depreciation.messages.batchPostPartial', {
          success: result.success,
          failed: result.failed,
        })
      )
    } else {
      ElMessage.success(t('common.messages.operationSuccess'))
    }
    selectedRows.value = []
    await refreshPage()
  } catch (error: any) {
    ElMessage.error(error?.message || t('common.messages.operationFailed'))
  } finally {
    posting.value = false
  }
}

const openReportDrawer = async () => {
  await loadReport(true)
}

const handleExport = async () => {
  exporting.value = true
  try {
    const blob = await depreciationApi.exportReport({
      period: activePeriod.value,
      format: 'xlsx',
    })
    const url = window.URL.createObjectURL(blob)
    const anchor = document.createElement('a')
    anchor.href = url
    anchor.download = `depreciation-report-${activePeriod.value}.xlsx`
    anchor.click()
    window.URL.revokeObjectURL(url)
    ElMessage.success(t('common.messages.operationSuccess'))
  } catch (error: any) {
    ElMessage.error(error?.message || t('common.messages.operationFailed'))
  } finally {
    exporting.value = false
  }
}

const handleGeneratorSuccess = async () => {
  await refreshPage()
}

onMounted(async () => {
  await refreshPage()
})
</script>

<style scoped>
.depreciation-list-page {
  display: flex;
  flex-direction: column;
  gap: 16px;
  padding: 20px;
}

.summary-grid {
  margin: 0;
}

.summary-card {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.summary-card__label {
  color: #909399;
  font-size: 13px;
}

.summary-card__value {
  color: #303133;
  font-size: 24px;
  line-height: 1.2;
}

.table-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 16px;
  flex-wrap: wrap;
}

.table-header h3 {
  margin: 0 0 4px;
  font-size: 18px;
}

.table-header p {
  margin: 0;
  color: #909399;
}

.table-footer {
  display: flex;
  justify-content: flex-end;
  margin-top: 16px;
}

.report-summary {
  margin-bottom: 20px;
}

@media (max-width: 768px) {
  .depreciation-list-page {
    padding: 16px;
  }

  .table-header {
    flex-direction: column;
    align-items: stretch;
  }
}
</style>
