# Phase 2.1: 企业微信SSO登录 - 测试方案

## 测试概览

| 测试类型 | 覆盖范围 | 优先级 |
|---------|---------|--------|
| 单元测试 | 适配器、服务层 | P0 |
| API测试 | 登录接口 | P0 |
| 集成测试 | OAuth流程 | P1 |
| E2E测试 | 完整登录流程 | P1 |

---

## 1. 后端单元测试

### 1.1 企业微信适配器测试

```python
# apps/sso/tests/test_wework_adapter.py

from django.test import TestCase
from unittest.mock import Mock, patch
from apps.sso.models import WeWorkConfig
from apps.sso.adapters.wework_adapter import WeWorkAdapter


class WeWorkAdapterTest(TestCase):
    """企业微信适配器测试"""

    def setUp(self):
        from apps.organizations.models import Organization

        self.organization = Organization.objects.create(
            name='测试企业',
            code='TEST'
        )

        self.config = WeWorkConfig.objects.create(
            organization=self.organization,
            corp_id='ww123456',
            corp_name='测试企业',
            agent_id=1000001,
            agent_secret='test_secret'
        )

        self.adapter = WeWorkAdapter(self.config)

    @patch('requests.get')
    def test_get_access_token_success(self, mock_get):
        """测试成功获取access_token"""
        mock_response = Mock()
        mock_response.json.return_value = {
            'errcode': 0,
            'errmsg': 'ok',
            'access_token': 'test_token_123',
            'expires_in': 7200
        }
        mock_get.return_value = mock_response

        token = self.adapter.get_access_token()

        self.assertEqual(token, 'test_token_123')
        mock_get.assert_called_once()

    @patch('requests.get')
    def test_get_access_token_failure(self, mock_get):
        """测试获取access_token失败"""
        mock_response = Mock()
        mock_response.json.return_value = {
            'errcode': 40013,
            'errmsg': '不合法的CorpID'
        }
        mock_get.return_value = mock_response

        with self.assertRaises(Exception) as context:
            self.adapter.get_access_token()

        self.assertIn('不合法的CorpID', str(context.exception))

    def test_get_oauth_url(self):
        """测试获取OAuth授权URL"""
        redirect_uri = 'https://example.com/callback'
        state = 'test_state_123'

        url = self.adapter.get_oauth_url(redirect_uri, state)

        self.assertIn('https://open.weixin.qq.com/connect/oauth2/authorize', url)
        self.assertIn('appid=ww123456', url)
        self.assertIn('redirect_uri=', url)
        self.assertIn('state=test_state_123', url)

    def test_get_qr_connect_url(self):
        """测试获取扫码登录URL"""
        redirect_uri = 'https://example.com/callback'

        url = self.adapter.get_qr_connect_url(redirect_uri)

        self.assertIn('https://open.work.weixin.qq.com/wwopen/sso/qrConnect', url)
        self.assertIn('appid=ww123456', url)
        self.assertIn('agentid=1000001', url)

    @patch('requests.get')
    def test_get_user_detail_success(self, mock_get):
        """测试成功获取用户详情"""
        mock_get.side_effect = [
            # get_access_token
            Mock(json=lambda: {
                'errcode': 0,
                'access_token': 'test_token'
            }),
            # get_user_detail
            Mock(json=lambda: {
                'errcode': 0,
                'userid': 'zhangsan',
                'name': '张三',
                'department': [1, 2],
                'position': '工程师',
                'mobile': '13800138000',
                'email': 'zhangsan@example.com',
                'avatar': 'http://example.com/avatar.jpg',
                'status': 1
            })
        ]

        user_info = self.adapter.get_user_detail('zhangsan')

        self.assertEqual(user_info['userid'], 'zhangsan')
        self.assertEqual(user_info['name'], '张三')
        self.assertEqual(user_info['position'], '工程师')
```

### 1.2 SSO服务测试

