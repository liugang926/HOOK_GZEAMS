## 前端公共组件引用

| 组件名 | 组件路径 | 用途 |
|--------|---------|------|
| BaseListPage | @/components/common/BaseListPage.vue | 列表页面 |
| BaseFormPage | @/components/common/BaseFormPage.vue | 表单页面 |
| BaseDetailPage | @/components/common/BaseDetailPage.vue | 详情页面 |

---

# Phase 1.7: 资产生命周期管理 - 前端实现

## 1. 页面结构

### 1.1 页面层级

```
src/views/lifecycle/
├── purchase/                      # 采购申请
│   ├── RequestList.vue           # 采购申请列表
│   ├── RequestDetail.vue         # 采购申请详情
│   ├── RequestForm.vue           # 采购申请表单
│   └── components/
│       ├── RequestItemsTable.vue # 申请明细表格
│       └── RequestApprovalFlow.vue # 审批流程展示
│
├── receipt/                       # 资产入库
│   ├── ReceiptList.vue           # 验收单列表
│   ├── ReceiptDetail.vue         # 验收单详情
│   ├── ReceiptForm.vue           # 验收单表单
│   └── components/
│       ├── ReceiptItemsTable.vue # 验收明细表格
│       └── AssetGenerationResult.vue # 资产生成结果
│
├── maintenance/                   # 维护保养
│   ├── MaintenanceList.vue       # 维修单列表
│   ├── MaintenanceDetail.vue     # 维修单详情
│   ├── MaintenanceForm.vue       # 维修申请表单
│   ├── MaintenancePlanList.vue   # 保养计划列表
│   ├── MaintenancePlanForm.vue   # 保养计划表单
│   ├── MaintenanceTaskList.vue   # 保养任务列表
│   ├── MaintenanceTaskDetail.vue # 保养任务详情
│   └── components/
│       ├── FaultPhotoUpload.vue  # 故障照片上传
│       ├── TechnicianSelector.vue # 维修人员选择
│       └── TaskCalendar.vue      # 任务日历视图
│
└── disposal/                      # 报废处置
    ├── DisposalList.vue          # 报废申请列表
    ├── DisposalDetail.vue        # 报废申请详情
    ├── DisposalForm.vue          # 报废申请表单
    └── components/
        ├── AssetSelector.vue     # 资产选择器
        ├── AppraisalForm.vue     # 鉴定表单
        └── DisposalExecution.vue # 处置执行
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

## 2. 采购申请模块

### 2.1 采购申请列表 (RequestList.vue)

```vue
<template>
  <div class="purchase-request-list">
    <!-- 搜索筛选区 -->
    <el-card class="search-card">
      <el-form :model="searchForm" inline>
        <el-form-item label="申请单号">
          <el-input v-model="searchForm.request_no" placeholder="请输入申请单号" clearable />
        </el-form-item>
        <el-form-item label="状态">
          <el-select v-model="searchForm.status" placeholder="全部状态" clearable>
            <el-option label="草稿" value="draft" />
            <el-option label="已提交" value="submitted" />
            <el-option label="已审批" value="approved" />
            <el-option label="已拒绝" value="rejected" />
            <el-option label="采购中" value="processing" />
            <el-option label="采购完成" value="completed" />
          </el-select>
        </el-form-item>
        <el-form-item label="申请部门">
          <dept-picker v-model="searchForm.department_id" />
        </el-form-item>
        <el-form-item label="申请日期">
          <el-date-picker
            v-model="searchForm.dateRange"
            type="daterange"
            range-separator="至"
            start-placeholder="开始日期"
            end-placeholder="结束日期"
          />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="handleSearch">查询</el-button>
          <el-button @click="handleReset">重置</el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <!-- 操作按钮区 -->
    <div class="toolbar">
      <el-button type="primary" :icon="Plus" @click="handleCreate">新建申请</el-button>
      <el-button :icon="Download" @click="handleExport">导出</el-button>
    </div>

    <!-- 数据表格 -->
    <el-table
      v-loading="loading"
      :data="tableData"
      border
      stripe
      @row-click="handleRowClick"
    >
      <el-table-column prop="request_no" label="申请单号" width="150" />
      <el-table-column prop="status" label="状态" width="100">
        <template #default="{ row }">
          <el-tag :type="getStatusType(row.status)">
            {{ row.status_display }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="applicant.full_name" label="申请人" width="100" />
      <el-table-column prop="department.name" label="申请部门" width="120" />
      <el-table-column prop="request_date" label="需求日期" width="110" />
      <el-table-column prop="expected_date" label="期望到货" width="110" />
      <el-table-column prop="reason" label="申请原因" min-width="200" show-overflow-tooltip />
      <el-table-column prop="items_total_amount" label="申请金额" width="110" align="right">
        <template #default="{ row }">¥{{ formatMoney(row.items_total_amount) }}</template>
      </el-table-column>
      <el-table-column prop="m18_purchase_order_no" label="M18采购单" width="130" />
      <el-table-column label="操作" width="200" fixed="right">
        <template #default="{ row }">
          <el-button link type="primary" @click.stop="handleView(row)">查看</el-button>
          <el-button
            v-if="row.status === 'draft'"
            link
            type="primary"
            @click.stop="handleEdit(row)"
          >编辑</el-button>
          <el-button
            v-if="row.status === 'draft'"
            link
            type="success"
            @click.stop="handleSubmit(row)"
          >提交</el-button>
          <el-button
            v-if="row.status === 'submitted'"
            link
            type="warning"
            @click.stop="handleApprove(row)"
          >审批</el-button>
          <el-button
            v-if="row.status === 'draft'"
            link
            type="danger"
            @click.stop="handleDelete(row)"
          >删除</el-button>
        </template>
      </el-table-column>
    </el-table>

    <!-- 分页 -->
    <el-pagination
      v-model:current-page="pagination.page"
      v-model:page-size="pagination.pageSize"
      :total="pagination.total"
      :page-sizes="[20, 50, 100]"
      layout="total, sizes, prev, pager, next, jumper"
      @size-change="fetchData"
      @current-change="fetchData"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { Plus, Download } from '@element-plus/icons-vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { purchaseRequestApi } from '@/api/lifecycle/purchase'
import { formatMoney } from '@/utils/format'

const router = useRouter()
const loading = ref(false)
const tableData = ref([])

const searchForm = reactive({
  request_no: '',
  status: '',
  department_id: null,
  dateRange: null
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
    processing: 'primary',
    completed: 'success'
  }
  return typeMap[status] || 'info'
}

const fetchData = async () => {
  loading.value = true
  try {
    const { dateRange, ...params } = searchForm
    if (dateRange) {
      params.date_from = dateRange[0]
      params.date_to = dateRange[1]
    }
    const res = await purchaseRequestApi.list({
      ...params,
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
    request_no: '',
    status: '',
    department_id: null,
    dateRange: null
  })
  handleSearch()
}

const handleCreate = () => {
  router.push('/lifecycle/purchase/create')
}

const handleView = (row: any) => {
  router.push(`/lifecycle/purchase/${row.id}`)
}

const handleEdit = (row: any) => {
  router.push(`/lifecycle/purchase/edit/${row.id}`)
}

const handleSubmit = async (row: any) => {
  try {
    await ElMessageBox.confirm('确认提交该采购申请？', '提示', {
      type: 'warning'
    })
    await purchaseRequestApi.submit(row.id)
    ElMessage.success('提交成功')
    fetchData()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('操作失败')
    }
  }
}

const handleApprove = (row: any) => {
  router.push({
    path: `/lifecycle/purchase/${row.id}`,
    query: { mode: 'approve' }
  })
}

const handleDelete = async (row: any) => {
  try {
    await ElMessageBox.confirm('确认删除该采购申请？', '提示', {
      type: 'warning',
      confirmButtonText: '确定',
      cancelButtonText: '取消'
    })
    await purchaseRequestApi.delete(row.id)
    ElMessage.success('删除成功')
    fetchData()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('删除失败')
    }
  }
}

