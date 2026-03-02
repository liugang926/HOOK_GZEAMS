# Phase 5.3: Depreciation Management - Frontend Implementation v2

## Document Information

| Project | Details |
|---------|---------|
| PRD Version | v2.0 (Updated for API Standardization) |
| Updated Date | 2026-01-22 |
| References | [frontend_api_standardization_design.md](../common_base_features/00_core/frontend_api_standardization_design.md) |

---

## Task Overview

Implement asset depreciation calculation, tracking, and reporting with support for multiple depreciation methods and automatic voucher generation.

---

## API Service Layer

### Type Definitions

```typescript
// frontend/src/types/depreciation.ts

export interface DepreciationRecord {
  id: string
  assetId: string
  asset?: Asset
  period: string
  periodIndex: number
  depreciationMethod: DepreciationMethod
  purchasePrice: number
  residualValue: number
  usefulLife: number
  usedMonths: number
  depreciationAmount: number
  accumulatedDepreciation: number
  netValue: number
  status: DepreciationStatus
  voucherId?: string
  voucherNo?: string
  organizationId: string
  createdAt: string
}

export enum DepreciationMethod {
  STRAIGHT_LINE = 'straight_line',
  DOUBLE_DECLINING = 'double_declining',
  SUM_OF_YEARS = 'sum_of_years'
}

export enum DepreciationStatus {
  DRAFT = 'draft',
  SUBMITTED = 'submitted',
  APPROVED = 'approved',
  POSTED = 'posted'
}

export interface Asset {
  id: string
  code: string
  name: string
  categoryId?: string
  category?: AssetCategory
  purchasePrice: number
  purchaseDate: string
  residualRate: number
  usefulLife: number
  depreciationMethod: DepreciationMethod
}

export interface AssetCategory {
  id: string
  code: string
  name: string
  defaultDepreciationMethod?: DepreciationMethod
  defaultUsefulLife?: number
  defaultResidualRate?: number
}

export interface DepreciationCalculation {
  assetId: string
  period: string
  method: DepreciationMethod
  purchasePrice: number
  residualValue: number
  usefulLife: number
  usedMonths: number
  monthlyDepreciation: number
  currentPeriodDepreciation: number
  accumulatedDepreciation: number
  netValue: number
}

export interface DepreciationSummary {
  assetCount: number
  originalValue: number
  currentAmount: number
  accumulatedAmount: number
  netValue: number
}

export interface DepreciationReport {
  period: string
  summary: DepreciationSummary
  byCategory: CategoryDepreciation[]
  byAsset: AssetDepreciation[]
}

export interface CategoryDepreciation {
  categoryId: string
  categoryName: string
  assetCount: number
  originalValue: number
  currentDepreciation: number
  accumulatedDepreciation: number
  netValue: number
  depreciationRate: number
}

export interface AssetDepreciation {
  assetId: string
  assetCode: string
  assetName: string
  categoryName: string
  purchasePrice: number
  currentDepreciation: number
  accumulatedDepreciation: number
  netValue: number
  depreciationRate: number
}

export interface DepreciationConfig {
  categoryId?: string
  depreciationMethod: DepreciationMethod
  usefulLife: number
  residualRate: number
}
```

### API Service

