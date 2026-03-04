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
            {{ $t('assets.lifecycle.assetReceipt.detailTitle') }}
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
            @click="handleSubmitInspection"
          >
            {{ $t('assets.lifecycle.assetReceipt.actions.submitInspection') }}
          </el-button>
          <el-button
            v-if="detail.status === 'inspecting'"
            type="success"
            @click="inspectDialog = true"
          >
            {{ $t('assets.lifecycle.assetReceipt.actions.inspect') }}
          </el-button>
          <el-button
            v-if="detail.status === 'passed'"
            type="primary"
            @click="handleGenerateAssets"
          >
            {{ $t('assets.lifecycle.assetReceipt.actions.generateAssets') }}
          </el-button>
          <el-button
            v-if="['draft', 'submitted'].includes(detail.status)"
            @click="handleCancel"
          >
            {{ $t('assets.lifecycle.assetReceipt.actions.cancel') }}
          </el-button>
        </div>
      </div>

      <!-- Status Steps -->
      <el-card class="steps-card mb-4">
        <el-steps
          :active="getStepIndex(detail.status)"
          finish-status="success"
        >
          <el-step :title="$t('assets.lifecycle.assetReceipt.status.draft')" />
          <el-step :title="$t('assets.lifecycle.assetReceipt.status.submitted')" />
          <el-step :title="$t('assets.lifecycle.assetReceipt.status.inspecting')" />
          <el-step :title="$t('assets.lifecycle.assetReceipt.status.passed')" />
        </el-steps>
      </el-card>

      <!-- Basic Info -->
      <el-card class="info-card">
        <el-descriptions
          :column="3"
          border
        >
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
      <el-card class="items-card mt-4">
        <template #header>
          <span>{{ $t('assets.lifecycle.assetReceipt.form.itemsTitle') }}</span>
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
            :label="$t('assets.lifecycle.assetReceipt.form.itemName')"
            prop="itemName"
          />
          <el-table-column
            :label="$t('assets.lifecycle.assetReceipt.form.specification')"
            prop="specification"
            width="140"
          />
          <el-table-column
            :label="$t('assets.lifecycle.assetReceipt.form.orderedQuantity')"
            prop="orderedQuantity"
            width="100"
            align="right"
          />
          <el-table-column
            :label="$t('assets.lifecycle.assetReceipt.form.receivedQuantity')"
            prop="receivedQuantity"
            width="100"
            align="right"
          />
          <el-table-column
            :label="$t('assets.lifecycle.assetReceipt.form.qualifiedQuantity')"
            prop="qualifiedQuantity"
            width="100"
            align="right"
          />
          <el-table-column
            :label="$t('assets.lifecycle.assetReceipt.form.unitPrice')"
            prop="unitPrice"
            width="110"
            align="right"
          />
          <el-table-column
            :label="$t('assets.lifecycle.assetReceipt.form.totalAmount')"
            prop="totalAmount"
            width="120"
            align="right"
          />
          <el-table-column
            :label="$t('assets.lifecycle.assetReceipt.form.assetGenerated')"
            width="100"
            align="center"
          >
            <template #default="{ row }">
              <el-icon
                v-if="row.assetGenerated"
                color="#67c23a"
              >
                <Check />
              </el-icon>
              <el-icon
                v-else
                color="#909399"
              >
                <Close />
              </el-icon>
            </template>
          </el-table-column>
        </el-table>
      </el-card>
    </div>

    <!-- Inspection Dialog -->
    <el-dialog
      v-model="inspectDialog"
      :title="$t('assets.lifecycle.assetReceipt.dialog.inspectTitle')"
      width="480px"
      destroy-on-close
    >
      <el-form
        :model="inspectForm"
        label-width="120px"
      >
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
            <el-radio :value="true">
              {{ $t('assets.lifecycle.assetReceipt.dialog.passedYes') }}
            </el-radio>
            <el-radio :value="false">
              {{ $t('assets.lifecycle.assetReceipt.dialog.passedNo') }}
            </el-radio>
          </el-radio-group>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="inspectDialog = false">
          {{ $t('common.actions.cancel') }}
        </el-button>
        <el-button
          type="primary"
          @click="handleInspect"
        >
          {{ $t('common.actions.confirm') }}
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, reactive } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ArrowLeft, Check, Close } from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { useI18n } from 'vue-i18n'
import { assetReceiptApi } from '@/api/lifecycle'

const route = useRoute()
const router = useRouter()
const { t } = useI18n()
const id = route.params.id as string
const loading = ref(true)
const detail = ref<any>(null)
const items = ref<any[]>([])
const inspectDialog = ref(false)
const inspectForm = reactive({ result: '', passed: true })

onMounted(async () => {
  try {
    detail.value = await assetReceiptApi.detail(id)
    try {
      const res = await assetReceiptApi.items(id) as any
      items.value = Array.isArray(res) ? res : (res.data || [])
    } catch { /* optional */ }
  } catch {
    ElMessage.error(t('assets.lifecycle.assetReceipt.messages.loadFailed'))
  } finally {
    loading.value = false
  }
})

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

const handleSubmitInspection = async () => {
  try {
    await assetReceiptApi.submitInspection(id)
    ElMessage.success(t('assets.lifecycle.assetReceipt.messages.submitInspectionSuccess'))
    detail.value = await assetReceiptApi.detail(id)
  } catch (e: any) { ElMessage.error(e?.message) }
}

const handleInspect = async () => {
  try {
    await assetReceiptApi.inspect(id, inspectForm.result, inspectForm.passed)
    ElMessage.success(inspectForm.passed
      ? t('assets.lifecycle.assetReceipt.messages.inspectPassSuccess')
      : t('assets.lifecycle.assetReceipt.messages.inspectFailSuccess'))
    inspectDialog.value = false
    detail.value = await assetReceiptApi.detail(id)
  } catch (e: any) { ElMessage.error(e?.message) }
}

const handleGenerateAssets = async () => {
  try {
    await ElMessageBox.confirm(t('assets.lifecycle.assetReceipt.messages.generateAssetsConfirm'), t('common.messages.confirmTitle'), { type: 'success' })
    await assetReceiptApi.generateAssets(id)
    ElMessage.success(t('assets.lifecycle.assetReceipt.messages.generateAssetsSuccess'))
    detail.value = await assetReceiptApi.detail(id)
    const res = await assetReceiptApi.items(id) as any
    items.value = Array.isArray(res) ? res : (res.data || [])
  } catch { /* cancelled */ }
}

const handleCancel = async () => {
  try {
    await ElMessageBox.confirm(t('assets.lifecycle.assetReceipt.messages.cancelConfirm'), t('common.messages.confirmTitle'), { type: 'warning' })
    await assetReceiptApi.cancel(id)
    ElMessage.success(t('assets.lifecycle.assetReceipt.messages.cancelSuccess'))
    detail.value = await assetReceiptApi.detail(id)
  } catch { /* cancelled */ }
}
</script>

<style scoped lang="scss">
.detail-wrapper {
  .page-header { display: flex; align-items: center; justify-content: space-between; margin-bottom: 16px;
    .header-left { display: flex; align-items: center; gap: 12px; .page-title { margin: 0; font-size: 18px; } }
    .header-actions { display: flex; gap: 8px; }
  }
  .mb-4 { margin-bottom: 16px; }
  .mt-4 { margin-top: 16px; }
  .ml-2 { margin-left: 8px; }
}
</style>
