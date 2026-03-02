# Phase 1.6: Consumables Management - Frontend Implementation v2

## Document Information

| Project | Details |
|---------|---------|
| PRD Version | v2.0 (Updated for API Standardization) |
| Updated Date | 2026-01-22 |
| References | [frontend_api_standardization_design.md](../common_base_features/00_core/frontend_api_standardization_design.md) |

---

## Task Overview

Implement low-value consumables management with archive management, purchase/issue/return workflows, and stock tracking.

---

## API Service Layer

### Type Definitions

```typescript
// frontend/src/types/consumables.ts

export interface Consumable {
  id: string
  code: string
  name: string
  categoryId: string
  category?: ConsumableCategory
  specification?: string
  brand?: string
  unit: string
  currentStock: number
  availableStock: number
  minStock: number
  reorderPoint: number
  maxStock: number
  purchasePrice: number
  averagePrice: number
  status: ConsumableStatus
  warehouseId?: string
  warehouse?: Warehouse
  organizationId: string
  createdAt: string
  updatedAt: string
}

export enum ConsumableStatus {
  NORMAL = 'normal',
  LOW_STOCK = 'low_stock',
  OUT_OF_STOCK = 'out_of_stock',
  DISCONTINUED = 'discontinued'
}

export interface ConsumableCategory {
  id: string
  code: string
  name: string
  parentId?: string
  level: number
}

export interface StockSummary {
  totalItems: number
  totalValue: number
  totalLowStock: number
  totalOutOfStock: number
}

export interface StockMovement {
  id: string
  consumableId: string
  transactionType: TransactionType
  quantity: number
  beforeStock: number
  afterStock: number
  sourceNo?: string
  remark?: string
  createdAt: string
  handler?: User
}

export enum TransactionType {
  PURCHASE = 'purchase',
  ISSUE = 'issue',
  RETURN = 'return',
  TRANSFER_IN = 'transfer_in',
  TRANSFER_OUT = 'transfer_out',
  INVENTORY_ADD = 'inventory_add',
  INVENTORY_REDUCE = 'inventory_reduce',
  ADJUSTMENT = 'adjustment'
}

// Purchase Order
export interface PurchaseOrder {
  id: string
  purchaseNo: string
  purchaseDate: string
  purchaseType: PurchaseType
  supplierId?: string
  supplier?: Supplier
  applicantId: string
  applicant?: User
  remark?: string
  status: PurchaseStatus
  totalAmount: number
  items: PurchaseOrderItem[]
  approvals?: ApprovalRecord[]
  organizationId: string
  createdAt: string
}

export enum PurchaseType {
  REGULAR = 'regular',
  URGENT = 'urgent',
  REPLENISH = 'replenish'
}

export enum PurchaseStatus {
  DRAFT = 'draft',
  SUBMITTED = 'submitted',
  APPROVED = 'approved',
  REJECTED = 'rejected',
  RECEIVED = 'received'
}

export interface PurchaseOrderItem {
  id: string
  consumableId: string
  consumable?: Consumable
  orderQuantity: number
  receivedQuantity: number
  unitPrice: number
  amount: number
}

// Issue Order
export interface IssueOrder {
  id: string
  issueNo: string
  issueDate: string
  issueType: IssueType
  departmentId?: string
  department?: Department
  applicantId: string
  purpose: string
  status: IssueStatus
  items: IssueOrderItem[]
  approvals?: ApprovalRecord[]
  organizationId: string
  createdAt: string
}

export enum IssueType {
  DEPARTMENT = 'department',
  PERSONAL = 'personal',
  PROJECT = 'project'
}

export enum IssueStatus {
  DRAFT = 'draft',
  SUBMITTED = 'submitted',
  APPROVED = 'approved',
  ISSUED = 'issued',
  REJECTED = 'rejected'
}

export interface IssueOrderItem {
  id: string
  consumableId: string
  consumable?: Consumable
  quantity: number
}
```

### API Service

