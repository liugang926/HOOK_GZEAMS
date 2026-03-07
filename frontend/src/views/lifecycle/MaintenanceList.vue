<template>
  <div class="page-container">
    <BaseListPage
      ref="listRef"
      :title="$t('assets.lifecycle.maintenance.title')"
      :search-fields="searchFields"
      :table-columns="columns"
      :api="fetchList"
    >
      <template #toolbar>
        <el-button
          type="primary"
          :icon="Plus"
          @click="handleCreate"
        >
          {{ $t('assets.lifecycle.maintenance.createButton') }}
        </el-button>
      </template>

      <template #priority="{ row }">
        <el-tag
          :type="getPriorityType(row.priority)"
          size="small"
        >
          {{ getPriorityLabel(row.priority) }}
        </el-tag>
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
          v-if="['pending', 'assigned', 'in_progress'].includes(row.status)"
          link
          type="danger"
          @click="handleCancel(row)"
        >
          {{ $t('assets.lifecycle.maintenance.actions.cancel') }}
        </el-button>
      </template>
    </BaseListPage>

    <ContextDrawer
      v-model="drawerVisible"
      object-code="Maintenance"
      size="800px"
      @success="handleDrawerSuccess"
    />
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { Plus } from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { useI18n } from 'vue-i18n'
import { maintenanceApi } from '@/api/lifecycle'
import BaseListPage from '@/components/common/BaseListPage.vue'
import ContextDrawer from '@/components/common/ContextDrawer.vue'
import type { TableColumn, SearchField } from '@/types/common'

const router = useRouter()
const { t } = useI18n()
const listRef = ref()

const fetchList = async (params: any) => {
  const res = await maintenanceApi.list({
    ...params,
    page_size: params.pageSize
  }) as any
  return {
    results: res.results || res.items || [],
    count: res.count || res.total || 0
  }
}

const priorities = ['low', 'normal', 'high', 'urgent']
const statuses = ['pending', 'assigned', 'in_progress', 'completed', 'verified', 'cancelled']

const searchFields: SearchField[] = [
  {
    prop: 'priority',
    label: t('assets.lifecycle.maintenance.columns.priority'),
    type: 'select',
    options: priorities.map(p => ({
      label: t(`assets.lifecycle.maintenance.priority.${p}`),
      value: p
    }))
  },
  {
    prop: 'status',
    label: t('assets.lifecycle.maintenance.columns.status'),
    type: 'select',
    options: statuses.map(s => ({
      label: t(`assets.lifecycle.maintenance.status.${s}`),
      value: s
    }))
  },
  {
    prop: 'search',
    label: t('common.actions.search'),
    type: 'text',
    placeholder: t('assets.lifecycle.maintenance.columns.maintenanceNo')
  }
]

const getPriorityType = (p: string) => {
  const map: Record<string, string> = { low: 'info', normal: '', high: 'warning', urgent: 'danger' }
  return map[p] || ''
}
const getPriorityLabel = (p: string) => t(`assets.lifecycle.maintenance.priority.${p}`) || p

const getStatusType = (s: string) => {
  const map: Record<string, string> = {
    pending: 'info', assigned: 'warning', in_progress: 'primary',
    completed: 'warning', verified: 'success', cancelled: 'info'
  }
  return map[s] || 'info'
}
const getStatusLabel = (s: string) => t(`assets.lifecycle.maintenance.status.${s}`) || s

const columns: TableColumn[] = [
  { prop: 'maintenanceNo', label: t('assets.lifecycle.maintenance.columns.maintenanceNo'), width: 160 },
  { prop: 'assetDisplay', label: t('assets.lifecycle.maintenance.columns.assetDisplay'), width: 140 },
  { prop: 'faultDescription', label: t('assets.lifecycle.maintenance.columns.faultDescription'), minWidth: 180 },
  { prop: 'priority', label: t('assets.lifecycle.maintenance.columns.priority'), width: 90, slot: 'priority' },
  { prop: 'status', label: t('assets.lifecycle.maintenance.columns.status'), width: 110, slot: 'status' },
  { prop: 'technicianDisplay', label: t('assets.lifecycle.maintenance.columns.technicianDisplay'), width: 100 },
  { prop: 'createdAt', label: t('assets.lifecycle.maintenance.columns.createdAt'), width: 160 }
]

const drawerVisible = ref(false)
const handleCreate = () => { drawerVisible.value = true }
const handleDrawerSuccess = () => { listRef.value?.refresh() }
const handleView = (row: any) => router.push(`/assets/lifecycle/maintenance/${row.id}`)

const handleCancel = async (row: any) => {
  try {
    await ElMessageBox.confirm(
      t('assets.lifecycle.maintenance.messages.cancelConfirm'),
      t('common.messages.confirmTitle'),
      { type: 'warning' }
    )
    await maintenanceApi.cancel(row.id)
    ElMessage.success(t('assets.lifecycle.maintenance.messages.cancelSuccess'))
    listRef.value?.refresh()
  } catch { /* user cancelled */ }
}
</script>
