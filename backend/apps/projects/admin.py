"""
Django admin registration for projects module.
"""
from django.contrib import admin
from .models import AssetProject, ProjectAsset, ProjectMember


class ProjectAssetInline(admin.TabularInline):
    """Inline display of project asset allocations."""
    model = ProjectAsset
    extra = 0
    readonly_fields = ('allocation_no', 'allocation_date', 'allocation_cost',
                       'monthly_depreciation', 'return_status', 'created_at')
    fields = ('allocation_no', 'asset', 'allocation_type', 'allocated_by',
              'custodian', 'allocation_date', 'return_date', 'return_status',
              'allocation_cost', 'monthly_depreciation')


class ProjectMemberInline(admin.TabularInline):
    """Inline display of project members."""
    model = ProjectMember
    extra = 0
    readonly_fields = ('join_date', 'created_at')
    fields = ('user', 'role', 'is_primary', 'is_active',
              'can_allocate_asset', 'can_view_cost', 'join_date', 'leave_date')


@admin.register(AssetProject)
class AssetProjectAdmin(admin.ModelAdmin):
    """Admin configuration for AssetProject."""
    list_display = ('project_code', 'project_name', 'project_type',
                    'status', 'project_manager', 'department',
                    'start_date', 'end_date', 'total_assets', 'active_assets')
    list_filter = ('status', 'project_type', 'organization')
    search_fields = ('project_code', 'project_name', 'project_alias')
    readonly_fields = ('project_code', 'total_assets', 'active_assets',
                       'asset_cost', 'created_at', 'updated_at', 'created_by')
    inlines = [ProjectAssetInline, ProjectMemberInline]
    fieldsets = (
        ('Project Information', {
            'fields': ('project_code', 'project_name', 'project_alias',
                       'project_type', 'status', 'description',
                       'technical_requirements')
        }),
        ('Management', {
            'fields': ('project_manager', 'department', 'organization')
        }),
        ('Schedule', {
            'fields': ('start_date', 'end_date',
                       'actual_start_date', 'actual_end_date')
        }),
        ('Budget & Cost', {
            'fields': ('planned_budget', 'actual_cost', 'asset_cost')
        }),
        ('Metrics', {
            'fields': ('total_assets', 'active_assets',
                       'completed_milestones', 'total_milestones')
        }),
        ('Audit', {
            'classes': ('collapse',),
            'fields': ('created_by', 'created_at', 'updated_at')
        }),
    )


@admin.register(ProjectAsset)
class ProjectAssetAdmin(admin.ModelAdmin):
    """Admin configuration for ProjectAsset."""
    list_display = ('allocation_no', 'project', 'asset', 'allocation_type',
                    'return_status', 'allocation_date', 'allocation_cost')
    list_filter = ('return_status', 'allocation_type', 'organization')
    search_fields = ('allocation_no', 'project__project_code',
                     'asset__asset_code', 'asset__asset_name')
    readonly_fields = ('allocation_no', 'created_at', 'updated_at', 'created_by')


@admin.register(ProjectMember)
class ProjectMemberAdmin(admin.ModelAdmin):
    """Admin configuration for ProjectMember."""
    list_display = ('project', 'user', 'role', 'is_primary',
                    'is_active', 'join_date', 'leave_date')
    list_filter = ('role', 'is_active', 'is_primary', 'organization')
    search_fields = ('project__project_code', 'project__project_name',
                     'user__username', 'user__first_name', 'user__last_name')
    readonly_fields = ('created_at', 'updated_at', 'created_by')
