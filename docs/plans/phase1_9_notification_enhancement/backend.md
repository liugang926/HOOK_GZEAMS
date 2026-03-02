## 公共模型引用

> 本模块所有后端组件必须继承以下公共基类

| 组件类型 | 基类 | 引用路径 | 自动获得功能 |
|---------|------|---------|-------------|
| **Model** | `BaseModel` | `apps.common.models.BaseModel` | 组织隔离、软删除、审计字段、custom_fields |
| **Serializer** | `BaseModelSerializer` | `apps.common.serializers.base.BaseModelSerializer` | 公共字段序列化、custom_fields序列化 |
| **ViewSet** | `BaseModelViewSetWithBatch` | `apps.common.viewsets.base.BaseModelViewSetWithBatch` | 组织过滤、软删除、批量操作 |
| **Filter** | `BaseModelFilter` | `apps.common.filters.base.BaseModelFilter` | 时间范围过滤、用户过滤 |
| **Service** | `BaseCRUDService` | `apps.common.services.base_crud.BaseCRUDService` | 统一CRUD方法 |

---

# Phase 1.9: 统一通知机制 - 后端实现

> **注意**: 本文档中的所有序列化器、ViewSet、Service 和 Filter 均使用公共基类实现。

## 1. 数据模型设计

### 1.1 通知模板

```python
# apps/notifications/models.py

from django.db import models
from django.conf import settings
from apps.common.models import BaseModel


class NotificationTemplate(BaseModel):
    """
    通知模板
    定义各类通知的内容模板
    """
    CHANNEL_TYPES = [
        ('inbox', '站内信'),
        ('email', '邮件'),
        ('sms', '短信'),
        ('wework', '企业微信'),
        ('dingtalk', '钉钉'),
        ('feishu', '飞书'),
    ]

    # 基本信息
    template_code = models.CharField(
        max_length=50,
        unique=True,
        db_index=True,
        verbose_name='模板代码'
    )
    template_name = models.CharField(max_length=100, verbose_name='模板名称')
    template_type = models.CharField(
        max_length=50,
        verbose_name='通知类型',
        help_text='如: workflow_approval, inventory_assigned'
    )
    channel = models.CharField(
        max_length=20,
        choices=CHANNEL_TYPES,
        verbose_name='发送渠道'
    )

    # 模板内容
    subject_template = models.TextField(
        blank=True,
        verbose_name='标题模板',
        help_text='支持Jinja2语法'
    )
    content_template = models.TextField(
        verbose_name='内容模板',
        help_text='支持Jinja2语法'
    )

    # 模板变量定义 (JSON格式)
    variables = models.JSONField(
        default=dict,
        verbose_name='变量定义',
        help_text='定义模板中可用的变量及其默认值'
    )

    # 模板配置
    language = models.CharField(
        max_length=10,
        default='zh-CN',
        verbose_name='语言'
    )
    is_active = models.BooleanField(default=True, verbose_name='是否启用')
    is_system = models.BooleanField(default=False, verbose_name='系统模板')

    # 版本控制
    version = models.IntegerField(default=1, verbose_name='版本号')
    previous_version = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='next_versions',
        verbose_name='上一版本'
    )

    # 备注
    description = models.TextField(blank=True, verbose_name='说明')
    example_data = models.JSONField(
        null=True, blank=True,
        verbose_name='示例数据',
        help_text='用于预览模板效果'
    )

    class Meta:
        db_table = 'notification_template'
        verbose_name = '通知模板'
        verbose_name_plural = '通知模板'
        ordering = ['template_type', 'channel']
        indexes = [
            models.Index(fields=['template_code']),
            models.Index(fields=['template_type', 'channel']),
            models.Index(fields=['is_active']),
        ]

    def __str__(self):
        return f"{self.template_name} ({self.channel})"

    def render(self, context: dict) -> dict:
        """渲染模板"""
        from jinja2 import Template

        subject = ''
        content = ''

        if self.subject_template:
            subject = Template(self.subject_template).render(**context)

        if self.content_template:
            content = Template(self.content_template).render(**context)

        return {'subject': subject, 'content': content}

    def save_new_version(self):
        """保存新版本"""
        if self.pk:
            self.pk = None
            self.version = self.__class__.objects.filter(
                template_code=self.template_code
            ).count() + 1
            self.is_active = False  # 新版本默认不启用
        self.save()
```

### 1.2 通知记录

```python
class Notification(BaseModel):
    """
    通知记录
    记录发送给用户的通知
    """
    PRIORITIES = [
        ('urgent', '紧急'),
        ('high', '重要'),
        ('normal', '普通'),
        ('low', '低'),
    ]
    STATUSES = [
        ('pending', '待发送'),
        ('sending', '发送中'),
        ('success', '成功'),
        ('failed', '失败'),
        ('cancelled', '已取消'),
    ]

    # 接收人
    recipient = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='notifications',
        verbose_name='接收人'
    )

    # 模板
    template = models.ForeignKey(
        NotificationTemplate,
        on_delete=models.SET_NULL,
        null=True,
        related_name='notifications',
        verbose_name='使用的模板'
    )

    # 通知信息
    notification_type = models.CharField(
        max_length=50,
        db_index=True,
        verbose_name='通知类型'
    )
    priority = models.CharField(
        max_length=20,
        choices=PRIORITIES,
        default='normal',
        verbose_name='优先级'
    )
    channel = models.CharField(
        max_length=20,
        choices=NotificationTemplate.CHANNEL_TYPES,
        verbose_name='发送渠道'
    )

    # 内容
    title = models.CharField(max_length=200, verbose_name='标题')
    content = models.TextField(verbose_name='内容')
    data = models.JSONField(
        default=dict,
        verbose_name='附加数据',
        help_text='链接、跳转信息等'
    )

    # 发送状态
    status = models.CharField(
        max_length=20,
        choices=STATUSES,
        default='pending',
        verbose_name='状态'
    )

    # 发送时间
    scheduled_at = models.DateTimeField(
        null=True, blank=True,
        verbose_name='计划发送时间'
    )
    sent_at = models.DateTimeField(
        null=True, blank=True,
        verbose_name='实际发送时间'
    )

    # 阅读状态 (仅站内信)
    read_at = models.DateTimeField(
        null=True, blank=True,
        verbose_name='阅读时间'
    )

    # 重试信息
    retry_count = models.IntegerField(default=0, verbose_name='重试次数')
    max_retries = models.IntegerField(default=3, verbose_name='最大重试次数')
    next_retry_at = models.DateTimeField(
        null=True, blank=True,
        verbose_name='下次重试时间'
    )

    # 关联对象 (可选)
    related_content_type = models.ForeignKey(
        'contenttypes.ContentType',
        on_delete=models.CASCADE,
        null=True, blank=True,
        verbose_name='关联对象类型'
    )
    related_object_id = models.PositiveIntegerField(
        null=True, blank=True,
        verbose_name='关联对象ID'
    )

    # 发送者 (可选)
    sender = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='sent_notifications',
        verbose_name='发送者'
    )

    class Meta:
        db_table = 'notification'
        verbose_name = '通知'
        verbose_name_plural = '通知'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['recipient', '-created_at']),
            models.Index(fields=['status', 'next_retry_at']),
            models.Index(fields=['notification_type']),
            models.Index(fields=['priority', 'status']),
        ]

    def __str__(self):
        return f"{self.recipient.username} - {self.title}"

    def mark_as_read(self):
        """标记为已读"""
        if not self.read_at:
            from django.utils import timezone
            self.read_at = timezone.now()
            self.save(update_fields=['read_at'])

    def mark_as_unread(self):
        """标记为未读"""
        self.read_at = None
        self.save(update_fields=['read_at'])
```

### 1.3 通知日志

```python
class NotificationLog(BaseModel):
    """
    通知发送日志
    记录每次发送尝试的详细信息
    """
    # 关联通知
    notification = models.ForeignKey(
        Notification,
        on_delete=models.CASCADE,
        related_name='logs',
        verbose_name='通知'
    )

    # 发送信息
    channel = models.CharField(
        max_length=20,
        verbose_name='发送渠道'
    )
    status = models.CharField(
        max_length=20,
        verbose_name='状态'
    )

    # 请求和响应
    request_data = models.JSONField(
        null=True, blank=True,
        verbose_name='请求数据'
    )
    response_data = models.JSONField(
        null=True, blank=True,
        verbose_name='响应数据'
    )

    # 错误信息
    error_code = models.CharField(
        max_length=50,
        blank=True,
        verbose_name='错误码'
    )
    error_message = models.TextField(
        blank=True,
        verbose_name='错误信息'
    )

    # 执行信息
    retry_count = models.IntegerField(default=0, verbose_name='第N次尝试')
    duration = models.IntegerField(
        null=True, blank=True,
        verbose_name='耗时(毫秒)'
    )

    # 渠道返回的信息
    external_id = models.CharField(
        max_length=200,
        blank=True,
        verbose_name='外部ID',
        help_text='如邮件ID、短信ID等'
    )
    external_status = models.CharField(
        max_length=50,
        blank=True,
        verbose_name='外部状态'
    )

    class Meta:
        db_table = 'notification_log'
        verbose_name = '通知日志'
        verbose_name_plural = '通知日志'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['notification', '-created_at']),
            models.Index(fields=['status']),
        ]

    def __str__(self):
        return f"{self.notification} - {self.status}"
```

### 1.4 通知配置

