# Phase 3.2: 工作流执行引擎 - 前端实现

## 前端公共组件引用

| 组件名 | 组件路径 | 用途 |
|--------|---------|------|
| BaseListPage | @/components/common/BaseListPage.vue | 列表页面 |
| BaseFormPage | @/components/common/BaseFormPage.vue | 表单页面 |
| BaseDetailPage | @/components/common/BaseDetailPage.vue | 详情页面 |

---

## 概述

前端主要实现待办任务管理、审批操作界面、流程历史追踪、流程进度可视化等功能。

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

## 页面结构

```
src/views/workflows/
├── TaskCenter.vue          # 任务中心（首页）
├── MyTasks.vue             # 我的待办
├── TaskDetail.vue          # 任务详情/审批页
├── WorkflowInstance.vue    # 流程实例详情
└── components/
    ├── TaskCard.vue        # 任务卡片
    ├── TaskApprovalPanel.vue    # 审批面板
    ├── WorkflowProgress.vue     # 流程进度
    ├── ApprovalChain.vue        # 审批链
    ├── WorkflowLog.vue          # 操作日志
    ├── CommentList.vue          # 评论列表
    └── TransferDialog.vue       # 转交对话框
```

---

## 1. 任务中心页面

```vue
<!-- src/views/workflows/TaskCenter.vue -->
<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useWorkflowStore } from '@/stores/workflow'
import TaskCard from '@/views/workflows/components/TaskCard.vue'
import WorkflowProgress from '@/views/workflows/components/WorkflowProgress.vue'

const router = useRouter()
const workflowStore = useWorkflowStore()

// 标签页
const activeTab = ref('pending')
const tabs = [
  { key: 'pending', label: '待处理', count: 0 },
  { key: 'approved', label: '已处理', count: 0 },
  { key: 'initiated', label: '我发起的', count: 0 },
  { key: 'cc', label: '抄送我的', count: 0 }
]

// 数据
const loading = ref(false)
const tasks = ref([])
const instances = ref([])
const statistics = ref({})

// 计算属性
const pendingTasks = computed(() =>
  tasks.value.filter(t => t.status === 'pending')
)

const overdueTasks = computed(() =>
  tasks.value.filter(t => t.is_overdue)
)

// 获取统计数据
const fetchStatistics = async () => {
  try {
    const data = await workflowStore.getStatistics()
    statistics.value = data

    // 更新标签计数
    tabs[0].count = data.pending_count
    tabs[1].count = data.completed_today
    tabs[2].count = data.initiated_count
  } catch (error) {
    console.error('获取统计失败', error)
  }
}

// 获取任务列表
const fetchTasks = async () => {
  loading.value = true
  try {
    if (activeTab.value === 'initiated') {
      const data = await workflowStore.getMyInstances()
      instances.value = data
    } else if (activeTab.value === 'cc') {
      const data = await workflowStore.getMyCCTasks()
      tasks.value = data
    } else {
      const data = await workflowStore.getMyTasks(activeTab.value)
      tasks.value = data
    }
  } finally {
    loading.value = false
  }
}

// 标签切换
const handleTabChange = (tab) => {
  activeTab.value = tab
  fetchTasks()
}

// 快速审批
const handleQuickApprove = async (task) => {
  await workflowStore.approveTask(task.id, { comment: '同意' })
  fetchTasks()
  fetchStatistics()
}

// 查看详情
const handleViewDetail = (task) => {
  if (activeTab.value === 'initiated') {
    router.push(`/workflows/instance/${task.id}`)
  } else {
    router.push(`/workflows/task/${task.id}`)
  }
}

// 刷新
const handleRefresh = () => {
  fetchTasks()
  fetchStatistics()
}

onMounted(() => {
  fetchStatistics()
  fetchTasks()
})
</script>

<template>
  <div class="task-center">
    <!-- 头部统计 -->
    <div class="statistics-cards">
      <el-row :gutter="16">
        <el-col :span="6">
          <el-card shadow="hover" class="stat-card pending">
            <div class="stat-content">
              <div class="stat-value">{{ statistics.pending_count || 0 }}</div>
              <div class="stat-label">待处理任务</div>
            </div>
            <el-icon class="stat-icon"><Clock /></el-icon>
          </el-card>
        </el-col>
        <el-col :span="6">
          <el-card shadow="hover" class="stat-card success">
            <div class="stat-content">
              <div class="stat-value">{{ statistics.completed_today || 0 }}</div>
              <div class="stat-label">今日已完成</div>
            </div>
            <el-icon class="stat-icon"><CircleCheck /></el-icon>
          </el-card>
        </el-col>
        <el-col :span="6">
          <el-card shadow="hover" class="stat-card warning">
            <div class="stat-content">
              <div class="stat-value">{{ overdueTasks.length }}</div>
              <div class="stat-label">超时任务</div>
            </div>
            <el-icon class="stat-icon"><Warning /></el-icon>
          </el-card>
        </el-col>
        <el-col :span="6">
          <el-card shadow="hover" class="stat-card info">
            <div class="stat-content">
              <div class="stat-value">{{ statistics.initiated_count || 0 }}</div>
              <div class="stat-label">发起的流程</div>
            </div>
            <el-icon class="stat-icon"><Document /></el-icon>
          </el-card>
        </el-col>
      </el-row>
    </div>

    <!-- 标签页 -->
    <el-card class="task-tabs-card" shadow="never">
      <el-tabs v-model="activeTab" @tab-change="handleTabChange">
        <el-tab-pane
          v-for="tab in tabs"
          :key="tab.key"
          :name="tab.key"
        >
          <template #label>
            <span class="tab-label">
              {{ tab.label }}
              <el-badge v-if="tab.count > 0" :value="tab.count" type="danger" />
            </span>
          </template>
        </el-tab-pane>
      </el-tabs>

      <!-- 工具栏 -->
      <div class="toolbar">
        <el-input
          v-model="searchText"
          placeholder="搜索任务..."
          :prefix-icon="Search"
          style="width: 300px"
          clearable
        />
        <el-button type="primary" :icon="Refresh" @click="handleRefresh">
          刷新
        </el-button>
      </div>

      <!-- 任务列表 -->
      <div v-loading="loading" class="task-list">
        <!-- 我发起的流程实例 -->
        <template v-if="activeTab === 'initiated'">
          <div v-for="instance in instances" :key="instance.id" class="instance-item">
            <WorkflowProgress :instance="instance" @click="handleViewDetail(instance)" />
          </div>
        </template>

        <!-- 任务列表 -->
        <template v-else>
          <div v-if="tasks.length === 0" class="empty-state">
            <el-empty description="暂无任务" />
          </div>
          <div v-else class="task-grid">
            <TaskCard
              v-for="task in tasks"
              :key="task.id"
              :task="task"
              @approve="handleQuickApprove(task)"
              @detail="handleViewDetail(task)"
            />
          </div>
        </template>
      </div>
    </el-card>
  </div>
</template>

<style scoped lang="scss">
.task-center {
  padding: 20px;
  background: #f5f7fa;
  min-height: 100vh;

  .statistics-cards {
    margin-bottom: 20px;

    .stat-card {
      position: relative;
      overflow: hidden;
      cursor: pointer;
      transition: all 0.3s;

      &:hover {
        transform: translateY(-4px);
      }

      &.pending { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); }
      &.success { background: linear-gradient(135deg, #84fab0 0%, #8fd3f4 100%); }
      &.warning { background: linear-gradient(135deg, #fccb90 0%, #d57eeb 100%); }
      &.info { background: linear-gradient(135deg, #a1c4fd 0%, #c2e9fb 100%); }

      :deep(.el-card__body) {
        color: white;
        display: flex;
        justify-content: space-between;
        align-items: center;
      }

      .stat-content {
        .stat-value {
          font-size: 36px;
          font-weight: bold;
        }
        .stat-label {
          font-size: 14px;
          opacity: 0.9;
        }
      }

      .stat-icon {
        font-size: 48px;
        opacity: 0.3;
      }
    }
  }

  .task-tabs-card {
    .toolbar {
      display: flex;
      justify-content: space-between;
      margin-bottom: 20px;
    }

    .task-list {
      min-height: 400px;

      .task-grid {
        display: grid;
        grid-template-columns: repeat(auto-fill, minmax(350px, 1fr));
        gap: 16px;
      }

      .instance-item {
        margin-bottom: 16px;
      }
    }
  }
}
</style>
```

