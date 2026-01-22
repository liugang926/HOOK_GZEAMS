<!--
  VoucherList View

  Finance voucher list page with:
  - Voucher filtering and search
  - Create/Submit/Approve/Push operations
  - Debit/Credit balance visualization
  - ERP integration status display
-->

<template>
  <div class="voucher-list-page">
    <BaseListPage
      title="财务凭证"
      :search-fields="searchFields"
      :table-columns="columns"
      :api="fetchVouchers"
      :batch-actions="batchActions"
      @row-click="handleRowClick"
    >
      <template #toolbar>
        <el-button type="primary" :icon="Plus" @click="handleCreate">
          新增凭证
        </el-button>
        <el-button :icon="Upload" @click="handleBatchPush">
          批量推送
        </el-button>
        <el-button :icon="Download" @click="handleExport">
          导出
        </el-button>
      </template>

      <template #actions="{ selectedRows }">
        <span v-if="selectedRows.length > 0" class="selection-info">
          已选择 {{ selectedRows.length }} 项
        </span>
      </template>

      <template #cell-businessType="{ row }">
        <el-tag :type="getBusinessTypeColor(row.businessType)" size="small">
          {{ getBusinessTypeLabel(row.businessType) }}
        </el-tag>
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

      <template #cell-isBalanced="{ row }">
        <el-icon v-if="row.totalDebit === row.totalCredit" class="balanced-icon">
          <CircleCheck />
        </el-icon>
        <el-icon v-else class="unbalanced-icon">
          <CircleClose />
        </el-icon>
      </template>

      <template #cell-isPushed="{ row }">
        <el-tag v-if="row.pushedAt" type="success" size="small">
          已推送
        </el-tag>
        <el-tag v-else type="info" size="small">
          未推送
        </el-tag>
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
          type="success"
          @click="handleSubmit(row)"
        >
          提交
        </el-button>
        <el-button
          v-if="row.status === 'submitted'"
          link
          type="warning"
          @click="handleApprove(row)"
        >
          审核
        </el-button>
        <el-button
          v-if="['approved', 'posted'].includes(row.status) && !row.pushedAt"
          link
          type="primary"
          @click="handlePush(row)"
        >
          推送
        </el-button>
        <el-button
          v-if="row.status === 'draft'"
          link
          type="danger"
          @click="handleDelete(row)"
        >
          删除
        </el-button>
      </template>
    </BaseListPage>

    <!-- Voucher Form Dialog -->
    <VoucherFormDialog
      v-model="formVisible"
      :voucher="currentVoucher"
      @success="handleFormSuccess"
    />

    <!-- Approval Dialog -->
    <ApprovalDialog
      v-model="approvalVisible"
      :voucher="currentVoucher"
      @success="handleApprovalSuccess"
    />
  </div>
</template>

<script setup lang="ts">
/**
 * VoucherList View Component
 *
 * Main list view for finance voucher management.
 * Supports CRUD, approval workflow, and ERP integration.
 */

import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { Plus, Upload, Download, CircleCheck, CircleClose } from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import BaseListPage from '@/components/common/BaseListPage.vue'
import VoucherFormDialog from '@/components/finance/VoucherFormDialog.vue'
import ApprovalDialog from '@/components/finance/ApprovalDialog.vue'
import { financeApi } from '@/api/finance'
import type { FinanceVoucher, VoucherStatus, BusinessType } from '@/types/finance'
import type { TableColumn, SearchField } from '@/types/common'
import { formatMoney } from '@/utils/numberFormat'

const router = useRouter()

// ============================================================================
// State
// ============================================================================

const formVisible = ref(false)
const approvalVisible = ref(false)
const currentVoucher = ref<FinanceVoucher | null>(null)

// ============================================================================
// Table Columns
// ============================================================================

const columns: TableColumn[] = [
  { prop: 'voucherNo', label: '凭证号', width: 140, fixed: 'left' },
  { prop: 'voucherDate', label: '凭证日期', width: 120 },
  { prop: 'businessType', label: '业务类型', width: 120, slot: true },
  { prop: 'description', label: '摘要', minWidth: 180 },
  { prop: 'totalDebit', label: '借方金额', width: 130, slot: true, align: 'right' },
  { prop: 'totalCredit', label: '贷方金额', width: 130, slot: true, align: 'right' },
  { prop: 'isBalanced', label: '平衡', width: 70, slot: true, align: 'center' },
  { prop: 'status', label: '状态', width: 90, slot: true },
  { prop: 'isPushed', label: 'ERP状态', width: 90, slot: true },
  { prop: 'createdAt', label: '创建时间', width: 160 }
]

