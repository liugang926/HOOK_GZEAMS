<template>
  <div class="page-container">
    <BaseListPage
      ref="listRef"
      :title="$t('assets.lifecycle.purchaseRequest.title')"
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
          {{ $t('assets.lifecycle.purchaseRequest.createButton') }}
        </el-button>
      </template>

      <template #status="{ row }">
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
          {{ $t('common.actions.view') }}
        </el-button>
        <el-button
          v-if="row.status === 'draft'"
          link
          type="primary"
          @click="handleSubmit(row)"
        >
          {{ $t('assets.lifecycle.purchaseRequest.actions.submit') }}
        </el-button>
        <el-button
          v-if="['draft', 'submitted'].includes(row.status)"
          link
          type="danger"
          @click="handleCancel(row)"
        >
          {{ $t('assets.lifecycle.purchaseRequest.actions.cancel') }}
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
import { purchaseRequestApi } from '@/api/lifecycle'
import BaseListPage from '@/components/common/BaseListPage.vue'
import type { TableColumn, SearchField } from '@/types/common'

const router = useRouter()
const { t } = useI18n()
const listRef = ref()

const fetchList = async (params: any) => {
  const res = await purchaseRequestApi.list({
    ...params,
    page_size: params.pageSize
  }) as any
  return {
    results: res.results || res.items || [],
    count: res.count || res.total || 0
  }
}

const statusOptions = [
  'draft', 'submitted', 'approved', 'rejected', 'processing', 'completed', 'cancelled'
]

const searchFields: SearchField[] = [
  {
    prop: 'status',
    label: t('assets.lifecycle.purchaseRequest.columns.status'),
    type: 'select',
    options: statusOptions.map(s => ({
      label: t(`assets.lifecycle.purchaseRequest.status.${s}`),
      value: s
    }))
  },
  {
    prop: 'search',
    label: t('common.actions.search'),
    type: 'text',
    placeholder: t('assets.lifecycle.purchaseRequest.columns.requestNo')
  }
]

const getStatusType = (status: string) => {
  const map: Record<string, string> = {
    draft: 'info',
    submitted: 'warning',
    approved: 'success',
    rejected: 'danger',
    processing: 'primary',
    completed: '',
    cancelled: 'info'
  }
  return map[status] || 'info'
}

const getStatusLabel = (status: string) =>
  t(`assets.lifecycle.purchaseRequest.status.${status}`) || status

const columns: TableColumn[] = [
  { prop: 'requestNo', label: t('assets.lifecycle.purchaseRequest.columns.requestNo'), width: 160 },
  { prop: 'requesterDisplay', label: t('assets.lifecycle.purchaseRequest.columns.requester'), width: 100 },
  { prop: 'departmentDisplay', label: t('assets.lifecycle.purchaseRequest.columns.department'), width: 120 },
  { prop: 'totalAmount', label: t('assets.lifecycle.purchaseRequest.columns.totalAmount'), width: 120, align: 'right' },
  { prop: 'status', label: t('assets.lifecycle.purchaseRequest.columns.status'), width: 100, slot: 'status' },
  { prop: 'createdAt', label: t('assets.lifecycle.purchaseRequest.columns.createdAt'), width: 160 }
]

const handleCreate = () => router.push('/assets/lifecycle/purchase-requests/create')
const handleView = (row: any) => router.push(`/assets/lifecycle/purchase-requests/${row.id}`)

const handleSubmit = async (row: any) => {
  try {
    await ElMessageBox.confirm(
      t('assets.lifecycle.purchaseRequest.actions.submit'),
      t('common.messages.confirmTitle'),
      { type: 'info' }
    )
    await purchaseRequestApi.submit(row.id)
    ElMessage.success(t('assets.lifecycle.purchaseRequest.messages.submitSuccess'))
    listRef.value?.refresh()
  } catch { /* user cancelled */ }
}

const handleCancel = async (row: any) => {
  try {
    await ElMessageBox.confirm(
      t('assets.lifecycle.purchaseRequest.messages.cancelConfirm'),
      t('common.messages.confirmTitle'),
      { type: 'warning' }
    )
    await purchaseRequestApi.cancel(row.id)
    ElMessage.success(t('assets.lifecycle.purchaseRequest.messages.cancelSuccess'))
    listRef.value?.refresh()
  } catch { /* user cancelled */ }
}
</script>
