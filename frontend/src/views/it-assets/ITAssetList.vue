<template>
  <div class="it-asset-list">
    <BaseListPage
      ref="listRef"
      :title="t('itAssets.title')"
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
          {{ t('itAssets.actions.add') }}
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
          :title="t('itAssets.messages.deleteConfirm')"
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

    <!-- Asset Form Dialog -->
    <ITAssetForm
      v-model:visible="dialogVisible"
      :data="currentRow"
      @success="handleRefresh"
    />

    <!-- Asset Detail Drawer -->
    <el-drawer
      v-model="detailDrawerVisible"
      :title="$t('itAssets.detail.title')"
      size="600px"
    >
      <div
        v-if="currentRow"
        class="asset-detail"
      >
        <el-descriptions
          :column="2"
          border
        >
          <el-descriptions-item :label="$t('itAssets.columns.assetCode')">
            {{ currentRow.asset_code }}
          </el-descriptions-item>
          <el-descriptions-item :label="$t('itAssets.columns.assetName')">
            {{ currentRow.asset_name }}
          </el-descriptions-item>
          <el-descriptions-item :label="$t('itAssets.detail.status')">
            <el-tag :type="currentRow.disk_encrypted ? 'success' : 'warning'">
              {{ currentRow.disk_encrypted ? $t('itAssets.status.secure') : $t('itAssets.status.attentionNeeded') }}
            </el-tag>
          </el-descriptions-item>
        </el-descriptions>

        <div class="section-title">
          {{ $t('itAssets.detail.hardwareConfig') }}
        </div>
        <el-descriptions
          :column="2"
          border
        >
          <el-descriptions-item :label="$t('itAssets.columns.cpu')">
            {{ currentRow.cpu_model || '-' }}
          </el-descriptions-item>
          <el-descriptions-item :label="$t('itAssets.detail.coresThreads')">
            {{ currentRow.cpu_cores || '-' }} / {{ currentRow.cpu_threads || '-' }}
          </el-descriptions-item>
          <el-descriptions-item :label="$t('itAssets.columns.ram')">
            {{ currentRow.ram_capacity ? `${currentRow.ram_capacity} GB` : '-' }}
          </el-descriptions-item>
          <el-descriptions-item :label="$t('itAssets.detail.ramType')">
            {{ currentRow.ram_type || '-' }}
          </el-descriptions-item>
          <el-descriptions-item :label="$t('itAssets.columns.disk')">
            {{ currentRow.disk_capacity ? `${currentRow.disk_capacity} GB` : '-' }}
          </el-descriptions-item>
          <el-descriptions-item :label="$t('itAssets.detail.diskType')">
            {{ currentRow.disk_type_display || '-' }}
          </el-descriptions-item>
          <el-descriptions-item
            :label="$t('itAssets.detail.gpu')"
            :span="2"
          >
            {{ currentRow.gpu_model || '-' }}
          </el-descriptions-item>
        </el-descriptions>

        <div class="section-title">
          {{ $t('itAssets.detail.networkInfo') }}
        </div>
        <el-descriptions
          :column="2"
          border
        >
          <el-descriptions-item :label="$t('itAssets.detail.hostname')">
            {{ currentRow.hostname || '-' }}
          </el-descriptions-item>
          <el-descriptions-item :label="$t('itAssets.columns.ipAddress')">
            {{ currentRow.ip_address || '-' }}
          </el-descriptions-item>
          <el-descriptions-item
            :label="$t('itAssets.columns.macAddress')"
            :span="2"
          >
            {{ currentRow.mac_address || '-' }}
          </el-descriptions-item>
        </el-descriptions>

        <div class="section-title">
          {{ $t('itAssets.detail.operatingSystem') }}
        </div>
        <el-descriptions
          :column="2"
          border
        >
          <el-descriptions-item :label="$t('itAssets.detail.osName')">
            {{ currentRow.os_name || '-' }}
          </el-descriptions-item>
          <el-descriptions-item :label="$t('itAssets.detail.version')">
            {{ currentRow.os_version || '-' }}
          </el-descriptions-item>
          <el-descriptions-item :label="$t('itAssets.detail.architecture')">
            {{ currentRow.os_architecture || '-' }}
          </el-descriptions-item>
          <el-descriptions-item :label="$t('itAssets.detail.licenseKey')">
            {{ currentRow.os_license_key ? '******' : '-' }}
          </el-descriptions-item>
        </el-descriptions>

        <div class="section-title">
          {{ $t('itAssets.columns.security') }}
        </div>
        <el-descriptions
          :column="2"
          border
        >
          <el-descriptions-item :label="$t('itAssets.detail.diskEncrypted')">
            <el-tag :type="currentRow.disk_encrypted ? 'success' : 'warning'">
              {{ currentRow.disk_encrypted ? $t('itAssets.status.yes') : $t('itAssets.status.no') }}
            </el-tag>
          </el-descriptions-item>
          <el-descriptions-item :label="$t('itAssets.detail.antivirus')">
            {{ currentRow.antivirus_software || '-' }}
          </el-descriptions-item>
          <el-descriptions-item :label="$t('itAssets.detail.antivirusEnabled')">
            <el-tag :type="currentRow.antivirus_enabled ? 'success' : 'danger'">
              {{ currentRow.antivirus_enabled ? $t('itAssets.status.yes') : $t('itAssets.status.no') }}
            </el-tag>
          </el-descriptions-item>
        </el-descriptions>

        <div class="section-title">
          {{ $t('itAssets.detail.activeDirectory') }}
        </div>
        <el-descriptions
          :column="2"
          border
        >
          <el-descriptions-item :label="$t('itAssets.detail.domain')">
            {{ currentRow.ad_domain || '-' }}
          </el-descriptions-item>
          <el-descriptions-item :label="$t('itAssets.detail.computerName')">
            {{ currentRow.ad_computer_name || '-' }}
          </el-descriptions-item>
        </el-descriptions>

        <div
          v-if="currentRow.full_config"
          class="section-title"
        >
          {{ $t('itAssets.detail.configSummary') }}
        </div>
        <el-alert
          v-if="currentRow.full_config"
          type="info"
          :closable="false"
        >
          {{ currentRow.full_config }}
        </el-alert>
      </div>
    </el-drawer>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { ElMessage } from 'element-plus'
