# Phase 4.5: 盘点业务链条 - 前端实现

## 1. 页面结构

### 1.1 页面层级

```
src/views/inventory/reconciliation/
├── difference/                    # 差异管理
│   ├── DifferenceList.vue        # 差异列表
│   ├── DifferenceDetail.vue      # 差异详情
│   ├── components/
│   │   ├── DifferenceConfirmDialog.vue # 差异认定对话框
│   │   ├── DifferenceFilter.vue       # 差异筛选器
│   │   └── DifferenceStatistics.vue   # 差异统计图表
│
├── resolution/                    # 差异处理
│   ├── ResolutionList.vue        # 处理单列表
│   ├── ResolutionDetail.vue      # 处理单详情
│   ├── ResolutionForm.vue        # 处理单创建/编辑
│   └── components/
│       ├── DifferenceSelector.vue    # 差异选择器
│       └── ResolutionFlow.vue        # 处理流程展示
│
├── adjustment/                    # 资产调账
│   ├── AdjustmentList.vue        # 调账记录列表
│   ├── AdjustmentDetail.vue      # 调账详情
│   └── components/
│       └── AdjustmentDiffView.vue    # 调账前后对比视图
│
└── report/                        # 盘点报告
    ├── ReportList.vue            # 报告列表
    ├── ReportDetail.vue          # 报告详情
    ├── ReportPreview.vue         # 报告预览
    ├── TemplateManage.vue        # 模板管理
    └── components/
        ├── ReportSummary.vue         # 报告概况
        ├── DifferenceChart.vue       # 差异图表
        └── ApprovalFlow.vue          # 审批流程展示
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

## 2. 差异管理模块

### 2.1 差异列表 (DifferenceList.vue)

```vue
<template>
  <div class="difference-list">
    <!-- 统计卡片 -->
    <el-row :gutter="16" class="stats-row">
      <el-col :span="6">
        <el-card class="stat-card">
          <div class="stat-content">
            <div class="stat-number">{{ statistics.total }}</div>
            <div class="stat-label">总差异</div>
          </div>
          <el-icon class="stat-icon" color="#409EFF"><Document /></el-icon>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card class="stat-card pending">
          <div class="stat-content">
            <div class="stat-number">{{ statistics.pending }}</div>
            <div class="stat-label">待认定</div>
          </div>
          <el-icon class="stat-icon" color="#E6A23C"><Clock /></el-icon>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card class="stat-card processing">
          <div class="stat-content">
            <div class="stat-number">{{ statistics.processing }}</div>
            <div class="stat-label">处理中</div>
          </div>
          <el-icon class="stat-icon" color="#409EFF"><Loading /></el-icon>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card class="stat-card resolved">
          <div class="stat-content">
            <div class="stat-number">{{ statistics.resolved }}</div>
            <div class="stat-label">已处理</div>
          </div>
          <el-icon class="stat-icon" color="#67C23A"><CircleCheck /></el-icon>
        </el-card>
      </el-col>
    </el-row>

    <!-- 筛选区 -->
    <el-card class="filter-card">
      <difference-filter v-model="searchForm" @search="handleSearch" @reset="handleReset" />
    </el-card>

    <!-- 操作区 -->
    <div class="toolbar">
      <el-button type="primary" :icon="Refresh" @click="handleAnalyze">重新分析</el-button>
      <el-button
        type="success"
        :icon="Check"
        :disabled="selectedIds.length === 0"
        @click="handleBatchConfirm"
      >
        批量认定
      </el-button>
      <el-button :icon="Download" @click="handleExport">导出</el-button>
    </div>

    <!-- 差异列表 -->
    <el-table
      v-loading="loading"
      :data="tableData"
      border
      stripe
      @selection-change="handleSelectionChange"
    >
      <el-table-column type="selection" width="55" :selectable="checkSelectable" />
      <el-table-column prop="task.task_no" label="盘点任务" width="150" />
      <el-table-column label="差异类型" width="100">
        <template #default="{ row }">
          <el-tag :type="getTypeColor(row.difference_type)">
            {{ row.difference_type_display }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column label="状态" width="90">
        <template #default="{ row }">
          <el-tag :type="getStatusColor(row.status)">
            {{ row.status_display }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column label="资产信息" min-width="200">
        <template #default="{ row }">
          <div v-if="row.asset">
            <div>{{ row.asset.asset_name }}</div>
            <div class="text-secondary">{{ row.asset.asset_no }}</div>
          </div>
          <span v-else class="text-muted">-</span>
        </template>
      </el-table-column>
      <el-table-column label="账面信息" width="150">
        <template #default="{ row }">
          <div v-if="row.account_location">
            <div>{{ row.account_location.name }}</div>
            <div class="text-secondary">{{ row.account_status_display }}</div>
          </div>
          <span v-else class="text-muted">-</span>
        </template>
      </el-table-column>
      <el-table-column label="实物信息" width="150">
        <template #default="{ row }">
          <div v-if="row.actual_location">
            <div>{{ row.actual_location.name }}</div>
            <div class="text-secondary">{{ row.actual_status_display || '-' }}</div>
          </div>
          <span v-else class="text-muted">-</span>
        </template>
      </el-table-column>
      <el-table-column prop="description" label="差异说明" min-width="200" show-overflow-tooltip />
      <el-table-column label="责任人" width="100">
        <template #default="{ row }">
          {{ row.responsible_user?.full_name || '-' }}
        </template>
      </el-table-column>
      <el-table-column label="操作" width="180" fixed="right">
        <template #default="{ row }">
          <el-button link type="primary" @click="handleView(row)">查看</el-button>
          <el-button
            v-if="row.status === 'pending'"
            link
            type="success"
            @click="handleConfirm(row)"
          >认定</el-button>
          <el-button
            v-if="['confirmed', 'processing'].includes(row.status)"
            link
            type="warning"
            @click="handleViewResolution(row)"
          >处理</el-button>
        </template>
      </el-table-column>
    </el-table>

    <!-- 分页 -->
    <el-pagination
      v-model:current-page="pagination.page"
      v-model:page-size="pagination.pageSize"
      :total="pagination.total"
      layout="total, sizes, prev, pager, next"
      @size-change="fetchData"
      @current-change="fetchData"
    />

    <!-- 差异认定对话框 -->
    <difference-confirm-dialog
      v-model="confirmDialogVisible"
      :difference-id="currentDifferenceId"
      :difference-ids="batchMode ? selectedIds : []"
      @success="handleConfirmSuccess"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  Document, Clock, Loading, CircleCheck, Refresh, Check, Download
} from '@element-plus/icons-vue'
import { differenceApi } from '@/api/inventory/difference'
import DifferenceFilter from './components/DifferenceFilter.vue'
import DifferenceConfirmDialog from './components/DifferenceConfirmDialog.vue'

const router = useRouter()
const loading = ref(false)
const tableData = ref([])
const selectedIds = ref<number[]>([])
const confirmDialogVisible = ref(false)
const currentDifferenceId = ref<number>()
const batchMode = ref(false)

const searchForm = reactive({
  task_id: null,
  difference_type: '',
  status: '',
  responsible_user_id: null,
  keyword: ''
})

const pagination = reactive({
  page: 1,
  pageSize: 20,
  total: 0
})

const statistics = reactive({
  total: 0,
  pending: 0,
  processing: 0,
  resolved: 0
})

const getTypeColor = (type: string) => {
  const colorMap: Record<string, string> = {
    surplus: 'success',
    loss: 'danger',
    location_mismatch: 'warning',
    status_mismatch: 'warning',
    value_mismatch: 'info',
    info_mismatch: 'info'
  }
  return colorMap[type] || 'info'
}

const getStatusColor = (status: string) => {
  const colorMap: Record<string, string> = {
    pending: 'warning',
    confirmed: 'primary',
    processing: 'primary',
    approved: 'success',
    resolved: 'success',
    closed: 'info'
  }
  return colorMap[status] || 'info'
}

const checkSelectable = (row: any) => {
  return row.status === 'pending'
}

const fetchData = async () => {
  loading.value = true
  try {
    const res = await differenceApi.list({
      ...searchForm,
      page: pagination.page,
      page_size: pagination.pageSize
    })
    tableData.value = res.results
    pagination.total = res.count

    // 更新统计
    Object.assign(statistics, res.statistics || {})
  } finally {
    loading.value = false
  }
}

const handleSearch = () => {
  pagination.page = 1
  fetchData()
}

const handleReset = () => {
  Object.assign(searchForm, {
    task_id: null,
    difference_type: '',
    status: '',
    responsible_user_id: null,
    keyword: ''
  })
  handleSearch()
}

const handleAnalyze = async () => {
  try {
    await ElMessageBox.confirm(
      '重新分析将覆盖现有差异数据，是否继续？',
      '警告',
      { type: 'warning' }
    )
    loading.value = true
    await differenceApi.analyze({ task_id: searchForm.task_id })
    ElMessage.success('分析完成')
    fetchData()
  } catch {
    // 取消
  } finally {
    loading.value = false
  }
}

const handleBatchConfirm = () => {
  batchMode.value = true
  confirmDialogVisible.value = true
}

const handleConfirm = (row: any) => {
  batchMode.value = false
  currentDifferenceId.value = row.id
  confirmDialogVisible.value = true
}

const handleConfirmSuccess = () => {
  confirmDialogVisible.value = false
  fetchData()
}

const handleView = (row: any) => {
  router.push(`/inventory/reconciliation/difference/${row.id}`)
}

const handleViewResolution = (row: any) => {
  if (row.resolution) {
    router.push(`/inventory/reconciliation/resolution/${row.resolution.id}`)
  }
}

const handleSelectionChange = (selection: any[]) => {
  selectedIds.value = selection.map(item => item.id)
}

const handleExport = async () => {
  // TODO: 实现导出
  ElMessage.info('导出功能开发中')
}

onMounted(fetchData)
</script>

<style scoped>
.stats-row {
  margin-bottom: 16px;
}

.stat-card {
  position: relative;
  overflow: hidden;
}

.stat-card.pending :deep(.el-card__body) {
  border-left: 4px solid #E6A23C;
}

.stat-card.processing :deep(.el-card__body) {
  border-left: 4px solid #409EFF;
}

.stat-card.resolved :deep(.el-card__body) {
  border-left: 4px solid #67C23A;
}

.stat-content {
  display: flex;
  flex-direction: column;
}

.stat-number {
  font-size: 28px;
  font-weight: bold;
  color: #303133;
}

.stat-label {
  font-size: 14px;
  color: #909399;
  margin-top: 4px;
}

.stat-icon {
  position: absolute;
  right: 16px;
  top: 50%;
  transform: translateY(-50%);
  font-size: 40px;
  opacity: 0.2;
}

.text-secondary {
  font-size: 12px;
  color: #909399;
}

.text-muted {
  color: #C0C4CC;
}
</style>
```

### 2.2 差异认定对话框 (DifferenceConfirmDialog.vue)

```vue
<template>
  <el-dialog
    v-model="visible"
    :title="batchMode ? `批量认定差异 (${differenceIds.length}条)` : '认定差异'"
    width="600px"
    :close-on-click-modal="false"
  >
    <el-form ref="formRef" :model="formData" :rules="formRules" label-width="100px">
      <el-form-item label="认定意见" prop="confirmation_note">
        <el-input
          v-model="formData.confirmation_note"
          type="textarea"
          :rows="3"
          placeholder="请输入认定意见"
        />
      </el-form-item>

      <el-form-item label="责任人" prop="responsible_user_id">
        <user-picker v-model="formData.responsible_user_id" />
      </el-form-item>

      <el-form-item label="责任部门" prop="responsible_department_id">
        <dept-picker v-model="formData.responsible_department_id" />
      </el-form-item>

      <el-form-item label="处理建议" prop="suggested_action">
        <el-radio-group v-model="formData.suggested_action">
          <el-radio label="adjust_account">调整账面</el-radio>
          <el-radio label="adjust_asset">调整实物</el-radio>
          <el-radio label="write_off">资产报损</el-radio>
          <el-radio label="pending">待处理</el-radio>
        </el-radio-group>
      </el-form-item>

      <el-form-item label="建议说明">
        <el-input
          v-model="formData.suggestion_note"
          type="textarea"
          :rows="2"
          placeholder="请输入处理建议说明"
        />
      </el-form-item>
    </el-form>

    <template #footer>
      <el-button @click="visible = false">取消</el-button>
      <el-button type="primary" @click="handleConfirm" :loading="submitting">
        确认认定
      </el-button>
    </template>
  </el-dialog>
</template>

<script setup lang="ts">
import { ref, reactive, watch } from 'vue'
import { ElMessage } from 'element-plus'
import type { FormInstance, FormRules } from 'element-plus'
import { differenceApi } from '@/api/inventory/difference'

const props = defineProps<{
  differenceId?: number
  differenceIds?: number[]
}>()

const emit = defineEmits<{
  (e: 'update:modelValue', value: boolean): void
  (e: 'success'): void
}>()

const visible = defineModel<boolean>()
const formRef = ref<FormInstance>()
const submitting = ref(false)

const batchMode = ref(false)

const formData = reactive({
  confirmation_note: '',
  responsible_user_id: null,
  responsible_department_id: null,
  suggested_action: 'adjust_account',
  suggestion_note: ''
})

const formRules: FormRules = {
  confirmation_note: [{ required: true, message: '请输入认定意见', trigger: 'blur' }],
  responsible_user_id: [{ required: true, message: '请选择责任人', trigger: 'change' }]
}

watch(() => [props.differenceId, props.differenceIds], () => {
  batchMode.value = !!(props.differenceIds && props.differenceIds.length > 1)
}, { immediate: true })

const handleConfirm = async () => {
  try {
    await formRef.value?.validate()

    submitting.value = true

    if (batchMode.value && props.differenceIds) {
      await differenceApi.batchConfirm({
        difference_ids: props.differenceIds,
        ...formData
      })
      ElMessage.success(`成功认定 ${props.differenceIds.length} 条差异`)
    } else if (props.differenceId) {
      await differenceApi.confirm(props.differenceId, formData)
      ElMessage.success('认定成功')
    }

    emit('success')
  } catch {
    // 验证失败或请求失败
  } finally {
    submitting.value = false
  }
}
</script>
```

---

## 3. 差异处理模块

### 3.1 处理单列表 (ResolutionList.vue)

```vue
<template>
  <div class="resolution-list">
    <!-- 筛选区 -->
    <el-card class="filter-card">
      <el-form :model="searchForm" inline>
        <el-form-item label="盘点任务">
          <task-picker v-model="searchForm.task_id" />
        </el-form-item>
        <el-form-item label="状态">
          <el-select v-model="searchForm.status" placeholder="全部状态" clearable>
            <el-option label="草稿" value="draft" />
            <el-option label="已提交" value="submitted" />
            <el-option label="已批准" value="approved" />
            <el-option label="已驳回" value="rejected" />
            <el-option label="已完成" value="completed" />
          </el-select>
        </el-form-item>
        <el-form-item label="处理方式">
          <el-select v-model="searchForm.action" placeholder="全部方式" clearable>
            <el-option label="调整账面" value="adjust_account" />
            <el-option label="调整实物" value="adjust_asset" />
            <el-option label="补录资产" value="record_asset" />
            <el-option label="资产报损" value="write_off" />
          </el-select>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="handleSearch">查询</el-button>
          <el-button @click="handleReset">重置</el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <!-- 操作区 -->
    <div class="toolbar">
      <el-button type="primary" :icon="Plus" @click="handleCreate">
        新建处理单
      </el-button>
    </div>

    <!-- 处理单列表 -->
    <el-table v-loading="loading" :data="tableData" border stripe>
      <el-table-column prop="resolution_no" label="处理单号" width="150" />
      <el-table-column label="状态" width="90">
        <template #default="{ row }">
          <el-tag :type="getStatusType(row.status)">
            {{ row.status_display }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="task.task_name" label="盘点任务" min-width="200" />
      <el-table-column label="处理方式" width="110">
        <template #default="{ row }">{{ row.action_display }}</template>
      </el-table-column>
      <el-table-column prop="description" label="处理说明" min-width="200" show-overflow-tooltip />
      <el-table-column label="差异数量" width="90" align="center">
        <template #default="{ row }">{{ row.differences_count }}</template>
      </el-table-column>
      <el-table-column prop="applicant.full_name" label="申请人" width="100" />
      <el-table-column prop="application_date" label="申请日期" width="110" />
      <el-table-column label="当前审批人" width="110">
        <template #default="{ row }">
          {{ row.current_approver?.full_name || '-' }}
        </template>
      </el-table-column>
      <el-table-column label="操作" width="180" fixed="right">
        <template #default="{ row }">
          <el-button link type="primary" @click="handleView(row)">查看</el-button>
          <el-button
            v-if="row.status === 'draft'"
            link
            type="primary"
            @click="handleEdit(row)"
          >编辑</el-button>
          <el-button
            v-if="row.status === 'draft'"
            link
            type="success"
            @click="handleSubmit(row)"
          >提交</el-button>
          <el-button
            v-if="row.status === 'submitted' && isCurrentApprover(row)"
            link
            type="warning"
            @click="handleApprove(row)"
          >审批</el-button>
        </template>
      </el-table-column>
    </el-table>

    <!-- 分页 -->
    <el-pagination
      v-model:current-page="pagination.page"
      v-model:page-size="pagination.pageSize"
      :total="pagination.total"
      layout="total, sizes, prev, pager, next"
      @size-change="fetchData"
      @current-change="fetchData"
    />

    <!-- 审批对话框 -->
    <approval-dialog
      v-model="approvalDialogVisible"
      :resolution="currentResolution"
      @success="handleApprovalSuccess"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, computed } from 'vue'
import { useRouter } from 'vue-router'
import { useUserStore } from '@/stores/user'
import { Plus } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import { resolutionApi } from '@/api/inventory/resolution'
import ApprovalDialog from './components/ApprovalDialog.vue'

const router = useRouter()
const userStore = useUserStore()
const loading = ref(false)
const tableData = ref([])
const approvalDialogVisible = ref(false)
const currentResolution = ref<any>(null)

const searchForm = reactive({
  task_id: null,
  status: '',
  action: ''
})

const pagination = reactive({
  page: 1,
  pageSize: 20,
  total: 0
})

const getStatusType = (status: string) => {
  const typeMap: Record<string, string> = {
    draft: 'info',
    submitted: 'warning',
    approved: 'success',
    rejected: 'danger',
    completed: 'success'
  }
  return typeMap[status] || 'info'
}

const isCurrentApprover = (row: any) => {
  return row.current_approver?.id === userStore.user.id
}

const fetchData = async () => {
  loading.value = true
  try {
    const res = await resolutionApi.list({
      ...searchForm,
      page: pagination.page,
      page_size: pagination.pageSize
    })
    tableData.value = res.results
    pagination.total = res.count
  } finally {
    loading.value = false
  }
}

const handleSearch = () => {
  pagination.page = 1
  fetchData()
}

const handleReset = () => {
  Object.assign(searchForm, {
    task_id: null,
    status: '',
    action: ''
  })
  handleSearch()
}

const handleCreate = () => {
  router.push('/inventory/reconciliation/resolution/create')
}

const handleView = (row: any) => {
  router.push(`/inventory/reconciliation/resolution/${row.id}`)
}

const handleEdit = (row: any) => {
  router.push(`/inventory/reconciliation/resolution/edit/${row.id}`)
}

const handleSubmit = async (row: any) => {
  try {
    await resolutionApi.submit(row.id)
    ElMessage.success('提交成功')
    fetchData()
  } catch {
    ElMessage.error('提交失败')
  }
}

const handleApprove = (row: any) => {
  currentResolution.value = row
  approvalDialogVisible.value = true
}

const handleApprovalSuccess = () => {
  approvalDialogVisible.value = false
  fetchData()
}

onMounted(fetchData)
</script>
```

### 3.2 处理单表单 (ResolutionForm.vue)

```vue
<template>
  <div class="resolution-form">
    <el-form
      ref="formRef"
      :model="formData"
      :rules="formRules"
      label-width="120px"
    >
      <el-card header="基本信息">
        <el-form-item label="盘点任务" prop="task_id">
          <task-picker v-model="formData.task_id" @change="handleTaskChange" />
        </el-form-item>
        <el-form-item label="处理方式" prop="action">
          <el-radio-group v-model="formData.action">
            <el-radio label="adjust_account">调整账面</el-radio>
            <el-radio label="adjust_asset">调整实物</el-radio>
            <el-radio label="record_asset">补录资产</el-radio>
            <el-radio label="write_off">资产报损</el-radio>
            <el-radio label="pending">待处理</el-radio>
          </el-radio-group>
        </el-form-item>
        <el-form-item label="处理说明" prop="description">
          <el-input
            v-model="formData.description"
            type="textarea"
            :rows="3"
            placeholder="请详细说明处理方案"
          />
        </el-form-item>
      </el-card>

      <el-card header="差异选择">
        <difference-selector
          v-model="formData.difference_ids"
          :task-id="formData.task_id"
          :status-filter="['confirmed']"
        />
      </el-card>

      <el-card header="处理详情" v-if="selectedDifferences.length > 0">
        <el-table :data="selectedDifferences" border>
          <el-table-column prop="asset.asset_name" label="资产" width="150" />
          <el-table-column label="差异类型" width="100">
            <template #default="{ row }">
              {{ row.difference_type_display }}
            </template>
          </el-table-column>
          <el-table-column label="账面信息" width="150">
            <template #default="{ row }">
              {{ row.account_location?.name || '-' }}
            </template>
          </el-table-column>
          <el-table-column label="实物信息" width="150">
            <template #default="{ row }">
              {{ row.actual_location?.name || '-' }}
            </template>
          </el-table-column>
          <el-table-column prop="description" label="差异说明" min-width="200" />
        </el-table>
      </el-card>

      <div class="form-actions">
        <el-button @click="handleBack">返回</el-button>
        <el-button type="primary" @click="handleSave">保存草稿</el-button>
        <el-button type="success" @click="handleSubmit">提交审批</el-button>
      </div>
    </el-form>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { ElMessage } from 'element-plus'
import type { FormInstance, FormRules } from 'element-plus'
import { resolutionApi } from '@/api/inventory/resolution'
import { differenceApi } from '@/api/inventory/difference'
import DifferenceSelector from './components/DifferenceSelector.vue'

const router = useRouter()
const route = useRoute()
const formRef = ref<FormInstance>()
const isEdit = ref(false)
const resolutionId = ref<number>()

const formData = reactive({
  task_id: null,
  action: 'adjust_account',
  description: '',
  difference_ids: []
})

const formRules: FormRules = {
  task_id: [{ required: true, message: '请选择盘点任务', trigger: 'change' }],
  action: [{ required: true, message: '请选择处理方式', trigger: 'change' }],
  description: [{ required: true, message: '请填写处理说明', trigger: 'blur' }]
}

const selectedDifferences = ref<any[]>([])

const handleTaskChange = async () => {
  formData.difference_ids = []
  selectedDifferences.value = []
}

const handleSave = async () => {
  try {
    await formRef.value?.validate()
    if (isEdit.value) {
      await resolutionApi.update(resolutionId.value, formData)
    } else {
      const res = await resolutionApi.create(formData)
      router.replace(`/inventory/reconciliation/resolution/edit/${res.id}`)
    }
    ElMessage.success('保存成功')
  } catch {
    // 验证失败
  }
}

const handleSubmit = async () => {
  try {
    await formRef.value?.validate()
    const data = isEdit.value
      ? await resolutionApi.update(resolutionId.value, formData)
      : await resolutionApi.create(formData)
    await resolutionApi.submit(data.id)
    ElMessage.success('提交成功')
    router.push('/inventory/reconciliation/resolution')
  } catch {
    // 失败
  }
}

const handleBack = () => {
  router.back()
}

onMounted(async () => {
  if (route.params.id) {
    isEdit.value = true
    resolutionId.value = Number(route.params.id)
    const data = await resolutionApi.detail(resolutionId.value)
    Object.assign(formData, data)
    selectedDifferences.value = data.differences || []
  }
})
</script>
```

---

## 4. 盘点报告模块

### 4.1 报告详情 (ReportDetail.vue)

```vue
<template>
  <div class="report-detail" v-loading="loading">
    <!-- 操作栏 -->
    <div class="toolbar">
      <el-button :icon="Download" @click="handleExport('pdf')">导出PDF</el-button>
      <el-button :icon="Download" @click="handleExport('excel')">导出Excel</el-button>
      <el-button
        v-if="report.status === 'draft'"
        type="primary"
        @click="handleSubmit"
      >提交审批</el-button>
      <el-button
        v-if="canApprove"
        type="warning"
        @click="approvalDialogVisible = true"
      >审批</el-button>
    </div>

    <!-- 报告内容 -->
    <div class="report-content">
      <!-- 报告头部 -->
      <div class="report-header">
        <h1>{{ report.report_no }}</h1>
        <div class="report-meta">
          <el-tag :type="getStatusType(report.status)">
            {{ report.status_display }}
          </el-tag>
          <span>生成时间：{{ formatDateTime(report.generated_at) }}</span>
          <span>生成人：{{ report.generated_by?.full_name }}</span>
        </div>
      </div>

      <!-- 盘点概况 -->
      <report-summary :summary="report.report_data?.summary" />

      <!-- 差异统计图表 -->
      <el-card header="差异统计" class="chart-section">
        <el-row :gutter="20">
          <el-col :span="12">
            <difference-chart
              type="pie"
              :data="report.report_data?.differences_by_type"
              title="差异类型分布"
            />
          </el-col>
          <el-col :span="12">
            <difference-chart
              type="bar"
              :data="report.report_data?.differences_by_department"
              title="部门差异统计"
            />
          </el-col>
        </el-row>
      </el-card>

      <!-- 差异明细 -->
      <el-card header="差异明细">
        <el-table :data="report.report_data?.differences_detail" border>
          <el-table-column prop="asset_no" label="资产编号" width="130" />
          <el-table-column prop="asset" label="资产名称" width="150" />
          <el-table-column prop="type" label="差异类型" width="100" />
          <el-table-column prop="description" label="差异说明" min-width="200" />
          <el-table-column prop="status" label="处理状态" width="100">
            <template #default="{ row }">
              <el-tag :type="row.status === '已处理' ? 'success' : 'warning'">
                {{ row.status }}
              </el-tag>
            </template>
          </el-table-column>
        </el-table>
      </el-card>

      <!-- 审批流程 -->
      <el-card header="审批流程">
        <approval-flow :approvals="report.approvals" />
      </el-card>
    </div>

    <!-- 审批对话框 -->
    <report-approval-dialog
      v-model="approvalDialogVisible"
      :report="report"
      @success="handleApprovalSuccess"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useUserStore } from '@/stores/user'
