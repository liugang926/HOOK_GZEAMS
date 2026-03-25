# Phase 3.1: LogicFlow流程设计器 - 测试方案

## 测试概览

| 测试类型 | 框架 | 覆盖范围 |
|---------|------|----------|
| 前端单元测试 | Vitest + Vue Test Utils | WorkflowDesigner, 节点配置组件 |
| 前端组件测试 | @vue/test-utils | 自定义节点, 属性面板 |
| API测试 | pytest + DRF APIClient | 工作流CRUD, 激活, 克隆 |
| E2E测试 | Playwright | 完整设计流程, 拖拽操作 |

---

## 1. 前端单元测试

### 1.1 WorkflowDesigner 组件测试

```javascript
// tests/workflows/WorkflowDesigner.spec.js

import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'
import WorkflowDesigner from '@/views/workflows/WorkflowDesigner.vue'
import { useWorkflowStore } from '@/stores/workflow'

// Mock LogicFlow
vi.mock('@logicflow/core', () => ({
  default: class MockLogicFlow {
    constructor() {
      this.graphData = { nodes: [], edges: [] }
    }
    render() {}
    on() {}
    off() {}
    getGraphData() { return this.graphData }
    setGraphData(data) { this.graphData = data }
    clearData() { this.graphData = { nodes: [], edges: [] } }
  }
}))

describe('WorkflowDesigner', () => {
  let wrapper
  let store

  beforeEach(() => {
    setActivePinia(createPinia())
    store = useWorkflowStore()
  })

  const createWrapper = (props = {}) => {
    return mount(WorkflowDesigner, {
      props: {
        workflowId: null,
        businessObject: 'asset_pickup',
        ...props
      },
      global: {
        stubs: ['el-drawer', 'el-button', 'el-form', 'el-form-item']
      }
    })
  }

  it('应正确初始化LogicFlow实例', async () => {
    const wrapper = createWrapper()
    await wrapper.vm.$nextTick()
    expect(wrapper.vm.lf).toBeTruthy()
  })

  it('应注册所有自定义节点', async () => {
    const wrapper = createWrapper()
    await wrapper.vm.$nextTick()
    const customNodes = ['start', 'approval', 'condition', 'cc', 'end']
    // 验证节点类型已注册
    expect(wrapper.vm.nodeTypes).toEqual(expect.arrayContaining(customNodes))
  })

  it('应加载已有工作流数据', async () => {
    const mockWorkflow = {
      id: 1,
      code: 'test_workflow',
      name: '测试流程',
      graph_data: {
        nodes: [
          { id: 'node_1', type: 'start', x: 100, y: 100, text: '开始' }
        ],
        edges: []
      }
    }

    store.currentWorkflow = mockWorkflow
    const wrapper = createWrapper({ workflowId: 1 })
    await wrapper.vm.$nextTick()

    expect(wrapper.vm.graphData).toEqual(mockWorkflow.graph_data)
  })

  it('应验证工作流数据有效性', () => {
    const wrapper = createWrapper()

    // 有效数据
    const validData = {
      nodes: [
        { id: 'node_1', type: 'start' },
        { id: 'node_2', type: 'end' }
      ],
      edges: [
        { sourceNodeId: 'node_1', targetNodeId: 'node_2' }
      ]
    }
    expect(wrapper.vm.validateGraphData(validData)).toBe(true)

    // 无效数据 - 缺少开始节点
    const invalidData1 = {
      nodes: [
        { id: 'node_1', type: 'approval' },
        { id: 'node_2', type: 'end' }
      ],
      edges: []
    }
    expect(wrapper.vm.validateGraphData(invalidData1)).toBe(false)

    // 无效数据 - 缺少结束节点
    const invalidData2 = {
      nodes: [
        { id: 'node_1', type: 'start' }
      ],
      edges: []
    }
    expect(wrapper.vm.validateGraphData(invalidData2)).toBe(false)
  })

  it('应正确保存工作流', async () => {
    const wrapper = createWrapper()
    const saveSpy = vi.spyOn(store, 'saveWorkflow').mockResolvedValue({
      id: 1,
      code: 'test_workflow'
    })

    wrapper.vm.workflowName = '新流程'
    wrapper.vm.graphData = {
      nodes: [
        { id: 'node_1', type: 'start', x: 100, y: 100 },
        { id: 'node_2', type: 'end', x: 300, y: 100 }
      ],
      edges: [
        { sourceNodeId: 'node_1', targetNodeId: 'node_2' }
      ]
    }

    await wrapper.vm.handleSave()

    expect(saveSpy).toHaveBeenCalled()
  })
})
```

### 1.2 节点配置组件测试

