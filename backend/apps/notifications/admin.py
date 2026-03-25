"""
Notification Admin Configuration

Django admin configuration for notification models.
"""
from django.contrib import admin
from django.utils import timezone
from django.utils.html import format_html
from django.db.models import Count

from apps.notifications.models import (
    NotificationTemplate,
    Notification,
    NotificationLog,
    NotificationConfig,
    NotificationChannel,
    NotificationMessage,
    InAppMessage,
)


@admin.register(NotificationTemplate)
class NotificationTemplateAdmin(admin.ModelAdmin):
    """Admin interface for NotificationTemplate."""

    list_display = [
        'template_code',
        'template_name',
        'template_type',
        'channel',
        'language',
        'is_active',
        'version',
        'created_at',
    ]
    list_filter = ['template_type', 'channel', 'language', 'is_active', 'is_system']
    search_fields = ['template_code', 'template_name', 'description']
    readonly_fields = ['created_at', 'updated_at', 'created_by']
    fieldsets = (
        ('Basic Information', {
            'fields': (
                'template_code',
                'template_name',
                'template_type',
                'channel',
                'language',
            )
        }),
        ('Template Content', {
            'fields': (
                'subject_template',
                'content_template',
            )
        }),
        ('Variables', {
            'fields': (
                'variables',
                'example_data',
            ),
            'classes': ('collapse',),
        }),
        ('Configuration', {
            'fields': (
                'is_active',
                'is_system',
                'version',
                'previous_version',
            )
        }),
        ('Description', {
            'fields': ('description',),
            'classes': ('collapse',),
        }),
        ('Audit', {
            'fields': ('created_at', 'updated_at', 'created_by'),
            'classes': ('collapse',),
        }),
    )
    actions = ['activate_templates', 'deactivate_templates']

    def has_delete_permission(self, request, obj=None):
        """Prevent deletion of system templates."""
        if obj and obj.is_system:
            return False
        return super().has_delete_permission(request, obj)

    def activate_templates(self, request, queryset):
        """Activate selected templates."""
        updated = queryset.update(is_active=True)
        self.message_user(request, f'{updated} templates activated.')
    activate_templates.short_description = 'Activate selected templates'

    def deactivate_templates(self, request, queryset):
        """Deactivate selected templates (except system templates)."""
        queryset = queryset.filter(is_system=False)
        updated = queryset.update(is_active=False)
        self.message_user(request, f'{updated} templates deactivated.')
    deactivate_templates.short_description = 'Deactivate selected templates'


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    """Admin interface for Notification."""

    list_display = [
        'id',
        'recipient',
        'notification_type',
        'title',
        'channel',
        'priority',
        'status',
        'is_read',
        'scheduled_at',
        'sent_at',
        'created_at',
    ]
    list_filter = [
        'notification_type',
        'channel',
        'priority',
        'status',
        'created_at',
        'scheduled_at',
        'sent_at',
    ]
    search_fields = ['title', 'content', 'recipient__username', 'recipient__email']
    readonly_fields = [
        'id',
        'created_at',
        'updated_at',
        'sent_at',
        'next_retry_at',
    ]
    date_hierarchy = 'created_at'
    actions = ['mark_as_read', 'mark_as_unread', 'retry_failed']

    def is_read(self, obj):
        """Display read status."""
        return bool(obj.read_at)
    is_read.boolean = True
    is_read.short_description = 'Read'

    def mark_as_read(self, request, queryset):
        """Mark selected notifications as read."""
        updated = queryset.filter(read_at__isnull=True).update(
            read_at=timezone.now()
        )
        self.message_user(request, f'{updated} notifications marked as read.')
    mark_as_read.short_description = 'Mark as read'

    def mark_as_unread(self, request, queryset):
        """Mark selected notifications as unread."""
        updated = queryset.update(read_at=None)
        self.message_user(request, f'{updated} notifications marked as unread.')
    mark_as_unread.short_description = 'Mark as unread'

    def retry_failed(self, request, queryset):
        """Retry failed notifications."""
        failed = queryset.filter(status='failed')
        count = failed.count()
        # Update to pending for retry
        failed.update(status='pending', retry_count=0)
        self.message_user(request, f'{count} notifications queued for retry.')
    retry_failed.short_description = 'Retry failed notifications'

    def get_readonly_fields(self, request, obj=None):
        """Make recipient and type readonly when editing."""
        if obj:
            return self.readonly_fields + ['recipient', 'notification_type']
        return self.readonly_fields


