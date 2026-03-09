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
            {{ detail.requestNo || $t('assets.lifecycle.purchaseRequest.detailTitle') }}
          </h2>
          <el-tag
            :type="getStatusType(detail.status)"
            class="ml-2"
          >
            {{ getStatusLabel(detail.status) }}
          </el-tag>
        </div>
        <div class="header-right">
          <el-button
            v-if="['approved', 'processing'].includes(detail.status)"
            type="success"
            @click="handleCreateReceipt"
          >
            {{ $t('assets.lifecycle.purchaseRequest.actions.createReceipt') }}
          </el-button>
        </div>
      </div>

      <!-- Workflow Actions -->
      <StatusActionBar
        :status="detail.status"
        :actions="workflowActions"
        @action-success="handleRefresh"
      />

      <!-- Basic Info -->
      <el-card class="info-card">
        <el-descriptions
          :column="3"
          border
        >
          <el-descriptions-item :label="$t('assets.lifecycle.purchaseRequest.columns.requestNo')">
            {{ detail.requestNo }}
          </el-descriptions-item>
          <el-descriptions-item :label="$t('assets.lifecycle.purchaseRequest.columns.requester')">
            {{ detail.requesterDisplay || detail.applicantDisplay || '—' }}
          </el-descriptions-item>
          <el-descriptions-item :label="$t('assets.lifecycle.purchaseRequest.columns.department')">
            {{ detail.departmentDisplay || '—' }}
          </el-descriptions-item>
          <el-descriptions-item
            :label="$t('assets.lifecycle.purchaseRequest.form.reason')"
            :span="3"
          >
            {{ detail.reason }}
          </el-descriptions-item>
          <el-descriptions-item :label="$t('assets.lifecycle.purchaseRequest.columns.totalAmount')">
            {{ detail.totalAmount ? `¥ ${detail.totalAmount}` : '—' }}
          </el-descriptions-item>
          <el-descriptions-item :label="$t('assets.lifecycle.purchaseRequest.columns.createdAt')">
            {{ detail.createdAt }}
          </el-descriptions-item>
        </el-descriptions>
      </el-card>

      <!-- Items Sub-table -->
      <SubTablePanel
        :title="$t('assets.lifecycle.purchaseRequest.form.itemsTitle')"
        :columns="itemColumns"
        :data="items"
        :loading="itemsLoading"
        :show-summary="true"
        :summary-method="summaryMethod"
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
import { purchaseRequestApi } from '@/api/lifecycle'
import StatusActionBar, { type StatusAction } from '@/components/common/StatusActionBar.vue'
import SubTablePanel, { type SubTableColumn } from '@/components/common/SubTablePanel.vue'

const route = useRoute()
const router = useRouter()
const { t } = useI18n()
const loading = ref(true)
const itemsLoading = ref(false)
const detail = ref<any>(null)
const items = ref<any[]>([])

const id = route.params.id as string

const workflowActions = computed<StatusAction[]>(() => [
  {
    key: 'submit',
    label: t('assets.lifecycle.purchaseRequest.actions.submit'),
    type: 'primary',
    confirmMessage: t('assets.lifecycle.purchaseRequest.actions.submit') + '?',
    apiCall: () => purchaseRequestApi.submit(id),
    visibleWhen: (s: string) => s === 'draft',
  },
  {
    key: 'approve',
    label: t('assets.lifecycle.purchaseRequest.actions.approve'),
    type: 'success',
    confirmMessage: t('assets.lifecycle.purchaseRequest.actions.approve') + '?',
    apiCall: () => purchaseRequestApi.approve(id, 'approved'),
    visibleWhen: (s: string) => s === 'submitted',
  },
  {
    key: 'reject',
    label: t('assets.lifecycle.purchaseRequest.actions.reject'),
    type: 'danger',
    confirmMessage: t('assets.lifecycle.purchaseRequest.actions.reject') + '?',
    confirmType: 'warning',
    apiCall: () => purchaseRequestApi.approve(id, 'rejected'),
    visibleWhen: (s: string) => s === 'submitted',
  },
  {
    key: 'complete',
    label: t('assets.lifecycle.purchaseRequest.actions.complete'),
    type: 'success',
    confirmMessage: t('common.actions.complete') + '?',
    apiCall: () => purchaseRequestApi.complete(id),
    visibleWhen: (s: string) => s === 'processing',
  },
  {
    key: 'cancel',
    label: t('assets.lifecycle.purchaseRequest.actions.cancel'),
    type: 'default',
    confirmMessage: t('assets.lifecycle.purchaseRequest.messages.cancelConfirm'),
    confirmType: 'warning',
    apiCall: () => purchaseRequestApi.cancel(id),
    visibleWhen: (s: string) => ['draft', 'submitted'].includes(s),
  },
])

