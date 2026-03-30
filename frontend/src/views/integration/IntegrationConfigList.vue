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
      @m18-sync="openM18SyncDialog"
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

    <M18SyncDialog
      v-model="m18SyncDialogVisible"
      :integration="selectedM18Config"
      :submitting="m18Syncing"
      @trigger="handleM18Sync"
    />
  </div>
</template>

<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { ElMessage } from 'element-plus'
import { triggerSync } from '@/api/integration'
import type { IntegrationConfig, TriggerSyncPayload } from '@/types/integration'
import IntegrationConfigFilterBar from './components/IntegrationConfigFilterBar.vue'
import IntegrationConfigFormDialog from './components/IntegrationConfigFormDialog.vue'
import IntegrationLogDetailDialog from './components/IntegrationLogDetailDialog.vue'
import IntegrationLogsDrawer from './components/IntegrationLogsDrawer.vue'
import M18SyncDialog from './components/M18SyncDialog.vue'
import IntegrationStatsCards from './components/IntegrationStatsCards.vue'
import IntegrationConfigTable from './components/IntegrationConfigTable.vue'
import { useIntegrationConfigList } from './composables'

const { t } = useI18n()

const integration = useIntegrationConfigList()
const query = integration.query
const actions = integration.actions
const logViewer = integration.logViewer
const m18SyncDialogVisible = ref(false)
const m18Syncing = ref(false)
const selectedM18Config = ref<IntegrationConfig | null>(null)

const openM18SyncDialog = (row: IntegrationConfig) => {
  selectedM18Config.value = row
  m18SyncDialogVisible.value = true
}

const handleM18Sync = async (payload: TriggerSyncPayload) => {
  if (!selectedM18Config.value) {
    return
  }

  m18Syncing.value = true
  try {
    await triggerSync(selectedM18Config.value.id, payload)
    ElMessage.success(t('integration.messages.syncTaskCreated'))
    m18SyncDialogVisible.value = false
    await query.fetchData()
  } catch (error: any) {
    ElMessage.error(error?.message || t('integration.messages.syncFailed'))
  } finally {
    m18Syncing.value = false
  }
}

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