import { ElMessage } from 'element-plus'
import { Download } from '@element-plus/icons-vue'
import { reportApi } from '@/api/inventory/report'
import { formatDateTime } from '@/utils/format'
import ReportSummary from './components/ReportSummary.vue'
import DifferenceChart from './components/DifferenceChart.vue'
import ApprovalFlow from './components/ApprovalFlow.vue'
import ReportApprovalDialog from './components/ReportApprovalDialog.vue'

const route = useRoute()
const router = useRouter()
const userStore = useUserStore()
const loading = ref(false)
const report = ref<any>({})
const approvalDialogVisible = ref(false)

const canApprove = computed(() => {
  return report.value.current_approver?.id === userStore.user.id
})

const getStatusType = (status: string) => {
  const typeMap: Record<string, string> = {
    draft: 'info',
    pending_approval: 'warning',
    approved: 'success',
    rejected: 'danger',
    archived: 'info'
  }
  return typeMap[status] || 'info'
}

const fetchData = async () => {
  loading.value = true
  try {
    const data = await reportApi.detail(Number(route.params.id))
    report.value = data
  } finally {
    loading.value = false
  }
}

const handleSubmit = async () => {
  try {
    await reportApi.submit(report.value.id)
    ElMessage.success('提交成功')
    fetchData()
  } catch {
    ElMessage.error('提交失败')
  }
}

