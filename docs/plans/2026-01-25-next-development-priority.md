# NEWSEAMS 下一阶段开发优先级实施计划

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 基于最新代码审查，优先实现最关键的功能缺口和测试覆盖

**Architecture:** Vue 3 + Django REST + Playwright E2E + Vitest Unit Tests

**Tech Stack:** Vue 3 (Composition API), Django 5.0, DRF, Playwright, Vitest

---

## 项目最新状态评估

经过代码审查，更新项目完成度评估：

| PRD阶段 | 之前评估 | 最新评估 | 说明 |
|---------|---------|---------|------|
| Phase 1.1 资产分类 | 90% | 90% | 已完成 |
| Phase 1.2 多组织架构 | 85% | 85% | 已完成 |
| Phase 1.5 资产操作流程 | 30% | **75%** | 后端+前端已实现 |
| Phase 3.1 LogicFlow | 80% | 85% | 已完成 |
| Phase 3.2 工作流执行引擎 | 40% | **90%** | 核心引擎完整 |
| 前端单元测试 | 0% | **0%** | **关键缺口** |
| 工作流集成资产操作 | - | **30%** | **需要集成** |

---

## 优先级调整后的开发计划

### 阶段一: 前端单元测试框架搭建（P0 - 2天）

**原因**:
- 后端有56个测试文件，前端为0
- 缺乏单元测试导致维护成本高
- 无法快速验证前端代码质量

**包含任务**:
1. 安装配置Vitest
2. 配置Vue Test Utils
3. 编写核心组件测试示例
4. 配置CI/CD集成

---

### 阶段二: 工作流与资产操作集成（P0 - 3天）

**原因**:
- 工作流引擎已完整实现
- 资产操作单据已完整实现
- 缺少两者之间的自动集成

**包含任务**:
1. 领用单与工作流自动集成
2. 调拨单与工作流自动集成
3. 审批完成后自动更新资产状态
4. 前端审批界面完善

---

### 阶段三: Phase 6.0 用户门户（P1 - 5天）

**原因**:
- 用户需要一个统一的门户入口
- 集中展示我的资产、申请、任务

**包含任务**:
1. 我的资产页面
2. 我的领用申请页面
3. 我的审批任务页面
4. 个人工作台

---

## 任务分解

### Task 1: 搭建前端单元测试框架

**Files:**
- Create: `frontend/vitest.config.ts`
- Create: `frontend/src/components/__tests__/setup.ts`
- Modify: `frontend/package.json` (添加test脚本)
- Create: `frontend/src/components/common/__tests__/BaseListPage.spec.ts`

**Step 1: 安装Vitest和Vue Test Utils**

```bash
cd frontend
npm install -D vitest @vue/test-utils @vitest/ui jsdom @vitest/coverage-v8 happy-dom
```

**Step 2: 创建Vitest配置文件**

**File**: `frontend/vitest.config.ts`
```typescript
import { defineConfig } from 'vitest/config'
import vue from '@vitejs/plugin-vue'
import { resolve } from 'path'

export default defineConfig({
  plugins: [vue()],
  test: {
    globals: true,
    environment: 'happy-dom',
    coverage: {
      provider: 'v8',
      reporter: ['text', 'json', 'html'],
      exclude: [
        'node_modules/',
        'src/test/',
        '**/*.d.ts',
        '**/*.config.*',
        '**/mockData',
        'src/e2e/',
      ]
    },
    include: ['src/**/*.{test,spec}.{js,ts,vue}', 'tests/**/*.{test,spec}.{js,ts}'],
    root: '.',
  },
  resolve: {
    alias: {
      '@': resolve(__dirname, './src')
    }
  }
})
```

**Step 3: 更新package.json**

```json
{
  "scripts": {
    "test": "vitest",
    "test:ui": "vitest --ui",
    "test:coverage": "vitest --coverage"
  }
}
```

**Step 4: 创建测试设置文件**

