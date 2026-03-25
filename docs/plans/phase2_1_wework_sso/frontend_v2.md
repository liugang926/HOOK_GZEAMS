# Phase 2.1: WeWork SSO Integration - Frontend Implementation

## Document Information

| Project | Details |
|---------|---------|
| PRD Version | v2.0 (Updated for API Standardization) |
| Updated Date | 2026-01-22 |
| References | [frontend_api_standardization_design.md](../common_base_features/00_core/frontend_api_standardization_design.md) |

---

## Task Overview

Implement WeWork (企业微信) SSO login integration, including QR code login, authorization callback, and account binding.

**Key Changes from v1:**
- ✅ All code converted to TypeScript
- ✅ Token management standardized
- ✅ Error handling uses standardized error codes
- ✅ User store follows standard pattern

---

## API Service Layer

### Type Definitions

```typescript
// frontend/src/types/auth.ts

/**
 * Login response data
 */
export interface LoginResponse {
  accessToken: string
  refreshToken: string
  user: User
  currentOrganization: Organization | null
  organizations: Organization[]
  permissions: string[]
}

/**
 * User profile
 */
export interface User {
  id: string
  username: string
  realName: string
  email?: string
  phone?: string
  avatar?: string
  departmentId?: string
  departmentName?: string
  isActive: boolean
  isSuperuser: boolean
  organizationId: string
  createdAt: string
}

/**
 * Organization
 */
export interface Organization {
  id: string
  name: string
  logo?: string
}

/**
 * WeWork auth URL response
 */
export interface WeWorkAuthUrl {
  authUrl: string
  state: string
}

/**
 * WeWork QR code response
 */
export interface WeWorkQrCode {
  qrCode: string
  state: string
  expiresAt: string
}

/**
 * WeWork config
 */
export interface WeWorkConfig {
  enabled: boolean
  corpId: string
  agentId: string
}

/**
 * Login request data
 */
export interface LoginRequest {
  username: string
  password: string
}

/**
 * Refresh token request
 */
export interface RefreshTokenRequest {
  refreshToken: string
}

/**
 * WeWork callback data
 */
export interface WeWorkCallback {
  code: string
  state: string
}
```

### API Service

```typescript
// frontend/src/api/auth.ts

import request from '@/utils/request'
import type { ApiResponse } from '@/types/api'
import type {
  LoginResponse,
  LoginRequest,
  WeWorkConfig,
  WeWorkAuthUrl,
  WeWorkQrCode,
  WeWorkCallback
} from '@/types/auth'

/**
 * Authentication API
 */
export const authApi = {
  /**
   * Get WeWork SSO configuration
   */
  getWeWorkConfig(): Promise<WeWorkConfig> {
    return request.get('/sso/wework/config/')
  },

  /**
   * Get WeWork authorization URL
   * @param redirectUri - Redirect URI after authorization
   */
  getWeWorkAuthUrl(redirectUri?: string): Promise<WeWorkAuthUrl> {
    return request.get('/sso/wework/auth-url/', {
      params: { redirectUri }
    })
  },

  /**
   * Get WeWork QR code for login
   */
  getWeWorkQrCode(): Promise<WeWorkQrCode> {
    return request.get('/sso/wework/qr-url/')
  },

  /**
   * Handle WeWork OAuth callback
   * @param data - Callback data from WeWork
   */
  handleWeWorkCallback(data: WeWorkCallback): Promise<LoginResponse> {
    return request.post('/sso/wework/callback/', data)
  },

  /**
   * Bind WeWork account to current user
   * @param code - Authorization code from WeWork
   */
  bindWeWork(code: string): Promise<void> {
    return request.post('/sso/wework/bind/', { code })
  },

  /**
   * Unbind WeWork account
   */
  unbindWeWork(): Promise<void> {
    return request.delete('/sso/wework/unbind/')
  },

  /**
   * Standard username/password login
   * @param data - Login credentials
   */
  login(data: LoginRequest): Promise<LoginResponse> {
    return request.post('/auth/login/', data)
  },

  /**
   * Logout
   */
  logout(): Promise<void> {
    return request.post('/auth/logout/')
  },

  /**
   * Get current user info
   */
  getCurrentUser(): Promise<User> {
    return request.get('/auth/me/')
  },

  /**
   * Refresh access token
   * @param data - Refresh token data
   */
  refreshToken(data: RefreshTokenRequest): Promise<{ accessToken: string }> {
    return request.post('/auth/refresh/', data)
  }
}
```