const handleApprovalSuccess = () => {
  approvalDialogVisible.value = false
  fetchData()
}

const handleExport = async (format: string) => {
  try {
    const url = await reportApi.export(report.value.id, format)
    window.open(url, '_blank')
  } catch {
    ElMessage.error('导出失败')
  }
}

onMounted(fetchData)
</script>

<style scoped>
.report-content {
  max-width: 1200px;
  margin: 0 auto;
  padding: 20px;
}

.report-header {
  text-align: center;
  margin-bottom: 30px;
}

.report-header h1 {
  font-size: 24px;
  margin-bottom: 10px;
}

.report-meta {
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 20px;
  color: #606266;
}

.chart-section {
  margin: 20px 0;
}
</style>
```

### 4.2 差异统计图表 (DifferenceChart.vue)

```vue
<template>
  <div class="difference-chart" ref="chartRef"></div>
</template>

<script setup lang="ts">
import { ref, onMounted, watch } from 'vue'
import * as echarts from 'echarts'

const props = defineProps<{
  type: 'pie' | 'bar'
  data: Record<string, number> | any[]
  title?: string
}>()

const chartRef = ref<HTMLElement>()
let chart: echarts.ECharts | null = null

const initChart = () => {
  if (!chartRef.value) return

  chart = echarts.init(chartRef.value)

  if (props.type === 'pie') {
    initPieChart()
  } else {
    initBarChart()
  }
}

