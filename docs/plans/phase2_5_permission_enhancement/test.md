# Phase 2.5: 权限体系增强 - 测试计划

## 1. 测试概述

### 1.1 测试目标

- 验证字段级权限控制正确性
- 验证数据级权限隔离有效性
- 验证权限继承机制正确工作
- 验证权限审计日志完整性
- 验证权限缓存和性能

### 1.2 测试范围

| 模块 | 测试类型 | 优先级 |
|------|----------|--------|
| 字段权限 | 功能、性能、安全 | 高 |
| 数据权限 | 功能、性能、安全 | 高 |
| 权限继承 | 功能 | 中 |
| 权限审计 | 功能、性能 | 中 |
| 权限缓存 | 性能 | 中 |

---

## 2. 后端单元测试

### 2.1 字段权限测试

**文件**: `apps/permissions/tests/test_field_permission.py`

```python
import pytest
from django.test import TestCase
from django.contrib.contenttypes.models import ContentType
from apps.accounts.models import User, Role
from apps.permissions.models import FieldPermission
from apps.permissions.engine import PermissionEngine


class FieldPermissionTest(TestCase):
    """字段权限测试"""

    def setUp(self):
        self.org = create_test_org()
        self.role = Role.objects.create(
            name='测试角色',
            code='test_role',
            org=self.org
        )
        self.user = User.objects.create_user(
            username='testuser',
            org=self.org
        )
        self.user.roles.add(self.role)

        self.content_type = ContentType.objects.get_by_natural_key(
            'assets', 'asset'
        )

    def test_grant_field_permission(self):
        """测试授予字段权限"""
        permission = FieldPermission.objects.create(
            role=self.role,
            content_type=self.content_type,
            field_name='original_value',
            permission_type='masked',
            mask_rule='range',
            org=self.org
        )

        assert permission.permission_type == 'masked'
        assert permission.field_name == 'original_value'

    def test_get_field_permissions(self):
        """测试获取字段权限"""
        # 创建权限配置
        FieldPermission.objects.create(
            role=self.role,
            content_type=self.content_type,
            field_name='original_value',
            permission_type='masked',
            org=self.org
        )
        FieldPermission.objects.create(
            role=self.role,
            content_type=self.content_type,
            field_name='supplier',
            permission_type='hidden',
            org=self.org
        )

        # 获取权限
        permissions = PermissionEngine.get_field_permissions(
            self.user,
            'assets.Asset',
            'view'
        )

        assert permissions['original_value'] == 'masked'
        assert permissions['supplier'] == 'hidden'

    def test_field_permission_priority(self):
        """测试权限优先级"""
        # 角色权限：只读
        FieldPermission.objects.create(
            role=self.role,
            content_type=self.content_type,
            field_name='original_value',
            permission_type='read',
            priority=1,
            org=self.org
        )

        # 用户权限：脱敏（优先级更高）
        FieldPermission.objects.create(
            user=self.user,
            content_type=self.content_type,
            field_name='original_value',
            permission_type='masked',
            priority=10,
            org=self.org
        )

        permissions = PermissionEngine.get_field_permissions(
            self.user,
            'assets.Asset',
            'view'
        )

        # 应该使用用户权限（优先级更高）
        assert permissions['original_value'] == 'masked'

    def test_field_permission_condition(self):
        """测试权限条件"""
        FieldPermission.objects.create(
            role=self.role,
            content_type=self.content_type,
            field_name='supplier',
            permission_type='hidden',
            condition={
                'type': 'eq',
                'field': 'role_code',
                'value': 'asset_user'
            },
            org=self.org
        )

        permissions = PermissionEngine.get_field_permissions(
            self.user,
            'assets.Asset',
            'view'
        )

        # 角色代码不匹配，不应该应用此权限
        assert 'supplier' not in permissions

    def test_apply_field_permissions_hidden(self):
        """测试应用字段权限 - 隐藏"""
        data = [
            {
                'id': 1,
                'asset_no': 'ZC001',
                'original_value': 10000.00,
                'supplier': '供应商A'
            }
        ]

        # 设置权限
        PermissionEngine._field_permissions_cache = {
            'test_key': {'supplier': 'hidden'}
        }

        result = PermissionEngine.apply_field_permissions(
            data,
            self.user,
            'assets.Asset',
            'view'
        )

        assert 'supplier' not in result[0]
        assert 'original_value' in result[0]

    def test_apply_field_permissions_masked(self):
        """测试应用字段权限 - 脱敏"""
        data = [
            {
                'id': 1,
                'phone': '13812345678',
                'id_card': '110101199001011234',
                'bank_card': '6222021234567890123'
            }
        ]

        # 设置脱敏权限
        PermissionEngine._field_permissions_cache = {
            'test_key': {
                'phone': 'masked',
                'id_card': 'masked',
                'bank_card': 'masked'
            }
        }

        result = PermissionEngine.apply_field_permissions(
            data,
            self.user,
            'assets.Asset',
            'view'
        )

        assert result[0]['phone'] == '138****5678'
        assert result[0]['id_card'] == '110***********1234'
        assert result[0]['bank_card'] == '************0123'

    def test_mask_phone(self):
        """测试手机号脱敏"""
        assert PermissionEngine._mask_phone('13812345678') == '138****5678'
        assert PermissionEngine._mask_phone('1234567') == '****'

    def test_mask_id_card(self):
        """测试身份证脱敏"""
        assert PermissionEngine._mask_id_card('110101199001011234') == '110***********1234'

    def test_mask_bank_card(self):
        """测试银行卡脱敏"""
        assert PermissionEngine._mask_bank_card('6222021234567890123') == '************0123'

    def test_mask_name(self):
        """测试姓名脱敏"""
        assert PermissionEngine._mask_name('张三') == '*三'
        assert PermissionEngine._mask_name('李四光') == '*光'

    def test_clear_cache(self):
        """测试清除缓存"""
        # 设置缓存
        PermissionEngine._field_permissions_cache['test_key'] = {'field': 'read'}

        # 清除用户缓存
        PermissionEngine.clear_cache(self.user.id)

        # 验证缓存已清除
        assert 'test_key' not in PermissionEngine._field_permissions_cache
```

