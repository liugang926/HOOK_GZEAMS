# Phase 2.4: 组织架构增强与数据权限 - 测试计划

## 概述

本文档描述组织架构增强与数据权限模块的测试策略，包括单元测试、集成测试、端到端测试和性能测试。

---

## 1. 单元测试

### 1.1 Department 模型测试

```python
# tests/apps/organizations/test_models.py

import pytest
from apps.organizations.models import Department, UserDepartment
from apps.accounts.models import User


@pytest.mark.django_db
class TestDepartmentModel:
    """Department 模型测试"""

    def test_create_root_department(self, organization):
        """测试创建根部门"""
        dept = Department.objects.create(
            organization=organization,
            code='HQ',
            name='总部'
        )

        assert dept.level == 0
        assert dept.full_path == '总部'
        assert dept.full_path_name == '总部'
        assert dept.parent is None

    def test_create_child_department(self, organization):
        """测试创建子部门"""
        parent = Department.objects.create(
            organization=organization,
            code='HQ',
            name='总部'
        )

        child = Department.objects.create(
            organization=organization,
            code='TECH',
            name='技术部',
            parent=parent
        )

        assert child.level == 1
        assert child.full_path == '总部/技术部'
        assert child.full_path_name == '总部/技术部'
        assert child.parent_id == parent.id

    def test_update_department_path_recursively(self, organization):
        """测试更新部门路径时递归更新子部门"""
        root = Department.objects.create(
            organization=organization,
            code='HQ',
            name='总部'
        )

        child1 = Department.objects.create(
            organization=organization,
            code='TECH',
            name='技术部',
            parent=root
        )

        child2 = Department.objects.create(
            organization=organization,
            code='BACKEND',
            name='后端组',
            parent=child1
        )

        # 修改根部门名称
        root.name = '中国区总部'
        root.save()

        # 刷新子部门
        child1.refresh_from_db()
        child2.refresh_from_db()

        assert child1.full_path_name == '中国区总部/技术部'
        assert child2.full_path_name == '中国区总部/技术部/后端组'

    def test_get_all_children(self, organization):
        """测试获取所有子部门"""
        root = Department.objects.create(
            organization=organization,
            code='HQ',
            name='总部'
        )

        child1 = Department.objects.create(
            organization=organization,
            code='TECH',
            name='技术部',
            parent=root
        )

        child2 = Department.objects.create(
            organization=organization,
            code='BACKEND',
            name='后端组',
            parent=child1
        )

        children = root.get_all_children()

        assert len(children) == 2
        assert child1 in children
        assert child2 in children

    def test_get_descendant_ids(self, organization):
        """测试获取所有后代部门ID"""
        root = Department.objects.create(
            organization=organization,
            code='HQ',
            name='总部'
        )

        child1 = Department.objects.create(
            organization=organization,
            code='TECH',
            name='技术部',
            parent=root
        )

        child2 = Department.objects.create(
            organization=organization,
            code='BACKEND',
            name='后端组',
            parent=child1
        )

        descendant_ids = root.get_descendant_ids()

        assert root.id in descendant_ids
        assert child1.id in descendant_ids
        assert child2.id in descendant_ids

    def test_department_leader(self, organization, user):
        """测试部门负责人"""
        dept = Department.objects.create(
            organization=organization,
            code='TECH',
            name='技术部',
            leader=user
        )

        assert dept.leader_id == user.id
        assert dept.leader == user


@pytest.mark.django_db
class TestUserDepartmentModel:
    """UserDepartment 模型测试"""

    def test_user_multiple_departments(self, organization, user):
        """测试用户属于多个部门"""
        dept1 = Department.objects.create(
            organization=organization,
            code='TECH',
            name='技术部'
        )

        dept2 = Department.objects.create(
            organization=organization,
            code='ADMIN',
            name='行政部'
        )

        ud1 = UserDepartment.objects.create(
            user=user,
            organization=organization,
            department=dept1,
            is_primary=True,
            is_asset_department=True
        )

        ud2 = UserDepartment.objects.create(
            user=user,
            organization=organization,
            department=dept2,
            is_primary=False,
            is_asset_department=False
        )

        assert user.my_departments.count() == 2
        assert user.primary_department == dept1

    def test_only_one_primary_department(self, organization, user):
        """测试用户只能有一个主部门"""
        dept1 = Department.objects.create(
            organization=organization,
            code='TECH',
            name='技术部'
        )

        dept2 = Department.objects.create(
            organization=organization,
            code='ADMIN',
            name='行政部'
        )

        UserDepartment.objects.create(
            user=user,
            organization=organization,
            department=dept1,
            is_primary=True
        )

        # 创建第二个主部门关联
        UserDepartment.objects.create(
            user=user,
            organization=organization,
            department=dept2,
            is_primary=True
        )

        # 只有最新的一个是主部门
        primary_depts = user.my_departments.filter(is_primary=True)
        assert primary_depts.count() == 1
        assert primary_depts.first().department == dept2

    def test_user_asset_department_property(self, organization, user):
        """测试用户资产归属部门"""
        dept = Department.objects.create(
            organization=organization,
            code='TECH',
            name='技术部'
        )

        user.asset_department = dept
        user.save()

        assert user.asset_department_name == '技术部'
        assert user.get_department_for_asset() == dept
```

### 1.2 数据权限服务测试

