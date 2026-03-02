# Frontend Remaining Features Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Implement all remaining frontend features to complete the GZEAMS (Hook Fixed Assets) system including lifecycle management, integration, permissions, leasing, insurance, notifications, SSO, and mobile modules.

**Architecture:** Vue 3 (Composition API) + TypeScript + Element Plus UI, following the existing BaseListPage/BaseDetailPage/BaseFormPage pattern with metadata-driven components. Backend uses Django REST Framework with standardized API response format and camelCase field transformation.

**Tech Stack:** Vue 3, Vite, Element Plus, Pinia, TypeScript, Axios, Django REST Framework

---

## Current Status Summary

### Completed Modules (100%)
| Module | Pages | Status |
|--------|-------|--------|
| Assets | 22 pages | Complete |
| Software Licenses | 5 pages | Complete |
| Inventory | 2 pages | Complete |
| Consumables | 1 page | Complete |
| Finance | 2 pages | Complete |
| Workflow Admin | 2 pages | Complete |
| System/Departments | 1 page | Partial (needs CRUD) |
| Workflow Tasks | 2 pages | Partial (needs real API) |

### Backend APIs Available (No Frontend Yet)
| Module | Endpoints | Frontend Status |
|--------|-----------|-----------------|
| Lifecycle | purchase-requests, asset-receipts, maintenance, maintenance-plans, maintenance-tasks, disposal-requests | Missing |
| Integration | configs, sync-tasks, logs, mappings | Missing |
| Permissions | field-permissions, data-permissions, data-permission-expands, audit-logs | Missing |
| Leasing | lease-contracts, lease-items, rent-payments, lease-returns, lease-extensions | Missing |
| Insurance | companies, policies, insured-assets, payments, claims, renewals | Missing |
| Notifications | templates, configs, logs, channels, messages, inapp | Missing |
| SSO | configs, mappings, sync | Missing |
| Mobile | devices, security-logs, sync, conflicts, sync-logs, approvals, delegates | Partial |

### Stub Pages Needing Completion
1. `TaskDetail.vue` - Workflow task approval (currently mock data)
2. `DepartmentList.vue` - Department CRUD (TODO comments present)

---

## Implementation Priority

### Priority P0 (Critical - Core Business)
- TaskDetail.vue - Real workflow task approval
- DepartmentList.vue - Complete CRUD operations
- Return API - `/assets/returns/` endpoint (backend exists)

### Priority P1 (High - Essential Features)
- Lifecycle Management API client and pages
- Permissions Management API client and pages
- Notifications API client and pages
- Integration Management API client and pages

### Priority P2 (Medium - Extended Features)
- Leasing Management API client and pages
- Insurance Management API client and pages
- SSO Management API client and pages
- Mobile Enhancement API client and pages

---

## Task 1: Complete TaskDetail.vue - Workflow Task Approval

**Files:**
- Modify: `frontend/src/views/workflow/TaskDetail.vue`
- Modify: `frontend/src/api/workflow.ts`
- Test: Create test file after implementation

**Step 1: Add workflow detail API**

Edit `frontend/src/api/workflow.ts`:
```typescript
// Add these functions after existing exports

export const getTaskDetail = (id: string) => {
    return request({
        url: `/workflows/tasks/${id}/`,
        method: 'get'
    })
}

export const approveTask = (id: string, data: { comment: string }) => {
    return request({
        url: `/workflows/tasks/${id}/approve/`,
        method: 'post',
        data
    })
}

export const rejectTask = (id: string, data: { comment: string }) => {
    return request({
        url: `/workflows/tasks/${id}/reject/`,
        method: 'post',
        data
    })
}

export const getTaskFormData = (taskId: string) => {
    return request({
        url: `/workflows/tasks/${taskId}/form-data/`,
        method: 'get'
    })
}
```

**Step 2: Rewrite TaskDetail.vue with real API integration**

Replace entire `frontend/src/views/workflow/TaskDetail.vue`:
```vue
<template>
  <div class="task-detail">
    <el-page-header @back="$router.back()" content="任务办理" class="page-header" />

    <el-card v-loading="loading" class="mt-20">
      <template #header>
        <span>任务信息</span>
      </template>
      <el-descriptions v-if="taskData" border :column="2">
        <el-descriptions-item label="任务标题">{{ taskData.title }}</el-descriptions-item>
        <el-descriptions-item label="任务类型">{{ taskData.workflowName }}</el-descriptions-item>
        <el-descriptions-item label="发起人">{{ taskData.initiator?.realName }}</el-descriptions-item>
        <el-descriptions-item label="发起时间">{{ formatDate(taskData.createdAt) }}</el-descriptions-item>
        <el-descriptions-item label="当前节点">{{ taskData.currentNodeName }}</el-descriptions-item>
        <el-descriptions-item label="任务状态">
          <el-tag :type="getStatusType(taskData.status)">{{ getStatusText(taskData.status) }}</el-tag>
        </el-descriptions-item>
      </el-descriptions>
    </el-card>

    <el-card v-if="formData" class="mt-20">
      <template #header>
        <span>表单信息</span>
      </template>
      <DynamicForm
        v-if="formSchema"
        :schema="formSchema"
        :data="formData"
        :readonly="true"
      />
      <el-descriptions v-else border>
        <el-descriptions-item
          v-for="(value, key) in formData"
          :key="key"
          :label="key"
        >
          {{ value }}
        </el-descriptions-item>
      </el-descriptions>
    </el-card>

    <el-card v-if="taskData && taskData.status === 'pending'" class="mt-20">
      <template #header>
        <span>审批处理</span>
      </template>
      <el-form label-width="80px">
        <el-form-item label="审批意见" required>
          <el-input
            v-model="comment"
            type="textarea"
            :rows="4"
            placeholder="请输入审批意见"
          />
        </el-form-item>
        <el-form-item>
          <el-button
            type="success"
            :loading="submitting"
            @click="handleApprove"
          >
            同意
          </el-button>
          <el-button
            type="danger"
            :loading="submitting"
            @click="handleReject"
          >
            拒绝
          </el-button>
        </el-form-item>
      </el-form>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { getTaskDetail, approveTask, rejectTask, getTaskFormData } from '@/api/workflow'
import DynamicForm from '@/components/engine/DynamicForm.vue'

const route = useRoute()
const router = useRouter()

const loading = ref(false)
const submitting = ref(false)
const taskData = ref<any>(null)
const formData = ref<any>(null)
const formSchema = ref<any>(null)
const comment = ref('同意')

const taskId = route.params.id as string

const formatDate = (date: string) => {
  return new Date(date).toLocaleString('zh-CN')
}

const getStatusType = (status: string) => {
  const map: Record<string, string> = {
    pending: 'warning',
    approved: 'success',
    rejected: 'danger',
    cancelled: 'info'
  }
  return map[status] || 'info'
}

const getStatusText = (status: string) => {
  const map: Record<string, string> = {
    pending: '待审批',
    approved: '已通过',
    rejected: '已拒绝',
    cancelled: '已取消'
  }
  return map[status] || status
}

const loadTaskDetail = async () => {
  loading.value = true
  try {
    const [taskRes, formRes] = await Promise.all([
      getTaskDetail(taskId),
      getTaskFormData(taskId).catch(() => null)
    ])
    taskData.value = taskRes.data || taskRes
    if (formRes) {
      formData.value = formRes.data || formRes
    }
  } catch (error: any) {
    ElMessage.error(error.message || '加载任务详情失败')
  } finally {
    loading.value = false
  }
}

const handleApprove = async () => {
  if (!comment.value.trim()) {
    ElMessage.warning('请输入审批意见')
    return
  }

  await ElMessageBox.confirm('确认同意该审批吗？', '确认', {
    type: 'warning'
  })

  submitting.value = true
  try {
    await approveTask(taskId, { comment: comment.value })
    ElMessage.success('审批成功')
    router.back()
  } catch (error: any) {
    ElMessage.error(error.message || '审批失败')
  } finally {
    submitting.value = false
  }
}

const handleReject = async () => {
  if (!comment.value.trim()) {
    ElMessage.warning('请输入拒绝理由')
    return
  }

  await ElMessageBox.confirm('确认拒绝该审批吗？', '确认', {
    type: 'warning'
  })

  submitting.value = true
  try {
    await rejectTask(taskId, { comment: comment.value })
    ElMessage.success('已拒绝')
    router.back()
  } catch (error: any) {
    ElMessage.error(error.message || '操作失败')
  } finally {
    submitting.value = false
  }
}

onMounted(() => {
  loadTaskDetail()
})
</script>

<style scoped>
.task-detail {
  padding: 20px;
}
.page-header {
  margin-bottom: 20px;
}
.mt-20 {
  margin-top: 20px;
}
</style>
```

