# Phase 6: User Portal (用户门户) - 前端实现

## 概述

用户门户前端采用 Vue 3 + Element Plus 实现，支持 PC 端和移动端自适应布局。

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

## 目录结构

```
src/views/portal/                    # 门户模块
├── PortalHome.vue                   # 门户首页
├── MyAssets/                        # 我的资产
│   ├── AssetList.vue                # 资产列表
│   ├── AssetDetail.vue              # 资产详情
│   └── AssetSummary.vue             # 资产汇总
├── MyRequests/                      # 我的申请
│   ├── RequestList.vue              # 申请列表
│   ├── RequestDetail.vue            # 申请详情
│   └── RequestTabs.vue              # 申请分类标签页
├── MyTasks/                         # 我的待办
│   ├── TaskList.vue                 # 待办列表
│   ├── TaskDetail.vue               # 待办详情
│   └── TaskCenter.vue               # 待办中心
├── Profile/                         # 个人中心
│   ├── ProfileIndex.vue             # 个人信息
│   ├── ProfileEdit.vue              # 编辑资料
│   └── Preferences.vue              # 偏好设置
└── mobile/                          # 移动端页面
    ├── MobileHome.vue               # 移动端首页
    ├── MobileAssets.vue             # 移动端资产
    ├── MobileTasks.vue              # 移动端待办
    └── ScanPage.vue                 # 扫码页面

src/components/portal/               # 门户组件
├── AssetCard.vue                    # 资产卡片
├── RequestCard.vue                  # 申请卡片
├── TaskCard.vue                     # 待办卡片
├── QuickActions.vue                 # 快捷操作
├── StatCard.vue                     # 统计卡片
└── mobile/                          # 移动端组件
    ├── MobileHeader.vue             # 移动端头部
    ├── MobileTabBar.vue             # 移动端底部导航
    └── ScanButton.vue               # 扫码按钮

src/api/portal/                      # 门户API
└── index.ts                         # 门户API封装

src/stores/portal.ts                 # 门户状态管理
```

---

## 1. 门户首页 (PortalHome.vue)

### 1.1 PC端首页布局

```vue
<!-- src/views/portal/PortalHome.vue -->

<template>
  <div class="portal-home">
    <!-- 用户信息卡片 -->
    <el-row :gutter="16" class="mb-16">
      <el-col :span="18">
        <UserCard :user="overview.user" />
      </el-col>
      <el-col :span="6">
        <StatCard title="待处理" :value="overview.tasks?.pending || 0" type="warning" />
      </el-col>
    </el-row>

    <!-- 快捷操作 -->
    <el-card class="mb-16">
      <template #header>
        <span class="card-title">快捷操作</span>
      </template>
      <QuickActions :actions="overview.quick_actions" @action="handleQuickAction" />
    </el-card>

    <!-- 主要内容区 -->
    <el-row :gutter="16">
      <!-- 我的资产 -->
      <el-col :span="12">
        <el-card>
          <template #header>
            <div class="card-header">
              <span>我的资产</span>
              <el-link type="primary" @click="goTo('/portal/my-assets')">
                查看全部
              </el-link>
            </div>
          </template>
          <AssetList
            :assets="overview.assets?.recent || []"
            :loading="loading"
            :show-header="false"
          />
        </el-card>
      </el-col>

      <!-- 我的待办 -->
      <el-col :span="12">
        <el-card>
          <template #header>
            <div class="card-header">
              <span>我的待办</span>
              <el-badge :value="overview.tasks?.pending || 0" type="danger">
                <el-link type="primary" @click="goTo('/portal/my-tasks')">
                  查看全部
                </el-link>
              </el-badge>
            </div>
          </template>
          <TaskList
            :tasks="overview.tasks?.items || []"
            :loading="loading"
            :show-header="false"
            compact
          />
        </el-card>
      </el-col>
    </el-row>

    <!-- 最近申请 -->
    <el-card class="mt-16">
      <template #header>
        <div class="card-header">
          <span>最近申请</span>
          <el-link type="primary" @click="goTo('/portal/my-requests')">
            查看全部
          </el-link>
        </div>
      </template>
      <RequestList
        :requests="overview.requests?.recent || []"
        :loading="loading"
        :show-header="false"
      />
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { portalApi } from '@/api/portal'
import UserCard from '@/components/portal/UserCard.vue'
import StatCard from '@/components/portal/StatCard.vue'
import QuickActions from '@/components/portal/QuickActions.vue'
import AssetList from '@/views/portal/MyAssets/AssetList.vue'
import TaskList from '@/views/portal/MyTasks/TaskList.vue'
import RequestList from '@/views/portal/MyRequests/RequestList.vue'

const router = useRouter()
const loading = ref(false)
const overview = ref({
  user: null,
  assets: null,
  tasks: null,
  requests: null,
  quick_actions: []
})

const fetchOverview = async () => {
  loading.value = true
  try {
    const { data } = await portalApi.getOverview()
    overview.value = data
  } finally {
    loading.value = false
  }
}

const handleQuickAction = (action: any) => {
  if (action.action === 'navigate' && action.url) {
    router.push(action.url)
  } else if (action.action === 'scan') {
    // 打开扫码
    router.push('/portal/scan')
  }
}

const goTo = (path: string) => {
  router.push(path)
}

onMounted(() => {
  fetchOverview()
})
</script>

<style scoped>
.portal-home {
  padding: 16px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.card-title {
  font-size: 16px;
  font-weight: 500;
}

.mb-16 {
  margin-bottom: 16px;
}

.mt-16 {
  margin-top: 16px;
}
</style>
```

### 1.2 用户卡片组件

