# Phase 2.3: 通知中心模块 - 后端实现

## 1. 公共模型引用声明

### 1.1 引用公共基类

本模块所有数据模型均继承自 `apps.common.models.BaseModel`，自动获得以下能力：

- **多组织数据隔离**：内置 `organization` 字段，自动过滤组织数据
- **软删除机制**：内置 `is_deleted`、`deleted_at` 字段，物理删除禁用
- **审计字段**：内置 `created_at`、`updated_at`、`created_by` 字段，追踪数据变更
- **动态扩展**：内置 `custom_fields` (JSONB) 字段，支持低代码动态扩展

### 1.2 引用公共模型

| 模型名称 | 引用路径 | 用途 |
|----------|----------|------|
| **Organization** | `apps.organizations.models.Organization` | 组织多租户隔离 |
| **User** | `apps.accounts.models.User` | 系统用户，通知接收者 |
| **BaseModel** | `apps.common.models.BaseModel` | 所有模型的抽象基类 |
| **BaseModelSerializer** | `apps.common.serializers.base.BaseModelSerializer` | 序列化器基类 |
| **BaseModelViewSet** | `apps.common.viewsets.base.BaseModelViewSetWithBatch` | 视图集基类 |
| **BaseCRUDService** | `apps.common.services.base_crud.BaseCRUDService` | 服务层基类 |

### 1.3 引用第三方集成模型

| 模型名称 | 引用路径 | 用途 |
|----------|----------|------|
| **UserMapping** | `apps.sso.models.UserMapping` | 第三方平台用户ID映射 |

---

## 2. 数据模型设计

### 2.1 模型依赖关系

```
Organization (组织)
    │
    ├─> NotificationChannel (通知渠道配置)
    │       └─> NotificationMessage (通知消息)
    │               └─> NotificationLog (发送日志)
    │
    ├─> NotificationTemplate (消息模板)
    │
    └─> InAppMessage (站内信)
            └─> User (接收用户)
```

### 2.2 通知渠道配置模型

#### NotificationChannel (通知渠道表)

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| channel_type | string | max_length=20 | 渠道类型 (wework/dingtalk/feishu/email/sms/inapp/webhook) |
| config | JSON | default=dict | 渠道配置参数 |
| priority | integer | default=0 | 优先级 (越小越高) |
| is_enabled | boolean | default=True | 是否启用 |
| description | string | max_length=200, blank | 描述 |

*继承 BaseModel 自动获得: organization, is_deleted, deleted_at, created_at, updated_at, created_by, custom_fields*

*唯一约束: (organization, channel_type)*
*索引: (organization, channel_type), (organization, is_enabled, priority)*
*方法: get_config_value(key, default)*

### 2.3 消息模板模型

#### NotificationTemplate (消息模板表)

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| code | string | max_length=50, unique, index | 模板编码 (全局唯一) |
| name | string | max_length=100 | 模板名称 |
| template_type | string | max_length=20 | 模板类型 (text/textcard/markdown/template_card/html/interactive) |
| title | string | max_length=200, blank | 标题模板 |
| content | text | - | 内容模板 (支持Jinja2语法) |
| url_template | URL | blank | 跳转链接模板 |
| button_text | string | max_length=50, blank | 按钮文字 |
| button_url_template | URL | blank | 按钮链接模板 |
| business_category | string | max_length=50, index | 业务分类 (approval/asset/inventory/system/reminder) |
| remark | text | blank | 备注 |

*继承 BaseModel 自动获得公共字段*
*索引: code, business_category*

### 2.4 通知消息记录模型

```python
class NotificationMessage(BaseModel):
    """
    通知消息记录

    记录每次通知发送的完整信息，包括：
    - 消息内容
    - 接收人列表
    - 发送渠道
    - 发送状态
    - 发送结果统计
    """

    class Meta:
        db_table = 'notification_message'
        verbose_name = '通知消息'
        verbose_name_plural = '通知消息'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['organization', 'business_type', 'business_id']),
            models.Index(fields=['organization', 'status', 'created_at']),
        ]

    # ========== BaseModel 继承字段 ==========
    # organization: ForeignKey (自动继承)
    # is_deleted, deleted_at, created_at, updated_at, created_by

    # ========== 业务字段 ==========

    # 消息模板
    template = models.ForeignKey(
        'NotificationTemplate',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name='消息模板'
    )

    # 业务关联
    business_type = models.CharField(
        max_length=50,
        blank=True,
        db_index=True,
        verbose_name='业务类型',
        help_text='如：asset_pickup、approval、inventory_alert等'
    )
    business_id = models.CharField(
        max_length=100,
        blank=True,
        db_index=True,
        verbose_name='业务ID'
    )

    # 消息内容
    title = models.CharField(
        max_length=200,
        verbose_name='标题'
    )
    content = models.TextField(
        verbose_name='内容'
    )

    # 跳转链接
    url = models.URLField(
        blank=True,
        verbose_name='跳转链接'
    )
    button_text = models.CharField(
        max_length=50,
        blank=True,
        verbose_name='按钮文字'
    )
    button_url = models.URLField(
        blank=True,
        verbose_name='按钮链接'
    )

    # 接收人（JSON存储）
    recipients = models.JSONField(
        default=list,
        verbose_name='接收人',
        help_text='[{"user_id": "1", "channel": "wework"}]'
    )

    # 发送状态
    status = models.CharField(
        max_length=20,
        choices=[
            ('pending', '待发送'),
            ('sending', '发送中'),
            ('success', '成功'),
            ('partial_success', '部分成功'),
            ('failed', '失败'),
        ],
        default='pending',
        db_index=True,
        verbose_name='发送状态'
    )

    # 发送结果统计
    sent_count = models.IntegerField(
        default=0,
        verbose_name='发送成功数'
    )
    failed_count = models.IntegerField(
        default=0,
        verbose_name='发送失败数'
    )

    # 发送时间
    sent_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='发送时间'
    )

    # 错误信息
    error_message = models.TextField(
        blank=True,
        verbose_name='错误信息'
    )

    # 失败详情
    failure_details = models.JSONField(
        default=list,
        blank=True,
        verbose_name='失败详情'
    )

    def __str__(self):
        return f"{self.title} - {self.get_status_display()}"

    @property
    def total_recipients(self):
        """总接收人数"""
        return len(self.recipients) if isinstance(self.recipients, list) else 0
```

### 2.5 站内信模型

```python
class InAppMessage(BaseModel):
    """
    站内消息

    存储系统内的通知消息，用户可查看、标记已读、删除。
    通过WebSocket实时推送到前端。
    """

    class Meta:
        db_table = 'inapp_message'
        verbose_name = '站内消息'
        verbose_name_plural = '站内消息'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'is_read', 'created_at']),
            models.Index(fields=['user', 'message_type', 'created_at']),
        ]

    # ========== BaseModel 继承字段 ==========
    # organization: ForeignKey (自动继承，通过user间接关联)
    # is_deleted, deleted_at, created_at, updated_at, created_by

    # ========== 业务字段 ==========

    # 接收用户
    user = models.ForeignKey(
        'accounts.User',
        on_delete=models.CASCADE,
        related_name='inapp_messages',
        verbose_name='接收用户'
    )

    # 消息类型
    message_type = models.CharField(
        max_length=20,
        choices=[
            ('system', '系统通知'),
            ('approval', '审批通知'),
            ('asset', '资产通知'),
            ('inventory', '库存通知'),
            ('reminder', '提醒通知'),
        ],
        default='system',
        db_index=True,
        verbose_name='消息类型'
    )

    # 标题和内容
    title = models.CharField(
        max_length=200,
        verbose_name='标题'
    )
    content = models.TextField(
        verbose_name='内容'
    )

    # 跳转链接
    url = models.URLField(
        blank=True,
        verbose_name='跳转链接'
    )
    button_text = models.CharField(
        max_length=50,
        blank=True,
        verbose_name='按钮文字'
    )
    button_url = models.URLField(
        blank=True,
        verbose_name='按钮链接'
    )

    # 业务关联
    business_type = models.CharField(
        max_length=50,
        blank=True,
        verbose_name='业务类型'
    )
    business_id = models.CharField(
        max_length=100,
        blank=True,
        verbose_name='业务ID'
    )

    # 阅读状态
    is_read = models.BooleanField(
        default=False,
        db_index=True,
        verbose_name='是否已读'
    )
    read_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='阅读时间'
    )

    def __str__(self):
        return f"{self.title} - {self.user.get_full_name() or self.user.username}"

    def mark_as_read(self):
        """标记为已读"""
        from django.utils import timezone
        self.is_read = True
        self.read_at = timezone.now()
        self.save(update_fields=['is_read', 'read_at'])
```

### 2.6 通知发送日志模型

