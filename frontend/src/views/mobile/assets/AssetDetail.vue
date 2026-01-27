<!--
  Mobile Asset Detail View

  Mobile-optimized asset detail page using Vant UI.
  Features:
  - Responsive layout with Vant components
  - Touch-optimized interactions
  - Action sheet for additional options
  - Timeline for operation history
-->

<template>
  <div class="mobile-asset-detail">
    <van-nav-bar
      title="资产详情"
      left-text="返回"
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
        加载中...
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
            size="small"
          >
            {{ asset.categoryName }}
          </van-tag>
        </div>
      </van-cell-group>

      <!-- Basic Information -->
      <van-cell-group
        inset
        title="基本信息"
      >
        <van-cell
          title="资产编码"
          :value="asset.code"
        />
        <van-cell
          title="资产名称"
          :value="asset.name"
        />
        <van-cell
          title="资产分类"
          :value="asset.categoryName || '-'"
        />
        <van-cell
          title="采购金额"
          :value="`¥${formatMoney(asset.purchasePrice)}`"
        />
        <van-cell
          title="采购日期"
          :value="asset.purchaseDate"
        />
        <van-cell
          title="规格型号"
          :value="asset.specification || '-'"
        />
      </van-cell-group>

      <!-- Location & Custodian -->
      <van-cell-group
        inset
        title="位置与使用人"
      >
        <van-cell
          title="存放位置"
          :value="asset.locationName || '-'"
          is-link
        />
        <van-cell
          title="使用人"
          :value="asset.custodianName || '-'"
        />
        <van-cell
          title="管理部门"
          :value="asset.departmentName || '-'"
        />
      </van-cell-group>

      <!-- Custom Fields -->
      <van-cell-group
        v-if="hasCustomFields"
        inset
        title="扩展信息"
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
        title="采购信息"
      >
        <van-cell
          title="供应商"
          :value="asset.supplierName"
        />
        <van-cell
          title="供应商联系方式"
          value="-"
        />
      </van-cell-group>

      <!-- Notes -->
      <van-cell-group
        v-if="asset.description"
        inset
        title="备注"
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
        title="二维码"
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
            显示二维码
          </van-button>
        </div>
      </van-cell-group>

      <!-- Operation Timeline -->
      <van-cell-group
        inset
        title="操作记录"
      >
        <div class="timeline-container">
          <van-empty
            v-if="!timeline || timeline.length === 0"
            description="暂无操作记录"
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
                  操作人: {{ item.operator }}
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
          编辑
        </van-button>
        <van-button
          size="large"
          icon="share-o"
          @click="handleTransfer"
        >
          调拨
        </van-button>
      </div>
    </div>

    <!-- Error State -->
    <van-empty
      v-else
      description="资产不存在"
    />

    <!-- Action Sheet -->
    <van-action-sheet
      v-model:show="showActions"
      :actions="actionItems"
      cancel-text="取消"
      @select="handleAction"
    />

    <!-- QR Code Dialog -->
    <van-dialog
      v-model:show="qrCodeVisible"
      title="资产二维码"
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
          扫描二维码查看资产详情
        </p>
      </div>
      <template #footer>
        <van-button @click="qrCodeVisible = false">
          关闭
        </van-button>
        <van-button
          type="primary"
          @click="handleDownloadQR"
        >
          保存图片
        </van-button>
      </template>
    </van-dialog>
  </div>
</template>

<script setup lang="ts">
/**
 * Mobile Asset Detail View
 *
 * Mobile-optimized asset detail page using Vant UI components.
 */

import { ref, computed, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { showToast, showDialog, showImagePreview } from 'vant'
import type { Asset, AssetStatus } from '@/types/assets'
import { assetApi } from '@/api/assets'
import { formatMoney } from '@/utils/numberFormat'

const router = useRouter()
const route = useRoute()

// ============================================================================
// State
// ============================================================================

const loading = ref(true)
const asset = ref<Asset | null>(null)
const showActions = ref(false)
const qrCodeVisible = ref(false)
const timeline = ref<any[]>([])

// ============================================================================
// Action Items
// ============================================================================

const actionItems = [
  { name: '编辑资产', icon: 'edit' },
  { name: '资产调拨', icon: 'exchange' },
  { name: '打印二维码', icon: 'qr' },
  { name: '查看操作记录', icon: 'records' },
  { name: '删除资产', icon: 'delete-o', color: '#ee0a24' }
]

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
  const labels: Record<AssetStatus, string> = {
    draft: '草稿',
    in_use: '使用中',
    idle: '闲置',
    maintenance: '维修中',
    scrapped: '已报废'
  }
  return labels[status] || status
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
    warrantyExpiry: '保修到期日',
    manufacturer: '制造商',
    modelNumber: '型号',
    serialNumber: '序列号'
  }
  return labels[key] || key
}

/**
 * Format custom field value
 */
const formatCustomFieldValue = (value: any): string => {
  if (value === null || value === undefined) return '-'
  if (typeof value === 'boolean') return value ? '是' : '否'
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
      showToast('查看操作记录')
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
  showToast('二维码保存功能开发中...')
}

/**
 * Handle delete
 */
const handleDelete = async () => {
  showDialog({
    title: '确认删除',
    message: '确定要删除此资产吗？',
    showCancelButton: true
  }).then(async (action: string) => {
    if (action === 'confirm') {
      try {
        await assetApi.delete(asset.value!.id)
        showToast('删除成功')
        goBack()
      } catch (error) {
        showToast('删除失败')
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
    showToast('加载失败')
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
