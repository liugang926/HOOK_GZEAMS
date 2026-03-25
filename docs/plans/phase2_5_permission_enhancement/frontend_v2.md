# Phase 2.5: Permission Enhancement - Frontend Implementation v2

## Document Information

| Project | Details |
|---------|---------|
| PRD Version | v2.0 (Updated for API Standardization) |
| Updated Date | 2026-01-22 |
| References | [frontend_api_standardization_design.md](../common_base_features/00_core/frontend_api_standardization_design.md) |

---

## Task Overview

Implement enhanced permission management including field-level permissions, data scope permissions, and permission audit logs.

---

## API Service Layer

### Type Definitions

```typescript
// frontend/src/types/permission.ts

export interface FieldPermission {
  id: string
  objectType: string
  objectCode: string
  fieldCode: string
  fieldName: string
  permission: 'hidden' | 'readonly' | 'editable'
  roles?: string[]
  users?: string[]
}

export interface DataScope {
  id: string
  objectType: string
  objectCode: string
  scopeType: 'all' | 'own' | 'department' | 'organization' | 'custom'
  scopeFilter?: Record<string, any>
  roles?: string[]
  users?: string[]
}

export interface PermissionTemplate {
  id: string
  name: string
  code: string
  description?: string
  permissions: string[]
  isSystem: boolean
}

export interface PermissionAudit {
  id: string
  userId: string
  userName: string
  action: string
  resource: string
  details: Record<string, any>
  ipAddress: string
  userAgent: string
  status: 'allowed' | 'denied'
  createdAt: string
}

export interface UserPermission {
  userId: string
  userName: string
  permissions: string[]
  roles: string[]
  fieldPermissions: Record<string, FieldPermissionEntry>
  dataScopes: Record<string, string>
}

export interface FieldPermissionEntry {
  read: boolean
  write: boolean
}

export interface PermissionCheck {
  permission: string
  resource?: string
  resourceId?: string
}
```

### API Service

```typescript
// frontend/src/api/permissions.ts

import request from '@/utils/request'
import type { PaginatedResponse } from '@/types/api'
import type {
  FieldPermission,
  DataScope,
  PermissionTemplate,
  PermissionAudit,
  UserPermission
} from '@/types/permission'

export const permissionApi = {
  // Field Permissions
  getFieldPermissions(params?: any): Promise<PaginatedResponse<FieldPermission>> {
    return request.get('/permissions/field/', { params })
  },

  createFieldPermission(data: Partial<FieldPermission>): Promise<FieldPermission> {
    return request.post('/permissions/field/', data)
  },

  updateFieldPermission(id: string, data: Partial<FieldPermission>): Promise<FieldPermission> {
    return request.put(`/permissions/field/${id}/`, data)
  },

  deleteFieldPermission(id: string): Promise<void> {
    return request.delete(`/permissions/field/${id}/`)
  },

  // Data Scopes
  getDataScopes(params?: any): Promise<PaginatedResponse<DataScope>> {
    return request.get('/permissions/data/', { params })
  },

  createDataScope(data: Partial<DataScope>): Promise<DataScope> {
    return request.post('/permissions/data/', data)
  },

  updateDataScope(id: string, data: Partial<DataScope>): Promise<DataScope> {
    return request.put(`/permissions/data/${id}/`, data)
  },

  deleteDataScope(id: string): Promise<void> {
    return request.delete(`/permissions/data/${id}/`)
  },

  // Permission Templates
  getTemplates(params?: any): Promise<PaginatedResponse<PermissionTemplate>> {
    return request.get('/permissions/templates/', { params })
  },

  createTemplate(data: Partial<PermissionTemplate>): Promise<PermissionTemplate> {
    return request.post('/permissions/templates/', data)
  },

  // User Permissions
  getUserPermissions(userId: string): Promise<UserPermission> {
    return request.get(`/permissions/users/${userId}/`)
  },

  assignPermissions(userId: string, permissions: string[]): Promise<void> {
    return request.post(`/permissions/users/${userId}/assign/`, { permissions })
  },

  revokePermissions(userId: string, permissions: string[]): Promise<void> {
    return request.post(`/permissions/users/${userId}/revoke/`, { permissions })
  },

  // Audit Logs
  getAuditLogs(params?: any): Promise<PaginatedResponse<PermissionAudit>> {
    return request.get('/permissions/audit/', { params })
  }
}
```

---

## Composable: usePermission

