## 前端公共组件引用

| 组件名 | 组件路径 | 用途 |
|--------|---------|------|
| BaseListPage | @/components/common/BaseListPage.vue | 列表页面 |
| BaseFormPage | @/components/common/BaseFormPage.vue | 表单页面 |
| BaseDetailPage | @/components/common/BaseDetailPage.vue | 详情页面 |

---

# Phase 1.6: 低值易耗品/办公用品管理 - 前端实现

## 组件结构

```
src/views/consumables/
├── ConsumableList.vue          # 耗材档案列表
├── ConsumableForm.vue          # 耗品档案表单
├── PurchaseList.vue            # 采购单列表
├── PurchaseForm.vue            # 采购单表单
├── IssueList.vue               # 领用单列表
├── IssueForm.vue               # 领用单表单
├── ReturnList.vue              # 退库单列表
├── ReturnForm.vue              # 退库单表单
├── InventoryList.vue           # 盘点单列表
├── InventoryForm.vue           # 盘点单表单
├── StockMovement.vue           # 库存流水查询
└── components/
    ├── ConsumableSelector.vue  # 耗材选择器
    ├── StockAlertPanel.vue     # 库存预警面板
    └── StockSummaryCard.vue    # 库存汇总卡片
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

## 1. 耗材档案组件

### ConsumableList.vue - 耗材档案列表

```vue
<template>
  <div class="consumable-list">
    <el-page-header @back="goBack" title="返回">
      <template #content>
        <span class="text-large font-600">低值易耗品</span>
      </template>
      <template #extra>
        <el-button type="primary" :icon="Plus" @click="handleCreate">新增耗材</el-button>
      </template>
    </el-page-header>

    <!-- 统计卡片 -->
    <el-row :gutter="20" class="summary-cards">
      <el-col :span="6">
        <el-card shadow="hover">
          <el-statistic title="总品种数" :value="summary.total_items">
            <template #suffix>种</template>
          </el-statistic>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="hover">
          <el-statistic title="库存总值" :value="summary.total_value" :precision="2">
            <template #prefix>¥</template>
          </el-statistic>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="hover">
          <el-statistic title="低库存" :value="summary.total_low_stock">
            <template #suffix>种</template>
          </el-statistic>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="hover">
          <el-statistic title="缺货" :value="summary.total_out_of_stock">
            <template #suffix>种</template>
          </el-statistic>
        </el-card>
      </el-col>
    </el-row>

    <!-- 低库存预警 -->
    <el-alert
      v-if="hasLowStock"
      title="库存预警"
      type="warning"
      :description="`发现 ${summary.total_low_stock + summary.total_out_of_stock} 种耗材库存不足或已缺货，请及时补货`"
      show-icon
      closable
      class="mt-4"
    />

    <!-- 筛选条件 -->
    <el-card class="filter-card" shadow="never">
      <el-form :model="filterForm" inline>
        <el-form-item label="分类">
          <el-tree-select
            v-model="filterForm.category"
            :data="categoryOptions"
            :props="{ value: 'id', label: 'name', children: 'children' }"
            placeholder="全部分类"
            clearable
            check-strictly
            @change="handleSearch"
          />
        </el-form-item>
        <el-form-item label="状态">
          <el-select v-model="filterForm.status" clearable placeholder="全部状态" @change="handleSearch">
            <el-option label="正常" value="normal" />
            <el-option label="库存不足" value="low_stock" />
            <el-option label="缺货" value="out_of_stock" />
            <el-option label="停用" value="discontinued" />
          </el-select>
        </el-form-item>
        <el-form-item label="搜索">
          <el-input
            v-model="filterForm.search"
            placeholder="编码/名称/品牌"
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

    <!-- 数据表格 -->
    <el-card shadow="never">
      <el-table
        v-loading="loading"
        :data="tableData"
        @row-click="handleRowClick"
        style="width: 100%"
      >
        <el-table-column prop="code" label="编码" width="120" />
        <el-table-column prop="name" label="名称" width="200" />
        <el-table-column prop="category.name" label="分类" width="120" />
        <el-table-column prop="specification" label="规格型号" width="150" />
        <el-table-column prop="brand" label="品牌" width="100" />

        <el-table-column label="库存" width="120">
          <template #default="{ row }">
            <div class="stock-info">
              <span :class="getStockClass(row)">
                {{ row.available_stock }} / {{ row.max_stock }}
              </span>
              <span class="unit">{{ row.unit }}</span>
            </div>
            <el-progress
              :percentage="getStockPercentage(row)"
              :color="getProgressColor(row)"
              :show-text="false"
              :stroke-width="4"
            />
          </template>
        </el-table-column>

        <el-table-column prop="average_price" label="平均价格" width="100">
          <template #default="{ row }">¥{{ row.average_price }}</template>
        </el-table-column>

        <el-table-column label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="getStatusType(row.status)">
              {{ getStatusLabel(row.status) }}
            </el-tag>
          </template>
        </el-table-column>

        <el-table-column prop="warehouse.name" label="存放仓库" width="120" />

        <el-table-column label="操作" width="220" fixed="right">
          <template #default="{ row }">
            <el-button link type="primary" @click.stop="handleView(row)">查看</el-button>
            <el-button link type="primary" @click.stop="handleEdit(row)">编辑</el-button>
            <el-button link type="primary" @click.stop="handleViewStock(row)">流水</el-button>
            <el-button link type="success" @click.stop="handleQuickIssue(row)">领用</el-button>
          </template>
        </el-table-column>
      </el-table>

      <!-- 分页 -->
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

    <!-- 库存流水弹窗 -->
    <StockMovementDialog
      v-model="stockMovementVisible"
      :consumable="currentConsumable"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { Plus, Search } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import { getConsumables, getStockSummary } from '@/api/consumables'