```javascript
// tests/workflows/ApprovalNodeConfig.spec.js

import { describe, it, expect, vi } from 'vitest'
import { mount } from '@vue/test-utils'
import ApprovalNodeConfig from '@/components/workflow/ApprovalNodeConfig.vue'

describe('ApprovalNodeConfig', () => {
  const mockNode = {
    id: 'node_1',
    type: 'approval',
    text: '部门审批',
    properties: {
      approveType: 'or',
      approvers: [],
      timeout: 72
    }
  }

  it('应正确显示节点属性', () => {
    const wrapper = mount(ApprovalNodeConfig, {
      props: { node: mockNode }
    })

    expect(wrapper.find('.node-name input').element.value).toBe('部门审批')
    expect(wrapper.vm.localProperties.approveType).toBe('or')
    expect(wrapper.vm.localProperties.timeout).toBe(72)
  })

  it('应切换审批方式', async () => {
    const wrapper = mount(ApprovalNodeConfig, {
      props: { node: mockNode }
    })

    await wrapper.vm.$nextTick()

    // 切换到会签
    const andOption = wrapper.findAll('.approve-type-option')[1]
    await andOption.trigger('click')

    expect(wrapper.vm.localProperties.approveType).toBe('and')
    expect(wrapper.emitted('update:properties')).toBeTruthy()
  })

  it('应添加审批人', async () => {
    const wrapper = mount(ApprovalNodeConfig, {
      props: { node: mockNode }
    })

    const newApprover = {
      type: 'user',
      user_id: 1,
      user_name: '张三'
    }

    wrapper.vm.addApprover(newApprover)
    await wrapper.vm.$nextTick()

    expect(wrapper.vm.localProperties.approvers).toContainEqual(newApprover)
  })

  it('应验证必填审批人', () => {
    const wrapper = mount(ApprovalNodeConfig, {
      props: {
        node: {
          ...mockNode,
          properties: {
            approveType: 'or',
            approvers: [],
            timeout: 72
          }
        }
      }
    })

    const result = wrapper.vm.validate()
    expect(result.valid).toBe(false)
    expect(result.errors).toContain('请选择审批人')
  })
})
```

### 1.3 ApproverSelector 测试

```javascript
// tests/workflows/ApproverSelector.spec.js

import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'
import ApproverSelector from '@/components/workflow/ApproverSelector.vue'
import { useUserStore } from '@/stores/user'

vi.mock('@/api/user', () => ({
  getUsers: () => Promise.resolve([
    { id: 1, name: '张三', department_id: 1 },
    { id: 2, name: '李四', department_id: 1 }
  ]),
  getDepartments: () => Promise.resolve([
    { id: 1, name: '技术部' },
    { id: 2, name: '财务部' }
  ])
}))

describe('ApproverSelector', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
  })

  it('应显示审批人类型选项', () => {
    const wrapper = mount(ApproverSelector, {
      props: {
        modelValue: { type: 'user', user_id: null }
      }
    })

    const types = wrapper.findAll('.approver-type-item')
    expect(types.length).toBeGreaterThanOrEqual(4) // user, role, leader, self_select
  })

  it('应选择指定成员', async () => {
    const wrapper = mount(ApproverSelector, {
      props: {
        modelValue: { type: 'user', user_id: null }
      }
    })

    await wrapper.vm.selectUser({ id: 1, name: '张三' })

    expect(wrapper.emitted('update:modelValue')).toBeTruthy()
    expect(wrapper.emitted('update:modelValue')[0][0]).toEqual({
      type: 'user',
      user_id: 1,
      user_name: '张三'
    })
  })

  it('应配置发起人领导', async () => {
    const wrapper = mount(ApproverSelector, {
      props: {
        modelValue: { type: 'leader' }
      }
    })

    // 选择直属上级
    await wrapper.vm.selectLeaderType('direct')

    expect(wrapper.emitted('update:modelValue')).toBeTruthy()
    expect(wrapper.emitted('update:modelValue')[0][0]).toEqual({
      type: 'leader',
      leader_type: 'direct',
      level: 1
    })
  })

  it('应配置自选范围', async () => {
    const wrapper = mount(ApproverSelector, {
      props: {
        modelValue: { type: 'self_select' }
      }
    })

    await wrapper.vm.setSelfSelectRange('department')
    await wrapper.vm.setApproverCount(1)

    expect(wrapper.emitted('update:modelValue')).toBeTruthy()
  })
})
```

### 1.4 条件节点配置测试