---

## 2. 任务卡片组件

```vue
<!-- src/views/workflows/components/TaskCard.vue -->
<script setup>
import { computed } from 'vue'
import { useRouter } from 'vue-router'

const props = defineProps({
  task: {
    type: Object,
    required: true
  }
})

const emit = defineEmits(['approve', 'detail'])

const router = useRouter()

// 计算属性
const isOverdue = computed(() => props.task.is_overdue)
const statusType = computed(() => {
  const statusMap = {
    pending: 'warning',
    approved: 'success',
    rejected: 'danger',
    skipped: 'info'
  }
  return statusMap[props.task.status] || 'info'
})

const remainingText = computed(() => {
  const hours = props.task.remaining_hours
  if (hours === null) return ''
  if (hours <= 0) return '已超时'
  if (hours < 1) return `${Math.round(hours * 60)}分钟内处理`
  return `剩余 ${hours} 小时`
})

// 快速审批
const handleQuickApprove = () => {
  emit('approve', props.task)
}

// 查看详情
const handleDetail = () => {
  emit('detail', props.task)
}
</script>

<template>
  <el-card
    class="task-card"
    :class="{ overdue: isOverdue }"
    shadow="hover"
    @click="handleDetail"
  >
    <!-- 头部 -->
    <template #header>
      <div class="card-header">
        <div class="header-left">
          <el-tag :type="statusType" size="small">
            {{ task.status_display }}
          </el-tag>
          <span class="task-title">{{ task.node_name }}</span>
        </div>
        <div v-if="isOverdue" class="overdue-badge">
          <el-icon color="#f56c6c"><WarningFilled /></el-icon>
        </div>
      </div>
    </template>

    <!-- 内容 -->
    <div class="card-content">
      <!-- 业务信息 -->
      <div class="business-info">
        <div class="info-row">
          <span class="label">单据编号:</span>
          <span class="value">{{ task.instance_no }}</span>
        </div>
        <div class="info-row">
          <span class="label">发起人:</span>
          <div class="value user-info">
            <el-avatar :size="24" :src="task.initiator_avatar" />
            <span>{{ task.initiator_name }}</span>
          </div>
        </div>
      </div>

      <!-- 时间信息 -->
      <div class="time-info">
        <div class="info-row">
          <el-icon><Clock /></el-icon>
          <span>{{ remainingText || formatTime(task.assigned_at) }}</span>
        </div>
      </div>
    </div>

    <!-- 底部操作 -->
    <template #footer>
      <div class="card-footer">
        <span class="assignee">
          <el-avatar :size="24" :src="task.assignee_avatar" />
          <span>审批人: {{ task.assignee_name }}</span>
        </span>
        <div v-if="task.status === 'pending'" class="actions" @click.stop>
          <el-button
            type="success"
            size="small"
            :icon="Select"
            @click="handleQuickApprove"
          >
            同意
          </el-button>
          <el-button
            type="danger"
            size="small"
            :icon="Close"
            @click="handleDetail"
          >
            拒绝
          </el-button>
        </div>
      </div>
    </template>
  </el-card>
</template>

<style scoped lang="scss">
.task-card {
  cursor: pointer;
  transition: all 0.3s;

  &:hover {
    transform: translateY(-2px);
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
  }

  &.overdue {
    border-left: 3px solid #f56c6c;
  }

  .card-header {
    display: flex;
    justify-content: space-between;
    align-items: center;

    .header-left {
      display: flex;
      align-items: center;
      gap: 8px;

      .task-title {
        font-weight: 500;
        font-size: 15px;
      }
    }

    .overdue-badge {
      animation: pulse 2s infinite;
    }
  }

  .card-content {
    .business-info {
      margin-bottom: 12px;

      .info-row {
        display: flex;
        align-items: center;
        margin-bottom: 8px;

        .label {
          color: #909399;
          margin-right: 8px;
          font-size: 13px;
        }

        .value {
          color: #303133;
          font-size: 13px;

          &.user-info {
            display: flex;
            align-items: center;
            gap: 6px;
          }
        }
      }
    }

    .time-info {
      padding-top: 8px;
      border-top: 1px dashed #ebeef5;

      .info-row {
        display: flex;
        align-items: center;
        gap: 4px;
        color: #909399;
        font-size: 12px;
      }
    }
  }

  .card-footer {
    display: flex;
    justify-content: space-between;
    align-items: center;

    .assignee {
      display: flex;
      align-items: center;
      gap: 6px;
      font-size: 13px;
      color: #606266;
    }

    .actions {
      display: flex;
      gap: 8px;
    }
  }
}

@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.5; }
}
</style>
```