```python
class NotificationLog(BaseModel):
    """
    通知发送日志

    记录每条消息的每个接收人在每个渠道的发送状态。
    用于问题排查和发送统计。
    """

    class Meta:
        db_table = 'notification_log'
        verbose_name = '通知发送日志'
        verbose_name_plural = '通知发送日志'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['message', 'recipient_id']),
            models.Index(fields=['channel', 'status', 'created_at']),
        ]

    # ========== BaseModel 继承字段 ==========
    # organization: ForeignKey (自动继承，通过message间接关联)
    # is_deleted, deleted_at, created_at, updated_at, created_by

    # ========== 业务字段 ==========

    # 关联消息
    message = models.ForeignKey(
        'NotificationMessage',
        on_delete=models.CASCADE,
        related_name='logs',
        verbose_name='消息记录'
    )

    # 接收人
    recipient_id = models.CharField(
        max_length=100,
        db_index=True,
        verbose_name='接收人ID'
    )
    recipient_channel_id = models.CharField(
        max_length=100,
        blank=True,
        verbose_name='渠道用户ID'
    )

    # 发送渠道
    channel = models.CharField(
        max_length=20,
        db_index=True,
        verbose_name='发送渠道'
    )

    # 发送状态
    status = models.CharField(
        max_length=20,
        choices=[
            ('pending', '待发送'),
            ('sent', '已发送'),
            ('delivered', '已送达'),
            ('read', '已读'),
            ('failed', '失败'),
        ],
        default='pending',
        db_index=True,
        verbose_name='状态'
    )

    # 渠道返回的消息ID
    external_message_id = models.CharField(
        max_length=100,
        blank=True,
        verbose_name='外部消息ID'
    )

    # 错误信息
    error_message = models.TextField(
        blank=True,
        verbose_name='错误信息'
    )

    # 时间记录
    sent_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='发送时间'
    )
    delivered_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='送达时间'
    )
    read_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='阅读时间'
    )

    def __str__(self):
        return f"{self.recipient_id} - {self.channel} - {self.get_status_display()}"
```

---

## 3. 渠道适配器架构

### 3.1 抽象基类

```python
# apps/notifications/channels/base.py

from abc import ABC, abstractmethod
from typing import List, Dict, Any


class NotificationChannelAdapter(ABC):
    """
    通知渠道适配器抽象基类

    所有渠道适配器必须实现此接口，确保统一的调用方式。
    """

    def __init__(self, config: Dict[str, Any]):
        """
        初始化适配器

        Args:
            config: 渠道配置字典
        """
        self.config = config
        self.channel_type = self.get_channel_type()
        self._access_token = None

    @abstractmethod
    def get_channel_type(self) -> str:
        """获取渠道类型标识"""
        pass

    @abstractmethod
    def get_channel_name(self) -> str:
        """获取渠道名称"""
        pass

    @abstractmethod
    def is_available(self) -> bool:
        """检查渠道是否可用"""
        pass

    @abstractmethod
    def send_message(self, message: Dict, recipients: List[Dict]) -> Dict:
        """
        发送消息

        Args:
            message: 消息内容
                {
                    'title': str,
                    'content': str,
                    'url': str,
                    'button_text': str,
                    'button_url': str,
                }
            recipients: 接收人列表
                [{
                    'user_id': str,  # 系统用户ID
                    'channel_id': str,  # 渠道用户ID（可选）
                }]

        Returns:
            发送结果
                {
                    'success': bool,
                    'sent_count': int,
                    'failed_count': int,
                    'details': [{
                        'user_id': str,
                        'status': str,
                        'external_id': str,
                        'error': str,
                    }]
                }
        """
        pass

    @abstractmethod
    def get_user_channel_id(self, system_user_id: str) -> str:
        """
        获取用户在当前渠道的ID

        Args:
            system_user_id: 系统用户ID

        Returns:
            渠道用户ID
        """
        pass

    def send_template(self, template_code: str, params: Dict, recipients: List[Dict]) -> Dict:
        """
        发送模板消息（默认实现）

        Args:
            template_code: 模板编码
            params: 模板参数
            recipients: 接收人列表

        Returns:
            发送结果
        """
        from apps.notifications.models import NotificationTemplate

        template = NotificationTemplate.objects.get(code=template_code)

        # 解析模板
        content = self.parse_template(template.content, params)
        title = self.parse_template(template.title, params)
        url = self.parse_template(template.url_template, params) if template.url_template else ''

        return self.send_message({
            'title': title,
            'content': content,
            'url': url,
            'button_text': template.button_text,
            'button_url': template.button_url_template
        }, recipients)

    def batch_get_user_channel_ids(self, system_user_ids: List[str]) -> Dict[str, str]:
        """
        批量获取用户的渠道ID

        Args:
            system_user_ids: 系统用户ID列表

        Returns:
            {system_user_id: channel_id} 映射
        """
        return {
            user_id: self.get_user_channel_id(user_id)
            for user_id in system_user_ids
        }

    def supports_template_card(self) -> bool:
        """是否支持卡片消息"""
        return False

    def supports_markdown(self) -> bool:
        """是否支持Markdown"""
        return False

    def parse_template(self, content: str, params: Dict) -> str:
        """
        解析模板变量

        支持的变量格式:
        - {{variable}} 或 {variable}
        - 支持嵌套对象访问: {{user.name}}

        Args:
            content: 模板内容
            params: 参数字典

        Returns:
            解析后的内容
        """
        import re

        def replace_var(match):
            var_path = match.group(1) or match.group(2)
            value = self._get_nested_value(params, var_path)
            return str(value) if value is not None else ''

        # 匹配 {{variable}} 或 {variable}
        result = re.sub(r'\{\{([^}]+)\}\}|\{([^}]+)\}', replace_var, content)

        return result

    def _get_nested_value(self, data: Dict, path: str) -> Any:
        """获取嵌套字典的值"""
        keys = path.strip().split('.')
        value = data
        for key in keys:
            if isinstance(value, dict):
                value = value.get(key)
            else:
                return None
            if value is None:
                return None
        return value
```

### 3.2 渠道适配器注册表

```python
# apps/notifications/channels/registry.py

CHANNEL_CLASSES = {
    'wework': 'apps.notifications.channels.wework_channel.WeWorkNotificationChannel',
    'dingtalk': 'apps.notifications.channels.dingtalk_channel.DingTalkNotificationChannel',
    'feishu': 'apps.notifications.channels.feishu_channel.FeishuNotificationChannel',
    'email': 'apps.notifications.channels.email_channel.EmailNotificationChannel',
    'inapp': 'apps.notifications.channels.inapp_channel.InAppNotificationChannel',
}


def get_channel_class(channel_type: str):
    """动态导入渠道类"""
    from django.utils.module_loading import import_string
    class_path = CHANNEL_CLASSES.get(channel_type)
    if not class_path:
        raise ValueError(f"不支持的渠道类型: {channel_type}")
    return import_string(class_path)
```

### 3.3 企业微信渠道实现

```python
# apps/notifications/channels/wework_channel.py

import requests
from typing import Dict, List
from .base import NotificationChannelAdapter


class WeWorkNotificationChannel(NotificationChannelAdapter):
    """企业微信通知渠道"""

    API_BASE = "https://qyapi.weixin.qq.com/cgi-bin"

    def __init__(self, config: Dict):
        super().__init__(config)
        self.corp_id = config.get('corp_id')
        self.agent_id = config.get('agent_id')
        self.agent_secret = config.get('agent_secret')

    def get_channel_type(self) -> str:
        return 'wework'

    def get_channel_name(self) -> str:
        return '企业微信'

    def is_available(self) -> bool:
        """检查企业微信配置是否可用"""
        return bool(self.corp_id and self.agent_id and self.agent_secret)

    def get_access_token(self) -> str:
        """获取access_token"""
        if self._access_token:
            return self._access_token

        url = f"{self.API_BASE}/gettoken"
        params = {
            "corpid": self.corp_id,
            "corpsecret": self.agent_secret
        }

        response = requests.get(url, params=params, timeout=10)
        data = response.json()

        if data['errcode'] != 0:
            raise Exception(f"获取企业微信token失败: {data['errmsg']}")

        self._access_token = data['access_token']
        return self._access_token

    def get_user_channel_id(self, system_user_id: str) -> str:
        """获取用户的企业微信userid"""
        from apps.sso.models import UserMapping

        mapping = UserMapping.objects.filter(
            platform='wework',
            system_user_id=system_user_id
        ).first()

        if mapping:
            return mapping.platform_userid

        raise ValueError(f"用户 {system_user_id} 未绑定企业微信")

    def send_message(self, message: Dict, recipients: List[Dict]) -> Dict:
        """发送企业微信消息"""
        token = self.get_access_token()
        url = f"{self.API_BASE}/message/send?access_token={token}"

        details = []
        sent_count = 0
        failed_count = 0

        # 获取用户渠道ID
        recipient_map = {}
        for recipient in recipients:
            try:
                channel_id = recipient.get('channel_id')
                if not channel_id:
                    channel_id = self.get_user_channel_id(recipient['user_id'])
                recipient_map[recipient['user_id']] = channel_id
            except Exception as e:
                details.append({
                    'user_id': recipient['user_id'],
                    'status': 'failed',
                    'error': str(e)
                })
                failed_count += 1

        # 批量发送（企业微信支持批量，最多1000人）
        user_ids = "|".join(recipient_map.values())

        payload = {
            "touser": user_ids,
            "msgtype": "textcard",
            "agentid": self.agent_id,
            "textcard": {
                "title": message['title'],
                "description": message['content'],
                "url": message.get('url', ''),
                "btntxt": message.get('button_text', '详情')
            }
        }

        response = requests.post(url, json=payload, timeout=10)
        result = response.json()

        if result.get('errcode') == 0:
            sent_count = len(recipient_map)
            for user_id in recipient_map.keys():
                details.append({
                    'user_id': user_id,
                    'status': 'sent',
                    'external_id': ''
                })
        else:
            failed_count = len(recipient_map)
            for user_id in recipient_map.keys():
                details.append({
                    'user_id': user_id,
                    'status': 'failed',
                    'error': result.get('errmsg', '未知错误')
                })

        return {
            'success': result.get('errcode') == 0,
            'sent_count': sent_count,
            'failed_count': failed_count,
            'details': details
        }

    def supports_template_card(self) -> bool:
        return True
```

### 3.4 邮件渠道实现

