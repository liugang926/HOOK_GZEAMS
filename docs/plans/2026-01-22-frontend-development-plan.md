# GZEAMS Frontend Development Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Build a comprehensive Vue 3 frontend for the GZEAMS fixed asset management system based on the existing backend API (85% complete) and PRD specifications.

**Architecture:**
- **Framework**: Vue 3 with Composition API, TypeScript
- **UI Library**: Element Plus
- **Build Tool**: Vite
- **State Management**: Pinia
- **Routing**: Vue Router
- **Low-code Engine**: Dynamic metadata-driven forms and lists

**Tech Stack:**
- Vue 3.4+, TypeScript 5.0+, Vite 5.0+
- Element Plus, Pinia, Vue Router
- LogicFlow (workflow designer)
- Axios (HTTP client)
- VueI18n (internationalization)

---

## Document Information

| Item | Description |
|------|-------------|
| Plan Version | v1.0 |
| Created | 2026-01-22 |
| Based on | Backend API 85% complete, PRD specifications |
| Estimated Effort | 80-120 developer days |
| Priority Order | Phases 1-6 as numbered below |

---

## Project Completeness Summary (Current State)

| Module | Backend | Frontend | Overall | Priority |
|--------|---------|----------|---------|----------|
| Common (公共基类) | 95% | N/A | 95% | - |
| Organizations (组织架构) | 90% | 20% | 55% | P1 |
| Assets (资产管理) | 95% | 30% | 65% | P1 |
| Inventory (盘点管理) | 85% | 15% | 50% | P2 |
| System/ Metadata (元数据引擎) | 85% | 0% | 40% | P1 |
| Workflows (工作流) | 85% | 0% | 40% | P2 |
| Mobile (移动端) | 70% | 0% | 35% | P3 |
| Integrations (集成) | 70% | 0% | 35% | P4 |
| Notifications (通知) | 55% | 0% | 30% | P3 |
| Leasing (租赁管理) | 75% | 0% | 35% | P2 |
| Insurance (保险管理) | 80% | 0% | 40% | P2 |
| IT Assets (IT资产) | 65% | 0% | 30% | P2 |
| Lifecycle (生命周期) | 70% | 0% | 35% | P2 |
| User Portal (用户门户) | 50% | 0% | 25% | P4 |

**Overall Project: Backend 85%, Frontend 15%, Total 50%**

---

## Phase 1: Foundation & Core Components (Priority 1)

**Estimated Effort:** 15-20 days
**Dependencies:** None
**Deliverables:** Complete frontend foundation with reusable components

### Task 1.1: Project Scaffolding

**Files:**
- Create: `frontend/vite.config.ts`
- Create: `frontend/tsconfig.json`
- Create: `frontend/package.json`
- Create: `frontend/index.html`
- Create: `frontend/src/main.ts`

**Step 1: Initialize Vite project with Vue 3 and TypeScript**

```bash
# In frontend/ directory
npm create vite@latest . -- --template vue-ts
npm install
```

**Step 2: Install core dependencies**

```bash
npm install vue@^3.4.0 vue-router@^4.2.0 pinia@^2.1.0
npm install element-plus@^2.4.0 @element-plus/icons-vue
npm install axios@^1.6.0
npm install @logicflow/core @logicflow/extension
npm install vue-i18n@^9.8.0 dayjs
```

**Step 3: Install dev dependencies**

```bash
npm install -D @types/node sass unplugin-vue-components unplugin-auto-import
```

**Step 4: Configure vite.config.ts**

```typescript
import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import AutoImport from 'unplugin-auto-import/vite'
import Components from 'unplugin-vue-components/vite'
import { ElementPlusResolver } from 'unplugin-vue-components/resolvers'
import { resolve } from 'path'

export default defineConfig({
  plugins: [
    vue(),
    AutoImport({
      resolvers: [ElementPlusResolver()],
      imports: ['vue', 'vue-router', 'pinia'],
      dts: 'src/auto-imports.d.ts'
    }),
    Components({
      resolvers: [ElementPlusResolver()],
      dts: 'src/components.d.ts'
    })
  ],
  resolve: {
    alias: {
      '@': resolve(__dirname, 'src')
    }
  },
  server: {
    port: 5173,
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true
      }
    }
  }
})
```

**Step 5: Commit**

```bash
git add frontend/package.json frontend/vite.config.ts frontend/tsconfig.json frontend/index.html frontend/src/main.ts
git commit -m "feat: initialize Vue 3 + TypeScript + Vite project"
```

---

### Task 1.2: Router & State Management

**Files:**
- Create: `frontend/src/router/index.ts`
- Create: `frontend/src/stores/user.ts`
- Create: `frontend/src/stores/organization.ts`
- Create: `frontend/src/stores/permission.ts`

**Step 1: Create router configuration**

```typescript
// frontend/src/router/index.ts
import { createRouter, createWebHistory, RouteRecordRaw } from 'vue-router'
import { useUserStore } from '@/stores/user'

const routes: RouteRecordRaw[] = [
  {
    path: '/login',
    name: 'Login',
    component: () => import('@/views/auth/Login.vue'),
    meta: { requiresAuth: false }
  },
  {
    path: '/',
    component: () => import('@/layouts/MainLayout.vue'),
    meta: { requiresAuth: true },
    children: [
      {
        path: '',
        redirect: '/dashboard'
      },
      {
        path: 'dashboard',
        name: 'Dashboard',
        component: () => import('@/views/Dashboard.vue'),
        meta: { title: '首页' }
      }
    ]
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

// Navigation guard
router.beforeEach((to, from, next) => {
  const userStore = useUserStore()
  const isAuthenticated = !!userStore.token

  if (to.meta.requiresAuth !== false && !isAuthenticated) {
    next({ name: 'Login', query: { redirect: to.fullPath } })
  } else if (to.name === 'Login' && isAuthenticated) {
    next({ name: 'Dashboard' })
  } else {
    next()
  }
})

export default router
```

**Step 2: Create user store**

```typescript
// frontend/src/stores/user.ts
import { defineStore } from 'pinia'
import { login, logout, getUserInfo } from '@/api/auth'

export const useUserStore = defineStore('user', {
  state: () => ({
    token: localStorage.getItem('access_token') || '',
    userInfo: null as any,
    permissions: [] as string[]
  }),

  actions: {
    async login(credentials: { username: string; password: string }) {
      const res = await login(credentials)
      this.token = res.access_token
      localStorage.setItem('access_token', res.access_token)
      await this.getUserInfo()
    },

    async getUserInfo() {
      const res = await getUserInfo()
      this.userInfo = res.user
      this.permissions = res.permissions || []
    },

    async logout() {
      await logout()
      this.token = ''
      this.userInfo = null
      this.permissions = []
      localStorage.removeItem('access_token')
    }
  }
})
```

