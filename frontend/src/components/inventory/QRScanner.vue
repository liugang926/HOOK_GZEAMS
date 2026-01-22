<!--
  QRScanner Component

  QR code scanner component for inventory operations.
  Features:
  - Camera access with @zxing/library
  - Flashlight toggle support
  - Manual input fallback
  - Scan result validation
  - Scan history display
-->

<template>
  <div class="qr-scanner">
    <div class="scanner-container" ref="containerRef">
      <video ref="videoRef" class="scanner-video" autoplay playsinline />
      <div class="scan-overlay">
        <div class="scan-frame">
          <div class="scan-line"></div>
        </div>
        <p class="scan-hint">将二维码放入框内自动扫描</p>
      </div>

      <!-- Torch control -->
      <div v-if="hasTorch" class="torch-control">
        <el-button
          :icon="torchOn ? FlashlightOff : Flashlight"
          circle
          @click="toggleTorch"
        >
        </el-button>
      </div>

      <!-- Camera selector -->
      <div v-if="cameras.length > 1" class="camera-selector">
        <el-select
          v-model="selectedCameraId"
          @change="switchCamera"
          size="small"
        >
          <el-option
            v-for="camera in cameras"
            :key="camera.id"
            :label="camera.label"
            :value="camera.id"
          />
        </el-select>
      </div>
    </div>

    <!-- Scan Info -->
    <div class="scan-info">
      <div class="scan-count">
        <span class="count-label">已扫描:</span>
        <span class="count-number">{{ scannedCount }}</span>
        <span class="count-divider">/</span>
        <span class="count-total">{{ totalCount }}</span>
      </div>
      <div class="scan-status" :class="`status-${lastScanStatus}`">
        {{ lastScanMessage }}
      </div>
    </div>

    <!-- Scanner Controls -->
    <div class="scanner-controls">
      <el-button @click="handleManualInput">
        <el-icon><Edit /></el-icon>
        手动输入
      </el-button>
      <el-button @click="handleShowHistory" v-if="scanHistory.length > 0">
        <el-icon><Clock /></el-icon>
        扫描记录 ({{ scanHistory.length }})
      </el-button>
    </div>

    <!-- Manual Input Dialog -->
    <el-dialog
      v-model="inputVisible"
      title="手动输入"
      width="400px"
      :close-on-click-modal="false"
    >
      <el-form @submit.prevent="handleManualSubmit">
        <el-form-item label="资产编码/二维码">
          <el-input
            v-model="manualCode"
            ref="manualInputRef"
            placeholder="请输入资产编码或扫描结果"
            clearable
            autofocus
            @keyup.enter="handleManualSubmit"
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="inputVisible = false">取消</el-button>
        <el-button type="primary" @click="handleManualSubmit">
          确认
        </el-button>
      </template>
    </el-dialog>

    <!-- Scan History Dialog -->
    <el-dialog
      v-model="historyVisible"
      title="扫描记录"
      width="500px"
    >
      <el-table :data="scanHistory" max-height="400">
        <el-table-column prop="scannedAt" label="时间" width="160">
          <template #default="{ row }">
            {{ formatTime(row.scannedAt) }}
          </template>
        </el-table-column>
        <el-table-column prop="code" label="编码" />
        <el-table-column prop="assetName" label="资产名称" />
        <el-table-column prop="result" label="状态" width="80">
          <template #default="{ row }">
            <el-tag :type="row.result === 'success' ? 'success' : 'danger'" size="small">
              {{ row.result === 'success' ? '成功' : '异常' }}
            </el-tag>
          </template>
        </el-table-column>
      </el-table>
      <template #footer>
        <el-button @click="clearHistory">清空记录</el-button>
        <el-button type="primary" @click="historyVisible = false">关闭</el-button>
      </template>
    </el-dialog>

    <!-- Asset Preview Dialog -->
    <el-dialog
      v-model="previewVisible"
      :title="previewAsset?.name"
      width="500px"
    >
      <div v-if="previewAsset" class="asset-preview">
        <el-descriptions :column="1" border>
          <el-descriptions-item label="资产编码">
            {{ previewAsset.code }}
          </el-descriptions-item>
          <el-descriptions-item label="资产分类">
            {{ previewAsset.categoryName }}
          </el-descriptions-item>
          <el-descriptions-item label="当前状态">
            <el-tag :type="getStatusType(previewAsset.status)" size="small">
              {{ getStatusLabel(previewAsset.status) }}
            </el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="存放位置">
            {{ previewAsset.locationName }}
          </el-descriptions-item>
        </el-descriptions>
      </div>
      <template #footer>
        <el-button @click="previewVisible = false">关闭</el-button>
        <el-button type="primary" @click="confirmScan">
          确认扫描
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
/**
 * QRScanner Component
 *
 * QR code scanner for inventory operations using @zxing/library.
 * Supports camera access, flashlight, manual input, and scan history.
 */

