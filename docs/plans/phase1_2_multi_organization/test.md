# Phase 1.2: 多组织数据隔离 - 测试验证

## 测试策略

采用**多层测试**策略，确保多组织数据隔离的可靠性：
1. 单元测试：测试中间件、管理器、服务层
2. 集成测试：测试完整的请求-响应循环
3. 安全测试：尝试绕过组织隔离
4. E2E测试：前端组织切换和跨组织调拨流程

---

## 单元测试

### 后端单元测试

```python
# apps/common/tests/test_organization_isolation.py

from django.test import TestCase, override_settings
from apps.common.models import BaseModel
from apps.common.services.organization_service import (
    OrganizationContext,
    set_current_organization,
    get_current_organization,
    clear_current_organization
)
from apps.organizations.models import Organization
from apps.accounts.models import User


class OrganizationContextTest(TestCase):
    """组织上下文测试"""

    def setUp(self):
        self.org1 = Organization.objects.create(name='组织1', code='ORG1')
        self.org2 = Organization.objects.create(name='组织2', code='ORG2')

    def test_set_and_get_organization(self):
        """测试设置和获取组织"""
        set_current_organization(self.org1.id)
        self.assertEqual(get_current_organization(), self.org1.id)

    def test_clear_organization(self):
        """测试清除组织"""
        set_current_organization(self.org1.id)
        self.assertIsNotNone(get_current_organization())

        clear_current_organization()
        self.assertIsNone(get_current_organization())

    def test_context_manager_switch(self):
        """测试上下文管理器切换"""
        set_current_organization(self.org1.id)
        self.assertEqual(get_current_organization(), self.org1.id)

        with OrganizationContext.switch(self.org2.id):
            self.assertEqual(get_current_organization(), self.org2.id)

        # 恢复原组织
        self.assertEqual(get_current_organization(), self.org1.id)

    def test_context_manager_restore_after_none(self):
        """测试从无组织切换后恢复"""
        clear_current_organization()

        with OrganizationContext.switch(self.org1.id):
            self.assertEqual(get_current_organization(), self.org1.id)

        # 恢复到None
        self.assertIsNone(get_current_organization())


class OrganizationManagerTest(TestCase):
    """组织管理器测试"""

    def setUp(self):
        self.org1 = Organization.objects.create(name='组织1', code='ORG1')
        self.org2 = Organization.objects.create(name='组织2', code='ORG2')

        # 创建测试模型
        from apps.assets.models import Asset
        self.asset1_org1 = Asset.objects.create(
            organization=self.org1,
            code='A001',
            name='资产1'
        )
        self.asset2_org1 = Asset.objects.create(
            organization=self.org1,
            code='A002',
            name='资产2'
        )
        self.asset1_org2 = Asset.objects.create(
            organization=self.org2,
            code='A003',
            name='资产3'
        )

    def test_manager_filters_by_organization(self):
        """测试管理器自动过滤组织"""
        set_current_organization(self.org1.id)

        from apps.assets.models import Asset
        assets = Asset.objects.all()

        self.assertEqual(assets.count(), 2)
        self.assertIn(self.asset1_org1, assets)
        self.assertIn(self.asset2_org1, assets)
        self.assertNotIn(self.asset1_org2, assets)

    def test_manager_filters_soft_delete(self):
        """测试管理器过滤软删除"""
        set_current_organization(self.org1.id)

        from apps.assets.models import Asset
        self.asset1_org1.soft_delete()

        assets = Asset.objects.all()
        self.assertEqual(assets.count(), 1)
        self.assertNotIn(self.asset1_org1, assets)

    def test_all_objects_bypass_filter(self):
        """测试all_objects绕过过滤"""
        from apps.assets.models import Asset

        # 使用 all_objects 不受组织过滤影响
        all_assets = Asset.all_objects.filter(organization=self.org1)
        self.assertEqual(all_assets.count(), 2)


class UserOrganizationTest(TestCase):
    """用户多组织测试"""

    def setUp(self):
        self.org1 = Organization.objects.create(name='组织1', code='ORG1')
        self.org2 = Organization.objects.create(name='组织2', code='ORG2')

        self.user = User.objects.create_user(
            username='testuser',
            password='testpass'
        )

    def test_user_join_organization(self):
        """测试用户加入组织"""
        self.user.organizations.add(self.org1, through_defaults={'role': 'member'})

        self.assertTrue(self.user.organizations.filter(id=self.org1.id).exists())
        self.assertEqual(
            self.user.get_org_roles(self.org1.id),
            ['member']
        )

    def test_user_switch_organization(self):
        """测试用户切换组织"""
        self.user.organizations.add(self.org1, self.org2)
        self.user.current_organization = self.org1
        self.user.save()

        self.assertTrue(self.user.switch_organization(self.org2.id))
        self.user.refresh_from_db()
        self.assertEqual(self.user.current_organization, self.org2)

    def test_user_cannot_switch_to_non_member_org(self):
        """测试不能切换到非成员组织"""
        self.user.current_organization = None
        self.user.save()

        self.assertFalse(self.user.switch_organization(self.org1.id))
        self.user.refresh_from_db()
        self.assertIsNone(self.user.current_organization)
```

