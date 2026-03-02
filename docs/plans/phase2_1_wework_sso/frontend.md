# Phase 2.1: 企业微信SSO登录 - 前端实现

## 组件结构

```
src/views/auth/
├── Login.vue                  # 统一登录页面
├── WeWorkLogin.vue            # 企业微信登录页面
├── components/
│   ├── LoginForm.vue          # 账号密码登录表单
│   ├── WeWorkQRCode.vue       # 企业微信二维码
│   └── LoginSwitcher.vue      # 登录方式切换
└── middleware/
    └── auth.ts                # 认证中间件
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

## 1. 统一登录页面

### Login.vue - 统一登录入口

```vue
<template>
  <div class="login-page">
    <div class="login-container">
      <div class="login-header">
        <h1>钩子固定资产管理系统</h1>
        <p>低代码资产管理平台</p>
      </div>

      <el-card class="login-card" shadow="always">
        <!-- 登录方式切换 -->
        <div class="login-tabs">
          <el-radio-group v-model="loginType" size="large">
            <el-radio-button label="password">账号登录</el-radio-button>
            <el-radio-button label="wework">企业微信</el-radio-button>
          </el-radio-group>
        </div>

        <!-- 账号密码登录 -->
        <div v-show="loginType === 'password'" class="login-section">
          <LoginForm @success="handleLoginSuccess" />
        </div>

        <!-- 企业微信登录 -->
        <div v-show="loginType === 'wework'" class="login-section">
          <WeWorkQRCode @success="handleLoginSuccess" />
        </div>
      </el-card>

      <div class="login-footer">
        <p>© 2024 钩子固定资产管理系统</p>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import LoginForm from './components/LoginForm.vue'
import WeWorkQRCode from './components/WeWorkQRCode.vue'
import { useUserStore } from '@/stores/user'

const router = useRouter()
const route = useRoute()
const userStore = useUserStore()

const loginType = ref('password')

// 检查URL参数是否包含企业微信回调
const checkCallback = () => {
  const params = new URLSearchParams(window.location.search)
  if (params.has('code') && params.has('state')) {
    loginType.value = 'wework'
  }
}

const handleLoginSuccess = (data: { token: string; user: any }) => {
  userStore.setToken(data.token)
  userStore.setUser(data.user)

  // 跳转到目标页面或首页
  const redirect = route.query.redirect as string || '/'
  router.push(redirect)
}

checkCallback()
</script>

<style scoped>
.login-page {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}

.login-container {
  width: 100%;
  max-width: 420px;
  padding: 20px;
}

.login-header {
  text-align: center;
  color: white;
  margin-bottom: 30px;
}

.login-header h1 {
  font-size: 28px;
  font-weight: 600;
  margin-bottom: 8px;
}

.login-header p {
  font-size: 14px;
  opacity: 0.8;
}

.login-card {
  border-radius: 12px;
  overflow: hidden;
}

.login-tabs {
  display: flex;
  justify-content: center;
  padding: 20px 20px 0;
  margin-bottom: 20px;
}

.login-section {
  padding: 0 20px 20px;
}

.login-footer {
  text-align: center;
  color: rgba(255, 255, 255, 0.7);
  margin-top: 20px;
  font-size: 12px;
}
</style>
```

---

## 2. 企业微信登录组件

### WeWorkQRCode.vue - 企业微信二维码登录

```vue
<template>
  <div class="wework-qrcode">
    <!-- 配置检查中 -->
    <div v-if="loading" class="loading-state">
      <el-icon class="is-loading" :size="40">
        <Loading />
      </el-icon>
      <p>正在加载企业微信配置...</p>
    </div>

    <!-- 配置未启用 -->
    <div v-else-if="!config.enabled" class="error-state">
      <el-empty description="企业微信登录未启用">
        <template #image>
          <el-icon :size="60" color="#909399">
            <Warning />
          </el-icon>
        </template>
      </el-empty>
    </div>

    <!-- 显示二维码 -->
    <div v-else-if="showQR" class="qr-container">
      <div class="qr-header">
        <img src="@/assets/wework-logo.png" alt="企业微信" class="wework-logo" />
        <h3>企业微信扫码登录</h3>
        <p>请使用企业微信扫描二维码登录</p>
      </div>

      <div class="qr-wrapper" v-loading="qrLoading">
        <iframe
          :src="qrUrl"
          class="qr-iframe"
          frameborder="0"
          scrolling="no"
        />
      </div>

      <div class="qr-tips">
        <el-text type="info" size="small">
          <el-icon><InfoFilled /></el-icon>
          仅限企业内部员工使用
        </el-text>
      </div>
    </div>

    <!-- 登录结果 -->
    <div v-else-if="loginResult" class="result-container">
      <el-result
        :icon="loginResult.success ? 'success' : 'error'"
        :title="loginResult.title"
      >
        <template #sub-title>
          <span v-if="loginResult.success">欢迎，{{ loginResult.userName }}</span>
          <span v-else>{{ loginResult.message }}</span>
        </template>
        <template #extra>
          <el-button
            v-if="loginResult.success"
            type="primary"
            @click="handleEnter"
          >
            进入系统
          </el-button>
          <el-button v-else @click="handleRetry">重试</el-button>
        </template>
      </el-result>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { Loading, Warning, InfoFilled } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import { getWeWorkConfig, getWeWorkQRUrl, handleWeWorkCallback } from '@/api/sso'