```python
# tests/apps/organizations/test_permission_service.py

import pytest
from apps.organizations.services.permission_service import OrgDataPermissionService
from apps.organizations.models import Department, UserDepartment
from apps.accounts.models import User
from apps.assets.models import Asset


@pytest.mark.django_db
class TestOrgDataPermissionService:
    """数据权限服务测试"""

    def test_get_viewable_departments_own_depts(self, organization, user):
        """测试获取可查看的部门（自己所属的部门）"""
        dept1 = Department.objects.create(
            organization=organization,
            code='TECH',
            name='技术部'
        )

        dept2 = Department.objects.create(
            organization=organization,
            code='ADMIN',
            name='行政部'
        )

        UserDepartment.objects.create(
            user=user,
            organization=organization,
            department=dept1
        )

        UserDepartment.objects.create(
            user=user,
            organization=organization,
            department=dept2
        )

        service = OrgDataPermissionService(user, organization.id)
        dept_ids = service.get_viewable_department_ids()

        assert dept1.id in dept_ids
        assert dept2.id in dept_ids

    def test_get_viewable_departments_led_depts(self, organization, user, another_user):
        """测试获取可查看的部门（负责的部门）"""
        dept1 = Department.objects.create(
            organization=organization,
            code='TECH',
            name='技术部',
            leader=user
        )

        dept2 = Department.objects.create(
            organization=organization,
            code='BACKEND',
            name='后端组',
            parent=dept1
        )

        # 用户不属于技术部，但是是负责人
        service = OrgDataPermissionService(user, organization.id)
        dept_ids = service.get_viewable_department_ids(recursive=True)

        assert dept1.id in dept_ids
        assert dept2.id in dept_ids  # 递归包含子部门

    def test_can_view_asset_own_custodian(self, organization, user):
        """测试是否可以查看资产（自己是保管人）"""
        asset = Asset.objects.create(
            organization=organization,
            asset_code='ZC001',
            asset_name='MacBook Pro',
            custodian=user
        )

        service = OrgDataPermissionService(user, organization.id)
        assert service.can_view_asset(asset) is True

    def test_can_view_asset_subordinate(self, organization, user, another_user):
        """测试是否可以查看资产（下属的资产）"""
        dept = Department.objects.create(
            organization=organization,
            code='TECH',
            name='技术部',
            leader=user
        )

        UserDepartment.objects.create(
            user=another_user,
            organization=organization,
            department=dept
        )

        asset = Asset.objects.create(
            organization=organization,
            asset_code='ZC001',
            asset_name='MacBook Pro',
            custodian=another_user
        )

        service = OrgDataPermissionService(user, organization.id)
        assert service.can_view_asset(asset) is True

    def test_cannot_view_asset_unrelated(self, organization, user, another_user):
        """测试不能查看无关资产"""
        asset = Asset.objects.create(
            organization=organization,
            asset_code='ZC001',
            asset_name='MacBook Pro',
            custodian=another_user
        )

        service = OrgDataPermissionService(user, organization.id)
        assert service.can_view_asset(asset) is False

    def test_get_managed_asset_queryset(self, organization, user, another_user):
        """测试获取可管理的资产查询集"""
        dept = Department.objects.create(
            organization=organization,
            code='TECH',
            name='技术部',
            leader=user
        )

        UserDepartment.objects.create(
            user=another_user,
            organization=organization,
            department=dept
        )

        # 创建两个资产
        asset1 = Asset.objects.create(
            organization=organization,
            asset_code='ZC001',
            asset_name='MacBook Pro',
            custodian=another_user
        )

        asset2 = Asset.objects.create(
            organization=organization,
            asset_code='ZC002',
            asset_name='Dell 显示器',
            custodian=user
        )

        service = OrgDataPermissionService(user, organization.id)
        queryset = service.get_managed_asset_queryset(Asset)

        assert asset1 in queryset
        assert asset2 in queryset

    def test_check_department_leader_permission_direct(self, organization, user):
        """测试检查部门负责人权限（直接负责人）"""
        dept = Department.objects.create(
            organization=organization,
            code='TECH',
            name='技术部',
            leader=user
        )

        service = OrgDataPermissionService(user, organization.id)
        assert service.check_department_leader_permission(dept.id, user) is True

    def test_check_department_leader_permission_parent(self, organization, user):
        """测试检查部门负责人权限（上级部门负责人）"""
        parent_dept = Department.objects.create(
            organization=organization,
            code='TECH',
            name='技术部',
            leader=user
        )

        child_dept = Department.objects.create(
            organization=organization,
            code='BACKEND',
            name='后端组',
            parent=parent_dept
        )

        service = OrgDataPermissionService(user, organization.id)
        assert service.check_department_leader_permission(child_dept.id, user) is True

    def test_get_subordinate_users(self, organization, user, another_user):
        """测试获取下属用户列表"""
        dept = Department.objects.create(
            organization=organization,
            code='TECH',
            name='技术部',
            leader=user
        )

        UserDepartment.objects.create(
            user=another_user,
            organization=organization,
            department=dept
        )

        service = OrgDataPermissionService(user, organization.id)
        subordinates = service.get_subordinate_users()

        assert another_user in subordinates
        assert user not in subordinates  # 不包含自己
```

### 1.3 资产操作服务测试

