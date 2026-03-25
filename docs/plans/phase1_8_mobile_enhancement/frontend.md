# Phase 1.8: 移动端功能增强 - 前端实现

## 1. 技术架构

### 1.1 技术栈

| 技术 | 版本 | 用途 |
|------|------|------|
| Vue 3 | 3.4+ | 前端框架 |
| Vite | 5.0+ | 构建工具 |
| Vant 4 | 4.8+ | 移动端UI组件库 |
| Dexie.js | 3.2+ | IndexedDB封装 |
| Workbox | 7.0+ | PWA支持 |
| Comlink | 4.4+ | Web Worker封装 |

### 1.2 目录结构

```
src/mobile/
├── main.ts                      # 移动端入口
├── App.vue                      # 根组件
├── permission.ts                # 权限指令
├── router/                      # 路由配置
├── stores/                      # 状态管理
│   ├── sync.ts                  # 同步状态
│   ├── offline.ts               # 离线状态
│   └── approval.ts              # 审批状态
├── services/                    # 服务层
│   ├── sync.service.ts          # 同步服务
│   ├── offline.service.ts       # 离线服务
│   ├── device.service.ts        # 设备服务
│   └── approval.service.ts      # 审批服务
├── database/                    # 本地数据库
│   ├── index.ts                 # Dexie初始化
│   ├── schema.ts                # 数据库结构
│   └── migrations/              # 数据迁移
├── workers/                     # Web Worker
│   ├── sync.worker.ts           # 同步Worker
│   └── conflict.worker.ts       # 冲突处理Worker
├── views/                       # 页面组件
│   ├── home/                    # 首页
│   ├── asset/                   # 资产管理
│   ├── inventory/               # 盘点管理
│   ├── approval/                # 审批管理
│   ├── profile/                 # 个人中心
│   └── settings/                # 设置
├── components/                  # 公共组件
│   ├── AssetCard.vue            # 资产卡片
│   ├── ScanButton.vue           # 扫码按钮
│   ├── SyncIndicator.vue        # 同步指示器
│   ├── OfflineBanner.vue        # 离线提示
│   └── ConflictDialog.vue       # 冲突处理对话框
└── utils/                       # 工具函数
    ├── crypto.ts                # 加密工具
    ├── network.ts               # 网络检测
    └── logger.ts                # 日志工具
```

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

## 2. 本地数据库设计

### 2.1 Dexie 数据库定义

**文件**: `src/mobile/database/schema.ts`

```typescript
import Dexie, { Table } from 'dexie'

export interface Asset {
  id?: string
  asset_no: string
  asset_name: string
  category: string
  location: string
  status: string
  version: number
  updated_at: string
  _synced?: boolean
}

export interface InventoryScan {
  id?: string
  task_id: string
  asset_no: string
  scan_time: string
  location: string
  status: string
  _synced?: boolean
  _deleted?: boolean
}

export interface SyncQueue {
  id?: number
  table_name: string
  record_id: string
  operation: 'create' | 'update' | 'delete'
  data: any
  old_data?: any
  version: number
  created_at: string
  retry_count: number
}

export interface SyncMetadata {
  id?: number
  key: string
  value: any
}

class GZEAMSDatabase extends Dexie {
  assets!: Table<Asset, string>
  inventory_scans!: Table<InventoryScan, string>
  sync_queue!: Table<SyncQueue, number>
  sync_metadata!: Table<SyncMetadata, number>

  constructor() {
    super('GZEAMS-Mobile')

    this.version(1).stores({
      assets: 'id, asset_no, category, location, _synced',
      inventory_scans: 'id, task_id, asset_no, _synced, _deleted',
      sync_queue: '++id, table_name, record_id',
      sync_metadata: '++id, key'
    })
  }
}

export const db = new GZEAMSDatabase()
```

### 2.2 离线数据服务

**文件**: `src/mobile/services/offline.service.ts`