@admin.register(NotificationLog)
class NotificationLogAdmin(admin.ModelAdmin):
    """Admin interface for NotificationLog (read-only)."""

    list_display = [
        'id',
        'notification_title',
        'channel',
        'status',
        'retry_count',
        'duration_ms',
        'error_code',
        'created_at',
    ]
    list_filter = ['channel', 'status', 'error_code', 'created_at']
    search_fields = ['error_message', 'external_id', 'notification__title']
    readonly_fields = [
        'id',
        'notification',
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
        'created_at',
    ]
    date_hierarchy = 'created_at'

    def has_add_permission(self, request):
        """Logs cannot be created manually."""
        return False

    def has_change_permission(self, request, obj=None):
        """Logs cannot be modified."""
        return False

    def has_delete_permission(self, request, obj=None):
        """Only admins can delete logs."""
        return request.user.is_superuser

    def notification_title(self, obj):
        """Display notification title."""
        if obj.notification:
            return obj.notification.title
        return '-'
    notification_title.short_description = 'Notification'

    def duration_ms(self, obj):
        """Display duration in milliseconds."""
        if obj.duration:
            return f'{obj.duration}ms'
        return '-'
    duration_ms.short_description = 'Duration'


@admin.register(NotificationConfig)
class NotificationConfigAdmin(admin.ModelAdmin):
    """Admin interface for NotificationConfig."""

    list_display = [
        'id',
        'user',
        'enable_inbox',
        'enable_email',
        'enable_sms',
        'enable_wework',
        'enable_dingtalk',
        'quiet_hours_enabled',
        'created_at',
    ]
    list_filter = [
        'enable_inbox',
        'enable_email',
        'enable_sms',
        'enable_wework',
        'enable_dingtalk',
        'quiet_hours_enabled',
    ]
    search_fields = ['user__username', 'user__email']
    readonly_fields = ['id', 'created_at', 'updated_at']
    fieldsets = (
        ('User', {
            'fields': ('user',)
        }),
        ('Channel Settings', {
            'fields': (
                'channel_settings',
                'enable_inbox',
                'enable_email',
                'enable_sms',
                'enable_wework',
                'enable_dingtalk',
            )
        }),
        ('Quiet Hours', {
            'fields': (
                'quiet_hours_enabled',
                'quiet_hours_start',
                'quiet_hours_end',
            ),
            'classes': ('collapse',),
        }),
        ('Contact Override', {
            'fields': (
                'email_address',
                'phone_number',
            ),
            'classes': ('collapse',),
        }),
        ('Audit', {
            'fields': ('id', 'created_at', 'updated_at'),
            'classes': ('collapse',),
        }),
    )

    def get_readonly_fields(self, request, obj=None):
        """Make user readonly when editing."""
        if obj:
            return self.readonly_fields + ['user']
        return self.readonly_fields


# Custom admin site configuration
class NotificationAdminSite(admin.AdminSite):
    """Custom admin site for notification management."""

    site_header = 'Notification Management'
    site_title = 'Notification Portal'
    index_title = 'Welcome to Notification Portal'

    def get_urls(self):
        """Add custom URLs for notification dashboard."""
        from django.urls import path
        urls = super().get_urls()
        custom_urls = [
            path('dashboard/', self.admin_view(self.dashboard), name='dashboard'),
        ]
        return custom_urls + urls

    def dashboard(self, request):
        """Notification dashboard view."""
        from django.template.response import TemplateResponse
        from apps.notifications.models import Notification, NotificationLog, NotificationTemplate

        # Get dashboard stats
        total_notifications = Notification.objects.count()
        pending_notifications = Notification.objects.filter(status='pending').count()
        failed_notifications = Notification.objects.filter(status='failed').count()

        total_templates = NotificationTemplate.objects.count()
        active_templates = NotificationTemplate.objects.filter(is_active=True).count()

        recent_logs = NotificationLog.objects.select_related(
            'notification'
        ).order_by('-created_at')[:10]

        context = {
            **self.each_context(request),
            'title': 'Notification Dashboard',
            'total_notifications': total_notifications,
            'pending_notifications': pending_notifications,
            'failed_notifications': failed_notifications,
            'total_templates': total_templates,
            'active_templates': active_templates,
            'recent_logs': recent_logs,
        }
        return TemplateResponse(request, 'admin/notifications/dashboard.html', context)