```python
# tests/apps/assets/test_operation_services.py

import pytest
from datetime import date, datetime
from apps.assets.services.operation_service import (
    AssetTransferService, AssetReturnService, AssetBorrowService, AssetUseService
)
from apps.assets.models.operations import AssetTransfer, AssetReturn, AssetBorrow, AssetUse
from apps.assets.models import Asset
from apps.organizations.models import Department
from apps.accounts.models import User


@pytest.mark.django_db
class TestAssetTransferService:
    """资产调拨服务测试"""

    def test_create_transfer(self, organization, user, another_user):
        """测试创建调拨单"""
        from_dept = Department.objects.create(
            organization=organization,
            code='TECH',
            name='技术部'
        )

        to_dept = Department.objects.create(
            organization=organization,
            code='ADMIN',
            name='行政部'
        )

        asset = Asset.objects.create(
            organization=organization,
            asset_code='ZC001',
            asset_name='MacBook Pro',
            department=from_dept,
            custodian=user
        )

        service = AssetTransferService(user)
        transfer = service.create_transfer(
            asset_ids=[asset.id],
            to_department_id=to_dept.id,
            to_custodian_id=another_user.id,
            reason='部门间调拨'
        )

        assert transfer.status == 'pending'
        assert transfer.from_department == from_dept
        assert transfer.to_department == to_dept
        assert transfer.items.count() == 1

    def test_approve_transfer(self, organization, user, another_user, admin_user):
        """测试审批调拨单"""
        from_dept = Department.objects.create(
            organization=organization,
            code='TECH',
            name='技术部'
        )

        to_dept = Department.objects.create(
            organization=organization,
            code='ADMIN',
            name='行政部'
        )

        asset = Asset.objects.create(
            organization=organization,
            asset_code='ZC001',
            asset_name='MacBook Pro',
            department=from_dept,
            custodian=user,
            status='in_use'
        )

        service = AssetTransferService(user)
        transfer = service.create_transfer(
            asset_ids=[asset.id],
            to_department_id=to_dept.id,
            to_custodian_id=another_user.id,
            reason='部门间调拨'
        )

        admin_service = AssetTransferService(admin_user)
        approved_transfer = admin_service.approve_transfer(
            transfer.id,
            approved=True,
            comment='同意调拨'
        )

        assert approved_transfer.status == 'approved'
        assert approved_transfer.approver == admin_user

        # 验证资产已更新
        asset.refresh_from_db()
        assert asset.department == to_dept
        assert asset.custodian == another_user

    def test_reject_transfer(self, organization, user, admin_user):
        """测试拒绝调拨单"""
        from_dept = Department.objects.create(
            organization=organization,
            code='TECH',
            name='技术部'
        )

        to_dept = Department.objects.create(
            organization=organization,
            code='ADMIN',
            name='行政部'
        )

        asset = Asset.objects.create(
            organization=organization,
            asset_code='ZC001',
            asset_name='MacBook Pro',
            department=from_dept,
            custodian=user
        )

        service = AssetTransferService(user)
        transfer = service.create_transfer(
            asset_ids=[asset.id],
            to_department_id=to_dept.id,
            to_custodian_id=None,
            reason='部门间调拨'
        )

        admin_service = AssetTransferService(admin_user)
        rejected_transfer = admin_service.approve_transfer(
            transfer.id,
            approved=False,
            comment='调拨理由不充分'
        )

        assert rejected_transfer.status == 'rejected'
        assert rejected_transfer.approver == admin_user


@pytest.mark.django_db
class TestAssetReturnService:
    """资产归还服务测试"""

    def test_create_return(self, organization, user):
        """测试创建归还单"""
        asset = Asset.objects.create(
            organization=organization,
            asset_code='ZC001',
            asset_name='MacBook Pro',
            custodian=user,
            status='in_use'
        )

        service = AssetReturnService()
        service.user = user

        asset_return = service.create_return(
            asset_id=asset.id,
            asset_status='normal',
            remark='资产完好'
        )

        assert asset_return.status == 'pending'
        assert asset_return.asset == asset
        assert asset_return.returner == user
        assert asset_return.asset_status == 'normal'

    def test_generate_return_code(self, organization, user):
        """测试归还单号生成"""
        service = AssetReturnService()
        service.user = user

        code1 = service._generate_code()
        code2 = service._generate_code()

        assert code1.startswith('GH')
        assert code2.startswith('GH')
        assert code1 != code2


@pytest.mark.django_db
class TestAssetBorrowService:
    """资产借用服务测试"""

    def test_create_borrow(self, organization, user):
        """测试创建借用单"""
        asset = Asset.objects.create(
            organization=organization,
            asset_code='ZC001',
            asset_name='投影仪',
            status='idle'
        )

        service = AssetBorrowService()
        service.user = user

        borrow = service.create_borrow(
            asset_id=asset.id,
            expected_return_date=date(2024, 2, 15),
            purpose='项目演示使用'
        )

        assert borrow.status == 'pending'
        assert borrow.asset == asset
        assert borrow.borrower == user
        assert borrow.purpose == '项目演示使用'
        assert borrow.expected_return_date == date(2024, 2, 15)

    def test_generate_borrow_code(self, organization, user):
        """测试借用单号生成"""
        service = AssetBorrowService()
        service.user = user

        code1 = service._generate_code()
        code2 = service._generate_code()

        assert code1.startswith('JY')
        assert code2.startswith('JY')
        assert code1 != code2


@pytest.mark.django_db
class TestAssetUseService:
    """资产领用服务测试"""

    def test_create_use(self, organization, user):
        """测试创建领用单"""
        asset = Asset.objects.create(
            organization=organization,
            asset_code='ZC001',
            asset_name='办公电脑',
            status='idle'
        )

        service = AssetUseService()
        service.user = user

        asset_use = service.create_use(
            asset_id=asset.id,
            purpose='日常工作使用'
        )

        assert asset_use.status == 'pending'
        assert asset_use.asset == asset
        assert asset_use.receiver == user
        assert asset_use.purpose == '日常工作使用'

    def test_generate_use_code(self, organization, user):
        """测试领用单号生成"""
        service = AssetUseService()
        service.user = user

        code1 = service._generate_code()
        code2 = service._generate_code()

        assert code1.startswith('LY')
        assert code2.startswith('LY')
        assert code1 != code2
```

---

## 2. API 集成测试

