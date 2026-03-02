# Phase 7.2: 资产项目管理 - 前端实现

## 1. 前端组件结构

```
frontend/src/views/projects/
├── ProjectList.vue           # 项目列表
├── ProjectForm.vue           # 项目表单
├── ProjectDetail.vue         # 项目详情
├── ProjectAssetList.vue      # 项目资产列表
├── ProjectAssetForm.vue      # 资产分配表单
├── ProjectMemberList.vue     # 项目成员管理
├── ProjectCostSummary.vue    # 成本汇总
└── components/
    ├── ProjectCard.vue           # 项目卡片
    ├── AssetAllocationSelector.vue # 资产分配选择器
    ├── AssetAllocationCard.vue    # 分配资产卡片
    ├── CostSummaryCard.vue        # 成本汇总卡片
    └── ProjectProgress.vue        # 项目进度条

frontend/src/api/projects.js    # 项目API
frontend/src/stores/projects.js  # 项目状态管理
```

## 2. 核心页面示例

### 2.1 ProjectList.vue

```vue
<template>
  <BaseListPage
    title="项目管理"
    :columns="columns"
    :data-source="loadProjects"
    :search-fields="searchFields"
  >
    <template #toolbar>
      <el-button type="primary" @click="handleCreate">
        <el-icon><Plus /></el-icon>
        新建项目
      </el-button>
      <el-button @click="handleMyProjects">
        我的项目
      </el-button>
    </template>

    <template #status="{ row }">
      <el-tag :type="getStatusType(row.status)">
        {{ getStatusText(row.status) }}
      </el-tag>
    </template>

    <template #progress="{ row }">
      <el-progress
        :percentage="row.progress"
        :color="getProgressColor(row.progress)"
      />
    </template>

    <template #actions="{ row }">
      <el-button link type="primary" @click="handleView(row)">
        查看
      </el-button>
      <el-dropdown @command="handleCommand($event, row)">
        <el-button link type="primary">
          更多
        </el-button>
        <template #dropdown>
          <el-dropdown-menu>
            <el-dropdown-item command="assets">
              项目资产 ({{ row.asset_count }})
            </el-dropdown-item>
            <el-dropdown-item command="members">
              项目成员 ({{ row.member_count }})
            </el-dropdown-item>
            <el-dropdown-item command="cost">
              成本汇总
            </el-dropdown-item>
            <el-dropdown-item command="close" v-if="row.status === 'active'">
              关闭项目
            </el-dropdown-item>
          </el-dropdown-menu>
        </template>
      </el-dropdown>
    </template>
  </BaseListPage>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { Plus } from '@element-plus/icons-vue'
import BaseListPage from '@/components/common/BaseListPage.vue'
import { getProjects } from '@/api/projects'

const router = useRouter()

const columns = ref([
  { prop: 'project_code', label: '项目编号', width: 140 },
  { prop: 'project_name', label: '项目名称', width: 200 },
  { prop: 'project_type', label: '项目类型', width: 100 },
  { prop: 'project_manager', label: '项目经理', width: 120 },
  { prop: 'start_date', label: '开始日期', width: 110 },
  { prop: 'end_date', label: '结束日期', width: 110 },
  { prop: 'status', label: '状态', width: 100, slot: true },
  { prop: 'progress', label: '进度', width: 150, slot: true },
  { prop: 'active_assets', label: '在用资产', width: 100 },
  { prop: 'asset_cost', label: '资产成本', width: 120 }
])

const searchFields = ref([
  {
    prop: 'status',
    label: '状态',
    type: 'select',
    options: [
      { label: '全部', value: '' },
      { label: '筹备中', value: 'planning' },
      { label: '进行中', value: 'active' },
      { label: '已暂停', value: 'suspended' },
      { label: '已完成', value: 'completed' }
    ]
  },
  {
    prop: 'keyword',
    label: '搜索',
    type: 'input',
    placeholder: '项目编号/名称'
  }
])

const loadProjects = async (params) => {
  const response = await getProjects(params)
  return response.data
}

const getStatusType = (status) => {
  const map = {
    planning: 'info',
    active: 'success',
    suspended: 'warning',
    completed: '',
    cancelled: 'danger'
  }
  return map[status] || ''
}

const getStatusText = (status) => {
  const map = {
    planning: '筹备中',
    active: '进行中',
    suspended: '已暂停',
    completed: '已完成',
    cancelled: '已取消'
  }
  return map[status] || status
}

const getProgressColor = (progress) => {
  if (progress >= 80) return '#67c23a'
  if (progress >= 50) return '#409eff'
  if (progress >= 20) return '#e6a23c'
  return '#f56c6c'
}

const handleCreate = () => {
  router.push({ name: 'ProjectCreate' })
}

const handleMyProjects = () => {
  router.push({ name: 'MyProjects' })
}

const handleView = (row) => {
  router.push({
    name: 'ProjectDetail',
    params: { id: row.id }
  })
}

const handleCommand = (command, row) => {
  const commands = {
    assets: () => router.push({ name: 'ProjectAssets', params: { id: row.id } }),
    members: () => router.push({ name: 'ProjectMembers', params: { id: row.id } }),
    cost: () => router.push({ name: 'ProjectCost', params: { id: row.id } }),
    close: () => handleCloseProject(row)
  }
  commands[command]?.()
}
</script>
```