### 2.2 数据权限测试

**文件**: `apps/permissions/tests/test_data_permission.py`

```python
import pytest
from django.test import TestCase
from apps.accounts.models import User, Role
from apps.organizations.models import Department
from apps.permissions.models import DataPermission
from apps.permissions.engine import PermissionEngine
from apps.assets.models import Asset


class DataPermissionTest(TestCase):
    """数据权限测试"""

    def setUp(self):
        self.org = create_test_org()

        # 创建部门树
        self.root_dept = Department.objects.create(
            name='总部',
            org=self.org,
            parent=None
        )
        self.dept1 = Department.objects.create(
            name='部门1',
            org=self.org,
            parent=self.root_dept
        )
        self.dept2 = Department.objects.create(
            name='部门2',
            org=self.org,
            parent=self.root_dept
        )
        self.sub_dept1 = Department.objects.create(
            name='部门1-1',
            org=self.org,
            parent=self.dept1
        )

        # 创建用户
        self.user = User.objects.create_user(
            username='testuser',
            org=self.org,
            department=self.dept1
        )
        self.role = Role.objects.create(
            name='测试角色',
            code='test_role',
            org=self.org
        )
        self.user.roles.add(self.role)

        # 创建测试资产
        Asset.objects.create(
            asset_no='ZC001',
            asset_name='资产1',
            department=self.root_dept,
            org=self.org
        )
        Asset.objects.create(
            asset_no='ZC002',
            asset_name='资产2',
            department=self.dept1,
            org=self.org
        )
        Asset.objects.create(
            asset_no='ZC003',
            asset_name='资产3',
            department=self.dept2,
            org=self.org
        )
        Asset.objects.create(
            asset_no='ZC004',
            asset_name='资产4',
            department=self.sub_dept1,
            org=self.org
        )

        self.content_type = ContentType.objects.get_by_natural_key(
            'assets', 'asset'
        )

    def test_get_data_scope_all(self):
        """测试获取数据范围 - 全部"""
        DataPermission.objects.create(
            role=self.role,
            content_type=self.content_type,
            scope_type='all',
            org=self.org
        )

        scope = PermissionEngine.get_data_scope(self.user, 'assets.Asset')
        assert scope['scope_type'] == 'all'

    def test_get_data_scope_self_dept(self):
        """测试获取数据范围 - 本部门"""
        DataPermission.objects.create(
            role=self.role,
            content_type=self.content_type,
            scope_type='self_dept',
            scope_value={'department_field': 'department'},
            org=self.org
        )

        scope = PermissionEngine.get_data_scope(self.user, 'assets.Asset')
        assert scope['scope_type'] == 'self_dept'

    def test_get_data_scope_self_and_sub(self):
        """测试获取数据范围 - 本部门及下级"""
        DataPermission.objects.create(
            role=self.role,
            content_type=self.content_type,
            scope_type='self_and_sub',
            scope_value={'department_field': 'department'},
            org=self.org
        )

        scope = PermissionEngine.get_data_scope(self.user, 'assets.Asset')
        assert scope['scope_type'] == 'self_and_sub'

    def test_apply_data_scope_all(self):
        """测试应用数据范围 - 全部"""
        DataPermission.objects.create(
            role=self.role,
            content_type=self.content_type,
            scope_type='all',
            org=self.org
        )

        queryset = Asset.objects.filter(org=self.org)
        filtered = PermissionEngine.apply_data_scope(
            queryset,
            self.user,
            'assets.Asset'
        )

        assert filtered.count() == 4

    def test_apply_data_scope_self_dept(self):
        """测试应用数据范围 - 本部门"""
        DataPermission.objects.create(
            role=self.role,
            content_type=self.content_type,
            scope_type='self_dept',
            scope_value={'department_field': 'department'},
            org=self.org
        )

        queryset = Asset.objects.filter(org=self.org)
        filtered = PermissionEngine.apply_data_scope(
            queryset,
            self.user,
            'assets.Asset'
        )

        # 只能看到部门1的资产
        assert filtered.count() == 1
        assert filtered.first().asset_no == 'ZC002'

    def test_apply_data_scope_self_and_sub(self):
        """测试应用数据范围 - 本部门及下级"""
        DataPermission.objects.create(
            role=self.role,
            content_type=self.content_type,
            scope_type='self_and_sub',
            scope_value={'department_field': 'department'},
            org=self.org
        )

        queryset = Asset.objects.filter(org=self.org)
        filtered = PermissionEngine.apply_data_scope(
            queryset,
            self.user,
            'assets.Asset'
        )

        # 可以看到部门1和部门1-1的资产
        assert filtered.count() == 2
        asset_nos = {a.asset_no for a in filtered}
        assert asset_nos == {'ZC002', 'ZC004'}

    def test_apply_data_scope_specified(self):
        """测试应用数据范围 - 指定部门"""
        DataPermission.objects.create(
            role=self.role,
            content_type=self.content_type,
            scope_type='specified',
            scope_value={'department_ids': [self.dept2.id]},
            org=self.org
        )

        queryset = Asset.objects.filter(org=self.org)
        filtered = PermissionEngine.apply_data_scope(
            queryset,
            self.user,
            'assets.Asset'
        )

        # 只能看到部门2的资产
        assert filtered.count() == 1
        assert filtered.first().asset_no == 'ZC003'

    def test_data_permission_expand(self):
        """测试数据权限扩展"""
        # 基础权限：本部门
        base_perm = DataPermission.objects.create(
            role=self.role,
            content_type=self.content_type,
            scope_type='self_dept',
            scope_value={'department_field': 'department'},
            org=self.org
        )

        # 扩展：可访问部门2
        DataPermissionExpand.objects.create(
            base_permission=base_perm,
            expand_type='department',
            expand_value={'department_ids': [self.dept2.id]},
            org=self.org
        )

        scope = PermissionEngine.get_data_scope(self.user, 'assets.Asset')

        assert len(scope['expansions']) == 1
        assert scope['expansions'][0]['type'] == 'department'

    def test_get_accessible_departments(self):
        """测试获取可访问部门"""
        DataPermission.objects.create(
            role=self.role,
            content_type=self.content_type,
            scope_type='self_and_sub',
            scope_value={'department_field': 'department'},
            org=self.org
        )

        dept_ids = DataPermissionService.get_user_accessible_departments(
            self.user,
            'assets.Asset'
        )

        # 应该包含部门1和部门1-1
        assert self.dept1.id in dept_ids
        assert self.sub_dept1.id in dept_ids
        assert self.dept2.id not in dept_ids
```

