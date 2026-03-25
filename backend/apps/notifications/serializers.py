"""
Notification Serializers

All serializers inherit from BaseModelSerializer for automatic
serialization of common fields and custom_fields support.
"""
from rest_framework import serializers
from apps.common.serializers.base import (
    BaseModelSerializer,
    BaseModelWithAuditSerializer
)
from apps.notifications.models import (
    NotificationTemplate,
    Notification,
    NotificationLog,
    NotificationConfig,
    NotificationChannel,
    NotificationMessage,
    InAppMessage,
)


class NotificationTemplateSerializer(BaseModelSerializer):
    """Notification template serializer."""

    channel_display = serializers.CharField(
        source='get_channel_display',
        read_only=True
    )

    class Meta(BaseModelSerializer.Meta):
        model = NotificationTemplate
        fields = BaseModelSerializer.Meta.fields + [
            'template_code',
            'template_name',
            'template_type',
            'channel',
            'channel_display',
            'subject_template',
            'content_template',
            'variables',
            'language',
            'is_active',
            'is_system',
            'version',
            'previous_version',
            'description',
            'example_data',
        ]


class NotificationTemplateDetailSerializer(BaseModelWithAuditSerializer):
    """Notification template detail serializer with full audit info."""

    previous_version_detail = NotificationTemplateSerializer(
        source='previous_version',
        read_only=True,
        allow_null=True
    )

    class Meta(BaseModelWithAuditSerializer.Meta):
        model = NotificationTemplate
        fields = BaseModelWithAuditSerializer.Meta.fields + [
            'template_code',
            'template_name',
            'template_type',
            'channel',
            'channel_display',
            'subject_template',
            'content_template',
            'variables',
            'language',
            'is_active',
            'is_system',
            'version',
            'previous_version',
            'previous_version_detail',
            'description',
            'example_data',
        ]


