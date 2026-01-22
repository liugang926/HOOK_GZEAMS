<!--
  Unified Scan Page (Mobile)

  Unified QR code scanning page for mobile.
  Features:
  - Full-screen QR scanner
  - Recent scan history
  - Manual input fallback
  - Asset preview after scan
-->

<template>
  <div class="unified-scan">
    <van-nav-bar
      title="扫码"
      left-text="返回"
      left-arrow
      @click-left="goBack"
    >
      <template #right>
        <van-icon name="ellipsis" size="18" @click="showMore = true" />
      </template>
    </van-nav-bar>

    <!-- Scanner Component -->
    <div class="scanner-wrapper">
      <MobileQRScanner
        :task-id="taskId"
        @scan="handleScan"
        @error="handleScanError"
        :show-preview="true"
        ref="scannerRef"
      />
    </div>

    <!-- Recent Scans -->
    <div class="recent-scans" v-if="recentScans.length > 0">
      <div class="section-header">
        <span class="section-title">最近扫描</span>
        <van-button
          type="primary"
          size="mini"
          plain
          @click="clearHistory"
        >
          清空
        </van-button>
      </div>
      <div class="scan-list">
        <van-cell
          v-for="item in recentScans.slice(0, 5)"
          :key="item.id"
          :title="item.assetName"
          :label="formatTime(item.scannedAt)"
          is-link
          @click="handleViewAsset(item.assetId)"
        >
          <template #icon>
            <van-icon name="checked" color="#52c41a" />
          </template>
          <template #right-icon>
            <van-tag :type="item.result === 'success' ? 'success' : 'danger'" size="small">
              {{ item.result === 'success' ? '成功' : '异常' }}
            </van-tag>
          </template>
        </van-cell>
      </div>
    </div>

    <!-- Manual Input -->
    <div class="manual-input-area">
      <van-button
        block
        type="primary"
        icon="aim"
        @click="showManualInput = true"
      >
        手动输入资产编码
      </van-button>
    </div>

    <!-- Manual Input Dialog -->
    <van-dialog
      v-model:show="showManualInput"
      title="手动输入"
      show-cancel-button
      @confirm="handleManualSubmit"
    >
      <van-field
        v-model="manualCode"
        placeholder="请输入资产编码或二维码内容"
        clearable
        autofocus
      />
    </van-dialog>

    <!-- More Actions Popup -->
    <van-popup v-model:show="showMore" position="bottom">
      <van-picker
        :columns="moreActions"
        @confirm="handleMoreAction"
        @cancel="showMore = false"
      />
    </van-popup>

    <!-- Asset Preview Dialog -->
    <van-dialog
      v-model:show="previewVisible"
      :title="previewAsset?.name"
      :show-confirm-button="false"
    >
      <div class="asset-preview" v-if="previewAsset">
        <van-cell-group inset>
          <van-cell title="资产编码" :value="previewAsset.code" />
          <van-cell title="资产分类" :value="previewAsset.categoryName" />
          <van-cell title="资产状态" :value="getStatusLabel(previewAsset.status)" />
          <van-cell title="存放位置" :value="previewAsset.locationName" />
          <van-cell title="使用人" :value="previewAsset.custodianName" />
        </van-cell-group>
      </div>
      <template #footer>
        <van-button @click="previewVisible = false">关闭</van-button>
        <van-button type="primary" @click="handleConfirmPreview">查看详情</van-button>
      </template>
    </van-dialog>
  </div>
</template>

<script setup lang="ts">
/**
 * Unified Scan Page (Mobile)
 *
 * Unified QR code scanning page for mobile devices.
 * Supports scanner, manual input, and recent history.
 */

