"""
Admin Configuration for Mobile Enhancement Module.

Registers all mobile models with Django admin interface.
"""
from django.contrib import admin
from django.utils import timezone
from django.utils.html import format_html
from apps.mobile.models import (
    MobileDevice,
    DeviceSecurityLog,
    OfflineData,
    SyncConflict,
    SyncLog,
    ApprovalDelegate,
)


@admin.register(MobileDevice)
class MobileDeviceAdmin(admin.ModelAdmin):
    """Admin interface for MobileDevice model."""

    list_display = [
        'device_id',
        'device_name',
        'device_type',
        'user_link',
        'is_bound',
        'is_active',
        'last_login_at',
        'last_sync_at',
        'created_at',
    ]
    list_filter = ['device_type', 'is_bound', 'is_active', 'created_at']
    search_fields = ['device_id', 'device_name', 'user__username', 'user__email']
    readonly_fields = [
        'device_id', 'created_at', 'updated_at', 'created_by', 'deleted_at',
        'last_login_at', 'last_sync_at',
    ]
    date_hierarchy = 'created_at'

    fieldsets = (
        ('Device Information', {
            'fields': ('device_id', 'device_name', 'device_type', 'user')
        }),
        ('Device Details', {
            'fields': ('os_version', 'app_version', 'device_info')
        }),
        ('Status', {
            'fields': ('is_bound', 'is_active', 'enable_biometric', 'allow_offline')
        }),
        ('Activity Tracking', {
            'fields': ('last_login_at', 'last_login_ip', 'last_sync_at', 'last_location')
        }),
        ('Audit Information', {
            'fields': ('created_at', 'updated_at', 'created_by', 'is_deleted', 'deleted_at'),
            'classes': ('collapse',)
        }),
    )

    def user_link(self, obj):
        """Display user as clickable link."""
        if obj.user:
            return format_html('<a href="/admin/auth/user/{}/">{}</a>',
                             obj.user.id, obj.user.username)
        return '-'
    user_link.short_description = 'User'

    def get_queryset(self, request):
        """Show only active records by default."""
        qs = super().get_queryset(request)
        if request.GET.get('is_deleted__exact') == '1':
            return qs
        return qs.filter(is_deleted=False)


@admin.register(DeviceSecurityLog)
class DeviceSecurityLogAdmin(admin.ModelAdmin):
    """Admin interface for DeviceSecurityLog model."""

    list_display = [
        'id',
        'device_link',
        'event_type',
        'ip_address',
        'location_display',
        'created_at',
    ]
    list_filter = ['event_type', 'created_at']
    search_fields = ['device__device_id', 'device__device_name', 'ip_address']
    readonly_fields = ['device', 'event_type', 'ip_address', 'location', 'details', 'created_at']
    date_hierarchy = 'created_at'

    def device_link(self, obj):
        """Display device as clickable link."""
        if obj.device:
            return format_html('<a href="/admin/mobile/mobiledevice/{}">{}</a>',
                             obj.device.id, obj.device.device_name)
        return '-'
    device_link.short_description = 'Device'

    def location_display(self, obj):
        """Display location in readable format."""
        if obj.location:
            return f"{obj.location.get('latitude', 'N/A')}, {obj.location.get('longitude', 'N/A')}"
        return '-'
    location_display.short_description = 'Location'

    def has_add_permission(self, request):
        """Security logs should not be manually added."""
        return False

    def has_change_permission(self, request, obj=None):
        """Security logs should not be modified."""
        return False


@admin.register(OfflineData)
class OfflineDataAdmin(admin.ModelAdmin):
    """Admin interface for OfflineData model."""

    list_display = [
        'id',
        'table_name',
        'record_id',
        'operation',
        'sync_status',
        'user_link',
        'device_link',
        'client_created_at',
        'synced_at',
    ]
    list_filter = ['operation', 'sync_status', 'table_name', 'client_created_at']
    search_fields = ['table_name', 'record_id', 'user__username', 'device__device_id']
    readonly_fields = [
        'user', 'device', 'table_name', 'record_id', 'operation',
        'data', 'client_version', 'server_version',
        'client_created_at', 'synced_at', 'created_at'
    ]
    date_hierarchy = 'client_created_at'

    def user_link(self, obj):
        """Display user as clickable link."""
        if obj.user:
            return format_html('<a href="/admin/auth/user/{}">{}</a>',
                             obj.user.id, obj.user.username)
        return '-'
    user_link.short_description = 'User'

    def device_link(self, obj):
        """Display device as clickable link."""
        if obj.device:
            return format_html('<a href="/admin/mobile/mobiledevice/{}">{}</a>',
                             obj.device.id, obj.device.device_name)
        return '-'
    device_link.short_description = 'Device'

    def has_add_permission(self, request):
        """Offline data should not be manually added."""
        return False

    def has_change_permission(self, request, obj=None):
        """Offline data sync status can be modified for debugging."""
        return request.user.is_superuser


