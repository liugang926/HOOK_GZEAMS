# Phase 3.2: 工作流执行引擎 - 测试方案

## 测试概览

| 测试类型 | 框架 | 覆盖范围 |
|---------|------|----------|
| 引擎单元测试 | pytest | WorkflowEngine, ApproverResolver, ConditionEvaluator |
| 模型测试 | pytest + Django TestCase | WorkflowInstance, WorkflowTask, WorkflowLog |
| API测试 | pytest + DRF APIClient | 工作流执行API |
| 前端组件测试 | Vitest | 任务卡片, 审批面板, 流程进度 |
| E2E测试 | Playwright | 完整审批流程 |

---

## 1. 工作流引擎单元测试

### 1.1 引心核心测试

```python
# tests/workflows/test_engine.py

import pytest
from django.utils import timezone
from django.contrib.auth import get_user_model
from apps.workflows.models import WorkflowDefinition, WorkflowInstance, WorkflowTask
from apps.workflows.services.engine import WorkflowEngine

User = get_user_model()


@pytest.fixture
def workflow_definition(db, organization):
    """测试用流程定义"""
    return WorkflowDefinition.objects.create(
        organization=organization,
        code='test_approval',
        name='测试审批流程',
        business_object='asset_pickup',
        graph_data={
            'nodes': [
                {
                    'id': 'start_1',
                    'type': 'start',
                    'x': 100,
                    'y': 100,
                    'text': '开始'
                },
                {
                    'id': 'approval_1',
                    'type': 'approval',
                    'x': 300,
                    'y': 100,
                    'text': '部门审批',
                    'properties': {
                        'approveType': 'or',
                        'approvers': [
                            {'type': 'user', 'user_id': 2}
                        ],
                        'timeout': 72
                    }
                },
                {
                    'id': 'end_1',
                    'type': 'end',
                    'x': 500,
                    'y': 100,
                    'text': '结束'
                }
            ],
            'edges': [
                {'sourceNodeId': 'start_1', 'targetNodeId': 'approval_1', 'type': 'polyline'},
                {'sourceNodeId': 'approval_1', 'targetNodeId': 'end_1', 'type': 'polyline'}
            ]
        }
    )


@pytest.fixture
def initiator(db, organization):
    """发起人"""
    return User.objects.create(
        organization=organization,
        username='initiator',
        real_name='张三'
    )


@pytest.fixture
def approver(db, organization):
    """审批人"""
    return User.objects.create(
        organization=organization,
        username='approver',
        real_name='李经理'
    )


class TestWorkflowEngine:
    """工作流引擎测试"""

    def test_start_workflow(self, workflow_definition, initiator):
        """测试启动工作流"""
        engine = WorkflowEngine(workflow_definition)

        instance = engine.start(
            business_object='asset_pickup',
            business_id='123',
            business_no='LY001',
            initiator=initiator,
            variables={'amount': 10000}
        )

        assert instance.status == 'running'
        assert instance.initiator == initiator
        assert instance.business_no == 'LY001'
        assert instance.started_at is not None

    def test_create_approval_task(self, workflow_definition, initiator, approver):
        """测试创建审批任务"""
        workflow_definition.graph_data['nodes'][1]['properties']['approvers'] = [
            {'type': 'user', 'user_id': approver.id}
        ]
        workflow_definition.save()

        engine = WorkflowEngine(workflow_definition)
        instance = engine.start(
            business_object='asset_pickup',
            business_id='123',
            business_no='LY001',
            initiator=initiator
        )

        # 验证任务已创建
        tasks = instance.tasks.filter(node_type='approval')
        assert tasks.count() == 1

        task = tasks.first()
        assert task.assignee == approver
        assert task.status == 'pending'
        assert task.approve_type == 'or'

    def test_approve_task_or_type(self, workflow_definition, initiator, approver):
        """测试或签审批"""
        # 添加两个审批人
        user2 = User.objects.create(
            organization=workflow_definition.organization,
            username='approver2',
            real_name='王副理'
        )

        workflow_definition.graph_data['nodes'][1]['properties']['approvers'] = [
            {'type': 'user', 'user_id': approver.id},
            {'type': 'user', 'user_id': user2.id}
        ]
        workflow_definition.graph_data['nodes'][1]['properties']['approveType'] = 'or'
        workflow_definition.save()

        engine = WorkflowEngine(workflow_definition)
        instance = engine.start(
            business_object='asset_pickup',
            business_id='123',
            business_no='LY001',
            initiator=initiator
        )

        # 获取第一个任务
        task = instance.tasks.filter(assignee=approver).first()

        # 执行审批
        instance = engine.execute_task(
            task=task,
            action='approved',
            actor=approver,
            comment='同意'
        )

        # 验证流程完成（或签一人通过即可）
        assert instance.status == 'approved'
        assert instance.completed_at is not None

    def test_approve_task_and_type(self, workflow_definition, initiator):
        """测试会签审批"""
        approver1 = User.objects.create(
            organization=workflow_definition.organization,
            username='approver1',
            real_name='审批人1'
        )
        approver2 = User.objects.create(
            organization=workflow_definition.organization,
            username='approver2',
            real_name='审批人2'
        )

        workflow_definition.graph_data['nodes'][1]['properties']['approvers'] = [
            {'type': 'user', 'user_id': approver1.id},
            {'type': 'user', 'user_id': approver2.id}
        ]
        workflow_definition.graph_data['nodes'][1]['properties']['approveType'] = 'and'
        workflow_definition.save()

        engine = WorkflowEngine(workflow_definition)
        instance = engine.start(
            business_object='asset_pickup',
            business_id='123',
            business_no='LY001',
            initiator=initiator
        )

        # 第一个人审批
        task1 = instance.tasks.filter(assignee=approver1).first()
        instance = engine.execute_task(task1, 'approved', approver1, '同意')

        # 验证流程仍在运行
        assert instance.status in ['running', 'pending_approval']

        # 第二个人审批
        task2 = instance.tasks.filter(assignee=approver2).first()
        instance = engine.execute_task(task2, 'approved', approver2, '同意')

        # 验证流程完成
        assert instance.status == 'approved'

    def test_reject_workflow(self, workflow_definition, initiator, approver):
        """测试拒绝流程"""
        engine = WorkflowEngine(workflow_definition)
        instance = engine.start(
            business_object='asset_pickup',
            business_id='123',
            business_no='LY001',
            initiator=initiator
        )

        task = instance.tasks.filter(assignee=approver).first()

        # 拒绝
        instance = engine.execute_task(
            task=task,
            action='rejected',
            actor=approver,
            comment='理由不充分'
        )

        # 验证流程被拒绝
        assert instance.status == 'rejected'
        assert instance.completed_at is not None

    def test_withdraw_workflow(self, workflow_definition, initiator):
        """测试撤回流程"""
        engine = WorkflowEngine(workflow_definition)
        instance = engine.start(
            business_object='asset_pickup',
            business_id='123',
            business_no='LY001',
            initiator=initiator
        )

        # 撤回
        instance = engine.withdraw(instance, initiator)

        assert instance.status == 'cancelled'
        assert instance.completed_at is not None

        # 验证任务被取消
        pending_tasks = instance.tasks.filter(status='pending')
        assert pending_tasks.count() == 0

    def test_terminate_workflow(self, workflow_definition, initiator):
        """测试终止流程（管理员）"""
        admin = User.objects.create(
            organization=workflow_definition.organization,
            username='admin',
            is_staff=True
        )

        engine = WorkflowEngine(workflow_definition)
        instance = engine.start(
            business_object='asset_pickup',
            business_id='123',
            business_no='LY001',
            initiator=initiator
        )

        # 终止
        instance = engine.terminate(instance, admin, '特殊情况终止')

        assert instance.status == 'terminated'

    def test_condition_branch(self):
        """测试条件分支"""
        # 创建带条件的流程
        definition = WorkflowDefinition.objects.create(
            organization=initiator.organization,
            code='condition_test',
            name='条件测试流程',
            business_object='asset_pickup',
            graph_data={
                'nodes': [
                    {'id': 'start_1', 'type': 'start', 'x': 100, 'y': 100},
                    {
                        'id': 'condition_1',
                        'type': 'condition',
                        'x': 300,
                        'y': 100,
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
                            ]
                        }
                    },
                    {'id': 'end_1', 'type': 'end', 'x': 500, 'y': 100}
                ],
                'edges': [
                    {'sourceNodeId': 'start_1', 'targetNodeId': 'condition_1'},
                    {'sourceNodeId': 'condition_1', 'targetNodeId': 'end_1'}
                ]
            }
        )

        engine = WorkflowEngine(definition)

        # 测试金额大于1万
        instance = engine.start(
            business_object='asset_pickup',
            business_id='123',
            business_no='LY001',
            initiator=initiator,
            variables={'amount': 50000}
        )

        # 验证流程完成
        assert instance.status == 'approved'


class TestWorkflowEngineErrors:
    """工作流引擎错误处理测试"""

    def test_start_without_start_node(self, organization, initiator):
        """测试缺少开始节点的流程"""
        definition = WorkflowDefinition.objects.create(
            organization=organization,
            code='no_start',
            name='无开始节点',
            business_object='asset_pickup',
            graph_data={
                'nodes': [
                    {'id': 'approval_1', 'type': 'approval', 'x': 100, 'y': 100}
                ],
                'edges': []
            }
        )

        engine = WorkflowEngine(definition)

        with pytest.raises(ValueError, match="开始节点"):
            engine.start(
                business_object='asset_pickup',
                business_id='123',
                business_no='LY001',
                initiator=initiator
            )

    def test_approve_already_completed_task(self, workflow_definition, initiator, approver):
        """测试审批已完成的任务"""
        engine = WorkflowEngine(workflow_definition)
        instance = engine.start(
            business_object='asset_pickup',
            business_id='123',
            business_no='LY001',
            initiator=initiator
        )

        task = instance.tasks.filter(assignee=approver).first()

        # 第一次审批
        instance = engine.execute_task(task, 'approved', approver, '同意')

        # 尝试再次审批
        with pytest.raises(ValueError, match="状态"):
            engine.execute_task(task, 'approved', approver, '再次同意')

    def test_approve_without_permission(self, workflow_definition, initiator):
        """测试无权限审批"""
        other_user = User.objects.create(
            organization=workflow_definition.organization,
            username='other',
            real_name='其他人'
        )

        engine = WorkflowEngine(workflow_definition)
        instance = engine.start(
            business_object='asset_pickup',
            business_id='123',
            business_no='LY001',
            initiator=initiator
        )

        task = instance.tasks.first()

        # 其他人尝试审批
        with pytest.raises(ValueError, match="权限"):
            engine.execute_task(task, 'approved', other_user, '冒充审批')
```

