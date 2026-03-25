# Phase 1.2: Organizations 独立模块 - 测试用例

## 测试概述

本模块测试覆盖组织管理、部门管理、用户-组织/部门关联等核心功能。

---

## 一、单元测试

### 1. Organization 模型测试

```python
# apps/organizations/tests/test_models.py

from django.test import TestCase
from apps.organizations.models import Organization, Department
from apps.accounts.models import User


class OrganizationModelTest(TestCase):
    """Organization 模型测试"""

    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com'
        )

    def test_create_organization(self):
        """测试创建组织"""
        org = Organization.objects.create(
            name='测试公司',
            code='TEST',
            created_by=self.user
        )

        self.assertEqual(org.name, '测试公司')
        self.assertEqual(org.code, 'TEST')
        self.assertEqual(org.level, 0)
        self.assertTrue(org.is_active)

    def test_organization_hierarchy(self):
        """测试组织层级"""
        parent = Organization.objects.create(
            name='集团',
            code='GROUP',
            created_by=self.user
        )

        child = Organization.objects.create(
            name='分公司',
            code='BRANCH',
            parent=parent,
            created_by=self.user
        )

        self.assertEqual(child.level, 1)
        self.assertEqual(child.parent, parent)
        self.assertEqual(parent.full_name, '集团')
        self.assertEqual(child.full_name, '集团 > 分公司')

    def test_organization_path_update(self):
        """测试路径更新"""
        parent = Organization.objects.create(
            name='集团',
            code='GROUP',
            created_by=self.user
        )

        child = Organization.objects.create(
            name='分公司',
            code='BRANCH',
            parent=parent,
            created_by=self.user
        )

        self.assertEqual(child.path, '/GROUP/BRANCH')

    def test_regenerate_invite_code(self):
        """测试邀请码生成"""
        org = Organization.objects.create(
            name='测试公司',
            code='TEST',
            created_by=self.user
        )

        code = org.regenerate_invite_code()

        self.assertIsNotNone(code)
        self.assertEqual(len(code), 8)
        self.assertEqual(org.invite_code, code)

    def test_get_all_children(self):
        """测试获取所有子组织"""
        root = Organization.objects.create(
            name='集团',
            code='GROUP',
            created_by=self.user
        )

        child1 = Organization.objects.create(
            name='分公司A',
            code='BRANCH_A',
            parent=root,
            created_by=self.user
        )

        child2 = Organization.objects.create(
            name='分公司B',
            code='BRANCH_B',
            parent=root,
            created_by=self.user
        )

        grandchild = Organization.objects.create(
            name='子公司',
            code='SUB',
            parent=child1,
            created_by=self.user
        )

        children = root.get_all_children()
        self.assertEqual(len(children), 3)
        self.assertIn(child1, children)
        self.assertIn(child2, children)
        self.assertIn(grandchild, children)


class DepartmentModelTest(TestCase):
    """Department 模型测试"""

    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com'
        )
        self.org = Organization.objects.create(
            name='测试公司',
            code='TEST',
            created_by=self.user
        )

    def test_create_department(self):
        """测试创建部门"""
        dept = Department.objects.create(
            organization=self.org,
            name='技术部',
            code='TECH',
            created_by=self.user
        )

        self.assertEqual(dept.name, '技术部')
        self.assertEqual(dept.level, 0)
        self.assertEqual(dept.full_path, '技术部')
        self.assertEqual(dept.full_path_name, '技术部')

    def test_department_hierarchy(self):
        """测试部门层级"""
        parent = Department.objects.create(
            organization=self.org,
            name='总部',
            code='HQ',
            created_by=self.user
        )

        child = Department.objects.create(
            organization=self.org,
            name='技术部',
            code='TECH',
            parent=parent,
            created_by=self.user
        )

        self.assertEqual(child.level, 1)
        self.assertEqual(child.full_path, '总部/技术部')
        self.assertEqual(child.full_path_name, '总部/技术部')

    def test_department_tree_update(self):
        """测试部门树更新"""
        parent = Department.objects.create(
            organization=self.org,
            name='总部',
            code='HQ',
            created_by=self.user
        )

        child = Department.objects.create(
            organization=self.org,
            name='技术部',
            code='TECH',
            parent=parent,
            created_by=self.user
        )

        grandchild = Department.objects.create(
            organization=self.org,
            name='后端组',
            code='BACKEND',
            parent=child,
            created_by=self.user
        )

        self.assertEqual(grandchild.level, 2)
        self.assertEqual(grandchild.full_path, '总部/技术部/后端组')

    def test_get_descendant_ids(self):
        """测试获取所有后代部门ID"""
        root = Department.objects.create(
            organization=self.org,
            name='总部',
            code='HQ',
            created_by=self.user
        )

        child = Department.objects.create(
            organization=self.org,
            name='技术部',
            code='TECH',
            parent=root,
            created_by=self.user
        )

        grandchild = Department.objects.create(
            organization=self.org,
            name='后端组',
            code='BACKEND',
            parent=child,
            created_by=self.user
        )

        descendants = root.get_descendant_ids()
        self.assertEqual(len(descendants), 3)
        self.assertIn(root.id, descendants)
        self.assertIn(child.id, descendants)
        self.assertIn(grandchild.id, descendants)
```