```vue
<!-- src/components/portal/UserCard.vue -->

<template>
  <el-card class="user-card">
    <div class="user-info">
      <el-avatar :size="64" :src="user?.avatar">
        {{ user?.real_name?.charAt(0) }}
      </el-avatar>
      <div class="user-details">
        <h3 class="user-name">{{ user?.real_name }}</h3>
        <p class="user-meta">
          <el-tag size="small">{{ user?.primary_department?.name }}</el-tag>
          <span class="divider">|</span>
          <span class="organization">{{ user?.organization?.name }}</span>
        </p>
      </div>
    </div>

    <el-divider />

    <el-row :gutter="16" class="user-stats">
      <el-col :span="8">
        <div class="stat-item" @click="$emit('navigate', 'assets')">
          <div class="stat-value">{{ userStats.assets_count || 0 }}</div>
          <div class="stat-label">我的资产</div>
        </div>
      </el-col>
      <el-col :span="8">
        <div class="stat-item" @click="$emit('navigate', 'requests')">
          <div class="stat-value">{{ userStats.requests_count || 0 }}</div>
          <div class="stat-label">我的申请</div>
        </div>
      </el-col>
      <el-col :span="8">
        <div class="stat-item" @click="$emit('navigate', 'tasks')">
          <div class="stat-value">{{ userStats.tasks_pending || 0 }}</div>
          <div class="stat-label">待处理</div>
        </div>
      </el-col>
    </el-row>

    <el-button
      type="primary"
      text
      class="profile-btn"
      @click="$emit('navigate', 'profile')"
    >
      个人设置
      <el-icon class="el-icon--right"><ArrowRight /></el-icon>
    </el-button>
  </el-card>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { ArrowRight } from '@element-plus/icons-vue'

interface Props {
  user: {
    real_name?: string
    avatar?: string
    primary_department?: { name?: string }
    organization?: { name?: string }
  }
  statistics?: {
    assets_count?: number
    requests_count?: number
    tasks_pending?: number
  }
}

const props = defineProps<Props>()

defineEmits<{
  navigate: [page: string]
}>()

const userStats = computed(() => props.statistics || {})
</script>

<style scoped>
.user-card {
  position: relative;
}

.user-info {
  display: flex;
  align-items: center;
  gap: 16px;
}

.user-details {
  flex: 1;
}

.user-name {
  margin: 0 0 8px 0;
  font-size: 18px;
  font-weight: 500;
}

.user-meta {
  margin: 0;
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 14px;
  color: #606266;
}

.divider {
  color: #dcdfe6;
}

.organization {
  color: #909399;
}

.user-stats {
  margin-top: 16px;
}

.stat-item {
  text-align: center;
  padding: 8px 0;
  cursor: pointer;
  border-radius: 4px;
  transition: background-color 0.3s;
}

.stat-item:hover {
  background-color: #f5f7fa;
}

.stat-value {
  font-size: 20px;
  font-weight: 500;
  color: #409eff;
}

.stat-label {
  font-size: 12px;
  color: #909399;
  margin-top: 4px;
}

.profile-btn {
  width: 100%;
  margin-top: 16px;
}
</style>
```

### 1.3 快捷操作组件

```vue
<!-- src/components/portal/QuickActions.vue -->

<template>
  <div class="quick-actions">
    <div
      v-for="action in actions"
      :key="action.id"
      class="action-item"
      :class="{ 'action-item-scan': action.action === 'scan' }"
      @click="$emit('action', action)"
    >
      <div class="action-icon" :style="{ background: action.color || getActionColor(action.id) }">
        <el-icon :size="24">
          <component :is="getActionIcon(action.icon)" />
        </el-icon>
      </div>
      <div class="action-info">
        <div class="action-name">{{ action.name }}</div>
        <div class="action-desc">{{ action.description }}</div>
      </div>
      <el-icon v-if="action.action === 'navigate'" class="action-arrow">
        <ArrowRight />
      </el-icon>
    </div>
  </div>
</template>

<script setup lang="ts">
import { markRaw } from 'vue'
import {
  ArrowRight,
  Box, ShoppingCart, HandHolding, QrScan, Approval,
  ClipboardList, Bell, More
} from '@/components/icons'

defineProps<{
  actions: Array<{
    id: string
    name: string
    icon: string
    description: string
    action?: string
    url?: string
    color?: string
  }>
}>()

defineEmits<{
  action: [action: any]
}>()

const icons = {
  'box': markRaw(Box),
  'shopping-cart': markRaw(ShoppingCart),
  'hand-holding': markRaw(HandHolding),
  'qr-scan': markRaw(QrScan),
  'approval': markRaw(Approval),
  'clipboard-list': markRaw(ClipboardList),
  'bell': markRaw(Bell),
  'more': markRaw(More)
}

const getActionIcon = (iconName: string) => {
  return icons[iconName] || Box
}

const getActionColor = (actionId: string) => {
  const colors = {
    'scan_qr': 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
    'my_assets': 'linear-gradient(135deg, #f093fb 0%, #f5576c 100%)',
    'apply_pickup': 'linear-gradient(135deg, #4facfe 0%, #00f2fe 100%)',
    'apply_loan': 'linear-gradient(135deg, #43e97b 0%, #38f9d7 100%)',
    'my_tasks': 'linear-gradient(135deg, #fa709a 0%, #fee140 100%)',
    'my_requests': 'linear-gradient(135deg, #30cfd0 0%, #330867 100%)'
  }
  return colors[actionId] || '#409eff'
}
</script>

<style scoped>
.quick-actions {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 16px;
}

.action-item {
  display: flex;
  align-items: center;
  padding: 16px;
  background: #f5f7fa;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.3s;
}

.action-item:hover {
  background: #ecf5ff;
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}

.action-item-scan {
  grid-column: span 2;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}

.action-item-scan .action-name,
.action-item-scan .action-desc {
  color: white;
}

.action-icon {
  width: 48px;
  height: 48px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
}

.action-info {
  flex: 1;
  margin-left: 12px;
}

.action-name {
  font-size: 14px;
  font-weight: 500;
  color: #303133;
}

.action-desc {
  font-size: 12px;
  color: #909399;
  margin-top: 2px;
}

.action-arrow {
  color: #c0c4cc;
}
</style>
```

---

## 2. 我的资产 (MyAssets)

### 2.1 资产列表

