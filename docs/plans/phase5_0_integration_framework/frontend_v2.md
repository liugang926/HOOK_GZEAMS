# Phase 5.0: Integration Framework - Frontend Implementation v2

## Document Information

| Project | Details |
|---------|---------|
| PRD Version | v2.0 (Updated for API Standardization) |
| Updated Date | 2026-01-22 |
| References | [frontend_api_standardization_design.md](../common_base_features/00_core/frontend_api_standardization_design.md) |

---

## Task Overview

Implement integration framework for external system connections including M18 ERP and financial system integration.

---

## API Service Layer

### Type Definitions

```typescript
// frontend/src/types/integration.ts

export interface IntegrationConfig {
  id: string
  name: string
  code: string
  integrationType: 'm18' | 'finance' | 'oa' | 'custom'
  isEnabled: boolean
  config: Record<string, any>
  lastSyncAt?: string
  lastSyncStatus?: 'success' | 'failed' | 'partial'
  organizationId: string
}

export interface M18Config {
  apiBaseUrl: string
  apiKey: string
  apiSecret: string
  companyCode: string
  autoSync: boolean
  syncInterval: number
}

export interface SyncJob {
  id: string
  integrationId: string
  integrationName: string
  jobType: 'purchase_orders' | 'assets' | 'vendors'
  status: 'pending' | 'running' | 'completed' | 'failed'
  progress: number
  startedAt: string
  completedAt?: string
  result?: SyncJobResult
}

export interface SyncJobResult {
  total: number
  succeeded: number
  failed: number
  skipped: number
  errors: Array<{
    record: string
    error: string
  }>
}

export interface PurchaseOrderSync {
  startDate?: string
  endDate?: string
  orderNos?: string[]
  async: boolean
}
```

### API Service

```typescript
// frontend/src/api/integration.ts

import request from '@/utils/request'
import type { PaginatedResponse, BatchResponse } from '@/types/api'
import type {
  IntegrationConfig,
  M18Config,
  SyncJob,
  PurchaseOrderSync
} from '@/types/integration'

export const integrationApi = {
  // Integration Config
  getConfigs(): Promise<IntegrationConfig[]> {
    return request.get('/integration/configs/')
  },

  getConfig(id: string): Promise<IntegrationConfig> {
    return request.get(`/integration/configs/${id}/`)
  },

  updateConfig(id: string, config: Partial<IntegrationConfig>): Promise<IntegrationConfig> {
    return request.put(`/integration/configs/${id}/`, config)
  },

  // M18 Integration
  getM18Status(): Promise<{ connected: boolean; lastSyncAt?: string }> {
    return request.get('/integration/m18/status/')
  },

  testM18Connection(): Promise<{ success: boolean; message: string }> {
    return request.post('/integration/m18/test-connection/')
  },

  syncPurchaseOrders(data: PurchaseOrderSync): Promise<SyncJob> {
    return request.post('/integration/m18/sync/purchase-orders/', data)
  },

  syncAssets(): Promise<SyncJob> {
    return request.post('/integration/m18/sync/assets/')
  },

  // Sync Jobs
  getJobs(params?: any): Promise<PaginatedResponse<SyncJob>> {
    return request.get('/integration/jobs/', { params })
  },

  getJob(id: string): Promise<SyncJob> {
    return request.get(`/integration/jobs/${id}/`)
  },

  retryJob(id: string): Promise<SyncJob> {
    return request.post(`/integration/jobs/${id}/retry/`)
  }
}
```

---

## Component: Integration List

