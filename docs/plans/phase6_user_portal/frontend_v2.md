# Phase 6: User Portal - Frontend Implementation

## Document Information

| Project | Details |
|---------|---------|
| PRD Version | v2.0 (Updated for API Standardization) |
| Updated Date | 2026-01-22 |
| Status | **CRITICAL** - Backend APIs need to be implemented first |
| References | [frontend_api_standardization_design.md](../common_base_features/00_core/frontend_api_standardization_design.md) |

---

## Task Overview

Implement the user portal for mobile/web access, including "My Assets", "My Requests", "My Tasks", profile management, and field configuration.

**Critical Notes:**
- 🔴 **23 Backend APIs are currently MISSING** - Must be implemented before frontend
- 🔴 **Field Configuration System is a CRITICAL dependency** for all modules
- ✅ This PRD defines the complete frontend API contract for backend implementation

---

## Missing Backend APIs - Specification

The following APIs MUST be implemented by the backend team:

### My Requests APIs

| Endpoint | Method | Description | Priority |
|----------|--------|-------------|----------|
| `/portal/my-requests/` | GET | Aggregate user requests across all types | CRITICAL |
| `/portal/my-requests/{type}/{id}/detail/` | GET | Get request detail by type and ID | HIGH |
| `/portal/my-requests/{type}/{id}/urge/` | POST | Send urge notification to approver | MEDIUM |
| `/portal/my-requests/{type}/{id}/withdraw/` | POST | Withdraw pending request | MEDIUM |

### My Tasks APIs

| Endpoint | Method | Description | Priority |
|----------|--------|-------------|----------|
| `/portal/my-tasks/` | GET | Get user's approval tasks | CRITICAL |
| `/portal/my-tasks/batch-action/` | POST | Batch approve/reject tasks | HIGH |
| `/portal/my-tasks/{id}/transfer/` | POST | Transfer task to another user | MEDIUM |

### Profile APIs

| Endpoint | Method | Description | Priority |
|----------|--------|-------------|----------|
| `/portal/profile/` | GET | Get user profile with statistics | HIGH |
| `/portal/profile/` | PUT | Update user profile | MEDIUM |
| `/portal/profile/switch-department/` | POST | Switch current department | LOW |
| `/portal/profile/preferences/` | PUT | Update user preferences | LOW |

### Field Configuration APIs

| Endpoint | Method | Description | Priority |
|----------|--------|-------------|----------|
| `/system/field-templates/` | GET | List field templates | CRITICAL |
| `/system/field-templates/` | POST | Create field template | CRITICAL |
| `/system/field-templates/{id}/` | PUT | Update field template | CRITICAL |
| `/system/field-templates/{id}/` | DELETE | Delete field template | CRITICAL |
| `/system/field-templates/{id}/set-default/` | POST | Set template as default | CRITICAL |
| `/system/my-field-config/` | GET | Get user's field config | CRITICAL |
| `/system/my-field-config/` | POST | Save user's field config | CRITICAL |
| `/system/my-field-config/reset/` | POST | Reset to default config | CRITICAL |

---

## API Service Layer

### Type Definitions