const initPieChart = () => {
  const data = Object.entries(props.data).map(([name, value]) => ({ name, value }))

  const option: echarts.EChartsOption = {
    title: {
      text: props.title,
      left: 'center'
    },
    tooltip: {
      trigger: 'item',
      formatter: '{b}: {c} ({d}%)'
    },
    legend: {
      orient: 'vertical',
      left: 'left'
    },
    series: [
      {
        type: 'pie',
        radius: '50%',
        data,
        emphasis: {
          itemStyle: {
            shadowBlur: 10,
            shadowOffsetX: 0,
            shadowColor: 'rgba(0, 0, 0, 0.5)'
          }
        }
      }
    ]
  }

  chart?.setOption(option)
}

const initBarChart = () => {
  const categories = props.data.map((item: any) => item.department || item.name)
  const values = props.data.map((item: any) => item.total || item.count || item.value)

  const option: echarts.EChartsOption = {
    title: {
      text: props.title,
      left: 'center'
    },
    tooltip: {
      trigger: 'axis',
      axisPointer: {
        type: 'shadow'
      }
    },
    xAxis: {
      type: 'category',
      data: categories
    },
    yAxis: {
      type: 'value'
    },
    series: [
      {
        type: 'bar',
        data: values,
        itemStyle: {
          color: '#409EFF'
        }
      }
    ]
  }

  chart?.setOption(option)
}

