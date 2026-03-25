# 10. 资产扫码通用场景 - 详细设计

## 概述

本文档描述资产扫码在各种业务场景下的统一处理方式，确保从不同入口扫码（盘点、领用、调拨、日常查询）都能获得一致的体验。

---

## 1. 扫码场景分类

| 场景 | 说明 | 预期操作 | 返回后操作 |
|------|------|---------|-----------|
| 盘点任务 | 盘点中扫码 | 记录盘点结果 | 继续盘点 |
| 领用申请 | 填写领用单时扫码 | 添加到领用单 | 继续填写 |
| 调拨申请 | 填写调拨单时扫码 | 添加到调拨单 | 继续填写 |
| 资产归还 | 借用资产归还扫码 | 确认归还 | 返回列表 |
| 资产调拨接收 | 调拨接收扫码 | 确认接收 | 返回列表 |
| 日常查询 | 无特定场景扫码 | 查看资产详情 | - |

---

## 2. 扫码入口统一

### 2.1 移动端扫码入口

```
┌─────────────────────────────────────────┐
│  HOOK 固定资产                            │
├─────────────────────────────────────────┤
│  ┌─────────────────────────────────────┐│
│  │  ┌─────────────────────────────────┐││
│  │  │         快捷操作                │││
│  │  │  ┌─────┐ ┌─────┐ ┌─────┐       │││
│  │  │  │扫码 │ │资产 │ │待办 │       │││
│  │  │  └─────┘ └─────┘ └─────┘       │││
│  │  └─────────────────────────────────┘││
│  └─────────────────────────────────────┘│
│                                         │
│  或在任意页面点击右上角扫码图标           │
└─────────────────────────────────────────┘
```

### 2.2 扫码来源传递

扫码时需要传递来源信息：

```javascript
// 从盘点任务扫码
startScan({ source: 'inventory', sourceId: 'task_123' })

// 从领用申请扫码
startScan({ source: 'pickup', sourceId: 'pickup_draft_456' })

// 日常查询扫码
startScan({ source: 'general' })
```

---

## 3. 统一扫码结果页

### 3.1 页面结构

```
┌─────────────────────────────────────────┐
│  ×  扫描结果                              │
│  ┌─────────────────────────────────────┐│
│  │ 来源: 盘点任务 - 3楼盘点            ││
│  └─────────────────────────────────────┘│
│                                         │
│  ┌─────────────────────────────────────┐│
│  │  [基础] [使用] [财务] [记录]        ││
│  └─────────────────────────────────────┘│
│                                         │
│  ┌─────────────────────────────────────┐│
│  │         ┌─────────────┐             ││
│  │         │   [照片]    │             ││
│  │         └─────────────┘             ││
│  │  资产编码  ZC001                     ││
│  │  资产名称  MacBook Pro 16寸           ││
│  │  资产分类  电子设备 > 电脑 > 笔记本   ││
│  └─────────────────────────────────────┘│
│                                         │
│  ┌─────────────────────────────────────┐│
│  │ 盘点操作:                           ││
│  │  [✓正常] [位置变更] [损坏] [缺失]    ││
│  └─────────────────────────────────────┘│
│                                         │
│  ┌─────────────────────────────────────┐│
│  │       [继续扫码]  [完成盘点]         ││
│  └─────────────────────────────────────┘│
└─────────────────────────────────────────┘
```

### 3.2 不同来源的操作按钮差异

| 来源 | 操作按钮 |
|------|---------|
| inventory（盘点） | ✓正常、位置变更、损坏、缺失、拍照记录 |
| pickup（领用） | 添加到领用单、查看详情 |
| transfer（调拨） | 添加到调拨单、查看详情 |
| return（归还） | 确认归还、查看详情 |
| receive（接收） | 确认接收、查看详情 |
| general（通用） | 查看详情、查看二维码、分享 |

---

## 4. 连续扫码模式

### 4.1 连续扫码界面