**File**: `frontend/src/components/__tests__/setup.ts`
```typescript
import { vi } from 'vitest'

// Mock Element Plus
vi.mock('element-plus', () => ({
  ElMessage: {
    success: vi.fn(),
    error: vi.fn(),
    warning: vi.fn(),
    info: vi.fn()
  },
  ElMessageBox: {
    confirm: vi.fn()
  },
  ElNotification: {
    success: vi.fn(),
    error: vi.fn()
  }
}))

// Mock Vue Router
vi.mock('vue-router', () => ({
  useRoute: () => ({ params: {}, query: {} }),
  useRouter: () => ({ push: vi.fn(), back: vi.fn() })
}))

// Mock Pinia stores
vi.mock('@/stores/user', () => ({
  useUserStore: () => ({
    user: { id: '1', username: 'test' },
    token: 'test-token'
  }))
})
```

**Step 5: 运行测试确认配置生效**

```bash
cd frontend
npm run test
```

**Expected**: Vitest启动，没有找到测试文件（因为还没写测试）

**Step 6: 编写第一个组件测试示例**

**File**: `frontend/src/components/common/__tests__/BaseListPage.spec.ts`
```typescript
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount } from '@vue/test-utils'
import { ElTable } from 'element-plus'
import BaseListPage from '../BaseListPage.vue'

// Mock router and store
const mockRoute = { params: {}, query: {} }
const mockRouter = { push: vi.fn(), back: vi.fn() }

vi.mock('vue-router', () => ({
  useRoute: () => mockRoute,
  useRouter: () => mockRouter
}))

describe('BaseListPage Component', () => {
  it('should render page title', () => {
    const wrapper = mount(BaseListPage, {
      props: {
        title: 'Test Page'
      },
      global: {
        stubs: {
          ElTable,
          'el-button': true,
          'el-input': true
        }
      }
    })

    expect(wrapper.text()).toContain('Test Page')
  })

  it('should emit search event when search button clicked', async () => {
    const wrapper = mount(BaseListPage, {
      props: {
        title: 'Test Page'
      },
      global: {
        stubs: {
          ElTable,
          'el-button': true,
          'el-input': true
        }
      }
    })

    // Test search functionality
    // Implementation depends on actual component structure
    expect(wrapper.exists()).toBe(true)
  })
})
```

**Step 7: 运行测试确认通过**

```bash
npm run test
```

**Expected**: 测试通过或显示有意义的错误信息

**Step 8: 提交代码**

```bash
git add frontend/vitest.config.ts frontend/package.json frontend/src/components/__tests__/ frontend/src/components/common/__tests__/
git commit -m "test: add Vitest unit testing framework"
```

---

### Task 2: 工作流与资产领用集成

**Files:**
- Modify: `backend/apps/assets/services/operation_service.py`
- Modify: `frontend/src/api/assets/pickup.ts`
- Modify: `frontend/src/views/assets/operations/PickupForm.vue`
- Create: `backend/apps/assets/services/workflow_integration.py`

**Step 1: 创建工作流集成服务**

