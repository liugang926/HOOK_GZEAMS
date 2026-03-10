<template>
  <div
    v-loading="loading"
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
          {{ detail.warrantyNo || $t('assets.lifecycle.assetWarranty.detailTitle') }}
        </h2>
        <el-tag
          :type="getStatusType(detail.status)"
          class="ml-2"
        >
          {{ $t(`assets.lifecycle.assetWarranty.status.${detail.status || 'draft'}`) }}
        </el-tag>
      </div>
      <div class="header-right">
        <el-button
          v-if="detail.status === 'draft'"
          type="success"
          @click="handleActivate"
        >
          {{ $t('assets.lifecycle.assetWarranty.actions.activate') }}
        </el-button>
        <el-button
          v-if="['active', 'expiring'].includes(detail.status)"
          type="warning"
          @click="handleRenew"
        >
          {{ $t('assets.lifecycle.assetWarranty.actions.renew') }}
        </el-button>
        <el-button
          v-if="['active', 'expiring'].includes(detail.status)"
          type="primary"
          @click="handleRecordClaim"
        >
          {{ $t('assets.lifecycle.assetWarranty.actions.recordClaim') }}
        </el-button>
        <el-button
          v-if="!['cancelled', 'expired'].includes(detail.status)"
          type="danger"
          @click="handleCancel"
        >
          {{ $t('assets.lifecycle.assetWarranty.actions.cancel') }}
        </el-button>
      </div>
    </div>

    <!-- Basic Info -->
    <el-card class="info-card">
      <el-descriptions
        :column="3"
        border
      >
        <el-descriptions-item :label="$t('assets.lifecycle.assetWarranty.columns.warrantyNo')">
          {{ detail.warranty_no }}
        </el-descriptions-item>
        <el-descriptions-item :label="$t('assets.lifecycle.assetWarranty.columns.warrantyType')">
          {{ $t(`assets.lifecycle.assetWarranty.warrantyType.${detail.warranty_type || 'manufacturer'}`) }}
        </el-descriptions-item>
        <el-descriptions-item :label="$t('assets.lifecycle.assetWarranty.columns.status')">
          <el-tag
            :type="getStatusType(detail.status)"
            size="small"
          >
            {{ $t(`assets.lifecycle.assetWarranty.status.${detail.status || 'draft'}`) }}
          </el-tag>
        </el-descriptions-item>
        <el-descriptions-item :label="$t('assets.lifecycle.assetWarranty.columns.assetName')">
          {{ detail.asset_name || detail.asset_code }}
        </el-descriptions-item>
        <el-descriptions-item :label="$t('assets.lifecycle.assetWarranty.columns.startDate')">
          {{ detail.start_date }}
        </el-descriptions-item>
        <el-descriptions-item :label="$t('assets.lifecycle.assetWarranty.columns.endDate')">
          {{ detail.end_date }}
        </el-descriptions-item>
      </el-descriptions>
    </el-card>

    <!-- Provider Info -->
    <el-card class="info-card">
      <template #header>
        <span>{{ $t('assets.lifecycle.assetWarranty.sections.providerInfo') }}</span>
      </template>
      <el-descriptions
        :column="2"
        border
      >
        <el-descriptions-item :label="$t('assets.lifecycle.assetWarranty.columns.warrantyProvider')">
          {{ detail.warranty_provider }}
        </el-descriptions-item>
        <el-descriptions-item :label="$t('assets.lifecycle.assetWarranty.form.providerContact')">
          {{ detail.provider_contact }}
        </el-descriptions-item>
        <el-descriptions-item :label="$t('assets.lifecycle.assetWarranty.form.providerPhone')">
          {{ detail.provider_phone }}
        </el-descriptions-item>
        <el-descriptions-item :label="$t('assets.lifecycle.assetWarranty.form.providerEmail')">
          {{ detail.provider_email }}
        </el-descriptions-item>
      </el-descriptions>
    </el-card>

    <!-- Financial & Coverage Info -->
    <el-card class="info-card">
      <template #header>
        <span>{{ $t('assets.lifecycle.assetWarranty.sections.coverageInfo') }}</span>
      </template>
      <el-descriptions
        :column="2"
        border
      >
        <el-descriptions-item :label="$t('assets.lifecycle.assetWarranty.columns.warrantyCost')">
          {{ detail.warranty_cost ? `¥${detail.warranty_cost}` : '-' }}
        </el-descriptions-item>
        <el-descriptions-item :label="$t('assets.lifecycle.assetWarranty.form.contractNo')">
          {{ detail.contract_no || '-' }}
        </el-descriptions-item>
        <el-descriptions-item :label="$t('assets.lifecycle.assetWarranty.columns.claimCount')">
          {{ detail.claim_count || 0 }}
        </el-descriptions-item>
        <el-descriptions-item :label="$t('assets.lifecycle.assetWarranty.form.lastClaimDate')">
          {{ detail.last_claim_date || '-' }}
        </el-descriptions-item>
        <el-descriptions-item
          :label="$t('assets.lifecycle.assetWarranty.form.coverageDescription')"
          :span="2"
        >
          {{ detail.coverage_description || '-' }}
        </el-descriptions-item>
        <el-descriptions-item
          :label="$t('assets.lifecycle.assetWarranty.form.remark')"
          :span="2"
        >
          {{ detail.remark || '-' }}
        </el-descriptions-item>
      </el-descriptions>
    </el-card>

    <!-- Renew Dialog -->
    <el-dialog
      v-model="renewDialogVisible"
      :title="$t('assets.lifecycle.assetWarranty.dialog.renewTitle')"
      width="500px"
    >
      <el-form label-width="120px">
        <el-form-item :label="$t('assets.lifecycle.assetWarranty.form.newEndDate')">
          <el-date-picker
            v-model="renewForm.end_date"
            type="date"
            value-format="YYYY-MM-DD"
            style="width: 100%"
          />
        </el-form-item>
        <el-form-item :label="$t('assets.lifecycle.assetWarranty.columns.warrantyCost')">
          <el-input-number
            v-model="renewForm.warranty_cost"
            :min="0"
            :precision="2"
            style="width: 100%"
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="renewDialogVisible = false">
          {{ $t('common.actions.cancel') }}
        </el-button>
        <el-button
          type="primary"
          @click="submitRenew"
        >
          {{ $t('common.actions.confirm') }}
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { ElMessage, ElMessageBox } from 'element-plus'
import { ArrowLeft } from '@element-plus/icons-vue'
import { assetWarrantyApi } from '@/api/lifecycle'