```javascript
// tests/workflows/ConditionNodeConfig.spec.js

import { describe, it, expect } from 'vitest'
import { mount } from '@vue/test-utils'
import ConditionNodeConfig from '@/components/workflow/ConditionNodeConfig.vue'

describe('ConditionNodeConfig', () => {
  const mockNode = {
    id: 'node_1',
    type: 'condition',
    text: '金额判断',
    properties: {
      branches: [
        {
          id: 'branch_1',
          name: '大于1万',
          conditions: [
            { field: 'amount', operator: 'gt', value: '10000' }
          ]
        }
      ],
      defaultFlow: false
    }
  }

  it('应显示所有分支', () => {
    const wrapper = mount(ConditionNodeConfig, {
      props: { node: mockNode }
    })

    const branches = wrapper.findAll('.condition-branch')
    expect(branches.length).toBe(1)
  })

  it('应添加新分支', async () => {
    const wrapper = mount(ConditionNodeConfig, {
      props: { node: mockNode }
    })

    wrapper.vm.addBranch()
    await wrapper.vm.$nextTick()

    expect(wrapper.vm.localProperties.branches.length).toBe(2)
  })

  it('应删除分支', async () => {
    const wrapper = mount(ConditionNodeConfig, {
      props: { node: mockNode }
    })

    wrapper.vm.removeBranch('branch_1')
    await wrapper.vm.$nextTick()

    expect(wrapper.vm.localProperties.branches.length).toBe(0)
  })

  it('应配置条件表达式', async () => {
    const wrapper = mount(ConditionNodeConfig, {
      props: { node: mockNode }
    })

    await wrapper.vm.updateCondition('branch_1', 0, {
      field: 'amount',
      operator: 'lt',
      value: '5000'
    })

    expect(wrapper.vm.localProperties.branches[0].conditions[0]).toEqual({
      field: 'amount',
      operator: 'lt',
      value: '5000'
    })
  })

  it('应验证条件配置', () => {
    const wrapper = mount(ConditionNodeConfig, {
      props: {
        node: {
          ...mockNode,
          properties: {
            branches: [
              {
                id: 'branch_1',
                name: '',
                conditions: []
              }
            ]
          }
        }
      }
    })

    const result = wrapper.vm.validate()
    expect(result.valid).toBe(false)
  })
})
```

---

## 2. API测试

### 2.1 Workflow API 测试

