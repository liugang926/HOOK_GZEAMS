# Phase 5.1: 万达宝M18适配器 - 前端实现

## 概述

M18适配器的前端页面复用通用集成框架的组件，M18特定的配置通过动态组件实现。

---

---

## 公共组件引用

### 页面组件
本模块使用以下公共页面组件（详见 `common_base_features/frontend.md`）：

| 组件 | 用途 | 引用路径 |
|------|------|---------|
| `BaseListPage` | 标准列表页面 | `@/components/common/BaseListPage.vue` |
| `BaseFormPage` | 标准表单页面 | `@/components/common/BaseFormPage.vue` |
| `BaseDetailPage` | 标准详情页面 | `@/components/common/BaseDetailPage.vue` |

### 基础组件

| 组件 | 用途 | 引用路径 |
|------|------|---------|
| `BaseTable` | 统一表格 | `@/components/common/BaseTable.vue` |
| `BaseSearchBar` | 搜索栏 | `@/components/common/BaseSearchBar.vue` |
| `BasePagination` | 分页 | `@/components/common/BasePagination.vue` |
| `BaseAuditInfo` | 审计信息 | `@/components/common/BaseAuditInfo.vue` |
| `BaseFileUpload` | 文件上传 | `@/components/common/BaseFileUpload.vue` |

### 列表字段显示管理（推荐）

| 组件 | Hook | 参考文档 |
|------|------|---------|
| `ColumnManager` | 列显示/隐藏/排序/列宽配置 | `list_column_configuration.md` |
| `useColumnConfig` | 列配置Hook（获取/保存/重置） | `list_column_configuration.md` |

**功能包括**:
- ✓ 列的显示/隐藏
- ✓ 列的拖拽排序
- ✓ 列宽调整
- ✓ 列固定（左/右）
- ✓ 用户个性化配置保存

### 布局组件

| 组件 | 用途 | 参考文档 |
|------|------|---------|
| `DynamicTabs` | 动态标签页 | `tab_configuration.md` |
| `SectionBlock` | 区块容器 | `section_block_layout.md` |
| `FieldRenderer` | 动态字段渲染 | `field_configuration_layout.md` |

### Composables/Hooks

| Hook | 用途 | 引用路径 |
|------|------|---------|
| `useListPage` | 列表页面逻辑 | `@/composables/useListPage.js` |
| `useFormPage` | 表单页面逻辑 | `@/composables/useFormPage.js` |
| `usePermission` | 权限检查 | `@/composables/usePermission.js` |

### 组件继承关系

```vue
<!-- 列表页面 -->
<BaseListPage
    title="页面标题"
    :fetch-method="fetchData"
    :columns="columns"
    :search-fields="searchFields"
>
    <!-- 自定义列插槽 -->
</BaseListPage>

<!-- 表单页面 -->
<BaseFormPage
    title="表单标题"
    :submit-method="handleSubmit"
    :initial-data="formData"
    :rules="rules"
>
    <!-- 自定义表单项 -->
</BaseFormPage>
```

---

## 1. M18连接配置组件

### M18ConnectionForm.vue

已在通用框架的 `frontend.md` 中定义。完整实现如下：

```vue
<template>
  <div class="m18-connection-form">
    <el-alert
      title="万达宝M18连接配置"
      type="info"
      :closable="false"
      show-icon
      class="mb-16"
    >
      <p>请填写M18系统的API连接信息：</p>
      <ul>
        <li>API地址：如 http://m18.example.com/M18/api/</li>
        <li>API密钥：在M18系统后台生成</li>
        <li>用户名/密码：用于OAuth认证</li>
      </ul>
    </el-alert>

    <el-form-item label="API地址" required>
      <el-input
        :model-value="modelValue.api_url"
        @input="updateField('api_url', $event)"
        placeholder="http://m18.example.com/M18/api/"
      >
        <template #prepend>http://</template>
      </el-input>
    </el-form-item>

    <el-form-item label="API密钥" required>
      <el-input
        :model-value="modelValue.api_key"
        @input="updateField('api_key', $event)"
        type="password"
        show-password
        placeholder="请输入M18 API密钥"
      >
        <template #append>
          <el-button @click="generateKey">生成</el-button>
        </template>
      </el-input>
    </el-form-item>

    <el-form-item label="客户端ID">
      <el-input
        :model-value="modelValue.client_id"
        @input="updateField('client_id', $event)"
        placeholder="默认: GZEAMS"
      />
    </el-form-item>

    <el-divider>OAuth认证</el-divider>

    <el-form-item label="用户名" required>
      <el-input
        :model-value="modelValue.username"
        @input="updateField('username', $event)"
        placeholder="M18系统用户名"
      />
    </el-form-item>

    <el-form-item label="密码" required>
      <el-input
        :model-value="modelValue.password"
        @input="updateField('password', $event)"
        type="password"
        show-password
        placeholder="M18系统密码"
      />
    </el-form-item>

    <el-form-item label="超时时间">
      <el-input-number
        :model-value="modelValue.timeout || 30"
        @change="updateField('timeout', $event)"
        :min="5"
        :max="300"
      />
      <span style="margin-left: 8px">秒</span>
    </el-form-item>

    <el-form-item label="启用SSL">
      <el-switch
        :model-value="modelValue.verify_ssl !== false"
        @change="updateField('verify_ssl', $event)"
      />
      <span class="ml-8 text-gray">生产环境建议开启</span>
    </el-form-item>
  </div>
</template>

<script setup lang="ts">
const props = defineProps({
  modelValue: {
    type: Object,
    default: () => ({})
  }
})

const emit = defineEmits(['update:modelValue'])

const updateField = (field, value) => {
  emit('update:modelValue', {
    ...props.modelValue,
    [field]: value
  })
}

const generateKey = () => {
  // 生成随机API密钥
  const key = 'GZ' + Math.random().toString(36).substring(2, 15) +
              Math.random().toString(36).substring(2, 15)
  updateField('api_key', key.toUpperCase())
}
</script>

<style scoped>
.mb-16 {
  margin-bottom: 16px;
}

.ml-8 {
  margin-left: 8px;
}

.text-gray {
  color: #909399;
}
</style>
```

