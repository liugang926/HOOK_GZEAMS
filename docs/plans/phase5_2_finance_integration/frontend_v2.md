# Phase 5.2: Finance Integration - Frontend Implementation v2

## Document Information

| Project | Details |
|---------|---------|
| PRD Version | v2.0 (Updated for API Standardization) |
| Updated Date | 2026-01-22 |
| References | [frontend_api_standardization_design.md](../common_base_features/00_core/frontend_api_standardization_design.md) |

---

## Task Overview

Implement financial voucher management with template configuration, ERP integration, and automated voucher generation for asset transactions.

---

## API Service Layer

### Type Definitions

```typescript
// frontend/src/types/finance.ts

export interface FinanceVoucher {
  id: string
  voucherNo: string
  voucherDate: string
  businessType: BusinessType
  businessId?: string
  voucherType: string
  description: string
  totalDebit: number
  totalCredit: number
  status: VoucherStatus
  entries: VoucherEntry[]
  externalVoucherNo?: string
  externalSystem?: IntegrationSystem
  integrationStatus?: IntegrationStatus
  integrationError?: string
  approvedBy?: string
  approvedAt?: string
  approveComment?: string
  organizationId: string
  createdAt: string
  createdBy: string
}

export enum BusinessType {
  ASSET_PURCHASE = 'asset_purchase',
  ASSET_DEPRECIATION = 'asset_depreciation',
  ASSET_DISPOSAL = 'asset_disposal',
  ASSET_TRANSFER = 'asset_transfer',
  CONSUMABLE_PURCHASE = 'consumable_purchase'
}

export enum VoucherStatus {
  DRAFT = 'draft',
  SUBMITTED = 'submitted',
  APPROVED = 'approved',
  REJECTED = 'rejected',
  POSTED = 'posted'
}

export enum IntegrationSystem {
  M18 = 'm18',
  SAP = 'sap',
  KINGDEE = 'kingdee',
  YONYOU = 'yonyou'
}

export enum IntegrationStatus {
  PENDING = 'pending',
  SUCCESS = 'success',
  FAILED = 'failed'
}

export interface VoucherEntry {
  id: string
  lineNo: number
  accountCode: string
  accountName: string
  debit: number
  credit: number
  description: string
}

export interface VoucherTemplate {
  id: string
  templateName: string
  code: string
  businessType: BusinessType
  voucherType: string
  defaultDescription: string
  entriesConfig: TemplateEntryConfig[]
  isActive: boolean
  organizationId: string
}

export interface TemplateEntryConfig {
  lineNo: number
  accountCode: string
  accountName: string
  debitOrCredit: 'debit' | 'credit'
  amountFormula?: string
  description?: string
}

export interface VoucherCreate {
  voucherDate: string
  businessType: BusinessType
  businessId?: string
  description: string
  entries: Array<{
    accountCode: string
    debit: number
    credit: number
    description: string
  }>
}

export interface VoucherApprovalAction {
  action: 'approve' | 'reject'
  comment?: string
}
```

### API Service

