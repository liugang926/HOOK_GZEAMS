# Phase 4.2: RFID批量盘点 - 前端实现

## 概述

RFID批量盘点功能允许用户使用RFID读取器批量读取资产标签，快速完成盘点任务。本文档描述PC端管理界面和移动端RFID盘点界面的前端实现。

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
src/views/inventory/
├── rfid/
│   ├── RfidTaskList.vue          # RFID盘点任务列表
│   ├── RfidTaskDetail.vue        # RFID盘点任务详情
│   └── components/
│       ├── RfidReaderStatus.vue   # RFID读取器状态
│       ├── RfidScanProgress.vue    # RFID扫描进度
│       └── TagList.vue             # 标签列表
└── mobile/
    └── rfid/
        ├── RfidScanPage.vue       # RFID扫描页面
        └── RfidResultList.vue      # RFID结果列表
```

---

## 1. PC端任务列表

### 1.1 RFID任务列表页面

```vue
<!-- src/views/inventory/rfid/RfidTaskList.vue -->

<template>
  <div class="rfid-task-list">
    <el-page-header @back="goBack" title="RFID批量盘点">
      <template #extra>
        <el-button type="primary" :icon="Plus" @click="handleCreate">
          创建RFID任务
        </el-button>
      </template>
    </el-page-header>

    <!-- 筛选条件 -->
    <el-card class="filter-card">
      <el-form :model="filterForm" inline>
        <el-form-item label="任务状态">
          <el-select v-model="filterForm.status" clearable @change="fetchData">
            <el-option label="全部" value="" />
            <el-option label="待执行" value="pending" />
            <el-option label="进行中" value="in_progress" />
            <el-option label="已完成" value="completed" />
          </el-select>
        </el-form-item>
        <el-form-item label="关键词">
          <el-input
            v-model="filterForm.search"
            placeholder="任务名称/编号"
            clearable
            @keyup.enter="fetchData"
          >
            <template #append>
              <el-button :icon="Search" @click="fetchData" />
            </template>
          </el-input>
        </el-form-item>
      </el-form>
    </el-card>

    <!-- 任务列表 -->
    <el-table v-loading="loading" :data="tableData" @row-click="handleViewDetail">
      <el-table-column prop="task_no" label="任务编号" width="150" />
      <el-table-column prop="task_name" label="任务名称" min-width="180" />
      <el-table-column label="盘点范围" width="200">
        <template #default="{ row }">
          {{ row.location?.name }} ({{ row.asset_count }}项)
        </template>
      </el-table-column>
      <el-table-column label="RFID设备" width="150">
        <template #default="{ row }">
          {{ row.rfid_device?.name || '未指定' }}
        </template>
      </el-table-column>
      <el-table-column label="进度" width="150">
        <template #default="{ row }">
          <el-progress
            :percentage="getProgress(row)"
            :format="() => `${row.scanned_count}/${row.asset_count}`"
          />
        </template>
      </el-table-column>
      <el-table-column prop="status" label="状态" width="100">
        <template #default="{ row }">
          <el-tag :type="getStatusType(row.status)">
            {{ getStatusLabel(row.status) }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="planned_date" label="计划日期" width="110" />
      <el-table-column label="操作" width="200" fixed="right">
        <template #default="{ row }">
          <el-button link type="primary" @click.stop="handleViewDetail(row)">
            详情
          </el-button>
          <el-button
            v-if="row.status === 'pending'"
            link
            type="primary"
            @click.stop="handleStart(row)"
          >
            开始盘点
          </el-button>
          <el-dropdown v-if="row.status === 'in_progress'" @command="cmd => handleCommand(cmd, row)">
            <el-button link type="primary">
              更多<el-icon class="el-icon--right"><ArrowDown /></el-icon>
            </el-button>
            <template #dropdown>
              <el-dropdown-menu>
                <el-dropdown-item command="pause">暂停</el-dropdown-item>
                <el-dropdown-item command="sync">同步数据</el-dropdown-item>
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
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { Plus, Search, ArrowDown } from '@element-plus/icons-vue'
import { rfidTaskApi } from '@/api/inventory/rfid'

const router = useRouter()
const loading = ref(false)
const tableData = ref([])

const filterForm = reactive({
  status: '',
  search: ''
})

const pagination = reactive({
  page: 1,
  page_size: 20,
  total: 0
})

const fetchData = async () => {
  loading.value = true
  try {
    const { data } = await rfidTaskApi.getList({
      ...filterForm,
      ...pagination
    })
    tableData.value = data.items
    pagination.total = data.total
  } finally {
    loading.value = false
  }
}

const handleCreate = () => {
  router.push('/inventory/rfid/create')
}

const handleViewDetail = (row: any) => {
  router.push(`/inventory/rfid/${row.id}`)
}

const handleStart = async (row: any) => {
  await rfidTaskApi.start(row.id)
  fetchData()
}

const handleCommand = async (command: string, row: any) => {
  switch (command) {
    case 'pause':
      await rfidTaskApi.pause(row.id)
      break
    case 'sync':
      await rfidTaskApi.sync(row.id)
      break
  }
  fetchData()
}

const getProgress = (row: any) => {
  return row.asset_count > 0 ? Math.round((row.scanned_count / row.asset_count) * 100) : 0
}

const getStatusType = (status: string) => {
  const types = { pending: 'info', in_progress: 'warning', completed: 'success' }
  return types[status] || 'info'
}

const getStatusLabel = (status: string) => {
  const labels = { pending: '待执行', in_progress: '进行中', completed: '已完成' }
  return labels[status] || status
}

const goBack = () => {
  router.back()
}

onMounted(() => {
  fetchData()
})
</script>

<style scoped>
.rfid-task-list {
  padding: 20px;
}

.filter-card {
  margin-bottom: 20px;
}
</style>
```

---

## 2. PC端任务详情

### 2.1 RFID任务详情页面

```vue
<!-- src/views/inventory/rfid/RfidTaskDetail.vue -->

<template>
  <div class="rfid-task-detail">
    <el-page-header @back="goBack" :title="task.task_name">
      <template #extra>
        <el-button v-if="task.status === 'pending'" type="primary" @click="handleStart">
          开始盘点
        </el-button>
        <el-button v-if="task.status === 'in_progress'" type="warning" @click="handlePause">
          暂停盘点
        </el-button>
        <el-button v-if="task.status === 'in_progress'" type="success" @click="handleComplete">
          完成盘点
        </el-button>
      </template>
    </el-page-header>

    <!-- 任务基本信息 -->
    <el-card class="mb-16">
      <template #header>
        <span class="card-title">任务信息</span>
      </template>
      <el-descriptions :column="2" border>
        <el-descriptions-item label="任务编号">
          {{ task.task_no }}
        </el-descriptions-item>
        <el-descriptions-item label="任务状态">
          <el-tag :type="getStatusType(task.status)">
            {{ getStatusLabel(task.status) }}
          </el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="盘点地点">
          {{ task.location?.name }}
        </el-descriptions-item>
        <el-descriptions-item label="资产总数">
          {{ task.asset_count }}
        </el-descriptions-item>
        <el-descriptions-item label="已扫描">
          {{ task.scanned_count }}
        </el-descriptions-item>
        <el-descriptions-item label="RFID设备">
          {{ task.rfid_device?.name || '未指定' }}
        </el-descriptions-item>
        <el-descriptions-item label="计划日期">
          {{ task.planned_date }}
        </el-descriptions-item>
      </el-descriptions>
    </el-card>

    <!-- 扫描进度 -->
    <el-card v-if="task.status === 'in_progress'" class="mb-16">
      <template #header>
        <span class="card-title">扫描进度</span>
        <el-button type="text" @click="refreshProgress">刷新</el-button>
      </template>

      <el-row :gutter="16" class="mb-16">
        <el-col :span="8">
          <el-statistic title="总资产" :value="task.asset_count" />
        </el-col>
        <el-col :span="8">
          <el-statistic title="已扫描" :value="task.scanned_count" />
        </el-col>
        <el-col :span="8">
          <el-statistic title="异常" :value="task.abnormal_count" />
        </el-col>
      </el-row>

      <el-progress
        :percentage="getProgress(task)"
        :status="getProgress(task) === 100 ? 'success' : undefined"
      >
        <template #default="{ percentage }">
          {{ task.scanned_count }} / {{ task.asset_count }}
        </template>
      </el-progress>
    </el-card>

    <!-- 扫描结果列表 -->
    <el-card>
      <template #header>
        <span class="card-title">扫描结果</span>
        <el-space>
          <el-radio-group v-model="resultFilter" size="small" @change="fetchResults">
            <el-radio-button label="all">全部</el-radio-button>
            <el-radio-button label="scanned">已扫描</el-radio-button>
            <el-radio-button label="unscanned">未扫描</el-radio-button>
            <el-radio-button label="abnormal">异常</el-radio-button>
          </el-radio-group>
          <el-button type="primary" size="small" @click="exportResults">导出</el-button>
        </el-space>
      </template>

      <el-table v-loading="loading" :data="scanResults" @row-click="handleShowTag">
        <el-table-column label="资产编码" prop="asset_code" width="140" />
        <el-table-column label="资产名称" prop="asset_name" min-width="180" />
        <el-table-column label="RFID标签" prop="rfid_epc" width="160" />
        <el-table-column label="扫描状态" width="100">
          <template #default="{ row }">
            <el-tag v-if="row.scanned" type="success" size="small">已扫描</el-tag>
            <el-tag v-else type="info" size="small">未扫描</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="扫描时间" width="160">
          <template #default="{ row }">
            {{ row.scanned_at || '-' }}
          </template>
        </el-table-column>
        <el-table-column label="扫描结果" width="100">
          <template #default="{ row }">
            <el-tag v-if="!row.scanned" type="info" size="small">-</el-tag>
            <el-tag v-else-if="row.scan_result === 'normal'" type="success" size="small">正常</el-tag>
            <el-tag v-else type="danger" size="small">{{ getScanResultLabel(row.scan_result) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="备注" width="120">
          <template #default="{ row }">
            {{ row.remark || '-' }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="100" fixed="right">
          <template #default="{ row }">
            <el-button link type="primary" @click.stop="handleShowAsset(row)">
              查看
            </el-button>
          </template>
        </el-table-column>
      </el-table>

      <el-pagination
        v-model:current-page="pagination.page"
        v-model:page-size="pagination.page_size"
        :total="pagination.total"
        layout="total, sizes, prev, pager, next"
        @size-change="fetchResults"
        @current-change="fetchResults"
      />
    </el-card>

    <!-- 标签详情抽屉 -->
    <TagDetailDrawer
      v-model="tagDrawerVisible"
      :tag="currentTag"
      @refresh="fetchResults"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, computed } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { rfidTaskApi } from '@/api/inventory/rfid'
import TagDetailDrawer from './components/TagDetailDrawer.vue'

const router = useRouter()
const route = useRoute()

const loading = ref(false)
const task = ref({
  task_no: '',
  task_name: '',
  status: '',
  asset_count: 0,
  scanned_count: 0,
  abnormal_count: 0,
  location: null,
  rfid_device: null,
  planned_date: ''
})

const scanResults = ref([])
const resultFilter = ref('all')
const tagDrawerVisible = ref(false)
const currentTag = ref(null)

const pagination = reactive({
  page: 1,
  page_size: 20,
  total: 0
})

const getProgress = (task: any) => {
  return task.asset_count > 0 ? Math.round((task.scanned_count / task.asset_count) * 100) : 0
}

const getStatusType = (status: string) => {
  const types = { pending: 'info', in_progress: 'warning', completed: 'success' }
  return types[status] || 'info'
}

const getStatusLabel = (status: string) => {
  const labels = { pending: '待执行', in_progress: '进行中', completed: '已完成' }
  return labels[status] || status
}

const getScanResultLabel = (result: string) => {
  const labels = {
    normal: '正常',
    location_changed: '位置变更',
    damaged: '损坏',
    missing: '缺失',
    duplicate: '重复'
  }
  return labels[result] || result
}

const fetchResults = async () => {
  loading.value = true
  try {
    const { data } = await rfidTaskApi.getScanResults(route.params.id, {
      filter: resultFilter.value,
      ...pagination
    })
    scanResults.value = data.items
    pagination.total = data.total
  } finally {
    loading.value = false
  }
}

const handleShowTag = (row: any) => {
  currentTag.value = row
  tagDrawerVisible.value = true
}

const goBack = () => {
  router.back()
}

onMounted(async () => {
  // 获取任务详情
  const { data } = await rfidTaskApi.getDetail(route.params.id)
  task.value = data

  // 如果任务进行中，加载扫描结果
  if (data.status === 'in_progress') {
    await fetchResults()
  }
})
</script>

<style scoped>
.rfid-task-detail {
  padding: 20px;
}

.mb-16 {
  margin-bottom: 16px;
}

.card-title {
  font-size: 16px;
  font-weight: 500;
}
</style>
```

---

## 3. 移动端RFID扫描

### 3.1 RFID扫描页面

```vue
<!-- src/views/inventory/mobile/rfid/RfidScanPage.vue -->

<template>
  <div class="rfid-scan-page">
    <van-nav-bar
      :title="task.task_name"
      left-text="返回"
      @click-left="goBack"
    >
      <template #right>
        <van-icon :name="isScanning ? 'pause' : 'play'" @click="toggleScan" />
      </template>
    </van-nav-bar>

    <!-- RFID设备状态 -->
    <RfidReaderStatus
      :device="rfidDevice"
      :connected="deviceConnected"
      :battery="batteryLevel"
    />

    <!-- 扫描进度 -->
    <div class="scan-progress">
      <div class="progress-info">
        <span class="scanned">{{ task.scanned_count }}</span>
        <span class="separator">/</span>
        <span class="total">{{ task.asset_count }}</span>
        <span class="percentage">({{ getProgress(task) }}%)</span>
      </div>
      <van-progress
        :percentage="getProgress(task)"
        :color="getProgress(task) === 100 ? '#52c41a' : '#1989fa'"
      />
    </div>

    <!-- 最近扫描标签 -->
    <div class="recent-tags">
      <div class="section-title">
        最近扫描 ({{ recentTags.length }})
      </div>
      <div v-if="recentTags.length === 0" class="empty-state">
        <van-empty description="暂无扫描记录" />
      </div>
      <div v-else class="tag-list">
        <div
          v-for="tag in recentTags"
          :key="tag.id"
          class="tag-item"
          @click="handleShowTag(tag)"
        >
          <div class="tag-info">
            <span class="tag-epc">{{ tag.rfid_epc }}</span>
            <span class="tag-name">{{ tag.asset_name }}</span>
          </div>
          <van-tag :type="getScanResultType(tag)">
            {{ getScanResultLabel(tag) }}
          </van-tag>
        </div>
      </div>
    </div>

    <!-- 扫描控制 -->
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
        v-if="getProgress(task) >= 100"
        type="success"
        block
        @click="handleComplete"
      >
        完成盘点
      </van-button>
    </div>

    <!-- 标签详情弹窗 -->
    <van-popup
      v-model:show="tagDetailVisible"
      position="bottom"
      :style="{ height: '70%' }"
    >
      <TagDetail
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
import { rfidTaskApi } from '@/api/inventory/rfid'
import RfidReaderStatus from '@/components/inventory/rfid/RfidReaderStatus.vue'
import TagDetail from '@/components/inventory/rfid/TagDetail.vue'

const router = useRouter()
const route = useRoute()

const task = ref({
  id: route.params.id,
  task_name: '',
  asset_count: 0,
  scanned_count: 0,
  status: 'pending'
})

const isScanning = ref(false)
const deviceConnected = ref(false)
const batteryLevel = ref(100)
const rfidDevice = ref(null)
const recentTags = ref([])
const tagDetailVisible = ref(false)
const currentTag = ref(null)

let scanInterval: any = null

const getProgress = (task: any) => {
  return task.asset_count > 0 ? Math.round((task.scanned_count / task.asset_count) * 100) : 0
}

const getScanResultType = (tag: any) => {
  if (!tag.scanned) return 'default'
  if (tag.scan_result === 'normal') return 'success'
  return 'danger'
}

const getScanResultLabel = (tag: any) => {
  if (!tag.scanned) return '未扫描'
  if (tag.scan_result === 'normal') return '正常'
  if (tag.scan_result === 'location_changed') return '位置变更'
  if (tag.scan_result === 'damaged') return '损坏'
  if (tag.scan_result === 'missing') return '缺失'
  return '异常'
}

const startScan = async () => {
  try {
    await rfidTaskApi.startScan(task.value.id)
    isScanning.value = true
    startPolling()
  } catch (error) {
    showToast('启动扫描失败')
  }
}

const pauseScan = async () => {
  try {
    await rfidTaskApi.pauseScan(task.value.id)
    isScanning.value = false
    stopPolling()
  } catch (error) {
    showToast('暂停扫描失败')
  }
}

const startPolling = () => {
  // 定时获取扫描结果
  scanInterval = setInterval(async () => {
    try {
      const { data } = await rfidTaskApi.getRecentTags(task.value.id)
      recentTags.value = data.items
      task.value.scanned_count = data.scanned_count

      // 震动反馈
      if (navigator.vibrate && data.new_scanned > 0) {
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

const handleShowTag = (tag: any) => {
  currentTag.value = tag
  tagDetailVisible.value = true
}

const handleTagConfirm = async (result: any) => {
  try {
    await rfidTaskApi.confirmTag(task.value.id, currentTag.value.id, result)
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
  const { data } = await rfidTaskApi.getDetail(task.value.id)
  task.value = { ...task.value, ...data }
}

const fetchRecentTags = async () => {
  const { data } = await rfidTaskApi.getRecentTags(task.value.id)
  recentTags.value = data.items
}

onMounted(async () => {
  await fetchTaskDetail()

  // 如果任务正在扫描，自动开始扫描
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

## 4. RFID读取器状态组件

```vue
<!-- src/components/inventory/rfid/RfidReaderStatus.vue -->

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
        <div class="device-model" v-if="device">
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
          :class="{ 'low': batteryLevel < 20, 'medium': batteryLevel < 50 }"
          :style="{ width: batteryLevel + '%' }"
        />
      </div>
      <span class="battery-value">{{ batteryLevel }}%</span>
    </div>

    <div v-if="connected" class="signal-strength">
      <span class="signal-label">信号:</span>
      <div class="signal-bars">
        <div class="bar" :class="{ active: signalStrength >= 1 }"></div>
        <div class="bar" :class="{ active: signalStrength >= 2 }"></div>
        <div class="bar" :class="{ active: signalStrength >= 3 }"></div>
        <div class="bar" :class="{ active: signalStrength >= 4 }"></div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { Connection } from '@element-plus/icons-vue'

interface Props {
  device: any
  connected: boolean
  battery: number | null
  signalStrength?: number
}

const props = defineProps<Props>()
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

## 5. 标签详情组件

```vue
<!-- src/components/inventory/rfid/TagDetail.vue -->

<template>
  <div class="tag-detail">
    <van-nav-bar
      title="标签详情"
      left-text="关闭"
      @click-left="$emit('close')"
    />

    <van-cell-group>
      <van-cell title="RFID标签" :value="tag.rfid_epc" />
      <van-cell title="资产编码" :value="tag.asset_code" />
      <van-cell title="资产名称" :value="tag.asset_name" />
      <van-cell title="扫描时间" :value="tag.scanned_at || '未扫描'" />
    </van-cell-group>

    <van-cell-group title="扫描结果" inset>
      <van-radio-group v-model="selectedResult">
        <van-cell
          title="✓ 正常"
          clickable
          @click="selectedResult = 'normal'"
        >
          <template #right-icon>
            <van-radio name="normal" />
          </template>
        </van-cell>
        <van-cell
          title="📍 位置变更"
          clickable
          @click="selectedResult = 'location_changed'"
        >
          <template #right-icon>
            <van-radio name="location_changed" />
          </template>
        </van-cell>
        <van-cell
          title="🔧 损坏"
          clickable
          @click="selectedResult = 'damaged'"
        >
          <template #right-icon>
            <van-radio name="damaged" />
          </template>
        </van-cell>
        <van-cell
          title="❓ 缺失"
          clickable
          @click="selectedResult = 'missing'"
        >
          <template #right-icon>
            <van-radio name="missing" />
          </template>
        </van-cell>
      </van-radio-group>
    </van-cell-group>

    <van-cell-group title="备注信息" inset>
      <van-field
        v-model="remark"
        type="textarea"
        placeholder="请输入备注信息"
        rows="3"
      />
    </van-cell-group>

    <div class="action-buttons">
      <van-button block type="primary" @click="handleConfirm">
        确认
      </van-button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'

interface Props {
  tag: any
  task: any
}

const props = defineProps<Props>()
const emit = defineEmits(['confirm', 'close'])

const selectedResult = ref('normal')
const remark = ref('')

const handleConfirm = () => {
  emit('confirm', {
    tag_id: props.tag.id,
    scan_result: selectedResult.value,
    remark: remark.value
  })
}
</script>

<style scoped>
.tag-detail {
  height: 100%;
}

.action-buttons {
  padding: 16px;
}
</style>
```

---

## 6. API封装

```typescript
// src/api/inventory/rfid.ts

import request from '@/utils/request'

export const rfidTaskApi = {
  // 获取RFID任务列表
  getList(params?: any) {
    return request.get('/api/inventory/rfid/tasks/', { params })
  },

  // 获取任务详情
  getDetail(id: string | number) {
    return request.get(`/api/inventory/rfid/tasks/${id}/`)
  },

  // 创建RFID任务
  create(data: any) {
    return request.post('/api/inventory/rfid/tasks/', data)
  },

  // 更新任务
  update(id: string | number, data: any) {
    return request.put(`/api/inventory/rfid/tasks/${id}/`, data)
  },

  // 开始盘点
  start(id: string | number) {
    return request.post(`/api/inventory/rfid/tasks/${id}/start/`)
  },

  // 暂停盘点
  pause(id: string | number) {
    return request.post(`/api/inventory/rfid/tasks/${id}/pause/`)
  },

  // 开始扫描
  startScan(id: string | number) {
    return request.post(`/api/inventory/rfid/tasks/${id}/scan-start/`)
  },

  // 暂停扫描
  pauseScan(id: string | number) {
    return request.post(`/api/inventory/rfid/tasks/${id}/scan-stop/`)
  },

  // 获取最近扫描的标签
  getRecentTags(id: string | number) {
    return request.get(`/api/inventory/rfid/tasks/${id}/recent-tags/`)
  },

  // 确认标签扫描结果
  confirmTag(taskId: string | number, tagId: string | number, data: any) {
    return request.post(`/api/inventory/rfid/tasks/${taskId}/tags/${tagId}/confirm/`, data)
  },

  // 获取扫描结果列表
  getScanResults(id: string | number, params?: any) {
    return request.get(`/api/inventory/rfid/tasks/${id}/scan-results/`, { params })
  },

  // 同步数据
  sync(id: string | number) {
    return request.post(`/api/inventory/rfid/tasks/${id}/sync/`)
  },

  // 完成盘点
  complete(id: string | number, data?: any) {
    return request.post(`/api/inventory/rfid/tasks/${id}/complete/`, data)
  }
}
```

---

## 7. 移动端路由配置

```typescript
// src/router/modules/inventory.ts

export default {
  path: '/inventory',
  component: () => import('@/layouts/MobileLayout.vue'),
  children: [
    {
      path: 'rfid',
      children: [
        {
          path: '',
          name: 'RfidTaskList',
          component: () => import('@/views/inventory/mobile/rfid/RfidTaskList.vue')
        },
        {
          path: ':id',
          name: 'RfidScanPage',
          component: () => import('@/views/inventory/mobile/rfid/RfidScanPage.vue')
        },
        {
          path: ':id/complete',
          name: 'RfidComplete',
          component: () => import('@/views/inventory/mobile/rfid/RfidComplete.vue')
        }
      ]
    }
  ]
}
```