**Step 3: Test the implementation**

Run: `npm run dev`
Navigate to: `/workflow/task/:id` (use a valid task ID from backend)
Expected: Task details load, approve/reject buttons work

**Step 4: Commit**

```bash
git add frontend/src/views/workflow/TaskDetail.vue frontend/src/api/workflow.ts
git commit -m "feat(workflow): implement real task approval in TaskDetail"
```

---

## Task 2: Complete DepartmentList.vue - CRUD Operations

**Files:**
- Modify: `frontend/src/views/system/DepartmentList.vue`
- Modify: `frontend/src/api/system.ts`
- Create: `frontend/src/views/system/components/DepartmentForm.vue`

**Step 1: Add department API to system.ts**

Edit `frontend/src/api/system.ts` - add after existing exports:
```typescript
// Department CRUD operations
export const getDepartmentTree = () => {
    return request({
        url: '/organizations/departments/tree/',
        method: 'get'
    })
}

export const getDepartmentDetail = (id: string) => {
    return request({
        url: `/organizations/departments/${id}/`,
        method: 'get'
    })
}

export const createDepartment = (data: any) => {
    return request({
        url: '/organizations/departments/',
        method: 'post',
        data
    })
}

export const updateDepartment = (id: string, data: any) => {
    return request({
        url: `/organizations/departments/${id}/`,
        method: 'put',
        data
    })
}

export const partialUpdateDepartment = (id: string, data: any) => {
    return request({
        url: `/organizations/departments/${id}/`,
        method: 'patch',
        data
    })
}

export const deleteDepartment = (id: string) => {
    return request({
        url: `/organizations/departments/${id}/`,
        method: 'delete'
    })
}
```

**Step 2: Create DepartmentForm component**

Create `frontend/src/views/system/components/DepartmentForm.vue`:
```vue
<template>
  <el-dialog
    :model-value="visible"
    :title="isEdit ? '编辑部门' : (isSub ? '添加子部门' : '新建部门')"
    width="500px"
    @update:model-value="$emit('update:visible', $event)"
    @close="handleClose"
  >
    <el-form
      ref="formRef"
      :model="formData"
      :rules="rules"
      label-width="100px"
    >
      <el-form-item label="部门名称" prop="name">
        <el-input v-model="formData.name" placeholder="请输入部门名称" />
      </el-form-item>
      <el-form-item label="部门编码" prop="code">
        <el-input v-model="formData.code" placeholder="请输入部门编码" />
      </el-form-item>
      <el-form-item label="上级部门" prop="parentId" v-if="!isSub">
        <el-tree-select
          v-model="formData.parentId"
          :data="departmentTree"
          :props="{ label: 'name', value: 'id' }"
          placeholder="请选择上级部门（不选则为顶级部门）"
          clearable
          check-strictly
        />
      </el-form-item>
      <el-form-item label="负责人" prop="managerId">
        <el-select
          v-model="formData.managerId"
          placeholder="请选择负责人"
          filterable
          clearable
        >
          <el-option
            v-for="user in managerOptions"
            :key="user.id"
            :label="user.realName"
            :value="user.id"
          />
        </el-select>
      </el-form-item>
      <el-form-item label="联系电话" prop="phone">
        <el-input v-model="formData.phone" placeholder="请输入联系电话" />
      </el-form-item>
      <el-form-item label="排序" prop="sortOrder">
        <el-input-number v-model="formData.sortOrder" :min="0" :max="9999" />
      </el-form-item>
      <el-form-item label="状态" prop="isActive">
        <el-switch v-model="formData.isActive" />
      </el-form-item>
      <el-form-item label="描述" prop="description">
        <el-input
          v-model="formData.description"
          type="textarea"
          :rows="3"
          placeholder="请输入描述"
        />
      </el-form-item>
    </el-form>
    <template #footer>
      <el-button @click="handleClose">取消</el-button>
      <el-button type="primary" :loading="saving" @click="handleSubmit">确定</el-button>
    </template>
  </el-dialog>
</template>

<script setup lang="ts">
import { ref, reactive, watch, computed } from 'vue'
import { ElMessage } from 'element-plus'
import type { FormInstance } from 'element-plus'
import {
  createDepartment,
  updateDepartment,
  getDepartmentTree,
  getUsers
} from '@/api/system'

interface Props {
  visible: boolean
  data?: any
  parentData?: any
  departmentTree?: any[]
}

const props = defineProps<Props>()
const emit = defineEmits(['update:visible', 'success'])

const formRef = ref<FormInstance>()
const saving = ref(false)
const managerOptions = ref<any[]>([])

const isEdit = computed(() => !!props.data?.id)
const isSub = computed(() => !!props.parentData)

const formData = reactive({
  name: '',
  code: '',
  parentId: null as string | null,
  managerId: null as string | null,
  phone: '',
  sortOrder: 0,
  isActive: true,
  description: ''
})

const rules = {
  name: [{ required: true, message: '请输入部门名称', trigger: 'blur' }],
  code: [{ required: true, message: '请输入部门编码', trigger: 'blur' }]
}

const loadManagers = async () => {
  try {
    const res = await getUsers({ pageSize: 1000 })
    managerOptions.value = res.results || res.items || res
  } catch (error) {
    console.error('Failed to load users:', error)
  }
}

const resetForm = () => {
  Object.assign(formData, {
    name: '',
    code: '',
    parentId: null,
    managerId: null,
    phone: '',
    sortOrder: 0,
    isActive: true,
    description: ''
  })
  formRef.value?.clearValidate()
}

const handleClose = () => {
  emit('update:visible', false)
  resetForm()
}

const handleSubmit = async () => {
  if (!formRef.value) return

  await formRef.value.validate(async (valid) => {
    if (!valid) return

    saving.value = true
    try {
      const data = { ...formData }

      if (isSub.value && props.parentData?.id) {
        data.parentId = props.parentData.id
      }

      if (isEdit.value) {
        await updateDepartment(props.data.id, data)
        ElMessage.success('更新成功')
      } else {
        await createDepartment(data)
        ElMessage.success('创建成功')
      }

      emit('success')
      handleClose()
    } catch (error: any) {
      ElMessage.error(error.message || '操作失败')
    } finally {
      saving.value = false
    }
  })
}

watch(() => props.visible, (val) => {
  if (val) {
    loadManagers()
    if (props.data?.id) {
      Object.assign(formData, {
        name: props.data.name || '',
        code: props.data.code || '',
        parentId: props.data.parentId || null,
        managerId: props.data.managerId || null,
        phone: props.data.phone || '',
        sortOrder: props.data.sortOrder || 0,
        isActive: props.data.isActive ?? true,
        description: props.data.description || ''
      })
    }
  }
})
</script>
```