const handleExport = async () => {
  // TODO: 实现导出功能
  ElMessage.info('导出功能开发中')
}

const handleRowClick = (row: any) => {
  handleView(row)
}

onMounted(() => {
  fetchData()
})
</script>
```

### 2.2 采购申请表单 (RequestForm.vue)

```vue
<template>
  <div class="purchase-request-form">
    <el-form
      ref="formRef"
      :model="formData"
      :rules="formRules"
      label-width="120px"
    >
      <!-- 基本信息 -->
      <el-card class="form-section" header="基本信息">
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="申请部门" prop="department_id">
              <dept-picker v-model="formData.department_id" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="成本中心" prop="cost_center_id">
              <cost-center-picker v-model="formData.cost_center_id" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="需求日期" prop="request_date">
              <el-date-picker
                v-model="formData.request_date"
                type="date"
                placeholder="请选择需求日期"
              />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="期望到货日期" prop="expected_date">
              <el-date-picker
                v-model="formData.expected_date"
                type="date"
                placeholder="请选择期望到货日期"
              />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="预算金额" prop="budget_amount">
              <el-input-number
                v-model="formData.budget_amount"
                :precision="2"
                :min="0"
                :max="99999999"
                controls-position="right"
              />
            </el-form-item>
          </el-col>
        </el-row>
        <el-form-item label="申请原因" prop="reason">
          <el-input
            v-model="formData.reason"
            type="textarea"
            :rows="3"
            placeholder="请详细说明申请原因"
          />
        </el-form-item>
      </el-card>

      <!-- 申请明细 -->
      <el-card class="form-section" header="申请明细">
        <request-items-table v-model="formData.items" />
      </el-card>

      <!-- 附件 -->
      <el-card class="form-section" header="附件">
        <file-upload v-model="formData.attachments" />
      </el-card>

      <!-- 操作按钮 -->
      <div class="form-actions">
        <el-button @click="handleBack">返回</el-button>
        <el-button @click="handleSaveDraft">保存草稿</el-button>
        <el-button type="primary" @click="handleSubmit">提交审批</el-button>
      </div>
    </el-form>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { ElMessage } from 'element-plus'
import type { FormInstance, FormRules } from 'element-plus'
import { purchaseRequestApi } from '@/api/lifecycle/purchase'
import RequestItemsTable from './components/RequestItemsTable.vue'

const router = useRouter()
const route = useRoute()
const formRef = ref<FormInstance>()
const isEdit = ref(false)
const requestId = ref<number>()

const formData = reactive({
  department_id: null,
  cost_center_id: null,
  request_date: '',
  expected_date: '',
  budget_amount: null,
  reason: '',
  items: [{ asset_category_id: null, item_name: '', specification: '', quantity: 1, unit_price: 0 }],
  attachments: []
})

const formRules: FormRules = {
  department_id: [{ required: true, message: '请选择申请部门', trigger: 'change' }],
  request_date: [{ required: true, message: '请选择需求日期', trigger: 'change' }],
  expected_date: [{ required: true, message: '请选择期望到货日期', trigger: 'change' }],
  reason: [{ required: true, message: '请填写申请原因', trigger: 'blur' }]
}

const handleSaveDraft = async () => {
  try {
    if (isEdit.value) {
      await purchaseRequestApi.update(requestId.value, formData)
      ElMessage.success('保存成功')
    } else {
      const res = await purchaseRequestApi.create(formData)
      ElMessage.success('创建成功')
      router.replace(`/lifecycle/purchase/edit/${res.id}`)
    }
  } catch {
    ElMessage.error('保存失败')
  }
}

const handleSubmit = async () => {
  try {
    await formRef.value?.validate()
    await ElMessageBox.confirm('确认提交审批？提交后将无法修改', '提示', {
      type: 'warning'
    })
    const data = isEdit.value
      ? await purchaseRequestApi.update(requestId.value, formData)
      : await purchaseRequestApi.create(formData)
    await purchaseRequestApi.submit(data.id)
    ElMessage.success('提交成功')
    router.push('/lifecycle/purchase')
  } catch {
    // 验证失败或取消
  }
}

const handleBack = () => {
  router.back()
}

