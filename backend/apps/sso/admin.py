"""
SSO Admin Configuration

Django admin configuration for SSO models.
"""
from django.contrib import admin
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _

from apps.sso.models import WeWorkConfig, UserMapping, OAuthState, SyncLog


@admin.register(WeWorkConfig)
class WeWorkConfigAdmin(admin.ModelAdmin):
    """Admin interface for WeWorkConfig."""

    list_display = [
        'corp_name',
        'corp_id',
        'agent_id',
        'is_enabled',
        'auto_create_user',
        'organization',
        'created_at',
    ]
    list_filter = ['is_enabled', 'auto_create_user', 'sync_department', 'sync_user']
    search_fields = ['corp_name', 'corp_id']
    readonly_fields = ['created_at', 'updated_at', 'created_by']

    fieldsets = (
        (_('WeWork Credentials'), {
            'fields': ('corp_id', 'corp_name', 'agent_id', 'agent_secret')
        }),
        (_('Sync Settings'), {
            'fields': ('sync_department', 'sync_user', 'auto_create_user', 'default_role_id')
        }),
        (_('Callback Settings'), {
            'fields': ('redirect_uri',)
        }),
        (_('Status'), {
            'fields': ('is_enabled',)
        }),
        (_('Organization'), {
            'fields': ('organization',)
        }),
        (_('Audit Info'), {
            'fields': ('created_at', 'updated_at', 'created_by'),
            'classes': ('collapse',)
        }),
    )

    def save_model(self, request, obj, form, change):
        """Set created_by on creation."""
        if not change and not obj.created_by_id:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(UserMapping)
class UserMappingAdmin(admin.ModelAdmin):
    """Admin interface for UserMapping."""

    list_display = [
        'system_user',
        'platform',
        'platform_userid',
        'platform_name',
        'organization',
        'created_at',
    ]
    list_filter = ['platform']
    search_fields = ['platform_name', 'platform_userid', 'system_user__username']
    readonly_fields = ['created_at', 'updated_at', 'created_by']

    fieldsets = (
        (_('System User'), {
            'fields': ('system_user',)
        }),
        (_('Platform Info'), {
            'fields': ('platform', 'platform_userid', 'platform_unionid', 'platform_name')
        }),
        (_('Extra Data'), {
            'fields': ('extra_data',)
        }),
        (_('Organization'), {
            'fields': ('organization',)
        }),
        (_('Audit Info'), {
            'fields': ('created_at', 'updated_at', 'created_by'),
            'classes': ('collapse',)
        }),
    )

    def save_model(self, request, obj, form, change):
        """Set created_by on creation."""
        if not change and not obj.created_by_id:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(OAuthState)
class OAuthStateAdmin(admin.ModelAdmin):
    """Admin interface for OAuthState."""

    list_display = [
        'state',
        'platform',
        'consumed',
        'expires_at',
        'created_at',
        'is_valid_display',
    ]
    list_filter = ['platform', 'consumed']
    search_fields = ['state']
    readonly_fields = ['created_at', 'consumed_at']

    fieldsets = (
        (_('OAuth State'), {
            'fields': ('state', 'platform', 'session_data')
        }),
        (_('Status'), {
            'fields': ('consumed', 'consumed_at', 'expires_at')
        }),
        (_('Audit Info'), {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )

    def is_valid_display(self, obj):
        """Display if state is valid."""
        if obj.is_valid():
            return format_html('<span style="color: green;">Valid</span>')
        return format_html('<span style="color: red;">Invalid</span>')
    is_valid_display.short_description = 'Is Valid'


@admin.register(SyncLog)
class SyncLogAdmin(admin.ModelAdmin):
    """Admin interface for SyncLog."""

    list_display = [
        'sync_type_display',
        'sync_source_display',
        'status_display',
        'total_count',
        'created_count',
        'updated_count',
        'failed_count',
        'duration_display',
        'started_at',
        'organization',
    ]
    list_filter = ['sync_type', 'sync_source', 'status']
    search_fields = ['organization__name', 'error_message']
    readonly_fields = ['started_at', 'finished_at', 'duration', 'created_at', 'created_by']

    fieldsets = (
        (_('Sync Info'), {
            'fields': ('sync_type', 'sync_source', 'status')
        }),
        (_('Statistics'), {
            'fields': ('total_count', 'created_count', 'updated_count',
                       'deleted_count', 'failed_count')
        }),
        (_('Timestamps'), {
            'fields': ('started_at', 'finished_at', 'duration')
        }),
        (_('Error Info'), {
            'fields': ('error_message', 'error_details'),
            'classes': ('collapse',)
        }),
        (_('Organization'), {
            'fields': ('organization',)
        }),
        (_('Audit Info'), {
            'fields': ('created_at', 'updated_at', 'created_by'),
            'classes': ('collapse',)
        }),
    )

    def sync_type_display(self, obj):
        """Display sync type with color."""
        colors = {
            'full': 'blue',
            'department': 'green',
            'user': 'orange',
        }
        color = colors.get(obj.sync_type, 'gray')
        return format_html('<span style="color: {};">{}</span>',
                         color, obj.get_sync_type_display())
    sync_type_display.short_description = 'Sync Type'

    def sync_source_display(self, obj):
        """Display sync source."""
        return obj.get_sync_source_display()
    sync_source_display.short_description = 'Source'

    def status_display(self, obj):
        """Display status with color."""
        colors = {
            'running': 'blue',
            'success': 'green',
            'failed': 'red',
            'partial': 'orange',
        }
        color = colors.get(obj.status, 'gray')
        return format_html('<span style="color: {};">{}</span>',
                         color, obj.get_status_display())
    status_display.short_description = 'Status'

    def duration_display(self, obj):
        """Display duration."""
        if obj.duration:
            return f"{obj.duration}s"
        return '-'
    duration_display.short_description = 'Duration'

    def has_delete_permission(self, request, obj=None):
        """Disable delete from admin UI."""
        return False

    def has_add_permission(self, request):
        """Disable add from admin UI (sync logs are created by system)."""
        return False