```python
# apps/notifications/channels/email_channel.py

from typing import Dict, List
from django.core.mail import EmailMultiAlternatives
from .base import NotificationChannelAdapter


class EmailNotificationChannel(NotificationChannelAdapter):
    """邮件通知渠道"""

    def __init__(self, config: Dict):
        super().__init__(config)
        self.from_email = config.get('from_email')
        self.email_host = config.get('email_host')
        self.email_port = config.get('email_port', 587)
        self.email_use_tls = config.get('email_use_tls', True)
        self.email_host_user = config.get('email_host_user')
        self.email_host_password = config.get('email_host_password')

    def get_channel_type(self) -> str:
        return 'email'

    def get_channel_name(self) -> str:
        return '邮件'

    def is_available(self) -> bool:
        return bool(self.from_email)

    def get_user_channel_id(self, system_user_id: str) -> str:
        """获取用户邮箱"""
        from apps.accounts.models import User

        try:
            user = User.objects.get(id=system_user_id)
            if user.email:
                return user.email
        except User.DoesNotExist:
            pass

        raise ValueError(f"用户 {system_user_id} 未设置邮箱")

    def send_message(self, message: Dict, recipients: List[Dict]) -> Dict:
        """发送邮件"""
        email_addresses = []
        details = []
        sent_count = 0
        failed_count = 0

        for recipient in recipients:
            try:
                email = recipient.get('channel_id')
                if not email:
                    email = self.get_user_channel_id(recipient['user_id'])
                email_addresses.append(email)
                details.append({
                    'user_id': recipient['user_id'],
                    'status': 'sent',
                    'external_id': ''
                })
                sent_count += 1
            except Exception as e:
                details.append({
                    'user_id': recipient['user_id'],
                    'status': 'failed',
                    'error': str(e)
                })
                failed_count += 1

        # 发送邮件
        try:
            email_message = EmailMultiAlternatives(
                subject=message['title'],
                body=message['content'],
                from_email=self.from_email,
                bcc=email_addresses
            )

            # HTML版本
            html_content = f"""
            <html>
            <body style="font-family: Arial, sans-serif;">
                <h2 style="color: #333;">{message['title']}</h2>
                <p style="color: #666; line-height: 1.6;">
                    {message['content'].replace(chr(10), '<br>')}
                </p>
                {f'<p><a href="{message.get("url", "")}" style="color: #409EFF; text-decoration: none;">{message.get("button_text", "查看详情")}</a></p>' if message.get('url') else ''}
            </body>
            </html>
            """
            email_message.attach_alternative(html_content, "text/html")
            email_message.send()

        except Exception as e:
            # 全部失败
            for detail in details:
                if detail['status'] == 'sent':
                    detail['status'] = 'failed'
                    detail['error'] = str(e)
            sent_count = 0
            failed_count = len(email_addresses)

        return {
            'success': sent_count > 0,
            'sent_count': sent_count,
            'failed_count': failed_count,
            'details': details
        }

    def supports_template_card(self) -> bool:
        return True

    def supports_markdown(self) -> bool:
        return True
```

### 3.5 站内信渠道实现

```python
# apps/notifications/channels/inapp_channel.py

from typing import Dict, List
from .base import NotificationChannelAdapter


class InAppNotificationChannel(NotificationChannelAdapter):
    """站内信通知渠道"""

    def get_channel_type(self) -> str:
        return 'inapp'

    def get_channel_name(self) -> str:
        return '站内信'

    def is_available(self) -> bool:
        return True

    def get_user_channel_id(self, system_user_id: str) -> str:
        return system_user_id

    def send_message(self, message: Dict, recipients: List[Dict]) -> Dict:
        """发送站内信"""
        from apps.notifications.models import InAppMessage

        messages = []
        for recipient in recipients:
            msg = InAppMessage.objects.create(
                user_id=recipient['user_id'],
                title=message['title'],
                content=message['content'],
                url=message.get('url', ''),
                button_text=message.get('button_text', ''),
                button_url=message.get('button_url', '')
            )
            messages.append(msg)

        return {
            'success': True,
            'sent_count': len(messages),
            'failed_count': 0,
            'details': [
                {
                    'user_id': msg.user_id,
                    'status': 'sent',
                    'external_id': str(msg.id)
                }
                for msg in messages
            ]
        }

    def supports_markdown(self) -> bool:
        return True
```

---

## 4. 通知服务层

### 4.1 统一服务类

```python
# apps/notifications/services/notification_service.py

from typing import List, Dict, Optional
from django.utils import timezone
from apps.notifications.models import (
    NotificationChannel,
    NotificationMessage,
    NotificationTemplate,
    NotificationLog
)
from .channels.registry import get_channel_class


class NotificationService:
    """
    通知服务（统一入口）

    使用示例：
    ```python
    # 直接发送
    service = NotificationService()
    service.send(
        business_type='asset_pickup',
        business_id='123',
        title='待审批: 资产领用',
        content='...',
        recipients=[{'user_id': '1'}],
        channels=['wework', 'inapp']
    )

    # 模板发送
    service.send_template(
        template_code='asset_pickup_created',
        recipients=[{'user_id': '1'}],
        params={'applicant': '张三'}
    )
    ```
    """

    def __init__(self, organization=None):
        """
        初始化通知服务

        Args:
            organization: 组织对象（可选，默认使用当前组织）
        """
        if organization is None:
            from apps.common.context import get_current_organization
            organization = get_current_organization()

        self.organization = organization
        self._channels = {}  # 缓存渠道实例

    def send(self, business_type: str, business_id: str, title: str,
             content: str, recipients: List[Dict], channels: List[str] = None,
             url: str = '', button_text: str = '', button_url: str = '',
             template_code: str = None, params: Dict = None) -> NotificationMessage:
        """
        发送通知（统一入口）

        Args:
            business_type: 业务类型
            business_id: 业务ID
            title: 标题
            content: 内容
            recipients: 接收人列表
            channels: 指定渠道列表
            url: 跳转链接
            button_text: 按钮文字
            button_url: 按钮链接
            template_code: 模板编码（如果使用模板）
            params: 模板参数

        Returns:
            NotificationMessage 对象
        """
        # 如果指定了模板，从模板获取内容
        if template_code:
            return self.send_template(
                template_code=template_code,
                business_type=business_type,
                business_id=business_id,
                recipients=recipients,
                channels=channels,
                params=params or {}
            )

        # 创建消息记录
        message = NotificationMessage.objects.create(
            organization=self.organization,
            title=title,
            content=content,
            url=url,
            button_text=button_text,
            button_url=button_url,
            business_type=business_type,
            business_id=business_id,
            recipients=recipients,
            status='pending'
        )

        # 获取启用的渠道
        if channels is None:
            channels = self._get_enabled_channels()

        # 发送到各个渠道
        results = self._send_to_channels(
            message=message,
            channels=channels,
            recipients=recipients
        )

        # 更新消息状态
        total_sent = sum(r['sent_count'] for r in results)
        total_failed = sum(r['failed_count'] for r in results)

        if total_failed == 0:
            message.status = 'success'
        elif total_sent > 0:
            message.status = 'partial_success'
        else:
            message.status = 'failed'

        message.sent_count = total_sent
        message.failed_count = total_failed
        message.sent_at = timezone.now()
        message.save()

        return message

    def send_template(self, template_code: str, recipients: List[Dict],
                     params: Dict, channels: List[str] = None,
                     business_type: str = None, business_id: str = None) -> NotificationMessage:
        """
        发送模板消息

        Args:
            template_code: 模板编码
            recipients: 接收人列表
            params: 模板参数
            channels: 指定渠道列表
            business_type: 业务类型
            business_id: 业务ID

        Returns:
            NotificationMessage 对象
        """
        # 获取模板
        template = NotificationTemplate.objects.get(code=template_code)

        # 使用第一个可用渠道解析模板
        available_channels = channels or self._get_enabled_channels()
        channel = self._get_channel_instance(available_channels[0])

        title = channel.parse_template(template.title, params)
        content = channel.parse_template(template.content, params)
        url = channel.parse_template(template.url_template, params) if template.url_template else ''
        button_url = channel.parse_template(template.button_url_template, params) if template.button_url_template else ''

        return self.send(
            business_type=business_type or template.business_category,
            business_id=business_id or '',
            title=title,
            content=content,
            recipients=recipients,
            channels=channels,
            url=url,
            button_text=template.button_text,
            button_url=button_url
        )

    def _get_enabled_channels(self) -> List[str]:
        """获取启用的渠道列表"""
        channels = NotificationChannel.objects.filter(
            organization=self.organization,
            is_enabled=True
        ).order_by('priority').values_list('channel_type', flat=True)

        return list(channels)

    def _get_channel_instance(self, channel_type: str):
        """获取渠道实例"""
        if channel_type not in self._channels:
            # 从数据库获取配置
            channel_config = NotificationChannel.objects.filter(
                organization=self.organization,
                channel_type=channel_type,
                is_enabled=True
            ).first()

            if not channel_config:
                raise ValueError(f"渠道 {channel_type} 未启用或不存在")

            # 实例化渠道
            channel_class = get_channel_class(channel_type)
            self._channels[channel_type] = channel_class(channel_config.config)

        return self._channels[channel_type]

    def _send_to_channels(self, message: NotificationMessage,
                         channels: List[str], recipients: List[Dict]) -> List[Dict]:
        """发送到各个渠道"""
        results = []

        for channel_type in channels:
            try:
                channel = self._get_channel_instance(channel_type)
                result = channel.send_message({
                    'title': message.title,
                    'content': message.content,
                    'url': message.url,
                    'button_text': message.button_text,
                    'button_url': message.button_url,
                }, recipients)

                results.append({
                    'channel': channel_type,
                    **result
                })

                # 记录日志
                self._create_logs(
                    message=message,
                    channel=channel_type,
                    details=result.get('details', [])
                )

            except Exception as e:
                results.append({
                    'channel': channel_type,
                    'success': False,
                    'sent_count': 0,
                    'failed_count': len(recipients),
                    'error': str(e)
                })

        return results

    def _create_logs(self, message: NotificationMessage, channel: str,
                     details: List[Dict]):
        """创建发送日志"""
        logs = []
        for detail in details:
            logs.append(NotificationLog(
                message=message,
                recipient_id=detail['user_id'],
                channel=channel,
                status='sent' if detail['status'] == 'sent' else 'failed',
                external_message_id=detail.get('external_id', ''),
                error_message=detail.get('error', '')
            ))
        NotificationLog.objects.bulk_create(logs)
```