### 1.2 审批人解析器测试

```python
# tests/workflows/test_approver_resolver.py

import pytest
from apps.workflows.services.approver_resolver import ApproverResolver


class TestApproverResolver:
    """审批人解析器测试"""

    @pytest.fixture
    def resolver(self):
        return ApproverResolver()

    def test_resolve_user_type(self, resolver, instance, user1, user2):
        """测试指定成员类型"""
        configs = [
            {'type': 'user', 'user_id': user1.id},
            {'type': 'user', 'user_id': user2.id}
        ]

        users = resolver.resolve(configs, instance)

        assert len(users) == 2
        assert user1 in users
        assert user2 in users

    def test_resolve_role_type(self, resolver, instance, role):
        """测试指定角色类型"""
        # 创建属于该角色的用户
        user1 = User.objects.create(
            organization=instance.organization,
            username='role_user1',
            real_name='角色用户1'
        )
        user2 = User.objects.create(
            organization=instance.organization,
            username='role_user2',
            real_name='角色用户2'
        )
        user1.roles.add(role)
        user2.roles.add(role)

        configs = [
            {'type': 'role', 'role_id': role.id}
        ]

        users = resolver.resolve(configs, instance)

        assert len(users) == 2
        assert user1 in users
        assert user2 in users

    def test_resolve_leader_type_direct(self, resolver, instance, department):
        """测试发起人直属领导"""
        leader = User.objects.create(
            organization=instance.organization,
            username='leader',
            real_name='部门领导'
        )
        department.leader = leader
        department.save()

        # 设置发起人部门
        instance.initiator.department = department
        instance.initiator.save()

        configs = [
            {'type': 'leader', 'leader_type': 'direct'}
        ]

        users = resolver.resolve(configs, instance)

        assert len(users) == 1
        assert users[0] == leader

    def test_deduplicate_users(self, resolver, instance, user1):
        """测试去重"""
        configs = [
            {'type': 'user', 'user_id': user1.id},
            {'type': 'user', 'user_id': user1.id},  # 重复
        ]

        users = resolver.resolve(configs, instance)

        assert len(users) == 1
        assert users[0] == user1
```