import { ref, onMounted, onUnmounted, nextTick } from 'vue'
import { ElMessage } from 'element-plus'
import { BrowserMultiFormatReader, NotFoundException } from '@zxing/library'
import { Flashlight, FlashlightOff, Edit, Clock } from '@element-plus/icons-vue'
import { qrScanApi } from '@/api/inventory'
import type { AssetStatus } from '@/types/assets'

// ============================================================================
// Props & Emits
// ============================================================================

interface Props {
  taskId?: string
  autoSubmit?: boolean
  showPreview?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  autoSubmit: false,
  showPreview: true
})

const emit = defineEmits<{
  scan: [code: string, asset?: any]
  error: [error: string]
}>()

// ============================================================================
// State
// ============================================================================

const containerRef = ref<HTMLElement>()
const videoRef = ref<HTMLVideoElement>()
const manualInputRef = ref<HTMLInputElement>()

const codeReader = new BrowserMultiFormatReader()
const stream = ref<MediaStream | null>(null)
const torchOn = ref(false)
const hasTorch = ref(false)

const cameras = ref<Array<{ id: string; label: string }>>([])
const selectedCameraId = ref('')

const scannedCount = ref(0)
const totalCount = ref(0)
const lastScanStatus = ref<'idle' | 'success' | 'error'>('idle')
const lastScanMessage = ref('准备扫描...')
const scannedCodes = ref<Set<string>>(new Set())
const scanHistory = ref<Array<{
  code: string
  assetName: string
  scannedAt: Date
  result: 'success' | 'error'
}>>([])

const inputVisible = ref(false)
const manualCode = ref('')
const historyVisible = ref(false)
const previewVisible = ref(false)
const previewAsset = ref<any>(null)
const pendingScanCode = ref('')

let isScanning = false
let lastScanTime = 0
const SCAN_COOLDOWN = 1500 // ms between scans

// ============================================================================
// Methods
// ============================================================================

/**
 * Initialize scanner
 */
const initScanner = async () => {
  try {
    // Get available cameras
    const devices = await navigator.mediaDevices.enumerateDevices()
    cameras.value = devices
      .filter(d => d.kind === 'videoinput')
      .map(d => ({ id: d.deviceId, label: d.label || `Camera ${d.deviceId.slice(0, 5)}` }))
      .slice(0, 3) // Limit to 3 cameras

    if (cameras.value.length === 0) {
      ElMessage.error('未检测到摄像头')
      return
    }

    // Select back camera by default
    const backCamera = cameras.value.find(c =>
      c.label.toLowerCase().includes('back') ||
      c.label.toLowerCase().includes('environment')
    )
    selectedCameraId.value = backCamera?.id || cameras.value[0].id

    await startScanner()
  } catch (error) {
    console.error('Failed to initialize scanner:', error)
    ElMessage.error('摄像头初始化失败，请检查权限设置')
  }
}

/**
 * Start scanner
 */