import { getConsumableCategories } from '@/api/consumables/category'
import StockMovementDialog from './components/StockMovementDialog.vue'

const router = useRouter()

interface Consumable {
  id: number
  code: string
  name: string
  category: { id: number; name: string }
  specification: string
  brand: string
  unit: string
  available_stock: number
  max_stock: number
  average_price: number
  status: string
  warehouse: { name: string }
}

const loading = ref(false)
const tableData = ref<Consumable[]>([])
const stockMovementVisible = ref(false)
const currentConsumable = ref<Consumable | null>(null)

const categoryOptions = ref([])

const filterForm = reactive({
  category: null,
  status: '',
  search: ''
})

const pagination = reactive({
  page: 1,
  page_size: 20,
  total: 0
})

const summary = ref({
  total_items: 0,
  total_value: 0,
  total_low_stock: 0,
  total_out_of_stock: 0
})

const hasLowStock = computed(() => {
  return summary.value.total_low_stock > 0 || summary.value.total_out_of_stock > 0
})

const getStockClass = (row: Consumable) => {
  if (row.status === 'out_of_stock') return 'text-danger'
  if (row.status === 'low_stock') return 'text-warning'
  return 'text-success'
}

const getStockPercentage = (row: Consumable) => {
  if (row.max_stock === 0) return 0
  return Math.min((row.available_stock / row.max_stock) * 100, 100)
}

const getProgressColor = (row: Consumable) => {
  const percentage = getStockPercentage(row)
  if (percentage <= 20) return '#f56c6c'
  if (percentage <= 50) return '#e6a23c'
  return '#67c23a'
}

const getStatusType = (status: string) => {
  const types: Record<string, string> = {
    normal: 'success',
    low_stock: 'warning',
    out_of_stock: 'danger',
    discontinued: 'info'
  }
  return types[status] || 'info'
}

const getStatusLabel = (status: string) => {
  const labels: Record<string, string> = {
    normal: '正常',
    low_stock: '库存不足',
    out_of_stock: '缺货',
    discontinued: '停用'
  }
  return labels[status] || status
}

const fetchData = async () => {
  loading.value = true
  try {
    const res = await getConsumables({
      ...filterForm,
      ...pagination
    })
    tableData.value = res.items
    pagination.total = res.total
  } finally {
    loading.value = false
  }
}

const fetchSummary = async () => {
  try {
    const res = await getStockSummary(filterForm.category)
    summary.value = res
  } catch (error) {
    console.error('Failed to fetch summary:', error)
  }
}

const fetchCategories = async () => {
  try {
    const res = await getConsumableCategories()
    categoryOptions.value = res.items
  } catch (error) {
    console.error('Failed to fetch categories:', error)
  }
}

const handleSearch = () => {
  pagination.page = 1
  fetchData()
  fetchSummary()
}

const handleCreate = () => {
  router.push('/consumables/create')
}

const handleView = (row: Consumable) => {
  router.push(`/consumables/${row.id}`)
}

const handleEdit = (row: Consumable) => {
  router.push(`/consumables/${row.id}/edit`)
}

const handleRowClick = (row: Consumable) => {
  handleView(row)
}

const handleViewStock = (row: Consumable) => {
  currentConsumable.value = row
  stockMovementVisible.value = true
}

const handleQuickIssue = (row: Consumable) => {
  router.push({
    path: '/consumables/issue/create',
    query: { consumable_id: row.id }
  })
}

const goBack = () => {
  router.back()
}

onMounted(async () => {
  await Promise.all([fetchData(), fetchSummary(), fetchCategories()])
})
</script>

<style scoped>
.consumable-list {
  padding: 20px;
}

.summary-cards {
  margin: 20px 0;
}

.filter-card {
  margin-bottom: 20px;
}

.mt-4 {
  margin-top: 16px;
}

.stock-info {
  display: flex;
  align-items: baseline;
  gap: 4px;
}

.stock-info .unit {
  font-size: 12px;
  color: #909399;
}

.text-success {
  color: #67c23a;
}

.text-warning {
  color: #e6a23c;
}

