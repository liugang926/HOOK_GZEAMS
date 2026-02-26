<template>
  <div class="configuration-change-list">
    <BaseListPage
      ref="listRef"
      :title="t('itAssets.configChange.title')"
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
          {{ t('itAssets.common.addChange') }}
        </el-button>
      </template>

      <template #change_display="{ row }">
        <div class="change-display">
          <span class="old-value">{{ row.old_value || t('itAssets.configChange.empty') }}</span>
          <el-icon class="arrow-icon">
            <Right />
          </el-icon>
          <span class="new-value">{{ row.new_value || t('itAssets.configChange.empty') }}</span>
        </div>
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

    <!-- Configuration Change Form Dialog -->
    <ConfigurationChangeForm
      v-model:visible="dialogVisible"
      :data="currentRow"
      @success="handleRefresh"
    />

    <!-- Detail Drawer -->
    <el-drawer
      v-model="detailDrawerVisible"
      :title="$t('itAssets.configChange.title')"
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
          <el-descriptions-item :label="$t('itAssets.configChange.field')">
            {{ getFieldName(currentRow.field_name) }}
          </el-descriptions-item>
          <el-descriptions-item :label="$t('itAssets.common.date')">
            {{ currentRow.change_date }}
          </el-descriptions-item>
          <el-descriptions-item :label="$t('itAssets.common.changedBy')">
            {{ currentRow.changed_by_username || '-' }}
          </el-descriptions-item>
        </el-descriptions>

        <div class="section-title">
          {{ $t('itAssets.configChange.changeDetails') }}
        </div>
        <div class="change-comparison">
          <div class="change-side old">
            <div class="change-label">
              {{ $t('itAssets.configChange.oldValue') }}
            </div>
            <div class="change-value">
              {{ currentRow.old_value || $t('itAssets.configChange.empty') }}
            </div>
          </div>
          <el-icon class="change-arrow">
            <Right />
          </el-icon>
          <div class="change-side new">
            <div class="change-label">
              {{ $t('itAssets.configChange.newValue') }}
            </div>
            <div class="change-value">
              {{ currentRow.new_value || $t('itAssets.configChange.empty') }}
            </div>
          </div>
        </div>

        <div
          v-if="currentRow.change_reason"
          class="section-title"
        >
          {{ $t('itAssets.common.reason') }}
        </div>
        <div
          v-if="currentRow.change_reason"
          class="reason-text"
        >
          {{ currentRow.change_reason }}
        </div>
      </div>
    </el-drawer>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { ElMessage } from 'element-plus'
import { Right } from '@element-plus/icons-vue'
import type { ConfigurationChange } from '@/api/itAssets'
import { configurationChangeApi } from '@/api/itAssets'
import BaseListPage from '@/components/common/BaseListPage.vue'
import type { TableColumn, SearchField } from '@/types/common'
import ConfigurationChangeForm from './components/ConfigurationChangeForm.vue'
import { useI18n } from 'vue-i18n'

const { t } = useI18n()

const listRef = ref()
const dialogVisible = ref(false)
const detailDrawerVisible = ref(false)
const currentRow = ref<ConfigurationChange | null>(null)

const searchFields = computed<SearchField[]>(() => [
  {
    prop: 'search',
    label: t('itAssets.filters.search'),
    type: 'text',
    placeholder: t('itAssets.common.searchConfigPlaceholder')
  },
  {
    prop: 'field_name',
    label: t('itAssets.configChange.field'),
    type: 'select',
    placeholder: t('itAssets.configChange.allFields'),
    options: [
      { label: t('itAssets.configChange.fields.cpuModel'), value: 'cpu_model' },
      { label: t('itAssets.configChange.fields.ramCapacity'), value: 'ram_capacity' },
      { label: t('itAssets.configChange.fields.diskCapacity'), value: 'disk_capacity' },
      { label: t('itAssets.configChange.fields.osName'), value: 'os_name' },
      { label: t('itAssets.configChange.fields.ipAddress'), value: 'ip_address' }
    ]
  },
  {
    prop: 'change_date',
    label: t('itAssets.filters.dateRange'),
    type: 'dateRange'
  }
])