**Step 3: Commit**

```bash
git add frontend/src/router frontend/src/stores
git commit -m "feat: add router and state management with Pinia"
```

---

### Task 1.3: Request Interceptor & Error Handler

**Files:**
- Create: `frontend/src/utils/request.ts`
- Create: `frontend/src/plugins/errorHandler.ts`

**Step 1: Create axios instance with interceptors**

```typescript
// frontend/src/utils/request.ts
import axios, { AxiosError } from 'axios'
import { ElMessage } from 'element-plus'
import router from '@/router'

const request = axios.create({
  baseURL: '/api',
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json'
  }
})

// Request interceptor
request.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('access_token')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    const orgId = localStorage.getItem('current_org_id')
    if (orgId) {
      config.headers['X-Organization-ID'] = orgId
    }
    return config
  },
  (error) => Promise.reject(error)
)

// Response interceptor
request.interceptors.response.use(
  (response) => {
    const res = response.data
    // Handle standard API response format
    if (res.success === false) {
      ElMessage.error(res.error?.message || 'Request failed')
      return Promise.reject(new Error(res.error?.message || 'Error'))
    }
    return res.data || res
  },
  (error: AxiosError) => {
    const status = error.response?.status
    const messages: Record<number, string> = {
      401: '登录已过期，请重新登录',
      403: '权限不足',
      404: '请求的资源不存在',
      410: '资源已被删除',
      429: '请求过于频繁，请稍后再试',
      500: '服务器错误，请稍后再试'
    }

    const message = messages[status || 500] || '网络异常，请稍后重试'

    if (status === 401) {
      localStorage.removeItem('access_token')
      router.push({ name: 'Login', query: { redirect: router.currentRoute.value.fullPath } })
    }

    ElMessage.error(message)
    return Promise.reject(error)
  }
)

export default request
```

**Step 2: Commit**

```bash
git add frontend/src/utils/request.ts frontend/src/plugins/errorHandler.ts
git commit -m "feat: add request interceptor and error handler"
```

---

### Task 1.4: Base Common Components

**Files:**
- Create: `frontend/src/components/common/BaseListPage.vue`
- Create: `frontend/src/components/common/BaseFormPage.vue`
- Create: `frontend/src/components/common/BaseDetailPage.vue`
- Create: `frontend/src/components/common/BaseTable.vue`
- Create: `frontend/src/components/common/BaseSearchBar.vue`
- Create: `frontend/src/components/common/BasePagination.vue`
- Create: `frontend/src/components/common/BaseAuditInfo.vue`

**Step 1: Create BaseListPage component**

```vue
<!-- frontend/src/components/common/BaseListPage.vue -->
<template>
  <div class="base-list-page">
    <el-card shadow="never">
      <!-- Page Header -->
      <template #header>
        <div class="page-header">
          <span class="page-title">{{ title }}</span>
          <div class="page-actions">
            <el-button
              v-if="showCreate"
              type="primary"
              :icon="Plus"
              @click="handleCreate"
            >
              新建
            </el-button>
          </div>
        </div>
      </template>

      <!-- Search Bar -->
      <BaseSearchBar
        v-if="searchFields.length || filterFields.length"
        :search-fields="searchFields"
        :filter-fields="filterFields"
        @search="handleSearch"
        @reset="handleReset"
      />

      <!-- Batch Actions -->
      <div v-if="showBatchDelete && selectedRows.length > 0" class="batch-bar">
        <span class="selected-count">已选择 {{ selectedRows.length }} 项</span>
        <el-button type="danger" size="small" @click="handleBatchDelete">
          批量删除
        </el-button>
      </div>

      <!-- Table -->
      <BaseTable
        :data="tableData"
        :columns="columns"
        :loading="loading"
        :selection-enabled="showBatchDelete"
        @selection-change="handleSelectionChange"
        @row-click="handleRowClick"
      >
        <template v-for="slot in customSlots" #[slot]="scope">
          <slot :name="slot" v-bind="scope" />
        </template>
      </BaseTable>

      <!-- Pagination -->
      <BasePagination
        v-model:page="currentPage"
        v-model:page-size="pageSize"
        :total="total"
        @change="handlePageChange"
      />
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { Plus } from '@element-plus/icons-vue'
import BaseSearchBar from './BaseSearchBar.vue'
import BaseTable from './BaseTable.vue'
import BasePagination from './BasePagination.vue'

interface Props {
  title: string
  fetchMethod: (params: any) => Promise<any>
  deleteMethod?: (id: string) => Promise<void>
  batchDeleteMethod?: (ids: string[]) => Promise<void>
  columns: any[]
  searchFields?: any[]
  filterFields?: any[]
  showCreate?: boolean
  showBatchDelete?: boolean
  customSlots?: string[]
}

const props = withDefaults(defineProps<Props>(), {
  searchFields: () => [],
  filterFields: () => [],
  showCreate: true,
  showBatchDelete: true,
  customSlots: () => []
})

const emit = defineEmits(['create', 'refresh', 'row-click'])

const loading = ref(false)
const tableData = ref([])
const total = ref(0)
const currentPage = ref(1)
const pageSize = ref(20)
const selectedRows = ref<any[]>([])
const searchParams = ref({})

const loadData = async () => {
  loading.value = true
  try {
    const res = await props.fetchMethod({
      page: currentPage.value,
      page_size: pageSize.value,
      ...searchParams.value
    })
    tableData.value = res.results || res.data || []
    total.value = res.count || res.total || 0
  } finally {
    loading.value = false
  }
}

const handleSearch = (params: any) => {
  searchParams.value = params
  currentPage.value = 1
  loadData()
}

const handleReset = () => {
  searchParams.value = {}
  currentPage.value = 1
  loadData()
}

const handlePageChange = () => {
  loadData()
}

const handleCreate = () => emit('create')

const handleRowClick = (row: any) => emit('row-click', row)

const handleSelectionChange = (selection: any[]) => {
  selectedRows.value = selection
}

const handleBatchDelete = async () => {
  if (props.batchDeleteMethod) {
    const ids = selectedRows.value.map(r => r.id)
    await props.batchDeleteMethod(ids)
    loadData()
  }
}

onMounted(loadData)

defineExpose({ refresh: loadData })
</script>

<style scoped>
.base-list-page {
  padding: 20px;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.page-title {
  font-size: 18px;
  font-weight: 500;
}

.batch-bar {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 12px;
  padding: 8px 12px;
  background: #f0f9ff;
  border-radius: 4px;
}

.selected-count {
  font-size: 14px;
  color: #606266;
}
</style>
```

**Step 2: Create BaseFormPage component**