const route = useRoute()
const router = useRouter()
const { t } = useI18n()
const id = route.params.id as string

// ─── State ──────────────────────────────────────────────────────────────────
const loading = ref(false)
const detail = ref<any>({})
const renewDialogVisible = ref(false)
const renewForm = ref({ end_date: '', warranty_cost: 0 })

// ─── Status Helper ──────────────────────────────────────────────────────────
const getStatusType = (status: string) => {
  const map: Record<string, string> = {
    draft: 'info',
    active: 'success',
    expiring: 'warning',
    expired: 'danger',
    claimed: '',
    cancelled: 'info'
  }
  return map[status] || 'info'
}

// ─── Data Loading ───────────────────────────────────────────────────────────
const loadData = async () => {
  loading.value = true
  try {
    detail.value = await assetWarrantyApi.detail(id)
  } catch { /* handled by interceptor */ } finally {
    loading.value = false
  }
}

// ─── Workflow Actions ───────────────────────────────────────────────────────
const handleActivate = async () => {
  try {
    await ElMessageBox.confirm(
      t('assets.lifecycle.assetWarranty.messages.activateConfirm'),
      t('common.actions.confirm'),
      { type: 'info' }
    )
    await assetWarrantyApi.activate(id)
    ElMessage.success(t('assets.lifecycle.assetWarranty.messages.activateSuccess'))
    loadData()
  } catch { /* cancelled */ }
}

const handleRenew = () => {
  renewForm.value = {
    end_date: '',
    warranty_cost: detail.value.warranty_cost || 0
  }
  renewDialogVisible.value = true
}

const submitRenew = async () => {
  if (!renewForm.value.end_date) {
    ElMessage.warning(t('assets.lifecycle.assetWarranty.messages.endDateRequired'))
    return
  }
  try {
    await assetWarrantyApi.renew(id, renewForm.value)
    ElMessage.success(t('assets.lifecycle.assetWarranty.messages.renewSuccess'))
    renewDialogVisible.value = false
    loadData()
  } catch { /* handled by interceptor */ }
}

const handleRecordClaim = async () => {
  try {
    await ElMessageBox.confirm(
      t('assets.lifecycle.assetWarranty.messages.claimConfirm'),
      t('common.actions.confirm'),
      { type: 'warning' }
    )
    await assetWarrantyApi.recordClaim(id)
    ElMessage.success(t('assets.lifecycle.assetWarranty.messages.claimSuccess'))
    loadData()
  } catch { /* cancelled */ }
}

const handleCancel = async () => {
  try {
    await ElMessageBox.confirm(
      t('assets.lifecycle.assetWarranty.messages.cancelConfirm'),
      t('common.actions.confirm'),
      { type: 'warning' }
    )
    await assetWarrantyApi.cancel(id)
    ElMessage.success(t('assets.lifecycle.assetWarranty.messages.cancelSuccess'))
    loadData()
  } catch { /* cancelled */ }
}

onMounted(loadData)
</script>

<style scoped>
.detail-wrapper {
  padding: 16px;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 12px;
}

.header-right {
  display: flex;
  gap: 8px;
}

.page-title {
  margin: 0;
  font-size: 18px;
  font-weight: 600;
}

.info-card {
  margin-bottom: 16px;
}
</style>