**Step 3: Rewrite DepartmentList.vue with full CRUD**

Replace `frontend/src/views/system/DepartmentList.vue`:
```vue
<template>
  <div class="department-list">
    <div class="page-header">
      <h3>部门管理</h3>
      <el-button type="primary" @click="handleCreate">新建部门</el-button>
    </div>

    <el-table
      :data="tableData"
      border
      row-key="id"
      default-expand-all
      :tree-props="{ children: 'children' }"
      v-loading="loading"
    >
      <el-table-column prop="name" label="部门名称" width="200" />
      <el-table-column prop="code" label="编码" width="120" />
      <el-table-column prop="manager.realName" label="负责人" width="120">
        <template #default="{ row }">
          {{ row.manager?.realName || '-' }}
        </template>
      </el-table-column>
      <el-table-column prop="phone" label="联系电话" width="140" />
      <el-table-column label="排序" width="80" align="center">
        <template #default="{ row }">{{ row.sortOrder }}</template>
      </el-table-column>
      <el-table-column label="状态" width="80" align="center">
        <template #default="{ row }">
          <el-tag :type="row.isActive ? 'success' : 'info'" size="small">
            {{ row.isActive ? '启用' : '停用' }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column label="操作" width="240" fixed="right">
        <template #default="{ row }">
          <el-button link type="primary" @click="handleEdit(row)">编辑</el-button>
          <el-button link type="primary" @click="handleAddSub(row)">添加子部门</el-button>
          <el-popconfirm
            title="确定删除该部门吗？"
            @confirm="handleDelete(row)"
          >
            <template #reference>
              <el-button link type="danger">删除</el-button>
            </template>
          </el-popconfirm>
        </template>
      </el-table-column>
    </el-table>

    <DepartmentForm
      v-model:visible="dialogVisible"
      :data="currentRow"
      :parent-data="parentRow"
      :department-tree="flatTreeData"
      @success="loadData"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { ElMessage } from 'element-plus'
import { getDepartmentTree, deleteDepartment } from '@/api/system'
import DepartmentForm from './components/DepartmentForm.vue'

const loading = ref(false)
const tableData = ref<any[]>([])
const dialogVisible = ref(false)
const currentRow = ref<any>(null)
const parentRow = ref<any>(null)

// Flatten tree for select dropdown
const flatTreeData = computed(() => {
  const flatten = (nodes: any[]): any[] => {
    const result: any[] = []
    nodes.forEach(node => {
      result.push({
        id: node.id,
        name: node.name,
        children: node.children
      })
      if (node.children?.length) {
        result.push(...flatten(node.children))
      }
    })
    return result
  }
  return flatten(tableData.value)
})

const loadData = async () => {
  loading.value = true
  try {
    const res = await getDepartmentTree()
    tableData.value = res.data || res
  } catch (error: any) {
    ElMessage.error(error.message || '加载部门列表失败')
  } finally {
    loading.value = false
  }
}

const handleCreate = () => {
  currentRow.value = null
  parentRow.value = null
  dialogVisible.value = true
}

const handleEdit = (row: any) => {
  currentRow.value = row
  parentRow.value = null
  dialogVisible.value = true
}

const handleAddSub = (row: any) => {
  currentRow.value = null
  parentRow.value = row
  dialogVisible.value = true
}

const handleDelete = async (row: any) => {
  try {
    await deleteDepartment(row.id)
    ElMessage.success('删除成功')
    await loadData()
  } catch (error: any) {
    ElMessage.error(error.message || '删除失败')
  }
}

onMounted(() => {
  loadData()
})
</script>

<style scoped>
.department-list {
  padding: 20px;
}
.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}
.page-header h3 {
  margin: 0;
  font-size: 18px;
}
</style>
```

**Step 4: Create components directory if missing**

Run:
```bash
mkdir -p frontend/src/views/system/components
touch frontend/src/views/system/components/__init__.py
```

**Step 5: Commit**

```bash
git add frontend/src/views/system/DepartmentList.vue frontend/src/api/system.ts frontend/src/views/system/components/DepartmentForm.vue
git commit -m "feat(system): complete department CRUD with form dialog"
```

---

## Task 3: Create Return API Client

**Files:**
- Create: `frontend/src/api/assets/return.ts`

**Step 1: Create return.ts API file**

Create `frontend/src/api/assets/return.ts`:
```typescript
import request from '@/utils/request'

export const getReturnList = (params: any) => {
    return request({
        url: '/assets/returns/',
        method: 'get',
        params
    })
}

export const getReturnDetail = (id: string) => {
    return request({
        url: `/assets/returns/${id}/`,
        method: 'get'
    })
}

export const createReturn = (data: any) => {
    return request({
        url: '/assets/returns/',
        method: 'post',
        data
    })
}

export const updateReturn = (id: string, data: any) => {
    return request({
        url: `/assets/returns/${id}/`,
        method: 'put',
        data
    })
}

export const submitReturn = (id: string) => {
    return request({
        url: `/assets/returns/${id}/submit/`,
        method: 'post'
    })
}

export const cancelReturn = (id: string) => {
    return request({
        url: `/assets/returns/${id}/cancel/`,
        method: 'post'
    })
}

export const approveReturn = (id: string) => {
    return request({
        url: `/assets/returns/${id}/approve/`,
        method: 'post'
    })
}

export const completeReturn = (id: string, data: any) => {
    return request({
        url: `/assets/returns/${id}/complete/`,
        method: 'post',
        data
    })
}
```

**Step 2: Commit**

```bash
git add frontend/src/api/assets/return.ts
git commit -m "feat(api): add asset return API client"
```

---

## Task 4: Create Lifecycle Management API Client

**Files:**
- Create: `frontend/src/api/lifecycle.ts`

**Step 1: Create lifecycle.ts API file**