---

## User Store (Pinia)

```typescript
// frontend/src/stores/user.ts

import { defineStore } from 'pinia'
import { authApi } from '@/api/auth'
import type { User, Organization, LoginResponse } from '@/types/auth'
import router from '@/router'

interface UserState {
  accessToken: string | null
  refreshToken: string | null
  user: User | null
  currentOrganization: Organization | null
  organizations: Organization[]
  permissions: string[]
}

export const useUserStore = defineStore('user', {
  state: (): UserState => ({
    accessToken: localStorage.getItem('access_token'),
    refreshToken: localStorage.getItem('refresh_token'),
    user: null,
    currentOrganization: null,
    organizations: [],
    permissions: []
  }),

  getters: {
    isLoggedIn: (state) => !!state.accessToken,
    userDisplayName: (state) => state.user?.realName || state.user?.username || '',
    hasPermission: (state) => (permission: string) => {
      if (state.user?.isSuperuser) return true
      return state.permissions.includes(permission)
    }
  },

  actions: {
    /**
     * Set authentication data
     */
    setAuthData(data: LoginResponse) {
      this.accessToken = data.accessToken
      this.refreshToken = data.refreshToken
      this.user = data.user
      this.currentOrganization = data.currentOrganization
      this.organizations = data.organizations
      this.permissions = data.permissions

      // Persist to localStorage
      localStorage.setItem('access_token', data.accessToken)
      localStorage.setItem('refresh_token', data.refreshToken)
    },

    /**
     * Clear authentication data
     */
    clearAuth() {
      this.accessToken = null
      this.refreshToken = null
      this.user = null
      this.currentOrganization = null
      this.organizations = []
      this.permissions = []

      localStorage.removeItem('access_token')
      localStorage.removeItem('refresh_token')
    },

    /**
     * Login with username/password
     */
    async login(username: string, password: string) {
      const data = await authApi.login({ username, password })
      this.setAuthData(data)
      return data
    },

    /**
     * Handle WeWork SSO callback
     */
    async handleWeWorkCallback(code: string, state: string) {
      const data = await authApi.handleWeWorkCallback({ code, state })
      this.setAuthData(data)
      return data
    },

    /**
     * Logout
     */
    async logout() {
      try {
        await authApi.logout()
      } catch (error) {
        // Continue with local logout even if API call fails
      } finally {
        this.clearAuth()
        router.push('/login')
      }
    },

    /**
     * Fetch current user info
     */
    async fetchUser() {
      if (!this.accessToken) return

      try {
        this.user = await authApi.getCurrentUser()
      } catch (error) {
        this.clearAuth()
        router.push('/login')
      }
    },

    /**
     * Refresh access token
     */
    async refreshAccessToken() {
      if (!this.refreshToken) {
        throw new Error('No refresh token available')
      }

      const data = await authApi.refreshToken({
        refreshToken: this.refreshToken
      })

      this.accessToken = data.accessToken
      localStorage.setItem('access_token', data.accessToken)
    },

    /**
     * Switch organization
     */
    async switchOrganization(organizationId: string) {
      // Will be implemented in organization module
      const targetOrg = this.organizations.find(o => o.id === organizationId)
      if (targetOrg) {
        this.currentOrganization = targetOrg
      }
    }
  }
})
```

---

## Component Implementation

