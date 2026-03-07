<template>
  <div class="page-container">
    <div v-if="loading">
      <el-skeleton :rows="8" animated />
    </div>
    <div v-else-if="detail" class="detail-wrapper">
      <!-- Header -->
      <div class="page-header">
        <div class="header-left">
          <el-button :icon="ArrowLeft" @click="router.back()">
            {{ $t('common.actions.back') }}
          </el-button>
          <h2 class="page-title">
            {{ detail.receiptNo || $t('assets.lifecycle.assetReceipt.detailTitle') }}
          </h2>
          <el-tag :type="getStatusType(detail.status)" class="ml-2">
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
        <el-steps :active="getStepIndex(detail.status)" finish-status="success">
          <el-step :title="$t('assets.lifecycle.assetReceipt.status.draft')" />
          <el-step :title="$t('assets.lifecycle.assetReceipt.status.submitted')" />
          <el-step :title="$t('assets.lifecycle.assetReceipt.status.inspecting')" />
          <el-step :title="$t('assets.lifecycle.assetReceipt.status.passed')" />
        </el-steps>
      </el-card>

      <!-- Basic Info -->
      <el-card class="info-card">
        <el-descriptions :column="3" border>
          <el-descriptions-item :label="$t('assets.lifecycle.assetReceipt.columns.receiptNo')">
            {{ detail.receiptNo }}
          </el-descriptions-item>
          <el-descriptions-item :label="$t('assets.lifecycle.assetReceipt.columns.supplier')">
            {{ detail.supplier || '—' }}
          </el-descriptions-item>
          <el-descriptions-item :label="$t('assets.lifecycle.assetReceipt.columns.deliveryNo')">
            {{ detail.deliveryNo || '—' }}
          </el-descriptions-item>
          <el-descriptions-item :label="$t('assets.lifecycle.assetReceipt.form.receiptDate')">
            {{ detail.receiptDate }}
          </el-descriptions-item>
          <el-descriptions-item :label="$t('assets.lifecycle.assetReceipt.columns.createdAt')">
            {{ detail.createdAt }}
          </el-descriptions-item>
          <el-descriptions-item
            v-if="detail.inspectionResult"
            :label="$t('assets.lifecycle.assetReceipt.form.inspectionResult')"
            :span="3"
          >
            {{ detail.inspectionResult }}
          </el-descriptions-item>
        </el-descriptions>
      </el-card>

      <!-- Items Sub-table -->
      <SubTablePanel
        :title="$t('assets.lifecycle.assetReceipt.form.itemsTitle')"
        :columns="itemColumns"
        :data="items"
        :loading="itemsLoading"
        :empty-text="$t('common.messages.noData')"
      >
        <template #assetGenerated="{ row }">
          <el-icon v-if="row.assetGenerated" color="#67c23a"><Check /></el-icon>
          <el-icon v-else color="#909399"><Close /></el-icon>
        </template>
      </SubTablePanel>
    </div>

    <!-- Inspection Dialog -->
    <el-dialog
      v-model="inspectDialog"
      :title="$t('assets.lifecycle.assetReceipt.dialog.inspectTitle')"
      width="480px"
      destroy-on-close
    >
      <el-form :model="inspectForm" label-width="120px">
        <el-form-item :label="$t('assets.lifecycle.assetReceipt.form.inspectionResult')">
          <el-input
            v-model="inspectForm.result"
            type="textarea"
            :rows="4"
            :placeholder="$t('assets.lifecycle.assetReceipt.dialog.inspectionResultPlaceholder')"
          />
        </el-form-item>
        <el-form-item :label="$t('assets.lifecycle.assetReceipt.dialog.passed')">
          <el-radio-group v-model="inspectForm.passed">
            <el-radio :value="true">{{ $t('assets.lifecycle.assetReceipt.dialog.passedYes') }}</el-radio>
            <el-radio :value="false">{{ $t('assets.lifecycle.assetReceipt.dialog.passedNo') }}</el-radio>
          </el-radio-group>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="inspectDialog = false">{{ $t('common.actions.cancel') }}</el-button>
        <el-button type="primary" @click="handleInspect">{{ $t('common.actions.confirm') }}</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, reactive, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ArrowLeft, Check, Close } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import { useI18n } from 'vue-i18n'
import { assetReceiptApi } from '@/api/lifecycle'
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
const inspectDialog = ref(false)
const inspectForm = reactive({ result: '', passed: true })