```python
class NotificationConfig(BaseModel):
    """
    用户通知配置
    用户自定义通知接收偏好
    """
    # 关联用户
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='notification_config',
        verbose_name='用户'
    )

    # 渠道开关配置 (JSON格式)
    # {'workflow_approval': {'inbox': true, 'email': false, 'sms': false}}
    channel_settings = models.JSONField(
        default=dict,
        verbose_name='渠道设置'
    )

    # 全局开关
    enable_inbox = models.BooleanField(default=True, verbose_name='启用站内信')
    enable_email = models.BooleanField(default=True, verbose_name='启用邮件')
    enable_sms = models.BooleanField(default=False, verbose_name='启用短信')
    enable_wework = models.BooleanField(default=True, verbose_name='启用企业微信')
    enable_dingtalk = models.BooleanField(default=False, verbose_name='启用钉钉')

    # 免打扰时段
    quiet_hours_enabled = models.BooleanField(
        default=False,
        verbose_name='启用免打扰'
    )
    quiet_hours_start = models.TimeField(
        null=True, blank=True,
        verbose_name='免打扰开始时间'
    )
    quiet_hours_end = models.TimeField(
        null=True, blank=True,
        verbose_name='免打扰结束时间'
    )

    # 邮件设置
    email_address = models.EmailField(
        blank=True,
        verbose_name='接收邮箱',
        help_text='留空则使用用户默认邮箱'
    )

    # 短信设置
    phone_number = models.CharField(
        max_length=20,
        blank=True,
        verbose_name='接收手机号',
        help_text='留空则使用用户默认手机号'
    )

    class Meta:
        db_table = 'notification_config'
        verbose_name = '通知配置'
        verbose_name_plural = '通知配置'

    def __str__(self):
        return f"{self.user.username} 的通知配置"

    def is_channel_enabled(self, notification_type: str, channel: str) -> bool:
        """检查某类型通知的某渠道是否启用"""
        # 检查全局开关
        global_enable = getattr(self, f'enable_{channel}', True)
        if not global_enable:
            return False

        # 检查类型级别配置
        type_config = self.channel_settings.get(notification_type, {})
        return type_config.get(channel, True)

    def is_in_quiet_hours(self) -> bool:
        """检查是否在免打扰时段"""
        if not self.quiet_hours_enabled:
            return False

        from django.utils import timezone
        now = timezone.now().time()

        if self.quiet_hours_start and self.quiet_hours_end:
            if self.quiet_hours_start <= self.quiet_hours_end:
                return self.quiet_hours_start <= now <= self.quiet_hours_end
            else:  # 跨天情况
                return now >= self.quiet_hours_start or now <= self.quiet_hours_end

        return False
```

---

## 2. 序列化器

### 2.1 通知模板序列化器

```python
# apps/notifications/serializers.py

from rest_framework import serializers
from apps.common.serializers.base import BaseModelSerializer, BaseModelWithAuditSerializer
from apps.notifications.models import NotificationTemplate, Notification, NotificationLog, NotificationConfig


class NotificationTemplateSerializer(BaseModelSerializer):
    """通知模板序列化器"""

    class Meta(BaseModelSerializer.Meta):
        model = NotificationTemplate
        fields = BaseModelSerializer.Meta.fields + [
            'template_code', 'template_name', 'template_type', 'channel',
            'subject_template', 'content_template', 'variables',
            'language', 'is_active', 'is_system', 'version',
            'previous_version', 'description', 'example_data'
        ]


class NotificationTemplateDetailSerializer(BaseModelWithAuditSerializer):
    """通知模板详情序列化器 - 包含完整审计信息"""

    previous_version_detail = NotificationTemplateSerializer(
        source='previous_version',
        read_only=True,
        allow_null=True
    )

    class Meta(BaseModelWithAuditSerializer.Meta):
        model = NotificationTemplate
        fields = BaseModelWithAuditSerializer.Meta.fields + [
            'template_code', 'template_name', 'template_type', 'channel',
            'subject_template', 'content_template', 'variables',
            'language', 'is_active', 'is_system', 'version',
            'previous_version', 'previous_version_detail',
            'description', 'example_data'
        ]


class NotificationSerializer(BaseModelSerializer):
    """通知序列化器"""

    recipient_name = serializers.CharField(
        source='recipient.username',
        read_only=True
    )
    template_name = serializers.CharField(
        source='template.template_name',
        read_only=True,
        allow_null=True
    )
    sender_name = serializers.CharField(
        source='sender.username',
        read_only=True,
        allow_null=True
    )

    class Meta(BaseModelSerializer.Meta):
        model = Notification
        fields = BaseModelSerializer.Meta.fields + [
            'recipient', 'recipient_name', 'template', 'template_name',
            'notification_type', 'priority', 'channel',
            'title', 'content', 'data', 'status',
            'scheduled_at', 'sent_at', 'read_at',
            'retry_count', 'max_retries', 'next_retry_at',
            'related_content_type', 'related_object_id',
            'sender', 'sender_name'
        ]


class NotificationListSerializer(BaseModelSerializer):
    """通知列表序列化器 - 精简字段"""

    recipient_name = serializers.CharField(
        source='recipient.username',
        read_only=True
    )

    class Meta(BaseModelSerializer.Meta):
        model = Notification
        fields = BaseModelSerializer.Meta.fields + [
            'recipient', 'recipient_name', 'notification_type',
            'priority', 'channel', 'title', 'status',
            'read_at', 'scheduled_at', 'sent_at'
        ]


class NotificationLogSerializer(BaseModelSerializer):
    """通知日志序列化器"""

    class Meta(BaseModelSerializer.Meta):
        model = NotificationLog
        fields = BaseModelSerializer.Meta.fields + [
            'notification', 'channel', 'status',
            'request_data', 'response_data',
            'error_code', 'error_message',
            'retry_count', 'duration',
            'external_id', 'external_status'
        ]


class NotificationConfigSerializer(BaseModelSerializer):
    """通知配置序列化器"""

    user_name = serializers.CharField(
        source='user.username',
        read_only=True
    )

    class Meta(BaseModelSerializer.Meta):
        model = NotificationConfig
        fields = BaseModelSerializer.Meta.fields + [
            'user', 'user_name', 'channel_settings',
            'enable_inbox', 'enable_email', 'enable_sms',
            'enable_wework', 'enable_dingtalk',
            'quiet_hours_enabled', 'quiet_hours_start',
            'quiet_hours_end', 'email_address', 'phone_number'
        ]


class NotificationConfigUpdateSerializer(serializers.Serializer):
    """通知配置更新序列化器"""

    channel_settings = serializers.JSONField(required=False)
    enable_inbox = serializers.BooleanField(required=False)
    enable_email = serializers.BooleanField(required=False)
    enable_sms = serializers.BooleanField(required=False)
    enable_wework = serializers.BooleanField(required=False)
    enable_dingtalk = serializers.BooleanField(required=False)
    quiet_hours_enabled = serializers.BooleanField(required=False)
    quiet_hours_start = serializers.TimeField(required=False, allow_null=True)
    quiet_hours_end = serializers.TimeField(required=False, allow_null=True)
    email_address = serializers.EmailField(required=False, allow_blank=True)
    phone_number = serializers.CharField(required=False, allow_blank=True, max_length=20)

    def update(self, instance, validated_data):
        """更新配置"""
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        return instance
```

---

## 3. 过滤器

### 3.1 通知过滤器

```python
# apps/notifications/filters.py

from django_filters import rest_framework as filters
from apps.common.filters.base import BaseModelFilter
from apps.notifications.models import Notification, NotificationTemplate


class NotificationFilter(BaseModelFilter):
    """通知过滤器 - 继承公共过滤器"""

    # 业务字段过滤
    notification_type = filters.CharFilter(field_name='notification_type', label='通知类型')
    priority = filters.ChoiceFilter(choices=Notification.PRIORITIES, label='优先级')
    channel = filters.ChoiceFilter(choices=Notification.CHANNEL_TYPES, label='发送渠道')
    status = filters.ChoiceFilter(choices=Notification.STATUSES, label='状态')

    # 时间范围过滤
    scheduled_at = filters.DateFromToRangeFilter(label='计划发送时间')
    sent_at = filters.DateFromToRangeFilter(label='实际发送时间')
    read_at = filters.DateFromToRangeFilter(label='阅读时间')

    # 接收人过滤
    recipient = filters.UUIDFilter(field_name='recipient_id', label='接收人')

    # 是否已读
    is_read = filters.BooleanFilter(
        method='filter_is_read',
        label='是否已读'
    )

    class Meta(BaseModelFilter.Meta):
        model = Notification
        # 继承公共字段 + 业务字段
        fields = BaseModelFilter.Meta.fields + [
            'notification_type', 'priority', 'channel', 'status',
            'scheduled_at', 'sent_at', 'read_at', 'recipient', 'is_read'
        ]

    def filter_is_read(self, queryset, name, value):
        """过滤是否已读"""
        if value is True:
            return queryset.filter(read_at__isnull=False)
        elif value is False:
            return queryset.filter(read_at__isnull=True)
        return queryset


class NotificationTemplateFilter(BaseModelFilter):
    """通知模板过滤器"""

    template_code = filters.CharFilter(lookup_expr='icontains', label='模板代码')
    template_name = filters.CharFilter(lookup_expr='icontains', label='模板名称')
    template_type = filters.CharFilter(field_name='template_type', label='通知类型')
    channel = filters.ChoiceFilter(choices=NotificationTemplate.CHANNEL_TYPES, label='发送渠道')
    is_active = filters.BooleanFilter(label='是否启用')
    is_system = filters.BooleanFilter(label='系统模板')

    class Meta(BaseModelFilter.Meta):
        model = NotificationTemplate
        fields = BaseModelFilter.Meta.fields + [
            'template_code', 'template_name', 'template_type',
            'channel', 'is_active', 'is_system', 'language', 'version'
        ]
```

---

## 4. 视图

### 4.1 通知模板视图

