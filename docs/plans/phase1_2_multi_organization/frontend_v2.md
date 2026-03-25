# Phase 1.2: Multi-Organization Data Isolation - Frontend Implementation v2

## Document Information

| Project | Details |
|---------|---------|
| PRD Version | v2.0 (Updated for API Standardization) |
| Updated Date | 2026-01-22 |
| References | [frontend_api_standardization_design.md](../common_base_features/00_core/frontend_api_standardization_design.md) |

---

## Task Overview

Implement multi-organization support including organization selector, data isolation, cross-organization transfers, and organization switching.

---

## API Service Layer

### Type Definitions

```typescript
// frontend/src/types/organization.ts

export interface Organization {
  id: string
  name: string
  code: string
  logo?: string
  isActive: boolean
  userRole: string
  isDefault: boolean
}

export interface OrganizationSwitchRequest {
  organizationId: string
}

export interface OrganizationSwitchResponse {
  currentOrganization: Organization
  accessToken: string
}

export interface OrganizationTransfer {
  fromOrganizationId: string
  toOrganizationId: string
  assetIds: string[]
  reason?: string
}

export interface TransferApproval {
  transferId: string
  approved: boolean
  comment?: string
}
```

### API Service

```typescript
// frontend/src/api/organizations.ts

import request from '@/utils/request'
import type { PaginatedResponse } from '@/types/api'
import type {
  Organization,
  OrganizationSwitchResponse,
  OrganizationTransfer
} from '@/types/organization'

export const organizationApi = {
  getAvailableOrganizations(): Promise<Organization[]> {
    return request.get('/organizations/user/organizations/')
  },

  getOrganizationsForTransfer(): Promise<Organization[]> {
    return request.get('/organizations/available-for-transfer/')
  },

  switchOrganization(organizationId: string): Promise<OrganizationSwitchResponse> {
    return request.post('/accounts/switch-organization/', { organizationId })
  },

  joinOrganization(inviteCode: string): Promise<void> {
    return request.post('/organizations/join/', { inviteCode })
  },

  leaveOrganization(organizationId: string): Promise<void> {
    return request.delete(`/organizations/user/organizations/${organizationId}/`)
  },

  initiateTransfer(data: OrganizationTransfer): Promise<void> {
    return request.post('/organizations/transfers/', data)
  },

  approveTransfer(transferId: string, data: TransferApproval): Promise<void> {
    return request.post(`/organizations/transfers/${transferId}/approve/`, data)
  }
}
```

---

## User Store (Multi-Org Support)

```typescript
// frontend/src/stores/user.ts (additional methods)

export const useUserStore = defineStore('user', {
  state: (): UserState => ({
    // ... existing state
    currentOrganization: null,
    organizations: []
  }),

  actions: {
    async switchOrganization(organizationId: string) {
      const data = await organizationApi.switchOrganization(organizationId)
      this.accessToken = data.accessToken
      this.currentOrganization = data.currentOrganization
      localStorage.setItem('access_token', data.accessToken)
      // Reload page to refresh data
      window.location.reload()
    },

    async loadOrganizations() {
      this.organizations = await organizationApi.getAvailableOrganizations()
      if (!this.currentOrganization && this.organizations.length > 0) {
        const defaultOrg = this.organizations.find(o => o.isDefault) || this.organizations[0]
        this.currentOrganization = defaultOrg
      }
    }
  }
})
```

---

## Component: Organization Selector

```vue
<!-- frontend/src/components/organization/OrganizationSelector.vue -->
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
          :class="{ active: org.id === currentOrg?.id }"
        >
          <div class="org-item">
            <el-icon v-if="org.id === currentOrg?.id" class="check-icon">
              <Check />
            </el-icon>
            <span>{{ org.name }}</span>
            <el-tag v-if="org.isDefault" size="small" type="info">默认</el-tag>
          </div>
        </el-dropdown-item>
        <el-dropdown-item divided command="join">
          <el-icon><Plus /></el-icon>
          加入组织
        </el-dropdown-item>
      </el-dropdown-menu>
    </template>
  </el-dropdown>

  <!-- Join Organization Dialog -->
  <JoinOrganizationDialog v-model="joinDialogVisible" @joined="handleJoined" />
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { useUserStore } from '@/stores/user'
import { organizationApi } from '@/api/organizations'
import JoinOrganizationDialog from './JoinOrganizationDialog.vue'

const userStore = useUserStore()
const organizations = computed(() => userStore.organizations)
const currentOrg = computed(() => userStore.currentOrganization)
const joinDialogVisible = ref(false)

const handleSwitch = async (command: string) => {
  if (command === 'join') {
    joinDialogVisible.value = true
    return
  }

  if (command === currentOrg.value?.id) return

  try {
    await ElMessageBox.confirm(
      `切换到 ${organizations.value.find(o => o.id === command)?.name}？`,
      '确认切换组织',
      { type: 'warning' }
    )
    await userStore.switchOrganization(command)
    ElMessage.success('组织已切换')
  } catch (error) {
    // User cancelled or error
  }
}

const handleJoined = () => {
  userStore.loadOrganizations()
}

onMounted(() => {
  userStore.loadOrganizations()
})
</script>
```

---

## Output Files

| File | Description |
|------|-------------|
| `frontend/src/types/organization.ts` | Organization type definitions |
| `frontend/src/api/organizations.ts` | Organization API service |
| `frontend/src/components/organization/OrganizationSelector.vue` | Org selector component |
| `frontend/src/components/organization/JoinOrganizationDialog.vue` | Join org dialog |
