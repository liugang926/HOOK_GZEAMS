<template>
  <div class="page-container">
    <div v-if="loading"><el-skeleton :rows="8" animated /></div>
    <div v-else-if="detail" class="detail-wrapper">
      <!-- Header -->
      <div class="page-header">
        <div class="header-left">
          <el-button :icon="ArrowLeft" @click="router.back()">{{ $t('common.actions.back') }}</el-button>
          <h2 class="page-title">{{ detail.planName || $t('assets.lifecycle.maintenancePlan.detailTitle') }}</h2>
          <el-tag :type="getStatusType(detail.status)" class="ml-2">{{ getStatusLabel(detail.status) }}</el-tag>
        </div>
      </div>

      <!-- Workflow Actions -->
      <StatusActionBar :status="detail.status" :actions="workflowActions" @action-success="handleRefresh" />

      <!-- Basic Info -->
      <el-card class="info-card">
        <el-descriptions :column="3" border>
          <el-descriptions-item :label="$t('assets.lifecycle.maintenancePlan.columns.planCode')">{{ detail.planCode }}</el-descriptions-item>
          <el-descriptions-item :label="$t('assets.lifecycle.maintenancePlan.columns.planName')">{{ detail.planName }}</el-descriptions-item>
          <el-descriptions-item :label="$t('assets.lifecycle.maintenancePlan.columns.cycleType')">
            {{ t(`assets.lifecycle.maintenancePlan.cycle.${detail.cycleType}`) || detail.cycleType }}
            <template v-if="detail.cycleValue > 1">&nbsp;&times;&nbsp;{{ detail.cycleValue }}</template>
          </el-descriptions-item>
          <el-descriptions-item :label="$t('assets.lifecycle.maintenancePlan.columns.startDate')">{{ detail.startDate }}</el-descriptions-item>
          <el-descriptions-item :label="$t('assets.lifecycle.maintenancePlan.form.endDate')">{{ detail.endDate || '—' }}</el-descriptions-item>
          <el-descriptions-item :label="$t('assets.lifecycle.maintenancePlan.columns.estimatedHours')">{{ detail.estimatedHours }} h</el-descriptions-item>
          <el-descriptions-item :label="$t('assets.lifecycle.maintenancePlan.form.remindDaysBefore')">
            {{ t('assets.lifecycle.maintenancePlan.form.daysBefore', { days: detail.remindDaysBefore }) }}
          </el-descriptions-item>
          <el-descriptions-item :label="$t('assets.lifecycle.maintenancePlan.form.maintenanceContent')" :span="3">{{ detail.maintenanceContent }}</el-descriptions-item>
          <el-descriptions-item v-if="detail.remark" :label="$t('assets.lifecycle.maintenancePlan.form.remark')" :span="3">{{ detail.remark }}</el-descriptions-item>
        </el-descriptions>
      </el-card>

      <!-- Last Generate Result -->
      <el-alert v-if="lastGenerateCount !== null" type="success" class="mt-4" :closable="true">
        {{ $t('assets.lifecycle.maintenancePlan.messages.generateTasksSuccess', { count: lastGenerateCount }) }}
      </el-alert>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ArrowLeft } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import { useI18n } from 'vue-i18n'
import { maintenancePlanApi } from '@/api/lifecycle'
import StatusActionBar, { type StatusAction } from '@/components/common/StatusActionBar.vue'

const route = useRoute()
const router = useRouter()
const { t } = useI18n()
const id = route.params.id as string
const loading = ref(true)
const detail = ref<any>(null)
const lastGenerateCount = ref<number | null>(null)

const workflowActions = computed<StatusAction[]>(() => [
  {
    key: 'activate',
    label: t('assets.lifecycle.maintenancePlan.actions.activate'),
    type: 'success',
    apiCall: () => maintenancePlanApi.activate(id),
    visibleWhen: (s: string) => s === 'paused',
  },
  {
    key: 'pause',
    label: t('assets.lifecycle.maintenancePlan.actions.pause'),
    type: 'warning',
    confirmMessage: t('assets.lifecycle.maintenancePlan.actions.pause') + '?',
    apiCall: () => maintenancePlanApi.pause(id),
    visibleWhen: (s: string) => s === 'active',
  },
  {
    key: 'generateTasks',
    label: t('assets.lifecycle.maintenancePlan.actions.generateTasks'),
    type: 'primary',
    confirmMessage: t('assets.lifecycle.maintenancePlan.messages.generateTasksConfirm'),
    apiCall: async () => {
      const res: any = await maintenancePlanApi.generateTasks(id)
      const count = res?.generated_count ?? res?.data?.generated_count ?? 0
      lastGenerateCount.value = count
      return res
    },
    visibleWhen: (s: string) => ['active', 'paused'].includes(s),
  },
  {
    key: 'archive',
    label: t('assets.lifecycle.maintenancePlan.actions.archive'),
    type: 'danger',
    confirmMessage: t('assets.lifecycle.maintenancePlan.messages.archiveConfirm'),
    confirmType: 'warning',
    apiCall: () => maintenancePlanApi.archive(id),
    visibleWhen: (s: string) => ['active', 'paused'].includes(s),
  },
])

const getStatusType = (s: string) => {
  const map: Record<string, string> = { active: 'success', paused: 'warning', archived: 'info' }
  return map[s] || 'info'
}
const getStatusLabel = (s: string) => t(`assets.lifecycle.maintenancePlan.status.${s}`) || s

const handleRefresh = async () => {
  try { detail.value = await maintenancePlanApi.detail(id) } catch { /* ignore */ }
}

onMounted(async () => {
  try { detail.value = await maintenancePlanApi.detail(id) }
  catch { ElMessage.error(t('assets.lifecycle.maintenancePlan.messages.loadFailed')) }
  finally { loading.value = false }
})
</script>

<style scoped lang="scss">
.detail-wrapper {
  .page-header {
    display: flex; align-items: center; justify-content: space-between; margin-bottom: 8px;
    .header-left { display: flex; align-items: center; gap: 12px; .page-title { margin: 0; font-size: 18px; } }
  }
  .mt-4 { margin-top: 16px; }
  .ml-2 { margin-left: 8px; }
}
</style>
