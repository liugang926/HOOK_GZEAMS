# Phase 1.2: Organizations 独立模块 - 前端实现

## 概述

实现组织和部门管理的前端页面，包括组织选择器、部门树管理、用户部门关联等功能。

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
├── organizations/                 # 组织管理
│   ├── OrganizationList.vue       # 组织列表
│   ├── OrganizationForm.vue       # 组织编辑表单
│   ├── DepartmentList.vue         # 部门列表（树形）
│   ├── DepartmentForm.vue         # 部门编辑表单
│   └── MemberList.vue             # 成员管理
├── profile/                       # 用户设置
│   ├── MyOrganizations.vue        # 我加入的组织
│   └── MyDepartments.vue          # 我的部门
└── components/
    ├── OrganizationSelector.vue   # 组织选择器
    ├── DepartmentSelector.vue     # 部门选择器（带完整路径）
    ├── DepartmentTree.vue         # 部门树组件
    └── MemberPicker.vue           # 成员选择器
```

---

## 1. 组织选择器组件

### OrganizationSelector.vue

```vue
<template>
  <el-dropdown trigger="click" @command="handleCommand">
    <div class="org-selector">
      <el-icon><OfficeBuilding /></el-icon>
      <span class="org-name">{{ currentOrg?.name || '选择组织' }}</span>
      <el-tag v-if="currentOrg" size="small" type="success" class="ml-8">
        {{ getRoleName(currentOrg?.role) }}
      </el-tag>
      <el-icon><ArrowDown /></el-icon>
    </div>
    <template #dropdown>
      <el-dropdown-menu>
        <el-dropdown-item
          v-for="org in organizations"
          :key="org.id"
          :command="org.id"
          :class="{ 'is-active': org.id === currentOrg?.id }"
        >
          <div class="org-item">
            <div class="org-main">
              <span class="org-name">{{ org.name }}</span>
              <el-tag v-if="org.id === currentOrg?.id" size="small" type="success">
                当前
              </el-tag>
            </div>
            <div class="org-meta">
              <span class="org-role">{{ getRoleName(org.role) }}</span>
              <span class="org-code">{{ org.code }}</span>
            </div>
          </div>
        </el-dropdown-item>
        <el-dropdown-item divided command="join">
          <el-icon><Plus /></el-icon>
          加入新组织
        </el-dropdown-item>
        <el-dropdown-item divided command="manage">
          <el-icon><Setting /></el-icon>
          组织管理
        </el-dropdown-item>
      </el-dropdown-menu>
    </template>
  </el-dropdown>

  <!-- 加入组织对话框 -->
  <JoinOrganizationDialog v-model="showJoinDialog" @success="loadOrganizations" />
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { OfficeBuilding, ArrowDown, Plus, Setting } from '@element-plus/icons-vue'
import { orgApi } from '@/api/organizations'
import { useUserStore } from '@/stores/user'
import JoinOrganizationDialog from '@/views/profile/JoinOrganizationDialog.vue'

const userStore = useUserStore()
const showJoinDialog = ref(false)
const organizations = ref([])

const currentOrg = computed(() => userStore.currentOrganization)

const getRoleName = (role: string) => {
  const roleMap = {
    admin: '管理员',
    member: '成员',
    auditor: '审计员'
  }
  return roleMap[role] || '成员'
}

const loadOrganizations = async () => {
  try {
    const { data } = await orgApi.getUserOrganizations()
    organizations.value = data.organizations
  } catch (error) {
    console.error('加载组织列表失败', error)
  }
}

const handleCommand = async (command: string) => {
  if (command === 'join') {
    showJoinDialog.value = true
  } else if (command === 'manage') {
    // 跳转到组织管理页面
    window.location.href = '/organizations'
  } else {
    // 切换组织
    try {
      await orgApi.switchOrganization(command)
      ElMessage.success('组织切换成功')
      location.reload()
    } catch (error) {
      ElMessage.error('组织切换失败')
    }
  }
}

onMounted(() => {
  loadOrganizations()
})
</script>

<style scoped>
.org-selector {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 12px;
  border-radius: 4px;
  cursor: pointer;
  transition: background-color 0.2s;
}

.org-selector:hover {
  background-color: var(--el-fill-color-light);
}

.org-item {
  width: 200px;
}

