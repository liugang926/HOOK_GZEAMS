# Phase 2.2: 企业微信通讯录同步 - 前端实现

## 组件结构

```
src/views/admin/
├── SyncManagement.vue           # 同步管理主页面
└── components/
    ├── SyncStatus.vue           # 同步状态卡片
    ├── SyncStats.vue            # 同步统计展示
    └── SyncLogs.vue             # 同步日志列表
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

## 1. 同步管理主页面

### SyncManagement.vue

```vue
<template>
  <div class="sync-management">
    <el-row :gutter="20">
      <!-- 左侧：同步状态和操作 -->
      <el-col :span="8">
        <SyncStatus
          :status="syncStatus"
          :loading="statusLoading"
          @refresh="fetchSyncStatus"
          @sync="handleSync"
        />
      </el-col>

      <!-- 右侧：同步统计 -->
      <el-col :span="16">
        <SyncStats :stats="syncStats" :logs="recentLogs" />
      </el-col>
    </el-row>

    <!-- 底部：同步日志列表 -->
    <el-row style="margin-top: 20px">
      <el-col :span="24">
        <SyncLogs
          :logs="syncLogs"
          :loading="logsLoading"
          @refresh="fetchSyncLogs"
        />
      </el-col>
    </el-row>

    <!-- 同步进度弹窗 -->
    <SyncProgressDialog
      v-model:visible="showProgressDialog"
      :log-id="currentLogId"
      @finished="handleSyncFinished"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue'
import { ElMessage } from 'element-plus'
import SyncStatus from './components/SyncStatus.vue'
import SyncStats from './components/SyncStats.vue'
import SyncLogs from './components/SyncLogs.vue'
import SyncProgressDialog from './components/SyncProgressDialog.vue'
import { getSyncStatus, getSyncLogs, triggerSync } from '@/api/sso'

// 同步状态
const syncStatus = ref({
  enabled: false,
  status: 'never_synced',
  lastSyncTime: null as Date | null,
  corpName: ''
})
const statusLoading = ref(false)

// 同步统计
const syncStats = ref({
  total: 0,
  created: 0,
  updated: 0,
  deleted: 0,
  failed: 0
})

// 同步日志
const syncLogs = ref([])
const recentLogs = ref([])
const logsLoading = ref(false)

// 进度弹窗
const showProgressDialog = ref(false)
const currentLogId = ref<number | null>(null)

// 定时刷新
let refreshTimer: number | null = null

// 获取同步状态
const fetchSyncStatus = async () => {
  statusLoading.value = true
  try {
    const res = await getSyncStatus()
    syncStatus.value = res

    // 更新统计
    if (res.stats) {
      syncStats.value = res.stats
    }
  } catch (error) {
    console.error('获取同步状态失败', error)
  } finally {
    statusLoading.value = false
  }
}

// 获取同步日志
const fetchSyncLogs = async () => {
  logsLoading.value = true
  try {
    const logs = await getSyncLogs()
    syncLogs.value = logs

    // 最近5条用于统计卡片
    recentLogs.value = logs.slice(0, 5)
  } catch (error) {
    console.error('获取同步日志失败', error)
  } finally {
    logsLoading.value = false
  }
}

// 触发同步
const handleSync = async (syncType: string = 'full') => {
  try {
    const res = await triggerSync({ sync_type: syncType })
    ElMessage.success('同步任务已启动')

    // 显示进度弹窗
    showProgressDialog.value = true

    // 开始轮询状态
    startPolling()
  } catch (error: any) {
    ElMessage.error(error.response?.data?.error || '启动同步失败')
  }
}

// 同步完成
const handleSyncFinished = (log: any) => {
  showProgressDialog.value = false
  stopPolling()

  // 刷新状态和日志
  fetchSyncStatus()
  fetchSyncLogs()

  if (log.status === 'success') {
    ElMessage.success('同步完成')
  } else {
    ElMessage.error(`同步失败: ${log.error_message || '未知错误'}`)
  }
}

// 开始轮询
const startPolling = () => {
  stopPolling()
  refreshTimer = window.setInterval(() => {
    fetchSyncStatus()
    fetchSyncLogs()
  }, 3000) // 每3秒轮询
}

// 停止轮询
const stopPolling = () => {
  if (refreshTimer) {
    clearInterval(refreshTimer)
    refreshTimer = null
  }
}