```typescript
// frontend/src/types/portal.ts

/**
 * Portal overview statistics
 */
export interface PortalOverview {
  totalAssets: number
  myAssets: number
  pendingRequests: number
  pendingTasks: number
  recentActivities: Activity[]
}

/**
 * Activity item
 */
export interface Activity {
  id: string
  type: 'pickup' | 'loan' | 'transfer' | 'return' | 'consumable'
  typeName: string
  description: string
  createdAt: string
  status: string
}

/**
 * My asset item
 */
export interface MyAsset {
  id: string
  assetCode: string
  assetName: string
  categoryName: string
  status: string
  statusLabel: string
  locationName: string
  acquireDate: string
  imageUrl?: string
  qrCode: string
}

/**
 * My asset detail
 */
export interface MyAssetDetail extends MyAsset {
  description?: string
  specifications: Record<string, string>
  custodianName?: string
  departmentName?: string
  maintenanceDate?: string
  warrantyExpireDate?: string
}

/**
 * My requests response (aggregated)
 */
export interface MyRequestsResponse {
  summary: RequestSummary
  groupBy: 'type' | 'status' | 'date'
  groups: RequestGroup[]
}

/**
 * Request summary
 */
export interface RequestSummary {
  total: number
  pending: number
  approved: number
  rejected: number
  completed: number
}

/**
 * Request group
 */
export interface RequestGroup {
  type: string
  typeName: string
  count: number
  items: RequestItem[]
}

/**
 * Request item (unified across types)
 */
export interface RequestItem {
  id: string
  type: 'pickup' | 'loan' | 'transfer' | 'return' | 'consumable_issue' | 'consumable_purchase'
  typeLabel: string
  requestNo: string
  title: string
  status: string
  statusLabel: string
  currentApprover?: string
  createdAt: string
  updatedAt: string
  canUrge: boolean
  canWithdraw: boolean
}

/**
 * Request detail (unified)
 */
export interface RequestDetail extends RequestItem {
  items: RequestItemDetail[]
  reason?: string
  remark?: string
  approvals: ApprovalRecord[]
  auditInfo: AuditInfo
}

/**
 * Request item detail
 */
export interface RequestItemDetail {
  assetCode: string
  assetName: string
  categoryName: string
  quantity: number
  unit?: string
}

/**
 * My task item
 */
export interface MyTask {
  id: string
  taskId: string
  taskType: 'approval' | 'review' | 'inventory'
  taskTypeLabel: string
  title: string
  description: string
  requestType?: string
  requestNo?: string
  status: string
  statusLabel: string
  createdAt: string
  dueDate?: string
  canApprove: boolean
  canReject: boolean
  canTransfer: boolean
}

/**
 * Task detail
 */
export interface MyTaskDetail extends MyTask {
  requesterName: string
  requesterDepartment: string
  requestData: any
  approvals: ApprovalRecord[]
  comments: Comment[]
}

/**
 * Batch task action
 */
export interface BatchTaskAction {
  action: 'approve' | 'reject' | 'transfer'
  taskIds: string[]
  comment?: string
  transferTo?: string
}

/**
 * Batch task action result
 */
export interface BatchTaskActionResult {
  summary: {
    total: number
    succeeded: number
    failed: number
  }
  results: Array<{
    taskId: string
    success: boolean
    error?: string
  }>
}

/**
 * User profile
 */
export interface UserProfile {
  id: string
  username: string
  realName: string
  email?: string
  phone?: string
  avatar?: string
  departmentId?: string
  departmentName?: string
  position?: string
  employeeNo?: string
  organizationId: string
  organizationName?: string
  preferences: UserPreferences
  statistics: UserStatistics
}

/**
 * User preferences
 */
export interface UserPreferences {
  language: string
  theme: 'light' | 'dark' | 'auto'
  notificationEnabled: boolean
  emailNotificationEnabled: boolean
  fieldConfigs: Record<string, FieldConfig>
}

/**
 * User statistics
 */
export interface UserStatistics {
  totalAssets: number
  pendingRequests: number
  pendingTasks: number
  completedRequests: number
  completedTasks: number
}

/**
 * Field configuration
 */
export interface FieldConfig {
  module: string
  view: 'list' | 'form' | 'detail'
  columns: FieldColumn[]
  sortBy: string
  sortOrder: 'asc' | 'desc'
  pageSize: number
}

/**
 * Field column
 */
export interface FieldColumn {
  field: string
  label: string
  width: number
  visible: boolean
  sortable: boolean
  fixed?: 'left' | 'right'
}

/**
 * Approval record
 */
export interface ApprovalRecord {
  id: string
  approverName: string
  approverAvatar?: string
  action: 'approved' | 'rejected' | 'returned' | 'pending'
  actionLabel: string
  comment?: string
  createdAt: string
}

/**
 * Comment
 */
export interface Comment {
  id: string
  userName: string
  userAvatar?: string
  content: string
  createdAt: string
}

/**
 * Audit info
 */
export interface AuditInfo {
  createdBy: string
  createdAt: string
  updatedBy?: string
  updatedAt?: string
}

/**
 * My assets filters
 */
export interface MyAssetsFilters {
  page?: number
  pageSize?: number
  status?: string
  categoryId?: string
  keyword?: string
}

/**
 * My requests filters
 */
export interface MyRequestsFilters {
  page?: number
  pageSize?: number
  type?: string
  status?: string
  groupBy?: 'type' | 'status' | 'date'
}

/**
 * My tasks filters
 */
export interface MyTasksFilters {
  page?: number
  pageSize?: number
  taskType?: string
  status?: string
}
```

### API Service