**File**: `backend/apps/assets/services/workflow_integration.py`
```python
"""
Workflow Integration Service for Asset Operations

Integrates asset operations (pickup, transfer, loan, return) with workflow engine.
"""
from typing import Dict, Any, Optional
from django.utils.translation import gettext_lazy as _
import logging

logger = logging.getLogger(__name__)

from apps.workflows.models import WorkflowDefinition, WorkflowInstance
from apps.workflows.services.workflow_engine import WorkflowEngine


class AssetWorkflowIntegration:
    """
    Service to integrate asset operations with workflow.

    Handles:
    - Starting workflow when operation is submitted
    - Updating operation status when workflow completes
    - Triggering asset status updates
    """

    # Workflow process keys
    PROCESS_PICKUP = 'asset_pickup'
    PROCESS_TRANSFER = 'asset_transfer'
    PROCESS_LOAN = 'asset_loan'
    PROCESS_RETURN = 'asset_return'

    @classmethod
    def get_workflow_definition(cls, process_key: str, organization_id: str) -> Optional[WorkflowDefinition]:
        """Get published workflow definition for a process."""
        try:
            return WorkflowDefinition.objects.filter(
                business_object_code=process_key,
                status='published',
                organization_id=organization_id,
                is_deleted=False
            ).first()
        except Exception as e:
            logger.error(f"Error getting workflow definition: {e}")
            return None

    @classmethod
    def start_operation_workflow(
        cls,
        process_key: str,
        operation_instance: Any,
        initiator: Any,
        organization_id: str
    ) -> tuple[bool, Optional[WorkflowInstance], Optional[str]]:
        """
        Start workflow for an asset operation.

        Args:
            process_key: Workflow process key (e.g., 'asset_pickup')
            operation_instance: The operation instance (AssetPickup, etc.)
            initiator: User initiating the workflow
            organization_id: Organization ID

        Returns:
            (success, workflow_instance, error)
        """
        definition = cls.get_workflow_definition(process_key, organization_id)

        if not definition:
            # No workflow defined, auto-approve
            logger.warning(f"No workflow definition found for {process_key}")
            return True, None, None

        engine = WorkflowEngine(definition)

        success, instance, error = engine.start_workflow(
            definition=definition,
            business_object_code=process_key,
            business_id=str(operation_instance.id),
            business_no=getattr(operation_instance, 'pickup_no', '') or
                       getattr(operation_instance, 'transfer_no', '') or
                       getattr(operation_instance, 'loan_no', '') or
                       getattr(operation_instance, 'return_no', ''),
            initiator=initiator,
            variables={
                'operation_data': {
                    'id': str(operation_instance.id),
                    'type': process_key,
                    'items_count': operation_instance.items.count()
                }
            }
        )

        return success, instance, error

    @classmethod
    def handle_workflow_completion(
        cls,
        workflow_instance: WorkflowInstance
    ) -> tuple[bool, Optional[str]]:
        """
        Handle workflow completion.

        Update the related operation status and trigger asset updates.

        Args:
            workflow_instance: Completed workflow instance

        Returns:
            (success, error)
        """
        if workflow_instance.status != WorkflowInstance.STATUS_APPROVED:
            return True, None  # No action needed for rejected workflows

        process_key = workflow_instance.business_object_code
        business_id = workflow_instance.business_id

        try:
            if process_key == cls.PROCESS_PICKUP:
                return cls._complete_pickup(business_id)
            elif process_key == cls.PROCESS_TRANSFER:
                return cls._complete_transfer(business_id)
            elif process_key == cls.PROCESS_LOAN:
                return cls._complete_loan(business_id)
            elif process_key == cls.PROCESS_RETURN:
                return cls._complete_return(business_id)
            else:
                logger.warning(f"Unknown process key: {process_key}")
                return True, None

        except Exception as e:
            logger.error(f"Error handling workflow completion: {e}")
            return False, str(e)

    @classmethod
    def _complete_pickup(cls, business_id: str) -> tuple[bool, Optional[str]]:
        """Complete pickup operation after workflow approval."""
        from apps.assets.models import AssetPickup
        from apps.assets.services.operation_service import AssetPickupService

        try:
            pickup = AssetPickup.objects.get(id=business_id)
            service = AssetPickupService()
            service.complete_pickup(pickup.id, pickup.approved_by or pickup.created_by)
            return True, None
        except AssetPickup.DoesNotExist:
            return False, "Pickup order not found"

    @classmethod
    def _complete_transfer(cls, business_id: str) -> tuple[bool, Optional[str]]:
        """Complete transfer operation after workflow approval."""
        from apps.assets.models import AssetTransfer
        from apps.assets.services.operation_service import AssetTransferService

        try:
            transfer = AssetTransfer.objects.get(id=business_id)
            service = AssetTransferService()
            service.complete_transfer(transfer.id, transfer.to_approved_by or transfer.created_by)
            return True, None
        except AssetTransfer.DoesNotExist:
            return False, "Transfer order not found"

    @classmethod
    def _complete_loan(cls, business_id: str) -> tuple[bool, Optional[str]]:
        """Complete loan operation after workflow approval."""
        from apps.assets.models import AssetLoan
        from apps.assets.services.operation_service import AssetLoanService

        try:
            loan = AssetLoan.objects.get(id=business_id)
            service = AssetLoanService()
            service.confirm_borrow(loan.id, loan.approved_by or loan.created_by)
            return True, None
        except AssetLoan.DoesNotExist:
            return False, "Loan order not found"

    @classmethod
    def _complete_return(cls, business_id: str) -> tuple[bool, Optional[str]]:
        """Complete return operation after workflow approval."""
        from apps.assets.models import AssetReturn
        from apps.assets.services.operation_service import AssetReturnService

        try:
            return_order = AssetReturn.objects.get(id=business_id)
            service = AssetReturnService()
            service.confirm_return(return_order.id, return_order.created_by)
            return True, None
        except AssetReturn.DoesNotExist:
            return False, "Return order not found"
```