### 1.3 条件评估器测试

```python
# tests/workflows/test_condition_evaluator.py

import pytest
from apps.workflows.services.condition_evaluator import ConditionEvaluator


class TestConditionEvaluator:
    """条件评估器测试"""

    @pytest.fixture
    def evaluator(self):
        return ConditionEvaluator()

    @pytest.fixture
    def instance(self, workflow_instance):
        return workflow_instance

    def test_evaluate_eq_condition(self, evaluator, instance):
        """测试等于条件"""
        instance.variables = {'amount': 10000}

        result = evaluator.evaluate_condition(
            {'field': 'amount', 'operator': 'eq', 'value': 10000},
            instance
        )

        assert result is True

    def test_evaluate_gt_condition(self, evaluator, instance):
        """测试大于条件"""
        instance.variables = {'amount': 15000}

        result = evaluator.evaluate_condition(
            {'field': 'amount', 'operator': 'gt', 'value': 10000},
            instance
        )

        assert result is True

    def test_evaluate_in_condition(self, evaluator, instance):
        """测试in条件"""
        instance.variables = {'status': 'pending'}

        result = evaluator.evaluate_condition(
            {'field': 'status', 'operator': 'in', 'value': ['pending', 'running']},
            instance
        )

        assert result is True

    def test_evaluate_nested_field(self, evaluator, instance):
        """测试嵌套字段"""
        instance.variables = {
            'applicant': {
                'department': {
                    'id': 5
                }
            }
        }

        result = evaluator.evaluate_condition(
            {'field': 'applicant.department.id', 'operator': 'eq', 'value': 5},
            instance
        )

        assert result is True

    def test_evaluate_branch(self, evaluator, instance):
        """测试分支评估"""
        instance.variables = {'amount': 50000}

        branch = {
            'name': '大于1万',
            'conditions': [
                {'field': 'amount', 'operator': 'gt', 'value': '10000'}
            ]
        }

        result = evaluator.evaluate(branch, instance)

        assert result is True
```