onMounted(() => {
  fetchSyncStatus()
  fetchSyncLogs()
})

onUnmounted(() => {
  stopPolling()
})
</script>

<style scoped>
.sync-management {
  padding: 20px;
}
</style>
```

---

## 2. 同步状态组件

### SyncStatus.vue

```vue
<template>
  <el-card header="同步状态" shadow="hover">
    <template #extra>
      <el-button
        :icon="Refresh"
        circle
        :loading="loading"
        @click="$emit('refresh')"
      />
    </template>

    <div v-if="!status.enabled" class="not-configured">
      <el-empty description="企业微信未配置">
        <el-button type="primary" @click="goToConfig">
          前往配置
        </el-button>
      </el-empty>
    </div>

    <div v-else class="status-content">
      <!-- 状态指示 -->
      <div class="status-indicator">
        <el-tag :type="statusType" size="large" effect="dark">
          {{ statusLabel }}
        </el-tag>
      </div>

      <!-- 企业信息 -->
      <div v-if="status.corpName" class="corp-info">
        <el-text type="info">
          <el-icon><OfficeBuilding /></el-icon>
          {{ status.corpName }}
        </el-text>
      </div>

      <!-- 最后同步时间 -->
      <el-descriptions :column="1" border class="status-details">
        <el-descriptions-item label="最后同步时间">
          {{ formattedLastSyncTime }}
        </el-descriptions-item>
        <el-descriptions-item label="同步状态">
          <el-tag :type="statusType" size="small">
            {{ statusLabel }}
          </el-tag>
        </el-descriptions-item>
      </el-descriptions>

      <!-- 操作按钮 -->
      <div class="sync-actions">
        <el-button
          type="primary"
          :icon="Refresh"
          :loading="syncing"
          :disabled="status.status === 'running'"
          @click="handleFullSync"
        >
          {{ syncing ? '同步中...' : '立即同步' }}
        </el-button>

        <el-dropdown @command="handleSelectiveSync">
          <el-button :disabled="status.status === 'running'">
            选择性同步
            <el-icon class="el-icon--right"><ArrowDown /></el-icon>
          </el-button>
          <template #dropdown>
            <el-dropdown-menu>
              <el-dropdown-item command="department">
                <el-icon><FolderOpened /></el-icon>
                仅同步部门
              </el-dropdown-item>
              <el-dropdown-item command="user">
                <el-icon><User /></el-icon>
                仅同步用户
              </el-dropdown-item>
            </el-dropdown-menu>
          </template>
        </el-dropdown>
      </div>
    </div>
  </el-card>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue'
import { useRouter } from 'vue-router'
import {
  Refresh,
  ArrowDown,
  OfficeBuilding,
  FolderOpened,
  User
} from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'

interface Props {
  status: {
    enabled: boolean
    status: string
    lastSyncTime: Date | string | null
    corpName: string
  }
  loading?: boolean
}

interface Emits {
  (e: 'refresh'): void
  (e: 'sync', syncType: string): void
}

const props = defineProps<Props>()
const emit = defineEmits<Emits>()

const router = useRouter()
const syncing = ref(false)

const statusType = computed(() => {
  switch (props.status.status) {
    case 'success':
      return 'success'
    case 'failed':
      return 'danger'
    case 'running':
      return 'warning'
    default:
      return 'info'
  }
})

const statusLabel = computed(() => {
  switch (props.status.status) {
    case 'success':
      return '同步成功'
    case 'failed':
      return '同步失败'
    case 'running':
      return '同步中'
    case 'never_synced':
      return '从未同步'
    default:
      return '未知状态'
  }
})

const formattedLastSyncTime = computed(() => {
  if (!props.status.lastSyncTime) return '-'
  const date = new Date(props.status.lastSyncTime)
  return date.toLocaleString('zh-CN')
})

const handleFullSync = () => {
  syncing.value = true
  emit('sync', 'full')
  setTimeout(() => {
    syncing.value = false
  }, 1000)
}

const handleSelectiveSync = (command: string) => {
  emit('sync', command)
}

const goToConfig = () => {
  router.push('/admin/sso/wework')
}
</script>

<style scoped>
.not-configured {
  padding: 20px 0;
}

.status-content {
  padding: 10px 0;
}

.status-indicator {
  text-align: center;
  margin-bottom: 20px;
}