---

## API集成测试

```python
# apps/common/tests/test_organization_api.py

from django.test import TestCase
from rest_framework.test import APIClient
from apps.organizations.models import Organization
from apps.accounts.models import User


class OrganizationAPITest(TestCase):
    """组织API测试"""

    def setUp(self):
        self.client = APIClient()
        self.org1 = Organization.objects.create(name='组织1', code='ORG1')
        self.org2 = Organization.objects.create(name='组织2', code='ORG2')

        self.user = User.objects.create_user(
            username='testuser',
            password='testpass',
            current_organization=self.org1
        )
        self.user.organizations.add(self.org1, through_defaults={'role': 'admin'})
        self.user.organizations.add(self.org2, through_defaults={'role': 'member'})

        self.client.force_authenticate(user=self.user)

    def test_get_user_organizations(self):
        """测试获取用户组织列表"""
        response = self.client.get('/api/organizations/user/organizations/')

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(len(data['organizations']), 2)

    def test_switch_organization(self):
        """测试切换组织"""
        response = self.client.post('/api/accounts/switch-organization/', {
            'organization_id': self.org2.id
        })

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['current_organization']['id'], self.org2.id)

        # 验证token包含新组织信息
        self.assertIn('token', data)

    def test_switch_to_non_member_org_fails(self):
        """测试切换到非成员组织失败"""
        org3 = Organization.objects.create(name='组织3', code='ORG3')

        response = self.client.post('/api/accounts/switch-organization/', {
            'organization_id': org3.id
        })

        self.assertEqual(response.status_code, 403)

    def test_data_isolation_after_switch(self):
        """测试切换后数据隔离"""
        from apps.assets.models import Asset

        # 在org1创建资产
        asset1 = Asset.objects.create(
            organization=self.org1,
            code='A001',
            name='资产1'
        )

        # 在org2创建资产
        asset2 = Asset.objects.create(
            organization=self.org2,
            code='A002',
            name='资产2'
        )

        # 切换到org1，只能看到asset1
        self.client.post('/api/accounts/switch-organization/', {
            'organization_id': self.org1.id
        })
        response = self.client.get('/api/assets/assets/')
        self.assertEqual(response.status_code, 200)
        assets = response.json()['results']
        self.assertEqual(len(assets), 1)
        self.assertEqual(assets[0]['code'], 'A001')

        # 切换到org2，只能看到asset2
        self.client.post('/api/accounts/switch-organization/', {
            'organization_id': self.org2.id
        })
        response = self.client.get('/api/assets/assets/')
        self.assertEqual(response.status_code, 200)
        assets = response.json()['results']
        self.assertEqual(len(assets), 1)
        self.assertEqual(assets[0]['code'], 'A002')


class CrossOrganizationTransferAPITest(TestCase):
    """跨组织调拨API测试"""

    def setUp(self):
        self.client = APIClient()
        self.org1 = Organization.objects.create(name='组织1', code='ORG1')
        self.org2 = Organization.objects.create(name='组织2', code='ORG2')

        self.user1 = User.objects.create_user(
            username='user1',
            password='testpass',
            current_organization=self.org1
        )
        self.user1.organizations.add(self.org1, through_defaults={'role': 'admin'})

        self.user2 = User.objects.create_user(
            username='user2',
            password='testpass',
            current_organization=self.org2
        )
        self.user2.organizations.add(self.org2, through_defaults={'role': 'admin'})

        # 创建测试资产
        from apps.assets.models import Asset
        self.asset = Asset.objects.create(
            organization=self.org1,
            code='A001',
            name='测试资产',
            status='idle'
        )

    def test_create_cross_org_transfer(self):
        """测试创建跨组织调拨单"""
        self.client.force_authenticate(user=self.user1)

        response = self.client.post('/api/assets/transfers/cross-org/', {
            'to_organization_id': self.org2.id,
            'expected_date': '2024-12-31',
            'reason': '调拨使用',
            'asset_ids': [self.asset.id]
        })

        self.assertEqual(response.status_code, 201)
        data = response.json()
        self.assertEqual(data['from_organization']['id'], self.org1.id)
        self.assertEqual(data['to_organization']['id'], self.org2.id)
        self.assertEqual(data['status'], 'pending_approval')

    def test_approve_transfer(self):
        """测试审批调拨单"""
        # 先创建调拨单
        self.client.force_authenticate(user=self.user1)
        create_response = self.client.post('/api/assets/transfers/cross-org/', {
            'to_organization_id': self.org2.id,
            'expected_date': '2024-12-31',
            'reason': '调拨使用',
            'asset_ids': [self.asset.id]
        })
        transfer_id = create_response.json()['id']

        # 用org2的用户审批
        self.client.force_authenticate(user=self.user2)
        response = self.client.post(
            f'/api/assets/transfers/cross-org/{transfer_id}/approve/',
            {
                'decision': 'approved',
                'to_location_id': 1,
                'to_custodian_id': self.user2.id,
                'comment': '确认接收'
            }
        )

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['status'], 'completed')

        # 验证资产已转移到org2
        from apps.assets.models import Asset
        self.asset.refresh_from_db()
        self.assertEqual(self.asset.organization_id, self.org2.id)

    def test_cannot_approve_own_outgoing_transfer(self):
        """测试不能审批自己发起的调出"""
        self.client.force_authenticate(user=self.user1)

        create_response = self.client.post('/api/assets/transfers/cross-org/', {
            'to_organization_id': self.org2.id,
            'expected_date': '2024-12-31',
            'reason': '调拨使用',
            'asset_ids': [self.asset.id]
        })
        transfer_id = create_response.json()['id']

        # 尝试用org1用户审批（应该失败）
        response = self.client.post(
            f'/api/assets/transfers/cross-org/{transfer_id}/approve/',
            {
                'decision': 'approved',
                'to_location_id': 1,
                'to_custodian_id': self.user1.id
            }
        )

        self.assertEqual(response.status_code, 403)
```