```vue
<!-- src/views/portal/MyAssets/AssetList.vue -->

<template>
  <div class="asset-list">
    <!-- 统计卡片 -->
    <el-row :gutter="16" class="mb-16">
      <el-col :span="6">
        <el-card shadow="hover">
          <el-statistic title="全部" :value="summary.total_count || 0" />
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="hover">
          <el-statistic title="保管中" :value="summary.custodian_count || 0">
            <template #suffix>
              <el-icon color="#67c23a"><Box /></el-icon>
            </template>
          </el-statistic>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="hover">
          <el-statistic title="借用中" :value="summary.borrowed_count || 0">
            <template #suffix>
              <el-icon color="#e6a23c"><HandHolding /></el-icon>
            </template>
          </el-statistic>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="hover">
          <el-statistic title="领用" :value="summary.pickup_count || 0">
            <template #suffix>
              <el-icon color="#409eff"><ShoppingCart /></el-icon>
            </template>
          </el-statistic>
        </el-card>
      </el-col>
    </el-row>

    <!-- 筛选区 -->
    <el-card class="mb-16">
      <el-form :inline="true" :model="filters" @submit.prevent="handleSearch">
        <el-form-item label="关系类型">
          <el-select v-model="filters.relation" placeholder="全部" clearable @change="handleSearch">
            <el-option label="保管中" value="custodian" />
            <el-option label="借用中" value="borrowed" />
            <el-option label="领用" value="pickup" />
          </el-select>
        </el-form-item>
        <el-form-item label="资产状态">
          <el-select v-model="filters.status" placeholder="全部" clearable @change="handleSearch">
            <el-option label="在用" value="in_use" />
            <el-option label="闲置" value="idle" />
            <el-option label="维修中" value="maintenance" />
          </el-select>
        </el-form-item>
        <el-form-item label="关键词">
          <el-input
            v-model="filters.keyword"
            placeholder="资产编码/名称/序列号"
            clearable
            @keyup.enter="handleSearch"
          >
            <template #append>
              <el-button :icon="Search" @click="handleSearch" />
            </template>
          </el-input>
        </el-form-item>
      </el-form>
    </el-card>

    <!-- 资产列表 -->
    <el-card>
      <el-table
        v-loading="loading"
        :data="assets"
        @row-click="handleViewDetail"
      >
        <el-table-column prop="asset_code" label="资产编码" width="140" />
        <el-table-column prop="asset_name" label="资产名称" min-width="180">
          <template #default="{ row }">
            <div class="asset-name-cell">
              <el-image
                v-if="row.image"
                :src="row.image"
                class="asset-thumb"
                fit="cover"
                :preview-src-list="[row.image]"
              />
              <div v-else class="asset-thumb-placeholder">
                <el-icon><Picture /></el-icon>
              </div>
              <div>
                <div class="asset-name">{{ row.asset_name }}</div>
                <div class="asset-spec">{{ row.specification }}</div>
              </div>
            </div>
          </template>
        </el-table-column>
        <el-table-column label="关系" width="100">
          <template #default="{ row }">
            <el-tag :type="getRelationType(row.relation)" size="small">
              {{ row.relation_label }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="asset_status_label" label="状态" width="90">
          <template #default="{ row }">
            <el-tag :type="getStatusType(row.asset_status)" size="small">
              {{ row.asset_status_label }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="department.name" label="使用部门" width="120" />
        <el-table-column prop="location.name" label="存放地点" width="120" />
        <el-table-column label="操作" width="180" fixed="right">
          <template #default="{ row }">
            <el-button link type="primary" @click.stop="handleViewDetail(row)">
              详情
            </el-button>
            <el-button
              v-if="row.can_transfer"
              link
              type="primary"
              @click.stop="handleTransfer(row)"
            >
              调拨
            </el-button>
            <el-button
              v-if="row.can_return"
              link
              type="warning"
              @click.stop="handleReturn(row)"
            >
              归还
            </el-button>
            <el-dropdown @command="(cmd) => handleMoreAction(cmd, row)">
              <el-button link type="info">
                更多<el-icon class="el-icon--right"><ArrowDown /></el-icon>
              </el-button>
              <template #dropdown>
                <el-dropdown-menu>
                  <el-dropdown-item command="qr">
                    <el-icon><QrCode /></el-icon> 二维码
                  </el-dropdown-item>
                  <el-dropdown-item command="history">
                    <el-icon><Clock /></el-icon> 操作记录
                  </el-dropdown-item>
                </el-dropdown-menu>
              </template>
            </el-dropdown>
          </template>
        </el-table-column>
      </el-table>

      <el-pagination
        v-model:current-page="pagination.page"
        v-model:page-size="pagination.page_size"
        :total="pagination.total"
        :page-sizes="[10, 20, 50, 100]"
        layout="total, sizes, prev, pager, next, jumper"
        @size-change="fetchData"
        @current-change="fetchData"
      />
    </el-card>

    <!-- 资产详情抽屉 -->
    <AssetDetailDrawer
      v-model="detailVisible"
      :asset-id="currentAssetId"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, computed } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import {
  Search, Picture, ArrowDown, QrCode, Clock,
  Box, ShoppingCart, HandHolding
} from '@element-plus/icons-vue'
import { portalApi } from '@/api/portal'
import AssetDetailDrawer from './AssetDetailDrawer.vue'

const router = useRouter()

const loading = ref(false)
const assets = ref([])
const summary = ref({})
const detailVisible = ref(false)
const currentAssetId = ref<number | null>(null)

const filters = reactive({
  relation: '',
  status: '',
  keyword: ''
})

const pagination = reactive({
  page: 1,
  page_size: 20,
  total: 0
})

const fetchData = async () => {
  loading.value = true
  try {
    const { data } = await portalApi.getMyAssets({
      ...filters,
      page: pagination.page,
      page_size: pagination.page_size
    })
    assets.value = data.items
    summary.value = data.summary
    pagination.total = data.total
  } finally {
    loading.value = false
  }
}

const handleSearch = () => {
  pagination.page = 1
  fetchData()
}

const handleViewDetail = (row: any) => {
  currentAssetId.value = row.id
  detailVisible.value = true
}

const handleTransfer = (row: any) => {
  router.push({
    name: 'AssetTransferForm',
    query: { assets: row.id }
  })
}

const handleReturn = (row: any) => {
  if (row.relation === 'borrowed') {
    router.push({
      name: 'AssetLoanReturn',
      query: { loan: row.related_documents.find((d: any) => d.type === 'loan')?.id }
    })
  } else {
    router.push({
      name: 'AssetReturnForm',
      query: { assets: row.id }
    })
  }
}

const handleMoreAction = (command: string, row: any) => {
  switch (command) {
    case 'qr':
      // 显示二维码
      break
    case 'history':
      // 显示操作记录
      break
  }
}

const getRelationType = (relation: string) => {
  const types = {
    'custodian': 'success',
    'borrowed': 'warning',
    'pickup': 'primary'
  }
  return types[relation] || 'info'
}

const getStatusType = (status: string) => {
  const types = {
    'in_use': 'success',
    'idle': 'info',
    'maintenance': 'danger'
  }
  return types[status] || 'info'
}

onMounted(() => {
  fetchData()
})
</script>

<style scoped>
.asset-name-cell {
  display: flex;
  align-items: center;
  gap: 12px;
}

.asset-thumb {
  width: 40px;
  height: 40px;
  border-radius: 4px;
}

.asset-thumb-placeholder {
  width: 40px;
  height: 40px;
  border-radius: 4px;
  background: #f5f7fa;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #c0c4cc;
}

.asset-name {
  font-weight: 500;
  color: #303133;
}

.asset-spec {
  font-size: 12px;
  color: #909399;
  margin-top: 2px;
}

.mb-16 {
  margin-bottom: 16px;
}
</style>
```

### 2.2 资产详情抽屉