```typescript
// frontend/src/api/portal.ts

import request from '@/utils/request'
import type { ApiResponse, PaginatedResponse } from '@/types/api'
import type {
  PortalOverview,
  MyAsset,
  MyAssetDetail,
  MyAssetsFilters,
  MyRequestsResponse,
  MyRequestsFilters,
  RequestDetail,
  MyTask,
  MyTaskDetail,
  MyTasksFilters,
  BatchTaskAction,
  BatchTaskActionResult,
  UserProfile,
  UserPreferences
} from '@/types/portal'

/**
 * User Portal API
 * All endpoints use /portal/ base path (no /api prefix required)
 *
 * NOTE: These APIs are currently MISSING and must be implemented by backend
 */
export const portalApi = {
  // ==================== Overview ====================

  /**
   * Get portal overview statistics
   */
  getOverview(): Promise<PortalOverview> {
    return request.get('/portal/overview/')
  },

  // ==================== My Assets ====================

  /**
   * Get user's assets
   * @param params - Query parameters (camelCase)
   */
  getMyAssets(params?: MyAssetsFilters): Promise<PaginatedResponse<MyAsset>> {
    return request.get('/portal/my-assets/', { params })
  },

  /**
   * Get asset detail for portal view
   * @param id - Asset ID
   */
  getAssetDetail(id: string): Promise<MyAssetDetail> {
    return request.get(`/portal/my-assets/${id}/`)
  },

  /**
   * Batch action on assets
   * @param data - Batch action data
   */
  batchAssetAction(data: {
    action: 'return' | 'transfer'
    assetIds: string[]
    target?: string
  }): Promise<BatchTaskActionResult> {
    return request.post('/portal/my-assets/batch-action/', data)
  },

  // ==================== My Requests ====================

  /**
   * Get user's requests (aggregated across types)
   * @param params - Query parameters (camelCase)
   *
   * Response format:
   * {
   *   summary: { total, pending, approved, rejected, completed },
   *   groupBy: 'type',
   *   groups: [{ type, typeName, count, items: [...] }]
   * }
   */
  getMyRequests(params?: MyRequestsFilters): Promise<MyRequestsResponse> {
    return request.get('/portal/my-requests/', { params })
  },

  /**
   * Get request detail by type and ID
   * @param type - Request type (pickup/loan/transfer/return/consumable_issue/consumable_purchase)
   * @param id - Request ID
   */
  getRequestDetail(type: string, id: string): Promise<RequestDetail> {
    return request.get(`/portal/my-requests/${type}/${id}/detail/`)
  },

  /**
   * Urge a pending request
   * @param type - Request type
   * @param id - Request ID
   * @param comment - Optional comment
   */
  urgeRequest(type: string, id: string, comment?: string): Promise<void> {
    return request.post(`/portal/my-requests/${type}/${id}/urge/`, { comment })
  },

  /**
   * Withdraw a pending request
   * @param type - Request type
   * @param id - Request ID
   */
  withdrawRequest(type: string, id: string): Promise<void> {
    return request.post(`/portal/my-requests/${type}/${id}/withdraw/`)
  },

  // ==================== My Tasks ====================

  /**
   * Get user's approval tasks
   * @param params - Query parameters
   */
  getMyTasks(params?: MyTasksFilters): Promise<PaginatedResponse<MyTask>> {
    return request.get('/portal/my-tasks/', { params })
  },

  /**
   * Get task detail
   * @param id - Task ID
   */
  getTaskDetail(id: string): Promise<MyTaskDetail> {
    return request.get(`/portal/my-tasks/${id}/`)
  },

  /**
   * Approve a task
   * @param id - Task ID
   * @param comment - Optional approval comment
   */
  approveTask(id: string, comment?: string): Promise<void> {
    return request.post(`/portal/my-tasks/${id}/approve/`, { comment })
  },

  /**
   * Reject a task
   * @param id - Task ID
   * @param comment - Rejection reason
   */
  rejectTask(id: string, comment: string): Promise<void> {
    return request.post(`/portal/my-tasks/${id}/reject/`, { comment })
  },

  /**
   * Batch action on tasks
   * @param data - Batch action data
   */
  batchTaskAction(data: BatchTaskAction): Promise<BatchTaskActionResult> {
    return request.post('/portal/my-tasks/batch-action/', data)
  },

  /**
   * Transfer task to another user
   * @param id - Task ID
   * @param transferTo - Target user ID
   * @param comment - Optional comment
   */
  transferTask(id: string, transferTo: string, comment?: string): Promise<void> {
    return request.post(`/portal/my-tasks/${id}/transfer/`, { transferTo, comment })
  },

  // ==================== Profile ====================

  /**
   * Get user profile with statistics
   */
  getProfile(): Promise<UserProfile> {
    return request.get('/portal/profile/')
  },

  /**
   * Update user profile
   * @param data - Profile data
   */
  updateProfile(data: Partial<UserProfile>): Promise<UserProfile> {
    return request.put('/portal/profile/', data)
  },

  /**
   * Switch current department
   * @param departmentId - Target department ID
   */
  switchDepartment(departmentId: string): Promise<{ token: string }> {
    return request.post('/portal/profile/switch-department/', { departmentId })
  },

  /**
   * Update user preferences
   * @param preferences - Preferences object
   */
  updatePreferences(preferences: Partial<UserPreferences>): Promise<void> {
    return request.put('/portal/profile/preferences/', preferences)
  },

  // ==================== Field Configuration ====================

  /**
   * Get field configuration for a module
   * @param module - Module code (my_assets, my_requests, my_tasks)
   * @param view - View type (list/form/detail)
   */
  getFieldConfig(module: string, view: string): Promise<FieldConfig> {
    return request.get('/system/my-field-config/', {
      params: { module, view }
    })
  },

  /**
   * Save field configuration
   * @param config - Field configuration object
   */
  saveFieldConfig(config: FieldConfig): Promise<void> {
    return request.post('/system/my-field-config/', config)
  },

  /**
   * Reset field configuration to default
   * @param module - Module code
   * @param view - View type
   */
  resetFieldConfig(module: string, view: string): Promise<void> {
    return request.post('/system/my-field-config/reset/', { module, view })
  }
}

/**
 * Field configuration (re-export for convenience)
 */
export interface FieldConfig {
  module: string
  view: 'list' | 'form' | 'detail'
  columns: Array<{
    field: string
    label: string
    width: number
    visible: boolean
    sortable: boolean
    fixed?: 'left' | 'right'
  }>
  sortBy: string
  sortOrder: 'asc' | 'desc'
  pageSize: number
}
```