---

## 安全测试

```python
# apps/common/tests/test_security.py

from django.test import TestCase
from rest_framework.test import APIClient
from apps.organizations.models import Organization
from apps.accounts.models import User


class OrganizationIsolationSecurityTest(TestCase):
    """组织隔离安全测试"""

    def setUp(self):
        self.client = APIClient()
        self.org1 = Organization.objects.create(name='组织1', code='ORG1')
        self.org2 = Organization.objects.create(name='组织2', code='ORG2')

        self.user1 = User.objects.create_user(
            username='user1',
            password='testpass',
            current_organization=self.org1
        )
        self.user1.organizations.add(self.org1)

        self.user2 = User.objects.create_user(
            username='user2',
            password='testpass',
            current_organization=self.org2
        )
        self.user2.organizations.add(self.org2)

        # 在org1创建资产
        from apps.assets.models import Asset
        self.asset = Asset.objects.create(
            organization=self.org1,
            code='SECRET_ASSET',
            name='机密资产'
        )

    def test_cannot_access_other_org_data_by_id(self):
        """测试不能通过ID访问其他组织数据"""
        self.client.force_authenticate(user=self.user2)

        # 尝试直接访问org1的资产
        response = self.client.get(f'/api/assets/assets/{self.asset.id}/')

        # 应该返回404而不是200（防止信息泄露）
        self.assertEqual(response.status_code, 404)

    def test_cannot_modify_other_org_data(self):
        """测试不能修改其他组织数据"""
        self.client.force_authenticate(user=self.user2)

        response = self.client.put(f'/api/assets/assets/{self.asset.id}/', {
            'name': '尝试修改'
        })

        self.assertEqual(response.status_code, 404)

    def test_cannot_delete_other_org_data(self):
        """测试不能删除其他组织数据"""
        self.client.force_authenticate(user=self.user2)

        response = self.client.delete(f'/api/assets/assets/{self.asset.id}/')

        self.assertEqual(response.status_code, 404)

        # 验证资产仍然存在
        from apps.assets.models import Asset
        self.assertTrue(Asset.objects.filter(id=self.asset.id).exists())

    def test_header_org_id_respected(self):
        """测试请求头中的组织ID被正确处理"""
        self.client.force_authenticate(user=self.user1)

        # 尝试通过请求头访问org2的数据（应该失败）
        response = self.client.get(
            '/api/assets/assets/',
            HTTP_X_ORGANIZATION_ID=self.org2.id
        )

        # user1不是org2成员，应该返回403
        self.assertIn(response.status_code, [403, 404])

    def test_session_isolation(self):
        """测试会话隔离"""
        # user1登录并设置组织
        self.client.force_authenticate(user=self.user1)
        response1 = self.client.get('/api/assets/assets/')
        assets1 = response1.json()['results']

        # 模拟用户切换（清除认证）
        self.client.force_authenticate(user=None)

        # user2登录
        self.client.force_authenticate(user=self.user2)
        response2 = self.client.get('/api/assets/assets/')
        assets2 = response2.json()['results']

        # 验证看到的数据不同
        self.assertNotEqual(len(assets1), len(assets2))


class JwtTokenSecurityTest(TestCase):
    """JWT Token安全测试"""

    def setUp(self):
        from rest_framework_simplejwt.tokens import RefreshToken
        self.org1 = Organization.objects.create(name='组织1', code='ORG1')
        self.org2 = Organization.objects.create(name='组织2', code='ORG2')

        self.user = User.objects.create_user(
            username='testuser',
            password='testpass',
            current_organization=self.org1
        )
        self.user.organizations.add(self.org1, self.org2)

    def test_token_contains_organization(self):
        """测试Token包含组织信息"""
        from rest_framework_simplejwt.tokens import AccessToken

        token = AccessToken.for_user(self.user)
        payload = token.payload

        self.assertIn('organization_id', payload)
        self.assertEqual(payload['organization_id'], self.org1.id)

    def test_token_with_invalid_org_fails(self):
        """测试伪造组织ID的Token失败"""
        from rest_framework_simplejwt.tokens import AccessToken

        token = AccessToken.for_user(self.user)
        payload = token.payload

        # 修改组织ID
        payload['organization_id'] = 99999
        token.set_payload(payload)

        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
        response = self.client.get('/api/assets/assets/')

        # 应该返回401或403
        self.assertIn(response.status_code, [401, 403])
```