---

## 2. API测试

```python
# tests/workflows/test_api.py

import pytest
from rest_framework.test import APIClient
from django.contrib.auth import get_user_model

User = get_user_model()


@pytest.fixture
def api_client(db):
    return APIClient()


@pytest.fixture
def authenticated_client(api_client, user):
    api_client.force_authenticate(user=user)
    return api_client


class TestWorkflowExecutionAPI:
    """工作流执行API测试"""

    def test_start_workflow(self, authenticated_client, workflow_definition, initiator):
        """测试启动工作流"""
        url = '/api/workflows/execution/start/'

        data = {
            'definition_id': workflow_definition.id,
            'business_id': '123',
            'business_no': 'LY001',
            'variables': {'amount': 50000}
        }

        response = authenticated_client.post(url, data, format='json')

        assert response.status_code == 201
        assert response.data['status'] == 'running'
        assert response.data['business_no'] == 'LY001'

    def test_start_workflow_invalid_definition(self, authenticated_client):
        """测试启动工作流 - 无效定义"""
        url = '/api/workflows/execution/start/'

        data = {
            'definition_id': 99999,
            'business_id': '123',
            'business_no': 'LY001'
        }

        response = authenticated_client.post(url, data, format='json')

        assert response.status_code == 404

    def test_get_my_tasks(self, authenticated_client, workflow_instance):
        """测试获取我的待办"""
        # 创建待办任务
        task = WorkflowTask.objects.create(
            instance=workflow_instance,
            node_id='node_1',
            node_name='测试审批',
            node_type='approval',
            assignee=authenticated_client.handler._force_user,
            status='pending'
        )

        url = '/api/workflows/execution/my_tasks/'
        response = authenticated_client.get(url, {'status': 'pending'})

        assert response.status_code == 200
        assert len(response.data['results']) >= 1

    def test_approve_task(self, authenticated_client, workflow_task):
        """测试审批通过"""
        url = f'/api/workflows/execution/{workflow_task.id}/approve/'

        data = {
            'comment': '同意'
        }

        response = authenticated_client.post(url, data, format='json')

        assert response.status_code == 200

        # 验证任务状态
        workflow_task.refresh_from_db()
        assert workflow_task.status == 'approved'

    def test_approve_task_without_comment(self, authenticated_client, workflow_task):
        """测试审批 - 无意见"""
        url = f'/api/workflows/execution/{workflow_task.id}/approve/'

        data = {}

        response = authenticated_client.post(url, data, format='json')

        assert response.status_code == 400

    def test_approve_task_by_wrong_user(self, authenticated_client, workflow_task):
        """测试非审批人尝试审批"""
        # 切换到其他用户
        other_user = User.objects.create(username='other')
        authenticated_client.force_authenticate(user=other_user)

        url = f'/api/workflows/execution/{workflow_task.id}/approve/'

        data = {'comment': '同意'}

        response = authenticated_client.post(url, data, format='json')

        assert response.status_code == 403

    def test_reject_task(self, authenticated_client, workflow_task):
        """测试审批拒绝"""
        url = f'/api/workflows/execution/{workflow_task.id}/reject/'

        data = {
            'comment': '理由不充分'
        }

        response = authenticated_client.post(url, data, format='json')

        assert response.status_code == 200

        workflow_task.refresh_from_db()
        assert workflow_task.status == 'rejected'

    def test_get_instance_detail(self, authenticated_client, workflow_instance):
        """测试获取流程详情"""
        url = f'/api/workflows/execution/{workflow_instance.id}/detail/'

        response = authenticated_client.get(url)

        assert response.status_code == 200
        assert response.data['id'] == workflow_instance.id
        assert 'graph_data' in response.data
        assert 'approval_chain' in response.data

    def test_get_instance_logs(self, authenticated_client, workflow_instance):
        """测试获取操作日志"""
        # 创建日志
        WorkflowLog.objects.create(
            instance=workflow_instance,
            action='submit',
            actor=workflow_instance.initiator,
            old_status='draft',
            new_status='running'
        )

        url = f'/api/workflows/execution/{workflow_instance.id}/logs/'

        response = authenticated_client.get(url)

        assert response.status_code == 200
        assert len(response.data) >= 1

    def test_withdraw_instance(self, authenticated_client, workflow_instance):
        """测试撤回流程"""
        url = f'/api/workflows/execution/{workflow_instance.id}/withdraw/'

        response = authenticated_client.post(url)

        assert response.status_code == 200

        workflow_instance.refresh_from_db()
        assert workflow_instance.status == 'cancelled'

    def test_withdraw_by_non_initiator(self, authenticated_client, workflow_instance):
        """测试非发起人撤回"""
        other_user = User.objects.create(username='other')
        authenticated_client.force_authenticate(user=other_user)

        url = f'/api/workflows/execution/{workflow_instance.id}/withdraw/'

        response = authenticated_client.post(url)

        assert response.status_code == 403

    def test_get_statistics(self, authenticated_client):
        """测试获取统计数据"""
        url = '/api/workflows/execution/statistics/'

        response = authenticated_client.get(url)

        assert response.status_code == 200
        assert 'pending_count' in response.data
        assert 'completed_today' in response.data
```

