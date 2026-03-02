# Phase 6: User Portal (用户门户) - 测试方案

## 测试概览

| 测试类型 | 覆盖范围 | 优先级 |
|---------|---------|--------|
| 单元测试 | 门户服务 (UserAssetService, UserRequestService, UserTaskService) | P0 |
| API测试 | 门户相关接口 | P0 |
| 前端组件测试 | Vue组件 (PortalHome, MyAssets, MyRequests) | P1 |
| E2E测试 | 用户门户完整流程 | P1 |
| 移动端测试 | 移动端页面和交互 | P1 |

---

## 1. 后端单元测试

### 1.1 用户资产服务测试

```python
# apps/portal/tests/test_user_asset_service.py

import pytest
from django.test import TestCase
from django.utils import timezone
from apps.portal.services import UserAssetService
from apps.accounts.models import User
from apps.organizations.models import Organization, Department
from apps.assets.models import Asset, AssetCategory, AssetPickup, AssetLoan


class UserAssetServiceTest(TestCase):
    """用户资产服务测试"""

    def setUp(self):
        self.org = Organization.objects.create(name='测试公司')
        self.dept = Department.objects.create(
            organization=self.org,
            name='研发部'
        )
        self.user = User.objects.create_user(
            username='testuser',
            real_name='张三',
            organization=self.org
        )
        self.user.departments.add(self.dept)

        self.category = AssetCategory.objects.create(
            organization=self.org,
            code='2001',
            name='计算机设备'
        )

        self.service = UserAssetService()

    def test_get_my_assets_custodian(self):
        """测试获取保管的资产"""
        asset = Asset.objects.create(
            organization=self.org,
            asset_category=self.category,
            asset_code='ZC20240101001',
            asset_name='测试电脑',
            custodian=self.user,
            asset_status='in_use',
            purchase_price=10000,
            purchase_date=timezone.now().date()
        )

        result = self.service.get_my_assets(self.user.id)

        self.assertEqual(result['summary']['total_count'], 1)
        self.assertEqual(result['summary']['custodian_count'], 1)
        self.assertEqual(len(result['items']), 1)
        self.assertEqual(result['items'][0]['relation'], 'custodian')
        self.assertEqual(result['items'][0]['relation_label'], '保管中')

    def test_get_my_assets_borrowed(self):
        """测试获取借用的资产"""
        asset = Asset.objects.create(
            organization=self.org,
            asset_category=self.category,
            asset_code='ZC20240101002',
            asset_name='借用电脑',
            purchase_price=8000,
            purchase_date=timezone.now().date()
        )

        # 创建借用单
        loan = AssetLoan.objects.create(
            borrower=self.user,
            borrow_date=timezone.now().date(),
            expected_return_date=timezone.now().date() + timezone.timedelta(days=30),
            status='borrowed'
        )
        # 添加借用明细
        loan.items.create(asset=asset, quantity=1)

        result = self.service.get_my_assets(self.user.id)

        self.assertEqual(result['summary']['borrowed_count'], 1)
        self.assertEqual(result['items'][0]['relation'], 'borrowed')
        self.assertEqual(result['items'][0]['relation_label'], '借用中')

    def test_get_my_assets_pickup(self):
        """测试获取领用的资产"""
        asset = Asset.objects.create(
            organization=self.org,
            asset_category=self.category,
            asset_code='ZC20240101003',
            asset_name='领用电脑',
            purchase_price=12000,
            purchase_date=timezone.now().date()
        )

        # 创建领用单
        pickup = AssetPickup.objects.create(
            applicant=self.user,
            department=self.dept,
            pickup_date=timezone.now().date(),
            status='completed'
        )
        pickup.items.create(asset=asset, quantity=1)

        result = self.service.get_my_assets(self.user.id)

        self.assertEqual(result['summary']['pickup_count'], 1)
        self.assertEqual(result['items'][0]['relation'], 'pickup')

    def test_get_my_assets_filter_by_status(self):
        """测试按状态过滤"""
        Asset.objects.create(
            organization=self.org,
            asset_category=self.category,
            asset_code='ZC20240101004',
            asset_name='在用资产',
            custodian=self.user,
            asset_status='in_use',
            purchase_price=10000,
            purchase_date=timezone.now().date()
        )
        Asset.objects.create(
            organization=self.org,
            asset_category=self.category,
            asset_code='ZC20240101005',
            asset_name='闲置资产',
            custodian=self.user,
            asset_status='idle',
            purchase_price=5000,
            purchase_date=timezone.now().date()
        )

        result = self.service.get_my_assets(
            self.user.id,
            filters={'status': 'in_use'}
        )

        self.assertEqual(len(result['items']), 1)
        self.assertEqual(result['items'][0]['asset_status'], 'in_use')

    def test_get_my_assets_search(self):
        """测试搜索功能"""
        Asset.objects.create(
            organization=self.org,
            asset_category=self.category,
            asset_code='ZC20240101006',
            asset_name='MacBook Pro',
            serial_number='C02XXXX',
            custodian=self.user,
            asset_status='in_use',
            purchase_price=15000,
            purchase_date=timezone.now().date()
        )

        # 搜索名称
        result = self.service.get_my_assets(
            self.user.id,
            filters={'keyword': 'MacBook'}
        )
        self.assertEqual(len(result['items']), 1)

        # 搜索序列号
        result = self.service.get_my_assets(
            self.user.id,
            filters={'keyword': 'C02XXXX'}
        )
        self.assertEqual(len(result['items']), 1)

    def test_get_asset_detail(self):
        """测试获取资产详情"""
        asset = Asset.objects.create(
            organization=self.org,
            asset_category=self.category,
            asset_code='ZC20240101007',
            asset_name='详情测试',
            custodian=self.user,
            asset_status='in_use',
            department=self.dept,
            purchase_price=10000,
            purchase_date=timezone.now().date(),
            serial_number='SN123456'
        )

        result = self.service.get_asset_detail(asset.id, self.user.id)

        self.assertEqual(result['asset']['id'], asset.id)
        self.assertEqual(result['asset']['asset_code'], 'ZC20240101007')
        self.assertEqual(result['relation'], 'custodian')
        self.assertIn('history', result)
        self.assertIn('available_actions', result)

    def test_can_return_asset(self):
        """测试归还判断"""
        asset = Asset.objects.create(
            organization=self.org,
            asset_category=self.category,
            asset_code='ZC20240101008',
            asset_name='测试资产',
            purchase_price=5000,
            purchase_date=timezone.now().date()
        )

        # 借用的资产可以归还
        loan = AssetLoan.objects.create(
            borrower=self.user,
            borrow_date=timezone.now().date(),
            expected_return_date=timezone.now().date() + timezone.timedelta(days=30),
            status='borrowed'
        )
        loan.items.create(asset=asset, quantity=1)

        service = UserAssetService()
        self.assertTrue(service._can_return_asset(asset, self.user, 'borrowed'))
        self.assertFalse(service._can_return_asset(asset, self.user, 'custodian'))

    def test_get_my_assets_pagination(self):
        """测试分页"""
        # 创建20个资产
        for i in range(20):
            Asset.objects.create(
                organization=self.org,
                asset_category=self.category,
                asset_code=f'ZC202401{i:03d}',
                asset_name=f'资产{i}',
                custodian=self.user,
                asset_status='in_use',
                purchase_price=5000 + i * 100,
                purchase_date=timezone.now().date()
            )

        result = self.service.get_my_assets(
            self.user.id,
            filters={'page': 1, 'page_size': 10}
        )

        self.assertEqual(result['total'], 20)
        self.assertEqual(len(result['items']), 10)
        self.assertEqual(result['page'], 1)
        self.assertEqual(result['page_size'], 10)
```