```
┌─────────────────────────────────────────┐
│  ← 盘点任务 - 3楼盘点                    │
├─────────────────────────────────────────┤
│  ┌─────────────────────────────────────┐│
│  │ 进度: 15/120 已完成 12.5%           ││
│  │ ████████░░░░░░░░░░░░░░░░░░░░░░░░░││
│  └─────────────────────────────────────┘│
│                                         │
│  ┌─────────────────────────────────────┐│
│  │ 最近扫码记录:                        ││
│  │  • ZC001 MacBook Pro  ✓正常          ││
│  │  • ZC002 Dell显示器  ✓正常            ││
│  │  • ZC003 键盘鼠标     ⏳待处理        ││
│  └─────────────────────────────────────┘│
│                                         │
│  ┌─────────────────────────────────────┐│
│  │         ┌─────────────────────┐     ││
│  │         │   [扫码取景框]       │     ││
│  │         │                     │     ││
│  │         │   将二维码放入框内    │     ││
│  │         │                     │     ││
│  │         └─────────────────────┘     ││
│  │                                     ││
│  │  也可输入资产编码:                   ││
│  │  ┌─────────────────────────────────┐││
│  │  │ ZC...                            │││
│  │  └─────────────────────────────────┘││
│  └─────────────────────────────────────┘│
│                                         │
│  ┌─────────────────────────────────────┐│
│  │              [查看进度] [完成任务]    ││
│  └─────────────────────────────────────┘│
└─────────────────────────────────────────┘
```

### 4.2 扫码后快速确认

```
┌─────────────────────────────────────────┐
│  ZC001 MacBook Pro 16寸                   │
│                                         │
│  ┌─────────────────────────────────────┐│
│  │ 快速确认:                           ││
│  │  ┌─────┐ ┌─────┐ ┌─────┐ ┌─────┐    ││
│  │  │ ✓正常│ │位置变│ │损坏 │ │缺失 │    ││
│  │  └─────┘ └─────┘ └─────┘ └─────┘    ││
│  └─────────────────────────────────────┘│
│                                         │
│  ┌─────────────────────────────────────┐│
│  │  备注:                              ││
│  │  ┌─────────────────────────────────┐││
│  │  │                                 │││
│  │  └─────────────────────────────────┘││
│  └─────────────────────────────────────┘│
│                                         │
│  ┌─────────────────────────────────────┐│
│  │     [取消]  [确认并继续扫码]         ││
│  └─────────────────────────────────────┘│
└─────────────────────────────────────────┘
```

---

## 5. 扫码历史记录

### 5.1 本地扫码历史

```
┌─────────────────────────────────────────┐
│  扫码历史                                │
├─────────────────────────────────────────┤
│  ┌─────────────────────────────────────┐│
│  │ 今天                15条记录          ││
│  │  ┌─────────────────────────────────┐││
│  │  │ ZC001  MacBook Pro    10:30    │││
│  │  │ ZC002  Dell显示器     10:28    │││
│  │  │ ZC003  键盘鼠标      10:25    │││
│  │  └─────────────────────────────────┘││
│  └─────────────────────────────────────┘│
│                                         │
│  ┌─────────────────────────────────────┐│
│  │ 昨天                45条记录          ││
│  └─────────────────────────────────────┘│
│                                         │
│  ┌─────────────────────────────────────┐│
│  │ 更早                [查看更多]        ││
│  └─────────────────────────────────────┘│
│                                         │
│  ┌─────────────────────────────────────┐│
│  │              [清空历史]               ││
│  └─────────────────────────────────────┘│
└─────────────────────────────────────────┘
```

### 5.2 IndexedDB 存储

```javascript
// 扫码历史 IndexedDB 存储
{
  storeName: 'scan_history',
  indexes: [
    { name: 'scanned_at', keyPath: 'scanned_at' },
    { name: 'asset_code', keyPath: 'asset_code' }
  ],
  data: {
    id: 'scan_001',
    asset_code: 'ZC001',
    asset_name: 'MacBook Pro 16寸',
    scan_source: 'inventory', // inventory | pickup | general
    source_id: 'task_123',
    scan_result: 'normal',  // normal | location_changed | damaged | missing
    scanned_at: '2024-01-15T10:30:00Z'
  }
}
```