```vue
<!-- frontend/src/components/common/BaseFormPage.vue -->
<template>
  <div class="base-form-page">
    <el-card shadow="never">
      <template #header>
        <span class="page-title">{{ title }}</span>
      </template>

      <el-form
        ref="formRef"
        :model="formData"
        :rules="formRules"
        :label-width="labelWidth"
        :label-position="labelPosition"
      >
        <slot name="default" :data="formData"></slot>
      </el-form>

      <div class="form-actions">
        <el-button @click="handleCancel">取消</el-button>
        <el-button type="primary" :loading="submitting" @click="handleSubmit">
          {{ submitText }}
        </el-button>
      </div>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, watch } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import type { FormInstance, FormRules } from 'element-plus'

interface Props {
  title: string
  submitMethod: (data: any) => Promise<any>
  initialData?: Record<string, any>
  rules?: FormRules
  submitText?: string
  labelWidth?: string
  labelPosition?: 'left' | 'right' | 'top'
  redirectPath?: string
}

const props = withDefaults(defineProps<Props>(), {
  initialData: () => ({}),
  rules: () => ({}),
  submitText: '提交',
  labelWidth: '120px',
  labelPosition: 'right',
  redirectPath: ''
})

const emit = defineEmits(['submit-success', 'cancel'])

const router = useRouter()
const formRef = ref<FormInstance>()
const formData = reactive({ ...props.initialData })
const formRules = reactive(props.rules)
const submitting = ref(false)

// Watch for initialData changes
watch(() => props.initialData, (newVal) => {
  Object.assign(formData, newVal)
}, { deep: true })

const handleSubmit = async () => {
  const valid = await formRef.value?.validate().catch(() => false)
  if (!valid) return

  submitting.value = true
  try {
    await props.submitMethod(formData)
    ElMessage.success('操作成功')
    emit('submit-success', formData)
    if (props.redirectPath) {
      router.push(props.redirectPath)
    }
  } finally {
    submitting.value = false
  }
}

const handleCancel = () => {
  emit('cancel')
  if (props.redirectPath) {
    router.push(props.redirectPath)
  } else {
    router.back()
  }
}

defineExpose({ formRef, formData, validate: () => formRef.value?.validate() })
</script>

<style scoped>
.base-form-page {
  padding: 20px;
}

.page-title {
  font-size: 18px;
  font-weight: 500;
}

.form-actions {
  display: flex;
  justify-content: center;
  gap: 12px;
  margin-top: 24px;
}
</style>
```

**Step 3: Commit**

```bash
git add frontend/src/components/common/
git commit -m "feat: add BaseListPage, BaseFormPage, BaseDetailPage components"
```

---

### Task 1.5: Authentication & Main Layout

**Files:**
- Create: `frontend/src/views/auth/Login.vue`
- Create: `frontend/src/layouts/MainLayout.vue`
- Create: `frontend/src/api/auth.ts`

**Step 1: Create Login page**

```vue
<!-- frontend/src/views/auth/Login.vue -->
<template>
  <div class="login-page">
    <el-card class="login-card">
      <template #header>
        <div class="login-header">
          <h1>GZEAMS</h1>
          <p>固定资产管理系统</p>
        </div>
      </template>

      <el-form
        ref="formRef"
        :model="loginForm"
        :rules="loginRules"
        size="large"
        @submit.prevent="handleLogin"
      >
        <el-form-item prop="username">
          <el-input
            v-model="loginForm.username"
            placeholder="用户名"
            :prefix-icon="User"
          />
        </el-form-item>

        <el-form-item prop="password">
          <el-input
            v-model="loginForm.password"
            type="password"
            placeholder="密码"
            :prefix-icon="Lock"
            show-password
            @keyup.enter="handleLogin"
          />
        </el-form-item>

        <el-form-item>
          <el-button
            type="primary"
            :loading="loading"
            style="width: 100%"
            @click="handleLogin"
          >
            登录
          </el-button>
        </el-form-item>
      </el-form>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { reactive, ref } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { User, Lock } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import { useUserStore } from '@/stores/user'
import type { FormInstance, FormRules } from 'element-plus'

const router = useRouter()
const route = useRoute()
const userStore = useUserStore()

const formRef = ref<FormInstance>()
const loading = ref(false)

const loginForm = reactive({
  username: '',
  password: ''
})

const loginRules: FormRules = {
  username: [{ required: true, message: '请输入用户名', trigger: 'blur' }],
  password: [{ required: true, message: '请输入密码', trigger: 'blur' }]
}

const handleLogin = async () => {
  const valid = await formRef.value?.validate().catch(() => false)
  if (!valid) return

  loading.value = true
  try {
    await userStore.login(loginForm)
    ElMessage.success('登录成功')
    const redirect = route.query.redirect as string || '/dashboard'
    router.push(redirect)
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.login-page {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 100vh;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}

.login-card {
  width: 400px;
}

.login-header {
  text-align: center;
}

.login-header h1 {
  margin: 0;
  font-size: 28px;
  color: #333;
}

.login-header p {
  margin: 8px 0 0;
  color: #666;
}
</style>
```

**Step 2: Commit**

```bash
git add frontend/src/views/auth/Login.vue frontend/src/layouts/MainLayout.vue frontend/src/api/auth.ts
git commit -m "feat: add login page and main layout"
```

---

## Phase 2: Low-Code Metadata Engine (Priority 1)

**Estimated Effort:** 20-25 days
**Dependencies:** Phase 1
**Deliverables:** Dynamic form, list, and metadata management UI

### Task 2.1: Dynamic Form Component

**Files:**
- Create: `frontend/src/components/engine/DynamicForm.vue`
- Create: `frontend/src/components/engine/FieldRenderer.vue`
- Create: `frontend/src/components/engine/fields/TextField.vue`
- Create: `frontend/src/components/engine/fields/NumberField.vue`
- Create: `frontend/src/components/engine/fields/DateField.vue`
- Create: `frontend/src/components/engine/fields/SelectField.vue`
- Create: `frontend/src/components/engine/fields/UserField.vue`
- Create: `frontend/src/components/engine/fields/DeptField.vue`
- Create: `frontend/src/components/engine/fields/ReferenceField.vue`
- Create: `frontend/src/components/engine/fields/FormulaField.vue`
- Create: `frontend/src/components/engine/fields/SubTableField.vue`

**Step 1: Create useDynamicForm hook**