---

## 3. 任务详情/审批页面

```vue
<!-- src/views/workflows/TaskDetail.vue -->
<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useWorkflowStore } from '@/stores/workflow'
import { ElMessage, ElMessageBox } from 'element-plus'
import TaskApprovalPanel from '@/views/workflows/components/TaskApprovalPanel.vue'
import WorkflowProgress from '@/views/workflows/components/WorkflowProgress.vue'
import ApprovalChain from '@/views/workflows/components/ApprovalChain.vue'
import DynamicForm from '@/components/engine/DynamicForm.vue'

const route = useRoute()
const router = useRouter()
const workflowStore = useWorkflowStore()

const taskId = route.params.id
const task = ref(null)
const instance = ref(null)
const businessData = ref(null)
const logs = ref([])
const loading = ref(false)
const submitting = ref(false)

// 审批表单
const approvalForm = ref({
  action: 'approved',
  comment: ''
})

// 字段权限
const fieldPermissions = computed(() => {
  return task.value?.field_permissions || {}
})

// 获取任务详情
const fetchTaskDetail = async () => {
  loading.value = true
  try {
    const data = await workflowStore.getTaskDetail(taskId)
    task.value = data.task
    instance.value = data.instance
    businessData.value = data.business_data
    logs.value = data.logs
  } finally {
    loading.value = false
  }
}

// 提交审批
const handleSubmit = async () => {
  if (!approvalForm.value.comment) {
    ElMessage.warning('请填写审批意见')
    return
  }

  await ElMessageBox.confirm(
    `确认${approvalForm.value.action === 'approved' ? '同意' : '拒绝'}此审批?`,
    '提示',
    {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    }
  )

  submitting.value = true
  try {
    if (approvalForm.value.action === 'approved') {
      await workflowStore.approveTask(taskId, {
        comment: approvalForm.value.comment
      })
    } else {
      await workflowStore.rejectTask(taskId, {
        comment: approvalForm.value.comment
      })
    }

    ElMessage.success('审批成功')
    router.push('/workflows/tasks')
  } catch (error) {
    ElMessage.error(error.message || '审批失败')
  } finally {
    submitting.value = false
  }
}

// 转交
const handleTransfer = async (targetUserId) => {
  try {
    await workflowStore.transferTask(taskId, {
      target_user_id: targetUserId,
      comment: '转交审批'
    })
    ElMessage.success('转交成功')
    router.push('/workflows/tasks')
  } catch (error) {
    ElMessage.error(error.message || '转交失败')
  }
}

// 查看流程图
const handleViewFlowChart = () => {
  // 打开流程图对话框
}

onMounted(() => {
  fetchTaskDetail()
})
</script>

<template>
  <div class="task-detail-page" v-loading="loading">
    <el-page-header @back="router.push('/workflows/tasks')">
      <template #content>
        <span class="page-title">{{ task?.node_name }}</span>
        <el-tag :type="task?.status === 'pending' ? 'warning' : 'success'">
          {{ task?.status_display }}
        </el-tag>
      </template>
    </el-page-header>

    <el-row :gutter="20" class="content-row">
      <!-- 左侧：业务数据和审批 -->
      <el-col :span="14">
        <!-- 业务数据 -->
        <el-card class="business-card" shadow="never">
          <template #header>
            <div class="card-header">
              <span>业务数据</span>
              <el-button text type="primary" @click="handleViewFlowChart">
                查看流程图
              </el-button>
            </div>
          </template>

          <DynamicForm
            v-if="businessData"
            :data="businessData"
            :field-permissions="fieldPermissions"
            :readonly="true"
          />
        </el-card>

        <!-- 审批面板 -->
        <TaskApprovalPanel
          v-if="task?.status === 'pending'"
          :task="task"
          v-model="approvalForm"
          :submitting="submitting"
          @submit="handleSubmit"
          @transfer="handleTransfer"
        />
      </el-col>

      <!-- 右侧：流程进度和日志 -->
      <el-col :span="10">
        <!-- 流程进度 -->
        <WorkflowProgress
          v-if="instance"
          :instance="instance"
          class="progress-card"
        />

        <!-- 审批链 -->
        <ApprovalChain
          v-if="instance"
          :instance-id="instance.id"
          class="chain-card"
        />

        <!-- 操作日志 -->
        <el-card class="logs-card" shadow="never">
          <template #header>
            <span>操作日志</span>
          </template>

          <div class="log-list">
            <div
              v-for="log in logs"
              :key="log.id"
              class="log-item"
            >
              <div class="log-header">
                <el-avatar :size="32" :src="log.actor_avatar" />
                <div class="log-info">
                  <span class="actor">{{ log.actor_name }}</span>
                  <span class="action">{{ log.action_display }}</span>
                </div>
                <span class="time">{{ formatTime(log.created_at) }}</span>
              </div>
              <div v-if="log.comment" class="log-comment">
                {{ log.comment }}
              </div>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<style scoped lang="scss">
.task-detail-page {
  padding: 20px;
  background: #f5f7fa;
  min-height: 100vh;

  .page-title {
    font-size: 18px;
    font-weight: 500;
    margin-right: 12px;
  }

  .content-row {
    margin-top: 20px;

    .business-card,
    .logs-card {
      margin-bottom: 20px;
    }

    .progress-card,
    .chain-card {
      margin-bottom: 20px;
    }
  }

  .card-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
  }

  .log-list {
    .log-item {
      padding: 12px 0;
      border-bottom: 1px solid #ebeef5;

      &:last-child {
        border-bottom: none;
      }

      .log-header {
        display: flex;
        align-items: center;
        gap: 12px;

        .log-info {
          flex: 1;

          .actor {
            font-weight: 500;
            margin-right: 8px;
          }

          .action {
            color: #909399;
            font-size: 13px;
          }
        }

        .time {
          color: #909399;
          font-size: 12px;
        }
      }

      .log-comment {
        margin-top: 8px;
        margin-left: 44px;
        color: #606266;
        font-size: 13px;
        background: #f5f7fa;
        padding: 8px 12px;
        border-radius: 4px;
      }
    }
  }
}
</style>
```