```typescript
import { db, Asset, InventoryScan, SyncQueue } from '@/mobile/database/schema'
import { v4 as uuidv4 } from 'uuid'

export class OfflineService {
  /**
   * 保存资产到本地数据库
   */
  static async saveAsset(asset: Asset): Promise<string> {
    const id = asset.id || uuidv4()
    asset.id = id
    asset._synced = false

    await db.assets.put(asset)
    await this.addToSyncQueue('assets.Asset', id, 'create', asset)

    return id
  }

  /**
   * 更新本地资产
   */
  static async updateAsset(id: string, data: Partial<Asset>): Promise<void> {
    const oldAsset = await db.assets.get(id)

    await db.assets.update(id, {
      ...data,
      _synced: false
    })

    await this.addToSyncQueue('assets.Asset', id, 'update', data, oldAsset)
  }

  /**
   * 获取本地资产列表
   */
  static async getAssets(filter?: {
    category?: string
    location?: string
    synced?: boolean
  }): Promise<Asset[]> {
    let query = db.assets.toCollection()

    if (filter?.synced !== undefined) {
      // 过滤同步状态
    }

    return await query.toArray()
  }

  /**
   * 保存盘点扫描记录
   */
  static async saveScan(scan: Omit<InventoryScan, 'id'>): Promise<string> {
    const id = uuidv4()
    await db.inventory_scans.put({
      ...scan,
      id,
      _synced: false
    })

    await this.addToSyncQueue('inventory.InventoryScan', id, 'create', scan)

    return id
  }

  /**
   * 获取待同步记录数
   */
  static async getPendingCount(): Promise<number> {
    const pendingAssets = await db.assets.filter(a => !a._synced).count()
    const pendingScans = await db.inventory_scans.filter(s => !s._synced).count()
    const queueCount = await db.sync_queue.count()

    return pendingAssets + pendingScans + queueCount
  }

  /**
   * 添加到同步队列
   */
  private static async addToSyncQueue(
    table_name: string,
    record_id: string,
    operation: 'create' | 'update' | 'delete',
    data: any,
    old_data?: any
  ): Promise<void> {
    // 检查是否已存在相同记录的队列项
    const existing = await db.sync_queue
      .where('[table_name+record_id]')
      .equals([table_name, record_id])
      .first()

    if (existing) {
      // 更新现有队列项
      await db.sync_queue.update(existing.id!, {
        operation,
        data,
        old_data,
        retry_count: 0
      })
    } else {
      // 添加新队列项
      await db.sync_queue.add({
        table_name,
        record_id,
        operation,
        data,
        old_data,
        version: Date.now(),
        created_at: new Date().toISOString(),
        retry_count: 0
      })
    }
  }

  /**
   * 获取同步队列
   */
  static async getSyncQueue(limit: number = 50): Promise<SyncQueue[]> {
    return await db.sync_queue
      .orderBy('created_at')
      .limit(limit)
      .toArray()
  }

  /**
   * 从同步队列移除
   */
  static async removeFromQueue(queueId: number): Promise<void> {
    await db.sync_queue.delete(queueId)
  }

  /**
   * 清空所有本地数据
   */
  static async clearAll(): Promise<void> {
    await db.assets.clear()
    await db.inventory_scans.clear()
    await db.sync_queue.clear()
    await db.sync_metadata.clear()
  }
}
```

---

## 3. 数据同步服务

### 3.1 同步服务核心

**文件**: `src/mobile/services/sync.service.ts`