---

## 6. 离线扫码支持

### 6.1 离线模式处理

```
┌─────────────────────────────────────────┐
│  ⚠️  网络不可用                          │
│                                         │
│  扫码记录将保存到本地                   │
│  网络恢复后自动同步                     │
│                                         │
│  当前离线记录: 5条                     │
│                                         │
│  ┌─────────────────────────────────────┐│
│  │  ZC001  MacBook Pro    待同步       ││
│  │  ZC002  Dell显示器     待同步       ││
│  │  ZC003  键盘鼠标      待同步       ││
│  │  ZC004  耳机          待同步       ││
│  │  ZC005  鼠标          待同步       ││
│  └─────────────────────────────────────┘│
│                                         │
│  ┌─────────────────────────────────────┐│
│  │       [立即重试]  [离线继续]         ││
│  └─────────────────────────────────────┘│
└─────────────────────────────────────────┘
```

### 6.2 网络恢复后同步

```
┌─────────────────────────────────────────┐
│  同步完成                               │
├─────────────────────────────────────────┤
│  ┌─────────────────────────────────────┐│
│  │  成功: 5条                           ││
│  │  失败: 0条                           ││
│  └─────────────────────────────────────┘│
│                                         │
│  ┌─────────────────────────────────────┐│
│  │       [确定]                         ││
│  └─────────────────────────────────────┘│
└─────────────────────────────────────────┘
```

---

## 7. API设计

### 7.1 统一扫码接口

```http
POST /api/portal/mobile/scan/

Request:
{
  "qr_data": "ZC202406001234",
  "scan_source": "inventory",     # inventory | pickup | transfer | return | receive | general
  "source_id": "task_123",         # 可选，关联的任务/单据ID
  "scan_result": null,            # 可选，离线扫码时的结果
  "remark": null                  # 可选，备注信息
}

Response:
{
  "asset": {
    "id": 1,
    "asset_code": "ZC001",
    "asset_name": "MacBook Pro 16寸",
    "basic_info": {...},
    "usage_info": {...}
  },
  "context": {
    "inventory_task": {
      "id": "task_123",
      "name": "3楼盘点",
      "snapshot_id": "snap_001",
      "snapshot_location": "3楼A区"
    }
  },
  "available_actions": ["confirm_normal", "confirm_location_change", "confirm_damaged", "confirm_missing"]
}
```

### 7.2 批量提交扫码结果

```http
POST /api/portal/mobile/scan/batch/

Request:
{
  "source": "inventory",
  "source_id": "task_123",
  "results": [
    {
      "asset_code": "ZC001",
      "scan_result": "normal",
      "scanned_at": "2024-01-15T10:30:00Z"
    },
    {
      "asset_code": "ZC002",
      "scan_result": "location_changed",
      "new_location": "3楼B区",
      "scanned_at": "2024-01-15T10:31:00Z"
    }
  ]
}

Response:
{
  "success": true,
  "processed": 2,
  "failed": 0,
  "task_progress": {
    "total": 120,
    "scanned": 17,
    "percentage": 14.2
  }
}
```

---

## 8. Vue组件设计

### 8.1 统一扫码结果组件