```typescript
// frontend/src/components/engine/hooks/useDynamicForm.ts
import { ref, reactive } from 'vue'
import { getFieldDefinitions, getPageLayout } from '@/api/metadata'

export function useDynamicForm(businessObject: string, layoutCode = 'form') {
  const formRef = ref()
  const formData = reactive({})
  const formRules = reactive({})
  const fieldDefinitions = ref<any[]>([])
  const layoutSections = ref<any[]>([])
  const loading = ref(false)

  const loadMetadata = async () => {
    loading.value = true
    try {
      const [fieldsRes, layoutRes] = await Promise.all([
        getFieldDefinitions(businessObject),
        getPageLayout(businessObject, layoutCode)
      ])

      fieldDefinitions.value = fieldsRes.fields || []
      layoutSections.value = parseLayoutConfig(layoutRes.layout_config)
      Object.assign(formRules, buildFormRules(fieldDefinitions.value))
      initFormData(fieldDefinitions.value)
    } finally {
      loading.value = false
    }
  }

  const parseLayoutConfig = (config: any) => {
    if (!config) {
      return [{
        id: 'default',
        title: '',
        columns: 1,
        fields: fieldDefinitions.value.map((f: any) => f.code),
        visible: true
      }]
    }
    return (config.sections || []).map((section: any) => ({
      ...section,
      visible: true,
      collapsed: false
    }))
  }

  const initFormData = (fields: any[]) => {
    fields.forEach(field => {
      if (!(field.code in formData)) {
        if (field.default_value !== undefined && field.default_value !== null) {
          formData[field.code] = parseDefaultValue(field.default_value)
        } else if (field.field_type === 'select') {
          formData[field.code] = field.multiple ? [] : ''
        } else if (field.field_type === 'number') {
          formData[field.code] = 0
        } else if (field.field_type === 'sub_table') {
          formData[field.code] = []
        } else {
          formData[field.code] = ''
        }
      }
    })
  }

  const parseDefaultValue = (value: any) => {
    if (typeof value !== 'string') return value

    const variables: Record<string, any> = {
      '{current_user}': () => JSON.parse(localStorage.getItem('user_info') || '{}').id,
      '{current_user.name}': () => JSON.parse(localStorage.getItem('user_info') || '{}').name,
      '{today}': () => new Date().toISOString().split('T')[0],
      '{now}': () => new Date().toISOString()
    }

    for (const [key, getter] of Object.entries(variables)) {
      if (value.includes(key)) {
        return value.replace(key, getter())
      }
    }
    return value
  }

  const buildFormRules = (fields: any[]) => {
    const rules: any = {}
    fields.forEach(field => {
      if (field.is_required) {
        rules[field.code] = [
          { required: true, message: `请输入${field.name}`, trigger: 'blur' }
        ]
      }
    })
    return rules
  }

  const validate = () => formRef.value?.validate()

  const resetFields = () => {
    formRef.value?.resetFields()
    Object.keys(formData).forEach(key => delete formData[key])
    initFormData(fieldDefinitions.value)
  }

  return {
    formRef,
    formData,
    formRules,
    fieldDefinitions,
    layoutSections,
    loading,
    loadMetadata,
    validate,
    resetFields
  }
}
```

**Step 2: Create DynamicForm component**

```vue
<!-- frontend/src/components/engine/DynamicForm.vue -->
<template>
  <div v-loading="loading" class="dynamic-form">
    <el-form
      ref="formRef"
      :model="formData"
      :rules="formRules"
      :label-width="labelWidth"
      :label-position="labelPosition"
    >
      <template v-for="section in layoutSections" :key="section.id">
        <el-card v-if="section.visible !== false" class="form-section" :shadow="never">
          <template v-if="section.title" #header>
            <span>{{ section.title }}</span>
          </template>

          <el-row :gutter="20">
            <el-col
              v-for="field in getSectionFields(section)"
              :key="field.code"
              :span="field.colspan || 24"
              v-show="isFieldVisible(field)"
            >
              <el-form-item
                :label="field.name"
                :prop="field.code"
                :required="field.is_required"
              >
                <!-- Read-only field -->
                <template v-if="isFieldReadonly(field)">
                  <span class="readonly-value">{{ formData[field.code] }}</span>
                </template>

                <!-- Editable field -->
                <FieldRenderer
                  v-else
                  :field="field"
                  :model-value="formData[field.code]"
                  @update:model-value="handleFieldValueChange(field.code, $event)"
                />
              </el-form-item>
            </el-col>
          </el-row>
        </el-card>
      </template>
    </el-form>
  </div>
</template>

<script setup lang="ts">
import { onMounted, computed } from 'vue'
import { useDynamicForm } from './hooks/useDynamicForm'
import { useFieldPermissions } from './hooks/useFieldPermissions'
import FieldRenderer from './FieldRenderer.vue'

interface Props {
  businessObject: string
  layoutCode?: string
  modelValue?: Record<string, any>
  fieldPermissions?: Record<string, string>
  labelWidth?: string
  labelPosition?: 'left' | 'right' | 'top'
}

const props = withDefaults(defineProps<Props>(), {
  layoutCode: 'form',
  modelValue: () => ({}),
  fieldPermissions: () => ({}),
  labelWidth: '120px',
  labelPosition: 'right'
})

const emit = defineEmits(['update:modelValue', 'change'])

const {
  formRef,
  formData,
  formRules,
  fieldDefinitions,
  layoutSections,
  loading,
  loadMetadata,
  validate,
  resetFields
} = useDynamicForm(props.businessObject, props.layoutCode)

const {
  isFieldReadonly,
  isFieldVisible
} = useFieldPermissions(props.fieldPermissions, fieldDefinitions)

onMounted(async () => {
  await loadMetadata()
  if (props.modelValue && Object.keys(props.modelValue).length > 0) {
    Object.assign(formData, props.modelValue)
  }
})

const handleFieldValueChange = (fieldCode: string, value: any) => {
  formData[fieldCode] = value
  emit('update:modelValue', { ...formData })
  emit('change', { fieldCode, value })
}

const getSectionFields = (section: any) => {
  const fieldCodes = section.fields || []
  return fieldDefinitions.value.filter(f => fieldCodes.includes(f.code))
}

defineExpose({ validate, resetFields, getFormData: () => formData })
</script>

<style scoped>
.dynamic-form {
  width: 100%;
}

.form-section {
  margin-bottom: 20px;
}

.form-section:last-child {
  margin-bottom: 0;
}

.readonly-value {
  color: #606266;
}
</style>
```

**Step 3: Commit**

```bash
git add frontend/src/components/engine/
git commit -m "feat: add DynamicForm component with field rendering"
```

---

### Task 2.2: Metadata Management UI

**Files:**
- Create: `frontend/src/views/system/BusinessObjectList.vue`
- Create: `frontend/src/views/system/BusinessObjectForm.vue`
- Create: `frontend/src/views/system/FieldDefinitionList.vue`
- Create: `frontend/src/views/system/FieldDefinitionForm.vue`
- Create: `frontend/src/views/system/PageLayoutList.vue`
- Create: `frontend/src/views/system/PageLayoutDesigner.vue`

**Step 1: Create BusinessObjectList page**