```typescript
import { OfflineService } from './offline.service'
import { api } from '@/api'
import { useNetworkStore } from '@/mobile/stores/network'
import { useSyncStore } from '@/mobile/stores/sync'

export interface SyncResult {
  success: number
  failed: number
  conflicts: number
  errors: Array<{ record_id: string; error: string }>
}

export class SyncService {
  private static isSyncing = false
  private static syncWorker: Worker | null = null

  /**
   * 初始化同步服务
   */
  static async init(): Promise<void> {
    // 注册 Service Worker
    if ('serviceWorker' in navigator) {
      const registration = await navigator.serviceWorker.register(
        import.meta.env.BASE_URL + 'sw.js'
      )

      // 监听同步事件
      registration.addEventListener('sync', (event: any) => {
        if (event.tag === 'background-sync') {
          event.waitUntil(this.sync())
        }
      })
    }

    // 初始化同步Worker
    if (window.Worker) {
      this.syncWorker = new Worker(
        new URL('@/mobile/workers/sync.worker.ts', import.meta.url),
        { type: 'module' }
      )

      this.syncWorker.onmessage = (e) => {
        const { type, data } = e.data
        switch (type) {
          case 'sync-progress':
            this.handleSyncProgress(data)
            break
          case 'sync-complete':
            this.handleSyncComplete(data)
            break
          case 'sync-error':
            this.handleSyncError(data)
            break
        }
      }
    }

    // 监听网络状态
    window.addEventListener('online', () => {
      this.sync()
    })
  }

  /**
   * 执行同步
   */
  static async sync(): Promise<SyncResult> {
    if (this.isSyncing) {
      throw new Error('同步正在进行中')
    }

    const networkStore = useNetworkStore()
    if (!networkStore.isOnline) {
      throw new Error('网络未连接')
    }

    this.isSyncing = true
    const syncStore = useSyncStore()
    syncStore.setSyncing(true)

    try {
      // 1. 上传离线数据
      const uploadResult = await this.uploadOfflineData()

      // 2. 下载服务端变更
      const downloadResult = await this.downloadChanges()

      // 3. 更新同步状态
      await this.updateSyncMetadata()

      return {
        success: uploadResult.success + downloadResult.count,
        failed: uploadResult.failed,
        conflicts: uploadResult.conflicts,
        errors: uploadResult.errors
      }
    } finally {
      this.isSyncing = false
      syncStore.setSyncing(false)
    }
  }

  /**
   * 上传离线数据
   */
  private static async uploadOfflineData(): Promise<SyncResult> {
    const result: SyncResult = {
      success: 0,
      failed: 0,
      conflicts: 0,
      errors: []
    }

    const queue = await OfflineService.getSyncQueue(100)
    const syncData = queue.map(item => ({
      table_name: item.table_name,
      record_id: item.record_id,
      operation: item.operation,
      data: item.data,
      old_data: item.old_data,
      version: item.version,
      created_at: item.created_at,
      updated_at: item.created_at
    }))

    if (syncData.length === 0) {
      return result
    }

    try {
      const deviceId = await this.getDeviceId()
      const response = await api.post('/mobile/sync/upload/', {
        device_id: deviceId,
        data: syncData
      })

      result.success = response.data.success
      result.failed = response.data.failed
      result.conflicts = response.data.conflicts
      result.errors = response.data.errors || []

      // 移除已同步的记录
      for (const item of queue) {
        await OfflineService.removeFromQueue(item.id!)
      }

    } catch (error: any) {
      result.failed = syncData.length
      result.errors = syncData.map(item => ({
        record_id: item.record_id,
        error: error.message
      }))
    }

    return result
  }

  /**
   * 下载服务端变更
   */
  private static async downloadChanges(): Promise<{ count: number; version: number }> {
    const syncStore = useSyncStore()
    const lastVersion = syncStore.lastServerVersion || 0

    const tables = ['assets.Asset', 'inventory.InventoryTask', 'organizations.Department']

    try {
      const response = await api.post('/mobile/sync/download/', {
        last_sync_version: lastVersion,
        tables
      })

      const { version, changes } = response.data
      let count = 0

      // 更新本地数据
      for (const [tableName, records] of Object.entries(changes)) {
        if (Array.isArray(records) && records.length > 0) {
          await this.applyDownloadChanges(tableName, records as any[])
          count += records.length
        }
      }

      // 更新版本号
      syncStore.setLastServerVersion(version)

      return { count, version }
    } catch (error) {
      return { count: 0, version: lastVersion }
    }
  }

  /**
   * 应用下载的变更
   */
  private static async applyDownloadChanges(tableName: string, records: any[]): Promise<void> {
    const localTableName = tableName.split('.')[1].toLowerCase()

    for (const record of records) {
      if (localTableName === 'asset') {
        await db.assets.put({
          ...record,
          _synced: true
        })
      }
      // 其他表类似处理
    }
  }

  /**
   * 更新同步元数据
   */
  private static async updateSyncMetadata(): Promise<void> {
    const now = new Date().toISOString()
    await db.sync_metadata.put({
      key: 'last_sync_at',
      value: now
    })
  }

  /**
   * 获取设备ID
   */
  private static async getDeviceId(): Promise<string> {
    let deviceId = await db.sync_metadata.get('device_id')
    if (!deviceId) {
      deviceId = this.generateDeviceId()
      await db.sync_metadata.put({
        key: 'device_id',
        value: deviceId
      })
    }
    return deviceId.value
  }

  /**
   * 生成设备ID
   */
  private static generateDeviceId(): string {
    return 'mobile-' + Date.now() + '-' + Math.random().toString(36).substr(2, 9)
  }

  /**
   * 处理同步进度
   */
  private static handleSyncProgress(data: any): void {
    const syncStore = useSyncStore()
    syncStore.setProgress(data.progress)
  }

  /**
   * 处理同步完成
   */
  private static handleSyncComplete(data: any): void {
    const syncStore = useSyncStore()
    syncStore.setSyncing(false)
    syncStore.setLastSyncAt(new Date())

    // 显示通知
    if (data.conflicts > 0) {
      this.showConflictNotification(data.conflicts)
    } else {
      this.showSuccessNotification(data.success)
    }
  }

  /**
   * 处理同步错误
   */
  private static handleSyncError(data: any): void {
    this.isSyncing = false
    const syncStore = useSyncStore()
    syncStore.setSyncing(false)
  }

  /**
   * 显示冲突通知
   */
  private static showConflictNotification(count: number): void {
    // 使用 Vant 的 Toast 或 Notify
  }

  /**
   * 显示成功通知
   */
  private static showSuccessNotification(count: number): void {
    // 使用 Vant 的 Toast 或 Notify
  }
}
```

