# Phase 2.4: 组织架构增强与数据权限 - 前端实现

## 概述

实现组织架构增强的前端页面，包括一人多部门管理、完整部门路径显示、资产权限控制，以及资产操作流程（调拨、归还、借用、领用）的申请和审批。

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
src/views/
├── organizations/              # 组织管理
│   ├── DepartmentList.vue      # 部门列表（树形显示）
│   ├── DepartmentForm.vue      # 部门编辑表单
│   ├── UserDepartmentList.vue  # 用户部门关联
│   └── PermissionCenter.vue    # 权限中心
├── assets/                     # 资产操作
│   ├── operations/
│   │   ├── TransferList.vue    # 调拨单列表
│   │   ├── TransferForm.vue    # 调拨申请
│   │   ├── ReturnList.vue      # 归还单列表
│   │   ├── BorrowList.vue      # 借用单列表
│   │   ├── BorrowForm.vue      # 借用申请
│   │   ├── UseList.vue         # 领用单列表
│   │   └── UseForm.vue         # 领用申请
└── components/
    ├── DepartmentSelector.vue  # 部门选择器（带完整路径）
    └── CustodianSelector.vue    # 保管人选择器（带部门信息）
```

---

## 1. 部门列表（树形显示）

### DepartmentList.vue

```vue
<template>
  <div class="department-list">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>部门管理</span>
          <el-button type="primary" @click="handleCreate">
            <el-icon><Plus /></el-icon> 新增部门
          </el-button>
        </div>
      </template>

      <!-- 工具栏 -->
      <div class="toolbar">
        <el-input
          v-model="searchText"
          placeholder="搜索部门名称"
          clearable
          style="width: 250px"
        >
          <template #prefix>
            <el-icon><Search /></el-icon>
          </template>
        </el-input>
        <el-switch
          v-model="showInactive"
          active-text="显示已禁用"
          @change="fetchData"
        />
      </div>

      <!-- 部门树 -->
      <el-table
        :data="tableData"
        row-key="id"
        :tree-props="{ children: 'children', hasChildren: 'hasChildren' }"
        :expand-row-keys="expandedKeys"
        border
        class="dept-table"
      >
        <el-table-column prop="name" label="部门名称" width="300">
          <template #default="{ row }">
            <div class="dept-name-cell">
              <el-icon v-if="row.children?.length" class="folder-icon">
                <Folder />
              </el-icon>
              <el-icon v-else class="dept-icon">
                <OfficeBuilding />
              </el-icon>
              <span class="dept-name">{{ row.name }}</span>
              <el-tag v-if="!row.is_active" type="info" size="small" class="ml-8">
                已禁用
              </el-tag>
            </div>
          </template>
        </el-table-column>

        <el-table-column prop="full_path_name" label="完整路径" min-width="250">
          <template #default="{ row }">
            <span class="path-text">{{ row.full_path_name }}</span>
          </template>
        </el-table-column>

        <el-table-column prop="leader_name" label="部门负责人" width="120">
          <template #default="{ row }">
            <div v-if="row.leader_id" class="leader-cell">
              <el-avatar :size="24" :src="row.leader_avatar">
                {{ row.leader_name?.charAt(0) }}
              </el-avatar>
              <span class="ml-8">{{ row.leader_name }}</span>
            </div>
            <el-button v-else link type="primary" size="small" @click="handleSetLeader(row)">
              设置
            </el-button>
          </template>
        </el-table-column>

        <el-table-column prop="member_count" label="成员数" width="100" align="center" />

        <el-table-column prop="asset_count" label="资产数" width="100" align="center" />

        <el-table-column prop="level" label="层级" width="80" align="center" />

        <el-table-column label="操作" width="220" fixed="right">
          <template #default="{ row }">
            <el-button link type="primary" @click="handleViewMembers(row)">
              成员
            </el-button>
            <el-button link type="primary" @click="handleEdit(row)">
              编辑
            </el-button>
            <el-dropdown @command="(cmd) => handleCommand(cmd, row)">
              <el-button link type="primary">
                更多<el-icon class="el-icon--right"><ArrowDown /></el-icon>
              </el-button>
              <template #dropdown>
                <el-dropdown-menu>
                  <el-dropdown-item command="addChildren">添加子部门</el-dropdown-item>
                  <el-dropdown-item command="setLeader">设置负责人</el-dropdown-item>
                  <el-dropdown-item command="toggleActive">
                    {{ row.is_active ? '禁用' : '启用' }}
                  </el-dropdown-item>
                  <el-dropdown-item command="delete" divided>删除</el-dropdown-item>
                </el-dropdown-menu>
              </template>
            </el-dropdown>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <!-- 部门表单弹窗 -->
    <DepartmentForm
      v-model="formVisible"
      :department="currentDepartment"
      :parent-departments="flatDepartments"
      @success="fetchData"
    />

    <!-- 设置负责人弹窗 -->
    <SetLeaderDialog
      v-model="leaderVisible"
      :department="currentDepartment"
      @success="fetchData"
    />

    <!-- 成员列表弹窗 -->
    <MemberListDialog
      v-model="membersVisible"
      :department="currentDepartment"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  Plus, Search, Folder, OfficeBuilding, ArrowDown
} from '@element-plus/icons-vue'
import { orgApi } from '@/api/organizations'
import DepartmentForm from './DepartmentForm.vue'
import SetLeaderDialog from './SetLeaderDialog.vue'
import MemberListDialog from './MemberListDialog.vue'

