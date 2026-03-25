# Phase 7.2: 资产项目管理 - 测试验证

## 测试策略

采用**TDD（测试驱动开发）**思路，确保项目创建、资产分配、成本核算、项目结项功能的可靠性。

---

## 单元测试

### 后端模型测试

```python
# apps/projects/tests/test_models.py

from django.test import TestCase
from django.utils import timezone
from apps.projects.models import AssetProject, ProjectAsset, ProjectMember
from apps.assets.models import Asset
from apps.accounts.models import User
from apps.organizations.models import Organization, Department
from decimal import Decimal
from datetime import date, timedelta


class AssetProjectModelTest(TestCase):
    """AssetProject模型测试"""

    def setUp(self):
        self.org = Organization.objects.create(code='TEST', name='Test Org')
        self.dept = Department.objects.create(
            organization=self.org,
            name='研发部',
            code='RD'
        )
        self.user = User.objects.create(username='testuser', organization=self.org)

    def test_project_creation(self):
        """测试项目创建"""
        project = AssetProject.objects.create(
            organization=self.org,
            project_code='XM2025010001',
            project_name='AI平台研发项目',
            project_alias='AI平台',
            project_type='development',
            project_manager=self.user,
            department=self.dept,
            start_date=date.today(),
            end_date=date.today() + timedelta(days=180),
            planned_budget=Decimal('500000.00'),
            created_by=self.user,
        )

        self.assertEqual(project.project_code, 'XM2025010001')
        self.assertEqual(project.project_name, 'AI平台研发项目')
        self.assertEqual(project.project_type, 'development')
        self.assertEqual(project.status, 'planning')
        self.assertEqual(project.project_manager, self.user)

    def test_project_status_transition(self):
        """测试项目状态流转"""
        project = AssetProject.objects.create(
            organization=self.org,
            project_code='XM2025010002',
            project_name='测试项目',
            project_type='development',
            project_manager=self.user,
            department=self.dept,
            start_date=date.today(),
            end_date=date.today() + timedelta(days=180),
            created_by=self.user,
        )

        # planning -> active
        project.status = 'active'
        project.actual_start_date = date.today()
        project.save()
        self.assertEqual(project.status, 'active')

        # active -> completed
        project.status = 'completed'
        project.actual_end_date = date.today()
        project.save()
        self.assertEqual(project.status, 'completed')

    def test_project_soft_delete(self):
        """测试项目软删除"""
        project = AssetProject.objects.create(
            organization=self.org,
            project_code='XM2025010003',
            project_name='待删除项目',
            project_type='development',
            project_manager=self.user,
            department=self.dept,
            start_date=date.today(),
            created_by=self.user,
        )

        # 软删除
        project.soft_delete()

        self.assertTrue(project.is_deleted)
        self.assertIsNotNone(project.deleted_at)

        # 正常查询无法获取
        active_projects = AssetProject.objects.filter(project_code='XM2025010003')
        self.assertEqual(active_projects.count(), 0)

    def test_organization_isolation(self):
        """测试组织隔离"""
        org2 = Organization.objects.create(code='TEST2', name='Test Org 2')

        project = AssetProject.objects.create(
            organization=self.org,
            project_code='XM2025010004',
            project_name='测试项目',
            project_type='development',
            project_manager=self.user,
            department=self.dept,
            start_date=date.today(),
            created_by=self.user,
        )

        # 同组织可以查询
        projects = AssetProject.objects.filter(organization=self.org)
        self.assertEqual(projects.count(), 1)

        # 不同组织无法查询
        projects_org2 = AssetProject.objects.filter(organization=org2)
        self.assertEqual(projects_org2.count(), 0)

    def test_project_statistics(self):
        """测试项目统计字段"""
        project = AssetProject.objects.create(
            organization=self.org,
            project_code='XM2025010005',
            project_name='统计测试项目',
            project_type='development',
            project_manager=self.user,
            department=self.dept,
            start_date=date.today(),
            total_assets=10,
            active_assets=8,
            completed_milestones=3,
            total_milestones=10,
            created_by=self.user,
        )

        self.assertEqual(project.total_assets, 10)
        self.assertEqual(project.active_assets, 8)
        self.assertEqual(project.completed_milestones, 3)
        self.assertEqual(project.total_milestones, 10)


class ProjectAssetModelTest(TestCase):
    """ProjectAsset模型测试"""

    def setUp(self):
        self.org = Organization.objects.create(code='TEST', name='Test Org')
        self.dept = Department.objects.create(
            organization=self.org,
            name='研发部',
            code='RD'
        )
        self.user = User.objects.create(username='testuser', organization=self.org)

        self.project = AssetProject.objects.create(
            organization=self.org,
            project_code='XM2025010001',
            project_name='AI平台项目',
            project_type='development',
            project_manager=self.user,
            department=self.dept,
            start_date=date.today(),
            status='active',
            created_by=self.user,
        )

        # 创建资产
        self.asset = Asset.objects.create(
            organization=self.org,
            asset_code='ZC001',
            asset_name='GPU服务器',
            purchase_price=Decimal('50000.00'),
            asset_status='idle',
            created_by=self.user,
        )

    def test_asset_allocation_creation(self):
        """测试资产分配创建"""
        allocation = ProjectAsset.objects.create(
            organization=self.org,
            project=self.project,
            asset=self.asset,
            allocation_no='FP2025010001',
            allocation_date=date.today(),
            allocation_type='temporary',
            allocated_by=self.user,
            custodian=self.user,
            return_date=date.today() + timedelta(days=90),
            allocation_cost=self.asset.purchase_price,
            purpose='用于AI模型训练',
            created_by=self.user,
        )

        self.assertEqual(allocation.project, self.project)
        self.assertEqual(allocation.asset, self.asset)
        self.assertEqual(allocation.allocation_type, 'temporary')
        self.assertEqual(allocation.return_status, 'in_use')
        self.assertTrue(allocation.allocation_no.startswith('FP'))

    def test_asset_snapshot(self):
        """测试资产快照"""
        allocation = ProjectAsset.objects.create(
            organization=self.org,
            project=self.project,
            asset=self.asset,
            allocation_no='FP2025010002',
            allocation_date=date.today(),
            allocation_type='permanent',
            allocated_by=self.user,
            allocation_cost=self.asset.purchase_price,
            asset_snapshot={
                'asset_code': 'ZC001',
                'asset_name': 'GPU服务器',
                'category_name': '电子设备',
                'original_cost': '50000.00',
                'purchase_date': '2024-01-01',
                'status': 'idle'
            },
            created_by=self.user,
        )

        snapshot = allocation.asset_snapshot
        self.assertEqual(snapshot['asset_code'], 'ZC001')
        self.assertEqual(snapshot['asset_name'], 'GPU服务器')
        self.assertEqual(snapshot['original_cost'], '50000.00')

    def test_asset_return(self):
        """测试资产归还"""
        allocation = ProjectAsset.objects.create(
            organization=self.org,
            project=self.project,
            asset=self.asset,
            allocation_no='FP2025010003',
            allocation_date=date.today(),
            allocation_type='temporary',
            allocated_by=self.user,
            return_status='in_use',
            created_by=self.user,
        )

        # 归还资产
        allocation.return_status = 'returned'
        allocation.actual_return_date = date.today()
        allocation.save()

        self.assertEqual(allocation.return_status, 'returned')
        self.assertIsNotNone(allocation.actual_return_date)

    def test_asset_transfer(self):
        """测试资产转移"""
        target_project = AssetProject.objects.create(
            organization=self.org,
            project_code='XM2025010002',
            project_name='目标项目',
            project_type='development',
            project_manager=self.user,
            department=self.dept,
            start_date=date.today(),
            status='active',
            created_by=self.user,
        )

        allocation = ProjectAsset.objects.create(
            organization=self.org,
            project=self.project,
            asset=self.asset,
            allocation_no='FP2025010004',
            allocation_date=date.today(),
            allocation_type='temporary',
            allocated_by=self.user,
            return_status='in_use',
            created_by=self.user,
        )

        # 转移资产
        allocation.return_status = 'transferred'
        allocation.actual_return_date = date.today()
        allocation.save()

        self.assertEqual(allocation.return_status, 'transferred')

    def test_depreciation_calculation(self):
        """测试折旧计算"""
        allocation = ProjectAsset.objects.create(
            organization=self.org,
            project=self.project,
            asset=self.asset,
            allocation_no='FP2025010005',
            allocation_date=date.today(),
            allocation_type='permanent',
            allocated_by=self.user,
            allocation_cost=Decimal('50000.00'),
            depreciation_rate=Decimal('0.01'),
            monthly_depreciation=Decimal('500.00'),
            created_by=self.user,
        )

        self.assertEqual(allocation.monthly_depreciation, Decimal('500.00'))
        self.assertEqual(allocation.depreciation_rate, Decimal('0.01'))


class ProjectMemberModelTest(TestCase):
    """ProjectMember模型测试"""

    def setUp(self):
        self.org = Organization.objects.create(code='TEST', name='Test Org')
        self.dept = Department.objects.create(
            organization=self.org,
            name='研发部',
            code='RD'
        )
        self.user = User.objects.create(username='testuser', organization=self.org)

        self.project = AssetProject.objects.create(
            organization=self.org,
            project_code='XM2025010001',
            project_name='AI平台项目',
            project_type='development',
            project_manager=self.user,
            department=self.dept,
            start_date=date.today(),
            created_by=self.user,
        )

    def test_add_project_member(self):
        """测试添加项目成员"""
        member = ProjectMember.objects.create(
            organization=self.org,
            project=self.project,
            user=self.user,
            role='member',
            join_date=date.today(),
            created_by=self.user,
        )

        self.assertEqual(member.project, self.project)
        self.assertEqual(member.user, self.user)
        self.assertEqual(member.role, 'member')
        self.assertTrue(member.is_active)

    def test_project_manager_role(self):
        """测试项目经理角色"""
        manager = ProjectMember.objects.create(
            organization=self.org,
            project=self.project,
            user=self.user,
            role='manager',
            join_date=date.today(),
            can_allocate_asset=True,
            can_view_cost=True,
            created_by=self.user,
        )

        self.assertEqual(manager.role, 'manager')
        self.assertTrue(manager.can_allocate_asset)
        self.assertTrue(manager.can_view_cost)

    def test_member_leave_project(self):
        """测试成员离开项目"""
        member = ProjectMember.objects.create(
            organization=self.org,
            project=self.project,
            user=self.user,
            role='member',
            join_date=date.today(),
            created_by=self.user,
        )

        # 离开项目
        member.is_active = False
        member.leave_date = date.today()
        member.save()

        self.assertFalse(member.is_active)
        self.assertIsNotNone(member.leave_date)

    def test_unique_project_user(self):
        """测试项目成员唯一性"""
        ProjectMember.objects.create(
            organization=self.org,
            project=self.project,
            user=self.user,
            role='member',
            join_date=date.today(),
            created_by=self.user,
        )

        # 尝试重复添加应该失败
        with self.assertRaises(Exception):
            ProjectMember.objects.create(
                organization=self.org,
                project=self.project,
                user=self.user,
                role='member',
                join_date=date.today(),
                created_by=self.user,
            )
```

