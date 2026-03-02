# Phase 4.2: RFID Inventory - Frontend Implementation v2

## Document Information

| Project | Details |
|---------|---------|
| PRD Version | v2.0 (Updated for API Standardization) |
| Updated Date | 2026-01-22 |
| References | [frontend_api_standardization_design.md](../common_base_features/00_core/frontend_api_standardization_design.md) |

---

## Task Overview

Implement RFID batch inventory scanning with PC management interface and mobile scanning capabilities for efficient asset inventory.

---

## API Service Layer

### Type Definitions

```typescript
// frontend/src/types/rfid.ts

export interface RfidTask extends InventoryTask {
  rfidDeviceId?: string
  rfidDevice?: RfidDevice
  scanMode: ScanMode
  readPower?: number
}

export enum ScanMode {
  SINGLE = 'single',
  CONTINUOUS = 'continuous',
  BATCH = 'batch'
}

export interface RfidDevice {
  id: string
  name: string
  model: string
  deviceId: string
  deviceType: DeviceType
  status: DeviceStatus
  batteryLevel?: number
  signalStrength?: number
  lastConnectedAt?: string
}

export enum DeviceType {
  HANDHELD = 'handheld',
  FIXED = 'fixed',
  BLUETOOTH = 'bluetooth'
}

export enum DeviceStatus {
  ONLINE = 'online',
  OFFLINE = 'offline',
  CONNECTING = 'connecting',
  ERROR = 'error'
}

export interface RfidScanResult {
  id: string
  taskId: string
  tagEpc: string
  assetId?: string
  asset?: Asset
  scanned: boolean
  scannedAt?: string
  rssi?: number
  scanCount: number
  scanResult?: ScanResult
  remark?: string
}

export interface RfidTag {
  id: string
  epc: string
  assetId?: string
  asset?: Asset
  status: TagStatus
  assignedAt?: string
  lastScannedAt?: string
}

export enum TagStatus {
  ASSIGNED = 'assigned',
  UNASSIGNED = 'unassigned',
  DAMAGED = 'damaged',
  LOST = 'lost'
}
```

### API Service

```typescript
// frontend/src/api/rfid.ts

import request from '@/utils/request'
import type { PaginatedResponse } from '@/types/api'
import type { RfidTask, RfidDevice, RfidScanResult, RfidTag } from '@/types/rfid'

export const rfidApi = {
  // RFID Tasks
  listTasks(params?: any): Promise<PaginatedResponse<RfidTask>> {
    return request.get('/inventory/rfid/tasks/', { params })
  },

  getTask(id: string): Promise<RfidTask> {
    return request.get(`/inventory/rfid/tasks/${id}/`)
  },

  createTask(data: {
    taskName: string
    locationId?: string
    rfidDeviceId: string
    scanMode: ScanMode
    plannedDate: string
  }): Promise<RfidTask> {
    return request.post('/inventory/rfid/tasks/', data)
  },

  startScan(id: string): Promise<void> {
    return request.post(`/inventory/rfid/tasks/${id}/scan-start/`)
  },

  pauseScan(id: string): Promise<void> {
    return request.post(`/inventory/rfid/tasks/${id}/scan-stop/`)
  },

  getRecentTags(id: string): Promise<{ items: RfidScanResult[]; scannedCount: number }> {
    return request.get(`/inventory/rfid/tasks/${id}/recent-tags/`)
  },

  getScanResults(id: string, params?: {
    filter?: 'all' | 'scanned' | 'unscanned' | 'abnormal'
  }): Promise<PaginatedResponse<RfidScanResult>> {
    return request.get(`/inventory/rfid/tasks/${id}/results/`, { params })
  },

  confirmTag(taskId: string, tagId: string, data: {
    scanResult: ScanResult
    remark?: string
  }): Promise<void> {
    return request.post(`/inventory/rfid/tasks/${taskId}/tags/${tagId}/confirm/`, data)
  },

  sync(id: string): Promise<void> {
    return request.post(`/inventory/rfid/tasks/${id}/sync/`)
  },

  complete(id: string): Promise<void> {
    return request.post(`/inventory/rfid/tasks/${id}/complete/`)
  },

  // RFID Devices
  listDevices(): Promise<RfidDevice[]> {
    return request.get('/inventory/rfid/devices/')
  },

  connectDevice(id: string): Promise<void> {
    return request.post(`/inventory/rfid/devices/${id}/connect/`)
  },

  disconnectDevice(id: string): Promise<void> {
    return request.post(`/inventory/rfid/devices/${id}/disconnect/`)
  },

  getDeviceStatus(id: string): Promise<RfidDevice> {
    return request.get(`/inventory/rfid/devices/${id}/status/`)
  },

  // RFID Tags
  listTags(params?: { status?: TagStatus }): Promise<PaginatedResponse<RfidTag>> {
    return request.get('/inventory/rfid/tags/', { params })
  },

  assignTag(epc: string, assetId: string): Promise<RfidTag> {
    return request.post('/inventory/rfid/tags/assign/', { epc, assetId })
  },

  unassignTag(tagId: string): Promise<void> {
    return request.post(`/inventory/rfid/tags/${tagId}/unassign/`)
  }
}
```