Create `frontend/src/api/lifecycle.ts`:
```typescript
import request from '@/utils/request'

// Purchase Requests
export const getPurchaseRequestList = (params: any) => {
    return request({
        url: '/lifecycle/purchase-requests/',
        method: 'get',
        params
    })
}

export const getPurchaseRequestDetail = (id: string) => {
    return request({
        url: `/lifecycle/purchase-requests/${id}/`,
        method: 'get'
    })
}

export const createPurchaseRequest = (data: any) => {
    return request({
        url: '/lifecycle/purchase-requests/',
        method: 'post',
        data
    })
}

export const updatePurchaseRequest = (id: string, data: any) => {
    return request({
        url: `/lifecycle/purchase-requests/${id}/`,
        method: 'put',
        data
    })
}

export const submitPurchaseRequest = (id: string) => {
    return request({
        url: `/lifecycle/purchase-requests/${id}/submit/`,
        method: 'post'
    })
}

export const approvePurchaseRequest = (id: string, data: any) => {
    return request({
        url: `/lifecycle/purchase-requests/${id}/approve/`,
        method: 'post',
        data
    })
}

export const rejectPurchaseRequest = (id: string, data: any) => {
    return request({
        url: `/lifecycle/purchase-requests/${id}/reject/`,
        method: 'post',
        data
    })
}

// Asset Receipts
export const getAssetReceiptList = (params: any) => {
    return request({
        url: '/lifecycle/asset-receipts/',
        method: 'get',
        params
    })
}

export const getAssetReceiptDetail = (id: string) => {
    return request({
        url: `/lifecycle/asset-receipts/${id}/`,
        method: 'get'
    })
}

export const createAssetReceipt = (data: any) => {
    return request({
        url: '/lifecycle/asset-receipts/',
        method: 'post',
        data
    })
}

export const confirmReceipt = (id: string, data: any) => {
    return request({
        url: `/lifecycle/asset-receipts/${id}/confirm/`,
        method: 'post',
        data
    })
}

// Maintenance
export const getMaintenanceList = (params: any) => {
    return request({
        url: '/lifecycle/maintenance/',
        method: 'get',
        params
    })
}

export const getMaintenanceDetail = (id: string) => {
    return request({
        url: `/lifecycle/maintenance/${id}/`,
        method: 'get'
    })
}

export const createMaintenance = (data: any) => {
    return request({
        url: '/lifecycle/maintenance/',
        method: 'post',
        data
    })
}

export const updateMaintenance = (id: string, data: any) => {
    return request({
        url: `/lifecycle/maintenance/${id}/`,
        method: 'put',
        data
    })
}

export const completeMaintenance = (id: string, data: any) => {
    return request({
        url: `/lifecycle/maintenance/${id}/complete/`,
        method: 'post',
        data
    })
}

// Maintenance Plans
export const getMaintenancePlanList = (params: any) => {
    return request({
        url: '/lifecycle/maintenance-plans/',
        method: 'get',
        params
    })
}

export const getMaintenancePlanDetail = (id: string) => {
    return request({
        url: `/lifecycle/maintenance-plans/${id}/`,
        method: 'get'
    })
}

export const createMaintenancePlan = (data: any) => {
    return request({
        url: '/lifecycle/maintenance-plans/',
        method: 'post',
        data
    })
}

export const updateMaintenancePlan = (id: string, data: any) => {
    return request({
        url: `/lifecycle/maintenance-plans/${id}/`,
        method: 'put',
        data
    })
}

export const activateMaintenancePlan = (id: string) => {
    return request({
        url: `/lifecycle/maintenance-plans/${id}/activate/`,
        method: 'post'
    })
}

// Maintenance Tasks
export const getMaintenanceTaskList = (params: any) => {
    return request({
        url: '/lifecycle/maintenance-tasks/',
        method: 'get',
        params
    })
}

export const getMaintenanceTaskDetail = (id: string) => {
    return request({
        url: `/lifecycle/maintenance-tasks/${id}/`,
        method: 'get'
    })
}

export const completeMaintenanceTask = (id: string, data: any) => {
    return request({
        url: `/lifecycle/maintenance-tasks/${id}/complete/`,
        method: 'post',
        data
    })
}

// Disposal Requests
export const getDisposalRequestList = (params: any) => {
    return request({
        url: '/lifecycle/disposal-requests/',
        method: 'get',
        params
    })
}

export const getDisposalRequestDetail = (id: string) => {
    return request({
        url: `/lifecycle/disposal-requests/${id}/`,
        method: 'get'
    })
}

export const createDisposalRequest = (data: any) => {
    return request({
        url: '/lifecycle/disposal-requests/',
        method: 'post',
        data
    })
}

export const updateDisposalRequest = (id: string, data: any) => {
    return request({
        url: `/lifecycle/disposal-requests/${id}/`,
        method: 'put',
        data
    })
}

export const submitDisposalRequest = (id: string) => {
    return request({
        url: `/lifecycle/disposal-requests/${id}/submit/`,
        method: 'post'
    })
}

export const approveDisposalRequest = (id: string, data: any) => {
    return request({
        url: `/lifecycle/disposal-requests/${id}/approve/`,
        method: 'post',
        data
    })
}

export const confirmDisposal = (id: string, data: any) => {
    return request({
        url: `/lifecycle/disposal-requests/${id}/confirm/`,
        method: 'post',
        data
    })
}
```

**Step 2: Commit**

```bash
git add frontend/src/api/lifecycle.ts
git commit -m "feat(api): add lifecycle management API client"
```

---

## Task 5: Create Permissions Management API Client

**Files:**
- Create: `frontend/src/api/permissions.ts`

**Step 1: Create permissions.ts API file**

