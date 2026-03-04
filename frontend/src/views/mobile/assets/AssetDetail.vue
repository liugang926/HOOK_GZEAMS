<!--
  Mobile Asset Detail View

  Mobile-optimized asset detail page using Vant UI.
  Features:
  - Responsive layout with Vant components
  - Touch-optimized interactions
  - Action sheet for additional options
  - Timeline for operation history
  - Full i18n support
-->

<template>
  <div class="mobile-asset-detail">
    <van-nav-bar
      :title="$t('mobile.assetDetail.title')"
      :left-text="$t('common.actions.back')"
      left-arrow
      @click-left="goBack"
    >
      <template #right>
        <van-icon
          name="ellipsis"
          size="18"
          @click="showActions = true"
        />
      </template>
    </van-nav-bar>

    <!-- Loading State -->
    <div
      v-if="loading"
      class="loading-container"
    >
      <van-loading
        size="24px"
        color="#409eff"
      >
        {{ $t('common.status.loading') }}
      </van-loading>
    </div>

    <!-- Asset Content -->
    <div
      v-else-if="asset"
      class="asset-content"
    >
      <!-- Asset Header Card -->
      <van-cell-group
        inset
        class="header-card"
      >
        <div class="asset-header">
          <div class="asset-code">
            {{ asset.code }}
          </div>
          <van-tag :type="getStatusType(asset.status)">
            {{ getStatusLabel(asset.status) }}
          </van-tag>
        </div>
        <div class="asset-name">
          {{ asset.name }}
        </div>
        <div
          v-if="asset.categoryName"
          class="asset-category"
        >
          <van-tag
            type="primary"
            plain
            size="medium"
          >
            {{ asset.categoryName }}
          </van-tag>
        </div>
      </van-cell-group>

      <!-- Basic Information -->
      <van-cell-group
        inset
        :title="$t('mobile.assetDetail.basicInfo')"
      >
        <van-cell
          :title="$t('assets.fields.assetCode')"
          :value="asset.code"
        />
        <van-cell
          :title="$t('assets.fields.assetName')"
          :value="asset.name"
        />
        <van-cell
          :title="$t('assets.fields.category')"
          :value="asset.categoryName || '-'"
        />
        <van-cell
          :title="$t('assets.fields.purchasePrice')"
          :value="`¥${formatMoney(asset.purchasePrice)}`"
        />
        <van-cell
          :title="$t('assets.fields.purchaseDate')"
          :value="asset.purchaseDate"
        />
        <van-cell
          :title="$t('assets.fields.model')"
          :value="asset.specification || '-'"
        />
      </van-cell-group>

      <!-- Location & Custodian -->
      <van-cell-group
        inset
        :title="$t('mobile.assetDetail.usageInfo')"
      >
        <van-cell
          :title="$t('assets.fields.location')"
          :value="asset.locationName || '-'"
          is-link
        />
        <van-cell
          :title="$t('assets.fields.user')"
          :value="asset.custodianName || '-'"
        />
        <van-cell
          :title="$t('assets.fields.department')"
          :value="asset.departmentName || '-'"
        />
      </van-cell-group>

      <!-- Custom Fields -->
      <van-cell-group
        v-if="hasCustomFields"
        inset
        :title="$t('mobile.assetDetail.maintenanceInfo')"
      >
        <van-cell
          v-for="(value, key) in asset.customFields"
          :key="key"
          :title="getFieldLabel(key)"
          :value="formatCustomFieldValue(value)"
        />
      </van-cell-group>

      <!-- Purchase Info -->
      <van-cell-group
        v-if="asset.supplierName"
        inset
        :title="$t('assets.fields.supplier')"
      >
        <van-cell
          :title="$t('assets.fields.supplier')"
          :value="asset.supplierName"
        />
        <van-cell
          :title="$t('assets.fields.supplier') + $t('common.labels.contact')"
          value="-"
        />
      </van-cell-group>

      <!-- Notes -->
      <van-cell-group
        v-if="asset.description"
        inset
        :title="$t('common.labels.description')"
      >
        <van-cell>
          <template #title>
            <div class="description-text">
              {{ asset.description }}
            </div>
          </template>
        </van-cell>
      </van-cell-group>

      <!-- QR Code Card -->
      <van-cell-group
        inset
        :title="$t('mobile.assetDetail.scanQR')"
      >
        <div class="qr-code-card">
          <div class="qr-code-placeholder">
            <van-icon
              name="qr-code"
              size="64"
              color="#409eff"
            />
            <p class="qr-hint">
              {{ asset.code }}
            </p>
          </div>
          <van-button
            type="primary"
            size="small"
            icon="photo"
            @click="handleShowQRCode"
          >
            {{ $t('mobile.actions.scanQR') }}
          </van-button>
        </div>
      </van-cell-group>

      <!-- Operation Timeline -->
      <van-cell-group
        inset
        :title="$t('mobile.assetDetail.scanRecord')"
      >
        <div class="timeline-container">
          <van-empty
            v-if="!timeline || timeline.length === 0"
            :description="$t('common.table.noData')"
          />
          <van-steps
            v-else
            direction="vertical"
            :active="timeline.length"
          >
            <van-step
              v-for="(item, index) in timeline"
              :key="index"
            >
              <template #icon>
                <van-icon :name="getStepIcon(item.type)" />
              </template>
              <template #title>
                <span class="step-title">{{ item.title }}</span>
                <span class="step-time">{{ formatTime(item.createdAt) }}</span>
              </template>
              <template #default>
                <p class="step-desc">
                  {{ item.description }}
                </p>
                <p
                  v-if="item.operator"
                  class="step-operator"
                >
                  {{ $t('common.labels.createdBy') }}: {{ item.operator }}
                </p>
              </template>
            </van-step>
          </van-steps>
        </div>
      </van-cell-group>

      <!-- Bottom Actions -->
      <div class="bottom-actions">
        <van-button
          type="primary"
          size="large"
          icon="edit"
          @click="handleEdit"
        >
          {{ $t('common.actions.edit') }}
        </van-button>
        <van-button
          size="large"
          icon="share-o"
          @click="handleTransfer"
        >
          {{ $t('mobile.actions.transfer') }}
        </van-button>
      </div>
    </div>

    <!-- Error State -->
    <van-empty
      v-else
      :description="$t('mobile.messages.assetNotFound')"
    />

    <!-- Action Sheet -->
    <van-action-sheet
      v-model:show="showActions"
      :actions="actionItems"
      :cancel-text="$t('common.actions.cancel')"
      @select="handleAction"
    />

    <!-- QR Code Dialog -->
    <van-dialog
      v-model:show="qrCodeVisible"
      :title="$t('mobile.assetDetail.scanQR')"
      :show-confirm-button="false"
    >
      <div class="qr-dialog-content">
        <div class="qr-large-placeholder">
          <van-icon
            name="qr-code"
            size="160"
            color="#000"
          />
          <p class="qr-code-text">
            {{ asset?.code }}
          </p>
        </div>
        <p class="qr-hint-text">
          {{ $t('mobile.messages.scanSuccess') }}
        </p>
      </div>
      <template #footer>
        <van-button @click="qrCodeVisible = false">
          {{ $t('common.actions.close') }}
        </van-button>
        <van-button
          type="primary"
          @click="handleDownloadQR"
        >
          {{ $t('common.actions.download') }}
        </van-button>
      </template>
    </van-dialog>
  </div>
