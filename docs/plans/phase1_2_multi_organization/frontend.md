# Phase 1.2: 多组织数据隔离 - 前端实现

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
- ✅ 列的显示/隐藏
- ✅ 列的拖拽排序
- ✅ 列宽调整
- ✅ 列固定（左/右）
- ✅ 用户个性化配置保存

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

## 任务概述
实现前端组织切换功能，包括组织选择器、组织上下文管理、跨组织调拨界面等。

## 页面组件

### 1. 组织选择器组件 (OrganizationSelector)

```vue
<!-- frontend/src/components/common/OrganizationSelector.vue -->
<template>
  <el-dropdown trigger="click" @command="handleSwitch">
    <div class="org-selector">
      <el-icon><OfficeBuilding /></el-icon>
      <span class="org-name">{{ currentOrg?.name || '选择组织' }}</span>
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
            <span class="org-name">{{ org.name }}</span>
            <el-tag v-if="org.id === currentOrg?.id" size="small" type="success">当前</el-tag>
          </div>
          <div class="org-role">{{ getRoleName(org.role) }}</div>
        </el-dropdown-item>
        <el-dropdown-item divided :command="'add'">
          <el-icon><Plus /></el-icon>
          加入新组织
        </el-dropdown-item>
      </el-dropdown-menu>
    </template>
  </el-dropdown>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { OfficeBuilding, ArrowDown, Plus } from '@element-plus/icons-vue'
import { switchOrganization, getUserOrganizations } from '@/api/organization'
import { useUserStore } from '@/stores/user'

const userStore = useUserStore()
const organizations = ref([])
const currentOrg = computed(() => userStore.currentOrganization)

const getRoleName = (role) => {
  const roleMap = {
    admin: '管理员',
    member: '成员',
    auditor: '审计员'
  }
  return roleMap[role] || '成员'
}

const loadOrganizations = async () => {
  try {
    const { data } = await getUserOrganizations()
    organizations.value = data.organizations
  } catch (error) {
    ElMessage.error('加载组织列表失败')
  }
}

const handleSwitch = async (orgId) => {
  if (orgId === 'add') {
    // 跳转到加入组织页面
    return
  }

  try {
    await switchOrganization(orgId)
    ElMessage.success('组织切换成功')
    // 刷新页面以重新加载组织上下文数据
    location.reload()
  } catch (error) {
    ElMessage.error('组织切换失败')
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
  display: flex;
  justify-content: space-between;
  align-items: center;
  width: 200px;
}

.org-role {
  font-size: 12px;
  color: var(--el-text-color-secondary);
}

.is-active {
  background-color: var(--el-color-primary-light-9);
}
</style>
```

### 2. 组织切换Pinia Store

```javascript
// frontend/src/stores/user.js

import { defineStore } from 'pinia'
import { switchOrganization, getUserProfile } from '@/api/accounts'

export const useUserStore = defineStore('user', {
  state: () => ({
    token: localStorage.getItem('token'),
    refreshToken: localStorage.getItem('refresh_token'),
    userInfo: null,
    currentOrganization: null,
    organizations: [],
    permissions: []
  }),

  getters: {
    isLoggedIn: (state) => !!state.token,
    isAdmin: (state) => {
      const currentOrg = state.organizations.find(o => o.id === state.currentOrganization?.id)
      return currentOrg?.role === 'admin'
    },
    hasPermission: (state) => (permission) => {
      return state.permissions.includes(permission)
    }
  },

  actions: {
    async switchOrganization(orgId) {
      try {
        const { data } = await switchOrganization(orgId)

        // 更新当前组织
        this.currentOrganization = data.current_organization

        // 更新token（包含新的组织上下文）
        if (data.token) {
          this.token = data.token
          localStorage.setItem('token', data.token)
        }

        // 重新加载用户权限
        await this.loadPermissions()

        return data
      } catch (error) {
        throw error
      }
    },

    async loadPermissions() {
      // 根据当前组织和角色加载权限
      const { data } = await getUserPermissions()
      this.permissions = data.permissions
    }
  }
})
```

### 3. 跨组织调拨页面

