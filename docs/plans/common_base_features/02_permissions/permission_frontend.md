# 前端权限组件设计

## 任务概述

为前端提供统一的权限控制方案，包括权限指令、权限组件、权限组合函数，以及与后端权限 API 的集成。

---

## 权限前端组件模型

### PermissionButton 组件模型

| 属性 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| permission | string | - | 权限码 |
| resource | string | - | 资源标识 |
| action | string | 'read' | 操作类型 |

### usePermission Composable 返回模型

| 属性 | 类型 | 说明 |
|------|------|------|
| hasPermission | (code:string) => boolean | 检查权限函数 |
| isGranted | Ref<boolean> | 当前资源是否授权 |

---

## 1. 设计目标

### 1.1 核心功能

| 功能 | 说明 |
|------|------|
| 权限指令 | `v-permission` 指令用于声明式权限控制 |
| 权限组件 | `PermissionButton` 等权限控制组件 |
| 权限组合函数 | `usePermission()` 提供权限检查能力 |
| 权限 Store | Pinia store 管理用户权限状态 |
| 字段权限支持 | 支持字段级读写权限控制 |

### 1.2 设计原则

1. **声明式优先** - 优先使用指令，代码更简洁
2. **组合式复用** - 使用 Composable API 提供灵活的权限控制
3. **性能优化** - 权限信息缓存，减少 API 请求
4. **类型安全** - 支持 TypeScript 类型推导

---

## 2. 文件结构

```
frontend/src/
├── stores/
│   └── permission.js              # 权限 Store
├── composables/
│   └── usePermission.js          # 权限组合函数
├── directives/
│   ├── index.js                  # 指令入口
│   └── permission.js             # 权限指令
├── components/common/
│   ├── PermissionButton.vue      # 权限按钮
│   ├── PermissionLink.vue        # 权限链接
│   ├── PermissionTag.vue         # 权限标签
│   └── PermissionVisible.vue     # 权限可见性容器
└── api/
    └── permissions.js            # 权限 API
```

---

## 3. 权限 Store

### 3.1 状态定义

| 字段 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| permissions | Array | [] | 用户权限列表 |
| roles | Array | [] | 用户角色列表 |
| fieldPermissions | Object | {} | 字段权限缓存 `{ object_code: { field_code: { read, write, visible } } }` |
| loading | Boolean | false | 权限加载状态 |
| lastLoadTime | Number | null | 最后加载时间 |
| cacheTimeout | Number | 1800000 | 缓存有效期（毫秒，默认30分钟） |

### 3.2 Getters

| Getter | 参数 | 返回值 | 说明 |
|--------|------|--------|------|
| hasPermission() | permissionCode | bool | 检查是否拥有指定权限（支持通配符） |
| hasAnyPermission() | permissionCodes | bool | 检查是否拥有任一权限 |
| hasAllPermissions() | permissionCodes | bool | 检查是否拥有所有权限 |
| hasRole() | roleCode | bool | 检查是否拥有指定角色 |
| hasAnyRole() | roleCodes | bool | 检查是否拥有任一角色 |
| isSuperAdmin | - | bool | 是否为超级管理员 |
| isFieldReadable() | objectCode, fieldCode | bool | 检查字段是否可读 |
| isFieldWritable() | objectCode, fieldCode | bool | 检查字段是否可写 |
| isCacheExpired | - | bool | 检查缓存是否过期 |

### 3.3 Actions

| Action | 参数 | 返回值 | 说明 |
|--------|------|--------|------|
| loadPermissions() | force (默认false) | Promise | 加载用户权限 |
| loadRoles() | force (默认false) | Promise | 加载用户角色 |
| loadFieldPermissions() | objectCode, force (默认false) | Promise | 加载字段权限 |
| refreshCache() | - | Promise | 刷新权限缓存 |
| clear() | - | void | 清除权限数据（登出时调用） |

---

## 4. 权限组合函数

### 4.1 usePermission Composable

**返回值：**

| 方法/属性 | 类型 | 说明 |
|----------|------|------|
| hasPermission() | Function | 检查是否拥有指定权限 |
| hasAnyPermission() | Function | 检查是否拥有任一权限 |
| hasAllPermissions() | Function | 检查是否拥有所有权限 |
| hasRole() | Function | 检查是否拥有指定角色 |
| hasAnyRole() | Function | 检查是否拥有任一角色 |
| isFieldReadable() | Function | 检查字段是否可读 |
| isFieldWritable() | Function | 检查字段是否可写 |
| getFieldPermissions() | Function | 获取字段权限 |
| refreshPermissions() | Function | 刷新权限 |
| isSuperAdmin | ComputedRef | 是否为超级管理员 |
| permissions | ComputedRef | 权限列表 |
| roles | ComputedRef | 角色列表 |
| loading | ComputedRef | 加载状态 |