### 2.1 部门管理 API 测试

```python
# tests/api/test_departments_api.py

import pytest
from django.urls import reverse
from apps.organizations.models import Department


@pytest.mark.django_db
class TestDepartmentsAPI:
    """部门管理 API 测试"""

    def test_list_departments(self, auth_client, organization):
        """测试获取部门列表"""
        Department.objects.create(
            organization=organization,
            code='TECH',
            name='技术部'
        )

        Department.objects.create(
            organization=organization,
            code='ADMIN',
            name='行政部'
        )

        url = reverse('departments-list')
        response = auth_client.get(url)

        assert response.status_code == 200
        assert response.data['count'] == 2

    def test_get_department_tree(self, auth_client, organization):
        """测试获取部门树"""
        root = Department.objects.create(
            organization=organization,
            code='HQ',
            name='总部'
        )

        child = Department.objects.create(
            organization=organization,
            code='TECH',
            name='技术部',
            parent=root
        )

        url = reverse('departments-tree')
        response = auth_client.get(url)

        assert response.status_code == 200
        assert len(response.data) == 1
        assert response.data[0]['name'] == '总部'
        assert len(response.data[0]['children']) == 1
        assert response.data[0]['children'][0]['name'] == '技术部'

    def test_create_department(self, admin_client, organization):
        """测试创建部门"""
        url = reverse('departments-list')
        data = {
            'code': 'TECH',
            'name': '技术部'
        }
        response = admin_client.post(url, data)

        assert response.status_code == 201
        assert response.data['code'] == 'TECH'
        assert response.data['name'] == '技术部'

    def test_update_department_leader(self, admin_client, organization, user):
        """测试设置部门负责人"""
        dept = Department.objects.create(
            organization=organization,
            code='TECH',
            name='技术部'
        )

        url = reverse('departments-set-leader', kwargs={'pk': dept.id})
        data = {'leader_id': user.id}
        response = admin_client.put(url, data)

        assert response.status_code == 200
        assert response.data['leader_id'] == str(user.id)

    def test_get_department_members(self, auth_client, organization, user):
        """测试获取部门成员"""
        dept = Department.objects.create(
            organization=organization,
            code='TECH',
            name='技术部'
        )

        from apps.organizations.models import UserDepartment
        UserDepartment.objects.create(
            user=user,
            organization=organization,
            department=dept,
            is_primary=True
        )

        url = reverse('departments-members', kwargs={'pk': dept.id})
        response = auth_client.get(url)

        assert response.status_code == 200
        assert response.data['total_count'] == 1
        assert response.data['members'][0]['user_id'] == str(user.id)

    def test_get_department_descendants(self, auth_client, organization):
        """测试获取子部门（递归）"""
        root = Department.objects.create(
            organization=organization,
            code='HQ',
            name='总部'
        )

        child1 = Department.objects.create(
            organization=organization,
            code='TECH',
            name='技术部',
            parent=root
        )

        child2 = Department.objects.create(
            organization=organization,
            code='BACKEND',
            name='后端组',
            parent=child1
        )

        url = reverse('departments-descendants', kwargs={'pk': root.id})
        response = auth_client.get(url, {'recursive': True})

        assert response.status_code == 200
        # 应包含所有后代部门
        assert len(response.data) >= 2
```

### 2.2 用户部门关联 API 测试

```python
# tests/api/test_user_departments_api.py

import pytest
from django.urls import reverse
from apps.organizations.models import UserDepartment


@pytest.mark.django_db
class TestUserDepartmentsAPI:
    """用户部门关联 API 测试"""

    def test_get_user_departments(self, auth_client, organization, user):
        """测试获取用户部门关联列表"""
        dept1 = Department.objects.create(
            organization=organization,
            code='TECH',
            name='技术部'
        )

        dept2 = Department.objects.create(
            organization=organization,
            code='ADMIN',
            name='行政部'
        )

        UserDepartment.objects.create(
            user=user,
            organization=organization,
            department=dept1,
            is_primary=True
        )

        UserDepartment.objects.create(
            user=user,
            organization=organization,
            department=dept2,
            is_primary=False
        )

        url = reverse('user-departments-list')
        response = auth_client.get(url)

        assert response.status_code == 200
        assert len(response.data) == 2

    def test_add_user_department(self, admin_client, organization, user):
        """测试添加用户部门关联"""
        dept = Department.objects.create(
            organization=organization,
            code='TECH',
            name='技术部'
        )

        url = reverse('user-departments-list')
        data = {
            'user_id': str(user.id),
            'department_id': str(dept.id),
            'is_primary': True,
            'position': '工程师'
        }
        response = admin_client.post(url, data)

        assert response.status_code == 201
        assert response.data['is_primary'] is True

    def test_set_asset_department(self, auth_client, organization, user):
        """测试设置用户资产归属部门"""
        dept = Department.objects.create(
            organization=organization,
            code='TECH',
            name='技术部'
        )

        url = reverse('users-set-asset-dept', kwargs={'pk': user.id})
        data = {'asset_department_id': str(dept.id)}
        response = auth_client.put(url, data)

        assert response.status_code == 200
        assert response.data['asset_department_name'] == '技术部'
```

### 2.3 资产操作 API 测试