.text-danger {
  color: #f56c6c;
}
</style>
```

### ConsumableForm.vue - 耗品档案表单

```vue
<template>
  <div class="consumable-form">
    <el-page-header @back="goBack" title="返回">
      <template #content>
        <span class="text-large font-600">
          {{ isEdit ? '编辑耗材' : '新增耗材' }}
        </span>
      </template>
      <template #extra>
        <el-button type="primary" @click="handleSubmit">保存</el-button>
      </template>
    </el-page-header>

    <el-form
      ref="formRef"
      :model="form"
      :rules="rules"
      label-width="120px"
      class="form-content"
    >
      <!-- 基础信息 -->
      <el-card header="基础信息" shadow="never">
        <el-row :gutter="20">
          <el-col :span="8">
            <el-form-item label="耗材编码" prop="code">
              <el-input v-model="form.code" placeholder="自动生成或手动输入" />
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="耗材名称" prop="name">
              <el-input v-model="form.name" placeholder="请输入耗材名称" />
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="品牌" prop="brand">
              <el-input v-model="form.brand" placeholder="请输入品牌" />
            </el-form-item>
          </el-col>
        </el-row>

        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="所属分类" prop="category">
              <el-tree-select
                v-model="form.category"
                :data="categoryOptions"
                :props="{ value: 'id', label: 'name', children: 'children' }"
                placeholder="请选择分类"
              />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="规格型号" prop="specification">
              <el-input v-model="form.specification" placeholder="请输入规格型号" />
            </el-form-item>
          </el-col>
        </el-row>

        <el-form-item label="计量单位" prop="unit">
          <el-select v-model="form.unit" placeholder="请选择单位">
            <el-option label="件" value="件" />
            <el-option label="个" value="个" />
            <el-option label="套" value="套" />
            <el-option label="包" value="包" />
            <el-option label="箱" value="箱" />
            <el-option label="瓶" value="瓶" />
            <el-option label="卷" value="卷" />
            <el-option label="本" value="本" />
            <el-option label="支" value="支" />
            <el-option label="把" value="把" />
          </el-select>
        </el-form-item>
      </el-card>

      <!-- 库存信息 -->
      <el-card header="库存信息" shadow="never">
        <el-row :gutter="20">
          <el-col :span="6">
            <el-form-item label="当前库存">
              <el-input-number v-model="form.current_stock" :min="0" disabled />
            </el-form-item>
          </el-col>
          <el-col :span="6">
            <el-form-item label="最低库存" prop="min_stock">
              <el-input-number v-model="form.min_stock" :min="0" />
            </el-form-item>
          </el-col>
          <el-col :span="6">
            <el-form-item label="补货点" prop="reorder_point">
              <el-input-number v-model="form.reorder_point" :min="0" />
            </el-form-item>
          </el-col>
          <el-col :span="6">
            <el-form-item label="最高库存" prop="max_stock">
              <el-input-number v-model="form.max_stock" :min="0" />
            </el-form-item>
          </el-col>
        </el-row>

        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="采购价格">
              <el-input-number v-model="form.purchase_price" :min="0" :precision="2" />
              <span class="ml-2">元</span>
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="平均价格">
              <el-input-number v-model="form.average_price" :min="0" :precision="2" disabled />
              <span class="ml-2">元</span>
            </el-form-item>
          </el-col>
        </el-row>

        <el-form-item label="存放仓库">
          <LocationTree v-model="form.warehouse" placeholder="请选择仓库" />
        </el-form-item>
      </el-card>

      <!-- 备注 -->
      <el-card header="其他信息" shadow="never">
        <el-form-item label="备注">
          <el-input
            v-model="form.remark"
            type="textarea"
            :rows="3"
            placeholder="请输入备注信息"
          />
        </el-form-item>
      </el-card>
    </el-form>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { ElMessage } from 'element-plus'
import { createConsumable, updateConsumable, getConsumableDetail } from '@/api/consumables'
import { getConsumableCategories } from '@/api/consumables/category'
import LocationTree from '@/components/LocationTree.vue'

const router = useRouter()
const route = useRoute()

const formRef = ref()
const categoryOptions = ref([])

const isEdit = computed(() => !!route.params.id)

const form = reactive({
  code: '',
  name: '',
  category: null,
  specification: '',
  brand: '',
  unit: '件',
  current_stock: 0,
  min_stock: 10,
  reorder_point: 20,
  max_stock: 100,
  purchase_price: 0,
  average_price: 0,
  warehouse: null,
  remark: ''
})

const rules = {
  name: [{ required: true, message: '请输入耗材名称', trigger: 'blur' }],
  category: [{ required: true, message: '请选择分类', trigger: 'change' }],
  unit: [{ required: true, message: '请选择单位', trigger: 'change' }]
}

const handleSubmit = async () => {
  await formRef.value.validate()
  try {
    if (isEdit.value) {
      await updateConsumable(Number(route.params.id), form)
      ElMessage.success('更新成功')
    } else {
      await createConsumable(form)
      ElMessage.success('创建成功')
    }
    goBack()
  } catch (error) {
    ElMessage.error('操作失败')
  }
}

const loadDetail = async () => {
  const res = await getConsumableDetail(Number(route.params.id))
  Object.assign(form, {
    code: res.code,
    name: res.name,
    category: res.category?.id,
    specification: res.specification,
    brand: res.brand,
    unit: res.unit,
    current_stock: res.current_stock,
    min_stock: res.min_stock,
    reorder_point: res.reorder_point,
    max_stock: res.max_stock,
    purchase_price: res.purchase_price,
    average_price: res.average_price,
    warehouse: res.warehouse?.id,
    remark: res.remark
  })
}

