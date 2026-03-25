"""
Admin configuration for inventory app.
"""
from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from django.utils.html import format_html

from apps.inventory.models import (
    InventoryTask,
    InventorySnapshot,
    InventoryScan,
    InventoryDifference,
    InventoryTaskExecutor,
)


@admin.register(InventoryTask)
class InventoryTaskAdmin(admin.ModelAdmin):
    """Admin interface for InventoryTask."""

    list_display = [
        'task_code',
        'task_name',
        'inventory_type',
        'status',
        'organization',
        'total_count',
        'scanned_count',
        'progress_percentage',
        'planned_date',
        'created_at',
    ]
    list_filter = ['inventory_type', 'status', 'created_at', 'planned_date']
    search_fields = ['task_code', 'task_name', 'description']
    readonly_fields = [
        'task_code',
        'total_count',
        'scanned_count',
        'normal_count',
        'surplus_count',
        'missing_count',
        'damaged_count',
        'location_changed_count',
        'progress_percentage',
        'started_at',
        'completed_at',
        'created_at',
        'updated_at',
        'created_by',
        'updated_by',
        'deleted_by',
    ]
    fieldsets = (
        (_('Basic Information'), {
            'fields': ('task_code', 'task_name', 'description', 'organization')
        }),
        (_('Inventory Configuration'), {
            'fields': (
                'inventory_type',
                'department',
                'category',
                'sample_ratio',
            )
        }),
        (_('Status & Scheduling'), {
            'fields': ('status', 'planned_date', 'started_at', 'completed_at')
        }),
        (_('Statistics'), {
            'fields': (
                'total_count',
                'scanned_count',
                'normal_count',
                'surplus_count',
                'missing_count',
                'damaged_count',
                'location_changed_count',
                'progress_percentage',
            )
        }),
        (_('Additional'), {
            'fields': ('notes', 'created_by')
        }),
    )

    def progress_percentage(self, obj):
        """Display progress as a progress bar."""
        if obj.total_count > 0:
            percentage = (obj.scanned_count / obj.total_count) * 100
            color = 'green' if percentage >= 80 else 'orange' if percentage >= 50 else 'red'
            return format_html(
                '<div style="width: 100px; background: #eee; border-radius: 4px;">'
                '<div style="width: {}%; background: {}; border-radius: 4px; height: 20px;">'
                '{:.1f}%'
                '</div></div>',
                percentage, color, percentage
            )
        return '-'
    progress_percentage.short_description = _('Progress')


@admin.register(InventorySnapshot)
class InventorySnapshotAdmin(admin.ModelAdmin):
    """Admin interface for InventorySnapshot."""

    list_display = [
        'task_code',
        'asset_code',
        'asset_name',
        'location_name',
        'custodian_name',
        'department_name',
        'scanned',
        'scan_count',
        'created_at',
    ]
    list_filter = ['scanned', 'asset_status', 'created_at']
    search_fields = ['asset_code', 'asset_name', 'location_name', 'custodian_name']
    readonly_fields = ['created_at', 'scanned_at', 'created_by']

    def task_code(self, obj):
        """Display task code."""
        return obj.task.task_code if obj.task else '-'
    task_code.short_description = _('Task Code')


@admin.register(InventoryScan)
class InventoryScanAdmin(admin.ModelAdmin):
    """Admin interface for InventoryScan."""

    list_display = [
        'task_code',
        'asset_code',
        'asset_name',
        'scanned_by',
        'scan_method',
        'scan_status',
        'scanned_at',
        'location_changed',
    ]
    list_filter = ['scan_method', 'scan_status', 'scanned_at']
    search_fields = ['qr_code', 'asset__asset_code', 'asset__asset_name']
    readonly_fields = ['created_at', 'scanned_at', 'created_by']

    def task_code(self, obj):
        """Display task code."""
        return obj.task.task_code if obj.task else '-'
    task_code.short_description = _('Task Code')

    def asset_code(self, obj):
        """Display asset code."""
        return obj.asset.asset_code if obj.asset else '-'
    asset_code.short_description = _('Asset Code')

    def asset_name(self, obj):
        """Display asset name."""
        return obj.asset.asset_name if obj.asset else '-'
    asset_name.short_description = _('Asset Name')

    def location_changed(self, obj):
        """Check if location changed."""
        if obj.original_location_name and obj.actual_location_name:
            return obj.original_location_name != obj.actual_location_name
        return False
    location_changed.boolean = True
    location_changed.short_description = _('Location Changed')


@admin.register(InventoryDifference)
class InventoryDifferenceAdmin(admin.ModelAdmin):
    """Admin interface for InventoryDifference."""

    list_display = [
        'task_code',
        'asset_code',
        'asset_name',
        'difference_type',
        'status',
        'resolved_by',
        'resolved_at',
        'created_at',
    ]
    list_filter = ['difference_type', 'status', 'created_at', 'resolved_at']
    search_fields = ['asset__asset_code', 'asset__asset_name', 'description', 'resolution']
    readonly_fields = ['created_at', 'resolved_at', 'created_by', 'resolved_by']

    def task_code(self, obj):
        """Display task code."""
        return obj.task.task_code if obj.task else '-'
    task_code.short_description = _('Task Code')

    def asset_code(self, obj):
        """Display asset code."""
        return obj.asset.asset_code if obj.asset else '-'
    asset_code.short_description = _('Asset Code')

    def asset_name(self, obj):
        """Display asset name."""
        return obj.asset.asset_name if obj.asset else '-'
    asset_name.short_description = _('Asset Name')


@admin.register(InventoryTaskExecutor)
class InventoryTaskExecutorAdmin(admin.ModelAdmin):
    """Admin interface for InventoryTaskExecutor."""

    list_display = [
        'task_code',
        'executor_username',
        'executor',
        'is_primary',
        'completed_count',
    ]
    list_filter = ['is_primary']
    search_fields = ['task__task_code', 'executor__username', 'executor__get_full_name']

    def task_code(self, obj):
        """Display task code."""
        return obj.task.task_code if obj.task else '-'
    task_code.short_description = _('Task Code')

    def executor_username(self, obj):
        """Display executor username."""
        return obj.executor.username if obj.executor else '-'
    executor_username.short_description = _('Executor Username')