### 后端服务测试

```python
# apps/projects/tests/test_services.py

from django.test import TestCase
from apps.projects.services import AssetProjectService
from apps.projects.models import AssetProject, ProjectAsset, ProjectMember
from apps.assets.models import Asset
from apps.accounts.models import User
from apps.organizations.models import Organization, Department
from decimal import Decimal
from datetime import date, timedelta


class AssetProjectServiceTest(TestCase):
    """AssetProjectService测试"""

    def setUp(self):
        self.org = Organization.objects.create(code='TEST', name='Test Org')
        self.dept = Department.objects.create(
            organization=self.org,
            name='研发部',
            code='RD'
        )
        self.user = User.objects.create(username='testuser', organization=self.org)
        self.service = AssetProjectService()

        self.project = AssetProject.objects.create(
            organization=self.org,
            project_code='XM2025010001',
            project_name='AI平台项目',
            project_type='development',
            project_manager=self.user,
            department=self.dept,
            start_date=date.today(),
            status='active',
            created_by=self.user,
        )

    def test_allocate_assets(self):
        """测试分配资产到项目"""
        asset = Asset.objects.create(
            organization=self.org,
            asset_code='ZC001',
            asset_name='GPU服务器',
            purchase_price=Decimal('50000.00'),
            asset_status='idle',
            created_by=self.user,
        )

        assets_data = [
            {'asset_id': str(asset.id), 'custodian_id': str(self.user.id)}
        ]

        allocations = self.service.allocate_assets(
            project=self.project,
            assets_data=assets_data,
            allocation_type='temporary',
            allocation_date=date.today(),
            return_date=date.today() + timedelta(days=90),
            purpose='用于AI模型训练',
            usage_location='数据中心',
            allocated_by=self.user
        )

        self.assertEqual(len(allocations), 1)
        self.assertEqual(allocations[0].project, self.project)
        self.assertEqual(allocations[0].asset, asset)

        # 验证项目统计更新
        self.project.refresh_from_db()
        self.assertEqual(self.project.total_assets, 1)
        self.assertEqual(self.project.active_assets, 1)

    def test_return_assets_to_inventory(self):
        """测试归还资产到库存"""
        asset = Asset.objects.create(
            organization=self.org,
            asset_code='ZC002',
            asset_name='工作站',
            purchase_price=Decimal('20000.00'),
            asset_status='project_assigned',
            created_by=self.user,
        )

        allocation = ProjectAsset.objects.create(
            organization=self.org,
            project=self.project,
            asset=asset,
            allocation_no='FP2025010001',
            allocation_date=date.today(),
            allocation_type='temporary',
            allocated_by=self.user,
            return_status='in_use',
            created_by=self.user,
        )

        # 归还资产
        results = self.service.return_assets(
            project=self.project,
            asset_ids=[str(asset.id)],
            return_type='to_inventory',
            target_project_id=None,
            notes='项目结束',
            operator=self.user
        )

        self.assertEqual(results['returned_count'], 1)

        # 验证分配记录状态
        allocation.refresh_from_db()
        self.assertEqual(allocation.return_status, 'returned')

        # 验证资产状态
        asset.refresh_from_db()
        self.assertEqual(asset.asset_status, 'idle')

    def test_transfer_asset_to_project(self):
        """测试转移资产到其他项目"""
        target_project = AssetProject.objects.create(
            organization=self.org,
            project_code='XM2025010002',
            project_name='目标项目',
            project_type='development',
            project_manager=self.user,
            department=self.dept,
            start_date=date.today(),
            status='active',
            created_by=self.user,
        )

        asset = Asset.objects.create(
            organization=self.org,
            asset_code='ZC003',
            asset_name='服务器',
            purchase_price=Decimal('30000.00'),
            created_by=self.user,
        )

        allocation = ProjectAsset.objects.create(
            organization=self.org,
            project=self.project,
            asset=asset,
            allocation_no='FP2025010002',
            allocation_date=date.today(),
            allocation_type='temporary',
            allocated_by=self.user,
            return_status='in_use',
            created_by=self.user,
        )

        # 转移资产
        new_allocation = self.service.transfer_asset(
            allocation=allocation,
            target_project_id=str(target_project.id),
            reason='项目调整',
            operator=self.user
        )

        self.assertEqual(new_allocation.project, target_project)
        self.assertEqual(new_allocation.asset, asset)

        # 验证原分配记录
        allocation.refresh_from_db()
        self.assertEqual(allocation.return_status, 'transferred')

    def test_calculate_cost_summary(self):
        """测试计算成本汇总"""
        # 创建多个资产分配
        for i in range(3):
            asset = Asset.objects.create(
                organization=self.org,
                asset_code=f'ZC{i:03d}',
                asset_name=f'资产{i}',
                purchase_price=Decimal('50000.00'),
                created_by=self.user,
            )

            ProjectAsset.objects.create(
                organization=self.org,
                project=self.project,
                asset=asset,
                allocation_no=f'FP202501000{i}',
                allocation_date=date.today(),
                allocation_type='permanent',
                allocated_by=self.user,
                allocation_cost=Decimal('50000.00'),
                monthly_depreciation=Decimal('500.00'),
                return_status='in_use',
                created_by=self.user,
            )

        cost_summary = self.service.calculate_cost_summary(self.project)

        self.assertEqual(float(cost_summary['total_asset_cost']), 150000.00)
        self.assertEqual(float(cost_summary['monthly_depreciation']), 1500.00)
        self.assertEqual(cost_summary['allocation_count'], 3)

    def test_generate_allocation_no(self):
        """测试生成分配单号"""
        allocation_no = self.service._generate_allocation_no()
        self.assertTrue(allocation_no.startswith('FP'))
        self.assertIn(str(date.today().year), allocation_no)
        self.assertIn(str(date.today().month).zfill(2), allocation_no)

    def test_close_project_with_assets(self):
        """测试关闭有资产的项目"""
        Asset.objects.create(
            organization=self.org,
            asset_code='ZC001',
            asset_name='GPU服务器',
            created_by=self.user,
        )

        ProjectAsset.objects.create(
            organization=self.org,
            project=self.project,
            asset_id='test-asset-id',
            allocation_no='FP2025010001',
            allocation_date=date.today(),
            return_status='in_use',
            created_by=self.user,
        )

        # 尝试关闭有资产的项目应该失败
        with self.assertRaises(Exception):
            self.service.close_project(self.project, self.user)

    def test_close_project_without_assets(self):
        """测试关闭无资产的项目"""
        # 确保没有未归还的资产
        ProjectAsset.objects.filter(project=self.project, return_status='in_use').delete()

        # 关闭项目
        result = self.service.close_project(self.project, self.user)

        self.project.refresh_from_db()
        self.assertEqual(self.project.status, 'completed')
        self.assertIsNotNone(self.project.actual_end_date)
```