```python
# apps/notifications/views.py

from rest_framework import status
from rest_framework.decorators import action
from rest_framework.response import Response
from apps.common.viewsets.base import BaseModelViewSetWithBatch
from apps.notifications.models import NotificationTemplate, Notification, NotificationConfig
from apps.notifications.serializers import (
    NotificationTemplateSerializer,
    NotificationTemplateDetailSerializer,
    NotificationSerializer,
    NotificationListSerializer,
    NotificationLogSerializer,
    NotificationConfigSerializer,
    NotificationConfigUpdateSerializer
)
from apps.notifications.filters import NotificationFilter, NotificationTemplateFilter
from apps.notifications.services.template_service import TemplateEngine


class NotificationTemplateViewSet(BaseModelViewSetWithBatch):
    """通知模板 ViewSet - 继承公共基类"""

    queryset = NotificationTemplate.objects.all()
    serializer_class = NotificationTemplateSerializer
    filterset_class = NotificationTemplateFilter
    # 自动获得：
    # - 组织隔离
    # - 软删除
    # - 批量删除/恢复/更新
    # - 已删除列表查询

    def get_serializer_class(self):
        """根据操作返回不同的序列化器"""
        if self.action == 'retrieve':
            return NotificationTemplateDetailSerializer
        return NotificationTemplateSerializer

    @action(detail=True, methods=['post'])
    def save_new_version(self, request, pk=None):
        """保存新版本"""
        template = self.get_object()
        new_version = template.save_new_version()

        serializer = self.get_serializer(new_version)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['post'])
    def activate(self, request, pk=None):
        """激活模板"""
        template = self.get_object()

        # 禁用同类型的其他版本
        NotificationTemplate.objects.filter(
            template_code=template.template_code,
            channel=template.channel
        ).update(is_active=False)

        # 激活当前版本
        template.is_active = True
        template.save(update_fields=['is_active'])

        serializer = self.get_serializer(template)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def preview(self, request, pk=None):
        """预览模板"""
        template = self.get_object()
        example_data = request.data.get('example_data', template.example_data or {})

        if not example_data:
            return Response(
                {'detail': '请提供示例数据'},
                status=status.HTTP_400_BAD_REQUEST
            )

        rendered = TemplateEngine.preview_template(template.id, example_data)
        return Response(rendered)


class NotificationViewSet(BaseModelViewSetWithBatch):
    """通知 ViewSet - 继承公共基类"""

    queryset = Notification.objects.select_related(
        'recipient', 'template', 'sender'
    ).all()
    serializer_class = NotificationSerializer
    filterset_class = NotificationFilter
    # 自动获得完整的批量操作能力

    def get_serializer_class(self):
        """根据操作返回不同的序列化器"""
        if self.action == 'list':
            return NotificationListSerializer
        return NotificationSerializer

    @action(detail=True, methods=['post'])
    def mark_as_read(self, request, pk=None):
        """标记为已读"""
        notification = self.get_object()
        notification.mark_as_read()

        serializer = self.get_serializer(notification)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def mark_as_unread(self, request, pk=None):
        """标记为未读"""
        notification = self.get_object()
        notification.mark_as_unread()

        serializer = self.get_serializer(notification)
        return Response(serializer.data)

    @action(detail=False, methods=['post'])
    def batch_mark_read(self, request):
        """批量标记为已读"""
        ids = request.data.get('ids', [])

        if not ids:
            return Response(
                {'detail': '请提供要标记的ID列表'},
                status=status.HTTP_400_BAD_REQUEST
            )

        objects = self._get_batch_objects(ids)
        results = []

        for obj in objects:
            try:
                obj.mark_as_read()
                results.append({
                    'id': str(obj.id),
                    'success': True
                })
            except Exception as e:
                results.append({
                    'id': str(obj.id),
                    'success': False,
                    'error': str(e)
                })

        return self._batch_operation_response(results, '批量标记已读')

    @action(detail=False, methods=['get'])
    def unread_count(self, request):
        """获取未读数量"""
        from django.contrib.contenttypes.models import ContentType

        # 获取当前用户的未读通知数量
        count = self.queryset.filter(
            recipient=request.user,
            read_at__isnull=True
        ).count()

        return Response({'unread_count': count})

    @action(detail=False, methods=['get'])
    def statistics(self, request):
        """获取通知统计"""
        from django.db.models import Count

        stats = self.queryset.values('status').annotate(
            count=Count('id')
        )

        return Response(list(stats))


class NotificationConfigViewSet(BaseModelViewSetWithBatch):
    """通知配置 ViewSet - 继承公共基类"""

    queryset = NotificationConfig.objects.select_related('user').all()
    serializer_class = NotificationConfigSerializer
    # 自动获得完整的批量操作能力

    def get_queryset(self):
        """只返回当前用户的配置"""
        return self.queryset.filter(user=self.request.user)

    @action(detail=False, methods=['get', 'put'])
    def my_config(self, request):
        """获取/更新当前用户配置"""
        config, created = NotificationConfig.objects.get_or_create(
            user=request.user
        )

        if request.method == 'PUT':
            serializer = NotificationConfigUpdateSerializer(
                config,
                data=request.data
            )
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(NotificationConfigSerializer(config).data)

        serializer = self.get_serializer(config)
        return Response(serializer.data)
```

---

## 5. 服务层

### 5.1 通知服务

```python
# apps/notifications/services/notification_service.py

from typing import List, Union, Dict, Any
from django.utils import timezone
from django.db import transaction
from apps.common.services.base_crud import BaseCRUDService
from apps.notifications.models import Notification, NotificationLog, NotificationConfig
from apps.notifications.channels.base import NotificationMessage, SendResult
from apps.notifications.channels import get_channel


class NotificationService(BaseCRUDService):
    """通知服务 - 继承公共 CRUD 服务基类"""

    def __init__(self):
        super().__init__(Notification)

    # 重试策略配置
    RETRY_STRATEGIES = {
        'urgent': {'max_retries': 5, 'backoff': 'immediate', 'initial_delay': 0},
        'high': {'max_retries': 3, 'backoff': 'exponential', 'initial_delay': 60},
        'normal': {'max_retries': 3, 'backoff': 'exponential', 'initial_delay': 300},
        'low': {'max_retries': 0, 'backoff': 'none', 'initial_delay': 0},
    }

    def send(
        self,
        recipient: Any,
        notification_type: str,
        variables: Dict[str, Any],
        channels: List[str] = None,
        priority: str = 'normal',
        sender: Any = None,
        scheduled_at: timezone.datetime = None,
        user=None
    ) -> Notification:
        """
        发送通知
        Args:
            recipient: 接收人用户对象
            notification_type: 通知类型
            variables: 模板变量
            channels: 指定渠道列表，不指定则使用默认渠道
            priority: 优先级
            sender: 发送人
            scheduled_at: 计划发送时间
            user: 操作用户
        Returns:
            通知对象
        """
        from apps.notifications.services.template_service import TemplateEngine

        # 获取用户通知配置
        config = self._get_user_config(recipient)

        # 确定发送渠道
        if channels is None:
            channels = self._get_default_channels(notification_type)

        # 过滤禁用渠道
        channels = [c for c in channels if config.is_channel_enabled(notification_type, c)]

        if not channels:
            # 没有可用渠道，创建站内信记录
            channels = ['inbox']

        # 为每个渠道创建通知记录
        notification = None

        with transaction.atomic():
            for channel in channels:
                # 渲染模板
                rendered = TemplateEngine.render_template(
                    notification_type,
                    channel,
                    {'recipient': recipient, **variables}
                )

                # 使用基类的 create 方法
                notification = self.create(
                    data={
                        'recipient': recipient,
                        'notification_type': notification_type,
                        'priority': priority,
                        'channel': channel,
                        'title': rendered.get('subject', ''),
                        'content': rendered.get('content', ''),
                        'data': variables,
                        'sender': sender,
                        'scheduled_at': scheduled_at,
                        'status': 'pending' if not scheduled_at else 'scheduled'
                    },
                    user=user
                )

                # 如果是立即发送，加入队列
                if not scheduled_at:
                    self._enqueue_notification(notification)

        return notification

    def send_batch(
        self,
        recipients: List[Any],
        notification_type: str,
        variables: Dict[str, Any],
        channels: List[str] = None,
        priority: str = 'normal',
        user=None
    ) -> List[Notification]:
        """批量发送通知"""
        notifications = []

        for recipient in recipients:
            notification = self.send(
                recipient=recipient,
                notification_type=notification_type,
                variables=variables,
                channels=channels,
                priority=priority,
                user=user
            )
            notifications.append(notification)

        return notifications

    def get_user_notifications(
        self,
        user: Any,
        is_read: bool = None,
        notification_type: str = None
    ):
        """
        获取用户通知列表

        Args:
            user: 用户对象
            is_read: 是否已读（None=全部）
            notification_type: 通知类型

        Returns:
            QuerySet
        """
        filters = {'recipient': user}

        if is_read is True:
            filters['read_at__isnull'] = False
        elif is_read is False:
            filters['read_at__isnull'] = True

        if notification_type:
            filters['notification_type'] = notification_type

        return self.query(filters=filters, order_by='-created_at')

    def mark_all_as_read(self, user: Any) -> int:
        """将用户所有通知标记为已读"""
        count = self.query(filters={'recipient': user, 'read_at__isnull': True}).update(
            read_at=timezone.now()
        )
        return count

    def _get_user_config(self, user) -> NotificationConfig:
        """获取用户通知配置"""
        config = getattr(user, 'notification_config', None)
        if not config:
            config = NotificationConfig.objects.create(user=user)
        return config

    def _get_default_channels(self, notification_type: str) -> List[str]:
        """获取默认渠道"""
        default_channels = {
            'workflow_approval': ['inbox', 'wework'],
            'workflow_approved': ['inbox', 'email'],
            'workflow_rejected': ['inbox', 'email'],
            'inventory_assigned': ['inbox', 'sms'],
            'inventory_reminder': ['inbox', 'wework'],
            'asset_warning': ['inbox', 'email'],
            'system_announcement': ['inbox'],
            'report_generated': ['inbox', 'email'],
        }
        return default_channels.get(notification_type, ['inbox'])

    def _enqueue_notification(self, notification: Notification):
        """将通知加入发送队列"""
        from apps.notifications.tasks import send_notification_task

        # 根据优先级设置延迟
        priority_map = {'urgent': 0, 'high': 3, 'normal': 5, 'low': 7}

        send_notification_task.apply_async(
            args=[notification.id],
            priority=priority_map.get(notification.priority, 5)
        )

    def process_notification(self, notification_id: int) -> bool:
        """处理通知发送"""
        try:
            notification = Notification.objects.select_for_update().get(id=notification_id)
        except Notification.DoesNotExist:
            return False

        # 检查是否需要发送
        if notification.status in ['success', 'cancelled']:
            return True

        # 检查计划发送时间
        if notification.scheduled_at and notification.scheduled_at > timezone.now():
            # 重新调度
            self._enqueue_notification(notification)
            return True

        # 检查免打扰时段
        config = self._get_user_config(notification.recipient)
        if config.is_in_quiet_hours() and notification.priority != 'urgent':
            # 延迟到免打扰时段结束
            notification.scheduled_at = self._calculate_after_quiet_hours(config)
            notification.save(update_fields=['scheduled_at'])
            self._enqueue_notification(notification)
            return True

        # 执行发送
        return self._do_send(notification)

    def _do_send(self, notification: Notification) -> bool:
        """执行发送"""
        import time
        from apps.notifications.channels import get_channel

        notification.status = 'sending'
        notification.save(update_fields=['status'])

        # 获取渠道适配器
        channel = get_channel(notification.channel)

        # 构建消息
        message = NotificationMessage(
            recipient=notification.recipient,
            title=notification.title,
            content=notification.content,
            data=notification.data,
            notification_id=notification.id
        )

        # 发送
        start_time = time.time()
        result: SendResult = channel.send(message)
        duration = int((time.time() - start_time) * 1000)

        # 记录日志
        self._create_log(notification, result, duration)

        if result.success:
            # 发送成功
            notification.status = 'success'
            notification.sent_at = timezone.now()
            notification.save(update_fields=['status', 'sent_at'])
            return True
        else:
            # 发送失败，检查是否需要重试
            retry_config = self.RETRY_STRATEGIES.get(notification.priority, {})
            max_retries = retry_config.get('max_retries', 3)

            if notification.retry_count < max_retries and channel.supports_retry():
                # 安排重试
                notification.retry_count += 1
                notification.next_retry_at = self._calculate_retry_time(
                    notification.retry_count,
                    retry_config
                )
                notification.status = 'pending'
                notification.save()

                # 重新加入队列
                self._enqueue_notification(notification)
                return False
            else:
                # 标记为失败
                notification.status = 'failed'
                notification.save(update_fields=['status'])
                return False

    def _create_log(self, notification: Notification, result: SendResult, duration: int):
        """创建发送日志"""
        NotificationLog.objects.create(
            notification=notification,
            channel=notification.channel,
            status='success' if result.success else 'failed',
            error_code=result.error_code,
            error_message=result.error_message,
            external_id=result.message_id,
            duration=duration
        )

    def _calculate_retry_time(self, retry_count: int, config: Dict) -> timezone.datetime:
        """计算下次重试时间"""
        from django.utils import timezone
        import timedelta

        backoff = config.get('backoff', 'exponential')
        initial_delay = config.get('initial_delay', 60)

        if backoff == 'immediate':
            delay = 0
        elif backoff == 'fixed':
            delay = initial_delay
        elif backoff == 'exponential':
            delay = initial_delay * (2 ** (retry_count - 1))
        elif backoff == 'linear':
            delay = initial_delay * retry_count
        else:
            delay = initial_delay

        # 最大延迟限制
        max_delay = config.get('max_delay', 3600)
        delay = min(delay, max_delay)

        return timezone.now() + timezone.timedelta(seconds=delay)

    def _calculate_after_quiet_hours(self, config: NotificationConfig) -> timezone.datetime:
        """计算免打扰结束后的发送时间"""
        from django.utils import timezone
        import datetime

        today = timezone.now().date()
        quiet_end = datetime.datetime.combine(today, config.quiet_hours_end)

        if quiet_end.time() <= timezone.now().time():
            # 已经过了今天的结束时间，安排到明天
            quiet_end = quiet_end + timezone.timedelta(days=1)

        return timezone.make_aware(quiet_end)
```

