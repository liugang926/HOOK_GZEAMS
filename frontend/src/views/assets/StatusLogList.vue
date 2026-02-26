<template>
  <div class="status-log-list">
    <BaseListPage
      ref="listRef"
      :title="t('assets.statusLog.title')"
      :search-fields="searchFields"
      :table-columns="columns"
      :api="fetchList"
    >
      <template #search-assetId="{ form }">
        <el-select
          v-model="form.assetId"
          filterable
          remote
          clearable
          :placeholder="t('assets.statusLog.selectAsset')"
          :remote-method="searchAssets"
          :loading="assetSearchLoading"
        >
          <el-option
            v-for="asset in assetOptions"
            :key="asset.id"
            :label="`${asset.code} - ${asset.name}`"
            :value="asset.id"
          />
        </el-select>
      </template>

      <template #actions="{ row }">
        <el-button
          link
          type="primary"
          @click.stop="handleView(row)"
        >
          {{ t('common.actions.detail') }}
        </el-button>
      </template>
    </BaseListPage>

    <!-- Detail Dialog -->
    <el-dialog
      v-model="detailDialogVisible"
      :title="$t('assets.statusLog.detailTitle')"
      width="700px"
    >
      <el-descriptions
        v-if="currentLog"
        :column="2"
        border
      >
        <el-descriptions-item :label="$t('assets.statusLog.assetCode')">
          {{ currentLog.asset?.code }}
        </el-descriptions-item>
        <el-descriptions-item :label="$t('assets.statusLog.assetName')">
          {{ currentLog.asset?.name }}
        </el-descriptions-item>
        <el-descriptions-item :label="$t('assets.statusLog.statusChange')">
          <el-tag :type="getChangeTypeColor(currentLog.changeType)">
            {{ getChangeTypeLabel(currentLog.changeType) }}
          </el-tag>
        </el-descriptions-item>
        <el-descriptions-item :label="$t('assets.statusLog.operationTime')">
          {{ currentLog.operationTime }}
        </el-descriptions-item>
        <el-descriptions-item :label="$t('assets.statusLog.previousStatus')">
          {{ currentLog.fromStatus ? getStatusLabel(currentLog.fromStatus) : '-' }}
        </el-descriptions-item>
        <el-descriptions-item :label="$t('assets.statusLog.newStatus')">
          {{ currentLog.toStatus ? getStatusLabel(currentLog.toStatus) : '-' }}
        </el-descriptions-item>
        <el-descriptions-item :label="$t('assets.statusLog.operator')">
          {{ currentLog.operator?.realName }}
        </el-descriptions-item>
        <el-descriptions-item :label="$t('assets.statusLog.relatedBusiness')">
          {{ currentLog.relatedBusinessType ? getBusinessTypeLabel(currentLog.relatedBusinessType) : '-' }}
        </el-descriptions-item>
        <el-descriptions-item
          :label="$t('assets.statusLog.relatedNo')"
          :span="2"
        >
          {{ currentLog.relatedBusinessNo || '-' }}
        </el-descriptions-item>
        <el-descriptions-item :label="$t('assets.statusLog.ipAddress')">
          {{ currentLog.ipAddress || '-' }}
        </el-descriptions-item>
        <el-descriptions-item :label="$t('assets.statusLog.userAgent')">
          {{ currentLog.userAgent || '-' }}
        </el-descriptions-item>
        <el-descriptions-item
          :label="$t('assets.statusLog.remark')"
          :span="2"
        >
          {{ currentLog.remark || '-' }}
        </el-descriptions-item>
      </el-descriptions>
      <template #footer>
        <el-button @click="detailDialogVisible = false">
          {{ $t('common.actions.close') }}
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { ElMessage } from 'element-plus'
import { useI18n } from 'vue-i18n'
import BaseListPage from '@/components/common/BaseListPage.vue'
import type { TableColumn, SearchField } from '@/types/common'
import { getStatusLogList } from '@/api/assets/statusLogs'
import { getAssets } from '@/api/assets'

const { t } = useI18n()

const listRef = ref()
const assetSearchLoading = ref(false)
const assetOptions = ref<any[]>([])
const detailDialogVisible = ref(false)
const currentLog = ref<any>(null)

const getChangeTypeColor = (type: string) => {
  const map: Record<string, string> = {
    inbound: 'success',
    pickup: 'warning',
    transfer: 'primary',
    return: 'info',
    loan: 'warning',
    loan_return: 'success',
    disposal: 'danger',
    inventory: 'primary',
    maintenance: 'warning'
  }
  return map[type] || ''
}

const getChangeTypeLabel = (type: string) => {
  const map: Record<string, string> = {
    inbound: t('assets.statusLog.changeTypes.inbound'),
    pickup: t('assets.statusLog.changeTypes.pickup'),
    transfer: t('assets.statusLog.changeTypes.transfer'),
    return: t('assets.statusLog.changeTypes.return'),
    loan: t('assets.statusLog.changeTypes.loan'),
    loan_return: t('assets.statusLog.changeTypes.loanReturn'),
    disposal: t('assets.statusLog.changeTypes.disposal'),
    inventory: t('assets.statusLog.changeTypes.inventory'),
    maintenance: t('assets.statusLog.changeTypes.maintenance')
  }
  return map[type] || type
}

