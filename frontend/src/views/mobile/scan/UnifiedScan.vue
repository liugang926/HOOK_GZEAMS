<template>
  <div class="unified-scan">
    <van-nav-bar
      :title="$t('mobile.unifiedScan.title')"
      :left-text="$t('common.actions.back')"
      left-arrow
      @click-left="goBack"
    >
      <template #right>
        <van-icon
          name="ellipsis"
          size="18"
          @click="showMore = true"
        />
      </template>
    </van-nav-bar>

    <div class="scanner-wrapper">
      <MobileQRScanner
        ref="scannerRef"
        :task-id="taskId"
        :auto-start="false"
        :show-preview="true"
        @scan="handleScan"
        @error="handleScanError"
      />
    </div>

    <div
      v-if="recentScans.length > 0"
      class="recent-scans"
    >
      <div class="section-header">
        <span class="section-title">{{ $t('mobile.unifiedScan.recentScans') }}</span>
        <van-button
          type="primary"
          size="mini"
          plain
          @click="clearHistory"
        >
          {{ $t('common.actions.clear') }}
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
            <van-icon
              name="checked"
              color="#52c41a"
            />
          </template>
          <template #right-icon>
            <van-tag
              :type="item.result === 'success' ? 'success' : 'danger'"
              size="medium"
            >
              {{ item.result === 'success' ? $t('mobile.unifiedScan.result.success') : $t('mobile.unifiedScan.result.error') }}
            </van-tag>
          </template>
        </van-cell>
      </div>
    </div>

    <div class="manual-input-area">
      <van-button
        block
        type="primary"
        icon="aim"
        @click="showManualInput = true"
      >
        {{ $t('mobile.unifiedScan.manualInputButton') }}
      </van-button>
    </div>

    <van-dialog
      v-model:show="showManualInput"
      :title="$t('mobile.unifiedScan.manualInputTitle')"
      :show-cancel-button="true"
      :confirm-button-text="$t('common.actions.confirm')"
      :cancel-button-text="$t('common.actions.cancel')"
      @confirm="handleManualSubmit"
    >
      <van-field
        v-model="manualCode"
        :placeholder="$t('mobile.unifiedScan.manualInputPlaceholder')"
        clearable
        autofocus
      />
    </van-dialog>

    <van-popup
      v-model:show="showMore"
      position="bottom"
    >
      <van-picker
        :columns="moreActions"
        @confirm="handleMoreAction"
        @cancel="showMore = false"
      />
    </van-popup>

    <van-dialog
      v-model:show="previewVisible"
      :title="previewAsset?.name"
      :show-confirm-button="false"
    >
      <div
        v-if="previewAsset"
        class="asset-preview"
      >
        <van-cell-group inset>
          <van-cell
            :title="$t('mobile.unifiedScan.preview.assetCode')"
            :value="previewAsset.code"
          />
          <van-cell
            :title="$t('mobile.unifiedScan.preview.assetCategory')"
            :value="previewAsset.categoryName"
          />
          <van-cell
            :title="$t('mobile.unifiedScan.preview.assetStatus')"
            :value="getStatusLabel(previewAsset.status)"
          />
          <van-cell
            :title="$t('mobile.unifiedScan.preview.assetLocation')"
            :value="previewAsset.locationName"
          />
          <van-cell
            :title="$t('mobile.unifiedScan.preview.assetCustodian')"
            :value="previewAsset.custodianName"
          />
        </van-cell-group>
      </div>
      <template #footer>
        <van-button @click="previewVisible = false">
          {{ $t('common.actions.close') }}
        </van-button>
        <van-button
          type="primary"
          @click="handleConfirmPreview"
        >
          {{ $t('common.actions.detail') }}
        </van-button>
      </template>
    </van-dialog>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { showDialog, showToast } from 'vant'
import MobileQRScanner from '@/components/mobile/MobileQRScanner.vue'
import { qrScanApi } from '@/api/inventory'
import type { AssetStatus } from '@/types/assets'
import { readStorageJson, writeStorageJson } from '@/platform/storage/browserStorage'

const router = useRouter()
const route = useRoute()
const { t } = useI18n()