const columns = computed<TableColumn[]>(() => [
  { prop: 'asset_code', label: t('itAssets.common.asset'), width: 140 },
  {
    prop: 'field_name',
    label: t('itAssets.configChange.field'),
    width: 180,
    format: (_v: any, row: ConfigurationChange) => getFieldName(row.field_name)
  },
  { prop: 'change_display', label: t('itAssets.common.change'), minWidth: 300, slot: true },
  { prop: 'change_reason', label: t('itAssets.common.reason'), minWidth: 200 },
  { prop: 'change_date', label: t('itAssets.common.date'), width: 120 },
  { prop: 'changed_by_username', label: t('itAssets.common.changedBy'), width: 120 },
  { prop: 'actions', label: t('itAssets.columns.actions'), width: 160, fixed: 'right', slot: true }
])

const fetchList = async (params: any) => {
  try {
    const nextParams = { ...params }
    if (Array.isArray(nextParams.change_date) && nextParams.change_date.length === 2) {
      nextParams.change_date_from = nextParams.change_date[0]
      nextParams.change_date_to = nextParams.change_date[1]
      delete nextParams.change_date
    }

    const res = await configurationChangeApi.list({
      ...nextParams,
      page_size: nextParams.pageSize
    }) as any
    return {
      results: res.results || res.items || [],
      count: res.count || res.total || 0
    }
  } catch (error) {
    ElMessage.error(t('itAssets.messages.loadConfigFailed'))
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

const handleView = (row: ConfigurationChange) => {
  currentRow.value = row
  detailDrawerVisible.value = true
}

const handleEdit = (row: ConfigurationChange) => {
  currentRow.value = row
  dialogVisible.value = true
}

const handleDelete = async (row: ConfigurationChange) => {
  try {
    await configurationChangeApi.delete(row.id)
    ElMessage.success(t('itAssets.messages.deleteSuccess'))
    handleRefresh()
  } catch (error: any) {
    if (error !== 'cancel') {
      ElMessage.error(t('itAssets.messages.deleteFailed'))
    }
  }
}

const getFieldName = (field: string) => {
  const map: Record<string, string> = {
    'cpu_model': 'cpuModel',
    'ram_capacity': 'ramCapacity',
    'disk_capacity': 'diskCapacity',
    'os_name': 'osName',
    'ip_address': 'ipAddress'
  }
  const key = map[field]
  return key ? t(`itAssets.configChange.fields.${key}`) : field
}
</script>

<style scoped>
.change-display {
  display: flex;
  align-items: center;
  gap: 8px;
}

.old-value {
  color: #f56c6c;
  text-decoration: line-through;
}

.new-value {
  color: #67c23a;
  font-weight: 500;
}

.arrow-icon {
  color: #909399;
}

.detail-content .section-title {
  margin: 20px 0 10px;
  font-size: 14px;
  font-weight: 600;
  color: #303133;
  border-left: 3px solid #409eff;
  padding-left: 10px;
}

.change-comparison {
  display: flex;
  align-items: center;
  gap: 20px;
  padding: 15px;
  background: #f5f7fa;
  border-radius: 4px;
}

.change-side {
  flex: 1;
}

.change-label {
  font-size: 12px;
  color: #909399;
  margin-bottom: 5px;
}

.change-value {
  padding: 10px;
  background: white;
  border-radius: 4px;
  min-height: 40px;
  word-break: break-all;
}

.change-side.old .change-value {
  color: #f56c6c;
  text-decoration: line-through;
}

.change-side.new .change-value {
  color: #67c23a;
  font-weight: 500;
}

.change-arrow {
  font-size: 20px;
  color: #409eff;
}

.reason-text {
  padding: 10px;
  background: #f5f7fa;
  border-radius: 4px;
  white-space: pre-wrap;
  line-height: 1.6;
}
</style>