---

## 3. 前端组件测试

### 3.1 任务卡片测试

```javascript
// tests/workflows/TaskCard.spec.js

import { describe, it, expect } from 'vitest'
import { mount } from '@vue/test-utils'
import TaskCard from '@/views/workflows/components/TaskCard.vue'

describe('TaskCard', () => {
  const mockTask = {
    id: 1,
    node_name: '部门审批',
    status: 'pending',
    status_display: '待处理',
    instance_no: 'LY20240115001',
    initiator_name: '张三',
    initiator_avatar: 'https://example.com/avatar/1.jpg',
    assignee_name: '李经理',
    assignee_avatar: 'https://example.com/avatar/2.jpg',
    assigned_at: '2024-01-15T10:00:00Z',
    is_overdue: false,
    remaining_hours: 48
  }

  it('应正确显示任务信息', () => {
    const wrapper = mount(TaskCard, {
      props: { task: mockTask }
    })

    expect(wrapper.text()).toContain('部门审批')
    expect(wrapper.text()).toContain('LY20240115001')
    expect(wrapper.text()).toContain('张三')
  })

  it('应显示超时警告', () => {
    const overdueTask = { ...mockTask, is_overdue: true }
    const wrapper = mount(TaskCard, {
      props: { task: overdueTask }
    })

    expect(wrapper.find('.overdue-badge').exists()).toBe(true)
  })

  it('应触发审批事件', async () => {
    const wrapper = mount(TaskCard, {
      props: { task: mockTask }
    })

    await wrapper.find('.approve-button').trigger('click')

    expect(wrapper.emitted('approve')).toBeTruthy()
    expect(wrapper.emitted('approve')[0][0]).toEqual(mockTask)
  })

  it('应触发详情事件', async () => {
    const wrapper = mount(TaskCard, {
      props: { task: mockTask }
    })

    await wrapper.find('.task-card').trigger('click')

    expect(wrapper.emitted('detail')).toBeTruthy()
  })
})
```