const itemColumns = computed<SubTableColumn[]>(() => [
  { prop: 'itemName', label: t('assets.lifecycle.purchaseRequest.form.assetName') },
  { prop: 'specification', label: t('assets.lifecycle.purchaseRequest.form.specification'), width: 160 },
  { prop: 'quantity', label: t('assets.lifecycle.purchaseRequest.form.quantity'), width: 100, align: 'right' },
  { prop: 'unitPrice', label: t('assets.lifecycle.purchaseRequest.form.estimatedUnitPrice'), width: 130, align: 'right' },
  { prop: 'totalAmount', label: t('assets.lifecycle.purchaseRequest.columns.totalAmount'), width: 130, align: 'right' },
  { prop: 'suggestedSupplier', label: t('assets.lifecycle.purchaseRequest.form.supplier'), width: 140 },
  { prop: 'remark', label: t('assets.lifecycle.purchaseRequest.form.remark') },
])

const summaryMethod = ({ columns, data }: { columns: any[]; data: any[] }) => {
  return columns.map((col: any, index: number) => {
    if (index === 0) return t('common.labels.total')
    if (col.property === 'totalAmount') {
      const sum = data.reduce((acc, row) => acc + (Number(row.totalAmount) || 0), 0)
      return `¥ ${sum.toFixed(2)}`
    }
    if (col.property === 'quantity') {
      return data.reduce((acc, row) => acc + (Number(row.quantity) || 0), 0)
    }
    return ''
  })
}

const getStatusType = (status: string) => {
  const map: Record<string, string> = {
    draft: 'info', submitted: 'warning', approved: 'success',
    rejected: 'danger', processing: 'primary', completed: '', cancelled: 'info'
  }
  return map[status] || 'info'
}
const getStatusLabel = (status: string) =>
  t(`assets.lifecycle.purchaseRequest.status.${status}`) || status

const handleRefresh = async () => {
  try {
    detail.value = await purchaseRequestApi.detail(id)
    const res = await purchaseRequestApi.items(id) as any
    items.value = Array.isArray(res) ? res : (res.data || [])
  } catch { /* ignore */ }
}

const handleCreateReceipt = () => {
  router.push({
    path: '/assets/lifecycle/asset-receipts/create',
    query: { purchaseRequestId: id, purchaseRequestNo: detail.value?.requestNo || '' }
  })
}

onMounted(async () => {
  try {
    detail.value = await purchaseRequestApi.detail(id)
    itemsLoading.value = true
    try {
      const res = await purchaseRequestApi.items(id) as any
      items.value = Array.isArray(res) ? res : (res.data || [])
    } catch { /* items endpoint may not exist */ }
    itemsLoading.value = false
  } catch {
    ElMessage.error(t('assets.lifecycle.purchaseRequest.messages.loadFailed'))
  } finally {
    loading.value = false
  }
})
</script>

<style scoped lang="scss">
.detail-wrapper {
  .page-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin-bottom: 8px;
    .header-left {
      display: flex;
      align-items: center;
      gap: 12px;
      .page-title { margin: 0; font-size: 18px; }
    }
  }
  .mt-4 { margin-top: 16px; }
  .ml-2 { margin-left: 8px; }
}
</style>
