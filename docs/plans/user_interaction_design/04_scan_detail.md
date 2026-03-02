# 04. 移动端扫码详情 - 详细设计

## 概述

本文档描述移动端扫码后统一展示资产信息的交互设计，适用于所有扫码场景（盘点、领用、调拨、日常查询等）。采用滑动卡片模式，确保不同扫码入口的展示体验一致。

---

## 1. 扫码结果统一页面

### 1.1 页面结构

```
┌─────────────────────────────────────────┐
│  ×                                     │
│  ┌─────────────────────────────────────┐│
│  │  [基础信息] [使用信息] [财务信息]   ││
│  └─────────────────────────────────────┘│
│                                         │
│  ┌─────────────────────────────────────┐│
│  │         ┌─────────────┐             ││
│  │         │   [照片]    │             ││
│  │         └─────────────┘             ││
│  │           [放大查看]                ││
│  │                                     ││
│  │  资产编码  ZC202406001234           ││
│  │  资产名称  MacBook Pro 16寸         ││
│  │  资产分类  电子设备 > 电脑 > 笔记本 ││
│  │  规格型号  M3 Max/64G/1T           ││
│  └─────────────────────────────────────┘│
│                                         │
│  < 左右滑动切换卡片 >                    ││
│                                         │
│  ┌─────────────────────────────────────┐│
│  │  根据扫码来源显示不同操作:           ││
│  │                                     ││
│  │  盘点场景:                           ││
│  │  [✓正常] [位置变更] [损坏] [缺失]    ││
│  │                                     ││
│  │  领用场景:                           ││
│  │  [添加到领用单]                      ││
│  │                                     ││
│  │  调拨场景:                           ││
│  │  [添加到调拨单]                      ││
│  │                                     ││
│  │  通用场景:                           ││
│  │  [查看二维码] [操作记录] [分享]      ││
│  └─────────────────────────────────────┘│
└─────────────────────────────────────────┘
```

### 1.2 卡片分组

#### 基础信息卡（默认显示）

| 字段 | 显示格式 | 说明 |
|------|---------|------|
| 资产照片 | 大图展示 | 支持点击放大 |
| 资产编码 | 高亮显示 | 支持长按复制 |
| 资产名称 | 主标题 | - |
| 资产分类 | 层级显示 | 显示完整路径 |
| 规格型号 | 支持复制 | - |
| 序列号 | 支持复制 | 有则显示 |

#### 使用信息卡

| 字段 | 显示格式 | 说明 |
|------|---------|------|
| 存放地点 | 快照 vs 当前 | 有变化则高亮 |
| 保管人 | 头像 + 姓名 + 部门 | - |
| 使用状态 | 标签式 | 在用/闲置/维修中 |
| 关系类型 | 保管/借用/领用 | 显示与扫码用户的关系 |
| 领用日期 | YYYY-MM-DD | 有则显示 |
| 预计归还 | 借用资产显示 | 临近到期高亮 |

#### 财务信息卡

| 字段 | 显示格式 | 说明 |
|------|---------|------|
| 资产原值 | ¥12,999.00 | - |
| 累计折旧 | ¥4,332.15 | - |
| 净值 | ¥8,666.85 | - |
| 采购日期 | 2024-01-10 | - |
| 供应商 | Apple授权经销商 | - |

#### 操作记录卡

| 字段 | 显示格式 | 说明 |
|------|---------|------|
| 最近操作 | 时间线 | 最近5条记录 |
| 操作类型 | 领用/调拨/借用/归还 | 带图标 |
| 操作人 | 姓名 + 时间 | - |

---

## 2. 场景化操作按钮

### 2.1 不同扫码来源的操作

| 扫码来源 | 操作按钮 | 说明 |
|---------|---------|------|
| 盘点任务 | ✓正常、位置变更、损坏、缺失 | 记录盘点结果 |
| 领用申请 | 添加到领用单 | 添加到当前领用单 |
| 调拨申请 | 添加到调拨单 | 添加到当前调拨单 |
| 借用申请 | 添加到借用单 | 添加到当前借用单 |
| 资产归还 | 确认归还 | 确认归还操作 |
| 通用查询 | 查看二维码、操作记录、分享 | 基础操作 |