onMounted(initChart)

watch(() => props.data, () => {
  initChart()
}, { deep: true })
</script>

<style scoped>
.difference-chart {
  width: 100%;
  height: 300px;
}
</style>
```

### 4.3 审批流程 (ApprovalFlow.vue)

```vue
<template>
  <div class="approval-flow">
    <el-steps :active="activeStep" align-center finish-status="success">
      <el-step
        v-for="(approval, index) in approvals"
        :key="index"
        :title="approval.approver"
        :description="formatStepDescription(approval)"
      />
    </el-steps>

    <el-timeline class="approval-timeline">
      <el-timeline-item
        v-for="(approval, index) in approvals"
        :key="index"
        :timestamp="formatDateTime(approval.approved_at)"
        :type="getTimelineType(approval.action)"
      >
        <div class="timeline-content">
          <div class="approval-level">
            <el-tag size="small">第{{ approval.level }}级审批</el-tag>
          </div>
          <div class="approval-info">
            <span class="approver">{{ approval.approver }}</span>
            <el-tag :type="getActionType(approval.action)" size="small">
              {{ getActionText(approval.action) }}
            </el-tag>
          </div>
          <div v-if="approval.opinion" class="approval-opinion">
            意见：{{ approval.opinion }}
          </div>
        </div>
      </el-timeline-item>
    </el-timeline>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { formatDateTime } from '@/utils/format'