```python
# tests/workflows/test_api.py

import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient
from apps.workflows.models import WorkflowDefinition, WorkflowNode
from apps.organizations.models import Organization


@pytest.fixture
def api_client(db):
    return APIClient()


@pytest.fixture
def authenticated_client(api_client, user):
    api_client.force_authenticate(user=user)
    return api_client


@pytest.fixture
def organization(db):
    return Organization.objects.create(
        name="测试公司",
        code="TEST001"
    )


@pytest.fixture
def workflow_data(organization):
    return {
        'code': 'asset_pickup_approval',
        'name': '资产领用审批',
        'business_object': 'asset_pickup',
        'graph_data': {
            'nodes': [
                {
                    'id': 'node_1',
                    'type': 'start',
                    'x': 100,
                    'y': 100,
                    'text': '开始'
                },
                {
                    'id': 'node_2',
                    'type': 'approval',
                    'x': 300,
                    'y': 100,
                    'text': '部门审批',
                    'properties': {
                        'approveType': 'or',
                        'approvers': [],
                        'timeout': 72
                    }
                }
            ],
            'edges': [
                {
                    'id': 'edge_1',
                    'sourceNodeId': 'node_1',
                    'targetNodeId': 'node_2',
                    'type': 'polyline'
                }
            ]
        },
        'description': '资产领用审批流程'
    }


class TestWorkflowAPI:
    """工作流API测试"""

    def test_list_workflows(self, authenticated_client, organization):
        """测试获取工作流列表"""
        WorkflowDefinition.objects.create(
            organization=organization,
            code='test_workflow',
            name='测试流程',
            business_object='asset_pickup'
        )

        url = reverse('workflow-list')
        response = authenticated_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data['count'] >= 1

    def test_create_workflow(self, authenticated_client, workflow_data):
        """测试创建工作流"""
        url = reverse('workflow-list')
        response = authenticated_client.post(url, workflow_data, format='json')

        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['code'] == 'asset_pickup_approval'
        assert response.data['version'] == 1

        # 验证数据库
        workflow = WorkflowDefinition.objects.get(code='asset_pickup_approval')
        assert workflow.name == '资产领用审批'

    def test_create_duplicate_code_fails(self, authenticated_client, workflow_data):
        """测试重复编码失败"""
        url = reverse('workflow-list')

        # 第一次创建成功
        response1 = authenticated_client.post(url, workflow_data, format='json')
        assert response1.status_code == status.HTTP_201_CREATED

        # 第二次创建失败
        response2 = authenticated_client.post(url, workflow_data, format='json')
        assert response2.status_code == status.HTTP_400_BAD_REQUEST

    def test_update_workflow(self, authenticated_client, workflow_data):
        """测试更新工作流"""
        # 先创建
        workflow = WorkflowDefinition.objects.create(**workflow_data)

        url = reverse('workflow-detail', kwargs={'pk': workflow.id})
        update_data = {'name': '资产领用审批（新版）'}
        response = authenticated_client.patch(url, update_data, format='json')

        assert response.status_code == status.HTTP_200_OK
        assert response.data['name'] == '资产领用审批（新版）'

    def test_delete_workflow(self, authenticated_client, workflow_data):
        """测试删除工作流"""
        workflow = WorkflowDefinition.objects.create(**workflow_data)

        url = reverse('workflow-detail', kwargs={'pk': workflow.id})
        response = authenticated_client.delete(url)

        assert response.status_code == status.HTTP_204_NO_CONTENT

        # 验证软删除
        workflow.refresh_from_db()
        assert workflow.is_deleted is True

    def test_activate_workflow(self, authenticated_client, workflow_data):
        """测试激活工作流"""
        workflow = WorkflowDefinition.objects.create(
            **workflow_data,
            is_enabled=False,
            is_default=False
        )

        url = reverse('workflow-activate', kwargs={'pk': workflow.id})
        response = authenticated_client.post(url)

        assert response.status_code == status.HTTP_200_OK

        workflow.refresh_from_db()
        assert workflow.is_enabled is True

    def test_clone_workflow(self, authenticated_client, workflow_data):
        """测试克隆工作流"""
        workflow = WorkflowDefinition.objects.create(**workflow_data)

        url = reverse('workflow-clone', kwargs={'pk': workflow.id})
        response = authenticated_client.post(url)

        assert response.status_code == status.HTTP_201_CREATED
        assert 'copy' in response.data['code']
        assert response.data['name'].endswith('(副本)')

        # 验证原工作流仍存在
        assert WorkflowDefinition.objects.filter(code=workflow_data['code']).exists()

    def test_get_by_business_object(self, authenticated_client, workflow_data):
        """测试根据业务对象获取工作流"""
        WorkflowDefinition.objects.create(
            **workflow_data,
            is_enabled=True
        )

        url = reverse('workflow-by-business-object')
        response = authenticated_client.get(url, {'business_object': 'asset_pickup'})

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['results']) >= 1

    def test_validate_graph_data_missing_nodes(self, authenticated_client):
        """测试验证无效图数据 - 缺少节点"""
        url = reverse('workflow-list')
        invalid_data = {
            'code': 'invalid_workflow',
            'name': '无效流程',
            'business_object': 'asset_pickup',
            'graph_data': {'edges': []}  # 缺少nodes
        }

        response = authenticated_client.post(url, invalid_data, format='json')
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_validate_graph_data_missing_edges(self, authenticated_client):
        """测试验证无效图数据 - 缺少边"""
        url = reverse('workflow-list')
        invalid_data = {
            'code': 'invalid_workflow',
            'name': '无效流程',
            'business_object': 'asset_pickup',
            'graph_data': {'nodes': []}  # 缺少edges
        }

        response = authenticated_client.post(url, invalid_data, format='json')
        assert response.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.django_db
class TestWorkflowValidation:
    """工作流数据验证测试"""

    def test_workflow_must_have_start_node(self, authenticated_client):
        """工作流必须包含开始节点"""
        url = reverse('workflow-list')
        data = {
            'code': 'no_start_workflow',
            'name': '无开始节点流程',
            'business_object': 'asset_pickup',
            'graph_data': {
                'nodes': [
                    {'id': 'node_1', 'type': 'approval', 'x': 100, 'y': 100}
                ],
                'edges': []
            }
        }

        response = authenticated_client.post(url, data, format='json')
        # 前端验证或后端验证应捕获此错误

    def test_workflow_must_have_end_node(self, authenticated_client):
        """工作流必须包含结束节点"""
        url = reverse('workflow-list')
        data = {
            'code': 'no_end_workflow',
            'name': '无结束节点流程',
            'business_object': 'asset_pickup',
            'graph_data': {
                'nodes': [
                    {'id': 'node_1', 'type': 'start', 'x': 100, 'y': 100}
                ],
                'edges': []
            }
        }

        response = authenticated_client.post(url, data, format='json')
        # 前端验证或后端验证应捕获此错误
```

### 2.2 工作流模型测试

