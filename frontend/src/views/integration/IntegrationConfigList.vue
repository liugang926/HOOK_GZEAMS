<template>
  <div class="integration-config-list">
    <div class="page-header">
      <h3>Integration Configuration</h3>
      <el-button
        type="primary"
        @click="handleCreate"
      >
        New Integration
      </el-button>
    </div>

    <!-- Statistics Cards -->
    <el-row
      :gutter="20"
      class="stats-row"
    >
      <el-col :span="6">
        <el-card>
          <div class="stat-item">
            <div class="stat-value">
              {{ stats.total }}
            </div>
            <div class="stat-label">
              Total Integrations
            </div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card>
          <div class="stat-item">
            <div class="stat-value healthy">
              {{ stats.healthy }}
            </div>
            <div class="stat-label">
              Healthy
            </div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card>
          <div class="stat-item">
            <div class="stat-value degraded">
              {{ stats.degraded }}
            </div>
            <div class="stat-label">
              Degraded
            </div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card>
          <div class="stat-item">
            <div class="stat-value unhealthy">
              {{ stats.unhealthy }}
            </div>
            <div class="stat-label">
              Unhealthy
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- Filters -->
    <el-form
      :model="filterForm"
      inline
      class="filter-form"
    >
      <el-form-item label="System Type">
        <el-select
          v-model="filterForm.systemType"
          clearable
          placeholder="All Systems"
          @change="fetchData"
        >
          <el-option
            label="M18"
            value="m18"
          />
          <el-option
            label="SAP"
            value="sap"
          />
          <el-option
            label="Kingdee"
            value="kingdee"
          />
          <el-option
            label="Yonyou"
            value="yonyou"
          />
          <el-option
            label="Oracle EBS"
            value="oracle"
          />
          <el-option
            label="Odoo"
            value="odoo"
          />
        </el-select>
      </el-form-item>
      <el-form-item label="Status">
        <el-select
          v-model="filterForm.isEnabled"
          clearable
          placeholder="All"
          @change="fetchData"
        >
          <el-option
            label="Enabled"
            :value="true"
          />
          <el-option
            label="Disabled"
            :value="false"
          />
        </el-select>
      </el-form-item>
      <el-form-item label="Health">
        <el-select
          v-model="filterForm.healthStatus"
          clearable
          placeholder="All"
          @change="fetchData"
        >
          <el-option
            label="Healthy"
            value="healthy"
          />
          <el-option
            label="Degraded"
            value="degraded"
          />
          <el-option
            label="Unhealthy"
            value="unhealthy"
          />
        </el-select>
      </el-form-item>
      <el-form-item>
        <el-button
          type="primary"
          @click="fetchData"
        >
          Search
        </el-button>
        <el-button @click="handleFilterReset">
          Reset
        </el-button>
      </el-form-item>
    </el-form>

    <!-- Integration Configs Table -->
    <el-table
      v-loading="loading"
      :data="tableData"
      border
      stripe
      style="width: 100%"
    >
      <el-table-column
        prop="systemName"
        label="Name"
        min-width="150"
      />
      <el-table-column
        label="System Type"
        width="120"
      >
        <template #default="{ row }">
          <el-tag :type="getSystemTypeTagType(row.systemType)">
            {{ getSystemTypeLabel(row.systemType) }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column
        label="Health Status"
        width="100"
      >
        <template #default="{ row }">
          <el-tag :type="getHealthStatusTagType(row.healthStatus)">
            {{ getHealthStatusLabel(row.healthStatus) }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column
        label="Status"
        width="100"
      >
        <template #default="{ row }">
          <el-tag :type="row.isEnabled ? 'success' : 'info'">
            {{ row.isEnabled ? 'Enabled' : 'Disabled' }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column
        label="Modules"
        width="200"
      >
        <template #default="{ row }">
          <el-tag
            v-for="module in row.enabledModules"
            :key="module"
            size="small"
            style="margin-right: 5px; margin-bottom: 3px"
          >
            {{ getModuleLabel(module) }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column
        prop="lastSyncAt"
        label="Last Sync"
        width="170"
      >
        <template #default="{ row }">
          {{ row.lastSyncAt ? formatDate(row.lastSyncAt) : '-' }}
        </template>
      </el-table-column>
      <el-table-column
        label="Last Sync Status"
        width="100"
      >
        <template #default="{ row }">
          <el-tag
            v-if="row.lastSyncStatus"
            :type="getSyncStatusTagType(row.lastSyncStatus)"
            size="small"
          >
            {{ getSyncStatusLabel(row.lastSyncStatus) }}
          </el-tag>
          <span v-else>-</span>
        </template>
      </el-table-column>
      <el-table-column
        label="Actions"
        width="320"
        fixed="right"
      >
        <template #default="{ row }">
          <el-button
            link
            type="primary"
            :loading="testing[row.id]"
            @click="handleTest(row)"
          >
            Test Connection
          </el-button>
          <el-button
            link
            type="primary"
            :loading="syncing[row.id]"
            @click="handleSync(row)"
          >
            Sync Now
          </el-button>
          <el-button
            link
            type="primary"
            @click="handleViewLogs(row)"
          >
            Logs
          </el-button>
          <el-button
            link
            type="primary"
            @click="handleEdit(row)"
          >
            Edit
          </el-button>
          <el-popconfirm
            title="Are you sure to delete this integration?"
            @confirm="handleDelete(row)"
          >
            <template #reference>
              <el-button
                link
                type="danger"
              >
                Delete
              </el-button>
            </template>
          </el-popconfirm>
        </template>
      </el-table-column>
    </el-table>

    <!-- Pagination -->
    <div class="pagination-footer">
      <el-pagination
        v-model:current-page="pagination.page"
        v-model:page-size="pagination.pageSize"
        :total="pagination.total"
        :page-sizes="[10, 20, 50, 100]"
        layout="total, sizes, prev, pager, next, jumper"
        @size-change="fetchData"
        @current-change="fetchData"
      />
    </div>

    <!-- Edit/Create Dialog -->
    <el-dialog
      v-model="dialogVisible"
      :title="isEdit ? 'Edit Integration' : 'New Integration'"
      width="700px"
      @close="handleDialogClose"
    >
      <el-form
        ref="formRef"
        :model="formData"
        :rules="rules"
        label-width="150px"
      >
        <el-divider content-position="left">
          Basic Configuration
        </el-divider>

        <el-form-item
          label="System Type"
          prop="systemType"
        >
          <el-select
            v-model="formData.systemType"
            placeholder="Select system type"
            style="width: 100%"
            :disabled="isEdit"
          >
            <el-option
              label="M18"
              value="m18"
            />
            <el-option
              label="SAP"
              value="sap"
            />
            <el-option
              label="Kingdee"
              value="kingdee"
            />
            <el-option
              label="Yonyou"
              value="yonyou"
            />
            <el-option
              label="Oracle EBS"
              value="oracle"
            />
            <el-option
              label="Odoo"
              value="odoo"
            />
          </el-select>
        </el-form-item>

        <el-form-item
          label="System Name"
          prop="systemName"
        >
          <el-input
            v-model="formData.systemName"
            placeholder="e.g., Production M18"
          />
        </el-form-item>

        <el-form-item label="Enabled">
          <el-switch v-model="formData.isEnabled" />
        </el-form-item>

        <el-divider content-position="left">
          Connection Configuration
        </el-divider>

        <el-form-item label="API Endpoint">
          <el-input
            v-model="formData.connectionConfig.apiUrl"
            placeholder="https://api.example.com"
          />
        </el-form-item>

        <el-form-item label="API Key">
          <el-input
            v-model="formData.connectionConfig.apiKey"
            type="password"
            show-password
            placeholder="Enter API key"
          />
        </el-form-item>

        <el-form-item label="API Secret">
          <el-input
            v-model="formData.connectionConfig.apiSecret"
            type="password"
            show-password
            placeholder="Enter API secret"
          />
        </el-form-item>

        <el-form-item label="Timeout (seconds)">
          <el-input-number
            v-model="formData.connectionConfig.timeout"
            :min="1"
            :max="300"
            style="width: 100%"
          />
        </el-form-item>

        <el-divider content-position="left">
          Module Configuration
        </el-divider>

        <el-form-item label="Enabled Modules">
          <el-checkbox-group v-model="formData.enabledModules">
            <el-checkbox label="procurement">
              Procurement
            </el-checkbox>
            <el-checkbox label="finance">
              Finance
            </el-checkbox>
            <el-checkbox label="inventory">
              Inventory
            </el-checkbox>
            <el-checkbox label="hr">
              HR
            </el-checkbox>
            <el-checkbox label="crm">
              CRM
            </el-checkbox>
          </el-checkbox-group>
        </el-form-item>

        <el-divider content-position="left">
          Sync Configuration
        </el-divider>

        <el-form-item label="Auto Sync">
          <el-switch v-model="formData.syncConfig.autoSync" />
        </el-form-item>

        <el-form-item
          v-if="formData.syncConfig.autoSync"
          label="Sync Interval (minutes)"
        >
          <el-input-number
            v-model="formData.syncConfig.interval"
            :min="1"
            :max="1440"
            style="width: 100%"
          />
        </el-form-item>
      </el-form>

      <template #footer>
        <el-button @click="dialogVisible = false">
          Cancel
        </el-button>
        <el-button
          type="primary"
          :loading="submitting"
          @click="handleSubmit"
        >
          {{ isEdit ? 'Save' : 'Create' }}
        </el-button>
      </template>
    </el-dialog>

    <!-- Logs Drawer -->
    <el-drawer
      v-model="logsDrawerVisible"
      title="Integration Logs"
      size="800px"
    >
      <div
        v-if="currentConfig"
        class="logs-content"
      >
        <div class="logs-header">
          <h4>{{ currentConfig.systemName }} - Logs</h4>
          <el-button
            type="primary"
            size="small"
            @click="fetchLogs"
          >
            Refresh
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
            label="Time"
            width="160"
          />
          <el-table-column
            prop="integrationType"
            label="Type"
            width="120"
          />
          <el-table-column
            prop="action"
            label="Action"
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
            label="Method"
            width="80"
          />
          <el-table-column
            prop="statusCode"
            label="Status"
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
            label="Success"
            width="80"
          >
            <template #default="{ row }">
              <el-tag
                size="small"
                :type="row.success ? 'success' : 'danger'"
              >
                {{ row.success ? 'Yes' : 'No' }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column
            prop="durationMs"
            label="Duration"
            width="90"
          >
            <template #default="{ row }">
              {{ row.durationMs ? `${row.durationMs}ms` : '-' }}
            </template>
          </el-table-column>
          <el-table-column
            label="Actions"
            width="80"
          >
            <template #default="{ row }">
              <el-button
                link
                type="primary"
                size="small"
                @click="handleViewLogDetail(row)"
              >
                View
              </el-button>
            </template>
          </el-table-column>
        </el-table>

        <div class="pagination-footer">
          <el-pagination
            v-model:current-page="logsPagination.page"
            v-model:page-size="logsPagination.pageSize"
            :total="logsPagination.total"
            :page-sizes="[10, 20, 50]"
            layout="total, sizes, prev, pager, next"
            @size-change="fetchLogs"
            @current-change="fetchLogs"
          />
        </div>
      </div>
    </el-drawer>

    <!-- Log Detail Dialog -->
    <el-dialog
      v-model="logDetailVisible"
      title="Log Detail"
      width="900px"
    >
      <el-descriptions
        v-if="currentLog"
        :column="2"
        border
      >
        <el-descriptions-item label="Time">
          {{ currentLog.createdAt }}
        </el-descriptions-item>
        <el-descriptions-item label="Integration Type">
          {{ currentLog.integrationType }}
        </el-descriptions-item>
        <el-descriptions-item label="Action">
          <el-tag :type="currentLog.action === 'push' ? 'success' : 'warning'">
            {{ currentLog.action }}
          </el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="Method">
          {{ currentLog.requestMethod }}
        </el-descriptions-item>
        <el-descriptions-item label="Status Code">
          <el-tag :type="currentLog.statusCode < 300 ? 'success' : 'danger'">
            {{ currentLog.statusCode }}
          </el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="Success">
          <el-tag :type="currentLog.success ? 'success' : 'danger'">
            {{ currentLog.success ? 'Yes' : 'No' }}
          </el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="Duration">
          {{ currentLog.durationMs }}ms
        </el-descriptions-item>
        <el-descriptions-item label="Business Type">
          {{ currentLog.businessType || '-' }}
        </el-descriptions-item>
      </el-descriptions>

      <el-divider>Request</el-divider>
      <div class="code-block">
        <pre><code>{{ JSON.stringify(currentLog?.requestBody || {}, null, 2) }}</code></pre>
      </div>

      <el-divider>Response</el-divider>
      <div class="code-block">
        <pre><code>{{ JSON.stringify(currentLog?.responseBody || {}, null, 2) }}</code></pre>
      </div>

      <div
        v-if="currentLog?.errorMessage"
        class="error-message"
      >
        <el-divider>Error</el-divider>
        <pre>{{ currentLog.errorMessage }}</pre>
      </div>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import type { FormInstance, FormRules } from 'element-plus'
import { integrationConfigApi, integrationLogApi } from '@/api/integration'

interface IntegrationConfig {
  id: string
  systemType: string
  systemName: string
  isEnabled: boolean
  enabledModules: string[]
  connectionConfig: Record<string, any>
  syncConfig: Record<string, any>
  healthStatus: string
  lastSyncAt: string | null
  lastSyncStatus: string
}

interface IntegrationLog {
  id: string
  createdAt: string
  integrationType: string
  action: string
  requestMethod: string
  statusCode: number
  success: boolean
  durationMs: number
  requestBody: any
  responseBody: any
  errorMessage: string
  businessType: string
}

const loading = ref(false)
const tableData = ref<IntegrationConfig[]>([])
const dialogVisible = ref(false)
const logsDrawerVisible = ref(false)
const logDetailVisible = ref(false)
const submitting = ref(false)
const testing = ref<Record<string, boolean>>({})
const syncing = ref<Record<string, boolean>>({})
const logsLoading = ref(false)

const currentConfig = ref<IntegrationConfig | null>(null)
const currentLog = ref<IntegrationLog | null>(null)
const logs = ref<IntegrationLog[]>([])

const filterForm = reactive({
  systemType: undefined as unknown as string,
  isEnabled: undefined as unknown as boolean,
  healthStatus: undefined as unknown as string
})

const pagination = reactive({
  page: 1,
  pageSize: 20,
  total: 0
})

const logsPagination = reactive({
  page: 1,
  pageSize: 20,
  total: 0
})

const stats = ref({
  total: 0,
  healthy: 0,
  degraded: 0,
  unhealthy: 0
})

const formRef = ref<FormInstance>()
const isEdit = ref(false)

const formData = ref({
  systemType: '',
  systemName: '',
  isEnabled: true,
  enabledModules: [] as string[],
  connectionConfig: {
    apiUrl: '',
    apiKey: '',
    apiSecret: '',
    timeout: 30
  },
  syncConfig: {
    autoSync: false,
    interval: 60
  }
})

const rules: FormRules = {
  systemType: [
    { required: true, message: 'Please select system type', trigger: 'change' }
  ],
  systemName: [
    { required: true, message: 'Please enter system name', trigger: 'blur' }
  ]
}

const getSystemTypeLabel = (type: string) => {
  const labels: Record<string, string> = {
    m18: 'M18',
    sap: 'SAP',
    kingdee: 'Kingdee',
    yonyou: 'Yonyou',
    oracle: 'Oracle EBS',
    odoo: 'Odoo'
  }
  return labels[type] || type
}

const getSystemTypeTagType = (type: string) => {
  const types: Record<string, string> = {
    m18: 'primary',
    sap: 'success',
    kingdee: 'warning',
    yonyou: 'danger',
    oracle: 'info',
    odoo: ''
  }
  return types[type] || ''
}

const getHealthStatusLabel = (status: string) => {
  const labels: Record<string, string> = {
    healthy: 'Healthy',
    degraded: 'Degraded',
    unhealthy: 'Unhealthy'
  }
  return labels[status] || status
}

const getHealthStatusTagType = (status: string) => {
  const types: Record<string, string> = {
    healthy: 'success',
    degraded: 'warning',
    unhealthy: 'danger'
  }
  return types[status] || ''
}

const getSyncStatusLabel = (status: string) => {
  const labels: Record<string, string> = {
    pending: 'Pending',
    running: 'Running',
    success: 'Success',
    partial_success: 'Partial',
    failed: 'Failed',
    cancelled: 'Cancelled'
  }
  return labels[status] || status
}

const getSyncStatusTagType = (status: string) => {
  const types: Record<string, string> = {
    pending: 'info',
    running: 'warning',
    success: 'success',
    partial_success: 'warning',
    failed: 'danger',
    cancelled: 'info'
  }
  return types[status] || ''
}

const getModuleLabel = (module: string) => {
  const labels: Record<string, string> = {
    procurement: 'Procurement',
    finance: 'Finance',
    inventory: 'Inventory',
    hr: 'HR',
    crm: 'CRM'
  }
  return labels[module] || module
}

const formatDate = (dateStr: string) => {
  if (!dateStr) return '-'
  return new Date(dateStr).toLocaleString()
}

const fetchData = async () => {
  loading.value = true
  try {
    const params: any = {
      page: pagination.page,
      page_size: pagination.pageSize
    }
    if (filterForm.systemType) {
      params.systemType = filterForm.systemType
    }
    if (filterForm.isEnabled !== undefined) {
      params.isEnabled = filterForm.isEnabled
    }
    if (filterForm.healthStatus) {
      params.healthStatus = filterForm.healthStatus
    }

    const res = await integrationConfigApi.list(params)
    tableData.value = res.results || []
    pagination.total = res.count || 0

    // Update stats
    stats.value = {
      total: res.count || 0,
      healthy: (res.results || []).filter((r: IntegrationConfig) => r.healthStatus === 'healthy').length,
      degraded: (res.results || []).filter((r: IntegrationConfig) => r.healthStatus === 'degraded').length,
      unhealthy: (res.results || []).filter((r: IntegrationConfig) => r.healthStatus === 'unhealthy').length
    }
  } catch (error) {
    ElMessage.error('Failed to load integration configs')
  } finally {
    loading.value = false
  }
}

const handleFilterReset = () => {
  filterForm.systemType = undefined as unknown as string
  filterForm.isEnabled = undefined as unknown as boolean
  filterForm.healthStatus = undefined as unknown as string
  fetchData()
}

const handleCreate = () => {
  isEdit.value = false
  formData.value = {
    systemType: '',
    systemName: '',
    isEnabled: true,
    enabledModules: [] as string[],
    connectionConfig: {
      apiUrl: '',
      apiKey: '',
      apiSecret: '',
      timeout: 30
    },
    syncConfig: {
      autoSync: false,
      interval: 60
    }
  }
  dialogVisible.value = true
}

const handleEdit = (row: IntegrationConfig) => {
  isEdit.value = true
  formData.value = {
    systemType: row.systemType,
    systemName: row.systemName,
    isEnabled: row.isEnabled,
    enabledModules: row.enabledModules || [],
    connectionConfig: row.connectionConfig || { apiUrl: '', apiKey: '', apiSecret: '', timeout: 30 },
    syncConfig: row.syncConfig || { autoSync: false, interval: 60 }
  }
  currentConfig.value = row
  dialogVisible.value = true
}

const handleDialogClose = () => {
  formRef.value?.clearValidate()
}

const handleSubmit = async () => {
  if (!formRef.value) return

  await formRef.value.validate(async (valid) => {
    if (!valid) return

    submitting.value = true
    try {
      if (isEdit.value && currentConfig.value) {
        await integrationConfigApi.update(currentConfig.value.id, formData.value)
        ElMessage.success('Updated successfully')
      } else {
        await integrationConfigApi.create(formData.value)
        ElMessage.success('Created successfully')
      }
      dialogVisible.value = false
      fetchData()
    } catch (error) {
      ElMessage.error('Operation failed')
    } finally {
      submitting.value = false
    }
  })
}

const handleDelete = async (row: IntegrationConfig) => {
  try {
    await integrationConfigApi.delete(row.id)
    ElMessage.success('Deleted successfully')
    fetchData()
  } catch (error) {
    ElMessage.error('Delete failed')
  }
}

const handleTest = async (row: IntegrationConfig) => {
  testing.value[row.id] = true
  try {
    const res = await integrationConfigApi.test(row.id)
    if (res.success) ElMessage.success(res.message || 'Connection test successful')
    else ElMessage.warning(res.message || 'Connection test failed')
    fetchData()
  } catch (error) {
    ElMessage.error('Connection test failed')
  } finally {
    testing.value[row.id] = false
  }
}

const handleSync = async (row: IntegrationConfig) => {
  syncing.value[row.id] = true
  try {
    const res = await integrationConfigApi.sync(row.id)
    if (res.success) ElMessage.success(res.message || 'Sync task created successfully')
    else ElMessage.warning(res.message || 'Sync failed')
    fetchData()
  } catch (error) {
    ElMessage.error('Sync failed')
  } finally {
    syncing.value[row.id] = false
  }
}

const handleViewLogs = (row: IntegrationConfig) => {
  currentConfig.value = row
  logsDrawerVisible.value = true
  logsPagination.page = 1
  fetchLogs()
}

const fetchLogs = async () => {
  if (!currentConfig.value) return

  logsLoading.value = true
  try {
    const params: any = {
      page: logsPagination.page,
      page_size: logsPagination.pageSize,
      systemType: currentConfig.value.systemType
    }
    const res = await integrationLogApi.list(params)
    logs.value = res.results || []
    logsPagination.total = res.count || 0
  } catch (error) {
    ElMessage.error('Failed to load logs')
  } finally {
    logsLoading.value = false
  }
}

const handleViewLogDetail = (log: IntegrationLog) => {
  currentLog.value = log
  logDetailVisible.value = true
}

onMounted(() => {
  fetchData()
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

.filter-form {
  margin-bottom: 20px;
}

.stats-row {
  margin-bottom: 20px;
}

.stat-item {
  text-align: center;
}

.stat-value {
  font-size: 28px;
  font-weight: bold;
  color: #409eff;
}

.stat-value.healthy {
  color: #67c23a;
}

.stat-value.degraded {
  color: #e6a23c;
}

.stat-value.unhealthy {
  color: #f56c6c;
}

.stat-label {
  font-size: 14px;
  color: #909399;
  margin-top: 5px;
}

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

.code-block {
  background: #f5f7fa;
  border-radius: 4px;
  padding: 15px;
  max-height: 300px;
  overflow: auto;
}

.code-block pre {
  margin: 0;
  font-size: 12px;
  font-family: 'Courier New', monospace;
}

.error-message {
  margin-top: 15px;
}

.error-message pre {
  background: #fef0f0;
  color: #f56c6c;
  padding: 10px;
  border-radius: 4px;
  white-space: pre-wrap;
  font-size: 12px;
}
</style>