### 4.2 业务通知助手类

```python
# apps/notifications/services/helpers.py

class AssetNotificationHelper:
    """资产通知助手类"""

    @staticmethod
    def notify_pickup_created(pickup, channels: List[str] = None):
        """领用单创建通知"""
        from .notification_service import NotificationService

        # 获取审批人（从工作流配置中获取）
        approvers = []  # TODO: 从工作流获取审批人

        recipients = [{'user_id': str(approver.id)} for approver in approvers]

        service = NotificationService(pickup.organization)
        service.send_template(
            template_code='asset_pickup_created',
            business_type='asset_pickup',
            business_id=str(pickup.id),
            recipients=recipients,
            channels=channels,
            params={
                'applicant': pickup.applicant.get_full_name(),
                'department': pickup.department.name,
                'pickup_no': pickup.pickup_no,
                'pickup_reason': pickup.pickup_reason,
            }
        )

    @staticmethod
    def notify_pickup_approved(pickup, channels: List[str] = None):
        """领用单审批通过通知"""
        from .notification_service import NotificationService

        service = NotificationService(pickup.organization)
        service.send_template(
            template_code='asset_pickup_approved',
            business_type='asset_pickup',
            business_id=str(pickup.id),
            recipients=[{'user_id': str(pickup.applicant.id)}],
            channels=channels,
            params={
                'pickup_no': pickup.pickup_no,
            }
        )


class InventoryNotificationHelper:
    """库存预警通知助手"""

    @staticmethod
    def notify_low_stock(consumable):
        """低库存预警通知"""
        from .notification_service import NotificationService
        from apps.accounts.models import User

        # 获取采购人员（有采购权限的用户）
        purchasers = User.objects.filter(
            organization=consumable.organization,
            roles__permissions__codename__in=['purchase_consumable']
        ).distinct()

        recipients = [{'user_id': str(p.id)} for p in purchasers]

        service = NotificationService(consumable.organization)
        service.send_template(
            template_code='consumable_low_stock',
            business_type='inventory_alert',
            business_id=str(consumable.id),
            recipients=recipients,
            params={
                'consumable_name': consumable.name,
                'consumable_code': consumable.code,
                'current_stock': consumable.available_stock,
                'min_stock': consumable.min_stock,
                'unit': consumable.unit
            }
        )
```

---

## 5. Celery异步任务

### 5.1 发送任务

```python
# apps/notifications/tasks.py

from celery import shared_task
from typing import List, Dict


@shared_task(
    bind=True,
    max_retries=3,
    default_retry_delay=60,
    autoretry_for=(ConnectionError, TimeoutError)
)
def send_notification_async(self, business_type: str, business_id: str,
                            title: str, content: str, recipients: List[Dict],
                            channels: List[str] = None, org_id: int = None,
                            url: str = '', button_text: str = ''):
    """
    异步发送通知

    支持指数退避重试：
    - 第1次重试：60秒
    - 第2次重试：120秒
    - 第3次重试：240秒
    """
    from apps.notifications.services.notification_service import NotificationService
    from apps.organizations.models import Organization

    org = Organization.objects.get(id=org_id) if org_id else None
    service = NotificationService(org)

    message = service.send(
        business_type=business_type,
        business_id=business_id,
        title=title,
        content=content,
        recipients=recipients,
        channels=channels,
        url=url,
        button_text=button_text
    )

    return {
        'message_id': str(message.id),
        'status': message.status,
        'sent_count': message.sent_count,
        'failed_count': message.failed_count
    }


@shared_task(
    bind=True,
    max_retries=3,
    default_retry_delay=60
)
def send_template_notification_async(self, template_code: str,
                                     recipients: List[Dict], params: Dict,
                                     channels: List[str] = None,
                                     org_id: int = None):
    """异步发送模板通知"""
    from apps.notifications.services.notification_service import NotificationService
    from apps.organizations.models import Organization

    org = Organization.objects.get(id=org_id) if org_id else None
    service = NotificationService(org)

    message = service.send_template(
        template_code=template_code,
        recipients=recipients,
        params=params,
        channels=channels
    )

    return {
        'message_id': str(message.id),
        'status': message.status,
        'sent_count': message.sent_count,
        'failed_count': message.failed_count
    }
```

---

## 6. 序列化器

### 6.1 模型序列化器

```python
# apps/notifications/serializers.py

from rest_framework import serializers
from apps.common.serializers.base import BaseModelSerializer
from apps.notifications.models import (
    NotificationChannel,
    NotificationTemplate,
    NotificationMessage,
    NotificationLog,
    InAppMessage
)


class NotificationChannelSerializer(BaseModelSerializer):
    """
    通知渠道序列化器

    继承 BaseModelSerializer，自动序列化：
    - id, organization, is_deleted, deleted_at
    - created_at, updated_at, created_by
    - custom_fields
    """
    channel_type_display = serializers.CharField(
        source='get_channel_type_display',
        read_only=True
    )

    class Meta(BaseModelSerializer.Meta):
        model = NotificationChannel
        fields = BaseModelSerializer.Meta.fields + [
            'channel_type',
            'channel_type_display',
            'config',
            'priority',
            'is_enabled',
            'description'
        ]


class NotificationTemplateSerializer(BaseModelSerializer):
    """消息模板序列化器"""
    template_type_display = serializers.CharField(
        source='get_template_type_display',
        read_only=True
    )
    business_category_display = serializers.CharField(
        source='get_business_category_display',
        read_only=True
    )

    class Meta(BaseModelSerializer.Meta):
        model = NotificationTemplate
        fields = BaseModelSerializer.Meta.fields + [
            'code',
            'name',
            'template_type',
            'template_type_display',
            'title',
            'content',
            'url_template',
            'button_text',
            'button_url_template',
            'business_category',
            'business_category_display',
            'remark'
        ]


class NotificationLogSerializer(serializers.ModelSerializer):
    """通知日志序列化器"""
    status_display = serializers.CharField(
        source='get_status_display',
        read_only=True
    )
    channel_display = serializers.SerializerMethodField()

    class Meta:
        model = NotificationLog
        fields = [
            'id',
            'recipient_id',
            'channel',
            'channel_display',
            'status',
            'status_display',
            'external_message_id',
            'error_message',
            'sent_at',
            'delivered_at',
            'read_at'
        ]

    def get_channel_display(self, obj):
        channel_names = {
            'wework': '企业微信',
            'dingtalk': '钉钉',
            'feishu': '飞书',
            'email': '邮件',
            'inapp': '站内信'
        }
        return channel_names.get(obj.channel, obj.channel)


class NotificationMessageSerializer(BaseModelSerializer):
    """通知消息序列化器"""
    status_display = serializers.CharField(
        source='get_status_display',
        read_only=True
    )
    logs = NotificationLogSerializer(
        many=True,
        read_only=True
    )

    class Meta(BaseModelSerializer.Meta):
        model = NotificationMessage
        fields = BaseModelSerializer.Meta.fields + [
            'template',
            'business_type',
            'business_id',
            'title',
            'content',
            'url',
            'button_text',
            'button_url',
            'recipients',
            'status',
            'status_display',
            'sent_count',
            'failed_count',
            'sent_at',
            'error_message',
            'failure_details',
            'logs'
        ]


class InAppMessageSerializer(BaseModelSerializer):
    """站内消息序列化器"""
    message_type_display = serializers.CharField(
        source='get_message_type_display',
        read_only=True
    )

    class Meta(BaseModelSerializer.Meta):
        model = InAppMessage
        fields = BaseModelSerializer.Meta.fields + [
            'user',
            'message_type',
            'message_type_display',
            'title',
            'content',
            'url',
            'button_text',
            'button_url',
            'business_type',
            'business_id',
            'is_read',
            'read_at'
        ]
```

---

## 7. ViewSets

### 7.1 视图集定义