---

## 前端组件测试

```vue
<!-- frontend/src/components/common/__tests__/OrganizationSelector.spec.vue -->

<script setup>
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount } from '@vue/test-utils'
import OrganizationSelector from '../OrganizationSelector.vue'
import { useUserStore } from '@/stores/user'
import { switchOrganization, getUserOrganizations } from '@/api/organization'

vi.mock('@/stores/user')
vi.mock('@/api/organization')

describe('OrganizationSelector.vue', () => {
  let wrapper
  let mockUserStore

  const mockOrganizations = [
    { id: 1, name: '总部', role: 'admin', is_current: true },
    { id: 2, name: '分公司', role: 'member', is_current: false }
  ]

  beforeEach(() => {
    mockUserStore = {
      currentOrganization: { id: 1, name: '总部' }
    }
    useUserStore.mockReturnValue(mockUserStore)
    getUserOrganizations.mockResolvedValue({
      data: { organizations: mockOrganizations }
    })
  })

  it('渲染组织选择器', () => {
    wrapper = mount(OrganizationSelector)
    expect(wrapper.find('.org-selector').exists()).toBe(true)
    expect(wrapper.text()).toContain('总部')
  })

  it('显示组织列表', async () => {
    wrapper = mount(OrganizationSelector)
    await wrapper.vm.loadOrganizations()

    expect(wrapper.vm.organizations).toEqual(mockOrganizations)
  })

  it('切换组织', async () => {
    switchOrganization.mockResolvedValue({
      data: { token: 'new_token', current_organization: { id: 2, name: '分公司' } }
    })

    wrapper = mount(OrganizationSelector)
    await wrapper.vm.handleSwitch(2)

    expect(switchOrganization).toHaveBeenCalledWith(2)
  })

  it('显示当前组织标记', async () => {
    wrapper = mount(OrganizationSelector)
    await wrapper.vm.loadOrganizations()

    const currentOrg = wrapper.vm.organizations.find(o => o.id === 1)
    expect(currentOrg.is_current).toBe(true)
  })
})
</script>
```

---

## E2E测试