@admin.register(SyncConflict)
class SyncConflictAdmin(admin.ModelAdmin):
    """Admin interface for SyncConflict model."""

    list_display = [
        'id',
        'table_name',
        'conflict_type',
        'resolution',
        'user_link',
        'created_at',
        'resolved_at',
    ]
    list_filter = ['conflict_type', 'resolution', 'created_at', 'resolved_at']
    search_fields = ['table_name', 'record_id', 'user__username']
    readonly_fields = [
        'user', 'offline_data', 'conflict_type', 'table_name',
        'record_id', 'local_data', 'server_data', 'resolution',
        'merged_data', 'resolution_note', 'resolved_at', 'created_at'
    ]
    date_hierarchy = 'created_at'

    def table_name(self, obj):
        """Get table name from offline data."""
        if obj.offline_data:
            return obj.offline_data.table_name
        return '-'
    table_name.short_description = 'Table'

    def user_link(self, obj):
        """Display user as clickable link."""
        if obj.user:
            return format_html('<a href="/admin/auth/user/{}">{}</a>',
                             obj.user.id, obj.user.username)
        return '-'
    user_link.short_description = 'User'

    def get_queryset(self, request):
        """Show only active records by default."""
        qs = super().get_queryset(request)
        if request.GET.get('is_deleted__exact') == '1':
            return qs
        return qs.filter(is_deleted=False)


@admin.register(SyncLog)
class SyncLogAdmin(admin.ModelAdmin):
    """Admin interface for SyncLog model."""

    list_display = [
        'id',
        'sync_type',
        'sync_direction',
        'status',
        'user_link',
        'device_link',
        'upload_count',
        'download_count',
        'conflict_count',
        'duration_display',
        'started_at',
        'finished_at',
    ]
    list_filter = ['sync_type', 'sync_direction', 'status', 'started_at']
    search_fields = ['user__username', 'device__device_id', 'error_message']
    readonly_fields = [
        'user', 'device', 'sync_type', 'sync_direction', 'status',
        'upload_count', 'download_count', 'conflict_count', 'duration',
        'error_message', 'started_at', 'finished_at', 'created_at'
    ]
    date_hierarchy = 'started_at'

    def user_link(self, obj):
        """Display user as clickable link."""
        if obj.user:
            return format_html('<a href="/admin/auth/user/{}">{}</a>',
                             obj.user.id, obj.user.username)
        return '-'
    user_link.short_description = 'User'

    def device_link(self, obj):
        """Display device as clickable link."""
        if obj.device:
            return format_html('<a href="/admin/mobile/mobiledevice/{}">{}</a>',
                             obj.device.id, obj.device.device_name)
        return '-'
    device_link.short_description = 'Device'

    def duration_display(self, obj):
        """Display duration in readable format."""
        if obj.duration:
            if obj.duration < 60:
                return f"{obj.duration}s"
            return f"{obj.duration // 60}m {obj.duration % 60}s"
        return '-'
    duration_display.short_description = 'Duration'

    def has_add_permission(self, request):
        """Sync logs should not be manually added."""
        return False

    def has_change_permission(self, request, obj=None):
        """Sync logs should not be modified."""
        return False


@admin.register(ApprovalDelegate)
class ApprovalDelegateAdmin(admin.ModelAdmin):
    """Admin interface for ApprovalDelegate model."""

    list_display = [
        'id',
        'delegator_link',
        'delegate_link',
        'delegate_type',
        'is_valid_display',
        'is_active',
        'is_revoked',
        'start_time',
        'end_time',
        'created_at',
    ]
    list_filter = ['delegate_type', 'delegate_scope', 'is_active', 'is_revoked', 'created_at']
    search_fields = ['delegator__username', 'delegate__username']
    readonly_fields = [
        'delegator', 'delegate', 'delegate_type', 'delegate_scope',
        'is_active', 'is_revoked', 'revoked_at', 'revoked_by',
        'start_time', 'end_time', 'created_at', 'updated_at', 'created_by', 'deleted_at'
    ]
    date_hierarchy = 'created_at'

    fieldsets = (
        ('Delegation Information', {
            'fields': ('delegator', 'delegate', 'delegate_type', 'delegate_scope')
        }),
        ('Status', {
            'fields': ('is_active', 'is_revoked', 'start_time', 'end_time')
        }),
        ('Revocation Details', {
            'fields': ('revoked_at', 'revoked_by', 'revoked_reason'),
            'classes': ('collapse',)
        }),
        ('Audit Information', {
            'fields': ('created_at', 'updated_at', 'created_by', 'is_deleted', 'deleted_at'),
            'classes': ('collapse',)
        }),
    )

    def delegator_link(self, obj):
        """Display delegator as clickable link."""
        if obj.delegator:
            return format_html('<a href="/admin/auth/user/{}">{}</a>',
                             obj.delegator.id, obj.delegator.username)
        return '-'
    delegator_link.short_description = 'Delegator'

    def delegate_link(self, obj):
        """Display delegate as clickable link."""
        if obj.delegate:
            return format_html('<a href="/admin/auth/user/{}">{}</a>',
                             obj.delegate.id, obj.delegate.username)
        return '-'
    delegate_link.short_description = 'Delegate'

    def is_valid_display(self, obj):
        """Display validation status with color."""
        is_valid = obj.is_valid()
        color = 'green' if is_valid else 'red'
        status = 'Valid' if is_valid else 'Invalid'
        return format_html('<span style="color: {};">{}</span>', color, status)
    is_valid_display.short_description = 'Is Valid'

    def get_queryset(self, request):
        """Show only active records by default."""
        qs = super().get_queryset(request)
        if request.GET.get('is_deleted__exact') == '1':
            return qs
        return qs.filter(is_deleted=False)


# Customize admin site headers
admin.site.site_header = 'Hook Fixed Assets Administration'
admin.site.site_title = 'Hook Admin'
admin.site.index_title = 'Welcome to Hook Fixed Assets Admin Portal'