### 1.2 用户申请服务测试

```python
# apps/portal/tests/test_user_request_service.py

import pytest
from django.test import TestCase
from django.utils import timezone
from apps.portal.services import UserRequestService
from apps.accounts.models import User
from apps.organizations.models import Organization, Department
from apps.assets.models import Asset, AssetCategory, AssetPickup, AssetLoan


class UserRequestServiceTest(TestCase):
    """用户申请服务测试"""

    def setUp(self):
        self.org = Organization.objects.create(name='测试公司')
        self.dept = Department.objects.create(
            organization=self.org,
            name='研发部'
        )
        self.user = User.objects.create_user(
            username='testuser',
            real_name='张三',
            organization=self.org
        )
        self.user.departments.add(self.dept)

        self.category = AssetCategory.objects.create(
            organization=self.org,
            code='2001',
            name='计算机设备'
        )

        self.asset = Asset.objects.create(
            organization=self.org,
            asset_category=self.category,
            asset_code='ZC20240101001',
            asset_name='测试资产',
            purchase_price=10000,
            purchase_date=timezone.now().date()
        )

        self.service = UserRequestService()

    def test_get_my_requests_aggregation(self):
        """测试申请聚合功能"""
        # 创建领用单
        pickup = AssetPickup.objects.create(
            applicant=self.user,
            department=self.dept,
            pickup_date=timezone.now().date(),
            pickup_reason='测试领用',
            status='pending'
        )
        pickup.items.create(asset=self.asset, quantity=1)

        # 创建借用单
        loan = AssetLoan.objects.create(
            borrower=self.user,
            borrow_date=timezone.now().date(),
            expected_return_date=timezone.now().date() + timezone.timedelta(days=30),
            loan_reason='测试借用',
            status='approved'
        )
        loan.items.create(asset=self.asset, quantity=1)

        result = self.service.get_my_requests(self.user.id)

        self.assertEqual(result['summary']['total'], 2)
        self.assertIn('pickup', result['summary']['by_type'])
        self.assertIn('loan', result['summary']['by_type'])
        self.assertEqual(len(result['items']), 2)

    def test_get_my_requests_filter_by_status(self):
        """测试按状态过滤"""
        # 创建不同状态的申请
        for status in ['draft', 'pending', 'approved', 'completed']:
            pickup = AssetPickup.objects.create(
                applicant=self.user,
                department=self.dept,
                pickup_date=timezone.now().date(),
                status=status
            )
            pickup.items.create(asset=self.asset, quantity=1)

        result = self.service.get_my_requests(
            self.user.id,
            filters={'status': 'pending'}
        )

        self.assertEqual(len(result['items']), 1)
        self.assertEqual(result['items'][0]['status'], 'pending')

    def test_get_my_requests_filter_by_type(self):
        """测试按类型过滤"""
        # 创建领用单
        pickup = AssetPickup.objects.create(
            applicant=self.user,
            department=self.dept,
            pickup_date=timezone.now().date(),
            status='pending'
        )
        pickup.items.create(asset=self.asset, quantity=1)

        # 创建借用单
        loan = AssetLoan.objects.create(
            borrower=self.user,
            borrow_date=timezone.now().date(),
            expected_return_date=timezone.now().date() + timezone.timedelta(days=30),
            status='pending'
        )
        loan.items.create(asset=self.asset, quantity=1)

        result = self.service.get_my_requests(
            self.user.id,
            filters={'type': 'pickup'}
        )

        self.assertEqual(len(result['items']), 1)
        self.assertEqual(result['items'][0]['request_type'], 'pickup')

    def test_get_request_detail_pickup(self):
        """测试获取领用单详情"""
        pickup = AssetPickup.objects.create(
            applicant=self.user,
            department=self.dept,
            pickup_date=timezone.now().date(),
            pickup_reason='测试',
            status='approved'
        )
        pickup.items.create(asset=self.asset, quantity=1, remark='测试备注')

        result = self.service.get_request_detail('pickup', pickup.id, self.user.id)

        self.assertEqual(result['request_type'], 'pickup')
        self.assertEqual(result['no'], pickup.pickup_no)
        self.assertEqual(result['status'], 'approved')
        self.assertEqual(len(result['items']), 1)

    def test_get_request_detail_loan(self):
        """测试获取借用单详情"""
        loan = AssetLoan.objects.create(
            borrower=self.user,
            borrow_date=timezone.now().date(),
            expected_return_date=timezone.now().date() + timezone.timedelta(days=30),
            loan_reason='临时借用',
            status='borrowed'
        )
        loan.items.create(asset=self.asset, quantity=1)

        result = self.service.get_request_detail('loan', loan.id, self.user.id)

        self.assertEqual(result['request_type'], 'loan')
        self.assertEqual(result['borrower']['id'], self.user.id)
        self.assertIn('is_overdue', result)

    def test_cancel_request(self):
        """测试取消申请"""
        pickup = AssetPickup.objects.create(
            applicant=self.user,
            department=self.dept,
            pickup_date=timezone.now().date(),
            status='draft'
        )
        pickup.items.create(asset=self.asset, quantity=1)

        result = self.service.cancel_request('pickup', pickup.id, self.user.id)

        self.assertTrue(result['success'])
        pickup.refresh_from_db()
        self.assertEqual(pickup.status, 'cancelled')

    def test_cancel_request_not_allowed(self):
        """测试不允许取消"""
        pickup = AssetPickup.objects.create(
            applicant=self.user,
            department=self.dept,
            pickup_date=timezone.now().date(),
            status='completed'
        )
        pickup.items.create(asset=self.asset, quantity=1)

        with self.assertRaises(ValueError):
            self.service.cancel_request('pickup', pickup.id, self.user.id)

    def test_cancel_request_permission_denied(self):
        """测试权限限制"""
        other_user = User.objects.create_user(
            username='otheruser',
            organization=self.org
        )

        pickup = AssetPickup.objects.create(
            applicant=self.user,
            department=self.dept,
            pickup_date=timezone.now().date(),
            status='draft'
        )
        pickup.items.create(asset=self.asset, quantity=1)

        with self.assertRaises(PermissionError):
            self.service.cancel_request('pickup', pickup.id, other_user.id)
```