.corp-info {
  text-align: center;
  margin-bottom: 20px;
}

.status-details {
  margin-bottom: 20px;
}

.sync-actions {
  display: flex;
  gap: 10px;
  justify-content: center;
}
</style>
```

---

## 3. 同步统计组件

### SyncStats.vue

```vue
<template>
  <el-card header="同步统计" shadow="hover">
    <el-row :gutter="20">
      <!-- 统计卡片 -->
      <el-col :span="6" v-for="stat in stats" :key="stat.key">
        <el-statistic :title="stat.label" :value="stat.value">
          <template #suffix>
            <span :class="stat.color">{{ stat.suffix }}</span>
          </template>
          <template #prefix>
            <el-icon :size="20" :color="stat.iconColor">
              <component :is="stat.icon" />
            </el-icon>
          </template>
        </el-statistic>
      </el-col>
    </el-row>

    <!-- 最近同步趋势 -->
    <el-divider>最近同步趋势</el-divider>

    <div v-if="logs.length === 0" class="empty-trend">
      <el-empty description="暂无同步记录" :image-size="80" />
    </div>

    <div v-else class="trend-chart">
      <div ref="chartRef" style="height: 200px"></div>
    </div>
  </el-card>
</template>

<script setup lang="ts">
import { computed, ref, onMounted, watch } from 'vue'
import * as echarts from 'echarts'
import {
  DataLine,
  CirclePlus,
  Edit,
  Delete,
  CircleClose
} from '@element-plus/icons-vue'

interface Props {
  stats: {
    total: number
    created: number
    updated: number
    deleted: number
    failed: number
  }
  logs: Array<{
    id: number
    created_at: string
    status: string
    total_count: number
    created_count: number
    updated_count: number
    failed_count: number
  }>
}

const props = defineProps<Props>()
const chartRef = ref<HTMLElement>()
let chart: echarts.ECharts | null = null

const stats = computed(() => [
  {
    key: 'total',
    label: '处理总数',
    value: props.stats.total,
    suffix: '条',
    color: '',
    icon: DataLine,
    iconColor: '#409EFF'
  },
  {
    key: 'created',
    label: '新增',
    value: props.stats.created,
    suffix: '条',
    color: 'text-success',
    icon: CirclePlus,
    iconColor: '#67C23A'
  },
  {
    key: 'updated',
    label: '更新',
    value: props.stats.updated,
    suffix: '条',
    color: 'text-warning',
    icon: Edit,
    iconColor: '#E6A23C'
  },
  {
    key: 'failed',
    label: '失败',
    value: props.stats.failed,
    suffix: '条',
    color: 'text-danger',
    icon: CircleClose,
    iconColor: '#F56C6C'
  }
])

const initChart = () => {
  if (!chartRef.value) return

  chart = echarts.init(chartRef.value)

  // 准备数据
  const dates = props.logs.map(log => {
    const date = new Date(log.created_at)
    return `${date.getMonth() + 1}/${date.getDate()} ${date.getHours()}:${date.getMinutes().toString().padStart(2, '0')}`
  }).reverse()

  const totalData = props.logs.map(log => log.total_count).reverse()
  const createdData = props.logs.map(log => log.created_count).reverse()
  const updatedData = props.logs.map(log => log.updated_count).reverse()

  const option = {
    tooltip: {
      trigger: 'axis'
    },
    legend: {
      data: ['总数', '新增', '更新']
    },
    grid: {
      left: '3%',
      right: '4%',
      bottom: '3%',
      containLabel: true
    },
    xAxis: {
      type: 'category',
      boundaryGap: false,
      data: dates
    },
    yAxis: {
      type: 'value'
    },
    series: [
      {
        name: '总数',
        type: 'line',
        data: totalData,
        smooth: true,
        itemStyle: { color: '#409EFF' }
      },
      {
        name: '新增',
        type: 'line',
        data: createdData,
        smooth: true,
        itemStyle: { color: '#67C23A' }
      },
      {
        name: '更新',
        type: 'line',
        data: updatedData,
        smooth: true,
        itemStyle: { color: '#E6A23C' }
      }
    ]
  }

  chart.setOption(option)
}

watch(() => props.logs, () => {
  if (chart) {
    chart.dispose()
  }
  initChart()
}, { deep: true })