### 2.2 盘点场景操作

```
┌─────────────────────────────────────────┐
│  请选择盘点状态                         │
├─────────────────────────────────────────┤
│                                         │
│  ┌─────────────────────────────────────┐│
│  │  ✓ 正常                              ││
│  │  资产位置和状态均正常                ││
│  └─────────────────────────────────────┘│
│                                         │
│  ┌─────────────────────────────────────┐│
│  │  📍 位置变更                         ││
│  │  资产当前位置与快照不符              ││
│  └─────────────────────────────────────┘│
│                                         │
│  ┌─────────────────────────────────────┐│
│  │  🔧 损坏                             ││
│  │  资产已损坏需维修或报废              ││
│  └─────────────────────────────────────┘│
│                                         │
│  ┌─────────────────────────────────────┐│
│  │  ❓ 缺失                             ││
│  │  找不到资产                          ││
│  └─────────────────────────────────────┘│
│                                         │
│  ┌─────────────────────────────────────┐│
│  │  📷 拍照记录                         ││
│  └─────────────────────────────────────┘│
│                                         │
│  ┌─────────────────────────────────────┐│
│  │  📝 备注                             ││
│  │  ┌─────────────────────────────────┐││
│  │  │                                 │││
│  │  └─────────────────────────────────┘││
│  └─────────────────────────────────────┘│
│                                         │
│  ┌─────────────────────────────────────┐│
│  │       [取消]  [确认提交]             ││
│  └─────────────────────────────────────┘│
└─────────────────────────────────────────┘
```

### 2.3 领用场景操作

```
┌─────────────────────────────────────────┐
│  添加到领用单                           │
├─────────────────────────────────────────┤
│                                         │
│  ┌─────────────────────────────────────┐│
│  │  资产: MacBook Pro 16寸             ││
│  │  编码: ZC001                        ││
│  │  状态: ✅可领用                      ││
│  └─────────────────────────────────────┘│
│                                         │
│  领用数量                               │
│  ┌─────────────────────────────────────┐│
│  │  [─]  1  [+ ]                        ││
│  └─────────────────────────────────────┘│
│                                         │
│  领用备注（可选）                       │
│  ┌─────────────────────────────────────┐│
│  │  ┌─────────────────────────────────┐││
│  │  │                                 │││
│  │  └─────────────────────────────────┘││
│  └─────────────────────────────────────┘│
│                                         │
│  ┌─────────────────────────────────────┐│
│  │    [取消]  [添加到领用单]            ││
│  └─────────────────────────────────────┘│
└─────────────────────────────────────────┘
```

---

## 3. 混合数据获取

### 3.1 数据获取时机

| 时机 | 获取内容 | 存储位置 |
|------|---------|---------|
| 任务启动 | 预取资产基础信息（前500条） | IndexedDB |
| 扫码后 | 实时获取该资产完整详情 | 内存 + IndexedDB缓存 |
| 切换卡片 | 按需获取该卡片数据 | 内存 |

### 3.2 离线处理

```
扫码时
    │
    ├──── 有网络 ────> 解析QR码 → 从服务器获取资产详情
    │                           │
    │                           ▼
    │                    显示资产详情卡片
    │
    └──── 无网络 ────> 解析QR码 → 从本地缓存查找
                              │
                              ├──── 找到 ────> 显示缓存的详情
                              │                   (标注离线数据)
                              │
                              └──── 未找到 ────> 提示"资产信息未缓存"
                                                      │
                                                      ▼
                                              ┌─────────────────────┐
                                              │ 暂存扫码记录        │
                                              │ 网络恢复后自动更新 │
                                              └─────────────────────┘
```

---

## 4. API设计

### 4.1 扫码解析