Create `frontend/src/api/permissions.ts`:
```typescript
import request from '@/utils/request'

// Field Permissions
export const getFieldPermissionList = (params: any) => {
    return request({
        url: '/permissions/field-permissions/',
        method: 'get',
        params
    })
}

export const getFieldPermissionDetail = (id: string) => {
    return request({
        url: `/permissions/field-permissions/${id}/`,
        method: 'get'
    })
}

export const createFieldPermission = (data: any) => {
    return request({
        url: '/permissions/field-permissions/',
        method: 'post',
        data
    })
}

export const updateFieldPermission = (id: string, data: any) => {
    return request({
        url: `/permissions/field-permissions/${id}/`,
        method: 'put',
        data
    })
}

export const deleteFieldPermission = (id: string) => {
    return request({
        url: `/permissions/field-permissions/${id}/`,
        method: 'delete'
    })
}

export const grantFieldPermission = (data: any) => {
    return request({
        url: '/permissions/field-permissions/grant/',
        method: 'post',
        data
    })
}

export const revokeFieldPermission = (data: any) => {
    return request({
        url: '/permissions/field-permissions/revoke/',
        method: 'post',
        data
    })
}

// Data Permissions
export const getDataPermissionList = (params: any) => {
    return request({
        url: '/permissions/data-permissions/',
        method: 'get',
        params
    })
}

export const getDataPermissionDetail = (id: string) => {
    return request({
        url: `/permissions/data-permissions/${id}/`,
        method: 'get'
    })
}

export const createDataPermission = (data: any) => {
    return request({
        url: '/permissions/data-permissions/',
        method: 'post',
        data
    })
}

export const updateDataPermission = (id: string, data: any) => {
    return request({
        url: `/permissions/data-permissions/${id}/`,
        method: 'put',
        data
    })
}

export const deleteDataPermission = (id: string) => {
    return request({
        url: `/permissions/data-permissions/${id}/`,
        method: 'delete'
    })
}

export const grantDataPermission = (data: any) => {
    return request({
        url: '/permissions/data-permissions/grant/',
        method: 'post',
        data
    })
}

export const revokeDataPermission = (data: any) => {
    return request({
        url: '/permissions/data-permissions/revoke/',
        method: 'post',
        data
    })
}

// Data Permission Expansions
export const getDataPermissionExpandList = (params: any) => {
    return request({
        url: '/permissions/data-permission-expands/',
        method: 'get',
        params
    })
}

export const getDataPermissionExpandDetail = (id: string) => {
    return request({
        url: `/permissions/data-permission-expands/${id}/`,
        method: 'get'
    })
}

export const activateDataPermissionExpand = (id: string) => {
    return request({
        url: `/permissions/data-permission-expands/${id}/activate/`,
        method: 'post'
    })
}

export const deactivateDataPermissionExpand = (id: string) => {
    return request({
        url: `/permissions/data-permission-expands/${id}/deactivate/`,
        method: 'post'
    })
}

// Audit Logs
export const getPermissionAuditLogList = (params: any) => {
    return request({
        url: '/permissions/audit-logs/',
        method: 'get',
        params
    })
}

export const getPermissionAuditLogDetail = (id: string) => {
    return request({
        url: `/permissions/audit-logs/${id}/`,
        method: 'get'
    })
}

export const getPermissionAuditLogStatistics = (params: any) => {
    return request({
        url: '/permissions/audit-logs/statistics/',
        method: 'get',
        params
    })
}
```

**Step 2: Commit**

```bash
git add frontend/src/api/permissions.ts
git commit -m "feat(api): add permissions management API client"
```

---

## Task 6: Create Integration Management API Client

**Files:**
- Create: `frontend/src/api/integration.ts`

**Step 1: Create integration.ts API file**

Create `frontend/src/api/integration.ts`:
```typescript
import request from '@/utils/request'

// Integration Configs
export const getIntegrationConfigList = (params: any) => {
    return request({
        url: '/integration/configs/',
        method: 'get',
        params
    })
}

export const getIntegrationConfigDetail = (id: string) => {
    return request({
        url: `/integration/configs/${id}/`,
        method: 'get'
    })
}

export const createIntegrationConfig = (data: any) => {
    return request({
        url: '/integration/configs/',
        method: 'post',
        data
    })
}

export const updateIntegrationConfig = (id: string, data: any) => {
    return request({
        url: `/integration/configs/${id}/`,
        method: 'put',
        data
    })
}

export const deleteIntegrationConfig = (id: string) => {
    return request({
        url: `/integration/configs/${id}/`,
        method: 'delete'
    })
}

export const testIntegrationConnection = (id: string) => {
    return request({
        url: `/integration/configs/${id}/test/`,
        method: 'post'
    })
}

export const syncIntegrationData = (id: string) => {
    return request({
        url: `/integration/configs/${id}/sync/`,
        method: 'post'
    })
}

// Sync Tasks
export const getSyncTaskList = (params: any) => {
    return request({
        url: '/integration/sync-tasks/',
        method: 'get',
        params
    })
}

export const getSyncTaskDetail = (id: string) => {
    return request({
        url: `/integration/sync-tasks/${id}/`,
        method: 'get'
    })
}

export const executeSyncTask = (id: string) => {
    return request({
        url: `/integration/sync-tasks/${id}/execute/`,
        method: 'post'
    })
}

export const cancelSyncTask = (id: string) => {
    return request({
        url: `/integration/sync-tasks/${id}/cancel/`,
        method: 'post'
    })
}

// Integration Logs
export const getIntegrationLogList = (params: any) => {
    return request({
        url: '/integration/logs/',
        method: 'get',
        params
    })
}

export const getIntegrationLogDetail = (id: string) => {
    return request({
        url: `/integration/logs/${id}/`,
        method: 'get'
    })
}

export const retryIntegrationLog = (id: string) => {
    return request({
        url: `/integration/logs/${id}/retry/`,
        method: 'post'
    })
}

// Data Mapping Templates
export const getDataMappingTemplateList = (params: any) => {
    return request({
        url: '/integration/mappings/',
        method: 'get',
        params
    })
}

export const getDataMappingTemplateDetail = (id: string) => {
    return request({
        url: `/integration/mappings/${id}/`,
        method: 'get'
    })
}

export const createDataMappingTemplate = (data: any) => {
    return request({
        url: '/integration/mappings/',
        method: 'post',
        data
    })
}

export const updateDataMappingTemplate = (id: string, data: any) => {
    return request({
        url: `/integration/mappings/${id}/`,
        method: 'put',
        data
    })
}

export const deleteDataMappingTemplate = (id: string) => {
    return request({
        url: `/integration/mappings/${id}/`,
        method: 'delete'
    })
}

export const testDataMapping = (id: string, data: any) => {
    return request({
        url: `/integration/mappings/${id}/test/`,
        method: 'post',
        data
    })
}
```

**Step 2: Commit**

```bash
git add frontend/src/api/integration.ts
git commit -m "feat(api): add integration management API client"
```

---

## Task 7: Create Notifications API Client

**Files:**
- Create: `frontend/src/api/notifications.ts`

**Step 1: Create notifications.ts API file**

