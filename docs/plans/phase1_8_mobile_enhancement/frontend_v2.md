# Phase 1.8: Mobile Enhancement - Frontend Implementation v2

## Document Information

| Project | Details |
|---------|---------|
| PRD Version | v2.0 (Updated for API Standardization) |
| Updated Date | 2026-01-22 |
| References | [frontend_api_standardization_design.md](../common_base_features/00_core/frontend_api_standardization_design.md) |

---

## Task Overview

Implement mobile-first features including offline sync, QR scanning, and responsive components.

---

## API Service Layer

### Type Definitions

```typescript
// frontend/src/types/mobile.ts

export interface SyncStatus {
  isSyncing: boolean
  lastSyncAt: string
  lastServerVersion: number
  pendingCount: number
  progress: number
  syncStatus: 'idle' | 'syncing' | 'success' | 'error'
}

export interface SyncUploadData {
  deviceId: string
  data: SyncRecord[]
}

export interface SyncRecord {
  tableName: string
  recordId: string
  operation: 'create' | 'update' | 'delete'
  data: Record<string, any>
  oldData?: Record<string, any>
  version: number
  createdAt: string
}

export interface SyncUploadResponse {
  summary: {
    total: number
    succeeded: number
    failed: number
    conflicts: number
  }
  results: SyncResult[]
  errors: Array<{
    record: SyncRecord
    error: string
  }>
}

export interface SyncResult {
  tableName: string
  recordId: string
  success: boolean
  serverVersion?: number
  error?: string
}

export interface SyncDownloadData {
  lastVersion: number
  deviceId: string
}

export interface PendingApproval {
  id: string
  type: string
  title: string
  requesterName: string
  createdAt: string
  canApprove: boolean
  canReject: boolean
}

export interface ApprovalAction {
  approvalId: string
  action: 'approve' | 'reject'
  comment?: string
}
```

### API Service

```typescript
// frontend/src/api/mobile.ts

import request from '@/utils/request'
import type {
  SyncStatus,
  SyncUploadData,
  SyncUploadResponse,
  SyncDownloadData,
  PendingApproval
} from '@/types/mobile'

export const mobileApi = {
  // Sync APIs
  getSyncStatus(): Promise<SyncStatus> {
    return request.get('/mobile/sync/status/')
  },

  uploadOfflineData(data: SyncUploadData): Promise<SyncUploadResponse> {
    return request.post('/mobile/sync/upload/', data)
  },

  downloadServerChanges(data: SyncDownloadData): Promise<any> {
    return request.post('/mobile/sync/download/', data)
  },

  // Approval APIs
  getPendingApprovals(): Promise<PendingApproval[]> {
    return request.get('/mobile/approval/pending/')
  },

  submitApproval(data: ApprovalAction): Promise<void> {
    return request.post('/mobile/approval/approve/', data)
  }
}
```

---

## Composable: Offline Sync

```typescript
// frontend/src/composables/useOfflineSync.ts

import { ref } from 'vue'
import { mobileApi } from '@/api/mobile'
import type { SyncStatus } from '@/types/mobile'

export function useOfflineSync() {
  const syncStatus = ref<SyncStatus>({
    isSyncing: false,
    lastSyncAt: '',
    lastServerVersion: 0,
    pendingCount: 0,
    progress: 0,
    syncStatus: 'idle'
  })

  /**
   * Check sync status
   */
  const checkSyncStatus = async () => {
    try {
      syncStatus.value = await mobileApi.getSyncStatus()
    } catch (error) {
      syncStatus.value.syncStatus = 'error'
    }
  }

  /**
   * Upload offline data
   */
  const uploadOfflineData = async () => {
    syncStatus.value.isSyncing = true
    syncStatus.value.syncStatus = 'syncing'
    syncStatus.value.progress = 0

    try {
      // Get pending records from IndexedDB
      const pendingRecords = await getPendingRecords()

      const result = await mobileApi.uploadOfflineData({
        deviceId: getDeviceId(),
        data: pendingRecords
      })

      syncStatus.value.progress = 100
      syncStatus.value.syncStatus = result.summary.failed > 0 ? 'error' : 'success'
      syncStatus.value.pendingCount = result.summary.failed

      // Clear synced records
      await clearSyncedRecords(result.results)

      return result
    } catch (error) {
      syncStatus.value.syncStatus = 'error'
      throw error
    } finally {
      syncStatus.value.isSyncing = false
    }
  }

  /**
   * Download server changes
   */
  const downloadServerChanges = async () => {
    syncStatus.value.isSyncing = true
    syncStatus.value.syncStatus = 'syncing'

    try {
      const changes = await mobileApi.downloadServerChanges({
        lastVersion: syncStatus.value.lastServerVersion,
        deviceId: getDeviceId()
      })

      // Apply changes to IndexedDB
      await applyChanges(changes)

      syncStatus.value.lastSyncAt = new Date().toISOString()
      syncStatus.value.syncStatus = 'success'
    } catch (error) {
      syncStatus.value.syncStatus = 'error'
      throw error
    } finally {
      syncStatus.value.isSyncing = false
    }
  }

  /**
   * Full sync (upload + download)
   */
  const fullSync = async () => {
    await uploadOfflineData()
    await downloadServerChanges()
  }

  return {
    syncStatus,
    checkSyncStatus,
    uploadOfflineData,
    downloadServerChanges,
    fullSync
  }
}

// Helper functions (would use IndexedDB)
async function getPendingRecords() {
  // Get records from IndexedDB sync queue
  return []
}

async function clearSyncedRecords(results: any[]) {
  // Clear synced records from IndexedDB
}

async function applyChanges(changes: any) {
  // Apply server changes to IndexedDB
}

function getDeviceId(): string {
  let deviceId = localStorage.getItem('device_id')
  if (!deviceId) {
    deviceId = generateUUID()
    localStorage.setItem('device_id', deviceId)
  }
  return deviceId
}

function generateUUID(): string {
  return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, (c) => {
    const r = Math.random() * 16 | 0
    const v = c === 'x' ? r : (r & 0x3 | 0x8)
    return v.toString(16)
  })
}
```