### 3.2 同步状态管理

**文件**: `src/mobile/stores/sync.ts`

```typescript
import { defineStore } from 'pinia'
import { ref } from 'vue'

export const useSyncStore = defineStore('mobile-sync', () => {
  const isSyncing = ref(false)
  const lastSyncAt = ref<Date | null>(null)
  const lastServerVersion = ref(0)
  const pendingCount = ref(0)
  const progress = ref(0)
  const syncStatus = ref<'idle' | 'syncing' | 'success' | 'error'>('idle')

  const setSyncing = (value: boolean) => {
    isSyncing.value = value
    syncStatus.value = value ? 'syncing' : 'idle'
  }

  const setLastSyncAt = (date: Date) => {
    lastSyncAt.value = date
  }

  const setLastServerVersion = (version: number) => {
    lastServerVersion.value = version
  }

  const setPendingCount = (count: number) => {
    pendingCount.value = count
  }

  const setProgress = (value: number) => {
    progress.value = value
  }

  const setError = () => {
    syncStatus.value = 'error'
  }

  return {
    isSyncing,
    lastSyncAt,
    lastServerVersion,
    pendingCount,
    progress,
    syncStatus,
    setSyncing,
    setLastSyncAt,
    setLastServerVersion,
    setPendingCount,
    setProgress,
    setError
  }
})
```

---

## 4. 移动审批功能

### 4.1 审批列表页面

**文件**: `src/mobile/views/approval/Index.vue`