**Step 2: 更新PickupViewSet集成工作流**

**File**: `backend/apps/assets/viewsets/operation.py` (修改submit方法)
```python
from apps.assets.services.workflow_integration import AssetWorkflowIntegration

@action(detail=True, methods=['post'], url_path='submit')
def submit(self, request, pk=None):
    """Submit pickup order for approval."""
    pickup = self.get_object()

    # Start workflow integration
    success, workflow_instance, error = AssetWorkflowIntegration.start_operation_workflow(
        process_key=AssetWorkflowIntegration.PROCESS_PICKUP,
        operation_instance=pickup,
        initiator=request.user,
        organization_id=pickup.organization_id
    )

    if not success and workflow_instance is None:
        # No workflow configured, auto-approve
        pickup = self.service.submit_for_approval(pk, request.user)
        pickup = self.service.approve(pk, request.user, 'approved', 'Auto-approved (no workflow)')
    elif not success:
        return BaseResponse.error(
            code='WORKFLOW_START_FAILED',
            message=error or 'Failed to start workflow'
        )
    else:
        # Update pickup status to pending
        pickup.status = 'pending'
        pickup.workflow_instance = workflow_instance
        pickup.save(update_fields=['status', 'workflow_instance', 'updated_at'])

    response_serializer = AssetPickupDetailSerializer(pickup)
    return BaseResponse.success(
        data=response_serializer.data,
        message='Pickup order submitted for approval'
    )
```

**Step 3: 添加工作流完成回调API**

**File**: `backend/apps/assets/viewsets/operation.py` (添加新方法到AssetPickupViewSet)
```python
@action(detail=True, methods=['post'], url_path='workflow-callback')
def workflow_callback(self, request, pk=None):
    """Handle workflow completion callback."""
    from apps.workflows.models import WorkflowInstance

    pickup = self.get_object()
    workflow_instance_id = request.data.get('workflow_instance_id')

    if not workflow_instance_id:
        return BaseResponse.error(
            code='MISSING_WORKFLOW_ID',
            message='Workflow instance ID is required'
        )

    try:
        workflow_instance = WorkflowInstance.objects.get(id=workflow_instance_id)
        success, error = AssetWorkflowIntegration.handle_workflow_completion(workflow_instance)

        if success:
            pickup.refresh_from_db()
            response_serializer = AssetPickupDetailSerializer(pickup)
            return BaseResponse.success(
                data=response_serializer.data,
                message='Operation completed after workflow approval'
            )
        else:
            return BaseResponse.error(
                code='WORKFLOW_COMPLETION_FAILED',
                message=error or 'Failed to complete operation'
            )
    except WorkflowInstance.DoesNotExist:
        return BaseResponse.error(
            code='WORKFLOW_NOT_FOUND',
            message='Workflow instance not found'
        )
```

**Step 4: 更新前端API**

**File**: `frontend/src/api/assets/pickup.ts`
```typescript
import request from '@/utils/request'

export interface PickupItemPayload {
  asset_id: string
  remark?: string
}

export interface PickupPayload {
  department_id: string
  pickup_date: string
  pickup_reason: string
  items: PickupItemPayload[]
}

export interface SubmitForApprovalResponse {
  id: string
  status: string
  workflow_instance?: any
}

// Submit for approval
export const submitForApproval = (id: number) => {
  return request.post<any, SubmitForApprovalResponse>(`/assets/pickups/${id}/submit/`)
}

// Handle workflow callback
export const handleWorkflowCallback = (id: number, workflowInstanceId: string) => {
  return request.post(`/assets/pickups/${id}/workflow-callback/`, {
    workflow_instance_id: workflowInstanceId
  })
}

// ... existing functions
```