// ============================================================================
// Search Fields
// ============================================================================

const searchFields: SearchField[] = [
  {
    prop: 'search',
    label: '关键词',
    type: 'text',
    placeholder: '凭证号/摘要'
  },
  {
    prop: 'businessType',
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
    prop: 'status',
    label: '状态',
    type: 'select',
    options: [
      { label: '草稿', value: 'draft' },
      { label: '已提交', value: 'submitted' },
      { label: '已审核', value: 'approved' },
      { label: '已驳回', value: 'rejected' },
      { label: '已过账', value: 'posted' }
    ]
  },
  {
    prop: 'isPushed',
    label: 'ERP状态',
    type: 'select',
    options: [
      { label: '已推送', value: 'true' },
      { label: '未推送', value: 'false' }
    ]
  },
  {
    prop: 'voucherDateRange',
    label: '凭证日期',
    type: 'dateRange'
  }
]

// ============================================================================
// Batch Actions
// ============================================================================

const batchActions = [
  {
    label: '批量提交',
    type: 'success' as const,
    action: handleBatchSubmit
  },
  {
    label: '批量推送',
    type: 'primary' as const,
    action: handleBatchPush
  },
  {
    label: '批量删除',
    type: 'danger' as const,
    action: handleBatchDelete
  }
]

// ============================================================================
// Methods
// ============================================================================

/**
 * Fetch vouchers from API
 */
const fetchVouchers = async (params: any) => {
  return await financeApi.listVouchers(params)
}

/**
 * Get business type label
 */
const getBusinessTypeLabel = (type: BusinessType): string => {
  const labels: Record<BusinessType, string> = {
    asset_purchase: '资产购入',
    asset_depreciation: '资产折旧',
    asset_disposal: '资产处置',
    asset_transfer: '资产调拨'
  }
  return labels[type] || type
}

/**
 * Get business type color
 */
const getBusinessTypeColor = (type: BusinessType): string => {
  const colors: Record<BusinessType, 'primary' | 'success' | 'warning' | 'info'> = {
    asset_purchase: 'primary',
    asset_depreciation: 'warning',
    asset_disposal: 'danger',
    asset_transfer: 'info'
  }
  return colors[type] || 'info'
}

/**
 * Get status label
 */
const getStatusLabel = (status: VoucherStatus): string => {
  const labels: Record<VoucherStatus, string> = {
    draft: '草稿',
    submitted: '已提交',
    approved: '已审核',
    rejected: '已驳回',
    posted: '已过账'
  }
  return labels[status] || status
}

/**
 * Get status type
 */
const getStatusType = (status: VoucherStatus): string => {
  const types: Record<VoucherStatus, 'info' | 'warning' | 'success' | 'danger' | 'primary'> = {
    draft: 'info',
    submitted: 'warning',
    approved: 'success',
    rejected: 'danger',
    posted: 'primary'
  }
  return types[status] || 'info'
}

/**
 * Handle row click
 */
const handleRowClick = (row: FinanceVoucher) => {
  handleView(row)
}

/**
 * Handle create button
 */
const handleCreate = () => {
  currentVoucher.value = null
  formVisible.value = true
}

/**
 * Handle view button
 */
const handleView = (row: FinanceVoucher) => {
  router.push(`/finance/vouchers/${row.id}`)
}

/**
 * Handle edit button
 */
const handleEdit = (row: FinanceVoucher) => {
  currentVoucher.value = row
  formVisible.value = true
}

/**
 * Handle submit button
 */
const handleSubmit = async (row: FinanceVoucher) => {
  try {
    await ElMessageBox.confirm(
      `确认提交凭证"${row.voucherNo}"？提交后需要审核才能过账。`,
      '提交确认',
      {
        type: 'warning',
        confirmButtonText: '确认提交',
        cancelButtonText: '取消'
      }
    )
    await financeApi.submitVoucher(row.id)
    ElMessage.success('提交成功')
    refreshList()
  } catch (error) {
    // User cancelled
  }
}

/**
 * Handle approve button - open approval dialog
 */
const handleApprove = (row: FinanceVoucher) => {
  currentVoucher.value = row
  approvalVisible.value = true
}

/**
 * Handle push button
 */
const handlePush = async (row: FinanceVoucher) => {
  try {
    await ElMessageBox.confirm(
      `确认推送凭证"${row.voucherNo}"到ERP系统？`,
      '推送确认',
      {
        type: 'warning',
        confirmButtonText: '确认推送',
        cancelButtonText: '取消'
      }
    )
    const result = await financeApi.pushVoucher(row.id)
    if (result.success) {
      ElMessage.success(`推送成功，ERP凭证号: ${result.externalVoucherNo}`)
    } else {
      ElMessage.error(`推送失败: ${result.error}`)
    }
    refreshList()
  } catch (error) {
    // User cancelled or error
  }
}