---

## 4. 审批面板组件

```vue
<!-- src/views/workflows/components/TaskApprovalPanel.vue -->
<script setup>
import { ref, computed } from 'vue'
import { ElMessage } from 'element-plus'

const props = defineProps({
  task: {
    type: Object,
    required: true
  },
  modelValue: {
    type: Object,
    required: true
  },
  submitting: {
    type: Boolean,
    default: false
  }
})

const emit = defineEmits(['update:modelValue', 'submit', 'transfer'])

// 快捷评论
const quickComments = [
  '同意',
  '已核实，同意',
  '情况属实，批准',
  '请补充说明',
  '不符合规定，拒绝'
]

// 转交对话框
const transferDialogVisible = ref(false)
const transferTarget = ref(null)

// 设置快捷评论
const setQuickComment = (comment) => {
  emit('update:modelValue', {
    ...props.modelValue,
    comment
  })
}

// 切换审批动作
const setAction = (action) => {
  emit('update:modelValue', {
    ...props.modelValue,
    action
  })
}

// 确认转交
const confirmTransfer = () => {
  if (!transferTarget.value) {
    ElMessage.warning('请选择转交对象')
    return
  }
  emit('transfer', transferTarget.value)
  transferDialogVisible.value = false
  transferTarget.value = null
}

// 是否显示转交功能
const canTransfer = computed(() => {
  return props.task?.node_type === 'approval'
})
</script>

<template>
  <el-card class="approval-panel" shadow="never">
    <template #header>
      <span>审批操作</span>
    </template>

    <!-- 审批动作选择 -->
    <div class="action-selector">
      <div
        class="action-item"
        :class="{ active: modelValue.action === 'approved' }"
        @click="setAction('approved')"
      >
        <el-icon color="#67c23a"><CircleCheck /></el-icon>
        <span>同意</span>
      </div>
      <div
        class="action-item"
        :class="{ active: modelValue.action === 'rejected' }"
        @click="setAction('rejected')"
      >
        <el-icon color="#f56c6c"><CircleClose /></el-icon>
        <span>拒绝</span>
      </div>
    </div>

    <!-- 审批意见 -->
    <div class="comment-section">
      <div class="quick-comments">
        <el-tag
          v-for="comment in quickComments"
          :key="comment"
          @click="setQuickComment(comment)"
        >
          {{ comment }}
        </el-tag>
      </div>

      <el-input
        v-model="modelValue.comment"
        type="textarea"
        :rows="4"
        placeholder="请输入审批意见..."
        maxlength="500"
        show-word-limit
      />
    </div>

    <!-- 附件上传（可选） -->
    <div class="attachment-section">
      <el-upload
        action="#"
        :auto-upload="false"
        :on-change="handleFileChange"
      >
        <el-button text type="primary">
          <el-icon><Paperclip /></el-icon>
          添加附件
        </el-button>
      </el-upload>
    </div>

    <!-- 操作按钮 -->
    <div class="action-buttons">
      <el-button
        type="success"
        :loading="submitting"
        :disabled="!modelValue.comment"
        @click="emit('submit')"
      >
        提交审批
      </el-button>

      <el-button
        v-if="canTransfer"
        @click="transferDialogVisible = true"
      >
        <el-icon><Promotion /></el-icon>
        转交他人
      </el-button>
    </div>

    <!-- 转交对话框 -->
    <el-dialog
      v-model="transferDialogVisible"
      title="转交审批"
      width="500px"
    >
      <el-form>
        <el-form-item label="转交给">
          <UserSelector v-model="transferTarget" />
        </el-form-item>
        <el-form-item label="转交说明">
          <el-input
            v-model="transferReason"
            type="textarea"
            :rows="3"
            placeholder="请说明转交原因..."
          />
        </el-form-item>
      </el-form>

      <template #footer>
        <el-button @click="transferDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="confirmTransfer">
          确认转交
        </el-button>
      </template>
    </el-dialog>
  </el-card>
</template>

<style scoped lang="scss">
.approval-panel {
  .action-selector {
    display: flex;
    gap: 16px;
    margin-bottom: 20px;

    .action-item {
      flex: 1;
      display: flex;
      flex-direction: column;
      align-items: center;
      justify-content: center;
      padding: 20px;
      border: 2px solid #ebeef5;
      border-radius: 8px;
      cursor: pointer;
      transition: all 0.3s;

      &:hover {
        border-color: #c0c4cc;
      }

      &.active {
        border-color: #409eff;
        background: #ecf5ff;
      }

      .el-icon {
        font-size: 32px;
        margin-bottom: 8px;
      }

      span {
        font-size: 14px;
        font-weight: 500;
      }
    }
  }

  .comment-section {
    margin-bottom: 20px;

    .quick-comments {
      display: flex;
      gap: 8px;
      margin-bottom: 12px;
      flex-wrap: wrap;

      .el-tag {
        cursor: pointer;
        transition: all 0.2s;

        &:hover {
          transform: translateY(-2px);
          box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
        }
      }
    }
  }

  .attachment-section {
    margin-bottom: 20px;
    padding: 12px;
    background: #f5f7fa;
    border-radius: 4px;
  }

  .action-buttons {
    display: flex;
    gap: 12px;
  }
}
</style>
```

