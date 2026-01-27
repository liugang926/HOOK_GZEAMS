"""
Django admin configuration for permissions app.
"""
from django.contrib import admin
from django.utils.html import format_html
from django.db.models import Count

from apps.permissions.models import (
    FieldPermission,
    DataPermission,
    DataPermissionExpand,
    PermissionAuditLog,
)


@admin.register(FieldPermission)
class FieldPermissionAdmin(admin.ModelAdmin):
    """Admin interface for FieldPermission."""

    list_display = [
        'id',
        'target_display',
        'content_type_display',
        'field_name',
        'permission_type',
        'mask_rule_display',
        'priority',
        'is_active',
        'created_at',
    ]
    list_filter = [
        'permission_type',
        'mask_rule',
        'is_deleted',
        'created_at',
    ]
    search_fields = [
        'field_name',
        'description',
        'user__username',
        'content_type__model',
    ]
    readonly_fields = [
        'id',
        'created_at',
        'updated_at',
        'created_by',
    ]
    fieldsets = (
        ('Target', {
            'fields': ('user',)
        }),
        ('Content Type', {
            'fields': (
                'content_type',
                'field_name',
            )
        }),
        ('Permission', {
            'fields': (
                'permission_type',
                'mask_rule',
                'custom_mask_pattern',
            )
        }),
        ('Condition & Priority', {
            'fields': (
                'condition',
                'priority',
                'description',
            ),
            'classes': ('collapse',),
        }),
        ('Audit', {
            'fields': ('id', 'created_at', 'updated_at', 'created_by'),
            'classes': ('collapse',),
        }),
    )
    actions = ['activate_permissions', 'deactivate_permissions']

    def target_display(self, obj):
        """Display target (user)."""
        if obj.user:
            return format_html('<span style="color: #e67e22;">User: {}</span>', obj.user.username)
        return '-'
    target_display.short_description = 'Target'

    def content_type_display(self, obj):
        """Display content type."""
        return f'{obj.content_type.app_label}.{obj.content_type.model}'
    content_type_display.short_description = 'Content Type'

    def mask_rule_display(self, obj):
        """Display mask rule."""
        if obj.mask_rule:
            return obj.get_mask_rule_display()
        return '-'
    mask_rule_display.short_description = 'Mask Rule'

    def is_active(self, obj):
        """Check if permission is active (not deleted)."""
        return not obj.is_deleted
    is_active.boolean = True
    is_active.short_description = 'Active'

    def activate_permissions(self, request, queryset):
        """Mark permissions as active (undelete)."""
        updated = queryset.filter(is_deleted=True).update(
            is_deleted=False,
            deleted_at=None
        )
        self.message_user(request, f'{updated} permissions activated.')
    activate_permissions.short_description = 'Activate selected'

    def deactivate_permissions(self, request, queryset):
        """Soft delete selected permissions."""
        count = 0
        for obj in queryset:
            obj.soft_delete(request.user)
            count += 1
        self.message_user(request, f'{count} permissions deactivated.')
    deactivate_permissions.short_description = 'Deactivate selected'


@admin.register(DataPermission)
class DataPermissionAdmin(admin.ModelAdmin):
    """Admin interface for DataPermission."""

    list_display = [
        'id',
        'target_display',
        'content_type_display',
        'scope_type_display',
        'is_active',
        'created_at',
    ]
    list_filter = [
        'scope_type',
        'is_deleted',
        'created_at',
    ]
    search_fields = [
        'description',
        'user__username',
        'content_type__model',
    ]
    readonly_fields = [
        'id',
        'created_at',
        'updated_at',
        'created_by',
    ]
    fieldsets = (
        ('Target', {
            'fields': ('user',)
        }),
        ('Content Type', {
            'fields': ('content_type',)
        }),
        ('Scope', {
            'fields': (
                'scope_type',
                'scope_value',
                'department_field',
                'user_field',
            )
        }),
        ('Description', {
            'fields': ('description',),
            'classes': ('collapse',),
        }),
        ('Audit', {
            'fields': ('id', 'created_at', 'updated_at', 'created_by'),
            'classes': ('collapse',),
        }),
    )
    actions = ['activate_permissions', 'deactivate_permissions']

    def target_display(self, obj):
        """Display target (user)."""
        if obj.user:
            return format_html('<span style="color: #e67e22;">User: {}</span>', obj.user.username)
        return '-'
    target_display.short_description = 'Target'

    def content_type_display(self, obj):
        """Display content type."""
        return f'{obj.content_type.app_label}.{obj.content_type.model}'
    content_type_display.short_description = 'Content Type'

    def scope_type_display(self, obj):
        """Display scope type with color coding."""
        colors = {
            'all': '#27ae60',
            'self': '#95a5a6',
            'self_dept': '#3498db',
            'self_and_sub': '#9b59b6',
            'specified': '#e67e22',
            'custom': '#c0392b',
        }
        color = colors.get(obj.scope_type, '#000')
        return format_html(
            '<span style="color: {};">{}</span>',
            color,
            obj.get_scope_type_display()
        )
    scope_type_display.short_description = 'Scope Type'

    def is_active(self, obj):
        """Check if permission is active (not deleted)."""
        return not obj.is_deleted
    is_active.boolean = True
    is_active.short_description = 'Active'

    def activate_permissions(self, request, queryset):
        """Mark permissions as active (undelete)."""
        updated = queryset.filter(is_deleted=True).update(
            is_deleted=False,
            deleted_at=None
        )
        self.message_user(request, f'{updated} permissions activated.')
    activate_permissions.short_description = 'Activate selected'

    def deactivate_permissions(self, request, queryset):
        """Soft delete selected permissions."""
        count = 0
        for obj in queryset:
            obj.soft_delete(request.user)
            count += 1
        self.message_user(request, f'{count} permissions deactivated.')
    deactivate_permissions.short_description = 'Deactivate selected'