```vue
<!-- frontend/src/views/system/BusinessObjectList.vue -->
<template>
  <BaseListPage
    title="业务对象"
    :fetch-method="fetchObjects"
    :columns="columns"
    :search-fields="searchFields"
    @create="handleCreate"
    @row-click="handleRowClick"
  >
    <template #actions="{ row }">
      <el-button link type="primary" @click.stop="handleEditFields(row)">
        字段管理
      </el-button>
      <el-button link type="primary" @click.stop="handleEditLayout(row)">
        布局配置
      </el-button>
    </template>
  </BaseListPage>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import BaseListPage from '@/components/common/BaseListPage.vue'
import { getBusinessObjects } from '@/api/system'

const router = useRouter()

const columns = [
  { prop: 'code', label: '对象编码', width: 180 },
  { prop: 'name', label: '对象名称', width: 200 },
  { prop: 'table_name', label: '数据表', width: 180 },
  { prop: 'description', label: '描述', minWidth: 200 },
  { prop: 'is_enabled', label: '状态', width: 100, tag: true }
]

const searchFields = [
  { prop: 'keyword', label: '搜索', placeholder: '编码/名称' }
]

const fetchObjects = (params: any) => getBusinessObjects(params)

const handleCreate = () => router.push({ name: 'BusinessObjectCreate' })
const handleRowClick = (row: any) => router.push({ name: 'BusinessObjectEdit', params: { id: row.id } })
const handleEditFields = (row: any) => router.push({ name: 'FieldDefinitionList', query: { object: row.code } })
const handleEditLayout = (row: any) => router.push({ name: 'PageLayoutList', query: { object: row.code } })
</script>
```

**Step 2: Commit**

```bash
git add frontend/src/views/system/
git commit -m "feat: add metadata management pages"
```

---

## Phase 3: Visual Workflow Designer (Priority 2)

**Estimated Effort:** 12-15 days
**Dependencies:** Phase 1, Phase 2
**Deliverables:** LogicFlow-based workflow designer UI

### Task 3.1: Workflow Designer Component

**Files:**
- Create: `frontend/src/components/workflow/WorkflowDesigner.vue`
- Create: `frontend/src/components/workflow/ApprovalNodeConfig.vue`
- Create: `frontend/src/components/workflow/ConditionNodeConfig.vue`
- Create: `frontend/src/components/workflow/FieldPermissionConfig.vue`
- Create: `frontend/src/components/workflow/ApproverSelector.vue`

**Reference:** See `docs/plans/phase3_1_logicflow/frontend.md` for complete implementation.

**Step 1: Install LogicFlow**

```bash
npm install @logicflow/core @logicflow/extension
```

**Step 2: Create WorkflowDesigner component**

```vue
<!-- frontend/src/components/workflow/WorkflowDesigner.vue -->
<template>
  <div class="workflow-designer">
    <!-- Toolbar -->
    <div class="toolbar">
      <el-button-group>
        <el-button :icon="ZoomOut" @click="handleZoomOut" />
        <el-button @click="handleZoomReset">100%</el-button>
        <el-button :icon="ZoomIn" @click="handleZoomIn" />
      </el-button-group>
      <el-divider direction="vertical" />
      <el-button :icon="Download" @click="handleExport">导出JSON</el-button>
      <el-button :icon="Upload" @click="handleImport">导入JSON</el-button>
      <el-divider direction="vertical" />
      <el-button type="primary" @click="handleSave">保存流程</el-button>
    </div>

    <!-- Node Panel -->
    <div class="node-panel">
      <div class="panel-section">
        <div class="section-title">基础节点</div>
        <div class="node-item" data-type="start">
          <div class="node-icon start">开始</div>
        </div>
        <div class="node-item" data-type="end">
          <div class="node-icon end">结束</div>
        </div>
      </div>
      <div class="panel-section">
        <div class="section-title">审批节点</div>
        <div class="node-item" data-type="approval">
          <div class="node-icon approval">审批</div>
        </div>
        <div class="node-item" data-type="condition">
          <div class="node-icon condition">条件</div>
        </div>
      </div>
    </div>

    <!-- Canvas -->
    <div ref="containerRef" class="canvas-container"></div>

    <!-- Property Panel -->
    <div v-if="selectedNode" class="property-panel">
      <el-tabs v-model="activeTab">
        <el-tab-pane label="基础属性" name="basic">
          <el-form :model="selectedNode" label-width="80px">
            <el-form-item label="节点名称">
              <el-input v-model="selectedNode.text" />
            </el-form-item>
          </el-form>
        </el-tab-pane>
        <el-tab-pane v-if="selectedNode.type === 'approval'" label="审批配置" name="approval">
          <ApprovalNodeConfig v-model="selectedNode.properties" />
        </el-tab-pane>
        <el-tab-pane v-if="selectedNode.type === 'condition'" label="条件配置" name="condition">
          <ConditionNodeConfig v-model="selectedNode.properties" />
        </el-tab-pane>
      </el-tabs>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue'
import LogicFlow from '@logicflow/core'
import { DndPanel, Menu } from '@logicflow/extension'
import '@logicflow/core/dist/style/index.css'
import '@logicflow/extension/lib/style/index.css'
import { ZoomIn, ZoomOut, Download, Upload } from '@element-plus/icons-vue'
import ApprovalNodeConfig from './ApprovalNodeConfig.vue'
import ConditionNodeConfig from './ConditionNodeConfig.vue'

interface Props {
  modelValue?: any
  businessObject?: string
  readonly?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  readonly: false
})

const emit = defineEmits(['update:modelValue', 'save'])

const containerRef = ref<HTMLElement>()
const lf = ref<LogicFlow>()
const selectedNode = ref<any>(null)
const activeTab = ref('basic')

onMounted(() => {
  initLogicFlow()
})

onUnmounted(() => {
  lf.value?.destroy()
})

const initLogicFlow = () => {
  if (!containerRef.value) return

  lf.value = new LogicFlow({
    container: containerRef.value,
    width: containerRef.value.clientWidth,
    height: 800,
    plugins: [DndPanel, Menu],
    grid: { size: 20, type: 'dot', visible: true }
  })

  // Register custom nodes
  registerCustomNodes()
}

const registerCustomNodes = () => {
  // Custom node registration here
}

const handleZoomIn = () => lf.value?.zoom(true)
const handleZoomOut = () => lf.value?.zoom(false)
const handleZoomReset = () => lf.value?.resetZoom()
const handleExport = () => {
  const data = lf.value?.getGraphData()
  const json = JSON.stringify(data, null, 2)
  const blob = new Blob([json], { type: 'application/json' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = `workflow_${Date.now()}.json`
  a.click()
}
const handleImport = () => {}
const handleSave = () => {
  const data = lf.value?.getGraphData()
  emit('save', data)
}
</script>

<style scoped>
.workflow-designer {
  display: flex;
  flex-direction: column;
  height: 100%;
  background: #f5f5f5;
}

.toolbar {
  display: flex;
  align-items: center;
  padding: 10px 15px;
  background: #fff;
  border-bottom: 1px solid #ddd;
  gap: 10px;
}

.node-panel {
  position: absolute;
  left: 20px;
  top: 70px;
  width: 160px;
  background: #fff;
  border-radius: 4px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  padding: 15px;
  z-index: 100;
}

.node-icon {
  padding: 10px 16px;
  text-align: center;
  border-radius: 4px;
  color: #fff;
  cursor: grab;
  margin-bottom: 8px;
}

.node-icon.start { background: #67C23A; }
.node-icon.end { background: #F56C6C; }
.node-icon.approval { background: #409EFF; }
.node-icon.condition { background: #E6A23C; }

.canvas-container {
  flex: 1;
  margin: 70px 330px 20px 180px;
  background: #fff;
  border-radius: 4px;
}

.property-panel {
  position: absolute;
  right: 20px;
  top: 70px;
  width: 320px;
  background: #fff;
  border-radius: 4px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  z-index: 100;
  max-height: calc(100vh - 100px);
}
</style>
```