```python
# tests/workflows/test_models.py

import pytest
from apps.workflows.models import WorkflowDefinition, WorkflowNode, FieldPermission


class TestWorkflowDefinition:
    """工作流定义模型测试"""

    def test_activate_sets_default(self, db, organization):
        """测试激活工作流设置默认"""
        workflow1 = WorkflowDefinition.objects.create(
            organization=organization,
            code='workflow1',
            name='流程1',
            business_object='asset_pickup',
            is_default=True
        )
        workflow2 = WorkflowDefinition.objects.create(
            organization=organization,
            code='workflow2',
            name='流程2',
            business_object='asset_pickup',
            is_default=False
        )

        # 激活workflow2，应将workflow1设为非默认
        workflow2.activate()
        workflow1.refresh_from_db()

        assert workflow2.is_enabled is True
        assert workflow1.is_default is False

    def test_version_auto_increment(self, db, organization):
        """测试版本自动递增"""
        workflow = WorkflowDefinition.objects.create(
            organization=organization,
            code='version_test',
            name='版本测试',
            business_object='asset_pickup'
        )

        assert workflow.version == 1


class TestWorkflowNode:
    """工作流节点模型测试"""

    def test_node_unique_constraint(self, db, organization):
        """测试节点唯一约束"""
        workflow = WorkflowDefinition.objects.create(
            organization=organization,
            code='node_test',
            name='节点测试',
            business_object='asset_pickup'
        )

        WorkflowNode.objects.create(
            workflow=workflow,
            node_id='node_1',
            node_type='approval',
            node_name='审批节点'
        )

        # 相同workflow和node_id不能重复
        with pytest.raises(Exception):
            WorkflowNode.objects.create(
                workflow=workflow,
                node_id='node_1',
                node_type='condition',
                node_name='条件节点'
            )

    def test_field_permission_unique_constraint(self, db, organization):
        """测试字段权限唯一约束"""
        workflow = WorkflowDefinition.objects.create(
            organization=organization,
            code='permission_test',
            name='权限测试',
            business_object='asset_pickup'
        )
        node = WorkflowNode.objects.create(
            workflow=workflow,
            node_id='node_1',
            node_type='approval',
            node_name='审批节点'
        )

        FieldPermission.objects.create(
            node=node,
            field_code='amount',
            field_name='金额',
            permission='read_only'
        )

        # 相同node和field_code不能重复
        with pytest.raises(Exception):
            FieldPermission.objects.create(
                node=node,
                field_code='amount',
                field_name='金额',
                permission='editable'
            )
```

---

## 3. E2E测试

### 3.1 工作流设计器E2E测试