---

## 6. 模板引擎

```python
# apps/notifications/services/template_service.py

from jinja2 import Template, Environment, BaseLoader
from typing import Dict, Any
from apps.notifications.models import NotificationTemplate


class TemplateEngine:
    """通知模板引擎"""

    # 内置过滤器
    filters = {
        'format_date': lambda value, fmt='%Y-%m-%d %H:%M': value.strftime(fmt) if value else '',
        'format_money': lambda value: f'¥{value:,.2f}' if value is not None else '¥0.00',
        'truncate': lambda value, length=50: str(value)[:length] + '...' if len(str(value)) > length else value,
    }

    # 内置函数
    functions = {
        'now': lambda: timezone.now(),
        'today': lambda: timezone.now().date(),
    }

    @classmethod
    def render_template(
        cls,
        template_code: str,
        channel: str,
        context: Dict[str, Any],
        language: str = 'zh-CN'
    ) -> Dict[str, str]:
        """
        渲染模板
        Args:
            template_code: 模板代码
            channel: 渠道类型
            context: 模板变量
            language: 语言
        Returns:
            {'subject': '标题', 'content': '内容'}
        """
        # 获取模板
        template = NotificationTemplate.objects.filter(
            template_code=template_code,
            channel=channel,
            language=language,
            is_active=True
        ).first()

        if not template:
            # 使用默认模板
            template = NotificationTemplate.objects.filter(
                template_code=template_code,
                channel=channel,
                is_active=True
            ).first()

        if not template:
            # 返回默认内容
            return cls._render_default(template_code, context)

        # 添加内置变量
        render_context = {
            **context,
            **cls._get_builtin_variables(context),
        }

        # 渲染
        env = Environment(loader=BaseLoader())
        env.filters.update(cls.filters)
        env.globals.update(cls.functions)

        result = {}
        if template.subject_template:
            result['subject'] = env.from_string(template.subject_template).render(**render_context)
        if template.content_template:
            result['content'] = env.from_string(template.content_template).render(**render_context)

        return result

    @classmethod
    def _get_builtin_variables(cls, context: Dict[str, Any]) -> Dict[str, Any]:
        """获取内置变量"""
        from django.utils import timezone
        from django.conf import settings

        recipient = context.get('recipient')
        return {
            'system_name': getattr(settings, 'SYSTEM_NAME', '钩子固定资产'),
            'current_date': timezone.now().date(),
            'current_time': timezone.now().time(),
            'current_datetime': timezone.now(),
            'recipient_name': getattr(recipient, 'full_name', '') or getattr(recipient, 'username', ''),
            'recipient_email': getattr(recipient, 'email', ''),
        }

    @classmethod
    def _render_default(cls, template_code: str, context: Dict[str, Any]) -> Dict[str, str]:
        """渲染默认内容"""
        return {
            'subject': f"新通知 - {template_code}",
            'content': str(context)
        }

    @classmethod
    def preview_template(
        cls,
        template_id: int,
        example_data: Dict[str, Any]
    ) -> Dict[str, str]:
        """预览模板"""
        template = NotificationTemplate.objects.get(id=template_id)

        render_context = {
            **example_data,
            **cls._get_builtin_variables(example_data),
        }

        env = Environment(loader=BaseLoader())
        env.filters.update(cls.filters)

        result = {}
        if template.subject_template:
            result['subject'] = env.from_string(template.subject_template).render(**render_context)
        if template.content_template:
            result['content'] = env.from_string(template.content_template).render(**render_context)

        return result
```

---

## 3. 渠道适配器

### 3.1 基类定义

```python
# apps/notifications/channels/base.py

from abc import ABC, abstractmethod
from typing import Dict, Any
from dataclasses import dataclass


@dataclass
class NotificationMessage:
    """通知消息"""
    recipient: Any  # 用户对象
    title: str
    content: str
    data: Dict[str, Any]
    notification_id: int = None


@dataclass
class SendResult:
    """发送结果"""
    success: bool
    message_id: str = None
    error_code: str = None
    error_message: str = None
    external_data: Dict[str, Any] = None


class NotificationChannel(ABC):
    """通知渠道适配器基类"""

    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}

    @abstractmethod
    def send(self, message: NotificationMessage) -> SendResult:
        """发送通知"""
        pass

    @abstractmethod
    def get_channel_code(self) -> str:
        """获取渠道代码"""
        pass

    def supports_retry(self) -> bool:
        """是否支持重试"""
        return True

    def validate_recipient(self, recipient) -> bool:
        """验证接收人是否有效"""
        return True
```

### 3.2 站内信渠道

```python
# apps/notifications/channels/inbox.py

class InboxChannel(NotificationChannel):
    """站内信渠道"""

    def get_channel_code(self) -> str:
        return 'inbox'

    def send(self, message: NotificationMessage) -> SendResult:
        """发送站内信"""
        from apps.notifications.models import Notification

        try:
            # 站内信直接创建记录
            notification = Notification.objects.get(id=message.notification_id)
            notification.status = 'success'
            notification.sent_at = timezone.now()
            notification.save(update_fields=['status', 'sent_at'])

            return SendResult(
                success=True,
                message_id=str(notification.id)
            )
        except Exception as e:
            return SendResult(
                success=False,
                error_message=str(e)
            )

    def supports_retry(self) -> bool:
        return False  # 站内信不需要重试
```

### 3.3 邮件渠道