```vue
<!-- src/views/portal/MyAssets/AssetDetailDrawer.vue -->

<template>
  <el-drawer
    v-model="visible"
    :title="asset?.asset_name || '资产详情'"
    size="50%"
    @closed="handleClosed"
  >
    <div v-if="loading" class="loading-container">
      <el-skeleton :rows="10" animated />
    </div>

    <div v-else-if="asset" class="asset-detail">
      <!-- 资产图片 -->
      <div class="asset-image-section">
        <el-image
          v-if="asset.asset.image"
          :src="asset.asset.image"
          class="asset-image"
          fit="contain"
          :preview-src-list="[asset.asset.image]"
        />
        <div v-else class="asset-image-placeholder">
          <el-icon :size="64"><Picture /></el-icon>
        </div>
        <el-tag :type="getStatusType(asset.asset.asset_status)" class="status-tag">
          {{ asset.asset.asset_status_label }}
        </el-tag>
        <el-tag type="info" class="relation-tag">
          {{ asset.relation_label }}
        </el-tag>
      </div>

      <!-- 基本信息 -->
      <el-descriptions title="基本信息" :column="2" border>
        <el-descriptions-item label="资产编码">
          {{ asset.asset.asset_code }}
          <el-button
            link
            type="primary"
            size="small"
            @click="showQRCode"
          >
            <el-icon><QrCode /></el-icon>
          </el-button>
        </el-descriptions-item>
        <el-descriptions-item label="资产名称">
          {{ asset.asset.asset_name }}
        </el-descriptions-item>
        <el-descriptions-item label="分类">
          {{ asset.asset.category?.name }}
        </el-descriptions-item>
        <el-descriptions-item label="规格型号">
          {{ asset.asset.specification || '-' }}
        </el-descriptions-item>
        <el-descriptions-item label="序列号">
          {{ asset.asset.serial_number || '-' }}
        </el-descriptions-item>
        <el-descriptions-item label="使用部门">
          {{ asset.asset.department?.name || '-' }}
        </el-descriptions-item>
        <el-descriptions-item label="存放地点">
          {{ asset.asset.location?.path || '-' }}
        </el-descriptions-item>
        <el-descriptions-item label="保管人">
          <template v-if="asset.asset.custodian">
            {{ asset.asset.custodian.name }}
            <el-tag v-if="asset.asset.custodian.department" size="small" class="ml-8">
              {{ asset.asset.custodian.department }}
            </el-tag>
          </template>
          <template v-else>-</template>
        </el-descriptions-item>
      </el-descriptions>

      <!-- 财务信息 -->
      <el-descriptions title="财务信息" :column="2" border class="mt-16">
        <el-descriptions-item label="采购价格">
          ¥{{ formatMoney(asset.asset.purchase_price) }}
        </el-descriptions-item>
        <el-descriptions-item label="采购日期">
          {{ asset.asset.purchase_date || '-' }}
        </el-descriptions-item>
        <el-descriptions-item label="供应商">
          {{ asset.asset.supplier?.name || '-' }}
        </el-descriptions-item>
        <el-descriptions-item label="当前净值">
          ¥{{ formatMoney(asset.asset.net_value) }}
        </el-descriptions-item>
        <el-descriptions-item label="折旧方式">
          {{ getDepreciationMethod(asset.asset.depreciation_method) }}
        </el-descriptions-item>
        <el-descriptions-item label="使用年限">
          {{ asset.asset.useful_life }} 个月
        </el-descriptions-item>
      </el-descriptions>

      <!-- 可用操作 -->
      <div v-if="asset.available_actions?.length" class="mt-16">
        <el-divider>快速操作</el-divider>
        <el-button-group>
          <el-button
            v-if="asset.available_actions.includes('apply_transfer')"
            type="primary"
            @click="handleTransfer"
          >
            <el-icon><Switch /></el-icon> 申请调拨
          </el-button>
          <el-button
            v-if="asset.available_actions.includes('apply_return')"
            type="warning"
            @click="handleReturn"
          >
            <el-icon><Back /></el-icon> 申请归还
          </el-button>
          <el-button @click="showHistory = true">
            <el-icon><Clock /></el-icon> 操作记录
          </el-button>
        </el-button-group>
      </div>

      <!-- 关联单据 -->
      <div v-if="asset.related_documents?.length" class="mt-16">
        <el-divider>关联单据</el-divider>
        <el-timeline>
          <el-timeline-item
            v-for="doc in asset.related_documents"
            :key="doc.id"
            :timestamp="doc.created_at"
            placement="top"
          >
            <el-card>
              <div class="doc-item">
                <el-tag :type="getDocTypeColor(doc.type)" size="small">
                  {{ doc.type_label }}
                </el-tag>
                <span class="doc-no">{{ doc.no }}</span>
                <el-tag :type="getDocStatusColor(doc.status)" size="small">
                  {{ doc.status_label }}
                </el-tag>
              </div>
            </el-card>
          </el-timeline-item>
        </el-timeline>
      </div>
    </div>

    <!-- 二维码弹窗 -->
    <el-dialog v-model="qrVisible" title="资产二维码" width="300px">
      <div class="qr-container">
        <el-image :src="asset?.asset?.qr_code" fit="contain" />
      </div>
    </el-dialog>

    <!-- 操作记录弹窗 -->
    <el-dialog v-model="showHistory" title="操作记录" width="600px">
      <el-timeline>
        <el-timeline-item
          v-for="log in asset?.history || []"
          :key="log.id"
          :timestamp="log.created_at"
          placement="top"
        >
          <div class="history-item">
            <el-tag size="small">{{ log.action_label }}</el-tag>
            <span v-if="log.from_status" class="status-change">
              {{ getStatusLabel(log.from_status) }} → {{ getStatusLabel(log.to_status) }}
            </span>
            <div class="operator">
              操作人: {{ log.operator }}
            </div>
            <div v-if="log.reason" class="reason">
              原因: {{ log.reason }}
            </div>
          </div>
        </el-timeline-item>
      </el-timeline>
    </el-dialog>
  </el-drawer>
</template>

<script setup lang="ts">
import { ref, watch } from 'vue'
import { ElMessage } from 'element-plus'
import {
  Picture, QrCode, Switch, Back, Clock
} from '@element-plus/icons-vue'
import { portalApi } from '@/api/portal'

interface Props {
  modelValue: boolean
  assetId: number | null
}

const props = defineProps<Props>()
const emit = defineEmits<{
  'update:modelValue': [value: boolean]
}>()

const visible = ref(false)
const loading = ref(false)
const asset = ref<any>(null)
const qrVisible = ref(false)
const showHistory = ref(false)

watch(() => props.modelValue, (val) => {
  visible.value = val
  if (val && props.assetId) {
    fetchAssetDetail()
  }
})

watch(visible, (val) => {
  emit('update:modelValue', val)
})

const fetchAssetDetail = async () => {
  if (!props.assetId) return

  loading.value = true
  try {
    const { data } = await portalApi.getAssetDetail(props.assetId)
    asset.value = data
  } finally {
    loading.value = false
  }
}

const handleClosed = () => {
  asset.value = null
}

const showQRCode = () => {
  qrVisible.value = true
}

const formatMoney = (val: number) => {
  if (!val) return '0.00'
  return val.toLocaleString('zh-CN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })
}

const getDepreciationMethod = (method: string) => {
  const methods = {
    'straight_line': '直线法',
    'double_declining': '双倍余额递减法',
    'sum_of_years': '年数总和法'
  }
  return methods[method] || method
}

const getStatusType = (status: string) => {
  const types = { 'in_use': 'success', 'idle': 'info', 'maintenance': 'danger' }
  return types[status] || 'info'
}

const getDocTypeColor = (type: string) => {
  const colors = {
    'pickup': 'primary',
    'loan': 'warning',
    'transfer': 'success',
    'return': 'info'
  }
  return colors[type] || 'info'
}

const getDocStatusColor = (status: string) => {
  const colors = {
    'pending': 'warning',
    'approved': 'success',
    'completed': 'info',
    'rejected': 'danger'
  }
  return colors[status] || 'info'
}

const getStatusLabel = (status: string) => {
  const labels = {
    'idle': '闲置', 'in_use': '在用', 'maintenance': '维修中'
  }
  return labels[status] || status
}

const handleTransfer = () => {
  ElMessage.info('跳转到调拨申请页面')
}

const handleReturn = () => {
  ElMessage.info('跳转到归还申请页面')
}
</script>

<style scoped>
.asset-detail {
  padding: 0 16px;
}

.asset-image-section {
  position: relative;
  text-align: center;
  padding: 20px;
  background: #f5f7fa;
  border-radius: 8px;
  margin-bottom: 20px;
}

.asset-image {
  max-width: 200px;
  max-height: 200px;
}

.asset-image-placeholder {
  width: 200px;
  height: 200px;
  margin: 0 auto;
  display: flex;
  align-items: center;
  justify-content: center;
  background: white;
  border-radius: 8px;
  color: #c0c4cc;
}

.status-tag {
  position: absolute;
  top: 20px;
  right: 20px;
}

.relation-tag {
  position: absolute;
  top: 20px;
  left: 20px;
}

.mt-16 {
  margin-top: 16px;
}

.ml-8 {
  margin-left: 8px;
}

.qr-container {
  text-align: center;
}

.qr-container :deep(.el-image) {
  width: 200px;
  height: 200px;
}

.doc-item {
  display: flex;
  align-items: center;
  gap: 12px;
}

.doc-no {
  font-weight: 500;
}

.history-item {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.status-change {
  color: #409eff;
  font-size: 12px;
}

.operator {
  font-size: 12px;
  color: #909399;
}

.reason {
  font-size: 12px;
  color: #606266;
}
</style>
```