const loadCategories = async () => {
  const res = await getConsumableCategories()
  categoryOptions.value = res.items
}

const goBack = () => {
  router.back()
}

onMounted(async () => {
  await loadCategories()
  if (isEdit.value) {
    await loadDetail()
  }
})
</script>

<style scoped>
.consumable-form {
  padding: 20px;
}

.form-content {
  margin-top: 20px;
}

.ml-2 {
  margin-left: 8px;
}
</style>
```

---

## 2. 采购单组件

### PurchaseForm.vue - 采购单表单

```vue
<template>
  <div class="purchase-form">
    <el-page-header @back="goBack" title="返回">
      <template #content>
        <span class="text-large font-600">
          {{ isEdit ? '编辑采购单' : '新建采购单' }}
        </span>
      </template>
      <template #extra>
        <el-button v-if="!isEdit" type="primary" @click="handleSubmit">创建采购单</el-button>
        <el-button
          v-if="isEdit && canEdit"
          type="primary"
          @click="handleUpdate"
        >
          保存
        </el-button>
        <el-button
          v-if="isEdit && form.status === 'submitted'"
          type="success"
          @click="handleApprove"
        >
          审批
        </el-button>
        <el-button
          v-if="isEdit && form.status === 'approved'"
          type="success"
          @click="handleConfirmReceipt"
        >
          确认入库
        </el-button>
      </template>
    </el-page-header>

    <el-form
      ref="formRef"
      :model="form"
      :rules="rules"
      label-width="120px"
      class="form-content"
    >
      <!-- 基础信息 -->
      <el-card header="基础信息" shadow="never">
        <el-row :gutter="20">
          <el-col :span="8">
            <el-form-item label="采购单号">
              <el-input v-model="form.purchase_no" disabled />
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="采购日期" prop="purchase_date">
              <el-date-picker
                v-model="form.purchase_date"
                type="date"
                value-format="YYYY-MM-DD"
                :disabled="!canEdit"
              />
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="采购类型" prop="purchase_type">
              <el-select v-model="form.purchase_type" :disabled="!canEdit">
                <el-option label="常规采购" value="regular" />
                <el-option label="紧急采购" value="urgent" />
                <el-option label="补货采购" value="replenish" />
              </el-select>
            </el-form-item>
          </el-col>
        </el-row>

        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="供应商" prop="supplier">
              <SupplierSelect v-model="form.supplier" :disabled="!canEdit" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="申请人">
              <el-input :value="userStore.realName" disabled />
            </el-form-item>
          </el-col>
        </el-row>

        <el-form-item label="备注">
          <el-input
            v-model="form.remark"
            type="textarea"
            :rows="2"
            :disabled="!canEdit"
          />
        </el-form-item>
      </el-card>

      <!-- 采购明细 -->
      <el-card header="采购明细" shadow="never">
        <div v-if="canEdit" class="mb-3">
          <el-button type="primary" :icon="Plus" @click="showConsumableSelector">
            添加耗材
          </el-button>
        </div>

        <el-table :data="form.items" border show-summary :summary-method="getSummaries">
          <el-table-column prop="consumable.code" label="耗材编码" width="120" />
          <el-table-column prop="consumable.name" label="耗材名称" width="180" />
          <el-table-column prop="consumable.unit" label="单位" width="60" />
          <el-table-column label="订购数量" width="120">
            <template #default="{ row, $index }">
              <el-input-number
                v-if="canEdit"
                v-model="row.order_quantity"
                :min="1"
                @change="calculateAmount(row)"
              />
              <span v-else>{{ row.order_quantity }}</span>
            </template>
          </el-table-column>
          <el-table-column label="实收数量" width="120">
            <template #default="{ row }">
              <el-input-number
                v-if="form.status === 'approved'"
                v-model="row.received_quantity"
                :min="0"
                :max="row.order_quantity"
              />
              <span v-else>{{ row.received_quantity }}</span>
            </template>
          </el-table-column>
          <el-table-column label="单价" width="120">
            <template #default="{ row, $index }">
              <el-input-number
                v-if="canEdit"
                v-model="row.unit_price"
                :min="0"
                :precision="2"
                @change="calculateAmount(row)"
              />
              <span v-else>¥{{ row.unit_price }}</span>
            </template>
          </el-table-column>
          <el-table-column prop="amount" label="金额" width="120">
            <template #default="{ row }">¥{{ row.amount }}</template>
          </el-table-column>
          <el-table-column v-if="canEdit" label="操作" width="60" fixed="right">
            <template #default="{ $index }">
              <el-button
                link
                type="danger"
                :icon="Delete"
                @click="handleRemoveItem($index)"
              />
            </template>
          </el-table-column>
        </el-table>
      </el-card>

      <!-- 审批信息 -->
      <ApprovalFlow
        v-if="isEdit"
        :status="form.status"
        :approvals="form.approvals"
        class="mt-4"
      />
    </el-form>

    <!-- 耗材选择弹窗 -->
    <ConsumableSelector
      v-model="selectorVisible"
      @confirm="handleConsumableSelect"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { Plus, Delete } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import { createPurchase, updatePurchase, approvePurchase, confirmReceipt } from '@/api/consumables/purchase'