const startScanner = async () => {
  try {
    stopScanner()

    // Request camera with constraints
    const constraints: MediaStreamConstraints = {
      video: {
        deviceId: selectedCameraId.value ? { exact: selectedCameraId.value } : undefined,
        facingMode: 'environment',
        width: { ideal: 1280 },
        height: { ideal: 720 }
      }
    }

    stream.value = await navigator.mediaDevices.getUserMedia(constraints)

    if (videoRef.value) {
      videoRef.value.srcObject = stream.value
      videoRef.value.play()

      // Start QR code reading
      isScanning = true
      codeReader.decodeFromVideoDevice(
        null,
        videoRef.value,
        (result, error) => {
          if (result && isScanning) {
            handleScanResult(result.text)
          }
        }
      )
    }

    // Check for torch capability
    const track = stream.value?.getVideoTracks()[0]
    const capabilities = (track as any)?.getCapabilities()
    hasTorch.value = capabilities?.torch || false

  } catch (error: any) {
    console.error('Failed to start scanner:', error)
    ElMessage.error(error.message || '无法访问摄像头')
  }
}

/**
 * Stop scanner
 */
const stopScanner = () => {
  isScanning = false
  codeReader.reset()
  stream.value?.getTracks().forEach(track => track.stop())
  stream.value = null
}

/**
 * Handle scan result
 */
const handleScanResult = async (code: string) => {
  // Prevent duplicate scans and cooldown
  const now = Date.now()
  if (scannedCodes.value.has(code) || now - lastScanTime < SCAN_COOLDOWN) {
    return
  }

  lastScanTime = now
  lastScanStatus.value = 'idle'
  lastScanMessage.value = '验证中...'

  try {
    // Verify QR code
    const asset = await qrScanApi.getAssetByQrCode(code)
    lastScanStatus.value = 'success'
    lastScanMessage.value = `扫描成功: ${asset.name}`

    // Add to scanned set
    scannedCodes.value.add(code)
    scannedCount.value = scannedCodes.value.size

    // Add to history
    scanHistory.value.unshift({
      code,
      assetName: asset.name,
      scannedAt: new Date(),
      result: 'success'
    })

    if (props.showPreview && !props.autoSubmit) {
      // Show preview dialog
      previewAsset.value = asset
      pendingScanCode.value = code
      previewVisible.value = true
    } else {
      // Auto submit
      emit('scan', code, asset)
    }

  } catch (error: any) {
    lastScanStatus.value = 'error'
    lastScanMessage.value = `未找到资产: ${code}`

    // Add error to history
    scanHistory.value.unshift({
      code,
      assetName: '未找到',
      scannedAt: new Date(),
      result: 'error'
    })

    emit('error', `未找到资产: ${code}`)
  }
}

/**
 * Toggle torch/flashlight
 */
const toggleTorch = async () => {
  const track = stream.value?.getVideoTracks()[0]
  if (!track) return

  try {
    torchOn.value = !torchOn.value
    await (track as any).applyConstraints({
      advanced: [{ torch: torchOn.value }]
    })
  } catch (error) {
    console.error('Failed to toggle torch:', error)
  }
}

/**
 * Switch camera
 */
const switchCamera = async () => {
  await startScanner()
}

/**
 * Handle manual input
 */
const handleManualInput = () => {
  inputVisible.value = true
  nextTick(() => {
    manualInputRef.value?.focus()
  })
}

/**
 * Handle manual submit
 */
const handleManualSubmit = () => {
  const code = manualCode.value.trim()
  if (code) {
    handleScanResult(code)
    manualCode.value = ''
    inputVisible.value = false
  }
}

/**
 * Handle show history
 */
const handleShowHistory = () => {
  historyVisible.value = true
}

/**
 * Clear history
 */
const clearHistory = () => {
  scanHistory.value = []
  historyVisible.value = false
}

/**
 * Confirm scan from preview
 */
const confirmScan = () => {
  if (pendingScanCode.value) {
    emit('scan', pendingScanCode.value, previewAsset.value)
  }
  previewVisible.value = true
}

/**
 * Get status type
 */
const getStatusType = (status: AssetStatus): string => {
  const types: Record<AssetStatus, string> = {
    draft: 'info',
    in_use: 'success',
    idle: 'warning',
    maintenance: 'danger',
    scrapped: 'info'
  }
  return types[status] || 'info'
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
  return new Date(date).toLocaleTimeString('zh-CN', {
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit'
  })
}

/**
 * Public method to set total count
 */
const setTotalCount = (count: number) => {
  totalCount.value = count
}