```vue
<template>
  <div class="approval-page">
    <van-nav-bar title="审批" left-arrow @click-left="$router.back()" />

    <!-- Tab切换 -->
    <van-tabs v-model:active="activeTab" sticky>
      <van-tab title="待审批" name="pending">
        <PullRefresh @refresh="onRefresh">
          <List
            v-model:loading="loading"
            :finished="finished"
            @load="onLoad"
          >
            <van-cell
              v-for="item in pendingList"
              :key="item.id"
              :title="item.title"
              :label="item.workflow_name"
              is-link
              @click="goDetail(item.id)"
            >
              <template #right-icon>
                <van-tag v-if="item.urgent" type="danger">紧急</van-tag>
              </template>
            </van-cell>
          </List>
        </PullRefresh>
      </van-tab>

      <van-tab title="已审批" name="approved">
        <List
          v-model:loading="loading"
          :finished="finished"
          @load="onLoad"
        >
          <van-cell
            v-for="item in approvedList"
            :key="item.id"
            :title="item.title"
            :label="item.approved_at"
          >
            <template #right-icon>
              <van-tag :type="item.action === 'approve' ? 'success' : 'danger'">
                {{ item.action === 'approve' ? '同意' : '拒绝' }}
              </van-tag>
            </template>
          </van-cell>
        </List>
      </van-tab>

      <van-tab title="我发起的" name="initiated">
        <!-- 发起的流程列表 -->
      </van-tab>
    </van-tabs>

    <!-- 批量操作按钮 -->
    <div v-if="activeTab === 'pending' && selectedIds.length > 0" class="batch-actions">
      <van-button type="primary" @click="batchApprove">
        批量同意({{ selectedIds.length }})
      </van-button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { NavBar, Tab, Tabs, Cell, Tag, Button, List, PullRefresh, showDialog } from 'vant'
import { approvalApi } from '@/api/mobile'

const router = useRouter()
const activeTab = ref('pending')
const loading = ref(false)
const finished = ref(false)
const pendingList = ref([])
const approvedList = ref([])
const selectedIds = ref<string[]>([])

const onLoad = async () => {
  loading.value = true
  try {
    if (activeTab.value === 'pending') {
      const { data } = await approvalApi.getPending({ limit: 20 })
      pendingList.value = data.results
      finished.value = data.results.length === 0
    } else if (activeTab.value === 'approved') {
      // 加载已审批列表
    }
  } finally {
    loading.value = false
  }
}

const onRefresh = async () => {
  finished.value = false
  await onLoad()
}

const goDetail = (id: string) => {
  router.push(`/mobile/approval/${id}`)
}

const batchApprove = async () => {
  const confirmed = await showDialog({
    title: '批量审批',
    message: `确认同意选中的 ${selectedIds.value.length} 项审批？`
  })

  if (confirmed) {
    const { data } = await approvalApi.batchApprove({
      instance_ids: selectedIds.value,
      action: 'approve',
      comment: '批量同意'
    })

    if (data.success > 0) {
      selectedIds.value = []
      onRefresh()
    }
  }
}

onMounted(() => {
  onLoad()
})
</script>
```

### 4.2 审批详情页面

**文件**: `src/mobile/views/approval/Detail.vue`