/**
 * Handle delete button
 */
const handleDelete = async (row: FinanceVoucher) => {
  try {
    await ElMessageBox.confirm(
      `确认删除凭证"${row.voucherNo}"？`,
      '删除确认',
      {
        type: 'warning',
        confirmButtonText: '确认删除',
        cancelButtonText: '取消'
      }
    )
    await financeApi.deleteVoucher(row.id)
    ElMessage.success('删除成功')
    refreshList()
  } catch (error) {
    // User cancelled
  }
}

/**
 * Handle batch submit
 */
const handleBatchSubmit = async (selectedRows: FinanceVoucher[]) => {
  const draftVouchers = selectedRows.filter(r => r.status === 'draft')
  if (draftVouchers.length === 0) {
    ElMessage.warning('请选择草稿状态的凭证')
    return
  }
  try {
    await ElMessageBox.confirm(
      `确认提交选中的 ${draftVouchers.length} 张凭证？`,
      '批量提交',
      {
        type: 'warning',
        confirmButtonText: '确认提交',
        cancelButtonText: '取消'
      }
    )
    await Promise.all(draftVouchers.map(v => financeApi.submitVoucher(v.id)))
    ElMessage.success(`成功提交 ${draftVouchers.length} 张凭证`)
    refreshList()
  } catch (error) {
    // User cancelled
  }
}

/**
 * Handle batch push
 */
const handleBatchPush = async (selectedRows?: FinanceVoucher[]) => {
  if (!selectedRows) return

  const pushableVouchers = selectedRows.filter(r =>
    ['approved', 'posted'].includes(r.status) && !r.pushedAt
  )
  if (pushableVouchers.length === 0) {
    ElMessage.warning('没有可推送的凭证（仅已审核/已过账且未推送的凭证可推送）')
    return
  }
  try {
    await ElMessageBox.confirm(
      `确认推送选中的 ${pushableVouchers.length} 张凭证到ERP？`,
      '批量推送',
      {
        type: 'warning',
        confirmButtonText: '确认推送',
        cancelButtonText: '取消'
      }
    )
    const result = await financeApi.batchPushVouchers(pushableVouchers.map(v => v.id))
    ElMessage.success(
      `推送完成：成功 ${result.success}，失败 ${result.failed}`
    )
    refreshList()
  } catch (error) {
    // User cancelled
  }
}

/**
 * Handle batch delete
 */
const handleBatchDelete = async (selectedRows: FinanceVoucher[]) => {
  const draftVouchers = selectedRows.filter(r => r.status === 'draft')
  if (draftVouchers.length === 0) {
    ElMessage.warning('只能删除草稿状态的凭证')
    return
  }
  try {
    await ElMessageBox.confirm(
      `确认删除选中的 ${draftVouchers.length} 张凭证？`,
      '批量删除',
      {
        type: 'warning',
        confirmButtonText: '确认删除',
        cancelButtonText: '取消'
      }
    )
    await Promise.all(draftVouchers.map(v => financeApi.deleteVoucher(v.id)))
    ElMessage.success(`成功删除 ${draftVouchers.length} 张凭证`)
    refreshList()
  } catch (error) {
    // User cancelled
  }
}

/**
 * Handle export
 */
const handleExport = async () => {
  try {
    ElMessage.info('导出功能开发中...')
  } catch (error) {
    ElMessage.error('导出失败')
  }
}

/**
 * Handle form success
 */
const handleFormSuccess = () => {
  formVisible.value = false
  refreshList()
}

/**
 * Handle approval success
 */
const handleApprovalSuccess = () => {
  approvalVisible.value = false
  refreshList()
}

/**
 * Refresh list
 */
const refreshList = () => {
  window.dispatchEvent(new CustomEvent('refresh-base-list'))
}
</script>

<style scoped lang="scss">
.voucher-list-page {
  height: 100%;
}

.money-text {
  font-family: 'Monaco', 'Consolas', monospace;
  font-weight: 500;

  &.debit {
    color: #f56c6c;
  }

  &.credit {
    color: #67c23a;
  }
}

.balanced-icon {
  font-size: 20px;
  color: #67c23a;
}

.unbalanced-icon {
  font-size: 20px;
  color: #f56c6c;
}

.selection-info {
  margin-right: 16px;
  color: #409eff;
  font-size: 14px;
}
</style>
