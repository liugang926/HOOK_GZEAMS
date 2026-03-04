<template>
  <div class="page-container">
    <BaseListPage
      ref="listRef"
      :title="$t('assets.lifecycle.maintenanceTask.title')"
      :search-fields="searchFields"
      :table-columns="columns"
      :api="fetchList"
    >
      <template #quickFilters>
        <div class="quick-filters">
          <el-button
            size="small"
            :icon="Warning"
            type="danger"
            @click="loadOverdue"
          >
            {{ $t('assets.lifecycle.maintenanceTask.filter.overdue') }}
          </el-button>
          <el-button
            size="small"
            :icon="Calendar"
            type="primary"
            @click="loadToday"
          >
            {{ $t('assets.lifecycle.maintenanceTask.filter.today') }}
          </el-button>
          <el-button
            size="small"
            @click="loadAll"
          >
            {{ $t('assets.lifecycle.maintenanceTask.filter.all') }}
          </el-button>
        </div>
      </template>

      <template #status="{ row }">
        <el-tag
          :type="getStatusType(row.status)"
          size="small"
        >
          {{ getStatusLabel(row.status) }}
        </el-tag>
      </template>

      <template #actions="{ row }">
        <el-button
          link
          type="primary"
          @click="handleView(row)"
        >
          {{ $t('common.actions.view') }}
        </el-button>
        <el-button
          v-if="['pending', 'in_progress'].includes(row.status)"
          link
          type="success"
          @click="router.push(`/assets/lifecycle/maintenance-tasks/${row.id}`)"
        >
          {{ $t('assets.lifecycle.maintenanceTask.actions.execute') }}
        </el-button>
        <el-button
          v-if="row.status === 'pending'"
          link
          type="warning"
          @click="handleSkip(row)"
        >
          {{ $t('assets.lifecycle.maintenanceTask.actions.skip') }}
        </el-button>
      </template>
    </BaseListPage>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { Warning, Calendar } from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { useI18n } from 'vue-i18n'
import { maintenanceTaskApi } from '@/api/maintenanceTasks'
import BaseListPage from '@/components/common/BaseListPage.vue'
import type { TableColumn, SearchField } from '@/types/common'

const router = useRouter()
const { t } = useI18n()
const listRef = ref()
const filterMode = ref<'all' | 'overdue' | 'today'>('all')

const fetchList = async (params: any) => {
  if (filterMode.value === 'overdue') {
    const res = await maintenanceTaskApi.overdue() as any
    const arr = Array.isArray(res) ? res : (res.data || [])
    return { results: arr, count: arr.length }
  }
  if (filterMode.value === 'today') {
    const res = await maintenanceTaskApi.today() as any
    const arr = Array.isArray(res) ? res : (res.data || [])
    return { results: arr, count: arr.length }
  }
  const res = await maintenanceTaskApi.list({ ...params, page_size: params.pageSize }) as any
  return { results: res.results || res.items || [], count: res.count || res.total || 0 }
}

const statuses = ['pending', 'in_progress', 'completed', 'verified', 'skipped']

const searchFields: SearchField[] = [
  {
    prop: 'status',
    label: t('assets.lifecycle.maintenanceTask.columns.status'),
    type: 'select',
    options: statuses.map(s => ({
      label: t(`assets.lifecycle.maintenanceTask.status.${s}`),
      value: s
    }))
  },
  {
    prop: 'search',
    label: t('common.actions.search'),
    type: 'text',
    placeholder: t('assets.lifecycle.maintenanceTask.columns.taskNo')
  }
]

const getStatusType = (s: string) => {
  const map: Record<string, string> = {
    pending: 'warning', in_progress: 'primary',
    completed: 'success', verified: '', skipped: 'info'
  }
  return map[s] || 'info'
}
const getStatusLabel = (s: string) => t(`assets.lifecycle.maintenanceTask.status.${s}`) || s

const columns: TableColumn[] = [
  { prop: 'taskNo', label: t('assets.lifecycle.maintenanceTask.columns.taskNo'), width: 160 },
  { prop: 'assetDisplay', label: t('assets.lifecycle.maintenanceTask.columns.asset'), width: 140 },
  { prop: 'maintenanceContent', label: t('assets.lifecycle.maintenanceTask.columns.maintenanceContent'), minWidth: 200 },
  { prop: 'scheduledDate', label: t('assets.lifecycle.maintenanceTask.columns.scheduledDate'), width: 120 },
  { prop: 'status', label: t('assets.lifecycle.maintenanceTask.columns.status'), width: 110, slot: 'status' }
]

const loadOverdue = () => { filterMode.value = 'overdue'; listRef.value?.refresh() }
const loadToday = () => { filterMode.value = 'today'; listRef.value?.refresh() }
const loadAll = () => { filterMode.value = 'all'; listRef.value?.refresh() }
const handleView = (row: any) => router.push(`/assets/lifecycle/maintenance-tasks/${row.id}`)

const handleSkip = async (row: any) => {
  try {
    const { value: reason } = await ElMessageBox.prompt(
      t('assets.lifecycle.maintenanceTask.dialog.skipReasonPlaceholder'),
      t('assets.lifecycle.maintenanceTask.actions.skip'),
      { inputType: 'textarea', confirmButtonText: t('common.actions.confirm'), cancelButtonText: t('common.actions.cancel') }
    )
    await maintenanceTaskApi.skip(row.id, reason)
    ElMessage.success(t('assets.lifecycle.maintenanceTask.messages.skipSuccess'))
    listRef.value?.refresh()
  } catch { /* cancelled */ }
}
</script>

<style scoped lang="scss">
.quick-filters { display: flex; gap: 8px; margin-bottom: 8px; }
</style>