---

## 3. 我的申请 (MyRequests)

### 3.1 申请列表

```vue
<!-- src/views/portal/MyRequests/RequestList.vue -->

<template>
  <div class="request-list">
    <!-- 分类标签页 -->
    <el-tabs v-model="activeTab" @tab-change="handleTabChange">
      <el-tab-pane label="全部" name="all">
        <template #label>
          <span class="tab-label">
            全部
            <el-badge v-if="summary.total" :value="summary.total" :max="99" />
          </span>
        </template>
      </el-tab-pane>
      <el-tab-pane label="待审批" name="pending">
        <template #label>
          <span class="tab-label">
            待审批
            <el-badge v-if="summary.by_status?.pending" :value="summary.by_status.pending" type="warning" />
          </span>
        </template>
      </el-tab-pane>
      <el-tab-pane label="进行中" name="in_progress">
        <template #label>
          <span class="tab-label">
            进行中
            <el-badge v-if="inProgressCount" :value="inProgressCount" type="primary" />
          </span>
        </template>
      </el-tab-pane>
      <el-tab-pane label="已完成" name="completed">
        <template #label>
          <span class="tab-label">
            已完成
            <el-badge v-if="summary.by_status?.completed" :value="summary.by_status.completed" />
          </span>
        </template>
      </el-tab-pane>
      <el-tab-pane label="草稿" name="draft" />
    </el-tabs>

    <!-- 类型筛选 -->
    <div class="type-filters">
      <el-radio-group v-model="filters.type" size="small" @change="fetchData">
        <el-radio-button label="">全部类型</el-radio-button>
        <el-radio-button label="pickup">领用</el-radio-button>
        <el-radio-button label="loan">借用</el-radio-button>
        <el-radio-button label="transfer">调拨</el-radio-button>
        <el-radio-button label="return">退库</el-radio-button>
        <el-radio-button label="consumable_issue">耗材领用</el-radio-button>
        <el-radio-button label="consumable_purchase">耗材采购</el-radio-button>
      </el-radio-group>

      <el-input
        v-model="filters.keyword"
        placeholder="搜索单号"
        clearable
        style="width: 200px"
        @keyup.enter="fetchData"
      >
        <template #prefix>
          <el-icon><Search /></el-icon>
        </template>
      </el-input>
    </div>

    <!-- 列表 -->
    <el-table v-loading="loading" :data="requests" @row-click="handleViewDetail">
      <el-table-column label="类型" width="100">
        <template #default="{ row }">
          <el-tag :type="getTypeColor(row.request_type)" size="small">
            {{ row.request_type_label }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="no" label="单号" width="160" />
      <el-table-column prop="summary" label="摘要" min-width="200" />
      <el-table-column label="状态" width="100">
        <template #default="{ row }">
          <el-tag :type="getStatusColor(row.status)" size="small">
            {{ row.status_label }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="created_at" label="创建时间" width="160">
        <template #default="{ row }">
          {{ formatDateTime(row.created_at) }}
        </template>
      </el-table-column>
      <el-table-column label="操作" width="160" fixed="right">
        <template #default="{ row }">
          <el-button link type="primary" @click.stop="handleViewDetail(row)">
            查看
          </el-button>
          <el-button
            v-if="row.can_edit"
            link
            type="primary"
            @click.stop="handleEdit(row)"
          >
            编辑
          </el-button>
          <el-dropdown
            v-if="row.can_cancel || row.can_withdraw"
            @command="(cmd) => handleAction(cmd, row)"
          >
            <el-button link type="primary">
              更多<el-icon class="el-icon--right"><ArrowDown /></el-icon>
            </el-button>
            <template #dropdown>
              <el-dropdown-menu>
                <el-dropdown-item v-if="row.can_cancel" command="cancel">
                  取消申请
                </el-dropdown-item>
                <el-dropdown-item v-if="row.can_withdraw" command="withdraw">
                  撤回申请
                </el-dropdown-item>
              </el-dropdown-menu>
            </template>
          </el-dropdown>
        </template>
      </el-table-column>
    </el-table>

    <el-pagination
      v-model:current-page="pagination.page"
      v-model:page-size="pagination.page_size"
      :total="pagination.total"
      layout="total, sizes, prev, pager, next, jumper"
      @size-change="fetchData"
      @current-change="fetchData"
    />

    <!-- 申请详情抽屉 -->
    <RequestDetailDrawer
      v-model="detailVisible"
      :request-type="currentRequestType"
      :request-id="currentRequestId"
      @refresh="fetchData"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Search, ArrowDown } from '@element-plus/icons-vue'
import { portalApi } from '@/api/portal'
import RequestDetailDrawer from './RequestDetailDrawer.vue'

const router = useRouter()

const activeTab = ref('all')
const loading = ref(false)
const requests = ref([])
const summary = ref({})
const detailVisible = ref(false)
const currentRequestType = ref('')
const currentRequestId = ref<number | null>(null)

const filters = reactive({
  type: '',
  keyword: ''
})

const pagination = reactive({
  page: 1,
  page_size: 20,
  total: 0
})

const inProgressCount = computed(() => {
  const s = summary.value.by_status || {}
  return (s.pending || 0) + (s.approved || 0) + (s.borrowed || 0)
})

const fetchData = async () => {
  loading.value = true
  try {
    const params: any = {
      page: pagination.page,
      page_size: pagination.page_size
    }

    if (activeTab.value !== 'all') {
      if (activeTab.value === 'in_progress') {
        params.status = ['pending', 'approved', 'borrowed']
      } else {
        params.status = activeTab.value
      }
    }

    if (filters.type) params.type = filters.type
    if (filters.keyword) params.keyword = filters.keyword

    const { data } = await portalApi.getMyRequests(params)
    requests.value = data.items
    summary.value = data.summary
    pagination.total = data.total
  } finally {
    loading.value = false
  }
}

const handleTabChange = () => {
  pagination.page = 1
  fetchData()
}

const handleViewDetail = (row: any) => {
  const [type, id] = row.id.split('_')
  currentRequestType.value = type
  currentRequestId.value = parseInt(id)
  detailVisible.value = true
}

const handleEdit = (row: any) => {
  const [type, id] = row.id.split('_')
  router.push({
    name: getRequestRouteName(type),
    params: { id }
  })
}

const handleAction = async (command: string, row: any) => {
  const [type, id] = row.id.split('_')

  if (command === 'cancel') {
    try {
      await ElMessageBox.confirm('确认取消此申请？', '提示')
      await portalApi.cancelRequest(type, parseInt(id))
      ElMessage.success('申请已取消')
      fetchData()
    } catch {
      // 用户取消
    }
  } else if (command === 'withdraw') {
    try {
      await ElMessageBox.confirm('确认撤回此申请？', '提示')
      await portalApi.withdrawRequest(type, parseInt(id))
      ElMessage.success('申请已撤回')
      fetchData()
    } catch {
      // 用户取消
    }
  }
}

const getTypeColor = (type: string) => {
  const colors = {
    'pickup': 'primary',
    'loan': 'warning',
    'transfer': 'success',
    'return': 'info',
    'consumable_issue': '',
    'consumable_purchase': ''
  }
  return colors[type] || ''
}

const getStatusColor = (status: string) => {
  const colors = {
    'draft': 'info',
    'pending': 'warning',
    'approved': 'success',
    'rejected': 'danger',
    'completed': '',
    'cancelled': 'info'
  }
  return colors[status] || ''
}

const formatDateTime = (datetime: string) => {
  return new Date(datetime).toLocaleString('zh-CN')
}

const getRequestRouteName = (type: string) => {
  const routes = {
    'pickup': 'AssetPickupDetail',
    'loan': 'AssetLoanDetail',
    'transfer': 'AssetTransferDetail',
    'return': 'AssetReturnDetail',
    'consumable_issue': 'ConsumableIssueDetail',
    'consumable_purchase': 'ConsumablePurchaseDetail'
  }
  return routes[type] || 'RequestDetail'
}

onMounted(() => {
  fetchData()
})
</script>

<style scoped>
.request-list {
  padding: 16px;
}

.type-filters {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.tab-label {
  display: flex;
  align-items: center;
  gap: 8px;
}
</style>
```