---

## Component Implementation

### Portal Home Page

```vue
<!-- frontend/src/views/portal/PortalHome.vue -->
<template>
  <div class="portal-home">
    <!-- Header -->
    <div class="portal-header">
      <h1>工作台</h1>
      <div class="user-info">
        <el-avatar :src="userProfile.avatar" :size="40">
          {{ userProfile.realName?.charAt(0) }}
        </el-avatar>
        <span>{{ userProfile.realName }}</span>
      </div>
    </div>

    <!-- Overview Cards -->
    <el-row :gutter="16" class="overview-cards">
      <el-col :xs="12" :sm="6">
        <el-card class="stat-card" @click="navigateTo('/portal/my-assets')">
          <el-statistic :value="overview.myAssets" title="我的资产">
            <template #suffix>件</template>
          </el-statistic>
        </el-card>
      </el-col>
      <el-col :xs="12" :sm="6">
        <el-card class="stat-card" @click="navigateTo('/portal/my-requests')">
          <el-statistic :value="overview.pendingRequests" title="待处理请求">
            <template #suffix>条</template>
          </el-statistic>
        </el-card>
      </el-col>
      <el-col :xs="12" :sm="6">
        <el-card class="stat-card" @click="navigateTo('/portal/my-tasks')">
          <el-statistic :value="overview.pendingTasks" title="待审批任务">
            <template #suffix>个</template>
          </el-statistic>
        </el-card>
      </el-col>
      <el-col :xs="12" :sm="6">
        <el-card class="stat-card">
          <el-statistic :value="overview.totalAssets" title="资产总数">
            <template #suffix>件</template>
          </el-statistic>
        </el-card>
      </el-col>
    </el-row>

    <!-- Recent Activities -->
    <el-card class="activities-card">
      <template #header>
        <div class="card-header">
          <span>最近动态</span>
          <el-button link @click="navigateTo('/portal/activities')">查看全部</el-button>
        </div>
      </template>
      <el-timeline>
        <el-timeline-item
          v-for="activity in overview.recentActivities"
          :key="activity.id"
          :timestamp="formatDate(activity.createdAt)"
          placement="top"
        >
          <div class="activity-item">
            <el-tag :type="getActivityTagType(activity.type)" size="small">
              {{ activity.typeName }}
            </el-tag>
            <span class="activity-desc">{{ activity.description }}</span>
            <el-tag v-if="activity.status" size="small" class="activity-status">
              {{ activity.status }}
            </el-tag>
          </div>
        </el-timeline-item>
      </el-timeline>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { portalApi } from '@/api/portal'
import { useUserStore } from '@/stores/user'
import type { PortalOverview, UserProfile } from '@/types/portal'

const router = useRouter()
const userStore = useUserStore()

const overview = ref<PortalOverview>({
  totalAssets: 0,
  myAssets: 0,
  pendingRequests: 0,
  pendingTasks: 0,
  recentActivities: []
})

const userProfile = ref<UserProfile>({
  id: '',
  username: '',
  realName: '',
  organizationId: '',
  preferences: {
    language: 'zh-CN',
    theme: 'auto',
    notificationEnabled: true,
    emailNotificationEnabled: true,
    fieldConfigs: {}
  },
  statistics: {
    totalAssets: 0,
    pendingRequests: 0,
    pendingTasks: 0,
    completedRequests: 0,
    completedTasks: 0
  }
})

/**
 * Load overview data
 */
const loadOverview = async () => {
  try {
    overview.value = await portalApi.getOverview()
  } catch (error) {
    // Error handled by interceptor
  }
}

/**
 * Load user profile
 */
const loadProfile = async () => {
  try {
    userProfile.value = await portalApi.getProfile()
  } catch (error) {
    // Error handled by interceptor
  }
}

/**
 * Navigate to page
 */
const navigateTo = (path: string) => {
  router.push(path)
}

/**
 * Format date
 */
const formatDate = (dateStr: string) => {
  // Date formatting logic
  return new Date(dateStr).toLocaleString('zh-CN')
}

/**
 * Get activity tag type
 */
const getActivityTagType = (type: string) => {
  const typeMap: Record<string, string> = {
    pickup: 'primary',
    loan: 'success',
    transfer: 'warning',
    return: 'info',
    consumable: ''
  }
  return typeMap[type] || ''
}

onMounted(() => {
  loadOverview()
  loadProfile()
})
</script>

<style scoped>
.portal-home {
  padding: 20px;
}

.portal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24px;
}

.portal-header h1 {
  font-size: 24px;
  font-weight: 600;
  margin: 0;
}

.user-info {
  display: flex;
  align-items: center;
  gap: 12px;
}

.overview-cards {
  margin-bottom: 24px;
}

.stat-card {
  cursor: pointer;
  transition: transform 0.2s;
}

.stat-card:hover {
  transform: translateY(-4px);
}

.activities-card {
  background: white;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.activity-item {
  display: flex;
  align-items: center;
  gap: 8px;
}

.activity-desc {
  flex: 1;
}

.activity-status {
  margin-left: auto;
}
</style>
```