**Step 3: Commit**

```bash
git add frontend/src/components/workflow/
git commit -m "feat: add workflow designer with LogicFlow"
```

---

## Phase 4: Business Module Frontends (Priority 2)

**Estimated Effort:** 20-25 days
**Dependencies:** Phase 1, Phase 2
**Deliverables:** Complete UI for Assets, Inventory, Leasing, Insurance, IT Assets

### Task 4.1: Assets Module Frontend

**Files:**
- Create: `frontend/src/views/assets/AssetList.vue`
- Create: `frontend/src/views/assets/AssetForm.vue`
- Create: `frontend/src/views/assets/AssetDetail.vue`
- Create: `frontend/src/views/assets/CategoryList.vue`
- Create: `frontend/src/api/assets.ts`

**Step 1: Create AssetList page**

```vue
<!-- frontend/src/views/assets/AssetList.vue -->
<template>
  <BaseListPage
    title="资产列表"
    :fetch-method="fetchAssets"
    :columns="columns"
    :search-fields="searchFields"
    :filter-fields="filterFields"
    :custom-slots="['status', 'actions']"
    @row-click="handleRowClick"
  >
    <template #status="{ row }">
      <el-tag :type="getStatusType(row.asset_status)">
        {{ getStatusLabel(row.asset_status) }}
      </el-tag>
    </template>

    <template #actions="{ row }">
      <el-button link type="primary" @click.stop="handleEdit(row)">编辑</el-button>
      <el-button link type="primary" @click.stop="handleQRCode(row)">二维码</el-button>
    </template>
  </BaseListPage>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import BaseListPage from '@/components/common/BaseListPage.vue'
import { getAssetList } from '@/api/assets'

const router = useRouter()

const columns = [
  { prop: 'asset_code', label: '资产编码', width: 150, fixed: 'left' },
  { prop: 'asset_name', label: '资产名称', minWidth: 200 },
  { prop: 'asset_category', label: '分类', width: 120, formatter: (r: any) => r.asset_category?.name },
  { prop: 'asset_status', label: '状态', width: 100, slot: true },
  { prop: 'location', label: '存放位置', width: 150, formatter: (r: any) => r.location?.name },
  { prop: 'custodian', label: '保管人', width: 120, formatter: (r: any) => r.custodian?.username },
  { prop: 'original_value', label: '原值', width: 120, align: 'right' },
  { prop: 'created_at', label: '创建时间', width: 180 }
]

const searchFields = [
  { prop: 'keyword', label: '搜索', placeholder: '编码/名称/序列号' }
]

const filterFields = [
  { prop: 'asset_status', label: '状态', type: 'select', options: [
    { value: 'idle', label: '闲置' },
    { value: 'in_use', label: '在用' },
    { value: 'maintenance', label: '维修中' },
    { value: 'scrapped', label: '已报废' }
  ]},
  { prop: 'asset_category', label: '分类', type: 'select', options: [] }
]

const fetchAssets = (params: any) => getAssetList(params)

const getStatusType = (status: string) => {
  const types: Record<string, any> = {
    idle: 'info',
    in_use: 'success',
    maintenance: 'warning',
    scrapped: 'danger'
  }
  return types[status] || ''
}

const getStatusLabel = (status: string) => {
  const labels: Record<string, string> = {
    idle: '闲置',
    in_use: '在用',
    maintenance: '维修中',
    scrapped: '已报废'
  }
  return labels[status] || status
}

const handleRowClick = (row: any) => router.push({ name: 'AssetDetail', params: { id: row.id } })
const handleEdit = (row: any) => router.push({ name: 'AssetEdit', params: { id: row.id } })
const handleQRCode = (row: any) => window.open(`/api/assets/${row.id}/qr_code/`, '_blank')
</script>
```

**Step 2: Create API module**

```typescript
// frontend/src/api/assets.ts
import request from '@/utils/request'

export const getAssetList = (params: any) => {
  return request.get('/assets/assets/', { params })
}

export const getAssetDetail = (id: string) => {
  return request.get(`/assets/assets/${id}/`)
}

export const createAsset = (data: any) => {
  return request.post('/assets/assets/', data)
}

export const updateAsset = (id: string, data: any) => {
  return request.put(`/assets/assets/${id}/`, data)
}

export const deleteAsset = (id: string) => {
  return request.delete(`/assets/assets/${id}/`)
}

export const batchDeleteAssets = (ids: string[]) => {
  return request.post('/assets/assets/batch-delete/', { ids })
}

export const getAssetStatistics = () => {
  return request.get('/assets/assets/statistics/')
}

export const changeAssetStatus = (id: string, data: any) => {
  return request.post(`/assets/assets/${id}/change-status/`, data)
}
```

**Step 3: Commit**

```bash
git add frontend/src/views/assets/ frontend/src/api/assets.ts
git commit -m "feat: add assets module frontend pages"
```

---

### Task 4.2: Inventory Module Frontend

**Files:**
- Create: `frontend/src/views/inventory/TaskList.vue`
- Create: `frontend/src/views/inventory/TaskForm.vue`
- Create: `frontend/src/views/inventory/ScanPage.vue`
- Create: `frontend/src/views/inventory/Reconciliation.vue`
- Create: `frontend/src/api/inventory.ts`

**Step 1: Create inventory pages**