### Login Page with WeWork QR Code

```vue
<!-- frontend/src/views/auth/LoginView.vue -->
<template>
  <div class="login-page">
    <div class="login-container">
      <div class="login-header">
        <h1>固定资产管理系统</h1>
        <p>Hook Fixed Assets Management System</p>
      </div>

      <el-card class="login-card">
        <el-tabs v-model="activeTab">
          <!-- Password Login Tab -->
          <el-tab-pane label="账号登录" name="password">
            <el-form
              ref="loginFormRef"
              :model="loginForm"
              :rules="loginRules"
              @submit.prevent="handlePasswordLogin"
            >
              <el-form-item prop="username">
                <el-input
                  v-model="loginForm.username"
                  placeholder="请输入用户名"
                  prefix-icon="User"
                  size="large"
                />
              </el-form-item>

              <el-form-item prop="password">
                <el-input
                  v-model="loginForm.password"
                  type="password"
                  placeholder="请输入密码"
                  prefix-icon="Lock"
                  size="large"
                  show-password
                  @keyup.enter="handlePasswordLogin"
                />
              </el-form-item>

              <el-form-item>
                <el-button
                  type="primary"
                  size="large"
                  :loading="loading"
                  style="width: 100%"
                  @click="handlePasswordLogin"
                >
                  登录
                </el-button>
              </el-form-item>
            </el-form>
          </el-tab-pane>

          <!-- WeWork QR Code Tab -->
          <el-tab-pane
            v-if="weWorkConfig.enabled"
            label="企业微信登录"
            name="wework"
          >
            <div class="qrcode-container">
              <div v-if="qrCodeData.qrCode" class="qrcode-wrapper">
                <qrcode-vue
                  :value="qrCodeData.qrCode"
                  :size="200"
                  level="M"
                />
                <p class="qrcode-tip">请使用企业微信扫码登录</p>
                <el-button link type="primary" @click="refreshQrCode">
                  刷新二维码
                </el-button>
              </div>
              <el-skeleton v-else :rows="1" animated />
            </div>
          </el-tab-pane>
        </el-tabs>
      </el-card>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { ElMessage } from 'element-plus'
import type { FormInstance, FormRules } from 'element-plus'
import QrcodeVue from 'qrcode.vue'
import { useUserStore } from '@/stores/user'
import { authApi } from '@/api/auth'
import type { WeWorkConfig, WeWorkQrCode } from '@/types/auth'

const router = useRouter()
const route = useRoute()
const userStore = useUserStore()

const activeTab = ref('password')
const loading = ref(false)
const loginFormRef = ref<FormInstance>()

const loginForm = ref({
  username: '',
  password: ''
})

const loginRules: FormRules = {
  username: [{ required: true, message: '请输入用户名', trigger: 'blur' }],
  password: [{ required: true, message: '请输入密码', trigger: 'blur' }]
}

const weWorkConfig = ref<WeWorkConfig>({ enabled: false, corpId: '', agentId: '' })
const qrCodeData = ref<WeWorkQrCode>({ qrCode: '', state: '', expiresAt: '' })

let pollTimer: number | null = null

/**
 * Load WeWork config
 */
const loadWeWorkConfig = async () => {
  try {
    weWorkConfig.value = await authApi.getWeWorkConfig()
    if (weWorkConfig.value.enabled) {
      await loadQrCode()
    }
  } catch (error) {
    // WeWork not configured, hide tab
  }
}

/**
 * Load QR code
 */
const loadQrCode = async () => {
  try {
    qrCodeData.value = await authApi.getWeWorkQrCode()
    startPolling()
  } catch (error) {
    // Error handled by interceptor
  }
}

/**
 * Refresh QR code
 */
const refreshQrCode = () => {
  stopPolling()
  loadQrCode()
}

/**
 * Start polling for login status
 */
const startPolling = () => {
  stopPolling()

  pollTimer = window.setInterval(async () => {
    // Check login status via backend
    // This would be a separate endpoint that checks if login completed
  }, 2000)
}

/**
 * Stop polling
 */
const stopPolling = () => {
  if (pollTimer) {
    clearInterval(pollTimer)
    pollTimer = null
  }
}

/**
 * Handle password login
 */
const handlePasswordLogin = async () => {
  if (!loginFormRef.value) return

  try {
    await loginFormRef.value.validate()
  } catch {
    return
  }

  loading.value = true

  try {
    await userStore.login(loginForm.value.username, loginForm.value.password)
    ElMessage.success('登录成功')

    // Redirect to original page or home
    const redirect = route.query.redirect as string || '/'
    router.push(redirect)
  } catch (error) {
    // Error handled by interceptor
  } finally {
    loading.value = false
  }
}

/**
 * Handle WeWork callback
 */
const handleWeWorkCallback = async () => {
  const code = route.query.code as string
  const state = route.query.state as string

  if (!code) return

  loading.value = true

  try {
    await userStore.handleWeWorkCallback(code, state)
    ElMessage.success('登录成功')
    router.push('/')
  } catch (error) {
    // Error handled by interceptor
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  // Check if already logged in
  if (userStore.isLoggedIn) {
    router.push('/')
    return
  }

  // Check for WeWork callback
  if (route.query.code) {
    handleWeWorkCallback()
    return
  }

  // Load WeWork config
  loadWeWorkConfig()
})

onUnmounted(() => {
  stopPolling()
})
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
  width: 400px;
  padding: 20px;
}

.login-header {
  text-align: center;
  margin-bottom: 30px;
  color: white;
}

.login-header h1 {
  font-size: 28px;
  margin-bottom: 10px;
}

.login-header p {
  font-size: 14px;
  opacity: 0.8;
}

.login-card {
  border-radius: 8px;
}

.qrcode-container {
  text-align: center;
  padding: 20px;
}

.qrcode-wrapper {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 16px;
}

.qrcode-tip {
  color: var(--el-text-color-secondary);
  font-size: 14px;
  margin: 0;
}
</style>
```