Create `frontend/src/api/notifications.ts`:
```typescript
import request from '@/utils/request'

// Notifications (User's notifications)
export const getNotificationList = (params: any) => {
    return request({
        url: '/notifications/',
        method: 'get',
        params
    })
}

export const getNotificationDetail = (id: string) => {
    return request({
        url: `/notifications/${id}/`,
        method: 'get'
    })
}

export const markNotificationAsRead = (id: string) => {
    return request({
        url: `/notifications/${id}/read/`,
        method: 'post'
    })
}

export const markAllNotificationsAsRead = () => {
    return request({
        url: '/notifications/mark-all-read/',
        method: 'post'
    })
}

export const deleteNotification = (id: string) => {
    return request({
        url: `/notifications/${id}/`,
        method: 'delete'
    })
}

export const getUnreadCount = () => {
    return request({
        url: '/notifications/unread-count/',
        method: 'get'
    })
}

// Notification Templates
export const getNotificationTemplateList = (params: any) => {
    return request({
        url: '/notifications/templates/',
        method: 'get',
        params
    })
}

export const getNotificationTemplateDetail = (id: string) => {
    return request({
        url: `/notifications/templates/${id}/`,
        method: 'get'
    })
}

export const createNotificationTemplate = (data: any) => {
    return request({
        url: '/notifications/templates/',
        method: 'post',
        data
    })
}

export const updateNotificationTemplate = (id: string, data: any) => {
    return request({
        url: `/notifications/templates/${id}/`,
        method: 'put',
        data
    })
}

export const deleteNotificationTemplate = (id: string) => {
    return request({
        url: `/notifications/templates/${id}/`,
        method: 'delete'
    })
}

export const previewNotificationTemplate = (id: string, data: any) => {
    return request({
        url: `/notifications/templates/${id}/preview/`,
        method: 'post',
        data
    })
}

// Notification Configs
export const getNotificationConfigList = (params: any) => {
    return request({
        url: '/notifications/configs/',
        method: 'get',
        params
    })
}

export const getNotificationConfigDetail = (id: string) => {
    return request({
        url: `/notifications/configs/${id}/`,
        method: 'get'
    })
}

export const updateNotificationConfig = (id: string, data: any) => {
    return request({
        url: `/notifications/configs/${id}/`,
        method: 'put',
        data
    })
}

// Notification Channels
export const getNotificationChannelList = (params: any) => {
    return request({
        url: '/notifications/channels/',
        method: 'get',
        params
    })
}

export const getNotificationChannelDetail = (id: string) => {
    return request({
        url: `/notifications/channels/${id}/`,
        method: 'get'
    })
}

export const createNotificationChannel = (data: any) => {
    return request({
        url: '/notifications/channels/',
        method: 'post',
        data
    })
}

export const updateNotificationChannel = (id: string, data: any) => {
    return request({
        url: `/notifications/channels/${id}/`,
        method: 'put',
        data
    })
}

export const deleteNotificationChannel = (id: string) => {
    return request({
        url: `/notifications/channels/${id}/`,
        method: 'delete'
    })
}

export const testNotificationChannel = (id: string) => {
    return request({
        url: `/notifications/channels/${id}/test/`,
        method: 'post'
    })
}

// Notification Logs
export const getNotificationLogList = (params: any) => {
    return request({
        url: '/notifications/logs/',
        method: 'get',
        params
    })
}

export const getNotificationLogDetail = (id: string) => {
    return request({
        url: `/notifications/logs/${id}/`,
        method: 'get'
    })
}

export const resendNotification = (logId: string) => {
    return request({
        url: `/notifications/logs/${logId}/resend/`,
        method: 'post'
    })
}

// In-App Messages
export const getInAppMessageList = (params: any) => {
    return request({
        url: '/notifications/inapp/',
        method: 'get',
        params
    })
}

export const getInAppMessageDetail = (id: string) => {
    return request({
        url: `/notifications/inapp/${id}/`,
        method: 'get'
    })
}

export const createInAppMessage = (data: any) => {
    return request({
        url: '/notifications/inapp/',
        method: 'post',
        data
    })
}

export const updateInAppMessage = (id: string, data: any) => {
    return request({
        url: `/notifications/inapp/${id}/`,
        method: 'put',
        data
    })
}

export const deleteInAppMessage = (id: string) => {
    return request({
        url: `/notifications/inapp/${id}/`,
        method: 'delete'
    })
}
```

**Step 2: Commit**

```bash
git add frontend/src/api/notifications.ts
git commit -m "feat(api): add notifications API client"
```

---

## Task 8: Create Leasing Management API Client

**Files:**
- Create: `frontend/src/api/leasing.ts`

**Step 1: Create leasing.ts API file**

Create `frontend/src/api/leasing.ts`:
```typescript
import request from '@/utils/request'

// Lease Contracts
export const getLeaseContractList = (params: any) => {
    return request({
        url: '/leasing/lease-contracts/',
        method: 'get',
        params
    })
}

export const getLeaseContractDetail = (id: string) => {
    return request({
        url: `/leasing/lease-contracts/${id}/`,
        method: 'get'
    })
}

export const createLeaseContract = (data: any) => {
    return request({
        url: '/leasing/lease-contracts/',
        method: 'post',
        data
    })
}

export const updateLeaseContract = (id: string, data: any) => {
    return request({
        url: `/leasing/lease-contracts/${id}/`,
        method: 'put',
        data
    })
}

export const deleteLeaseContract = (id: string) => {
    return request({
        url: `/leasing/lease-contracts/${id}/`,
        method: 'delete'
    })
}

export const activateLeaseContract = (id: string) => {
    return request({
        url: `/leasing/lease-contracts/${id}/activate/`,
        method: 'post'
    })
}

export const terminateLeaseContract = (id: string, data: any) => {
    return request({
        url: `/leasing/lease-contracts/${id}/terminate/`,
        method: 'post',
        data
    })
}

// Lease Items
export const getLeaseItemList = (params: any) => {
    return request({
        url: '/leasing/lease-items/',
        method: 'get',
        params
    })
}

export const getLeaseItemDetail = (id: string) => {
    return request({
        url: `/leasing/lease-items/${id}/`,
        method: 'get'
    })
}

export const createLeaseItem = (data: any) => {
    return request({
        url: '/leasing/lease-items/',
        method: 'post',
        data
    })
}

export const updateLeaseItem = (id: string, data: any) => {
    return request({
        url: `/leasing/lease-items/${id}/`,
        method: 'put',
        data
    })
}

export const deleteLeaseItem = (id: string) => {
    return request({
        url: `/leasing/lease-items/${id}/`,
        method: 'delete'
    })
}

// Rent Payments
export const getRentPaymentList = (params: any) => {
    return request({
        url: '/leasing/rent-payments/',
        method: 'get',
        params
    })
}

export const getRentPaymentDetail = (id: string) => {
    return request({
        url: `/leasing/rent-payments/${id}/`,
        method: 'get'
    })
}

export const createRentPayment = (data: any) => {
    return request({
        url: '/leasing/rent-payments/',
        method: 'post',
        data
    })
}

export const confirmRentPayment = (id: string, data: any) => {
    return request({
        url: `/leasing/rent-payments/${id}/confirm/`,
        method: 'post',
        data
    })
}

// Lease Returns
export const getLeaseReturnList = (params: any) => {
    return request({
        url: '/leasing/lease-returns/',
        method: 'get',
        params
    })
}

export const getLeaseReturnDetail = (id: string) => {
    return request({
        url: `/leasing/lease-returns/${id}/`,
        method: 'get'
    })
}

export const createLeaseReturn = (data: any) => {
    return request({
        url: '/leasing/lease-returns/',
        method: 'post',
        data
    })
}

export const confirmLeaseReturn = (id: string, data: any) => {
    return request({
        url: `/leasing/lease-returns/${id}/confirm/`,
        method: 'post',
        data
    })
}

// Lease Extensions
export const getLeaseExtensionList = (params: any) => {
    return request({
        url: '/leasing/lease-extensions/',
        method: 'get',
        params
    })
}

export const getLeaseExtensionDetail = (id: string) => {
    return request({
        url: `/leasing/lease-extensions/${id}/`,
        method: 'get'
    })
}

export const createLeaseExtension = (data: any) => {
    return request({
        url: '/leasing/lease-extensions/',
        method: 'post',
        data
    })
}

export const approveLeaseExtension = (id: string) => {
    return request({
        url: `/leasing/lease-extensions/${id}/approve/`,
        method: 'post'
    })
}
```