const workflowActions = computed<StatusAction[]>(() => [
  {
    key: 'submitInspection',
    label: t('assets.lifecycle.assetReceipt.actions.submitInspection'),
    type: 'primary',
    confirmMessage: t('assets.lifecycle.assetReceipt.actions.submitInspection') + '?',
    apiCall: () => assetReceiptApi.submitInspection(id),
    visibleWhen: (s: string) => s === 'draft',
  },
  {
    key: 'inspect',
    label: t('assets.lifecycle.assetReceipt.actions.inspect'),
    type: 'success',
    apiCall: async () => { inspectDialog.value = true },
    visibleWhen: (s: string) => s === 'inspecting',
  },
  {
    key: 'generateAssets',
    label: t('assets.lifecycle.assetReceipt.actions.generateAssets'),
    type: 'primary',
    confirmMessage: t('assets.lifecycle.assetReceipt.messages.generateAssetsConfirm'),
    confirmType: 'info',
    apiCall: () => assetReceiptApi.generateAssets(id),
    visibleWhen: (s: string) => s === 'passed',
  },
  {
    key: 'cancel',
    label: t('assets.lifecycle.assetReceipt.actions.cancel'),
    type: 'default',
    confirmMessage: t('assets.lifecycle.assetReceipt.messages.cancelConfirm'),
    confirmType: 'warning',
    apiCall: () => assetReceiptApi.cancel(id),
    visibleWhen: (s: string) => ['draft', 'submitted'].includes(s),
  },
])

const itemColumns = computed<SubTableColumn[]>(() => [
  { prop: 'itemName', label: t('assets.lifecycle.assetReceipt.form.itemName') },
  { prop: 'specification', label: t('assets.lifecycle.assetReceipt.form.specification'), width: 140 },
  { prop: 'orderedQuantity', label: t('assets.lifecycle.assetReceipt.form.orderedQuantity'), width: 100, align: 'right' },
  { prop: 'receivedQuantity', label: t('assets.lifecycle.assetReceipt.form.receivedQuantity'), width: 100, align: 'right' },
  { prop: 'qualifiedQuantity', label: t('assets.lifecycle.assetReceipt.form.qualifiedQuantity'), width: 100, align: 'right' },
  { prop: 'unitPrice', label: t('assets.lifecycle.assetReceipt.form.unitPrice'), width: 110, align: 'right' },
  { prop: 'totalAmount', label: t('assets.lifecycle.assetReceipt.form.totalAmount'), width: 120, align: 'right' },
  { prop: 'assetGenerated', label: t('assets.lifecycle.assetReceipt.form.assetGenerated'), width: 100, align: 'center', slot: 'assetGenerated' },
])

const statusSteps = ['draft', 'submitted', 'inspecting', 'passed']
const getStepIndex = (s: string) => Math.max(0, statusSteps.indexOf(s))
const getStatusType = (s: string) => {
  const map: Record<string, string> = {
    draft: 'info', submitted: 'warning', inspecting: 'primary',
    passed: 'success', rejected: 'danger', cancelled: 'info'
  }
  return map[s] || 'info'
}
const getStatusLabel = (s: string) => t(`assets.lifecycle.assetReceipt.status.${s}`) || s

const handleRefresh = async () => {
  try {
    detail.value = await assetReceiptApi.detail(id)
    const res = await assetReceiptApi.items(id) as any
    items.value = Array.isArray(res) ? res : (res.data || [])
  } catch { /* ignore */ }
}

const handleInspect = async () => {
  try {
    await assetReceiptApi.inspect(id, inspectForm.result, inspectForm.passed)
    ElMessage.success(inspectForm.passed
      ? t('assets.lifecycle.assetReceipt.messages.inspectPassSuccess')
      : t('assets.lifecycle.assetReceipt.messages.inspectFailSuccess'))
    inspectDialog.value = false
    await handleRefresh()
  } catch (e: any) { ElMessage.error(e?.message) }
}

onMounted(async () => {
  try {
    detail.value = await assetReceiptApi.detail(id)
    itemsLoading.value = true
    try {
      const res = await assetReceiptApi.items(id) as any
      items.value = Array.isArray(res) ? res : (res.data || [])
    } catch { /* optional */ }
    itemsLoading.value = false
  } catch {
    ElMessage.error(t('assets.lifecycle.assetReceipt.messages.loadFailed'))
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
