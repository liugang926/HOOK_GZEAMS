<!--
  Mobile QR Scanner Component

  Mobile-optimized QR code scanner component.
  Features:
  - Full-screen camera view
  - Touch-optimized controls
  - Vibration feedback
  - Torch toggle
  - Camera switching
-->

<template>
  <div class="mobile-qr-scanner">
    <div class="scanner-container" ref="containerRef">
      <video
        ref="videoRef"
        class="scanner-video"
        autoplay
        playsinline
        muted
      />

      <!-- Scan Overlay -->
      <div class="scan-overlay">
        <div class="scan-frame">
          <div class="scan-line"></div>
          <div class="scan-corner top-left"></div>
          <div class="scan-corner top-right"></div>
          <div class="scan-corner bottom-left"></div>
          <div class="scan-corner bottom-right"></div>
        </div>
        <p class="scan-hint">将二维码放入框内自动扫描</p>
      </div>

      <!-- Top Controls -->
      <div class="top-controls">
        <van-button
          v-if="cameras.length > 1"
          icon="photo-o"
          size="small"
          round
          @click="showCameraSelector = true"
        />
      </div>

      <!-- Bottom Controls -->
      <div class="bottom-controls">
        <van-button
          v-if="hasTorch"
          :icon="torchOn ? 'photo-fail' : 'photo'"
          size="large"
          round
          @click="toggleTorch"
        />
        <van-button
          icon="aim"
          size="large"
          round
          type="primary"
          @click="handleManualInput"
        />
      </div>
    </div>

    <!-- Scan Status Overlay -->
    <transition name="fade">
      <div v-if="lastScanStatus" class="scan-status-overlay" :class="`status-${lastScanStatus}`">
        <van-icon
          :name="lastScanStatus === 'success' ? 'checked' : 'close'"
          :size="48"
        />
        <p>{{ lastScanMessage }}</p>
      </div>
    </transition>

    <!-- Camera Selector -->
    <van-action-sheet
      v-model:show="showCameraSelector"
      title="选择摄像头"
      :actions="cameraActions"
      @select="handleCameraSelect"
    />

    <!-- Manual Input -->
    <van-dialog
      v-model:show="inputVisible"
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
  </div>
</template>

<script setup lang="ts">
/**
 * Mobile QR Scanner Component
 *
 * Mobile-optimized QR scanner using @zxing/library.
 * Features fullscreen camera, touch controls, and vibration feedback.
 */

import { ref, onMounted, onUnmounted } from 'vue'
import { showToast } from 'vant'
import { BrowserMultiFormatReader } from '@zxing/library'
import { qrScanApi } from '@/api/inventory'

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
const codeReader = new BrowserMultiFormatReader()
const stream = ref<MediaStream | null>(null)
const torchOn = ref(false)
const hasTorch = ref(false)

const cameras = ref<Array<{ id: string; label: string }>>([])
const selectedCameraId = ref('')
const showCameraSelector = ref(false)
const cameraActions = ref<Array<{ name: string; value: string }>>([])

const scannedCount = ref(0)
const totalCount = ref(0)
const lastScanStatus = ref<'success' | 'error' | null>(null)
const lastScanMessage = ref('')
const scannedCodes = ref<Set<string>>(new Set())

const inputVisible = ref(false)
const manualCode = ref('')

let isScanning = false
let lastScanTime = 0
const SCAN_COOLDOWN = 2000 // ms between scans
let statusTimeout: ReturnType<typeof setTimeout> | null = null

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
      .slice(0, 3)

    cameraActions.value = cameras.value.map(c => ({
      name: c.label,
      value: c.id
    }))

    if (cameras.value.length === 0) {
      emit('error', '未检测到摄像头')
      return
    }

    // Select back camera by default
    const backCamera = cameras.value.find(c =>
      c.label.toLowerCase().includes('back') ||
      c.label.toLowerCase().includes('environment') ||
      c.label.toLowerCase().includes('后')
    )
    selectedCameraId.value = backCamera?.id || cameras.value[0].id

    await startScanner()
  } catch (error) {
    console.error('Failed to initialize scanner:', error)
    emit('error', '摄像头初始化失败，请检查权限设置')
  }
}

/**
 * Start scanner
 */