```vue
<!-- frontend/src/views/inventory/TaskList.vue -->
<template>
  <BaseListPage
    title="盘点任务"
    :fetch-method="fetchTasks"
    :columns="columns"
    :custom-slots="['status', 'actions']"
    @create="handleCreate"
  >
    <template #status="{ row }">
      <el-tag :type="getStatusType(row.status)">
        {{ getStatusLabel(row.status) }}
      </el-tag>
    </template>

    <template #actions="{ row }">
      <el-button link type="primary" @click.stop="handleScan(row)">扫码盘点</el-button>
      <el-button link type="primary" @click.stop="handleReconcile(row)">盘点核对</el-button>
    </template>
  </BaseListPage>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import BaseListPage from '@/components/common/BaseListPage.vue'
import { getInventoryTasks } from '@/api/inventory'

const router = useRouter()

const columns = [
  { prop: 'task_no', label: '任务编号', width: 180 },
  { prop: 'name', label: '任务名称', minWidth: 200 },
  { prop: 'status', label: '状态', width: 100, slot: true },
  { prop: 'plan_date', label: '计划日期', width: 120 },
  { prop: 'total_assets', label: '资产数量', width: 100 },
  { prop: 'scanned_count', label: '已扫描', width: 100 }
]

const fetchTasks = (params: any) => getInventoryTasks(params)

const getStatusType = (status: string) => {
  const types: Record<string, any> = {
    draft: 'info',
    ongoing: 'warning',
    completed: 'success'
  }
  return types[status] || ''
}

const getStatusLabel = (status: string) => {
  const labels: Record<string, string> = {
    draft: '草稿',
    ongoing: '进行中',
    completed: '已完成'
  }
  return labels[status] || status
}

const handleCreate = () => router.push({ name: 'InventoryTaskCreate' })
const handleScan = (row: any) => router.push({ name: 'InventoryScan', params: { id: row.id } })
const handleReconcile = (row: any) => router.push({ name: 'InventoryReconciliation', params: { id: row.id } })
</script>
```

**Step 2: Commit**

```bash
git add frontend/src/views/inventory/ frontend/src/api/inventory.ts
git commit -m "feat: add inventory module frontend pages"
```

---

### Task 4.3: Other Module Frontends

**Files to create for each module:**
- Leasing: `frontend/src/views/leasing/*`, `frontend/src/api/leasing.ts`
- Insurance: `frontend/src/views/insurance/*`, `frontend/src/api/insurance.ts`
- IT Assets: `frontend/src/views/it-assets/*`, `frontend/src/api/it-assets.ts`
- Lifecycle: `frontend/src/views/lifecycle/*`, `frontend/src/api/lifecycle.ts`
- Consumables: `frontend/src/views/consumables/*`, `frontend/src/api/consumables.ts`

---

## Phase 5: Mobile & Notifications (Priority 3)

**Estimated Effort:** 12-15 days
**Dependencies:** Phase 1, Phase 4
**Deliverables:** Mobile scanning interface and notification management

### Task 5.1: Mobile Scanning Interface

**Files:**
- Create: `frontend/src/views/mobile/ScanPage.vue`
- Create: `frontend/src/views/mobile/AssetDetail.vue`
- Create: `frontend/src/components/mobile/QRScanner.vue`
- Create: `frontend/src/components/mobile/RFIDReader.vue`

**Step 1: Create mobile scan page**

```vue
<!-- frontend/src/views/mobile/ScanPage.vue -->
<template>
  <div class="mobile-scan-page">
    <div class="scan-header">
      <h1>资产盘点</h1>
      <p>扫描二维码或RFID标签</p>
    </div>

    <div class="scan-area">
      <QRScanner @scan="handleQRScan" />
      <el-divider>或</el-divider>
      <RFIDReader @scan="handleRFIDScan" />
    </div>

    <div v-if="lastScannedAsset" class="scanned-result">
      <el-descriptions title="已扫描资产" :column="1" border>
        <el-descriptions-item label="资产编码">
          {{ lastScannedAsset.asset_code }}
        </el-descriptions-item>
        <el-descriptions-item label="资产名称">
          {{ lastScannedAsset.asset_name }}
        </el-descriptions-item>
        <el-descriptions-item label="状态">
          <el-tag :type="getStatusType(lastScannedAsset.asset_status)">
            {{ lastScannedAsset.asset_status }}
          </el-tag>
        </el-descriptions-item>
      </el-descriptions>
    </div>

    <div class="scan-history">
      <h3>扫描记录 ({{ scannedAssets.length }})</h3>
      <el-empty v-if="scannedAssets.length === 0" description="暂无扫描记录" />
      <div v-else class="history-list">
        <div
          v-for="asset in scannedAssets"
          :key="asset.id"
          class="history-item"
          @click="viewAssetDetail(asset)"
        >
          <span class="asset-code">{{ asset.asset_code }}</span>
          <span class="asset-name">{{ asset.asset_name }}</span>
          <el-icon class="arrow"><ArrowRight /></el-icon>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { ArrowRight } from '@element-plus/icons-vue'
import QRScanner from '@/components/mobile/QRScanner.vue'
import RFIDReader from '@/components/mobile/RFIDReader.vue'
import { lookupAsset } from '@/api/assets'

const router = useRouter()
const lastScannedAsset = ref<any>(null)
const scannedAssets = ref<any[]>([])

const handleQRScan = async (qrCode: string) => {
  try {
    const asset = await lookupAsset({ qr_code: qrCode })
    addScannedAsset(asset)
  } catch (error) {
    console.error('Asset not found:', error)
  }
}

const handleRFIDScan = async (rfidCode: string) => {
  try {
    const asset = await lookupAsset({ rfid_code: rfidCode })
    addScannedAsset(asset)
  } catch (error) {
    console.error('Asset not found:', error)
  }
}

const addScannedAsset = (asset: any) => {
  lastScannedAsset.value = asset
  const existing = scannedAssets.value.find(a => a.id === asset.id)
  if (!existing) {
    scannedAssets.value.unshift(asset)
  }
}

const viewAssetDetail = (asset: any) => {
  router.push({ name: 'MobileAssetDetail', params: { id: asset.id } })
}

const getStatusType = (status: string) => {
  const types: Record<string, any> = {
    idle: 'info',
    in_use: 'success',
    maintenance: 'warning'
  }
  return types[status] || ''
}
</script>

<style scoped>
.mobile-scan-page {
  min-height: 100vh;
  padding: 20px;
  background: #f5f5f5;
}

.scan-header {
  text-align: center;
  margin-bottom: 24px;
}

.scan-header h1 {
  margin: 0;
  font-size: 24px;
}

.scan-header p {
  margin: 8px 0 0;
  color: #666;
}

.scan-area {
  background: white;
  border-radius: 8px;
  padding: 20px;
  margin-bottom: 20px;
}

.scanned-result {
  background: white;
  border-radius: 8px;
  padding: 16px;
  margin-bottom: 20px;
}

.scan-history {
  background: white;
  border-radius: 8px;
  padding: 16px;
}

.scan-history h3 {
  margin: 0 0 16px;
  font-size: 16px;
}

.history-item {
  display: flex;
  align-items: center;
  padding: 12px;
  border-bottom: 1px solid #eee;
  cursor: pointer;
}

.history-item:last-child {
  border-bottom: none;
}

.asset-code {
  font-weight: 500;
  margin-right: 12px;
}

.asset-name {
  flex: 1;
  color: #666;
}

.arrow {
  color: #999;
}
</style>
```