### 2.2 资产分配表单

```vue
<template>
  <BaseFormPage
    title="分配资产到项目"
    :loading="loading"
    @submit="handleSubmit"
    @cancel="handleCancel"
  >
    <el-form ref="formRef" :model="formData" :rules="rules" label-width="120px">
      <el-form-item label="项目" prop="project_id">
        <el-select v-model="formData.project_id" disabled>
          <el-option
            :label="project.project_name"
            :value="project.id"
          />
        </el-select>
      </el-form-item>

      <el-form-item label="选择资产" prop="assets" required>
        <AssetAllocationSelector
          v-model="formData.assets"
          :organization="currentOrganization"
          :excluded-project-id="project.id"
        />
      </el-form-item>

      <el-form-item label="分配类型" prop="allocation_type">
        <el-radio-group v-model="formData.allocation_type">
          <el-radio label="permanent">永久分配（专用）</el-radio>
          <el-radio label="temporary">临时分配（共享）</el-radio>
          <el-radio label="shared">共享分配</el-radio>
        </el-radio-group>
      </el-form-item>

      <el-form-item label="分配日期" prop="allocation_date">
        <el-date-picker
          v-model="formData.allocation_date"
          type="date"
          value-format="YYYY-MM-DD"
        />
      </el-form-item>

      <el-form-item label="计划归还日期" prop="return_date">
        <el-date-picker
          v-model="formData.return_date"
          type="date"
          value-format="YYYY-MM-DD"
        />
      </el-form-item>

      <el-form-item label="用途说明" prop="purpose">
        <el-input
          v-model="formData.purpose"
          type="textarea"
          :rows="3"
        />
      </el-form-item>

      <el-form-item label="使用地点" prop="usage_location">
        <el-input v-model="formData.usage_location" />
      </el-form-item>

      <!-- 已选资产列表 -->
      <el-form-item label="已选资产">
        <el-table :data="formData.assets" border>
          <el-table-column prop="asset_code" label="资产编号" width="140" />
          <el-table-column prop="asset_name" label="资产名称" />
          <el-table-column prop="category_name" label="分类" width="120" />
          <el-table-column prop="original_cost" label="原值" width="100">
            <template #default="{ row }">
              ¥{{ row.original_cost }}
            </template>
          </el-table-column>
          <el-table-column label="保管人" width="150">
            <template #default="{ row }">
              <UserPicker v-model="row.custodian_id" />
            </template>
          </el-table-column>
          <el-table-column label="操作" width="80">
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
      </el-form-item>
    </el-form>
  </BaseFormPage>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import BaseFormPage from '@/components/common/BaseListPage.vue'
import AssetAllocationSelector from '@/views/projects/components/AssetAllocationSelector.vue'
import UserPicker from '@/components/common/UserPicker.vue'
import { allocateAssetsToProject } from '@/api/projects'

const props = defineProps({
  projectId: {
    type: String,
    required: true
  },
  project: {
    type: Object,
    required: true
  }
})

const router = useRouter()
const formRef = ref(null)
const loading = ref(false)

const formData = ref({
  project_id: props.projectId,
  assets: [],
  allocation_type: 'temporary',
  allocation_date: new Date().toISOString().split('T')[0],
  return_date: '',
  purpose: '',
  usage_location: ''
})

const rules = {
  assets: [
    { required: true, type: 'array', min: 1, message: '请选择至少一项资产' }
  ]
}

const removeAsset = (index) => {
  formData.value.assets.splice(index, 1)
}

const handleSubmit = async () => {
  try {
    await formRef.value.validate()
    loading.value = true

    await allocateAssetsToProject(props.projectId, formData.value)

    ElMessage.success('资产分配成功')
    router.back()
  } catch (error) {
    ElMessage.error(error.message || '分配失败')
  } finally {
    loading.value = false
  }
}

const handleCancel = () => {
  router.back()
}
</script>
```