### 2.3 权限引擎性能测试

**文件**: `apps/permissions/tests/test_performance.py`

```python
import pytest
import time
from django.test import TestCase
from django.test.utils import override_settings
from apps.permissions.engine import PermissionEngine


class PermissionEnginePerformanceTest(TestCase):
    """权限引擎性能测试"""

    def setUp(self):
        self.user = create_test_user()
        self.object_type = 'assets.Asset'

    @override_settings(DEBUG=True)
    def test_permission_cache_performance(self):
        """测试权限缓存性能"""
        # 首次查询（无缓存）
        start = time.time()
        PermissionEngine.get_field_permissions(
            self.user,
            self.object_type,
            'view'
        )
        first_duration = time.time() - start

        # 第二次查询（有缓存）
        start = time.time()
        PermissionEngine.get_field_permissions(
            self.user,
            self.object_type,
            'view'
        )
        cached_duration = time.time() - start

        # 缓存查询应该快得多
        assert cached_duration < first_duration
        assert cached_duration < 0.001  # 小于1ms

    def test_batch_permission_check(self):
        """测试批量权限检查性能"""
        users = [create_test_user(username=f'user{i}') for i in range(100)]

        start = time.time()
        for user in users:
            PermissionEngine.get_data_scope(user, 'assets.Asset')
        duration = time.time() - start

        # 100次检查应该在合理时间内完成
        assert duration < 1.0

    def test_concurrent_permission_check(self):
        """测试并发权限检查"""
        import threading

        results = []
        errors = []

        def check_permission(user_id):
            try:
                user = User.objects.get(id=user_id)
                PermissionEngine.get_field_permissions(
                    user,
                    'assets.Asset',
                    'view'
                )
                results.append(user_id)
            except Exception as e:
                errors.append(str(e))

        threads = []
        for i in range(50):
            user = create_test_user(username=f'concurrent_user{i}')
            t = threading.Thread(target=check_permission, args=(user.id,))
            threads.append(t)
            t.start()

        for t in threads:
            t.join()

        assert len(errors) == 0
        assert len(results) == 50
```

