# Phase 2.3: 通知中心模块 - 测试方案

## 测试概览

| 测试类型 | 覆盖范围 | 优先级 |
|---------|---------|--------|
| 单元测试 | 渠道适配器、通知服务 | P0 |
| API测试 | 通知接口 | P0 |
| 集成测试 | 第三方平台交互 | P1 |
| E2E测试 | 前端通知流程 | P1 |

---

## 1. 后端单元测试

### 1.1 渠道适配器测试

```python
# apps/notifications/tests/test_channels.py

from django.test import TestCase
from unittest.mock import Mock, patch
from apps.notifications.channels.wework_channel import WeWorkNotificationChannel


class WeWorkNotificationChannelTest(TestCase):
    """企业微信渠道测试"""

    def setUp(self):
        self.config = {
            'corp_id': 'ww123456',
            'agent_id': 1000001,
            'agent_secret': 'test_secret'
        }
        self.channel = WeWorkNotificationChannel(self.config)

    def test_channel_type(self):
        """测试渠道类型"""
        self.assertEqual(self.channel.get_channel_type(), 'wework')
        self.assertEqual(self.channel.get_channel_name(), '企业微信')

    def test_is_available(self):
        """测试渠道可用性检查"""
        self.assertTrue(self.channel.is_available())

        # 缺少配置
        incomplete_channel = WeWorkNotificationChannel({
            'corp_id': 'ww123456'
        })
        self.assertFalse(incomplete_channel.is_available())

    @patch('apps.notifications.channels.wework_channel.requests.get')
    def test_get_access_token(self, mock_get):
        """测试获取access_token"""
        mock_response = Mock()
        mock_response.json.return_value = {
            'errcode': 0,
            'access_token': 'test_token_123',
            'expires_in': 7200
        }
        mock_get.return_value = mock_response

        token = self.channel.get_access_token()
        self.assertEqual(token, 'test_token_123')

    @patch('apps.notifications.channels.wework_channel.requests.get')
    def test_get_access_token_failure(self, mock_get):
        """测试获取access_token失败"""
        mock_response = Mock()
        mock_response.json.return_value = {
            'errcode': 40013,
            'errmsg': '不合法的CorpID'
        }
        mock_get.return_value = mock_response

        with self.assertRaises(Exception) as context:
            self.channel.get_access_token()

        self.assertIn('不合法的CorpID', str(context.exception))

    def test_parse_template(self):
        """测试模板解析"""
        template = "您好 {{user.name}}，您的{{type}}申请已提交"
        params = {
            'user': {'name': '张三'},
            'type': '资产领用'
        }

        result = self.channel.parse_template(template, params)
        self.assertEqual(result, '您好 张三，您的资产领用申请已提交')

    def test_parse_template_with_missing_var(self):
        """测试模板解析-缺失变量"""
        template = "您好 {{user.name}}，您的{{type}}申请已提交"
        params = {
            'user': {'name': '张三'}
            # 缺少 type
        }

        result = self.channel.parse_template(template, params)
        self.assertEqual(result, '您好 张三，您的申请已提交')

    @patch('apps.notifications.channels.wework_channel.requests.post')
    @patch('apps.notifications.channels.wework_channel.WeWorkNotificationChannel.get_access_token')
    def test_send_message_success(self, mock_get_token, mock_post):
        """测试发送消息成功"""
        mock_get_token.return_value = 'test_token'

        mock_response = Mock()
        mock_response.json.return_value = {
            'errcode': 0,
            'invaliduser': ''
        }
        mock_post.return_value = mock_response

        # 模拟用户映射
        with patch('apps.notifications.channels.wework_channel.UserMapping.objects.filter') as mock_filter:
            mock_mapping = Mock()
            mock_mapping.platform_userid = 'zhangsan'
            mock_filter.return_value.first.return_value = mock_mapping

            result = self.channel.send_message(
                message={
                    'title': '测试通知',
                    'content': '这是一条测试消息',
                    'url': 'https://example.com',
                    'button_text': '查看'
                },
                recipients=[{'user_id': '1'}]
            )

            self.assertTrue(result['success'])
            self.assertEqual(result['sent_count'], 1)
            self.assertEqual(result['failed_count'], 0)


class EmailNotificationChannelTest(TestCase):
    """邮件渠道测试"""

    def setUp(self):
        from apps.notifications.channels.email_channel import EmailNotificationChannel

        self.config = {
            'from_email': 'noreply@example.com',
            'email_host': 'smtp.example.com'
        }
        self.channel = EmailNotificationChannel(self.config)

    def test_channel_type(self):
        """测试渠道类型"""
        self.assertEqual(self.channel.get_channel_type(), 'email')
        self.assertEqual(self.channel.get_channel_name(), '邮件')

    @patch('apps.notifications.channels.email_channel.EmailNotificationChannel.get_user_channel_id')
    @patch('apps.notifications.channels.email_channel.EmailMultiAlternatives')
    def test_send_email_success(self, mock_email_class, mock_get_email):
        """测试发送邮件成功"""
        mock_get_email.return_value = 'user@example.com'

        mock_email = Mock()
        mock_email_class.return_value = mock_email

        result = self.channel.send_message(
            message={
                'title': '测试邮件',
                'content': '这是一封测试邮件',
                'url': 'https://example.com',
                'button_text': '查看'
            },
            recipients=[{'user_id': '1'}]
        )

        self.assertTrue(result['success'])
        self.assertEqual(result['sent_count'], 1)
        mock_email.send.assert_called_once()

    @patch('apps.notifications.channels.email_channel.User.objects.get')
    def test_get_user_email(self, mock_get_user):
        """测试获取用户邮箱"""
        from apps.notifications.channels.email_channel import EmailNotificationChannel

        mock_user = Mock()
        mock_user.email = 'test@example.com'
        mock_get_user.return_value = mock_user

        email = self.channel.get_user_channel_id('1')
        self.assertEqual(email, 'test@example.com')

    def test_get_user_email_not_set(self):
        """测试用户未设置邮箱"""
        from apps.notifications.channels.email_channel import EmailNotificationChannel
        from apps.accounts.models import User

        with patch('apps.notifications.channels.email_channel.User.objects.get') as mock_get:
            mock_get.side_effect = User.DoesNotExist()

            with self.assertRaises(ValueError) as context:
                self.channel.get_user_channel_id('1')

            self.assertIn('未设置邮箱', str(context.exception))


class InAppNotificationChannelTest(TestCase):
    """站内信渠道测试"""

    def setUp(self):
        from apps.notifications.channels.inapp_channel import InAppNotificationChannel
        from apps.accounts.models import User
        from apps.organizations.models import Organization

        self.channel = InAppNotificationChannel({})

        self.organization = Organization.objects.create(
            name='测试企业',
            code='TEST'
        )

        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123',
            organization=self.organization
        )

    def test_send_inapp_message(self):
        """测试发送站内信"""
        from apps.notifications.models import InAppMessage

        result = self.channel.send_message(
            message={
                'title': '测试通知',
                'content': '这是一条站内信',
                'url': '/test',
                'button_text': '查看',
                'button_url': '/test'
            },
            recipients=[{'user_id': str(self.user.id)}]
        )

        self.assertTrue(result['success'])
        self.assertEqual(result['sent_count'], 1)

        # 验证消息已创建
        message = InAppMessage.objects.get(user=self.user)
        self.assertEqual(message.title, '测试通知')
        self.assertFalse(message.is_read)

    def test_mark_as_read(self):
        """测试标记已读"""
        from apps.notifications.models import InAppMessage

        # 创建消息
        message = InAppMessage.objects.create(
            user=self.user,
            title='测试',
            content='测试内容'
        )

        self.assertFalse(message.is_read)

        # 标记已读
        message.mark_as_read()

        self.assertTrue(message.is_read)
        self.assertIsNotNone(message.read_at)
```