```http
POST /api/portal/mobile/scan/

Request:
{
  "qr_data": "ZC202406001234",
  "scan_source": "inventory",  # inventory | pickup | transfer | loan | general
  "source_id": "task_123"       # 可选，关联的任务ID
}

Response:
{
  "asset_id": 1,
  "asset_code": "ZC001",
  "asset_name": "MacBook Pro 16寸",
  "basic_info": {
    "asset_code": "ZC001",
    "asset_name": "MacBook Pro 16寸",
    "category_path": "电子设备 > 电脑 > 笔记本电脑",
    "specification": "M3 Max/64G/1T",
    "serial_number": "C02XYZ123",
    "photos": [...]
  },
  "usage_info": {
    "location": "3楼A区",
    "custodian": {...},
    "asset_status": "in_use",
    "pickup_date": "2024-01-15"
  },
  "financial_info": {
    "original_value": 12999.00,
    "net_value": 8666.85
  },
  "available_actions": ["confirm_normal", "confirm_location_change", "confirm_damaged", "confirm_missing"],
  "_cache_info": {
    "cached": false,
    "cached_at": null
  }
}
```

### 4.2 获取资产详情

```http
GET /api/portal/assets/{asset_id}/detail/

Query Parameters:
  - sections: list  # 需要返回的详情区块
  - scan_source: str # 扫码来源

Response:
{
  "asset_id": 1,
  "basic": {...},
  "usage": {...},
  "financial": {...},
  "history": [...],
  "context_actions": {
    "inventory": {
      "snapshot_id": "snap_001",
      "snapshot_location": "3楼A区",
      "can_scan": true
    },
    "pickup": {
      "is_available": true,
      "current_status": "idle"
    }
  }
}
```

---

## 5. Vue组件设计

### 5.1 扫码结果页面

```vue
<!-- src/views/portal/mobile/ScanResult.vue -->

<template>
  <div class="scan-result-page">
    <!-- 顶部导航 -->
    <van-nav-bar
      title="资产详情"
      left-text="关闭"
      @click-left="handleClose"
    />

    <!-- 场景标识 -->
    <div v-if="scanSource" class="scan-source-badge">
      {{ getSourceLabel(scanSource) }}
    </div>

    <!-- 离线标识 -->
    <van-tag v-if="isOffline" type="warning" class="offline-badge">
      离线数据
    </van-tag>

    <!-- 卡片切换 -->
    <van-tabs v-model:active="activeCard" :stretch="true">
      <van-tab title="基础" name="basic">
        <BasicInfoCard :asset="asset" />
      </van-tab>
      <van-tab title="使用" name="usage">
        <UsageInfoCard :asset="asset" />
      </van-tab>
      <van-tab title="财务" name="financial">
        <FinancialInfoCard :asset="asset" />
      </van-tab>
      <van-tab title="记录" name="history">
        <HistoryCard :asset="asset" />
      </van-tab>
    </van-tabs>

    <!-- 场景化操作 -->
    <div class="action-panel">
      <!-- 盘点操作 -->
      <InventoryActions
        v-if="scanSource === 'inventory'"
        :asset="asset"
        @confirm="handleInventoryConfirm"
      />

      <!-- 领用操作 -->
      <PickupActions
        v-else-if="scanSource === 'pickup'"
        :asset="asset"
        @add="handleAddToPickup"
      />

      <!-- 通用操作 -->
      <GeneralActions
        v-else
        :asset="asset"
        @qr="handleShowQR"
        @share="handleShare"
      />
    </div>

    <!-- 继续扫码按钮 -->
    <van-button
      v-if="allowContinuousScan"
      type="primary"
      block
      class="continue-scan-btn"
      @click="handleContinueScan"
    >
      继续扫码
    </van-button>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { scanApi } from '@/api/scan'

const route = useRoute()
const asset = ref(null)
const activeCard = ref('basic')
const scanSource = ref(route.query.source || 'general')
const isOffline = ref(false)

const allowContinuousScan = computed(() => {
  return ['inventory', 'pickup'].includes(scanSource.value)
})

const loadAssetDetail = async () => {
  try {
    const qrData = route.query.qr
    const { data } = await scanApi.parseQR(qrData, scanSource.value)
    asset.value = data
    isOffline.value = data._cache_info?.cached || false

    // 保存到本地缓存
    await saveToLocalCache(data)
  } catch (error) {
    // 网络错误，尝试从本地缓存读取
    const cached = await getFromLocalCache(route.query.qr)
    if (cached) {
      asset.value = cached
      isOffline.value = true
    } else {
      showToast('无法获取资产信息')
    }
  }
}

onMounted(() => {
  loadAssetDetail()
})
</script>
```