const props = defineProps<{
  approvals: any[]
}>()

const activeStep = computed(() => {
  const approvedCount = props.approvals.filter(a => a.action === 'approved').length
  return approvedCount
})

const formatStepDescription = (approval: any) => {
  if (approval.action === 'approved') {
    return '已通过'
  } else if (approval.action === 'rejected') {
    return '已拒绝'
  }
  return '待审批'
}

const getTimelineType = (action: string) => {
  if (action === 'approved') return 'success'
  if (action === 'rejected') return 'danger'
  return 'primary'
}

const getActionType = (action: string) => {
  if (action === 'approved') return 'success'
  if (action === 'rejected') return 'danger'
  return 'info'
}

const getActionText = (action: string) => {
  const textMap: Record<string, string> = {
    approved: '同意',
    rejected: '拒绝',
    commented: '意见'
  }
  return textMap[action] || action
}
</script>

<style scoped>
.approval-flow {
  padding: 20px 0;
}

.approval-timeline {
  margin-top: 30px;
}

.timeline-content {
  padding: 10px;
  background: #f5f7fa;
  border-radius: 4px;
}

.approval-level {
  margin-bottom: 8px;
}

.approval-info {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 8px;
}

.approver {
  font-weight: bold;
}

.approval-opinion {
  color: #606266;
  font-size: 14px;
}
</style>
```

---

## 5. API 封装

```typescript
// src/api/inventory/difference.ts