```vue
<!-- frontend/src/views/assets/CrossOrgTransfer.vue -->
<template>
  <div class="cross-org-transfer">
    <el-page-header title="跨组织调拨" @back="goBack">
      <template #extra>
        <el-button type="primary" @click="handleSubmit" :loading="submitting">
          提交调拨申请
        </el-button>
      </template>
    </el-page-header>

    <el-form
      ref="formRef"
      :model="formData"
      :rules="formRules"
      label-width="120px"
      class="transfer-form"
    >
      <el-card header="调拨信息" class="form-section">
        <el-form-item label="调入组织" prop="to_organization_id">
          <el-select
            v-model="formData.to_organization_id"
            placeholder="请选择目标组织"
            filterable
            :disabled="!!transferId"
          >
            <el-option
              v-for="org in availableOrganizations"
              :key="org.id"
              :label="org.name"
              :value="org.id"
            />
          </el-select>
        </el-form-item>

        <el-form-item label="预计调拨日期" prop="expected_date">
          <el-date-picker
            v-model="formData.expected_date"
            type="date"
            placeholder="选择日期"
          />
        </el-form-item>

        <el-form-item label="调拨原因" prop="reason">
          <el-input
            v-model="formData.reason"
            type="textarea"
            :rows="3"
            placeholder="请说明调拨原因"
          />
        </el-form-item>
      </el-card>

      <el-card header="调拨资产" class="form-section">
        <div class="asset-selector">
          <el-button type="primary" @click="showAssetPicker = true">
            <el-icon><Plus /></el-icon>
            添加资产
          </el-button>

          <el-tag type="info">已选择 {{ selectedAssets.length }} 项资产</el-tag>
        </div>

        <el-table :data="selectedAssets" border>
          <el-table-column prop="code" label="资产编码" width="150" />
          <el-table-column prop="name" label="资产名称" />
          <el-table-column prop="category" label="分类" width="120" />
          <el-table-column prop="location" label="当前位置" width="120" />
          <el-table-column prop="custodian" label="保管人" width="100" />
          <el-table-column prop="status" label="状态" width="100">
            <template #default="{ row }">
              <el-tag :type="getStatusType(row.status)">
                {{ getStatusText(row.status) }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column label="操作" width="80" fixed="right">
            <template #default="{ $index }">
              <el-button
                link
                type="danger"
                @click="removeAsset($index)"
              >
                移除
              </el-button>
            </template>
          </el-table-column>
        </el-table>
      </el-card>
    </el-form>

    <!-- 资产选择器对话框 -->
    <AssetPickerDialog
      v-model="showAssetPicker"
      :exclude-ids="selectedAssets.map(a => a.id)"
      @confirm="handleAssetsSelected"
    />
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus } from '@element-plus/icons-vue'
import { createCrossOrgTransfer, getTransferDetail, updateTransfer } from '@/api/assets'
import { getAvailableOrganizations } from '@/api/organization'
import AssetPickerDialog from '@/components/assets/AssetPickerDialog.vue'

const router = useRouter()
const route = useRoute()
const transferId = route.params.id

const formRef = ref(null)
const submitting = ref(false)
const showAssetPicker = ref(false)
const availableOrganizations = ref([])
const selectedAssets = ref([])

const formData = reactive({
  to_organization_id: null,
  expected_date: null,
  reason: '',
  asset_ids: []
})

const formRules = {
  to_organization_id: [
    { required: true, message: '请选择调入组织', trigger: 'change' }
  ],
  expected_date: [
    { required: true, message: '请选择预计调拨日期', trigger: 'change' }
  ],
  reason: [
    { required: true, message: '请填写调拨原因', trigger: 'blur' }
  ]
}

const loadAvailableOrganizations = async () => {
  try {
    const { data } = await getAvailableOrganizations()
    // 排除当前组织
    const currentOrgId = useUserStore().currentOrganization?.id
    availableOrganizations.value = data.organizations.filter(o => o.id !== currentOrgId)
  } catch (error) {
    ElMessage.error('加载组织列表失败')
  }
}

const handleAssetsSelected = (assets) => {
  selectedAssets.value = [...selectedAssets.value, ...assets]
}

const removeAsset = (index) => {
  selectedAssets.value.splice(index, 1)
}

const handleSubmit = async () => {
  await formRef.value.validate()

  if (selectedAssets.value.length === 0) {
    ElMessage.warning('请至少选择一项资产')
    return
  }

  submitting.value = true

  try {
    const payload = {
      ...formData,
      asset_ids: selectedAssets.value.map(a => a.id)
    }

    if (transferId) {
      await updateTransfer(transferId, payload)
      ElMessage.success('更新成功')
    } else {
      await createCrossOrgTransfer(payload)
      ElMessage.success('调拨申请已提交，等待对方组织审批')
    }

    router.push('/assets/transfers')
  } catch (error) {
    ElMessage.error('操作失败')
  } finally {
    submitting.value = false
  }
}

const goBack = () => {
  router.back()
}

const getStatusType = (status) => {
  const map = {
    idle: 'info',
    in_use: 'success',
    maintenance: 'warning',
    lost: 'danger'
  }
  return map[status] || 'info'
}

const getStatusText = (status) => {
  const map = {
    idle: '空闲',
    in_use: '在用',
    maintenance: '维修中',
    lost: '已丢失'
  }
  return map[status] || status
}

onMounted(() => {
  loadAvailableOrganizations()

  if (transferId) {
    // 加载已有调拨单数据
    loadTransferDetail(transferId)
  }
})
</script>

<style scoped>
.cross-org-transfer {
  padding: 20px;
}

.transfer-form {
  margin-top: 20px;
}

.form-section {
  margin-bottom: 20px;
}

.asset-selector {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}
</style>
```