---

## 4. 移动端页面

### 4.1 移动端首页

```vue
<!-- src/views/portal/mobile/MobileHome.vue -->

<template>
  <div class="mobile-home">
    <!-- 头部 -->
    <div class="mobile-header">
      <div class="user-section">
        <el-avatar :size="48" :src="overview.user?.avatar">
          {{ overview.user?.real_name?.charAt(0) }}
        </el-avatar>
        <div class="user-info">
          <div class="user-name">{{ overview.user?.real_name }}</div>
          <div class="user-dept">{{ overview.user?.primary_department?.name }}</div>
        </div>
        <el-button link @click="goTo('/portal/profile')">
          <el-icon :size="20"><Setting /></el-icon>
        </el-button>
      </div>

      <!-- 统计卡片 -->
      <div class="stats-row">
        <div class="stat-card" @click="goTo('/portal/my-assets')">
          <div class="stat-value">{{ overview.summary?.assets_count || 0 }}</div>
          <div class="stat-label">我的资产</div>
        </div>
        <div class="stat-card" @click="goTo('/portal/my-tasks')">
          <div class="stat-value">{{ overview.summary?.tasks_count || 0 }}</div>
          <div class="stat-label">待办</div>
        </div>
        <div class="stat-card" @click="goTo('/portal/my-requests')">
          <div class="stat-value">{{ overview.summary?.notifications_count || 0 }}</div>
          <div class="stat-label">消息</div>
        </div>
      </div>
    </div>

    <!-- 快捷操作 -->
    <div class="quick-actions-grid">
      <div
        v-for="action in quickActions"
        :key="action.id"
        class="quick-action-btn"
        :style="{ background: action.color }"
        @click="handleQuickAction(action)"
      >
        <el-icon :size="28" color="white">
          <component :is="getActionIcon(action.icon)" />
        </el-icon>
        <span>{{ action.name }}</span>
      </div>
    </div>

    <!-- 待办事项 -->
    <div v-if="pendingTasks.length" class="section">
      <div class="section-header">
        <span class="section-title">待办事项</span>
        <el-link type="primary" @click="goTo('/portal/my-tasks')">全部</el-link>
      </div>
      <div class="task-list">
        <div
          v-for="task in pendingTasks"
          :key="task.id"
          class="task-item"
          :class="{ 'urgent': task.priority === 'urgent' }"
          @click="handleTask(task)"
        >
          <div class="task-icon">
            <el-icon :size="20">
              <component :is="getTaskIcon(task.task_type)" />
            </el-icon>
          </div>
          <div class="task-content">
            <div class="task-title">{{ task.title }}</div>
            <div class="task-desc">{{ task.description }}</div>
          </div>
          <el-icon class="task-arrow"><ArrowRight /></el-icon>
        </div>
      </div>
    </div>

    <!-- 最近资产 -->
    <div class="section">
      <div class="section-header">
        <span class="section-title">我的资产</span>
        <el-link type="primary" @click="goTo('/portal/my-assets')">全部</el-link>
      </div>
      <div class="asset-scroll">
        <div
          v-for="asset in recentAssets"
          :key="asset.id"
          class="asset-scroll-item"
          @click="goToAsset(asset.id)"
        >
          <el-image :src="asset.image" fit="cover" />
          <div class="asset-info">
            <div class="asset-name">{{ asset.asset_name }}</div>
            <el-tag size="small" type="success">{{ asset.relation_label }}</el-tag>
          </div>
        </div>
      </div>
    </div>

    <!-- 底部导航 -->
    <MobileTabBar active="home" />
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { Setting, ArrowRight } from '@element-plus/icons-vue'
import { portalApi } from '@/api/portal'
import MobileTabBar from '@/components/portal/mobile/MobileTabBar.vue'

const router = useRouter()

const overview = ref({
  user: null,
  summary: null,
  tasks: null,
  quick_actions: []
})

const pendingTasks = ref([])
const recentAssets = ref([])

const quickActions = ref([
  { id: 'scan', name: '扫码', icon: 'qr-scan', color: '#409EFF' },
  { id: 'my_assets', name: '我的资产', icon: 'box', color: '#67C23A' },
  { id: 'apply_pickup', name: '领用', icon: 'shopping-cart', color: '#E6A23C' },
  { id: 'apply_loan', name: '借用', icon: 'hand-holding', color: '#909399' }
])

const fetchData = async () => {
  const { data } = await portalApi.getMobileHome()
  overview.value = data
  pendingTasks.value = data.tasks?.items?.slice(0, 3) || []
  recentAssets.value = data.recent_assets || []
}

const goTo = (path: string) => {
  router.push(path)
}

const goToAsset = (id: number) => {
  router.push(`/portal/mobile/assets/${id}`)
}

const handleQuickAction = (action: any) => {
  if (action.id === 'scan') {
    router.push('/portal/scan')
  } else if (action.id === 'my_assets') {
    router.push('/portal/my-assets')
  } else if (action.id === 'apply_pickup') {
    router.push('/assets/pickups/create')
  } else if (action.id === 'apply_loan') {
    router.push('/assets/loans/create')
  }
}

const handleTask = (task: any) => {
  router.push(task.action_url)
}

const getActionIcon = (iconName: string) => {
  // 返回对应图标组件
  return Setting
}

const getTaskIcon = (type: string) => {
  // 根据任务类型返回图标
  return Setting
}

onMounted(() => {
  fetchData()
})
</script>

<style scoped>
.mobile-home {
  min-height: 100vh;
  background: #f5f7fa;
  padding-bottom: 60px;
}

.mobile-header {
  background: linear-gradient(135deg, #409eff 0%, #3a8ee6 100%);
  color: white;
  padding: 20px 16px;
  border-radius: 0 0 20px 20px;
}

.user-section {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 20px;
}

.user-info {
  flex: 1;
}

.user-name {
  font-size: 18px;
  font-weight: 500;
}

.user-dept {
  font-size: 14px;
  opacity: 0.9;
}

.stats-row {
  display: flex;
  gap: 12px;
}

.stat-card {
  flex: 1;
  background: rgba(255, 255, 255, 0.2);
  border-radius: 12px;
  padding: 12px;
  text-align: center;
}

.stat-value {
  font-size: 24px;
  font-weight: bold;
}

.stat-label {
  font-size: 12px;
  opacity: 0.9;
  margin-top: 4px;
}

.quick-actions-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 12px;
  padding: 16px;
}

.quick-action-btn {
  background: white;
  border-radius: 12px;
  padding: 16px 8px;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
  cursor: pointer;
}

.quick-action-btn span {
  font-size: 12px;
  color: white;
}

.section {
  padding: 16px;
}

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}

.section-title {
  font-size: 16px;
  font-weight: 500;
}

.task-list {
  background: white;
  border-radius: 12px;
  overflow: hidden;
}

.task-item {
  display: flex;
  align-items: center;
  padding: 16px;
  border-bottom: 1px solid #f5f7fa;
}

.task-item:last-child {
  border-bottom: none;
}

.task-item.urgent {
  background: #fef0f0;
}

.task-icon {
  width: 40px;
  height: 40px;
  border-radius: 10px;
  background: #ecf5ff;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #409eff;
}

.task-content {
  flex: 1;
  margin-left: 12px;
}

.task-title {
  font-size: 14px;
  font-weight: 500;
}

.task-desc {
  font-size: 12px;
  color: #909399;
  margin-top: 4px;
}

.task-arrow {
  color: #c0c4cc;
}

.asset-scroll {
  display: flex;
  gap: 12px;
  overflow-x: auto;
  padding-bottom: 8px;
}

.asset-scroll-item {
  flex-shrink: 0;
  width: 120px;
  background: white;
  border-radius: 12px;
  overflow: hidden;
  cursor: pointer;
}

.asset-scroll-item :deep(.el-image) {
  width: 120px;
  height: 90px;
}

.asset-info {
  padding: 8px;
}

.asset-name {
  font-size: 12px;
  font-weight: 500;
  margin-bottom: 4px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
</style>
```