import request from '@/utils/request'

export const differenceApi = {
  // 列表
  list: (params: any) => request.get('/inventory/differences/', { params }),

  // 详情
  detail: (id: number) => request.get(`/inventory/differences/${id}/`),

  // 认定
  confirm: (id: number, data: any) =>
    request.post(`/inventory/differences/${id}/confirm/`, data),

  // 批量认定
  batchConfirm: (data: any) =>
    request.post('/inventory/differences/batch-confirm/', data),

  // 重新分析
  analyze: (data: any) =>
    request.post('/inventory/differences/analyze/', data)
}

// src/api/inventory/resolution.ts

export const resolutionApi = {
  list: (params: any) => request.get('/inventory/resolutions/', { params }),
  detail: (id: number) => request.get(`/inventory/resolutions/${id}/`),
  create: (data: any) => request.post('/inventory/resolutions/', data),
  update: (id: number, data: any) => request.put(`/inventory/resolutions/${id}/`, data),
  delete: (id: number) => request.delete(`/inventory/resolutions/${id}/`),
  submit: (id: number) => request.post(`/inventory/resolutions/${id}/submit/`),
  approve: (id: number, data: any) =>
    request.post(`/inventory/resolutions/${id}/approve/`, data)
}

// src/api/inventory/adjustment.ts