### 4.2 使用示例

```vue
<script setup>
import { usePermission } from '@/composables/usePermission'

const { hasPermission, hasRole, isSuperAdmin } = usePermission()

// 检查权限
const canCreate = hasPermission('assets.create_asset')
const canEdit = hasPermission('assets.update_asset')
const canDelete = hasPermission('assets.delete_asset')
const isManager = hasRole('asset_manager')

// 组合使用
const canManage = hasAnyPermission([
  'assets.update_asset',
  'assets.delete_asset'
])

// 检查字段权限
const { isFieldReadable } = usePermission()
const canSeePrice = isFieldReadable('Asset', 'purchase_price')
</script>
```

---

## 5. 权限指令

### 5.1 指令列表

| 指令 | 参数 | 说明 | 使用示例 |
|------|------|------|----------|
| v-permission | permission_code | 精确匹配权限 | `v-permission="'assets.create_asset'"` |
| v-permission.any | permission_codes[] | 拥有任一权限 | `v-permission.any="['assets.view', 'assets.create']"` |
| v-permission.all | permission_codes[] | 拥有所有权限 | `v-permission.all="['assets.view', 'assets.create']"` |
| v-permission.role | role_code / role_codes[] | 拥有指定角色 | `v-permission.role="'admin'"` |
| v-field-permission | "Object.field_code" | 检查字段可读性 | `v-field-permission="'Asset.purchase_price'"` |
| v-field-permission:writable | "Object.field_code" | 检查字段可写性 | `v-field-permission:writable="'Asset.asset_code'"` |

### 5.2 指令注册

```javascript
// frontend/src/directives/index.js

import { permission, fieldPermission } from './permission'

export default {
  install(app) {
    app.directive('permission', permission)
    app.directive('field-permission', fieldPermission)
  }
}
```

### 5.3 使用示例

```vue
<template>
  <!-- 基础用法：精确匹配权限 -->
  <el-button
    v-permission="'assets.create_asset'"
    type="primary"
    @click="handleCreate"
  >
    新建资产
  </el-button>

  <!-- 拥有任一权限即可 -->
  <el-button
    v-permission.any="['assets.view_own', 'assets.view_all']"
    @click="handleView"
  >
    查看
  </el-button>

  <!-- 拥有所有权限才显示 -->
  <el-button
    v-permission.all="['assets.update', 'assets.approve']"
    @click="handleApprove"
  >
    审批通过
  </el-button>

  <!-- 角色检查 -->
  <el-button
    v-permission.role="'admin'"
    type="danger"
    @click="handleDelete"
  >
    删除
  </el-button>

  <!-- 多角色检查 -->
  <el-button
    v-permission.role="['admin', 'manager']"
    @click="handleManage"
  >
    管理
  </el-button>

  <!-- 字段权限：根据可读性显示/隐藏 -->
  <el-form-item
    v-field-permission="'Asset.purchase_price'"
    label="采购价格"
  >
    <el-input v-model="form.purchase_price" />
  </el-form-item>

  <!-- 字段权限：根据可写性禁用 -->
  <el-input
    v-field-permission:writable="'Asset.asset_code'"
    v-model="form.asset_code"
  />
</template>
```

---

## 6. 权限组件

### 6.1 PermissionButton

| Prop | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| permission | String \| Array | (required) | 权限代码 |
| mode | String | 'any' | 匹配模式：'any' \| 'all' |
| role | String \| Array | null | 角色代码 |
| hideOnNoPermission | Boolean | true | 无权限时是否隐藏 |
| noPermissionTooltip | String | '您没有权限执行此操作' | 无权限时的提示文本 |
| disabled | Boolean | false | 是否禁用 |

### 6.2 PermissionLink

| Prop | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| permission | String \| Array | (required) | 权限代码 |
| mode | String | 'any' | 匹配模式：'any' \| 'all' |
| hideOnNoPermission | Boolean | true | 无权限时是否隐藏 |
| noPermissionTooltip | String | '您没有权限访问此页面' | 无权限时的提示文本 |

### 6.3 PermissionVisible