### 2. Service 层测试

```python
# apps/organizations/tests/test_services.py

from django.test import TestCase
from django.contrib.auth import get_user_model
from apps.organizations.models import Organization, Department, UserOrganization, UserDepartment
from apps.organizations.services import organization_service, department_service

User = get_user_model()


class OrganizationServiceTest(TestCase):
    """OrganizationService 测试"""

    def setUp(self):
        self.creator = User.objects.create_user(
            username='creator',
            email='creator@example.com'
        )

    def test_create_organization(self):
        """测试创建组织"""
        org = organization_service.OrganizationService.create_organization(
            name='新公司',
            code='NEW',
            creator=self.creator
        )

        self.assertEqual(org.name, '新公司')
        self.assertIsNotNone(org.invite_code)

        # 检查创建者是否为管理员
        user_org = UserOrganization.objects.get(
            user=self.creator,
            organization=org
        )
        self.assertEqual(user_org.role, UserOrganization.Role.ADMIN)

    def test_add_member(self):
        """测试添加成员"""
        org = Organization.objects.create(
            name='测试公司',
            code='TEST',
            created_by=self.creator
        )

        member = User.objects.create_user(
            username='member',
            email='member@example.com'
        )

        user_org = organization_service.OrganizationService.add_member(
            organization=org,
            user=member,
            role=UserOrganization.Role.MEMBER
        )

        self.assertEqual(user_org.user, member)
        self.assertEqual(user_org.organization, org)
        self.assertEqual(user_org.role, UserOrganization.Role.MEMBER)

    def test_remove_member(self):
        """测试移除成员"""
        org = Organization.objects.create(
            name='测试公司',
            code='TEST',
            created_by=self.creator
        )

        member = User.objects.create_user(
            username='member',
            email='member@example.com'
        )

        organization_service.OrganizationService.add_member(org, member)
        organization_service.OrganizationService.remove_member(org, member)

        user_org = UserOrganization.objects.get(
            user=member,
            organization=org
        )
        self.assertFalse(user_org.is_active)

    def test_switch_organization(self):
        """测试切换组织"""
        org1 = Organization.objects.create(
            name='公司A',
            code='A',
            created_by=self.creator
        )

        org2 = Organization.objects.create(
            name='公司B',
            code='B',
            created_by=self.creator
        )

        organization_service.OrganizationService.add_member(org1, self.creator)
        organization_service.OrganizationService.add_member(org2, self.creator)

        result = organization_service.OrganizationService.switch_organization(
            user=self.creator,
            organization_id=org2.id
        )

        self.assertTrue(result)

        user_org = UserOrganization.objects.get(
            user=self.creator,
            organization=org2
        )
        self.assertTrue(user_org.is_primary)

    def test_validate_invite_code(self):
        """测试邀请码验证"""
        org = Organization.objects.create(
            name='测试公司',
            code='TEST',
            created_by=self.creator
        )
        org.regenerate_invite_code()

        validated_org = organization_service.OrganizationService.validate_invite_code(
            org.invite_code
        )

        self.assertEqual(validated_org, org)


class DepartmentServiceTest(TestCase):
    """DepartmentService 测试"""

    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com'
        )
        self.org = Organization.objects.create(
            name='测试公司',
            code='TEST',
            created_by=self.user
        )

    def test_create_department(self):
        """测试创建部门"""
        dept = department_service.DepartmentService.create_department(
            organization=self.org,
            name='技术部',
            code='TECH'
        )

        self.assertEqual(dept.name, '技术部')
        self.assertEqual(dept.organization, self.org)

    def test_get_department_tree(self):
        """测试获取部门树"""
        root = Department.objects.create(
            organization=self.org,
            name='总部',
            code='HQ',
            created_by=self.user
        )

        child = Department.objects.create(
            organization=self.org,
            name='技术部',
            code='TECH',
            parent=root,
            created_by=self.user
        )

        tree = department_service.DepartmentService.get_department_tree(self.org)

        self.assertEqual(len(tree), 1)
        self.assertEqual(tree[0]['name'], '总部')
        self.assertEqual(len(tree[0]['children']), 1)
        self.assertEqual(tree[0]['children'][0]['name'], '技术部')

    def test_add_user_to_department(self):
        """测试添加用户到部门"""
        dept = Department.objects.create(
            organization=self.org,
            name='技术部',
            code='TECH',
            created_by=self.user
        )

        member = User.objects.create_user(
            username='member',
            email='member@example.com'
        )

        user_dept = department_service.DepartmentService.add_user_to_department(
            user=member,
            department=dept,
            organization=self.org,
            position='工程师'
        )

        self.assertEqual(user_dept.user, member)
        self.assertEqual(user_dept.department, dept)
        self.assertEqual(user_dept.position, '工程师')

    def test_set_department_leader(self):
        """测试设置部门负责人"""
        dept = Department.objects.create(
            organization=self.org,
            name='技术部',
            code='TECH',
            created_by=self.user
        )

        leader = User.objects.create_user(
            username='leader',
            email='leader@example.com'
        )

        updated_dept = department_service.DepartmentService.set_department_leader(
            department=dept,
            leader=leader
        )

        self.assertEqual(updated_dept.leader, leader)

        user_dept = UserDepartment.objects.get(
            user=leader,
            department=dept
        )
        self.assertTrue(user_dept.is_leader)
```

