"""
Django Admin configuration for User management.
"""
from django.contrib import admin
from django.contrib.auth import get_user_model

from apps.accounts.models import UserOrganization

User = get_user_model()


@admin.register(UserOrganization)
class UserOrganizationAdmin(admin.ModelAdmin):
    """Admin interface for UserOrganization."""

    list_display = ['user', 'organization', 'role', 'is_active', 'is_primary', 'joined_at']
    list_filter = ['role', 'is_active', 'is_primary']
    search_fields = ['user__username', 'user__email', 'organization__name']
    readonly_fields = ['joined_at']
    ordering = ['-joined_at']


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    """
    Admin interface for User model.

    Custom admin for the custom User model with multi-organization support.
    """

    list_display = [
        'username', 'email', 'first_name', 'last_name',
        'is_active', 'is_staff', 'is_superuser',
        'current_organization', 'date_joined'
    ]
    list_filter = [
        'is_active', 'is_staff', 'is_superuser',
        'is_deleted', 'date_joined'
    ]
    search_fields = ['username', 'email', 'first_name', 'last_name']
    readonly_fields = [
        'date_joined', 'last_login',
        'wework_userid', 'wework_unionid',
        'dingtalk_userid', 'dingtalk_unionid',
        'feishu_userid', 'feishu_unionid',
        'created_at', 'updated_at', 'deleted_at',
        'created_by', 'updated_by', 'deleted_by'
    ]
    ordering = ['-date_joined']

    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        ('Personal info', {'fields': ('first_name', 'last_name', 'email')}),
        ('Organization', {'fields': ('current_organization',)}),
        ('SSO Integration', {
            'fields': (
                'wework_userid', 'wework_unionid',
                'dingtalk_userid', 'dingtalk_unionid',
                'feishu_userid', 'feishu_unionid',
            ),
            'classes': ('collapse',),
        }),
        ('Permissions', {
            'fields': (
                'is_active', 'is_staff', 'is_superuser',
                'groups', 'user_permissions'
            ),
        }),
        ('Important dates', {'fields': ('last_login', 'date_joined')}),
        ('Audit', {
            'fields': ('is_deleted', 'deleted_at', 'created_at', 'updated_at', 'created_by'),
            'classes': ('collapse',),
        }),
    )

    def get_queryset(self, request):
        """Use soft delete aware queryset."""
        qs = super().get_queryset(request)
        return qs.filter(is_deleted=False)