```python
# apps/notifications/viewsets.py

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from apps.common.viewsets.base import BaseModelViewSetWithBatch
from apps.common.filters.base import BaseModelFilter
from apps.notifications.models import (
    NotificationChannel,
    NotificationTemplate,
    NotificationMessage,
    InAppMessage
)
from apps.notifications.serializers import (
    NotificationChannelSerializer,
    NotificationTemplateSerializer,
    NotificationMessageSerializer,
    InAppMessageSerializer
)


class NotificationChannelFilter(BaseModelFilter):
    """通知渠道过滤器"""
    class Meta(BaseModelFilter.Meta):
        model = NotificationChannel
        fields = BaseModelFilter.Meta.fields + [
            'channel_type',
            'is_enabled'
        ]


class NotificationChannelViewSet(BaseModelViewSetWithBatch):
    """
    通知渠道视图集

    继承 BaseModelViewSetWithBatch，自动获得：
    - 标准CRUD操作
    - 组织过滤
    - 软删除
    - 批量操作
    """
    queryset = NotificationChannel.objects.all()
    serializer_class = NotificationChannelSerializer
    filterset_class = NotificationChannelFilter
    permission_classes = [IsAuthenticated]


class NotificationTemplateFilter(BaseModelFilter):
    """消息模板过滤器"""
    class Meta(BaseModelFilter.Meta):
        model = NotificationTemplate
        fields = BaseModelFilter.Meta.fields + [
            'code',
            'business_category'
        ]


class NotificationTemplateViewSet(BaseModelViewSetWithBatch):
    """消息模板视图集"""
    queryset = NotificationTemplate.objects.all()
    serializer_class = NotificationTemplateSerializer
    filterset_class = NotificationTemplateFilter
    permission_classes = [IsAuthenticated]


class NotificationMessageFilter(BaseModelFilter):
    """通知消息过滤器"""
    class Meta(BaseModelFilter.Meta):
        model = NotificationMessage
        fields = BaseModelFilter.Meta.fields + [
            'business_type',
            'status'
        ]


class NotificationMessageViewSet(BaseModelViewSetWithBatch):
    """通知消息视图集（管理员）"""
    queryset = NotificationMessage.objects.all()
    serializer_class = NotificationMessageSerializer
    filterset_class = NotificationMessageFilter
    permission_classes = [IsAuthenticated]


class InAppMessageFilter(BaseModelFilter):
    """站内消息过滤器"""
    class Meta(BaseModelFilter.Meta):
        model = InAppMessage
        fields = BaseModelFilter.Meta.fields + [
            'user',
            'message_type',
            'is_read'
        ]


class InAppMessageViewSet(BaseModelViewSetWithBatch):
    """
    站内消息视图集

    自动过滤当前用户的消息
    """
    serializer_class = InAppMessageSerializer
    filterset_class = InAppMessageFilter
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """只返回当前用户的消息"""
        return InAppMessage.objects.filter(
            user=self.request.user
        ).select_related('user')

    @action(detail=False, methods=['get'])
    def unread_count(self, request):
        """获取未读数量"""
        count = self.get_queryset().filter(is_read=False).count()
        return Response({'count': count})

    @action(detail=True, methods=['post'])
    def mark_read(self, request, pk=None):
        """标记为已读"""
        message = self.get_object()
        message.mark_as_read()
        return Response({'status': 'success'})

    @action(detail=False, methods=['post'])
    def mark_all_read(self, request):
        """全部标记为已读"""
        queryset = self.get_queryset().filter(is_read=False)
        count = queryset.count()
        for msg in queryset:
            msg.mark_as_read()
        return Response({'status': 'success', 'count': count})
```

---

## 8. 使用示例

### 8.1 业务代码中发送通知

```python
# 资产领用单创建后触发通知

from apps.notifications.tasks import send_template_notification_async

def create_asset_pickup(request):
    """创建资产领用单"""
    pickup = AssetPickup.objects.create(...)

    # ✅ 异步发送通知（推荐）
    send_template_notification_async.delay(
        template_code='asset_pickup_created',
        recipients=[{'user_id': str(pickup.approver.id)}],
        params={
            'applicant': pickup.applicant.get_full_name(),
            'department': pickup.department.name,
            'pickup_reason': pickup.pickup_reason,
        },
        org_id=pickup.organization.id
    )

    # ❌ 同步发送（不推荐，会阻塞请求）
    # from apps.notifications.services.notification_service import NotificationService
    # service = NotificationService(pickup.organization)
    # service.send_template(...)

    return pickup
```

### 8.2 使用助手类发送通知

```python
from apps.notifications.services.helpers import AssetNotificationHelper

def approve_asset_pickup(pickup):
    """审批通过领用单"""
    pickup.status = 'approved'
    pickup.save()

    # 发送通知给申请人
    AssetNotificationHelper.notify_pickup_approved(pickup)
```

---

---

## 错误处理机制

### 异常类型
- NetworkException: 网络异常
- APIException: API调用异常
- ValidationException: 数据验证异常
- TemplateException: 模板解析异常
- ChannelException: 渠道发送异常

### 重试策略
- 指数退避重试: 60s -> 120s -> 240s -> 480s
- 最大重试次数: 3次
- 失败告警: 记录IntegrationLog并发送通知

### 错误日志
所有错误记录到IntegrationLog模型，包含：
- request_url: 请求地址
- request_body: 请求体
- response_body: 响应体
- status_code: 状态码
- error_message: 错误信息

---

## 边界条件和异常场景测试

### 1. 消息模板异常测试

```python
# tests/test_notification_templates.py
import pytest
from unittest.mock import Mock, patch
from apps.notifications.models import NotificationTemplate
from apps.notifications.services.notification_service import NotificationService

class NotificationTemplateTest:
    def setUp(self):
        self.organization = self.create_organization()

    def test_template_not_found(self):
        """测试模板不存在的情况"""
        service = NotificationService(self.organization)

        with pytest.raises(NotificationTemplate.DoesNotExist):
            service.send_template(
                template_code='nonexistent_template',
                recipients=[{'user_id': '1'}],
                params={}
            )

    def test_template_variable_parsing(self):
        """测试模板变量解析异常"""
        template = NotificationTemplate.objects.create(
            code='test_template',
            name='测试模板',
            title='Hello {{name}}',
            content='This is a test template with {{nested.object.value}}',
            template_type='text'
        )

        service = NotificationService(self.organization)

        # 测试正常变量解析
        result = service.send_template(
            template_code='test_template',
            recipients=[{'user_id': '1'}],
            params={
                'name': '张三',
                'nested': {'object': {'value': '测试值'}}
            }
        )
        assert result.title == 'Hello 张三'
        assert '测试值' in result.content

        # 测试缺失变量
        result = service.send_template(
            template_code='test_template',
            recipients=[{'user_id': '1'}],
            params={}
        )
        assert result.title == 'Hello '
        assert 'None' not in result.content

    def test_template_syntax_error(self):
        """测试模板语法错误"""
        template = NotificationTemplate.objects.create(
            code='invalid_template',
            name='无效模板',
            title='Hello {{name',
            content='Invalid template syntax',
            template_type='text'
        )

        service = NotificationService(self.organization)

        # 验证是否正确处理模板语法错误
        with patch('apps.notifications.channels.base.NotificationChannelAdapter.parse_template') as mock_parse:
            mock_parse.side_effect = Exception("Template syntax error")

            with pytest.raises(Exception):
                service.send_template(
                    template_code='invalid_template',
                    recipients=[{'user_id': '1'}],
                    params={'name': '张三'}
                )

    def test_template_code_conflict(self):
        """测试模板编码冲突"""
        # 创建第一个模板
        NotificationTemplate.objects.create(
            code='conflict_code',
            name='冲突模板1',
            title='Title 1',
            content='Content 1',
            template_type='text'
        )

        # 尝试创建相同编码的模板应该失败
        with pytest.raises(Exception):
            NotificationTemplate.objects.create(
                code='conflict_code',
                name='冲突模板2',
                title='Title 2',
                content='Content 2',
                template_type='text'
            )

### 2. 通知渠道异常测试

```python
# tests/test_notification_channels.py
import pytest
from unittest.mock import Mock, patch
from apps.notifications.models import NotificationChannel
from apps.notifications.services.notification_service import NotificationService
from apps.notifications.channels.wework_channel import WeWorkNotificationChannel

class NotificationChannelTest:
    def setUp(self):
        self.organization = self.create_organization()
        self.channel = NotificationChannel.objects.create(
            organization=self.organization,
            channel_type='wework',
            config={
                'corp_id': 'test_corp',
                'agent_id': 1000001,
                'agent_secret': 'test_secret'
            },
            is_enabled=True
        )

    def test_channel_not_enabled(self):
        """测试渠道未启用的异常处理"""
        self.channel.is_enabled = False
        self.channel.save()

        service = NotificationService(self.organization)

        with pytest.raises(ValueError) as exc_info:
            service.send(
                business_type='test',
                business_id='123',
                title='测试消息',
                content='测试内容',
                recipients=[{'user_id': '1'}],
                channels=['wework']
            )

        assert '渠道未启用' in str(exc_info.value)

    @patch('requests.get')
    def test_channel_api_error(self, mock_get):
        """测试渠道API调用错误"""
        mock_response = Mock()
        mock_response.json.return_value = {
            'errcode': 40001,
            'errmsg': 'invalid corpid'
        }
        mock_get.return_value = mock_response

        channel_config = {
            'corp_id': 'invalid_corp',
            'agent_id': 1000001,
            'agent_secret': 'test_secret'
        }

        wework_channel = WeWorkNotificationChannel(channel_config)

        with pytest.raises(Exception):
            wework_channel.send_message(
                {
                    'title': '测试',
                    'content': '测试内容'
                },
                [{'user_id': '1'}]
            )

    def test_channel_config_missing(self):
        """测试渠道配置缺失"""
        channel = NotificationChannel.objects.create(
            organization=self.organization,
            channel_type='wework',
            config={},  # 空配置
            is_enabled=True
        )

        service = NotificationService(self.organization)

        with pytest.raises(ValueError):
            service.send(
                business_type='test',
                business_type='123',
                title='测试',
                content='测试',
                recipients=[{'user_id': '1'}],
                channels=['wework']
            )

    def test_channel_registration_failure(self):
        """测试渠道注册失败"""
        # 测试不支持的渠道类型
        service = NotificationService(self.organization)

        with pytest.raises(ValueError) as exc_info:
            service.send(
                business_type='test',
                business_id='123',
                title='测试',
                content='测试',
                recipients=[{'user_id': '1'}],
                channels=['invalid_channel']
            )

        assert '不支持的渠道类型' in str(exc_info.value)