const searchText = ref('')
const showInactive = ref(false)
const tableData = ref([])
const expandedKeys = ref([])
const formVisible = ref(false)
const leaderVisible = ref(false)
const membersVisible = ref(false)
const currentDepartment = ref(null)

const flatDepartures = computed(() => {
  const flatten = (depts) => {
    const result = []
    depts.forEach(dept => {
      result.push(dept)
      if (dept.children) {
        result.push(...flatten(dept.children))
      }
    })
    return result
  }
  return flatten(tableData.value)
})

const fetchData = async () => {
  const { data } = await orgApi.getDepartmentTree({
    include_inactive: showInactive.value
  })

  // 过滤搜索
  if (searchText.value) {
    tableData.value = filterTree(data, searchText.value)
  } else {
    tableData.value = data
  }
}

const filterTree = (data, keyword) => {
  const result = []
  data.forEach(item => {
    const match = item.name.toLowerCase().includes(keyword.toLowerCase())
    const children = item.children ? filterTree(item.children, keyword) : []

    if (match || children.length > 0) {
      result.push({
        ...item,
        children: children.length > 0 ? children : item.children
      })
    }
  })
  return result
}

const handleCreate = () => {
  currentDepartment.value = null
  formVisible.value = true
}

const handleEdit = (row) => {
  currentDepartment.value = row
  formVisible.value = true
}

const handleSetLeader = (row) => {
  currentDepartment.value = row
  leaderVisible.value = true
}

const handleViewMembers = (row) => {
  currentDepartment.value = row
  membersVisible.value = true
}

const handleCommand = async (command, row) => {
  switch (command) {
    case 'addChildren':
      currentDepartment.value = { parent: row }
      formVisible.value = true
      break
    case 'setLeader':
      handleSetLeader(row)
      break
    case 'toggleActive':
      await orgApi.updateDepartment(row.id, { is_active: !row.is_active })
      ElMessage.success('操作成功')
      fetchData()
      break
    case 'delete':
      try {
        await ElMessageBox.confirm('确认删除此部门？', '警告')
        await orgApi.deleteDepartment(row.id)
        ElMessage.success('删除成功')
        fetchData()
      } catch {
        // cancel
      }
      break
  }
}

onMounted(() => {
  fetchData()
})
</script>

<style scoped>
.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.toolbar {
  display: flex;
  gap: 16px;
  margin-bottom: 16px;
}

.dept-table {
  margin-top: 16px;
}

.dept-name-cell {
  display: flex;
  align-items: center;
}

.folder-icon,
.dept-icon {
  margin-right: 8px;
  color: #909399;
}

.dept-name {
  font-weight: 500;
}

.path-text {
  color: #909399;
  font-size: 13px;
}

.leader-cell {
  display: flex;
  align-items: center;
}

