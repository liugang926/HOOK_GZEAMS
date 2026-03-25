# Phase 1.9: 统一通知机制 - 测试计划

## 1. 测试概述

### 1.1 测试目标

- 验证模板引擎正确渲染
- 验证各渠道发送功能
- 验证失败重试机制
- 验证通知状态追踪
- 验证用户通知配置

### 1.2 测试范围

| 模块 | 测试类型 | 优先级 |
|------|----------|--------|
| 模板引擎 | 功能 | 高 |
| 渠道适配器 | 功能、集成 | 高 |
| 重试机制 | 功能 | 高 |
| 通知服务 | 功能 | 高 |
| 配置管理 | 功能 | 中 |

---

## 2. 后端单元测试

### 2.1 模板引擎测试

**文件**: `apps/notifications/tests/test_template.py`

```python
import pytest
from django.test import TestCase
from apps.notifications.models import NotificationTemplate
from apps.notifications.services.template_service import TemplateEngine


class TemplateEngineTest(TestCase):
    """模板引擎测试"""

    def setUp(self):
        self.template = NotificationTemplate.objects.create(
            template_code='TEST_TEMPLATE',
            template_name='测试模板',
            template_type='test',
            channel='inbox',
            subject_template='{{ title }} - {{ system_name }}',
            content_template='尊敬的{{ recipient_name }}，{{ content }}',
            language='zh-CN'
        )

    def test_render_template_basic(self):
        """测试基础模板渲染"""
        context = {
            'title': '测试标题',
            'content': '这是一条测试消息',
            'recipient': create_test_user()
        }

        result = TemplateEngine.render_template(
            'TEST_TEMPLATE',
            'inbox',
            context
        )

        assert '测试标题' in result['subject']
        assert '钩子固定资产' in result['subject']
        assert result['content']

    def test_render_template_with_loop(self):
        """测试带循环的模板渲染"""
        template = NotificationTemplate.objects.create(
            template_code='LOOP_TEMPLATE',
            template_name='循环模板',
            template_type='test',
            channel='inbox',
            content_template='''
                任务列表：
                {% for task in tasks %}
                - {{ task.title }}
                {% endfor %}
            '''
        )

        context = {
            'tasks': [
                {'title': '任务1'},
                {'title': '任务2'},
                {'title': '任务3'}
            ]
        }

        result = TemplateEngine.render_template(
            'LOOP_TEMPLATE',
            'inbox',
            context
        )

        assert '任务1' in result['content']
        assert '任务2' in result['content']
        assert '任务3' in result['content']

    def test_render_template_with_filter(self):
        """测试带过滤器的模板渲染"""
        template = NotificationTemplate.objects.create(
            template_code='FILTER_TEMPLATE',
            template_name='过滤器模板',
            template_type='test',
            channel='email',
            content_template='金额: {{ amount|format_money }}'
        )

        result = TemplateEngine.render_template(
            'FILTER_TEMPLATE',
            'email',
            {'amount': 12345.67}
        )

        assert '¥12,345.67' in result['content']

    def test_preview_template(self):
        """测试模板预览"""
        example_data = {
            'title': '示例标题',
            'content': '示例内容',
            'count': 5
        }

        result = TemplateEngine.preview_template(
            self.template.id,
            example_data
        )

        assert 'subject' in result
        assert 'content' in result

    def test_builtin_variables(self):
        """测试内置变量"""
        user = create_test_user(username='testuser')
        context = {'recipient': user}

        result = TemplateEngine.render_template(
            'TEST_TEMPLATE',
            'inbox',
            context
        )

        # 应该包含系统名称和用户名
        assert '钩子固定资产' in result['subject'] or result['content']
```

### 2.2 渠道适配器测试

**文件**: `apps/notifications/tests/test_channels.py`