```vue
<!-- frontend/src/views/integration/IntegrationList.vue -->
<template>
  <div class="integration-list">
    <el-card>
      <template #header>
        <span>系统集成</span>
      </template>

      <el-table :data="configs">
        <el-table-column prop="name" label="名称" width="200" />
        <el-table-column prop="code" label="编码" width="150" />
        <el-table-column prop="integrationType" label="类型" width="120">
          <template #default="{ row }">
            <el-tag>{{ getIntegrationTypeLabel(row.integrationType) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="isEnabled" label="状态" width="100">
          <template #default="{ row }">
            <el-switch
              :model-value="row.isEnabled"
              @change="handleToggle(row)"
            />
          </template>
        </el-table-column>
        <el-table-column prop="lastSyncStatus" label="上次同步" width="100">
          <template #default="{ row }">
            <el-tag v-if="row.lastSyncStatus" :type="getSyncStatusTagType(row.lastSyncStatus)">
              {{ getSyncStatusLabel(row.lastSyncStatus) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="lastSyncAt" label="同步时间" width="180">
          <template #default="{ row }">
            {{ formatDateTime(row.lastSyncAt) }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="250" fixed="right">
          <template #default="{ row }">
            <el-button link type="primary" @click="handleConfig(row)">
              配置
            </el-button>
            <el-button link type="success" @click="handleTest(row)">
              测试连接
            </el-button>
            <el-button link @click="handleSync(row)">
              立即同步
            </el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <!-- M18 Config Dialog -->
    <M18ConfigDialog
      v-model="configVisible"
      :config="selectedConfig"
      @saved="handleConfigSaved"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { integrationApi } from '@/api/integration'
import M18ConfigDialog from './components/M18ConfigDialog.vue'
import type { IntegrationConfig } from '@/types/integration'

const configs = ref<IntegrationConfig[]>([])
const selectedConfig = ref<IntegrationConfig>()
const configVisible = ref(false)

const loadConfigs = async () => {
  try {
    configs.value = await integrationApi.getConfigs()
  } catch (error) {
    // Error handled by interceptor
  }
}

const handleToggle = async (row: IntegrationConfig) => {
  try {
    await integrationApi.updateConfig(row.id, {
      isEnabled: !row.isEnabled
    })
    ElMessage.success('状态已更新')
    loadConfigs()
  } catch (error) {
    // Error handled by interceptor
  }
}

const handleConfig = (row: IntegrationConfig) => {
  selectedConfig.value = row
  configVisible.value = true
}

const handleTest = async (row: IntegrationConfig) => {
  try {
    const result = await integrationApi.testM18Connection()
    if (result.success) {
      ElMessage.success('连接测试成功')
    } else {
      ElMessage.error(result.message)
    }
  } catch (error) {
    // Error handled by interceptor
  }
}

const handleSync = async (row: IntegrationConfig) => {
  try {
    await integrationApi.syncAssets()
    ElMessage.success('同步任务已创建')
  } catch (error) {
    // Error handled by interceptor
  }
}

const handleConfigSaved = () => {
  configVisible.value = false
  loadConfigs()
}

const getIntegrationTypeLabel = (type: string) => {
  const labelMap: Record<string, string> = {
    m18: 'M18 ERP',
    finance: '财务系统',
    oa: 'OA系统',
    custom: '自定义'
  }
  return labelMap[type] || type
}

const getSyncStatusTagType = (status: string) => {
  const typeMap: Record<string, string> = {
    success: 'success',
    failed: 'danger',
    partial: 'warning'
  }
  return typeMap[status] || 'info'
}

const getSyncStatusLabel = (status: string) => {
  const labelMap: Record<string, string> = {
    success: '成功',
    failed: '失败',
    partial: '部分成功'
  }
  return labelMap[status] || status
}

const formatDateTime = (dateStr: string) => {
  if (!dateStr) return '-'
  return new Date(dateStr).toLocaleString('zh-CN')
}

onMounted(() => {
  loadConfigs()
})
</script>

<style scoped>
.integration-list {
  padding: 20px;
}
</style>
```

---

## Output Files

| File | Description |
|------|-------------|
| `frontend/src/types/integration.ts` | Integration type definitions |
| `frontend/src/api/integration.ts` | Integration API service |
| `frontend/src/views/integration/IntegrationList.vue` | Integration list page |
| `frontend/src/views/integration/SyncJobs.vue` | Sync jobs page |
| `frontend/src/components/integration/M18ConfigDialog.vue` | M18 config dialog |