```vue
<template>
  <div class="approval-detail-page">
    <van-nav-bar
      title="审批详情"
      left-arrow
      @click-left="$router.back()"
    >
      <template #right>
        <van-icon name="ellipsis" @click="showMore" />
      </template>
    </van-nav-bar>

    <Loading v-if="loading" />

    <div v-else class="detail-content">
      <!-- 流程信息 -->
      <van-cell-group title="流程信息" inset>
        <van-cell title="标题" :value="detail.title" />
        <van-cell title="流程" :value="detail.workflow_name" />
        <van-cell title="当前节点" :value="detail.current_node" />
        <van-cell title="发起人" :value="detail.created_by" />
        <van-cell title="发起时间" :value="formatDateTime(detail.created_at)" />
      </van-cell-group>

      <!-- 流程图 -->
      <div class="flow-chart">
        <h3>流程进度</h3>
        <van-steps direction="vertical" :active="currentStep">
          <van-step v-for="node in flowNodes" :key="node.id">
            <h4>{{ node.name }}</h4>
            <p v-if="node.approver">审批人: {{ node.approver }}</p>
            <p v-if="node.approved_at">{{ formatDateTime(node.approved_at) }}</p>
          </van-step>
        </van-steps>
      </div>

      <!-- 表单数据 -->
      <van-cell-group title="申请内容" inset>
        <van-cell
          v-for="(value, key) in formData"
          :key="key"
          :title="getFieldLabel(key)"
          :value="value"
        />
      </van-cell-group>

      <!-- 审批历史 -->
      <van-cell-group title="审批历史" inset>
        <van-cell
          v-for="record in approvalHistory"
          :key="record.id"
          :title="record.node_name"
          :label="formatDateTime(record.approved_at)"
        >
          <template #right-icon>
            <van-tag :type="getActionType(record.action)">
              {{ getActionLabel(record.action) }}
            </van-tag>
          </template>
        </van-cell>
      </van-cell-group>
    </div>

    <!-- 底部操作栏 -->
    <div class="action-bar">
      <van-button plain type="danger" @click="handleReject">
        拒绝
      </van-button>
      <van-button type="primary" @click="handleApprove">
        同意
      </van-button>
    </div>

    <!-- 审批意见弹窗 -->
    <van-dialog
      v-model:show="showCommentDialog"
      title="审批意见"
      show-cancel-button
      @confirm="submitApproval"
    >
      <van-field
        v-model="comment"
        type="textarea"
        placeholder="请输入审批意见"
        rows="3"
      />
    </van-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { NavBar, Icon, CellGroup, Cell, Steps, Step, Button, Dialog, Field, Tag, Loading, showToast } from 'vant'
import { approvalApi } from '@/api/mobile'

const route = useRoute()
const router = useRouter()
const instanceId = route.params.id as string

const loading = ref(true)
const detail = ref<any>({})
const flowNodes = ref([])
const formData = ref({})
const approvalHistory = ref([])

const showCommentDialog = ref(false)
const comment = ref('')
const currentAction = ref<'approve' | 'reject'>('approve')

const currentStep = computed(() => {
  return flowNodes.value.findIndex((node: any) => node.is_current)
})

const loadData = async () => {
  loading.value = true
  try {
    const { data } = await approvalApi.getDetail(instanceId)
    detail.value = data
    flowNodes.value = data.flow_chart?.nodes || []
    formData.value = data.form_data || {}
    approvalHistory.value = data.approval_history || []
  } finally {
    loading.value = false
  }
}

const handleApprove = () => {
  currentAction.value = 'approve'
  showCommentDialog.value = true
}

const handleReject = () => {
  currentAction.value = 'reject'
  showCommentDialog.value = true
}

const submitApproval = async () => {
  try {
    const { data } = await approvalApi.approve({
      instance_id: instanceId,
      action: currentAction.value,
      comment: comment.value
    })

    if (data.success) {
      showToast('审批成功')
      router.back()
    }
  } catch (error) {
    showToast('审批失败')
  }
}

const getFieldLabel = (key: string) => {
  const labels: Record<string, string> = {
    asset_name: '资产名称',
    quantity: '数量',
    budget: '预算'
  }
  return labels[key] || key
}

const getActionType = (action: string) => {
  const types: Record<string, string> = {
    approve: 'success',
    reject: 'danger',
    return: 'warning'
  }
  return types[action] || 'default'
}

const getActionLabel = (action: string) => {
  const labels: Record<string, string> = {
    approve: '同意',
    reject: '拒绝',
    return: '驳回',
    submit: '提交'
  }
  return labels[action] || action
}

const formatDateTime = (dateStr: string) => {
  return new Date(dateStr).toLocaleString('zh-CN')
}

onMounted(() => {
  loadData()
})
</script>

<style scoped>
.approval-detail-page {
  min-height: 100vh;
  background: #f5f5f5;
  padding-bottom: 60px;
}

.flow-chart {
  background: white;
  margin: 12px 0;
  padding: 16px;
}

.action-bar {
  position: fixed;
  bottom: 0;
  left: 0;
  right: 0;
  display: flex;
  gap: 12px;
  padding: 12px 16px;
  background: white;
  box-shadow: 0 -2px 10px rgba(0, 0, 0, 0.05);
}

.action-bar .van-button {
  flex: 1;
}
</style>
```

---

## 5. 公共组件

### 5.1 同步指示器

**文件**: `src/mobile/components/SyncIndicator.vue`