interface ScanHistoryItem {
  id: number
  assetId: string
  assetName: string
  scannedAt: string
  result: 'success' | 'error'
}

const HISTORY_KEY = 'scan_history'

const taskId = ref(route.query.taskId as string | undefined)
const recentScans = ref<ScanHistoryItem[]>([])
const showManualInput = ref(false)
const manualCode = ref('')
const showMore = ref(false)
const previewVisible = ref(false)
const previewAsset = ref<any>(null)
const scannerRef = ref<any>()

const moreActions = computed(() => [
  { text: t('mobile.unifiedScan.moreActions.history'), value: 'history' },
  { text: t('mobile.unifiedScan.moreActions.camera'), value: 'camera' },
  { text: t('mobile.unifiedScan.moreActions.torch'), value: 'torch' }
])

const loadScanHistory = () => {
  try {
    const saved = readStorageJson<ScanHistoryItem[] | unknown>(HISTORY_KEY, [])
    recentScans.value = Array.isArray(saved) ? (saved as ScanHistoryItem[]) : []
  } catch (error) {
    console.error(error)
  }
}

const saveScanHistory = () => {
  try {
    writeStorageJson(HISTORY_KEY, recentScans.value.slice(0, 50))
  } catch (error) {
    console.error(error)
  }
}

const handleScan = async (code: string, asset?: any) => {
  if (asset) {
    addToHistory(code, asset, 'success')
    previewAsset.value = asset
    previewVisible.value = true
    return
  }

  try {
    const result = await qrScanApi.getAssetByQrCode(code)
    previewAsset.value = result
    previewVisible.value = true
    addToHistory(code, result, 'success')
  } catch (error) {
    addToHistory(code, null, 'error')
    showToast(t('mobile.messages.assetNotFound'))
  }
}

const handleScanError = (error: string) => {
  showToast(error)
}

const addToHistory = (code: string, asset: any, result: 'success' | 'error') => {
  recentScans.value.unshift({
    id: Date.now(),
    assetId: asset?.id || code,
    assetName: asset?.name || code,
    scannedAt: new Date().toISOString(),
    result
  })
  saveScanHistory()
}

const handleManualSubmit = () => {
  const code = manualCode.value.trim()
  if (!code) return

  handleScan(code)
  manualCode.value = ''
  showManualInput.value = false
}

const handleViewAsset = (assetId: string) => {
  router.push(`/mobile/assets/${assetId}`)
}

const handleConfirmPreview = () => {
  previewVisible.value = false
  if (previewAsset.value) {
    handleViewAsset(previewAsset.value.id)
  }
}

const clearHistory = () => {
  showDialog({
    title: t('mobile.unifiedScan.messages.clearHistoryTitle'),
    message: t('mobile.unifiedScan.messages.clearHistoryConfirm'),
    showCancelButton: true,
    confirmButtonText: t('common.actions.confirm'),
    cancelButtonText: t('common.actions.cancel')
  }).then(() => {
    recentScans.value = []
    saveScanHistory()
    showToast(t('mobile.unifiedScan.messages.historyCleared'))
  }).catch(() => {
    // dialog cancelled
  })
}

const handleMoreAction = (payload: any) => {
  showMore.value = false
  const value = payload?.selectedOptions?.[0]?.value || payload?.selectedValues?.[0]

  switch (value) {
    case 'history':
      showToast(t('mobile.unifiedScan.messages.historyOpened'))
      break
    case 'camera':
      scannerRef.value?.switchCamera()
      break
    case 'torch':
      scannerRef.value?.toggleTorch()
      break
  }
}

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

const formatTime = (date: string | Date): string => {
  const now = Date.now()
  const target = new Date(date).getTime()
  const diff = now - target
  const minutes = Math.floor(diff / 60000)

  if (minutes < 1) return t('mobile.unifiedScan.time.justNow')
  if (minutes < 60) return t('mobile.unifiedScan.time.minutesAgo', { count: minutes })

  const hours = Math.floor(minutes / 60)
  if (hours < 24) return t('mobile.unifiedScan.time.hoursAgo', { count: hours })

  const days = Math.floor(hours / 24)
  return t('mobile.unifiedScan.time.daysAgo', { count: days })
}

const goBack = () => {
  router.back()
}

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