import { useUserStore } from '@/stores/user'
import ConsumableSelector from './components/ConsumableSelector.vue'
import ApprovalFlow from './components/ApprovalFlow.vue'

const router = useRouter()
const route = useRoute()
const userStore = useUserStore()

const formRef = ref()
const selectorVisible = ref(false)

const isEdit = computed(() => !!route.params.id)
const canEdit = computed(() => {
  return !isEdit.value || form.value.status === 'draft'
})

const form = ref({
  purchase_no: '',
  purchase_date: new Date().toISOString().split('T')[0],
  purchase_type: 'regular',
  supplier: null,
  remark: '',
  status: 'draft',
  total_amount: 0,
  items: [],
  approvals: []
})

const rules = {
  supplier: [{ required: true, message: '请选择供应商', trigger: 'change' }],
  purchase_date: [{ required: true, message: '请选择采购日期', trigger: 'change' }]
}

const calculateAmount = (row: any) => {
  row.amount = (row.unit_price || 0) * (row.received_quantity || row.order_quantity || 0)
}

const getSummaries = (param: any) => {
  const { columns, data } = param
  const sums: string[] = []
  columns.forEach((column: any, index: number) => {
    if (index === 0) {
      sums[index] = '合计'
      return
    }
    if (column.property === 'amount') {
      const total = data.reduce((sum: number, row: any) => sum + (row.amount || 0), 0)
      sums[index] = `¥${total.toFixed(2)}`
    } else {
      sums[index] = ''
    }
  })
  return sums
}

const showConsumableSelector = () => {
  selectorVisible.value = true
}

const handleConsumableSelect = (consumables: any[]) => {
  consumables.forEach(consumable => {
    if (!form.value.items.find((i: any) => i.consumable?.id === consumable.id)) {
      form.value.items.push({
        consumable,
        order_quantity: 1,
        received_quantity: 0,
        unit_price: consumable.purchase_price || 0,
        amount: 0
      })
      calculateAmount(form.value.items[form.value.items.length - 1])
    }
  })
}

const handleRemoveItem = (index: number) => {
  form.value.items.splice(index, 1)
}

const handleSubmit = async () => {
  await formRef.value.validate()
  try {
    const data = {
      ...form.value,
      items: form.value.items.map((i: any) => ({
        consumable_id: i.consumable.id,
        order_quantity: i.order_quantity,
        received_quantity: i.received_quantity,
        unit_price: i.unit_price
      }))
    }
    await createPurchase(data)
    ElMessage.success('采购单创建成功')
    goBack()
  } catch (error) {
    ElMessage.error('创建失败')
  }
}

const handleUpdate = async () => {
  await formRef.value.validate()
  // 更新逻辑
}

const handleApprove = async () => {
  try {
    await approvePurchase(Number(route.params.id), 'approved')
    ElMessage.success('已审批')
    // 重新加载数据
  } catch (error) {
    ElMessage.error('审批失败')
  }
}

const handleConfirmReceipt = async () => {
  try {
    await confirmReceipt(Number(route.params.id))
    ElMessage.success('入库成功，库存已更新')
    // 重新加载数据
  } catch (error) {
    ElMessage.error('入库失败')
  }
}

const goBack = () => {
  router.back()
}

onMounted(async () => {
  if (isEdit.value) {
    // 加载详情
  }
})
</script>

<style scoped>
.purchase-form {
  padding: 20px;
}

.form-content {
  margin-top: 20px;
}

.mb-3 {
  margin-bottom: 12px;
}