```typescript
// frontend/src/api/finance.ts

import request from '@/utils/request'
import type { PaginatedResponse } from '@/types/api'
import type {
  FinanceVoucher,
  VoucherTemplate,
  VoucherCreate,
  VoucherApprovalAction,
  BusinessType
} from '@/types/finance'

export const financeApi = {
  // Voucher Templates
  listTemplates(params?: {
    businessType?: BusinessType
    isActive?: boolean
  }): Promise<VoucherTemplate[]> {
    return request.get('/finance/voucher-templates/', { params })
  },

  getTemplate(id: string): Promise<VoucherTemplate> {
    return request.get(`/finance/voucher-templates/${id}/`)
  },

  createTemplate(data: Partial<VoucherTemplate>): Promise<VoucherTemplate> {
    return request.post('/finance/voucher-templates/', data)
  },

  updateTemplate(id: string, data: Partial<VoucherTemplate>): Promise<VoucherTemplate> {
    return request.put(`/finance/voucher-templates/${id}/`, data)
  },

  deleteTemplate(id: string): Promise<void> {
    return request.delete(`/finance/voucher-templates/${id}/`)
  },

  // Finance Vouchers
  listVouchers(params?: {
    voucherNo?: string
    businessType?: BusinessType
    status?: VoucherStatus
    voucherDateFrom?: string
    voucherDateTo?: string
    page?: number
    pageSize?: number
  }): Promise<PaginatedResponse<FinanceVoucher>> {
    return request.get('/finance/vouchers/', { params })
  },

  getVoucher(id: string): Promise<FinanceVoucher> {
    return request.get(`/finance/vouchers/${id}/`)
  },

  createVoucher(data: VoucherCreate): Promise<FinanceVoucher> {
    return request.post('/finance/vouchers/', data)
  },

  updateVoucher(id: string, data: Partial<FinanceVoucher>): Promise<FinanceVoucher> {
    return request.put(`/finance/vouchers/${id}/`, data)
  },

  deleteVoucher(id: string): Promise<void> {
    return request.delete(`/finance/vouchers/${id}/`)
  },

  submitVoucher(id: string): Promise<void> {
    return request.post(`/finance/vouchers/${id}/submit/`)
  },

  approveVoucher(id: string, data: VoucherApprovalAction): Promise<void> {
    return request.post(`/finance/vouchers/${id}/approve/`, data)
  },

  // Integration
  pushVoucher(id: string, system?: IntegrationSystem): Promise<{
    success: boolean
    externalVoucherNo?: string
    error?: string
  }> {
    return request.post(`/finance/vouchers/${id}/push/`, { system })
  },

  batchPushVouchers(ids: string[]): Promise<{
    success: number
    failed: number
    results: Array<{ id: string; success: boolean; error?: string }>
  }> {
    return request.post('/finance/vouchers/batch-push/', { ids })
  },

  // Auto-generation
  generateAssetPurchaseVoucher(data: {
    businessId: string
    assetIds: string[]
  }): Promise<FinanceVoucher> {
    return request.post('/finance/vouchers/generate/asset-purchase/', data)
  },

  generateDepreciationVoucher(data: {
    period: string
    categoryIds?: string[]
  }): Promise<FinanceVoucher> {
    return request.post('/finance/vouchers/generate/depreciation/', data)
  },

  generateDisposalVoucher(data: {
    businessId: string
    assetId: string
  }): Promise<FinanceVoucher> {
    return request.post('/finance/vouchers/generate/disposal/', data)
  }
}
```

---

## Component: VoucherList