---

## Backend Implementation Requirements

### My Requests Service

```python
# backend/apps/portal/services.py

from typing import Dict, Any, List
from apps.common.services.base_crud import BaseCRUDService


class UserRequestService(BaseCRUDService):
    """
    Aggregate user requests across multiple types
    """

    def get_my_requests(self, user_id: str, group_by: str = 'type',
                      filters: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Get aggregated requests for a user

        Args:
            user_id: Current user ID
            group_by: Group by 'type', 'status', or 'date'
            filters: Optional filters for status, type, etc.

        Returns:
            {
                'summary': {
                    'total': int,
                    'pending': int,
                    'approved': int,
                    'rejected': int,
                    'completed': int
                },
                'group_by': str,
                'groups': [
                    {
                        'type': str,
                        'typeName': str,
                        'count': int,
                        'items': [...]
                    }
                ]
            }
        """
        # Query across multiple request types:
        # - AssetPickup
        # - AssetLoan
        # - AssetTransfer
        # - AssetReturn
        # - ConsumableIssue
        # - ConsumablePurchase

        # Aggregate and group results
        pass

    def get_request_detail(self, request_type: str, request_id: str) -> Dict[str, Any]:
        """
        Get detail for a specific request

        Args:
            request_type: Type of request (pickup, loan, transfer, etc.)
            request_id: Request ID
        """
        pass

    def urge_request(self, request_type: str, request_id: str,
                    comment: str = None) -> None:
        """
        Send urge notification to current approver

        Args:
            request_type: Type of request
            request_id: Request ID
            comment: Optional comment
        """
        # Create notification for current approver
        pass

    def withdraw_request(self, request_type: str, request_id: str) -> None:
        """
        Withdraw a pending request

        Args:
            request_type: Type of request
            request_id: Request ID
        """
        # Update request status to 'withdrawn'
        # Create notification for approvers
        pass
```