.mt-4 {
  margin-top: 16px;
}
</style>
```

---

## 3. 领用单组件

### IssueForm.vue - 领用单表单

```vue
<template>
  <div class="issue-form">
    <el-page-header @back="goBack" title="返回">
      <template #content>
        <span class="text-large font-600">耗材领用申请</span>
      </template>
    </el-page-header>

    <el-form
      ref="formRef"
      :model="form"
      :rules="rules"
      label-width="120px"
      class="form-content"
    >
      <el-card header="基础信息" shadow="never">
        <el-row :gutter="20">
          <el-col :span="8">
            <el-form-item label="领用日期" prop="issue_date">
              <el-date-picker
                v-model="form.issue_date"
                type="date"
                value-format="YYYY-MM-DD"
              />
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="领用类型" prop="issue_type">
              <el-select v-model="form.issue_type">
                <el-option label="部门领用" value="department" />
                <el-option label="个人领用" value="personal" />
                <el-option label="项目领用" value="project" />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="领用部门" prop="department">
              <DepartmentTree v-model="form.department" />
            </el-form-item>
          </el-col>
        </el-row>

        <el-form-item label="用途说明" prop="purpose">
          <el-input
            v-model="form.purpose"
            type="textarea"
            :rows="2"
            placeholder="请说明领用用途"
          />
        </el-form-item>
      </el-card>

      <el-card header="领用明细" shadow="never">
        <el-button type="primary" :icon="Plus" @click="showConsumableSelector">
          添加耗材
        </el-button>

        <el-table :data="form.items" class="mt-3" border>
          <el-table-column prop="consumable.code" label="耗材编码" width="120" />
          <el-table-column prop="consumable.name" label="耗材名称" width="180" />
          <el-table-column prop="consumable.unit" label="单位" width="60" />
          <el-table-column label="当前库存" width="100">
            <template #default="{ row }">
              <span :class="getStockClass(row)">
                {{ row.consumable.available_stock }}
              </span>
            </template>
          </el-table-column>
          <el-table-column label="领用数量" width="120">
            <template #default="{ row }">
              <el-input-number
                v-model="row.quantity"
                :min="1"
                :max="row.consumable.available_stock"
              />
            </template>
          </el-table-column>
          <el-table-column label="操作" width="60">
            <template #default="{ $index }">
              <el-button
                link
                type="danger"
                :icon="Delete"
                @click="handleRemoveItem($index)"
              />
            </template>
          </el-table-column>
        </el-table>
      </el-card>

      <div class="form-actions">
        <el-button type="primary" @click="handleSubmit">提交领用</el-button>
        <el-button @click="goBack">取消</el-button>
      </div>
    </el-form>

    <ConsumableSelector
      v-model="selectorVisible"
      :stock-filter="true"
      @confirm="handleConsumableSelect"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { Plus, Delete } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import { createIssue } from '@/api/consumables/issue'
import DepartmentTree from '@/components/DepartmentTree.vue'
import ConsumableSelector from './components/ConsumableSelector.vue'

const router = useRouter()

const formRef = ref()
const selectorVisible = ref(false)

const form = reactive({
  issue_date: new Date().toISOString().split('T')[0],
  issue_type: 'department',
  department: null,
  purpose: '',
  items: []
})

const rules = {
  issue_date: [{ required: true, message: '请选择领用日期', trigger: 'change' }],
  issue_type: [{ required: true, message: '请选择领用类型', trigger: 'change' }],
  department: [{ required: true, message: '请选择领用部门', trigger: 'change' }],
  purpose: [{ required: true, message: '请填写用途说明', trigger: 'blur' }]
}

const getStockClass = (row: any) => {
  const stock = row.consumable.available_stock
  if (stock <= 0) return 'text-danger'
  if (stock <= row.consumable.min_stock) return 'text-warning'
  return ''

  const showConsumableSelector = () => {
    selectorVisible.value = true
  }

  const handleConsumableSelect = (consumables: any[]) => {
    consumables.forEach(consumable => {
      if (!form.items.find((i: any) => i.consumable?.id === consumable.id)) {
        form.items.push({
          consumable,
          quantity: 1
        })
      }
    })
  }

  const handleRemoveItem = (index: number) => {
    form.items.splice(index, 1)
  }

  const handleSubmit = async () => {
    await formRef.value.validate()

    if (form.items.length === 0) {
      ElMessage.warning('请至少添加一项耗材')
      return
    }

    try {
      const data = {
        ...form,
        items: form.items.map((i: any) => ({
          consumable_id: i.consumable.id,
          quantity: i.quantity
        }))
      }
      await createIssue(data)
      ElMessage.success('领用单已提交，等待审批')
      router.push('/consumables/issue')
    } catch (error) {
      ElMessage.error('提交失败')
    }
  }

  const goBack = () => {
    router.back()
  }
}
</script>

<style scoped>
.issue-form {
  padding: 20px;
}

.form-content {
  margin-top: 20px;
}

.mt-3 {
  margin-top: 12px;
}

.form-actions {
  margin-top: 20px;
  text-align: center;
}

.text-danger {
  color: #f56c6c;
}

.text-warning {
  color: #e6a23c;
}
</style>
```

---

## 4. 通用组件

### ConsumableSelector.vue - 耗材选择器

```vue
<template>
  <el-dialog
    v-model="visible"
    title="选择耗材"
    width="900px"
    :close-on-click-modal="false"
  >
    <div class="consumable-selector">
      <el-form :model="searchForm" inline>
        <el-form-item label="搜索">
          <el-input
            v-model="searchForm.search"
            placeholder="耗材编码/名称"
            clearable
            @keyup.enter="handleSearch"
          >
            <template #append>
              <el-button :icon="Search" @click="handleSearch" />
            </template>
          </el-input>
        </el-form-item>
        <el-form-item label="分类">
          <el-tree-select
            v-model="searchForm.category"
            :data="categoryOptions"
            clearable
            check-strictly
            @change="handleSearch"
          />
        </el-form-item>
        <el-form-item v-if="stockFilter" label="仅显示有库存">
          <el-switch v-model="searchForm.has_stock" @change="handleSearch" />
        </el-form-item>
      </el-form>

      <el-table
        ref="tableRef"
        v-loading="loading"
        :data="tableData"
        @selection-change="handleSelectionChange"
        height="400"
      >
        <el-table-column type="selection" width="50" />
        <el-table-column prop="code" label="编码" width="100" />
        <el-table-column prop="name" label="名称" width="150" />
        <el-table-column prop="category.name" label="分类" width="100" />
        <el-table-column prop="specification" label="规格" />
        <el-table-column label="库存" width="100">
          <template #default="{ row }">
            <span :class="getStockClass(row)">{{ row.available_stock }}</span>
            {{ row.unit }}
          </template>
        </el-table-column>
        <el-table-column prop="average_price" label="平均价" width="80">
          <template #default="{ row }">¥{{ row.average_price }}</template>
        </el-table-column>
      </el-table>

      <el-pagination
        v-model:current-page="pagination.page"
        v-model:page-size="pagination.page_size"
        :total="pagination.total"
        small
        layout="total, prev, pager, next"
        @current-change="fetchData"
      />
    </div>

    <template #footer>
      <el-button @click="visible = false">取消</el-button>
      <el-button type="primary" @click="handleConfirm">确定</el-button>
    </template>
  </el-dialog>