**Step 2: Commit**

```bash
git add frontend/src/api/leasing.ts
git commit -m "feat(api): add leasing management API client"
```

---

## Task 9: Create Insurance Management API Client

**Files:**
- Create: `frontend/src/api/insurance.ts`

**Step 1: Create insurance.ts API file**

Create `frontend/src/api/insurance.ts`:
```typescript
import request from '@/utils/request'

// Insurance Companies
export const getInsuranceCompanyList = (params: any) => {
    return request({
        url: '/insurance/companies/',
        method: 'get',
        params
    })
}

export const getInsuranceCompanyDetail = (id: string) => {
    return request({
        url: `/insurance/companies/${id}/`,
        method: 'get'
    })
}

export const createInsuranceCompany = (data: any) => {
    return request({
        url: '/insurance/companies/',
        method: 'post',
        data
    })
}

export const updateInsuranceCompany = (id: string, data: any) => {
    return request({
        url: `/insurance/companies/${id}/`,
        method: 'put',
        data
    })
}

export const deleteInsuranceCompany = (id: string) => {
    return request({
        url: `/insurance/companies/${id}/`,
        method: 'delete'
    })
}

// Insurance Policies
export const getInsurancePolicyList = (params: any) => {
    return request({
        url: '/insurance/policies/',
        method: 'get',
        params
    })
}

export const getInsurancePolicyDetail = (id: string) => {
    return request({
        url: `/insurance/policies/${id}/`,
        method: 'get'
    })
}

export const createInsurancePolicy = (data: any) => {
    return request({
        url: '/insurance/policies/',
        method: 'post',
        data
    })
}

export const updateInsurancePolicy = (id: string, data: any) => {
    return request({
        url: `/insurance/policies/${id}/`,
        method: 'put',
        data
    })
}

export const deleteInsurancePolicy = (id: string) => {
    return request({
        url: `/insurance/policies/${id}/`,
        method: 'delete'
    })
}

// Insured Assets
export const getInsuredAssetList = (params: any) => {
    return request({
        url: '/insurance/insured-assets/',
        method: 'get',
        params
    })
}

export const getInsuredAssetDetail = (id: string) => {
    return request({
        url: `/insurance/insured-assets/${id}/`,
        method: 'get'
    })
}

export const createInsuredAsset = (data: any) => {
    return request({
        url: '/insurance/insured-assets/',
        method: 'post',
        data
    })
}

export const updateInsuredAsset = (id: string, data: any) => {
    return request({
        url: `/insurance/insured-assets/${id}/`,
        method: 'put',
        data
    })
}

export const deleteInsuredAsset = (id: string) => {
    return request({
        url: `/insurance/insured-assets/${id}/`,
        method: 'delete'
    })
}

// Premium Payments
export const getPremiumPaymentList = (params: any) => {
    return request({
        url: '/insurance/payments/',
        method: 'get',
        params
    })
}

export const getPremiumPaymentDetail = (id: string) => {
    return request({
        url: `/insurance/payments/${id}/`,
        method: 'get'
    })
}

export const createPremiumPayment = (data: any) => {
    return request({
        url: '/insurance/payments/',
        method: 'post',
        data
    })
}

export const confirmPremiumPayment = (id: string, data: any) => {
    return request({
        url: `/insurance/payments/${id}/confirm/`,
        method: 'post',
        data
    })
}

// Claim Records
export const getClaimRecordList = (params: any) => {
    return request({
        url: '/insurance/claims/',
        method: 'get',
        params
    })
}

export const getClaimRecordDetail = (id: string) => {
    return request({
        url: `/insurance/claims/${id}/`,
        method: 'get'
    })
}

export const createClaimRecord = (data: any) => {
    return request({
        url: '/insurance/claims/',
        method: 'post',
        data
    })
}

export const updateClaimRecord = (id: string, data: any) => {
    return request({
        url: `/insurance/claims/${id}/`,
        method: 'put',
        data
    })
}

export const submitClaimRecord = (id: string) => {
    return request({
        url: `/insurance/claims/${id}/submit/`,
        method: 'post'
    })
}

export const approveClaimRecord = (id: string, data: any) => {
    return request({
        url: `/insurance/claims/${id}/approve/`,
        method: 'post',
        data
    })
}

// Policy Renewals
export const getPolicyRenewalList = (params: any) => {
    return request({
        url: '/insurance/renewals/',
        method: 'get',
        params
    })
}

export const getPolicyRenewalDetail = (id: string) => {
    return request({
        url: `/insurance/renewals/${id}/`,
        method: 'get'
    })
}

export const createPolicyRenewal = (data: any) => {
    return request({
        url: '/insurance/renewals/',
        method: 'post',
        data
    })
}

export const processPolicyRenewal = (id: string, data: any) => {
    return request({
        url: `/insurance/renewals/${id}/process/`,
        method: 'post',
        data
    })
}
```

**Step 2: Commit**

```bash
git add frontend/src/api/insurance.ts
git commit -m "feat(api): add insurance management API client"
```

---

## Task 10: Create SSO Management API Client

**Files:**
- Create: `frontend/src/api/sso.ts`

**Step 1: Create sso.ts API file**

Create `frontend/src/api/sso.ts`:
```typescript
import request from '@/utils/request'

// WeWork Configs
export const getWeWorkConfigList = (params: any) => {
    return request({
        url: '/sso/configs/',
        method: 'get',
        params
    })
}

export const getWeWorkConfigDetail = (id: string) => {
    return request({
        url: `/sso/configs/${id}/`,
        method: 'get'
    })
}

export const createWeWorkConfig = (data: any) => {
    return request({
        url: '/sso/configs/',
        method: 'post',
        data
    })
}

export const updateWeWorkConfig = (id: string, data: any) => {
    return request({
        url: `/sso/configs/${id}/`,
        method: 'put',
        data
    })
}

export const deleteWeWorkConfig = (id: string) => {
    return request({
        url: `/sso/configs/${id}/`,
        method: 'delete'
    })
}

export const testWeWorkConnection = (id: string) => {
    return request({
        url: `/sso/configs/${id}/test/`,
        method: 'post'
    })
}

// User Mappings
export const getUserMappingList = (params: any) => {
    return request({
        url: '/sso/mappings/',
        method: 'get',
        params
    })
}

export const getUserMappingDetail = (id: string) => {
    return request({
        url: `/sso/mappings/${id}/`,
        method: 'get'
    })
}

export const createUserMapping = (data: any) => {
    return request({
        url: '/sso/mappings/',
        method: 'post',
        data
    })
}

export const updateUserMapping = (id: string, data: any) => {
    return request({
        url: `/sso/mappings/${id}/`,
        method: 'put',
        data
    })
}

export const deleteUserMapping = (id: string) => {
    return request({
        url: `/sso/mappings/${id}/`,
        method: 'delete'
    })
}

export const syncUserMapping = (id: string) => {
    return request({
        url: `/sso/mappings/${id}/sync/`,
        method: 'post'
    })
}

// Sync Tasks
export const getSyncTaskList = (params: any) => {
    return request({
        url: '/sso/sync/',
        method: 'get',
        params
    })
}

export const getSyncTaskDetail = (id: string) => {
    return request({
        url: `/sso/sync/${id}/`,
        method: 'get'
    })
}

export const executeSyncTask = (platform: string) => {
    return request({
        url: `/sso/sync/${platform}/execute/`,
        method: 'post'
    })
}

export const getSyncLogList = (params: any) => {
    return request({
        url: '/sso/sync/logs/',
        method: 'get',
        params
    })
}
```