### 3. 接收人映射异常测试

```python
# tests/test_recipient_mapping.py
import pytest
from apps.notifications.services.notification_service import NotificationService
from apps.accounts.models import User
from apps.sso.models import UserMapping

class RecipientMappingTest:
    def setUp(self):
        self.organization = self.create_organization()
        self.user = User.objects.create(
            username='test_user',
            organization=self.organization
        )

    def test_recipient_not_found(self):
        """测试接收人不存在"""
        service = NotificationService(self.organization)

        # 尝试为不存在的用户发送通知
        with pytest.raises(User.DoesNotExist):
            service.send(
                business_type='test',
                business_id='123',
                title='测试',
                content='测试',
                recipients=[{'user_id': '99999999-0000-0000-0000-000000000000'}],
                channels=['inapp']
            )

    def test_wework_user_not_bound(self):
        """测试企业微信用户未绑定"""
        service = NotificationService(self.organization)

        # 尝试发送企业微信消息，但用户未绑定
        with pytest.raises(ValueError) as exc_info:
            service.send(
                business_type='test',
                business_id='123',
                title='测试',
                content='测试',
                recipients=[{'user_id': str(self.user.id)}],
                channels=['wework']
            )

        assert '未绑定企业微信' in str(exc_info.value)

    def test_user_email_missing(self):
        """测试用户邮箱缺失"""
        service = NotificationService(self.organization)

        # 尝试发送邮件，但用户没有邮箱
        with pytest.raises(ValueError) as exc_info:
            service.send(
                business_type='test',
                business_id='123',
                title='测试',
                content='测试',
                recipients=[{'user_id': str(self.user.id)}],
                channels=['email']
            )

        assert '未设置邮箱' in str(exc_info.value)

    def test_recipient_channel_id_invalid(self):
        """测试接收人渠道ID无效"""
        service = NotificationService(self.organization)

        # 提供无效的渠道ID
        with pytest.raises(Exception):
            service.send(
                business_type='test',
                business_id='123',
                title='测试',
                content='测试',
                recipients=[{'user_id': str(self.user.id), 'channel_id': 'invalid_id'}],
                channels=['wework']
            )

### 4. 批量发送异常测试

```python
# tests/test_batch_notification.py
import pytest
from unittest.mock import Mock, patch
from apps.notifications.services.notification_service import NotificationService
from apps.notifications.models import NotificationMessage

class BatchNotificationTest:
    def setUp(self):
        self.organization = self.create_organization()
        # 创建100个用户
        self.users = []
        for i in range(100):
            user = User.objects.create(
                username=f'user_{i}',
                organization=self.organization,
                email=f'user_{i}@test.com'
            )
            self.users.append(user)

    def test_large_recipients_list(self):
        """测试大量接收人列表"""
        service = NotificationService(self.organization)

        # 创建大量接收人
        recipients = [{'user_id': str(user.id)} for user in self.users]

        # 测试发送不会失败
        message = service.send(
            business_type='test',
            business_id='123',
            title='大批量测试',
            content='这是一条测试消息，用于测试大批量发送功能。',
            recipients=recipients,
            channels=['inapp']
        )

        # 验证消息创建成功
        assert message.status == 'success'
        assert message.sent_count == 100

    def test_mixed_recipient_channels(self):
        """测试混合接收人渠道"""
        # 绑定部分用户的企业微信
        from apps.sso.models import UserMapping
        for i in range(50):
            UserMapping.objects.create(
                platform='wework',
                platform_userid=f'ww_user_{i}',
                system_user=self.users[i]
            )

        service = NotificationService(self.organization)

        # 创建部分用户有企业微信，部分没有
        recipients = []
        for i in range(100):
            recipients.append({'user_id': str(self.users[i].id)})

        # 测试多渠道发送
        with patch.object(service, '_send_to_channels') as mock_send:
            mock_send.return_value = [
                {
                    'channel': 'wework',
                    'success': True,
                    'sent_count': 50,
                    'failed_count': 0
                },
                {
                    'channel': 'inapp',
                    'success': True,
                    'sent_count': 100,
                    'failed_count': 0
                }
            ]

            message = service.send(
                business_type='test',
                business_id='123',
                title='多渠道测试',
                content='多渠道发送测试',
                recipients=recipients,
                channels=['wework', 'inapp']
            )

        assert message.status == 'partial_success'

    def test_recipient_limit_exceeded(self):
        """测试接收人数量限制"""
        service = NotificationService(self.organization)

        # 创建超过限制的接收人（假设限制为1000）
        recipients = [{'user_id': str(user.id)} for user in self.users[:1001]]

        # 应该抛出异常
        with pytest.raises(Exception):
            service.send(
                business_type='test',
                business_id='123',
                title='超限测试',
                content='这条消息超过了接收人限制',
                recipients=recipients,
                channels=['inapp']
            )

### 5. Celery任务异常测试

```python
# tests/test_notification_tasks.py
import pytest
from unittest.mock import Mock, patch
from celery.exceptions import Retry
from apps.notifications.tasks import send_notification_async, send_template_notification_async
from apps.notifications.models import NotificationMessage, NotificationTemplate

class NotificationTasksTest:
    def setUp(self):
        self.organization = self.create_organization()
        self.template = NotificationTemplate.objects.create(
            code='test_template',
            name='测试模板',
            title='测试标题',
            content='测试内容',
            template_type='text'
        )

    @patch('apps.notifications.services.notification_service.NotificationService')
    def test_task_retry_mechanism(self, mock_service):
        """测试任务重试机制"""
        # 模拟服务初始化失败
        mock_service.side_effect = ConnectionError("Service unavailable")

        # 验证触发重试
        with pytest.raises(Retry):
            send_notification_async(
                business_type='test',
                business_id='123',
                title='测试',
                content='测试内容',
                recipients=[{'user_id': '1'}],
                org_id=self.organization.id
            )

    @patch('apps.notifications.services.notification_service.NotificationService')
    def test_task_success_case(self, mock_service):
        """测试任务成功执行"""
        # 模拟服务返回成功
        mock_message = Mock()
        mock_message.id = '123'
        mock_message.status = 'success'
        mock_message.sent_count = 1
        mock_message.failed_count = 0
        mock_service.return_value.send.return_value = mock_message

        result = send_notification_async(
            business_type='test',
            business_id='123',
            title='测试',
            content='测试内容',
            recipients=[{'user_id': '1'}],
            org_id=self.organization.id
        )

        assert result['message_id'] == '123'
        assert result['status'] == 'success'

    @patch('apps.notifications.services.notification_service.NotificationService')
    def test_task_partial_success(self, mock_service):
        """测试任务部分成功"""
        # 模拟服务返回部分成功
        mock_message = Mock()
        mock_message.id = '123'
        mock_message.status = 'partial_success'
        mock_message.sent_count = 1
        mock_message.failed_count = 1
        mock_service.return_value.send.return_value = mock_message

        result = send_notification_async(
            business_type='test',
            business_id='123',
            title='测试',
            content='测试内容',
            recipients=[{'user_id': '1'}, {'user_id': '2'}],
            org_id=self.organization.id
        )

        assert result['message_id'] == '123'
        assert result['status'] == 'partial_success'

    @patch('apps.notifications.services.notification_service.NotificationService')
    def test_task_escalation(self, mock_service):
        """测试任务升级（重试次数用完）"""
        # 模拟服务持续失败
        mock_service.side_effect = ConnectionError("Service unavailable")

        # 执行最大重试次数后应该抛出异常
        with pytest.raises(Exception):
            # 模拟多次重试后仍然失败
            for _ in range(4):  # 3次重试 + 1次原始调用
                try:
                    send_notification_async(
                        business_type='test',
                        business_id='123',
                        title='测试',
                        content='测试内容',
                        recipients=[{'user_id': '1'}],
                        org_id=self.organization.id
                    )
                except Retry:
                    continue

### 6. API接口异常测试

```python
# tests/test_notification_api.py
import pytest
from rest_framework.test import APIClient
from rest_framework import status
from django.urls import reverse

class NotificationAPITest:
    def setUp(self):
        self.client = APIClient()
        self.organization = self.create_organization()
        self.user = self.create_user(organization=self.organization)

    def test_api_without_auth(self):
        """测试未认证访问API"""
        response = self.client.get('/api/notifications/channels/')

        assert response.status_code == 401
        assert 'Authentication credentials' in response.data['detail']

    def test_create_channel_without_config(self):
        """测试创建渠道缺少配置"""
        self.client.force_authenticate(user=self.user)

        response = self.client.post('/api/notifications/channels/', {
            'channel_type': 'wework',
            'config': {},  # 空配置
            'is_enabled': True
        }, format='json')

        # 应该返回验证错误
        assert response.status_code == 400

    def test_send_notification_invalid_template(self):
        """测试发送通知使用无效模板"""
        self.client.force_authenticate(user=self.user)

        response = self.client.post('/api/notifications/messages/send-template/', {
            'template_code': 'invalid_template',
            'recipients': [{'user_id': str(self.user.id)}],
            'params': {}
        }, format='json')

        assert response.status_code == 404

    def test_inapp_message_permissions(self):
        """测试站内消息权限"""
        # 创建另一个组织的用户
        other_user = self.create_user(organization=self.create_organization(name="Other Org"))

        # 创建站内消息
        message = self.create_inapp_message(user=self.user)

        # 另一个组织的用户应该看不到
        self.client.force_authenticate(user=other_user)
        response = self.client.get(f'/api/notifications/inapp-messages/{message.id}/')

        assert response.status_code == 404

    def test_channel_type_validation(self):
        """测试渠道类型验证"""
        self.client.force_authenticate(user=self.user)

        response = self.client.post('/api/notifications/channels/', {
            'channel_type': 'invalid_channel',  # 无效的渠道类型
            'config': {'test': 'value'},
            'is_enabled': True
        }, format='json')

        assert response.status_code == 400
        assert 'channel_type' in response.data

    def test_message_recipient_validation(self):
        """测试接收人格式验证"""
        self.client.force_authenticate(user=self.user)

        response = self.client.post('/api/notifications/messages/send/', {
            'business_type': 'test',
            'business_id': '123',
            'title': '测试',
            'content': '测试内容',
            'recipients': [{}],  # 缺少user_id
            'channels': ['inapp']
        }, format='json')

        assert response.status_code == 400
        assert 'recipients' in response.data

    def test_batch_operations_mixed_results(self):
        """测试批量操作混合结果"""
        # 创建多个渠道
        channels = []
        for i in range(3):
            channel = self.create_notification_channel(
                organization=self.organization,
                channel_type='inapp',
                is_enabled=True
            )
            channels.append(channel)

        # 批量删除部分有效的部分无效的
        self.client.force_authenticate(user=self.user)

        response = self.client.post('/api/notifications/channels/batch-delete/', {
            'ids': [str(channels[0].id), str(channels[1].id), 'invalid-id']
        }, format='json')

        assert response.status_code == 200
        data = response.json()
        assert data['summary']['total'] == 3
        assert data['summary']['succeeded'] == 2
        assert data['summary']['failed'] == 1