## 3. API封装

```javascript
// frontend/src/api/projects.js
import request from '@/utils/request'

// 项目列表
export function getProjects(params) {
  return request({
    url: '/projects/',
    method: 'get',
    params
  })
}

// 项目详情
export function getProjectDetail(id) {
  return request({
    url: `/projects/${id}/`,
    method: 'get'
  })
}

// 创建项目
export function createProject(data) {
  return request({
    url: '/projects/',
    method: 'post',
    data
  })
}

// 更新项目
export function updateProject(id, data) {
  return request({
    url: `/projects/${id}/`,
    method: 'put',
    data
  })
}

// 分配资产
export function allocateAssetsToProject(id, data) {
  return request({
    url: `/projects/${id}/allocate-assets/`,
    method: 'post',
    data
  })
}

// 归还资产
export function returnProjectAssets(id, data) {
  return request({
    url: `/projects/${id}/return-assets/`,
    method: 'post',
    data
  })
}

// 获取项目资产
export function getProjectAssets(id, params) {
  return request({
    url: `/projects/${id}/assets/`,
    method: 'get',
    params
  })
}

// 获取项目成员
export function getProjectMembers(id, params) {
  return request({
    url: `/projects/${id}/members/`,
    method: 'get',
    params
  })
}

// 获取成本汇总
export function getProjectCostSummary(id) {
  return request({
    url: `/projects/${id}/cost-summary/`,
    method: 'get'
  })
}

// 关闭项目
export function closeProject(id) {
  return request({
    url: `/projects/${id}/close/`,
    method: 'post'
  })
}

// 我的项目
export function getMyProjects(params) {
  return request({
    url: '/projects/my-projects/',
    method: 'get',
    params
  })
}
```

## 4. 路由配置

```javascript
// frontend/src/router/modules/projects.js
export default {
  path: '/projects',
  name: 'Projects',
  component: () => import('@/layouts/DefaultLayout.vue'),
  meta: { title: '项目管理', icon: 'FolderOpened' },
  children: [
    {
      path: '',
      name: 'ProjectList',
      component: () => import('@/views/projects/ProjectList.vue'),
      meta: { title: '项目列表', cache: true }
    },
    {
      path: 'create',
      name: 'ProjectCreate',
      component: () => import('@/views/projects/ProjectForm.vue'),
      meta: { title: '新建项目', activeMenu: '/projects' }
    },
    {
      path: ':id',
      name: 'ProjectDetail',
      component: () => import('@/views/projects/ProjectDetail.vue'),
      meta: { title: '项目详情', activeMenu: '/projects', cache: true }
    },
    {
      path: ':id/assets',
      name: 'ProjectAssets',
      component: () => import('@/views/projects/ProjectAssetList.vue'),
      meta: { title: '项目资产', activeMenu: '/projects' }
    },
    {
      path: ':id/assets/allocate',
      name: 'ProjectAssetAllocate',
      component: () => import('@/views/projects/ProjectAssetForm.vue'),
      meta: { title: '分配资产', activeMenu: '/projects' }
    },
    {
      path: ':id/members',
      name: 'ProjectMembers',
      component: () => import('@/views/projects/ProjectMemberList.vue'),
      meta: { title: '项目成员', activeMenu: '/projects' }
    },
    {
      path: ':id/cost',
      name: 'ProjectCost',
      component: () => import('@/views/projects/ProjectCostSummary.vue'),
      meta: { title: '成本汇总', activeMenu: '/projects' }
    },
    {
      path: 'my',
      name: 'MyProjects',
      component: () => import('@/views/projects/MyProjects.vue'),
      meta: { title: '我的项目', activeMenu: '/projects' }
    }
  ]
}
```