interface Emits {
  (e: 'success', data: { token: string; user: any }): void
}

const emit = defineEmits<Emits>()
const router = useRouter()
const route = useRoute()

const loading = ref(true)
const qrLoading = ref(true)
const config = ref({ enabled: false })
const showQR = ref(false)
const qrUrl = ref('')
const loginResult = ref<any>(null)

// 检查配置
const checkConfig = async () => {
  loading.value = true
  try {
    const res = await getWeWorkConfig()
    config.value = res

    if (!res.enabled) {
      return
    }

    // 检查是否是回调
    const params = new URLSearchParams(window.location.search)
    const code = params.get('code')
    const state = params.get('state')

    if (code && state) {
      await handleCallback(code, state)
    } else {
      await loadQRCode()
    }
  } catch (error) {
    ElMessage.error('加载配置失败')
  } finally {
    loading.value = false
  }
}

// 加载二维码
const loadQRCode = async () => {
  showQR.value = true
  qrLoading.value = true

  try {
    const res = await getWeWorkQRUrl()
    qrUrl.value = res.qr_url
  } catch (error) {
    ElMessage.error('获取登录二维码失败')
    showQR.value = false
  } finally {
    qrLoading.value = false
  }
}

// 处理回调
const handleCallback = async (code: string, state: string) => {
  try {
    const res = await handleWeWorkCallback({ code, state })

    loginResult.value = {
      success: true,
      title: '登录成功',
      userName: res.user.real_name
    }

    // 通知父组件
    emit('success', res)

    // 延迟后自动跳转
    setTimeout(() => {
      handleEnter()
    }, 1500)

  } catch (error: any) {
    loginResult.value = {
      success: false,
      title: '登录失败',
      message: error.response?.data?.error || error.message || '登录失败，请重试'
    }
  }
}

const handleEnter = () => {
  const redirect = route.query.redirect as string || '/'
  router.push(redirect)
}

const handleRetry = () => {
  loginResult.value = null
  checkConfig()
}

onMounted(() => {
  checkConfig()
})
</script>

<style scoped>
.wework-qrcode {
  min-height: 300px;
}

.loading-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 40px 20px;
  color: #909399;
}

.error-state {
  padding: 20px;
}

.qr-container {
  text-align: center;
}

.qr-header {
  margin-bottom: 20px;
}

.wework-logo {
  width: 48px;
  height: 48px;
  margin-bottom: 12px;
}

.qr-header h3 {
  font-size: 18px;
  font-weight: 600;
  margin-bottom: 8px;
}

.qr-header p {
  color: #606266;
  font-size: 14px;
}

.qr-wrapper {
  display: flex;
  justify-content: center;
  margin-bottom: 16px;
}

.qr-iframe {
  width: 280px;
  height: 280px;
  border: none;
  border-radius: 8px;
}

.qr-tips {
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 4px;
}

.result-container {
  padding: 20px 0;
}
</style>
```

---

## 3. 账号密码登录表单

### LoginForm.vue - 账号密码登录

```vue
<template>
  <el-form
    ref="formRef"
    :model="form"
    :rules="rules"
    label-position="top"
    class="login-form"
  >
    <el-form-item prop="username">
      <el-input
        v-model="form.username"
        placeholder="请输入用户名"
        size="large"
        :prefix-icon="User"
      />
    </el-form-item>

    <el-form-item prop="password">
      <el-input
        v-model="form.password"
        type="password"
        placeholder="请输入密码"
        size="large"
        :prefix-icon="Lock"
        show-password
        @keyup.enter="handleLogin"
      />
    </el-form-item>

    <el-form-item>
      <div class="form-options">
        <el-checkbox v-model="form.remember">记住我</el-checkbox>
        <el-link type="primary">忘记密码？</el-link>
      </div>
    </el-form-item>

    <el-form-item>
      <el-button
        type="primary"
        size="large"
        :loading="loading"
        @click="handleLogin"
        style="width: 100%"
      >
        登录
      </el-button>
    </el-form-item>
  </el-form>