```python
# apps/sso/tests/test_sso_service.py

from django.test import TestCase
from unittest.mock import Mock, patch
from apps.sso.services.sso_service import WeWorkSSOService
from apps.sso.models import WeWorkConfig, UserMapping
from apps.accounts.models import User


class WeWorkSSOServiceTest(TestCase):
    """企业微信SSO服务测试"""

    def setUp(self):
        from apps.organizations.models import Organization

        self.organization = Organization.objects.create(
            name='测试企业',
            code='TEST'
        )

        self.config = WeWorkConfig.objects.create(
            organization=self.organization,
            corp_id='ww123456',
            corp_name='测试企业',
            agent_id=1000001,
            agent_secret='test_secret',
            auto_create_user=True
        )

    @patch('apps.sso.adapters.wework_adapter.WeWorkAdapter.get_user_info_by_code')
    def test_handle_callback_new_user(self, mock_get_user):
        """测试处理回调-新用户"""
        mock_get_user.return_value = {
            'userid': 'zhangsan',
            'name': '张三',
            'mobile': '13800138000',
            'email': 'zhangsan@example.com',
            'avatar': 'http://example.com/avatar.jpg',
            'main_department': None
        }

        result = WeWorkSSOService.handle_callback('test_code', 'test_state')

        self.assertIn('token', result)
        self.assertIn('user', result)
        self.assertEqual(result['user']['real_name'], '张三')

        # 验证用户已创建
        user = User.objects.get(username='ww_zhangsan')
        self.assertEqual(user.real_name, '张三')

        # 验证映射已创建
        mapping = UserMapping.objects.get(
            platform='wework',
            platform_userid='zhangsan'
        )
        self.assertEqual(mapping.system_user, user)

    @patch('apps.sso.adapters.wework_adapter.WeWorkAdapter.get_user_info_by_code')
    def test_handle_callback_existing_user(self, mock_get_user):
        """测试处理回调-已存在用户"""
        # 创建现有用户
        user = User.objects.create(
            username='existing_user',
            real_name='李四',
            organization=self.organization
        )
        UserMapping.objects.create(
            system_user=user,
            platform='wework',
            platform_userid='lisi',
            platform_name='李四'
        )

        mock_get_user.return_value = {
            'userid': 'lisi',
            'name': '李四',
            'mobile': '13900139000',
            'email': 'lisi@example.com'
        }

        result = WeWorkSSOService.handle_callback('test_code', 'test_state')

        self.assertEqual(result['user']['real_name'], '李四')

        # 验证没有重复创建用户
        self.assertEqual(User.objects.filter(username='ww_lisi').count(), 0)

    def test_handle_callback_invalid_state(self):
        """测试无效state参数"""
        # 没有创建state，应该验证失败

        with self.assertRaises(ValueError) as context:
            WeWorkSSOService.handle_callback('test_code', 'invalid_state')

        self.assertIn('无效的state', str(context.exception))

    def test_get_config_not_enabled(self):
        """测试配置未启用"""
        self.config.is_enabled = False
        self.config.save()

        with self.assertRaises(ValueError) as context:
            WeWorkSSOService.get_config()

        self.assertIn('未启用', str(context.exception))
```

### 1.3 OAuth状态测试

```python
# apps/sso/tests/test_oauth_state.py

from django.test import TestCase
from django.utils import timezone
from datetime import timedelta
from apps.sso.models import OAuthState


class OAuthStateTest(TestCase):
    """OAuth状态测试"""

    def test_create_and_validate_state(self):
        """测试创建和验证state"""
        state = OAuthState.objects.create(
            state='test_state_123',
            platform='wework',
            expires_at=timezone.now() + timedelta(minutes=10)
        )

        self.assertTrue(OAuthState.is_valid('test_state_123', 'wework'))

    def test_expired_state(self):
        """测试过期的state"""
        OAuthState.objects.create(
            state='expired_state',
            platform='wework',
            expires_at=timezone.now() - timedelta(minutes=1)
        )

        self.assertFalse(OAuthState.is_valid('expired_state', 'wework'))

    def test_consume_state(self):
        """测试消费state"""
        OAuthState.objects.create(
            state='consume_test',
            platform='wework',
            session_data={'test_key': 'test_value'},
            expires_at=timezone.now() + timedelta(minutes=10)
        )

        data = OAuthState.consume('consume_test', 'wework')

        self.assertEqual(data, {'test_key': 'test_value'})

        # 验证已被删除
        self.assertFalse(
            OAuthState.objects.filter(state='consume_test').exists()
        )

    def test_consume_nonexistent_state(self):
        """测试消费不存在的state"""
        data = OAuthState.consume('nonexistent', 'wework')
        self.assertIsNone(data)
```

---

## 2. API测试

