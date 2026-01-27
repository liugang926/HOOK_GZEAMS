<template>
  <div class="voucher-list-page">
    <BaseListPage
      title="财务凭证"
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
          新增凭证
        </el-button>
        <el-button
          :icon="Upload"
          @click="handlePushBatch"
        >
          批量推送到ERP
        </el-button>
      </template>

      <template #cell-amount="{ row }">
        <span class="money-text">¥{{ formatMoney(row.totalAmount) }}</span>
      </template>

      <template #cell-status="{ row }">
        <el-tag :type="getStatusType(row.status)">
          {{ getStatusLabel(row.status) }}
        </el-tag>
      </template>

      <template #actions="{ row }">
        <el-button
          link
          type="primary"
          @click="handleView(row)"
        >
          详情
        </el-button>
        <el-button 
          v-if="row.status === 'approved' && !row.isPosted" 
          link 
          type="success" 
          @click="handlePost(row)"
        >
          入账
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
  </div>
</template>

<script setup lang="ts">
import { Plus, Upload } from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import BaseListPage from '@/components/common/BaseListPage.vue'
import { financeApi } from '@/api/finance'
import { formatMoney } from '@/utils/numberFormat'

// ===================================
// Props & State
// ===================================

const columns = [
  { prop: 'voucherNo', label: '凭证号', width: 140, fixed: 'left' },
  { prop: 'businessType', label: '业务类型', width: 120 },
  { prop: 'voucherDate', label: '凭证日期', width: 120 },
  { prop: 'summary', label: '摘要', minWidth: 200 },
  { prop: 'amount', label: '总金额', width: 120, slot: true, align: 'right' },
  { prop: 'status', label: '状态', width: 100, slot: true, fixed: 'right' }
]

const searchFields = [
  { field: 'voucherNo', label: '凭证号', type: 'input' },
  { 
    field: 'businessType', 
    label: '业务类型', 
    type: 'select',
    options: [
      { label: '资产采购', value: 'asset_purchase' },
      { label: '折旧计提', value: 'depreciation' },
      { label: '资产处置', value: 'asset_disposal' }
    ]
  },
  {
    field: 'status',
    label: '状态',
    type: 'select',
    options: [
      { label: '草稿', value: 'draft' },
      { label: '待审批', value: 'pending' },
      { label: '已审批', value: 'approved' },
      { label: '已入账', value: 'posted' }
    ]
  },
  { field: 'voucherDateRange', label: '凭证日期', type: 'daterange' }
]

const batchActions = [
  {
    label: '批量推送',
    type: 'primary',
    action: (rows: any[]) => handleBatchPush(rows)
  }
]

// ===================================
// Methods
// ===================================

const fetchVouchers = async (params: any) => {
  // Map date range if needed
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
    pending: 'warning',
    approved: 'primary',
    posted: 'success',
    rejected: 'danger'
  }
  return map[status] || 'info'
}

const getStatusLabel = (status: string) => {
  const map: Record<string, string> = {
    draft: '草稿',
    pending: '待审批',
    approved: '已审批',
    posted: '已入账',
    rejected: '已驳回'
  }
  return map[status] || status
}

const handleCreate = () => {
    // TODO: Navigate to create page or open dialog
    ElMessage.info('功能开发中')
}

const handleView = (row: any) => {
    // TODO: Navigate to detail
    ElMessage.info(`查看凭证: ${row.voucherNo}`)
}

const handleDelete = async (row: any) => {
  try {
    await ElMessageBox.confirm(`确认删除凭证 ${row.voucherNo}?`, '提示', { type: 'warning' })
    await financeApi.deleteVoucher(row.id)
    ElMessage.success('删除成功')
    window.dispatchEvent(new CustomEvent('refresh-base-list'))
  } catch (e) {
    // cancelled
  }
}

const handlePost = async (row: any) => {
  try {
    await ElMessageBox.confirm(`确认将凭证 ${row.voucherNo} 记账?`, '提示', { type: 'warning' })
    await financeApi.postVoucher(row.id)
    ElMessage.success('记账成功')
    window.dispatchEvent(new CustomEvent('refresh-base-list'))
  } catch (e: any) {
     if (e !== 'cancel') ElMessage.error(e.message || '记账失败')
  }
}

const handlePushBatch = () => {
    ElMessage.info('请选择要推送的凭证')
}

const handleBatchPush = async (rows: any[]) => {
    try {
        const ids = rows.map(r => r.id)
        await financeApi.batchPushVouchers(ids)
        ElMessage.success('推送任务已提交')
    } catch (e: any) {
        ElMessage.error('推送失败')
    }
}
</script>

<style scoped>
.money-text {
  font-family: monospace;
  font-weight: bold;
}
</style>
