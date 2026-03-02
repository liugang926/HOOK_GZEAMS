# Phase 2.2: WeWork Sync - Frontend Implementation v2

## Document Information

| Project | Details |
|---------|---------|
| PRD Version | v2.0 (Updated for API Standardization) |
| Updated Date | 2026-01-22 |
| References | [frontend_api_standardization_design.md](../common_base_features/00_core/frontend_api_standardization_design.md) |

---

## Task Overview

Implement WeWork organization and user synchronization management interface.

---

## API Service Layer

### Type Definitions

```typescript
// frontend/src/types/wework.ts

export interface WeWorkSyncConfig {
  enabled: boolean
  autoSync: boolean
  syncInterval: number
  syncDepartments: boolean
  syncUsers: boolean
  departmentMapping?: Record<string, string>
  userMapping?: Record<string, string>
}

export interface WeWorkSyncStatus {
  isSyncing: boolean
  lastSyncAt: string
  nextSyncAt?: string
  lastSyncStatus: 'success' | 'failed' | 'partial'
  lastSyncStats?: SyncStats
  progress?: number
}

export interface SyncStats {
  total: number
  succeeded: number
  failed: number
  skipped: number
  duration: number
}

export interface WeWorkSyncLog {
  id: string
  syncType: 'full' | 'incremental' | 'manual'
  status: 'pending' | 'running' | 'completed' | 'failed'
  stats?: SyncStats
  errorMessage?: string
  createdAt: string
  completedAt?: string
}
```

### API Service

```typescript
// frontend/src/api/wework.ts

import request from '@/utils/request'
import type {
  WeWorkSyncConfig,
  WeWorkSyncStatus,
  WeWorkSyncLog
} from '@/types/wework'

export const weworkSyncApi = {
  getConfig(): Promise<WeWorkSyncConfig> {
    return request.get('/sso/sync/config/')
  },

  updateConfig(config: Partial<WeWorkSyncConfig>): Promise<WeWorkSyncConfig> {
    return request.put('/sso/sync/config/', config)
  },

  getStatus(): Promise<WeWorkSyncStatus> {
    return request.get('/sso/sync/status/')
  },

  getLogs(params?: any): Promise<{ results: WeWorkSyncLog[]; count: number }> {
    return request.get('/sso/sync/logs/', { params })
  },

  getLogDetail(id: string): Promise<WeWorkSyncLog> {
    return request.get(`/sso/sync/logs/${id}/`)
  },

  triggerSync(syncType: 'full' | 'incremental' = 'incremental'): Promise<void> {
    return request.post('/sso/sync/trigger/', { syncType })
  }
}
```

---

## Component: Sync Management

