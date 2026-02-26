<template>
  <div class="pickup-list page-container">
    <BaseListPage
      ref="listRef"
      :title="$t('assets.pickup.listTitle')"
      object-code="AssetPickup"
      :search-fields="searchFields"
      :table-columns="columns"
      :api="fetchPickupList"
    >
      <template #toolbar>
        <el-button
          type="primary"
          :icon="Plus"
          @click="handleCreate"
        >
          {{ $t('assets.pickup.createButton') }}
        </el-button>
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
          v-if="['draft', 'pending'].includes(row.status)"
          link
          type="primary"
          @click="handleEdit(row)"
        >
          {{ $t('common.actions.edit') }}
        </el-button>
        <el-button
          v-if="['draft', 'pending'].includes(row.status)"
          link
          type="warning"
          @click="handleCancel(row)"
        >
          {{ $t('common.actions.cancel') }}
        </el-button>
      </template>
    </BaseListPage>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { Plus } from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { getPickupList, cancelPickup } from '@/api/assets/pickup'
import BaseListPage from '@/components/common/BaseListPage.vue'
import type { TableColumn, SearchField } from '@/types/common'

const router = useRouter()
const { t } = useI18n()
const listRef = ref()

// API Wrapper to adapt to BaseListPage expectation if needed
// Assuming BaseListPage passes { page, pageSize, ...filters } and expects { results, count }
const fetchPickupList = async (params: any) => {
  // Convert standard params to what getPickupList expects (snake_case)
  const apiParams = {
    ...params,
    page_size: params.pageSize
  }
  const res = await getPickupList(apiParams) as any
  return {
    results: res.items || res.results || [],
    count: res.total || res.count || 0
  }
}

const searchFields: SearchField[] = [
  {
    prop: 'status',
    label: t('assets.search.status'),
    type: 'select',
    options: [
      { label: t('assets.status.draft'), value: 'draft' },
      { label: t('assets.status.pending'), value: 'pending' },
      { label: t('assets.status.approved'), value: 'approved' },
      { label: t('assets.status.rejected'), value: 'rejected' },
      { label: t('assets.status.completed'), value: 'completed' }
    ]
  },
  {
    prop: 'search',
    label: t('common.actions.search'),
    type: 'text',
    placeholder: t('assets.search.keywordPlaceholder')
  }
]

const columns: TableColumn[] = [
  { prop: 'pickupNo', label: t('assets.pickup.columns.pickupNo'), width: 150 },
  { prop: 'applicant.realName', label: t('assets.pickup.columns.applicant'), width: 100 },
  { prop: 'department.name', label: t('assets.pickup.columns.department'), width: 120 },
  { prop: 'pickupDate', label: t('assets.pickup.columns.pickupDate'), width: 110 },
  { prop: 'status', label: t('assets.pickup.columns.status'), width: 100, tagType: (row: any) => getStatusType(row.status), format: (value: any, row: any) => row?.statusLabel || getStatusLabel(value) },
  { prop: 'itemsCount', label: t('assets.pickup.columns.assetCount'), width: 100, align: 'center' },
  { prop: 'createdAt', label: t('assets.pickup.columns.createdAt'), width: 160 }
]

const getStatusType = (status: string) => {
  const map: any = {
    draft: 'info',
    pending: 'warning',
    approved: 'success',
    rejected: 'danger',
    completed: 'success',
    cancelled: 'info'
  }
  return map[status] || 'info'
}

const getStatusLabel = (status: string) => {
  const map: any = {
    draft: t('assets.status.draft'),
    pending: t('assets.status.pending'),
    approved: t('assets.status.approved'),
    rejected: t('assets.status.rejected'),
    completed: t('assets.status.completed'),
    cancelled: t('assets.status.cancelled')
  }
  return map[status] || status
}

const handleCreate = () => {
  router.push('/assets/operations/pickup/create')
}

const handleView = (row: any) => {
  router.push(`/assets/operations/pickup/${row.id}`)
}

const handleEdit = (row: any) => {
  router.push(`/assets/operations/pickup/${row.id}/edit`)
}

const handleCancel = async (row: any) => {
  try {
    await ElMessageBox.confirm(t('assets.pickup.messages.confirmCancel'), t('common.messages.confirmTitle'), { type: 'warning' })
    await cancelPickup(row.id)
    ElMessage.success(t('common.messages.cancelSuccess'))
    listRef.value?.refresh()
  } catch {
    // cancelled
  }
}
</script>

<style scoped lang="scss">
.pickup-list {
  // Using global styles now, minimal local overrides
}
</style>