/**
 * Public method to reset scanner
 */
const reset = () => {
  scannedCodes.value.clear()
  scannedCount.value = 0
  lastScanStatus.value = 'idle'
  lastScanMessage.value = '准备扫描...'
}

// ============================================================================
// Lifecycle
// ============================================================================

onMounted(() => {
  initScanner()
})

onUnmounted(() => {
  stopScanner()
})

// ============================================================================
// Expose
// ============================================================================

defineExpose({
  setTotalCount,
  reset,
  startScanner,
  stopScanner
})
</script>

<style scoped lang="scss">
.qr-scanner {
  display: flex;
  flex-direction: column;
  height: 100%;
  background: #000;
}

.scanner-container {
  position: relative;
  flex: 1;
  min-height: 300px;
  overflow: hidden;
}

.scanner-video {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.scan-overlay {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  background: rgba(0, 0, 0, 0.3);
}

.scan-frame {
  width: 260px;
  height: 260px;
  border: 3px solid rgba(64, 158, 255, 0.8);
  border-radius: 16px;
  position: relative;
  background: rgba(0, 0, 0, 0.2);
  box-shadow: 0 0 0 400px rgba(0, 0, 0, 0.5);

  // Corner markers
  &::before,
  &::after {
    content: '';
    position: absolute;
    width: 30px;
    height: 30px;
    border-color: #409eff;
    border-style: solid;
  }

  &::before {
    top: -3px;
    left: -3px;
    border-width: 4px 0 0 4px;
    border-radius: 12px 0 0 0;
  }

  &::after {
    bottom: -3px;
    right: -3px;
    border-width: 0 4px 4px 0;
    border-radius: 0 0 12px 0;
  }
}

.scan-line {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 3px;
  background: linear-gradient(90deg, transparent, #409eff, transparent);
  animation: scan 2s linear infinite;
  box-shadow: 0 0 10px #409eff;
}

@keyframes scan {
  0% { top: 0; }
  50% { top: calc(100% - 3px); }
  100% { top: 0; }
}

.scan-hint {
  margin-top: 24px;
  color: white;
  font-size: 15px;
  text-shadow: 0 1px 3px rgba(0, 0, 0, 0.8);
  background: rgba(0, 0, 0, 0.5);
  padding: 8px 16px;
  border-radius: 20px;
}

.torch-control {
  position: absolute;
  top: 16px;
  right: 16px;
  z-index: 10;

  .el-button {
    background: rgba(0, 0, 0, 0.6);
    border-color: rgba(255, 255, 255, 0.3);
    color: white;

    &:hover {
      background: rgba(0, 0, 0, 0.8);
    }
  }
}

.camera-selector {
  position: absolute;
  top: 16px;
  left: 16px;
  z-index: 10;

  :deep(.el-select) {
    background: rgba(0, 0, 0, 0.6);

    .el-input__wrapper {
      background: transparent;
      box-shadow: none;
      border: 1px solid rgba(255, 255, 255, 0.3);
    }

    .el-input__inner {
      color: white;
    }
  }
}

.scan-info {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 20px;
  background: #1a1a1a;
  color: white;
}

.scan-count {
  display: flex;
  align-items: center;
  gap: 4px;

  .count-label {
    font-size: 14px;
    color: #909399;
  }

  .count-number {
    font-size: 24px;
    font-weight: 600;
    color: #409eff;
  }

  .count-divider {
    margin: 0 4px;
    color: #606266;
  }

  .count-total {
    font-size: 16px;
    color: #909399;
  }
}

.scan-status {
  font-size: 14px;

  &.status-idle { color: #909399; }
  &.status-success { color: #67c23a; }
  &.status-error { color: #f56c6c; }
}

.scanner-controls {
  display: flex;
  gap: 12px;
  padding: 16px 20px;
  background: #1a1a1a;

  .el-button {
    flex: 1;
    background: #2a2a2a;
    border-color: #3a3a3a;
    color: white;

    &:hover {
      background: #3a3a3a;
      border-color: #4a4a4a;
    }
  }
}

.asset-preview {
  :deep(.el-descriptions__label) {
    width: 100px;
  }
}
</style>