onMounted(async () => {
  if (route.params.id) {
    isEdit.value = true
    requestId.value = Number(route.params.id)
    const data = await purchaseRequestApi.detail(requestId.value)
    Object.assign(formData, data)
  }
})
</script>
```

### 2.3 申请明细表格 (RequestItemsTable.vue)

```vue
<template>
  <div class="request-items-table">
    <el-button type="primary" :icon="Plus" @click="handleAdd" style="margin-bottom: 10px">
      添加明细
    </el-button>

    <el-table :data="items" border>
      <el-table-column label="序号" width="60" type="index" />
      <el-table-column label="资产类别" width="150">
        <template #default="{ row, $index }">
          <asset-category-picker v-model="row.asset_category_id" />
        </template>
      </el-table-column>
      <el-table-column label="物品名称" width="200">
        <template #default="{ row }">
          <el-input v-model="row.item_name" placeholder="请输入物品名称" />
        </template>
      </el-table-column>
      <el-table-column label="规格型号" min-width="200">
        <template #default="{ row }">
          <el-input v-model="row.specification" placeholder="请输入规格型号" />
        </template>
      </el-table-column>
      <el-table-column label="品牌" width="120">
        <template #default="{ row }">
          <el-input v-model="row.brand" placeholder="请输入品牌" />
        </template>
      </el-table-column>
      <el-table-column label="数量" width="100">
        <template #default="{ row }">
          <el-input-number v-model="row.quantity" :min="1" :max="9999" controls-position="right" />
        </template>
      </el-table-column>
      <el-table-column label="单位" width="80">
        <template #default="{ row }">
          <el-input v-model="row.unit" placeholder="单位" />
        </template>
      </el-table-column>
      <el-table-column label="单价" width="120">
        <template #default="{ row }">
          <el-input-number v-model="row.unit_price" :precision="2" :min="0" controls-position="right" />
        </template>
      </el-table-column>
      <el-table-column label="金额" width="120">
        <template #default="{ row }">
          ¥{{ (row.quantity * row.unit_price).toFixed(2) }}
        </template>
      </el-table-column>
      <el-table-column label="操作" width="80" fixed="right">
        <template #default="{ $index }">
          <el-button link type="danger" @click="handleDelete($index)">删除</el-button>
        </template>
      </el-table-column>
    </el-table>

    <div class="total-row">
      <span>合计金额：</span>
      <span class="total-amount">¥{{ totalAmount.toFixed(2) }}</span>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { Plus } from '@element-plus/icons-vue'

interface Item {
  asset_category_id: number | null
  item_name: string
  specification: string
  brand: string
  quantity: number
  unit: string
  unit_price: number
}

const props = defineProps<{
  modelValue: Item[]
}>()

const emit = defineEmits<{
  (e: 'update:modelValue', value: Item[]): void
}>()

const items = computed({
  get: () => props.modelValue,
  set: (value) => emit('update:modelValue', value)
})

const totalAmount = computed(() => {
  return items.value.reduce((sum, item) => sum + item.quantity * item.unit_price, 0)
})

const handleAdd = () => {
  items.value.push({
    asset_category_id: null,
    item_name: '',
    specification: '',
    brand: '',
    quantity: 1,
    unit: '',
    unit_price: 0
  })
}