---

## Component: RfidScanPage

```vue
<!-- frontend/src/views/inventory/mobile/rfid/RfidScanPage.vue -->
<template>
  <div class="rfid-scan-page">
    <van-nav-bar
      :title="task.taskName"
      left-text="返回"
      @click-left="goBack"
    >
      <template #right>
        <van-icon :name="isScanning ? 'pause' : 'play'" @click="toggleScan" />
      </template>
    </van-nav-bar>

    <!-- RFID Device Status -->
    <RfidReaderStatus
      :device="rfidDevice"
      :connected="deviceConnected"
      :battery="batteryLevel"
      :signal-strength="signalStrength"
    />

    <!-- Scan Progress -->
    <div class="scan-progress">
      <div class="progress-info">
        <span class="scanned">{{ task.scannedCount }}</span>
        <span class="separator">/</span>
        <span class="total">{{ task.assetCount }}</span>
        <span class="percentage">({{ getProgress }}%)</span>
      </div>
      <van-progress
        :percentage="getProgress"
        :color="getProgress === 100 ? '#52c41a' : '#1989fa'"
      />
    </div>

    <!-- Recent Tags -->
    <div class="recent-tags">
      <div class="section-title">最近扫描 ({{ recentTags.length }})</div>
      <van-empty v-if="recentTags.length === 0" description="暂无扫描记录" />
      <div v-else class="tag-list">
        <div
          v-for="tag in recentTags"
          :key="tag.id"
          class="tag-item"
          @click="handleShowTag(tag)"
        >
          <div class="tag-info">
            <span class="tag-epc">{{ tag.tagEpc }}</span>
            <span class="tag-name">{{ tag.asset?.name || '未关联' }}</span>
          </div>
          <van-tag :type="getScanResultType(tag)">
            {{ getScanResultLabel(tag) }}
          </van-tag>
        </div>
      </div>
    </div>

    <!-- Scan Controls -->
    <div class="scan-controls">
      <van-button
        v-if="!isScanning"
        type="primary"
        block
        size="large"
        @click="startScan"
      >
        开始扫描
      </van-button>
      <van-button
        v-else
        type="warning"
        block
        size="large"
        @click="pauseScan"
      >
        暂停扫描
      </van-button>

      <van-button
        v-if="getProgress >= 100"
        type="success"
        block
        @click="handleComplete"
      >
        完成盘点
      </van-button>
    </div>

    <!-- Tag Detail Popup -->
    <van-popup
      v-model:show="tagDetailVisible"
      position="bottom"
      :style="{ height: '70%' }"
    >
      <RfidTagDetail
        :tag="currentTag"
        :task="task"
        @confirm="handleTagConfirm"
        @close="tagDetailVisible = false"
      />
    </van-popup>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { rfidApi } from '@/api/rfid'
import RfidReaderStatus from '@/components/inventory/rfid/RfidReaderStatus.vue'
import RfidTagDetail from '@/components/inventory/rfid/RfidTagDetail.vue'
import type { RfidTask, RfidDevice, RfidScanResult } from '@/types/rfid'

const router = useRouter()
const route = useRoute()

const task = ref<RfidTask>({
  id: route.params.id as string,
  taskName: '',
  assetCount: 0,
  scannedCount: 0,
  status: 'pending'
} as RfidTask)

const isScanning = ref(false)
const deviceConnected = ref(false)
const batteryLevel = ref(100)
const signalStrength = ref(4)
const rfidDevice = ref<RfidDevice | null>(null)
const recentTags = ref<RfidScanResult[]>([])
const tagDetailVisible = ref(false)
const currentTag = ref<RfidScanResult | null>(null)

let scanInterval: number | null = null

const getProgress = computed(() => {
  return task.value.assetCount > 0
    ? Math.round((task.value.scannedCount / task.value.assetCount) * 100)
    : 0
})

const getScanResultType = (tag: RfidScanResult) => {
  if (!tag.scanned) return 'default'
  if (!tag.scanResult || tag.scanResult === 'normal') return 'success'
  return 'danger'
}

const getScanResultLabel = (tag: RfidScanResult) => {
  if (!tag.scanned) return '未扫描'
  if (!tag.scanResult || tag.scanResult === 'normal') return '正常'
  const labels: Record<string, string> = {
    location_changed: '位置变更',
    damaged: '损坏',
    missing: '缺失'
  }
  return labels[tag.scanResult] || '异常'
}

const startScan = async () => {
  try {
    await rfidApi.startScan(task.value.id)
    isScanning.value = true
    startPolling()
  } catch (error) {
    showToast('启动扫描失败')
  }
}

const pauseScan = async () => {
  try {
    await rfidApi.pauseScan(task.value.id)
    isScanning.value = false
    stopPolling()
  } catch (error) {
    showToast('暂停扫描失败')
  }
}

const startPolling = () => {
  scanInterval = window.setInterval(async () => {
    try {
      const { items, scannedCount } = await rfidApi.getRecentTags(task.value.id)
      recentTags.value = items
      task.value.scannedCount = scannedCount

      if (navigator.vibrate && items.length > 0) {
        navigator.vibrate(50)
      }
    } catch (error) {
      console.error('获取扫描结果失败', error)
    }
  }, 2000)
}

const stopPolling = () => {
  if (scanInterval) {
    clearInterval(scanInterval)
    scanInterval = null
  }
}

const toggleScan = () => {
  if (isScanning.value) {
    pauseScan()
  } else {
    startScan()
  }
}

const handleShowTag = (tag: RfidScanResult) => {
  currentTag.value = tag
  tagDetailVisible.value = true
}

const handleTagConfirm = async (result: any) => {
  try {
    await rfidApi.confirmTag(task.value.id, currentTag.value!.id, result)
    await fetchRecentTags()
    tagDetailVisible.value = false
  } catch (error) {
    showToast('确认失败')
  }
}

const handleComplete = () => {
  router.push(`/inventory/rfid/${task.value.id}/complete`)
}

const goBack = () => {
  router.back()
}

const fetchTaskDetail = async () => {
  const data = await rfidApi.getTask(task.value.id)
  task.value = { ...task.value, ...data }
}

const fetchRecentTags = async () => {
  const data = await rfidApi.getRecentTags(task.value.id)
  recentTags.value = data.items
}

onMounted(async () => {
  await fetchTaskDetail()

  if (task.value.status === 'in_progress') {
    isScanning.value = true
    await fetchRecentTags()
    startPolling()
  }
})

onUnmounted(() => {
  stopPolling()
})
</script>

<style scoped>
.rfid-scan-page {
  min-height: 100vh;
  background: #f5f5f5;
  padding-bottom: 80px;
}

.scan-progress {
  background: white;
  padding: 16px;
  margin-bottom: 12px;
}

.progress-info {
  display: flex;
  justify-content: space-between;
  margin-bottom: 8px;
  font-size: 14px;
}

.progress-info .scanned {
  font-size: 20px;
  font-weight: bold;
  color: #1989fa;
}

.progress-info .separator {
  color: #999;
}

.progress-info .total {
  color: #333;
}

.progress-info .percentage {
  color: #999;
}

.recent-tags {
  background: white;
  padding: 16px;
  margin-bottom: 12px;
}

.section-title {
  font-size: 14px;
  font-weight: 500;
  color: #333;
  margin-bottom: 12px;
}

.tag-list {
  max-height: 300px;
  overflow-y: auto;
}

.tag-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 0;
  border-bottom: 1px solid #eee;
}

.tag-info {
  flex: 1;
}

.tag-epc {
  font-size: 12px;
  color: #999;
  display: block;
}

.tag-name {
  font-size: 14px;
  color: #333;
  font-weight: 500;
}

.scan-controls {
  position: fixed;
  bottom: 0;
  left: 0;
  right: 0;
  padding: 12px 16px;
  background: white;
  box-shadow: 0 -2px 10px rgba(0, 0, 0, 0.1);
  z-index: 100;
}
</style>
```