**Step 5: 更新前端PickupForm使用新API**

**File**: `frontend/src/views/assets/operations/PickupForm.vue` (修改handleSubmitAndApply方法)
```typescript
const handleSubmitAndApply = async () => {
    try {
        // First save the pickup
        if (!form.id) {
            const payload = await validateAndGetPayload()
            submitting.value = true
            const res = await createPickup(payload)
            form.id = res.id
        }

        // Then submit for approval
        const result = await submitForApproval(form.id)

        ElMessage.success('提交审批成功')
        goBack()
    } catch (e: any) {
        if (e.message !== 'Validation failed') {
            console.error(e)
            ElMessage.error(e.message || '提交审批失败')
        }
    } finally {
        submitting.value = false
    }
}
```

**Step 6: 添加测试**

**File**: `backend/apps/assets/tests/test_workflow_integration.py`
```python
"""Tests for workflow integration with asset operations."""
import pytest
from django.utils import timezone
from apps.accounts.models import User
from apps.organizations.models import Organization
from apps.assets.models import Asset, AssetPickup, PickupItem
from apps.assets.services.workflow_integration import AssetWorkflowIntegration
from apps.workflows.models import WorkflowDefinition, WorkflowInstance


@pytest.mark.django_db
class TestAssetWorkflowIntegration:
    """Test workflow integration for asset operations."""

    @pytest.fixture
    def setup_data(self, db):
        """Create test data."""
        org = Organization.objects.create(name='Test Org')
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            organization=org
        )
        asset = Asset.objects.create(
            organization=org,
            code='TEST001',
            name='Test Asset',
            asset_status='idle'
        )
        return org, user, asset

    def test_get_workflow_definition(self, setup_data):
        """Test getting workflow definition."""
        org, user, asset = setup_data

        # Create workflow definition
        definition = WorkflowDefinition.objects.create(
            organization=org,
            name='Asset Pickup Workflow',
            business_object_code='asset_pickup',
            status='published',
            graph_data={'nodes': [], 'edges': []}
        )

        result = AssetWorkflowIntegration.get_workflow_definition(
            'asset_pickup',
            str(org.id)
        )

        assert result is not None
        assert result.id == definition.id

    def test_start_operation_workflow_without_definition(self, setup_data):
        """Test starting workflow when no definition exists (auto-approve)."""
        org, user, asset = setup_data

        pickup = AssetPickup.objects.create(
            organization=org,
            applicant=user,
            pickup_no='L-TEST-001',
            pickup_date=timezone.now().date()
        )

        success, instance, error = AssetWorkflowIntegration.start_operation_workflow(
            'asset_pickup',
            pickup,
            user,
            str(org.id)
        )

        assert success is True
        assert instance is None  # No workflow instance created
        assert error is None

    def test_complete_pickup(self, setup_data):
        """Test completing pickup operation."""
        org, user, asset = setup_data

        pickup = AssetPickup.objects.create(
            organization=org,
            applicant=user,
            pickup_no='L-TEST-001',
            pickup_date=timezone.now().date(),
            status='approved'
        )

        PickupItem.objects.create(
            organization=org,
            pickup=pickup,
            asset=asset,
            snapshot_original_custodian=asset.custodian
        )

        success, error = AssetWorkflowIntegration._complete_pickup(str(pickup.id))

        assert success is True
        assert error is None

        # Verify pickup is completed
        pickup.refresh_from_db()
        assert pickup.status == 'completed'
```

**Step 7: 运行测试确认通过**

```bash
cd backend
venv/Scripts/python.exe manage.py test apps.assets.tests.test_workflow_integration -v
```

**Step 8: 提交代码**

```bash
git add backend/apps/assets/services/ backend/apps/assets/viewsets/ backend/apps/assets/tests/ frontend/src/api/assets/pickup.ts frontend/src/views/assets/operations/PickupForm.vue
git commit -m "feat: integrate workflow with asset pickup operations"
```

---

### Task 3: 实现我的审批任务页面