---

## 3. API 集成测试

### 3.1 字段权限 API 测试

**文件**: `apps/permissions/tests/test_api_field.py`

```python
import pytest
from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient
from apps.accounts.models import User, Role


class FieldPermissionAPITest(TestCase):
    """字段权限 API 测试"""

    def setUp(self):
        self.client = APIClient()
        self.admin = create_admin_user()
        self.client.force_authenticate(user=self.admin)

        self.role = Role.objects.create(
            name='测试角色',
            code='test_role',
            org=self.admin.org
        )

    def test_list_field_permissions(self):
        """测试获取字段权限列表"""
        create_field_permission(self.role, 'assets.Asset', 'original_value', 'masked')

        url = reverse('fieldpermission-list')
        response = self.client.get(url)

        assert response.status_code == 200
        assert response.data['count'] >= 1

    def test_create_field_permission(self):
        """测试创建字段权限"""
        url = reverse('fieldpermission-list')
        data = {
            'role_id': self.role.id,
            'object_type': 'assets.Asset',
            'field_name': 'supplier',
            'permission_type': 'hidden',
            'priority': 10
        }

        response = self.client.post(url, data)

        assert response.status_code == 201
        assert response.data['field_name'] == 'supplier'
        assert response.data['permission_type'] == 'hidden'

    def test_create_field_permission_with_mask(self):
        """测试创建脱敏权限"""
        url = reverse('fieldpermission-list')
        data = {
            'role_id': self.role.id,
            'object_type': 'assets.Asset',
            'field_name': 'phone',
            'permission_type': 'masked',
            'mask_rule': 'phone'
        }

        response = self.client.post(url, data)

        assert response.status_code == 201
        assert response.data['mask_rule'] == 'phone'

    def test_batch_create_field_permissions(self):
        """测试批量创建字段权限"""
        url = reverse('fieldpermission-batch-create')
        data = {
            'role_id': self.role.id,
            'object_type': 'assets.Asset',
            'permissions': [
                {'field_name': 'original_value', 'permission_type': 'masked'},
                {'field_name': 'supplier', 'permission_type': 'hidden'},
                {'field_name': 'description', 'permission_type': 'read'}
            ]
        }

        response = self.client.post(url, data)

        assert response.status_code == 201
        assert response.data['created'] == 3

    def test_update_field_permission(self):
        """测试更新字段权限"""
        perm = create_field_permission(self.role, 'assets.Asset', 'field1', 'read')

        url = reverse('fieldpermission-detail', args=[perm.id])
        data = {'permission_type': 'write'}

        response = self.client.patch(url, data)

        assert response.status_code == 200
        assert response.data['permission_type'] == 'write'

    def test_delete_field_permission(self):
        """测试删除字段权限"""
        perm = create_field_permission(self.role, 'assets.Asset', 'field1', 'read')

        url = reverse('fieldpermission-detail', args=[perm.id])
        response = self.client.delete(url)

        assert response.status_code == 204

    def test_get_available_fields(self):
        """测试获取可配置字段"""
        url = reverse('fieldpermission-available-fields')
        response = self.client.get(url, {'object_type': 'assets.Asset'})

        assert response.status_code == 200
        assert 'fields' in response.data
        assert len(response.data['fields']) > 0
```