### 1.3 用户待办服务测试

```python
# apps/portal/tests/test_user_task_service.py

import pytest
from django.test import TestCase
from django.utils import timezone
from datetime import timedelta
from apps.portal.services import UserTaskService
from apps.accounts.models import User
from apps.organizations.models import Organization, Department
from apps.assets.models import Asset, AssetCategory, AssetLoan
from apps.workflows.models import WorkflowTask, WorkflowInstance, WorkflowDefinition


class UserTaskServiceTest(TestCase):
    """用户待办服务测试"""

    def setUp(self):
        self.org = Organization.objects.create(name='测试公司')
        self.dept = Department.objects.create(
            organization=self.org,
            name='研发部'
        )
        self.user = User.objects.create_user(
            username='testuser',
            real_name='张三',
            organization=self.org
        )
        self.user.departments.add(self.dept)

        self.category = AssetCategory.objects.create(
            organization=self.org,
            code='2001',
            name='计算机设备'
        )

        self.service = UserTaskService()

    def test_get_my_tasks_workflow(self):
        """测试获取工作流待办"""
        definition = WorkflowDefinition.objects.create(
            organization=self.org,
            name='资产领用流程',
            definition={'nodes': [], 'edges': []}
        )
        instance = WorkflowInstance.objects.create(
            organization=self.org,
            definition=definition,
            title='测试领用申请',
            initiator=self.user,
            status='running'
        )
        task = WorkflowTask.objects.create(
            instance=instance,
            node_id='node1',
            node_name='部门审批',
            assignee=self.user,
            status='pending',
            due_date=timezone.now() + timedelta(days=1)
        )

        result = self.service.get_my_tasks(self.user.id)

        # 验证包含工作流任务
        workflow_tasks = [t for t in result['items'] if t['task_type'] == 'workflow_approval']
        self.assertGreater(len(workflow_tasks), 0)
        self.assertEqual(workflow_tasks[0]['id'], f'workflow_{task.id}')

    def test_get_my_tasks_due_loan_reminder(self):
        """测试获取即将到期的借用提醒"""
        asset = Asset.objects.create(
            organization=self.org,
            asset_category=self.category,
            asset_code='ZC20240101001',
            asset_name='测试资产',
            purchase_price=10000,
            purchase_date=timezone.now().date()
        )

        # 创建即将到期的借用（3天内）
        loan = AssetLoan.objects.create(
            borrower=self.user,
            borrow_date=timezone.now().date() - timedelta(days=20),
            expected_return_date=timezone.now().date() + timedelta(days=3),
            status='borrowed'
        )
        loan.items.create(asset=asset, quantity=1)

        result = self.service.get_my_tasks(self.user.id)

        # 验证包含借用归还提醒
        loan_tasks = [t for t in result['items'] if t['task_type'] == 'loan_return']
        self.assertGreater(len(loan_tasks), 0)
        self.assertEqual(loan_tasks[0]['priority'], 'high')

    def test_get_my_tasks_overdue_loan(self):
        """测试获取逾期借用"""
        asset = Asset.objects.create(
            organization=self.org,
            asset_category=self.category,
            asset_code='ZC20240101002',
            asset_name='逾期资产',
            purchase_price=8000,
            purchase_date=timezone.now().date()
        )

        # 创建已逾期的借用
        loan = AssetLoan.objects.create(
            borrower=self.user,
            borrow_date=timezone.now().date() - timedelta(days=40),
            expected_return_date=timezone.now().date() - timedelta(days=5),
            status='borrowed'
        )
        loan.items.create(asset=asset, quantity=1)

        result = self.service.get_my_tasks(self.user.id)

        # 验证逾期任务优先级为urgent
        loan_tasks = [t for t in result['items'] if t['task_type'] == 'loan_return']
        self.assertGreater(len(loan_tasks), 0)
        self.assertEqual(loan_tasks[0]['priority'], 'urgent')
        self.assertTrue(loan_tasks[0]['is_overdue'])

    def test_get_my_tasks_summary(self):
        """测试待办汇总"""
        result = self.service.get_my_tasks(self.user.id)

        self.assertIn('summary', result)
        self.assertIn('total', result['summary'])
        self.assertIn('urgent', result['summary'])
        self.assertIn('high', result['summary'])
        self.assertIn('normal', result['summary'])
        self.assertIn('by_type', result['summary'])

    def test_task_priority_calculation(self):
        """测试任务优先级计算"""
        definition = WorkflowDefinition.objects.create(
            organization=self.org,
            name='测试流程',
            definition={'nodes': [], 'edges': []}
        )
        instance = WorkflowInstance.objects.create(
            organization=self.org,
            definition=definition,
            title='紧急任务',
            initiator=self.user,
            status='running'
        )

        # 已逾期的任务
        task1 = WorkflowTask.objects.create(
            instance=instance,
            node_id='node1',
            node_name='逾期审批',
            assignee=self.user,
            status='pending',
            due_date=timezone.now() - timedelta(days=1)
        )

        # 今天到期的任务
        task2 = WorkflowTask.objects.create(
            instance=instance,
            node_id='node2',
            node_name='今日审批',
            assignee=self.user,
            status='pending',
            due_date=timezone.now() + timedelta(hours=2)
        )

        result = self.service.get_my_tasks(self.user.id)
        workflow_tasks = [t for t in result['items'] if t['task_type'] == 'workflow_approval']

        # 验证优先级排序
        urgent_tasks = [t for t in workflow_tasks if t['priority'] == 'urgent']
        high_tasks = [t for t in workflow_tasks if t['priority'] == 'high']

        self.assertGreater(len(urgent_tasks), 0)
        self.assertGreater(len(high_tasks), 0)
```