.ml-8 {
  margin-left: 8px;
}
</style>
```

---

## 2. 部门选择器（带完整路径）

### DepartmentSelector.vue

```vue
<template>
  <el-select
    :model-value="modelValue"
    :placeholder="placeholder"
    :clearable="clearable"
    :multiple="multiple"
    :filterable="filterable"
    :disabled="disabled"
    @change="handleChange"
    @clear="handleClear"
  >
    <el-option
      v-for="dept in options"
      :key="dept.id"
      :label="dept.full_path_name || dept.name"
      :value="dept.id"
      :disabled="dept.disabled"
    >
      <div class="dept-option">
        <span class="dept-indent" :style="{ paddingLeft: dept.level * 16 + 'px' }"></span>
        <el-icon v-if="dept.level > 0" class="tree-icon"><ArrowRight /></el-icon>
        <span>{{ dept.name }}</span>
        <span class="dept-path">{{ dept.full_path }}</span>
      </div>
    </el-option>
  </el-select>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { ArrowRight } from '@element-plus/icons-vue'
import { orgApi } from '@/api/organizations'

const props = defineProps({
  modelValue: {
    type: [String, Number, Array],
    default: ''
  },
  placeholder: {
    type: String,
    default: '请选择部门'
  },
  clearable: {
    type: Boolean,
    default: true
  },
  multiple: {
    type: Boolean,
    default: false
  },
  filterable: {
    type: Boolean,
    default: true
  },
  disabled: {
    type: Boolean,
    default: false
  },
  showInactive: {
    type: Boolean,
    default: false
  },
  // 仅显示叶子节点
  onlyLeaf: {
    type: Boolean,
    default: false
  }
})

const emit = defineEmits(['update:modelValue', 'change'])

const options = ref([])

const flattenTree = (tree, level = 0) => {
  const result = []
  tree.forEach(node => {
    const isLeaf = !node.children || node.children.length === 0

    if (!props.onlyLeaf || isLeaf) {
      result.push({
        id: node.id,
        name: node.name,
        full_path: node.full_path,
        full_path_name: node.full_path_name,
        level,
        disabled: !node.is_active
      })
    }

    if (node.children && node.children.length > 0) {
      result.push(...flattenTree(node.children, level + 1))
    }
  })
  return result
}

const fetchData = async () => {
  const { data } = await orgApi.getDepartmentTree({
    include_inactive: props.showInactive
  })
  options.value = flattenTree(data)
}

const handleChange = (value) => {
  emit('update:modelValue', value)
  emit('change', value)
}

const handleClear = () => {
  emit('update:modelValue', props.multiple ? [] : '')
  emit('change', props.multiple ? [] : null)
}

onMounted(() => {
  fetchData()
})
</script>

<style scoped>
.dept-option {
  display: flex;
  align-items: center;
  width: 100%;
}

.dept-indent {
  display: inline-block;
}

.tree-icon {
  margin: 0 4px;
  font-size: 12px;
  color: #c0c4cc;
}

.dept-path {
  margin-left: 12px;
  font-size: 12px;
  color: #909399;
}
</style>
```

---

## 3. 保管人选择器（带部门信息）

### CustodianSelector.vue

```vue
<template>
  <el-select
    :model-value="modelValue"
    :placeholder="placeholder"
    :clearable="clearable"
    :filterable="filterable"
    :remote="remote"
    :remote-method="remoteSearch"
    :loading="loading"
    @change="handleChange"
  >
    <el-option
      v-for="user in options"
      :key="user.id"
      :label="user.label"
      :value="user.id"
    >
      <div class="user-option">
        <el-avatar :size="24" :src="user.avatar">
          {{ user.real_name?.charAt(0) }}
        </el-avatar>
        <span class="user-name">{{ user.real_name }}</span>
        <span class="user-dept">{{ user.department_path }}</span>
      </div>
    </el-option>
  </el-select>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { accountsApi } from '@/api/accounts'

const props = defineProps({
  modelValue: {
    type: [String, Number],
    default: ''
  },
  placeholder: {
    type: String,
    default: '请选择保管人'
  },
  clearable: {
    type: Boolean,
    default: true
  },
  filterable: {
    type: Boolean,
    default: true
  },
  remote: {
    type: Boolean,
    default: true
  },
  // 限制部门范围
  departmentId: {
    type: String,
    default: null
  }
})

const emit = defineEmits(['update:modelValue', 'change'])

const options = ref([])
const loading = ref(false)

const fetchUsers = async (keyword = '') => {
  loading.value = true
  try {
    const { data } = await accountsApi.listUsers({
      keyword,
      department_id: props.departmentId,
      page: 1,
      size: 50
    })

    options.value = data.results.map(u => ({
      id: u.id,
      real_name: u.real_name,
      avatar: u.avatar,
      department_path: u.asset_department_name || u.primary_department_name || '-',
      label: `${u.real_name} (${u.asset_department_name || u.primary_department_name || '-'})`
    }))
  } finally {
    loading.value = false
  }
}