### 3.2 数据权限 API 测试

**文件**: `apps/permissions/tests/test_api_data.py`

```python
import pytest
from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient


class DataPermissionAPITest(TestCase):
    """数据权限 API 测试"""

    def setUp(self):
        self.client = APIClient()
        self.admin = create_admin_user()
        self.client.force_authenticate(user=self.admin)

        self.role = Role.objects.create(
            name='测试角色',
            code='test_role',
            org=self.admin.org
        )

    def test_list_data_permissions(self):
        """测试获取数据权限列表"""
        create_data_permission(self.role, 'assets.Asset', 'self_dept')

        url = reverse('datapermission-list')
        response = self.client.get(url)

        assert response.status_code == 200

    def test_create_data_permission(self):
        """测试创建数据权限"""
        url = reverse('datapermission-list')
        data = {
            'role_id': self.role.id,
            'object_type': 'assets.Asset',
            'scope_type': 'self_and_sub',
            'scope_value': {'department_field': 'department'},
            'is_inherited': True
        }

        response = self.client.post(url, data)

        assert response.status_code == 201
        assert response.data['scope_type'] == 'self_and_sub'

    def test_add_data_permission_expand(self):
        """测试添加数据权限扩展"""
        perm = create_data_permission(self.role, 'assets.Asset', 'self_dept')

        url = reverse('datapermission-add-expansion', args=[perm.id])
        data = {
            'expand_type': 'department',
            'expand_value': {'department_ids': [1, 2, 3]}
        }

        response = self.client.post(url, data)

        assert response.status_code == 201

    def test_permission_check_api(self):
        """测试权限检查 API"""
        url = reverse('permission-check')
        data = {
            'object_type': 'assets.Asset',
            'action': 'view'
        }

        response = self.client.post(url, data)

        assert response.status_code == 200
        assert 'has_permission' in response.data
        assert 'field_permissions' in response.data
        assert 'data_scope' in response.data

    def test_batch_permission_check(self):
        """测试批量权限检查"""
        url = reverse('permission-check-batch')
        data = {
            'checks': [
                {'object_type': 'assets.Asset', 'action': 'view'},
                {'object_type': 'assets.Asset', 'action': 'edit'},
                {'object_type': 'inventory.InventoryTask', 'action': 'create'}
            ]
        }

        response = self.client.post(url, data)

        assert response.status_code == 200
        assert len(response.data['results']) == 3

    def test_get_accessible_departments(self):
        """测试获取可访问部门"""
        url = reverse('accessible-departments')
        response = self.client.get(url, {'object_type': 'assets.Asset'})

        assert response.status_code == 200
        assert 'department_ids' in response.data
        assert 'departments' in response.data
```

---

## 4. 前端组件测试

### 4.1 组件单元测试

**文件**: `src/components/permissions/__tests__/PermissionTypeTag.spec.ts`

```typescript
import { describe, it, expect } from 'vitest'
import { mount } from '@vue/test-utils'
import PermissionTypeTag from '../PermissionTypeTag.vue'

describe('PermissionTypeTag', () => {
  it('renders read permission correctly', () => {
    const wrapper = mount(PermissionTypeTag, {
      props: { type: 'read' }
    })
    expect(wrapper.text()).toBe('只读')
    expect(wrapper.find('.el-tag--info').exists()).toBe(true)
  })

  it('renders write permission correctly', () => {
    const wrapper = mount(PermissionTypeTag, {
      props: { type: 'write' }
    })
    expect(wrapper.text()).toBe('可写')
    expect(wrapper.find('.el-tag--success').exists()).toBe(true)
  })

  it('renders hidden permission correctly', () => {
    const wrapper = mount(PermissionTypeTag, {
      props: { type: 'hidden' }
    })
    expect(wrapper.text()).toBe('隐藏')
    expect(wrapper.find('.el-tag--danger').exists()).toBe(true)
  })

  it('renders masked permission correctly', () => {
    const wrapper = mount(PermissionTypeTag, {
      props: { type: 'masked' }
    })
    expect(wrapper.text()).toBe('脱敏')
    expect(wrapper.find('.el-tag--warning').exists()).toBe(true)
  })
})
```

