"""
Notification Filters

Filter classes for notification models.
All filters inherit from BaseModelFilter for consistent filtering behavior.
"""
import django_filters
from django_filters import rest_framework as filters

from apps.common.filters.base import BaseModelFilter
from apps.notifications.models import (
    NotificationTemplate,
    Notification,
    NotificationLog,
    NotificationConfig,
)


class NotificationTemplateFilter(BaseModelFilter):
    """Filter for NotificationTemplate model."""

    template_code = django_filters.CharFilter(
        lookup_expr='iexact',
        help_text='Exact template code match'
    )
    template_code__icontains = django_filters.CharFilter(
        field_name='template_code',
        lookup_expr='icontains',
        help_text='Template code contains'
    )
    template_name = django_filters.CharFilter(
        lookup_expr='icontains',
        help_text='Template name contains'
    )
    template_type = django_filters.CharFilter(
        lookup_expr='iexact',
        help_text='Exact template type match'
    )
    channel = django_filters.ChoiceFilter(
        choices=NotificationTemplate.CHANNEL_TYPES,
        help_text='Filter by channel'
    )
    language = django_filters.CharFilter(
        lookup_expr='iexact',
        help_text='Filter by language code'
    )
    is_active = django_filters.BooleanFilter(
        help_text='Filter by active status'
    )
    is_system = django_filters.BooleanFilter(
        help_text='Filter by system template flag'
    )
    version = django_filters.NumberFilter(
        help_text='Filter by version number'
    )
    version__gte = django_filters.NumberFilter(
        field_name='version',
        lookup_expr='gte',
        help_text='Version greater than or equal'
    )
    version__lte = django_filters.NumberFilter(
        field_name='version',
        lookup_expr='lte',
        help_text='Version less than or equal'
    )

    class Meta:
        model = NotificationTemplate
        fields = [
            'template_code',
            'template_type',
            'channel',
            'language',
            'is_active',
            'is_system',
            'version',
            'created_at',
            'updated_at',
        ]


class NotificationFilter(BaseModelFilter):
    """Filter for Notification model."""

    recipient = django_filters.UUIDFilter(
        help_text='Filter by recipient user ID'
    )
    template = django_filters.UUIDFilter(
        help_text='Filter by template ID'
    )
    notification_type = django_filters.CharFilter(
        lookup_expr='iexact',
        help_text='Exact notification type match'
    )
    notification_type__icontains = django_filters.CharFilter(
        field_name='notification_type',
        lookup_expr='icontains',
        help_text='Notification type contains'
    )
    priority = django_filters.ChoiceFilter(
        choices=Notification.PRIORITIES,
        help_text='Filter by priority'
    )
    channel = django_filters.ChoiceFilter(
        choices=NotificationTemplate.CHANNEL_TYPES,
        help_text='Filter by channel'
    )
    status = django_filters.ChoiceFilter(
        choices=Notification.STATUSES,
        help_text='Filter by delivery status'
    )
    is_read = django_filters.BooleanFilter(
        method='filter_is_read',
        help_text='Filter by read status'
    )
    scheduled_at = django_filters.DateTimeFilter(
        help_text='Filter by scheduled time'
    )
    scheduled_at__gte = django_filters.DateTimeFilter(
        field_name='scheduled_at',
        lookup_expr='gte',
        help_text='Scheduled at or after'
    )
    scheduled_at__lte = django_filters.DateTimeFilter(
        field_name='scheduled_at',
        lookup_expr='lte',
        help_text='Scheduled at or before'
    )
    sent_at = django_filters.DateTimeFilter(
        help_text='Filter by sent time'
    )
    sent_at__gte = django_filters.DateTimeFilter(
        field_name='sent_at',
        lookup_expr='gte',
        help_text='Sent at or after'
    )
    sent_at__lte = django_filters.DateTimeFilter(
        field_name='sent_at',
        lookup_expr='lte',
        help_text='Sent at or before'
    )
    read_at = django_filters.DateTimeFilter(
        help_text='Filter by read time'
    )
    read_at__gte = django_filters.DateTimeFilter(
        field_name='read_at',
        lookup_expr='gte',
        help_text='Read at or after'
    )
    read_at__lte = django_filters.DateTimeFilter(
        field_name='read_at',
        lookup_expr='lte',
        help_text='Read at or before'
    )
    read_at__isnull = django_filters.BooleanFilter(
        field_name='read_at',
        lookup_expr='isnull',
        help_text='Read status (null check)'
    )
    sender = django_filters.UUIDFilter(
        help_text='Filter by sender user ID'
    )
    title = django_filters.CharFilter(
        lookup_expr='icontains',
        help_text='Title contains'
    )
    content = django_filters.CharFilter(
        lookup_expr='icontains',
        help_text='Content contains'
    )
    retry_count = django_filters.NumberFilter(
        help_text='Filter by retry count'
    )
    retry_count__gte = django_filters.NumberFilter(
        field_name='retry_count',
        lookup_expr='gte',
        help_text='Retry count greater than or equal'
    )

    class Meta:
        model = Notification
        fields = [
            'recipient',
            'template',
            'notification_type',
            'priority',
            'channel',
            'status',
            'sender',
            'scheduled_at',
            'sent_at',
            'read_at',
            'retry_count',
            'created_at',
            'updated_at',
        ]

    def filter_is_read(self, queryset, name, value):
        """Filter by read status using read_at field."""
        if value is True:
            return queryset.filter(read_at__isnull=False)
        elif value is False:
            return queryset.filter(read_at__isnull=True)
        return queryset