```python
# tests/api/test_asset_operations_api.py

import pytest
from django.urls import reverse
from apps.assets.models.operations import AssetTransfer, AssetReturn


@pytest.mark.django_db
class TestAssetTransfersAPI:
    """资产调拨 API 测试"""

    def test_create_transfer(self, auth_client, organization, user, another_user):
        """测试创建调拨单"""
        from_dept = Department.objects.create(
            organization=organization,
            code='TECH',
            name='技术部'
        )

        to_dept = Department.objects.create(
            organization=organization,
            code='ADMIN',
            name='行政部'
        )

        asset = Asset.objects.create(
            organization=organization,
            asset_code='ZC001',
            asset_name='MacBook Pro',
            department=from_dept,
            custodian=user
        )

        url = reverse('transfers-list')
        data = {
            'asset_ids': [str(asset.id)],
            'to_department_id': str(to_dept.id),
            'to_custodian_id': str(another_user.id),
            'reason': '部门间调拨'
        }
        response = auth_client.post(url, data)

        assert response.status_code == 201
        assert response.data['status'] == 'pending'

    def test_list_transfers(self, auth_client, organization):
        """测试获取调拨单列表"""
        url = reverse('transfers-list')
        response = auth_client.get(url)

        assert response.status_code == 200

    def test_approve_transfer(self, admin_client, organization, user):
        """测试审批调拨单"""
        transfer = AssetTransfer.objects.create(
            organization=organization,
            transfer_code='DB20240115001',
            status='pending',
            applicant=user
        )

        url = reverse('transfers-approve', kwargs={'pk': transfer.id})
        data = {
            'approved': True,
            'comment': '同意调拨'
        }
        response = admin_client.post(url, data)

        assert response.status_code == 200
        assert response.data['status'] == 'approved'

    def test_confirm_transfer_receive(self, auth_client, organization):
        """测试确认接收调拨"""
        transfer = AssetTransfer.objects.create(
            organization=organization,
            transfer_code='DB20240115001',
            status='approved'
        )

        url = reverse('transfers-confirm', kwargs={'pk': transfer.id})
        data = {
            'items': [
                {
                    'item_id': 'test-item-id',
                    'confirmed': True,
                    'remark': '确认接收'
                }
            ]
        }
        response = auth_client.post(url, data)

        assert response.status_code == 200


@pytest.mark.django_db
class TestAssetReturnsAPI:
    """资产归还 API 测试"""

    def test_create_return(self, auth_client, organization, user):
        """测试创建归还单"""
        asset = Asset.objects.create(
            organization=organization,
            asset_code='ZC001',
            asset_name='MacBook Pro',
            custodian=user
        )

        url = reverse('returns-list')
        data = {
            'asset_id': str(asset.id),
            'asset_status': 'normal',
            'remark': '资产完好'
        }
        response = auth_client.post(url, data)

        assert response.status_code == 201
        assert response.data['status'] == 'pending'

    def test_confirm_return(self, admin_client, organization):
        """测试确认归还"""
        asset_return = AssetReturn.objects.create(
            organization=organization,
            return_code='GH20240115001',
            status='pending'
        )

        url = reverse('returns-confirm', kwargs={'pk': asset_return.id})
        data = {'confirmed': True}
        response = admin_client.post(url, data)

        assert response.status_code == 200
        assert response.data['status'] == 'confirmed'
```

### 2.4 数据权限 API 测试

```python
# tests/api/test_data_permissions_api.py

import pytest
from django.urls import reverse


@pytest.mark.django_db
class TestDataPermissionsAPI:
    """数据权限 API 测试"""

    def test_my_permissions(self, auth_client, organization, user):
        """测试获取我的权限范围"""
        dept = Department.objects.create(
            organization=organization,
            code='TECH',
            name='技术部',
            leader=user
        )

        url = reverse('my-permissions')
        response = auth_client.get(url)

        assert response.status_code == 200
        assert 'led_departments' in response.data
        assert 'my_departments' in response.data

    def test_viewable_departments(self, auth_client, organization):
        """测试获取可查看的部门"""
        url = reverse('viewable-departments')
        response = auth_client.get(url)

        assert response.status_code == 200
        assert isinstance(response.data, list)

    def test_subordinate_users(self, auth_client, organization, user, another_user):
        """测试获取下属用户列表"""
        dept = Department.objects.create(
            organization=organization,
            code='TECH',
            name='技术部',
            leader=user
        )

        from apps.organizations.models import UserDepartment
        UserDepartment.objects.create(
            user=another_user,
            organization=organization,
            department=dept
        )

        url = reverse('subordinate-users')
        response = auth_client.get(url)

        assert response.status_code == 200
        # 应包含下属用户
        assert response.data['count'] >= 1

    def test_asset_statistics(self, auth_client, organization):
        """测试获取资产统计"""
        url = reverse('asset-statistics')
        response = auth_client.get(url)

        assert response.status_code == 200
        assert 'total_assets' in response.data
        assert 'department_stats' in response.data
```

---

## 3. 前端组件测试

### 3.1 部门树组件测试

```typescript
// tests/components/organizations/DepartmentTree.spec.ts

import { describe, it, expect, vi } from 'vitest'
import { mount } from '@vue/test-utils'
import DepartmentTree from '@/components/organizations/DepartmentTree.vue'

describe('DepartmentTree.vue', () => {
  it('renders department tree correctly', () => {
    const departments = [
      {
        id: '1',
        name: '总部',
        level: 0,
        children: [
          {
            id: '2',
            name: '技术部',
            level: 1,
            children: []
          }
        ]
      }
    ]

    const wrapper = mount(DepartmentTree, {
      props: { departments }
    })

    expect(wrapper.text()).toContain('总部')
    expect(wrapper.text()).toContain('技术部')
  })

  it('emits select event when department is clicked', async () => {
    const departments = [
      {
        id: '1',
        name: '总部',
        level: 0,
        children: []
      }
    ]

    const wrapper = mount(DepartmentTree, {
      props: { departments }
    })

    await wrapper.find('.department-node').trigger('click')

    expect(wrapper.emitted('select')).toBeTruthy()
    expect(wrapper.emitted('select')![0]).toEqual([{ id: '1', name: '总部' }])
  })

  it('expands/collapses children on toggle', async () => {
    const departments = [
      {
        id: '1',
        name: '总部',
        level: 0,
        children: [
          {
            id: '2',
            name: '技术部',
            level: 1,
            children: []
          }
        ]
      }
    ]

    const wrapper = mount(DepartmentTree, {
      props: { departments }
    })

    // 初始状态应该展开
    expect(wrapper.find('.children-container').exists()).toBe(true)

    // 点击折叠按钮
    await wrapper.find('.toggle-btn').trigger('click')

    // 子节点应该隐藏
    expect(wrapper.find('.children-container').exists()).toBe(false)
  })
})
```