### 4.2 Store 测试

**文件**: `src/stores/__tests__/permission.spec.ts`

```typescript
import { describe, it, expect, beforeEach, vi } from 'vitest'
import { createPinia, setActivePinia } from 'pinia'
import { usePermissionStore } from '../permission'
import { permissionCheckApi } from '@/api/permissions'

vi.mock('@/api/permissions')

describe('Permission Store', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
  })

  it('fetches field permissions', async () => {
    const mockData = {
      field_permissions: {
        original_value: 'masked',
        supplier: 'hidden'
      }
    }
    vi.mocked(permissionCheckApi.check).mockResolvedValue({ data: mockData })

    const store = usePermissionStore()
    const result = await store.getFieldPermissions('assets.Asset', 'view')

    expect(result).toEqual(mockData.field_permissions)
    expect(permissionCheckApi.check).toHaveBeenCalledWith({
      object_type: 'assets.Asset',
      action: 'view'
    })
  })

  it('caches field permissions', async () => {
    const mockData = {
      field_permissions: { field1: 'read' }
    }
    vi.mocked(permissionCheckApi.check).mockResolvedValue({ data: mockData })

    const store = usePermissionStore()

    // First call
    await store.getFieldPermissions('assets.Asset', 'view')
    // Second call (should use cache)
    await store.getFieldPermissions('assets.Asset', 'view')

    expect(permissionCheckApi.check).toHaveBeenCalledTimes(1)
  })

  it('checks if field is hidden', async () => {
    const mockData = {
      field_permissions: { supplier: 'hidden' }
    }
    vi.mocked(permissionCheckApi.check).mockResolvedValue({ data: mockData })

    const store = usePermissionStore()
    await store.getFieldPermissions('assets.Asset', 'view')

    expect(store.isFieldHidden('assets.Asset', 'supplier')).toBe(true)
    expect(store.isFieldHidden('assets.Asset', 'asset_no')).toBe(false)
  })

  it('masks phone values', () => {
    const store = usePermissionStore()

    expect(store.getMaskedValue('13812345678', 'phone')).toBe('138****5678')
    expect(store.getMaskedValue('110101199001011234', 'id_card')).toBe('110***********1234')
  })

  it('clears cache', async () => {
    const mockData = {
      field_permissions: { field1: 'read' }
    }
    vi.mocked(permissionCheckApi.check).mockResolvedValue({ data: mockData })

    const store = usePermissionStore()
    await store.getFieldPermissions('assets.Asset', 'view')

    store.clearCache('assets.Asset')

    expect(store.fieldPermissions).toEqual({})
  })
})
```

---

## 5. 端到端测试

### 5.1 字段权限 E2E 测试

**文件**: `tests/e2e/permissions/field-permission.spec.ts`

```typescript
import { test, expect } from '@playwright/test'

test.describe('Field Permission Management', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/system/permissions/field')
    await page.waitForLoadState('networkidle')
  })

  test('displays field permission list', async ({ page }) => {
    await expect(page.locator('text=字段权限管理')).toBeVisible()
    await expect(page.locator('.el-table')).toBeVisible()
  })

  test('creates field permission', async ({ page }) => {
    // Click create button
    await page.click('button:has-text("新增权限")')

    // Fill form
    await page.selectOption('select[name="bind_type"]', 'role')
    await page.selectOption('select[name="role_id"]', { label: '资产用户' })
    await page.selectOption('select[name="object_type"]', { label: '资产' })
    await page.selectOption('select[name="field_name"]', { label: '原值' })
    await page.click('input[value="masked"]')

    // Submit
    await page.click('button:has-text("创建")')

    // Verify success message
    await expect(page.locator('.el-message--success')).toBeVisible()
  })

  test('creates field permissions in batch', async ({ page }) => {
    await page.click('button:has-text("批量配置")')

    // Select role and object type
    await page.selectOption('select[name="role_id"]', { label: '资产用户' })
    await page.selectOption('select[name="object_type"]', { label: '资产' })

    // Set permissions in matrix
    await page.selectOption('select[name="permissions[0].permission_type"]', 'masked')
    await page.selectOption('select[name="permissions[1].permission_type"]', 'hidden')

    // Submit
    await page.click('button:has-text("批量创建")')

    // Verify success
    await expect(page.locator('.el-message--success')).toBeVisible()
  })

  test('edits field permission', async ({ page }) => {
    // Click edit on first row
    await page.click('.el-table .el-button:first-child:has-text("编辑")')

    // Change permission type
    await page.click('input[value="write"]')

    // Submit
    await page.click('button:has-text("保存")')

    // Verify success
    await expect(page.locator('.el-message--success')).toBeVisible()
  })

  test('deletes field permission', async ({ page }) => {
    // Get initial row count
    const initialCount = await page.locator('.el-table tbody tr').count()

    // Click delete on first row
    await page.click('.el-table .el-button:has-text("删除")')

    // Confirm delete
    await page.click('.el-message-box__btns button:has-text("确认")')

    // Verify row was deleted
    const newCount = await page.locator('.el-table tbody tr').count()
    expect(newCount).toBe(initialCount - 1)
  })

  test('filters by permission type', async ({ page }) => {
    await page.selectOption('select[name="permission_type"]', 'masked')
    await page.click('button:has-text("查询")')

    // Wait for table to update
    await page.waitForSelector('.el-table')

    // Verify filter was applied
    const rows = await page.locator('.el-table tbody tr').count()
    if (rows > 0) {
      const firstRowType = await page.locator('.el-table tbody tr:first-child td:nth-child(5)').textContent()
      expect(firstRowType).toContain('脱敏')
    }
  })
})
```