export const adjustmentApi = {
  list: (params: any) => request.get('/inventory/adjustments/', { params }),
  detail: (id: number) => request.get(`/inventory/adjustments/${id}/`),
  rollback: (id: number, data: any) =>
    request.post(`/inventory/adjustments/${id}/rollback/`, data)
}

// src/api/inventory/report.ts

export const reportApi = {
  list: (params: any) => request.get('/inventory/reports/', { params }),
  detail: (id: number) => request.get(`/inventory/reports/${id}/`),
  generate: (data: any) => request.post('/inventory/reports/generate/', data),
  submit: (id: number) => request.post(`/inventory/reports/${id}/submit/`),
  approve: (id: number, data: any) =>
    request.post(`/inventory/reports/${id}/approve/`, data),
  export: (id: number, format: string) =>
    request.get(`/inventory/reports/${id}/export/`, {
      params: { format },
      responseType: 'blob'
    })
}

// src/api/inventory/template.ts

export const templateApi = {
  list: (params?: any) => request.get('/inventory/report-templates/', { params }),
  detail: (id: number) => request.get(`/inventory/report-templates/${id}/`),
  create: (data: any) => request.post('/inventory/report-templates/', data),
  update: (id: number, data: any) =>
    request.put(`/inventory/report-templates/${id}/`, data),
  delete: (id: number) => request.delete(`/inventory/report-templates/${id}/`),
  setDefault: (id: number) =>
    request.post(`/inventory/report-templates/${id}/set-default/`)
}
```

---

## 6. 路由配置

```typescript
// src/router/inventory-reconciliation.ts

export default [
  {
    path: '/inventory/reconciliation',
    component: () => import('@/layouts/MainLayout.vue'),
    meta: { title: '盘点业务链条', icon: 'Reconciliation' },
    children: [
      // 差异管理
      {
        path: 'difference',
        component: () => import('@/views/inventory/reconciliation/difference/DifferenceList.vue'),
        meta: { title: '差异管理' }
      },
      {
        path: 'difference/:id',
        component: () => import('@/views/inventory/reconciliation/difference/DifferenceDetail.vue'),
        meta: { title: '差异详情', hidden: true }
      },
      // 差异处理
      {
        path: 'resolution',
        component: () => import('@/views/inventory/reconciliation/resolution/ResolutionList.vue'),
        meta: { title: '差异处理' }
      },
      {
        path: 'resolution/create',
        component: () => import('@/views/inventory/reconciliation/resolution/ResolutionForm.vue'),
        meta: { title: '新建处理单', hidden: true }
      },
      {
        path: 'resolution/edit/:id',
        component: () => import('@/views/inventory/reconciliation/resolution/ResolutionForm.vue'),
        meta: { title: '编辑处理单', hidden: true }
      },
      {
        path: 'resolution/:id',
        component: () => import('@/views/inventory/reconciliation/resolution/ResolutionDetail.vue'),
        meta: { title: '处理单详情', hidden: true }
      },
      // 资产调账
      {
        path: 'adjustment',
        component: () => import('@/views/inventory/reconciliation/adjustment/AdjustmentList.vue'),
        meta: { title: '资产调账' }
      },
      {
        path: 'adjustment/:id',
        component: () => import('@/views/inventory/reconciliation/adjustment/AdjustmentDetail.vue'),
        meta: { title: '调账详情', hidden: true }
      },
      // 盘点报告
      {
        path: 'report',
        component: () => import('@/views/inventory/reconciliation/report/ReportList.vue'),
        meta: { title: '盘点报告' }
      },
      {
        path: 'report/:id',
        component: () => import('@/views/inventory/reconciliation/report/ReportDetail.vue'),
        meta: { title: '报告详情', hidden: true }
      },
      {
        path: 'report/:id/preview',
        component: () => import('@/views/inventory/reconciliation/report/ReportPreview.vue'),
        meta: { title: '报告预览', hidden: true }
      },
      // 报告模板
      {
        path: 'template',
        component: () => import('@/views/inventory/reconciliation/report/TemplateManage.vue'),
        meta: { title: '报告模板' }
      }
    ]
  }
]
```
