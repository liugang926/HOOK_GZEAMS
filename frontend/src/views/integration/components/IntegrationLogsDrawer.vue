<template>
  <el-drawer
    :model-value="modelValue"
    :title="t('integration.logs.drawerTitle')"
    size="800px"
    @update:model-value="emit('update:modelValue', $event)"
  >
    <div
      v-if="currentConfig"
      class="logs-content"
    >
      <div class="logs-header">
        <h4>{{ currentConfig.systemName }} - {{ t('integration.logs.shortTitle') }}</h4>
        <el-button
          type="primary"
          size="small"
          @click="emit('refresh')"
        >
          {{ t('integration.actions.refresh') }}
        </el-button>
      </div>

      <el-table
        v-loading="logsLoading"
        :data="logs"
        border
        stripe
        size="small"
        style="width: 100%"
      >
        <el-table-column
          prop="createdAt"
          :label="t('integration.logs.columns.time')"
          width="160"
        />
        <el-table-column
          prop="integrationType"
          :label="t('integration.logs.columns.type')"
          width="120"
        />
        <el-table-column
          prop="action"
          :label="t('integration.logs.columns.action')"
          width="100"
        >
          <template #default="{ row }">
            <el-tag
              size="small"
              :type="row.action === 'push' ? 'success' : 'warning'"
            >
              {{ row.action }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column
          prop="requestMethod"
          :label="t('integration.logs.columns.method')"
          width="80"
        />
        <el-table-column
          prop="statusCode"
          :label="t('integration.logs.columns.status')"
          width="80"
        >
          <template #default="{ row }">
            <el-tag
              v-if="row.statusCode"
              size="small"
              :type="row.statusCode < 300 ? 'success' : 'danger'"
            >
              {{ row.statusCode }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column
          :label="t('integration.logs.columns.success')"
          width="80"
        >
          <template #default="{ row }">
            <el-tag
              size="small"
              :type="row.success ? 'success' : 'danger'"
            >
              {{ row.success ? t('integration.common.yes') : t('integration.common.no') }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column
          prop="durationMs"
          :label="t('integration.logs.columns.duration')"
          width="90"
        >
          <template #default="{ row }">
            {{ row.durationMs ? `${row.durationMs}ms` : '-' }}
          </template>
        </el-table-column>
        <el-table-column
          :label="t('integration.logs.columns.actions')"
          width="80"
        >
          <template #default="{ row }">
            <el-button
              link
              type="primary"
              size="small"
              @click="emit('view-detail', row)"
            >
              {{ t('integration.actions.view') }}
            </el-button>
          </template>
        </el-table-column>
      </el-table>

      <div class="pagination-footer">
        <el-pagination
          :current-page="page"
          :page-size="pageSize"
          :total="total"
          :page-sizes="[10, 20, 50]"
          layout="total, sizes, prev, pager, next"
          @size-change="emit('page-size-change', $event)"
          @current-change="emit('page-change', $event)"
        />
      </div>
    </div>
  </el-drawer>
</template>

<script setup lang="ts">
import { useI18n } from 'vue-i18n'
import type { IntegrationConfig, IntegrationLog } from '@/types/integration'

withDefaults(defineProps<{
  modelValue: boolean
  currentConfig: IntegrationConfig | null
  logsLoading: boolean
  logs: IntegrationLog[]
  page: number
  pageSize: number
  total: number
}>(), {
  currentConfig: null,
  logs: () => []
})

const emit = defineEmits<{
  'update:modelValue': [value: boolean]
  refresh: []
  'view-detail': [log: IntegrationLog]
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

.logs-content {
  padding: 0 20px;
}

.logs-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.logs-header h4 {
  margin: 0;
}
</style>