---

## API集成测试

```python
# apps/projects/tests/test_api.py

from django.test import TestCase
from rest_framework.test import APIClient
from apps.projects.models import AssetProject, ProjectAsset, ProjectMember
from apps.assets.models import Asset
from apps.accounts.models import User
from apps.organizations.models import Organization, Department
from decimal import Decimal
from datetime import date, timedelta


class AssetProjectAPITest(TestCase):
    """项目API集成测试"""

    def setUp(self):
        self.client = APIClient()
        self.org = Organization.objects.create(code='TEST', name='Test Org')
        self.dept = Department.objects.create(
            organization=self.org,
            name='研发部',
            code='RD'
        )

        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123',
            organization=self.org
        )
        self.client.force_authenticate(user=self.user)

    def test_create_project(self):
        """测试创建项目"""
        response = self.client.post(
            '/api/projects/',
            {
                'project_name': 'AI平台研发项目',
                'project_alias': 'AI平台',
                'project_type': 'development',
                'project_manager': str(self.user.id),
                'department': str(self.dept.id),
                'start_date': str(date.today()),
                'end_date': str(date.today() + timedelta(days=180)),
                'planned_budget': '500000.00',
                'description': '企业级AI平台研发',
                'technical_requirements': 'Python、TensorFlow、GPU服务器'
            },
            format='json'
        )

        self.assertEqual(response.status_code, 201)
        data = response.json()
        self.assertTrue(data['success'])
        self.assertEqual(data['data']['project_name'], 'AI平台研发项目')
        self.assertTrue(data['data']['project_code'].startswith('XM'))

    def test_get_projects_list(self):
        """测试获取项目列表"""
        AssetProject.objects.create(
            organization=self.org,
            project_code='XM2025010001',
            project_name='AI平台项目',
            project_type='development',
            project_manager=self.user,
            department=self.dept,
            start_date=date.today(),
            status='active',
            created_by=self.user,
        )

        response = self.client.get('/api/projects/')

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn('results', data['data'])

    def test_get_project_detail(self):
        """测试获取项目详情"""
        project = AssetProject.objects.create(
            organization=self.org,
            project_code='XM2025010002',
            project_name='测试项目',
            project_type='development',
            project_manager=self.user,
            department=self.dept,
            start_date=date.today(),
            status='active',
            created_by=self.user,
        )

        response = self.client.get(f'/api/projects/{project.id}/')

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data['success'])
        self.assertEqual(data['data']['project_code'], 'XM2025010002')

    def test_allocate_assets_api(self):
        """测试分配资产API"""
        project = AssetProject.objects.create(
            organization=self.org,
            project_code='XM2025010003',
            project_name='测试项目',
            project_type='development',
            project_manager=self.user,
            department=self.dept,
            start_date=date.today(),
            status='active',
            created_by=self.user,
        )

        asset = Asset.objects.create(
            organization=self.org,
            asset_code='ZC001',
            asset_name='GPU服务器',
            purchase_price=Decimal('50000.00'),
            asset_status='idle',
            created_by=self.user,
        )

        response = self.client.post(
            f'/api/projects/{project.id}/allocate-assets/',
            {
                'assets': [
                    {
                        'asset_id': str(asset.id),
                        'custodian_id': str(self.user.id)
                    }
                ],
                'allocation_type': 'temporary',
                'allocation_date': str(date.today()),
                'return_date': str(date.today() + timedelta(days=90)),
                'purpose': '用于AI模型训练',
                'usage_location': '数据中心'
            },
            format='json'
        )

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data['success'])
        self.assertIn('成功分配', data['message'])

    def test_return_assets_api(self):
        """测试归还资产API"""
        project = AssetProject.objects.create(
            organization=self.org,
            project_code='XM2025010004',
            project_name='测试项目',
            project_type='development',
            project_manager=self.user,
            department=self.dept,
            start_date=date.today(),
            status='active',
            created_by=self.user,
        )

        asset = Asset.objects.create(
            organization=self.org,
            asset_code='ZC002',
            asset_name='工作站',
            asset_status='project_assigned',
            created_by=self.user,
        )

        ProjectAsset.objects.create(
            organization=self.org,
            project=project,
            asset=asset,
            allocation_no='FP2025010001',
            allocation_date=date.today(),
            return_status='in_use',
            created_by=self.user,
        )

        response = self.client.post(
            f'/api/projects/{project.id}/return-assets/',
            {
                'asset_ids': [str(asset.id)],
                'return_type': 'to_inventory',
                'notes': '项目结束'
            },
            format='json'
        )

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data['success'])
        self.assertEqual(data['summary']['returned'], 1)

    def test_get_project_assets(self):
        """测试获取项目资产"""
        project = AssetProject.objects.create(
            organization=self.org,
            project_code='XM2025010005',
            project_name='测试项目',
            project_type='development',
            project_manager=self.user,
            department=self.dept,
            start_date=date.today(),
            status='active',
            created_by=self.user,
        )

        asset = Asset.objects.create(
            organization=self.org,
            asset_code='ZC003',
            asset_name='服务器',
            created_by=self.user,
        )

        ProjectAsset.objects.create(
            organization=self.org,
            project=project,
            asset=asset,
            allocation_no='FP2025010002',
            allocation_date=date.today(),
            return_status='in_use',
            created_by=self.user,
        )

        response = self.client.get(f'/api/projects/{project.id}/assets/')

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn('results', data['data'])

    def test_get_cost_summary(self):
        """测试获取成本汇总"""
        project = AssetProject.objects.create(
            organization=self.org,
            project_code='XM2025010006',
            project_name='测试项目',
            project_type='development',
            project_manager=self.user,
            department=self.dept,
            start_date=date.today(),
            status='active',
            created_by=self.user,
        )

        response = self.client.get(f'/api/projects/{project.id}/cost-summary/')

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data['success'])
        self.assertIn('total_asset_cost', data['data'])

    def test_close_project_api(self):
        """测试关闭项目API"""
        project = AssetProject.objects.create(
            organization=self.org,
            project_code='XM2025010007',
            project_name='待关闭项目',
            project_type='development',
            project_manager=self.user,
            department=self.dept,
            start_date=date.today(),
            status='active',
            created_by=self.user,
        )

        response = self.client.post(f'/api/projects/{project.id}/close/')

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data['success'])
        self.assertEqual(data['data']['status'], 'completed')

    def test_close_project_with_assets_fails(self):
        """测试关闭有资产的项目失败"""
        project = AssetProject.objects.create(
            organization=self.org,
            project_code='XM2025010008',
            project_name='有资产项目',
            project_type='development',
            project_manager=self.user,
            department=self.dept,
            start_date=date.today(),
            status='active',
            total_assets=1,
            active_assets=1,
            created_by=self.user,
        )

        response = self.client.post(f'/api/projects/{project.id}/close/')

        self.assertEqual(response.status_code, 400)
        data = response.json()
        self.assertFalse(data['success'])
        self.assertEqual(data['error']['code'], 'ASSETS_NOT_RETURNED')

    def test_get_my_projects(self):
        """测试获取我的项目"""
        project = AssetProject.objects.create(
            organization=self.org,
            project_code='XM2025010009',
            project_name='我的项目',
            project_type='development',
            project_manager=self.user,
            department=self.dept,
            start_date=date.today(),
            status='active',
            created_by=self.user,
        )

        ProjectMember.objects.create(
            organization=self.org,
            project=project,
            user=self.user,
            role='member',
            join_date=date.today(),
            created_by=self.user,
        )

        response = self.client.get('/api/projects/my-projects/')

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertGreater(len(data['data']['results']), 0)


class ProjectAssetAPITest(TestCase):
    """项目资产API测试"""

    def setUp(self):
        self.client = APIClient()
        self.org = Organization.objects.create(code='TEST', name='Test Org')
        self.dept = Department.objects.create(
            organization=self.org,
            name='研发部',
            code='RD'
        )
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123',
            organization=self.org
        )
        self.client.force_authenticate(user=self.user)

        self.project = AssetProject.objects.create(
            organization=self.org,
            project_code='XM2025010001',
            project_name='AI平台项目',
            project_type='development',
            project_manager=self.user,
            department=self.dept,
            start_date=date.today(),
            status='active',
            created_by=self.user,
        )

        self.asset = Asset.objects.create(
            organization=self.org,
            asset_code='ZC001',
            asset_name='GPU服务器',
            purchase_price=Decimal('50000.00'),
            created_by=self.user,
        )

    def test_get_project_assets_list(self):
        """测试获取项目资产列表"""
        ProjectAsset.objects.create(
            organization=self.org,
            project=self.project,
            asset=self.asset,
            allocation_no='FP2025010001',
            allocation_date=date.today(),
            return_status='in_use',
            created_by=self.user,
        )

        response = self.client.get('/api/projects/assets/')

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn('results', data['data'])

    def test_transfer_asset(self):
        """测试转移资产"""
        target_project = AssetProject.objects.create(
            organization=self.org,
            project_code='XM2025010002',
            project_name='目标项目',
            project_type='development',
            project_manager=self.user,
            department=self.dept,
            start_date=date.today(),
            status='active',
            created_by=self.user,
        )

        allocation = ProjectAsset.objects.create(
            organization=self.org,
            project=self.project,
            asset=self.asset,
            allocation_no='FP2025010002',
            allocation_date=date.today(),
            return_status='in_use',
            created_by=self.user,
        )

        response = self.client.post(
            f'/api/projects/assets/{allocation.id}/transfer/',
            {
                'target_project_id': str(target_project.id),
                'reason': '项目调整'
            },
            format='json'
        )

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data['success'])
        self.assertEqual(data['data']['project']['project_code'], 'XM2025010002')
```