---

## 二、API 测试

```python
# apps/organizations/tests/test_api.py

from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status
from apps.organizations.models import Organization, Department, UserOrganization

User = get_user_model()


class OrganizationAPITest(TestCase):
    """Organization API 测试"""

    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )

        self.org = Organization.objects.create(
            name='测试公司',
            code='TEST',
            created_by=self.user
        )

        UserOrganization.objects.create(
            user=self.user,
            organization=self.org,
            role=UserOrganization.Role.ADMIN
        )

        self.client.force_authenticate(user=self.user)

    def test_list_organizations(self):
        """测试获取组织列表"""
        response = self.client.get('/api/organizations/')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)

    def test_create_organization(self):
        """测试创建组织"""
        data = {
            'name': '新公司',
            'code': 'NEW',
            'org_type': 'company'
        }

        response = self.client.post('/api/organizations/', data)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['name'], '新公司')

    def test_update_organization(self):
        """测试更新组织"""
        data = {
            'name': '更新后的公司名'
        }

        response = self.client.put(f'/api/organizations/{self.org.id}/', data)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['name'], '更新后的公司名')

    def test_delete_organization(self):
        """测试删除组织（软删除）"""
        response = self.client.delete(f'/api/organizations/{self.org.id}/')

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

        self.org.refresh_from_db()
        self.assertTrue(self.org.is_deleted)

    def test_regenerate_invite_code(self):
        """测试重新生成邀请码"""
        response = self.client.post(f'/api/organizations/{self.org.id}/regenerate-invite-code/')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('invite_code', response.data)


class DepartmentAPITest(TestCase):
    """Department API 测试"""

    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )

        self.org = Organization.objects.create(
            name='测试公司',
            code='TEST',
            created_by=self.user
        )

        UserOrganization.objects.create(
            user=self.user,
            organization=self.org,
            role=UserOrganization.Role.ADMIN
        )

        self.dept = Department.objects.create(
            organization=self.org,
            name='技术部',
            code='TECH',
            created_by=self.user
        )

        self.client.force_authenticate(user=self.user)

    def test_get_department_tree(self):
        """测试获取部门树"""
        response = self.client.get('/api/organizations/departments/tree/')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIsInstance(response.data, list)

    def test_create_department(self):
        """测试创建部门"""
        data = {
            'organization_id': str(self.org.id),
            'name': '市场部',
            'code': 'MARKETING'
        }

        response = self.client.post('/api/organizations/departments/', data)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['name'], '市场部')

    def test_update_department(self):
        """测试更新部门"""
        data = {
            'name': '更新后的部门名'
        }

        response = self.client.put(
            f'/api/organizations/departments/{self.dept.id}/',
            data
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_set_department_leader(self):
        """测试设置部门负责人"""
        leader = User.objects.create_user(
            username='leader',
            email='leader@example.com'
        )

        data = {
            'leader_id': str(leader.id)
        }

        response = self.client.put(
            f'/api/organizations/departments/{self.dept.id}/leader/',
            data
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_get_department_members(self):
        """测试获取部门成员"""
        response = self.client.get(
            f'/api/organizations/departments/{self.dept.id}/members/'
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)


class UserOrganizationAPITest(TestCase):
    """用户-组织关联 API 测试"""

    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )

        self.org = Organization.objects.create(
            name='测试公司',
            code='TEST',
            created_by=self.user
        )
        self.org.regenerate_invite_code()

        self.client.force_authenticate(user=self.user)

    def test_get_user_organizations(self):
        """测试获取用户组织列表"""
        response = self.client.get('/api/organizations/user/organizations/')

        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_join_organization_with_invite_code(self):
        """测试通过邀请码加入组织"""
        data = {
            'invite_code': self.org.invite_code
        }

        response = self.client.post('/api/organizations/user/organizations/', data)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_join_organization_with_invalid_code(self):
        """测试使用无效邀请码"""
        data = {
            'invite_code': 'INVALID'
        }

        response = self.client.post('/api/organizations/user/organizations/', data)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_switch_organization(self):
        """测试切换组织"""
        org2 = Organization.objects.create(
            name='公司B',
            code='B',
            created_by=self.user
        )

        UserOrganization.objects.create(
            user=self.user,
            organization=org2
        )

        data = {
            'organization_id': str(org2.id)
        }

        response = self.client.post('/api/organizations/user/switch-organization/', data)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
```