---

## 5. 流程进度组件

```vue
<!-- src/views/workflows/components/WorkflowProgress.vue -->
<script setup>
import { computed } from 'vue'
import { useRouter } from 'vue-router'

const props = defineProps({
  instance: {
    type: Object,
    required: true
  }
})

const emit = defineEmits(['click'])

const router = useRouter()

// 流程状态
const statusMap = {
  draft: { color: '#909399', icon: 'Document' },
  running: { color: '#409eff', icon: 'Loading' },
  pending_approval: { color: '#e6a23c', icon: 'Clock' },
  approved: { color: '#67c23a', icon: 'CircleCheck' },
  rejected: { color: '#f56c6c', icon: 'CircleClose' },
  cancelled: { color: '#909399', icon: 'CircleClose' },
  terminated: { color: '#f56c6c', icon: 'Warning' }
}

const currentStatus = computed(() => statusMap[props.instance.status] || statusMap.draft)

// 进度百分比
const progress = computed(() => props.instance.progress || 0)

// 当前任务
const currentTasks = computed(() => props.instance.current_tasks || [])

// 点击查看详情
const handleClick = () => {
  emit('click')
  router.push(`/workflows/instance/${props.instance.id}`)
}
</script>

<template>
  <el-card class="workflow-progress" shadow="hover" @click="handleClick">
    <!-- 头部 -->
    <div class="progress-header">
      <div class="header-info">
        <el-icon :color="currentStatus.color" :size="20">
          <component :is="currentStatus.icon" />
        </el-icon>
        <div class="info-text">
          <div class="title">{{ instance.definition_name }}</div>
          <div class="no">{{ instance.business_no }}</div>
        </div>
      </div>
      <el-tag :color="currentStatus.color" effect="plain">
        {{ instance.status_display }}
      </el-tag>
    </div>

    <!-- 进度条 -->
    <div class="progress-bar-container">
      <el-progress
        :percentage="progress"
        :stroke-width="8"
        :show-text="false"
        :color="currentStatus.color"
      />
      <div class="progress-text">
        <span>进度: {{ progress }}%</span>
        <span>{{ instance.completed_tasks }}/{{ instance.total_tasks }} 任务</span>
      </div>
    </div>

    <!-- 当前处理人 -->
    <div v-if="currentTasks.length > 0" class="current-assignees">
      <div class="assignees-label">当前处理:</div>
      <div class="assignees-list">
        <el-avatar
          v-for="task in currentTasks"
          :key="task.id"
          :size="32"
          :src="task.assignee_avatar"
          :title="task.assignee_name"
        />
      </div>
    </div>

    <!-- 时间信息 -->
    <div class="time-info">
      <span>发起于 {{ formatTime(instance.started_at) }}</span>
      <span v-if="instance.completed_at">
        · 完成于 {{ formatTime(instance.completed_at) }}
      </span>
    </div>
  </el-card>
</template>

<style scoped lang="scss">
.workflow-progress {
  cursor: pointer;
  transition: all 0.3s;

  &:hover {
    transform: translateY(-2px);
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
  }

  .progress-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 16px;

    .header-info {
      display: flex;
      align-items: center;
      gap: 12px;

      .info-text {
        .title {
          font-size: 15px;
          font-weight: 500;
          color: #303133;
        }
        .no {
          font-size: 12px;
          color: #909399;
          margin-top: 2px;
        }
      }
    }
  }

  .progress-bar-container {
    margin-bottom: 16px;

    .progress-text {
      display: flex;
      justify-content: space-between;
      margin-top: 8px;
      font-size: 12px;
      color: #909399;
    }
  }

  .current-assignees {
    display: flex;
    align-items: center;
    gap: 12px;
    padding: 12px;
    background: #f5f7fa;
    border-radius: 4px;
    margin-bottom: 12px;

    .assignees-label {
      font-size: 13px;
      color: #606266;
    }

    .assignees-list {
      display: flex;
      gap: -8px;

      .el-avatar {
        border: 2px solid white;
        margin-left: -8px;

        &:first-child {
          margin-left: 0;
        }
      }
    }
  }

  .time-info {
    font-size: 12px;
    color: #909399;
  }
}
</style>
```