</template>

<script setup lang="ts">
/**
 * Mobile Asset Detail View
 *
 * Mobile-optimized asset detail page using Vant UI components with full i18n support.
 */

import { ref, computed, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { showToast, showDialog } from 'vant'
import type { Asset, AssetStatus } from '@/types/assets'
import { assetApi } from '@/api/assets'
import { formatMoney } from '@/utils/numberFormat'

const router = useRouter()
const route = useRoute()
const { t } = useI18n()

// ============================================================================
// State
// ============================================================================

const loading = ref(true)
const asset = ref<Asset | null>(null)
const showActions = ref(false)
const qrCodeVisible = ref(false)
const timeline = ref<any[]>([])

// ============================================================================
// Action Items (computed to react to language changes)
// ============================================================================

const actionItems = computed(() => [
  { name: t('common.actions.edit') + ' ' + t('assets.fields.assetName'), icon: 'edit' },
  { name: t('assets.operations.transfer'), icon: 'exchange' },
  { name: t('common.actions.print') + ' ' + t('mobile.assetDetail.scanQR'), icon: 'qr' },
  { name: t('mobile.assetDetail.history'), icon: 'records' },
  { name: t('common.actions.delete') + ' ' + t('assets.fields.assetName'), icon: 'delete-o', color: '#ee0a24' }
])

// ============================================================================
// Computed
// ============================================================================

const hasCustomFields = computed(() => {
  return asset.value?.customFields && Object.keys(asset.value.customFields).length > 0
})

// ============================================================================
// Methods
// ============================================================================

/**
 * Get status label
 */
const getStatusLabel = (status: AssetStatus): string => {
  const keyMap: Record<AssetStatus, string> = {
    draft: 'assets.status.draft',
    in_use: 'assets.status.inUse',
    idle: 'assets.status.idle',
    maintenance: 'assets.status.maintenance',
    scrapped: 'assets.status.scrapped'
  }
  const key = keyMap[status]
  return key ? t(key) : status
}

/**
 * Get status type for Vant tag
 */
const getStatusType = (status: AssetStatus): any => {
  const types: Record<AssetStatus, 'success' | 'warning' | 'danger' | 'primary' | 'default'> = {
    draft: 'primary',
    in_use: 'success',
    idle: 'warning',
    maintenance: 'danger',
    scrapped: 'default'
  }
  return types[status] || 'default'
}

/**
 * Get field label from metadata
 */
const getFieldLabel = (key: string): string => {
  // Would fetch from field definition metadata
  const labels: Record<string, string> = {
    warrantyExpiry: t('assets.fields.warrantyDate'),
    manufacturer: t('assets.fields.brand'),
    modelNumber: t('assets.fields.model'),
    serialNumber: t('assets.fields.serialNumber')
  }
  return labels[key] || key
}

/**
 * Format custom field value
 */
const formatCustomFieldValue = (value: any): string => {
  if (value === null || value === undefined) return '-'
  if (typeof value === 'boolean') return value ? t('common.units.yes') : t('common.units.no')
  return String(value)
}

/**
 * Get step icon based on type
 */
const getStepIcon = (type: string): string => {
  const icons: Record<string, string> = {
    create: 'add-o',
    update: 'edit',
    transfer: 'exchange',
    inventory: 'scan',
    maintenance: 'repair-o',
    scrap: 'delete-o'
  }
  return icons[type] || 'circle'
}

/**
 * Format time
 */
const formatTime = (date: string): string => {
  return new Date(date).toLocaleString('zh-CN', {
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit'
  })
}

/**
 * Go back
 */
const goBack = () => {
  router.back()
}

/**
 * Handle action sheet select
 */
const handleAction = (item: any) => {
  showActions.value = false

  switch (item.icon) {
    case 'edit':
      handleEdit()
      break
    case 'exchange':
      handleTransfer()
      break
    case 'qr':
      handleShowQRCode()
      break
    case 'records':
      showToast(t('mobile.assetDetail.history'))
      break
    case 'delete-o':
      handleDelete()
      break
  }
}

/**
 * Handle edit
 */
const handleEdit = () => {
  router.push(`/assets/${asset.value?.id}/edit`)
}

/**
 * Handle transfer
 */
const handleTransfer = () => {
  router.push(`/assets/${asset.value?.id}/transfer`)
}

/**
 * Handle show QR code
 */
const handleShowQRCode = () => {
  qrCodeVisible.value = true
}

/**
 * Handle download QR code
 */
const handleDownloadQR = () => {
  showToast(t('common.status.processing'))
}

/**
 * Handle delete
 */
const handleDelete = async () => {
  showDialog({
    title: t('common.dialog.confirmDelete'),
    message: t('common.dialog.confirmDeleteMessage', { count: 1 }),
    showCancelButton: true,
    confirmButtonText: t('common.actions.confirm'),
    cancelButtonText: t('common.actions.cancel')
  }).then(async (action?: string) => {
    if (action === 'confirm') {
      try {
        await assetApi.delete(asset.value!.id)
        showToast(t('common.messages.deleteSuccess'))
        goBack()
      } catch (error) {
        showToast(t('common.messages.deleteFailed'))
      }
    }
  })
}

/**
 * Load timeline data
 */
const loadTimeline = async () => {
  // Would fetch from API
  timeline.value = []
}

/**
 * Load asset data
 */
const loadAsset = async () => {
  loading.value = true
  try {
    const id = route.params.id as string
    asset.value = await assetApi.get(id)
    await loadTimeline()
  } catch (error) {
    showToast(t('common.messages.operationFailed'))
    goBack()
  } finally {
    loading.value = false
  }
}

// ============================================================================
// Lifecycle
// ============================================================================

onMounted(() => {
  loadAsset()
})
</script>

<style scoped lang="scss">
.mobile-asset-detail {
  min-height: 100vh;
  background: #f5f5f5;
  padding-bottom: 80px;
}

.loading-container {
  display: flex;
  justify-content: center;
  align-items: center;
  height: 300px;
}

.asset-content {
  padding: 12px 0;
}

.header-card {
  margin-bottom: 12px;
}

.asset-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px;
}