onMounted(() => {
  initChart()

  window.addEventListener('resize', () => {
    chart?.resize()
  })
})
</script>

<style scoped>
.empty-trend {
  padding: 20px 0;
}

.trend-chart {
  width: 100%;
}

:deep(.el-statistic) {
  text-align: center;
  padding: 10px;
  background: #f5f7fa;
  border-radius: 8px;
}

.text-success {
  color: #67C23A;
}

.text-warning {
  color: #E6A23C;
}

.text-danger {
  color: #F56C6C;
}
</style>
```

---

## 4. 同步日志组件

### SyncLogs.vue

```vue
<template>
  <el-card header="同步日志" shadow="hover">
    <template #extra>
      <el-button
        :icon="Refresh"
        :loading="loading"
        @click="$emit('refresh')"
      >
        刷新
      </el-button>
    </template>

    <el-table
      :data="logs"
      v-loading="loading"
      stripe
      style="width: 100%"
    >
      <el-table-column prop="id" label="日志ID" width="80" />

      <el-table-column label="同步类型" width="120">
        <template #default="{ row }">
          <el-tag size="small">{{ getSyncTypeLabel(row.sync_type) }}</el-tag>
        </template>
      </el-table-column>

      <el-table-column label="状态" width="100">
        <template #default="{ row }">
          <el-tag :type="getStatusType(row.status)" size="small">
            {{ getStatusLabel(row.status) }}
          </el-tag>
        </template>
      </el-table-column>

      <el-table-column label="统计" width="300">
        <template #default="{ row }">
          <div class="stats-cell">
            <span class="stat-item">总数: {{ row.total_count }}</span>
            <span class="stat-item stat-created">新增: {{ row.created_count }}</span>
            <span class="stat-item stat-updated">更新: {{ row.updated_count }}</span>
            <span v-if="row.failed_count > 0" class="stat-item stat-failed">失败: {{ row.failed_count }}</span>
          </div>
        </template>
      </el-table-column>

      <el-table-column prop="started_at" label="开始时间" width="160">
        <template #default="{ row }">
          {{ formatDateTime(row.started_at) }}
        </template>
      </el-table-column>

      <el-table-column label="耗时" width="80">
        <template #default="{ row }">
          {{ row.duration ? `${row.duration}秒` : '-' }}
        </template>
      </el-table-column>

      <el-table-column label="操作" width="100" fixed="right">
        <template #default="{ row }">
          <el-button
            type="primary"
            link
            size="small"
            @click="showDetail(row)"
          >
            详情
          </el-button>
        </template>
      </el-table-column>
    </el-table>

    <!-- 分页 -->
    <div class="pagination">
      <el-pagination
        small
        background
        layout="total, prev, pager, next"
        :total="totalCount"
        :page-size="pageSize"
        :current-page="currentPage"
        @current-change="handlePageChange"
      />
    </div>

    <!-- 详情弹窗 -->
    <SyncLogDetailDialog
      v-model:visible="showDetailDialog"
      :log="selectedLog"
    />
  </el-card>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { Refresh } from '@element-plus/icons-vue'
import SyncLogDetailDialog from './SyncLogDetailDialog.vue'

interface SyncLog {
  id: number
  sync_type: string
  status: string
  total_count: number
  created_count: number
  updated_count: number
  deleted_count: number
  failed_count: number
  started_at: string
  finished_at: string | null
  duration?: number
  error_message?: string
}

interface Props {
  logs: SyncLog[]
  loading?: boolean
}

interface Emits {
  (e: 'refresh'): void
}

const props = defineProps<Props>()
const emit = defineEmits<Emits>()

const showDetailDialog = ref(false)
const selectedLog = ref<SyncLog | null>(null)

const pageSize = 20
const currentPage = ref(1)

const displayedLogs = computed(() => {
  const start = (currentPage.value - 1) * pageSize
  const end = start + pageSize
  return props.logs.slice(start, end)
})

const totalCount = computed(() => props.logs.length)

const getSyncTypeLabel = (type: string) => {
  const map = {
    'department': '部门同步',
    'user': '用户同步',
    'full': '全量同步'
  }
  return map[type] || type
}

const getStatusType = (status: string) => {
  const map = {
    'success': 'success',
    'failed': 'danger',
    'running': 'warning',
    'partial': 'warning'
  }
  return map[status] || 'info'
}