---

## 6. 审批链组件

```vue
<!-- src/views/workflows/components/ApprovalChain.vue -->
<script setup>
import { ref, onMounted } from 'vue'
import { useWorkflowStore } from '@/stores/workflow'

const props = defineProps({
  instanceId: {
    type: [String, Number],
    required: true
  }
})

const workflowStore = useWorkflowStore()

const chain = ref([])
const loading = ref(false)

const fetchChain = async () => {
  loading.value = true
  try {
    chain.value = await workflowStore.getApprovalChain(props.instanceId)
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  fetchChain()
})
</script>

<template>
  <el-card class="approval-chain" shadow="never" v-loading="loading">
    <template #header>
      <span>审批流程</span>
    </template>

    <div class="chain-list">
      <div
        v-for="(item, index) in chain"
        :key="item.id"
        class="chain-item"
      >
        <!-- 连接线 -->
        <div v-if="index > 0" class="connector"></div>

        <!-- 节点 -->
        <div class="node-content" :class="`status-${item.status}`">
          <div class="node-icon">
            <el-avatar
              v-if="item.assignee_avatar"
              :size="40"
              :src="item.assignee_avatar"
            />
            <el-icon v-else :size="40"><UserFilled /></el-icon>

            <div class="status-badge">
              <el-icon v-if="item.status === 'approved'" color="#67c23a">
                <CircleCheck />
              </el-icon>
              <el-icon v-else-if="item.status === 'rejected'" color="#f56c6c">
                <CircleClose />
              </el-icon>
              <el-icon v-else-if="item.status === 'pending'" color="#e6a23c">
                <Clock />
              </el-icon>
            </div>
          </div>

          <div class="node-info">
            <div class="node-title">{{ item.node_name }}</div>
            <div class="node-assignee">{{ item.assignee_name }}</div>
            <div v-if="item.comment" class="node-comment">
              {{ item.comment }}
            </div>
            <div class="node-time">
              {{ formatTime(item.completed_at || item.assigned_at) }}
            </div>
          </div>
        </div>
      </div>
    </div>
  </el-card>
</template>

<style scoped lang="scss">
.approval-chain {
  .chain-list {
    .chain-item {
      position: relative;
      padding-bottom: 24px;

      &:last-child {
        padding-bottom: 0;
      }

      .connector {
        position: absolute;
        left: 20px;
        top: 60px;
        bottom: 0;
        width: 2px;
        background: #e4e7ed;
      }

      .node-content {
        display: flex;
        gap: 12px;

        &.status-approved .node-icon {
          border-color: #67c23a;
        }

        &.status-rejected .node-icon {
          border-color: #f56c6c;
        }

        &.status-pending .node-icon {
          border-color: #e6a23c;
        }

        .node-icon {
          position: relative;
          width: 48px;
          height: 48px;
          border: 2px solid #e4e7ed;
          border-radius: 50%;
          display: flex;
          align-items: center;
          justify-content: center;
          background: white;
          flex-shrink: 0;

          .status-badge {
            position: absolute;
            right: -4px;
            bottom: -4px;
            width: 16px;
            height: 16px;
            background: white;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
          }
        }

        .node-info {
          flex: 1;
          padding-top: 4px;

          .node-title {
            font-size: 14px;
            font-weight: 500;
            color: #303133;
            margin-bottom: 4px;
          }

          .node-assignee {
            font-size: 13px;
            color: #606266;
            margin-bottom: 4px;
          }

          .node-comment {
            font-size: 12px;
            color: #909399;
            background: #f5f7fa;
            padding: 6px 10px;
            border-radius: 4px;
            margin-bottom: 4px;
          }

          .node-time {
            font-size: 12px;
            color: #c0c4cc;
          }
        }
      }
    }
  }
}
</style>
```

