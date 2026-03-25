# Phase 1.7: Asset Lifecycle Management - Frontend Implementation v2

## Document Information

| Project | Details |
|---------|---------|
| PRD Version | v2.0 (Updated for API Standardization) |
| Updated Date | 2026-01-22 |
| References | [frontend_api_standardization_design.md](../common_base_features/00_core/frontend_api_standardization_design.md) |

---

## Task Overview

Implement asset lifecycle management including purchase requests, asset receipts, maintenance, and disposal workflows.

---

## API Service Layer

### Type Definitions

```typescript
// frontend/src/types/lifecycle.ts

// Purchase Request
export interface PurchaseRequest {
  id: string
  requestNo: string
  departmentId?: string
  department?: Department
  costCenterId?: string
  requestDate: string
  expectedDate?: string
  budgetAmount?: number
  reason: string
  status: RequestStatus
  itemsTotalAmount: number
  m18PurchaseOrderNo?: string
  attachments: string[]
  items: PurchaseRequestItem[]
  approvals?: ApprovalRecord[]
  organizationId: string
  createdAt: string
  createdBy: string
}

export enum RequestStatus {
  DRAFT = 'draft',
  SUBMITTED = 'submitted',
  APPROVED = 'approved',
  REJECTED = 'rejected',
  PROCESSING = 'processing',
  COMPLETED = 'completed'
}

export interface PurchaseRequestItem {
  id: string
  assetCategoryId?: string
  assetCategory?: AssetCategory
  itemName: string
  specification?: string
  brand?: string
  quantity: number
  unit?: string
  unitPrice: number
  amount: number
}

// Asset Receipt
export interface AssetReceipt {
  id: string
  receiptNo: string
  receiptType: ReceiptType
  receiptDate: string
  supplier?: string
  deliveryNo?: string
  status: ReceiptStatus
  items: ReceiptItem[]
  inspections?: InspectionRecord[]
  organizationId: string
  createdAt: string
}

export enum ReceiptType {
  PURCHASE = 'purchase',
  TRANSFER = 'transfer',
  RETURN = 'return'
}

export enum ReceiptStatus {
  DRAFT = 'draft',
  SUBMITTED = 'submitted',
  INSPECTING = 'inspecting',
  PASSED = 'passed',
  REJECTED = 'rejected'
}

export interface ReceiptItem {
  id: string
  itemName: string
  specification?: string
  orderedQuantity: number
  receivedQuantity: number
  qualifiedQuantity: number
  defectiveQuantity: number
  remark?: string
}

// Maintenance
export interface MaintenanceRequest {
  id: string
  maintenanceNo: string
  assetId: string
  asset?: Asset
  priority: MaintenancePriority
  faultDescription: string
  faultPhotoUrls?: string[]
  status: MaintenanceStatus
  reporterId: string
  reporter?: User
  assignedToId?: string
  assignedTo?: User
  estimatedCost?: number
  actualCost?: number
  completedAt?: string
  organizationId: string
  createdAt: string
}

export enum MaintenancePriority {
  LOW = 'low',
  NORMAL = 'normal',
  HIGH = 'high',
  URGENT = 'urgent'
}

export enum MaintenanceStatus {
  REPORTED = 'reported',
  ASSIGNED = 'assigned',
  PROCESSING = 'processing',
  COMPLETED = 'completed',
  CANCELLED = 'cancelled'
}

export interface MaintenancePlan {
  id: string
  planNo: string
  name: string
  assetCategoryId?: string
  cycle: MaintenanceCycle
  cycleValue: number
  lastPlanDate?: string
  nextPlanDate: string
  organizationId: string
}

export enum MaintenanceCycle {
  DAILY = 'daily',
  WEEKLY = 'weekly',
  MONTHLY = 'monthly',
  QUARTERLY = 'quarterly',
  YEARLY = 'yearly'
}

export interface MaintenanceTask {
  id: string
  planId: string
  assetId: string
  asset?: Asset
  scheduledDate: string
  status: TaskStatus
  completedAt?: string
  result?: string
}

export enum TaskStatus {
  PENDING = 'pending',
  IN_PROGRESS = 'in_progress',
  COMPLETED = 'completed',
  OVERDUE = 'overdue'
}

// Disposal
export interface DisposalRequest {
  id: string
  disposalNo: string
  departmentId?: string
  department?: Department
  disposalType: DisposalType
  reasonType: DisposalReason
  disposalReason: string
  status: DisposalStatus
  items: DisposalItem[]
  approvals?: ApprovalRecord[]
  organizationId: string
  createdAt: string
}

export enum DisposalType {
  SCRAP = 'scrap',
  SALE = 'sale',
  DONATION = 'donation',
  TRANSFER = 'transfer',
  DESTROY = 'destroy'
}

export enum DisposalReason {
  DAMAGE = 'damage',
  OBSOLETE = 'obsolete',
  EXPIRED = 'expired',
  EXCESS = 'excess',
  OTHER = 'other'
}

export enum DisposalStatus {
  DRAFT = 'draft',
  SUBMITTED = 'submitted',
  APPRAISAL = 'appraisal',
  APPROVED = 'approved',
  REJECTED = 'rejected',
  EXECUTED = 'executed'
}

export interface DisposalItem {
  id: string
  assetId: string
  asset?: Asset
  appraisedValue?: number
  appraisalResult?: string
}

export interface ApprovalRecord {
  id: string
  approvalLevel: number
  approverId?: string
  approver?: User
  action: 'approve' | 'reject' | 'cancel'
  comment?: string
  actedAt?: string
}
```