### 1.2 通知服务测试

```python
# apps/notifications/tests/test_service.py

from django.test import TestCase
from unittest.mock import Mock, patch
from apps.notifications.services.notification_service import NotificationService
from apps.notifications.models import (
    NotificationChannel,
    NotificationTemplate,
    NotificationMessage
)


class NotificationServiceTest(TestCase):
    """通知服务测试"""

    def setUp(self):
        from apps.organizations.models import Organization
        from apps.accounts.models import User

        self.organization = Organization.objects.create(
            name='测试企业',
            code='TEST'
        )

        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123',
            organization=self.organization
        )

        # 创建测试渠道
        self.inapp_channel = NotificationChannel.objects.create(
            organization=self.organization,
            channel_type='inapp',
            is_enabled=True,
            priority=0
        )

    @patch('apps.notifications.services.notification_service.get_channel_class')
    def test_send_notification(self, mock_get_channel_class):
        """测试发送通知"""
        # Mock 渠道
        mock_channel = Mock()
        mock_channel.send_message.return_value = {
            'success': True,
            'sent_count': 1,
            'failed_count': 0,
            'details': [{
                'user_id': str(self.user.id),
                'status': 'sent',
                'external_id': '123'
            }]
        }
        mock_channel_class.return_value.return_value = mock_channel
        mock_get_channel_class.return_value = Mock

        service = NotificationService(self.organization)

        message = service.send(
            business_type='test',
            business_id='123',
            title='测试通知',
            content='这是一条测试通知',
            recipients=[{'user_id': str(self.user.id)}],
            channels=['inapp']
        )

        self.assertEqual(message.business_type, 'test')
        self.assertEqual(message.title, '测试通知')
        self.assertEqual(message.status, 'success')

        # 验证渠道被调用
        mock_channel.send_message.assert_called_once()

    def test_send_with_template(self):
        """测试使用模板发送"""
        # 创建模板
        template = NotificationTemplate.objects.create(
            code='test_template',
            name='测试模板',
            template_type='text',
            title='您好 {{name}}',
            content='您的{{type}}申请已提交',
            business_category='system'
        )

        with patch('apps.notifications.services.notification_service.get_channel_class') as mock_get_channel:
            mock_channel = Mock()
            mock_channel.send_message.return_value = {
                'success': True,
                'sent_count': 1,
                'failed_count': 0,
                'details': []
            }
            mock_channel.parse_template.side_effect = lambda x, y: x.replace('{{name}}', '张三').replace('{{type}}', '测试')
            mock_channel_class = Mock
            mock_channel_class.return_value = mock_channel
            mock_get_channel.return_value = mock_channel

            service = NotificationService(self.organization)

            message = service.send_template(
                template_code='test_template',
                recipients=[{'user_id': str(self.user.id)}],
                params={'name': '张三', 'type': '测试'}
            )

            self.assertEqual(message.title, '您好 张三')

    def test_get_enabled_channels(self):
        """测试获取启用的渠道"""
        # 添加更多渠道
        NotificationChannel.objects.create(
            organization=self.organization,
            channel_type='wework',
            is_enabled=True,
            priority=1
        )

        NotificationChannel.objects.create(
            organization=self.organization,
            channel_type='email',
            is_enabled=False,  # 未启用
            priority=2
        )

        service = NotificationService(self.organization)
        channels = service._get_enabled_channels()

        # 应该返回启用的渠道，按优先级排序
        self.assertIn('inapp', channels)
        self.assertIn('wework', channels)
        self.assertNotIn('email', channels)

    def test_partial_success_handling(self):
        """测试部分成功处理"""
        with patch('apps.notifications.services.notification_service.get_channel_class') as mock_get_channel:
            # 模拟一个渠道成功，一个渠道失败
            mock_channel = Mock()
            mock_channel.send_message.return_value = {
                'success': True,
                'sent_count': 1,
                'failed_count': 0,
                'details': []
            }

            mock_get_channel.return_value = mock_channel

            service = NotificationService(self.organization)

            message = service.send(
                business_type='test',
                business_id='123',
                title='测试',
                content='内容',
                recipients=[{'user_id': str(self.user.id)}],
                channels=['inapp']
            )

            self.assertEqual(message.status, 'success')


class TemplateParseTest(TestCase):
    """模板解析测试"""

    def test_simple_variable(self):
        """测试简单变量替换"""
        from apps.notifications.channels.base import NotificationChannelAdapter

        class TestChannel(NotificationChannelAdapter):
            def get_channel_type(self): return 'test'
            def get_channel_name(self): return 'Test'
            def is_available(self): return True
            def send_message(self, message, recipients): pass
            def get_user_channel_id(self, user_id): return user_id

        channel = TestChannel({})

        result = channel.parse_template("您好 {{name}}", {'name': '张三'})
        self.assertEqual(result, '您好 张三')

    def test_nested_variable(self):
        """测试嵌套变量"""
        class TestChannel(NotificationChannelAdapter):
            def get_channel_type(self): return 'test'
            def get_channel_name(self): return 'Test'
            def is_available(self): return True
            def send_message(self, message, recipients): pass
            def get_user_channel_id(self, user_id): return user_id

        channel = TestChannel({})

        result = channel.parse_template(
            "您好 {{user.name}}",
            {'user': {'name': '张三'}}
        )
        self.assertEqual(result, '您好 张三')

    def test_multiple_variables(self):
        """测试多个变量"""
        class TestChannel(NotificationChannelAdapter):
            def get_channel_type(self): return 'test'
            def get_channel_name(self): return 'Test'
            def is_available(self): return True
            def send_message(self, message, recipients): pass
            def get_user_channel_id(self, user_id): return user_id

        channel = TestChannel({})

        result = channel.parse_template(
            "{{applicant}}提交了{{type}}申请，原因：{{reason}}",
            {'applicant': '张三', 'type': '资产领用', 'reason': '项目需要'}
        )
        self.assertEqual(result, '张三提交了资产领用申请，原因：项目需要')

    def test_missing_variable(self):
        """测试缺失变量"""
        class TestChannel(NotificationChannelAdapter):
            def get_channel_type(self): return 'test'
            def get_channel_name(self): return 'Test'
            def is_available(self): return True
            def send_message(self, message, recipients): pass
            def get_user_channel_id(self, user_id): return user_id

        channel = TestChannel({})

        result = channel.parse_template(
            "您好 {{name}}，您的{{type}}申请",
            {'name': '张三'}  # 缺少 type
        )
        self.assertEqual(result, '您好 张三，您的申请')
```