```python
# apps/notifications/channels/email.py

class EmailChannel(NotificationChannel):
    """邮件渠道"""

    def get_channel_code(self) -> str:
        return 'email'

    def send(self, message: NotificationMessage) -> SendResult:
        """发送邮件"""
        from django.core.mail import send_mail
        from django.conf import settings
import time

        # 获取接收人邮箱
        recipient_email = self._get_recipient_email(message.recipient)

        if not recipient_email:
            return SendResult(
                success=False,
                error_code='NO_EMAIL',
                error_message='接收人邮箱为空'
            )

        try:
            # 发送邮件
            start_time = time.time()

            sent = send_mail(
                subject=message.title,
                message=message.content,
                html_message=self._render_html(message),
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[recipient_email],
                fail_silently=False
            )

            duration = int((time.time() - start_time) * 1000)

            if sent:
                return SendResult(
                    success=True,
                    message_id=f"email_{int(time.time())}",
                    external_data={'duration': duration}
                )
            else:
                return SendResult(
                    success=False,
                    error_code='SEND_FAILED',
                    error_message='邮件发送失败'
                )

        except Exception as e:
            return SendResult(
                success=False,
                error_code='EXCEPTION',
                error_message=str(e)
            )

    def _get_recipient_email(self, recipient) -> str:
        """获取接收人邮箱"""
        from apps.notifications.models import NotificationConfig

        # 检查用户配置
        config = getattr(recipient, 'notification_config', None)
        if config and config.email_address:
            return config.email_address

        return getattr(recipient, 'email', '')

    def _render_html(self, message: NotificationMessage) -> str:
        """渲染HTML邮件"""
        return f"""
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background: #1989fa; color: white; padding: 20px; text-align: center; }}
                .content {{ padding: 20px; background: #f5f5f5; }}
                .footer {{ text-align: center; padding: 20px; color: #999; font-size: 12px; }}
                .button {{ display: inline-block; padding: 10px 20px; background: #1989fa; color: white; text-decoration: none; border-radius: 4px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h2>{message.title}</h2>
                </div>
                <div class="content">
                    {message.content}
                </div>
                <div class="footer">
                    <p>本邮件由系统自动发送，请勿回复</p>
                </div>
            </div>
        </body>
        </html>
        """
```

### 3.4 短信渠道

```python
# apps/notifications/channels/sms.py

class SMSChannel(NotificationChannel):
    """短信渠道"""

    def get_channel_code(self) -> str:
        return 'sms'

    def send(self, message: NotificationMessage) -> SendResult:
        """发送短信"""
        # 根据配置选择短信服务商
        provider = self.config.get('provider', 'aliyun')

        if provider == 'aliyun':
            return self._send_aliyun(message)
        elif provider == 'tencent':
            return self._send_tencent(message)
        else:
            return SendResult(
                success=False,
                error_code='UNKNOWN_PROVIDER',
                error_message=f'未知的短信服务商: {provider}'
            )

    def _send_aliyun(self, message: NotificationMessage) -> SendResult:
        """阿里云短信发送"""
        from aliyunsdkcore.client import AcsClient
        from aliyunsdkdysmsapi.request.v20170525 import SendSmsRequest
import json

        access_key_id = self.config.get('aliyun_access_key_id')
        access_key_secret = self.config.get('aliyun_access_key_secret')
        sign_name = self.config.get('aliyun_sign_name')
        template_code = self.config.get('aliyun_template_code')

        try:
            client = AcsClient(access_key_id, access_key_secret, 'cn-hangzhou')

            request = SendSmsRequest.SendSmsRequest()
            request.set_PhoneNumbers(self._get_recipient_phone(message.recipient))
            request.set_SignName(sign_name)
            request.set_TemplateCode(template_code)
            request.set_TemplateParam(json.dumps(message.data))

            response = client.do_action_with_exception(request)

            result = json.loads(response.decode('utf-8'))

            if result.get('Code') == 'OK':
                return SendResult(
                    success=True,
                    message_id=result.get('BizId'),
                    external_data={'request_id': result.get('RequestId')}
                )
            else:
                return SendResult(
                    success=False,
                    error_code=result.get('Code'),
                    error_message=result.get('Message')
                )

        except Exception as e:
            return SendResult(
                success=False,
                error_code='EXCEPTION',
                error_message=str(e)
            )

    def _get_recipient_phone(self, recipient) -> str:
        """获取接收人手机号"""
        from apps.notifications.models import NotificationConfig

        # 检查用户配置
        config = getattr(recipient, 'notification_config', None)
        if config and config.phone_number:
            return config.phone_number

        return getattr(recipient, 'phone_number', '')
```

### 3.5 企业微信渠道

```python
# apps/notifications/channels/wework.py

class WeWorkChannel(NotificationChannel):
    """企业微信渠道"""

    def get_channel_code(self) -> str:
        return 'wework'

    def send(self, message: NotificationMessage) -> SendResult:
        """发送企业微信消息"""
        import requests

        corp_id = self.config.get('wework_corp_id')
        agent_id = self.config.get('wework_agent_id')
        secret = self.config.get('wework_secret')

        try:
            # 获取access_token
            token_url = f"https://qyapi.weixin.qq.com/cgi-bin/gettoken?corpid={corp_id}&corpsecret={secret}"
            token_response = requests.get(token_url)
            token_data = token_response.json()

            if token_data.get('errcode') != 0:
                return SendResult(
                    success=False,
                    error_code=str(token_data.get('errcode')),
                    error_message=token_data.get('errmsg')
                )

            access_token = token_data.get('access_token')

            # 发送消息
            user_id = self._get_wework_userid(message.recipient)

            send_url = f"https://qyapi.weixin.qq.com/cgi-bin/message/send?access_token={access_token}"

            payload = {
                "touser": user_id,
                "msgtype": "text",
                "agentid": agent_id,
                "text": {
                    "content": f"{message.title}\n\n{message.content}"
                },
                "safe": 0
            }

            if message.data.get('link'):
                payload['msgtype'] = 'textcard'
                payload['textcard'] = {
                    "title": message.title,
                    "description": message.content,
                    "url": message.data['link'],
                    "btntxt": "查看详情"
                }

            response = requests.post(send_url, json=payload)
            result = response.json()

            if result.get('errcode') == 0:
                return SendResult(
                    success=True,
                    message_id=result.get('msgid'),
                    external_data={'invaliduser': result.get('invaliduser', [])}
                )
            else:
                return SendResult(
                    success=False,
                    error_code=str(result.get('errcode')),
                    error_message=result.get('errmsg')
                )

        except Exception as e:
            return SendResult(
                success=False,
                error_code='EXCEPTION',
                error_message=str(e)
            )

    def _get_wework_userid(self, recipient) -> str:
        """获取企业微信UserID"""
        # 从用户属性或配置中获取
        wework_id = getattr(recipient, 'wework_userid', None)

        if not wework_id:
            # 尝试从手机号匹配
            phone = getattr(recipient, 'phone_number', '')
            if phone:
                wework_id = phone

        return wework_id or ''
```

---

## 7. Celery任务

```python
# apps/notifications/tasks.py

from celery import shared_task
from apps.notifications.services.notification_service import NotificationService


@shared_task(bind=True, max_retries=3)
def send_notification_task(self, notification_id: int):
    """发送通知任务"""
    try:
        service = NotificationService()
        success = service.process_notification(notification_id)
        return {'success': success, 'notification_id': notification_id}
    except Exception as exc:
        # 任务级别重试
        raise self.retry(exc=exc, countdown=60)


@shared_task
def retry_failed_notifications():
    """重试失败的通知（定时任务）"""
    from django.utils import timezone
    from apps.notifications.models import Notification

    notifications = Notification.objects.filter(
        status='pending',
        next_retry_at__lte=timezone.now()
    )

    service = NotificationService()
    for notification in notifications:
        service.process_notification(notification.id)

    return {'count': notifications.count()}


@shared_task
def cleanup_old_notifications():
    """清理旧通知（定时任务）"""
    from django.utils import timezone
    from apps.notifications.models import Notification, NotificationLog

    # 清理90天前的已读通知
    cutoff = timezone.now() - timezone.timedelta(days=90)
    deleted_count = Notification.objects.filter(
        read_at__lt=cutoff
    ).delete()[0]

    # 清理180天前的日志
    log_cutoff = timezone.now() - timezone.timedelta(days=180)
    NotificationLog.objects.filter(created_at__lt=log_cutoff).delete()

    return {'deleted_notifications': deleted_count}
```

---

## 8. URL配置

```python
# apps/notifications/urls.py

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from apps.notifications.views import (
    NotificationTemplateViewSet,
    NotificationViewSet,
    NotificationConfigViewSet
)

router = DefaultRouter()
router.register(r'templates', NotificationTemplateViewSet, basename='notification-template')
router.register(r'notifications', NotificationViewSet, basename='notification')
router.register(r'configs', NotificationConfigViewSet, basename='notification-config')

urlpatterns = [
    path('', include(router.urls)),
]
```

---

## 9. 使用示例

### 9.1 发送通知

```python
# 在业务代码中发送通知

from apps.notifications.services.notification_service import NotificationService

# 示例1: 工作流审批通知
def notify_workflow_approval(workflow_instance):
    service = NotificationService()

    service.send(
        recipient=workflow_instance.approver,
        notification_type='workflow_approval',
        variables={
            'workflow_name': workflow_instance.definition.name,
            'submitter': workflow_instance.submitter.username,
            'submit_time': workflow_instance.created_at,
            'detail_url': f'/workflows/{workflow_instance.id}'
        },
        channels=['inbox', 'wework'],
        priority='high',
        user=workflow_instance.submitter
    )

# 示例2: 批量发送盘点任务通知
def notify_inventory_task(task):
    service = NotificationService()

    recipients = [task.assignee for task in task.assignments.all()]

    service.send_batch(
        recipients=recipients,
        notification_type='inventory_assigned',
        variables={
            'task_name': task.name,
            'start_date': task.start_date,
            'end_date': task.end_date,
            'asset_count': task.assets.count()
        },
        channels=['inbox', 'sms'],
        priority='normal'
    )
```

### 9.2 查询通知

```python
# 使用服务层查询通知

from apps.notifications.services.notification_service import NotificationService

service = NotificationService()

# 获取用户未读通知
unread_notifications = service.get_user_notifications(
    user=request.user,
    is_read=False
)

# 获取特定类型的通知
workflow_notifications = service.get_user_notifications(
    user=request.user,
    notification_type='workflow_approval'
)

# 标记所有通知为已读
count = service.mark_all_as_read(request.user)
```