class NotificationLogFilter(BaseModelFilter):
    """Filter for NotificationLog model."""

    notification = django_filters.UUIDFilter(
        help_text='Filter by notification ID'
    )
    channel = django_filters.CharFilter(
        lookup_expr='iexact',
        help_text='Filter by channel'
    )
    status = django_filters.CharFilter(
        lookup_expr='iexact',
        help_text='Filter by log status'
    )
    error_code = django_filters.CharFilter(
        lookup_expr='iexact',
        help_text='Filter by error code'
    )
    error_code__icontains = django_filters.CharFilter(
        field_name='error_code',
        lookup_expr='icontains',
        help_text='Error code contains'
    )
    retry_count = django_filters.NumberFilter(
        help_text='Filter by retry attempt number'
    )
    duration = django_filters.NumberFilter(
        help_text='Filter by duration (ms)'
    )
    duration__gte = django_filters.NumberFilter(
        field_name='duration',
        lookup_expr='gte',
        help_text='Duration greater than or equal (ms)'
    )
    duration__lte = django_filters.NumberFilter(
        field_name='duration',
        lookup_expr='lte',
        help_text='Duration less than or equal (ms)'
    )
    external_id = django_filters.CharFilter(
        lookup_expr='icontains',
        help_text='External ID contains'
    )
    external_status = django_filters.CharFilter(
        lookup_expr='iexact',
        help_text='Filter by external status'
    )

    class Meta:
        model = NotificationLog
        fields = [
            'notification',
            'channel',
            'status',
            'error_code',
            'retry_count',
            'duration',
            'external_id',
            'external_status',
            'created_at',
        ]


class NotificationConfigFilter(BaseModelFilter):
    """Filter for NotificationConfig model."""

    user = django_filters.UUIDFilter(
        help_text='Filter by user ID'
    )
    enable_inbox = django_filters.BooleanFilter(
        help_text='Filter by inbox enabled status'
    )
    enable_email = django_filters.BooleanFilter(
        help_text='Filter by email enabled status'
    )
    enable_sms = django_filters.BooleanFilter(
        help_text='Filter by SMS enabled status'
    )
    enable_wework = django_filters.BooleanFilter(
        help_text='Filter by WeWork enabled status'
    )
    enable_dingtalk = django_filters.BooleanFilter(
        help_text='Filter by DingTalk enabled status'
    )
    quiet_hours_enabled = django_filters.BooleanFilter(
        help_text='Filter by quiet hours enabled status'
    )

    class Meta:
        model = NotificationConfig
        fields = [
            'user',
            'enable_inbox',
            'enable_email',
            'enable_sms',
            'enable_wework',
            'enable_dingtalk',
            'quiet_hours_enabled',
            'created_at',
        ]