### 5.2 基础信息卡片组件

```vue
<!-- src/components/mobile/asset/BasicInfoCard.vue -->

<template>
  <div class="basic-info-card">
    <!-- 资产照片 -->
    <div class="photo-section" @click="handlePreviewImage">
      <van-image
        :src="asset?.basic_info?.photos?.[0]?.url"
        fit="contain"
      >
        <template #error>
          <div class="image-placeholder">
            <van-icon name="photo-fail" size="48" />
          </div>
        </template>
      </van-image>
      <van-button
        type="primary"
        size="small"
        plain
        class="preview-btn"
      >
        放大查看
      </van-button>
    </div>

    <!-- 基础字段 -->
    <van-cell-group>
      <van-cell title="资产编码" :value="asset?.basic_info?.asset_code">
        <template #icon>
          <van-icon name="barcode" />
        </template>
        <template #right-icon>
          <van-button
            size="mini"
            @click.stop="handleCopy"
          >
            复制
          </van-button>
        </template>
      </van-cell>

      <van-cell title="资产名称" :value="asset?.basic_info?.asset_name" />

      <van-cell
        title="资产分类"
        :value="asset?.basic_info?.category_path"
      />

      <van-cell
        title="规格型号"
        :value="asset?.basic_info?.specification"
      />

      <van-cell
        v-if="asset?.basic_info?.serial_number"
        title="序列号"
        :value="asset?.basic_info?.serial_number"
      >
        <template #right-icon>
          <van-button
            size="mini"
            @click.stop="handleCopySerial"
          >
            复制
          </van-button>
        </template>
      </van-cell>
    </van-cell-group>
  </div>
</template>
```

### 5.3 使用信息卡片组件

```vue
<!-- src/components/mobile/asset/UsageInfoCard.vue -->

<template>
  <div class="usage-info-card">
    <van-cell-group>
      <van-cell title="存放地点">
        <template #value>
          <span :class="{ 'changed': hasLocationChange }">
            {{ asset?.usage_info?.location }}
          </span>
          <van-tag
            v-if="hasLocationChange"
            type="danger"
            size="small"
          >
            位置变更
          </van-tag>
        </template>
      </van-cell>

      <van-cell title="保管人">
        <template #value>
          <div class="custodian-info">
            <van-image
              :src="asset?.usage_info?.custodian?.avatar"
              round
              width="24"
              height="24"
            />
            {{ asset?.usage_info?.custodian?.name }}
            <van-tag size="small">
              {{ asset?.usage_info?.custodian?.department }}
            </van-tag>
          </div>
        </template>
      </van-cell>

      <van-cell title="使用状态">
        <template #value>
          <van-tag :type="getStatusType(asset?.usage_info?.asset_status)">
            {{ asset?.usage_info?.asset_status_label }}
          </van-tag>
        </template>
      </van-cell>

      <van-cell
        v-if="asset?.usage_info?.pickup_date"
        title="领用日期"
        :value="asset?.usage_info?.pickup_date"
      />

      <van-cell
        v-if="asset?.usage_info?.expected_return_date"
        title="预计归还"
      >
        <template #value>
          <span :class="{ 'urgent': isReturnNear }">
            {{ asset?.usage_info?.expected_return_date }}
          </span>
          <van-tag
            v-if="isReturnNear"
            type="warning"
            size="small"
          >
            即将到期
          </van-tag>
        </template>
      </van-cell>
    </van-cell-group>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'

interface Props {
  asset: any
}

const props = defineProps<Props>()

const hasLocationChange = computed(() => {
  return props.asset?.usage_info?.location_changed
})

const isReturnNear = computed(() => {
  // 判断是否临近归还日期
  const expected = props.asset?.usage_info?.expected_return_date
  if (!expected) return false

  const days = Math.ceil(
    (new Date(expected).getTime() - Date.now()) / (1000 * 60 * 60 * 24)
  )
  return days <= 3
})

const getStatusType = (status: string) => {
  const types = {
    'in_use': 'success',
    'idle': 'default',
    'maintenance': 'danger'
  }
  return types[status] || 'default'
}
</script>
```