---

## 10. 后续任务

1. 实现钉钉/飞书渠道适配器
2. 实现模板变量校验
3. 实现通知统计报表
4. 实现发送性能优化
5. 实现通知撤回功能
6. 编写单元测试

---

## 11. 公共基类使用总结

本模块完全使用了公共基类，带来的好处：

### 11.1 序列化器 (继承 BaseModelSerializer)

- ✅ 自动包含所有公共字段（id, organization, created_at, updated_at, created_by等）
- ✅ 自动处理 custom_fields 动态字段
- ✅ 统一的审计字段输出格式
- ✅ 支持嵌套序列化（关联用户、组织等）

### 11.2 视图 (继承 BaseModelViewSetWithBatch)

- ✅ 自动应用组织隔离和软删除过滤
- ✅ 自动设置审计字段（创建人、更新人）
- ✅ 自动使用软删除而非物理删除
- ✅ 完整的批量操作接口（删除、恢复、更新）
- ✅ 已删除记录查询和恢复功能

### 11.3 服务 (继承 BaseCRUDService)

- ✅ 统一的 CRUD 操作方法
- ✅ 自动处理组织隔离和软删除
- ✅ 支持复杂查询场景（过滤、搜索、排序、分页）
- ✅ 业务逻辑可扩展（添加 send, send_batch 等业务方法）

### 11.4 过滤器 (继承 BaseModelFilter)

- ✅ 公共字段过滤（创建时间、更新时间、创建人等）
- ✅ 时间范围查询（支持 from/to 格式）
- ✅ 统一的过滤接口

### 11.5 代码对比

**传统实现（不使用公共基类）**：
```python
class NotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notification
        fields = ['id', 'organization', 'is_deleted', 'deleted_at',
                  'created_at', 'updated_at', 'created_by', 'custom_fields',
                  'recipient', 'title', 'content', ...]  # 需要手动列举所有字段

class NotificationViewSet(viewsets.ModelViewSet):
    def get_queryset(self):
        # 需要手动实现组织过滤和软删除过滤
        return Notification.objects.filter(
            organization=get_current_organization(),
            is_deleted=False
        )

    def perform_create(self, serializer):
        # 需要手动设置创建人和组织
        serializer.save(
            created_by=self.request.user,
            organization_id=get_current_organization()
        )

    def perform_destroy(self, instance):
        # 需要手动实现软删除
        instance.is_deleted = True
        instance.deleted_at = timezone.now()
        instance.save()
```

**使用公共基类后**：
```python
class NotificationSerializer(BaseModelSerializer):
    """只需定义业务字段"""

    class Meta(BaseModelSerializer.Meta):
        model = Notification
        fields = BaseModelSerializer.Meta.fields + [
            'recipient', 'title', 'content', ...  # 只需添加业务字段
        ]

class NotificationViewSet(BaseModelViewSetWithBatch):
    """自动获得所有公共功能"""

    queryset = Notification.objects.all()
    serializer_class = NotificationSerializer
    # 自动获得：
    # - 组织隔离
    # - 软删除
    # - 批量操作
    # - 审计字段设置
```

**代码减少约 60-70%，同时功能更完整、更规范！**

---

## 12. 测试用例

### 12.1 模型测试

#### 12.1.1 组织隔离测试
```python
def test_notification_template_org_isolation():
    """测试通知模板的组织隔离"""
    org1 = Organization.objects.create(name="公司A")
    org2 = Organization.objects.create(name="公司B")

    # 不同组织的模板
    template1 = NotificationTemplate.objects.create(
        organization=org1,
        template_code="test_1",
        template_name="测试模板1"
    )
    template2 = NotificationTemplate.objects.create(
        organization=org2,
        template_code="test_2",
        template_name="测试模板2"
    )

    # 验证查询结果的组织隔离
    assert NotificationTemplate.objects.filter(organization=org1).count() == 1
    assert NotificationTemplate.objects.filter(organization=org2).count() == 1
    assert NotificationTemplate.objects.count() == 2

def test_notification_org_isolation():
    """测试通知记录的组织隔离"""
    org1 = Organization.objects.create(name="公司A")
    org2 = Organization.objects.create(name="公司B")
    user1 = User.objects.create_user(username="user1", organization=org1)
    user2 = User.objects.create_user(username="user2", organization=org2)

    # 创建通知
    notification1 = Notification.objects.create(
        organization=org1,
        recipient=user1,
        title="通知1"
    )
    notification2 = Notification.objects.create(
        organization=org2,
        recipient=user2,
        title="通知2"
    )

    # 验证查询结果的组织隔离
    assert Notification.objects.filter(organization=org1).count() == 1
    assert Notification.objects.filter(organization=org2).count() == 1
```

#### 12.1.2 软删除测试
```python
def test_notification_template_soft_delete():
    """测试通知模板的软删除"""
    template = NotificationTemplate.objects.create(
        template_code="test_delete",
        template_name="测试删除"
    )

    # 软删除
    template.delete()  # 自动调用软删除

    # 验证记录被标记为已删除
    template.refresh_from_db()
    assert template.is_deleted is True
    assert template.deleted_at is not None

    # 验证查询结果不包含软删除记录
    assert NotificationTemplate.objects.count() == 0
    assert NotificationTemplate.objects.all_with_deleted().count() == 1

    # 恢复记录
    template.restore()
    template.refresh_from_db()
    assert template.is_deleted is False
    assert NotificationTemplate.objects.count() == 1

def test_notification_soft_delete():
    """测试通知记录的软删除"""
    notification = Notification.objects.create(
        recipient=User.objects.create_user("test_user"),
        title="测试通知"
    )

    # 软删除通知及其日志
    notification.delete()

    # 验证通知被软删除
    notification.refresh_from_db()
    assert notification.is_deleted is True

    # 验证相关日志也被软删除
    assert NotificationLog.objects.count() == 0
```

#### 12.1.3 审计字段测试
```python
def test_notification_template_audit_fields():
    """测试通知模板的审计字段"""
    user = User.objects.create_user("admin")
    org = Organization.objects.create(name="测试组织")

    template = NotificationTemplate.objects.create(
        created_by=user,
        organization=org,
        template_code="audit_test",
        template_name="审计测试"
    )

    # 验证创建审计字段
    assert template.created_at is not None
    assert template.updated_at is not None
    assert template.created_by == user
    assert template.organization == org

    # 更新操作
    template.template_name = "审计测试更新"
    template.save()
    template.refresh_from_db()
    assert template.updated_at > template.created_at

def test_notification_audit_fields():
    """测试通知记录的审计字段"""
    user = User.objects.create_user("test_user")

    notification = Notification.objects.create(
        recipient=user,
        title="审计测试通知",
        created_by=user
    )

    # 验证创建审计字段
    assert notification.created_at is not None
    assert notification.updated_at is not None
    assert notification.created_by == user
```

#### 12.1.4 自定义字段测试
```python
def test_notification_template_custom_fields():
    """测试通知模板的自定义字段"""
    template = NotificationTemplate.objects.create(
        template_code="custom_test",
        template_name="自定义字段测试",
        custom_fields={
            "category": "workflow",
            "tags": ["重要", "审批"],
            "metadata": {"version": "1.0"}
        }
    )

    # 验证自定义字段存储
    template.refresh_from_db()
    assert template.custom_fields["category"] == "workflow"
    assert template.custom_fields["tags"] == ["重要", "审批"]
    assert template.custom_fields["metadata"]["version"] == "1.0"

def test_notification_config_custom_fields():
    """测试通知配置的自定义字段"""
    config = NotificationConfig.objects.create(
        user=User.objects.create_user("config_user"),
        custom_fields={
            "preferred_channels": ["email", "sms"],
            "quiet_hours": {"enabled": True}
        }
    )

    # 验证自定义字段存储
    config.refresh_from_db()
    assert "email" in config.custom_fields["preferred_channels"]
    assert config.custom_fields["quiet_hours"]["enabled"] is True
```

#### 12.1.5 批量操作测试
```python
def test_notification_template_batch_operations():
    """测试通知模板的批量操作"""
    templates = [
        NotificationTemplate.objects.create(
            template_code=f"batch_{i}",
            template_name=f"批量模板{i}"
        )
        for i in range(5)
    ]

    template_ids = [t.id for t in templates]

    # 批量删除
    result = NotificationTemplateViewSet._batch_delete(
        NotificationTemplateViewSet(),
        {"ids": template_ids}
    )
    assert result["summary"]["succeeded"] == 5

    # 批量恢复
    result = NotificationTemplateViewSet._batch_restore(
        NotificationTemplateViewSet(),
        {"ids": template_ids}
    )
    assert result["summary"]["succeeded"] == 5

    # 批量更新
    result = NotificationTemplateViewSet._batch_update(
        NotificationTemplateViewSet(),
        {"ids": template_ids, "data": {"is_active": False}}
    )
    assert result["summary"]["succeeded"] == 5
    for template in templates:
        template.refresh_from_db()
        assert template.is_active is False
```

### 12.2 API测试

#### 12.2.1 通知模板API测试
```python
class NotificationTemplateAPITest(APITestCase):
    """通知模板API测试"""

    def setUp(self):
        self.user = User.objects.create_user("test_user", is_staff=True)
        self.client.force_authenticate(user=self.user)

    def test_create_notification_template(self):
        """创建通知模板"""
        data = {
            "template_code": "api_test",
            "template_name": "API测试模板",
            "channel": "email",
            "subject_template": "{{ title }}",
            "content_template": "内容：{{ content }}"
        }

        response = self.client.post("/api/notifications/templates/", data)
        assert response.status_code == 201
        assert response.data["template_code"] == "api_test"

    def test_notification_template_list_filtering(self):
        """测试通知模板列表过滤"""
        # 创建测试数据
        NotificationTemplate.objects.create(
            template_code="filter_1",
            template_name="过滤测试1",
            channel="email"
        )
        NotificationTemplate.objects.create(
            template_code="filter_2",
            template_name="过滤测试2",
            channel="sms"
        )

        # 测试渠道过滤
        response = self.client.get("/api/notifications/templates/?channel=email")
        assert len(response.data["results"]) == 1
        assert response.data["results"][0]["channel"] == "email"

    def test_notification_template_version_control(self):
        """测试通知模板版本控制"""
        template = NotificationTemplate.objects.create(
            template_code="version_test",
            template_name="版本测试"
        )

        # 保存新版本
        response = self.client.post(
            f"/api/notifications/templates/{template.id}/save_new_version/"
        )
        assert response.status_code == 201
        new_version = response.data
        assert new_version["version"] == 2
        assert new_version["previous_version"] == str(template.id)
```