const startScanner = async () => {
  try {
    stopScanner()

    const constraints: MediaStreamConstraints = {
      video: {
        deviceId: selectedCameraId.value ? { exact: selectedCameraId.value } : undefined,
        facingMode: 'environment',
        width: { ideal: 1920 },
        height: { ideal: 1080 }
      }
    }

    stream.value = await navigator.mediaDevices.getUserMedia(constraints)

    if (videoRef.value) {
      videoRef.value.srcObject = stream.value
      videoRef.value.play()

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
    const capabilities = (track as any)?.getCapabilities?.()
    hasTorch.value = capabilities?.torch || false

  } catch (error: any) {
    console.error('Failed to start scanner:', error)
    emit('error', error.message || '无法访问摄像头')
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
  const now = Date.now()
  if (scannedCodes.value.has(code) || now - lastScanTime < SCAN_COOLDOWN) {
    return
  }

  lastScanTime = now

  // Vibration feedback
  if (navigator.vibrate) {
    navigator.vibrate(100)
  }

  // Show processing status
  showScanStatus('success', '扫描成功')

  try {
    const asset = await qrScanApi.getAssetByQrCode(code)
    scannedCodes.value.add(code)
    scannedCount.value++

    if (props.autoSubmit || !props.showPreview) {
      emit('scan', code, asset)
    } else {
      // Show preview - handled by parent component
      emit('scan', code, asset)
    }

    // Clear status after delay
    clearStatusAfterDelay()
  } catch (error) {
    showScanStatus('error', '未找到资产')
    emit('error', `未找到资产: ${code}`)
    clearStatusAfterDelay()
  }
}

/**
 * Show scan status overlay
 */
const showScanStatus = (status: 'success' | 'error', message: string) => {
  lastScanStatus.value = status
  lastScanMessage.value = message
}

/**
 * Clear status after delay
 */
const clearStatusAfterDelay = () => {
  if (statusTimeout) {
    clearTimeout(statusTimeout)
  }
  statusTimeout = setTimeout(() => {
    lastScanStatus.value = null
  }, 1500)
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
  const currentIndex = cameras.value.findIndex(c => c.id === selectedCameraId.value)
  const nextIndex = (currentIndex + 1) % cameras.value.length
  selectedCameraId.value = cameras.value[nextIndex].id
  await startScanner()
}

/**
 * Handle camera select
 */
const handleCameraSelect = (action: any) => {
  selectedCameraId.value = action.value
  startScanner()
}

/**
 * Handle manual input
 */
const handleManualInput = () => {
  inputVisible.value = true
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
  lastScanStatus.value = null
}

// ============================================================================
// Lifecycle
// ============================================================================

onMounted(() => {
  initScanner()
})

onUnmounted(() => {
  stopScanner()
  if (statusTimeout) {
    clearTimeout(statusTimeout)
  }
})

// ============================================================================
// Expose
// ============================================================================

defineExpose({
  setTotalCount,
  reset,
  startScanner,
  stopScanner,
  switchCamera,
  toggleTorch
})
</script>

<style scoped lang="scss">
.mobile-qr-scanner {
  position: relative;
  width: 100%;
  height: 100%;
  background: #000;
}

.scanner-container {
  position: relative;
  width: 100%;
  height: 100%;
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
  background: rgba(0, 0, 0, 0.2);
}

.scan-frame {
  width: 280px;
  height: 280px;
  position: relative;

  .scan-line {
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    height: 4px;
    background: linear-gradient(90deg, transparent, #00e676, transparent);
    animation: scan 2s linear infinite;
    box-shadow: 0 0 20px #00e676;
  }
}

@keyframes scan {
  0% { top: 0; }
  50% { top: calc(100% - 4px); }
  100% { top: 0; }
}

.scan-corner {
  position: absolute;
  width: 40px;
  height: 40px;
  border: 4px solid #00e676;

  &.top-left {
    top: 0;
    left: 0;
    border-right: none;
    border-bottom: none;
    border-radius: 8px 0 0 0;
  }

  &.top-right {
    top: 0;
    right: 0;
    border-left: none;
    border-bottom: none;
    border-radius: 0 8px 0 0;
  }

  &.bottom-left {
    bottom: 0;
    left: 0;
    border-right: none;
    border-top: none;
    border-radius: 0 0 0 8px;
  }

  &.bottom-right {
    bottom: 0;
    right: 0;
    border-left: none;
    border-top: none;
    border-radius: 0 0 8px 0;
  }
}

.scan-hint {
  margin-top: 40px;
  color: white;
  font-size: 16px;
  text-shadow: 0 2px 4px rgba(0, 0, 0, 0.8);
  background: rgba(0, 0, 0, 0.6);
  padding: 10px 20px;
  border-radius: 20px;
}

.top-controls {
  position: absolute;
  top: 16px;
  left: 16px;
  z-index: 10;
}

.bottom-controls {
  position: absolute;
  bottom: 32px;
  left: 0;
  right: 0;
  display: flex;
  justify-content: center;
  gap: 24px;
  z-index: 10;

  .van-button {
    width: 56px;
    height: 56px;
    background: rgba(255, 255, 255, 0.9);
    border: none;

    :deep(.van-icon) {
      font-size: 24px;
    }
  }
}

.scan-status-overlay {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 16px;
  padding: 32px;
  background: rgba(0, 0, 0, 0.85);
  border-radius: 16px;
  color: white;
  z-index: 20;

  &.status-success .van-icon {
    color: #00e676;
  }

  &.status-error .van-icon {
    color: #ff3b30;
  }

  p {
    font-size: 16px;
    margin: 0;
  }
}

.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.3s;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}
</style>