### API Service

```typescript
// frontend/src/api/lifecycle.ts

import request from '@/utils/request'
import type { PaginatedResponse } from '@/types/api'
import type {
  PurchaseRequest,
  AssetReceipt,
  MaintenanceRequest,
  MaintenancePlan,
  MaintenanceTask,
  DisposalRequest
} from '@/types/lifecycle'

// Purchase Request API
export const purchaseRequestApi = {
  list(params?: any): Promise<PaginatedResponse<PurchaseRequest>> {
    return request.get('/lifecycle/purchase-requests/', { params })
  },

  get(id: string): Promise<PurchaseRequest> {
    return request.get(`/lifecycle/purchase-requests/${id}/`)
  },

  create(data: any): Promise<PurchaseRequest> {
    return request.post('/lifecycle/purchase-requests/', data)
  },

  update(id: string, data: any): Promise<PurchaseRequest> {
    return request.put(`/lifecycle/purchase-requests/${id}/`, data)
  },

  delete(id: string): Promise<void> {
    return request.delete(`/lifecycle/purchase-requests/${id}/`)
  },

  submit(id: string): Promise<void> {
    return request.post(`/lifecycle/purchase-requests/${id}/submit/`)
  },

  approve(id: string, data: {
    action: 'approve' | 'reject'
    comment?: string
  }): Promise<void> {
    return request.post(`/lifecycle/purchase-requests/${id}/approve/`, data)
  }
}

// Asset Receipt API
export const receiptApi = {
  list(params?: any): Promise<PaginatedResponse<AssetReceipt>> {
    return request.get('/lifecycle/asset-receipts/', { params })
  },

  get(id: string): Promise<AssetReceipt> {
    return request.get(`/lifecycle/asset-receipts/${id}/`)
  },

  create(data: any): Promise<AssetReceipt> {
    return request.post('/lifecycle/asset-receipts/', data)
  },

  update(id: string, data: any): Promise<AssetReceipt> {
    return request.put(`/lifecycle/asset-receipts/${id}/`, data)
  },

  submit(id: string): Promise<void> {
    return request.post(`/lifecycle/asset-receipts/${id}/submit/`)
  },

  passInspection(id: string, data: {
    inspectionResult: string
  }): Promise<void> {
    return request.post(`/lifecycle/asset-receipts/${id}/pass-inspection/`, data)
  },

  rejectInspection(id: string, data: {
    reason: string
  }): Promise<void> {
    return request.post(`/lifecycle/asset-receipts/${id}/reject-inspection/`, data)
  }
}

// Maintenance API
export const maintenanceApi = {
  list(params?: any): Promise<PaginatedResponse<MaintenanceRequest>> {
    return request.get('/lifecycle/maintenance/', { params })
  },

  get(id: string): Promise<MaintenanceRequest> {
    return request.get(`/lifecycle/maintenance/${id}/`)
  },

  create(data: any): Promise<MaintenanceRequest> {
    return request.post('/lifecycle/maintenance/', data)
  },

  update(id: string, data: any): Promise<MaintenanceRequest> {
    return request.put(`/lifecycle/maintenance/${id}/`, data)
  },

  assign(id: string, data: {
    assignedTo: string
    estimatedCost?: number
  }): Promise<void> {
    return request.post(`/lifecycle/maintenance/${id}/assign/`, data)
  },

  complete(id: string, data: {
    actualCost: number
    result: string
    photoUrls?: string[]
  }): Promise<void> {
    return request.post(`/lifecycle/maintenance/${id}/complete/`, data)
  },

  verify(id: string, data: {
    action: 'approve' | 'reject'
    comment?: string
  }): Promise<void> {
    return request.post(`/lifecycle/maintenance/${id}/verify/`, data)
  }
}

export const maintenancePlanApi = {
  list(params?: any): Promise<PaginatedResponse<MaintenancePlan>> {
    return request.get('/lifecycle/maintenance-plans/', { params })
  },

  get(id: string): Promise<MaintenancePlan> {
    return request.get(`/lifecycle/maintenance-plans/${id}/`)
  },

  create(data: any): Promise<MaintenancePlan> {
    return request.post('/lifecycle/maintenance-plans/', data)
  },

  update(id: string, data: any): Promise<MaintenancePlan> {
    return request.put(`/lifecycle/maintenance-plans/${id}/`, data)
  },

  delete(id: string): Promise<void> {
    return request.delete(`/lifecycle/maintenance-plans/${id}/`)
  }
}

export const maintenanceTaskApi = {
  list(params?: any): Promise<PaginatedResponse<MaintenanceTask>> {
    return request.get('/lifecycle/maintenance-tasks/', { params })
  },

  get(id: string): Promise<MaintenanceTask> {
    return request.get(`/lifecycle/maintenance-tasks/${id}/`)
  },

  execute(id: string, data: {
    result: string
    photoUrls?: string[]
  }): Promise<void> {
    return request.post(`/lifecycle/maintenance-tasks/${id}/execute/`, data)
  }
}

// Disposal API
export const disposalApi = {
  list(params?: any): Promise<PaginatedResponse<DisposalRequest>> {
    return request.get('/lifecycle/disposal-requests/', { params })
  },

  get(id: string): Promise<DisposalRequest> {
    return request.get(`/lifecycle/disposal-requests/${id}/`)
  },

  create(data: any): Promise<DisposalRequest> {
    return request.post('/lifecycle/disposal-requests/', data)
  },

  update(id: string, data: any): Promise<DisposalRequest> {
    return request.put(`/lifecycle/disposal-requests/${id}/`, data)
  },

  delete(id: string): Promise<void> {
    return request.delete(`/lifecycle/disposal-requests/${id}/`)
  },

  submitAppraisal(id: string): Promise<void> {
    return request.post(`/lifecycle/disposal-requests/${id}/submit-appraisal/`)
  },

  completeAppraisal(itemId: string, data: {
    appraisedValue: number
    appraisalResult: string
  }): Promise<void> {
    return request.post(`/lifecycle/disposal-requests/items/${itemId}/complete-appraisal/`, data)
  },

  execute(id: string, data: {
    executionDate: string
    executionProof?: string[]
  }): Promise<void> {
    return request.post(`/lifecycle/disposal-requests/${id}/execute/`, data)
  }
}
```