| Prop | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| permission | String \| Array | (required) | 权限代码 |
| mode | String | 'any' | 匹配模式：'any' \| 'all' |
| hideOnNoPermission | Boolean | false | 无权限时是否隐藏 |
| noPermissionMessage | String | '您没有权限查看此内容' | 无权限时的提示信息 |

### 6.4 使用示例

```vue
<template>
  <!-- 权限按钮 -->
  <PermissionButton
    permission="assets.create_asset"
    type="primary"
    @click="handleCreate"
  >
    新建资产
  </PermissionButton>

  <!-- 多权限按钮（任一即可） -->
  <PermissionButton
    :permission="['assets.update', 'assets.delete']"
    mode="any"
    type="danger"
    @click="handleBatch"
  >
    批量操作
  </PermissionButton>

  <!-- 角色按钮 -->
  <PermissionButton
    role="admin"
    @click="handleAdminAction"
  >
    管理操作
  </PermissionButton>

  <!-- 权限链接 -->
  <PermissionLink
    :permission="['assets.view_own', 'assets.view_all']"
    to="/assets/detail"
  >
    查看详情
  </PermissionLink>

  <!-- 权限容器 -->
  <PermissionVisible
    permission="assets.export"
    :no-permission-message="'您没有导出权限'"
  >
    <ExportPanel />
  </PermissionVisible>
</template>
```

---

## 7. 权限 API

### 7.1 API 定义

| 方法 | 端点 | 说明 |
|------|------|------|
| getMyPermissions() | GET /api/permissions/my_permissions/ | 获取当前用户所有权限 |
| getMyRoles() | GET /api/permissions/my_roles/ | 获取当前用户所有角色 |
| getFieldPermissions(objectCode) | GET /api/permissions/field_permissions/ | 获取字段权限 |
| refreshCache() | POST /api/permissions/refresh_cache/ | 刷新权限缓存 |

---

## 8. 在应用初始化时加载权限

### 8.1 路由守卫集成

```javascript
// frontend/src/router/index.js

import { createRouter, createWebHistory } from 'vue-router'
import { usePermissionStore } from '@/stores/permission'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    // ... 路由配置
  ]
})

// 路由守卫
router.beforeEach(async (to, from, next) => {
  const permissionStore = usePermissionStore()

  // 已登录且权限未加载
  if (to.meta.requiresAuth !== false) {
    if (permissionStore.isCacheExpired) {
      await permissionStore.loadPermissions()
      await permissionStore.loadRoles()
    }
  }

  // 检查路由权限
  if (to.meta.permission) {
    if (permissionStore.hasPermission(to.meta.permission)) {
      next()
    } else {
      next('/403')
    }
  } else {
    next()
  }
})

export default router
```

### 8.2 在 main.js 中注册

```javascript
// frontend/src/main.js

import { createApp } from 'vue'
import { createPinia } from 'pinia'
import ElementPlus from 'element-plus'
import App from './App.vue'
import router from './router'
import directives from './directives'

const app = createApp(App)
const pinia = createPinia()

app.use(pinia)
app.use(router)
app.use(ElementPlus)
app.use(directives) // 注册权限指令

app.mount('#app')
```

---

## 9. 输出产物

| 文件 | 说明 |
|------|------|
| `frontend/src/stores/permission.js` | 权限 Store |
| `frontend/src/composables/usePermission.js` | 权限组合函数 |
| `frontend/src/directives/permission.js` | 权限指令 |
| `frontend/src/directives/index.js` | 指令入口 |
| `frontend/src/components/common/PermissionButton.vue` | 权限按钮 |
| `frontend/src/components/common/PermissionLink.vue` | 权限链接 |
| `frontend/src/components/common/PermissionVisible.vue` | 权限容器 |
| `frontend/src/api/permissions.js` | 权限 API |

---

## 10. 使用场景总结

| 场景 | 推荐方案 | 示例 |
|------|---------|------|
| 按钮权限控制 | `v-permission` 或 `PermissionButton` | `<el-button v-permission="'assets.create'">` |
| 链接权限控制 | `PermissionLink` | `<PermissionLink :permission="['assets.view']">` |
| 页面级权限 | 路由守卫 + `PermissionVisible` | `meta: { permission: 'assets.view' }` |
| 字段权限 | `v-field-permission` | `<input v-field-permission="'Asset.price'">` |
| 动态权限判断 | `usePermission()` | `const { hasPermission } = usePermission()` |
| 角色判断 | `v-permission.role` | `<div v-permission.role="'admin'">` |
| 组合权限 | `v-permission.any/all` | `v-permission.any="['view', 'create']"` |
