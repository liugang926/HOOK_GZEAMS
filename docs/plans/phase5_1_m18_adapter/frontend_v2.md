# Phase 5.1: M18 Adapter - Frontend Implementation v2

## Document Information

| Project | Details |
|---------|---------|
| PRD Version | v2.0 (Updated for API Standardization) |
| Updated Date | 2026-01-22 |
| References | [frontend_api_standardization_design.md](../common_base_features/00_core/frontend_api_standardization_design.md) |

---

## Task Overview

Implement M18 ERP integration adapter for purchase order synchronization and asset data synchronization.

---

## API Service Layer

### Type Definitions

```typescript
// frontend/src/types/m18.ts

export interface M18ConnectionStatus {
  connected: boolean
  lastSyncAt?: string
  apiVersion?: string
  companyInfo?: {
    companyCode: string
    companyName: string
  }
}

export interface M18PurchaseOrder {
  orderNo: string
  supplierCode: string
  supplierName: string
  orderDate: string
  deliveryDate?: string
  totalAmount: number
  currency: string
  status: string
  lineItems: M18PurchaseOrderLineItem[]
}

export interface M18PurchaseOrderLineItem {
  lineNo: string
  itemCode: string
  itemName: string
  quantity: number
  unit: string
  unitPrice: number
  totalPrice: number
}

export interface M18SyncConfig {
  autoSync: boolean
  syncInterval: number
  syncOrders: boolean
  syncAssets: boolean
  syncVendors: boolean
  startDate?: string
}

export interface M18SyncResult {
  orderId: string
  success: boolean
  assetId?: string
  error?: string
}
```

### API Service

```typescript
// frontend/src/api/m18.ts

import request from '@/utils/request'
import type { M18ConnectionStatus, M18SyncConfig, M18SyncResult } from '@/types/m18'

export const m18Api = {
  // Connection
  getStatus(): Promise<M18ConnectionStatus> {
    return request.get('/integration/m18/status/')
  },

  testConnection(): Promise<{ success: boolean; message: string }> {
    return request.post('/integration/m18/test-connection/')
  },

  // Configuration
  getConfig(): Promise<M18SyncConfig> {
    return request.get('/integration/m18/config/')
  },

  updateConfig(config: Partial<M18SyncConfig>): Promise<M18SyncConfig> {
    return request.put('/integration/m18/config/', config)
  },

  // Sync Operations
  syncPurchaseOrders(params?: {
    startDate?: string
    endDate?: string
    orderNos?: string[]
  }): Promise<{ jobId: string }> {
    return request.post('/integration/m18/sync/purchase-orders/', params)
  },

  syncAssets(): Promise<{ jobId: string }> {
    return request.post('/integration/m18/sync/assets/')
  },

  syncVendors(): Promise<{ jobId: string }> {
    return request.post('/integration/m18/sync/vendors/')
  },

  // Sync Jobs
  getJobs(params?: any): Promise<{ results: SyncJob[]; count: number }> {
    return request.get('/integration/m18/jobs/', { params })
  },

  getJobDetail(jobId: string): Promise<SyncJob> {
    return request.get(`/integration/m18/jobs/${jobId}/`)
  },

  retryJob(jobId: string): Promise<void> {
    return request.post(`/integration/m18/jobs/${jobId}/retry/`)
  }
}
```

---

## Component: M18 Config Panel