**Step 2: Commit**

```bash
git add frontend/src/api/sso.ts
git commit -m "feat(api): add SSO management API client"
```

---

## Task 11: Create Mobile Enhancement API Client

**Files:**
- Create: `frontend/src/api/mobile.ts`

**Step 1: Create mobile.ts API file**

Create `frontend/src/api/mobile.ts`:
```typescript
import request from '@/utils/request'

// Mobile Devices
export const getMobileDeviceList = (params: any) => {
    return request({
        url: '/mobile/devices/',
        method: 'get',
        params
    })
}

export const getMobileDeviceDetail = (id: string) => {
    return request({
        url: `/mobile/devices/${id}/`,
        method: 'get'
    })
}

export const registerMobileDevice = (data: any) => {
    return request({
        url: '/mobile/devices/register/',
        method: 'post',
        data
    })
}

export const updateMobileDevice = (id: string, data: any) => {
    return request({
        url: `/mobile/devices/${id}/`,
        method: 'put',
        data
    })
}

export const unbindMobileDevice = (id: string) => {
    return request({
        url: `/mobile/devices/${id}/unbind/`,
        method: 'post'
    })
}

export const getMyDevices = () => {
    return request({
        url: '/mobile/devices/my_devices/',
        method: 'get'
    })
}

// Security Logs
export const getSecurityLogList = (params: any) => {
    return request({
        url: '/mobile/security-logs/',
        method: 'get',
        params
    })
}

export const getSecurityLogDetail = (id: string) => {
    return request({
        url: `/mobile/security-logs/${id}/`,
        method: 'get'
    })
}

// Data Sync
export const getSyncDataList = (params: any) => {
    return request({
        url: '/mobile/sync/',
        method: 'get',
        params
    })
}

export const uploadOfflineData = (data: any) => {
    return request({
        url: '/mobile/sync/upload/',
        method: 'post',
        data
    })
}

export const downloadServerChanges = (params: any) => {
    return request({
        url: '/mobile/sync/download/',
        method: 'post',
        params
    })
}

export const resolveSyncConflict = (id: string, data: any) => {
    return request({
        url: '/mobile/sync/resolve_conflict/',
        method: 'post',
        data: { conflict_id: id, ...data }
    })
}

export const getPendingSyncCount = () => {
    return request({
        url: '/mobile/sync/pending_count/',
        method: 'get'
    })
}

export const syncAll = () => {
    return request({
        url: '/mobile/sync/sync_all/',
        method: 'post'
    })
}

// Sync Conflicts
export const getConflictList = (params: any) => {
    return request({
        url: '/mobile/conflicts/',
        method: 'get',
        params
    })
}

export const getPendingConflicts = () => {
    return request({
        url: '/mobile/conflicts/pending/',
        method: 'get'
    })
}

export const resolveConflict = (id: string, data: any) => {
    return request({
        url: `/mobile/conflicts/${id}/resolve/`,
        method: 'post',
        data
    })
}

// Sync Logs
export const getSyncLogList = (params: any) => {
    return request({
        url: '/mobile/sync-logs/',
        method: 'get',
        params
    })
}

export const getSyncLogDetail = (id: string) => {
    return request({
        url: `/mobile/sync-logs/${id}/`,
        method: 'get'
    })
}

// Mobile Approvals
export const getPendingApprovals = () => {
    return request({
        url: '/mobile/approvals/pending/',
        method: 'get'
    })
}

export const executeMobileApproval = (data: any) => {
    return request({
        url: '/mobile/approvals/approve/',
        method: 'post',
        data
    })
}

export const batchApprove = (data: any) => {
    return request({
        url: '/mobile/approvals/batch_approve/',
        method: 'post',
        data
    })
}

// Approval Delegates
export const getDelegateList = (params: any) => {
    return request({
        url: '/mobile/delegates/',
        method: 'get',
        params
    })
}

export const getActiveDelegates = () => {
    return request({
        url: '/mobile/delegates/active/',
        method: 'get'
    })
}

export const getMyDelegations = () => {
    return request({
        url: '/mobile/approvals/my_delegations/',
        method: 'get'
    })
}

export const activateDelegate = (id: string) => {
    return request({
        url: `/mobile/delegates/${id}/activate/`,
        method: 'post'
    })
}

export const deactivateDelegate = (id: string) => {
    return request({
        url: `/mobile/delegates/${id}/deactivate/`,
        method: 'post'
    })
}
```

**Step 2: Commit**

```bash
git add frontend/src/api/mobile.ts
git commit -m "feat(api): add mobile enhancement API client"
```

---

## Summary

After completing all tasks, the following will be implemented:

### New API Clients (9 files)
- `frontend/src/api/assets/return.ts` - Asset return operations
- `frontend/src/api/lifecycle.ts` - Purchase, receipt, maintenance, disposal
- `frontend/src/api/permissions.ts` - Field/data permissions, audit logs
- `frontend/src/api/integration.ts` - ERP/integration management
- `frontend/src/api/notifications.ts` - Templates, configs, channels, logs
- `frontend/src/api/leasing.ts` - Lease contracts, items, payments
- `frontend/src/api/insurance.ts` - Policies, claims, renewals
- `frontend/src/api/sso.ts` - SSO config, user mapping, sync
- `frontend/src/api/mobile.ts` - Devices, sync, approvals, delegates

### Completed Pages (2)
- `frontend/src/views/workflow/TaskDetail.vue` - Real task approval
- `frontend/src/views/system/DepartmentList.vue` - Full CRUD

### New Components (1)
- `frontend/src/views/system/components/DepartmentForm.vue` - Department form dialog

### Modified API Files (2)
- `frontend/src/api/workflow.ts` - Added task detail, approve, reject
- `frontend/src/api/system.ts` - Added department CRUD operations

---

## Implementation Notes

1. **Field Naming Convention**: All API responses use camelCase (transformed by axios interceptor)
2. **Base URL**: Configured as `/api` in `request.ts`, all API paths exclude `/api` prefix
3. **Common Components**: Use `BaseListPage`, `BaseDetailPage`, `BaseFormPage` where applicable
4. **DynamicForm**: For metadata-driven forms, use existing `DynamicForm` component
5. **Error Handling**: Use `ElMessage` for user feedback
6. **Loading States**: Always show loading indicators during API calls

---

## Testing Checklist

After implementation:
- [ ] All API clients can be imported without errors
- [ ] TaskDetail loads real data and approves/rejects correctly
- [ ] DepartmentList can create, edit, delete departments
- [ ] All new API clients follow the same pattern as existing ones
- [ ] Router includes routes for new pages when implemented