```python
# tests/e2e/test_organization_e2e.py

from playwright.sync_api import Page, expect


class TestOrganizationE2E:
    """组织切换E2E测试"""

    def setup_method(self):
        self.page = self.browser.new_page()
        self.page.goto('http://localhost:5173/login')
        # 登录...

    def test_switch_organization(self):
        """测试切换组织流程"""
        # 1. 点击组织选择器
        self.page.click('.org-selector')

        # 2. 选择另一个组织
        self.page.click('text="上海分公司"')

        # 3. 等待页面刷新（组织切换后会刷新）
        self.page.wait_for_load_state('networkidle')

        # 4. 验证当前组织已更新
        selector = self.page.locator('.org-selector')
        expect(selector).to_contain_text('上海分公司')

    def test_data_changes_after_switch(self):
        """测试切换后数据变化"""
        # 在组织A查看资产数量
        self.page.click('.org-selector')
        self.page.click('text="总部"')
        self.page.wait_for_load_state('networkidle')

        asset_count_before = self.page.locator('.asset-item').count()

        # 切换到组织B
        self.page.click('.org-selector')
        self.page.click('text="分公司"')
        self.page.wait_for_load_state('networkidle')

        asset_count_after = self.page.locator('.asset-item').count()

        # 数据应该不同
        expect(asset_count_before).not_to_equal(asset_count_after)

    def test_cross_org_transfer_flow(self):
        """测试跨组织调拨完整流程"""
        # 1. 进入跨组织调拨页面
        self.page.goto('http://localhost:5173/assets/transfer/cross-org')

        # 2. 选择调入组织
        self.page.click('[data-testid="to-organization-select"]')
        self.page.click('text="上海分公司"')

        # 3. 选择资产
        self.page.click('text="添加资产"')
        self.page.click('.asset-picker-item:first-child')
        self.page.click('text="确定"')

        # 4. 填写原因
        self.page.fill('[data-testid="reason-input"]', '设备调配使用')

        # 5. 提交
        self.page.click('text="提交调拨申请"')

        # 6. 等待成功提示
        self.page.wait_for_selector('.el-message--success')

        # 7. 验证跳转到调拨单列表
        expect(self.page).to_have_url('http://localhost:5173/assets/transfers')
```

---

## 验收标准检查清单

### 后端验收

- [ ] `OrganizationManager` 自动过滤当前组织数据
- [ ] `OrganizationMiddleware` 正确提取和设置组织上下文
- [ ] `OrganizationContext` 上下文管理器正常工作
- [ ] 用户可以切换到有权限的组织
- [ ] 用户不能切换到无权限的组织
- [ ] 跨组织调拨单创建和审批正常
- [ ] 调拨审批后资产正确转移到目标组织
- [ ] 软删除数据不在正常查询中出现
- [ ] `all_objects` 管理器可以访问所有数据

### 安全验收

- [ ] 不能通过ID访问其他组织数据
- [ ] 不能修改其他组织数据
- [ ] 不能删除其他组织数据
- [ ] JWT Token包含正确的组织信息
- [ ] 伪造组织ID的Token被拒绝
- [ ] 会话之间数据完全隔离

### 前端验收

- [ ] 组织选择器显示当前组织
- [ ] 组织切换成功后页面刷新
- [ ] 切换后显示正确的组织数据
- [ ] 跨组织调拨表单正常工作
- [ ] 调拨审批页面正常工作
- [ ] 组织切换有成功/失败提示

---

## 运行测试命令

```bash
# 后端单元测试
docker-compose exec backend python manage.py test apps.common.tests

# 运行特定测试
docker-compose exec backend python manage.py test apps.common.tests.test_organization_isolation

# 安全测试
docker-compose exec backend python manage.py test apps.common.tests.test_security

# 前端测试
npm run test

# E2E测试
npm run test:e2e
```

---

## 手动测试步骤

1. **多组织用户登录**
   ```bash
   # 创建属于多个组织的测试用户
   docker-compose exec backend python manage.py shell
   >>> from apps.accounts.models import User
   >>> from apps.organizations.models import Organization
   >>> user = User.objects.get(username='testuser')
   >>> user.organizations.add(org1, org2)
   ```

2. **测试组织切换**
   - 登录系统
   - 点击右上角组织选择器
   - 选择另一个组织
   - 验证页面刷新并显示新组织数据

3. **测试数据隔离**
   - 在组织A创建资产
   - 切换到组织B
   - 验证看不到组织A的资产

4. **测试跨组织调拨**
   - 在组织A创建跨组织调拨单
   - 切换到组织B
   - 在调拨审批列表找到该单据
   - 审批通过
   - 验证资产已转移到组织B