---

## 三、集成测试

```python
# apps/organizations/tests/test_integration.py

from django.test import TestCase
from django.contrib.auth import get_user_model
from apps.organizations.models import Organization, Department, UserOrganization, UserDepartment
from apps.organizations.services import organization_service, department_service

User = get_user_model()


class OrganizationIntegrationTest(TestCase):
    """组织模块集成测试"""

    def setUp(self):
        self.admin = User.objects.create_user(
            username='admin',
            email='admin@example.com',
            password='admin123'
        )

        self.member1 = User.objects.create_user(
            username='member1',
            email='member1@example.com'
        )

        self.member2 = User.objects.create_user(
            username='member2',
            email='member2@example.com'
        )

    def test_full_organization_lifecycle(self):
        """测试完整的组织生命周期"""

        # 1. 创建组织
        org = organization_service.OrganizationService.create_organization(
            name='测试集团',
            code='GROUP',
            creator=self.admin
        )

        # 2. 创建分公司
        branch = organization_service.OrganizationService.create_organization(
            name='上海分公司',
            code='SH',
            creator=self.admin
        )
        branch.parent = org
        branch.save()

        # 3. 添加成员
        organization_service.OrganizationService.add_member(
            organization=branch,
            user=self.member1,
            role=UserOrganization.Role.MEMBER
        )

        # 4. 创建部门
        root_dept = department_service.DepartmentService.create_department(
            organization=branch,
            name='总部',
            code='HQ'
        )

        tech_dept = department_service.DepartmentService.create_department(
            organization=branch,
            name='技术部',
            code='TECH',
            parent=root_dept
        )

        # 5. 添加用户到部门
        department_service.DepartmentService.add_user_to_department(
            user=self.member1,
            department=tech_dept,
            organization=branch,
            position='工程师'
        )

        # 6. 设置部门负责人
        department_service.DepartmentService.set_department_leader(
            department=tech_dept,
            leader=self.member1
        )

        # 验证
        self.assertEqual(branch.parent, org)
        self.assertEqual(branch.level, 1)

        user_org = UserOrganization.objects.get(
            user=self.member1,
            organization=branch
        )
        self.assertTrue(user_org.is_active)

        user_dept = UserDepartment.objects.get(
            user=self.member1,
            department=tech_dept
        )
        self.assertTrue(user_dept.is_leader)

        self.assertEqual(tech_dept.leader, self.member1)

    def test_multi_department_user(self):
        """测试一人多部门场景"""
        org = Organization.objects.create(
            name='测试公司',
            code='TEST',
            created_by=self.admin
        )

        dept1 = Department.objects.create(
            organization=org,
            name='技术部',
            code='TECH',
            created_by=self.admin
        )

        dept2 = Department.objects.create(
            organization=org,
            name='市场部',
            code='MARKETING',
            created_by=self.admin
        )

        # 用户同时属于两个部门
        department_service.DepartmentService.add_user_to_department(
            user=self.member1,
            department=dept1,
            organization=org,
            is_primary=True
        )

        department_service.DepartmentService.add_user_to_department(
            user=self.member1,
            department=dept2,
            organization=org,
            is_primary=False
        )

        user_depts = UserDepartment.objects.filter(user=self.member1, organization=org)
        self.assertEqual(user_depts.count(), 2)

        # 只有一个主部门
        primary_depts = user_depts.filter(is_primary=True)
        self.assertEqual(primary_depts.count(), 1)
        self.assertEqual(primary_depts.first().department, dept1)
```