.asset-code {
  font-size: 20px;
  font-weight: 600;
  color: #323233;
}

.asset-name {
  padding: 0 16px 16px;
  font-size: 15px;
  color: #646566;
}

.asset-category {
  padding: 0 16px 16px;
}

.description-text {
  color: #646566;
  line-height: 1.6;
  white-space: pre-wrap;
}

.qr-code-card {
  padding: 24px;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 16px;
}

.qr-code-placeholder {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
}

.qr-hint {
  font-size: 14px;
  color: #969799;
}

.qr-dialog-content {
  padding: 24px;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 16px;
}

.qr-large-placeholder {
  display: flex;
  flex-direction: column;
  align-items: center;
}

.qr-code-text {
  font-size: 18px;
  font-weight: 500;
  color: #323233;
}

.qr-hint-text {
  font-size: 13px;
  color: #969799;
}

.timeline-container {
  padding: 16px;
}

.step-title {
  font-weight: 500;
  color: #323233;
}

.step-time {
  margin-left: 12px;
  font-size: 12px;
  color: #969799;
  font-weight: normal;
}

.step-desc {
  margin: 4px 0 0;
  color: #646566;
  font-size: 14px;
}

.step-operator {
  margin: 4px 0 0;
  color: #969799;
  font-size: 12px;
}

.bottom-actions {
  position: fixed;
  bottom: 0;
  left: 0;
  right: 0;
  display: flex;
  gap: 12px;
  padding: 12px 16px;
  background: white;
  box-shadow: 0 -2px 10px rgba(0, 0, 0, 0.05);
  z-index: 100;

  .van-button {
    flex: 1;
  }
}
</style>
