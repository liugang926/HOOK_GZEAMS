<template>
  <div class="page-container">
    <BaseListPage
      ref="listRef"
      :title="$t('assets.lifecycle.maintenancePlan.title')"
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
          {{ $t('assets.lifecycle.maintenancePlan.createButton') }}
        </el-button>
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
          v-if="row.status === 'paused'"
          link
          type="success"
          @click="handleActivate(row)"
        >
          {{ $t('assets.lifecycle.maintenancePlan.actions.activate') }}
        </el-button>
        <el-button
          v-if="row.status === 'active'"
          link
          type="warning"
          @click="handlePause(row)"
        >
          {{ $t('assets.lifecycle.maintenancePlan.actions.pause') }}
        </el-button>
        <el-button
          v-if="['active', 'paused'].includes(row.status)"
          link
          type="info"
          @click="handleGenerateTasks(row)"
        >
          {{ $t('assets.lifecycle.maintenancePlan.actions.generateTasks') }}
        </el-button>
      </template>
    </BaseListPage>

    <ContextDrawer
      v-model="drawerVisible"
      object-code="MaintenancePlan"
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
import { maintenancePlanApi } from '@/api/lifecycle'
import BaseListPage from '@/components/common/BaseListPage.vue'
import ContextDrawer from '@/components/common/ContextDrawer.vue'
import type { TableColumn, SearchField } from '@/types/common'

const router = useRouter()
const { t } = useI18n()
const listRef = ref()

const fetchList = async (params: any) => {
  const res = await maintenancePlanApi.list({ ...params, page_size: params.pageSize }) as any
  return { results: res.results || res.items || [], count: res.count || res.total || 0 }
}

const statuses = ['active', 'paused', 'archived']

const searchFields: SearchField[] = [
  {
    prop: 'status',
    label: t('assets.lifecycle.maintenancePlan.columns.status'),
    type: 'select',
    options: statuses.map(s => ({
      label: t(`assets.lifecycle.maintenancePlan.status.${s}`),
      value: s
    }))
  },
  {
    prop: 'search',
    label: t('common.actions.search'),
    type: 'text',
    placeholder: t('assets.lifecycle.maintenancePlan.columns.planCode')
  }
]

const getStatusType = (s: string) => {
  const map: Record<string, string> = { active: 'success', paused: 'warning', archived: 'info' }
  return map[s] || 'info'
}
const getStatusLabel = (s: string) => t(`assets.lifecycle.maintenancePlan.status.${s}`) || s

const columns: TableColumn[] = [
  { prop: 'planCode', label: t('assets.lifecycle.maintenancePlan.columns.planCode'), width: 140 },
  { prop: 'planName', label: t('assets.lifecycle.maintenancePlan.columns.planName'), minWidth: 180 },
  { prop: 'cycleType', label: t('assets.lifecycle.maintenancePlan.columns.cycleType'), width: 110,
    format: (v: string) => t(`assets.lifecycle.maintenancePlan.cycle.${v}`) || v },
  { prop: 'startDate', label: t('assets.lifecycle.maintenancePlan.columns.startDate'), width: 120 },
  { prop: 'estimatedHours', label: t('assets.lifecycle.maintenancePlan.columns.estimatedHours'), width: 110, align: 'right' },
  { prop: 'status', label: t('assets.lifecycle.maintenancePlan.columns.status'), width: 100, slot: 'status' }
]

const drawerVisible = ref(false)
const handleCreate = () => { drawerVisible.value = true }
const handleDrawerSuccess = () => { listRef.value?.refresh() }
const handleView = (row: any) => router.push(`/assets/lifecycle/maintenance-plans/${row.id}`)

const handleActivate = async (row: any) => {
  try {
    await maintenancePlanApi.activate(row.id)
    ElMessage.success(t('assets.lifecycle.maintenancePlan.messages.activateSuccess'))
    listRef.value?.refresh()
  } catch (e: any) {
    ElMessage.error(e?.message || t('common.messages.operationFailed'))
  }
}

const handlePause = async (row: any) => {
  try {
    await maintenancePlanApi.pause(row.id)
    ElMessage.success(t('assets.lifecycle.maintenancePlan.messages.pauseSuccess'))
    listRef.value?.refresh()
  } catch (e: any) {
    ElMessage.error(e?.message || t('common.messages.operationFailed'))
  }
}

const handleGenerateTasks = async (row: any) => {
  try {
    await ElMessageBox.confirm(
      t('assets.lifecycle.maintenancePlan.messages.generateTasksConfirm'),
      t('common.messages.confirmTitle'),
      { type: 'info' }
    )
    const res: any = await maintenancePlanApi.generateTasks(row.id)
    ElMessage.success(
      t('assets.lifecycle.maintenancePlan.messages.generateTasksSuccess', {
        count: res?.generated_count || res?.data?.generated_count || '?'
      })
    )
    listRef.value?.refresh()
  } catch { /* cancelled */ }
}
</script>