```python
# apps/sso/tests/test_api.py

from rest_framework.test import APITestCase
from django.urls import reverse
from apps.sso.models import WeWorkConfig
from apps.organizations.models import Organization


class WeWorkLoginAPITest(APITestCase):
    """企业微信登录API测试"""

    def setUp(self):
        self.organization = Organization.objects.create(
            name='测试企业',
            code='TEST'
        )

    def test_get_config_enabled(self):
        """测试获取启用的配置"""
        WeWorkConfig.objects.create(
            organization=self.organization,
            corp_id='ww123456',
            corp_name='测试企业',
            agent_id=1000001,
            agent_secret='test_secret',
            is_enabled=True
        )

        url = reverse('wework_config')
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.data['enabled'])

    def test_get_config_disabled(self):
        """测试获取未启用的配置"""
        url = reverse('wework_config')
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.data['enabled'])

    @patch('apps.sso.services.sso_service.WeWorkSSOService.create_oauth_state')
    def test_get_qr_url(self, mock_create_state):
        """测试获取扫码登录URL"""
        WeWorkConfig.objects.create(
            organization=self.organization,
            corp_id='ww123456',
            corp_name='测试企业',
            agent_id=1000001,
            agent_secret='test_secret',
            is_enabled=True
        )

        mock_create_state.return_value = 'test_state_123'

        url = reverse('wework_qr_url')
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertIn('qr_url', response.data)
        self.assertIn('open.work.weixin.qq.com', response.data['qr_url'])

    def test_get_config_when_disabled(self):
        """测试配置未启用时获取二维码"""
        url = reverse('wework_qr_url')
        response = self.client.get(url)

        self.assertEqual(response.status_code, 400)
        self.assertIn('error', response.data)


class LoginAPITest(APITestCase):
    """登录API测试"""

    def setUp(self):
        from apps.accounts.models import User
        from apps.organizations.models import Organization

        self.organization = Organization.objects.create(
            name='测试企业',
            code='TEST'
        )

        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123',
            real_name='测试用户',
            organization=self.organization
        )

    def test_login_success(self):
        """测试成功登录"""
        url = reverse('login')
        response = self.client.post(url, {
            'username': 'testuser',
            'password': 'testpass123'
        })

        self.assertEqual(response.status_code, 200)
        self.assertIn('token', response.data)
        self.assertIn('user', response.data)

    def test_login_wrong_password(self):
        """测试密码错误"""
        url = reverse('login')
        response = self.client.post(url, {
            'username': 'testuser',
            'password': 'wrongpassword'
        })

        self.assertEqual(response.status_code, 401)

    def test_login_nonexistent_user(self):
        """测试用户不存在"""
        url = reverse('login')
        response = self.client.post(url, {
            'username': 'nonexistent',
            'password': 'testpass123'
        })

        self.assertEqual(response.status_code, 401)

    def test_get_current_user(self):
        """测试获取当前用户信息"""
        from rest_framework_simplejwt.tokens import RefreshToken

        # 获取token
        refresh = RefreshToken.for_user(self.user)
        access_token = refresh.access_token

        url = reverse('me')
        response = self.client.get(
            url,
            HTTP_AUTHORIZATION=f'Bearer {access_token}'
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['username'], 'testuser')
        self.assertEqual(response.data['real_name'], '测试用户')

    def test_get_current_user_without_token(self):
        """测试无token获取用户信息"""
        url = reverse('me')
        response = self.client.get(url)

        self.assertEqual(response.status_code, 401)

    def test_logout(self):
        """测试登出"""
        from rest_framework_simplejwt.tokens import RefreshToken

        refresh = RefreshToken.for_user(self.user)
        access_token = refresh.access_token

        url = reverse('logout')
        response = self.client.post(
            url,
            HTTP_AUTHORIZATION=f'Bearer {access_token}'
        )

        self.assertEqual(response.status_code, 200)
```

---

## 3. E2E测试

```typescript
// e2e/auth/wework-login.spec.ts

import { test, expect } from '@playwright/test'

test.describe('企业微信登录', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('http://localhost:5173/login')
  })

  test('显示企业微信登录选项', async ({ page }) => {
    // 切换到企业微信登录
    await page.click('label:has-text("企业微信")')

    // 验证二维码容器显示
    await expect(page.locator('.wework-qrcode')).toBeVisible()

    // 验证企业微信配置检查
    // 由于是真实环境，需要mock企业微信API
  })

  test('账号密码登录流程', async ({ page }) => {
    // 确保在账号密码登录tab
    await page.click('label:has-text("账号登录")')

    // 输入用户名密码
    await page.fill('input[placeholder*="用户名"]', 'testuser')
    await page.fill('input[type="password"]', 'testpass123')

    // 点击登录按钮
    await page.click('button:has-text("登录")')

    // 验证登录成功
    await page.waitForURL('/')
    await expect(page).toHaveURL(/\/.*/)
  })

  test('登录失败显示错误信息', async ({ page }) => {
    await page.click('label:has-text("账号登录")')

    await page.fill('input[placeholder*="用户名"]', 'wronguser')
    await page.fill('input[type="password"]', 'wrongpass')

    await page.click('button:has-text("登录")')

    // 验证错误提示
    await expect(page.locator('.el-message--error')).toBeVisible()
  })
})

test.describe('认证守卫', () => {
  test('未登录访问受保护页面重定向到登录页', async ({ page }) => {
    // 清除localStorage
    await page.context.clearCookies()
    await page.evaluate(() => localStorage.clear())

    // 尝试访问受保护页面
    await page.goto('http://localhost:5173/assets')

    // 应该重定向到登录页
    await page.waitForURL('/login')
    expect(page.url()).toContain('/login')
  })

  test('已登录用户可以访问受保护页面', async ({ page }) => {
    // 模拟登录状态
    await page.goto('http://localhost:5173/login')
    await page.evaluate(() => {
      localStorage.setItem('token', 'fake_token')
      localStorage.setItem('user', JSON.stringify({
        id: 1,
        username: 'testuser',
        real_name: '测试用户'
      }))
    })

    // 访问受保护页面
    await page.goto('http://localhost:5173/assets')

    // 不应该重定向
    expect(page.url()).not.toContain('/login')
  })
})
```