import { ref, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { showToast, showDialog } from 'vant'
import MobileQRScanner from '@/components/mobile/MobileQRScanner.vue'
import { qrScanApi } from '@/api/inventory'
import { assetApi } from '@/api/assets'
import type { AssetStatus } from '@/types/assets'

const router = useRouter()
const route = useRoute()

// ============================================================================
// State
// ============================================================================

const taskId = ref(route.query.taskId as string | undefined)
const recentScans = ref<Array<{
  id: number
  assetId: string
  assetName: string
  scannedAt: Date
  result: 'success' | 'error'
}>>([])

const showManualInput = ref(false)
const manualCode = ref('')
const showMore = ref(false)
const previewVisible = ref(false)
const previewAsset = ref<any>(null)
const scannerRef = ref()

const moreActions = [
  { text: '查看扫描历史', value: 'history' },
  { text: '切换摄像头', value: 'camera' },
  { text: '开灯/关灯', value: 'torch' }
]

// Load saved scan history from localStorage
const loadScanHistory = () => {
  try {
    const saved = localStorage.getItem('scan_history')
    if (saved) {
      recentScans.value = JSON.parse(saved)
    }
  } catch (error) {
    console.error('Failed to load scan history:', error)
  }
}

// Save scan history to localStorage
const saveScanHistory = () => {
  try {
    localStorage.setItem('scan_history', JSON.stringify(recentScans.value.slice(0, 50)))
  } catch (error) {
    console.error('Failed to save scan history:', error)
  }
}

/**
 * Handle scan result
 */
const handleScan = async (code: string, asset?: any) => {
  if (asset) {
    // Asset was found and validated by scanner
    addToHistory(code, asset, 'success')
    previewAsset.value = asset
    previewVisible.value = true
  } else {
    // Scan found code but no asset data - fetch it
    try {
      const result = await qrScanApi.getAssetByQrCode(code)
      previewAsset.value = result
      previewVisible.value = true
      addToHistory(code, result, 'success')
    } catch (error) {
      addToHistory(code, null, 'error')
      showToast('未找到对应资产')
    }
  }
}

/**
 * Handle scan error
 */
const handleScanError = (error: string) => {
  showToast(error)
}

/**
 * Add to scan history
 */
const addToHistory = (code: string, asset: any, result: 'success' | 'error') => {
  recentScans.value.unshift({
    id: Date.now(),
    assetId: asset?.id || code,
    assetName: asset?.name || code,
    scannedAt: new Date(),
    result
  })
  saveScanHistory()
}

/**
 * Handle manual submit
 */
const handleManualSubmit = () => {
  const code = manualCode.value.trim()
  if (code) {
    handleScan(code)
    manualCode.value = ''
    showManualInput.value = false
  }
}

/**
 * Handle view asset
 */
const handleViewAsset = (assetId: string) => {
  router.push(`/mobile/assets/${assetId}`)
}

/**
 * Handle confirm preview - navigate to detail
 */
const handleConfirmPreview = () => {
  previewVisible.value = false
  if (previewAsset.value) {
    handleViewAsset(previewAsset.value.id)
  }
}

/**
 * Clear history
 */
const clearHistory = () => {
  showDialog({
    title: '清空记录',
    message: '确定要清空扫描历史吗？',
    showCancelButton: true
  }).then((action: string) => {
    if (action === 'confirm') {
      recentScans.value = []
      saveScanHistory()
      showToast('已清空')
    }
  })
}

/**
 * Handle more action
 */
const handleMoreAction = ({ selectedOptions }: any) => {
  showMore.value = false
  const value = selectedOptions[0]?.value

  switch (value) {
    case 'history':
      showToast('查看扫描历史')
      break
    case 'camera':
      scannerRef.value?.switchCamera()
      break
    case 'torch':
      scannerRef.value?.toggleTorch()
      break
  }
}

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
 * Format time
 */
const formatTime = (date: Date): string => {
  const now = new Date()
  const diff = now.getTime() - new Date(date).getTime()
  const minutes = Math.floor(diff / 60000)

  if (minutes < 1) return '刚刚'
  if (minutes < 60) return `${minutes}分钟前`
  const hours = Math.floor(minutes / 60)
  if (hours < 24) return `${hours}小时前`
  const days = Math.floor(hours / 24)
  return `${days}天前`
}

/**
 * Go back
 */
const goBack = () => {
  router.back()
}

// ============================================================================
// Lifecycle
// ============================================================================

onMounted(() => {
  loadScanHistory()
})
</script>

<style scoped lang="scss">
.unified-scan {
  min-height: 100vh;
  background: #000;
}

.scanner-wrapper {
  height: calc(100vh - 46px - 60px);
  min-height: 400px;
}

.recent-scans {
  background: #f5f5f5;
  padding: 12px 16px;
}

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}

.section-title {
  font-size: 14px;
  font-weight: 500;
  color: #646566;
}

.scan-list {
  background: white;
  border-radius: 8px;
  overflow: hidden;
}

.manual-input-area {
  position: fixed;
  bottom: 0;
  left: 0;
  right: 0;
  padding: 12px 16px;
  background: white;
  box-shadow: 0 -2px 10px rgba(0, 0, 0, 0.1);
  z-index: 100;
}

.asset-preview {
  :deep(.van-cell-group) {
    margin: 0;
  }
}
</style>