---

## 前端组件测试

```vue
<!-- src/views/projects/__tests__/ProjectForm.spec.vue -->
<script setup>
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount } from '@vue/test-utils'
import ProjectForm from '../ProjectForm.vue'
import { createPinia, setActivePinia } from 'pinia'

vi.mock('@/api/projects', () => ({
  createProject: vi.fn(() => Promise.resolve({
    success: true,
    data: { id: 'project-uuid', project_code: 'XM2025010001' }
  })),
  updateProject: vi.fn(() => Promise.resolve({ success: true })),
  getProject: vi.fn(() => Promise.resolve({
    success: true,
    data: {
      id: 'project-uuid',
      project_name: 'AI平台项目',
      project_type: 'development'
    }
  }))
}))

describe('ProjectForm.vue', () => {
  let wrapper
  let pinia

  beforeEach(() => {
    pinia = createPinia()
    setActivePinia(pinia)

    wrapper = mount(ProjectForm, {
      props: {
        projectId: null
      },
      global: {
        stubs: {
          ElForm: true,
          ElFormItem: true,
          ElInput: true,
          ElSelect: true,
          ElOption: true,
          ElDatePicker: true,
          ElButton: true
        },
        mocks: {
          $router: { push: vi.fn() }
        }
      }
    })
  })

  it('初始化表单', () => {
    expect(wrapper.vm.form.project_name).toBe('')
    expect(wrapper.vm.form.project_type).toBe('development')
  })

  it('提交项目', async () => {
    wrapper.vm.form = {
      project_name: 'AI平台项目',
      project_type: 'development',
      project_manager: 'user-uuid',
      department: 'dept-uuid',
      start_date: new Date(),
      end_date: new Date(),
      planned_budget: '500000.00'
    }

    await wrapper.vm.handleSubmit()

    const { createProject } = await import('@/api/projects')
    expect(createProject).toHaveBeenCalled()
  })
})
</script>
```