```

---

## 9. 后续集成任务

1. **Phase 3.1**: 集成LogicFlow流程设计器，支持可视化审批流程配置
2. **Phase 3.2**: 实现工作流执行引擎，审批节点触发通知
3. **Phase 4.3**: 盘点任务分配时触发通知提醒
4. **Phase 5.4**: 报表生成完成后邮件通知

---

## 10. 核心规范总结

### 10.1 必须遵守的规则

1. ✅ **所有模型必须继承 BaseModel**
   ```python
   class NotificationChannel(BaseModel):  # ✅ 正确
   class NotificationChannel(models.Model):  # ❌ 错误
   ```

2. ✅ **所有序列化器必须继承 BaseModelSerializer**
   ```python
   class NotificationChannelSerializer(BaseModelSerializer):  # ✅ 正确
   ```

3. ✅ **所有视图集必须继承 BaseModelViewSetWithBatch**
   ```python
   class NotificationChannelViewSet(BaseModelViewSetWithBatch):  # ✅ 正确
   ```

4. ✅ **所有通知发送必须使用Celery异步任务**
   ```python
   send_template_notification_async.delay(...)  # ✅ 正确
   service.send_template(...)  # ❌ 错误（阻塞主线程）
   ```

5. ✅ **多组织数据隔离由BaseModel自动处理**
   ```python
   # 自动添加 organization 过滤
   channels = NotificationChannel.objects.all()
   # 自动转换为：
   # WHERE organization_id = <当前用户组织ID> AND is_deleted = False
   ```

### 10.2 错误处理规范

统一使用标准错误码：

```python
from apps.common.responses import ErrorResponse

# 渠道未启用
return ErrorResponse(
    error_code='CHANNEL_NOT_ENABLED',
    message='企业微信渠道未启用',
    details={'channel': 'wework'}
)

# 模板不存在
return ErrorResponse(
    error_code='TEMPLATE_NOT_FOUND',
    message=f'模板 {template_code} 不存在',
    details={'template_code': template_code}
)

---

## 11. API 规范

### 11.1 统一响应格式

#### 成功响应格式
```json
{
    "success": true,
    "message": "操作成功",
    "data": {
        "id": "550e8400-e29b-41d4-a716-446655440000",
        "channel_type": "wework",
        "channel_type_display": "企业微信",
        "config": {
            "corp_id": "wxCorpId",
            "agent_id": 1000001,
            "agent_secret": "secret"
        },
        "priority": 0,
        "is_enabled": true,
        "description": "企业微信通知渠道",
        "created_at": "2024-01-15T10:30:00Z",
        "updated_at": "2024-01-15T10:35:00Z",
        "created_by": "550e8400-e29b-41d4-a716-446655440000",
        "organization": "550e8400-e29b-41d4-a716-446655440000"
    }
}
```

#### 列表响应格式（分页）
```json
{
    "success": true,
    "data": {
        "count": 100,
        "next": "https://api.example.com/api/notifications/channels/?page=2",
        "previous": null,
        "results": [
            {
                "id": "550e8400-e29b-41d4-a716-446655440000",
                "channel_type": "wework",
                "channel_type_display": "企业微信",
                "priority": 0,
                "is_enabled": true,
                "created_at": "2024-01-15T10:30:00Z",
                "updated_at": "2024-01-15T10:35:00Z"
            }
        ]
    }
}
```

#### 错误响应格式
```json
{
    "success": false,
    "error": {
        "code": "VALIDATION_ERROR",
        "message": "请求数据验证失败",
        "details": {
            "channel_type": ["该字段不能为空"]
        }
    }
}
```

### 11.2 标准CRUD接口

| 接口 | 方法 | 路径 | 说明 |
|------|------|------|------|
| **通知渠道列表** | GET | `/api/notifications/channels/` | 分页查询通知渠道，支持过滤和搜索 |
| **通知渠道详情** | GET | `/api/notifications/channels/{id}/` | 获取单个通知渠道详情信息 |
| **创建通知渠道** | POST | `/api/notifications/channels/` | 创建新的通知渠道 |
| **更新通知渠道** | PUT | `/api/notifications/channels/{id}/` | 完整更新通知渠道信息 |
| **部分更新通知渠道** | PATCH | `/api/notifications/channels/{id}/` | 部分更新通知渠道信息 |
| **软删除通知渠道** | DELETE | `/api/notifications/channels/{id}/` | 软删除通知渠道 |
| **通知渠道列表（已删除）** | GET | `/api/notifications/channels/deleted/` | 查看已删除的通知渠道 |
| **恢复通知渠道** | POST | `/api/notifications/channels/{id}/restore/` | 恢复已删除的通知渠道 |

### 11.3 批量操作接口

| 接口 | 方法 | 路径 | 说明 |
|------|------|------|------|
| **批量软删除通知渠道** | POST | `/api/notifications/channels/batch-delete/` | 批量软删除通知渠道 |
| **批量恢复通知渠道** | POST | `/api/notifications/channels/batch-restore/` | 批量恢复通知渠道 |
| **批量更新通知渠道** | POST | `/api/notifications/channels/batch-update/` | 批量更新通知渠道信息 |

#### 批量删除请求示例
```http
POST /api/notifications/channels/batch-delete/
{
    "ids": [
        "550e8400-e29b-41d4-a716-446655440000",
        "550e8400-e29b-41d4-a716-446655440001"
    ]
}
```

### 11.4 通知模板管理接口

| 接口 | 方法 | 路径 | 说明 |
|------|------|------|------|
| **模板列表** | GET | `/api/notifications/templates/` | 分页查询通知模板 |
| **模板详情** | GET | `/api/notifications/templates/{id}/` | 获取单个模板详情 |
| **创建模板** | POST | `/api/notifications/templates/` | 创建新的通知模板 |
| **更新模板** | PUT | `/api/notifications/templates/{id}/` | 完整更新模板 |
| **部分更新模板** | PATCH | `/api/notifications/templates/{id}/` | 部分更新模板 |
| **软删除模板** | DELETE | `/api/notifications/templates/{id}/` | 软删除模板 |
| **模板预览** | POST | `/api/notifications/templates/{id}/preview/` | 预览模板渲染效果 |
| **测试模板** | POST | `/api/notifications/templates/{id}/test/` | 测试模板发送 |

### 11.5 通知消息管理接口

| 接口 | 方法 | 路径 | 说明 |
|------|------|------|------|
| **消息列表** | GET | `/api/notifications/messages/` | 分页查询通知消息 |
| **消息详情** | GET | `/api/notifications/messages/{id}/` | 获取单个消息详情 |
| **创建消息** | POST | `/api/notifications/messages/` | 创建新的通知消息 |
| **更新消息** | PUT | `/api/notifications/messages/{id}/` | 完整更新消息 |
| **部分更新消息** | PATCH | `/api/notifications/messages/{id}/` | 部分更新消息 |
| **软删除消息** | DELETE | `/api/notifications/messages/{id}/` | 软删除消息 |
| **发送模板消息** | POST | `/api/notifications/messages/send-template/` | 发送模板消息 |
| **直接发送消息** | POST | `/api/notifications/messages/send/` | 直接发送消息 |
| **消息发送重试** | POST | `/api/notifications/messages/{id}/retry/` | 重试发送失败的消息 |

#### 发送模板消息请求示例
```http
POST /api/notifications/messages/send-template/
Content-Type: application/json

{
    "template_code": "asset_pickup_created",
    "recipients": [
        {
            "user_id": "550e8400-e29b-41d4-a716-446655440000"
        }
    ],
    "params": {
        "applicant": "张三",
        "department": "技术部",
        "pickup_no": "PU20240115001"
    },
    "channels": ["wework", "inapp"]
}
```

#### 发送模板消息响应示例
```json
{
    "success": true,
    "message": "消息发送成功",
    "data": {
        "id": "550e8400-e29b-41d4-a716-446655440000",
        "status": "success",
        "template": "550e8400-e29b-41d4-a716-446655440000",
        "title": "待审批: 资产领用申请",
        "content": "张三提交了资产领用申请，请审批",
        "sent_count": 1,
        "failed_count": 0,
        "sent_at": "2024-01-15T10:35:00Z"
    }
}
```