---

## 2. API测试

```python
# apps/portal/tests/test_api.py

from django.test import TestCase
from rest_framework.test import APIClient
from apps.accounts.models import User
from apps.organizations.models import Organization
from apps.assets.models import Asset, AssetCategory
from apps.workflows.models import WorkflowTask, WorkflowInstance, WorkflowDefinition


class PortalAPITest(TestCase):
    """门户API测试"""

    def setUp(self):
        self.client = APIClient()
        self.org = Organization.objects.create(name='测试公司')

        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123',
            real_name='张三',
            organization=self.org
        )
        self.client.force_authenticate(user=self.user)

        self.category = AssetCategory.objects.create(
            organization=self.org,
            code='2001',
            name='计算机设备'
        )

    def test_get_overview(self):
        """测试获取门户概览"""
        # 创建测试数据
        Asset.objects.create(
            organization=self.org,
            asset_category=self.category,
            asset_code='ZC20240101001',
            asset_name='测试资产',
            custodian=self.user,
            asset_status='in_use',
            purchase_price=10000
        )

        response = self.client.get('/api/portal/overview/')

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn('user', data)
        self.assertIn('assets', data)
        self.assertIn('requests', data)
        self.assertIn('tasks', data)
        self.assertIn('quick_actions', data)

    def test_get_my_assets(self):
        """测试获取我的资产"""
        Asset.objects.create(
            organization=self.org,
            asset_category=self.category,
            asset_code='ZC20240101002',
            asset_name='我的资产',
            custodian=self.user,
            asset_status='in_use',
            purchase_price=8000
        )

        response = self.client.get('/api/portal/my-assets/')

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['total'], 1)
        self.assertEqual(len(data['items']), 1)

    def test_get_my_assets_filter(self):
        """测试资产过滤"""
        Asset.objects.create(
            organization=self.org,
            asset_category=self.category,
            asset_code='ZC20240101003',
            asset_name='在用资产',
            custodian=self.user,
            asset_status='in_use',
            purchase_price=5000
        )
        Asset.objects.create(
            organization=self.org,
            asset_category=self.category,
            asset_code='ZC20240101004',
            asset_name='闲置资产',
            custodian=self.user,
            asset_status='idle',
            purchase_price=3000
        )

        response = self.client.get('/api/portal/my-assets/?status=in_use')

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['total'], 1)
        self.assertEqual(data['items'][0]['asset_status'], 'in_use')

    def test_get_asset_detail(self):
        """测试获取资产详情"""
        asset = Asset.objects.create(
            organization=self.org,
            asset_category=self.category,
            asset_code='ZC20240101005',
            asset_name='详情测试',
            custodian=self.user,
            asset_status='in_use',
            purchase_price=12000,
            serial_number='SN123456'
        )

        response = self.client.get(f'/api/portal/my-assets/{asset.id}/')

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['asset']['id'], asset.id)
        self.assertEqual(data['asset']['serial_number'], 'SN123456')
        self.assertIn('history', data)
        self.assertIn('related_documents', data)

    def test_get_asset_summary(self):
        """测试获取资产汇总"""
        Asset.objects.create(
            organization=self.org,
            asset_category=self.category,
            asset_code='ZC20240101006',
            asset_name='资产1',
            custodian=self.user,
            asset_status='in_use',
            purchase_price=10000
        )

        response = self.client.get('/api/portal/my-assets/summary/')

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn('by_relation', data)
        self.assertIn('by_category', data)
        self.assertIn('by_status', data)
        self.assertIn('total_value', data)

    def test_get_my_requests(self):
        """测试获取我的申请"""
        from apps.assets.models import AssetPickup

        pickup = AssetPickup.objects.create(
            applicant=self.user,
            department=self.user.get_primary_department() or self.user.departments.first(),
            pickup_date='2024-01-15',
            status='pending'
        )

        response = self.client.get('/api/portal/my-requests/')

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['total'], 1)

    def test_get_my_tasks(self):
        """测试获取我的待办"""
        definition = WorkflowDefinition.objects.create(
            organization=self.org,
            name='测试流程',
            definition={'nodes': [], 'edges': []}
        )
        instance = WorkflowInstance.objects.create(
            organization=self.org,
            definition=definition,
            title='测试任务',
            initiator=self.user,
            status='running'
        )
        WorkflowTask.objects.create(
            instance=instance,
            node_id='node1',
            node_name='审批',
            assignee=self.user,
            status='pending'
        )

        response = self.client.get('/api/portal/my-tasks/')

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['total'], 1)
        self.assertEqual(data['items'][0]['task_type'], 'workflow_approval')

    def test_get_task_summary(self):
        """测试获取待办汇总"""
        response = self.client.get('/api/portal/my-tasks/summary/')

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn('total', data)
        self.assertIn('urgent', data)
        self.assertIn('by_type', data)

    def test_get_profile(self):
        """测试获取个人信息"""
        response = self.client.get('/api/portal/profile/')

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['id'], self.user.id)
        self.assertEqual(data['username'], 'testuser')
        self.assertIn('organization', data)
        self.assertIn('departments', data)

    def test_update_profile(self):
        """测试更新个人信息"""
        response = self.client.put('/api/portal/profile/', {
            'real_name': '张三丰',
            'mobile': '13900139000'
        })

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['real_name'], '张三丰')
        self.assertEqual(data['mobile'], '13900139000')

    def test_unauthorized_access(self):
        """测试未授权访问"""
        self.client.force_authenticate(user=None)

        response = self.client.get('/api/portal/overview/')

        self.assertEqual(response.status_code, 401)

    def test_quick_actions(self):
        """测试快捷操作"""
        response = self.client.post('/api/portal/quick-actions/', {
            'action': 'scan_qr',
            'params': {'qr_data': 'ASSET:ZC20240101001'}
        })

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn('action', data)

    def test_quick_actions_invalid(self):
        """测试无效的快捷操作"""
        response = self.client.post('/api/portal/quick-actions/', {
            'action': 'invalid_action'
        })

        self.assertEqual(response.status_code, 400)
```