@admin.register(DataPermissionExpand)
class DataPermissionExpandAdmin(admin.ModelAdmin):
    """Admin interface for DataPermissionExpand."""

    list_display = [
        'id',
        'data_permission_display',
        'priority',
        'is_active',
        'actions_count',
        'created_at',
    ]
    list_filter = [
        'is_active',
        'priority',
        'is_deleted',
        'created_at',
    ]
    search_fields = [
        'description',
        'data_permission__content_type__model',
    ]
    readonly_fields = [
        'id',
        'created_at',
        'updated_at',
        'created_by',
    ]
    fieldsets = (
        ('Base Permission', {
            'fields': ('data_permission',)
        }),
        ('Conditions', {
            'fields': (
                'filter_conditions',
                'allowed_fields',
                'denied_fields',
                'actions',
            )
        }),
        ('Settings', {
            'fields': (
                'priority',
                'is_active',
                'description',
            )
        }),
        ('Audit', {
            'fields': ('id', 'created_at', 'updated_at', 'created_by'),
            'classes': ('collapse',),
        }),
    )
    actions = ['activate_expansions', 'deactivate_expansions']

    def data_permission_display(self, obj):
        """Display data permission."""
        if obj.data_permission:
            return f'{obj.data_permission.content_type.model} - {obj.data_permission.get_scope_type_display()}'
        return '-'
    data_permission_display.short_description = 'Data Permission'

    def actions_count(self, obj):
        """Count allowed actions."""
        return len(obj.actions) if obj.actions else 0
    actions_count.short_description = 'Actions'

    def activate_expansions(self, request, queryset):
        """Activate selected expansions."""
        updated = queryset.update(is_active=True)
        self.message_user(request, f'{updated} expansions activated.')
    activate_expansions.short_description = 'Activate selected'

    def deactivate_expansions(self, request, queryset):
        """Deactivate selected expansions."""
        updated = queryset.update(is_active=False)
        self.message_user(request, f'{updated} expansions deactivated.')
    deactivate_expansions.short_description = 'Deactivate selected'


@admin.register(PermissionAuditLog)
class PermissionAuditLogAdmin(admin.ModelAdmin):
    """Admin interface for PermissionAuditLog (read-only)."""

    list_display = [
        'id',
        'actor_display',
        'target_display',
        'operation_type_display',
        'target_type_display',
        'result_display',
        'ip_address',
        'created_at',
    ]
    list_filter = [
        'operation_type',
        'target_type',
        'result',
        'created_at',
    ]
    search_fields = [
        'actor__username',
        'target_user__username',
        'error_message',
        'permission_details',
    ]
    readonly_fields = [
        'id',
        'actor',
        'target_user',
        'operation_type',
        'target_type',
        'permission_details',
        'content_type',
        'object_id',
        'result',
        'error_message',
        'ip_address',
        'user_agent',
        'request_metadata',
        'created_at',
    ]
    date_hierarchy = 'created_at'

    def has_add_permission(self, request):
        """Audit logs cannot be created manually."""
        return False

    def has_change_permission(self, request, obj=None):
        """Audit logs cannot be modified."""
        return False

    def has_delete_permission(self, request, obj=None):
        """Only admins can delete logs."""
        return request.user.is_superuser

    def actor_display(self, obj):
        """Display actor."""
        if obj.actor:
            return obj.actor.username
        return 'System'
    actor_display.short_description = 'Actor'

    def target_display(self, obj):
        """Display target (user)."""
        if obj.target_user:
            return f'User: {obj.target_user.username}'
        return '-'
    target_display.short_description = 'Target'

    def operation_type_display(self, obj):
        """Display operation type with color."""
        colors = {
            'check': '#95a5a6',
            'grant': '#27ae60',
            'revoke': '#e74c3c',
            'modify': '#f39c12',
            'deny': '#c0392b',
        }
        color = colors.get(obj.operation_type, '#000')
        return format_html(
            '<span style="color: {};">{}</span>',
            color,
            obj.get_operation_type_display()
        )
    operation_type_display.short_description = 'Operation'

    def target_type_display(self, obj):
        """Display target type."""
        return obj.get_target_type_display()
    target_type_display.short_description = 'Target Type'

    def result_display(self, obj):
        """Display result with color."""
        colors = {
            'success': '#27ae60',
            'failure': '#e74c3c',
            'partial': '#f39c12',
        }
        color = colors.get(obj.result, '#000')
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color,
            obj.get_result_display().upper()
        )
    result_display.short_description = 'Result'