```typescript
// frontend/src/api/depreciation.ts

import request from '@/utils/request'
import type { PaginatedResponse } from '@/types/api'
import type {
  DepreciationRecord,
  DepreciationCalculation,
  DepreciationReport,
  DepreciationConfig
} from '@/types/depreciation'

export const depreciationApi = {
  // Depreciation Records
  listRecords(params?: {
    assetId?: string
    period?: string
    status?: DepreciationStatus
    page?: number
    pageSize?: number
  }): Promise<PaginatedResponse<DepreciationRecord>> {
    return request.get('/depreciation/records/', { params })
  },

  getRecord(id: string): Promise<DepreciationRecord> {
    return request.get(`/depreciation/records/${id}/`)
  },

  // Calculate
  calculate(params?: {
    period?: string
    assetIds?: string[]
    categoryIds?: string[]
  }): Promise<{ taskId: string }> {
    return request.post('/depreciation/calculate/', params)
  },

  getCalculationStatus(taskId: string): Promise<{
    status: 'pending' | 'processing' | 'completed' | 'failed'
    progress: number
    total: number
    processed: number
  }> {
    return request.get(`/depreciation/calculate/${taskId}/status/`)
  },

  // Posting
  post(id: string): Promise<void> {
    return request.post(`/depreciation/records/${id}/post/`)
  },

  batchPost(ids: string[]): Promise<void> {
    return request.post('/depreciation/records/batch-post/', { ids })
  },

  // Reports
  getReport(params: {
    period: string
    categoryIds?: string[]
  }): Promise<DepreciationReport> {
    return request.get('/depreciation/report/', { params })
  },

  exportReport(params: {
    period: string
    categoryIds?: string[]
    format?: 'xlsx' | 'pdf'
  }): Promise<Blob> {
    return request.get('/depreciation/report/export/', {
      params,
      responseType: 'blob'
    })
  },

  // Asset Detail
  getAssetDetail(assetId: string): Promise<{
    assetInfo: Asset
    stat: {
      usedMonths: number
      accumulated: number
      netValue: number
      progress: number
    }
    records: DepreciationRecord[]
  }> {
    return request.get(`/depreciation/assets/${assetId}/detail/`)
  },

  // Configuration
  getCategoryConfig(categoryId: string): Promise<DepreciationConfig> {
    return request.get(`/depreciation/config/categories/${categoryId}/`)
  },

  updateCategoryConfig(categoryId: string, config: Partial<DepreciationConfig>): Promise<void> {
    return request.put(`/depreciation/config/categories/${categoryId}/`, config)
  }
}
```

---

## Component: DepreciationList