```typescript
// frontend/src/composables/usePermission.ts

import { computed } from 'vue'
import { useUserStore } from '@/stores/user'

export function usePermission() {
  const userStore = useUserStore()

  /**
   * Check if user has a specific permission
   */
  const hasPermission = (permission: string): boolean => {
    if (userStore.user?.isSuperuser) return true
    return userStore.permissions.includes(permission)
  }

  /**
   * Check if user has any of the specified permissions
   */
  const hasAnyPermission = (permissions: string[]): boolean => {
    if (userStore.user?.isSuperuser) return true
    return permissions.some(p => userStore.permissions.includes(p))
  }

  /**
   * Check if user has all of the specified permissions
   */
  const hasAllPermissions = (permissions: string[]): boolean => {
    if (userStore.user?.isSuperuser) return true
    return permissions.every(p => userStore.permissions.includes(p))
  }

  /**
   * Check field-level permission
   */
  const getFieldPermission = (objectCode: string, fieldCode: string): FieldPermissionEntry => {
    // Get from store or compute from user's field permissions
    const fieldPermissions = userStore.fieldPermissions || {}
    const key = `${objectCode}.${fieldCode}`
    return fieldPermissions[key] || { read: true, write: true }
  }

  /**
   * Check if field is readable
   */
  const canReadField = (objectCode: string, fieldCode: string): boolean => {
    return getFieldPermission(objectCode, fieldCode).read
  }

  /**
   * Check if field is writable
   */
  const canWriteField = (objectCode: string, fieldCode: string): boolean => {
    return getFieldPermission(objectCode, fieldCode).write
  }

  /**
   * Get data scope filter for an object
   */
  const getDataScopeFilter = (objectCode: string): Record<string, any> | null => {
    const dataScopes = userStore.dataScopes || {}
    const scope = dataScopes[objectCode]

    if (!scope) return null

    // Convert scope to filter
    switch (scope) {
      case 'all':
        return {}
      case 'own':
        return { createdBy: userStore.user?.id }
      case 'department':
        return { departmentId: userStore.user?.departmentId }
      case 'organization':
        return { organizationId: userStore.currentOrganization?.id }
      default:
        return null
    }
  }

  return {
    hasPermission,
    hasAnyPermission,
    hasAllPermissions,
    canReadField,
    canWriteField,
    getDataScopeFilter
  }
}
```

---

## Directive: v-permission

```typescript
// frontend/src/directives/permission.ts

import type { Directive, DirectiveBinding } from 'vue'
import { useUserStore } from '@/stores/user'

/**
 * Permission directive
 * Usage: v-permission="'assets.create_asset'"
 * Usage: v-permission.any="['assets.update', 'assets.delete']"
 * Usage: v-permission.all="['assets.update', 'assets.delete']"
 */
const permission: Directive = {
  mounted(el: HTMLElement, binding: DirectiveBinding) {
    const { value, modifiers } = binding
    const userStore = useUserStore()

    if (!value) return

    let hasPermission = false

    if (modifiers.any) {
      // Check if user has ANY of the permissions
      hasPermission = (value as string[]).some(p => userStore.permissions.includes(p))
    } else if (modifiers.all) {
      // Check if user has ALL of the permissions
      hasPermission = (value as string[]).every(p => userStore.permissions.includes(p))
    } else {
      // Single permission check
      hasPermission = userStore.permissions.includes(value as string)
    }

    if (!hasPermission && userStore.user?.isSuperuser !== true) {
      // Remove element from DOM
      el.parentNode?.removeChild(el)
    }
  }
}

export default permission
```

---

## Component: PermissionButton

```vue
<!-- frontend/src/components/common/PermissionButton.vue -->
<template>
  <el-button
    v-if="visible"
    v-bind="$attrs"
    :disabled="disabled"
    @click="handleClick"
  >
    <slot />
  </el-button>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { usePermission } from '@/composables/usePermission'

interface Props {
  permission: string | string[]
  mode?: 'any' | 'all'
  disableOnNoPermission?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  mode: 'all',
  disableOnNoPermission: false
})

const emit = defineEmits<{
  click: [event: MouseEvent]
}>()

const { hasPermission, hasAnyPermission, hasAllPermissions } = usePermission()

const visible = computed(() => {
  const perm = props.permission

  if (typeof perm === 'string') {
    return hasPermission(perm)
  }

  return props.mode === 'any'
    ? hasAnyPermission(perm)
    : hasAllPermissions(perm)
})

const disabled = computed(() => {
  if (props.disableOnNoPermission) {
    return !visible.value
  }
  return false
})

const handleClick = (event: MouseEvent) => {
  if (visible.value) {
    emit('click', event)
  }
}
</script>
```

---

## Output Files

| File | Description |
|------|-------------|
| `frontend/src/types/permission.ts` | Permission type definitions |
| `frontend/src/api/permissions.ts` | Permission API service |
| `frontend/src/composables/usePermission.ts` | Permission composable |
| `frontend/src/directives/permission.ts` | v-permission directive |
| `frontend/src/components/common/PermissionButton.vue` | Permission button component |
| `frontend/src/stores/permission.ts` | Permission Pinia store |