---

## Component: SyncIndicator

```vue
<!-- frontend/src/components/mobile/SyncIndicator.vue -->
<template>
  <div class="sync-indicator">
    <el-tooltip :content="syncTooltip">
      <el-badge :value="syncStatus.pendingCount" :hidden="syncStatus.pendingCount === 0">
        <el-button
          :icon="syncIcon"
          :loading="syncStatus.isSyncing"
          circle
          @click="handleSync"
        />
      </el-badge>
    </el-tooltip>

    <!-- Sync Progress Dialog -->
    <el-dialog v-model="showProgress" title="同步中" width="400px" :close-on-click-modal="false">
      <el-progress :percentage="syncStatus.progress" :status="syncStatus.syncStatus" />
      <p class="sync-message">{{ syncMessage }}</p>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { useOfflineSync } from '@/composables/useOfflineSync'
import { ElMessage } from 'element-plus'

const { syncStatus, fullSync, checkSyncStatus } = useOfflineSync()

const showProgress = ref(false)

const syncIcon = computed(() => {
  if (syncStatus.value.isSyncing) return 'Loading'
  if (syncStatus.value.syncStatus === 'error') return 'Warning'
  if (syncStatus.value.syncStatus === 'success') return 'CircleCheck'
  return 'Refresh'
})

const syncTooltip = computed(() => {
  if (syncStatus.value.isSyncing) return '正在同步...'
  if (syncStatus.value.lastSyncAt) {
    return `上次同步: ${new Date(syncStatus.value.lastSyncAt).toLocaleString()}`
  }
  return '点击同步'
})

const syncMessage = computed(() => {
  const messages: Record<string, string> = {
    idle: '准备同步...',
    syncing: `正在同步... ${syncStatus.value.progress}%`,
    success: `同步完成！成功 ${syncStatus.value.lastServerVersion} 条`,
    error: `同步失败，${syncStatus.value.pendingCount} 条数据待处理`
  }
  return messages[syncStatus.value.syncStatus] || ''
})

const handleSync = async () => {
  showProgress.value = true
  try {
    await fullSync()
    ElMessage.success('同步成功')
  } catch (error) {
    ElMessage.error('同步失败')
  } finally {
    showProgress.value = false
  }
}

// Check sync status on mount
checkSyncStatus()
</script>

<style scoped>
.sync-indicator {
  display: inline-block;
}

.sync-message {
  text-align: center;
  margin-top: 16px;
}
</style>
```

---

## Output Files

| File | Description |
|------|-------------|
| `frontend/src/types/mobile.ts` | Mobile type definitions |
| `frontend/src/api/mobile.ts` | Mobile API service |
| `frontend/src/composables/useOfflineSync.ts` | Offline sync composable |
| `frontend/src/components/mobile/SyncIndicator.vue` | Sync indicator component |
| `frontend/src/components/mobile/OfflineBanner.vue` | Offline status banner |
| `frontend/src/components/mobile/ScanButton.vue` | QR scan button component |
