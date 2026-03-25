# Phase 1.5: 资产领用/调拨/退库业务 - 前端实现

## 组件结构

```
src/views/assets/
├── operations/
│   ├── PickupList.vue          # 领用单列表
│   ├── PickupForm.vue          # 领用单表单
│   ├── TransferList.vue        # 调拨单列表
│   ├── TransferForm.vue        # 调拨单表单
│   ├── ReturnList.vue          # 退库单列表
│   ├── ReturnForm.vue          # 退库单表单
│   ├── LoanList.vue            # 借用单列表
│   ├── LoanForm.vue            # 借用单表单
│   └── components/
│       ├── AssetSelector.vue   # 资产选择器
│       ├── StatusTimeline.vue  # 状态流转时间线
│       └── ApprovalHistory.vue # 审批历史
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

## 1. 领用单组件

### PickupList.vue - 领用单列表

```vue
<template>
  <div class="pickup-list">
    <!-- 页面头部 -->
    <el-page-header @back="goBack" title="资产领用">
      <template #content>
        <span class="text-large font-600">资产领用单</span>
      </template>
      <template #extra>
        <el-button type="primary" :icon="Plus" @click="handleCreate">
          新建领用单
        </el-button>
      </template>
    </el-page-header>

    <!-- 筛选条件 -->
    <el-card class="filter-card" shadow="never">
      <el-form :model="filterForm" inline>
        <el-form-item label="状态">
          <el-select v-model="filterForm.status" clearable placeholder="全部状态" @change="handleSearch">
            <el-option label="草稿" value="draft" />
            <el-option label="待审批" value="pending" />
            <el-option label="已批准" value="approved" />
            <el-option label="已拒绝" value="rejected" />
            <el-option label="已完成" value="completed" />
          </el-select>
        </el-form-item>
        <el-form-item label="搜索">
          <el-input
            v-model="filterForm.search"
            placeholder="领用单号/申请人"
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
        <el-table-column prop="pickup_no" label="领用单号" width="150" />
        <el-table-column prop="applicant.real_name" label="申请人" width="100" />
        <el-table-column prop="department.name" label="领用部门" width="120" />
        <el-table-column prop="pickup_date" label="领用日期" width="110" />
        <el-table-column label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="getStatusType(row.status)">
              {{ getStatusLabel(row.status) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="items_count" label="资产数量" width="80" align="center" />
        <el-table-column prop="created_at" label="创建时间" width="160" />
        <el-table-column label="操作" width="200" fixed="right">
          <template #default="{ row }">
            <el-button link type="primary" @click.stop="handleView(row)">查看</el-button>
            <el-button
              v-if="row.status === 'draft' || row.status === 'pending'"
              link
              type="primary"
              @click.stop="handleEdit(row)"
            >
              编辑
            </el-button>
            <el-button
              v-if="row.status === 'draft' || row.status === 'pending'"
              link
              type="warning"
              @click.stop="handleCancel(row)"
            >
              取消
            </el-button>
            <el-button
              v-if="row.status === 'pending' && canApprove(row)"
              link
              type="success"
              @click.stop="handleApprove(row)"
            >
              审批
            </el-button>
            <el-button
              v-if="row.status === 'approved' && canComplete(row)"
              link
              type="primary"
              @click.stop="handleComplete(row)"
            >
              完成
            </el-button>
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

    <!-- 审批弹窗 -->
    <ApprovalDialog
      v-model="approvalVisible"
      :data="currentRow"
      type="pickup"
      @confirm="handleApprovalConfirm"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, computed } from 'vue'
import { useRouter } from 'vue-router'
import { Plus, Search } from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { getPickupList, cancelPickup, completePickup } from '@/api/assets/pickup'
import { useUserStore } from '@/stores/user'
import ApprovalDialog from './components/ApprovalDialog.vue'

const router = useRouter()
const userStore = useUserStore()

interface PickupItem {
  id: number
  pickup_no: string
  applicant: { id: number; real_name: string }
  department: { id: number; name: string }
  pickup_date: string
  status: string
  items_count: number
  created_at: string
}

const loading = ref(false)
const tableData = ref<PickupItem[]>([])
const approvalVisible = ref(false)
const currentRow = ref<PickupItem | null>(null)

const filterForm = reactive({
  status: '',
  search: ''
})

const pagination = reactive({
  page: 1,
  page_size: 20,
  total: 0
})

const canApprove = computed(() => (row: PickupItem) => {
  // 检查当前用户是否是审批人
  return userStore.hasPermission('assets:approve_pickup')
})

const canComplete = computed(() => (row: PickupItem) => {
  // 只有资产管理员可以完成
  return userStore.hasPermission('assets:complete_pickup')
})

const getStatusType = (status: string) => {
  const types: Record<string, string> = {
    draft: 'info',
    pending: 'warning',
    approved: 'success',
    rejected: 'danger',
    completed: '',
    cancelled: 'info'
  }
  return types[status] || 'info'
}

const getStatusLabel = (status: string) => {
  const labels: Record<string, string> = {
    draft: '草稿',
    pending: '待审批',
    approved: '已批准',
    rejected: '已拒绝',
    completed: '已完成',
    cancelled: '已取消'
  }
  return labels[status] || status
}

const fetchData = async () => {
  loading.value = true
  try {
    const res = await getPickupList({
      ...filterForm,
      ...pagination
    })
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

const handleCreate = () => {
  router.push('/assets/operations/pickup/create')
}

const handleView = (row: PickupItem) => {
  router.push(`/assets/operations/pickup/${row.id}`)
}

const handleEdit = (row: PickupItem) => {
  router.push(`/assets/operations/pickup/${row.id}/edit`)
}

const handleRowClick = (row: PickupItem) => {
  handleView(row)
}

const handleCancel = async (row: PickupItem) => {
  try {
    await ElMessageBox.confirm('确定要取消此领用单吗？', '确认操作', {
      type: 'warning'
    })
    await cancelPickup(row.id)
    ElMessage.success('已取消领用单')
    fetchData()
  } catch {
    // 用户取消
  }
}

const handleApprove = (row: PickupItem) => {
  currentRow.value = row
  approvalVisible.value = true
}

const handleApprovalConfirm = async (data: { approval: string; comment: string }) => {
  // 审批逻辑在 ApprovalDialog 中处理
  approvalVisible.value = false
  fetchData()
}

const handleComplete = async (row: PickupItem) => {
  try {
    await ElMessageBox.confirm('确认完成此领用单？资产将正式发放', '确认操作', {
      type: 'warning'
    })
    await completePickup(row.id)
    ElMessage.success('领用单已完成')
    fetchData()
  } catch {
    // 用户取消
  }
}

const goBack = () => {
  router.back()
}

onMounted(() => {
  fetchData()
})
</script>

<style scoped>
.pickup-list {
  padding: 20px;
}

.filter-card {
  margin: 20px 0;
}
</style>
```

### PickupForm.vue - 领用单表单

```vue
<template>
  <div class="pickup-form">
    <el-page-header @back="goBack" title="返回">
      <template #content>
        <span class="text-large font-600">
          {{ isEdit ? '编辑领用单' : '新建领用单' }}
        </span>
      </template>
      <template #extra>
        <el-button
          v-if="!isEdit && form.pickup_no"
          type="success"
          @click="handleSubmit"
        >
          提交审批
        </el-button>
        <el-button
          v-if="isEdit && form.status === 'draft'"
          type="primary"
          @click="handleUpdate"
        >
          保存
        </el-button>
        <el-button
          v-if="isEdit && form.status === 'draft'"
          type="success"
          @click="handleUpdateAndSubmit"
        >
          保存并提交
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
            <el-form-item label="领用单号">
              <el-input v-model="form.pickup_no" disabled />
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="申请人">
              <el-input :value="userStore.realName" disabled />
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="申请日期">
              <el-date-picker
                v-model="form.pickup_date"
                type="date"
                value-format="YYYY-MM-DD"
                :disabled="!canEdit"
              />
            </el-form-item>
          </el-col>
        </el-row>

        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="领用部门" prop="department">
              <DepartmentTree
                v-model="form.department"
                :disabled="!canEdit"
                placeholder="请选择领用部门"
              />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="预计归还日期">
              <el-date-picker
                v-model="form.expected_return_date"
                type="date"
                value-format="YYYY-MM-DD"
                placeholder="长期使用可不填"
                :disabled="!canEdit"
              />
            </el-form-item>
          </el-col>
        </el-row>

        <el-form-item label="领用原因" prop="pickup_reason">
          <el-input
            v-model="form.pickup_reason"
            type="textarea"
            :rows="3"
            placeholder="请填写领用原因"
            :disabled="!canEdit"
          />
        </el-form-item>
      </el-card>

      <!-- 领用明细 -->
      <el-card header="领用明细" shadow="never" class="mt-4">
        <div v-if="canEdit" class="mb-3">
          <el-button type="primary" :icon="Plus" @click="showAssetSelector">
            添加资产
          </el-button>
          <el-tag type="info" class="ml-2">
            已选择 {{ form.items.length }} 项资产
          </el-tag>
        </div>

        <el-table :data="form.items" border>
          <el-table-column prop="asset.asset_code" label="资产编码" width="140" />
          <el-table-column prop="asset.asset_name" label="资产名称" width="180" />
          <el-table-column prop="asset.specification" label="规格型号" />
          <el-table-column label="状态" width="100">
            <template #default="{ row }">
              <el-tag :type="row.asset.asset_status === 'idle' ? 'success' : 'info'">
                {{ getStatusLabel(row.asset.asset_status) }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column v-if="canEdit" label="操作" width="80" fixed="right">
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

        <el-empty v-if="form.items.length === 0" description="请添加领用资产" />
      </el-card>

      <!-- 审批流程（只读） -->
      <ApprovalFlow
        v-if="isEdit && form.status !== 'draft'"
        :status="form.status"
        :approvals="form.approvals"
        class="mt-4"
      />
    </el-form>

    <!-- 资产选择弹窗 -->
    <AssetSelector
      v-model="assetSelectorVisible"
      :exclude-asset-ids="selectedAssetIds"
      :status-filter="['idle', 'pending']"
      @confirm="handleAssetSelect"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { Plus, Delete } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import { createPickup, updatePickup, getPickupDetail, submitPickup } from '@/api/assets/pickup'
import { useUserStore } from '@/stores/user'
import DepartmentTree from '@/components/DepartmentTree.vue'
import AssetSelector from './components/AssetSelector.vue'
import ApprovalFlow from './components/ApprovalFlow.vue'

const router = useRouter()
const route = useRoute()
const userStore = useUserStore()

interface Asset {
  id: number
  asset_code: string
  asset_name: string
  specification: string
  asset_status: string
}

interface PickupItem {
  asset: Asset
  quantity: number
  remark: string
}

const formRef = ref()
const assetSelectorVisible = ref(false)

const isEdit = computed(() => !!route.params.id)
const canEdit = computed(() => {
  return !isEdit.value || form.value.status === 'draft'
})

const selectedAssetIds = computed(() => form.value.items.map(i => i.asset.id))

const form = ref({
  pickup_no: '',
  department: null,
  pickup_date: '',
  expected_return_date: '',
  pickup_reason: '',
  status: 'draft',
  items: [] as PickupItem[],
  approvals: []
})

const rules = {
  department: [{ required: true, message: '请选择领用部门', trigger: 'change' }],
  pickup_date: [{ required: true, message: '请选择领用日期', trigger: 'change' }],
  pickup_reason: [{ required: true, message: '请填写领用原因', trigger: 'blur' }]
}

const getStatusLabel = (status: string) => {
  const labels: Record<string, string> = {
    idle: '闲置',
    pending: '待入库',
    in_use: '在用'
  }
  return labels[status] || status
}

const showAssetSelector = () => {
  assetSelectorVisible.value = true
}

const handleAssetSelect = (assets: Asset[]) => {
  assets.forEach(asset => {
    if (!selectedAssetIds.value.includes(asset.id)) {
      form.value.items.push({
        asset,
        quantity: 1,
        remark: ''
      })
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
      department: form.value.department,
      pickup_date: form.value.pickup_date,
      pickup_reason: form.value.pickup_reason,
      items: form.value.items.map(i => ({
        asset_id: i.asset.id
      }))
    }
    const res = await createPickup(data)
    form.value.pickup_no = res.pickup_no
    form.value.status = 'draft'
    ElMessage.success('领用单创建成功，请提交审批')
  } catch (error) {
    ElMessage.error('创建失败')
  }
}

const handleUpdate = async () => {
  await formRef.value.validate()
  try {
    const id = Number(route.params.id)
    const data = {
      department: form.value.department,
      pickup_date: form.value.pickup_date,
      pickup_reason: form.value.pickup_reason,
      items: form.value.items.map(i => ({
        asset_id: i.asset.id
      }))
    }
    await updatePickup(id, data)
    ElMessage.success('保存成功')
  } catch (error) {
    ElMessage.error('保存失败')
  }
}

const handleUpdateAndSubmit = async () => {
  await handleUpdate()
  const id = Number(route.params.id)
  await submitPickup(id)
  ElMessage.success('已提交审批')
  goBack()
}

const loadDetail = async () => {
  const id = Number(route.params.id)
  const res = await getPickupDetail(id)
  form.value = {
    pickup_no: res.pickup_no,
    department: res.department?.id,
    pickup_date: res.pickup_date,
    expected_return_date: res.expected_return_date,
    pickup_reason: res.pickup_reason,
    status: res.status,
    items: res.items || [],
    approvals: res.approvals || []
  }
}

const goBack = () => {
  router.back()
}

onMounted(async () => {
  if (isEdit.value) {
    await loadDetail()
  } else {
    form.value.pickup_date = new Date().toISOString().split('T')[0]
    form.value.department = userStore.departmentId
  }
})
</script>

<style scoped>
.pickup-form {
  padding: 20px;
}

.form-content {
  margin-top: 20px;
}

.mt-4 {
  margin-top: 16px;
}

.mb-3 {
  margin-bottom: 12px;
}

.ml-2 {
  margin-left: 8px;
}
</style>
```

---

## 2. 调拨单组件

### TransferForm.vue - 调拨单表单

```vue
<template>
  <div class="transfer-form">
    <el-page-header @back="goBack" title="返回">
      <template #content>
        <span class="text-large font-600">
          {{ isEdit ? '编辑调拨单' : '新建调拨单' }}
        </span>
      </template>
    </el-page-header>

    <el-form
      ref="formRef"
      :model="form"
      :rules="rules"
      label-width="140px"
      class="form-content"
    >
      <!-- 基础信息 -->
      <el-card header="基础信息" shadow="never">
        <el-row :gutter="20">
          <el-col :span="8">
            <el-form-item label="调拨单号">
              <el-input v-model="form.transfer_no" disabled />
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="调拨日期" prop="transfer_date">
              <el-date-picker
                v-model="form.transfer_date"
                type="date"
                value-format="YYYY-MM-DD"
                :disabled="!canEdit"
              />
            </el-form-item>
          </el-col>
        </el-row>

        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="调出部门" prop="from_department">
              <DepartmentTree
                v-model="form.from_department"
                :disabled="!canEdit"
                placeholder="请选择调出部门"
              />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="调入部门" prop="to_department">
              <DepartmentTree
                v-model="form.to_department"
                :disabled="!canEdit"
                placeholder="请选择调入部门"
              />
            </el-form-item>
          </el-col>
        </el-row>

        <el-form-item label="调拨原因" prop="transfer_reason">
          <el-input
            v-model="form.transfer_reason"
            type="textarea"
            :rows="2"
            :disabled="!canEdit"
          />
        </el-form-item>
      </el-card>

      <!-- 调拨明细 -->
      <el-card header="调拨明细" shadow="never" class="mt-4">
        <div v-if="canEdit" class="mb-3">
          <el-button type="primary" :icon="Plus" @click="showAssetSelector">
            添加资产
          </el-button>
        </div>

        <el-table :data="form.items" border>
          <el-table-column prop="asset.asset_code" label="资产编码" width="130" />
          <el-table-column prop="asset.asset_name" label="资产名称" width="150" />
          <el-table-column label="原存放地点" width="150">
            <template #default="{ row }">
              {{ row.asset.location?.name || '-' }}
            </template>
          </el-table-column>
          <el-table-column label="目标存放地点" width="180">
            <template #default="{ row }" v-if="canEdit">
              <LocationTree v-model="row.to_location" />
            </template>
            <template #default="{ row }" v-else>
              {{ row.to_location_name || '-' }}
            </template>
          </el-table-column>
          <el-table-column prop="remark" label="备注" />
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

      <!-- 审批进度 -->
      <TransferApprovalProgress
        v-if="isEdit"
        :status="form.status"
        :from-approval="form.from_approved_by"
        :to-approval="form.to_approved_by"
        class="mt-4"
      />
    </el-form>

    <!-- 资产选择弹窗 -->
    <AssetSelector
      v-model="assetSelectorVisible"
      :department-id="form.from_department"
      :status-filter="['in_use', 'idle']"
      @confirm="handleAssetSelect"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted, watch } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { Plus, Delete } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import { createTransfer, updateTransfer, getTransferDetail } from '@/api/assets/transfer'
import DepartmentTree from '@/components/DepartmentTree.vue'
import LocationTree from '@/components/LocationTree.vue'
import AssetSelector from './components/AssetSelector.vue'
import TransferApprovalProgress from './components/TransferApprovalProgress.vue'

const router = useRouter()
const route = useRoute()

const formRef = ref()
const assetSelectorVisible = ref(false)

const isEdit = computed(() => !!route.params.id)
const canEdit = computed(() => {
  return !isEdit.value || form.value.status === 'draft'
})

const form = ref({
  transfer_no: '',
  from_department: null,
  to_department: null,
  transfer_date: '',
  transfer_reason: '',
  status: 'draft',
  items: []
})

const rules = {
  from_department: [{ required: true, message: '请选择调出部门', trigger: 'change' }],
  to_department: [
    { required: true, message: '请选择调入部门', trigger: 'change' },
    {
      validator: (rule: any, value: any, callback: any) => {
        if (value === form.value.from_department) {
          callback(new Error('调入部门不能与调出部门相同'))
        } else {
          callback()
        }
      },
      trigger: 'change'
    }
  ],
  transfer_date: [{ required: true, message: '请选择调拨日期', trigger: 'change' }]
}

// 监听调出部门变化，清空已选资产
watch(() => form.value.from_department, () => {
  if (canEdit.value) {
    form.value.items = []
  }
})

const showAssetSelector = () => {
  if (!form.value.from_department) {
    ElMessage.warning('请先选择调出部门')
    return
  }
  assetSelectorVisible.value = true
}

const handleAssetSelect = (assets: any[]) => {
  assets.forEach(asset => {
    if (!form.value.items.find((i: any) => i.asset.id === asset.id)) {
      form.value.items.push({
        asset,
        to_location: null,
        remark: ''
      })
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
      from_department: form.value.from_department,
      to_department: form.value.to_department,
      transfer_date: form.value.transfer_date,
      transfer_reason: form.value.transfer_reason,
      items: form.value.items.map((i: any) => ({
        asset_id: i.asset.id,
        to_location: i.to_location
      }))
    }
    const res = await createTransfer(data)
    form.value.transfer_no = res.transfer_no
    ElMessage.success('调拨单创建成功，请提交审批')
    router.push(`/assets/operations/transfer/${res.id}`)
  } catch (error) {
    ElMessage.error('创建失败')
  }
}

const goBack = () => {
  router.back()
}

onMounted(async () => {
  if (isEdit.value) {
    const res = await getTransferDetail(Number(route.params.id))
    form.value = {
      transfer_no: res.transfer_no,
      from_department: res.from_department?.id,
      to_department: res.to_department?.id,
      transfer_date: res.transfer_date,
      transfer_reason: res.transfer_reason,
      status: res.status,
      items: res.items || []
    }
  } else {
    form.value.transfer_date = new Date().toISOString().split('T')[0]
  }
})
</script>
```

---

## 3. 借用单组件

### LoanForm.vue - 借用单表单

```vue
<template>
  <div class="loan-form">
    <el-page-header @back="goBack" title="返回">
      <template #content>
        <span class="text-large font-600">新建资产借用单</span>
      </template>
    </el-page-header>

    <el-form
      ref="formRef"
      :model="form"
      :rules="rules"
      label-width="140px"
      class="form-content"
    >
      <el-card header="基础信息" shadow="never">
        <el-row :gutter="20">
          <el-col :span="8">
            <el-form-item label="借用人">
              <el-input :value="userStore.realName" disabled />
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="借出日期" prop="borrow_date">
              <el-date-picker
                v-model="form.borrow_date"
                type="date"
                value-format="YYYY-MM-DD"
              />
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="预计归还日期" prop="expected_return_date">
              <el-date-picker
                v-model="form.expected_return_date"
                type="date"
                value-format="YYYY-MM-DD"
                :disabled-date="disableDate"
              />
            </el-form-item>
          </el-col>
        </el-row>

        <el-form-item label="借用原因" prop="loan_reason">
          <el-input
            v-model="form.loan_reason"
            type="textarea"
            :rows="2"
            placeholder="请说明借用事由"
          />
        </el-form-item>

        <!-- 借用期限提示 -->
        <el-alert
          v-if="borrowDays > 0"
          :title="`借用期限：${borrowDays} 天`"
          :type="borrowDays > 30 ? 'warning' : 'info'"
          :closable="false"
          show-icon
          class="mb-3"
        >
          <template v-if="borrowDays > 30">
            <p>借用期限超过30天，需要部门负责人审批</p>
          </template>
        </el-alert>
      </el-card>

      <!-- 借用资产 -->
      <el-card header="借用资产" shadow="never">
        <el-button type="primary" :icon="Plus" @click="showAssetSelector">
          选择资产
        </el-button>

        <el-table :data="form.items" class="mt-3" border>
          <el-table-column prop="asset.asset_code" label="资产编码" width="140" />
          <el-table-column prop="asset.asset_name" label="资产名称" />
          <el-table-column label="操作" width="80">
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

      <!-- 提交按钮 -->
      <div class="form-actions">
        <el-button type="primary" @click="handleSubmit">提交审批</el-button>
        <el-button @click="goBack">取消</el-button>
      </div>
    </el-form>

    <AssetSelector
      v-model="assetSelectorVisible"
      :status-filter="['idle']"
      @confirm="handleAssetSelect"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import { Plus, Delete } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import { createLoan } from '@/api/assets/loan'
import { useUserStore } from '@/stores/user'
import AssetSelector from './components/AssetSelector.vue'

const router = useRouter()
const userStore = useUserStore()

const formRef = ref()
const assetSelectorVisible = ref(false)

const form = ref({
  borrow_date: new Date().toISOString().split('T')[0],
  expected_return_date: '',
  loan_reason: '',
  items: []
})

const borrowDays = computed(() => {
  if (!form.value.borrow_date || !form.value.expected_return_date) {
    return 0
  }
  const start = new Date(form.value.borrow_date)
  const end = new Date(form.value.expected_return_date)
  return Math.ceil((end.getTime() - start.getTime()) / (1000 * 60 * 60 * 24))
})

const disableDate = (time: Date) => {
  // 归还日期不能早于借出日期
  if (form.value.borrow_date) {
    const borrowDate = new Date(form.value.borrow_date)
    return time.getTime() <= borrowDate.getTime()
  }
  return false
}

const rules = {
  borrow_date: [{ required: true, message: '请选择借出日期', trigger: 'change' }],
  expected_return_date: [
    { required: true, message: '请选择预计归还日期', trigger: 'change' },
    {
      validator: (rule: any, value: any, callback: any) => {
        if (value && borrowDays.value > 90) {
          callback(new Error('借用期限不能超过90天'))
        } else {
          callback()
        }
      },
      trigger: 'change'
    }
  ],
  loan_reason: [{ required: true, message: '请填写借用原因', trigger: 'blur' }]
}

const showAssetSelector = () => {
  assetSelectorVisible.value = true
}

const handleAssetSelect = (assets: any[]) => {
  assets.forEach(asset => {
    if (!form.value.items.find((i: any) => i.asset.id === asset.id)) {
      form.value.items.push({
        asset,
        remark: ''
      })
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
      borrow_date: form.value.borrow_date,
      expected_return_date: form.value.expected_return_date,
      loan_reason: form.value.loan_reason,
      items: form.value.items.map((i: any) => ({
        asset_id: i.asset.id
      }))
    }
    await createLoan(data)
    ElMessage.success('借用单已提交，等待审批')
    router.push('/assets/operations/loan')
  } catch (error) {
    ElMessage.error('提交失败')
  }
}

const goBack = () => {
  router.back()
}
</script>

<style scoped>
.loan-form {
  padding: 20px;
}

.form-content {
  margin-top: 20px;
}

.form-actions {
  margin-top: 20px;
  text-align: center;
}

.mt-3 {
  margin-top: 12px;
}

.mb-3 {
  margin-bottom: 12px;
}
</style>
```

---

## 4. 通用组件

### AssetSelector.vue - 资产选择器

```vue
<template>
  <el-dialog
    v-model="visible"
    title="选择资产"
    width="900px"
    :close-on-click-modal="false"
  >
    <div class="asset-selector">
      <!-- 搜索条件 -->
      <el-form :model="searchForm" inline>
        <el-form-item label="搜索">
          <el-input
            v-model="searchForm.search"
            placeholder="资产编码/名称/序列号"
            clearable
            @keyup.enter="handleSearch"
          >
            <template #append>
              <el-button :icon="Search" @click="handleSearch" />
            </template>
          </el-input>
        </el-form-item>
        <el-form-item label="分类">
          <CategoryTree v-model="searchForm.category" />
        </el-form-item>
      </el-form>

      <!-- 资产表格 -->
      <el-table
        ref="tableRef"
        v-loading="loading"
        :data="tableData"
        @selection-change="handleSelectionChange"
        height="400"
      >
        <el-table-column type="selection" width="50" />
        <el-table-column prop="asset_code" label="资产编码" width="130" />
        <el-table-column prop="asset_name" label="资产名称" width="150" />
        <el-table-column prop="specification" label="规格型号" />
        <el-table-column label="状态" width="90">
          <template #default="{ row }">
            <el-tag size="small" :type="getStatusType(row.asset_status)">
              {{ getStatusLabel(row.asset_status) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="location.name" label="存放地点" />
      </el-table>

      <!-- 分页 -->
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
import { getAssetList } from '@/api/assets'
import CategoryTree from '@/components/CategoryTree.vue'

interface Props {
  modelValue: boolean
  excludeAssetIds?: number[]
  departmentId?: number | null
  statusFilter?: string[]
}

const props = withDefaults(defineProps<Props>(), {
  excludeAssetIds: () => [],
  statusFilter: () => []
})

const emit = defineEmits(['update:modelValue', 'confirm'])

const visible = computed({
  get: () => props.modelValue,
  set: (val) => emit('update:modelValue', val)
})

const loading = ref(false)
const tableRef = ref()
const tableData = ref([])
const selectedAssets = ref<any[]>([])

const searchForm = reactive({
  search: '',
  category: null
})

const pagination = reactive({
  page: 1,
  page_size: 20,
  total: 0
})

const getStatusType = (status: string) => {
  const types: Record<string, string> = {
    idle: 'success',
    in_use: 'warning',
    pending: 'info'
  }
  return types[status] || 'info'
}

const getStatusLabel = (status: string) => {
  const labels: Record<string, string> = {
    idle: '闲置',
    in_use: '在用',
    pending: '待入库'
  }
  return labels[status] || status
}

const fetchData = async () => {
  loading.value = true
  try {
    const params: any = {
      ...searchForm,
      ...pagination
    }

    // 状态过滤
    if (props.statusFilter.length > 0) {
      params.status = props.statusFilter
    }

    // 部门过滤
    if (props.departmentId) {
      params.department = props.departmentId
    }

    const res = await getAssetList(params)

    // 排除已选资产
    tableData.value = res.items.filter(
      (item: any) => !props.excludeAssetIds.includes(item.id)
    )

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
  selectedAssets.value = selection
}

const handleConfirm = () => {
  emit('confirm', selectedAssets.value)
  visible.value = false
}

watch(() => props.modelValue, (val) => {
  if (val) {
    fetchData()
  }
})
</script>

<style scoped>
.asset-selector {
  padding: 10px 0;
}
</style>
```

### ApprovalDialog.vue - 审批弹窗

```vue
<template>
  <el-dialog
    v-model="visible"
    :title="title"
    width="500px"
    :close-on-click-modal="false"
  >
    <el-form :model="form" label-width="100px">
      <el-form-item label="审批结果">
        <el-radio-group v-model="form.approval">
          <el-radio label="approved">同意</el-radio>
          <el-radio label="rejected">拒绝</el-radio>
        </el-radio-group>
      </el-form-item>

      <el-form-item label="审批意见">
        <el-input
          v-model="form.comment"
          type="textarea"
          :rows="4"
          placeholder="请填写审批意见"
        />
      </el-form-item>
    </el-form>

    <template #footer>
      <el-button @click="visible = false">取消</el-button>
      <el-button type="primary" @click="handleConfirm">确定</el-button>
    </template>
  </el-dialog>
</template>

<script setup lang="ts">
import { ref, reactive, computed } from 'vue'
import { ElMessage } from 'element-plus'
import { approvePickup } from '@/api/assets/pickup'
import { approveTransfer } from '@/api/assets/transfer'

interface Props {
  modelValue: boolean
  data: any
  type: 'pickup' | 'transfer' | 'loan'
}

const props = defineProps<Props>()

const emit = defineEmits(['update:modelValue', 'confirm'])

const visible = computed({
  get: () => props.modelValue,
  set: (val) => emit('update:modelValue', val)
})

const title = computed(() => {
  const typeLabels: Record<string, string> = {
    pickup: '审批领用单',
    transfer: '审批调拨单',
    loan: '审批借用单'
  }
  return typeLabels[props.type] || '审批'
})

const form = reactive({
  approval: 'approved',
  comment: ''
})

const handleConfirm = async () => {
  try {
    if (props.type === 'pickup') {
      await approvePickup(props.data.id, form.approval, form.comment)
    } else if (props.type === 'transfer') {
      // 调拨审批需要判断是调出方还是调入方
      await approveTransfer(props.data.id, form.approval, form.comment)
    }
    ElMessage.success('审批成功')
    emit('confirm')
  } catch (error) {
    ElMessage.error('审批失败')
  }
}
</script>
```

### ApprovalFlow.vue - 审批流程展示

```vue
<template>
  <el-card header="审批流程" shadow="never">
    <el-steps :active="activeStep" align-center finish-status="success">
      <el-step title="提交申请" :description="formatTime(form.created_at)" />
      <el-step
        v-if="form.approved_at"
        title="已审批"
        :description="`${form.approved_by?.real_name} ${formatTime(form.approved_at)}`"
      />
      <el-step
        v-if="form.completed_at"
        title="已完成"
        :description="formatTime(form.completed_at)"
      />
    </el-steps>

    <!-- 审批意见列表 -->
    <div v-if="approvals.length > 0" class="approval-list mt-4">
      <h4>审批记录</h4>
      <el-timeline>
        <el-timeline-item
          v-for="item in approvals"
          :key="item.id"
          :timestamp="formatTime(item.approved_at)"
          placement="top"
        >
          <el-card>
            <p>
              <strong>{{ item.approver?.real_name }}</strong>
              <el-tag
                :type="item.approval === 'approved' ? 'success' : 'danger'"
                size="small"
                class="ml-2"
              >
                {{ item.approval === 'approved' ? '同意' : '拒绝' }}
              </el-tag>
            </p>
            <p v-if="item.comment" class="mt-2">{{ item.comment }}</p>
          </el-card>
        </el-timeline-item>
      </el-timeline>
    </div>
  </el-card>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import dayjs from 'dayjs'

interface Props {
  status: string
  approvals: any[]
  form?: any
}

const props = withDefaults(defineProps<Props>(), {
  form: () => ({})
})

const activeStep = computed(() => {
  const stepMap: Record<string, number> = {
    draft: 0,
    pending: 1,
    approved: 2,
    completed: 3
  }
  return stepMap[props.status] || 0
})

const formatTime = (time: string) => {
  return time ? dayjs(time).format('YYYY-MM-DD HH:mm') : '-'
}
</script>

<style scoped>
.approval-list h4 {
  margin-bottom: 12px;
  color: #606266;
}

.mt-4 {
  margin-top: 16px;
}

.mt-2 {
  margin-top: 8px;
}

.ml-2 {
  margin-left: 8px;
}
</style>
```

---

## API 集成

```typescript
// src/api/assets/pickup.ts

import request from '@/utils/request'

export interface PickupItem {
  asset_id: number
  quantity?: number
  remark?: string
}

export interface CreatePickupData {
  department: number
  pickup_date: string
  pickup_reason: string
  items: PickupItem[]
}

// 获取领用单列表
export const getPickupList = (params: any) => {
  return request.get('/api/assets/pickups/', { params })
}

// 获取领用单详情
export const getPickupDetail = (id: number) => {
  return request.get(`/api/assets/pickups/${id}/`)
}

// 创建领用单
export const createPickup = (data: CreatePickupData) => {
  return request.post('/api/assets/pickups/', data)
}

// 更新领用单
export const updatePickup = (id: number, data: CreatePickupData) => {
  return request.put(`/api/assets/pickups/${id}/`, data)
}

// 提交审批
export const submitPickup = (id: number) => {
  return request.post(`/api/assets/pickups/${id}/submit/`)
}

// 审批领用单
export const approvePickup = (id: number, approval: string, comment: string) => {
  return request.post(`/api/assets/pickups/${id}/approve/`, {
    approval,
    comment
  })
}

// 完成领用
export const completePickup = (id: number) => {
  return request.post(`/api/assets/pickups/${id}/complete/`)
}

// 取消领用单
export const cancelPickup = (id: number) => {
  return request.post(`/api/assets/pickups/${id}/cancel/`)
}
```

```typescript
// src/api/assets/transfer.ts

import request from '@/utils/request'

export const getTransferList = (params: any) => {
  return request.get('/api/assets/transfers/', { params })
}

export const getTransferDetail = (id: number) => {
  return request.get(`/api/assets/transfers/${id}/`)
}

export const createTransfer = (data: any) => {
  return request.post('/api/assets/transfers/', data)
}

export const approveTransfer = (id: number, approval: string, comment: string) => {
  // 根据当前用户判断是调出方还是调入方审批
  return request.post(`/api/assets/transfers/${id}/approve/`, {
    approval,
    comment
  })
}

export const approveFrom = (id: number, comment: string) => {
  return request.post(`/api/assets/transfers/${id}/approve_from/`, { comment })
}

export const approveTo = (id: number, comment: string) => {
  return request.post(`/api/assets/transfers/${id}/approve_to/`, { comment })
}

export const completeTransfer = (id: number) => {
  return request.post(`/api/assets/transfers/${id}/complete/`)
}
```

---

## 路由配置

```typescript
// src/router/assets.ts

export default [
  {
    path: '/assets/operations',
    component: () => import('@/layouts/OperationLayout.vue'),
    children: [
      {
        path: 'pickup',
        name: 'AssetPickupList',
        component: () => import('@/views/assets/operations/PickupList.vue'),
        meta: { title: '资产领用' }
      },
      {
        path: 'pickup/create',
        name: 'AssetPickupCreate',
        component: () => import('@/views/assets/operations/PickupForm.vue'),
        meta: { title: '新建领用单' }
      },
      {
        path: 'pickup/:id',
        name: 'AssetPickupDetail',
        component: () => import('@/views/assets/operations/PickupForm.vue'),
        meta: { title: '领用单详情' }
      },
      {
        path: 'pickup/:id/edit',
        name: 'AssetPickupEdit',
        component: () => import('@/views/assets/operations/PickupForm.vue'),
        meta: { title: '编辑领用单' }
      },
      {
        path: 'transfer',
        name: 'AssetTransferList',
        component: () => import('@/views/assets/operations/TransferList.vue'),
        meta: { title: '资产调拨' }
      },
      {
        path: 'transfer/create',
        name: 'AssetTransferCreate',
        component: () => import('@/views/assets/operations/TransferForm.vue'),
        meta: { title: '新建调拨单' }
      },
      {
        path: 'transfer/:id',
        name: 'AssetTransferDetail',
        component: () => import('@/views/assets/operations/TransferForm.vue'),
        meta: { title: '调拨单详情' }
      },
      {
        path: 'return',
        name: 'AssetReturnList',
        component: () => import('@/views/assets/operations/ReturnList.vue'),
        meta: { title: '资产退库' }
      },
      {
        path: 'loan',
        name: 'AssetLoanList',
        component: () => import('@/views/assets/operations/LoanList.vue'),
        meta: { title: '资产借用' }
      },
      {
        path: 'loan/create',
        name: 'AssetLoanCreate',
        component: () => import('@/views/assets/operations/LoanForm.vue'),
        meta: { title: '新建借用单' }
      }
    ]
  }
]
```

---

## 状态管理

```typescript
// src/stores/assets.ts

import { defineStore } from 'pinia'
import { ref } from 'vue'

export const useAssetStore = defineStore('assets', () => {
  // 当前操作的资产列表
  const selectedAssets = ref<any[]>([])

  // 添加选中资产
  const addSelectedAssets = (assets: any[]) => {
    assets.forEach(asset => {
      if (!selectedAssets.value.find(a => a.id === asset.id)) {
        selectedAssets.value.push(asset)
      }
    })
  }

  // 移除选中资产
  const removeSelectedAsset = (id: number) => {
    const index = selectedAssets.value.findIndex(a => a.id === id)
    if (index > -1) {
      selectedAssets.value.splice(index, 1)
    }
  }

  // 清空选中
  const clearSelectedAssets = () => {
    selectedAssets.value = []
  }

  return {
    selectedAssets,
    addSelectedAssets,
    removeSelectedAsset,
    clearSelectedAssets
  }
})
```

---

## 后续任务

1. 实现移动端适配（资产扫码操作）
2. 集成工作流引擎（Phase 3.1-3.2）
3. 实现消息通知推送