```vue
<template>
  <div class="sync-indicator" @click="handleSync">
    <van-icon
      :name="iconName"
      :class="{ rotating: isSyncing }"
      :color="iconColor"
    />
    <span class="sync-text">{{ syncText }}</span>
    <van-badge
      v-if="pendingCount > 0"
      :content="pendingCount > 99 ? '99+' : pendingCount"
    />
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { Icon, Badge } from 'vant'
import { useSyncStore } from '@/mobile/stores/sync'
import { useNetworkStore } from '@/mobile/stores/network'
import { SyncService } from '@/mobile/services/sync.service'
import { showToast } from 'vant'

const syncStore = useSyncStore()
const networkStore = useNetworkStore()

const isSyncing = computed(() => syncStore.isSyncing)
const pendingCount = computed(() => syncStore.pendingCount)
const lastSyncAt = computed(() => syncStore.lastSyncAt)
const isOnline = computed(() => networkStore.isOnline)

const iconName = computed(() => {
  if (!isOnline.value) return 'warning-o'
  if (isSyncing.value) return 'replay'
  return 'completed'
})

const iconColor = computed(() => {
  if (!isOnline.value) return '#ff976a'
  if (pendingCount.value > 0) return '#1989fa'
  return '#07c160'
})

const syncText = computed(() => {
  if (!isOnline.value) return '离线'
  if (isSyncing.value) return '同步中'
  if (lastSyncAt.value) {
    const time = new Date(lastSyncAt.value)
    return `已同步 ${formatTime(time)}`
  }
  return '未同步'
})

const formatTime = (date: Date) => {
  const now = new Date()
  const diff = now.getTime() - date.getTime()

  if (diff < 60000) return '刚刚'
  if (diff < 3600000) return `${Math.floor(diff / 60000)}分钟前`
  if (diff < 86400000) return `${Math.floor(diff / 3600000)}小时前`
  return `${Math.floor(diff / 86400000)}天前`
}

const handleSync = async () => {
  if (!isOnline.value) {
    showToast('网络未连接')
    return
  }

  if (isSyncing.value) {
    showToast('正在同步中')
    return
  }

  try {
    await SyncService.sync()
    showToast('同步成功')
  } catch (error: any) {
    showToast(error.message || '同步失败')
  }
}
</script>

<style scoped>
.sync-indicator {
  display: flex;
  align-items: center;
  gap: 4px;
  padding: 4px 8px;
  font-size: 12px;
  cursor: pointer;
}

.sync-text {
  max-width: 100px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.rotating {
  animation: rotate 1s linear infinite;
}

@keyframes rotate {
  from {
    transform: rotate(0deg);
  }
  to {
    transform: rotate(360deg);
  }
}
</style>
```

### 5.2 离线提示横幅

**文件**: `src/mobile/components/OfflineBanner.vue`

```vue
<template>
  <van-badge
    v-if="!isOnline"
    is-dot
    color="#ff976a"
  >
    <div class="offline-banner">
      <van-icon name="warning-o" />
      <span>当前离线状态，数据将在联网后同步</span>
    </div>
  </van-badge>
</template>

<script setup lang="ts">
import { Icon, Badge } from 'vant'
import { useNetworkStore } from '@/mobile/stores/network'

const networkStore = useNetworkStore()
const isOnline = computed(() => networkStore.isOnline)
</script>

<style scoped>
.offline-banner {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 16px;
  background: #fff3cd;
  color: #856404;
  font-size: 14px;
}
</style>
```

### 5.3 扫码按钮

**文件**: `src/mobile/components/ScanButton.vue`

```vue
<template>
  <van-button
    type="primary"
    icon="scan"
    round
    :class="{ 'scan-button-scan': isScanning }"
    @click="handleScan"
  >
    {{ buttonText }}
  </van-button>

  <van-dialog v-model:show="showResult" title="扫码结果" :show-cancel-button="false">
    <div class="scan-result">
      <van-image v-if="resultImage" :src="resultImage" />
      <van-field
        v-model="scanResult"
        label="资产编号"
        readonly
      />
      <van-field
        v-model="location"
        label="存放位置"
        placeholder="请输入"
      />
    </div>
    <template #confirm>
      <van-button @click="confirmScan">确认</van-button>
    </template>
  </van-dialog>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { Button, Dialog, Image, Field, showToast } from 'vant'
import { scan } from '@vant/barcode-scanner'

interface Props {
  taskId: string
}

const props = defineProps<Props>()
const emit = defineEmits(['scanned'])

const isScanning = ref(false)
const buttonText = ref('扫码盘点')
const showResult = ref(false)
const scanResult = ref('')
const resultImage = ref('')
const location = ref('')

const handleScan = async () => {
  try {
    isScanning.value = true
    const result = await scan()

    if (result) {
      scanResult.value = result.text || result
      resultImage.value = result.image || ''
      showResult.value = true
    }
  } catch (error) {
    showToast('扫码失败')
  } finally {
    isScanning.value = false
  }
}

const confirmScan = () => {
  emit('scanned', {
    asset_no: scanResult.value,
    location: location.value
  })
  showResult.value = false
  scanResult.value = ''
  location.value = ''
}
</script>

<style scoped>
.scan-button-scan {
  animation: pulse 1s infinite;
}

@keyframes pulse {
  0%, 100% {
    opacity: 1;
  }
  50% {
    opacity: 0.5;
  }
}
</style>
```