```javascript
// tests/e2e/workflows/designer.spec.js

import { test, expect, Page } from '@playwright/test'

test.describe('工作流设计器', () => {
  let page: Page

  test.beforeEach(async ({ page }) => {
    // 登录
    await page.goto('/login')
    await page.fill('[name="username"]', 'admin')
    await page.fill('[name="password"]', 'admin123')
    await page.click('button[type="submit"]')
    await page.waitForURL('/dashboard')
  })

  test('应打开工作流设计器', async ({ page }) => {
    await page.goto('/workflows')
    await page.click('text=新建流程')

    await expect(page.locator('.workflow-designer')).toBeVisible()
    await expect(page.locator('.lf-container')).toBeVisible()
  })

  test('应从面板拖拽节点到画布', async ({ page }) => {
    await page.goto('/workflows/new?business_object=asset_pickup')

    // 拖拽开始节点
    const startNode = page.locator('.node-panel-item[data-type="start"]')
    const canvas = page.locator('.lf-container')

    await startNode.dragTo(canvas, {
      targetPosition: { x: 100, y: 100 }
    })

    // 验证节点已添加到画布
    await expect(page.locator('.lf-node[data-type="start"]')).toBeVisible()
  })

  test('应连接两个节点', async ({ page }) => {
    await page.goto('/workflows/new?business_object=asset_pickup')

    // 添加两个节点
    const startNode = page.locator('.node-panel-item[data-type="start"]')
    const approvalNode = page.locator('.node-panel-item[data-type="approval"]')
    const canvas = page.locator('.lf-container')

    await startNode.dragTo(canvas, { targetPosition: { x: 100, y: 100 } })
    await approvalNode.dragTo(canvas, { targetPosition: { x: 300, y: 100 } })

    await page.waitForTimeout(500)

    // 连接节点（拖拽锚点）
    const sourceAnchor = page.locator('.lf-node[data-type="start"] .lf-node-anchor')
    const targetNode = page.locator('.lf-node[data-type="approval"]')

    await sourceAnchor.dragTo(targetNode)

    // 验证连线已创建
    await expect(page.locator('.lf-edge')).toHaveCount(1)
  })

  test('应配置审批节点属性', async ({ page }) => {
    await page.goto('/workflows/new?business_object=asset_pickup')

    // 添加审批节点
    const approvalNode = page.locator('.node-panel-item[data-type="approval"]')
    await approvalNode.dragTo(page.locator('.lf-container'), {
      targetPosition: { x: 200, y: 100 }
    })

    await page.waitForTimeout(500)

    // 点击节点打开属性面板
    await page.click('.lf-node[data-type="approval"]')

    // 等待属性面板加载
    await expect(page.locator('.property-panel')).toBeVisible()

    // 设置节点名称
    await page.fill('.node-name input', '部门审批')
    await expect(page.locator('.node-name input')).toHaveValue('部门审批')

    // 选择审批方式
    await page.click('.approve-type-option[value="or"]')

    // 验证选中状态
    await expect(page.locator('.approve-type-option.active')).toHaveCount(1)
  })

  test('应添加审批人', async ({ page }) => {
    await page.goto('/workflows/new?business_object=asset_pickup')

    // 添加并点击审批节点
    const approvalNode = page.locator('.node-panel-item[data-type="approval"]')
    await approvalNode.dragTo(page.locator('.lf-container'), {
      targetPosition: { x: 200, y: 100 }
    })
    await page.waitForTimeout(500)
    await page.click('.lf-node[data-type="approval"]')

    // 点击添加审批人按钮
    await page.click('.add-approver-btn')

    // 选择审批人类型
    await page.click('.approver-type-item[value="user"]')

    // 打开用户选择器
    await page.click('.user-selector-trigger')

    // 搜索并选择用户
    await page.fill('.user-search-input', '张三')
    await page.click('.user-option:has-text("张三")')

    // 验证审批人已添加
    await expect(page.locator('.approver-item')).toBeVisible()
  })

  test('应保存工作流', async ({ page }) => {
    await page.goto('/workflows/new?business_object=asset_pickup')

    // 创建简单流程
    const startNode = page.locator('.node-panel-item[data-type="start"]')
    const endNode = page.locator('.node-panel-item[data-type="end"]')
    const canvas = page.locator('.lf-container')

    await startNode.dragTo(canvas, { targetPosition: { x: 100, y: 100 } })
    await endNode.dragTo(canvas, { targetPosition: { x: 300, y: 100 } })
    await page.waitForTimeout(500)

    // 连接节点
    const sourceAnchor = page.locator('.lf-node[data-type="start"] .lf-node-anchor')
    const target = page.locator('.lf-node[data-type="end"]')
    await sourceAnchor.dragTo(target)

    // 填写流程信息
    await page.fill('.workflow-code-input', 'test_approval_flow')
    await page.fill('.workflow-name-input', '测试审批流程')

    // 保存
    await page.click('.save-workflow-btn')

    // 验证保存成功提示
    await expect(page.locator('.el-message--success')).toBeVisible()

    // 验证跳转到列表页
    await page.waitForURL('/workflows')
  })

  test('应加载并编辑已有工作流', async ({ page }) => {
    await page.goto('/workflows')

    // 点击编辑按钮
    await page.click('.workflow-item:first-child .edit-btn')

    // 验证画布已加载节点
    await expect(page.locator('.lf-node')).toHaveCount(2)

    // 修改节点名称
    await page.click('.lf-node[data-type="approval"]')
    await page.fill('.node-name input', '财务审批')
    await page.click('.save-workflow-btn')

    // 验证保存成功
    await expect(page.locator('.el-message--success')).toBeVisible()
  })

  test('应克隆工作流', async ({ page }) => {
    await page.goto('/workflows')

    // 点击克隆按钮
    await page.click('.workflow-item:first-child .clone-btn')

    // 验证克隆确认对话框
    await expect(page.locator('.el-dialog:has-text("克隆工作流")')).toBeVisible()

    // 确认克隆
    await page.click('.el-dialog .confirm-btn')

    // 验证克隆成功
    await expect(page.locator('.el-message--success')).toBeVisible()
  })

  test('应删除工作流', async ({ page }) => {
    await page.goto('/workflows')

    // 获取初始工作流数量
    const initialCount = await page.locator('.workflow-item').count()

    // 点击删除按钮
    await page.click('.workflow-item:first-child .delete-btn')

    // 确认删除
    await page.click('.el-message-box .confirm-btn')

    // 验证删除成功
    await expect(page.locator('.workflow-item')).toHaveCount(initialCount - 1)
  })

  test('应验证流程完整性', async ({ page }) => {
    await page.goto('/workflows/new?business_object=asset_pickup')

    // 只添加开始节点
    const startNode = page.locator('.node-panel-item[data-type="start"]')
    await startNode.dragTo(page.locator('.lf-container'), {
      targetPosition: { x: 100, y: 100 }
    })

    // 尝试保存
    await page.fill('.workflow-code-input', 'invalid_flow')
    await page.fill('.workflow-name-input', '无效流程')
    await page.click('.save-workflow-btn')

    // 验证错误提示
    await expect(page.locator('.el-message--error:has-text("结束节点")')).toBeVisible()
  })
})

test.describe('条件节点配置', () => {
  test('应配置条件分支', async ({ page }) => {
    await page.goto('/workflows/new?business_object=asset_pickup')

    // 添加条件节点
    const conditionNode = page.locator('.node-panel-item[data-type="condition"]')
    await conditionNode.dragTo(page.locator('.lf-container'), {
      targetPosition: { x: 200, y: 100 }
    })
    await page.waitForTimeout(500)
    await page.click('.lf-node[data-type="condition"]')

    // 添加分支
    await page.click('.add-branch-btn')

    // 配置第一个分支条件
    await page.fill('.branch-name-input:first', '金额大于1万')
    await page.selectOption('.condition-field-select:first', 'amount')
    await page.selectOption('.condition-operator-select:first', 'gt')
    await page.fill('.condition-value-input:first', '10000')

    // 保存配置
    await page.click('.save-node-config-btn')

    // 验证节点显示分支信息
    await expect(page.locator('.lf-node[data-type="condition"]')).toContainText('金额大于1万')
  })
})
```