const remoteSearch = (query) => {
  fetchUsers(query)
}

const handleChange = (value) => {
  emit('update:modelValue', value)
  emit('change', value)
}

// 初始加载
fetchUsers()
</script>

<style scoped>
.user-option {
  display: flex;
  align-items: center;
  width: 100%;
}

.user-name {
  margin: 0 8px;
  font-weight: 500;
}

.user-dept {
  margin-left: auto;
  font-size: 12px;
  color: #909399;
}
</style>
```

---

## 4. 资产调拨申请

### TransferForm.vue

```vue
<template>
  <el-dialog
    v-model="visible"
    :title="isEdit ? '编辑调拨单' : '创建资产调拨'"
    width="800px"
    @close="handleClose"
  >
    <el-form
      ref="formRef"
      :model="form"
      :rules="rules"
      label-width="120px"
    >
      <!-- 资产选择 -->
      <el-form-item label="调拨资产" prop="asset_ids" required>
        <el-button @click="showAssetSelector = true">
          选择资产
        </el-button>
        <div v-if="selectedAssets.length > 0" class="selected-assets">
          <el-tag
            v-for="asset in selectedAssets"
            :key="asset.id"
            closable
            @close="removeAsset(asset)"
          >
            {{ asset.code }} - {{ asset.name }}
          </el-tag>
        </div>
      </el-form-item>

      <!-- 调入信息 -->
      <el-form-item label="调入部门" prop="to_department_id" required>
        <DepartmentSelector
          v-model="form.to_department_id"
          placeholder="请选择调入部门"
        />
      </el-form-item>

      <el-form-item label="调入保管人" prop="to_custodian_id" required>
        <CustodianSelector
          v-model="form.to_custodian_id"
          :department-id="form.to_department_id"
          placeholder="请选择调入保管人"
        />
      </el-form-item>

      <el-form-item label="调入位置">
        <LocationSelector v-model="form.to_location_id" />
      </el-form-item>

      <!-- 调拨原因 -->
      <el-form-item label="调拨原因" prop="reason" required>
        <el-input
          v-model="form.reason"
          type="textarea"
          :rows="3"
          placeholder="请输入调拨原因"
        />
      </el-form-item>

      <el-form-item label="备注">
        <el-input
          v-model="form.remark"
          type="textarea"
          :rows="2"
          placeholder="请输入备注"
        />
      </el-form-item>
    </el-form>

    <!-- 资产选择器 -->
    <AssetSelector
      v-model="showAssetSelector"
      :multiple="true"
      @confirm="handleAssetSelect"
    />

    <template #footer>
      <el-button @click="handleClose">取消</el-button>
      <el-button type="primary" @click="handleSubmit" :loading="submitting">
        提交申请
      </el-button>
    </template>
  </el-dialog>
</template>

<script setup lang="ts">
import { ref, reactive, computed } from 'vue'
import { ElMessage } from 'element-plus'
import { assetApi } from '@/api/assets'
import DepartmentSelector from '@/components/DepartmentSelector.vue'
import CustodianSelector from '@/components/CustodianSelector.vue'
import LocationSelector from '@/components/LocationSelector.vue'
import AssetSelector from '@/components/AssetSelector.vue'

const props = defineProps({
  modelValue: Boolean,
  transfer: Object
})

const emit = defineEmits(['update:modelValue', 'success'])

const visible = computed({
  get: () => props.modelValue,
  set: (val) => emit('update:modelValue', val)
})

const isEdit = computed(() => !!props.transfer)

const formRef = ref()
const submitting = ref(false)
const showAssetSelector = ref(false)
const selectedAssets = ref([])

const form = reactive({
  asset_ids: [],
  to_department_id: '',
  to_custodian_id: '',
  to_location_id: '',
  reason: '',
  remark: ''
})

const rules = {
  asset_ids: [{ required: true, message: '请选择调拨资产' }],
  to_department_id: [{ required: true, message: '请选择调入部门' }],
  to_custodian_id: [{ required: true, message: '请选择调入保管人' }],
  reason: [{ required: true, message: '请输入调拨原因' }]
}

const handleAssetSelect = (assets) => {
  selectedAssets.value = assets
  form.asset_ids = assets.map(a => a.id)
}