</template>

<script setup lang="ts">
import { ref, reactive } from 'vue'
import { User, Lock } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import { login } from '@/api/auth'

interface Emits {
  (e: 'success', data: { token: string; user: any }): void
}

const emit = defineEmits<Emits>()

const formRef = ref()
const loading = ref(false)

const form = reactive({
  username: '',
  password: '',
  remember: false
})

const rules = {
  username: [{ required: true, message: '请输入用户名', trigger: 'blur' }],
  password: [{ required: true, message: '请输入密码', trigger: 'blur' }]
}

const handleLogin = async () => {
  await formRef.value.validate()

  loading.value = true
  try {
    const res = await login({
      username: form.username,
      password: form.password
    })

    emit('success', res)

    if (form.remember) {
      localStorage.setItem('remembered_username', form.username)
    }
  } catch (error: any) {
    ElMessage.error(error.response?.data?.message || '登录失败')
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.login-form {
  padding: 20px 0;
}

.form-options {
  display: flex;
  justify-content: space-between;
  width: 100%;
}
</style>
```

---

## 4. API 集成

```typescript
// src/api/sso/index.ts

import request from '@/utils/request'

// 获取企业微信配置
export const getWeWorkConfig = () => {
  return request.get('/api/sso/wework/config/')
}

// 获取企业微信授权URL
export const getWeWorkAuthUrl = () => {
  return request.get('/api/sso/wework/auth-url/')
}

// 获取企业微信扫码登录URL
export const getWeWorkQRUrl = () => {
  return request.get('/api/sso/wework/qr-url/')
}

// 处理企业微信回调
export const handleWeWorkCallback = (data: { code: string; state: string }) => {
  return request.post('/api/sso/wework/callback/', data)
}

// 绑定企业微信账号
export const bindWeWork = (data: { wework_userid?: string; mobile?: string }) => {
  return request.post('/api/sso/wework/bind/', data)
}

// 解绑企业微信账号
export const unbindWeWork = () => {
  return request.delete('/api/sso/wework/unbind/')
}
```

```typescript
// src/api/auth/index.ts

import request from '@/utils/request'

export interface LoginData {
  username: string
  password: string
}

export interface LoginResponse {
  token: string
  user: {
    id: number
    username: string
    real_name: string
    email: string
    mobile: string
    avatar: string
    department: any
    roles: string[]
  }
}

// 账号密码登录
export const login = (data: LoginData) => {
  return request.post<LoginResponse>('/api/auth/login/', data)
}

// 登出
export const logout = () => {
  return request.post('/api/auth/logout/')
}

// 获取当前用户信息
export const getCurrentUser = () => {
  return request.get('/api/auth/me/')
}

// 刷新Token
export const refreshToken = () => {
  return request.post('/api/auth/refresh/')
}
```

---

## 5. 认证状态管理

```typescript
// src/stores/user.ts

import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { login as apiLogin, logout as apiLogout, getCurrentUser } from '@/api/auth'

export const useUserStore = defineStore('user', () => {
  const token = ref<string>(localStorage.getItem('token') || '')
  const user = ref<any>(null)

  const isLoggedIn = computed(() => !!token.value)
  const userName = computed(() => user.value?.real_name || '')
  const userAvatar = computed(() => user.value?.avatar || '')

  // 设置Token
  const setToken = (newToken: string) => {
    token.value = newToken
    localStorage.setItem('token', newToken)
  }

  // 设置用户信息
  const setUser = (userData: any) => {
    user.value = userData
    localStorage.setItem('user', JSON.stringify(userData))
  }

  // 清除认证信息
  const clearAuth = () => {
    token.value = ''
    user.value = null
    localStorage.removeItem('token')
    localStorage.removeItem('user')
  }

  // 登录
  const login = async (username: string, password: string) => {
    const res = await apiLogin({ username, password })
    setToken(res.token)
    setUser(res.user)
    return res
  }

  // 登出
  const logout = async () => {
    try {
      await apiLogout()
    } finally {
      clearAuth()
    }
  }

  // 获取当前用户信息
  const fetchUser = async () => {
    if (!token.value) return null

    try {
      const res = await getCurrentUser()
      setUser(res)
      return res
    } catch (error) {
      clearAuth()
      return null
    }
  }

  // 初始化（从本地存储恢复）
  const init = () => {
    const savedUser = localStorage.getItem('user')
    if (savedUser) {
      try {
        user.value = JSON.parse(savedUser)
      } catch {
        user.value = null
      }
    }
  }

  return {
    token,
    user,
    isLoggedIn,
    userName,
    userAvatar,
    setToken,
    setUser,
    clearAuth,
    login,
    logout,
    fetchUser,
    init
  }
})
```

---

## 6. 路由守卫

```typescript
// src/router/guards.ts

import { useUserStore } from '@/stores/user'
import type { Router } from 'vue-router'

export function setupAuthGuard(router: Router) {
  router.beforeEach(async (to, from, next) => {
    const userStore = useUserStore()

    // 初始化用户状态
    if (!userStore.user) {
      userStore.init()
    }

    // 不需要认证的页面
    const publicPages = ['/login', '/sso/wework/callback']
    const isPublicPage = publicPages.some(path => to.path.startsWith(path))

    if (isPublicPage) {
      next()
      return
    }

    // 检查登录状态
    if (!userStore.token) {
      next({
        path: '/login',
        query: { redirect: to.fullPath }
      })
      return
    }

    // 已登录但没有用户信息，尝试获取
    if (!userStore.user) {
      const userData = await userStore.fetchUser()
      if (!userData) {
        next({
          path: '/login',
          query: { redirect: to.fullPath }
        })
        return
      }
    }

    next()
  })
}
```

---

## 7. 路由配置

```typescript
// src/router/index.ts

import { createRouter, createWebHistory } from 'vue-router'
import type { RouteRecordRaw } from 'vue-router'

const routes: RouteRecordRaw[] = [
  {
    path: '/login',
    name: 'Login',
    component: () => import('@/views/auth/Login.vue'),
    meta: {
      title: '登录',
      requiresAuth: false
    }
  },
  {
    path: '/sso/wework/callback',
    name: 'WeWorkCallback',
    component: () => import('@/views/auth/WeWorkLogin.vue'),
    meta: {
      title: '企业微信登录回调',
      requiresAuth: false
    }
  },
  {
    path: '/',
    name: 'Home',
    component: () => import('@/views/Home.vue'),
    meta: { title: '首页' }
  }
  // ... 其他路由
]

const router = createRouter({
  history: createWebHistory(),
  routes
}

export default router
```

---

## 8. Axios 请求拦截器

```typescript
// src/utils/request.ts

import axios, { AxiosError, InternalAxiosRequestConfig } from 'axios'
import { ElMessage } from 'element-plus'
import { useUserStore } from '@/stores/user'

// 创建axios实例
const request = axios.create({
  baseURL: import.meta.env.VITE_API_URL || 'http://localhost:8000',
  timeout: 30000
})

// 请求拦截器
request.interceptors.request.use(
  (config: InternalAxiosRequestConfig) => {
    const userStore = useUserStore()

    // 添加Token
    if (userStore.token) {
      config.headers.Authorization = `Bearer ${userStore.token}`
    }

    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

// 响应拦截器
request.interceptors.response.use(
  (response) => {
    return response.data
  },
  (error: AxiosError) => {
    const userStore = useUserStore()

    if (error.response) {
      const status = error.response.status
      const data = error.response.data as any

      switch (status) {
        case 401:
          ElMessage.error('登录已过期，请重新登录')
          userStore.clearAuth()
          window.location.href = '/login'
          break
        case 403:
          ElMessage.error(data?.message || '没有权限访问')
          break
        case 404:
          ElMessage.error(data?.message || '请求的资源不存在')
          break
        case 500:
          ElMessage.error('服务器错误，请稍后重试')
          break
        default:
          ElMessage.error(data?.message || '请求失败')
      }
    } else if (error.request) {
      ElMessage.error('网络错误，请检查网络连接')
    } else {
      ElMessage.error('请求配置错误')
    }

    return Promise.reject(error)
  }
)

export default request
```

---

## 9. 环境变量

```bash
# .env.development
VITE_API_URL=http://localhost:8000
VITE_APP_NAME=钩子固定资产管理系统

# .env.production
VITE_API_URL=https://api.example.com
VITE_APP_NAME=钩子固定资产管理系统
```

---

## 后续任务

1. Phase 2.2: 实现企业微信通讯录同步
2. Phase 2.3: 实现消息通知功能
