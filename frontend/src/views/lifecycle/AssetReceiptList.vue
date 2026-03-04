<template>
  <div class="page-container">
    <BaseListPage
      ref="listRef"
      :title="$t('assets.lifecycle.assetReceipt.title')"
      :search-fields="searchFields"
      :table-columns="columns"
      :api="fetchList"
    >
      <template #toolbar>
        <el-button
          type="primary"
          :icon="Plus"
          @click="handleCreate"
        >
          {{ $t('assets.lifecycle.assetReceipt.createButton') }}
        </el-button>
      </template>

      <template #status="{ row }">
        <el-tag
          :type="getStatusType(row.status)"
          size="small"
        >
          {{ getStatusLabel(row.status) }}
        </el-tag>
      </template>

      <template #actions="{ row }">
        <el-button
          link
          type="primary"
          @click="handleView(row)"
        >
          {{ $t('common.actions.view') }}
        </el-button>
        <el-button
          v-if="row.status === 'draft'"
          link
          type="primary"
          @click="handleSubmitInspection(row)"
        >
          {{ $t('assets.lifecycle.assetReceipt.actions.submitInspection') }}
        </el-button>
        <el-button
          v-if="['draft', 'submitted'].includes(row.status)"
          link
          type="danger"
          @click="handleCancel(row)"
        >
          {{ $t('assets.lifecycle.assetReceipt.actions.cancel') }}
        </el-button>
      </template>
    </BaseListPage>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { Plus } from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { useI18n } from 'vue-i18n'
import { assetReceiptApi } from '@/api/lifecycle'
import BaseListPage from '@/components/common/BaseListPage.vue'
import type { TableColumn, SearchField } from '@/types/common'

const router = useRouter()
const { t } = useI18n()
const listRef = ref()

const fetchList = async (params: any) => {
  const res = await assetReceiptApi.list({ ...params, page_size: params.pageSize }) as any
  return { results: res.results || res.items || [], count: res.count || res.total || 0 }
}

const statuses = ['draft', 'submitted', 'inspecting', 'passed', 'rejected', 'cancelled']

const searchFields: SearchField[] = [
  {
    prop: 'status',
    label: t('assets.lifecycle.assetReceipt.columns.status'),
    type: 'select',
    options: statuses.map(s => ({
      label: t(`assets.lifecycle.assetReceipt.status.${s}`),
      value: s
    }))
  },
  {
    prop: 'search',
    label: t('common.actions.search'),
    type: 'text',
    placeholder: t('assets.lifecycle.assetReceipt.columns.receiptNo')
  }
]

const getStatusType = (s: string) => {
  const map: Record<string, string> = {
    draft: 'info', submitted: 'warning', inspecting: 'primary',
    passed: 'success', rejected: 'danger', cancelled: 'info'
  }
  return map[s] || 'info'
}
const getStatusLabel = (s: string) => t(`assets.lifecycle.assetReceipt.status.${s}`) || s

const columns: TableColumn[] = [
  { prop: 'receiptNo', label: t('assets.lifecycle.assetReceipt.columns.receiptNo'), width: 160 },
  { prop: 'supplier', label: t('assets.lifecycle.assetReceipt.columns.supplier'), width: 140 },
  { prop: 'deliveryNo', label: t('assets.lifecycle.assetReceipt.columns.deliveryNo'), width: 140 },
  { prop: 'receiptDate', label: t('assets.lifecycle.assetReceipt.columns.receiptDate'), width: 120 },
  { prop: 'status', label: t('assets.lifecycle.assetReceipt.columns.status'), width: 110, slot: 'status' },
  { prop: 'createdAt', label: t('assets.lifecycle.assetReceipt.columns.createdAt'), width: 160 }
]

const handleCreate = () => router.push('/assets/lifecycle/asset-receipts/create')
const handleView = (row: any) => router.push(`/assets/lifecycle/asset-receipts/${row.id}`)

const handleSubmitInspection = async (row: any) => {
  try {
    await ElMessageBox.confirm(
      t('assets.lifecycle.assetReceipt.messages.submitInspectionConfirm'),
      t('common.messages.confirmTitle'),
      { type: 'info' }
    )
    await assetReceiptApi.submitInspection(row.id)
    ElMessage.success(t('assets.lifecycle.assetReceipt.messages.submitInspectionSuccess'))
    listRef.value?.refresh()
  } catch { /* cancelled */ }
}

const handleCancel = async (row: any) => {
  try {
    await ElMessageBox.confirm(
      t('assets.lifecycle.assetReceipt.messages.cancelConfirm'),
      t('common.messages.confirmTitle'),
      { type: 'warning' }
    )
    await assetReceiptApi.cancel(row.id)
    ElMessage.success(t('assets.lifecycle.assetReceipt.messages.cancelSuccess'))
    listRef.value?.refresh()
  } catch { /* cancelled */ }
}
</script>