```python
import pytest
from django.test import TestCase
from apps.notifications.channels.inbox import InboxChannel
from apps.notifications.channels.email import EmailChannel
from apps.notifications.channels.sms import SMSChannel
from apps.notifications.channels.base import NotificationMessage, SendResult
from apps.notifications.models import Notification


class NotificationChannelTest(TestCase):
    """通知渠道测试"""

    def setUp(self):
        self.user = create_test_user(
            username='testuser',
            email='test@example.com',
            phone_number='13800138000'
        )

    def test_inbox_channel_send(self):
        """测试站内信发送"""
        notification = Notification.objects.create(
            recipient=self.user,
            notification_type='test',
            channel='inbox',
            title='测试通知',
            content='测试内容',
            org=self.user.org
        )

        channel = InboxChannel()
        message = NotificationMessage(
            recipient=self.user,
            title='测试通知',
            content='测试内容',
            data={},
            notification_id=notification.id
        )

        result = channel.send(message)

        assert result.success is True
        assert result.message_id is not None

        # 验证通知状态
        notification.refresh_from_db()
        assert notification.status == 'success'

    def test_email_channel_send(self):
        """测试邮件发送（mock）"""
        from unittest.mock import patch

        notification = Notification.objects.create(
            recipient=self.user,
            notification_type='test',
            channel='email',
            title='测试邮件',
            content='邮件内容',
            org=self.user.org
        )

        channel = EmailChannel()
        message = NotificationMessage(
            recipient=self.user,
            title='测试邮件',
            content='邮件内容',
            data={},
            notification_id=notification.id
        )

        with patch('django.core.mail.send_mail', return_value=1):
            result = channel.send(message)

        assert result.success is True

    def test_email_channel_no_recipient_email(self):
        """测试邮件发送 - 无邮箱"""
        user_no_email = create_test_user(username='noemail')
        user_no_email.email = ''

        channel = EmailChannel()
        message = NotificationMessage(
            recipient=user_no_email,
            title='测试',
            content='内容',
            data={}
        )

        result = channel.send(message)

        assert result.success is False
        assert result.error_code == 'NO_EMAIL'

    def test_sms_channel_send(self):
        """测试短信发送（mock）"""
        from unittest.mock import patch, MagicMock

        channel = SMSChannel({'provider': 'aliyun'})
        message = NotificationMessage(
            recipient=self.user,
            title='验证码',
            content='您的验证码是123456',
            data={'code': '123456'}
        )

        mock_response = MagicMock()
        mock_response.get('Code', 'OK')
        mock_response.get('BizId', '12345')

        with patch('apps.notifications.channels.sms.AcsClient') as mock_client:
            mock_instance = mock_client.return_value
            mock_instance.do_action_with_exception.return_value.decode.return_value = '{"Code":"OK","BizId":"12345"}'

            result = channel.send(message)

        assert result.success is True
        assert result.message_id == '12345'

    def test_channel_supports_retry(self):
        """测试渠道重试支持"""
        inbox = InboxChannel()
        email = EmailChannel()

        assert inbox.supports_retry() is False
        assert email.supports_retry() is True
```

### 2.3 通知服务测试

**文件**: `apps/notifications/tests/test_notification_service.py`

