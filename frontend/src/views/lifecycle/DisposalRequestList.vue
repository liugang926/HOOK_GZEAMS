<template>
  <div class="page-container">
    <BaseListPage
      ref="listRef"
      :title="$t('assets.lifecycle.disposalRequest.title')"
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
          {{ $t('assets.lifecycle.disposalRequest.createButton') }}
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
          @click="handleSubmit(row)"
        >
          {{ $t('assets.lifecycle.disposalRequest.actions.submit') }}
        </el-button>
        <el-button
          v-if="['draft', 'submitted'].includes(row.status)"
          link
          type="danger"
          @click="handleCancel(row)"
        >
          {{ $t('assets.lifecycle.disposalRequest.actions.cancel') }}
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
import { disposalRequestApi } from '@/api/lifecycle'
import BaseListPage from '@/components/common/BaseListPage.vue'
import type { TableColumn, SearchField } from '@/types/common'

const router = useRouter()
const { t } = useI18n()
const listRef = ref()

const fetchList = async (params: any) => {
  const res = await disposalRequestApi.list({
    ...params,
    page_size: params.pageSize
  }) as any
  return {
    results: res.results || res.items || [],
    count: res.count || res.total || 0
  }
}

const statuses = ['draft', 'submitted', 'appraising', 'approved', 'rejected', 'executing', 'completed', 'cancelled']

const searchFields: SearchField[] = [
  {
    prop: 'status',
    label: t('assets.lifecycle.disposalRequest.columns.status'),
    type: 'select',
    options: statuses.map(s => ({
      label: t(`assets.lifecycle.disposalRequest.status.${s}`),
      value: s
    }))
  },
  {
    prop: 'search',
    label: t('common.actions.search'),
    type: 'text',
    placeholder: t('assets.lifecycle.disposalRequest.columns.requestNo')
  }
]

const getStatusType = (s: string) => {
  const map: Record<string, string> = {
    draft: 'info', submitted: 'warning', appraising: 'primary',
    approved: 'success', rejected: 'danger',
    executing: 'primary', completed: '', cancelled: 'info'
  }
  return map[s] || 'info'
}
const getStatusLabel = (s: string) => t(`assets.lifecycle.disposalRequest.status.${s}`) || s

const columns: TableColumn[] = [
  { prop: 'requestNo', label: t('assets.lifecycle.disposalRequest.columns.requestNo'), width: 160 },
  { prop: 'requesterDisplay', label: t('assets.lifecycle.disposalRequest.columns.requesterDisplay'), width: 100 },
  { prop: 'disposalReason', label: t('assets.lifecycle.disposalRequest.columns.disposalReason'), minWidth: 180 },
  { prop: 'status', label: t('assets.lifecycle.disposalRequest.columns.status'), width: 110, slot: 'status' },
  { prop: 'createdAt', label: t('assets.lifecycle.disposalRequest.columns.createdAt'), width: 160 }
]

const handleCreate = () => router.push('/assets/lifecycle/disposal-requests/create')
const handleView = (row: any) => router.push(`/assets/lifecycle/disposal-requests/${row.id}`)

const handleSubmit = async (row: any) => {
  try {
    await ElMessageBox.confirm(
      t('assets.lifecycle.disposalRequest.actions.submit'),
      t('common.messages.confirmTitle'),
      { type: 'info' }
    )
    await disposalRequestApi.submit(row.id)
    ElMessage.success(t('assets.lifecycle.disposalRequest.messages.submitSuccess'))
    listRef.value?.refresh()
  } catch { /* user cancelled */ }
}

const handleCancel = async (row: any) => {
  try {
    await ElMessageBox.confirm(
      t('assets.lifecycle.disposalRequest.messages.cancelConfirm'),
      t('common.messages.confirmTitle'),
      { type: 'warning' }
    )
    await disposalRequestApi.cancel(row.id)
    ElMessage.success(t('assets.lifecycle.disposalRequest.messages.cancelSuccess'))
    listRef.value?.refresh()
  } catch { /* user cancelled */ }
}
</script>