```typescript
// frontend/src/api/consumables.ts

import request from '@/utils/request'
import type { PaginatedResponse } from '@/types/api'
import type {
  Consumable,
  StockSummary,
  StockMovement,
  PurchaseOrder,
  IssueOrder,
  ConsumableCreate,
  ConsumableUpdate,
  PurchaseCreate,
  IssueCreate
} from '@/types/consumables'

export const consumableApi = {
  // Consumable Archive
  list(params?: any): Promise<PaginatedResponse<Consumable>> {
    return request.get('/consumables/', { params })
  },

  get(id: string): Promise<Consumable> {
    return request.get(`/consumables/${id}/`)
  },

  create(data: ConsumableCreate): Promise<Consumable> {
    return request.post('/consumables/', data)
  },

  update(id: string, data: ConsumableUpdate): Promise<Consumable> {
    return request.put(`/consumables/${id}/`, data)
  },

  delete(id: string): Promise<void> {
    return request.delete(`/consumables/${id}/`)
  },

  // Stock
  getStockSummary(categoryId?: string): Promise<StockSummary> {
    return request.get('/consumables/stock-summary/', {
      params: { categoryId }
    })
  },

  getStockMovements(id: string, params?: {
    startDate?: string
    endDate?: string
  }): Promise<{ results: StockMovement[]; count: number }> {
    return request.get(`/consumables/${id}/movements/`, { params })
  }
}

export const purchaseOrderApi = {
  list(params?: any): Promise<PaginatedResponse<PurchaseOrder>> {
    return request.get('/consumables/purchases/', { params })
  },

  get(id: string): Promise<PurchaseOrder> {
    return request.get(`/consumables/purchases/${id}/`)
  },

  create(data: PurchaseCreate): Promise<PurchaseOrder> {
    return request.post('/consumables/purchases/', data)
  },

  update(id: string, data: Partial<PurchaseCreate>): Promise<PurchaseOrder> {
    return request.put(`/consumables/purchases/${id}/`, data)
  },

  submit(id: string): Promise<void> {
    return request.post(`/consumables/purchases/${id}/submit/`)
  },

  approve(id: string, data: {
    action: 'approve' | 'reject'
    comment?: string
  }): Promise<void> {
    return request.post(`/consumables/purchases/${id}/approve/`, data)
  },

  confirmReceipt(id: string, items: Array<{
    itemId: string
    receivedQuantity: number
    qualifiedQuantity: number
  }>): Promise<void> {
    return request.post(`/consumables/purchases/${id}/confirm-receipt/`, { items })
  }
}

export const issueOrderApi = {
  list(params?: any): Promise<PaginatedResponse<IssueOrder>> {
    return request.get('/consumables/issues/', { params })
  },

  get(id: string): Promise<IssueOrder> {
    return request.get(`/consumables/issues/${id}/`)
  },

  create(data: IssueCreate): Promise<IssueOrder> {
    return request.post('/consumables/issues/', data)
  },

  update(id: string, data: Partial<IssueCreate>): Promise<IssueOrder> {
    return request.put(`/consumables/issues/${id}/`, data)
  },

  submit(id: string): Promise<void> {
    return request.post(`/consumables/issues/${id}/submit/`)
  },

  approve(id: string, data: {
    action: 'approve' | 'reject'
    comment?: string
  }): Promise<void> {
    return request.post(`/consumables/issues/${id}/approve/`, data)
  },

  confirmIssue(id: string): Promise<void> {
    return request.post(`/consumables/issues/${id}/confirm-issue/`)
  }
}

export const consumableCategoryApi = {
  list(): Promise<{ results: ConsumableCategory[] }> {
    return request.get('/consumables/categories/')
  }
}
```

---

## Component: ConsumableList