const handleDelete = (index: number) => {
  items.value.splice(index, 1)
}
</script>
```

---

## 3. 资产入库模块

### 3.1 验收单列表 (ReceiptList.vue)

```vue
<template>
  <div class="receipt-list">
    <!-- 搜索筛选区 -->
    <el-card class="search-card">
      <el-form :model="searchForm" inline>
        <el-form-item label="验收单号">
          <el-input v-model="searchForm.receipt_no" placeholder="请输入验收单号" clearable />
        </el-form-item>
        <el-form-item label="状态">
          <el-select v-model="searchForm.status" placeholder="全部状态" clearable>
            <el-option label="草稿" value="draft" />
            <el-option label="已提交" value="submitted" />
            <el-option label="检验中" value="inspecting" />
            <el-option label="验收通过" value="passed" />
            <el-option label="验收不通过" value="rejected" />
          </el-select>
        </el-form-item>
        <el-form-item label="入库类型">
          <el-select v-model="searchForm.receipt_type" placeholder="全部类型" clearable>
            <el-option label="采购入库" value="purchase" />
            <el-option label="调拨入库" value="transfer" />
            <el-option label="退回入库" value="return" />
          </el-select>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="handleSearch">查询</el-button>
          <el-button @click="handleReset">重置</el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <!-- 操作按钮 -->
    <div class="toolbar">
      <el-button type="primary" :icon="Plus" @click="handleCreate">新建验收单</el-button>
    </div>

    <!-- 数据表格 -->
    <el-table v-loading="loading" :data="tableData" border stripe>
      <el-table-column prop="receipt_no" label="验收单号" width="150" />
      <el-table-column prop="status" label="状态" width="100">
        <template #default="{ row }">
          <el-tag :type="getStatusType(row.status)">{{ row.status_display }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="receipt_type" label="入库类型" width="100">
        <template #default="{ row }">{{ row.receipt_type_display }}</template>
      </el-table-column>
      <el-table-column prop="receipt_date" label="验收日期" width="110" />
      <el-table-column prop="supplier" label="供应商" min-width="150" />
      <el-table-column prop="delivery_no" label="送货单号" width="130" />
      <el-table-column prop="receiver.full_name" label="验收人" width="100" />
      <el-table-column label="操作" width="200" fixed="right">
        <template #default="{ row }">
          <el-button link type="primary" @click="handleView(row)">查看</el-button>
          <el-button
            v-if="row.status === 'submitted'"
            link
            type="success"
            @click="handleInspect(row)"
          >验收</el-button>
          <el-button
            v-if="['draft', 'submitted'].includes(row.status)"
            link
            type="primary"
            @click="handleEdit(row)"
          >编辑</el-button>
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
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { Plus } from '@element-plus/icons-vue'
import { useRouter } from 'vue-router'
import { receiptApi } from '@/api/lifecycle/receipt'

const router = useRouter()
const loading = ref(false)
const tableData = ref([])

const searchForm = reactive({
  receipt_no: '',
  status: '',
  receipt_type: ''
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
    inspecting: 'primary',
    passed: 'success',
    rejected: 'danger'
  }
  return typeMap[status] || 'info'
}

const fetchData = async () => {
  loading.value = true
  try {
    const res = await receiptApi.list({
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
    receipt_no: '',
    status: '',
    receipt_type: ''
  })
  handleSearch()
}

const handleCreate = () => {
  router.push('/lifecycle/receipt/create')
}

const handleView = (row: any) => {
  router.push(`/lifecycle/receipt/${row.id}`)
}

const handleEdit = (row: any) => {
  router.push(`/lifecycle/receipt/edit/${row.id}`)
}

const handleInspect = (row: any) => {
  router.push({
    path: `/lifecycle/receipt/${row.id}`,
    query: { mode: 'inspect' }
  })
}

onMounted(fetchData)
</script>
```

### 3.2 验收操作对话框

```vue
<template>
  <el-dialog
    v-model="visible"
    title="资产验收"
    width="80%"
    :close-on-click-modal="false"
  >
    <el-form :model="formData" label-width="100px">
      <!-- 验收结果 -->
      <el-form-item label="验收结果">
        <el-radio-group v-model="formData.result">
          <el-radio label="pass">验收通过</el-radio>
          <el-radio label="reject">验收不通过</el-radio>
        </el-radio-group>
      </el-form-item>

      <!-- 验收明细 -->
      <el-table :data="receiptItems" border>
        <el-table-column prop="item_name" label="物品名称" width="200" />
        <el-table-column prop="specification" label="规格型号" min-width="200" />
        <el-table-column prop="ordered_quantity" label="订购数量" width="100" />
        <el-table-column label="实收数量" width="120">
          <template #default="{ row }">
            <el-input-number
              v-model="row.received_quantity"
              :min="0"
              :max="row.ordered_quantity"
              controls-position="right"
            />
          </template>
        </el-table-column>
        <el-table-column label="合格数量" width="120">
          <template #default="{ row }">
            <el-input-number
              v-model="row.qualified_quantity"
              :min="0"
              :max="row.received_quantity"
              controls-position="right"
            />
          </template>
        </el-table-column>
        <el-table-column label="不合格数量" width="120">
          <template #default="{ row }">
            <el-input-number
              v-model="row.defective_quantity"
              :min="0"
              controls-position="right"
              :disabled="formData.result === 'pass'"
            />
          </template>
        </el-table-column>
        <el-table-column label="备注" width="200">
          <template #default="{ row }">
            <el-input v-model="row.remark" type="textarea" :rows="1" />
          </template>
        </el-table-column>
      </el-table>

      <!-- 验收说明 -->
      <el-form-item label="验收说明">
        <el-input
          v-model="formData.inspection_result"
          type="textarea"
          :rows="3"
          placeholder="请填写验收说明"
        />
      </el-form-item>

      <!-- 资产预览 -->
      <el-collapse v-if="formData.result === 'pass'">
        <el-collapse-item title="将生成的资产卡片预览" name="preview">
          <el-table :data="previewAssets" border>
            <el-table-column prop="asset_name" label="资产名称" />
            <el-table-column prop="specification" label="规格型号" />
            <el-table-column prop="quantity" label="数量" width="80" />
          </el-table>
        </el-collapse-item>
      </el-collapse>
    </el-form>

    <template #footer>
      <el-button @click="visible = false">取消</el-button>
      <el-button type="primary" @click="handleConfirm">确认</el-button>
    </template>
  </el-dialog>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { ElMessage } from 'element-plus'
import { receiptApi } from '@/api/lifecycle/receipt'

const visible = defineModel<boolean>()
const props = defineProps<{
  receiptId: number
  receiptItems: any[]
}>()

const formData = ref({
  result: 'pass',
  inspection_result: ''
})

// 计算将生成的资产卡片
const previewAssets = computed(() => {
  return props.receiptItems
    .filter(item => item.qualified_quantity > 0)
    .map(item => ({
      asset_name: item.item_name,
      specification: item.specification,
      quantity: item.qualified_quantity
    }))
})

const handleConfirm = async () => {
  try {
    if (formData.value.result === 'pass') {
      await receiptApi.passInspection(props.receiptId, {
        inspection_result: formData.value.inspection_result
      })
      ElMessage.success('验收通过，已生成资产卡片')
    } else {
      await receiptApi.rejectInspection(props.receiptId, {
        reason: formData.value.inspection_result
      })
      ElMessage.success('已标记为验收不通过')
    }
    visible.value = false
  } catch {
    ElMessage.error('操作失败')
  }
}
</script>
```

---

## 4. 维护保养模块

### 4.1 维修单列表 (MaintenanceList.vue)

```vue
<template>
  <div class="maintenance-list">
    <!-- Tab切换 -->
    <el-tabs v-model="activeTab" @tab-change="handleTabChange">
      <el-tab-pane label="全部" name="all" />
      <el-tab-pane label="待处理" name="reported" />
      <el-tab-pane label="处理中" name="processing" />
      <el-tab-pane label="已完成" name="completed" />
    </el-tabs>

    <!-- 搜索筛选 -->
    <el-form :model="searchForm" inline class="search-form">
      <el-form-item label="维修单号">
        <el-input v-model="searchForm.maintenance_no" placeholder="请输入" clearable />
      </el-form-item>
      <el-form-item label="资产">
        <asset-picker v-model="searchForm.asset_id" />
      </el-form-item>
      <el-form-item label="优先级">
        <el-select v-model="searchForm.priority" placeholder="全部" clearable>
          <el-option label="紧急" value="urgent" />
          <el-option label="高" value="high" />
          <el-option label="普通" value="normal" />
          <el-option label="低" value="low" />
        </el-select>
      </el-form-item>
      <el-form-item>
        <el-button type="primary" @click="handleSearch">查询</el-button>
        <el-button type="primary" :icon="Plus" @click="handleCreate">报修</el-button>
      </el-form-item>
    </el-form>

    <!-- 维修单卡片 -->
    <div class="maintenance-cards">
      <el-card
        v-for="item in tableData"
        :key="item.id"
        class="maintenance-card"
        :class="`priority-${item.priority}`"
        @click="handleView(item)"
      >
        <template #header>
          <div class="card-header">
            <span class="card-title">{{ item.maintenance_no }}</span>
            <el-tag :type="getStatusType(item.status)" size="small">
              {{ item.status_display }}
            </el-tag>
          </div>
        </template>
        <div class="card-content">
          <div class="asset-info">
            <el-icon><Monitor /></el-icon>
            <span>{{ item.asset.asset_name }}</span>
          </div>
          <div class="fault-desc">{{ item.fault_description }}</div>
          <div class="meta-info">
            <span><el-icon><User /></el-icon> {{ item.reporter.full_name }}</span>
            <span><el-icon><Clock /></el-icon> {{ formatDate(item.report_time) }}</span>
            <el-tag v-if="item.priority === 'urgent'" type="danger" size="small">紧急</el-tag>
          </div>
        </div>
      </el-card>
    </div>

    <!-- 分页 -->
    <el-pagination
      v-model:current-page="pagination.page"
      v-model:page-size="pagination.pageSize"
      :total="pagination.total"
      layout="total, prev, pager, next"
      @current-change="fetchData"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { Plus, Monitor, User, Clock } from '@element-plus/icons-vue'
import { useRouter } from 'vue-router'
import { maintenanceApi } from '@/api/lifecycle/maintenance'
import { formatDate } from '@/utils/format'

const router = useRouter()
const activeTab = ref('all')
const tableData = ref([])

const searchForm = reactive({
  maintenance_no: '',
  asset_id: null,
  priority: ''
})

const pagination = reactive({
  page: 1,
  pageSize: 20,
  total: 0
})

const getStatusType = (status: string) => {
  const typeMap: Record<string, string> = {
    reported: 'info',
    assigned: 'warning',
    processing: 'primary',
    completed: 'success',
    cancelled: 'danger'
  }
  return typeMap[status] || 'info'
}

const fetchData = async () => {
  const params: any = { ...searchForm, page: pagination.page, page_size: pagination.pageSize }
  if (activeTab.value !== 'all') {
    params.status = activeTab.value
  }
  const res = await maintenanceApi.list(params)
  tableData.value = res.results
  pagination.total = res.count
}

const handleTabChange = () => {
  pagination.page = 1
  fetchData()
}

const handleSearch = () => {
  pagination.page = 1
  fetchData()
}

const handleCreate = () => {
  router.push('/lifecycle/maintenance/create')
}

const handleView = (row: any) => {
  router.push(`/lifecycle/maintenance/${row.id}`)
}

onMounted(fetchData)
</script>

<style scoped>
.maintenance-cards {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(350px, 1fr));
  gap: 16px;
  margin: 16px 0;
}

.maintenance-card {
  cursor: pointer;
  transition: all 0.3s;
}

.maintenance-card:hover {
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
  transform: translateY(-2px);
}

.maintenance-card.priority-urgent {
  border-left: 4px solid #f56c6c;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.card-title {
  font-weight: bold;
  font-size: 16px;
}

.fault-desc {
  color: #606266;
  margin: 12px 0;
  min-height: 40px;
}

.meta-info {
  display: flex;
  gap: 16px;
  color: #909399;
  font-size: 13px;
}

.meta-info span {
  display: flex;
  align-items: center;
  gap: 4px;
}
</style>
```

### 4.2 维修申请表单 (MaintenanceForm.vue)

```vue
<template>
  <el-form
    ref="formRef"
    :model="formData"
    :rules="formRules"
    label-width="120px"
  >
    <el-card header="报修信息">
      <el-form-item label="报修资产" prop="asset_id">
        <asset-picker v-model="formData.asset_id" />
      </el-form-item>
      <el-form-item label="优先级" prop="priority">
        <el-radio-group v-model="formData.priority">
          <el-radio label="low">低</el-radio>
          <el-radio label="normal">普通</el-radio>
          <el-radio label="high">高</el-radio>
          <el-radio label="urgent">紧急</el-radio>
        </el-radio-group>
      </el-form-item>
      <el-form-item label="故障描述" prop="fault_description">
        <el-input
          v-model="formData.fault_description"
          type="textarea"
          :rows="4"
          placeholder="请详细描述故障情况"
        />
      </el-form-item>
      <el-form-item label="故障照片">
        <fault-photo-upload v-model="formData.fault_photo_urls" />
      </el-form-item>
    </el-card>

    <div class="form-actions">
      <el-button @click="handleBack">取消</el-button>
      <el-button type="primary" @click="handleSubmit">提交报修</el-button>
    </div>
  </el-form>
</template>

<script setup lang="ts">
import { ref, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import type { FormInstance, FormRules } from 'element-plus'
import { maintenanceApi } from '@/api/lifecycle/maintenance'
import FaultPhotoUpload from './components/FaultPhotoUpload.vue'

const router = useRouter()
const formRef = ref<FormInstance>()

const formData = reactive({
  asset_id: null,
  priority: 'normal',
  fault_description: '',
  fault_photo_urls: []
})

const formRules: FormRules = {
  asset_id: [{ required: true, message: '请选择报修资产', trigger: 'change' }],
  fault_description: [{ required: true, message: '请填写故障描述', trigger: 'blur' }]
}

const handleSubmit = async () => {
  try {
    await formRef.value?.validate()
    await maintenanceApi.create(formData)
    ElMessage.success('报修提交成功')
    router.push('/lifecycle/maintenance')
  } catch {
    // 验证失败
  }
}

const handleBack = () => {
  router.back()
}
</script>
```

### 4.3 保养任务日历 (TaskCalendar.vue)

```vue
<template>
  <div class="task-calendar">
    <div class="calendar-header">
      <el-button-group>
        <el-button :icon="ArrowLeft" @click="handlePrevMonth" />
        <el-button>{{ currentMonth }}</el-button>
        <el-button :icon="ArrowRight" @click="handleNextMonth" />
      </el-button-group>
      <div class="legend">
        <span class="legend-item"><span class="dot pending"></span>待执行</span>
        <span class="legend-item"><span class="dot in-progress"></span>进行中</span>
        <span class="legend-item"><span class="dot completed"></span>已完成</span>
        <span class="legend-item"><span class="dot overdue"></span>已逾期</span>
      </div>
    </div>

    <div class="calendar-grid">
      <div class="weekday-header">
        <div v-for="day in weekdays" :key="day" class="weekday">{{ day }}</div>
      </div>
      <div class="calendar-days">
        <div
          v-for="(day, index) in calendarDays"
          :key="index"
          class="calendar-day"
          :class="{ 'other-month': day.otherMonth, today: day.isToday }"
          @click="handleDayClick(day)"
        >
          <span class="day-number">{{ day.date }}</span>
          <div class="day-tasks">
            <div
              v-for="task in day.tasks"
              :key="task.id"
              class="task-item"
              :class="`status-${task.status}`"
              @click.stop="handleTaskClick(task)"
            >
              {{ task.asset_name }}
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 任务详情抽屉 -->
    <el-drawer v-model="drawerVisible" title="任务详情" size="400">
      <task-detail v-if="selectedTask" :task-id="selectedTask.id" @close="drawerVisible = false" />
    </el-drawer>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { ArrowLeft, ArrowRight } from '@element-plus/icons-vue'
import { maintenanceTaskApi } from '@/api/lifecycle/maintenance'

const weekdays = ['日', '一', '二', '三', '四', '五', '六']
const currentDate = ref(new Date())
const tasks = ref<any[]>([])
const drawerVisible = ref(false)
const selectedTask = ref<any>(null)

const currentMonth = computed(() => {
  return `${currentDate.value.getFullYear()}年${currentDate.value.getMonth() + 1}月`
})

const calendarDays = computed(() => {
  const year = currentDate.value.getFullYear()
  const month = currentDate.value.getMonth()
  const firstDay = new Date(year, month, 1)
  const lastDay = new Date(year, month + 1, 0)
  const startDayOfWeek = firstDay.getDay()
  const daysInMonth = lastDay.getDate()

  const days: any[] = []

  // 上个月的日期
  const prevMonth = new Date(year, month, 0)
  for (let i = startDayOfWeek - 1; i >= 0; i--) {
    days.push({
      date: prevMonth.getDate() - i,
      otherMonth: true,
      isToday: false,
      fullDate: new Date(year, month - 1, prevMonth.getDate() - i),
      tasks: []
    })
  }

  // 当月日期
  const today = new Date()
  for (let i = 1; i <= daysInMonth; i++) {
    const date = new Date(year, month, i)
    const dateStr = formatDate(date)
    days.push({
      date: i,
      otherMonth: false,
      isToday: isSameDay(date, today),
      fullDate: date,
      tasks: tasks.value.filter(t => t.scheduled_date === dateStr)
    })
  }

  // 下个月的日期
  const remainingDays = 42 - days.length
  for (let i = 1; i <= remainingDays; i++) {
    days.push({
      date: i,
      otherMonth: true,
      isToday: false,
      fullDate: new Date(year, month + 1, i),
      tasks: []
    })
  }

  return days
})

const fetchTasks = async () => {
  const year = currentDate.value.getFullYear()
  const month = currentDate.value.getMonth() + 1
  const res = await maintenanceTaskApi.list({
    scheduled_date_from: `${year}-${String(month).padStart(2, '0')}-01`,
    scheduled_date_to: `${year}-${String(month).padStart(2, '0')}-31`
  })
  tasks.value = res.results
}

const handlePrevMonth = () => {
  currentDate.value = new Date(currentDate.value.setMonth(currentDate.value.getMonth() - 1))
  fetchTasks()
}

const handleNextMonth = () => {
  currentDate.value = new Date(currentDate.value.setMonth(currentDate.value.getMonth() + 1))
  fetchTasks()
}

const handleDayClick = (day: any) => {
  if (day.tasks.length > 0) {
    // 显示当天任务列表
  }
}

const handleTaskClick = (task: any) => {
  selectedTask.value = task
  drawerVisible.value = true
}

const formatDate = (date: Date) => {
  return `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}-${String(date.getDate()).padStart(2, '0')}`
}

const isSameDay = (d1: Date, d2: Date) => {
  return d1.getFullYear() === d2.getFullYear() &&
    d1.getMonth() === d2.getMonth() &&
    d1.getDate() === d2.getDate()
}

onMounted(fetchTasks)
</script>

<style scoped>
.task-calendar {
  padding: 20px;
}

.calendar-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.legend {
  display: flex;
  gap: 16px;
}

.legend-item {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 13px;
}

.dot {
  width: 10px;
  height: 10px;
  border-radius: 50%;
}

.dot.pending { background: #909399; }
.dot.in-progress { background: #409eff; }
.dot.completed { background: #67c23a; }
.dot.overdue { background: #f56c6c; }

.calendar-grid {
  border: 1px solid #dcdfe6;
}

.weekday-header {
  display: grid;
  grid-template-columns: repeat(7, 1fr);
  background: #f5f7fa;
}

.weekday {
  padding: 10px;
  text-align: center;
  font-weight: bold;
  border-right: 1px solid #dcdfe6;
}

.calendar-days {
  display: grid;
  grid-template-columns: repeat(7, 1fr);
}

.calendar-day {
  min-height: 100px;
  padding: 8px;
  border-top: 1px solid #dcdfe6;
  border-right: 1px solid #dcdfe6;
  cursor: pointer;
}

.calendar-day:hover {
  background: #f5f7fa;
}

.calendar-day.other-month {
  background: #fafafa;
  color: #c0c4cc;
}

.calendar-day.today {
  background: #ecf5ff;
}

.day-number {
  font-size: 14px;
  font-weight: bold;
}

.day-tasks {
  margin-top: 4px;
}

.task-item {
  padding: 2px 6px;
  margin-bottom: 2px;
  font-size: 12px;
  border-radius: 3px;
  cursor: pointer;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.task-item.status-pending { background: #e4e7ed; color: #606266; }
.task-item.status-in_progress { background: #d9ecff; color: #409eff; }
.task-item.status-completed { background: #e1f3d8; color: #67c23a; }
.task-item.status-overdue { background: #fde2e2; color: #f56c6c; }
</style>
```

---

## 5. 报废处置模块

### 5.1 报废申请表单 (DisposalForm.vue)

```vue
<template>
  <el-form
    ref="formRef"
    :model="formData"
    :rules="formRules"
    label-width="120px"
  >
    <el-card header="基本信息">
      <el-form-item label="申请部门" prop="department_id">
        <dept-picker v-model="formData.department_id" />
      </el-form-item>
      <el-form-item label="处置方式" prop="disposal_type">
        <el-radio-group v-model="formData.disposal_type">
          <el-radio label="scrap">报废</el-radio>
          <el-radio label="sale">出售</el-radio>
          <el-radio label="donation">捐赠</el-radio>
          <el-radio label="transfer">调拨</el-radio>
          <el-radio label="destroy">销毁</el-radio>
        </el-radio-group>
      </el-form-item>
      <el-form-item label="处置原因" prop="reason_type">
        <el-select v-model="formData.reason_type" placeholder="请选择">
          <el-option label="损坏无法修复" value="damage" />
          <el-option label="技术淘汰" value="obsolete" />
          <el-option label="使用年限到期" value="expired" />
          <el-option label="闲置多余" value="excess" />
          <el-option label="其他原因" value="other" />
        </el-select>
      </el-form-item>
      <el-form-item label="详细说明" prop="disposal_reason">
        <el-input
          v-model="formData.disposal_reason"
          type="textarea"
          :rows="3"
          placeholder="请详细说明处置原因"
        />
      </el-form-item>
    </el-card>

    <el-card header="报废资产">
      <asset-selector
        v-model="formData.asset_ids"
        :department-id="formData.department_id"
        :multiple="true"
      />
    </el-card>

    <!-- 资产预览 -->
    <el-card v-if="previewAssets.length > 0" header="资产信息预览">
      <el-table :data="previewAssets" border>
        <el-table-column prop="asset_no" label="资产编号" width="150" />
        <el-table-column prop="asset_name" label="资产名称" min-width="150" />
        <el-table-column prop="category.name" label="资产类别" width="120" />
        <el-table-column prop="original_value" label="原值" width="120" align="right">
          <template #default="{ row }">¥{{ formatMoney(row.original_value) }}</template>
        </el-table-column>
        <el-table-column prop="accumulated_depreciation" label="累计折旧" width="120" align="right">
          <template #default="{ row }">¥{{ formatMoney(row.accumulated_depreciation) }}</template>
        </el-table-column>
        <el-table-column prop="net_value" label="净值" width="120" align="right">
          <template #default="{ row }">¥{{ formatMoney(row.net_value) }}</template>
        </el-table-column>
      </el-table>
      <div class="total-summary">
        <span>合计原值：¥{{ formatMoney(totalOriginalValue) }}</span>
        <span>合计净值：¥{{ formatMoney(totalNetValue) }}</span>
      </div>
    </el-card>

    <div class="form-actions">
      <el-button @click="handleBack">返回</el-button>
      <el-button type="primary" @click="handleSubmit">提交申请</el-button>
    </div>
  </el-form>
</template>

<script setup lang="ts">
import { ref, reactive, computed } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import type { FormInstance, FormRules } from 'element-plus'
import { disposalApi } from '@/api/lifecycle/disposal'
import { assetApi } from '@/api/assets'
import { formatMoney } from '@/utils/format'

const router = useRouter()
const formRef = ref<FormInstance>()

const formData = reactive({
  department_id: null,
  disposal_type: 'scrap',
  reason_type: '',
  disposal_reason: '',
  asset_ids: []
})

const formRules: FormRules = {
  department_id: [{ required: true, message: '请选择申请部门', trigger: 'change' }],
  disposal_type: [{ required: true, message: '请选择处置方式', trigger: 'change' }],
  reason_type: [{ required: true, message: '请选择处置原因', trigger: 'change' }],
  disposal_reason: [{ required: true, message: '请填写详细说明', trigger: 'blur' }]
}

const assetsMap = ref<Map<number, any>>(new Map())

const previewAssets = computed(() => {
  return formData.asset_ids.map(id => assetsMap.value.get(id)).filter(Boolean)
})

const totalOriginalValue = computed(() => {
  return previewAssets.value.reduce((sum, item) => sum + Number(item.original_value), 0)
})

const totalNetValue = computed(() => {
  return previewAssets.value.reduce((sum, item) => sum + Number(item.net_value), 0)
})

const handleSubmit = async () => {
  try {
    await formRef.value?.validate()
    await disposalApi.create(formData)
    ElMessage.success('提交成功')
    router.push('/lifecycle/disposal')
  } catch {
    // 验证失败
  }
}

const handleBack = () => {
  router.back()
}
</script>
```

### 5.2 资产选择器 (AssetSelector.vue)

```vue
<template>
  <div class="asset-selector">
    <el-button type="primary" :icon="Plus" @click="dialogVisible = true">
      选择资产
    </el-button>

    <el-table :data="selectedAssets" border style="margin-top: 10px">
      <el-table-column prop="asset_no" label="资产编号" width="150" />
      <el-table-column prop="asset_name" label="资产名称" />
      <el-table-column label="操作" width="80">
        <template #default="{ $index }">
          <el-button link type="danger" @click="handleRemove($index)">移除</el-button>
        </template>
      </el-table-column>
    </el-table>

    <!-- 选择对话框 -->
    <el-dialog
      v-model="dialogVisible"
      title="选择资产"
      width="80%"
      :close-on-click-modal="false"
    >
      <el-form :model="searchForm" inline>
        <el-form-item label="资产编号">
          <el-input v-model="searchForm.asset_no" placeholder="请输入" clearable />
        </el-form-item>
        <el-form-item label="资产名称">
          <el-input v-model="searchForm.asset_name" placeholder="请输入" clearable />
        </el-form-item>
        <el-form-item label="资产类别">
          <asset-category-picker v-model="searchForm.category_id" />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="handleSearch">查询</el-button>
        </el-form-item>
      </el-form>

      <el-table
        ref="tableRef"
        :data="tableData"
        border
        @selection-change="handleSelectionChange"
      >
        <el-table-column type="selection" width="55" :selectable="checkSelectable" />
        <el-table-column prop="asset_no" label="资产编号" width="150" />
        <el-table-column prop="asset_name" label="资产名称" />
        <el-table-column prop="category.name" label="资产类别" width="120" />
        <el-table-column prop="original_value" label="原值" width="120" align="right">
          <template #default="{ row }">¥{{ formatMoney(row.original_value) }}</template>
        </el-table-column>
        <el-table-column prop="net_value" label="净值" width="120" align="right">
          <template #default="{ row }">¥{{ formatMoney(row.net_value) }}</template>
        </el-table-column>
      </el-table>

      <el-pagination
        v-model:current-page="pagination.page"
        v-model:page-size="pagination.pageSize"
        :total="pagination.total"
        layout="total, prev, pager, next"
        @current-change="fetchData"
      />

      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleConfirm">确定</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, watch } from 'vue'
import { Plus } from '@element-plus/icons-vue'
import { assetApi } from '@/api/assets'
import { formatMoney } from '@/utils/format'

const props = defineProps<{
  modelValue: number[]
  departmentId?: number | null
  multiple?: boolean
}>()

const emit = defineEmits<{
  (e: 'update:modelValue', value: number[]): void
}>()

const dialogVisible = ref(false)
const tableRef = ref()
const tableData = ref([])
const selection = ref<any[]>([])

const searchForm = reactive({
  asset_no: '',
  asset_name: '',
  category_id: null,
  status: 'in_use'
})

const pagination = reactive({
  page: 1,
  pageSize: 20,
  total: 0
})

// 已选资产详情
const selectedAssetsData = ref<any[]>([])

const selectedAssets = computed(() => {
  return props.modelValue.map(id => selectedAssetsData.value.find(a => a.id === id)).filter(Boolean)
})

const checkSelectable = (row: any) => {
  // 检查是否已选择
  return !props.modelValue.includes(row.id)
}

const fetchData = async () => {
  const params: any = {
    ...searchForm,
    page: pagination.page,
    page_size: pagination.pageSize
  }
  if (props.departmentId) {
    params.department_id = props.departmentId
  }
  const res = await assetApi.list(params)
  tableData.value = res.results
  pagination.total = res.count
}

const handleSearch = () => {
  pagination.page = 1
  fetchData()
}

const handleSelectionChange = (val: any[]) => {
  selection.value = val
}

const handleConfirm = () => {
  const selectedIds = [...props.modelValue]
  selection.value.forEach(item => {
    if (!selectedIds.includes(item.id)) {
      selectedIds.push(item.id)
      selectedAssetsData.value.push(item)
    }
  })
  emit('update:modelValue', selectedIds)
  dialogVisible.value = false
}

const handleRemove = (index: number) => {
  const newIds = [...props.modelValue]
  newIds.splice(index, 1)
  emit('update:modelValue', newIds)
}

watch(dialogVisible, (val) => {
  if (val) {
    fetchData()
  }
})
</script>
```

---

## 6. API 封装

```typescript
// src/api/lifecycle/purchase.ts

import request from '@/utils/request'

export const purchaseRequestApi = {
  // 列表
  list: (params: any) => request.get('/lifecycle/purchase-requests/', { params }),

  // 详情
  detail: (id: number) => request.get(`/lifecycle/purchase-requests/${id}/`),

  // 创建
  create: (data: any) => request.post('/lifecycle/purchase-requests/', data),

  // 更新
  update: (id: number, data: any) => request.put(`/lifecycle/purchase-requests/${id}/`, data),

  // 删除
  delete: (id: number) => request.delete(`/lifecycle/purchase-requests/${id}/`),

  // 提交审批
  submit: (id: number) => request.post(`/lifecycle/purchase-requests/${id}/submit/`),

  // 审批
  approve: (id: number, data: any) => request.post(`/lifecycle/purchase-requests/${id}/approve/`, data),

  // 取消
  cancel: (id: number, data: any) => request.post(`/lifecycle/purchase-requests/${id}/cancel/`, data)
}

// src/api/lifecycle/receipt.ts

export const receiptApi = {
  list: (params: any) => request.get('/lifecycle/asset-receipts/', { params }),
  detail: (id: number) => request.get(`/lifecycle/asset-receipts/${id}/`),
  create: (data: any) => request.post('/lifecycle/asset-receipts/', data),
  update: (id: number, data: any) => request.put(`/lifecycle/asset-receipts/${id}/`, data),
  delete: (id: number) => request.delete(`/lifecycle/asset-receipts/${id}/`),
  submit: (id: number) => request.post(`/lifecycle/asset-receipts/${id}/submit/`),
  passInspection: (id: number, data: any) => request.post(`/lifecycle/asset-receipts/${id}/pass-inspection/`, data),
  rejectInspection: (id: number, data: any) => request.post(`/lifecycle/asset-receipts/${id}/reject-inspection/`, data)
}

// src/api/lifecycle/maintenance.ts

export const maintenanceApi = {
  list: (params: any) => request.get('/lifecycle/maintenance/', { params }),
  detail: (id: number) => request.get(`/lifecycle/maintenance/${id}/`),
  create: (data: any) => request.post('/lifecycle/maintenance/', data),
  update: (id: number, data: any) => request.put(`/lifecycle/maintenance/${id}/`, data),
  assign: (id: number, data: any) => request.post(`/lifecycle/maintenance/${id}/assign/`, data),
  complete: (id: number, data: any) => request.post(`/lifecycle/maintenance/${id}/complete/`, data),
  verify: (id: number, data: any) => request.post(`/lifecycle/maintenance/${id}/verify/`, data)
}

export const maintenancePlanApi = {
  list: (params: any) => request.get('/lifecycle/maintenance-plans/', { params }),
  detail: (id: number) => request.get(`/lifecycle/maintenance-plans/${id}/`),
  create: (data: any) => request.post('/lifecycle/maintenance-plans/', data),
  update: (id: number, data: any) => request.put(`/lifecycle/maintenance-plans/${id}/`, data),
  delete: (id: number) => request.delete(`/lifecycle/maintenance-plans/${id}/`)
}

export const maintenanceTaskApi = {
  list: (params: any) => request.get('/lifecycle/maintenance-tasks/', { params }),
  detail: (id: number) => request.get(`/lifecycle/maintenance-tasks/${id}/`),
  execute: (id: number, data: any) => request.post(`/lifecycle/maintenance-tasks/${id}/execute/`, data)
}

// src/api/lifecycle/disposal.ts

export const disposalApi = {
  list: (params: any) => request.get('/lifecycle/disposal-requests/', { params }),
  detail: (id: number) => request.get(`/lifecycle/disposal-requests/${id}/`),
  create: (data: any) => request.post('/lifecycle/disposal-requests/', data),
  update: (id: number, data: any) => request.put(`/lifecycle/disposal-requests/${id}/`, data),
  delete: (id: number) => request.delete(`/lifecycle/disposal-requests/${id}/`),
  submitAppraisal: (id: number) => request.post(`/lifecycle/disposal-requests/${id}/submit-appraisal/`),
  completeAppraisal: (itemId: number, data: any) => request.post(`/lifecycle/disposal-requests/items/${itemId}/complete-appraisal/`, data),
  execute: (id: number, data: any) => request.post(`/lifecycle/disposal-requests/${id}/execute/`, data)
}
```

---

## 7. 路由配置

```typescript
// src/router/lifecycle.ts

export default [
  {
    path: '/lifecycle',
    component: () => import('@/layouts/MainLayout.vue'),
    meta: { title: '资产生命周期', icon: 'Lifecycle' },
    children: [
      // 采购申请
      {
        path: 'purchase',
        component: () => import('@/views/lifecycle/purchase/RequestList.vue'),
        meta: { title: '采购申请' }
      },
      {
        path: 'purchase/create',
        component: () => import('@/views/lifecycle/purchase/RequestForm.vue'),
        meta: { title: '新建采购申请', hidden: true }
      },
      {
        path: 'purchase/edit/:id',
        component: () => import('@/views/lifecycle/purchase/RequestForm.vue'),
        meta: { title: '编辑采购申请', hidden: true }
      },
      {
        path: 'purchase/:id',
        component: () => import('@/views/lifecycle/purchase/RequestDetail.vue'),
        meta: { title: '采购申请详情', hidden: true }
      },
      // 资产入库
      {
        path: 'receipt',
        component: () => import('@/views/lifecycle/receipt/ReceiptList.vue'),
        meta: { title: '资产入库' }
      },
      {
        path: 'receipt/create',
        component: () => import('@/views/lifecycle/receipt/ReceiptForm.vue'),
        meta: { title: '新建验收单', hidden: true }
      },
      {
        path: 'receipt/:id',
        component: () => import('@/views/lifecycle/receipt/ReceiptDetail.vue'),
        meta: { title: '验收单详情', hidden: true }
      },
      // 维护保养
      {
        path: 'maintenance',
        component: () => import('@/views/lifecycle/maintenance/MaintenanceList.vue'),
        meta: { title: '维修管理' }
      },
      {
        path: 'maintenance/create',
        component: () => import('@/views/lifecycle/maintenance/MaintenanceForm.vue'),
        meta: { title: '新建报修', hidden: true }
      },
      {
        path: 'maintenance/:id',
        component: () => import('@/views/lifecycle/maintenance/MaintenanceDetail.vue'),
        meta: { title: '维修单详情', hidden: true }
      },
      {
        path: 'maintenance-plan',
        component: () => import('@/views/lifecycle/maintenance/MaintenancePlanList.vue'),
        meta: { title: '保养计划' }
      },
      {
        path: 'maintenance-plan/create',
        component: () => import('@/views/lifecycle/maintenance/MaintenancePlanForm.vue'),
        meta: { title: '新建保养计划', hidden: true }
      },
      {
        path: 'maintenance-task',
        component: () => import('@/views/lifecycle/maintenance/MaintenanceTaskList.vue'),
        meta: { title: '保养任务' }
      },
      // 报废处置
      {
        path: 'disposal',
        component: () => import('@/views/lifecycle/disposal/DisposalList.vue'),
        meta: { title: '报废处置' }
      },
      {
        path: 'disposal/create',
        component: () => import('@/views/lifecycle/disposal/DisposalForm.vue'),
        meta: { title: '新建报废申请', hidden: true }
      },
      {
        path: 'disposal/:id',
        component: () => import('@/views/lifecycle/disposal/DisposalDetail.vue'),
        meta: { title: '报废申请详情', hidden: true }
      }
    ]
  }
]
```
