<template>
  <div class="page-container">
    <div
      v-if="loading"
      class="loading-container"
    >
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
            {{ detail.requestNo || $t('assets.lifecycle.disposalRequest.detailTitle') }}
          </h2>
          <el-tag
            :type="getStatusType(detail.status)"
            class="ml-2"
          >
            {{ getStatusLabel(detail.status) }}
          </el-tag>
        </div>
      </div>

      <!-- Workflow Actions -->
      <StatusActionBar
        :status="detail.status"
        :actions="workflowActions"
        @action-success="handleRefresh"
      />

      <!-- Status Steps -->
      <el-card class="steps-card mb-4">
        <el-steps
          :active="getStepIndex(detail.status)"
          finish-status="success"
        >
          <el-step :title="$t('assets.lifecycle.disposalRequest.status.draft')" />
          <el-step :title="$t('assets.lifecycle.disposalRequest.status.submitted')" />
          <el-step :title="$t('assets.lifecycle.disposalRequest.status.appraising')" />
          <el-step :title="$t('assets.lifecycle.disposalRequest.status.approved')" />
          <el-step :title="$t('assets.lifecycle.disposalRequest.status.completed')" />
        </el-steps>
      </el-card>

      <!-- Basic Info -->
      <el-card class="info-card">
        <el-descriptions
          :column="3"
          border
        >
          <el-descriptions-item :label="$t('assets.lifecycle.disposalRequest.columns.requestNo')">
            {{ detail.requestNo }}
          </el-descriptions-item>
          <el-descriptions-item :label="$t('assets.lifecycle.disposalRequest.columns.requesterDisplay')">
            {{ detail.requesterDisplay || '—' }}
          </el-descriptions-item>
          <el-descriptions-item :label="$t('assets.lifecycle.disposalRequest.columns.createdAt')">
            {{ detail.createdAt }}
          </el-descriptions-item>
          <el-descriptions-item
            :label="$t('assets.lifecycle.disposalRequest.form.disposalReason')"
            :span="3"
          >
            {{ detail.disposalReason }}
          </el-descriptions-item>
        </el-descriptions>
      </el-card>

      <!-- Disposal Items Sub-table -->
      <SubTablePanel
        :title="$t('assets.lifecycle.disposalRequest.form.itemsTitle')"
        :columns="itemColumns"
        :data="items"
        :loading="itemsLoading"
        :empty-text="$t('common.messages.noData')"
      />
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ArrowLeft } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import { useI18n } from 'vue-i18n'
import { disposalRequestApi } from '@/api/lifecycle'
import StatusActionBar, { type StatusAction } from '@/components/common/StatusActionBar.vue'
import SubTablePanel, { type SubTableColumn } from '@/components/common/SubTablePanel.vue'

const route = useRoute()
const router = useRouter()
const { t } = useI18n()
const id = route.params.id as string
const loading = ref(true)
const itemsLoading = ref(false)
const detail = ref<any>(null)
const items = ref<any[]>([])

const workflowActions = computed<StatusAction[]>(() => [
  {
    key: 'submit',
    label: t('assets.lifecycle.disposalRequest.actions.submit'),
    type: 'primary',
    confirmMessage: t('assets.lifecycle.disposalRequest.actions.submit') + '?',
    apiCall: () => disposalRequestApi.submit(id),
    visibleWhen: (s: string) => s === 'draft',
  },
  {
    key: 'startAppraisal',
    label: t('assets.lifecycle.disposalRequest.actions.startAppraisal'),
    type: 'primary',
    confirmMessage: t('assets.lifecycle.disposalRequest.actions.startAppraisal') + '?',
    apiCall: () => disposalRequestApi.startAppraisal(id),
    visibleWhen: (s: string) => s === 'submitted',
  },
  {
    key: 'approve',
    label: t('assets.lifecycle.disposalRequest.actions.approve'),
    type: 'success',
    confirmMessage: t('assets.lifecycle.disposalRequest.actions.approve') + '?',
    apiCall: () => disposalRequestApi.approve(id, 'approved'),
    visibleWhen: (s: string) => s === 'appraising',
  },
  {
    key: 'reject',
    label: t('assets.lifecycle.disposalRequest.actions.reject'),
    type: 'danger',
    confirmMessage: t('assets.lifecycle.disposalRequest.actions.reject') + '?',
    confirmType: 'warning',
    apiCall: () => disposalRequestApi.approve(id, 'rejected'),
    visibleWhen: (s: string) => s === 'appraising',
  },
  {
    key: 'cancel',
    label: t('assets.lifecycle.disposalRequest.actions.cancel'),
    type: 'default',
    confirmMessage: t('assets.lifecycle.disposalRequest.messages.cancelConfirm'),
    confirmType: 'warning',
    apiCall: () => disposalRequestApi.cancel(id),
    visibleWhen: (s: string) => ['draft', 'submitted'].includes(s),
  },
])

const itemColumns = computed<SubTableColumn[]>(() => [
  { prop: 'assetDisplay', label: t('assets.lifecycle.disposalRequest.form.assetLabel') },
  { prop: 'assetCode', label: t('assets.lifecycle.disposalRequest.form.assetCode'), width: 140 },
  { prop: 'disposalMethod', label: t('assets.lifecycle.disposalRequest.form.disposalMethod'), width: 140 },
  { prop: 'appraisalValue', label: t('assets.lifecycle.disposalRequest.form.appraisalValue'), width: 130, align: 'right' },
  { prop: 'actualDisposalValue', label: t('assets.lifecycle.disposalRequest.form.disposalValue'), width: 130, align: 'right' },
])

const statusSteps = ['draft', 'submitted', 'appraising', 'approved', 'completed']
const getStepIndex = (status: string) => Math.max(0, statusSteps.indexOf(status))
const getStatusType = (s: string) => {
  const map: Record<string, string> = {
    draft: 'info', submitted: 'warning', appraising: 'primary',
    approved: 'success', rejected: 'danger', executing: 'primary', completed: '', cancelled: 'info'
  }
  return map[s] || 'info'
}
const getStatusLabel = (s: string) => t(`assets.lifecycle.disposalRequest.status.${s}`) || s

const handleRefresh = async () => {
  try {
    detail.value = await disposalRequestApi.detail(id)
    const res = await disposalRequestApi.items(id) as any
    items.value = Array.isArray(res) ? res : (res.data || [])
  } catch { /* ignore */ }
}

onMounted(async () => {
  try {
    detail.value = await disposalRequestApi.detail(id)
    itemsLoading.value = true
    try {
      const res = await disposalRequestApi.items(id) as any
      items.value = Array.isArray(res) ? res : (res.data || [])
    } catch { /* optional */ }
    itemsLoading.value = false
  } catch {
    ElMessage.error(t('assets.lifecycle.disposalRequest.messages.loadFailed'))
  } finally {
    loading.value = false
  }
})
</script>

<style scoped lang="scss">
.detail-wrapper {
  .page-header {
    display: flex; align-items: center; justify-content: space-between; margin-bottom: 8px;
    .header-left { display: flex; align-items: center; gap: 12px; .page-title { margin: 0; font-size: 18px; } }
  }
  .mb-4 { margin-bottom: 16px; }
  .mt-4 { margin-top: 16px; }
  .ml-2 { margin-left: 8px; }
}
</style>