# Uncomment to enable separate admin site for notifications
# notification_admin = NotificationAdminSite(name='notifications_admin')
# notification_admin.register(NotificationTemplate, NotificationTemplateAdmin)
# notification_admin.register(Notification, NotificationAdmin)
# notification_admin.register(NotificationLog, NotificationLogAdmin)
# notification_admin.register(NotificationConfig, NotificationConfigAdmin)


# =============================================================================
# Admin classes for new models (Phase 2.3)
# =============================================================================

@admin.register(NotificationChannel)
class NotificationChannelAdmin(admin.ModelAdmin):
    """Admin interface for NotificationChannel."""

    list_display = [
        'channel_type',
        'channel_name',
        'priority',
        'is_enabled',
        'status',
        'consecutive_failures',
        'last_error_at',
        'created_at',
    ]
    list_filter = ['channel_type', 'is_enabled', 'status']
    search_fields = ['channel_type', 'channel_name', 'last_error_message']
    readonly_fields = [
        'id',
        'created_at',
        'updated_at',
        'last_error_at',
        'consecutive_failures',
        'created_by',
    ]
    fieldsets = (
        ('Basic Information', {
            'fields': (
                'channel_type',
                'channel_name',
                'priority',
            )
        }),
        ('Configuration', {
            'fields': (
                'config',
                'template_mapping',
            ),
            'classes': ('collapse',),
        }),
        ('Status', {
            'fields': (
                'is_enabled',
                'status',
            )
        }),
        ('Rate Limiting', {
            'fields': (
                'rate_limit_per_minute',
                'rate_limit_per_hour',
            ),
            'classes': ('collapse',),
        }),
        ('Retry Settings', {
            'fields': (
                'max_retries',
                'retry_delay_seconds',
            ),
            'classes': ('collapse',),
        }),
        ('Error Tracking', {
            'fields': (
                'last_error_at',
                'last_error_message',
                'consecutive_failures',
            ),
            'classes': ('collapse',),
        }),
        ('Webhook', {
            'fields': (
                'webhook_url',
                'webhook_secret',
            ),
            'classes': ('collapse',),
        }),
        ('Audit', {
            'fields': ('id', 'created_at', 'updated_at', 'created_by'),
            'classes': ('collapse',),
        }),
    )
    actions = ['enable_channels', 'disable_channels', 'reset_errors']

    def enable_channels(self, request, queryset):
        """Enable selected channels."""
        updated = queryset.update(is_enabled=True, status='active')
        self.message_user(request, f'{updated} channels enabled.')
    enable_channels.short_description = 'Enable selected channels'

    def disable_channels(self, request, queryset):
        """Disable selected channels."""
        updated = queryset.update(is_enabled=False)
        self.message_user(request, f'{updated} channels disabled.')
    disable_channels.short_description = 'Disable selected channels'

    def reset_errors(self, request, queryset):
        """Reset error counters for selected channels."""
        updated = queryset.update(
            consecutive_failures=0,
            last_error_at=None,
            last_error_message='',
            status='active'
        )
        self.message_user(request, f'{updated} channels error counters reset.')
    reset_errors.short_description = 'Reset error counters'