### 5.2 数据权限 E2E 测试

**文件**: `tests/e2e/permissions/data-permission.spec.ts`

```typescript
import { test, expect } from '@playwright/test'

test.describe('Data Permission Management', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/system/permissions/data')
    await page.waitForLoadState('networkidle')
  })

  test('displays data permission list', async ({ page }) => {
    await expect(page.locator('text=数据权限管理')).toBeVisible()
    await expect(page.locator('.el-table')).toBeVisible()
  })

  test('creates data permission with self_dept scope', async ({ page }) => {
    await page.click('button:has-text("新增权限")')

    // Fill form
    await page.selectOption('select[name="role_id"]', { label: '部门管理员' })
    await page.selectOption('select[name="object_type"]', { label: '资产' })
    await page.click('input[value="self_dept"]')

    // Submit
    await page.click('button:has-text("创建")')

    // Verify success
    await expect(page.locator('.el-message--success')).toBeVisible()
  })

  test('creates data permission with specified departments', async ({ page }) => {
    await page.click('button:has-text("新增权限")')

    // Fill form
    await page.selectOption('select[name="role_id"]', { label: '部门管理员' })
    await page.selectOption('select[name="object_type"]', { label: '资产' })
    await page.click('input[value="specified"]')

    // Select departments
    await page.click('.el-tree-select')
    await page.click('.el-tree-node__label:has-text("财务部")')
    await page.click('.el-tree-node__label:has-text("IT部")')
    await page.click('body') // Close dropdown

    // Submit
    await page.click('button:has-text("创建")')

    // Verify success
    await expect(page.locator('.el-message--success')).toBeVisible()
  })

  test('adds data permission expansion', async ({ page }) => {
    // Click expand button on first row
    await page.click('.el-table .el-button:has-text("扩展")')

    // Fill expansion form
    await page.selectOption('select[name="expand_type"]', 'department')

    // Select departments
    await page.click('.el-tree-select')
    await page.click('.el-tree-node__label:has-text("财务部")')
    await page.click('body')

    // Submit
    await page.click('button:has-text("添加")')

    // Verify success
    await expect(page.locator('.el-message--success')).toBeVisible()
  })
})
```

### 5.3 权限审计 E2E 测试

**文件**: `tests/e2e/permissions/audit.spec.ts`