---

## 4. 前端组件测试

```typescript
// src/views/auth/__tests__/WeWorkQRCode.test.ts

import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount, VueWrapper } from '@vue/test-utils'
import WeWorkQRCode from '../WeWorkQRCode.vue'
import { getWeWorkConfig, getWeWorkQRUrl, handleWeWorkCallback } from '@/api/sso'

vi.mock('@/api/sso')

describe('WeWorkQRCode', () => {
  beforeEach(() => {
    // Mock路由
    vi.mock('vue-router', () => ({
      useRoute: () => ({ query: {} }),
      useRouter: () => ({ push: vi.fn() })
    }))
  })

  it('加载配置中显示loading状态', async () => {
    vi.mocked(getWeWorkConfig).mockImplementation(
      () => new Promise(() => {})
    )

    const wrapper = mount(WeWorkQRCode)
    expect(wrapper.find('.loading-state').exists()).toBe(true)
  })

  it('配置未启用显示错误状态', async () => {
    vi.mocked(getWeWorkConfig).mockResolvedValue({
      enabled: false
    })

    const wrapper = mount(WeWorkQRCode)
    await new Promise(resolve => setTimeout(resolve, 100))

    expect(wrapper.find('.error-state').exists()).toBe(true)
  })

  it('成功加载显示二维码', async () => {
    vi.mocked(getWeWorkConfig).mockResolvedValue({
      enabled: true,
      corp_name: '测试企业'
    })

    vi.mocked(getWeWorkQRUrl).mockResolvedValue({
      qr_url: 'https://open.work.weixin.qq.com/wwopen/sso/qrConnect?test'
    })

    const wrapper = mount(WeWorkQRCode)
    await new Promise(resolve => setTimeout(resolve, 200))

    expect(wrapper.find('.qr-iframe').exists()).toBe(true)
    expect(wrapper.find('.qr-iframe').attributes('src')).toBe(
      'https://open.work.weixin.qq.com/wwopen/sso/qrConnect?test'
    )
  })

  it('处理回调成功', async () => {
    // 模拟URL参数
    vi.stubGlobal('URLSearchParams', () => ({
      get: vi.fn((key) => {
        if (key === 'code') return 'test_code'
        if (key === 'state') return 'test_state'
        return null
      })
    }))

    vi.mocked(getWeWorkConfig).mockResolvedValue({
      enabled: true
    })

    vi.mocked(handleWeWorkCallback).mockResolvedValue({
      token: 'test_token',
      user: {
        id: 1,
        real_name: '张三'
      }
    })

    const wrapper = mount(WeWorkQRCode)
    await new Promise(resolve => setTimeout(resolve, 100))

    // 验证成功结果显示
    expect(wrapper.text()).toContain('登录成功')
    expect(wrapper.text()).toContain('张三')
  })
})
```

---

## 验收标准

### 功能验收

- [ ] 可以获取企业微信登录配置
- [ ] 可以获取企业微信扫码登录URL
- [ ] 可以获取企业微信网页授权URL
- [ ] OAuth回调处理正确
- [ ] 首次登录自动创建用户账号
- [ ] 再次登录使用已有账号
- [ ] 登录后正确获取JWT token
- [ ] 可以绑定/解绑企业微信账号
- [ ] 账号密码登录正常工作
- [ ] Token过期自动刷新或跳转登录

### 安全验收

- [ ] state参数验证（防CSRF）
- [ ] Token自动过期
- [ ] 无效Token返回401
- [ ] 敏感信息不记录在日志中
- [ ] HTTPS传输

### 测试覆盖率

- [ ] 适配器测试覆盖率 > 80%
- [ ] 服务层测试覆盖率 > 80%
- [ ] API测试覆盖率 > 90%
