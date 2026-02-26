<template>
  <div class="maintenance-list">
    <BaseListPage
      ref="listRef"
      :title="t('itAssets.maintenance.title')"
      :search-fields="searchFields"
      :table-columns="columns"
      :api="fetchList"
      @row-click="handleView"
    >
      <template #toolbar>
        <el-button
          type="primary"
          @click="handleCreate"
        >
          {{ t('itAssets.common.addRecord') }}
        </el-button>
      </template>

      <template #actions="{ row }">
        <el-button
          link
          type="primary"
          @click.stop="handleView(row)"
        >
          {{ t('itAssets.actions.view') }}
        </el-button>
        <el-button
          link
          type="primary"
          @click.stop="handleEdit(row)"
        >
          {{ t('itAssets.actions.edit') }}
        </el-button>
        <el-popconfirm
          :title="t('itAssets.messages.deleteRecordConfirm')"
          @confirm="handleDelete(row)"
        >
          <template #reference>
            <el-button
              link
              type="danger"
              @click.stop
            >
              {{ t('itAssets.actions.delete') }}
            </el-button>
          </template>
        </el-popconfirm>
      </template>
    </BaseListPage>

    <!-- Maintenance Form Dialog -->
    <MaintenanceForm
      v-model:visible="dialogVisible"
      :data="currentRow"
      @success="handleRefresh"
    />

    <!-- Detail Drawer -->
    <el-drawer
      v-model="detailDrawerVisible"
      :title="$t('itAssets.detail.title')"
      size="600px"
    >
      <div
        v-if="currentRow"
        class="detail-content"
      >
        <el-descriptions
          :column="2"
          border
        >
          <el-descriptions-item :label="$t('itAssets.common.asset')">
            {{ currentRow.asset_code }} - {{ currentRow.asset_name }}
          </el-descriptions-item>
          <el-descriptions-item :label="$t('itAssets.maintenance.type')">
            <el-tag :type="getMaintenanceTypeColor(currentRow.maintenance_type)">
              {{ $t('itAssets.maintenance.types.' + currentRow.maintenance_type) }}
            </el-tag>
          </el-descriptions-item>
          <el-descriptions-item
            :label="$t('itAssets.common.title')"
            :span="2"
          >
            {{ currentRow.title }}
          </el-descriptions-item>
          <el-descriptions-item :label="$t('itAssets.common.date')">
            {{ currentRow.maintenance_date }}
          </el-descriptions-item>
          <el-descriptions-item :label="$t('itAssets.common.cost')">
            {{ currentRow.cost ? `$${currentRow.cost}` : '-' }}
          </el-descriptions-item>
          <el-descriptions-item :label="$t('itAssets.common.vendor')">
            {{ currentRow.vendor || '-' }}
          </el-descriptions-item>
          <el-descriptions-item :label="$t('itAssets.common.performedBy')">
            {{ currentRow.performed_by_username || '-' }}
          </el-descriptions-item>
        </el-descriptions>

        <div
          v-if="currentRow.description"
          class="section-title"
        >
          {{ $t('itAssets.common.description') }}
        </div>
        <div
          v-if="currentRow.description"
          class="description-text"
        >
          {{ currentRow.description }}
        </div>

        <div
          v-if="currentRow.notes"
          class="section-title"
        >
          {{ $t('itAssets.common.notes') }}
        </div>
        <div
          v-if="currentRow.notes"
          class="description-text"
        >
          {{ currentRow.notes }}
        </div>
      </div>
    </el-drawer>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { ElMessage } from 'element-plus'
import { useI18n } from 'vue-i18n'
import type { ITMaintenanceRecord } from '@/api/itAssets'
import { itMaintenanceApi } from '@/api/itAssets'
import BaseListPage from '@/components/common/BaseListPage.vue'
import type { TableColumn, SearchField } from '@/types/common'
import MaintenanceForm from './components/MaintenanceForm.vue'

const { t } = useI18n()

const listRef = ref()
const dialogVisible = ref(false)
const detailDrawerVisible = ref(false)
const currentRow = ref<ITMaintenanceRecord | null>(null)

const getMaintenanceTypeColor = (type: string) => {
  const colorMap: Record<string, string> = {
    preventive: 'success',
    corrective: 'warning',
    upgrade: 'primary',
    replacement: 'danger',
    inspection: 'info',
    cleaning: '',
    other: ''
  }
  return colorMap[type] || ''
}