</template>

<script setup lang="ts">
import { ref, reactive, computed, watch } from 'vue'
import { Search } from '@element-plus/icons-vue'
import { getConsumables } from '@/api/consumables'

interface Props {
  modelValue: boolean
  stockFilter?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  stockFilter: false
})

const emit = defineEmits(['update:modelValue', 'confirm'])

const visible = computed({
  get: () => props.modelValue,
  set: (val) => emit('update:modelValue', val)
})

const loading = ref(false)
const tableRef = ref()
const tableData = ref([])
const selectedItems = ref<any[]>([])
const categoryOptions = ref([])

const searchForm = reactive({
  search: '',
  category: null,
  has_stock: true
})

const pagination = reactive({
  page: 1,
  page_size: 20,
  total: 0
})

const getStockClass = (row: any) => {
  if (row.available_stock <= 0) return 'text-danger'
  if (row.available_stock <= row.min_stock) return 'text-warning'
  return ''

  const fetchData = async () => {
    loading.value = true
    try {
      const params: any = {
        ...searchForm,
        ...pagination
      }

      if (props.stockFilter && searchForm.has_stock) {
        params.available_stock__gt = 0
      }

      const res = await getConsumables(params)
      tableData.value = res.items
      pagination.total = res.total
    } finally {
      loading.value = false
    }
  }

  const handleSearch = () => {
    pagination.page = 1
    fetchData()
  }

  const handleSelectionChange = (selection: any[]) => {
    selectedItems.value = selection
  }

  const handleConfirm = () => {
    emit('confirm', selectedItems.value)
    visible.value = false
  }

  watch(() => props.modelValue, (val) => {
    if (val) {
      fetchData()
    }
  })
}
</script>
```

### StockMovementDialog.vue - 库存流水弹窗

```vue
<template>
  <el-dialog
    v-model="visible"
    title="库存流水"
    width="800px"
  >
    <div v-if="consumable" class="mb-3">
      <el-descriptions :column="3" border>
        <el-descriptions-item label="耗材">{{ consumable.name }}</el-descriptions-item>
        <el-descriptions-item label="编码">{{ consumable.code }}</el-descriptions-item>
        <el-descriptions-item label="当前库存">
          {{ consumable.available_stock }} {{ consumable.unit }}
        </el-descriptions-item>
      </el-descriptions>
    </div>

    <el-date-picker
      v-model="dateRange"
      type="daterange"
      range-separator="至"
      start-placeholder="开始日期"
      end-placeholder="结束日期"
      @change="fetchData"
    />

    <el-table :data="movements" max-height="400" class="mt-3">
      <el-table-column prop="created_at" label="时间" width="160" />
      <el-table-column label="变动类型" width="120">
        <template #default="{ row }">
          <el-tag :type="getTransactionTypeColor(row.transaction_type)">
            {{ getTransactionTypeLabel(row.transaction_type) }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="quantity" label="数量" width="100">
        <template #default="{ row }">
          <span :class="row.quantity > 0 ? 'text-success' : 'text-danger'">
            {{ row.quantity > 0 ? '+' : '' }}{{ row.quantity }}
          </span>
        </template>
      </el-table-column>
      <el-table-column prop="before_stock" label="变动前" width="80" />
      <el-table-column prop="after_stock" label="变动后" width="80" />
      <el-table-column prop="source_no" label="来源单号" width="130" />
      <el-table-column prop="handler.real_name" label="经手人" width="100" />
      <el-table-column prop="remark" label="备注" />
    </el-table>
  </el-dialog>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { getStockMovements } from '@/api/consumables'

interface Props {
  modelValue: boolean
  consumable: any
}

const props = defineProps<Props>()

const emit = defineEmits(['update:modelValue'])

const visible = computed({
  get: () => props.modelValue,
  set: (val) => emit('update:modelValue', val)
})

const dateRange = ref([])
const movements = ref([])

const getTransactionTypeColor = (type: string) => {
  const colors: Record<string, string> = {
    purchase: 'success',
    issue: 'danger',
    return: 'success',
    transfer_in: 'success',
    transfer_out: 'danger',
    inventory_add: 'success',
    inventory_reduce: 'danger',
    adjustment: 'warning'
  }
  return colors[type] || 'info'
}

const getTransactionTypeLabel = (type: string) => {
  const labels: Record<string, string> = {
    purchase: '采购入库',
    issue: '领用出库',
    return: '退库入库',
    transfer_in: '调入入库',
    transfer_out: '调拨出库',
    inventory_add: '盘点增加',
    inventory_reduce: '盘亏减少',
    adjustment: '调整'
  }
  return labels[type] || type
}

const fetchData = async () => {
  if (!props.consumable) return

  const [start, end] = dateRange.value || []
  const res = await getStockMovements(
    props.consumable.id,
    start,
    end
  )
  movements.value = res.items
}

watch(() => props.modelValue, (val) => {
  if (val && props.consumable) {
    fetchData()
  }
})
</script>

<style scoped>
.text-success {
  color: #67c23a;
}

.text-danger {
  color: #f56c6c;
}

.mb-3 {
  margin-bottom: 12px;
}

.mt-3 {
  margin-top: 12px;
}
</style>
```

---

## API 集成

```typescript
// src/api/consumables/index.ts

import request from '@/utils/request'

// 耗材档案
export const getConsumables = (params: any) => {
  return request.get('/api/consumables/consumables/', { params })
}

export const getConsumableDetail = (id: number) => {
  return request.get(`/api/consumables/consumables/${id}/`)
}

export const createConsumable = (data: any) => {
  return request.post('/api/consumables/consumables/', data)
}

export const updateConsumable = (id: number, data: any) => {
  return request.put(`/api/consumables/consumables/${id}/`, data)
}

export const deleteConsumable = (id: number) => {
  return request.delete(`/api/consumables/consumables/${id}/`)
}

export const getStockSummary = (categoryId?: number) => {
  return request.get('/api/consumables/consumables/stock_summary/', {
    params: { category_id: categoryId }
  })
}

export const getStockMovements = (id: number, startDate?: string, endDate?: string) => {
  return request.get(`/api/consumables/consumables/${id}/stock_movements/`, {
    params: { start_date: startDate, end_date: endDate }
  })
}

// 分类
export const getConsumableCategories = () => {
  return request.get('/api/consumables/categories/')
}
```

```typescript
// src/api/consumables/purchase.ts

import request from '@/utils/request'

export const getPurchaseList = (params: any) => {
  return request.get('/api/consumables/purchases/', { params })
}

export const createPurchase = (data: any) => {
  return request.post('/api/consumables/purchases/', data)
}

export const approvePurchase = (id: number, approval: string) => {
  return request.post(`/api/consumables/purchases/${id}/approve/`, { approval })
}

export const confirmReceipt = (id: number) => {
  return request.post(`/api/consumables/purchases/${id}/confirm_receipt/`)
}
```

```typescript
// src/api/consumables/issue.ts

import request from '@/utils/request'

export const getIssueList = (params: any) => {
  return request.get('/api/consumables/issues/', { params })
}

export const createIssue = (data: any) => {
  return request.post('/api/consumables/issues/', data)
}

export const approveIssue = (id: number, approval: string) => {
  return request.post(`/api/consumables/issues/${id}/approve/`, { approval })
}

export const confirmIssue = (id: number) => {
  return request.post(`/api/consumables/issues/${id}/confirm_issue/`)
}
```

---

## 路由配置

```typescript
// src/router/consumables.ts

export default [
  {
    path: '/consumables',
    component: () => import('@/layouts/DefaultLayout.vue'),
    children: [
      {
        path: '',
        name: 'ConsumableList',
        component: () => import('@/views/consumables/ConsumableList.vue'),
        meta: { title: '低值易耗品' }
      },
      {
        path: 'create',
        name: 'ConsumableCreate',
        component: () => import('@/views/consumables/ConsumableForm.vue'),
        meta: { title: '新增耗材' }
      },
      {
        path: ':id',
        name: 'ConsumableDetail',
        component: () => import('@/views/consumables/ConsumableForm.vue'),
        meta: { title: '耗材详情' }
      },
      {
        path: ':id/edit',
        name: 'ConsumableEdit',
        component: () => import('@/views/consumables/ConsumableForm.vue'),
        meta: { title: '编辑耗材' }
      },
      {
        path: 'purchase',
        name: 'PurchaseList',
        component: () => import('@/views/consumables/PurchaseList.vue'),
        meta: { title: '采购单' }
      },
      {
        path: 'purchase/create',
        name: 'PurchaseCreate',
        component: () => import('@/views/consumables/PurchaseForm.vue'),
        meta: { title: '新建采购单' }
      },
      {
        path: 'issue',
        name: 'IssueList',
        component: () => import('@/views/consumables/IssueList.vue'),
        meta: { title: '领用单' }
      },
      {
        path: 'issue/create',
        name: 'IssueCreate',
        component: () => import('@/views/consumables/IssueForm.vue'),
        meta: { title: '新建领用单' }
      }
    ]
  }
]
```

---

## 后续任务

1. 实现退库单和盘点单前端
2. 集成库存预警通知
3. 实现移动端扫码领用