#### 12.2.2 通知API测试
```python
class NotificationAPITest(APITestCase):
    """通知API测试"""

    def setUp(self):
        self.user = User.objects.create_user("test_user")
        self.client.force_authenticate(user=self.user)

    def test_notification_list_filtering(self):
        """测试通知列表过滤"""
        # 创建测试数据
        Notification.objects.create(
            recipient=self.user,
            notification_type="workflow_approval",
            title="审批通知1"
        )
        Notification.objects.create(
            recipient=self.user,
            notification_type="asset_warning",
            title="预警通知"
        )

        # 测试类型过滤
        response = self.client.get("/api/notifications/?notification_type=workflow_approval")
        assert len(response.data["results"]) == 1
        assert response.data["results"][0]["notification_type"] == "workflow_approval"

    def test_notification_mark_as_read(self):
        """测试标记通知为已读"""
        notification = Notification.objects.create(
            recipient=self.user,
            title="测试通知"
        )

        # 标记为已读
        response = self.client.post(f"/api/notifications/{notification.id}/mark_as_read/")
        assert response.status_code == 200

        notification.refresh_from_db()
        assert notification.read_at is not None

    def test_batch_mark_read(self):
        """测试批量标记已读"""
        notifications = [
            Notification.objects.create(recipient=self.user, title=f"通知{i}")
            for i in range(3)
        ]
        ids = [str(n.id) for n in notifications]

        response = self.client.post("/api/notifications/batch_mark_read/", {"ids": ids})
        assert response.status_code == 200
        assert response.data["summary"]["succeeded"] == 3

    def test_unread_count(self):
        """测试未读数量统计"""
        # 创建未读通知
        Notification.objects.create(recipient=self.user, title="未读1")
        Notification.objects.create(recipient=self.user, title="未读2")

        response = self.client.get("/api/notifications/unread_count/")
        assert response.data["unread_count"] == 2
```

#### 12.2.3 通知配置API测试
```python
class NotificationConfigAPITest(APITestCase):
    """通知配置API测试"""

    def setUp(self):
        self.user = User.objects.create_user("test_user")
        self.client.force_authenticate(user=self.user)

    def test_get_my_config(self):
        """测试获取个人配置"""
        config = NotificationConfig.objects.create(
            user=self.user,
            enable_email=False,
            enable_sms=True
        )

        response = self.client.get("/api/notifications/configs/my_config/")
        assert response.status_code == 200
        assert response.data["enable_email"] is False
        assert response.data["enable_sms"] is True

    def test_update_my_config(self):
        """测试更新个人配置"""
        data = {
            "enable_email": True,
            "enable_sms": False,
            "quiet_hours_enabled": True,
            "quiet_hours_start": "22:00",
            "quiet_hours_end": "08:00"
        }

        response = self.client.put("/api/notifications/configs/my_config/", data)
        assert response.status_code == 200

        config = NotificationConfig.objects.get(user=self.user)
        assert config.enable_email is True
        assert config.enable_sms is False
        assert config.quiet_hours_enabled is True
```

### 12.3 边界条件测试

#### 12.3.1 权限测试
```python
class NotificationPermissionTest(APITestCase):
    """通知权限测试"""

    def setUp(self):
        self.org1 = Organization.objects.create(name="公司A")
        self.org2 = Organization.objects.create(name="公司B")
        self.user1 = User.objects.create_user("user1", organization=self.org1)
        self.user2 = User.objects.create_user("user2", organization=self.org2)

    def test_notification_template_org_isolation_enforcement(self):
        """测试通知模板组织隔离的强制执行"""
        # 用户1创建模板
        template = NotificationTemplate.objects.create(
            created_by=self.user1,
            organization=self.org1,
            template_code="org_test"
        )

        # 验证用户2无法访问用户1的模板
        self.client.force_authenticate(user=self.user2)
        response = self.client.get(f"/api/notifications/templates/{template.id}/")
        assert response.status_code == 404

    def test_notification_config_user_isolation(self):
        """测试通知配置的用户隔离"""
        config1 = NotificationConfig.objects.create(
            user=self.user1,
            custom_fields={"test": "user1_data"}
        )
        config2 = NotificationConfig.objects.create(
            user=self.user2,
            custom_fields={"test": "user2_data"}
        )

        # 用户1只能访问自己的配置
        self.client.force_authenticate(user=self.user1)
        response = self.client.get("/api/notifications/configs/my_config/")
        assert response.data["custom_fields"]["test"] == "user1_data"

        # 验证用户2看不到用户1的配置
        response = self.client.get(f"/api/notifications/configs/{config1.id}/")
        assert response.status_code == 404
```

#### 12.3.2 空值处理测试
```python
def test_notification_template_empty_values():
    """测试通知模板的空值处理"""
    template = NotificationTemplate.objects.create(
        template_code="empty_test",
        template_name="空值测试",
        subject_template="",  # 空标题模板
        content_template="",  # 空内容模板
        variables={}  # 空变量定义
    )

    # 验证空值正常存储
    template.refresh_from_db()
    assert template.subject_template == ""
    assert template.content_template == ""
    assert template.variables == {}

    # 测试模板渲染空值
    rendered = template.render({})
    assert rendered["subject"] == ""
    assert rendered["content"] == ""

def test_notification_empty_recipient():
    """测试通知接收人为空的边界情况"""
    # 创建通知时接收人为空（应该被拒绝）
    with pytest.raises(Exception):
        Notification.objects.create(
            recipient=None,
            title="空接收人测试"
        )
```

#### 12.3.3 并发操作测试
```python
def test_concurrent_notification_creation():
    """测试通知并发创建"""
    user = User.objects.create_user("concurrent_user")

    def create_notification(i):
        Notification.objects.create(
            recipient=user,
            title=f"并发通知{i}"
        )

    # 使用线程并发创建
    threads = []
    for i in range(10):
        t = threading.Thread(target=create_notification, args=(i,))
        threads.append(t)
        t.start()

    for t in threads:
        t.join()

    # 验证所有通知都成功创建
    assert Notification.objects.filter(recipient=user).count() == 10

def test_concurrent_notification_update():
    """测试通知并发更新"""
    notification = Notification.objects.create(
        recipient=User.objects.create_user("test_user"),
        title="并发更新测试"
    )

    def update_notification():
        notification.title = f"更新_{time.time()}"
        notification.save()

    # 使用线程并发更新
    threads = []
    for _ in range(5):
        t = threading.Thread(target=update_notification)
        threads.append(t)
        t.start()

    for t in threads:
        t.join()

    # 验证记录存在
    notification.refresh_from_db()
    assert notification.title.startswith("更新_")
```

#### 12.3.4 数据一致性测试
```python
def test_notification_soft_delete_cascade():
    """测试通知软删除的级联关系"""
    user = User.objects.create_user("test_user")
    notification = Notification.objects.create(
        recipient=user,
        title="级联删除测试"
    )

    # 创建日志
    NotificationLog.objects.create(
        notification=notification,
        channel="email",
        status="success"
    )

    # 软删除通知
    notification.delete()

    # 验证级联软删除
    assert Notification.objects.count() == 0
    assert NotificationLog.objects.count() == 0  # 日志也被软删除

def test_notification_template_version_consistency():
    """测试通知模板版本一致性"""
    template = NotificationTemplate.objects.create(
        template_code="version_test",
        template_name="版本一致性测试"
    )

    # 保存多个版本
    versions = []
    for i in range(3):
        response = template.save_new_version()
        versions.append(response)

    # 验证版本号连续
    versions.sort(key=lambda x: x['version'])
    for i in range(len(versions) - 1):
        assert versions[i+1]['version'] - versions[i]['version'] == 1

    # 验证版本关系正确
    for i in range(1, len(versions)):
        assert versions[i]['previous_version'] == versions[i-1]['id']
```

### 测试总结

所有测试用例均遵循GZEAMS公共基类架构标准，确保：

- ✅ **组织隔离**: 所有模型正确继承并实现组织隔离功能
- ✅ **软删除**: 所有模型正确实现软删除和恢复机制
- ✅ **审计字段**: 自动跟踪创建人、更新人、删除人等审计信息
- ✅ **自定义字段**: JSONField动态字段正确存储和读取
- ✅ **批量操作**: 标准化的批量删除、恢复、更新接口
- ✅ **权限控制**: 严格的用户和组织的访问控制
- ✅ **并发安全**: 并发操作下数据一致性
- ✅ **数据完整性**: 级联删除和版本控制的数据一致性

测试覆盖了模型层、API层和边界条件，确保通知模块的稳定性和可靠性。

---

## 13. API规范

### 13.1 统一响应格式

#### 成功响应格式
```json
{
    "success": true,
    "message": "操作成功",
    "data": {
        "id": "uuid",
        "template_code": "workflow_approval",
        "template_name": "工作流审批通知",
        "channel": "email",
        "is_active": true,
        "created_at": "2024-01-15T10:00:00Z",
        "updated_at": "2024-01-15T10:00:00Z",
        "created_by": {
            "id": "uuid",
            "username": "admin",
            "email": "admin@example.com"
        }
    }
}
```

