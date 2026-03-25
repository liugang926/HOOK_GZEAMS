# Phase 4.1: QR Code Inventory - Frontend Implementation v2

## Document Information

| Project | Details |
|---------|---------|
| PRD Version | v2.0 (Updated for API Standardization) |
| Updated Date | 2026-01-22 |
| References | [frontend_api_standardization_design.md](../common_base_features/00_core/frontend_api_standardization_design.md) |

---

## Task Overview

Implement QR code scanning, inventory task execution, asset tracking, and label printing for asset inventory management.

---

## API Service Layer

### Type Definitions

```typescript
// frontend/src/types/inventory.ts

export interface InventoryTask {
  id: string
  taskNo: string
  taskName: string
  taskType: TaskType
  status: TaskStatus
  plannedDate: string
  startDate?: string
  endDate?: string
  locationId?: string
  location?: Location
  assetCount: number
  scannedCount: number
  abnormalCount: number
  executorId?: string
  executor?: User
  remark?: string
  organizationId: string
  createdAt: string
  updatedAt: string
}

export enum TaskType {
  FULL = 'full',
  PARTIAL = 'partial',
  CATEGORY = 'category',
  LOCATION = 'location'
}

export enum TaskStatus {
  DRAFT = 'draft',
  PENDING = 'pending',
  IN_PROGRESS = 'in_progress',
  COMPLETED = 'completed',
  CANCELLED = 'cancelled'
}

export interface Location {
  id: string
  code: string
  name: string
  parentId?: string
  level: number
  path?: string
}

export interface User {
  id: string
  username: string
  realName: string
}

export interface InventorySnapshot {
  id: string
  taskId: string
  assetId: string
  asset?: Asset
  expectedLocation?: string
  expectedCustodian?: string
  status: SnapshotStatus
  scanned: boolean
  scannedAt?: string
  scanMethod?: ScanMethod
  actualLocation?: string
  scanResult?: ScanResult
  remark?: string
  photos?: string[]
}

export enum SnapshotStatus {
  PENDING = 'pending',
  SCANNED = 'scanned',
  MISSING = 'missing',
  ABNORMAL = 'abnormal'
}

export enum ScanMethod {
  QR = 'qr',
  MANUAL = 'manual',
  RFID = 'rfid'
}

export enum ScanResult {
  NORMAL = 'normal',
  LOCATION_CHANGED = 'location_changed',
  DAMAGED = 'damaged',
  MISSING = 'missing',
  EXTRA = 'extra'
}

export interface Asset {
  id: string
  code: string
  name: string
  categoryId?: string
  category?: AssetCategory
  specification?: string
  unit?: string
  status: AssetStatus
  locationId?: string
  location?: Location
  custodianId?: string
  custodian?: User
}

export enum AssetStatus {
  NORMAL = 'normal',
  IN_USE = 'in_use',
  IDLE = 'idle',
  DAMAGED = 'damaged',
  LOST = 'lost',
  SCRAPPED = 'scrapped'
}

export interface AssetCategory {
  id: string
  code: string
  name: string
}

export interface InventoryStatistics {
  totalCount: number
  scannedCount: number
  normalCount: number
  abnormalCount: number
  missingCount: number
  extraCount: number
  damagedCount: number
  locationChangedCount: number
  progress: number
}

export interface InventoryDifference {
  id: string
  taskId: string
  assetId: string
  asset?: Asset
  differenceType: DifferenceType
  description: string
  status: DifferenceStatus
  resolvedAt?: string
  resolution?: string
}

export enum DifferenceType {
  MISSING = 'missing',
  EXTRA = 'extra',
  LOCATION_CHANGED = 'location_changed',
  DAMAGED = 'damaged',
  DATA_MISMATCH = 'data_mismatch'
}

export enum DifferenceStatus {
  PENDING = 'pending',
  RESOLVED = 'resolved',
  IGNORED = 'ignored'
}

export interface AssetLabel {
  id: string
  assetId: string
  labelType: LabelType
  qrCode: string
  printCount: number
  lastPrintedAt?: string
}

export enum LabelType {
  STANDARD = 'standard',
  SMALL = 'small',
  LARGE = 'large'
}
```