import { useI18n } from 'vue-i18n'
import type { ITAssetInfo } from '@/api/itAssets'
import { itAssetInfoApi } from '@/api/itAssets'
import BaseListPage from '@/components/common/BaseListPage.vue'
import type { TableColumn, SearchField } from '@/types/common'
import ITAssetForm from './components/ITAssetForm.vue'

const { t } = useI18n()

const listRef = ref()
const dialogVisible = ref(false)
const detailDrawerVisible = ref(false)
const currentRow = ref<ITAssetInfo | null>(null)

const searchFields = computed<SearchField[]>(() => [
  {
    prop: 'search',
    label: t('itAssets.filters.search'),
    type: 'text',
    placeholder: t('itAssets.filters.searchPlaceholder')
  },
  {
    prop: 'os_name__icontains',
    label: t('itAssets.filters.os'),
    type: 'select',
    placeholder: t('itAssets.filters.allOs'),
    options: [
      { label: t('itAssets.filters.options.windows'), value: 'windows' },
      { label: t('itAssets.filters.options.macos'), value: 'macos' },
      { label: t('itAssets.filters.options.linux'), value: 'linux' }
    ]
  }
])

const formatCpu = (row: ITAssetInfo) => {
  const model = row.cpu_model
  const cores = row.cpu_cores
  if (model && cores) return `${model} (${cores} cores)`
  if (model) return model
  if (cores) return `${cores} cores`
  return '-'
}

const formatCapacity = (value?: number | string | null, unit = 'GB') => {
  if (value === null || value === undefined || value === '') return '-'
  return `${value} ${unit}`
}

const formatDisk = (row: ITAssetInfo) => {
  const capacity = row.disk_capacity ? `${row.disk_capacity} GB` : ''
  const type = row.disk_type ? String(row.disk_type) : ''
  if (capacity && type) return `${capacity} (${type})`
  return capacity || type || '-'
}

const formatOs = (row: ITAssetInfo) => {
  const name = row.os_name || ''
  const version = row.os_version || ''
  if (!name && !version) return '-'
  return `${name}${version ? ' ' + version : ''}`.trim()
}

const columns = computed<TableColumn[]>(() => [
  { prop: 'asset_code', label: t('itAssets.columns.assetCode'), width: 140 },
  { prop: 'asset_name', label: t('itAssets.columns.assetName'), minWidth: 180 },
  { prop: 'cpu_model', label: t('itAssets.columns.cpu'), minWidth: 150, format: (_v: any, row: ITAssetInfo) => formatCpu(row) },
  { prop: 'ram_capacity', label: t('itAssets.columns.ram'), width: 100, align: 'center', format: (value: any) => formatCapacity(value) },
  { prop: 'disk_capacity', label: t('itAssets.columns.disk'), width: 120, align: 'center', format: (_v: any, row: ITAssetInfo) => formatDisk(row) },
  { prop: 'os_name', label: t('itAssets.columns.os'), minWidth: 150, format: (_v: any, row: ITAssetInfo) => formatOs(row) },
  { prop: 'ip_address', label: t('itAssets.columns.ipAddress'), width: 140 },
  { prop: 'mac_address', label: t('itAssets.columns.macAddress'), width: 160 },
  {
    prop: 'disk_encrypted',
    label: t('itAssets.columns.security'),
    width: 100,
    align: 'center',
    tagType: (row: ITAssetInfo) => (row.disk_encrypted ? 'success' : 'warning'),
    format: (_v: any, row: ITAssetInfo) => (row.disk_encrypted ? t('itAssets.status.encrypted') : t('itAssets.status.notEncrypted'))
  },
  { prop: 'actions', label: t('itAssets.columns.actions'), width: 160, fixed: 'right', slot: true }
])

const fetchList = async (params: any) => {
  try {
    const res = await itAssetInfoApi.list({
      ...params,
      page_size: params.pageSize
    }) as any
    return {
      results: res.results || res.items || [],
      count: res.count || res.total || 0
    }
  } catch (error) {
    ElMessage.error(t('itAssets.messages.loadFailed'))
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

const handleView = (row: ITAssetInfo) => {
  currentRow.value = row
  detailDrawerVisible.value = true
}

const handleEdit = (row: ITAssetInfo) => {
  currentRow.value = row
  dialogVisible.value = true
}

const handleDelete = async (row: ITAssetInfo) => {
  try {
    await itAssetInfoApi.delete(row.id)
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
.it-asset-list {
  padding: 20px;
}

.asset-detail .section-title {
  margin: 20px 0 10px;
  font-size: 14px;
  font-weight: 600;
  color: #303133;
  border-left: 3px solid #409eff;
  padding-left: 10px;
}

.asset-detail .section-title:first-of-type {
  margin-top: 0;
}
</style>