---

## Component: PurchaseRequestList

```vue
<!-- frontend/src/views/lifecycle/purchase/PurchaseRequestList.vue -->
<template>
  <BaseListPage
    title="采购申请"
    :fetch-method="fetchData"
    :columns="columns"
    :search-fields="searchFields"
  >
    <template #actions="{ row }">
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
        v-if="row.status === 'submitted'"
        link
        type="warning"
        @click="handleApprove(row)"
      >审批</el-button>
      <el-button
        v-if="row.status === 'draft'"
        link
        type="danger"
        @click="handleDelete(row)"
      >删除</el-button>
    </template>
  </BaseListPage>
</template>

<script setup lang="ts">
import { useRouter } from 'vue-router'
import { ElMessageBox } from 'element-plus'
import { purchaseRequestApi } from '@/api/lifecycle'
import type { PurchaseRequest, RequestStatus } from '@/types/lifecycle'
import BaseListPage from '@/components/common/BaseListPage.vue'

const router = useRouter()

const columns = [
  { prop: 'requestNo', label: '申请单号', width: 150 },
  {
    prop: 'status',
    label: '状态',
    width: 100,
    format: (row: PurchaseRequest) => {
      const labelMap: Record<RequestStatus, string> = {
        draft: '草稿',
        submitted: '已提交',
        approved: '已审批',
        rejected: '已拒绝',
        processing: '采购中',
        completed: '采购完成'
      }
      return labelMap[row.status]
    },
    tag: (row: PurchaseRequest) => {
      const typeMap: Record<RequestStatus, string> = {
        draft: 'info',
        submitted: 'warning',
        approved: 'success',
        rejected: 'danger',
        processing: 'primary',
        completed: 'success'
      }
      return typeMap[row.status]
    }
  },
  { prop: 'applicant.fullName', label: '申请人', width: 100 },
  { prop: 'department.name', label: '申请部门', width: 120 },
  { prop: 'requestDate', label: '需求日期', width: 110 },
  { prop: 'expectedDate', label: '期望到货', width: 110 },
  { prop: 'reason', label: '申请原因', minWidth: 200, showOverflowTooltip: true },
  {
    prop: 'itemsTotalAmount',
    label: '申请金额',
    width: 110,
    align: 'right',
    format: (row: PurchaseRequest) => `¥${formatMoney(row.itemsTotalAmount)}`
  },
  { prop: 'm18PurchaseOrderNo', label: 'M18采购单', width: 130 }
]

const searchFields = [
  { field: 'requestNo', label: '申请单号', type: 'input' },
  {
    field: 'status',
    label: '状态',
    type: 'select',
    options: [
      { label: '草稿', value: 'draft' },
      { label: '已提交', value: 'submitted' },
      { label: '已审批', value: 'approved' },
      { label: '已拒绝', value: 'rejected' },
      { label: '采购中', value: 'processing' },
      { label: '采购完成', value: 'completed' }
    ]
  },
  { field: 'departmentId', label: '申请部门', type: 'dept-picker' },
  {
    field: 'dateRange',
    label: '申请日期',
    type: 'daterange',
    startField: 'dateFrom',
    endField: 'dateTo'
  }
]

const fetchData = async (params: any) => {
  const { dateRange, ...rest } = params
  const queryParams = { ...rest }
  if (dateRange && dateRange.length === 2) {
    queryParams.requestDateFrom = dateRange[0]
    queryParams.requestDateTo = dateRange[1]
  }
  return await purchaseRequestApi.list(queryParams)
}

const handleView = (row: PurchaseRequest) => {
  router.push(`/lifecycle/purchase/${row.id}`)
}

const handleEdit = (row: PurchaseRequest) => {
  router.push(`/lifecycle/purchase/${row.id}/edit`)
}

const handleSubmit = async (row: PurchaseRequest) => {
  try {
    await ElMessageBox.confirm('确认提交该采购申请？', '提示', {
      type: 'warning'
    })
    await purchaseRequestApi.submit(row.id)
    // Refresh handled by BaseListPage
    window.location.reload()
  } catch {
    // Cancelled
  }
}

const handleApprove = (row: PurchaseRequest) => {
  router.push({
    path: `/lifecycle/purchase/${row.id}`,
    query: { mode: 'approve' }
  })
}

const handleDelete = async (row: PurchaseRequest) => {
  try {
    await ElMessageBox.confirm('确认删除该采购申请？', '提示', {
      type: 'warning'
    })
    await purchaseRequestApi.delete(row.id)
    window.location.reload()
  } catch {
    // Cancelled
  }
}

const formatMoney = (value: number) => {
  return value.toFixed(2)
}
</script>
```