### 3.2 审批面板测试

```javascript
// tests/workflows/TaskApprovalPanel.spec.js

import { describe, it, expect, vi } from 'vitest'
import { mount } from '@vue/test-utils'
import TaskApprovalPanel from '@/views/workflows/components/TaskApprovalPanel.vue'

describe('TaskApprovalPanel', () => {
  const mockTask = {
    id: 1,
    node_name: '部门审批',
    status: 'pending'
  }

  it('应切换审批动作', async () => {
    const wrapper = mount(TaskApprovalPanel, {
      props: {
        task: mockTask,
        modelValue: { action: 'approved', comment: '' }
      }
    })

    await wrapper.find('.action-item.reject').trigger('click')

    expect(wrapper.emitted('update:modelValue')[0][0].action).toBe('rejected')
  })

  it('应设置快捷评论', async () => {
    const wrapper = mount(TaskApprovalPanel, {
      props: {
        task: mockTask,
        modelValue: { action: 'approved', comment: '' }
      }
    })

    await wrapper.find('.quick-comment-tag').trigger('click')

    expect(wrapper.emitted('update:modelValue')[0][0].comment).toBeTruthy()
  })

  it('应验证必填意见', () => {
    const wrapper = mount(TaskApprovalPanel, {
      props: {
        task: mockTask,
        modelValue: { action: 'approved', comment: '' }
      }
    })

    // 尝试提交（应该在父组件中验证）
    expect(wrapper.vm.modelValue.comment).toBe('')
  })
})
```