### 3.2 用户选择器组件测试

```typescript
// tests/components/common/UserSelector.spec.ts

import { describe, it, expect, vi } from 'vitest'
import { mount } from '@vue/test-utils'
import UserSelector from '@/components/common/UserSelector.vue'

describe('UserSelector.vue', () => {
  it('renders user list correctly', async () => {
    const users = [
      { id: '1', real_name: '张三', avatar: '' },
      { id: '2', real_name: '李四', avatar: '' }
    ]

    const wrapper = mount(UserSelector)

    await wrapper.setData({ users })

    expect(wrapper.text()).toContain('张三')
    expect(wrapper.text()).toContain('李四')
  })

  it('filters users by keyword', async () => {
    const users = [
      { id: '1', real_name: '张三', avatar: '' },
      { id: '2', real_name: '李四', avatar: '' }
    ]

    const wrapper = mount(UserSelector)
    await wrapper.setData({ users })

    await wrapper.find('input').setValue('张三')

    expect(wrapper.text()).toContain('张三')
    expect(wrapper.text()).not.toContain('李四')
  })

  it('emits select event when user is selected', async () => {
    const users = [
      { id: '1', real_name: '张三', avatar: '' }
    ]

    const wrapper = mount(UserSelector)
    await wrapper.setData({ users })

    await wrapper.find('.user-item').trigger('click')

    expect(wrapper.emitted('select')).toBeTruthy()
    expect(wrapper.emitted('select')![0]).toEqual([{ id: '1', real_name: '张三' }])
  })
})
```

### 3.3 调拨单组件测试

```typescript
// tests/views/assets/AssetTransferForm.spec.ts

import { describe, it, expect, vi } from 'vitest'
import { mount } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'
import AssetTransferForm from '@/views/assets/AssetTransferForm.vue'
import * as api from '@/api/assets'

vi.mock('@/api/assets')

describe('AssetTransferForm.vue', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
  })

  it('validates required fields', async () => {
    const wrapper = mount(AssetTransferForm)

    await wrapper.find('form').trigger('submit')

    expect(wrapper.text()).toContain('请选择调拨资产')
    expect(wrapper.text()).toContain('请选择调入部门')
  })

  it('submits transfer request successfully', async () => {
    vi.spyOn(api, 'createTransfer').mockResolvedValue({
      data: { id: '1', transfer_code: 'DB20240115001' }
    })

    const wrapper = mount(AssetTransferForm)
    await wrapper.setData({
      form: {
        asset_ids: ['asset-1'],
        to_department_id: 'dept-1',
        to_custodian_id: 'user-1',
        reason: '测试调拨'
      }
    })

    await wrapper.find('form').trigger('submit')

    expect(api.createTransfer).toHaveBeenCalledWith({
      asset_ids: ['asset-1'],
      to_department_id: 'dept-1',
      to_custodian_id: 'user-1',
      reason: '测试调拨'
    })
  })

  it('shows error message on submission failure', async () => {
    vi.spyOn(api, 'createTransfer').mockRejectedValue(new Error('网络错误'))

    const wrapper = mount(AssetTransferForm)
    await wrapper.setData({
      form: {
        asset_ids: ['asset-1'],
        to_department_id: 'dept-1',
        to_custodian_id: 'user-1',
        reason: '测试调拨'
      }
    })

    await wrapper.find('form').trigger('submit')

    expect(wrapper.text()).toContain('提交失败')
  })
})
```

---

## 4. 端到端测试

### 4.1 部门管理流程测试

```python
# tests/e2e/test_department_management.py

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import pytest


@pytest.mark.e2e
class TestDepartmentManagementE2E:
    """部门管理端到端测试"""

    @pytest.fixture(autouse=True)
    def setup_driver(self):
        self.driver = webdriver.Chrome()
        self.driver.implicitly_wait(10)
        yield
        self.driver.quit()

    def test_create_department_flow(self, admin_user):
        """测试创建部门完整流程"""
        # 登录
        self.driver.get('http://localhost:8080/login')
        self.driver.find_element(By.ID, 'username').send_keys(admin_user.username)
        self.driver.find_element(By.ID, 'password').send_keys('password')
        self.driver.find_element(By.CSS_SELECTOR, 'button[type="submit"]').click()

        # 等待跳转到首页
        WebDriverWait(self.driver, 10).until(
            EC.url_contains('/dashboard')
        )

        # 导航到部门管理
        self.driver.get('http://localhost:8080/organizations/departments')

        # 点击新建部门按钮
        self.driver.find_element(By.CSS_SELECTOR, '.btn-create-dept').click()

        # 填写部门信息
        self.driver.find_element(By.ID, 'dept-code').send_keys('TECH')
        self.driver.find_element(By.ID, 'dept-name').send_keys('技术部')

        # 选择上级部门
        self.driver.find_element(By.CSS_SELECTOR, '.parent-selector').click()
        self.driver.find_element(By.XPATH, '//div[contains(text(),"总部"]').click()

        # 保存
        self.driver.find_element(By.CSS_SELECTOR, '.btn-save').click()

        # 验证成功提示
        WebDriverWait(self.driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, '.el-message--success'))
        )

        # 验证部门出现在列表中
        dept_list = self.driver.find_element(By.CSS_SELECTOR, '.dept-list')
        assert '技术部' in dept_list.text

    def test_set_department_leader_flow(self, admin_user):
        """测试设置部门负责人流程"""
        # 登录并导航到部门详情页
        self.driver.get('http://localhost:8080/login')
        # ... 登录代码 ...

        self.driver.get('http://localhost:8080/organizations/departments/1')

        # 点击设置负责人按钮
        self.driver.find_element(By.CSS_SELECTOR, '.btn-set-leader').click()

        # 在弹出对话框中选择用户
        self.driver.find_element(By.CSS_SELECTOR, '.user-select').click()
        self.driver.find_element(By.XPATH, '//div[contains(text(),"张三"]').click()

        # 确认
        self.driver.find_element(By.CSS_SELECTOR, '.btn-confirm').click()

        # 验证负责人已更新
        leader_info = self.driver.find_element(By.CSS_SELECTOR, '.dept-leader')
        assert '张三' in leader_info.text
```