---

## Component: RfidReaderStatus

```vue
<!-- frontend/src/components/inventory/rfid/RfidReaderStatus.vue -->
<template>
  <div class="rfid-reader-status">
    <div class="device-card">
      <div class="device-icon">
        <el-icon :size="32" :color="connected ? '#52c41a' : '#999'">
          <Connection />
        </el-icon>
      </div>
      <div class="device-info">
        <div class="device-name">
          {{ device?.name || '未连接设备' }}
        </div>
        <div v-if="device" class="device-model">
          {{ device.model }}
        </div>
      </div>
      <div class="connection-status">
        <el-tag :type="connected ? 'success' : 'info'" size="small">
          {{ connected ? '已连接' : '未连接' }}
        </el-tag>
      </div>
    </div>

    <div v-if="connected && batteryLevel !== null" class="battery-info">
      <span class="battery-label">电量:</span>
      <div class="battery-bar">
        <div
          class="battery-fill"
          :class="{ low: batteryLevel < 20, medium: batteryLevel < 50 }"
          :style="{ width: batteryLevel + '%' }"
        />
      </div>
      <span class="battery-value">{{ batteryLevel }}%</span>
    </div>

    <div v-if="connected" class="signal-strength">
      <span class="signal-label">信号:</span>
      <div class="signal-bars">
        <div class="bar" :class="{ active: signalStrength >= 1 }" />
        <div class="bar" :class="{ active: signalStrength >= 2 }" />
        <div class="bar" :class="{ active: signalStrength >= 3 }" />
        <div class="bar" :class="{ active: signalStrength >= 4 }" />
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { Connection } from '@element-plus/icons-vue'
import type { RfidDevice } from '@/types/rfid'

interface Props {
  device: RfidDevice | null
  connected: boolean
  battery: number | null
  signalStrength?: number
}

defineProps<Props>()
</script>

<style scoped>
.rfid-reader-status {
  background: white;
  padding: 12px;
  margin-bottom: 12px;
  border-radius: 8px;
}

.device-card {
  display: flex;
  align-items: center;
  gap: 12px;
}

.device-icon {
  flex-shrink: 0;
}

.device-info {
  flex: 1;
}

.device-name {
  font-size: 14px;
  font-weight: 500;
  color: #333;
}

.device-model {
  font-size: 12px;
  color: #999;
}

.battery-info {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-top: 8px;
  font-size: 12px;
}

.battery-bar {
  flex: 1;
  height: 12px;
  background: #eee;
  border-radius: 6px;
  overflow: hidden;
}

.battery-fill {
  height: 100%;
  background: #52c41a;
  transition: width 0.3s;
}

.battery-fill.low {
  background: #f56c6c;
}

.battery-fill.medium {
  background: #e6a23c;
}

.signal-strength {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-top: 8px;
  font-size: 12px;
}

.signal-bars {
  display: flex;
  gap: 2px;
}

.signal-bars .bar {
  width: 4px;
  height: 12px;
  background: #ddd;
  border-radius: 2px;
}

.signal-bars .bar.active {
  background: #52c41a;
}
</style>
```

---

## Output Files

| File | Description |
|------|-------------|
| `frontend/src/types/rfid.ts` | RFID type definitions |
| `frontend/src/api/rfid.ts` | RFID API service |
| `frontend/src/views/inventory/mobile/rfid/RfidScanPage.vue` | Mobile RFID scan page |
| `frontend/src/views/inventory/rfid/RfidTaskList.vue` | RFID task list (PC) |
| `frontend/src/views/inventory/rfid/RfidTaskDetail.vue` | RFID task detail (PC) |
| `frontend/src/components/inventory/rfid/RfidReaderStatus.vue` | Device status component |
| `frontend/src/components/inventory/rfid/RfidTagDetail.vue` | Tag detail component |