### 4. 调拨审批页面

```vue
<!-- frontend/src/views/assets/TransferApproval.vue -->
<template>
  <div class="transfer-approval">
    <el-page-header title="跨组织调拨审批" />

    <el-card class="approval-content" v-loading="loading">
      <template v-if="transfer">
        <!-- 调拨单基本信息 -->
        <el-descriptions :column="2" border class="info-section">
          <el-descriptions-item label="调拨单号">
            {{ transfer.code }}
          </el-descriptions-item>
          <el-descriptions-item label="状态">
            <el-tag :type="getStatusType(transfer.status)">
              {{ getStatusText(transfer.status) }}
            </el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="调出组织">
            {{ transfer.from_organization.name }}
          </el-descriptions-item>
          <el-descriptions-item label="调入组织">
            {{ transfer.to_organization.name }}
          </el-descriptions-item>
          <el-descriptions-item label="申请时间">
            {{ formatDate(transfer.created_at) }}
          </el-descriptions-item>
          <el-descriptions-item label="预计调拨日期">
            {{ formatDate(transfer.expected_date) }}
          </el-descriptions-item>
          <el-descriptions-item label="调拨原因" :span="2">
            {{ transfer.reason }}
          </el-descriptions-item>
        </el-descriptions>

        <!-- 调拨资产列表 -->
        <div class="assets-section">
          <h3>调拨资产清单</h3>
          <el-table :data="transfer.items" border>
            <el-table-column prop="asset.code" label="资产编码" width="150" />
            <el-table-column prop="asset.name" label="资产名称" />
            <el-table-column prop="from_location" label="原位置" width="120" />
            <el-table-column prop="from_custodian" label="原保管人" width="100" />
            <el-table-column prop="to_location" label="目标位置" width="120" />
            <el-table-column prop="to_custodian" label="目标保管人" width="100" />
          </el-table>
        </div>

        <!-- 调入信息填写 -->
        <div v-if="transfer.status === 'pending_approval'" class="action-section">
          <h3>确认调入信息</h3>
          <el-form :model="approvalForm" label-width="120px">
            <el-form-item label="接收位置" required>
              <el-cascader
                v-model="approvalForm.location_id"
                :options="locationTree"
                :props="{ value: 'id', label: 'name' }"
                clearable
              />
            </el-form-item>
            <el-form-item label="接收保管人" required>
              <el-select
                v-model="approvalForm.custodian_id"
                filterable
                remote
                :remote-method="searchUsers"
                :loading="searchingUsers"
              >
                <el-option
                  v-for="user in userOptions"
                  :key="user.id"
                  :label="user.name"
                  :value="user.id"
                />
              </el-select>
            </el-form-item>
          </el-form>
        </div>

        <!-- 审批操作 -->
        <div v-if="transfer.status === 'pending_approval'" class="approval-actions">
          <el-button type="success" @click="handleApprove" :loading="approving">
            <el-icon><Select /></el-icon>
            同意接收
          </el-button>
          <el-button type="danger" @click="handleReject" :loading="approving">
            <el-icon><Close /></el-icon>
            拒绝接收
          </el-button>
        </div>

        <!-- 审批历史 -->
        <div class="history-section">
          <h3>审批历史</h3>
          <el-timeline>
            <el-timeline-item
              v-for="log in transfer.approval_logs"
              :key="log.id"
              :timestamp="formatDateTime(log.created_at)"
            >
              <div>
                <strong>{{ log.approver_name }}</strong>
                <el-tag size="small" :type="log.decision === 'approved' ? 'success' : 'danger'">
                  {{ log.decision === 'approved' ? '同意' : '拒绝' }}
                </el-tag>
              </div>
              <div v-if="log.comment">{{ log.comment }}</div>
            </el-timeline-item>
          </el-timeline>
        </div>
      </template>
    </el-card>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Select, Close } from '@element-plus/icons-vue'
import { getTransferDetail, approveTransfer } from '@/api/assets'
import { getLocationTree } from '@/api/locations'
import { searchUsers } from '@/api/accounts'

const route = useRoute()
const router = useRouter()
const transferId = route.params.id

const loading = ref(false)
const approving = ref(false)
const transfer = ref(null)
const locationTree = ref([])
const userOptions = ref([])
const searchingUsers = ref(false)

const approvalForm = reactive({
  location_id: null,
  custodian_id: null,
  decision: 'approved',
  reason: ''
})

const loadTransferDetail = async () => {
  loading.value = true
  try {
    const { data } = await getTransferDetail(transferId)
    transfer.value = data

    // 预填充目标信息
    if (data.to_location) {
      approvalForm.location_id = data.to_location.path
    }
    if (data.to_custodian) {
      approvalForm.custodian_id = data.to_custodian.id
    }
  } catch (error) {
    ElMessage.error('加载调拨单失败')
  } finally {
    loading.value = false
  }
}

const handleApprove = async () => {
  if (!approvalForm.location_id || !approvalForm.custodian_id) {
    ElMessage.warning('请完善接收信息')
    return
  }

  try {
    await ElMessageBox.confirm('确认接收这些资产吗？', '确认接收', {
      type: 'warning'
    })

    approving.value = true
    await approveTransfer(transferId, {
      ...approvalForm,
      decision: 'approved'
    })

    ElMessage.success('已确认接收，资产已转入本组织')
    router.push('/assets/transfers')
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('操作失败')
    }
  } finally {
    approving.value = false
  }
}

const handleReject = async () => {
  try {
    const { value } = await ElMessageBox.prompt('请输入拒绝原因', '拒绝接收', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      inputPattern: /.+/,
      inputErrorMessage: '请输入拒绝原因'
    })

    approving.value = true
    await approveTransfer(transferId, {
      decision: 'rejected',
      reason: value
    })

    ElMessage.success('已拒绝接收')
    router.push('/assets/transfers')
  } catch (error) {
    // 用户取消
  } finally {
    approving.value = false
  }
}

const getStatusType = (status) => {
  const map = {
    pending_approval: 'warning',
    completed: 'success',
    rejected: 'danger'
  }
  return map[status] || 'info'
}

const getStatusText = (status) => {
  const map = {
    pending_approval: '待审批',
    completed: '已完成',
    rejected: '已拒绝'
  }
  return map[status] || status
}

onMounted(() => {
  loadTransferDetail()
  getLocationTree().then(({ data }) => {
    locationTree.value = data
  })
})
</script>
```