### 4.2 资产调拨流程测试

```python
# tests/e2e/test_asset_transfer_flow.py

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import pytest


@pytest.mark.e2e
class TestAssetTransferFlowE2E:
    """资产调拨端到端测试"""

    @pytest.fixture(autouse=True)
    def setup_driver(self):
        self.driver = webdriver.Chrome()
        self.driver.implicitly_wait(10)
        yield
        self.driver.quit()

    def test_transfer_request_approval_flow(self, normal_user, admin_user):
        """测试调拨申请与审批流程"""
        # 1. 普通用户登录并创建调拨申请
        self.driver.get('http://localhost:8080/login')
        self.driver.find_element(By.ID, 'username').send_keys(normal_user.username)
        self.driver.find_element(By.ID, 'password').send_keys('password')
        self.driver.find_element(By.CSS_SELECTOR, 'button[type="submit"]').click()

        # 导航到资产调拨页面
        self.driver.get('http://localhost:8080/assets/transfers/create')

        # 选择要调拨的资产
        self.driver.find_element(By.CSS_SELECTOR, '.asset-selector').click()
        self.driver.find_element(By.XPATH, '//div[contains(text(),"MacBook Pro"]').click()

        # 选择调入部门和保管人
        self.driver.find_element(By.CSS_SELECTOR, '.to-dept-selector').click()
        self.driver.find_element(By.XPATH, '//div[contains(text(),"行政部"]').click()

        # 填写调拨原因
        self.driver.find_element(By.ID, 'transfer-reason').send_keys('项目需要')

        # 提交
        self.driver.find_element(By.CSS_SELECTOR, '.btn-submit').click()

        # 等待提交成功提示
        WebDriverWait(self.driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, '.el-message--success'))
        )

        # 获取生成的调拨单号
        transfer_code = self.driver.find_element(By.CSS_SELECTOR, '.transfer-code').text

        # 2. 管理员登录审批
        self.driver.get('http://localhost:8080/logout')
        self.driver.find_element(By.ID, 'username').send_keys(admin_user.username)
        self.driver.find_element(By.ID, 'password').send_keys('password')
        self.driver.find_element(By.CSS_SELECTOR, 'button[type="submit"]').click()

        # 导航到待审批列表
        self.driver.get('http://localhost:8080/approvals/pending')

        # 找到刚才的调拨申请并点击
        self.driver.find_element(By.XPATH, f'//td[contains(text(),"{transfer_code}"]').click()

        # 点击审批按钮
        self.driver.find_element(By.CSS_SELECTOR, '.btn-approve').click()

        # 填写审批意见
        self.driver.find_element(By.ID, 'approval-comment').send_keys('同意调拨')

        # 确认审批
        self.driver.find_element(By.CSS_SELECTOR, '.btn-confirm-approve').click()

        # 验证审批成功
        WebDriverWait(self.driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, '.el-message--success'))
        )

        # 验证调拨单状态变为已批准
        status = self.driver.find_element(By.CSS_SELECTOR, '.transfer-status').text
        assert status == '已批准'
```

---

## 5. 性能测试

### 5.1 部门树性能测试

```python
# tests/performance/test_department_tree_performance.py

import pytest
import time
from apps.organizations.models import Department


@pytest.mark.django_db
@pytest.mark.performance
class TestDepartmentTreePerformance:
    """部门树性能测试"""

    def test_large_tree_query_performance(self, organization):
        """测试大规模部门树查询性能"""
        # 创建1000个部门的树形结构
        departments = []
        parent = None

        for i in range(1000):
            dept = Department(
                organization=organization,
                code=f'DEPT{i:04d}',
                name=f'部门{i}',
                parent=parent
            )
            departments.append(dept)

            # 每10个部门创建一个子层级
            if i % 10 == 0 and i > 0:
                parent = departments[i - 10]

        Department.objects.bulk_create(departments)

        # 测试查询性能
        start_time = time.time()
        tree = Department.get_full_path_tree(organization)
        end_time = time.time()

        query_time = end_time - start_time

        # 断言查询时间在合理范围内（< 1秒）
        assert query_time < 1.0, f"查询耗时 {query_time:.2f} 秒，超过预期"

    def test_recursive_update_performance(self, organization):
        """测试递归更新路径的性能"""
        # 创建一个深度为5、广度为10的树
        roots = []
        for i in range(10):
            root = Department.objects.create(
                organization=organization,
                code=f'ROOT{i}',
                name=f'根部门{i}'
            )
            roots.append(root)

            # 创建5层子部门
            parent = root
            for j in range(5):
                parent = Department.objects.create(
                    organization=organization,
                    code=f'{root.code}_L{j}',
                    name=f'{root.name}-层级{j}',
                    parent=parent
                )

        # 修改根部门名称，触发递归更新
        start_time = time.time()
        roots[0].name = '修改后的根部门'
        roots[0].save()
        end_time = time.time()

        update_time = end_time - start_time

        # 断言更新时间在合理范围内（< 2秒）
        assert update_time < 2.0, f"更新耗时 {update_time:.2f} 秒，超过预期"
```

