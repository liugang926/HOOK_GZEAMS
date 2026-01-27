"""
Django admin configuration for organizations app.
"""
from django.contrib import admin
from django.utils.html import format_html
from apps.organizations.models import Organization, Department, UserDepartment


@admin.register(Organization)
class OrganizationAdmin(admin.ModelAdmin):
    """Admin interface for Organization model."""

    list_display = [
        'name', 'code', 'org_type', 'parent_name',
        'is_active', 'level', 'created_at'
    ]
    list_filter = ['org_type', 'is_active', 'is_deleted', 'created_at']
    search_fields = ['name', 'code', 'contact_person', 'email']
    readonly_fields = [
        'id', 'level', 'path', 'created_at', 'updated_at',
        'invite_code', 'invite_code_expires_at', 'is_invite_code_valid',
        'created_by'
    ]
    fieldsets = (
        ('Basic Information', {
            'fields': (
                'name', 'code', 'org_type', 'parent'
            )
        }),
        ('Contact Information', {
            'fields': (
                'contact_person', 'contact_phone', 'email', 'address'
            )
        }),
        ('Financial', {
            'fields': ('credit_code',),
            'classes': ('collapse',),
        }),
        ('WeWork Integration', {
            'fields': (
                'wework_dept_id', 'wework_parent_id'
            ),
            'classes': ('collapse',),
        }),
        ('Invite Code', {
            'fields': (
                'invite_code', 'invite_code_expires_at', 'is_invite_code_valid'
            ),
            'classes': ('collapse',),
        }),
        ('Status', {
            'fields': ('is_active', 'is_deleted')
        }),
        ('Audit', {
            'fields': ('id', 'created_at', 'updated_at', 'created_by'),
            'classes': ('collapse',),
        }),
    )
    actions = ['activate_organizations', 'deactivate_organizations']

    def parent_name(self, obj):
        """Display parent name."""
        return obj.parent.name if obj.parent else '-'
    parent_name.short_description = 'Parent'

    def is_invite_code_valid(self, obj):
        """Display invite code validity."""
        return obj.is_invite_code_valid()
    is_invite_code_valid.boolean = True
    is_invite_code_valid.short_description = 'Invite Valid'

    def activate_organizations(self, request, queryset):
        """Activate selected organizations."""
        updated = queryset.update(is_active=True)
        self.message_user(request, f'{updated} organizations activated.')
    activate_organizations.short_description = 'Activate selected'

    def deactivate_organizations(self, request, queryset):
        """Deactivate selected organizations."""
        updated = queryset.update(is_active=False)
        self.message_user(request, f'{updated} organizations deactivated.')
    deactivate_organizations.short_description = 'Deactivate selected'


