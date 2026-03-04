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
            {{ $t('assets.lifecycle.disposalRequest.detailTitle') }}
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
            v-if="detail.status === 'draft'"
            type="primary"
            @click="handleSubmit"
          >
            {{ $t('assets.lifecycle.disposalRequest.actions.submit') }}
          </el-button>
          <el-button
            v-if="detail.status === 'submitted'"
            type="primary"
            @click="handleStartAppraisal"
          >
            {{ $t('assets.lifecycle.disposalRequest.actions.startAppraisal') }}
          </el-button>
          <el-button
            v-if="detail.status === 'appraising'"
            type="success"
            @click="handleApprove"
          >
            {{ $t('assets.lifecycle.disposalRequest.actions.approve') }}
          </el-button>
          <el-button
            v-if="detail.status === 'appraising'"
            type="danger"
            @click="handleReject"
          >
            {{ $t('assets.lifecycle.disposalRequest.actions.reject') }}
          </el-button>
          <el-button
            v-if="['draft', 'submitted'].includes(detail.status)"
            @click="handleCancel"
          >
            {{ $t('assets.lifecycle.disposalRequest.actions.cancel') }}
          </el-button>
        </div>
      </div>

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
      <el-card class="items-card mt-4">
        <template #header>
          <span>{{ $t('assets.lifecycle.disposalRequest.form.itemsTitle') }}</span>
        </template>
        <el-table
          :data="items"
          border
          stripe
        >
          <el-table-column
            type="index"
            width="50"
          />
          <el-table-column
            :label="$t('assets.lifecycle.disposalRequest.form.assetLabel')"
            prop="assetDisplay"
          />
          <el-table-column
            label="Asset Code"
            prop="assetCode"
            width="140"
          />
          <el-table-column
            label="Disposal Method"
            prop="disposalMethod"
            width="140"
          />
          <el-table-column
            label="Appraisal Value"
            prop="appraisalValue"
            width="130"
            align="right"
          />
          <el-table-column
            label="Disposal Value"
            prop="actualDisposalValue"
            width="130"
            align="right"
          />
        </el-table>
      </el-card>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ArrowLeft } from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { useI18n } from 'vue-i18n'
import { disposalRequestApi } from '@/api/lifecycle'

const route = useRoute()
const router = useRouter()
const { t } = useI18n()
const id = route.params.id as string
const loading = ref(true)
const detail = ref<any>(null)
const items = ref<any[]>([])

onMounted(async () => {
  try {
    detail.value = await disposalRequestApi.detail(id)
    try {
      const res = await disposalRequestApi.items(id) as any
      items.value = Array.isArray(res) ? res : (res.data || [])
    } catch { /* items endpoint optional */ }
  } catch {
    ElMessage.error(t('assets.lifecycle.disposalRequest.messages.loadFailed'))
  } finally {
    loading.value = false
  }
})

const statusSteps = ['draft', 'submitted', 'appraising', 'approved', 'completed']
const getStepIndex = (status: string) => Math.max(0, statusSteps.indexOf(status))

const getStatusType = (s: string) => {
  const map: Record<string, string> = {
    draft: 'info', submitted: 'warning', appraising: 'primary',
    approved: 'success', rejected: 'danger',
    executing: 'primary', completed: '', cancelled: 'info'
  }
  return map[s] || 'info'
}
const getStatusLabel = (s: string) => t(`assets.lifecycle.disposalRequest.status.${s}`) || s

const handleSubmit = async () => {
  try {
    await ElMessageBox.confirm(t('assets.lifecycle.disposalRequest.actions.submit'), t('common.messages.confirmTitle'), { type: 'info' })
    await disposalRequestApi.submit(id)
    ElMessage.success(t('assets.lifecycle.disposalRequest.messages.submitSuccess'))
    detail.value = await disposalRequestApi.detail(id)
  } catch { /* cancelled */ }
}

const handleStartAppraisal = async () => {
  try {
    await disposalRequestApi.startAppraisal(id)
    ElMessage.info(t('assets.lifecycle.disposalRequest.actions.startAppraisal'))
    detail.value = await disposalRequestApi.detail(id)
  } catch (e: any) {
    ElMessage.error(e?.message || t('common.messages.operationFailed'))
  }
}

const handleApprove = async () => {
  try {
    await ElMessageBox.confirm(t('assets.lifecycle.disposalRequest.actions.approve'), t('common.messages.confirmTitle'), { type: 'success' })
    await disposalRequestApi.approve(id, 'approved')
    ElMessage.success(t('assets.lifecycle.disposalRequest.messages.approveSuccess'))
    detail.value = await disposalRequestApi.detail(id)
  } catch { /* cancelled */ }
}

const handleReject = async () => {
  try {
    const { value: comment } = await ElMessageBox.prompt(
      t('common.messages.rejectReason'),
      t('assets.lifecycle.disposalRequest.actions.reject'),
      { inputType: 'textarea', confirmButtonText: t('common.actions.confirm'), cancelButtonText: t('common.actions.cancel') }
    )
    await disposalRequestApi.approve(id, 'rejected', comment)
    ElMessage.success(t('assets.lifecycle.disposalRequest.messages.rejectSuccess'))
    detail.value = await disposalRequestApi.detail(id)
  } catch { /* cancelled */ }
}

const handleCancel = async () => {
  try {
    await ElMessageBox.confirm(t('assets.lifecycle.disposalRequest.messages.cancelConfirm'), t('common.messages.confirmTitle'), { type: 'warning' })
    await disposalRequestApi.cancel(id)
    ElMessage.success(t('assets.lifecycle.disposalRequest.messages.cancelSuccess'))
    detail.value = await disposalRequestApi.detail(id)
  } catch { /* cancelled */ }
}
</script>

<style scoped lang="scss">
.detail-wrapper {
  .page-header {
    display: flex; align-items: center; justify-content: space-between; margin-bottom: 16px;
    .header-left { display: flex; align-items: center; gap: 12px; .page-title { margin: 0; font-size: 18px; } }
    .header-actions { display: flex; gap: 8px; }
  }
  .mb-4 { margin-bottom: 16px; }
  .mt-4 { margin-top: 16px; }
  .ml-2 { margin-left: 8px; }
}
</style>