### 5.2 权限检查性能测试

```python
# tests/performance/test_permission_performance.py

import pytest
import time
from apps.organizations.services.permission_service import OrgDataPermissionService


@pytest.mark.django_db
@pytest.mark.performance
class TestPermissionPerformance:
    """数据权限性能测试"""

    def test_bulk_asset_permission_check(self, organization, user):
        """测试批量资产权限检查性能"""
        from apps.assets.models import Asset

        # 创建1000个资产
        assets = [
            Asset(
                organization=organization,
                asset_code=f'ZC{i:04d}',
                asset_name=f'资产{i}',
                custodian=user
            )
            for i in range(1000)
        ]
        Asset.objects.bulk_create(assets)

        service = OrgDataPermissionService(user, organization.id)

        # 测试批量权限检查性能
        start_time = time.time()
        queryset = service.get_managed_asset_queryset(Asset)
        count = queryset.count()
        end_time = time.time()

        check_time = end_time - start_time

        assert count == 1000
        assert check_time < 0.5, f"检查耗时 {check_time:.2f} 秒，超过预期"

    def test_get_viewable_users_performance(self, organization):
        """测试获取可查看用户列表的性能"""
        from apps.accounts.models import User
        from apps.organizations.models import UserDepartment, Department

        # 创建100个部门和1000个用户
        departments = [
            Department.objects.create(
                organization=organization,
                code=f'DEPT{i:02d}',
                name=f'部门{i}'
            )
            for i in range(100)
        ]

        users = []
        for i in range(1000):
            user = User.objects.create_user(
                username=f'user{i}',
                password='password'
            )
            UserDepartment.objects.create(
                user=user,
                organization=organization,
                department=departments[i % 100]
            )
            users.append(user)

        # 测试获取可查看用户性能
        leader = User.objects.create_user(
            username='leader',
            password='password'
        )

        departments[0].leader = leader
        departments[0].save()

        service = OrgDataPermissionService(leader, organization.id)

        start_time = time.time()
        subordinate_users = service.get_subordinate_users(departments[0].id)
        end_time = time.time()

        query_time = end_time - start_time

        # 应该能快速获取到约10个下属用户
        assert len(subordinate_users) == 10
        assert query_time < 0.3, f"查询耗时 {query_time:.2f} 秒，超过预期"
```

---

## 6. 测试数据 Fixture

```python
# tests/fixtures/organizations.py

import pytest
from apps.organizations.models import Department, UserDepartment
from apps.accounts.models import User


@pytest.fixture
def department_tree(organization):
    """创建部门树结构"""
    root = Department.objects.create(
        organization=organization,
        code='HQ',
        name='总部'
    )

    tech = Department.objects.create(
        organization=organization,
        code='TECH',
        name='技术部',
        parent=root
    )

    backend = Department.objects.create(
        organization=organization,
        code='BACKEND',
        name='后端组',
        parent=tech
    )

    frontend = Department.objects.create(
        organization=organization,
        code='FRONTEND',
        name='前端组',
        parent=tech
    )

    admin = Department.objects.create(
        organization=organization,
        code='ADMIN',
        name='行政部',
        parent=root
    )

    return {
        'root': root,
        'tech': tech,
        'backend': backend,
        'frontend': frontend,
        'admin': admin
    }


@pytest.fixture
def user_with_multiple_departments(organization, department_tree):
    """创建属于多个部门的用户"""
    user = User.objects.create_user(
        username='multi_dept_user',
        real_name='多部门用户',
        password='password'
    )

    UserDepartment.objects.create(
        user=user,
        organization=organization,
        department=department_tree['tech'],
        is_primary=True,
        is_asset_department=True
    )

    UserDepartment.objects.create(
        user=user,
        organization=organization,
        department=department_tree['admin'],
        is_primary=False,
        is_asset_department=False
    )

    return user


@pytest.fixture
def department_leader(organization, department_tree):
    """创建部门负责人用户"""
    leader = User.objects.create_user(
        username='dept_leader',
        real_name='部门负责人',
        password='password'
    )

    department_tree['tech'].leader = leader
    department_tree['tech'].save()

    UserDepartment.objects.create(
        user=leader,
        organization=organization,
        department=department_tree['tech'],
        is_primary=True,
        is_leader=True
    )

    return leader
```

---

## 7. 测试覆盖率目标

| 模块 | 单元测试覆盖率 | 集成测试覆盖率 |
|------|---------------|---------------|
| Department 模型 | 95%+ | - |
| UserDepartment 模型 | 95%+ | - |
| 数据权限服务 | 90%+ | - |
| 部门管理 API | - | 80%+ |
| 用户部门关联 API | - | 80%+ |
| 资产操作 API | - | 80%+ |
| 前端组件 | 80%+ | - |

---

## 后续任务

1. 实现所有单元测试用例
2. 实现所有集成测试用例
3. 实现端到端测试用例
4. 配置 CI/CD 自动化测试流程