```python
import pytest
from django.test import TestCase
from django.utils import timezone
from unittest.mock import patch, MagicMock
from apps.notifications.services import NotificationService
from apps.notifications.models import Notification, NotificationConfig


class NotificationServiceTest(TestCase):
    """通知服务测试"""

    def setUp(self):
        self.user = create_test_user()
        self.template = create_notification_template(
            template_code='WORKFLOW_APPROVAL',
            channel='inbox'
        )

    @patch('apps.notifications.services.NotificationService._enqueue_notification')
    def test_send_notification(self, mock_enqueue):
        """测试发送通知"""
        notification = NotificationService.send(
            recipient=self.user,
            notification_type='workflow_approval',
            variables={'task_title': '测试任务'},
            channels=['inbox']
        )

        assert notification is not None
        assert notification.notification_type == 'workflow_approval'
        assert notification.recipient == self.user
        assert mock_enqueue.called

    @patch('apps.notifications.services.NotificationService._enqueue_notification')
    def test_send_with_custom_channels(self, mock_enqueue):
        """测试指定渠道发送"""
        notification = NotificationService.send(
            recipient=self.user,
            notification_type='workflow_approval',
            variables={},
            channels=['inbox', 'email']
        )

        # 应该为每个渠道创建通知
        assert Notification.objects.filter(
            recipient=self.user,
            notification_type='workflow_approval'
        ).count() == 2

    @patch('apps.notifications.services.NotificationService._enqueue_notification')
    def test_send_batch_notifications(self, mock_enqueue):
        """测试批量发送"""
        users = [
            create_test_user(username=f'user{i}')
            for i in range(3)
        ]

        notifications = NotificationService.send_batch(
            recipients=users,
            notification_type='system_announcement',
            variables={'title': '系统通知'}
        )

        assert len(notifications) == 3

    def test_get_user_config(self):
        """测试获取用户配置"""
        config = NotificationService._get_user_config(self.user)

        assert isinstance(config, NotificationConfig)
        assert config.user == self.user

    def test_channel_disabled_by_user(self):
        """测试用户禁用渠道"""
        config = NotificationConfig.objects.get(user=self.user)
        config.enable_email = False
        config.save()

        # 用户禁用了邮件，应该只发送站内信
        with patch('apps.notifications.services.NotificationService._enqueue_notification'):
            notifications = NotificationService.send(
                recipient=self.user,
                notification_type='workflow_approval',
                variables={},
                channels=['inbox', 'email']
            )

        # 邮件通知应该被过滤掉
        assert Notification.objects.filter(
            recipient=self.user,
            channel='email'
        ).count() == 0

    @patch('apps.notifications.services.NotificationService._do_send')
    def test_process_notification_success(self, mock_send):
        """测试处理通知 - 成功"""
        mock_send.return_value = True

        notification = Notification.objects.create(
            recipient=self.user,
            notification_type='test',
            channel='inbox',
            title='测试',
            content='内容',
            status='pending',
            org=self.user.org
        )

        result = NotificationService.process_notification(notification.id)

        assert result is True
        notification.refresh_from_db()
        assert notification.status == 'success'

    def test_process_notification_with_retry(self):
        """测试处理通知 - 带重试"""
        # 模拟发送失败
        with patch('apps.notifications.channels.email.EmailChannel.send') as mock_send:
            mock_send.return_value = SendResult(
                success=False,
                error_code='TIMEOUT'
            )

            notification = Notification.objects.create(
                recipient=self.user,
                notification_type='test',
                channel='email',
                title='测试',
                content='内容',
                status='pending',
                priority='high',
                org=self.user.org
            )

            result = NotificationService.process_notification(notification.id)

        # 应该安排重试
        notification.refresh_from_db()
        assert notification.retry_count == 1
        assert notification.next_retry_at is not None

    def test_quiet_hours_filter(self):
        """测试免打扰时段过滤"""
        from datetime import time

        config = NotificationConfig.objects.get(user=self.user)
        config.quiet_hours_enabled = True
        config.quiet_hours_start = time(22, 0)
        config.quiet_hours_end = time(8, 0)
        config.save()

        with patch('apps.notifications.services.NotificationService._enqueue_notification'):
            # 普通优先级通知应该被延迟
            notification = NotificationService.send(
                recipient=self.user,
                notification_type='test',
                variables={},
                priority='normal'
            )

            assert notification.scheduled_at is not None

    def test_calculate_retry_time(self):
        """测试重试时间计算"""
        # 指数退避
        config = {
            'backoff': 'exponential',
            'initial_delay': 60,
            'max_delay': 3600
        }

        for retry_count in range(1, 5):
            retry_time = NotificationService._calculate_retry_time(retry_count, config)
            expected_delay = min(60 * (2 ** (retry_count - 1)), 3600)

            assert retry_time > timezone.now()
            assert retry_time < timezone.now() + timezone.timedelta(seconds=expected_delay + 1)
```

---

## 3. API 测试

**文件**: `apps/notifications/tests/test_api.py`