.org-main {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.org-meta {
  display: flex;
  justify-content: space-between;
  margin-top: 4px;
  font-size: 12px;
  color: var(--el-text-color-secondary);
}

.is-active {
  background-color: var(--el-color-primary-light-9);
}

.ml-8 {
  margin-left: 8px;
}
</style>
```

---

## 2. 部门列表（树形显示）

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

      <!-- 部门树表格 -->
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

        <el-table-column prop="leader_name" label="部门负责人" width="140">
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

        <el-table-column prop="order" label="排序" width="80" align="center" />

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

const flatDepartments = computed(() => {
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

## 3. 部门选择器（带完整路径）

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
  >
    <el-option
      v-for="dept in options"
      :key="dept.id"
      :label="dept.full_path_name || dept.name"
      :value="dept.id"
      :disabled="!dept.is_active"
    >
      <div class="dept-option">
        <span
          class="dept-indent"
          :style="{ paddingLeft: dept.level * 16 + 'px' }"
        ></span>
        <span class="dept-name">{{ dept.name }}</span>
        <span class="dept-path">{{ dept.full_path }}</span>
      </div>
    </el-option>
  </el-select>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
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
        is_active: node.is_active
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

.dept-name {
  flex-shrink: 0;
}

.dept-path {
  margin-left: 12px;
  font-size: 12px;
  color: #909399;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
</style>
```

---

## 4. 我加入的组织

### MyOrganizations.vue

```vue
<template>
  <div class="my-organizations">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>我加入的组织</span>
          <el-button type="primary" @click="showJoinDialog = true">
            <el-icon><Plus /></el-icon> 加入新组织
          </el-button>
        </div>
      </template>

      <div class="org-list">
        <div
          v-for="org in organizations"
          :key="org.id"
          class="org-card"
          :class="{ 'is-primary': org.is_primary }"
        >
          <div class="org-header">
            <div class="org-info">
              <el-icon class="org-icon"><OfficeBuilding /></el-icon>
              <div>
                <div class="org-name">{{ org.name }}</div>
                <div class="org-code">{{ org.code }}</div>
              </div>
            </div>
            <div class="org-actions">
              <el-tag v-if="org.is_primary" type="success" size="small">
                默认
              </el-tag>
              <el-tag :type="getRoleType(org.role)" size="small">
                {{ getRoleName(org.role) }}
              </el-tag>
            </div>
          </div>

          <div class="org-meta">
            <div class="meta-item">
              <el-icon><User /></el-icon>
              <span>{{ org.member_count || '-' }} 成员</span>
            </div>
            <div class="meta-item">
              <el-icon><Calendar /></el-icon>
              <span>加入于 {{ formatDate(org.joined_at) }}</span>
            </div>
          </div>

          <div class="org-footer">
            <el-button
              v-if="!org.is_primary"
              size="small"
              @click="handleSetPrimary(org)"
            >
              设为默认
            </el-button>
            <el-button
              size="small"
              type="danger"
              plain
              @click="handleLeave(org)"
            >
              退出
            </el-button>
          </div>
        </div>
      </div>
    </el-card>

    <!-- 加入组织对话框 -->
    <JoinOrganizationDialog
      v-model="showJoinDialog"
      @success="loadOrganizations"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  Plus, OfficeBuilding, User, Calendar
} from '@element-plus/icons-vue'
import { orgApi } from '@/api/organizations'
import JoinOrganizationDialog from './JoinOrganizationDialog.vue'

const showJoinDialog = ref(false)
const organizations = ref([])

const getRoleName = (role) => {
  const map = {
    admin: '管理员',
    member: '成员',
    auditor: '审计员'
  }
  return map[role] || '成员'
}

const getRoleType = (role) => {
  const map = {
    admin: 'danger',
    member: 'info',
    auditor: 'warning'
  }
  return map[role] || 'info'
}

const formatDate = (dateStr) => {
  const date = new Date(dateStr)
  return date.toLocaleDateString()
}

const loadOrganizations = async () => {
  const { data } = await orgApi.getUserOrganizations()
  organizations.value = data.organizations
}

const handleSetPrimary = async (org) => {
  try {
    await orgApi.switchOrganization(org.id)
    ElMessage.success('已切换为默认组织')
    loadOrganizations()
  } catch (error) {
    ElMessage.error('切换失败')
  }
}

const handleLeave = async (org) => {
  try {
    await ElMessageBox.confirm(
      `确认退出组织 "${org.name}"？退出后您将无法访问该组织的任何数据。`,
      '退出组织',
      { type: 'warning' }
    )

    await orgApi.leaveOrganization(org.id)
    ElMessage.success('已退出组织')
    loadOrganizations()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('操作失败')
    }
  }
}

onMounted(() => {
  loadOrganizations()
})
</script>

<style scoped>
.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.org-list {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: 16px;
}

.org-card {
  border: 1px solid var(--el-border-color);
  border-radius: 8px;
  padding: 16px;
  transition: all 0.3s;
}

.org-card:hover {
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.1);
}

.org-card.is-primary {
  border-color: var(--el-color-success);
  background-color: var(--el-color-success-light-9);
}

.org-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 12px;
}

.org-info {
  display: flex;
  gap: 12px;
}

.org-icon {
  font-size: 32px;
  color: var(--el-color-primary);
}

.org-name {
  font-size: 16px;
  font-weight: bold;
}

.org-code {
  font-size: 12px;
  color: var(--el-text-color-secondary);
  margin-top: 4px;
}

.org-actions {
  display: flex;
  gap: 8px;
}

.org-meta {
  display: flex;
  gap: 16px;
  margin-bottom: 12px;
  font-size: 13px;
  color: var(--el-text-color-secondary);
}

.meta-item {
  display: flex;
  align-items: center;
  gap: 4px;
}

.org-footer {
  display: flex;
  gap: 8px;
}
</style>
```

---

## 5. 加入组织对话框

### JoinOrganizationDialog.vue

```vue
<template>
  <el-dialog
    v-model="visible"
    title="加入组织"
    width="400px"
    @close="handleClose"
  >
    <el-form
      ref="formRef"
      :model="form"
      :rules="rules"
      label-width="100px"
    >
      <el-form-item label="邀请码" prop="invite_code">
        <el-input
          v-model="form.invite_code"
          placeholder="请输入组织邀请码"
          maxlength="8"
          show-word-limit
          clearable
        >
          <template #append>
            <el-button :icon="Refresh" @click="form.invite_code = ''">
              清空
            </el-button>
          </template>
        </el-input>
      </el-form-item>

      <el-alert
        type="info"
        :closable="false"
        show-icon
      >
        <template #title>
          邀请码由组织管理员生成，有效期30天
        </template>
      </el-alert>
    </el-form>

    <template #footer>
      <el-button @click="handleClose">取消</el-button>
      <el-button type="primary" @click="handleSubmit" :loading="submitting">
        加入
      </el-button>
    </template>
  </el-dialog>
</template>

<script setup lang="ts">
import { ref, reactive, computed } from 'vue'
import { ElMessage } from 'element-plus'
import { Refresh } from '@element-plus/icons-vue'
import { orgApi } from '@/api/organizations'

const props = defineProps({
  modelValue: Boolean
})

const emit = defineEmits(['update:modelValue', 'success'])

const visible = computed({
  get: () => props.modelValue,
  set: (val) => emit('update:modelValue', val)
})

const formRef = ref()
const submitting = ref(false)

const form = reactive({
  invite_code: ''
})

const rules = {
  invite_code: [
    { required: true, message: '请输入邀请码', trigger: 'blur' },
    { len: 8, message: '邀请码长度为8位', trigger: 'blur' }
  ]
}

const handleSubmit = async () => {
  await formRef.value.validate()

  submitting.value = true
  try {
    await orgApi.joinOrganization(form)
    ElMessage.success('成功加入组织')
    emit('success')
    handleClose()
  } catch (error) {
    const msg = error.response?.data?.message || '加入失败，请检查邀请码是否正确'
    ElMessage.error(msg)
  } finally {
    submitting.value = false
  }
}

const handleClose = () => {
  visible.value = false
  formRef.value?.resetFields()
}
</script>
```

---

## 6. API 封装

### organizations.ts

```typescript
// src/api/organizations.ts

import request from '@/utils/request'

export const orgApi = {
  // ========== 组织管理 ==========
  getOrganizations(params?: any) {
    return request.get('/api/organizations/', { params })
  },

  getOrganization(id: string) {
    return request.get(`/api/organizations/${id}/`)
  },

  createOrganization(data: any) {
    return request.post('/api/organizations/', data)
  },

  updateOrganization(id: string, data: any) {
    return request.put(`/api/organizations/${id}/`, data)
  },

  deleteOrganization(id: string) {
    return request.delete(`/api/organizations/${id}/`)
  },

  regenerateInviteCode(id: string) {
    return request.post(`/api/organizations/${id}/regenerate-invite-code/`)
  },

  // ========== 部门管理 ==========
  getDepartments(params?: any) {
    return request.get('/api/organizations/departments/', { params })
  },

  getDepartmentTree(params?: any) {
    return request.get('/api/organizations/departments/tree/', { params })
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

  setDepartmentLeader(id: string, leaderId: string) {
    return request.put(`/api/organizations/departments/${id}/leader/`, {
      leader_id: leaderId
    })
  },

  getDepartmentMembers(id: string, params?: any) {
    return request.get(`/api/organizations/departments/${id}/members/`, { params })
  },

  // ========== 用户组织关联 ==========
  getUserOrganizations() {
    return request.get('/api/organizations/user/organizations/')
  },

  joinOrganization(inviteCode: string) {
    return request.post('/api/organizations/user/organizations/', {
      invite_code: inviteCode
    })
  },

  leaveOrganization(id: string) {
    return request.delete(`/api/organizations/user/organizations/${id}/`)
  },

  switchOrganization(id: string) {
    return request.post('/api/organizations/user/switch-organization/', {
      organization_id: id
    })
  },

  // ========== 用户部门关联 ==========
  getUserDepartments(params?: any) {
    return request.get('/api/organizations/user/departments/', { params })
  },

  addUserDepartment(data: any) {
    return request.post('/api/organizations/user/departments/', data)
  },

  updateUserDepartment(id: string, data: any) {
    return request.put(`/api/organizations/user/departments/${id}/`, data)
  },

  deleteUserDepartment(id: string) {
    return request.delete(`/api/organizations/user/departments/${id}/`)
  },

  setPrimaryDepartment(id: string) {
    return request.put(`/api/organizations/user/departments/${id}/primary/`, {
      is_primary: true
    })
  },

  // ========== 数据权限 ==========
  getViewableDepartments(params?: any) {
    return request.get('/api/organizations/permissions/viewable-departments/', { params })
  },

  getViewableUsers(params?: any) {
    return request.get('/api/organizations/permissions/viewable-users/', { params })
  },

  getSubordinateUsers(params?: any) {
    return request.get('/api/organizations/permissions/subordinate-users/', { params })
  },

  getAssetStatistics(params?: any) {
    return request.get('/api/organizations/permissions/asset-statistics/', { params })
  }
}
```

---

## 7. 路由配置

### router/index.ts

```typescript
{
  path: '/organizations',
  component: Layout,
  meta: { title: '组织管理', requiresAuth: true },
  children: [
    {
      path: '',
      name: 'OrganizationList',
      component: () => import('@/views/organizations/OrganizationList.vue')
    },
    {
      path: 'departments',
      name: 'DepartmentList',
      component: () => import('@/views/organizations/DepartmentList.vue')
    }
  ]
},
{
  path: '/profile',
  component: Layout,
  meta: { title: '个人设置', requiresAuth: true },
  children: [
    {
      path: 'organizations',
      name: 'MyOrganizations',
      component: () => import('@/views/profile/MyOrganizations.vue')
    },
    {
      path: 'departments',
      name: 'MyDepartments',
      component: () => import('@/views/profile/MyDepartments.vue')
    }
  ]
}
```

---

## 组件清单

| 组件 | 路径 | 说明 |
|------|------|------|
| OrganizationSelector | components/ | 顶部组织选择器 |
| DepartmentSelector | components/ | 部门下拉选择器 |
| DepartmentTree | components/ | 部门树展示组件 |
| MemberPicker | components/ | 成员选择器 |
| OrganizationList | views/organizations/ | 组织列表 |
| DepartmentList | views/organizations/ | 部门列表（树形） |
| MyOrganizations | views/profile/ | 我加入的组织 |
| JoinOrganizationDialog | views/profile/ | 加入组织对话框 |
