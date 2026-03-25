```
<!--
  ConfigPackageList.vue - Configuration Package Management Page
-->

<template>
  <div class="config-package-list">
    <!-- Header -->
    <div class="page-header">
      <div class="header-left">
        <h2>{{ $t('system.configPackage.title') }}</h2>
        <el-text
          type="info"
          size="small"
        >
          {{ $t('system.configPackage.description') }}
        </el-text>
      </div>
      <div class="header-right">
        <el-button @click="showImportDialog = true">
          <el-icon><Upload /></el-icon>
          {{ $t('system.configPackage.actions.import') }}
        </el-button>
        <el-button
          type="primary"
          @click="showExportDialog = true"
        >
          <el-icon><Download /></el-icon>
          {{ $t('system.configPackage.actions.export') }}
        </el-button>
      </div>
    </div>

    <!-- Tabs -->
    <el-tabs
      v-model="activeTab"
      class="content-tabs"
    >
      <el-tab-pane
        :label="$t('system.configPackage.tabs.packages')"
        name="packages"
      >
        <template #label>
          <span>{{ $t('system.configPackage.tabs.packages') }}</span>
          <el-badge
            v-if="packages.length"
            :value="packages.length"
            class="tab-badge"
          />
        </template>
      </el-tab-pane>
      <el-tab-pane
        :label="$t('system.configPackage.tabs.history')"
        name="imports"
      >
        <template #label>
          <span>{{ $t('system.configPackage.tabs.history') }}</span>
          <el-badge
            v-if="importLogs.length"
            :value="importLogs.length"
            class="tab-badge"
          />
        </template>
      </el-tab-pane>
    </el-tabs>

    <!-- Packages Table -->
    <el-table
      v-if="activeTab === 'packages'"
      v-loading="loading"
      :data="packages"
      stripe
      class="data-table"
    >
      <el-table-column
        prop="name"
        :label="$t('system.configPackage.columns.name')"
        min-width="180"
      >
        <template #default="{ row }">
          <div class="package-name">
            <span>{{ row.name }}</span>
            <el-tag
              type="info"
              size="small"
            >
              v{{ row.version }}
            </el-tag>
          </div>
          <el-text
            v-if="row.description"
            type="info"
            size="small"
            class="desc"
          >
            {{ row.description }}
          </el-text>
        </template>
      </el-table-column>

      <el-table-column
        prop="package_type"
        :label="$t('system.configPackage.columns.type')"
        width="100"
      >
        <template #default="{ row }">
          <el-tag
            :type="getPackageTypeStyle(row.package_type)"
            size="small"
          >
            {{ getPackageTypeLabel(row.package_type) }}
          </el-tag>
        </template>
      </el-table-column>

      <el-table-column
        :label="$t('system.configPackage.columns.objects')"
        width="120"
      >
        <template #default="{ row }">
          <el-popover
            placement="top-start"
            :width="200"
            trigger="hover"
          >
            <template #reference>
              <el-tag size="small">
                {{ row.object_count || row.included_objects?.length || 0 }} {{ $t('common.item') }}
              </el-tag>
            </template>
            <div class="object-list">
              <el-tag
                v-for="code in row.included_objects"
                :key="code"
                size="small"
                class="object-tag"
              >
                {{ code }}
              </el-tag>
            </div>
          </el-popover>
        </template>
      </el-table-column>

      <el-table-column
        prop="source_environment"
        :label="$t('system.configPackage.columns.source')"
        width="120"
      >
        <template #default="{ row }">
          <el-tag
            v-if="row.source_environment"
            type="info"
            size="small"
            effect="plain"
          >
            {{ row.source_environment }}
          </el-tag>
          <span
            v-else
            class="text-muted"
          >-</span>
        </template>
      </el-table-column>

      <el-table-column
        prop="exported_at"
        :label="$t('system.configPackage.columns.exportTime')"
        width="170"
      >
        <template #default="{ row }">
          {{ formatDate(row.exported_at) }}
        </template>
      </el-table-column>

      <el-table-column
        prop="is_valid"
        :label="$t('system.configPackage.columns.status')"
        width="80"
        align="center"
      >
        <template #default="{ row }">
          <el-icon
            v-if="row.is_valid"
            class="text-success"
          >
            <CircleCheck />
          </el-icon>
          <el-icon
            v-else
            class="text-danger"
          >
            <CircleClose />
          </el-icon>
        </template>
      </el-table-column>

      <el-table-column
        :label="$t('system.configPackage.columns.operation')"
        width="200"
        fixed="right"
      >
        <template #default="{ row }">
          <el-button
            link
            type="primary"
            size="small"
            @click="handleImportPackage(row)"
          >
            {{ $t('system.configPackage.actions.import') }}
          </el-button>
          <el-button
            link
            type="info"
            size="small"
            @click="handleDownload(row)"
          >
            {{ $t('system.configPackage.actions.download') }}
          </el-button>
          <el-button
            link
            type="warning"
            size="small"
            @click="handleDiff(row)"
          >
            {{ $t('system.configPackage.actions.diff') }}
          </el-button>
          <el-popconfirm
            :title="$t('system.configPackage.messages.confirmDelete')"
            @confirm="handleDelete(row)"
          >
            <template #reference>
              <el-button
                link
                type="danger"
                size="small"
              >
                {{ $t('system.configPackage.actions.delete') }}
              </el-button>
            </template>
          </el-popconfirm>
        </template>
      </el-table-column>
    </el-table>

    <!-- Import Logs Table -->
    <el-table
      v-if="activeTab === 'imports'"
      v-loading="loadingLogs"
      :data="importLogs"
      stripe
      class="data-table"
    >
      <el-table-column
        :label="$t('system.configPackage.columns.package')"
        min-width="180"
      >
        <template #default="{ row }">
          <span>{{ row.package_name }}</span>
          <el-tag
            type="info"
            size="small"
            class="ml-2"
          >
            v{{ row.package_version }}
          </el-tag>
        </template>
      </el-table-column>

      <el-table-column
        prop="import_strategy"
        :label="$t('system.configPackage.columns.strategy')"
        width="80"
      >
        <template #default="{ row }">
          <el-tag
            size="small"
            effect="plain"
          >
            {{ getStrategyLabel(row.import_strategy) }}
          </el-tag>
        </template>
      </el-table-column>

      <el-table-column
        prop="status"
        :label="$t('system.configPackage.columns.status')"
        width="100"
      >
        <template #default="{ row }">
          <el-tag
            :type="getStatusStyle(row.status)"
            size="small"
          >
            {{ getStatusLabel(row.status) }}
          </el-tag>
        </template>
      </el-table-column>

      <el-table-column
        :label="$t('system.configPackage.columns.result')"
        width="200"
      >
        <template #default="{ row }">
          <div class="import-stats">
            <span class="stat created">+{{ row.objects_created }}</span>
            <span class="stat updated">~{{ row.objects_updated }}</span>
            <span class="stat skipped">={{ row.objects_skipped }}</span>
            <span
              v-if="row.objects_failed"
              class="stat failed"
            >!{{ row.objects_failed }}</span>
          </div>
        </template>
      </el-table-column>

      <el-table-column
        prop="imported_at"
        :label="$t('system.configPackage.columns.importTime')"
        width="170"
      >
        <template #default="{ row }">
          {{ formatDate(row.imported_at) }}
        </template>
      </el-table-column>

      <el-table-column
        :label="$t('system.configPackage.columns.operation')"
        width="100"
        fixed="right"
      >
        <template #default="{ row }">
          <el-button
            v-if="row.can_rollback && row.status === 'success'"
            link
            type="warning"
            size="small"
            @click="handleRollback(row)"
          >
            {{ $t('system.configPackage.actions.rollback') }}
          </el-button>
          <span
            v-else
            class="text-muted"
          >-</span>
        </template>
      </el-table-column>
    </el-table>

    <!-- Export Dialog -->
    <el-dialog
      v-model="showExportDialog"
      :title="$t('system.configPackage.dialog.exportTitle')"
      width="600px"
    >
      <el-form
        :model="exportForm"
        label-width="100px"
      >
        <el-form-item
          :label="$t('system.configPackage.dialog.name')"
          required
        >
          <el-input
            v-model="exportForm.name"
            :placeholder="$t('system.configPackage.dialog.namePlaceholder')"
          />
        </el-form-item>
        <el-form-item
          :label="$t('system.configPackage.dialog.version')"
          required
        >
          <el-input
            v-model="exportForm.version"
            :placeholder="$t('system.configPackage.dialog.versionPlaceholder')"
          />
        </el-form-item>
        <el-form-item :label="$t('system.configPackage.dialog.description')">
          <el-input
            v-model="exportForm.description"
            type="textarea"
            :rows="2"
          />
        </el-form-item>
        <el-form-item
          :label="$t('system.configPackage.dialog.objects')"
          required
        >
          <el-select
            v-model="exportForm.object_codes"
            multiple
            filterable
            :placeholder="$t('system.configPackage.dialog.objectsPlaceholder')"
            class="full-width"
          >
            <el-option
              v-for="bo in businessObjects"
              :key="bo.code"
              :label="bo.name"
              :value="bo.code"
            />
          </el-select>
        </el-form-item>
      </el-form>

      <template #footer>
        <el-button @click="showExportDialog = false">
          {{ $t('common.actions.cancel') }}
        </el-button>
        <el-button
          type="primary"
          :loading="exporting"
          @click="handleExport"
        >
          {{ $t('system.configPackage.actions.export') }}
        </el-button>
      </template>
    </el-dialog>

    <!-- Import Dialog -->
    <el-dialog
      v-model="showImportDialog"
      :title="$t('system.configPackage.dialog.importTitle')"
      width="600px"
    >
      <el-form
        :model="importForm"
        label-width="100px"
      >
        <el-form-item :label="$t('system.configPackage.dialog.package')">
          <el-select
            v-model="importForm.package_id"
            :placeholder="$t('system.configPackage.dialog.packagePlaceholder')"
            class="full-width"
          >
            <el-option
              v-for="pkg in packages"
              :key="pkg.id"
              :label="`${pkg.name} v${pkg.version}`"
              :value="pkg.id"
            />
          </el-select>
        </el-form-item>
        <el-form-item :label="$t('system.configPackage.dialog.strategy')">
          <el-radio-group v-model="importForm.strategy">
            <el-radio value="merge">
              {{ $t('system.configPackage.dialog.strategies.merge') }}
            </el-radio>
            <el-radio value="replace">
              {{ $t('system.configPackage.dialog.strategies.replace') }}
            </el-radio>
            <el-radio value="skip">
              {{ $t('system.configPackage.dialog.strategies.skip') }}
            </el-radio>
          </el-radio-group>
        </el-form-item>
      </el-form>

      <template #footer>
        <el-button @click="showImportDialog = false">
          {{ $t('common.actions.cancel') }}
        </el-button>
        <el-button
          type="primary"
          :loading="importing"
          @click="handleImport"
        >
          {{ $t('system.configPackage.actions.import') }}
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { useI18n } from 'vue-i18n'
import {
  Upload,
  Download,
  CircleCheck,
  CircleClose
} from '@element-plus/icons-vue'
import { useConfigPackageApi, type ConfigPackage, type ConfigImportLog } from '@/api/configPackage'
import { businessObjectApi } from '@/api/system'

const { t } = useI18n()

const {
  getPackages,
  exportPackage,
  importPackage,
  downloadPackage,
  deletePackage,
  getImportLogs,
  rollbackImport
} = useConfigPackageApi()

// State
const loading = ref(false)
const loadingLogs = ref(false)
const packages = ref<ConfigPackage[]>([])
const importLogs = ref<ConfigImportLog[]>([])
const businessObjects = ref<Array<{ code: string; name: string }>>([])
const activeTab = ref('packages')

const showExportDialog = ref(false)
const showImportDialog = ref(false)
const exporting = ref(false)
const importing = ref(false)

const exportForm = reactive({
  name: '',
  version: '1.0.0',
  description: '',
  object_codes: [] as string[]
})

const importForm = reactive({
  package_id: '',
  strategy: 'merge' as 'merge' | 'replace' | 'skip'
})

// Helpers
function formatDate(date: string): string {
  if (!date) return '-'
  return new Date(date).toLocaleString()
}

function getPackageTypeLabel(type: string): string {
  const labels: Record<string, string> = {
    full: t('system.configPackage.types.full'),
    partial: t('system.configPackage.types.partial'),
    diff: t('system.configPackage.types.diff')
  }
  return labels[type] || type
}

function getPackageTypeStyle(type: string): string {
  const styles: Record<string, string> = {
    full: 'primary',
    partial: 'warning',
    diff: 'info'
  }
  return styles[type] || 'info'
}

function getStrategyLabel(strategy: string): string {
  const labels: Record<string, string> = {
    merge: t('system.configPackage.strategies.merge'),
    replace: t('system.configPackage.strategies.replace'),
    skip: t('system.configPackage.strategies.skip')
  }
  return labels[strategy] || strategy
}

function getStatusLabel(status: string): string {
  const labels: Record<string, string> = {
    pending: t('system.configPackage.status.pending'),
    in_progress: t('system.configPackage.status.processing'),
    success: t('system.configPackage.status.success'),
    partial: t('system.configPackage.status.partial'),
    failed: t('system.configPackage.status.failed'),
    rolled_back: t('system.configPackage.status.rolled_back')
  }
  return labels[status] || status
}

function getStatusStyle(status: string): string {
  const styles: Record<string, string> = {
    pending: 'info',
    in_progress: 'warning',
    success: 'success',
    partial: 'warning',
    failed: 'danger',
    rolled_back: 'info'
  }
  return styles[status] || 'info'
}

// Data loading
async function loadPackages() {
  loading.value = true
  try {
    packages.value = await getPackages()
  } catch {
    ElMessage.error(t('system.configPackage.messages.loadPackagesFailed'))
  } finally {
    loading.value = false
  }
}

async function loadImportLogs() {
  loadingLogs.value = true
  try {
    importLogs.value = await getImportLogs()
  } catch {
    ElMessage.error(t('system.configPackage.messages.loadLogsFailed'))
  } finally {
    loadingLogs.value = false
  }
}

async function loadBusinessObjects() {
  try {
    const data: any = await businessObjectApi.list({ page_size: 500, is_active: true })
    const results = data?.results || data?.data?.results || data?.fields || data?.data?.fields || []
    businessObjects.value = (Array.isArray(results) ? results : []).map((item: any) => ({
      code: item.code || item.objectCode || item.object_code || '',
      name: item.name || item.objectName || item.object_name || item.label || item.code || ''
    })).filter((item: any) => !!item.code)
  } catch {
    // Ignore
  }
}

// Actions
async function handleExport() {
  if (!exportForm.name || !exportForm.version || exportForm.object_codes.length === 0) {
    ElMessage.warning(t('system.configPackage.messages.required'))
    return
  }

  exporting.value = true
  try {
    const result = await exportPackage({
      name: exportForm.name,
      version: exportForm.version,
      description: exportForm.description,
      object_codes: exportForm.object_codes
    })
    ElMessage.success(
      t('system.configPackage.messages.exportSuccess', {
        objects: result.summary.objects,
        fields: result.summary.fields,
        layouts: result.summary.layouts,
        rules: result.summary.rules
      })
    )
    showExportDialog.value = false
    loadPackages()
  } catch (error: any) {
    ElMessage.error(error.message || t('system.configPackage.messages.exportFailed'))
  } finally {
    exporting.value = false
  }
}

async function handleImport() {
  if (!importForm.package_id) {
    ElMessage.warning(t('system.configPackage.messages.selectPackage'))
    return
  }

  importing.value = true
  try {
    const result = await importPackage({
      package_id: importForm.package_id,
      strategy: importForm.strategy
    })

    if (result.success) {
      ElMessage.success(
        t('system.configPackage.messages.importSuccess', {
          created: result.summary.created,
          updated: result.summary.updated,
          skipped: result.summary.skipped
        })
      )
    } else {
      ElMessage.warning(t('system.configPackage.messages.importPartial', { failed: result.errors.length }))
    }

    showImportDialog.value = false
    loadImportLogs()
  } catch (error: any) {
    ElMessage.error(error.message || t('system.configPackage.messages.importFailed'))
  } finally {
    importing.value = false
  }
}

async function handleImportPackage(pkg: ConfigPackage) {
  importForm.package_id = pkg.id
  showImportDialog.value = true
}

async function handleDownload(pkg: ConfigPackage) {
  try {
    await downloadPackage(pkg.id)
    ElMessage.success(t('system.configPackage.messages.downloadStart'))
  } catch {
    ElMessage.error(t('system.configPackage.messages.downloadFailed'))
  }
}

function handleDiff(_pkg: ConfigPackage) {
  ElMessage.info(t('system.configPackage.messages.diffDeveloping'))
}

async function handleDelete(pkg: ConfigPackage) {
  try {
    await deletePackage(pkg.id)
    ElMessage.success(t('system.configPackage.messages.deleteSuccess'))
    loadPackages()
  } catch {
    ElMessage.error(t('system.configPackage.messages.deleteFailed'))
  }
}

async function handleRollback(log: ConfigImportLog) {
  try {
    await ElMessageBox.confirm(
      t('system.configPackage.messages.rollbackConfirm'),
      t('system.configPackage.messages.rollbackTitle')
    )

    const result = await rollbackImport(log.id)
    ElMessage.success(result.message || t('system.configPackage.messages.rollbackSuccess'))
    loadImportLogs()
  } catch (error: any) {
    if (error !== 'cancel') {
      ElMessage.error(error.message || t('system.configPackage.messages.rollbackFailed'))
    }
  }
}

// Lifecycle
onMounted(() => {
  loadPackages()
  loadImportLogs()
  loadBusinessObjects()
})
</script>

<style scoped>
.config-package-list {
  padding: 20px;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 20px;
}

.header-left h2 {
  margin: 0 0 4px 0;
}

.header-right {
  display: flex;
  gap: 12px;
}

.content-tabs {
  margin-bottom: 16px;
}

.tab-badge {
  margin-left: 6px;
}

.data-table {
  border-radius: 8px;
}

.package-name {
  display: flex;
  align-items: center;
  gap: 8px;
}

.desc {
  display: block;
  margin-top: 2px;
}

.object-list {
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
}

.object-tag {
  margin: 2px 0;
}

.import-stats {
  display: flex;
  gap: 8px;
  font-size: 12px;
  font-family: monospace;
}

.stat.created { color: var(--el-color-success); }
.stat.updated { color: var(--el-color-warning); }
.stat.skipped { color: var(--el-color-info); }
.stat.failed { color: var(--el-color-danger); }

.text-success { color: var(--el-color-success); }
.text-danger { color: var(--el-color-danger); }
.text-muted { color: var(--el-text-color-placeholder); }

.full-width { width: 100%; }
.ml-2 { margin-left: 8px; }
</style>
```