### 4.2 底部导航组件

```vue
<!-- src/components/portal/mobile/MobileTabBar.vue -->

<template>
  <div class="mobile-tab-bar">
    <div
      v-for="tab in tabs"
      :key="tab.name"
      class="tab-item"
      :class="{ 'active': active === tab.name }"
      @click="$emit('navigate', tab.name)"
    >
      <el-badge
        v-if="tab.badge"
        :value="tab.badge"
        :max="99"
        class="tab-badge"
      >
        <el-icon :size="24">
          <component :is="getTabIcon(tab.icon)" />
        </el-icon>
      </el-badge>
      <el-icon v-else :size="24">
        <component :is="getTabIcon(tab.icon)" />
      </el-icon>
      <span class="tab-label">{{ tab.label }}</span>
    </div>
  </div>
</template>

<script setup lang="ts">
import { Home, Box, Document, Bell, User } from '@element-plus/icons-vue'

interface Props {
  active?: string
}

defineProps<Props>()

defineEmits<{
  navigate: [name: string]
}>()

const tabs = [
  { name: 'home', label: '首页', icon: 'home' },
  { name: 'assets', label: '资产', icon: 'box' },
  { name: 'requests', label: '申请', icon: 'document' },
  { name: 'tasks', label: '待办', icon: 'bell' },
  { name: 'profile', label: '我的', icon: 'user' }
]

const icons = {
  'home': Home,
  'box': Box,
  'document': Document,
  'bell': Bell,
  'user': User
}

const getTabIcon = (iconName: string) => {
  return icons[iconName] || Home
}
</script>

<style scoped>
.mobile-tab-bar {
  position: fixed;
  bottom: 0;
  left: 0;
  right: 0;
  display: flex;
  background: white;
  border-top: 1px solid #e4e7ed;
  padding-bottom: env(safe-area-inset-bottom);
  z-index: 100;
}

.tab-item {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 8px 0;
  color: #909399;
  cursor: pointer;
  transition: color 0.3s;
}

.tab-item.active {
  color: #409eff;
}

.tab-label {
  font-size: 12px;
  margin-top: 4px;
}

.tab-badge {
  position: relative;
}
</style>
```