---

## Component: MaintenanceTaskCalendar

```vue
<!-- frontend/src/views/lifecycle/maintenance/TaskCalendar.vue -->
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
              {{ task.asset?.assetName || '未命名资产' }}
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Task Detail Drawer -->
    <el-drawer v-model="drawerVisible" title="任务详情" size="400">
      <TaskDetail v-if="selectedTask" :task-id="selectedTask.id" @close="drawerVisible = false" />
    </el-drawer>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { ArrowLeft, ArrowRight } from '@element-plus/icons-vue'
import { maintenanceTaskApi } from '@/api/lifecycle'
import type { MaintenanceTask } from '@/types/lifecycle'
import TaskDetail from './TaskDetail.vue'

const weekdays = ['日', '一', '二', '三', '四', '五', '六']
const currentDate = ref(new Date())
const tasks = ref<MaintenanceTask[]>([])
const drawerVisible = ref(false)
const selectedTask = ref<MaintenanceTask | null>(null)

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

  // Previous month days
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

  // Current month days
  const today = new Date()
  for (let i = 1; i <= daysInMonth; i++) {
    const date = new Date(year, month, i)
    const dateStr = formatDate(date)
    days.push({
      date: i,
      otherMonth: false,
      isToday: isSameDay(date, today),
      fullDate: date,
      tasks: tasks.value.filter(t => t.scheduledDate === dateStr)
    })
  }

  // Next month days
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
  const response = await maintenanceTaskApi.list({
    scheduledDateFrom: `${year}-${String(month).padStart(2, '0')}-01`,
    scheduledDateTo: `${year}-${String(month).padStart(2, '0')}-31`
  })
  tasks.value = response.results
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
    // Show day tasks
  }
}

const handleTaskClick = (task: MaintenanceTask) => {
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

## Output Files

| File | Description |
|------|-------------|
| `frontend/src/types/lifecycle.ts` | Lifecycle type definitions |
| `frontend/src/api/lifecycle.ts` | Lifecycle API service |
| `frontend/src/views/lifecycle/purchase/PurchaseRequestList.vue` | Purchase request list |
| `frontend/src/views/lifecycle/purchase/PurchaseRequestForm.vue` | Purchase request form |
| `frontend/src/views/lifecycle/receipt/ReceiptList.vue` | Asset receipt list |
| `frontend/src/views/lifecycle/receipt/ReceiptForm.vue` | Asset receipt form |
| `frontend/src/views/lifecycle/maintenance/MaintenanceList.vue` | Maintenance list |
| `frontend/src/views/lifecycle/maintenance/MaintenanceForm.vue` | Maintenance form |
| `frontend/src/views/lifecycle/maintenance/TaskCalendar.vue` | Task calendar view |
| `frontend/src/views/lifecycle/disposal/DisposalList.vue` | Disposal request list |
| `frontend/src/views/lifecycle/disposal/DisposalForm.vue` | Disposal request form |