---

## 2. M18同步状态页面

### M18SyncStatus.vue

```vue
<template>
  <div class="m18-sync-status">
    <el-card header="M18同步状态">
      <!-- 状态概览 -->
      <el-row :gutter="16" class="status-overview">
        <el-col :span="6">
          <div class="status-card">
            <el-icon class="status-icon" color="#409eff"><Connection /></el-icon>
            <div class="status-info">
              <div class="status-label">连接状态</div>
              <div class="status-value" :class="healthClass">
                {{ healthText }}
              </div>
            </div>
          </div>
        </el-col>
        <el-col :span="6">
          <div class="status-card">
            <el-icon class="status-icon" color="#67c23a"><Refresh /></el-icon>
            <div class="status-info">
              <div class="status-label">最后同步</div>
              <div class="status-value">
                {{ formatTime(config.last_sync_at) }}
              </div>
            </div>
          </div>
        </el-col>
        <el-col :span="6">
          <div class="status-card">
            <el-icon class="status-icon" color="#e6a23c"><Document /></el-icon>
            <div class="status-info">
              <div class="status-label">同步订单</div>
              <div class="status-value">{{ stats.po_count }}</div>
            </div>
          </div>
        </el-col>
        <el-col :span="6">
          <div class="status-card">
            <el-icon class="status-icon" color="#909399"><User /></el-icon>
            <div class="status-info">
              <div class="status-label">同步供应商</div>
              <div class="status-value">{{ stats.supplier_count }}</div>
            </div>
          </div>
        </el-col>
      </el-row>

      <!-- 操作按钮 -->
      <div class="action-buttons">
        <el-button type="primary" @click="handleTestConnection" :loading="testing">
          测试连接
        </el-button>
        <el-button @click="handleSyncPO" :loading="syncing">
          同步采购订单
        </el-button>
        <el-button @click="handleSyncSuppliers" :loading="syncingSuppliers">
          同步供应商
        </el-button>
        <el-button @click="handleViewLogs">查看日志</el-button>
      </div>

      <!-- 同步历史 -->
      <el-divider content-position="left">同步历史</el-divider>

      <el-table :data="syncHistory" size="small">
        <el-table-column prop="created_at" label="时间" width="160" />
        <el-table-column prop="business_type" label="类型" width="120">
          <template #default="{ row }">
            {{ getBusinessTypeName(row.business_type) }}
          </template>
        </el-table-column>
        <el-table-column prop="total_count" label="总数" width="80" align="right" />
        <el-table-column prop="success_count" label="成功" width="80" align="right" />
        <el-table-column prop="failed_count" label="失败" width="80" align="right" />
        <el-table-column prop="duration_ms" label="耗时" width="100">
          <template #default="{ row }">
            {{ row.duration_ms ? `${(row.duration_ms / 1000).toFixed(1)}s` : '-' }}
          </template>
        </el-table-column>
        <el-table-column prop="status" label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="getStatusType(row.status)" size="small">
              {{ getStatusName(row.status) }}
            </el-tag>
          </template>
        </el-table-column>
      </el-table>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { Connection, Refresh, Document, User } from '@element-plus/icons-vue'
import { m18Api } from '@/api/integration/m18'

const config = ref({})
const testing = ref(false)
const syncing = ref(false)
const syncingSuppliers = ref(false)

const stats = reactive({
  po_count: 0,
  supplier_count: 0
})

const syncHistory = ref([])

const healthText = computed(() => {
  const status = config.value.health_status
  const map = {
    healthy: '健康',
    degraded: '降级',
    unhealthy: '不可用'
  }
  return map[status] || '未知'
})

const healthClass = computed(() => {
  const status = config.value.health_status
  return {
    'status-healthy': status === 'healthy',
    'status-degraded': status === 'degraded',
    'status-unhealthy': status === 'unhealthy'
  }
})

const fetchData = async () => {
  const { data } = await m18Api.getStatus()
  Object.assign(config, data.config)
  Object.assign(stats, data.stats)
  syncHistory.value = data.history
}

const handleTestConnection = async () => {
  testing.value = true
  try {
    const { data } = await m18Api.testConnection()
    if (data.success) {
      ElMessage.success('连接成功')
      fetchData()
    } else {
      ElMessage.error(data.message)
    }
  } finally {
    testing.value = false
  }
}

const handleSyncPO = async () => {
  syncing.value = true
  try {
    const { data } = await m18Api.syncPurchaseOrders({ async: true })
    ElMessage.success('同步任务已提交')
    fetchData()
  } finally {
    syncing.value = false
  }
}

const handleSyncSuppliers = async () => {
  syncingSuppliers.value = true
  try {
    const { data } = await m18Api.syncSuppliers({ async: true })
    ElMessage.success('同步任务已提交')
    fetchData()
  } finally {
    syncingSuppliers.value = false
  }
}

const handleViewLogs = () => {
  // 跳转到日志页面
}

const getBusinessTypeName = (type) => {
  const map = {
    purchase_order: '采购订单',
    supplier: '供应商',
    goods_receipt: '收货单'
  }
  return map[type] || type
}

const getStatusType = (status) => {
  const map = {
    pending: 'info',
    running: 'warning',
    success: 'success',
    partial_success: 'warning',
    failed: 'danger'
  }
  return map[status] || ''
}

const getStatusName = (status) => {
  const map = {
    pending: '待执行',
    running: '执行中',
    success: '成功',
    partial_success: '部分成功',
    failed: '失败'
  }
  return map[status] || status
}

const formatTime = (time) => {
  return time ? new Date(time).toLocaleString('zh-CN') : '从未同步'
}

onMounted(() => {
  fetchData()
})
</script>

<style scoped>
.status-overview {
  margin-bottom: 24px;
}

.status-card {
  display: flex;
  align-items: center;
  padding: 16px;
  background: #f5f7fa;
  border-radius: 4px;
}

.status-icon {
  font-size: 32px;
  margin-right: 16px;
}

.status-info {
  flex: 1;
}

.status-label {
  font-size: 14px;
  color: #909399;
}

.status-value {
  font-size: 18px;
  font-weight: bold;
  margin-top: 4px;
}

.status-healthy {
  color: #67c23a;
}

.status-degraded {
  color: #e6a23c;
}

.status-unhealthy {
  color: #f56c6c;
}

.action-buttons {
  display: flex;
  gap: 12px;
  margin-bottom: 24px;
}
</style>
```