@admin.register(NotificationMessage)
class NotificationMessageAdmin(admin.ModelAdmin):
    """Admin interface for NotificationMessage."""

    list_display = [
        'message_code',
        'notification_type',
        'title',
        'target_type',
        'status',
        'priority',
        'progress',
        'total_recipients',
        'sent_count',
        'failed_count',
        'scheduled_at',
        'created_at',
    ]
    list_filter = [
        'notification_type',
        'status',
        'priority',
        'target_type',
        'created_at',
        'scheduled_at',
    ]
    search_fields = [
        'message_code',
        'title',
        'content',
        'notification_type',
    ]
    readonly_fields = [
        'id',
        'message_code',
        'created_at',
        'updated_at',
        'sent_at',
        'progress',
        'sent_count',
        'failed_count',
    ]
    date_hierarchy = 'created_at'
    fieldsets = (
        ('Basic Information', {
            'fields': (
                'message_code',
                'notification_type',
                'title',
                'content',
                'subject',
            )
        }),
        ('Targeting', {
            'fields': (
                'target_type',
                'target_ids',
                'total_recipients',
            )
        }),
        ('Channels', {
            'fields': (
                'channels',
                'primary_channel',
            )
        }),
        ('Status & Scheduling', {
            'fields': (
                'status',
                'priority',
                'scheduled_at',
                'sent_at',
            )
        }),
        ('Statistics', {
            'fields': (
                'sent_count',
                'failed_count',
                'read_count',
                'progress',
            ),
            'classes': ('collapse',),
        }),
        ('Template', {
            'fields': (
                'template',
                'data',
            ),
            'classes': ('collapse',),
        }),
        ('Related Object', {
            'fields': (
                'related_content_type',
                'related_object_id',
            ),
            'classes': ('collapse',),
        }),
        ('Sender', {
            'fields': ('sender',),
            'classes': ('collapse',),
        }),
        ('Error', {
            'fields': ('error_message',),
            'classes': ('collapse',),
        }),
        ('Audit', {
            'fields': ('id', 'created_at', 'updated_at', 'created_by'),
            'classes': ('collapse',),
        }),
    )
    actions = ['send_messages', 'cancel_messages']

    def send_messages(self, request, queryset):
        """Send selected pending messages."""
        from apps.notifications.services import notification_service
        count = 0
        for message in queryset.filter(status='draft'):
            # Generate message code if not set
            if not message.message_code:
                message.generate_message_code()
                message.save(update_fields=['message_code'])

            # Get recipients and send
            recipient_ids = message.get_recipient_users()
            message.total_recipients = len(recipient_ids)

            sent_count = 0
            failed_count = 0
            for recipient_id in recipient_ids:
                result = notification_service.send(
                    recipient=recipient_id,
                    notification_type=message.notification_type,
                    variables=message.data,
                    channels=message.channels,
                    priority=message.priority,
                    sender=message.sender,
                )
                if result['success']:
                    sent_count += 1
                else:
                    failed_count += 1

            message.update_progress(sent_count, failed_count)
            count += 1

        self.message_user(request, f'{count} messages sent.')
    send_messages.short_description = 'Send selected messages'

    def cancel_messages(self, request, queryset):
        """Cancel selected pending messages."""
        updated = queryset.filter(
            status__in=['draft', 'pending']
        ).update(status='cancelled')
        self.message_user(request, f'{updated} messages cancelled.')
    cancel_messages.short_description = 'Cancel selected messages'


@admin.register(InAppMessage)
class InAppMessageAdmin(admin.ModelAdmin):
    """Admin interface for InAppMessage."""

    list_display = [
        'id',
        'message_type',
        'title',
        'priority',
        'status',
        'show_popup',
        'publish_at',
        'expire_at',
        'view_count',
        'acknowledge_count',
        'created_at',
    ]
    list_filter = [
        'message_type',
        'status',
        'priority',
        'show_popup',
        'requires_acknowledgment',
        'created_at',
        'publish_at',
    ]
    search_fields = ['title', 'content']
    readonly_fields = [
        'id',
        'created_at',
        'updated_at',
        'view_count',
        'acknowledge_count',
        'dismiss_count',
    ]
    date_hierarchy = 'created_at'
    fieldsets = (
        ('Basic Information', {
            'fields': (
                'message_type',
                'title',
                'content',
                'priority',
            )
        }),
        ('Display Settings', {
            'fields': (
                'show_popup',
                'dismissible',
                'requires_acknowledgment',
            )
        }),
        ('Targeting', {
            'fields': (
                'target_type',
                'target_ids',
                'exclude_users',
            ),
            'classes': ('collapse',),
        }),
        ('Scheduling', {
            'fields': (
                'status',
                'publish_at',
                'expire_at',
            )
        }),
        ('Statistics', {
            'fields': (
                'view_count',
                'acknowledge_count',
                'dismiss_count',
            ),
            'classes': ('collapse',),
        }),
        ('Action Button', {
            'fields': (
                'action_url',
                'action_label',
            ),
            'classes': ('collapse',),
        }),
        ('Related Object', {
            'fields': (
                'related_content_type',
                'related_object_id',
            ),
            'classes': ('collapse',),
        }),
        ('Author', {
            'fields': ('author',),
            'classes': ('collapse',),
        }),
        ('Audit', {
            'fields': ('id', 'created_at', 'updated_at', 'created_by'),
            'classes': ('collapse',),
        }),
    )
    actions = ['publish_messages', 'archive_messages']

    def publish_messages(self, request, queryset):
        """Publish selected draft messages."""
        count = 0
        for message in queryset.filter(status='draft'):
            message.publish()
            count += 1
        self.message_user(request, f'{count} messages published.')
    publish_messages.short_description = 'Publish selected messages'

    def archive_messages(self, request, queryset):
        """Archive selected messages."""
        updated = queryset.update(status='archived')
        self.message_user(request, f'{updated} messages archived.')
    archive_messages.short_description = 'Archive selected messages'