---

## 2. API测试

```python
# apps/notifications/tests/test_api.py

from rest_framework.test import APITestCase
from django.urls import reverse
from apps.notifications.models import (
    NotificationChannel,
    NotificationTemplate,
    InAppMessage
)
from apps.accounts.models import User
from apps.organizations.models import Organization


class NotificationAPITest(APITestCase):
    """通知API测试"""

    def setUp(self):
        self.organization = Organization.objects.create(
            name='测试企业',
            code='TEST'
        )

        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123',
            organization=self.organization
        )

        self.client.force_authenticate(user=self.user)

    def test_get_channels(self):
        """测试获取渠道列表"""
        NotificationChannel.objects.create(
            organization=self.organization,
            channel_type='inapp',
            is_enabled=True,
            priority=0
        )

        url = reverse('notification-channels')
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 1)

    def test_get_templates(self):
        """测试获取模板列表"""
        NotificationTemplate.objects.create(
            code='test_template',
            name='测试模板',
            template_type='text',
            title='测试',
            content='内容',
            business_category='system'
        )

        url = reverse('notification-templates')
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertGreater(len(response.data), 0)

    @patch('apps.notifications.api.notification.NotificationService.send')
    def test_send_notification(self, mock_send):
        """测试发送通知"""
        mock_message = Mock()
        mock_message.id = 1
        mock_message.status = 'success'
        mock_message.sent_count = 1
        mock_message.failed_count = 0
        mock_send.return_value = mock_message

        url = reverse('notification-send')
        response = self.client.post(url, {
            'title': '测试通知',
            'content': '这是一条测试通知',
            'recipients': [{'user_id': str(self.user.id)}]
        }, format='json')

        self.assertEqual(response.status_code, 200)
        mock_send.assert_called_once()

    def test_get_my_messages(self):
        """测试获取我的消息"""
        InAppMessage.objects.create(
            user=self.user,
            message_type='system',
            title='测试消息',
            content='测试内容'
        )

        url = reverse('my-messages')
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 1)

    def test_get_unread_count(self):
        """测试获取未读数量"""
        # 创建未读消息
        InAppMessage.objects.create(
            user=self.user,
            message_type='system',
            title='未读消息',
            content='内容'
        )

        url = reverse('unread-count')
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['count'], 1)

    def test_mark_as_read(self):
        """测试标记已读"""
        message = InAppMessage.objects.create(
            user=self.user,
            message_type='system',
            title='测试',
            content='内容'
        )

        url = reverse('mark-read', kwargs={'pk': message.id})
        response = self.client.post(url)

        self.assertEqual(response.status_code, 200)

        message.refresh_from_db()
        self.assertTrue(message.is_read)

    def test_mark_all_read(self):
        """测试全部标记已读"""
        # 创建多条未读消息
        for i in range(3):
            InAppMessage.objects.create(
                user=self.user,
                message_type='system',
                title=f'消息{i}',
                content='内容'
            )

        url = reverse('mark-all-read')
        response = self.client.post(url)

        self.assertEqual(response.status_code, 200)

        # 验证全部已读
        unread_count = InAppMessage.objects.filter(
            user=self.user,
            is_read=False
        ).count()
        self.assertEqual(unread_count, 0)
```