```typescript
import { test, expect } from '@playwright/test'

test.describe('Permission Audit', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/system/permissions/audit')
    await page.waitForLoadState('networkidle')
  })

  test('displays audit log list', async ({ page }) => {
    await expect(page.locator('text=权限审计日志')).toBeVisible()

    // Check stat cards
    await expect(page.locator('.stat-card').first()).toBeVisible()
    await expect(page.locator('.el-table')).toBeVisible()
  })

  test('filters by action type', async ({ page }) => {
    await page.selectOption('select[name="action"]', 'grant')
    await page.click('button:has-text("查询")')

    await page.waitForSelector('.el-table')

    // Verify filter
    const rows = await page.locator('.el-table tbody tr').count()
    if (rows > 0) {
      const firstRowAction = await page.locator('.el-table tbody tr:first-child td:nth-child(3)').textContent()
      expect(firstRowAction).toContain('授权')
    }
  })

  test('filters by date range', async ({ page }) => {
    await page.click('.el-date-editor')
    await page.click('.el-picker-panel__content .el-date-table td.available:first-child')
    await page.click('.el-picker-panel__content .el-date-table td.available:last-child')

    await page.click('button:has-text("查询")')

    await page.waitForSelector('.el-table')
  })

  test('views audit log detail', async ({ page }) => {
    await page.click('.el-table .el-button:has-text("详情"):first-child')

    // Verify detail dialog
    await expect(page.locator('.el-dialog:has-text("日志详情")')).toBeVisible()
    await expect(page.locator('.el-descriptions')).toBeVisible()
  })

  test('exports audit logs', async ({ page }) => {
    const downloadPromise = page.waitForEvent('download')

    await page.click('button:has-text("导出日志")')

    const download = await downloadPromise
    expect(download.suggestedFilename()).toContain('audit-log')
  })
})
```

---

## 6. 安全测试

### 6.1 权限绕过测试

```python
class SecurityTest(TestCase):
    """权限安全测试"""

    def test_cannot_bypass_field_permission(self):
        """测试不能绕过字段权限"""
        user = create_test_user()
        client = APIClient()
        client.force_authenticate(user=user)

        # 设置字段隐藏
        set_field_hidden(user, 'assets.Asset', 'supplier')

        # 尝试直接访问
        response = client.get('/api/assets/assets/1/')

        # 确保敏感字段被过滤
        assert 'supplier' not in response.data

    def test_cannot_bypass_data_permission(self):
        """测试不能绕过数据权限"""
        user_dept = create_department('部门1')
        other_dept = create_department('部门2')
        user = create_user_with_dept(user_dept)

        # 设置数据权限：只能看本部门
        set_data_permission(user, 'self_dept')

        asset1 = create_asset(department=user_dept)
        asset2 = create_asset(department=other_dept)

        client = APIClient()
        client.force_authenticate(user=user)

        response = client.get('/api/assets/assets/')

        # 只能看到本部门资产
        asset_ids = [a['id'] for a in response.data['results']]
        assert asset1.id in asset_ids
        assert asset2.id not in asset_ids

    def test_permission_cache_isolation(self):
        """测试权限缓存隔离"""
        user1 = create_test_user(username='user1')
        user2 = create_test_user(username='user2')

        # 设置不同权限
        set_field_permission(user1, 'assets.Asset', 'field1', 'read')
        set_field_permission(user2, 'assets.Asset', 'field1', 'hidden')

        # 获取权限
        perms1 = PermissionEngine.get_field_permissions(user1, 'assets.Asset')
        perms2 = PermissionEngine.get_field_permissions(user2, 'assets.Asset')

        # 验证权限独立
        assert perms1['field1'] == 'read'
        assert perms2['field1'] == 'hidden'
```

---

## 7. 测试执行计划

### 7.1 单元测试

| 模块 | 测试文件 | 预计覆盖率 |
|------|----------|------------|
| 字段权限模型 | test_field_permission.py | 95% |
| 数据权限模型 | test_data_permission.py | 95% |
| 权限引擎 | test_engine.py | 90% |
| 权限服务 | test_services.py | 90% |

### 7.2 API 集成测试

| 模块 | 测试文件 | 覆盖接口数 |
|------|----------|------------|
| 字段权限 API | test_api_field.py | 8 |
| 数据权限 API | test_api_data.py | 7 |
| 继承 API | test_api_inheritance.py | 6 |
| 审计 API | test_api_audit.py | 5 |

### 7.3 E2E 测试

| 场景 | 测试文件 | 测试用例数 |
|------|----------|------------|
| 字段权限管理 | field-permission.spec.ts | 6 |
| 数据权限管理 | data-permission.spec.ts | 4 |
| 权限审计 | audit.spec.ts | 5 |
| 移动端权限 | mobile-permission.spec.ts | 3 |

---

## 8. 测试通过标准

1. **单元测试**: 所有测试用例通过，代码覆盖率 >= 90%
2. **API 测试**: 所有接口正常响应，权限验证正确
3. **E2E 测试**: 核心业务流程可正常完成
4. **性能测试**: 权限检查响应时间 < 100ms
5. **安全测试**: 无权限绕过漏洞