### My Tasks Service

```python
# backend/apps/portal/services.py (continued)

class UserTaskService(BaseCRUDService):
    """
    User task/approval management
    """

    def get_my_tasks(self, user_id: str, filters: Dict[str, Any] = None) -> List[Dict]:
        """
        Get pending approval tasks for user

        Returns tasks from:
        - Workflow approvals
        - Direct request approvals
        """
        pass

    def batch_task_action(self, user_id: str, task_ids: List[str],
                         action: str, comment: str = None) -> Dict[str, Any]:
        """
        Batch approve/reject tasks

        Returns:
            {
                'summary': {'total': int, 'succeeded': int, 'failed': int},
                'results': [...]
            }
        """
        pass

    def transfer_task(self, task_id: str, from_user_id: str,
                     to_user_id: str, comment: str = None) -> None:
        """
        Transfer task approval to another user
        """
        pass
```

### Field Template Model

```python
# backend/apps/system/models.py

from apps.common.models import BaseModel


class FieldTemplate(BaseModel):
    """
    Field configuration template for list/form/detail views
    Supports system/organization/user scoped configurations
    """
    SCOPE_CHOICES = [
        ('system', 'System Level'),
        ('organization', 'Organization Level'),
        ('user', 'User Level'),
    ]

    name = models.CharField(max_length=200)
    code = models.CharField(max_length=100)
    module = models.CharField(max_length=50)  # my_assets, my_requests, my_tasks
    view_type = models.CharField(
        max_length=20,
        choices=[('list', 'List'), ('form', 'Form'), ('detail', 'Detail')]
    )
    scope = models.CharField(max_length=20, choices=SCOPE_CHOICES, default='user')
    scope_id = models.UUIDField(null=True, blank=True)  # org_id or user_id
    config = models.JSONField(default=dict)  # Field configuration
    is_default = models.BooleanField(default=False)

    class Meta:
        db_table = 'system_field_templates'
        verbose_name = 'Field Template'
        verbose_name_plural = 'Field Templates'
        unique_together = [['code', 'scope', 'scope_id']]
```

---

## Page Routes

```typescript
// frontend/src/router/index.ts

{
  path: '/portal',
  component: PortalLayout,
  children: [
    {
      path: '',
      name: 'PortalHome',
      component: () => import('@/views/portal/PortalHome.vue'),
      meta: { title: '工作台' }
    },
    {
      path: 'my-assets',
      name: 'MyAssets',
      component: () => import('@/views/portal/MyAssets.vue'),
      meta: { title: '我的资产' }
    },
    {
      path: 'my-assets/:id',
      name: 'MyAssetDetail',
      component: () => import('@/views/portal/MyAssetDetail.vue'),
      meta: { title: '资产详情' }
    },
    {
      path: 'my-requests',
      name: 'MyRequests',
      component: () => import('@/views/portal/MyRequests.vue'),
      meta: { title: '我的请求' }
    },
    {
      path: 'my-requests/:type/:id',
      name: 'RequestDetail',
      component: () => import('@/views/portal/RequestDetail.vue'),
      meta: { title: '请求详情' }
    },
    {
      path: 'my-tasks',
      name: 'MyTasks',
      component: () => import('@/views/portal/MyTasks.vue'),
      meta: { title: '我的任务' }
    },
    {
      path: 'profile',
      name: 'UserProfile',
      component: () => import('@/views/portal/UserProfile.vue'),
      meta: { title: '个人中心' }
    }
  ]
}
```

---

## Output Files

| File | Description |
|------|-------------|
| `frontend/src/types/portal.ts` | Portal type definitions |
| `frontend/src/api/portal.ts` | Portal API service |
| `frontend/src/views/portal/PortalHome.vue` | Portal home page |
| `frontend/src/views/portal/MyAssets.vue` | My assets page |
| `frontend/src/views/portal/MyRequests.vue` | My requests page |
| `frontend/src/views/portal/MyTasks.vue` | My tasks page |
| `frontend/src/views/portal/UserProfile.vue` | User profile page |
| `frontend/src/components/portal/FieldConfigPanel.vue` | Field config panel |
| `backend/apps/portal/services.py` | Backend services (TO BE IMPLEMENTED) |
| `backend/apps/system/models.py` | Add FieldTemplate model |
| `backend/apps/portal/viewsets.py` | Portal viewsets (TO BE IMPLEMENTED) |