### API Service

```typescript
// frontend/src/api/inventory.ts

import request from '@/utils/request'
import type { PaginatedResponse } from '@/types/api'
import type {
  InventoryTask,
  InventorySnapshot,
  InventoryStatistics,
  InventoryDifference,
  AssetLabel,
  ScanRecordCreate
} from '@/types/inventory'

export const inventoryApi = {
  // Tasks
  listTasks(params?: {
    status?: TaskStatus
    taskType?: TaskType
    page?: number
    pageSize?: number
  }): Promise<PaginatedResponse<InventoryTask>> {
    return request.get('/inventory/tasks/', { params })
  },

  getTask(id: string): Promise<InventoryTask> {
    return request.get(`/inventory/tasks/${id}/`)
  },

  createTask(data: {
    taskName: string
    taskType: TaskType
    plannedDate: string
    locationId?: string
    categoryIds?: string[]
    remark?: string
  }): Promise<InventoryTask> {
    return request.post('/inventory/tasks/', data)
  },

  updateTask(id: string, data: Partial<InventoryTask>): Promise<InventoryTask> {
    return request.put(`/inventory/tasks/${id}/`, data)
  },

  startTask(id: string): Promise<void> {
    return request.post(`/inventory/tasks/${id}/start/`)
  },

  completeTask(id: string): Promise<void> {
    return request.post(`/inventory/tasks/${id}/complete/`)
  },

  cancelTask(id: string, reason?: string): Promise<void> {
    return request.post(`/inventory/tasks/${id}/cancel/`, { reason })
  },

  // Statistics
  getStatistics(taskId: string): Promise<InventoryStatistics> {
    return request.get(`/inventory/tasks/${taskId}/statistics/`)
  },

  // Scanning
  recordScan(taskId: string, data: ScanRecordCreate): Promise<InventorySnapshot> {
    return request.post(`/inventory/tasks/${taskId}/scan/`, data)
  },

  // Snapshots
  getSnapshots(taskId: string, params?: {
    status?: SnapshotStatus
    page?: number
    pageSize?: number
  }): Promise<PaginatedResponse<InventorySnapshot>> {
    return request.get(`/inventory/tasks/${taskId}/snapshots/`, { params })
  },

  updateSnapshot(taskId: string, snapshotId: string, data: {
    scanResult?: ScanResult
    actualLocation?: string
    remark?: string
    photos?: string[]
  }): Promise<InventorySnapshot> {
    return request.patch(`/inventory/tasks/${taskId}/snapshots/${snapshotId}/`, data)
  },

  // Differences
  getDifferences(taskId: string): Promise<InventoryDifference[]> {
    return request.get(`/inventory/tasks/${taskId}/differences/`)
  },

  resolveDifference(taskId: string, differenceId: string, data: {
    action: 'resolve' | 'ignore'
    resolution?: string
  }): Promise<void> {
    return request.post(`/inventory/tasks/${taskId}/differences/${differenceId}/resolve/`, data)
  },

  // Asset Labels
  generateLabel(assetId: string, labelType: LabelType): Promise<{ qrCode: string; labelData: any }> {
    return request.post(`/inventory/assets/${assetId}/label/generate/`, { labelType })
  },

  printLabel(assetId: string): Promise<AssetLabel> {
    return request.post(`/inventory/assets/${assetId}/label/print/`)
  },

  getLabelPrintData(assetId: string): Promise<{ qrCode: string; assetData: any }> {
    return request.get(`/inventory/assets/${assetId}/label/data/`)
  }
}
```

---

## Component: QRScanner