const getStatusLabel = (status: string) => {
  const map = {
    'success': '成功',
    'failed': '失败',
    'running': '运行中',
    'partial': '部分成功'
  }
  return map[status] || status
}

const formatDateTime = (dateStr: string) => {
  const date = new Date(dateStr)
  return date.toLocaleString('zh-CN')
}

const showDetail = (log: SyncLog) => {
  selectedLog.value = log
  showDetailDialog.value = true
}

const handlePageChange = (page: number) => {
  currentPage.value = page
}
</script>

<style scoped>
.stats-cell {
  display: flex;
  gap: 12px;
  font-size: 12px;
}

.stat-item {
  color: #606266;
}

.stat-created {
  color: #67C23A;
}

.stat-updated {
  color: #E6A23C;
}

.stat-failed {
  color: #F56C6C;
}

.pagination {
  margin-top: 16px;
  display: flex;
  justify-content: flex-end;
}
</style>
```

---

## 5. 同步进度弹窗

### SyncProgressDialog.vue

```vue
<template>
  <el-dialog
    v-model="dialogVisible"
    title="同步进度"
    width="500px"
    :close-on-click-modal="false"
    :close-on-press-escape="false"
    :show-close="!running"
  >
    <div class="sync-progress">
      <!-- 进度动画 -->
      <div class="progress-animation">
        <div class="sync-circle" :class="{ spinning: running }">
          <el-icon :size="60" v-if="running">
            <Loading />
          </el-icon>
          <el-icon :size="60" color="#67C23A" v-else-if="finished && !failed">
            <CircleCheck />
          </el-icon>
          <el-icon :size="60" color="#F56C6C" v-else>
            <CircleClose />
          </el-icon>
        </div>
      </div>

      <!-- 进度状态 -->
      <div class="progress-status">
        <h3>{{ progressTitle }}</h3>
        <p>{{ progressMessage }}</p>
      </div>

      <!-- 进度条 -->
      <div v-if="running" class="progress-bar-wrapper">
        <el-progress
          :percentage="progressPercentage"
          :indeterminate="indeterminate"
          status="success"
        />
      </div>

      <!-- 实时统计 -->
      <div v-if="stats.total > 0 || running" class="progress-stats">
        <el-row :gutter="10">
          <el-col :span="6">
            <el-statistic title="处理总数" :value="stats.total" />
          </el-col>
          <el-col :span="6">
            <el-statistic title="新增" :value="stats.created" />
          </el-col>
          <el-col :span="6">
            <el-statistic title="更新" :value="stats.updated" />
          </el-col>
          <el-col :span="6">
            <el-statistic title="失败" :value="stats.failed" />
          </el-col>
        </el-row>
      </div>

      <!-- 错误信息 -->
      <div v-if="failed && errorMessage" class="error-message">
        <el-alert type="error" :closable="false">
          {{ errorMessage }}
        </el-alert>
      </div>
    </div>

    <template #footer v-if="!running">
      <el-button @click="handleClose">关闭</el-button>
      <el-button v-if="failed" type="primary" @click="handleRetry">
        重试
      </el-button>
    </template>
  </el-dialog>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { Loading, CircleCheck, CircleClose } from '@element-plus/icons-vue'

interface Props {
  visible: boolean
  logId: number | null
}

interface Emits {
  (e: 'update:visible', value: boolean): void
  (e: 'finished', log: any): void
}

const props = defineProps<Props>()
const emit = defineEmits<Emits>()

const dialogVisible = computed({
  get: () => props.visible,
  set: (value) => emit('update:visible', value)
})

const running = ref(false)
const finished = ref(false)
const failed = ref(false)
const progressPercentage = ref(0)
const indeterminate = ref(true)
const stats = ref({
  total: 0,
  created: 0,
  updated: 0,
  failed: 0
})
const errorMessage = ref('')

const progressTitle = computed(() => {
  if (running.value) return '正在同步...'
  if (failed.value) return '同步失败'
  if (finished.value) return '同步完成'
  return '准备同步'
})

const progressMessage = computed(() => {
  if (running.value) return '正在与企业微信同步数据，请稍候...'
  if (failed.value) return '同步过程中出现错误，请查看错误信息'
  if (finished.value) return `已完成同步，共处理 ${stats.value.total} 条数据`
  return '正在初始化同步任务'
})