const getStatusLabel = (status: string) => {
  const map: Record<string, string> = {
    idle: t('assets.statusLog.assetStatus.idle'),
    in_use: t('assets.statusLog.assetStatus.inUse'),
    pickup_pending: t('assets.statusLog.assetStatus.pickupPending'),
    transfer_pending: t('assets.statusLog.assetStatus.transferPending'),
    return_pending: t('assets.statusLog.assetStatus.returnPending'),
    on_loan: t('assets.statusLog.assetStatus.onLoan'),
    maintenance: t('assets.statusLog.assetStatus.maintenance'),
    disposal: t('assets.statusLog.assetStatus.disposal'),
    lost: t('assets.statusLog.assetStatus.lost')
  }
  return map[status] || status
}

const getBusinessTypeLabel = (type: string) => {
  const map: Record<string, string> = {
    pickup: t('assets.statusLog.businessTypes.pickup'),
    transfer: t('assets.statusLog.businessTypes.transfer'),
    return: t('assets.statusLog.businessTypes.return'),
    loan: t('assets.statusLog.businessTypes.loan'),
    inventory: t('assets.statusLog.businessTypes.inventory'),
    maintenance: t('assets.statusLog.businessTypes.maintenance')
  }
  return map[type] || type
}

const searchAssets = async (query: string) => {
  if (!query) {
    assetOptions.value = []
    return
  }
  assetSearchLoading.value = true
  try {
    const res = await getAssets({ search: query, page_size: 20 }) as any
    assetOptions.value = res.results || res.items || []
  } finally {
    assetSearchLoading.value = false
  }
}

const searchFields = computed<SearchField[]>(() => [
  {
    prop: 'search',
    label: t('assets.search.keyword'),
    type: 'text',
    placeholder: t('assets.search.keywordPlaceholder')
  },
  {
    prop: 'assetId',
    label: t('assets.fields.assetName'),
    type: 'slot'
  },
  {
    prop: 'changeType',
    label: t('assets.statusLog.statusChange'),
    type: 'select',
    placeholder: t('assets.statusLog.allTypes'),
    options: [
      { label: t('assets.statusLog.changeTypes.inbound'), value: 'inbound' },
      { label: t('assets.statusLog.changeTypes.pickup'), value: 'pickup' },
      { label: t('assets.statusLog.changeTypes.transfer'), value: 'transfer' },
      { label: t('assets.statusLog.changeTypes.return'), value: 'return' },
      { label: t('assets.statusLog.changeTypes.loan'), value: 'loan' },
      { label: t('assets.statusLog.changeTypes.loanReturn'), value: 'loan_return' },
      { label: t('assets.statusLog.changeTypes.disposal'), value: 'disposal' },
      { label: t('assets.statusLog.changeTypes.inventory'), value: 'inventory' },
      { label: t('assets.statusLog.changeTypes.maintenance'), value: 'maintenance' }
    ]
  },
  {
    prop: 'operationTime',
    label: t('assets.statusLog.dateRange'),
    type: 'dateRange'
  }
])

const columns = computed<TableColumn[]>(() => [
  { prop: 'asset.code', label: t('assets.statusLog.assetCode'), width: 140 },
  { prop: 'asset.name', label: t('assets.statusLog.assetName'), minWidth: 160 },
  {
    prop: 'changeType',
    label: t('assets.statusLog.statusChange'),
    width: 120,
    align: 'center',
    tagType: (row: any) => getChangeTypeColor(row.changeType),
    format: (_v: any, row: any) => getChangeTypeLabel(row.changeType)
  },
  {
    prop: 'fromStatus',
    label: t('assets.statusLog.previousStatus'),
    width: 120,
    format: (_v: any, row: any) => (row.fromStatus ? getStatusLabel(row.fromStatus) : '-')
  },
  {
    prop: 'toStatus',
    label: t('assets.statusLog.newStatus'),
    width: 120,
    format: (_v: any, row: any) => (row.toStatus ? getStatusLabel(row.toStatus) : '-')
  },
  { prop: 'operator.realName', label: t('assets.statusLog.operator'), width: 120 },
  { prop: 'operationTime', label: t('assets.statusLog.operationTime'), width: 160 },
  {
    prop: 'relatedBusinessType',
    label: t('assets.statusLog.relatedBusiness'),
    width: 160,
    format: (_v: any, row: any) => (row.relatedBusinessType ? getBusinessTypeLabel(row.relatedBusinessType) : '-')
  },
  { prop: 'remark', label: t('assets.statusLog.remark'), minWidth: 200 },
  { prop: 'actions', label: t('common.table.operations'), width: 120, fixed: 'right', slot: true }
])

const fetchList = async (params: any) => {
  try {
    const nextParams = { ...params, page_size: params.pageSize }

    if (nextParams.assetId) {
      nextParams.asset = nextParams.assetId
      delete nextParams.assetId
    }

    if (Array.isArray(nextParams.operationTime) && nextParams.operationTime.length === 2) {
      nextParams.operationTimeFrom = nextParams.operationTime[0]
      nextParams.operationTimeTo = nextParams.operationTime[1]
      delete nextParams.operationTime
    }

    const res = await getStatusLogList(nextParams) as any
    return {
      results: res.results || res.items || [],
      count: res.count || res.total || 0
    }
  } catch (error) {
    ElMessage.error(t('common.messages.loadFailed'))
    return { results: [], count: 0 }
  }
}

const handleView = (row: any) => {
  currentLog.value = row
  detailDialogVisible.value = true
}
</script>

<style scoped>
.status-log-list {
  padding: 20px;
}
</style>