```vue
<!-- src/components/mobile/scan/ScanResult.vue -->

<template>
  <div class="scan-result-page">
    <!-- 来源标识 -->
    <div v-if="scanSource" class="source-badge">
      {{ getSourceLabel(scanSource) }}
    </div>

    <!-- 离线标识 -->
    <van-tag v-if="isOffline" type="warning" class="offline-badge">
      离线模式
    </van-tag>

    <!-- 资产卡片 -->
    <AssetDetailCards
      :asset="asset"
      :active-card="activeCard"
      @card-change="handleCardChange"
    />

    <!-- 场景化操作 -->
    <component
      :is="getActionComponent()"
      :asset="asset"
      :context="scanContext"
      @confirm="handleActionConfirm"
      @continue="handleContinueScan"
    />

    <!-- 继续扫码按钮 -->
    <van-button
      v-if="allowContinuousScan"
      type="primary"
      block
      class="continue-scan-btn"
      @click="handleContinueScan"
    >
      {{ continueScanText }}
    </van-button>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { useRoute } from 'vue-router'
import AssetDetailCards from '@/components/mobile/asset/AssetDetailCards.vue'
import InventoryActions from '@/components/mobile/scan/actions/InventoryActions.vue'
import PickupActions from '@/components/mobile/scan/actions/PickupActions.vue'

const route = useRoute()
const asset = ref(null)
const activeCard = ref('basic')
const scanSource = ref(route.query.source || 'general')
const scanContext = ref(null)
const isOffline = ref(false)

const allowContinuousScan = computed(() => {
  return ['inventory', 'pickup', 'transfer'].includes(scanSource.value)
})

const continueScanText = computed(() => {
  const texts = {
    'inventory': '继续盘点',
    'pickup': '继续添加',
    'transfer': '继续添加',
    'return': '继续归还',
    'general': '再次扫码'
  }
  return texts[scanSource.value] || '再次扫码'
})

const getActionComponent = () => {
  const components = {
    'inventory': InventoryActions,
    'pickup': PickupActions,
    'transfer': PickupActions,
    'return': ReturnActions
  }
  return components[scanSource.value] || GeneralActions
}

const handleActionConfirm = (result) => {
  // 处理操作确认
  if (allowContinuousScan.value) {
    // 继续扫码
    handleContinueScan()
  } else {
    // 返回
    router.back()
  }
}

const handleContinueScan = () => {
  // 重新进入扫码
  router.push({
    path: '/scan',
    query: {
      source: scanSource.value,
      sourceId: route.query.sourceId
    }
  })
}
</script>
```

### 8.2 连续扫码组件

```vue
<!-- src/components/mobile/scan/ContinuousScan.vue -->

<template>
  <div class="continuous-scan-page">
    <!-- 进度条 -->
    <div class="progress-section">
      <div class="progress-info">
        <span>{{ progress.scanned }}/{{ progress.total }}</span>
        <span class="percentage">{{ progress.percentage }}%</span>
      </div>
      <van-progress :percentage="progress.percentage" />
    </div>

    <!-- 最近扫码记录 -->
    <div class="recent-scans">
      <div class="section-title">最近扫码</div>
      <div
        v-for="item in recentScans"
        :key="item.id"
        class="scan-item"
      >
        <div class="asset-info">
          <span class="asset-code">{{ item.asset_code }}</span>
          <span class="asset-name">{{ item.asset_name }}</span>
        </div>
        <van-tag :type="getScanResultType(item.scan_result)">
          {{ getScanResultLabel(item.scan_result) }}
        </van-tag>
      </div>
    </div>

    <!-- 扫码区域 -->
    <div class="scan-section">
      <ScannerView
        @scan="handleScan"
        @manual-input="handleManualInput"
      />
    </div>

    <!-- 完成按钮 -->
    <van-button
      type="primary"
      block
      size="large"
      @click="handleComplete"
    >
      完成盘点
    </van-button>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'

const router = useRouter()
const progress = ref({ total: 120, scanned: 15, percentage: 12.5 })
const recentScans = ref([])

const handleScan = async (qrData: string) => {
  // 处理扫码
  const result = await scanApi.scan(qrData, 'inventory')

  // 更新进度
  progress.value.scanned++
  progress.value.percentage = Math.round(
    (progress.value.scanned / progress.value.total) * 100
  )

  // 添加到最近记录
  recentScans.value.unshift({
    id: `scan_${Date.now()}`,
    asset_code: result.asset.asset_code,
    asset_name: result.asset.asset_name,
    scan_result: 'normal',
    scanned_at: new Date().toISOString()
  })

  // 震动反馈
  if (navigator.vibrate) {
    navigator.vibrate(50)
  }
}

const handleComplete = () => {
  // 完成盘点，返回任务详情
  router.back()
}
</script>
```