```vue
<!-- frontend/src/views/consumables/ConsumableList.vue -->
<template>
  <BaseListPage
    title="低值易耗品"
    :fetch-method="fetchData"
    :columns="columns"
    :search-fields="searchFields"
  >
    <template #summary>
      <el-row :gutter="20" class="summary-cards">
        <el-col :span="6">
          <el-card shadow="hover">
            <el-statistic title="总品种数" :value="summary.totalItems">
              <template #suffix>种</template>
            </el-statistic>
          </el-card>
        </el-col>
        <el-col :span="6">
          <el-card shadow="hover">
            <el-statistic title="库存总值" :value="summary.totalValue" :precision="2">
              <template #prefix>¥</template>
            </el-statistic>
          </el-card>
        </el-col>
        <el-col :span="6">
          <el-card shadow="hover">
            <el-statistic title="低库存" :value="summary.totalLowStock">
              <template #suffix>种</template>
            </el-statistic>
          </el-card>
        </el-col>
        <el-col :span="6">
          <el-card shadow="hover">
            <el-statistic title="缺货" :value="summary.totalOutOfStock">
              <template #suffix>种</template>
            </el-statistic>
          </el-card>
        </el-col>
      </el-row>
    </template>

    <template #cell-stock="{ row }">
      <div class="stock-info">
        <span :class="getStockClass(row)">
          {{ row.availableStock }} / {{ row.maxStock }}
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

    <template #cell-status="{ row }">
      <el-tag :type="getStatusType(row.status)">
        {{ getStatusLabel(row.status) }}
      </el-tag>
    </template>

    <template #actions="{ row }">
      <el-button link type="primary" @click="handleView(row)">查看</el-button>
      <el-button link type="primary" @click="handleEdit(row)">编辑</el-button>
      <el-button link type="primary" @click="handleViewStock(row)">流水</el-button>
      <el-button link type="success" @click="handleQuickIssue(row)">领用</el-button>
    </template>
  </BaseListPage>

  <StockMovementDialog
    v-model="stockMovementVisible"
    :consumable="currentConsumable"
  />
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { consumableApi, consumableCategoryApi } from '@/api/consumables'
import type { Consumable, StockSummary, ConsumableStatus } from '@/types/consumables'
import BaseListPage from '@/components/common/BaseListPage.vue'
import StockMovementDialog from './components/StockMovementDialog.vue'

const router = useRouter()

const columns = [
  { prop: 'code', label: '编码', width: 120 },
  { prop: 'name', label: '名称', width: 200 },
  { prop: 'category.name', label: '分类', width: 120 },
  { prop: 'specification', label: '规格型号', width: 150 },
  { prop: 'brand', label: '品牌', width: 100 },
  { prop: 'stock', label: '库存', width: 120, slot: true },
  { prop: 'averagePrice', label: '平均价格', width: 100, format: (row: any) => `¥${row.averagePrice}` },
  { prop: 'status', label: '状态', width: 100, slot: true },
  { prop: 'warehouse.name', label: '存放仓库', width: 120 }
]

const searchFields = [
  {
    field: 'category',
    label: '分类',
    type: 'tree-select',
    options: [],
    optionLabel: 'name',
    optionValue: 'id'
  },
  {
    field: 'status',
    label: '状态',
    type: 'select',
    options: [
      { label: '正常', value: 'normal' },
      { label: '库存不足', value: 'low_stock' },
      { label: '缺货', value: 'out_of_stock' },
      { label: '停用', value: 'discontinued' }
    ]
  },
  {
    field: 'search',
    label: '搜索',
    type: 'input',
    placeholder: '编码/名称/品牌'
  }
]

const summary = ref<StockSummary>({
  totalItems: 0,
  totalValue: 0,
  totalLowStock: 0,
  totalOutOfStock: 0
})

const stockMovementVisible = ref(false)
const currentConsumable = ref<Consumable | null>(null)

const getStockClass = (row: Consumable) => {
  if (row.status === 'out_of_stock') return 'text-danger'
  if (row.status === 'low_stock') return 'text-warning'
  return 'text-success'
}

const getStockPercentage = (row: Consumable) => {
  if (row.maxStock === 0) return 0
  return Math.min((row.availableStock / row.maxStock) * 100, 100)
}

const getProgressColor = (row: Consumable) => {
  const percentage = getStockPercentage(row)
  if (percentage <= 20) return '#f56c6c'
  if (percentage <= 50) return '#e6a23c'
  return '#67c23a'
}

const getStatusType = (status: ConsumableStatus) => {
  const typeMap: Record<ConsumableStatus, string> = {
    normal: 'success',
    low_stock: 'warning',
    out_of_stock: 'danger',
    discontinued: 'info'
  }
  return typeMap[status] || 'info'
}

const getStatusLabel = (status: ConsumableStatus) => {
  const labelMap: Record<ConsumableStatus, string> = {
    normal: '正常',
    low_stock: '库存不足',
    out_of_stock: '缺货',
    discontinued: '停用'
  }
  return labelMap[status] || status
}

const fetchData = async (params: any) => {
  const [data, summaryData] = await Promise.all([
    consumableApi.list(params),
    consumableApi.getStockSummary(params.category)
  ])
  summary.value = summaryData
  return data
}

const handleView = (row: Consumable) => {
  router.push(`/consumables/${row.id}`)
}

const handleEdit = (row: Consumable) => {
  router.push(`/consumables/${row.id}/edit`)
}

const handleViewStock = (row: Consumable) => {
  currentConsumable.value = row
  stockMovementVisible.value = true
}

const handleQuickIssue = (row: Consumable) => {
  router.push({
    path: '/consumables/issue/create',
    query: { consumableId: row.id }
  })
}

onMounted(async () => {
  // Load categories for search filter
  const { results } = await consumableCategoryApi.list()
  const categoryField = searchFields.find(f => f.field === 'category')
  if (categoryField) {
    categoryField.options = results
  }
})
</script>

<style scoped>
.summary-cards {
  margin-bottom: 20px;
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

---

## Component: ConsumableSelector

```vue
<!-- frontend/src/components/consumables/ConsumableSelector.vue -->
<template>
  <el-dialog
    v-model="visible"
    title="选择耗材"
    width="900px"
    :close-on-click-modal="false"
  >
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
        <el-switch v-model="searchForm.hasStock" @change="handleSearch" />
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
          <span :class="getStockClass(row)">{{ row.availableStock }}</span>
          {{ row.unit }}
        </template>
      </el-table-column>
      <el-table-column prop="averagePrice" label="平均价" width="80">
        <template #default="{ row }">¥{{ row.averagePrice }}</template>
      </el-table-column>
    </el-table>

    <el-pagination
      v-model:current-page="pagination.page"
      v-model:page-size="pagination.pageSize"
      :total="pagination.total"
      small
      layout="total, prev, pager, next"
      @current-change="fetchData"
    />

    <template #footer>
      <el-button @click="visible = false">取消</el-button>
      <el-button type="primary" @click="handleConfirm">确定</el-button>
    </template>
  </el-dialog>