class NotificationSerializer(BaseModelSerializer):
    """Notification serializer."""

    recipient_name = serializers.CharField(
        source='recipient.username',
        read_only=True
    )
    recipient_email = serializers.EmailField(
        source='recipient.email',
        read_only=True,
        allow_null=True
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
    priority_display = serializers.CharField(
        source='get_priority_display',
        read_only=True
    )
    channel_display = serializers.CharField(
        source='get_channel_display',
        read_only=True
    )
    status_display = serializers.CharField(
        source='get_status_display',
        read_only=True
    )

    class Meta(BaseModelSerializer.Meta):
        model = Notification
        fields = BaseModelSerializer.Meta.fields + [
            'recipient',
            'recipient_name',
            'recipient_email',
            'template',
            'template_name',
            'notification_type',
            'priority',
            'priority_display',
            'channel',
            'channel_display',
            'title',
            'content',
            'data',
            'status',
            'status_display',
            'scheduled_at',
            'sent_at',
            'read_at',
            'retry_count',
            'max_retries',
            'next_retry_at',
            'related_content_type',
            'related_object_id',
            'sender',
            'sender_name',
        ]


class NotificationListSerializer(BaseModelSerializer):
    """Notification list serializer - optimized for list views."""

    recipient_name = serializers.CharField(
        source='recipient.username',
        read_only=True
    )
    priority_display = serializers.CharField(
        source='get_priority_display',
        read_only=True
    )
    status_display = serializers.CharField(
        source='get_status_display',
        read_only=True
    )
    is_read = serializers.SerializerMethodField()

    class Meta(BaseModelSerializer.Meta):
        model = Notification
        fields = BaseModelSerializer.Meta.fields + [
            'recipient',
            'recipient_name',
            'notification_type',
            'priority',
            'priority_display',
            'channel',
            'channel_display',
            'title',
            'status',
            'status_display',
            'is_read',
            'read_at',
            'scheduled_at',
            'sent_at',
        ]

    def get_is_read(self, obj):
        """Check if notification is read."""
        return obj.read_at is not None


class NotificationLogSerializer(BaseModelSerializer):
    """Notification log serializer."""

    notification_title = serializers.CharField(
        source='notification.title',
        read_only=True,
        allow_null=True
    )

    class Meta(BaseModelSerializer.Meta):
        model = NotificationLog
        fields = BaseModelSerializer.Meta.fields + [
            'notification',
            'notification_title',
            'channel',
            'status',
            'request_data',
            'response_data',
            'error_code',
            'error_message',
            'retry_count',
            'duration',
            'external_id',
            'external_status',
        ]


class NotificationConfigSerializer(BaseModelSerializer):
    """Notification configuration serializer."""

    user_name = serializers.CharField(
        source='user.username',
        read_only=True
    )
    user_email = serializers.EmailField(
        source='user.email',
        read_only=True,
        allow_null=True
    )

    class Meta(BaseModelSerializer.Meta):
        model = NotificationConfig
        fields = BaseModelSerializer.Meta.fields + [
            'user',
            'user_name',
            'user_email',
            'channel_settings',
            'enable_inbox',
            'enable_email',
            'enable_sms',
            'enable_wework',
            'enable_dingtalk',
            'quiet_hours_enabled',
            'quiet_hours_start',
            'quiet_hours_end',
            'email_address',
            'phone_number',
        ]


class NotificationConfigUpdateSerializer(serializers.Serializer):
    """Notification configuration update serializer."""

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
    phone_number = serializers.CharField(
        required=False,
        allow_blank=True,
        max_length=20
    )

    def update(self, instance, validated_data):
        """Update configuration."""
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        return instance


class SendNotificationSerializer(serializers.Serializer):
    """Send notification serializer."""

    recipient_id = serializers.UUIDField(help_text='Recipient user ID')
    notification_type = serializers.CharField(
        max_length=50,
        help_text='Notification type code'
    )
    variables = serializers.JSONField(
        default=dict,
        help_text='Template variables'
    )
    channels = serializers.ListField(
        child=serializers.CharField(max_length=20),
        required=False,
        help_text='Specific channels to use'
    )
    priority = serializers.ChoiceField(
        choices=['urgent', 'high', 'normal', 'low'],
        default='normal',
        required=False
    )
    scheduled_at = serializers.DateTimeField(
        allow_null=True,
        required=False,
        help_text='Schedule send time'
    )


class BatchSendNotificationSerializer(serializers.Serializer):
    """Batch send notification serializer."""

    recipient_ids = serializers.ListField(
        child=serializers.UUIDField(),
        help_text='List of recipient user IDs'
    )
    notification_type = serializers.CharField(
        max_length=50,
        help_text='Notification type code'
    )
    variables = serializers.JSONField(
        default=dict,
        help_text='Template variables'
    )
    channels = serializers.ListField(
        child=serializers.CharField(max_length=20),
        required=False,
        help_text='Specific channels to use'
    )
    priority = serializers.ChoiceField(
        choices=['urgent', 'high', 'normal', 'low'],
        default='normal',
        required=False
    )


# =============================================================================
# NotificationChannel Serializers
# =============================================================================

class NotificationChannelSerializer(BaseModelSerializer):
    """Notification channel configuration serializer."""

    channel_type_display = serializers.CharField(
        source='get_channel_type_display',
        read_only=True
    )
    status_display = serializers.CharField(
        source='get_status_display',
        read_only=True
    )
    is_available = serializers.SerializerMethodField()

    class Meta(BaseModelSerializer.Meta):
        model = NotificationChannel
        fields = BaseModelSerializer.Meta.fields + [
            'channel_type',
            'channel_type_display',
            'channel_name',
            'config',
            'priority',
            'is_enabled',
            'status',
            'status_display',
            'rate_limit_per_minute',
            'rate_limit_per_hour',
            'max_retries',
            'retry_delay_seconds',
            'template_mapping',
            'last_error_at',
            'last_error_message',
            'consecutive_failures',
            'webhook_url',
            'is_available',
        ]

    def get_is_available(self, obj):
        """Check if channel is available."""
        return obj.is_available()


class NotificationChannelUpdateSerializer(serializers.Serializer):
    """Notification channel configuration update serializer."""

    channel_name = serializers.CharField(required=False, max_length=100)
    config = serializers.JSONField(required=False)
    priority = serializers.IntegerField(required=False, min_value=0)
    is_enabled = serializers.BooleanField(required=False)
    rate_limit_per_minute = serializers.IntegerField(required=False, min_value=1)
    rate_limit_per_hour = serializers.IntegerField(required=False, min_value=1)
    max_retries = serializers.IntegerField(required=False, min_value=0)
    retry_delay_seconds = serializers.IntegerField(required=False, min_value=0)
    template_mapping = serializers.JSONField(required=False)
    webhook_url = serializers.URLField(required=False, allow_blank=True)
    webhook_secret = serializers.CharField(required=False, allow_blank=True, max_length=100)

    def update(self, instance, validated_data):
        """Update channel configuration."""
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        return instance


class NotificationChannelTestSerializer(serializers.Serializer):
    """Test channel connectivity serializer."""

    recipient = serializers.CharField(help_text='Test recipient address')
    message = serializers.CharField(help_text='Test message content')


# =============================================================================
# NotificationMessage Serializers
# =============================================================================

class NotificationMessageSerializer(BaseModelSerializer):
    """Centralized notification message tracking serializer."""

    priority_display = serializers.CharField(
        source='get_priority_display',
        read_only=True
    )
    status_display = serializers.CharField(
        source='get_status_display',
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
    progress_percentage = serializers.IntegerField(
        source='progress',
        read_only=True
    )

    class Meta(BaseModelSerializer.Meta):
        model = NotificationMessage
        fields = BaseModelSerializer.Meta.fields + [
            'message_code',
            'notification_type',
            'title',
            'content',
            'subject',
            'template',
            'template_name',
            'target_type',
            'target_ids',
            'channels',
            'primary_channel',
            'priority',
            'priority_display',
            'status',
            'status_display',
            'scheduled_at',
            'sent_at',
            'total_recipients',
            'sent_count',
            'failed_count',
            'read_count',
            'progress',
            'progress_percentage',
            'data',
            'related_content_type',
            'related_object_id',
            'sender',
            'sender_name',
            'error_message',
        ]


class NotificationMessageListSerializer(BaseModelSerializer):
    """Notification message list serializer - optimized for list views."""

    status_display = serializers.CharField(
        source='get_status_display',
        read_only=True
    )
    priority_display = serializers.CharField(
        source='get_priority_display',
        read_only=True
    )
    progress_percentage = serializers.IntegerField(read_only=True)

    class Meta(BaseModelSerializer.Meta):
        model = NotificationMessage
        fields = BaseModelSerializer.Meta.fields + [
            'message_code',
            'notification_type',
            'title',
            'status',
            'status_display',
            'priority',
            'priority_display',
            'scheduled_at',
            'sent_at',
            'total_recipients',
            'sent_count',
            'failed_count',
            'progress',
            'progress_percentage',
        ]


class NotificationMessageCreateSerializer(serializers.Serializer):
    """Create notification message serializer."""

    notification_type = serializers.CharField(max_length=50)
    title = serializers.CharField(max_length=200)
    content = serializers.CharField()
    subject = serializers.CharField(max_length=200, required=False, allow_blank=True)
    template_id = serializers.UUIDField(required=False, allow_null=True)
    target_type = serializers.CharField(
        max_length=20,
        help_text='Target type: user, role, department, all'
    )
    target_ids = serializers.ListField(
        child=serializers.CharField(),
        default=list,
        required=False
    )
    channels = serializers.ListField(
        child=serializers.CharField(max_length=20),
        default=list,
        required=False,
        help_text='Channels to use: inbox, email, wework, etc.'
    )
    primary_channel = serializers.CharField(max_length=20, required=False, allow_blank=True)
    priority = serializers.ChoiceField(
        choices=['urgent', 'high', 'normal', 'low'],
        default='normal',
        required=False
    )
    scheduled_at = serializers.DateTimeField(required=False, allow_null=True)
    data = serializers.JSONField(default=dict, required=False)
    sender_id = serializers.UUIDField(required=False, allow_null=True)

    def validate(self, data):
        """Validate notification message data."""
        if data.get('target_type') != 'all' and not data.get('target_ids'):
            raise serializers.ValidationError(
                {'target_ids': 'This field is required when target_type is not "all"'}
            )
        return data


class NotificationMessageSendSerializer(serializers.Serializer):
    """Send notification message serializer."""

    message_id = serializers.UUIDField(help_text='Notification message ID to send')


# =============================================================================
# InAppMessage Serializers
# =============================================================================

class InAppMessageSerializer(BaseModelSerializer):
    """In-app message serializer."""

    message_type_display = serializers.CharField(
        source='get_message_type_display',
        read_only=True
    )
    priority_display = serializers.CharField(
        source='get_priority_display',
        read_only=True
    )
    status_display = serializers.CharField(
        source='get_status_display',
        read_only=True
    )
    author_name = serializers.CharField(
        source='author.username',
        read_only=True,
        allow_null=True
    )
    is_active = serializers.SerializerMethodField()

    class Meta(BaseModelSerializer.Meta):
        model = InAppMessage
        fields = BaseModelSerializer.Meta.fields + [
            'message_type',
            'message_type_display',
            'title',
            'content',
            'priority',
            'priority_display',
            'status',
            'status_display',
            'target_type',
            'target_ids',
            'exclude_users',
            'show_popup',
            'dismissible',
            'requires_acknowledgment',
            'publish_at',
            'expire_at',
            'view_count',
            'acknowledge_count',
            'dismiss_count',
            'action_url',
            'action_label',
            'related_content_type',
            'related_object_id',
            'author',
            'author_name',
            'is_active',
        ]

    def get_is_active(self, obj):
        """Check if message is currently active."""
        return obj.is_active()


class InAppMessageListSerializer(BaseModelSerializer):
    """In-app message list serializer - optimized for list views."""

    message_type_display = serializers.CharField(
        source='get_message_type_display',
        read_only=True
    )
    status_display = serializers.CharField(
        source='get_status_display',
        read_only=True
    )
    is_active = serializers.SerializerMethodField()

    class Meta(BaseModelSerializer.Meta):
        model = InAppMessage
        fields = BaseModelSerializer.Meta.fields + [
            'message_type',
            'message_type_display',
            'title',
            'status',
            'status_display',
            'priority',
            'show_popup',
            'publish_at',
            'expire_at',
            'view_count',
            'acknowledge_count',
            'is_active',
        ]

    def get_is_active(self, obj):
        """Check if message is currently active."""
        return obj.is_active()


class InAppMessageCreateSerializer(serializers.Serializer):
    """Create in-app message serializer."""

    message_type = serializers.ChoiceField(
        choices=['announcement', 'system', 'reminder', 'user'],
        default='announcement'
    )
    title = serializers.CharField(max_length=200)
    content = serializers.CharField()
    priority = serializers.ChoiceField(
        choices=['urgent', 'high', 'normal', 'low'],
        default='normal'
    )
    target_type = serializers.CharField(
        max_length=20,
        default='all',
        help_text='Target: all, users, roles, departments'
    )
    target_ids = serializers.ListField(
        child=serializers.CharField(),
        default=list,
        required=False
    )
    exclude_users = serializers.ListField(
        child=serializers.CharField(),
        default=list,
        required=False
    )
    show_popup = serializers.BooleanField(default=False)
    dismissible = serializers.BooleanField(default=True)
    requires_acknowledgment = serializers.BooleanField(default=False)
    publish_at = serializers.DateTimeField(required=False, allow_null=True)
    expire_at = serializers.DateTimeField(required=False, allow_null=True)
    action_url = serializers.URLField(required=False, allow_blank=True)
    action_label = serializers.CharField(max_length=50, required=False, allow_blank=True)

    def validate(self, data):
        """Validate in-app message data."""
        if data.get('requires_acknowledgment') and data.get('dismissible', True):
            # If acknowledgment is required, message should not be simply dismissible
            pass
        return data


class InAppMessageActionSerializer(serializers.Serializer):
    """In-app message action serializer."""

    action = serializers.ChoiceField(
        choices=['publish', 'archive', 'increment_view', 'increment_acknowledge', 'increment_dismiss']
    )
