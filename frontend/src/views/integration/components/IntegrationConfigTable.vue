<template>
  <el-table
    v-loading="loading"
    :data="tableData"
    border
    stripe
    style="width: 100%"
  >
    <el-table-column
      prop="systemName"
      :label="t('integration.configList.table.name')"
      min-width="150"
    />
    <el-table-column
      :label="t('integration.configList.table.systemType')"
      width="120"
    >
      <template #default="{ row }">
        <el-tag :type="getSystemTypeTagType(row.systemType)">
          {{ getSystemTypeLabel(row.systemType, t) }}
        </el-tag>
      </template>
    </el-table-column>
    <el-table-column
      :label="t('integration.configList.table.healthStatus')"
      width="100"
    >
      <template #default="{ row }">
        <el-tag :type="getHealthStatusTagType(row.healthStatus)">
          {{ getHealthStatusLabel(row.healthStatus, t) }}
        </el-tag>
      </template>
    </el-table-column>
    <el-table-column
      :label="t('integration.configList.table.status')"
      width="100"
    >
      <template #default="{ row }">
        <el-tag :type="getEnabledStatusTagType(row.isEnabled)">
          {{ getEnabledStatusLabel(row.isEnabled, t) }}
        </el-tag>
      </template>
    </el-table-column>
    <el-table-column
      :label="t('integration.configList.table.modules')"
      width="200"
    >
      <template #default="{ row }">
        <el-tag
          v-for="module in row.enabledModules"
          :key="module"
          size="small"
          style="margin-right: 5px; margin-bottom: 3px"
        >
          {{ getModuleLabel(module, t) }}
        </el-tag>
      </template>
    </el-table-column>
    <el-table-column
      prop="lastSyncAt"
      :label="t('integration.configList.table.lastSync')"
      width="170"
    >
      <template #default="{ row }">
        {{ row.lastSyncAt ? formatDate(row.lastSyncAt) : '-' }}
      </template>
    </el-table-column>
    <el-table-column
      :label="t('integration.configList.table.lastSyncStatus')"
      width="100"
    >
      <template #default="{ row }">
        <el-tag
          v-if="row.lastSyncStatus"
          :type="getSyncStatusTagType(row.lastSyncStatus)"
          size="small"
        >
          {{ getSyncStatusLabel(row.lastSyncStatus, t) }}
        </el-tag>
        <span v-else>-</span>
      </template>
    </el-table-column>
    <el-table-column
      :label="t('integration.configList.table.actions')"
      width="320"
      fixed="right"
    >
      <template #default="{ row }">
        <el-button
          link
          type="primary"
          :loading="testing[row.id]"
          @click="emit('test', row)"
        >
          {{ t('integration.actions.testConnection') }}
        </el-button>
        <el-button
          link
          type="primary"
          :loading="syncing[row.id]"
          @click="emit('sync', row)"
        >
          {{ t('integration.actions.syncNow') }}
        </el-button>
        <el-button
          link
          type="primary"
          @click="emit('logs', row)"
        >
          {{ t('integration.actions.logs') }}
        </el-button>
        <el-button
          link
          type="primary"
          @click="emit('edit', row)"
        >
          {{ t('integration.actions.edit') }}
        </el-button>
        <el-popconfirm
          :title="t('integration.configList.deleteConfirm')"
          @confirm="emit('delete', row)"
        >
          <template #reference>
            <el-button
              link
              type="danger"
            >
              {{ t('integration.actions.delete') }}
            </el-button>
          </template>
        </el-popconfirm>
      </template>
    </el-table-column>
  </el-table>

  <div class="pagination-footer">
    <el-pagination
      :current-page="currentPage"
      :page-size="pageSize"
      :total="total"
      :page-sizes="[10, 20, 50, 100]"
      layout="total, sizes, prev, pager, next, jumper"
      @current-change="emit('page-change', $event)"
      @size-change="emit('page-size-change', $event)"
    />
  </div>
</template>

<script setup lang="ts">
import { useI18n } from 'vue-i18n'
import type { IntegrationConfig } from '@/types/integration'
import {
  formatDate,
  getEnabledStatusLabel,
  getEnabledStatusTagType,
  getHealthStatusLabel,
  getHealthStatusTagType,
  getModuleLabel,
  getSyncStatusLabel,
  getSyncStatusTagType,
  getSystemTypeLabel,
  getSystemTypeTagType
} from '@/views/integration/integrationConfig.constants'

defineProps<{
  loading: boolean
  tableData: IntegrationConfig[]
  testing: Record<string, boolean>
  syncing: Record<string, boolean>
  currentPage: number
  pageSize: number
  total: number
}>()

const emit = defineEmits<{
  test: [row: IntegrationConfig]
  sync: [row: IntegrationConfig]
  logs: [row: IntegrationConfig]
  edit: [row: IntegrationConfig]
  delete: [row: IntegrationConfig]
  'page-change': [page: number]
  'page-size-change': [pageSize: number]
}>()

const { t } = useI18n()
</script>

<style scoped>
.pagination-footer {
  margin-top: 20px;
  display: flex;
  justify-content: flex-end;
}
</style>