---

## 7. Pinia Store

```javascript
// src/stores/workflow.js

import { ref, computed } from 'vue'
import { defineStore } from 'pinia'
import workflowApi from '@/api/workflow'

export const useWorkflowStore = defineStore('workflow', () => {
  // State
  const tasks = ref([])
  const instances = ref([])
  const currentInstance = ref(null)
  const currentTask = ref(null)
  const loading = ref(false)

  // Getters
  const pendingTasks = computed(() =>
    tasks.value.filter(t => t.status === 'pending')
  )

  const overdueTasks = computed(() =>
    tasks.value.filter(t => t.is_overdue)
  )

  // Actions
  const getMyTasks = async (status = 'pending') => {
    const response = await workflowApi.getMyTasks(status)
    tasks.value = response.results || response
    return tasks.value
  }

  const getMyInstances = async () => {
    const response = await workflowApi.getMyInstances()
    instances.value = response.results || response
    return instances.value
  }

  const getMyCCTasks = async () => {
    const response = await workflowApi.getMyCCTasks()
    return response.results || response
  }

  const getTaskDetail = async (taskId) => {
    const response = await workflowApi.getTaskDetail(taskId)
    currentTask.value = response
    return response
  }

  const getInstanceDetail = async (instanceId) => {
    const response = await workflowApi.getInstanceDetail(instanceId)
    currentInstance.value = response
    return response
  }

  const approveTask = async (taskId, data) => {
    const response = await workflowApi.approveTask(taskId, data)
    // 更新本地状态
    const index = tasks.value.findIndex(t => t.id === taskId)
    if (index !== -1) {
      tasks.value.splice(index, 1)
    }
    return response
  }

  const rejectTask = async (taskId, data) => {
    const response = await workflowApi.rejectTask(taskId, data)
    const index = tasks.value.findIndex(t => t.id === taskId)
    if (index !== -1) {
      tasks.value.splice(index, 1)
    }
    return response
  }

  const transferTask = async (taskId, data) => {
    const response = await workflowApi.transferTask(taskId, data)
    const index = tasks.value.findIndex(t => t.id === taskId)
    if (index !== -1) {
      tasks.value.splice(index, 1)
    }
    return response
  }

  const withdrawInstance = async (instanceId) => {
    const response = await workflowApi.withdrawInstance(instanceId)
    const index = instances.value.findIndex(i => i.id === instanceId)
    if (index !== -1) {
      instances.value[index].status = 'cancelled'
    }
    return response
  }

  const getApprovalChain = async (instanceId) => {
    const response = await workflowApi.getApprovalChain(instanceId)
    return response
  }

  const getStatistics = async () => {
    const response = await workflowApi.getStatistics()
    return response
  }

  const startWorkflow = async (data) => {
    const response = await workflowApi.startWorkflow(data)
    return response
  }

  return {
    // State
    tasks,
    instances,
    currentInstance,
    currentTask,
    loading,
    // Getters
    pendingTasks,
    overdueTasks,
    // Actions
    getMyTasks,
    getMyInstances,
    getMyCCTasks,
    getTaskDetail,
    getInstanceDetail,
    approveTask,
    rejectTask,
    transferTask,
    withdrawInstance,
    getApprovalChain,
    getStatistics,
    startWorkflow
  }
})
```