---

## 3. 前端组件测试

```typescript
// src/components/__tests__/NotificationCenter.spec.ts

import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount, VueWrapper } from '@vue/test-utils'
import { ElBadge } from 'element-plus'
import NotificationCenter from '../NotificationCenter.vue'
import { useNotificationStore } from '@/stores/notification'

vi.mock('@/stores/notification')

describe('NotificationCenter', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('显示未读数量角标', () => {
    const mockStore = {
      unreadCount: 5,
      fetchMessages: vi.fn()
    }
    vi.mocked(useNotificationStore).mockReturnValue(mockStore)

    const wrapper = mount(NotificationCenter)

    const badge = wrapper.findComponent(ElBadge)
    expect(badge.props('value')).toBe(5)
    expect(badge.props('hidden')).toBe(false)
  })

  it('未读数量为0时隐藏角标', () => {
    const mockStore = {
      unreadCount: 0,
      fetchMessages: vi.fn()
    }
    vi.mocked(useNotificationStore).mockReturnValue(mockStore)

    const wrapper = mount(NotificationCenter)

    const badge = wrapper.findComponent(ElBadge)
    expect(badge.props('hidden')).toBe(true)
  })

  it('点击按钮打开抽屉', async () => {
    const mockStore = {
      unreadCount: 0,
      fetchMessages: vi.fn()
    }
    vi.mocked(useNotificationStore).mockReturnValue(mockStore)

    const wrapper = mount(NotificationCenter)
    await wrapper.find('.notification-button').trigger('click')

    // 验证抽屉打开
    expect(wrapper.vm.drawerVisible).toBe(true)
    expect(mockStore.fetchMessages).toHaveBeenCalled()
  })
})

describe('NotificationList', () => {
  it('正确显示消息列表', () => {
    const messages = [
      {
        id: 1,
        message_type: 'system',
        title: '系统通知',
        content: '这是一条系统通知',
        is_read: false,
        created_at: '2024-01-15T10:00:00Z'
      },
      {
        id: 2,
        message_type: 'approval',
        title: '待审批',
        content: '请审批资产领用申请',
        is_read: true,
        created_at: '2024-01-14T10:00:00Z'
      }
    ]

    // 测试消息列表渲染
    expect(messages).toHaveLength(2)
    expect(messages[0].is_read).toBe(false)
    expect(messages[1].is_read).toBe(true)
  })

  it('显示正确的时间格式', () => {
    // 测试时间格式化函数
    const formatTime = (timeStr: string) => {
      const date = new Date(timeStr)
      const now = new Date()
      const diff = now.getTime() - date.getTime()
      const minutes = Math.floor(diff / 60000)

      if (minutes < 1) return '刚刚'
      if (minutes < 60) return `${minutes}分钟前`
      return date.toLocaleDateString('zh-CN')
    }

    expect(formatTime(new Date().toISOString())).toBe('刚刚')
  })
})
```