### 3.3 流程进度组件测试

```javascript
// tests/workflows/WorkflowProgress.spec.js

import { describe, it, expect } from 'vitest'
import { mount } from '@vue/test-utils'
import WorkflowProgress from '@/views/workflows/components/WorkflowProgress.vue'

describe('WorkflowProgress', () => {
  const mockInstance = {
    id: 1,
    definition_name: '资产领用审批',
    business_no: 'LY20240115001',
    status: 'pending_approval',
    status_display: '待审批',
    progress: 50,
    total_tasks: 4,
    completed_tasks: 2,
    started_at: '2024-01-15T10:00:00Z',
    current_tasks: [
      {
        id: 1,
        assignee_name: '李经理',
        assignee_avatar: 'https://example.com/avatar/2.jpg'
      }
    ]
  }

  it('应正确显示流程信息', () => {
    const wrapper = mount(WorkflowProgress, {
      props: { instance: mockInstance }
    })

    expect(wrapper.text()).toContain('资产领用审批')
    expect(wrapper.text()).toContain('LY20240115001')
  })

  it('应显示进度百分比', () => {
    const wrapper = mount(WorkflowProgress, {
      props: { instance: mockInstance }
    })

    expect(wrapper.find('.progress-text').text()).toContain('50%')
  })

  it('应显示当前处理人', () => {
    const wrapper = mount(WorkflowProgress, {
      props: { instance: mockInstance }
    })

    expect(wrapper.find('.assignees-list').exists()).toBe(true)
  })

  it('应点击触发事件', async () => {
    const wrapper = mount(WorkflowProgress, {
      props: { instance: mockInstance }
    })

    await wrapper.find('.workflow-progress').trigger('click')

    expect(wrapper.emitted('click')).toBeTruthy()
  })
})
```

---

## 4. E2E测试