```vue
<!-- frontend/src/views/finance/VoucherList.vue -->
<template>
  <BaseListPage
    title="财务凭证"
    :fetch-method="fetchData"
    :columns="columns"
    :search-fields="searchFields"
  >
    <template #actions>
      <el-button type="primary" :icon="Plus" @click="handleCreate">
        新增凭证
      </el-button>
      <el-button
        :icon="Upload"
        :disabled="selectedRows.length === 0"
        @click="handleBatchPush"
      >
        批量推送
      </el-button>
      <el-button :icon="Download" @click="handleExport">
        导出
      </el-button>
    </template>

    <template #cell-status="{ row }">
      <el-tag :type="getStatusType(row.status)">
        {{ getStatusLabel(row.status) }}
      </el-tag>
    </template>

    <template #cell-totalDebit="{ row }">
      <span class="money-text debit">¥{{ formatMoney(row.totalDebit) }}</span>
    </template>

    <template #cell-totalCredit="{ row }">
      <span class="money-text credit">¥{{ formatMoney(row.totalCredit) }}</span>
    </template>

    <template #cell-integrationStatus="{ row }">
      <div v-if="row.externalSystem" class="integration-status">
        <el-tag size="small" type="info">
          {{ getSystemName(row.externalSystem) }}
        </el-tag>
        <el-tag
          v-if="row.integrationStatus"
          size="small"
          :type="row.integrationStatus === 'success' ? 'success' : 'danger'"
        >
          {{ row.externalVoucherNo || '失败' }}
        </el-tag>
      </div>
      <span v-else>-</span>
    </template>

    <template #actions="{ row }">
      <el-button link type="primary" @click="handleView(row)">
        详情
      </el-button>
      <el-button
        v-if="row.status === 'draft'"
        link
        type="primary"
        @click="handleEdit(row)"
      >
        编辑
      </el-button>
      <el-button
        v-if="row.status === 'draft'"
        link
        type="primary"
        @click="handleSubmit(row)"
      >
        提交
      </el-button>
      <el-button
        v-if="row.status === 'submitted'"
        link
        type="success"
        @click="handleApprove(row)"
      >
        审核
      </el-button>
      <el-button
        v-if="['approved', 'submitted'].includes(row.status) && !row.externalVoucherNo"
        link
        type="warning"
        @click="handlePush(row)"
      >
        推送
      </el-button>
    </template>
  </BaseListPage>

  <!-- Voucher Detail Dialog -->
  <VoucherDetailDialog
    v-model="detailVisible"
    :voucher="currentVoucher"
    @approve="handleApproveSubmit"
    @reject="handleReject"
  />

  <!-- Voucher Form Dialog -->
  <VoucherFormDialog
    v-model="formVisible"
    :voucher="editingVoucher"
    @success="refreshTable"
  />
</template>

<script setup lang="ts">
import { ref, reactive } from 'vue'
import { Plus, Upload, Download } from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { financeApi } from '@/api/finance'
import BaseListPage from '@/components/common/BaseListPage.vue'
import VoucherDetailDialog from '../components/VoucherDetailDialog.vue'
import VoucherFormDialog from '../components/VoucherFormDialog.vue'
import type { FinanceVoucher, VoucherStatus, IntegrationSystem } from '@/types/finance'

const columns = [
  { prop: 'voucherNo', label: '凭证号', width: 150 },
  { prop: 'voucherDate', label: '凭证日期', width: 120 },
  { prop: 'businessType', label: '业务类型', width: 120, format: getBusinessTypeLabel },
  { prop: 'voucherType', label: '凭证字', width: 80 },
  { prop: 'description', label: '摘要', minWidth: 200 },
  { prop: 'totalDebit', label: '借方合计', width: 130, slot: true },
  { prop: 'totalCredit', label: '贷方合计', width: 130, slot: true },
  { prop: 'status', label: '状态', width: 100, slot: true },
  { prop: 'integrationStatus', label: '推送状态', width: 160, slot: true }
]

const searchFields = [
  {
    field: 'voucherNo',
    label: '凭证号',
    type: 'input',
    placeholder: '请输入凭证号'
  },
  {
    field: 'businessType',
    label: '业务类型',
    type: 'select',
    options: [
      { label: '资产购入', value: 'asset_purchase' },
      { label: '资产折旧', value: 'asset_depreciation' },
      { label: '资产处置', value: 'asset_disposal' },
      { label: '资产调拨', value: 'asset_transfer' }
    ]
  },
  {
    field: 'status',
    label: '状态',
    type: 'select',
    options: [
      { label: '草稿', value: 'draft' },
      { label: '已提交', value: 'submitted' },
      { label: '已审核', value: 'approved' },
      { label: '已过账', value: 'posted' }
    ]
  },
  {
    field: 'dateRange',
    label: '凭证日期',
    type: 'daterange'
  }
]

const detailVisible = ref(false)
const formVisible = ref(false)
const currentVoucher = ref<FinanceVoucher | null>(null)
const editingVoucher = ref<FinanceVoucher | null>(null)
const selectedRows = ref<FinanceVoucher[]>([])

const fetchData = async (params: any) => {
  const queryParams = {
    ...params,
    voucherDateFrom: params.dateRange?.[0],
    voucherDateTo: params.dateRange?.[1]
  }
  delete queryParams.dateRange
  return financeApi.listVouchers(queryParams)
}

const getStatusType = (status: VoucherStatus) => {
  const typeMap: Record<VoucherStatus, string> = {
    draft: 'info',
    submitted: 'warning',
    approved: 'success',
    rejected: 'danger',
    posted: ''
  }
  return typeMap[status] || 'info'
}

const getStatusLabel = (status: VoucherStatus) => {
  const labelMap: Record<VoucherStatus, string> = {
    draft: '草稿',
    submitted: '已提交',
    approved: '已审核',
    rejected: '已驳回',
    posted: '已过账'
  }
  return labelMap[status] || status
}

const getBusinessTypeLabel = (type: string) => {
  const labelMap: Record<string, string> = {
    asset_purchase: '资产购入',
    asset_depreciation: '资产折旧',
    asset_disposal: '资产处置',
    asset_transfer: '资产调拨',
    consumable_purchase: '耗材购入'
  }
  return labelMap[type] || type
}

const getSystemName = (system: IntegrationSystem) => {
  const nameMap: Record<IntegrationSystem, string> = {
    m18: 'M18',
    sap: 'SAP',
    kingdee: '金蝶',
    yonyou: '用友'
  }
  return nameMap[system] || system
}

const formatMoney = (val: number) => {
  return Number(val).toLocaleString('zh-CN', { minimumFractionDigits: 2 })
}

const handleCreate = () => {
  editingVoucher.value = null
  formVisible.value = true
}

const handleView = (row: FinanceVoucher) => {
  currentVoucher.value = row
  detailVisible.value = true
}

const handleEdit = (row: FinanceVoucher) => {
  editingVoucher.value = row
  formVisible.value = true
}

const handleSubmit = async (row: FinanceVoucher) => {
  try {
    await ElMessageBox.confirm('确认提交此凭证？', '提示')
    await financeApi.submitVoucher(row.id)
    ElMessage.success('提交成功')
    refreshTable()
  } catch {
    // User cancelled
  }
}

const handleApprove = (row: FinanceVoucher) => {
  currentVoucher.value = row
  detailVisible.value = true
}

const handleApproveSubmit = async (data: { action: string; comment?: string }) => {
  if (!currentVoucher.value) return
  await financeApi.approveVoucher(currentVoucher.value.id, data as VoucherApprovalAction)
  ElMessage.success('审核成功')
  detailVisible.value = false
  refreshTable()
}

const handleReject = async (comment: string) => {
  if (!currentVoucher.value) return
  await financeApi.approveVoucher(currentVoucher.value.id, {
    action: 'reject',
    comment
  })
  ElMessage.success('已驳回')
  detailVisible.value = false
  refreshTable()
}

const handlePush = async (row: FinanceVoucher) => {
  try {
    await ElMessageBox.confirm('确认推送到ERP系统？', '提示')
    const result = await financeApi.pushVoucher(row.id)
    if (result.success) {
      ElMessage.success(`推送成功，外部凭证号: ${result.externalVoucherNo}`)
    } else {
      ElMessage.error(`推送失败: ${result.error}`)
    }
    refreshTable()
  } catch {
    // User cancelled
  }
}

const handleBatchPush = async () => {
  try {
    await ElMessageBox.confirm(
      `确认推送${selectedRows.value.length}张凭证到ERP系统？`,
      '批量推送'
    )
    const ids = selectedRows.value.map(r => r.id)
    const result = await financeApi.batchPushVouchers(ids)
    ElMessage.success(
      `推送完成: 成功${result.success}张，失败${result.failed}张`
    )
    refreshTable()
  } catch {
    // User cancelled
  }
}

const handleExport = () => {
  ElMessage.info('导出功能开发中')
}

const refreshTable = () => {
  // Trigger refresh via BaseListPage
  window.dispatchEvent(new Event('refresh-table'))
}
</script>

<style scoped>
.money-text {
  font-family: 'Monaco', monospace;
  font-weight: 500;
}

.money-text.debit {
  color: #f56c6c;
}

.money-text.credit {
  color: #67c23a;
}

.integration-status {
  display: flex;
  gap: 4px;
  align-items: center;
}
</style>
```

---

## Output Files

| File | Description |
|------|-------------|
| `frontend/src/types/finance.ts` | Finance type definitions |
| `frontend/src/api/finance.ts` | Finance API service |
| `frontend/src/views/finance/VoucherList.vue` | Voucher list page |
| `frontend/src/views/finance/VoucherForm.vue` | Voucher form page |
| `frontend/src/views/finance/VoucherTemplateList.vue` | Template management |
| `frontend/src/components/finance/VoucherDetailDialog.vue` | Voucher detail dialog |
| `frontend/src/components/finance/VoucherFormDialog.vue` | Voucher form dialog |
| `frontend/src/components/finance/EntryTable.vue` | Entry table component |