### 3.2 工作流列表E2E测试

```javascript
// tests/e2e/workflows/list.spec.js

import { test, expect } from '@playwright/test'

test.describe('工作流列表', () => {
  test.beforeEach(async ({ page }) => {
    // 登录
    await page.goto('/login')
    await page.fill('[name="username"]', 'admin')
    await page.fill('[name="password"]', 'admin123')
    await page.click('button[type="submit"]')
  })

  test('应显示工作流列表', async ({ page }) => {
    await page.goto('/workflows')

    await expect(page.locator('.workflow-list')).toBeVisible()
    await expect(page.locator('.workflow-item')).toHaveCount(3)
  })

  test('应按业务对象筛选', async ({ page }) => {
    await page.goto('/workflows')

    // 选择业务对象筛选
    await page.selectOption('.business-object-filter', 'asset_pickup')

    // 验证筛选结果
    const items = page.locator('.workflow-item')
    const count = await items.count()

    for (let i = 0; i < count; i++) {
      await expect(items.nth(i)).toContainText('asset_pickup')
    }
  })

  test('应搜索工作流', async ({ page }) => {
    await page.goto('/workflows')

    // 输入搜索关键词
    await page.fill('.workflow-search-input', '领用')
    await page.click('.search-btn')

    // 验证搜索结果
    await expect(page.locator('.workflow-item:first-child')).toContainText('领用')
  })

  test('应切换启用状态', async ({ page }) => {
    await page.goto('/workflows')

    // 获取第一个工作流的初始状态
    const statusToggle = page.locator('.workflow-item:first-child .status-toggle')
    const initialClass = await statusToggle.getAttribute('class')

    // 点击切换
    await statusToggle.click()

    // 验证状态已变更
    await expect(page.locator('.workflow-item:first-child .status-toggle')).not.toHaveAttribute('class', initialClass)
  })
})
```

---

## 4. 测试数据

### 4.1 Fixture数据