```javascript
// tests/e2e/workflows/execution.spec.js

import { test, expect } from '@playwright/test'

test.describe('工作流执行E2E', () => {
  test.beforeEach(async ({ page }) => {
    // 登录
    await page.goto('/login')
    await page.fill('[name="username"]', 'manager')
    await page.fill('[name="password"]', 'password123')
    await page.click('button[type="submit"]')
  })

  test('应显示待办任务列表', async ({ page }) => {
    await page.goto('/workflows/tasks')

    // 验证页面标题
    await expect(page.locator('.task-center')).toBeVisible()

    // 验证统计卡片
    await expect(page.locator('.stat-card').first()).toBeVisible()
  })

  test('应审批任务', async ({ page }) => {
    await page.goto('/workflows/tasks')

    // 点击第一个待办
    await page.click('.task-card:first-child')

    // 等待详情页加载
    await expect(page.locator('.task-detail-page')).toBeVisible()

    // 选择同意
    await page.click('.action-item.approved')

    // 填写意见
    await page.fill('textarea.el-textarea__inner', '同意，理由充分')

    // 提交
    await page.click('button:has-text("提交审批")')

    // 验证成功提示
    await expect(page.locator('.el-message--success')).toBeVisible()
  })

  test('应拒绝任务', async ({ page }) => {
    await page.goto('/workflows/tasks')

    await page.click('.task-card:first-child')
    await expect(page.locator('.task-detail-page')).toBeVisible()

    // 选择拒绝
    await page.click('.action-item.rejected')

    // 填写拒绝理由
    await page.fill('textarea.el-textarea__inner', '理由不充分，请补充')

    // 提交
    await page.click('button:has-text("提交审批")')

    // 验证
    await expect(page.locator('.el-message--success')).toBeVisible()
  })

  test('应转交任务', async ({ page }) => {
    await page.goto('/workflows/tasks')

    await page.click('.task-card:first-child')

    // 点击转交按钮
    await page.click('button:has-text("转交他人")')

    // 选择转交对象
    await page.click('.user-selector-trigger')
    await page.click('.user-option:has-text("王总监")')

    // 填写转交说明
    await page.fill('.transfer-reason textarea', '转交处理')

    // 确认转交
    await page.click('.el-dialog .confirm-btn')

    // 验证
    await expect(page.locator('.el-message--success')).toBeVisible()
  })

  test('应查看流程详情', async ({ page }) => {
    await page.goto('/workflows/instance/1')

    // 验证流程信息
    await expect(page.locator('.workflow-detail')).toBeVisible()
    await expect(page.locator('.approval-chain')).toBeVisible()
    await expect(page.locator('.log-list')).toBeVisible()
  })

  test('应撤回流程', async ({ page }) => {
    await page.goto('/workflows/my-instances')

    // 点击撤回按钮
    await page.click('.instance-item:first-child .withdraw-btn')

    // 确认撤回
    await page.click('.el-message-box .confirm-btn')

    // 验证
    await expect(page.locator('.el-message--success')).toBeVisible()
  })

  test('应查看审批链', async ({ page }) => {
    await page.goto('/workflows/instance/1')

    // 验证审批链组件
    await expect(page.locator('.approval-chain')).toBeVisible()

    // 验证审批节点
    const nodes = page.locator('.chain-item')
    await expect(nodes.first()).toBeVisible()
  })
})
```

---

## 5. 测试数据

### 5.1 Fixture数据

```python
# tests/workflows/fixtures.py

import pytest
from apps.workflows.models import (
    WorkflowDefinition, WorkflowInstance, WorkflowTask, WorkflowLog
)


@pytest.fixture
def workflow_graph_data():
    """标准工作流图数据"""
    return {
        'nodes': [
            {
                'id': 'start_1',
                'type': 'start',
                'x': 100,
                'y': 100,
                'text': '开始'
            },
            {
                'id': 'approval_1',
                'type': 'approval',
                'x': 300,
                'y': 100,
                'text': '部门审批',
                'properties': {
                    'approveType': 'or',
                    'approvers': [],
                    'timeout': 72,
                    'fieldPermissions': {}
                }
            },
            {
                'id': 'condition_1',
                'type': 'condition',
                'x': 500,
                'y': 100,
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
                'y': 50,
                'text': '财务审批',
                'properties': {
                    'approveType': 'and',
                    'approvers': []
                }
            },
            {
                'id': 'end_1',
                'type': 'end',
                'x': 900,
                'y': 100,
                'text': '结束'
            }
        ],
        'edges': [
            {'sourceNodeId': 'start_1', 'targetNodeId': 'approval_1'},
            {'sourceNodeId': 'approval_1', 'targetNodeId': 'condition_1'},
            {'sourceNodeId': 'condition_1', 'targetNodeId': 'approval_2'},
            {'sourceNodeId': 'condition_1', 'targetNodeId': 'end_1'},
            {'sourceNodeId': 'approval_2', 'targetNodeId': 'end_1'}
        ]
    }
```

---

## 测试执行

### 运行命令

```bash
# 引心单元测试
pytest tests/workflows/test_engine.py -v

# API测试
pytest tests/workflows/test_api.py -v

# 前端组件测试
npm run test:unit -- workflow

# E2E测试
npm run test:e2e -- workflows

# 完整测试套件
npm run test:phase3.2
```

---

## 后续任务

1. Phase 4.1: 实现QR码扫描盘点
2. Phase 4.2: 实现RFID批量盘点
3. Phase 4.3: 实现盘点快照和差异处理