</template>

<script setup lang="ts">
import { ref, reactive, computed, watch } from 'vue'
import { Search } from '@element-plus/icons-vue'
import { consumableApi, consumableCategoryApi } from '@/api/consumables'
import type { Consumable } from '@/types/consumables'

interface Props {
  modelValue: boolean
  stockFilter?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  stockFilter: false
})

const emit = defineEmits<{
  (e: 'update:modelValue', value: boolean): void
  (e: 'confirm', items: Consumable[]): void
}>()

const visible = computed({
  get: () => props.modelValue,
  set: (val) => emit('update:modelValue', val)
})

const loading = ref(false)
const tableRef = ref()
const tableData = ref<Consumable[]>([])
const selectedItems = ref<Consumable[]>([])
const categoryOptions = ref<any[]>([])

const searchForm = reactive({
  search: '',
  category: null,
  hasStock: true
})

const pagination = reactive({
  page: 1,
  pageSize: 20,
  total: 0
})

const getStockClass = (row: Consumable) => {
  if (row.availableStock <= 0) return 'text-danger'
  if (row.availableStock <= row.minStock) return 'text-warning'
  return ''
}

const fetchData = async () => {
  loading.value = true
  try {
    const params: any = {
      ...searchForm,
      page: pagination.page,
      pageSize: pagination.pageSize
    }

    if (props.stockFilter && searchForm.hasStock) {
      params.availableStock__gt = 0
    }

    const response = await consumableApi.list(params)
    tableData.value = response.results
    pagination.total = response.count
  } finally {
    loading.value = false
  }
}

const handleSearch = () => {
  pagination.page = 1
  fetchData()
}

const handleSelectionChange = (selection: Consumable[]) => {
  selectedItems.value = selection
}

const handleConfirm = () => {
  emit('confirm', selectedItems.value)
  visible.value = false
}

watch(() => props.modelValue, async (val) => {
  if (val) {
    // Load categories
    const { results } = await consumableCategoryApi.list()
    categoryOptions.value = results
    fetchData()
  }
})
</script>

<style scoped>
.text-danger {
  color: #f56c6c;
}

.text-warning {
  color: #e6a23c;
}
</style>
```

---

## Output Files

| File | Description |
|------|-------------|
| `frontend/src/types/consumables.ts` | Consumable type definitions |
| `frontend/src/api/consumables.ts` | Consumable API service |
| `frontend/src/views/consumables/ConsumableList.vue` | Consumable list page |
| `frontend/src/views/consumables/ConsumableForm.vue` | Consumable form page |
| `frontend/src/views/consumables/PurchaseList.vue` | Purchase order list |
| `frontend/src/views/consumables/PurchaseForm.vue` | Purchase order form |
| `frontend/src/views/consumables/IssueList.vue` | Issue order list |
| `frontend/src/views/consumables/IssueForm.vue` | Issue order form |
| `frontend/src/components/consumables/ConsumableSelector.vue` | Consumable selector |
| `frontend/src/components/consumables/StockMovementDialog.vue` | Stock movement dialog |