---

## 四、前端测试

### 单元测试

```typescript
// tests/unit/OrganizationSelector.spec.ts

import { describe, it, expect, vi } from 'vitest'
import { mount } from '@vue/test-utils'
import { createPinia } from 'pinia'
import OrganizationSelector from '@/components/OrganizationSelector.vue'

describe('OrganizationSelector', () => {
  it('renders organization name', () => {
    const wrapper = mount(OrganizationSelector, {
      global: {
        plugins: [createPinia()]
      },
      props: {
        currentOrg: { name: '测试公司', role: 'admin' }
      }
    })

    expect(wrapper.text()).toContain('测试公司')
  })

  it('emits switch event when clicking organization', async () => {
    const wrapper = mount(OrganizationSelector, {
      global: {
        plugins: [createPinia()]
      }
    })

    // 模拟点击事件
    // ... 具体测试逻辑
  })
})
```

### E2E 测试

```typescript
// tests/e2e/organizations.spec.ts

import { test, expect } from '@playwright/test'

test.describe('Organization Management', () => {
  test.beforeEach(async ({ page }) => {
    // 登录
    await page.goto('/login')
    await page.fill('input[name="username"]', 'testuser')
    await page.fill('input[name="password"]', 'testpass123')
    await page.click('button[type="submit"]')
    await page.waitForURL('/dashboard')
  })

  test('should display organization list', async ({ page }) => {
    await page.goto('/organizations')

    await expect(page.locator('.org-list')).toBeVisible()
    await expect(page.locator('.org-card').first()).toContainText('测试公司')
  })

  test('should create new organization', async ({ page }) => {
    await page.goto('/organizations')

    await page.click('button:has-text("新增组织")')

    await page.fill('input[name="name"]', '新公司')
    await page.fill('input[name="code"]', 'NEW')
    await page.click('button:has-text("提交")')

    await expect(page.locator('.el-message--success')).toBeVisible()
  })

  test('should switch organization', async ({ page }) => {
    await page.goto('/organizations')

    await page.click('.org-selector')
    await page.click('text=上海分公司')

    await expect(page.locator('.el-message--success')).toContainText('组织切换成功')
  })
})

test.describe('Department Management', () => {
  test('should display department tree', async ({ page }) => {
    await page.goto('/organizations/departments')

    await expect(page.locator('.dept-table')).toBeVisible()
    await expect(page.locator('.el-table__row').first()).toContainText('总部')
  })

  test('should create new department', async ({ page }) => {
    await page.goto('/organizations/departments')

    await page.click('button:has-text("新增部门")')

    await page.fill('input[name="name"]', '测试部门')
    await page.fill('input[name="code"]', 'TEST')
    await page.click('button:has-text("提交")')

    await expect(page.locator('.el-message--success')).toBeVisible()
  })
})
```

---

## 测试覆盖率目标

| 模块 | 目标覆盖率 |
|------|-----------|
| 模型 (Models) | > 90% |
| 服务层 (Services) | > 85% |
| API (Views) | > 80% |
| 前端组件 | > 75% |
| E2E | 覆盖核心流程 |
