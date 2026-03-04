<template>
  <div class="integration-config-list">
    <div class="page-header">
      <h3>{{ t('integration.configList.title') }}</h3>
      <el-button
        type="primary"
        @click="handleCreate"
      >
        {{ t('integration.actions.newIntegration') }}
      </el-button>
    </div>

    <IntegrationStatsCards :stats="stats" />

    <IntegrationConfigFilterBar
      :system-type="filterForm.systemType"
      :is-enabled="filterForm.isEnabled"
      :health-status="filterForm.healthStatus"
      @update:system-type="filterForm.systemType = $event"
      @update:is-enabled="filterForm.isEnabled = $event"
      @update:health-status="filterForm.healthStatus = $event"
      @search="fetchData"
      @reset="handleFilterReset"
    />

    <IntegrationConfigTable
      :loading="loading"
      :table-data="tableData"
      :testing="testing"
      :syncing="syncing"
      :current-page="pagination.page"
      :page-size="pagination.pageSize"
      :total="pagination.total"
      @test="handleTest"
      @sync="handleSync"
      @logs="handleViewLogs"
      @edit="handleEdit"
      @delete="handleDelete"
      @page-change="handlePageChange"
      @page-size-change="handlePageSizeChange"
    />

    <IntegrationConfigFormDialog
      v-model="dialogVisible"
      :is-edit="isEdit"
      :submitting="submitting"
      :form-data="formData"
      @submit="handleSubmit"
    />

    <IntegrationLogsDrawer
      v-model="logsDrawerVisible"
      :current-config="currentConfig"
      :logs-loading="logsLoading"
      :logs="logs"
      :page="logsPagination.page"
      :page-size="logsPagination.pageSize"
      :total="logsPagination.total"
      @refresh="fetchLogs"
      @view-detail="handleViewLogDetail"
      @page-change="handleLogsPageChange"
      @page-size-change="handleLogsPageSizeChange"
    />

    <IntegrationLogDetailDialog
      v-model="logDetailVisible"
      :current-log="currentLog"
    />
  </div>
</template>

<script setup lang="ts">
import { onMounted } from 'vue'
import { useI18n } from 'vue-i18n'
import IntegrationConfigFilterBar from './components/IntegrationConfigFilterBar.vue'
import IntegrationConfigFormDialog from './components/IntegrationConfigFormDialog.vue'
import IntegrationLogDetailDialog from './components/IntegrationLogDetailDialog.vue'
import IntegrationLogsDrawer from './components/IntegrationLogsDrawer.vue'
import IntegrationStatsCards from './components/IntegrationStatsCards.vue'
import IntegrationConfigTable from './components/IntegrationConfigTable.vue'
import { useIntegrationConfigList } from './composables/useIntegrationConfigList'

const { t } = useI18n()

const {
  loading,
  tableData,
  dialogVisible,
  logsDrawerVisible,
  logDetailVisible,
  submitting,
  testing,
  syncing,
  logsLoading,
  currentConfig,
  currentLog,
  logs,
  filterForm,
  pagination,
  logsPagination,
  stats,
  isEdit,
  formData,
  fetchData,
  handleFilterReset,
  handlePageChange,
  handlePageSizeChange,
  handleCreate,
  handleEdit,
  handleSubmit,
  handleDelete,
  handleTest,
  handleSync,
  handleViewLogs,
  fetchLogs,
  handleLogsPageChange,
  handleLogsPageSizeChange,
  handleViewLogDetail
} = useIntegrationConfigList()

onMounted(() => {
  void fetchData()
})
</script>

<style scoped>
.integration-config-list {
  padding: 20px;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.page-header h3 {
  margin: 0;
  font-size: 18px;
}

</style>