### 11.6 站内信管理接口

| 接口 | 方法 | 路径 | 说明 |
|------|------|------|------|
| **站内信列表** | GET | `/api/notifications/inapp-messages/` | 分页查询当前用户的站内信 |
| **站内信详情** | GET | `/api/notifications/inapp-messages/{id}/` | 获取单条站内信详情 |
| **站内信未读数量** | GET | `/api/notifications/inapp-messages/unread-count/` | 获取当前用户未读消息数量 |
| **标记已读** | POST | `/api/notifications/inapp-messages/{id}/mark-read/` | 标记单条消息为已读 |
| **全部标记已读** | POST | `/api/notifications/inapp-messages/mark-all-read/` | 标记所有消息为已读 |

### 11.7 通知日志查询接口

| 接口 | 方法 | 路径 | 说明 |
|------|------|------|------|
| **发送日志列表** | GET | `/api/notifications/logs/` | 分页查询通知发送日志 |
| **发送日志详情** | GET | `/api/notifications/logs/{id}/` | 获取单条发送日志详情 |
| **按消息查询日志** | GET | `/api/notifications/logs/message/{message_id}/` | 查询指定消息的所有发送日志 |
| **按接收人查询日志** | GET | `/api/notifications/logs/recipient/{user_id}/` | 查询指定接收人的所有发送日志 |

### 11.8 业务通知接口

| 接口 | 方法 | 路径 | 说明 |
|------|------|------|------|
| **资产领用通知** | POST | `/api/notifications/asset/pickup-created/` | 资产领用创建通知 |
| **资产审批通知** | POST | `/api/notifications/asset/approval/` | 资产审批结果通知 |
| **库存预警通知** | POST | `/api/notifications/inventory/low-stock/` | 库存低预警通知 |
| **盘点任务通知** | POST | `/api/notifications/inventory/task-assigned/` | 盘点任务分配通知 |
| **系统通知** | POST | `/api/notifications/system/announcement/` | 系统公告通知 |

### 11.9 批量操作接口

| 接口 | 方法 | 路径 | 说明 |
|------|------|------|------|
| **批量软删除通知模板** | POST | `/api/notifications/templates/batch-delete/` | 批量软删除通知模板 |
| **批量恢复通知模板** | POST | `/api/notifications/templates/batch-restore/` | 批量恢复通知模板 |
| **批量更新通知模板** | POST | `/api/notifications/templates/batch-update/` | 批量更新通知模板 |
| **批量软删除通知消息** | POST | `/api/notifications/messages/batch-delete/` | 批量软删除通知消息 |
| **批量恢复通知消息** | POST | `/api/notifications/messages/batch-restore/` | 批量恢复通知消息 |

### 11.10 标准错误码

| 错误码 | HTTP状态 | 描述 |
|--------|----------|------|
| `VALIDATION_ERROR` | 400 | 请求数据验证失败 |
| `UNAUTHORIZED` | 401 | 未认证访问 |
| `PERMISSION_DENIED` | 403 | 权限不足 |
| `NOT_FOUND` | 404 | 资源不存在 |
| `METHOD_NOT_ALLOWED` | 405 | 方法不被允许 |
| `CONFLICT` | 409 | 资源冲突 |
| `ORGANIZATION_MISMATCH` | 403 | 组织不匹配 |
| `SOFT_DELETED` | 410 | 资源已被软删除 |
| `RATE_LIMIT_EXCEEDED` | 429 | 请求频率超限 |
| `SERVER_ERROR` | 500 | 服务器内部错误 |
| `TEMPLATE_NOT_FOUND` | 404 | 通知模板不存在 |
| `CHANNEL_NOT_ENABLED` | 400 | 通知渠道未启用 |
| `RECIPIENT_NOT_FOUND` | 404 | 接收人不存在 |
| `TEMPLATE_RENDER_ERROR` | 400 | 模板渲染错误 |
| `CHANNEL_CONFIG_INVALID` | 400 | 渠道配置无效 |

### 11.11 扩展接口示例

#### 11.11.1 多渠道消息发送
```python
# 客户端发送多渠道消息的示例
import requests

# 发送消息到多个渠道
response = requests.post('/api/notifications/messages/send/',
                        json={
                            'business_type': 'asset_pickup',
                            'business_id': '123',
                            'title': '待审批: 资产领用',
                            'content': '张三申请领用笔记本电脑一台',
                            'recipients': [
                                {'user_id': 'user1', 'channel_id': 'ww_user1'},
                                {'user_id': 'user2'},
                                {'user_id': 'user3', 'channel_id': 'user3@example.com'}
                            ],
                            'channels': ['wework', 'email', 'inapp'],
                            'url': '/approvals/123',
                            'button_text': '立即审批',
                            'button_url': '/approvals/123'
                        },
                        headers={'Authorization': 'Bearer token'})

print(response.json())
```

#### 11.11.2 模板变量测试
```python
# 测试模板变量渲染的示例
response = requests.post('/api/notifications/templates/1/test/',
                        json={
                            'params': {
                                'applicant': '张三',
                                'department': '技术部',
                                'asset': {
                                    'name': 'ThinkPad X1',
                                    'code': 'TP001',
                                    'price': 8999
                                },
                                'approvals': ['李四', '王五']
                            }
                        },
                        headers={'Authorization': 'Bearer token'})

result = response.json()
print("渲染后的标题:", result['data']['title'])
print("渲染后的内容:", result['data']['content'])
```

#### 11.11.3 批量消息发送
```python
# 批量发送消息的示例
import requests
import uuid

# 生成批量接收人
recipients = []
for i in range(50):
    recipients.append({
        'user_id': str(uuid.uuid4()),
        'channel_id': f'channel_{i}'
    })

response = requests.post('/api/notifications/messages/send/',
                        json={
                            'business_type': 'system_announcement',
                            'business_id': 'ann001',
                            'title': '系统维护通知',
                            'content': '系统将于本周六凌晨2点进行维护，预计持续2小时。',
                            'recipients': recipients,
                            'channels': ['inapp']
                        },
                        headers={'Authorization': 'Bearer token'})

result = response.json()
print(f"发送结果: 成功{result['data']['sent_count']}条，失败{result['data']['failed_count']}条")
```

#### 11.11.4 通知状态查询
```python
# 查询通知发送状态的示例
import requests

# 查询消息发送状态
response = requests.get('/api/notifications/messages/123/',
                       headers={'Authorization': 'Bearer token'})

message = response.json()['data']
print(f"消息状态: {message['status']}")
print(f"发送成功: {message['sent_count']}人")
print(f"发送失败: {message['failed_count']}人")

# 查看详细发送日志
logs_response = requests.get('/api/notifications/logs/message/123/',
                           headers={'Authorization': 'Bearer token'})
logs = logs_response.json()['data']['results']

for log in logs:
    print(f"用户 {log['recipient_id']}: {log['channel']} - {log['status']}")
```

### 11.12 权限和安全

#### 11.12.1 权限要求
- 所有通知API需要认证
- 普通用户只能查看自己接收的站内信
- 管理员可以管理通知渠道、模板和消息
- 组织管理员只能管理自己组织的通知配置

#### 11.12.2 安全措施
- 敏感数据（如企业微信secret）加密存储
- 所有API调用记录到IntegrationLog
- 接收人信息脱敏显示
- 实现消息发送频率限制

#### 11.12.3 速率限制
- 创建通知渠道：每小时最多20次
- 发送消息：每分钟最多100次
- 模板查询：每秒最多10次
- 批量操作：每天最多1000次

### 11.13 WebSocket实时推送

#### 11.13.1 站内信实时推送
```javascript
// 前端WebSocket连接示例
const socket = new WebSocket('wss://api.example.com/ws/notifications/');

socket.onmessage = function(event) {
    const data = JSON.parse(event.data);

    if (data.type === 'new_message') {
        // 显示新消息通知
        showNotification(data.message);
        updateUnreadCount(data.unread_count);
    }

    if (data.type === 'message_read') {
        // 更新消息已读状态
        updateMessageStatus(data.message_id, 'read');
    }
};

// 发送已读确认
function markMessageRead(messageId) {
    socket.send(JSON.stringify({
        type: 'mark_read',
        message_id: messageId
    }));
}
```

#### 11.13.2 推送消息格式
```json
{
    "type": "new_message",
    "message": {
        "id": "550e8400-e29b-41d4-a716-446655440000",
        "title": "新消息通知",
        "content": "您有一条新的待办事项",
        "url": "/tasks/123",
        "is_read": false,
        "created_at": "2024-01-15T10:30:00Z"
    },
    "unread_count": 5
}
```
```
---

## API接口规范

### 统一响应格式

本模块遵循GZEAMS统一API响应格式规范。

#### 成功响应
```json
{
    "success": true,
    "message": "操作成功",
    "data": {...}
}
```

#### 列表响应
```json
{
    "success": true,
    "data": {
        "count": 100,
        "next": null,
        "previous": null,
        "results": [...]
    }
}
```

#### 错误响应
```json
{
    "success": false,
    "error": {
        "code": "VALIDATION_ERROR",
        "message": "验证失败",
        "details": {...}
    }
}
```

### 标准错误码

| 错误码 | HTTP状态码 | 说明 |
|--------|-----------|------|
| VALIDATION_ERROR | 400 | 验证失败 |
| UNAUTHORIZED | 401 | 未授权 |
| PERMISSION_DENIED | 403 | 权限不足 |
| NOT_FOUND | 404 | 不存在 |
| ORGANIZATION_MISMATCH | 403 | 组织不匹配 |
| SOFT_DELETED | 410 | 已删除 |
| SERVER_ERROR | 500 | 服务器错误 |