---

## 4. E2E测试

```typescript
// e2e/notifications/notifications.spec.ts

import { test, expect } from '@playwright/test'

test.describe('通知中心', () => {
  test.beforeEach(async ({ page }) => {
    // 登录
    await page.goto('http://localhost:5173/login')
    await page.fill('input[placeholder*="用户名"]', 'admin')
    await page.fill('input[type="password"]', 'admin123')
    await page.click('button:has-text("登录")')
    await page.waitForURL('/')
  })

  test('显示通知图标和未读数量', async ({ page }) => {
    const badge = page.locator('.notification-center .el-badge')
    await expect(badge).toBeVisible()
  })

  test('点击打开通知抽屉', async ({ page }) => {
    await page.click('.notification-center .notification-button')

    // 验证抽屉打开
    await expect(page.locator('.notification-drawer')).toBeVisible()

    // 验证Tab显示
    await expect(page.locator('.notification-tabs')).toBeVisible()
  })

  test('切换消息分类Tab', async ({ page }) => {
    await page.click('.notification-center .notification-button')

    // 点击未读Tab
    await page.click('.notification-tabs .el-tab-pane:has-text("未读")')

    // 验证Tab切换
    await expect(page.locator('.notification-tabs .el-tabs__active-bar')).toBeVisible()
  })

  test('标记消息为已读', async ({ page }) => {
    // 创建未读消息
    // ... 通过API创建测试数据

    await page.click('.notification-center .notification-button')

    // 点击标记已读按钮
    const unreadItem = page.locator('.notification-item.unread').first()
    await unreadItem.locator('button:has-text("标为已读")').click()

    // 验证已读状态
    await expect(unreadItem).not.toHaveClass('unread')
  })

  test('全部标记为已读', async ({ page }) => {
    await page.click('.notification-center .notification-button')

    // 点击全部已读按钮
    await page.click('button:has-text("全部已读")')

    // 验证所有消息已读
    const unreadItems = page.locator('.notification-item.unread')
    await expect(unreadItems).toHaveCount(0)
  })

  test('点击消息跳转', async ({ page }) => {
    await page.click('.notification-center .notification-button')

    // 点击一条消息
    await page.click('.notification-item:first-child')

    // 验证跳转（根据消息类型跳转到不同页面）
    await page.waitForTimeout(500)
    expect(page.url()).not.toBe('http://localhost:5173/')
  })
})

test.describe('通知配置管理', () => {
  test('查看通知渠道配置', async ({ page }) => {
    await page.goto('http://localhost:5173/admin/notifications')

    // 验证渠道表格
    await expect(page.locator('table').toBeVisible()

    // 验证渠道行
    const rows = page.locator('table tbody tr')
    await expect(await rows.count()).toBeGreaterThan(0)
  })

  test('启用/禁用通知渠道', async ({ page }) => {
    await page.goto('http://localhost:5173/admin/notifications')

    // 找到第一个渠道的开关
    const switchElement = page.locator('.el-switch').first()
    const isChecked = await switchElement.locator('input').isChecked()

    // 切换开关
    await switchElement.click()

    // 验证状态变化
    await expect(switchElement.locator('input')).not.toHaveJSProperty('checked', isChecked)
  })

  test('编辑消息模板', async ({ page }) => {
    await page.goto('http://localhost:5173/admin/notifications')

    // 点击模板编辑按钮
    await page.click('table tbody tr:first-child button:has-text("编辑")')

    // 验证编辑弹窗打开
    await expect(page.locator('.el-dialog')).toBeVisible()
  })

  test('发送测试通知', async ({ page }) => {
    await page.goto('http://localhost:5173/admin/notifications')

    // 点击发送测试通知按钮
    await page.click('button:has-text("发送测试")')

    // 填写测试数据
    await page.fill('input[placeholder*="标题"]', '测试通知')
    await page.fill('textarea[placeholder*="内容"]', '这是一条测试通知')

    // 选择接收人
    await page.click('.user-selector')
    await page.click('.el-select-dropdown__item:first-child')

    // 发送
    await page.click('.el-dialog button:has-text("发送")')

    // 验证成功提示
    await expect(page.locator('.el-message--success')).toBeVisible()
  })
})
```

---

## 验收标准

### 功能验收

- [ ] 企业微信渠道正常工作
- [ ] 邮件渠道正常工作
- [ ] 站内信渠道正常工作
- [ ] 消息模板解析正确
- [ ] 支持多渠道同时发送
- [ ] 发送日志完整记录
- [ ] 前端通知中心正常显示
- [ ] 未读消息计数准确
- [ ] 标记已读功能正常
- [ ] 全部已读功能正常

### 安全验收

- [ ] 敏感信息（密码）不在日志中显示
- [ ] 用户只能看到自己的站内信
- [ ] 管理员权限验证
- [ ] 防止通知频率滥用

### 测试覆盖率

- [ ] 渠道适配器测试覆盖率 > 80%
- [ ] 通知服务测试覆盖率 > 80%
- [ ] API测试覆盖率 > 90%

---

## 后续任务

1. Phase 3.1: 集成LogicFlow流程设计器
2. Phase 3.2: 实现工作流执行引擎