```vue
<!-- frontend/src/views/depreciation/DepreciationList.vue -->
<template>
  <div class="depreciation-list">
    <!-- Search and Actions -->
    <el-card class="search-card">
      <el-form :model="queryForm" inline>
        <el-form-item label="资产编码">
          <el-input
            v-model="queryForm.assetCode"
            placeholder="请输入"
            clearable
          />
        </el-form-item>
        <el-form-item label="折旧期间">
          <el-date-picker
            v-model="queryForm.period"
            type="month"
            format="YYYY-MM"
            value-format="YYYY-MM"
            placeholder="选择月份"
          />
        </el-form-item>
        <el-form-item label="状态">
          <el-select v-model="queryForm.status" placeholder="请选择" clearable>
            <el-option label="草稿" value="draft" />
            <el-option label="已提交" value="submitted" />
            <el-option label="已审核" value="approved" />
            <el-option label="已过账" value="posted" />
          </el-select>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="handleSearch">查询</el-button>
          <el-button @click="handleReset">重置</el-button>
        </el-form-item>
      </el-form>

      <div class="toolbar">
        <el-button
          type="primary"
          :loading="calculating"
          @click="handleCalculate"
        >
          计算当月折旧
        </el-button>
        <el-button
          :disabled="selectedRows.length === 0"
          @click="handleBatchPost"
        >
          批量过账
        </el-button>
        <el-button @click="handleExport">导出</el-button>
      </div>
    </el-card>

    <!-- Data Table -->
    <el-card>
      <el-table
        v-loading="loading"
        :data="tableData"
        border
        @selection-change="handleSelectionChange"
      >
        <el-table-column type="selection" width="50" />
        <el-table-column prop="asset.code" label="资产编码" width="140" />
        <el-table-column prop="asset.name" label="资产名称" width="180" />
        <el-table-column prop="period" label="折旧期间" width="100" />
        <el-table-column label="折旧方法" width="120">
          <template #default="{ row }">
            <el-tag size="small">{{ getMethodName(row.depreciationMethod) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="purchasePrice" label="原值" width="120" align="right">
          <template #default="{ row }">¥{{ formatMoney(row.purchasePrice) }}</template>
        </el-table-column>
        <el-table-column prop="depreciationAmount" label="本月折旧" width="120" align="right">
          <template #default="{ row }">¥{{ formatMoney(row.depreciationAmount) }}</template>
        </el-table-column>
        <el-table-column prop="accumulatedDepreciation" label="累计折旧" width="130" align="right">
          <template #default="{ row }">¥{{ formatMoney(row.accumulatedDepreciation) }}</template>
        </el-table-column>
        <el-table-column prop="netValue" label="净值" width="120" align="right">
          <template #default="{ row }">¥{{ formatMoney(row.netValue) }}</template>
        </el-table-column>
        <el-table-column prop="status" label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="getStatusType(row.status)">
              {{ getStatusName(row.status) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="150" fixed="right">
          <template #default="{ row }">
            <el-button link type="primary" @click="handleView(row)">
              详情
            </el-button>
            <el-button
              v-if="row.status === 'approved'"
              link
              type="success"
              @click="handlePost(row)"
            >
              过账
            </el-button>
          </template>
        </el-table-column>
      </el-table>

      <el-pagination
        v-model:current-page="pagination.page"
        v-model:page-size="pagination.pageSize"
        :total="pagination.total"
        layout="total, sizes, prev, pager, next"
        @size-change="fetchData"
        @current-change="fetchData"
      />
    </el-card>

    <!-- Calculation Progress Dialog -->
    <el-dialog
      v-model="calculationVisible"
      title="折旧计算"
      width="500px"
      :close-on-click-modal="false"
    >
      <div class="calculation-progress">
        <el-progress
          :percentage="calculationProgress"
          :status="calculationStatus === 'completed' ? 'success' : undefined"
        />
        <p class="progress-text">
          {{ calculationText }}
        </p>
      </div>
      <template #footer v-if="calculationStatus === 'completed'">
        <el-button type="primary" @click="calculationVisible = false">
          确定
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { depreciationApi } from '@/api/depreciation'
import type { DepreciationRecord, DepreciationMethod, DepreciationStatus } from '@/types/depreciation'

const router = useRouter()

const queryForm = reactive({
  assetCode: '',
  period: '',
  status: ''
})

const tableData = ref<DepreciationRecord[]>([])
const loading = ref(false)
const calculating = ref(false)
const selectedRows = ref<DepreciationRecord[]>([])

const pagination = reactive({
  page: 1,
  pageSize: 20,
  total: 0
})

const calculationVisible = ref(false)
const calculationProgress = ref(0)
const calculationStatus = ref<'pending' | 'processing' | 'completed' | 'failed'>('pending')
const calculationText = ref('')

const methodLabels: Record<DepreciationMethod, string> = {
  straight_line: '直线法',
  double_declining: '双倍余额递减法',
  sum_of_years: '年数总和法'
}

const statusLabels: Record<DepreciationStatus, string> = {
  draft: '草稿',
  submitted: '已提交',
  approved: '已审核',
  posted: '已过账'
}

const statusTypeMap: Record<DepreciationStatus, string> = {
  draft: 'info',
  submitted: 'warning',
  approved: 'success',
  posted: ''
}

const getMethodName = (method: DepreciationMethod) => methodLabels[method] || method
const getStatusName = (status: DepreciationStatus) => statusLabels[status] || status
const getStatusType = (status: DepreciationStatus) => statusTypeMap[status] || ''

const formatMoney = (val: number) => {
  return Number(val).toLocaleString('zh-CN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })
}

const fetchData = async () => {
  loading.value = true
  try {
    const response = await depreciationApi.listRecords({
      ...queryForm,
      page: pagination.page,
      pageSize: pagination.pageSize
    })
    tableData.value = response.results
    pagination.total = response.count
  } finally {
    loading.value = false
  }
}

const handleSearch = () => {
  pagination.page = 1
  fetchData()
}

const handleReset = () => {
  Object.assign(queryForm, {
    assetCode: '',
    period: '',
    status: ''
  })
  handleSearch()
}

const handleCalculate = async () => {
  try {
    await ElMessageBox.confirm('确认计算当月所有资产的折旧？', '提示', { type: 'warning' })
    calculating.value = true
    calculationVisible.value = true
    calculationProgress.value = 0
    calculationStatus.value = 'processing'
    calculationText.value = '正在提交计算任务...'

    const { taskId } = await depreciationApi.calculate()

    // Poll for status
    pollCalculationStatus(taskId)
  } catch (error) {
    calculating.value = false
  }
}

const pollCalculationStatus = async (taskId: string) => {
  const interval = setInterval(async () => {
    const status = await depreciationApi.getCalculationStatus(taskId)
    calculationProgress.value = Math.round((status.processed / status.total) * 100)
    calculationText.value = `正在计算... (${status.processed}/${status.total})`

    if (status.status === 'completed') {
      clearInterval(interval)
      calculationStatus.value = 'completed'
      calculationText.value = `计算完成，共处理 ${status.total} 项资产`
      calculating.value = false
      fetchData()
    } else if (status.status === 'failed') {
      clearInterval(interval)
      calculationStatus.value = 'failed'
      calculationText.value = '计算失败，请稍后重试'
      calculating.value = false
    }
  }, 1000)
}

const handlePost = async (row: DepreciationRecord) => {
  try {
    await ElMessageBox.confirm('确认过账此折旧记录？过账后将无法修改', '提示', { type: 'warning' })
    await depreciationApi.post(row.id)
    ElMessage.success('过账成功')
    fetchData()
  } catch {
    // User cancelled
  }
}

const handleBatchPost = async () => {
  try {
    await ElMessageBox.confirm(`确认过账 ${selectedRows.value.length} 条折旧记录？`, '批量过账')
    await depreciationApi.batchPost(selectedRows.value.map(r => r.id))
    ElMessage.success('批量过账成功')
    fetchData()
  } catch {
    // User cancelled
  }
}

const handleExport = async () => {
  try {
    const blob = await depreciationApi.exportReport({
      period: queryForm.period || new Date().toISOString().slice(0, 7)
    })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `折旧记录_${queryForm.period || '全部'}.xlsx`
    a.click()
    URL.revokeObjectURL(url)
  } catch {
    ElMessage.error('导出失败')
  }
}

const handleView = (row: DepreciationRecord) => {
  router.push(`/depreciation/assets/${row.assetId}`)
}

const handleSelectionChange = (rows: DepreciationRecord[]) => {
  selectedRows.value = rows
}

onMounted(() => {
  // Set default period to current month
  const now = new Date()
  queryForm.period = `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, '0')}`
  fetchData()
})
</script>

<style scoped>
.depreciation-list {
  padding: 20px;
}

.search-card {
  margin-bottom: 20px;
}

.toolbar {
  display: flex;
  gap: 12px;
  margin-top: 16px;
}

.calculation-progress {
  padding: 20px 0;
}

.progress-text {
  text-align: center;
  margin-top: 16px;
  color: #606266;
}
</style>
```

---

## Output Files

| File | Description |
|------|-------------|
| `frontend/src/types/depreciation.ts` | Depreciation type definitions |
| `frontend/src/api/depreciation.ts` | Depreciation API service |
| `frontend/src/views/depreciation/DepreciationList.vue` | Depreciation list page |
| `frontend/src/views/depreciation/AssetDepreciationDetail.vue` | Asset depreciation detail |
| `frontend/src/views/depreciation/DepreciationReport.vue` | Depreciation report |
| `frontend/src/views/depreciation/DepreciationConfig.vue` | Depreciation method configuration |