### 5.4 盘点操作组件

```vue
<!-- src/components/mobile/asset/InventoryActions.vue -->

<template>
  <div class="inventory-actions">
    <van-radio-group v-model="selectedStatus">
      <van-cell-group>
        <van-cell
          title="✓ 正常"
          label="资产位置和状态均正常"
          clickable
          @click="selectedStatus = 'normal'"
        >
          <template #right-icon>
            <van-radio name="normal" />
          </template>
        </van-cell>

        <van-cell
          title="📍 位置变更"
          label="资产当前位置与快照不符"
          clickable
          @click="selectedStatus = 'location_changed'"
        >
          <template #right-icon>
            <van-radio name="location_changed" />
          </template>
        </van-cell>

        <van-cell
          title="🔧 损坏"
          label="资产已损坏需维修或报废"
          clickable
          @click="selectedStatus = 'damaged'"
        >
          <template #right-icon>
            <van-radio name="damaged" />
          </template>
        </van-cell>

        <van-cell
          title="❓ 缺失"
          label="找不到资产"
          clickable
          @click="selectedStatus = 'missing'"
        >
          <template #right-icon>
            <van-radio name="missing" />
          </template>
        </van-cell>
      </van-cell-group>
    </van-radio-group>

    <!-- 附加操作 -->
    <van-cell-group class="mt-16">
      <van-cell
        title="📷 拍照记录"
        is-link
        @click="handleTakePhoto"
      />

      <van-cell
        title="📝 备注"
        :value="remark || '点击填写备注'"
        is-link
        @click="handleEditRemark"
      />
    </van-cell-group>

    <!-- 提交按钮 -->
    <div class="submit-actions">
      <van-button
        type="primary"
        block
        :disabled="!selectedStatus"
        @click="handleSubmit"
      >
        确认提交
      </van-button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'

interface Props {
  asset: any
}

const props = defineProps<Props>()
const emit = defineEmits(['confirm'])

const selectedStatus = ref('')
const remark = ref('')

const handleTakePhoto = () => {
  // 调用相机拍照
}

const handleEditRemark = () => {
  // 打开备注输入框
}

const handleSubmit = () => {
  emit('confirm', {
    asset_id: props.asset.asset_id,
    status: selectedStatus.value,
    remark: remark.value
  })
}
</script>
```

---

## 6. 与现有PRD的整合

### 6.1 需要更新的文档

| 文档 | 更新内容 |
|------|---------|
| `phase4_4_inventory_assignment/mobile_user_flow.md` | 统一扫码结果页面设计 |
| `phase6_user_portal/frontend.md` | 补充移动端扫码详情组件 |
| `phase4_1_inventory_qr/frontend.md` | 统一扫码处理逻辑 |

### 6.2 交互规范统一

| 规范项 | 统一标准 |
|-------|---------|
| 卡片切换 | 左右滑动 |
| 照片查看 | 点击放大 |
| 文本复制 | 长按复制 |
| 操作反馈 | Toast + 震动 |
| 离线提示 | 顶部固定标识 |