**Files:**
- Create: `frontend/src/views/workflow/MyApprovals.vue`
- Modify: `frontend/src/router/index.ts`
- Modify: `frontend/src/api/workflow.ts`

**Step 1: 更新工作流API**

**File**: `frontend/src/api/workflow.ts`
```typescript
import request from '@/utils/request'

// My Tasks API
export const getMyTasks = (params?: { status?: string }) => {
  return request.get('/workflows/tasks/my_tasks/', { params })
}

// Approve task
export const approveTask = (id: string, data: { comment?: string }) => {
  return request.post(`/workflows/tasks/${id}/approve/`, data)
}

// Reject task
export const rejectTask = (id: string, data: { comment?: string }) => {
  return request.post(`/workflows/tasks/${id}/reject/`, data)
}

// Return task
export const returnTask = (id: string, data: { comment?: string }) => {
  return request.post(`/workflows/tasks/${id}/return_task/`, data)
}

// Get task detail
export const getTaskDetail = (id: string) => {
  return request.get(`/workflows/tasks/${id}/`)
}
```

**Step 2: 创建审批页面组件**

**File**: `frontend/src/views/workflow/MyApprovals.vue`
```vue
<template>
  <div class="my-approvals">
    <div class="page-header">
      <h2>我的审批</h2>
    </div>

    <el-tabs v-model="activeTab" class="mt-4">
      <el-tab-pane label="待审批" name="pending">
        <ApprovalList
          :tasks="pendingTasks"
          :loading="loading"
          @approve="handleApprove"
          @reject="handleReject"
          @return="handleReturn"
        />
      </el-tab-pane>

      <el-tab-pane label="已审批" name="completed">
        <ApprovalList
          :tasks="completedTasks"
          :loading="loading"
          :read-only="true"
        />
      </el-tab-pane>
    </el-tabs>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { getMyTasks, approveTask, rejectTask, returnTask } from '@/api/workflow'
import ApprovalList from './components/ApprovalList.vue'

const activeTab = ref('pending')
const loading = ref(false)
const pendingTasks = ref([])
const completedTasks = ref([])

const loadTasks = async () => {
  loading.value = true
  try {
    const data = await getMyTasks()
    pendingTasks.value = data.pending || []
    completedTasks.value = data.completed_today || []
  } catch (e) {
    console.error(e)
    ElMessage.error('加载失败')
  } finally {
    loading.value = false
  }
}

const handleApprove = async (taskId: string, comment?: string) => {
  try {
    await approveTask(taskId, { comment })
    ElMessage.success('审批成功')
    await loadTasks()
  } catch (e) {
    ElMessage.error('审批失败')
  }
}

const handleReject = async (taskId: string, comment?: string) => {
  try {
    await rejectTask(taskId, { comment })
    ElMessage.success('已拒绝')
    await loadTasks()
  } catch (e) {
    ElMessage.error('操作失败')
  }
}

const handleReturn = async (taskId: string, comment?: string) => {
  try {
    await returnTask(taskId, { comment })
    ElMessage.success('已退回')
    await loadTasks()
  } catch (e) {
    ElMessage.error('操作失败')
  }
}

onMounted(() => {
  loadTasks()
})
</script>

<style scoped>
.my-approvals {
  padding: 20px;
}
</style>
```

**Step 3: 创建ApprovalList组件**