@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    """Admin interface for Department model."""

    list_display = [
        'code', 'name', 'full_path_display', 'leader_name',
        'level', 'is_active', 'order', 'created_at'
    ]
    list_filter = ['level', 'is_active', 'is_deleted', 'created_at']
    search_fields = ['code', 'name', 'full_path', 'full_path_name']
    readonly_fields = [
        'id', 'level', 'path', 'full_path', 'full_path_name',
        'created_at', 'updated_at', 'created_by'
    ]
    fieldsets = (
        ('Basic Information', {
            'fields': (
                'code', 'name', 'parent', 'leader', 'order'
            )
        }),
        ('Hierarchy', {
            'fields': (
                'level', 'path', 'full_path', 'full_path_name'
            ),
            'classes': ('collapse',),
        }),
        ('SSO Sync - WeWork', {
            'fields': (
                'wework_dept_id', 'wework_leader_id'
            ),
            'classes': ('collapse',),
        }),
        ('SSO Sync - DingTalk', {
            'fields': (
                'dingtalk_dept_id', 'dingtalk_leader_id'
            ),
            'classes': ('collapse',),
        }),
        ('SSO Sync - Feishu', {
            'fields': (
                'feishu_dept_id', 'feishu_leader_id'
            ),
            'classes': ('collapse',),
        }),
        ('Status', {
            'fields': ('is_active',)
        }),
        ('Audit', {
            'fields': ('id', 'created_at', 'updated_at', 'created_by'),
            'classes': ('collapse',),
        }),
    )
    actions = ['activate_departments', 'deactivate_departments']

    def full_path_display(self, obj):
        """Display full path with truncated display."""
        path = obj.full_path_name
        if len(path) > 50:
            return path[:47] + '...'
        return path
    full_path_display.short_description = 'Full Path'

    def leader_name(self, obj):
        """Display leader name."""
        if obj.leader:
            return getattr(obj.leader, 'real_name', obj.leader.username)
        return '-'
    leader_name.short_description = 'Leader'

    def activate_departments(self, request, queryset):
        """Activate selected departments."""
        updated = queryset.update(is_active=True)
        self.message_user(request, f'{updated} departments activated.')
    activate_departments.short_description = 'Activate selected'

    def deactivate_departments(self, request, queryset):
        """Deactivate selected departments."""
        updated = queryset.update(is_active=False)
        self.message_user(request, f'{updated} departments deactivated.')
    deactivate_departments.short_description = 'Deactivate selected'


@admin.register(UserDepartment)
class UserDepartmentAdmin(admin.ModelAdmin):
    """Admin interface for UserDepartment model."""

    list_display = [
        'user_display', 'department_display', 'is_primary',
        'is_asset_department', 'is_leader', 'position',
        'created_at'
    ]
    list_filter = ['is_primary', 'is_asset_department', 'is_leader', 'created_at']
    search_fields = ['user__username', 'user__real_name', 'department__name', 'position']
    readonly_fields = ['id', 'created_at', 'updated_at', 'created_by']
    fieldsets = (
        ('Association', {
            'fields': (
                'user', 'department', 'organization'
            )
        }),
        ('Flags', {
            'fields': (
                'is_primary', 'is_asset_department', 'is_leader'
            )
        }),
        ('Position', {
            'fields': ('position',)
        }),
        ('WeWork Sync', {
            'fields': (
                'wework_department_order', 'is_primary_in_wework'
            ),
            'classes': ('collapse',),
        }),
        ('Audit', {
            'fields': ('id', 'created_at', 'updated_at', 'created_by'),
            'classes': ('collapse',),
        }),
    )
    actions = ['set_primary', 'unset_primary', 'set_leader', 'unset_leader']

    def user_display(self, obj):
        """Display user name."""
        if obj.user:
            return getattr(obj.user, 'real_name', obj.user.username)
        return '-'
    user_display.short_description = 'User'

    def department_display(self, obj):
        """Display department path."""
        if obj.department:
            return obj.department.full_path_name
        return '-'
    department_display.short_description = 'Department'

    def set_primary(self, request, queryset):
        """Set selected associations as primary."""
        count = 0
        for obj in queryset:
            obj.is_primary = True
            obj.save(update_fields=['is_primary'])
            count += 1
        self.message_user(request, f'{count} associations set as primary.')
    set_primary.short_description = 'Set as primary'

    def unset_primary(self, request, queryset):
        """Unset primary flag from selected associations."""
        updated = queryset.update(is_primary=False)
        self.message_user(request, f'{updated} associations updated.')
    unset_primary.short_description = 'Unset primary'

    def set_leader(self, request, queryset):
        """Set selected associations as leader."""
        updated = queryset.update(is_leader=True)
        self.message_user(request, f'{updated} associations set as leader.')
    set_leader.short_description = 'Set as leader'

    def unset_leader(self, request, queryset):
        """Unset leader flag from selected associations."""
        updated = queryset.update(is_leader=False)
        self.message_user(request, f'{updated} associations updated.')
    unset_leader.short_description = 'Unset leader'