```vue
<!-- frontend/src/components/inventory/QRScanner.vue -->
<template>
  <div class="qr-scanner">
    <div v-if="!scannedAsset" class="scanner-container">
      <!-- Video Preview -->
      <div class="video-container" ref="videoContainer">
        <video
          ref="videoRef"
          muted
          playsinline
          :class="{ active: scanning }"
        />

        <!-- Scan Overlay -->
        <div v-if="scanning" class="scan-overlay">
          <div class="scan-corner corner-tl" />
          <div class="scan-corner corner-tr" />
          <div class="scan-corner corner-bl" />
          <div class="scan-corner corner-br" />
          <div class="scan-line" />
          <div class="scan-tip">将二维码放入框内</div>
        </div>

        <!-- Camera Placeholder -->
        <div v-else class="camera-placeholder">
          <el-icon :size="60"><VideoCamera /></el-icon>
          <p>点击下方按钮启动摄像头</p>
        </div>
      </div>

      <!-- Control Buttons -->
      <div class="scanner-controls">
        <el-button
          v-if="!scanning"
          type="primary"
          size="large"
          :icon="VideoCamera"
          @click="startScan"
        >
          启动扫描
        </el-button>

        <template v-else>
          <el-button
            v-if="videoDevices.length > 1"
            size="large"
            @click="switchCamera"
          >
            切换摄像头
          </el-button>
          <el-button
            type="danger"
            size="large"
            @click="stopScan"
          >
            停止扫描
          </el-button>
        </template>

        <el-button
          size="large"
          @click="manualInputVisible = true"
        >
          手动输入
        </el-button>
      </div>

      <!-- Scan History -->
      <div v-if="scanHistory.length > 0" class="scan-history">
        <div class="history-header">
          <span>扫描历史 ({{ scanHistory.length }})</span>
        </div>
        <div class="history-list">
          <div
            v-for="(item, index) in scanHistory.slice(0, 5)"
            :key="index"
            class="history-item"
          >
            <span class="asset-code">{{ item.code }}</span>
            <span class="scan-time">{{ formatTime(item.scannedAt) }}</span>
          </div>
        </div>
      </div>
    </div>

    <!-- Scan Result -->
    <div v-else class="scan-result">
      <el-card>
        <template #header>
          <div class="result-header">
            <div class="success-icon">
              <el-icon color="#67c23a" :size="32">
                <CircleCheck />
              </el-icon>
            </div>
            <span class="result-title">扫描成功</span>
            <el-button
              text
              type="primary"
              @click="continueScan"
            >
              继续扫描
            </el-button>
          </div>
        </template>

        <ScanResultForm
          :asset="scannedAsset"
          :task-id="taskId"
          @confirmed="handleConfirmed"
          @continue="continueScan"
        />
      </el-card>
    </div>

    <!-- Manual Input Dialog -->
    <el-dialog
      v-model="manualInputVisible"
      title="手动输入资产编码"
      width="400px"
    >
      <el-input
        v-model="manualCode"
        placeholder="请输入资产编码"
        clearable
        @keyup.enter="handleManualInput"
      />
      <template #footer>
        <el-button @click="manualInputVisible = false">取消</el-button>
        <el-button type="primary" @click="handleManualInput">确认</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue'
import { BrowserMultiFormatReader } from '@zxing/library'
import { VideoCamera, CircleCheck } from '@element-plus/icons-vue'
import { assetApi } from '@/api/assets'
import { inventoryApi } from '@/api/inventory'
import ScanResultForm from './ScanResultForm.vue'
import type { Asset } from '@/types/inventory'

interface Props {
  taskId: string
  continuous?: boolean
}

interface Emits {
  (e: 'scanned', asset: Asset): void
  (e: 'error', message: string): void
}

const props = withDefaults(defineProps<Props>(), {
  continuous: true
})

const emit = defineEmits<Emits>()

const videoRef = ref<HTMLVideoElement>()
const codeReader = ref<BrowserMultiFormatReader>()
const scanning = ref(false)
const scannedAsset = ref<Asset | null>(null)
const scanHistory = ref<Array<{ code: string; scannedAt: string }>>([])
const videoDevices = ref<MediaDeviceInfo[]>([])
const selectedDeviceId = ref('')
const manualInputVisible = ref(false)
const manualCode = ref('')

onMounted(async () => {
  await initCamera()
})

onUnmounted(() => {
  stopScan()
})

const initCamera = async () => {
  try {
    codeReader.value = new BrowserMultiFormatReader()
    const devices = await codeReader.value.listVideoInputDevices()
    videoDevices.value = devices

    if (devices.length > 0) {
      selectedDeviceId.value = devices[0].deviceId
    }
  } catch (error) {
    emit('error', '无法访问摄像头')
  }
}

const startScan = async () => {
  if (!selectedDeviceId.value || !codeReader.value) {
    emit('error', '未检测到摄像头设备')
    return
  }

  try {
    await codeReader.value.decodeFromVideoDevice(
      selectedDeviceId.value,
      videoRef.value!,
      (result, error) => {
        if (result) {
          handleScanResult(result.text)
        }
      }
    )
    scanning.value = true
  } catch (error) {
    emit('error', '无法启动摄像头')
  }
}

const stopScan = () => {
  codeReader.value?.reset()
  scanning.value = false
}

const switchCamera = () => {
  stopScan()
  const currentIndex = videoDevices.value.findIndex(
    d => d.deviceId === selectedDeviceId.value
  )
  const nextIndex = (currentIndex + 1) % videoDevices.value.length
  selectedDeviceId.value = videoDevices.value[nextIndex].deviceId
  startScan()
}

const handleScanResult = async (qrData: string) => {
  try {
    const data = JSON.parse(qrData)

    if (data.type !== 'asset') {
      emit('error', '请扫描资产二维码')
      return
    }

    const asset = await assetApi.getByCode(data.asset_code)
    scannedAsset.value = asset

    playBeep()
    if (navigator.vibrate) {
      navigator.vibrate(200)
    }

    emit('scanned', asset)

    scanHistory.value.unshift({
      code: asset.code,
      scannedAt: new Date().toISOString()
    })

    if (!props.continuous) {
      stopScan()
    }
  } catch (error) {
    emit('error', '无效的二维码')
  }
}

const handleManualInput = async () => {
  if (!manualCode.value.trim()) return

  try {
    const asset = await assetApi.getByCode(manualCode.value.trim())
    scannedAsset.value = asset
    emit('scanned', asset)
    manualCode.value = ''
    manualInputVisible.value = false
  } catch (error) {
    emit('error', '未找到该资产')
  }
}

const playBeep = () => {
  const audioContext = new (window.AudioContext || window.webkitAudioContext)()
  const oscillator = audioContext.createOscillator()
  const gainNode = audioContext.createGain()

  oscillator.connect(gainNode)
  gainNode.connect(audioContext.destination)

  oscillator.frequency.value = 1000
  oscillator.type = 'sine'

  gainNode.gain.setValueAtTime(0.1, audioContext.currentTime)

  oscillator.start()
  oscillator.stop(audioContext.currentTime + 0.15)
}

const continueScan = () => {
  scannedAsset.value = null
  if (!scanning.value) {
    startScan()
  }
}

const handleConfirmed = () => {
  continueScan()
}

const formatTime = (dateStr: string) => {
  const date = new Date(dateStr)
  const now = new Date()
  const diff = now.getTime() - date.getTime()

  if (diff < 60000) return '刚刚'
  if (diff < 3600000) return `${Math.floor(diff / 60000)}分钟前`
  if (diff < 86400000) return `${Math.floor(diff / 3600000)}小时前`
  return date.toLocaleDateString('zh-CN')
}
</script>

<style scoped>
.qr-scanner {
  max-width: 600px;
  margin: 0 auto;
  padding: 20px;
}

.video-container {
  position: relative;
  width: 100%;
  height: 400px;
  background: #000;
  border-radius: 16px;
  overflow: hidden;
}

.video-container video {
  width: 100%;
  height: 100%;
  object-fit: cover;
  opacity: 0.3;
}

.video-container video.active {
  opacity: 1;
}

.scan-overlay {
  position: absolute;
  inset: 0;
  display: flex;
  align-items: center;
  justify-content: center;
}

.scan-corner {
  position: absolute;
  width: 60px;
  height: 60px;
  border: 3px solid #00ff00;
}

.corner-tl {
  top: 80px;
  left: 50%;
  transform: translateX(-50%);
  border-right: none;
  border-bottom: none;
}

.corner-tr {
  top: 80px;
  left: 50%;
  transform: translateX(-50%);
  border-left: none;
  border-bottom: none;
}

.corner-bl {
  bottom: 80px;
  left: 50%;
  transform: translateX(-50%);
  border-right: none;
  border-top: none;
}

.corner-br {
  bottom: 80px;
  left: 50%;
  transform: translateX(-50%);
  border-left: none;
  border-top: none;
}

.scan-line {
  position: absolute;
  top: 80px;
  left: 50%;
  transform: translateX(-50%);
  width: 240px;
  height: 2px;
  background: linear-gradient(to right, transparent, #00ff00, transparent);
  animation: scanMove 2s infinite;
}

@keyframes scanMove {
  0%, 100% { top: 80px; }
  50% { top: 300px; }
}

.scan-tip {
  position: absolute;
  bottom: 60px;
  left: 50%;
  transform: translateX(-50%);
  color: white;
  font-size: 14px;
  white-space: nowrap;
}

.camera-placeholder {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 100%;
  color: rgba(255, 255, 255, 0.6);
}

.scanner-controls {
  display: flex;
  justify-content: center;
  gap: 12px;
  margin-top: 20px;
  flex-wrap: wrap;
}

.scan-history {
  margin-top: 24px;
  padding: 16px;
  background: #f5f7fa;
  border-radius: 8px;
}

.history-header {
  font-size: 14px;
  font-weight: 500;
  margin-bottom: 12px;
}

.history-item {
  display: flex;
  justify-content: space-between;
  padding: 8px 0;
  border-bottom: 1px solid #ebeef5;
}

.history-item:last-child {
  border-bottom: none;
}

.asset-code {
  font-family: 'Monaco', monospace;
  color: #303133;
}

.scan-time {
  color: #909399;
  font-size: 12px;
}

.result-header {
  display: flex;
  align-items: center;
  gap: 12px;
}

.success-icon {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 48px;
  height: 48px;
  background: #f0f9ff;
  border-radius: 50%;
}

.result-title {
  flex: 1;
  font-size: 16px;
  font-weight: 500;
}
</style>
```