```python
# tests/workflows/fixtures.py

import pytest
from apps.workflows.models import WorkflowDefinition, WorkflowNode


@pytest.fixture
def sample_workflow_graph():
    """示例工作流图数据"""
    return {
        'nodes': [
            {
                'id': 'start_1',
                'type': 'start',
                'x': 100,
                'y': 150,
                'text': '开始'
            },
            {
                'id': 'approval_1',
                'type': 'approval',
                'x': 300,
                'y': 150,
                'text': '部门审批',
                'properties': {
                    'approveType': 'or',
                    'approvers': [
                        {'type': 'user', 'user_id': 1, 'user_name': '张三'}
                    ],
                    'timeout': 72,
                    'timeoutAction': 'transfer'
                }
            },
            {
                'id': 'condition_1',
                'type': 'condition',
                'x': 500,
                'y': 150,
                'text': '金额判断',
                'properties': {
                    'branches': [
                        {
                            'id': 'branch_1',
                            'name': '大于1万',
                            'conditions': [
                                {'field': 'amount', 'operator': 'gt', 'value': '10000'}
                            ]
                        },
                        {
                            'id': 'branch_2',
                            'name': '小于等于1万',
                            'conditions': [
                                {'field': 'amount', 'operator': 'lte', 'value': '10000'}
                            ]
                        }
                    ],
                    'defaultFlow': False
                }
            },
            {
                'id': 'approval_2',
                'type': 'approval',
                'x': 700,
                'y': 100,
                'text': '财务审批',
                'properties': {
                    'approveType': 'and',
                    'approvers': [
                        {'type': 'role', 'role_id': 3, 'role_name': '财务'}
                    ]
                }
            },
            {
                'id': 'end_1',
                'type': 'end',
                'x': 900,
                'y': 150,
                'text': '结束'
            }
        ],
        'edges': [
            {'id': 'edge_1', 'sourceNodeId': 'start_1', 'targetNodeId': 'approval_1', 'type': 'polyline'},
            {'id': 'edge_2', 'sourceNodeId': 'approval_1', 'targetNodeId': 'condition_1', 'type': 'polyline'},
            {'id': 'edge_3', 'sourceNodeId': 'condition_1', 'targetNodeId': 'approval_2', 'type': 'polyline'},
            {'id': 'edge_4', 'sourceNodeId': 'condition_1', 'targetNodeId': 'end_1', 'type': 'polyline'},
            {'id': 'edge_5', 'sourceNodeId': 'approval_2', 'targetNodeId': 'end_1', 'type': 'polyline'}
        ]
    }


@pytest.fixture
def complex_workflow_graph():
    """复杂工作流图数据（包含抄送、条件、多级审批）"""
    return {
        'nodes': [
            {
                'id': 'start_1',
                'type': 'start',
                'x': 100,
                'y': 200,
                'text': '开始'
            },
            {
                'id': 'approval_1',
                'type': 'approval',
                'x': 300,
                'y': 200,
                'text': '主管审批',
                'properties': {
                    'approveType': 'or',
                    'approvers': [
                        {'type': 'leader', 'leader_type': 'direct', 'level': 1}
                    ],
                    'timeout': 24
                }
            },
            {
                'id': 'cc_1',
                'type': 'cc',
                'x': 500,
                'y': 200,
                'text': '抄送财务',
                'properties': {
                    'ccUsers': [
                        {'type': 'role', 'role_id': 3, 'role_name': '财务'}
                    ],
                    'ccType': 'after_approve'
                }
            },
            {
                'id': 'condition_1',
                'type': 'condition',
                'x': 700,
                'y': 200,
                'text': '金额条件',
                'properties': {
                    'branches': [
                        {
                            'id': 'branch_1',
                            'name': '大于5万',
                            'conditions': [
                                {'field': 'amount', 'operator': 'gt', 'value': '50000'}
                            ]
                        },
                        {
                            'id': 'branch_2',
                            'name': '小于等于5万',
                            'conditions': [
                                {'field': 'amount', 'operator': 'lte', 'value': '50000'}
                            ]
                        }
                    ]
                }
            },
            {
                'id': 'approval_2',
                'type': 'approval',
                'x': 900,
                'y': 150,
                'text': '总经理审批',
                'properties': {
                    'approveType': 'seq',
                    'approvers': [
                        {'type': 'user', 'user_id': 10, 'user_name': '总经理'}
                    ]
                }
            },
            {
                'id': 'approval_3',
                'type': 'approval',
                'x': 900,
                'y': 250,
                'text': '总监审批',
                'properties': {
                    'approveType': 'seq',
                    'approvers': [
                        {'type': 'role', 'role_id': 5, 'role_name': '总监'}
                    ]
                }
            },
            {
                'id': 'end_1',
                'type': 'end',
                'x': 1100,
                'y': 200,
                'text': '结束'
            }
        ],
        'edges': [
            {'id': 'e1', 'sourceNodeId': 'start_1', 'targetNodeId': 'approval_1'},
            {'id': 'e2', 'sourceNodeId': 'approval_1', 'targetNodeId': 'cc_1'},
            {'id': 'e3', 'sourceNodeId': 'cc_1', 'targetNodeId': 'condition_1'},
            {'id': 'e4', 'sourceNodeId': 'condition_1', 'targetNodeId': 'approval_2'},
            {'id': 'e5', 'sourceNodeId': 'condition_1', 'targetNodeId': 'approval_3'},
            {'id': 'e6', 'sourceNodeId': 'approval_2', 'targetNodeId': 'end_1'},
            {'id': 'e7', 'sourceNodeId': 'approval_3', 'targetNodeId': 'end_1'}
        ]
    }
```

---

## 测试执行

### 运行命令

```bash
# 前端单元测试
npm run test:unit -- workflows

# API测试
pytest tests/workflows/test_api.py -v

# E2E测试
npm run test:e2e -- workflows

# 完整测试套件
npm run test:phase3.1
```

---

## 后续任务

1. Phase 3.2: 实现工作流执行引擎
2. Phase 4.1: 实现QR码扫描盘点