```python
import pytest
from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient
from apps.notifications.models import Notification, NotificationTemplate


class NotificationAPITest(TestCase):
    """通知 API 测试"""

    def setUp(self):
        self.client = APIClient()
        self.user = create_test_user()
        self.client.force_authenticate(user=self.user)

    def test_get_my_notifications(self):
        """测试获取我的通知列表"""
        # 创建测试通知
        Notification.objects.create(
            recipient=self.user,
            notification_type='test',
            channel='inbox',
            title='测试通知',
            content='测试内容',
            org=self.user.org
        )

        url = reverse('notification-my-list')
        response = self.client.get(url)

        assert response.status_code == 200
        assert response.data['count'] >= 1

    def test_get_unread_count(self):
        """测试获取未读数量"""
        Notification.objects.create(
            recipient=self.user,
            notification_type='test',
            channel='inbox',
            title='未读通知',
            content='内容',
            org=self.user.org
        )

        url = reverse('notification-unread-count')
        response = self.client.get(url)

        assert response.status_code == 200
        assert response.data['unread_count'] >= 1

    def test_mark_as_read(self):
        """测试标记已读"""
        notification = Notification.objects.create(
            recipient=self.user,
            notification_type='test',
            channel='inbox',
            title='未读通知',
            content='内容',
            org=self.user.org
        )

        url = reverse('notification-mark-read', args=[notification.id])
        response = self.client.post(url)

        assert response.status_code == 200
        assert response.data['is_read'] is True

    def test_mark_all_read(self):
        """测试标记全部已读"""
        Notification.objects.create(
            recipient=self.user,
            notification_type='test',
            channel='inbox',
            title='未读通知1',
            content='内容',
            org=self.user.org
        )
        Notification.objects.create(
            recipient=self.user,
            notification_type='test',
            channel='inbox',
            title='未读通知2',
            content='内容',
            org=self.user.org
        )

        url = reverse('notification-mark-all-read')
        response = self.client.post(url, {'all': True})

        assert response.status_code == 200

    def test_delete_notification(self):
        """测试删除通知"""
        notification = Notification.objects.create(
            recipient=self.user,
            notification_type='test',
            channel='inbox',
            title='测试',
            content='内容',
            org=self.user.org
        )

        url = reverse('notification-detail', args=[notification.id])
        response = self.client.delete(url)

        assert response.status_code == 204

    def test_get_config(self):
        """测试获取通知配置"""
        url = reverse('notification-config')
        response = self.client.get(url)

        assert response.status_code == 200
        assert 'enable_inbox' in response.data
        assert 'enable_email' in response.data

    def test_update_config(self):
        """测试更新通知配置"""
        url = reverse('notification-config')
        data = {
            'enable_email': False,
            'enable_sms': True
        }

        response = self.client.patch(url, data)

        assert response.status_code == 200
        assert response.data['enable_email'] is False
        assert response.data['enable_sms'] is True

    def test_send_notification_api(self):
        """测试发送通知 API"""
        template = create_notification_template()

        url = reverse('notification-send')
        data = {
            'recipient_id': self.user.id,
            'notification_type': 'test',
            'variables': {'title': '测试'}
        }

        response = self.client.post(url, data)

        assert response.status_code == 200
```

---

## 4. 性能测试

### 4.1 批量发送性能

```python
class PerformanceTest(TestCase):
    """性能测试"""

    def test_batch_send_performance(self):
        """测试批量发送性能"""
        import time

        users = [create_test_user(username=f'user{i}') for i in range(100)]

        start_time = time.time()

        notifications = NotificationService.send_batch(
            recipients=users,
            notification_type='system_announcement',
            variables={'title': '批量测试'}
        )

        duration = time.time() - start_time

        assert len(notifications) == 100
        assert duration < 5  # 5秒内完成

    def test_template_rendering_performance(self):
        """测试模板渲染性能"""
        import time

        template = create_notification_template()

        start_time = time.time()

        for i in range(1000):
            TemplateEngine.render_template(
                'TEST_TEMPLATE',
                'inbox',
                {'title': f'测试{i}', 'content': '内容'}
            )

        duration = time.time() - start_time

        assert duration < 2  # 2秒内完成1000次渲染
```

---

## 5. 测试通过标准

1. **单元测试**: 代码覆盖率 >= 90%
2. **集成测试**: 核心流程可正常运行
3. **渠道测试**: 各渠道适配器正常工作
4. **重试测试**: 重试机制正确执行
5. **性能测试**: 批量发送1000条 < 30秒