#### 列表响应格式（分页）
```json
{
    "success": true,
    "data": {
        "count": 100,
        "next": "https://api.example.com/api/notifications/templates/?page=2",
        "previous": null,
        "results": [
            {
                "id": "uuid",
                "template_code": "workflow_approval",
                "template_name": "工作流审批通知",
                "channel": "email",
                "is_active": true,
                "created_at": "2024-01-15T10:00:00Z"
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
            "template_code": ["该字段不能为空"]
        }
    }
}
```

### 13.2 标准CRUD接口

| 接口 | 方法 | 路径 | 说明 |
|------|------|------|------|
| **列表查询** | GET | `/api/notifications/templates/` | 分页查询通知模板列表，支持过滤和搜索 |
| **详情查询** | GET | `/api/notifications/templates/{id}/` | 获取单个通知模板详情信息 |
| **创建模板** | POST | `/api/notifications/templates/` | 创建新的通知模板 |
| **更新模板** | PUT | `/api/notifications/templates/{id}/` | 完整更新通知模板信息 |
| **部分更新** | PATCH | `/api/notifications/templates/{id}/` | 部分更新通知模板信息 |
| **删除模板** | DELETE | `/api/notifications/templates/{id}/` | 软删除通知模板（物理删除禁止） |
| **已删除列表** | GET | `/api/notifications/templates/deleted/` | 查询已删除的通知模板列表 |
| **恢复模板** | POST | `/api/notifications/templates/{id}/restore/` | 恢复已删除的通知模板 |

### 13.3 批量操作接口

| 接口 | 方法 | 路径 | 说明 |
|------|------|------|------|
| **批量删除** | POST | `/api/notifications/templates/batch-delete/` | 批量软删除通知模板 |
| **批量恢复** | POST | `/api/notifications/templates/batch-restore/` | 批量恢复已删除的通知模板 |
| **批量更新** | POST | `/api/notifications/templates/batch-update/` | 批量更新通知模板状态 |

#### 批量删除请求示例
```http
POST /api/notifications/templates/batch-delete/
{
    "ids": ["uuid1", "uuid2", "uuid3"]
}
```

#### 批量操作响应格式
```json
{
    "success": true,
    "message": "批量删除完成",
    "summary": {
        "total": 3,
        "succeeded": 3,
        "failed": 0
    },
    "results": [
        {"id": "uuid1", "success": true},
        {"id": "uuid2", "success": true},
        {"id": "uuid3", "success": true}
    ]
}
```

### 13.4 通知模板管理接口

| 接口 | 方法 | 路径 | 说明 |
|------|------|------|------|
| **保存新版本** | POST | `/api/notifications/templates/{id}/save_new_version/` | 保存模板新版本 |
| **激活模板** | POST | `/api/notifications/templates/{id}/activate/` | 激活指定模板版本 |
| **预览模板** | POST | `/api/notifications/templates/{id}/preview/` | 预览模板渲染效果 |

#### 预览模板请求示例
```json
{
    "example_data": {
        "workflow_name": "采购审批",
        "submitter": "张三",
        "amount": 50000,
        "detail_url": "/workflows/123"
    }
}
```

### 13.5 通知管理接口

| 接口 | 方法 | 路径 | 说明 |
|------|------|------|------|
| **通知列表** | GET | `/api/notifications/` | 分页查询通知列表，支持过滤和搜索 |
| **通知详情** | GET | `/api/notifications/{id}/` | 获取单个通知详情信息 |
| **创建通知** | POST | `/api/notifications/` | 创建新的通知记录 |
| **更新通知** | PUT | `/api/notifications/{id}/` | 完整更新通知信息 |
| **部分更新** | PATCH | `/api/notifications/{id}/` | 部分更新通知信息 |
| **删除通知** | DELETE | `/api/notifications/{id}/` | 软删除通知记录 |
| **标记已读** | POST | `/api/notifications/{id}/mark_as_read/` | 标记通知为已读 |
| **标记未读** | POST | `/api/notifications/{id}/mark_as_unread/` | 标记通知为未读 |
| **批量已读** | POST | `/api/notifications/batch_mark_read/` | 批量标记通知为已读 |
| **未读数量** | GET | `/api/notifications/unread_count/` | 获取当前用户未读通知数量 |
| **通知统计** | GET | `/api/notifications/statistics/` | 获取通知统计信息 |

#### 批量标记已读请求示例
```json
{
    "ids": ["uuid1", "uuid2", "uuid3"]
}
```

### 13.6 通知配置接口

| 接口 | 方法 | 路径 | 说明 |
|------|------|------|------|
| **配置列表** | GET | `/api/notifications/configs/` | 分页查询通知配置列表 |
| **配置详情** | GET | `/api/notifications/configs/{id}/` | 获取单个通知配置详情 |
| **创建配置** | POST | `/api/notifications/configs/` | 创建新的通知配置 |
| **更新配置** | PUT | `/api/notifications/configs/{id}/` | 完整更新通知配置 |
| **部分更新** | PATCH | `/api/notifications/configs/{id}/` | 部分更新通知配置 |
| **我的配置** | GET | `/api/notifications/configs/my_config/` | 获取当前用户配置 |
| **更新我的配置** | PUT | `/api/notifications/configs/my_config/` | 更新当前用户配置 |

#### 更新我的配置请求示例
```json
{
    "channel_settings": {
        "workflow_approval": {
            "inbox": true,
            "email": false,
            "sms": false
        }
    },
    "enable_inbox": true,
    "enable_email": true,
    "quiet_hours_enabled": true,
    "quiet_hours_start": "22:00",
    "quiet_hours_end": "08:00"
}
```

### 13.7 通知日志接口

| 接口 | 方法 | 路径 | 说明 |
|------|------|------|------|
| **日志列表** | GET | `/api/notifications/logs/` | 分页查询通知发送日志 |
| **日志详情** | GET | `/api/notifications/logs/{id}/` | 获取单个发送日志详情 |
| **创建日志** | POST | `/api/notifications/logs/` | 创建新的发送日志 |
| **更新日志** | PUT | `/api/notifications/logs/{id}/` | 完整更新发送日志 |
| **部分更新** | PATCH | `/api/notifications/logs/{id}/` | 部分更新发送日志 |

### 13.8 发送通知接口

| 接口 | 方法 | 路径 | 说明 |
|------|------|------|------|
| **发送通知** | POST | `/api/notifications/send/` | 发送单个通知 |
| **批量发送** | POST | `/api/notifications/send_batch/` | 批量发送通知 |

#### 发送通知请求示例
```json
{
    "recipient_id": "uuid",
    "notification_type": "workflow_approval",
    "variables": {
        "workflow_name": "采购审批",
        "submitter": "张三",
        "amount": 50000,
        "detail_url": "/workflows/123"
    },
    "channels": ["inbox", "email"],
    "priority": "high"
}
```

### 13.9 标准错误码

| 错误码 | HTTP状态 | 描述 |
|--------|----------|------|
| `VALIDATION_ERROR` | 400 | 请求数据验证失败 |
| `UNAUTHORIZED` | 401 | 未授权访问 |
| `PERMISSION_DENIED` | 403 | 权限不足 |
| `NOT_FOUND` | 404 | 资源不存在 |
| `METHOD_NOT_ALLOWED` | 405 | 方法不允许 |
| `CONFLICT` | 409 | 资源冲突 |
| `ORGANIZATION_MISMATCH` | 403 | 组织不匹配 |
| `SOFT_DELETED` | 410 | 资源已被软删除 |
| `RATE_LIMIT_EXCEEDED` | 429 | 请求频率超限 |
| `SERVER_ERROR` | 500 | 服务器内部错误 |

### 13.10 扩展接口示例

#### 13.10.1 模板分类统计接口
```http
GET /api/notifications/templates/stats/by_type/
```

响应示例：
```json
{
    "success": true,
    "data": {
        "by_channel": {
            "email": 15,
            "sms": 8,
            "wework": 12,
            "inbox": 25
        },
        "by_status": {
            "active": 45,
            "inactive": 15
        },
        "by_language": {
            "zh-CN": 50,
            "en-US": 5
        }
    }
}
```

#### 13.10.2 通知发送状态接口
```http
GET /api/notifications/status/distribution/
```

响应示例：
```json
{
    "success": true,
    "data": {
        "status_distribution": {
            "pending": 10,
            "sending": 5,
            "success": 100,
            "failed": 3,
            "cancelled": 2
        },
        "channel_distribution": {
            "inbox": 80,
            "email": 25,
            "sms": 10,
            "wework": 5
        },
        "priority_distribution": {
            "urgent": 5,
            "high": 15,
            "normal": 80,
            "low": 20
        }
    }
}
```

#### 13.10.3 用户通知偏好接口
```http
GET /api/notifications/preferences/channels/
```

响应示例：
```json
{
    "success": true,
    "data": {
        "available_channels": [
            {"code": "inbox", "name": "站内信", "enabled": true},
            {"code": "email", "name": "邮件", "enabled": true},
            {"code": "sms", "name": "短信", "enabled": false},
            {"code": "wework", "name": "企业微信", "enabled": true}
        ],
        "default_channels": {
            "workflow_approval": ["inbox", "wework"],
            "inventory_reminder": ["inbox", "sms"],
            "system_announcement": ["inbox"]
        }
    }
}
```

#### 13.10.4 模板搜索接口
```http
GET /api/notifications/templates/search/?q=审批&channel=email
```

响应示例：
```json
{
    "success": true,
    "data": {
        "count": 5,
        "results": [
            {
                "id": "uuid",
                "template_code": "workflow_approval",
                "template_name": "工作流审批通知",
                "channel": "email",
                "match_score": 0.95
            }
        ]
    }
}
```

#### 13.10.5 通知撤回接口
```http
POST /api/notifications/{id}/recall/
```

请求示例：
```json
{
    "reason": "内容有误"
}
```

响应示例：
```json
{
    "success": true,
    "message": "通知已撤回",
    "data": {
        "id": "uuid",
        "recalled_at": "2024-01-15T10:00:00Z",
        "recall_reason": "内容有误"
    }
}
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