---

## 5. API 封装

```typescript
// src/api/portal/index.ts

import request from '@/utils/request'

/**
 * 用户门户 API
 */
export const portalApi = {
  /**
   * 获取门户首页概览
   */
  getOverview() {
    return request.get('/portal/overview/')
  },

  /**
   * 获取移动端首页
   */
  getMobileHome() {
    return request.get('/portal/mobile/home/')
  },

  /**
   * 获取我的资产列表
   */
  getMyAssets(params?: {
    relation?: string
    status?: string
    category?: number
    keyword?: string
    page?: number
    page_size?: number
  }) {
    return request.get('/portal/my-assets/', { params })
  },

  /**
   * 获取资产详情
   */
  getAssetDetail(id: number) {
    return request.get(`/portal/my-assets/${id}/`)
  },

  /**
   * 获取资产汇总
   */
  getAssetSummary() {
    return request.get('/portal/my-assets/summary/')
  },

  /**
   * 获取我的申请列表
   */
  getMyRequests(params?: {
    status?: string | string[]
    type?: string
    keyword?: string
    page?: number
    page_size?: number
  }) {
    return request.get('/portal/my-requests/', { params })
  },

  /**
   * 获取申请详情
   */
  getRequestDetail(type: string, id: number) {
    return request.get(`/portal/my-requests/${type}/${id}/`)
  },

  /**
   * 取消申请
   */
  cancelRequest(type: string, id: number) {
    return request.post(`/portal/my-requests/${type}/${id}/cancel/`)
  },

  /**
   * 撤回申请
   */
  withdrawRequest(type: string, id: number) {
    return request.post(`/portal/my-requests/${type}/${id}/withdraw/`)
  },

  /**
   * 获取我的待办列表
   */
  getMyTasks(params?: {
    task_type?: string
    priority?: string
    status?: string
    page?: number
    page_size?: number
  }) {
    return request.get('/portal/my-tasks/', { params })
  },

  /**
   * 获取待办汇总
   */
  getTaskSummary() {
    return request.get('/portal/my-tasks/summary/')
  },

  /**
   * 快速处理待办
   */
  quickCompleteTask(id: string, data: { action: string; comment?: string }) {
    return request.post(`/portal/my-tasks/${id}/quick-action/`, data)
  },

  /**
   * 获取个人信息
   */
  getProfile() {
    return request.get('/portal/profile/')
  },

  /**
   * 更新个人信息
   */
  updateProfile(data: any) {
    return request.put('/portal/profile/', data)
  },

  /**
   * 切换主部门
   */
  switchDepartment(departmentId: number) {
    return request.post('/portal/profile/switch-department/', {
      department_id: departmentId
    })
  },

  /**
   * 执行快捷操作
   */
  executeQuickAction(action: string, params?: any) {
    return request.post('/portal/quick-actions/', { action, params })
  },

  /**
   * 扫码解析
   */
  scanQRCode(qrData: string) {
    return request.post('/portal/mobile/scan/', { qr_data: qrData })
  }
}
```

---

## 6. 路由配置

```typescript
// src/router/modules/portal.ts

export default {
  path: '/portal',
  name: 'Portal',
  component: () => import('@/layouts/MainLayout.vue'),
  meta: { title: '用户门户', icon: 'Home' },
  redirect: '/portal/home',
  children: [
    {
      path: 'home',
      name: 'PortalHome',
      component: () => import('@/views/portal/PortalHome.vue'),
      meta: { title: '门户首页' }
    },
    {
      path: 'my-assets',
      name: 'MyAssets',
      component: () => import('@/views/portal/MyAssets/AssetList.vue'),
      meta: { title: '我的资产' }
    },
    {
      path: 'my-assets/:id',
      name: 'AssetDetail',
      component: () => import('@/views/portal/MyAssets/AssetDetail.vue'),
      meta: { title: '资产详情' }
    },
    {
      path: 'my-requests',
      name: 'MyRequests',
      component: () => import('@/views/portal/MyRequests/RequestList.vue'),
      meta: { title: '我的申请' }
    },
    {
      path: 'my-tasks',
      name: 'MyTasks',
      component: () => import('@/views/portal/MyTasks/TaskCenter.vue'),
      meta: { title: '我的待办' }
    },
    {
      path: 'profile',
      name: 'Profile',
      component: () => import('@/views/portal/Profile/ProfileIndex.vue'),
      meta: { title: '个人中心' }
    },
    // 移动端路由
    {
      path: 'mobile',
      children: [
        {
          path: 'home',
          name: 'MobileHome',
          component: () => import('@/views/portal/mobile/MobileHome.vue'),
          meta: { title: '首页', mobile: true }
        },
        {
          path: 'scan',
          name: 'MobileScan',
          component: () => import('@/views/portal/mobile/ScanPage.vue'),
          meta: { title: '扫码', mobile: true }
        }
      ]
    }
  ]
}
```

---

## 7. 响应式布局

```css
/* 移动端适配 */
@media (max-width: 768px) {
  .portal-home {
    padding: 8px;
  }

  .quick-actions {
    grid-template-columns: repeat(2, 1fr);
  }

  .action-item-scan {
    grid-column: span 2;
  }

  .el-table {
    font-size: 12px;
  }

  .el-pagination {
    justify-content: center;
  }
}

/* 平板适配 */
@media (min-width: 768px) and (max-width: 1024px) {
  .quick-actions {
    grid-template-columns: repeat(4, 1fr);
  }
}
```