const removeAsset = (asset) => {
  const index = selectedAssets.value.findIndex(a => a.id === asset.id)
  if (index > -1) {
    selectedAssets.value.splice(index, 1)
    form.asset_ids = selectedAssets.value.map(a => a.id)
  }
}

const handleSubmit = async () => {
  await formRef.value.validate()

  submitting.value = true
  try {
    await assetApi.createTransfer(form)
    ElMessage.success('调拨申请已提交')
    emit('success')
    handleClose()
  } finally {
    submitting.value = false
  }
}

const handleClose = () => {
  visible.value = false
  formRef.value?.resetFields()
  selectedAssets.value = []
}
</script>
```

---

## 5. 我的资产操作（用户端）

### MyAssetOperations.vue

```vue
<template>
  <div class="my-asset-operations">
    <!-- 操作卡片 -->
    <div class="operation-cards">
      <div class="operation-card" @click="goTo('borrow')">
        <div class="card-icon borrow">
          <el-icon><ShoppingCart /></el-icon>
        </div>
        <div class="card-info">
          <div class="card-title">借用资产</div>
          <div class="card-desc">临时借用公司资产</div>
        </div>
      </div>

      <div class="operation-card" @click="goTo('use')">
        <div class="card-icon use">
          <el-icon><Box /></el-icon>
        </div>
        <div class="card-info">
          <div class="card-title">领用资产</div>
          <div class="card-desc">领用工作所需资产</div>
        </div>
      </div>

      <div class="operation-card return" @click="goTo('return')">
        <div class="card-icon return">
          <el-icon><Back /></el-icon>
        </div>
        <div class="card-info">
          <div class="card-title">归还资产</div>
          <div class="card-desc">归还已借用的资产</div>
        </div>
      </div>
    </div>

    <!-- 进行中的操作 -->
    <el-card class="mt-16">
      <template #header>
        <span>进行中的操作</span>
      </template>

      <el-tabs v-model="activeTab">
        <el-tab-pane label="借用中" name="borrowing">
          <BorrowList :status="borrowed" />
        </el-tab-pane>

        <el-tab-pane label="待审批" name="pending">
          <div class="pending-list">
            <div
              v-for="item in pendingItems"
              :key="item.id"
              class="pending-item"
            >
              <div class="item-info">
                <span class="item-type">{{ getTypeName(item.operation_type) }}</span>
                <span class="item-code">{{ item.code }}</span>
                <span class="item-status">{{ item.status_display }}</span>
              </div>
              <el-button link type="primary" @click="viewDetail(item)">
                查看
              </el-button>
            </div>
          </div>
        </el-tab-pane>
      </el-tabs>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ShoppingCart, Box, Back } from '@element-plus/icons-vue'
import BorrowList from './operations/BorrowList.vue'

const router = useRouter()
const activeTab = ref('borrowing')
const pendingItems = ref([])

const goTo = (type) => {
  router.push({ name: `Asset${type.charAt(0).toUpperCase() + type.slice(1)}Form` })
}

const getTypeName = (type) => {
  const map = {
    transfer: '调拨',
    return: '归还',
    borrow: '借用',
    use: '领用'
  }
  return map[type] || type
}

const viewDetail = (item) => {
  // 查看详情
}
</script>

<style scoped>
.operation-cards {
  display: flex;
  gap: 16px;
}

.operation-card {
  flex: 1;
  display: flex;
  align-items: center;
  padding: 20px;
  background: white;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.05);
  cursor: pointer;
  transition: all 0.3s;
}

.operation-card:hover {
  box-shadow: 0 4px 16px rgba(0,0,0,0.1);
  transform: translateY(-2px);
}

.card-icon {
  width: 56px;
  height: 56px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 28px;
  color: white;
}

.card-icon.borrow { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); }
.card-icon.use { background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%); }
.card-icon.return { background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%); }

.card-info {
  margin-left: 16px;
}

.card-title {
  font-size: 16px;
  font-weight: bold;
  margin-bottom: 4px;
}

.card-desc {
  font-size: 13px;
  color: #909399;
}

.mt-16 {
  margin-top: 16px;
}

.pending-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px;
  border-bottom: 1px solid #f5f7fa;
}

.pending-item:last-child {
  border-bottom: none;
}

.item-info {
  display: flex;
  gap: 12px;
  align-items: center;
}