---

## Token Refresh Interceptor

```typescript
// frontend/src/utils/request.ts (additional code for token refresh)

import { useUserStore } from '@/stores/user'

/**
 * Response interceptor with token refresh
 */
request.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config

    // Handle 401 Unauthorized - try to refresh token
    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true

      const userStore = useUserStore()

      if (userStore.refreshToken) {
        try {
          await userStore.refreshAccessToken()

          // Retry original request with new token
          originalRequest.headers.Authorization = `Bearer ${userStore.accessToken}`
          return request(originalRequest)
        } catch (refreshError) {
          // Refresh failed, logout user
          userStore.clearAuth()
          window.location.href = '/login'
          return Promise.reject(refreshError)
        }
      } else {
        // No refresh token, logout
        userStore.clearAuth()
        window.location.href = '/login'
      }
    }

    return Promise.reject(error)
  }
)
```

---

## Page Routes

```typescript
// frontend/src/router/index.ts

{
  path: '/login',
  name: 'Login',
  component: () => import('@/views/auth/LoginView.vue'),
  meta: {
    title: '登录',
    requiresAuth: false
  }
}

{
  path: '/auth/wework/callback',
  name: 'WeWorkCallback',
  component: () => import('@/views/auth/WeWorkCallback.vue'),
  meta: {
    requiresAuth: false
  }
}
```

---

## Output Files

| File | Description |
|------|-------------|
| `frontend/src/types/auth.ts` | Authentication type definitions |
| `frontend/src/api/auth.ts` | Authentication API service |
| `frontend/src/stores/user.ts` | User Pinia store |
| `frontend/src/views/auth/LoginView.vue` | Login page with WeWork QR |
| `frontend/src/views/auth/WeWorkCallback.vue` | WeWork OAuth callback handler |