```vue
<!-- frontend/src/views/sso/WeWorkSyncManagement.vue -->
<template>
  <div class="sync-management">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>企业微信同步配置</span>
          <el-button
            type="primary"
            :loading="syncStatus.isSyncing"
            :disabled="syncStatus.isSyncing"
            @click="handleTriggerSync"
          >
            立即同步
          </el-button>
        </div>
      </template>

      <!-- Sync Status -->
      <el-descriptions :column="3" border>
        <el-descriptions-item label="同步状态">
          <el-tag :type="getStatusTagType(syncStatus.lastSyncStatus)">
            {{ getStatusLabel(syncStatus.lastSyncStatus) }}
          </el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="上次同步">
          {{ formatDateTime(syncStatus.lastSyncAt) || '未同步' }}
        </el-descriptions-item>
        <el-descriptions-item label="下次同步">
          {{ formatDateTime(syncStatus.nextSyncAt) || '-' }}
        </el-descriptions-item>
        <el-descriptions-item label="同步数量" :span="3">
          <template v-if="syncStatus.lastSyncStats">
            总计: {{ syncStatus.lastSyncStats.total }} |
            成功: {{ syncStatus.lastSyncStats.succeeded }} |
            失败: {{ syncStatus.lastSyncStats.failed }} |
            跳过: {{ syncStatus.lastSyncStats.skipped }} |
            耗时: {{ syncStatus.lastSyncStats.duration }}s
          </template>
        </el-descriptions-item>
      </el-descriptions>
    </el-card>

    <!-- Configuration -->
    <el-card class="config-card">
      <template #header>
        <span>同步配置</span>
      </template>

      <el-form :model="config" label-width="140px">
        <el-form-item label="启用自动同步">
          <el-switch v-model="config.autoSync" />
        </el-form-item>

        <el-form-item label="同步间隔">
          <el-input-number
            v-model="config.syncInterval"
            :min="5"
            :max="1440"
            :step="5"
          />
          <span style="margin-left: 8px">分钟</span>
        </el-form-item>

        <el-form-item label="同步部门">
          <el-switch v-model="config.syncDepartments" />
        </el-form-item>

        <el-form-item label="同步用户">
          <el-switch v-model="config.syncUsers" />
        </el-form-item>

        <el-form-item>
          <el-button type="primary" @click="handleSaveConfig">保存配置</el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <!-- Sync Logs -->
    <el-card>
      <template #header>
        <span>同步日志</span>
      </template>

      <el-table :data="logs" v-loading="loadingLogs">
        <el-table-column prop="id" label="日志ID" width="200" />
        <el-table-column prop="syncType" label="同步类型" width="120">
          <template #default="{ row }">
            <el-tag size="small">{{ getSyncTypeLabel(row.syncType) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="status" label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="getLogStatusTagType(row.status)" size="small">
              {{ getLogStatusLabel(row.status) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="统计" width="300">
          <template #default="{ row }">
            <template v-if="row.stats">
              总计: {{ row.stats.total }} | 成功: {{ row.stats.succeeded }} |
              失败: {{ row.stats.failed }}
            </template>
          </template>
        </el-table-column>
        <el-table-column prop="errorMessage" label="错误信息" show-overflow-tooltip />
        <el-table-column prop="createdAt" label="开始时间" width="180" />
        <el-table-column prop="completedAt" label="完成时间" width="180" />
      </el-table>
    </el-card>

    <!-- Progress Dialog -->
    <el-dialog v-model="showProgress" title="同步中" width="400px" :close-on-click-modal="false">
      <el-progress :percentage="syncProgress" :status="syncStatus.lastSyncStatus" />
      <p class="progress-text">正在同步企业微信数据...</p>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { ElMessage } from 'element-plus'
import { weworkSyncApi } from '@/api/wework'
import type { WeWorkSyncConfig, WeWorkSyncStatus, WeWorkSyncLog } from '@/types/wework'

const config = ref<WeWorkSyncConfig>({
  enabled: false,
  autoSync: false,
  syncInterval: 60,
  syncDepartments: true,
  syncUsers: true
})

const syncStatus = ref<WeWorkSyncStatus>({
  isSyncing: false,
  lastSyncAt: '',
  lastSyncStatus: 'success'
})

const logs = ref<WeWorkSyncLog[]>([])
const loadingLogs = ref(false)
const showProgress = ref(false)

let pollTimer: number | null = null

const syncProgress = computed(() => {
  return syncStatus.value.progress || 0
})

/**
 * Load sync config
 */
const loadConfig = async () => {
  try {
    config.value = await weworkSyncApi.getConfig()
  } catch (error) {
    // Error handled by interceptor
  }
}

/**
 * Load sync status
 */
const loadStatus = async () => {
  try {
    syncStatus.value = await weworkSyncApi.getStatus()

    if (syncStatus.value.isSyncing) {
      showProgress.value = true
      startPolling()
    } else {
      showProgress.value = false
      stopPolling()
    }
  } catch (error) {
    // Error handled by interceptor
  }
}

/**
 * Load sync logs
 */
const loadLogs = async () => {
  loadingLogs.value = true
  try {
    const response = await weworkSyncApi.getLogs({ limit: 10 })
    logs.value = response.results
  } catch (error) {
    // Error handled by interceptor
  } finally {
    loadingLogs.value = false
  }
}

/**
 * Save config
 */
const handleSaveConfig = async () => {
  try {
    await weworkSyncApi.updateConfig(config.value)
    ElMessage.success('配置已保存')
  } catch (error) {
    // Error handled by interceptor
  }
}

/**
 * Trigger sync
 */
const handleTriggerSync = async () => {
  try {
    await weworkSyncApi.triggerSync('incremental')
    showProgress.value = true
    await loadStatus()
  } catch (error) {
    // Error handled by interceptor
  }
}

/**
 * Start polling for sync status
 */
const startPolling = () => {
  stopPolling()
  pollTimer = window.setInterval(() => {
    loadStatus()
  }, 3000)
}

/**
 * Stop polling
 */
const stopPolling = () => {
  if (pollTimer) {
    clearInterval(pollTimer)
    pollTimer = null
  }
}

/**
 * Format date time
 */
const formatDateTime = (dateStr: string) => {
  if (!dateStr) return ''
  return new Date(dateStr).toLocaleString('zh-CN')
}

/**
 * Get status tag type
 */
const getStatusTagType = (status: string) => {
  const typeMap: Record<string, string> = {
    success: 'success',
    failed: 'danger',
    partial: 'warning'
  }
  return typeMap[status] || 'info'
}

/**
 * Get status label
 */
const getStatusLabel = (status: string) => {
  const labelMap: Record<string, string> = {
    success: '成功',
    failed: '失败',
    partial: '部分成功'
  }
  return labelMap[status] || status
}

/**
 * Get sync type label
 */
const getSyncTypeLabel = (type: string) => {
  const labelMap: Record<string, string> = {
    full: '全量同步',
    incremental: '增量同步',
    manual: '手动同步'
  }
  return labelMap[type] || type
}

/**
 * Get log status tag type
 */
const getLogStatusTagType = (status: string) => {
  const typeMap: Record<string, string> = {
    completed: 'success',
    failed: 'danger',
    running: 'warning',
    pending: 'info'
  }
  return typeMap[status] || 'info'
}

/**
 * Get log status label
 */
const getLogStatusLabel = (status: string) => {
  const labelMap: Record<string, string> = {
    completed: '已完成',
    failed: '失败',
    running: '运行中',
    pending: '等待中'
  }
  return labelMap[status] || status
}

onMounted(() => {
  loadConfig()
  loadStatus()
  loadLogs()
})

onUnmounted(() => {
  stopPolling()
})
</script>

<style scoped>
.sync-management {
  padding: 20px;
}

.sync-management .el-card {
  margin-bottom: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.progress-text {
  text-align: center;
  margin-top: 16px;
  color: var(--el-text-color-secondary);
}
</style>
```

---

## Output Files

| File | Description |
|------|-------------|
| `frontend/src/types/wework.ts` | WeWork sync type definitions |
| `frontend/src/api/wework.ts` | WeWork sync API service |
| `frontend/src/views/sso/WeWorkSyncManagement.vue` | Sync management page |