```vue
<!-- src/views/projects/__tests__/AssetAllocateDialog.spec.vue -->
<script setup>
import { describe, it, expect, vi } from 'vitest'
import { mount } from '@vue/test-utils'
import AssetAllocateDialog from '../AssetAllocateDialog.vue'

vi.mock('@/api/projects', () => ({
  allocateAssets: vi.fn(() => Promise.resolve({
    success: true,
    data: [{ id: 'allocation-uuid', allocation_no: 'FP2025010001' }]
  }))
}))

describe('AssetAllocateDialog.vue', () => {
  it('显示资产选择', () => {
    const wrapper = mount(AssetAllocateDialog, {
      props: {
        project: {
          id: 'project-uuid',
          project_name: 'AI平台项目',
          status: 'active'
        }
      },
      global: {
        stubs: {
          ElDialog: true,
          ElTable: true,
          ElButton: true
        }
      }
    })

    wrapper.vm.openDialog()
    expect(wrapper.vm.dialogVisible).toBe(true)
  })

  it('选择资产并提交', async () => {
    const wrapper = mount(AssetAllocateDialog, {
      props: {
        project: { id: 'project-uuid' }
      },
      global: { stubs: { ElDialog: true, ElButton: true } }
    })

    wrapper.vm.selectedAssets = [
      { asset_id: 'asset-1', custodian_id: 'user-1' },
      { asset_id: 'asset-2', custodian_id: 'user-2' }
    ]

    wrapper.vm.allocationForm = {
      allocation_type: 'temporary',
      return_date: '2025-06-30',
      purpose: '测试'
    }

    await wrapper.vm.handleAllocate()

    const { allocateAssets } = await import('@/api/projects')
    expect(allocateAssets).toHaveBeenCalled()
  })
})
</script>
```

