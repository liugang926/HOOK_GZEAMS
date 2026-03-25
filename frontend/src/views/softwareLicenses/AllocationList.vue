<!-- frontend/src/views/softwareLicenses/AllocationList.vue -->

<template>
  <BaseListPage
    :title="$t('softwareLicenses.allocations.title')"
    :api="licenseAllocationApi.list"
    :table-columns="columns"
    :search-fields="searchFields"
    @row-click="handleRowClick"
  >
    <template #toolbar>
      <el-button
        type="primary"
        @click="handleCreate"
      >
        <el-icon><Plus /></el-icon>
        {{ $t('softwareLicenses.allocations.add') }}
      </el-button>
    </template>
    <template #actions="{ row }">
      <el-button
        v-if="row.isActive"
        link
        type="warning"
        @click.stop="handleDeallocate(row)"
      >
        {{ $t('softwareLicenses.allocations.deallocate') }}
      </el-button>
      <el-text
        v-else
        type="info"
      >
        {{ $t('softwareLicenses.allocations.status.revoked') }}
      </el-text>
    </template>
  </BaseListPage>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { ElMessage, ElMessageBox } from 'element-plus'
import BaseListPage from '@/components/common/BaseListPage.vue'
import { licenseAllocationApi } from '@/api/softwareLicenses'
import type { TableColumn, SearchField } from '@/types/common'
import { Plus } from '@element-plus/icons-vue'

const router = useRouter()
const { t } = useI18n()

const columns = computed<TableColumn[]>(() => [
  { prop: 'softwareName', label: t('softwareLicenses.allocations.fields.software'), minWidth: 150 },
  { prop: 'licenseNo', label: t('softwareLicenses.allocations.fields.licenseNo'), width: 150 },
  { prop: 'assetCode', label: t('softwareLicenses.allocations.fields.assetCode'), width: 130 },
  { prop: 'assetName', label: t('softwareLicenses.allocations.fields.assetName'), minWidth: 150 },
  { prop: 'allocatedDate', label: t('softwareLicenses.allocations.fields.allocatedDate'), width: 120 },
  { prop: 'allocatedByName', label: t('softwareLicenses.allocations.fields.allocatedBy'), width: 100 },
  { prop: 'isActive', label: t('softwareLicenses.allocations.fields.status'), width: 100, tagType: (row: any) => (row.isActive ? 'success' : 'info'), format: (value: any) => (value ? t('softwareLicenses.allocations.status.allocated') : t('softwareLicenses.allocations.status.revoked')) },
  { prop: 'actions', label: t('common.labels.operation'), width: 120, slot: true, fixed: 'right' }
])

const searchFields = computed<SearchField[]>(() => [
  { prop: 'search', label: t('common.actions.search'), placeholder: t('softwareLicenses.allocations.fields.software') + '/' + t('softwareLicenses.allocations.fields.assetName') },
  { prop: 'isActive', label: t('softwareLicenses.allocations.fields.status'), type: 'select', options: [
    { label: t('softwareLicenses.allocations.status.allocated'), value: true },
    { label: t('softwareLicenses.allocations.status.revoked'), value: false }
  ]}
])

const handleRowClick = (row: any) => {
  router.push(`/software-licenses/allocations/${row.id}`)
}

const handleCreate = () => {
  router.push('/software-licenses/licenses')
}

const handleDeallocate = async (row: any) => {
  try {
    await ElMessageBox.confirm(
      t('softwareLicenses.allocations.messages.deallocateConfirm', { software: row.softwareName, asset: row.assetName }),
      t('common.messages.confirmTitle'),
      {
        confirmButtonText: t('common.actions.confirm'),
        cancelButtonText: t('common.actions.cancel'),
        type: 'warning'
      }
    )

    await licenseAllocationApi.deallocate(row.id)
    ElMessage.success(t('common.messages.operationSuccess'))
    // Refresh is handled by BaseListPage
    // Note: BaseListPage might need a way to trigger refresh manually if not handled via specialized event or ref
    window.dispatchEvent(new CustomEvent('refresh-base-list'))
  } catch (error: any) {
    if (error !== 'cancel') {
      ElMessage.error(error.message || t('common.messages.operationFailed'))
    }
  }
}
</script>