```vue
<!-- frontend/src/views/integration/M18ConfigPanel.vue -->
<template>
  <div class="m18-config-panel">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>M18 ERP 连接配置</span>
          <el-button
            :loading="testing"
            @click="handleTestConnection"
          >
            测试连接
          </el-button>
        </div>
      </template>

      <!-- Connection Status -->
      <el-alert
        v-if="connectionStatus"
        :type="connectionStatus.connected ? 'success' : 'error'"
        :title="connectionStatus.connected ? '已连接' : '未连接'"
        :description="connectionStatus.companyInfo?.companyName"
        show-icon
        :closable="false"
        style="margin-bottom: 20px"
      />

      <!-- Config Form -->
      <el-form :model="config" label-width="140px">
        <el-form-item label="API地址">
          <el-input v-model="form.apiBaseUrl" placeholder="https://api.m18.example.com" />
        </el-form-item>

        <el-form-item label="API Key">
          <el-input v-model="form.apiKey" placeholder="请输入API Key" show-password />
        </el-form-item>

        <el-form-item label="API Secret">
          <el-input v-model="form.apiSecret" placeholder="请输入API Secret" show-password />
        </el-form-item>

        <el-form-item label="公司代码">
          <el-input v-model="form.companyCode" placeholder="请输入M18公司代码" />
        </el-form-item>

        <el-divider>同步配置</el-divider>

        <el-form-item label="启用自动同步">
          <el-switch v-model="form.autoSync" />
        </el-form-item>

        <el-form-item label="同步间隔(分钟)">
          <el-input-number
            v-model="form.syncInterval"
            :min="5"
            :max="1440"
            :step="5"
          />
        </el-form-item>

        <el-form-item label="同步采购订单">
          <el-switch v-model="form.syncOrders" />
        </el-form-item>

        <el-form-item label="同步资产">
          <el-switch v-model="form.syncAssets" />
        </el-form-item>

        <el-form-item label="同步供应商">
          <el-switch v-model="form.syncVendors" />
        </el-form-item>

        <el-form-item>
          <el-button type="primary" :loading="saving" @click="handleSave">
            保存配置
          </el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <!-- Sync Actions -->
    <el-card class="sync-actions">
      <template #header>
        <span>同步操作</span>
      </template>

      <el-space direction="vertical" style="width: 100%">
        <el-descriptions title="采购订单同步" :column="3" border>
          <el-descriptions-item label="上次同步">
            {{ lastSyncInfo.ordersAt || '未同步' }}
          </el-descriptions-item>
          <el-descriptions-item label="同步数量">
            {{ lastSyncInfo.ordersCount || 0 }} 条
          </el-descriptions-item>
          <el-descriptions-item label="操作">
            <el-button size="small" @click="handleSyncOrders">
              立即同步
            </el-button>
          </el-descriptions-item>
        </el-descriptions>

        <el-descriptions title="资产同步" :column="3" border>
          <el-descriptions-item label="上次同步">
            {{ lastSyncInfo.assetsAt || '未同步' }}
          </el-descriptions-item>
          <el-descriptions-item label="同步数量">
            {{ lastSyncInfo.assetsCount || 0 }} 条
          </el-descriptions-item>
          <el-descriptions-item label="操作">
            <el-button size="small" @click="handleSyncAssets">
              立即同步
            </el-button>
          </el-descriptions-item>
        </el-descriptions>
      </el-space>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { m18Api } from '@/api/m18'
import type { M18ConnectionStatus, M18SyncConfig } from '@/types/m18'

const connectionStatus = ref<M18ConnectionStatus | null>(null)
const config = ref<M18SyncConfig>({
  autoSync: false,
  syncInterval: 60,
  syncOrders: true,
  syncAssets: true,
  syncVendors: false
})

const form = reactive({
  apiBaseUrl: '',
  apiKey: '',
  apiSecret: '',
  companyCode: '',
  autoSync: false,
  syncInterval: 60,
  syncOrders: true,
  syncAssets: true,
  syncVendors: false
})

const lastSyncInfo = ref({
  ordersAt: '',
  ordersCount: 0,
  assetsAt: '',
  assetsCount: 0
})

const testing = ref(false)
const saving = ref(false)

const loadStatus = async () => {
  try {
    connectionStatus.value = await m18Api.getStatus()
  } catch (error) {
    connectionStatus.value = null
  }
}

const loadConfig = async () => {
  try {
    const loadedConfig = await m18Api.getConfig()
    config.value = { ...config.value, ...loadedConfig }
    Object.assign(form, loadedConfig)
  } catch (error) {
    // Error handled by interceptor
  }
}

const handleTestConnection = async () => {
  testing.value = true
  try {
    const result = await m18Api.testConnection()
    if (result.success) {
      ElMessage.success('连接测试成功')
    } else {
      ElMessage.error(result.message)
    }
    await loadStatus()
  } catch (error) {
    // Error handled by interceptor
  } finally {
    testing.value = false
  }
}

const handleSave = async () => {
  saving.value = true
  try {
    await m18Api.updateConfig(form)
    ElMessage.success('配置已保存')
  } catch (error) {
    // Error handled by interceptor
  } finally {
    saving.value = false
  }
}

const handleSyncOrders = async () => {
  try {
    const result = await m18Api.syncPurchaseOrders({
      startDate: form.startDate
    })
    ElMessage.success('同步任务已创建')
  } catch (error) {
    // Error handled by interceptor
  }
}

const handleSyncAssets = async () => {
  try {
    await m18Api.syncAssets()
    ElMessage.success('同步任务已创建')
  } catch (error) {
    // Error handled by interceptor
  }
}

onMounted(() => {
  loadStatus()
  loadConfig()
})
</script>

<style scoped>
.m18-config-panel {
  padding: 20px;
}

.m18-config-panel .el-card {
  margin-bottom: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
</style>
```

---

## Output Files

| File | Description |
|------|-------------|
| `frontend/src/types/m18.ts` | M18 type definitions |
| `frontend/src/api/m18.ts` | M18 API service |
| `frontend/src/views/integration/M18ConfigPanel.vue` | M18 config panel |
| `frontend/src/views/integration/SyncJobList.vue` | Sync job list page |