---

## 8. API封装

```javascript
// src/api/workflow.js

import request from '@/utils/request'

export default {
  // 获取我的待办
  getMyTasks(status = 'pending', params = {}) {
    return request({
      url: '/api/workflows/execution/my_tasks/',
      method: 'get',
      params: { status, ...params }
    })
  },

  // 获取我发起的流程
  getMyInstances(params = {}) {
    return request({
      url: '/api/workflows/execution/my_instances/',
      method: 'get',
      params
    })
  },

  // 获取抄送我的
  getMyCCTasks(params = {}) {
    return request({
      url: '/api/workflows/execution/my_cc_tasks/',
      method: 'get',
      params
    })
  },

  // 获取任务详情
  getTaskDetail(taskId) {
    return request({
      url: `/api/workflows/execution/tasks/${taskId}/detail/`,
      method: 'get'
    })
  },

  // 获取流程实例详情
  getInstanceDetail(instanceId) {
    return request({
      url: `/api/workflows/execution/${instanceId}/detail/`,
      method: 'get'
    })
  },

  // 同意
  approveTask(taskId, data) {
    return request({
      url: `/api/workflows/execution/${taskId}/approve/`,
      method: 'post',
      data
    })
  },

  // 拒绝
  rejectTask(taskId, data) {
    return request({
      url: `/api/workflows/execution/${taskId}/reject/`,
      method: 'post',
      data
    })
  },

  // 转交
  transferTask(taskId, data) {
    return request({
      url: `/api/workflows/execution/${taskId}/transfer/`,
      method: 'post',
      data
    })
  },

  // 撤回
  withdrawInstance(instanceId) {
    return request({
      url: `/api/workflows/execution/${instanceId}/withdraw/`,
      method: 'post'
    })
  },

  // 获取审批链
  getApprovalChain(instanceId) {
    return request({
      url: `/api/workflows/execution/${instanceId}/chain/`,
      method: 'get'
    })
  },

  // 获取操作日志
  getLogs(instanceId) {
    return request({
      url: `/api/workflows/execution/${instanceId}/logs/`,
      method: 'get'
    })
  },

  // 获取统计数据
  getStatistics() {
    return request({
      url: '/api/workflows/execution/statistics/',
      method: 'get'
    })
  },

  // 启动工作流
  startWorkflow(data) {
    return request({
      url: '/api/workflows/execution/start/',
      method: 'post',
      data
    })
  }
}
```

---

## 9. 路由配置

```javascript
// src/router/workflows.js

export default [
  {
    path: '/workflows',
    component: () => import('@/layouts/WorkflowLayout.vue'),
    children: [
      {
        path: '',
        redirect: '/workflows/tasks'
      },
      {
        path: 'tasks',
        name: 'TaskCenter',
        component: () => import('@/views/workflows/TaskCenter.vue'),
        meta: { title: '任务中心', icon: 'List' }
      },
      {
        path: 'task/:id',
        name: 'TaskDetail',
        component: () => import('@/views/workflows/TaskDetail.vue'),
        meta: { title: '任务详情' }
      },
      {
        path: 'instance/:id',
        name: 'WorkflowInstance',
        component: () => import('@/views/workflows/WorkflowInstance.vue'),
        meta: { title: '流程详情' }
      },
      {
        path: 'my-instances',
        name: 'MyInstances',
        component: () => import('@/views/workflows/MyInstances.vue'),
        meta: { title: '我的流程', icon: 'Document' }
      }
    ]
  }
]
```

---

## 后续任务

1. Phase 4.1: 实现QR码扫描盘点
2. Phase 4.2: 实现RFID批量盘点
3. Phase 4.3: 实现盘点快照和差异处理