---

## 3. M18 API封装

```typescript
// src/api/integration/m18.ts

import request from '@/utils/request'

export const m18Api = {
  // 获取M18状态
  getStatus() {
    return request.get('/api/integration/m18/status/')
  },

  // 测试连接
  testConnection() {
    return request.post('/api/integration/m18/test-connection/')
  },

  // 同步采购订单
  syncPurchaseOrders(data: {
    start_date?: string
    end_date?: string
    async?: boolean
  }) {
    return request.post('/api/integration/m18/sync/purchase-orders/', data)
  },

  // 同步供应商
  syncSuppliers(data: {
    updated_since?: string
    async?: boolean
  }) {
    return request.post('/api/integration/m18/sync/suppliers/', data)
  },

  // 获取采购订单列表
  getPurchaseOrders(params: {
    po_code?: string
    page?: number
    size?: number
  }) {
    return request.get('/api/integration/m18/purchase-orders/', { params })
  },

  // 获取供应商列表
  getSuppliers(params?: any) {
    return request.get('/api/integration/m18/suppliers/', { params })
  },

  // 创建收货单
  createGoodsReceipt(data: {
    po_id: string
    receipt_date: string
    warehouse_code: string
    line_items: Array<{
      line_id?: string
      material_code: string
      quantity: number
      uom: string
      location?: string
    }>
  }) {
    return request.post('/api/integration/m18/goods-receipts/', data)
  }
}
```

---

## 后续任务

1. Phase 5.2: 实现财务凭证集成（基于通用框架）
2. 扩展其他ERP适配器