---

## E2E测试

```python
# tests/e2e/test_project_e2e.py

from playwright.sync_api import Page, expect


class TestProjectE2E:
    """项目管理端到端测试"""

    def setup_method(self):
        self.page = self.browser.new_page()
        self.page.goto('http://localhost:5173/login')
        self.page.fill('input[name="username"]', 'admin')
        self.page.fill('input[name="password"]', 'admin123')
        self.page.click('button:has-text("登录")')

    def test_create_project_flow(self):
        """测试创建项目完整流程"""
        self.page.goto('http://localhost:5173/projects')
        self.page.click('button:has-text("新建项目")')

        # 填写项目信息
        self.page.fill('[name="project_name"]', 'AI平台研发项目')
        self.page.fill('[name="project_alias"]', 'AI平台')
        self.page.select_option('[name="project_type"]', 'development')
        self.page.select_option('[name="project_manager"]', '张三')
        self.page.select_option('[name="department"]', '研发部')
        self.page.fill('[name="start_date"]', '2025-01-01')
        self.page.fill('[name="end_date"]', '2025-06-30')
        self.page.fill('[name="planned_budget"]', '500000')

        # 提交
        self.page.click('button:has-text("提交")')

        # 验证成功
        self.page.wait_for_selector('.el-message--success')

    def test_allocate_asset_flow(self):
        """测试分配资产流程"""
        self.page.goto('http://localhost:5173/projects/project-uuid')
        self.page.click('button:has-text("分配资产")')

        # 选择资产
        self.page.click('.asset-selector .el-select')
        self.page.click('text=GPU服务器')

        # 选择保管人
        self.page.click('.custodian-selector .el-select')
        self.page.click('text=李四')

        # 填写分配信息
        self.page.select_option('[name="allocation_type"]', 'temporary')
        self.page.fill('[name="return_date"]', '2025-06-30')
        self.page.fill('[name="purpose"]', '用于AI模型训练')

        # 确认分配
        self.page.click('button:has-text("确认分配")')

        # 验证成功
        self.page.wait_for_selector('.el-message--success')

    def test_view_project_assets(self):
        """测试查看项目资产"""
        self.page.goto('http://localhost:5173/projects/project-uuid')

        # 切换到资产标签
        self.page.click('text=项目资产')

        # 验证资产列表显示
        expect(self.page.locator('.asset-table')).to_be_visible()

    def test_view_cost_summary(self):
        """测试查看成本汇总"""
        self.page.goto('http://localhost:5173/projects/project-uuid')

        # 切换到成本标签
        self.page.click('text=成本汇总')

        # 验证成本数据显示
        expect(self.page.locator('.total-asset-cost')).to_be_visible()
        expect(self.page.locator('.monthly-depreciation')).to_be_visible()
```

