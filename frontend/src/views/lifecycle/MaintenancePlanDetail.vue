<template>
  <div class="page-container">
    <div v-if="loading">
      <el-skeleton
        :rows="8"
        animated
      />
    </div>
    <div
      v-else-if="detail"
      class="detail-wrapper"
    >
      <!-- Header -->
      <div class="page-header">
        <div class="header-left">
          <el-button
            :icon="ArrowLeft"
            @click="router.back()"
          >
            {{ $t('common.actions.back') }}
          </el-button>
          <h2 class="page-title">
            {{ $t('assets.lifecycle.maintenancePlan.detailTitle') }}
          </h2>
          <el-tag
            :type="getStatusType(detail.status)"
            class="ml-2"
          >
            {{ getStatusLabel(detail.status) }}
          </el-tag>
        </div>
        <div class="header-actions">
          <el-button
            v-if="detail.status === 'paused'"
            type="success"
            @click="handleActivate"
          >
            {{ $t('assets.lifecycle.maintenancePlan.actions.activate') }}
          </el-button>
          <el-button
            v-if="detail.status === 'active'"
            type="warning"
            @click="handlePause"
          >
            {{ $t('assets.lifecycle.maintenancePlan.actions.pause') }}
          </el-button>
          <el-button
            v-if="['active', 'paused'].includes(detail.status)"
            type="primary"
            @click="handleGenerateTasks"
          >
            {{ $t('assets.lifecycle.maintenancePlan.actions.generateTasks') }}
          </el-button>
          <el-button
            v-if="['active', 'paused'].includes(detail.status)"
            type="danger"
            @click="handleArchive"
          >
            {{ $t('assets.lifecycle.maintenancePlan.actions.archive') }}
          </el-button>
        </div>
      </div>

      <!-- Basic Info -->
      <el-card class="info-card">
        <el-descriptions
          :column="3"
          border
        >
          <el-descriptions-item :label="$t('assets.lifecycle.maintenancePlan.columns.planCode')">
            {{ detail.planCode }}
          </el-descriptions-item>
          <el-descriptions-item :label="$t('assets.lifecycle.maintenancePlan.columns.planName')">
            {{ detail.planName }}
          </el-descriptions-item>
          <el-descriptions-item :label="$t('assets.lifecycle.maintenancePlan.columns.cycleType')">
            {{ t(`assets.lifecycle.maintenancePlan.cycle.${detail.cycleType}`) || detail.cycleType }}
            <template v-if="detail.cycleValue > 1">
              &nbsp;×&nbsp;{{ detail.cycleValue }}
            </template>
          </el-descriptions-item>
          <el-descriptions-item :label="$t('assets.lifecycle.maintenancePlan.columns.startDate')">
            {{ detail.startDate }}
          </el-descriptions-item>
          <el-descriptions-item :label="$t('assets.lifecycle.maintenancePlan.form.endDate')">
            {{ detail.endDate || '—' }}
          </el-descriptions-item>
          <el-descriptions-item :label="$t('assets.lifecycle.maintenancePlan.columns.estimatedHours')">
            {{ detail.estimatedHours }} h
          </el-descriptions-item>
          <el-descriptions-item :label="$t('assets.lifecycle.maintenancePlan.form.remindDaysBefore')">
            {{ t('assets.lifecycle.maintenancePlan.form.daysBefore', { days: detail.remindDaysBefore }) }}
          </el-descriptions-item>
          <el-descriptions-item
            :label="$t('assets.lifecycle.maintenancePlan.form.maintenanceContent')"
            :span="3"
          >
            {{ detail.maintenanceContent }}
          </el-descriptions-item>
          <el-descriptions-item
            v-if="detail.remark"
            :label="$t('assets.lifecycle.maintenancePlan.form.remark')"
            :span="3"
          >
            {{ detail.remark }}
          </el-descriptions-item>
        </el-descriptions>
      </el-card>

      <!-- Last Generate Result -->
      <el-alert
        v-if="lastGenerateCount !== null"
        type="success"
        class="mt-4"
        :closable="true"
      >
        {{ $t('assets.lifecycle.maintenancePlan.messages.generateTasksSuccess', { count: lastGenerateCount }) }}
      </el-alert>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ArrowLeft } from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { useI18n } from 'vue-i18n'
import { maintenancePlanApi } from '@/api/lifecycle'

const route = useRoute()
const router = useRouter()
const { t } = useI18n()
const id = route.params.id as string
const loading = ref(true)
const detail = ref<any>(null)
const lastGenerateCount = ref<number | null>(null)

onMounted(async () => {
  try {
    detail.value = await maintenancePlanApi.detail(id)
  } catch {
    ElMessage.error(t('assets.lifecycle.maintenancePlan.messages.loadFailed'))
  } finally {
    loading.value = false
  }
})

const getStatusType = (s: string) => {
  const map: Record<string, string> = { active: 'success', paused: 'warning', archived: 'info' }
  return map[s] || 'info'
}
const getStatusLabel = (s: string) => t(`assets.lifecycle.maintenancePlan.status.${s}`) || s

const handleActivate = async () => {
  try {
    await maintenancePlanApi.activate(id)
    ElMessage.success(t('assets.lifecycle.maintenancePlan.messages.activateSuccess'))
    detail.value = await maintenancePlanApi.detail(id)
  } catch (e: any) { ElMessage.error(e?.message) }
}

const handlePause = async () => {
  try {
    await maintenancePlanApi.pause(id)
    ElMessage.success(t('assets.lifecycle.maintenancePlan.messages.pauseSuccess'))
    detail.value = await maintenancePlanApi.detail(id)
  } catch (e: any) { ElMessage.error(e?.message) }
}

const handleArchive = async () => {
  try {
    await ElMessageBox.confirm(t('assets.lifecycle.maintenancePlan.messages.archiveConfirm'), t('common.messages.confirmTitle'), { type: 'warning' })
    await maintenancePlanApi.archive(id)
    ElMessage.success(t('assets.lifecycle.maintenancePlan.messages.archiveSuccess'))
    detail.value = await maintenancePlanApi.detail(id)
  } catch { /* cancelled */ }
}

const handleGenerateTasks = async () => {
  try {
    await ElMessageBox.confirm(t('assets.lifecycle.maintenancePlan.messages.generateTasksConfirm'), t('common.messages.confirmTitle'), { type: 'info' })
    const res: any = await maintenancePlanApi.generateTasks(id)
    const count = res?.generated_count ?? res?.data?.generated_count ?? 0
    lastGenerateCount.value = count
    ElMessage.success(t('assets.lifecycle.maintenancePlan.messages.generateTasksSuccess', { count }))
  } catch { /* cancelled */ }
}
</script>

<style scoped lang="scss">
.detail-wrapper {
  .page-header { display: flex; align-items: center; justify-content: space-between; margin-bottom: 16px;
    .header-left { display: flex; align-items: center; gap: 12px; .page-title { margin: 0; font-size: 18px; } }
    .header-actions { display: flex; gap: 8px; }
  }
  .mt-4 { margin-top: 16px; }
  .ml-2 { margin-left: 8px; }
}
</style>