**Step 2: Commit**

```bash
git add frontend/src/views/mobile/ frontend/src/components/mobile/
git commit -m "feat: add mobile scanning interface"
```

---

### Task 5.2: Notification Management UI

**Files:**
- Create: `frontend/src/views/notifications/NotificationList.vue`
- Create: `frontend/src/views/notifications/TemplateList.vue`
- Create: `frontend/src/api/notifications.ts`

---

## Phase 6: Integration & Portal (Priority 4)

**Estimated Effort:** 10-15 days
**Dependencies:** Phase 1, Phase 4
**Deliverables:** ERP integration UI and user portal

### Task 6.1: Integration Management UI

**Files:**
- Create: `frontend/src/views/admin/IntegrationList.vue`
- Create: `frontend/src/views/admin/M18Config.vue`
- Create: `frontend/src/api/integration.ts`

### Task 6.2: User Portal

**Files:**
- Create: `frontend/src/views/portal/MyAssets.vue`
- Create: `frontend/src/views/portal/MyRequests.vue`
- Create: `frontend/src/views/portal/PendingApprovals.vue`

---

## Summary of File Structure

```
frontend/
├── src/
│   ├── api/                        # API modules
│   │   ├── auth.ts
│   │   ├── assets.ts
│   │   ├── inventory.ts
│   │   ├── workflows.ts
│   │   ├── system.ts
│   │   ├── notifications.ts
│   │   ├── integration.ts
│   │   └── ...
│   ├── assets/                     # Static assets
│   ├── components/
│   │   ├── common/                 # Base components
│   │   │   ├── BaseListPage.vue
│   │   │   ├── BaseFormPage.vue
│   │   │   ├── BaseDetailPage.vue
│   │   │   ├── BaseTable.vue
│   │   │   ├── BaseSearchBar.vue
│   │   │   ├── BasePagination.vue
│   │   │   └── BaseAuditInfo.vue
│   │   ├── engine/                 # Low-code engine
│   │   │   ├── DynamicForm.vue
│   │   │   ├── FieldRenderer.vue
│   │   │   ├── hooks/
│   │   │   │   ├── useDynamicForm.ts
│   │   │   │   ├── useFieldPermissions.ts
│   │   │   │   └── useFormula.ts
│   │   │   └── fields/
│   │   │       ├── TextField.vue
│   │   │       ├── NumberField.vue
│   │   │       ├── DateField.vue
│   │   │       ├── SelectField.vue
│   │   │       ├── UserField.vue
│   │   │       ├── DeptField.vue
│   │   │       ├── ReferenceField.vue
│   │   │       ├── FormulaField.vue
│   │   │       └── SubTableField.vue
│   │   ├── workflow/               # Workflow components
│   │   │   ├── WorkflowDesigner.vue
│   │   │   ├── ApprovalNodeConfig.vue
│   │   │   ├── ConditionNodeConfig.vue
│   │   │   ├── FieldPermissionConfig.vue
│   │   │   └── ApproverSelector.vue
│   │   └── mobile/                 # Mobile components
│   │       ├── QRScanner.vue
│   │       └── RFIDReader.vue
│   ├── composables/                # Shared composables
│   │   ├── useListPage.ts
│   │   ├── useFormPage.ts
│   │   ├── usePermission.ts
│   │   └── useI18n.ts
│   ├── layouts/
│   │   ├── MainLayout.vue
│   │   └── EmptyLayout.vue
│   ├── router/
│   │   └── index.ts
│   ├── stores/
│   │   ├── user.ts
│   │   ├── organization.ts
│   │   └── permission.ts
│   ├── utils/
│   │   ├── request.ts
│   │   ├── validation.ts
│   │   └── formula.ts
│   ├── views/
│   │   ├── auth/
│   │   │   └── Login.vue
│   │   ├── Dashboard.vue
│   │   ├── assets/
│   │   │   ├── AssetList.vue
│   │   │   ├── AssetForm.vue
│   │   │   ├── AssetDetail.vue
│   │   │   └── CategoryList.vue
│   │   ├── inventory/
│   │   │   ├── TaskList.vue
│   │   │   ├── TaskForm.vue
│   │   │   ├── ScanPage.vue
│   │   │   └── Reconciliation.vue
│   │   ├── workflows/
│   │   │   ├── WorkflowList.vue
│   │   │   └── WorkflowDesigner.vue
│   │   ├── system/
│   │   │   ├── BusinessObjectList.vue
│   │   │   ├── FieldDefinitionList.vue
│   │   │   └── PageLayoutDesigner.vue
│   │   ├── leasing/
│   │   ├── insurance/
│   │   ├── it-assets/
│   │   ├── mobile/
│   │   ├── notifications/
│   │   ├── portal/
│   │   └── admin/
│   ├── App.vue
│   └── main.ts
├── index.html
├── package.json
├── tsconfig.json
├── vite.config.ts
└── ...
```

---

## Execution Notes

### Development Workflow

1. **Setup environment first**
   ```bash
   cd frontend
   npm install
   npm run dev
   ```

2. **Follow phase order**: Phase 1 → Phase 2 → Phase 3 → Phase 4 → Phase 5 → Phase 6

3. **Testing after each task**:
   ```bash
   npm run build
   npm run lint
   ```

4. **Commit frequently** with semantic commit messages

### Key Integration Points

1. **Backend API Base URL**: `http://localhost:8000/api`
2. **Authentication**: JWT Bearer token in Authorization header
3. **Organization Context**: X-Organization-ID header for multi-tenancy
4. **Standard Response Format**: `{ success: true/false, data: {...}, error?: {...} }`

### Component Reusability

All business modules should extend the base components:
- List pages → `BaseListPage`
- Form pages → `BaseFormPage` (or `DynamicForm` for metadata-driven)
- Detail pages → `BaseDetailPage`

---

## Related Documents

| Document | Path |
|----------|------|
| Common Base Features | `docs/plans/common_base_features/00_core/frontend.md` |
| Metadata Engine | `docs/plans/phase1_3_business_metadata/frontend.md` |
| Workflow Designer | `docs/plans/phase3_1_logicflow/frontend.md` |
| PRD Writing Guide | `docs/plans/common_base_features/prd_writing_guide.md` |

---

**Plan complete and saved to `docs/plans/2026-01-22-frontend-development-plan.md`.**
