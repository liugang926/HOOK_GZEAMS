<template>
  <div class="transfer-list">
    <BaseListPage
      ref="listRef"
      :title="$t('assets.transfer.listTitle')"
      object-code="AssetTransfer"
      :search-fields="searchFields"
      :table-columns="columns"
      :api="fetchTransferList"
    >
      <template #toolbar>
        <el-button
          type="primary"
          :icon="Plus"
          @click="handleCreate"
        >
          {{ $t('assets.transfer.createButton') }}
        </el-button>
      </template>

      <template #actions="{ row }">
        <div v-if="row.status === 'pending'">
          <el-button
            link
            type="success"
            @click="handleApprove(row)"
          >
            {{ $t('common.actions.confirm') }}
          </el-button>
          <el-button
            link
            type="danger"
            @click="handleReject(row)"
          >
            {{ $t('common.actions.reject') }}
          </el-button>
        </div>
      </template>
    </BaseListPage>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { Plus } from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import BaseListPage from '@/components/common/BaseListPage.vue'
import type { TableColumn, SearchField } from '@/types/common'
import { transferApi } from '@/api/assets'

const router = useRouter()
const { t } = useI18n()
const listRef = ref()

const searchFields = computed<SearchField[]>(() => [
  {
    prop: 'status',
    label: t('assets.search.status'),
    type: 'select',
    options: [
      { label: t('assets.status.pending'), value: 'pending' },
      { label: t('assets.status.approved'), value: 'approved' },
      { label: t('assets.status.rejected'), value: 'rejected' }
    ]
  },
  {
    prop: 'search',
    label: t('common.actions.search'),
    type: 'text',
    placeholder: t('assets.search.keywordPlaceholder')
  }
])

const columns = computed<TableColumn[]>(() => [
  { prop: 'transferNo', label: t('assets.transfer.columns.transferNo'), width: 150 },
  { prop: 'asset.name', label: t('assets.transfer.columns.assetName'), width: 120 },
  { prop: 'fromLocation.name', label: t('assets.transfer.columns.fromLocation'), width: 120 },
  { prop: 'toLocation.name', label: t('assets.transfer.columns.toLocation'), width: 120 },
  { prop: 'applicant.realName', label: t('assets.transfer.columns.applicant'), width: 100 },
  { prop: 'createdAt', label: t('assets.transfer.columns.applyTime'), width: 160, dateFormatter: 'YYYY-MM-DD HH:mm:ss' },
  { prop: 'status', label: t('assets.transfer.columns.status'), width: 100, tagType: (row: any) => getStatusType(row.status), format: (value: any, row: any) => row?.statusLabel || getStatusLabel(value) },
  { prop: 'actions', label: t('common.labels.operation'), width: 200, slot: true, fixed: 'right' }
])

const getStatusType = (status: string) => {
  const map: any = { pending: 'warning', approved: 'success', rejected: 'danger' }
  return map[status] || 'info'
}

const getStatusLabel = (status: string) => {
  const map: any = { 
    pending: t('assets.status.pending'), 
    approved: t('assets.status.approved'), 
    rejected: t('assets.status.rejected') 
  }
  return map[status] || status
}

const fetchTransferList = async (params: any) => {
  const res = await transferApi.list({
    ...params,
    page_size: params.pageSize
  }) as any
  return {
    results: res.items || res.results || [],
    count: res.total || res.count || 0
  }
}

const handleCreate = () => {
  router.push('/assets/operations/transfer/create')
}

const handleApprove = async (row: any) => {
  try {
    await ElMessageBox.confirm(t('assets.transfer.messages.confirmApprove'), t('common.messages.confirmTitle'), { type: 'success' })
    await transferApi.approve(row.id)
    ElMessage.success(t('assets.transfer.messages.approveSuccess'))
    listRef.value?.refresh()
  } catch (error) {
    if (error && error !== 'cancel') {
      // ignore non-cancel errors here
    }
  }
}

const handleReject = async (row: any) => {
  try {
    const { value } = await ElMessageBox.prompt(t('assets.transfer.messages.confirmReject'), t('common.actions.reject'), {
      inputPattern: /\S+/,
      inputErrorMessage: t('assets.transfer.messages.rejectReasonRequired')
    })
    await transferApi.reject(row.id, value)
    ElMessage.success(t('assets.transfer.messages.rejectSuccess'))
    listRef.value?.refresh()
  } catch (error) {
    if (error && error !== 'cancel') {
      // ignore non-cancel errors here
    }
  }
}
</script>

<style scoped>
.transfer-list { padding: 20px; }
</style>