---

## 3. 前端组件测试

```typescript
// src/views/portal/__tests__/PortalHome.spec.ts

import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount } from '@vue/test-utils'
import { ElMessage } from 'element-plus'
import PortalHome from '../PortalHome.vue'
import { portalApi } from '@/api/portal'

vi.mock('@/api/portal', () => ({
  portalApi: {
    getOverview: vi.fn(() => Promise.resolve({
      data: {
        user: { id: 1, real_name: '张三', avatar: null },
        assets: { total: 5, recent: [] },
        tasks: { pending: 3, items: [] },
        requests: { total: 10, recent: [] },
        quick_actions: []
      }
    }))
  }
}))

vi.mock('vue-router', () => ({
  useRouter: () => ({
    push: vi.fn()
  })
}))

describe('PortalHome.vue', () => {
  it('renders portal home', () => {
    const wrapper = mount(PortalHome)
    expect(wrapper.find('.portal-home').exists()).toBe(true)
  })

  it('fetches overview on mount', async () => {
    const wrapper = mount(PortalHome)
    await new Promise(resolve => setTimeout(resolve, 100))
    expect(portalApi.getOverview).toHaveBeenCalledOnce()
  })

  it('displays user information', async () => {
    const wrapper = mount(PortalHome)
    await new Promise(resolve => setTimeout(resolve, 100))
    // 验证用户信息显示
  })

  it('navigates to quick action', async () => {
    const wrapper = mount(PortalHome)
    const router = wrapper.vm.$router
    await wrapper.vm.handleQuickAction({ action: 'navigate', url: '/test' })
    expect(router.push).toHaveBeenCalledWith('/test')
  })
})


describe('MyAssets.vue', () => {
  it('displays asset list', async () => {
    vi.mocked(portalApi.getMyAssets).mockResolvedValue({
      data: {
        items: [
          { id: 1, asset_code: 'ZC001', asset_name: '测试资产', relation: 'custodian' }
        ],
        total: 1,
        summary: { total_count: 1 }
      }
    })

    const wrapper = mount(MyAssets)
    await new Promise(resolve => setTimeout(resolve, 100))
    expect(portalApi.getMyAssets).toHaveBeenCalled()
  })

  it('filters by status', async () => {
    const wrapper = mount(MyAssets)
    wrapper.vm.filters.status = 'in_use'
    await wrapper.vm.handleSearch()
    expect(portalApi.getMyAssets).toHaveBeenCalledWith(
      expect.objectContaining({ status: 'in_use' })
    )
  })
})


describe('MyRequests.vue', () => {
  it('displays request list', async () => {
    vi.mocked(portalApi.getMyRequests).mockResolvedValue({
      data: {
        items: [
          { id: 'pickup_1', request_type: 'pickup', no: 'LY001', status: 'pending' }
        ],
        total: 1,
        summary: { total: 1, by_status: {} }
      }
    })

    const wrapper = mount(MyRequests)
    await new Promise(resolve => setTimeout(resolve, 100))
    expect(portalApi.getMyRequests).toHaveBeenCalled()
  })

  it('switches tabs correctly', async () => {
    const wrapper = mount(MyRequests)
    wrapper.vm.activeTab = 'pending'
    await wrapper.vm.fetchData()
    expect(portalApi.getMyRequests).toHaveBeenCalledWith(
      expect.objectContaining({ status: 'pending' })
    )
  })
})
```