// 轮询同步状态
let pollTimer: number | null = null

const startPolling = () => {
  pollTimer = window.setInterval(async () => {
    try {
      // 调用API获取同步状态
      const response = await fetch(`/api/sso/sync/logs/?limit=1`)
      const data = await response.json()

      if (data.results && data.results.length > 0) {
        const log = data.results[0]

        stats.value = {
          total: log.total_count,
          created: log.created_count,
          updated: log.updated_count,
          failed: log.failed_count
        }

        if (log.status === 'success') {
          running.value = false
          finished.value = true
          failed.value = false
          indeterminate.value = false
          progressPercentage.value = 100
          stopPolling()
          emit('finished', log)
        } else if (log.status === 'failed') {
          running.value = false
          finished.value = true
          failed.value = true
          errorMessage.value = log.error_message || '未知错误'
          stopPolling()
          emit('finished', log)
        }
      }
    } catch (error) {
      console.error('轮询同步状态失败', error)
    }
  }, 2000)
}

const stopPolling = () => {
  if (pollTimer) {
    clearInterval(pollTimer)
    pollTimer = null
  }
}

const handleClose = () => {
  dialogVisible.value = false
}

const handleRetry = () => {
  failed.value = false
  finished.value = false
  running.value = true
  emit('update:visible', false)
  // 重新触发同步
  emit('finished', null)
}

watch(() => props.visible, (visible) => {
  if (visible && props.logId) {
    running.value = true
    finished.value = false
    failed.value = false
    progressPercentage.value = 0
    indeterminate.value = true
    stats.value = { total: 0, created: 0, updated: 0, failed: 0 }
    errorMessage.value = ''
    startPolling()
  } else {
    stopPolling()
  }
})
</script>

<style scoped>
.sync-progress {
  text-align: center;
  padding: 20px;
}

.progress-animation {
  margin-bottom: 30px;
}

.sync-circle {
  width: 80px;
  height: 80px;
  margin: 0 auto;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 50%;
  background: #f0f9ff;
}

.sync-circle.spinning {
  animation: pulse 2s ease-in-out infinite;
}

@keyframes pulse {
  0%, 100% {
    opacity: 1;
  }
  50% {
    opacity: 0.6;
  }
}

.progress-status {
  margin-bottom: 20px;
}

.progress-status h3 {
  font-size: 18px;
  margin-bottom: 8px;
  color: #303133;
}

.progress-status p {
  color: #909399;
  font-size: 14px;
}

.progress-bar-wrapper {
  margin-bottom: 30px;
}

.progress-stats {
  margin-top: 30px;
  padding-top: 20px;
  border-top: 1px solid #ebeef5;
}

.error-message {
  margin-top: 20px;
  text-align: left;
}
</style>
```

---

## 6. API 集成

```typescript
// src/api/sso/index.ts

import request from '@/utils/request'

/**
 * 获取同步配置
 */
export const getSyncConfig = () => {
  return request.get('/api/sso/sync/config/')
}

/**
 * 获取同步状态
 */
export const getSyncStatus = () => {
  return request.get('/api/sso/sync/status/')
}

/**
 * 获取同步日志列表
 */
export const getSyncLogs = (params?: { limit?: number }) => {
  return request.get('/api/sso/sync/logs/', { params })
}

/**
 * 触发同步
 */
export const triggerSync = (data?: { sync_type?: string }) => {
  return request.post('/api/sso/sync/trigger/', data)
}

/**
 * 获取同步日志详情
 */
export const getSyncLogDetail = (id: number) => {
  return request.get(`/api/sso/sync/logs/${id}/`)
}
```

---

## 7. 路由配置

```typescript
// src/router/index.ts

import type { RouteRecordRaw } from 'vue-router'

const routes: RouteRecordRaw[] = [
  // ... 其他路由
  {
    path: '/admin',
    component: () => import('@/layouts/AdminLayout.vue'),
    meta: { requiresAuth: true },
    children: [
      {
        path: 'sync',
        name: 'SyncManagement',
        component: () => import('@/views/admin/SyncManagement.vue'),
        meta: {
          title: '同步管理',
          permission: 'sso.manage'
        }
      }
    ]
  }
]
```

---

## 后续任务

1. Phase 2.3: 实现企业微信消息推送通知
2. 扩展支持钉钉、飞书的通讯录同步前端