---

## 6. PWA配置

### 6.1 Service Worker

**文件**: `src/mobile/sw.ts`

```typescript
import { precacheAndRoute, cleanupOutdatedCaches } from 'workbox-precaching'
import { registerRoute, NavigationRoute, Route } from 'workbox-routing'
import { StaleWhileRevalidate, CacheFirst, NetworkFirst } from 'workbox-strategies'
import { ExpirationPlugin } from 'workbox-expiration'
import { CacheableResponsePlugin } from 'workbox-cacheable-response'

// 预缓存静态资源
precacheAndRoute(self.__WB_MANIFEST)
cleanupOutdatedCaches()

// API路由 - NetworkFirst策略
registerRoute(
  ({ url }) => url.pathname.startsWith('/api/'),
  new NetworkFirst({
    cacheName: 'api-cache',
    plugins: [
      new CacheableResponsePlugin({
        statuses: [0, 200]
      }),
      new ExpirationPlugin({
        maxEntries: 100,
        maxAgeSeconds: 5 * 60 // 5分钟
      })
    ]
  })
)

// 图片资源 - CacheFirst策略
registerRoute(
  ({ request }) => request.destination === 'image',
  new CacheFirst({
    cacheName: 'image-cache',
    plugins: [
      new CacheableResponsePlugin({
        statuses: [0, 200]
      }),
      new ExpirationPlugin({
        maxEntries: 50,
        maxAgeSeconds: 30 * 24 * 60 * 60 // 30天
      })
    ]
  })
)

// 后台同步
self.addEventListener('sync', (event: any) => {
  if (event.tag === 'background-sync') {
    event.waitUntil(
      (async () => {
        // 执行同步操作
        const clients = await self.clients.matchAll()
        clients.forEach(client => {
          client.postMessage({
            type: 'sync',
            data: { tag: event.tag }
          })
        })
      })()
    )
  }
})

// 推送通知
self.addEventListener('push', (event: any) => {
  const data = event.data.json()

  const options = {
    body: data.body || '',
    icon: '/icons/icon-192.png',
    badge: '/icons/badge-72.png',
    vibrate: [200, 100, 200],
    data: {
      url: data.url || '/'
    }
  }

  event.waitUntil(
    self.registration.showNotification(data.title || '新消息', options)
  )
})

self.addEventListener('notificationclick', (event) => {
  event.notification.close()
  event.waitUntil(
    clients.openWindow(event.notification.data.url)
  )
})
```

### 6.2 PWA配置文件

**文件**: `vite.config.pwa.ts`

```typescript
import { VitePWA } from 'vite-plugin-pwa'

export const pwaConfig = VitePWA({
  registerType: 'autoUpdate',
  includeAssets: ['icons/*.png', 'fonts/*.ttf'],
  manifest: {
    name: '钩子固定资产',
    short_name: 'HOOK资产',
    description: '固定资产管理系统移动端',
    theme_color: '#1989fa',
    background_color: '#ffffff',
    display: 'standalone',
    orientation: 'portrait',
    icons: [
      {
        src: 'icons/icon-72.png',
        sizes: '72x72',
        type: 'image/png'
      },
      {
        src: 'icons/icon-192.png',
        sizes: '192x192',
        type: 'image/png'
      },
      {
        src: 'icons/icon-512.png',
        sizes: '512x512',
        type: 'image/png'
      }
    ]
  },
  workbox: {
    globPatterns: ['**/*.{js,css,html,png,svg,woff2}'],
    runtimeCaching: [
      {
        urlPattern: /^https:\/\/api\.example\.com\/.*$/,
        handler: 'NetworkFirst',
        options: {
          cacheName: 'api-cache',
          expiration: {
            maxEntries: 100,
            maxAgeSeconds: 5 * 60
          }
        }
      }
    ]
  }
})
```
