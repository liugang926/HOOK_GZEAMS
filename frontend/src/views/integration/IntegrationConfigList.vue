<template>
  <div class="integration-config-list">
    <div class="page-header">
      <h3>{{ t('integration.configList.title') }}</h3>
      <el-button
        type="primary"
        @click="actions.handleCreate"
      >
        {{ t('integration.actions.newIntegration') }}
      </el-button>
    </div>

    <IntegrationStatsCards :stats="query.stats" />

    <IntegrationConfigFilterBar
      :system-type="query.filterForm.systemType"
      :is-enabled="query.filterForm.isEnabled"
      :health-status="query.filterForm.healthStatus"
      @update:system-type="query.filterForm.systemType = $event"
      @update:is-enabled="query.filterForm.isEnabled = $event"
      @update:health-status="query.filterForm.healthStatus = $event"
      @search="query.fetchData"
      @reset="query.handleFilterReset"
    />

    <IntegrationConfigTable
      :loading="query.loading"
      :table-data="query.tableData"
      :testing="actions.testing"
      :syncing="actions.syncing"
      :current-page="query.pagination.page"
      :page-size="query.pagination.pageSize"
      :total="query.pagination.total"
      @test="actions.handleTest"
      @sync="actions.handleSync"
      @logs="logViewer.handleViewLogs"
      @edit="actions.handleEdit"
      @delete="actions.handleDelete"
      @page-change="query.handlePageChange"
      @page-size-change="query.handlePageSizeChange"
    />

    <IntegrationConfigFormDialog
      v-model="actions.dialogVisible"
      :is-edit="actions.isEdit"
      :submitting="actions.submitting"
      :form-data="actions.formData"
      @submit="actions.handleSubmit"
    />

    <IntegrationLogsDrawer
      v-model="logViewer.logsDrawerVisible"
      :current-config="logViewer.currentConfig"
      :logs-loading="logViewer.logsLoading"
      :logs="logViewer.logs"
      :page="logViewer.logsPagination.page"
      :page-size="logViewer.logsPagination.pageSize"
      :total="logViewer.logsPagination.total"
      @refresh="logViewer.fetchLogs"
      @view-detail="logViewer.handleViewLogDetail"
      @page-change="logViewer.handleLogsPageChange"
      @page-size-change="logViewer.handleLogsPageSizeChange"
    />

    <IntegrationLogDetailDialog
      v-model="logViewer.logDetailVisible"
      :current-log="logViewer.currentLog"
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
import { useIntegrationConfigList } from './composables'

const { t } = useI18n()

const integration = useIntegrationConfigList()
const query = integration.query
const actions = integration.actions
const logViewer = integration.logViewer

onMounted(() => {
  void query.fetchData()
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