---

## 验收标准检查清单

### 后端验收

- [ ] AssetProject模型创建和状态流转正常
- [ ] ProjectAsset资产分配和归还正常
- [ ] ProjectMember成员管理正常
- [ ] 软删除功能正常
- [ ] 组织隔离正常
- [ ] 审计字段自动填充

### API验收

- [ ] 项目CRUD接口正常
- [ ] 分配资产接口正常
- [ ] 归还资产接口正常
- [ ] 转移资产接口正常
- [ ] 成本汇总接口正常
- [ ] 关闭项目接口正常
- [ ] 错误码和错误消息正确

### 前端验收

- [ ] ProjectForm组件正常提交
- [ ] AssetAllocateDialog组件正常
- [ ] ProjectAssetList组件正常显示
- [ ] CostSummary组件正常计算
- [ ] 项目列表和详情页正常

---

## 运行测试命令

```bash
# 后端单元测试
docker-compose exec backend python manage.py test apps.projects.tests

# 运行特定测试
docker-compose exec backend python manage.py test apps.projects.tests.test_models
docker-compose exec backend python manage.py test apps.projects.tests.test_services
docker-compose exec backend python manage.py test apps.projects.tests.test_api

# 带覆盖率报告
docker-compose exec backend coverage run --source='apps.projects' manage.py test apps.projects.tests
docker-compose exec backend coverage report

# 前端测试
npm run test

# E2E测试
npm run test:e2e
```