---

## 4. E2E测试

```typescript
// e2e/portal.spec.ts

import { test, expect } from '@playwright/test'

test.describe('Portal E2E Tests', () => {
  test.beforeEach(async ({ page }) => {
    // 登录
    await page.goto('http://localhost:5173/login')
    await page.fill('input[placeholder*="用户名"]', 'testuser')
    await page.fill('input[type="password"]', 'testpass123')
    await page.click('button:has-text("登录")')
    await page.waitForURL('/')
  })

  test('displays portal home', async ({ page }) => {
    await page.goto('http://localhost:5173/portal')

    // 验证用户信息
    await expect(page.locator('.user-name')).toBeVisible()

    // 验证统计卡片
    await expect(page.locator('.stat-card').nth(0)).toBeVisible()
  })

  test('navigates to my assets', async ({ page }) => {
    await page.goto('http://localhost:5173/portal')
    await page.click('text=我的资产')

    await expect(page).toHaveURL('/portal/my-assets')
    await expect(page.locator('.asset-list')).toBeVisible()
  })

  test('navigates to my requests', async ({ page }) => {
    await page.goto('http://localhost:5173/portal')
    await page.click('text=我的申请')

    await expect(page).toHaveURL('/portal/my-requests')
    await expect(page.locator('.request-list')).toBeVisible()
  })

  test('navigates to my tasks', async ({ page }) => {
    await page.goto('http://localhost:5173/portal')
    await page.click('text=待处理')

    await expect(page).toHaveURL('/portal/my-tasks')
    await expect(page.locator('.task-list')).toBeVisible()
  })

  test('filters assets by status', async ({ page }) => {
    await page.goto('http://localhost:5173/portal/my-assets')

    // 选择状态过滤
    await page.click('.el-select:has-text("关系类型")')
    await page.click('text=保管中')

    // 验证过滤结果
    await expect(page.locator('.el-table tbody tr')).toHaveCountGreaterThan(0)
  })

  test('views asset detail', async ({ page }) => {
    await page.goto('http://localhost:5173/portal/my-assets')

    // 点击第一行查看详情
    await page.click('.el-table tbody tr:first-child td:first-child')

    // 验证详情抽屉显示
    await expect(page.locator('.el-drawer')).toBeVisible()
    await expect(page.locator('.asset-detail')).toBeVisible()
  })

  test('switches request tabs', async ({ page }) => {
    await page.goto('http://localhost:5173/portal/my-requests')

    // 点击待审批标签
    await page.click('.el-tabs-item:has-text("待审批")')

    // 验证标签切换
    await expect(page.locator('.el-tabs-item.active')).toContainText('待审批')
  })
})


test.describe('Mobile Portal E2E Tests', () => {
  test.beforeEach(async ({ page, context }) => {
    // 设置移动端视口
    await context.setViewportSize({ width: 375, height: 667 })

    // 登录
    await page.goto('http://localhost:5173/login')
    await page.fill('input[placeholder*="用户名"]', 'testuser')
    await page.fill('input[type="password"]', 'testpass123')
    await page.click('button:has-text("登录")')
    await page.waitForURL('/')
  })

  test('displays mobile home', async ({ page }) => {
    await page.goto('http://localhost:5173/portal/mobile/home')

    // 验证头部
    await expect(page.locator('.mobile-header')).toBeVisible()

    // 验证快捷操作
    await expect(page.locator('.quick-action-btn')).toHaveCount(4)

    // 验证底部导航
    await expect(page.locator('.mobile-tab-bar')).toBeVisible()
  })

  test('navigates using bottom tab bar', async ({ page }) => {
    await page.goto('http://localhost:5173/portal/mobile/home')

    // 点击资产标签
    await page.click('.tab-item >> text=资产')

    // 验证导航
    await expect(page).toHaveURL('/portal/mobile/assets')
    await expect(page.locator('.tab-item.active')).toContainText('资产')
  })

  test('opens scan page', async ({ page }) => {
    await page.goto('http://localhost:5173/portal/mobile/home')

    // 点击扫码按钮
    await page.click('.quick-action-btn >> text=扫码')

    // 验证跳转到扫码页面
    await expect(page).toHaveURL('/portal/scan')
  })
})
```

---

## 5. 测试执行

```bash
# 后端单元测试
pytest apps/portal/tests/ -v

# 前端测试
npm run test -- portal

# E2E测试
npm run test:e2e -- portal.spec.ts

# 移动端E2E测试
npm run test:e2e:mob -- portal.spec.ts
```

---

## 6. 验收标准

### 功能验收

- [ ] 门户首页正确显示用户信息
- [ ] 我的资产列表正确展示用户关联的资产
- [ ] 我的申请列表正确聚合各类型申请
- [ ] 我的待办列表正确展示待处理事项
- [ ] 过滤和搜索功能正常工作
- [ ] 分页功能正常
- [ ] 快捷操作可正常执行
- [ ] 移动端页面适配正确

### 性能验收

- [ ] 门户首页加载时间 < 500ms
- [ ] 资产列表查询时间 < 200ms
- [ ] 申请列表聚合时间 < 300ms

### 兼容性验收

- [ ] Chrome/Firefox/Safari 正常显示
- [ ] 移动端浏览器正常显示
- [ ] 响应式布局正确