.item-type {
  padding: 2px 8px;
  background: #ecf5ff;
  color: #409eff;
  border-radius: 4px;
  font-size: 12px;
}

.item-code {
  font-weight: 500;
}

.item-status {
  padding: 2px 8px;
  background: #fef0f0;
  color: #f56c6c;
  border-radius: 4px;
  font-size: 12px;
}
</style>
```

---

## 6. API封装

```typescript
// src/api/organizations.ts

import request from '@/utils/request'

export const orgApi = {
  // 部门相关
  getDepartmentTree(params?: any) {
    return request.get('/api/organizations/departments/tree/', { params })
  },

  getDepartments(params?: any) {
    return request.get('/api/organizations/departments/', { params })
  },

  getDepartment(id: string) {
    return request.get(`/api/organizations/departments/${id}/`)
  },

  createDepartment(data: any) {
    return request.post('/api/organizations/departments/', data)
  },

  updateDepartment(id: string, data: any) {
    return request.put(`/api/organizations/departments/${id}/`, data)
  },

  deleteDepartment(id: string) {
    return request.delete(`/api/organizations/departments/${id}/`)
  },

  setDepartmentLeader(id: string, leader_id: string) {
    return request.put(`/api/organizations/departments/${id}/leader/`, { leader_id })
  },

  getDepartmentMembers(id: string, params?: any) {
    return request.get(`/api/organizations/departments/${id}/members/`, { params })
  },

  // 用户部门关联
  getUserDepartments(params?: any) {
    return request.get('/api/organizations/user-departments/', { params })
  },

  addUserDepartment(data: any) {
    return request.post('/api/organizations/user-departments/', data)
  },

  updateUserDepartment(id: string, data: any) {
    return request.put(`/api/organizations/user-departments/${id}/`, data)
  },

  deleteUserDepartment(id: string) {
    return request.delete(`/api/organizations/user-departments/${id}/`)
  },

  setUserAssetDepartment(userId: string, data: any) {
    return request.put(`/api/organizations/users/${userId}/asset-department/`, data)
  },

  // 数据权限
  getMyPermissions() {
    return request.get('/api/organizations/my-permissions/')
  },

  getViewableDepartments(params?: any) {
    return request.get('/api/organizations/viewable-departments/', { params })
  },

  getViewableUsers(params?: any) {
    return request.get('/api/organizations/viewable-users/', { params })
  },

  getSubordinateUsers(params?: any) {
    return request.get('/api/organizations/subordinate-users/', { params })
  },

  getAssetStatistics(params?: any) {
    return request.get('/api/organizations/asset-statistics/', { params })
  }
}

// src/api/assets/operations.ts

import request from '@/utils/request'

export const assetApi = {
  // 调拨
  createTransfer(data: any) {
    return request.post('/api/assets/transfers/', data)
  },

  getTransfers(params?: any) {
    return request.get('/api/assets/transfers/', { params })
  },

  getTransfer(id: string) {
    return request.get(`/api/assets/transfers/${id}/`)
  },

  approveTransfer(id: string, data: any) {
    return request.post(`/api/assets/transfers/${id}/approve/`, data)
  },

  confirmTransfer(id: string, data: any) {
    return request.post(`/api/assets/transfers/${id}/confirm/`, data)
  },

  // 归还
  createReturn(data: any) {
    return request.post('/api/assets/returns/', data)
  },

  getReturns(params?: any) {
    return request.get('/api/assets/returns/', { params })
  },

  confirmReturn(id: string, data: any) {
    return request.post(`/api/assets/returns/${id}/confirm/`, data)
  },

  // 借用
  createBorrow(data: any) {
    return request.post('/api/assets/borrows/', data)
  },

  getBorrows(params?: any) {
    return request.get('/api/assets/borrows/', { params })
  },

  approveBorrow(id: string, data: any) {
    return request.post(`/api/assets/borrows/${id}/approve/`, data)
  },

  returnBorrow(id: string, data: any) {
    return request.post(`/api/assets/borrows/${id}/return/`, data)
  },

  // 领用
  createUse(data: any) {
    return request.post('/api/assets/uses/', data)
  },

  getUses(params?: any) {
    return request.get('/api/assets/uses/', { params })
  },

  approveUse(id: string, data: any) {
    return request.post(`/api/assets/uses/${id}/approve/`, data)
  }
}
```

---

## 后续任务

所有Phase已完成！