## API集成

```javascript
// frontend/src/api/organization.js

import request from '@/utils/request'

// 获取用户可访问的组织列表
export function getUserOrganizations() {
  return request({
    url: '/api/organizations/user/organizations/',
    method: 'get'
  })
}

// 获取可调拨的组织列表
export function getAvailableOrganizations() {
  return request({
    url: '/api/organizations/available-for-transfer/',
    method: 'get'
  })
}

// 切换当前组织
export function switchOrganization(orgId) {
  return request({
    url: '/api/accounts/switch-organization/',
    method: 'post',
    data: { organization_id: orgId }
  })
}

// 加入新组织
export function joinOrganization(code) {
  return request({
    url: '/api/organizations/join/',
    method: 'post',
    data: { invite_code: code }
  })
}
```

## 路由配置

```javascript
// frontend/src/router/index.js

{
  path: '/assets',
  component: Layout,
  children: [
    {
      path: 'transfer/cross-org',
      name: 'CrossOrgTransfer',
      component: () => import('@/views/assets/CrossOrgTransfer.vue'),
      meta: { title: '跨组织调拨', requiresAuth: true }
    },
    {
      path: 'transfer/approval/:id',
      name: 'TransferApproval',
      component: () => import('@/views/assets/TransferApproval.vue'),
      meta: { title: '调拨审批', requiresAuth: true }
    }
  ]
}
```

## 组件目录结构

```
frontend/src/
├── components/
│   └── common/
│       └── OrganizationSelector.vue    # 组织选择器组件
├── views/
│   └── assets/
│       ├── CrossOrgTransfer.vue        # 跨组织调拨页面
│       └── TransferApproval.vue        # 调拨审批页面
├── stores/
│   └── user.js                         # 用户状态管理
├── api/
│   └── organization.js                 # 组织相关API
└── router/
    └── index.js                        # 路由配置
```

## 实施步骤

1. ✅ 创建组织选择器组件
2. ✅ 实现用户Store组织切换逻辑
3. ✅ 创建跨组织调拨页面
4. ✅ 创建调拨审批页面
5. ✅ 配置API接口
6. ✅ 配置路由

## 输出产物

| 文件 | 说明 |
|------|------|
| `frontend/src/components/common/OrganizationSelector.vue` | 组织选择器 |
| `frontend/src/views/assets/CrossOrgTransfer.vue` | 跨组织调拨页面 |
| `frontend/src/views/assets/TransferApproval.vue` | 调拨审批页面 |
| `frontend/src/stores/user.js` | 用户状态管理 |
| `frontend/src/api/organization.js` | 组织API |
| `frontend/src/router/index.js` | 路由配置 |