---

## Component: InventoryProgress

```vue
<!-- frontend/src/components/inventory/InventoryProgress.vue -->
<template>
  <div class="inventory-progress">
    <el-row :gutter="16">
      <el-col :span="6">
        <el-card shadow="hover" class="stat-card">
          <el-statistic title="应盘资产" :value="statistics.totalCount">
            <template #suffix>项</template>
          </el-statistic>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="hover" class="stat-card success">
          <el-statistic title="已盘点" :value="statistics.scannedCount">
            <template #suffix>项</template>
          </el-statistic>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="hover" class="stat-card warning">
          <el-statistic title="异常" :value="statistics.abnormalCount">
            <template #suffix>项</template>
          </el-statistic>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="hover" class="stat-card info">
          <el-statistic title="盘点进度">
            <template #default>
              <div class="progress-value">
                {{ statistics.progress }}%
              </div>
            </template>
          </el-statistic>
        </el-card>
      </el-col>
    </el-row>

    <!-- Progress Bar -->
    <div class="progress-bar-container">
      <div class="progress-label">
        <span>盘点进度</span>
        <span>{{ statistics.scannedCount }} / {{ statistics.totalCount }}</span>
      </div>
      <el-progress
        :percentage="statistics.progress"
        :status="getProgressStatus(statistics.progress)"
        :stroke-width="20"
      />
    </div>

    <!-- Detail Stats -->
    <el-card v-if="showDetails" class="detail-stats">
      <template #header>详细统计</template>
      <el-row :gutter="16">
        <el-col :span="8">
          <div class="detail-item">
            <span class="detail-label">正常</span>
            <span class="detail-value normal">{{ statistics.normalCount }}</span>
          </div>
        </el-col>
        <el-col :span="8">
          <div class="detail-item">
            <span class="detail-label">盘亏</span>
            <span class="detail-value missing">{{ statistics.missingCount }}</span>
          </div>
        </el-col>
        <el-col :span="8">
          <div class="detail-item">
            <span class="detail-label">盘盈</span>
            <span class="detail-value extra">{{ statistics.extraCount }}</span>
          </div>
        </el-col>
        <el-col :span="8">
          <div class="detail-item">
            <span class="detail-label">损坏</span>
            <span class="detail-value damaged">{{ statistics.damagedCount }}</span>
          </div>
        </el-col>
        <el-col :span="8">
          <div class="detail-item">
            <span class="detail-label">位置变更</span>
            <span class="detail-value location">{{ statistics.locationChangedCount }}</span>
          </div>
        </el-col>
      </el-row>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import type { InventoryStatistics } from '@/types/inventory'

interface Props {
  statistics: InventoryStatistics
  showDetails?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  showDetails: true
})

const getProgressStatus = (progress: number) => {
  if (progress >= 100) return 'success'
  if (progress >= 50) return undefined
  return 'exception'
}
</script>

<style scoped>
.inventory-progress {
  margin-bottom: 20px;
}

.stat-card {
  text-align: center;
}

.stat-card.success :deep(.el-statistic__content) {
  color: #67c23a;
}

.stat-card.warning :deep(.el-statistic__content) {
  color: #e6a23c;
}

.stat-card.info :deep(.el-statistic__content) {
  color: #409eff;
}

.progress-value {
  font-size: 32px;
  font-weight: bold;
  color: #409eff;
}

.progress-bar-container {
  margin-top: 16px;
  padding: 16px;
  background: white;
  border-radius: 8px;
}

.progress-label {
  display: flex;
  justify-content: space-between;
  margin-bottom: 12px;
  font-size: 14px;
  color: #606266;
}

.detail-stats {
  margin-top: 16px;
}

.detail-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 0;
  border-bottom: 1px solid #ebeef5;
}

.detail-item:last-child {
  border-bottom: none;
}

.detail-label {
  color: #909399;
  font-size: 14px;
}

.detail-value {
  font-size: 20px;
  font-weight: 500;
}

.detail-value.normal { color: #67c23a; }
.detail-value.missing { color: #f56c6c; }
.detail-value.extra { color: #409eff; }
.detail-value.damaged { color: #e6a23c; }
.detail-value.location { color: #909399; }
</style>
```

---

## Output Files

| File | Description |
|------|-------------|
| `frontend/src/types/inventory.ts` | Inventory type definitions |
| `frontend/src/api/inventory.ts` | Inventory API service |
| `frontend/src/components/inventory/QRScanner.vue` | QR scanner component |
| `frontend/src/components/inventory/ScanResultForm.vue` | Scan result form |
| `frontend/src/components/inventory/InventoryProgress.vue` | Inventory progress display |
| `frontend/src/views/inventory/TaskList.vue` | Inventory task list |
| `frontend/src/views/inventory/TaskExecute.vue` | Task execution page |
| `frontend/src/views/inventory/TaskDetail.vue` | Task detail page |
| `frontend/src/views/inventory/AssetLabel.vue` | Asset label printing |