const searchFields = computed<SearchField[]>(() => [
  {
    prop: 'search',
    label: t('itAssets.filters.search'),
    type: 'text',
    placeholder: t('itAssets.common.searchMaintenancePlaceholder')
  },
  {
    prop: 'maintenance_type',
    label: t('itAssets.maintenance.type'),
    type: 'select',
    placeholder: t('itAssets.maintenance.allTypes'),
    options: [
      { label: t('itAssets.maintenance.types.preventive'), value: 'preventive' },
      { label: t('itAssets.maintenance.types.corrective'), value: 'corrective' },
      { label: t('itAssets.maintenance.types.upgrade'), value: 'upgrade' },
      { label: t('itAssets.maintenance.types.replacement'), value: 'replacement' },
      { label: t('itAssets.maintenance.types.inspection'), value: 'inspection' },
      { label: t('itAssets.maintenance.types.cleaning'), value: 'cleaning' },
      { label: t('itAssets.maintenance.types.other'), value: 'other' }
    ]
  },
  {
    prop: 'maintenance_date',
    label: t('itAssets.filters.dateRange'),
    type: 'dateRange'
  }
])

const columns = computed<TableColumn[]>(() => [
  { prop: 'asset_code', label: t('itAssets.common.asset'), width: 140 },
  {
    prop: 'maintenance_type',
    label: t('itAssets.maintenance.type'),
    width: 120,
    tagType: (row: ITMaintenanceRecord) => getMaintenanceTypeColor(row.maintenance_type),
    format: (_v: any, row: ITMaintenanceRecord) => t(`itAssets.maintenance.types.${row.maintenance_type}`)
  },
  { prop: 'title', label: t('itAssets.common.title'), minWidth: 200 },
  { prop: 'maintenance_date', label: t('itAssets.common.date'), width: 120 },
  {
    prop: 'cost',
    label: t('itAssets.common.cost'),
    width: 100,
    align: 'right',
    format: (value: any) => (value !== undefined && value !== null && value !== '' ? `$${value}` : '-')
  },
  { prop: 'vendor', label: t('itAssets.common.vendor'), minWidth: 150 },
  { prop: 'performed_by_username', label: t('itAssets.common.performedBy'), width: 120 },
  { prop: 'actions', label: t('itAssets.columns.actions'), width: 160, fixed: 'right', slot: true }
])

const fetchList = async (params: any) => {
  try {
    const nextParams = { ...params }
    if (Array.isArray(nextParams.maintenance_date) && nextParams.maintenance_date.length === 2) {
      nextParams.maintenance_date_from = nextParams.maintenance_date[0]
      nextParams.maintenance_date_to = nextParams.maintenance_date[1]
      delete nextParams.maintenance_date
    }

    const res = await itMaintenanceApi.list({
      ...nextParams,
      page_size: nextParams.pageSize
    }) as any
    return {
      results: res.results || res.items || [],
      count: res.count || res.total || 0
    }
  } catch (error) {
    ElMessage.error(t('itAssets.messages.loadMaintenanceFailed'))
    return { results: [], count: 0 }
  }
}

const handleRefresh = () => {
  listRef.value?.refresh()
}

const handleCreate = () => {
  currentRow.value = null
  dialogVisible.value = true
}

const handleView = (row: ITMaintenanceRecord) => {
  currentRow.value = row
  detailDrawerVisible.value = true
}

const handleEdit = (row: ITMaintenanceRecord) => {
  currentRow.value = row
  dialogVisible.value = true
}

const handleDelete = async (row: ITMaintenanceRecord) => {
  try {
    await itMaintenanceApi.delete(row.id)
    ElMessage.success(t('itAssets.messages.deleteSuccess'))
    handleRefresh()
  } catch (error: any) {
    if (error !== 'cancel') {
      ElMessage.error(t('itAssets.messages.deleteFailed'))
    }
  }
}
</script>

<style scoped>
.maintenance-list {
  padding: 20px;
}

.detail-content .section-title {
  margin: 20px 0 10px;
  font-size: 14px;
  font-weight: 600;
  color: #303133;
  border-left: 3px solid #409eff;
  padding-left: 10px;
}

.detail-content .description-text {
  padding: 10px;
  background: #f5f7fa;
  border-radius: 4px;
  white-space: pre-wrap;
  line-height: 1.6;
}
</style>