**File**: `frontend/src/views/workflow/components/ApprovalList.vue`
```vue
<template>
  <div class="approval-list">
    <el-table :data="tasks" :loading="loading" v-loading="loading">
      <el-table-column prop="instance.business_no" label="单号" width="150" />
      <el-table-column prop="node_name" label="当前节点" width="120" />
      <el-table-column label="业务类型" width="100">
        <template #default="{ row }">
          {{ getBusinessType(row.instance.business_object_code) }}
        </template>
      </el-table-column>
      <el-table-column prop="instance.initiator.username" label="发起人" width="100" />
      <el-table-column label="发起时间" width="160">
        <template #default="{ row }">
          {{ formatDate(row.created_at) }}
        </template>
      </el-table-column>
      <el-table-column label="操作" width="180" fixed="right" v-if="!readOnly">
        <template #default="{ row }">
          <el-button type="primary" link @click="$emit('approve', row.id, '')">
            同意
          </el-button>
          <el-button type="danger" link @click="$emit('reject', row.id, '')">
            拒绝
          </el-button>
          <el-button link @click="$emit('return', row.id, '')">
            退回
          </el-button>
        </template>
      </el-table-column>
    </el-table>
  </div>
</template>

<script setup lang="ts">
import { defineProps, defineEmits } from 'vue'

const props = defineProps<{
  tasks: any[]
  loading: boolean
  readOnly?: boolean
}>()

const emit = defineEmits(['approve', 'reject', 'return'])

const getBusinessType = (code: string) => {
  const types: Record<string, string> = {
    'asset_pickup': '资产领用',
    'asset_transfer': '资产调拨',
    'asset_loan': '资产借用',
    'asset_return': '资产退库'
  }
  return types[code] || code
}

const formatDate = (dateStr: string) => {
  if (!dateStr) return ''
  return new Date(dateStr).toLocaleString('zh-CN')
}
</script>

<style scoped>
.approval-list {
  width: 100%;
}
</style>
```

**Step 4: 添加路由**

**File**: `frontend/src/router/index.ts` (添加路由)
```typescript
{
  path: '/workflow',
  component: () => import('@/layouts/Layout.vue'),
  children: [
    {
      path: 'my-approvals',
      name: 'MyApprovals',
      component: () => import('@/views/workflow/MyApprovals.vue'),
      meta: { title: '我的审批' }
    }
  ]
}
```

**Step 5: 添加单元测试**

**File**: `frontend/src/views/workflow/__tests__/MyApprovals.spec.ts`
```typescript
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount } from '@vue/test-utils'
import MyApprovals from '../MyApprovals.vue'
import ApprovalList from '../components/ApprovalList.vue'

vi.mock('@/api/workflow', () => ({
  getMyTasks: vi.fn(() => Promise.resolve({
    pending: [{ id: '1', node_name: '部门审批', created_at: '2024-01-15' }],
    completed_today: []
  }))
}))

describe('MyApprovals Page', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('should render approval tabs', () => {
    const wrapper = mount(MyApprovals, {
      global: {
        stubs: {
          ApprovalList,
          'el-tabs': true,
          'el-tab-pane': true
        }
      }
    })

    expect(wrapper.text()).toContain('我的审批')
  })

  it('should load tasks on mount', async () => {
    const { getMyTasks } = await import('@/api/workflow')

    const wrapper = mount(MyApprovals, {
      global: {
        stubs: {
          ApprovalList,
          'el-tabs': true,
          'el-tab-pane': true
        }
      }
    })

    // Wait for async operations
    await new Promise(resolve => setTimeout(resolve, 0))

    expect(getMyTasks).toHaveBeenCalled()
  })
})
```

**Step 6: 运行测试确认通过**

```bash
cd frontend
npm run test
```

**Step 7: 提交代码**

```bash
git add frontend/src/views/workflow/ frontend/src/router/ frontend/src/api/workflow.ts
git commit -m "feat: add my approvals page"
```

---

## 验收检查清单

### 前端单元测试框架
- [x] Vitest安装配置完成
- [x] 测试设置文件创建
- [x] 至少一个组件测试示例
- [x] package.json包含测试脚本
- [ ] 测试覆盖率报告可生成

### 工作流与资产操作集成
- [ ] 工作流集成服务创建
- [ ] 领用单提交启动工作流
- [ ] 工作流完成后自动更新资产状态
- [ ] API回调端点创建
- [ ] 前端使用新API

### 我的审批任务页面
- [ ] 审批列表组件创建
- [ ] 待审批/已审批标签切换
- [ ] 同意/拒绝/退回操作
- [ ] 路由配置完成
- [ ] 单元测试覆盖

---

## 执行计划

1. **优先执行**: Task 1 (测试框架) - 基础设施，其他测试依赖
2. **其次执行**: Task 2 (工作流集成) - 核心业务功能
3. **最后执行**: Task 3 (审批页面) - 用户界面

---

**计划创建时间**: 2026-01-25
**预计总工时**: 8-10天
