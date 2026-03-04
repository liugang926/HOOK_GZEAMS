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
            {{ $t('assets.lifecycle.purchaseRequest.detailTitle') }}
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
            {{ $t('assets.lifecycle.purchaseRequest.actions.submit') }}
          </el-button>
          <el-button
            v-if="detail.status === 'submitted'"
            type="success"
            @click="handleApprove"
          >
            {{ $t('assets.lifecycle.purchaseRequest.actions.approve') }}
          </el-button>
          <el-button
            v-if="detail.status === 'submitted'"
            type="danger"
            @click="handleReject"
          >
            {{ $t('assets.lifecycle.purchaseRequest.actions.reject') }}
          </el-button>
          <el-button
            v-if="['draft', 'submitted'].includes(detail.status)"
            @click="handleCancel"
          >
            {{ $t('assets.lifecycle.purchaseRequest.actions.cancel') }}
          </el-button>
        </div>
      </div>

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
            {{ detail.requesterDisplay || '—' }}
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
      <el-card class="items-card mt-4">
        <template #header>
          <span>{{ $t('assets.lifecycle.purchaseRequest.form.itemsTitle') }}</span>
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
            :label="$t('assets.lifecycle.purchaseRequest.form.assetName')"
            prop="assetName"
          />
          <el-table-column
            :label="$t('assets.lifecycle.purchaseRequest.form.specification')"
            prop="specification"
            width="160"
          />
          <el-table-column
            :label="$t('assets.lifecycle.purchaseRequest.form.quantity')"
            prop="quantity"
            width="100"
            align="right"
          />
          <el-table-column
            :label="$t('assets.lifecycle.purchaseRequest.form.estimatedUnitPrice')"
            prop="estimatedUnitPrice"
            width="130"
            align="right"
          />
          <el-table-column
            :label="$t('assets.lifecycle.purchaseRequest.form.supplier')"
            prop="supplierDisplay"
            width="140"
          />
          <el-table-column
            :label="$t('assets.lifecycle.purchaseRequest.form.remark')"
            prop="remark"
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
import { purchaseRequestApi } from '@/api/lifecycle'

const route = useRoute()
const router = useRouter()
const { t } = useI18n()
const loading = ref(true)
const detail = ref<any>(null)
const items = ref<any[]>([])

const id = route.params.id as string

onMounted(async () => {
  try {
    detail.value = await purchaseRequestApi.detail(id)
    try {
      const res = await purchaseRequestApi.items(id) as any
      items.value = Array.isArray(res) ? res : (res.data || [])
    } catch { /* items endpoint may not exist */ }
  } catch {
    ElMessage.error(t('assets.lifecycle.purchaseRequest.messages.loadFailed'))
  } finally {
    loading.value = false
  }
})

const getStatusType = (status: string) => {
  const map: Record<string, string> = {
    draft: 'info', submitted: 'warning', approved: 'success',
    rejected: 'danger', processing: 'primary', completed: '', cancelled: 'info'
  }
  return map[status] || 'info'
}
const getStatusLabel = (status: string) =>
  t(`assets.lifecycle.purchaseRequest.status.${status}`) || status

const handleSubmit = async () => {
  try {
    await ElMessageBox.confirm(t('assets.lifecycle.purchaseRequest.actions.submit'), t('common.messages.confirmTitle'), { type: 'info' })
    await purchaseRequestApi.submit(id)
    ElMessage.success(t('assets.lifecycle.purchaseRequest.messages.submitSuccess'))
    detail.value = await purchaseRequestApi.detail(id)
  } catch { /* cancelled */ }
}

const handleApprove = async () => {
  try {
    await ElMessageBox.confirm(t('assets.lifecycle.purchaseRequest.actions.approve'), t('common.messages.confirmTitle'), { type: 'success' })
    await purchaseRequestApi.approve(id, 'approved')
    ElMessage.success(t('assets.lifecycle.purchaseRequest.messages.approveSuccess'))
    detail.value = await purchaseRequestApi.detail(id)
  } catch { /* cancelled */ }
}

const handleReject = async () => {
  try {
    const { value: comment } = await ElMessageBox.prompt(
      t('assets.lifecycle.purchaseRequest.dialog.rejectCommentPlaceholder'),
      t('assets.lifecycle.purchaseRequest.dialog.rejectTitle'),
      { inputType: 'textarea', confirmButtonText: t('common.actions.confirm'), cancelButtonText: t('common.actions.cancel') }
    )
    await purchaseRequestApi.approve(id, 'rejected', comment)
    ElMessage.success(t('assets.lifecycle.purchaseRequest.messages.rejectSuccess'))
    detail.value = await purchaseRequestApi.detail(id)
  } catch { /* cancelled */ }
}

const handleCancel = async () => {
  try {
    await ElMessageBox.confirm(t('assets.lifecycle.purchaseRequest.messages.cancelConfirm'), t('common.messages.confirmTitle'), { type: 'warning' })
    await purchaseRequestApi.cancel(id)
    ElMessage.success(t('assets.lifecycle.purchaseRequest.messages.cancelSuccess'))
    detail.value = await purchaseRequestApi.detail(id)
  } catch { /* cancelled */ }
}
</script>

<style scoped lang="scss">
.detail-wrapper {
  .page-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin-bottom: 16px;
    .header-left {
      display: flex;
      align-items: center;
      gap: 12px;
      .page-title { margin: 0; font-size: 18px; }
    }
    .header-actions { display: flex; gap: 8px; }
  }
  .mt-4 { margin-top: 16px; }
  .ml-2 { margin-left: 8px; }
}
</style>
