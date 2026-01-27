"""
Django Admin configuration for Lifecycle models.

Provides admin interface for:
- PurchaseRequest: Asset purchase requests
- AssetReceipt: Asset receiving/entry
- Maintenance: Maintenance records
- MaintenancePlan: Planned maintenance
- MaintenanceTask: Maintenance tasks
- DisposalRequest: Asset disposal requests
"""
from django.contrib import admin

from .models import (
    PurchaseRequest,
    PurchaseRequestItem,
    AssetReceipt,
    AssetReceiptItem,
    Maintenance,
    MaintenancePlan,
    MaintenanceTask,
    DisposalRequest,
    DisposalItem,
)


class PurchaseRequestItemInline(admin.TabularInline):
    """Inline admin for PurchaseRequestItem."""

    model = PurchaseRequestItem
    extra = 0


@admin.register(PurchaseRequest)
class PurchaseRequestAdmin(admin.ModelAdmin):
    """Admin interface for Purchase Request."""

    list_display = ['request_no', 'applicant', 'department', 'request_date', 'status']
    list_filter = ['status', 'request_date']
    search_fields = ['request_no', 'applicant__username']
    readonly_fields = ['request_no', 'created_at', 'updated_at', 'created_by', 'updated_by', 'deleted_by']
    inlines = [PurchaseRequestItemInline]
    ordering = ['-request_date']


class AssetReceiptItemInline(admin.TabularInline):
    """Inline admin for AssetReceiptItem."""

    model = AssetReceiptItem
    extra = 0


@admin.register(AssetReceipt)
class AssetReceiptAdmin(admin.ModelAdmin):
    """Admin interface for Asset Receipt."""

    list_display = ['receipt_no', 'supplier', 'receipt_date', 'status']
    list_filter = ['status', 'receipt_date']
    search_fields = ['receipt_no', 'supplier']
    readonly_fields = ['receipt_no', 'created_at', 'updated_at', 'created_by', 'updated_by', 'deleted_by']
    inlines = [AssetReceiptItemInline]
    ordering = ['-receipt_date']


@admin.register(Maintenance)
class MaintenanceAdmin(admin.ModelAdmin):
    """Admin interface for Maintenance."""

    list_display = ['maintenance_no', 'asset', 'status', 'priority', 'report_time']
    list_filter = ['status', 'priority']
    search_fields = ['maintenance_no', 'asset__asset_code', 'asset__asset_name']
    readonly_fields = ['maintenance_no', 'created_at', 'updated_at', 'created_by', 'updated_by', 'deleted_by']
    ordering = ['-created_at']


class MaintenanceTaskInline(admin.TabularInline):
    """Inline admin for MaintenanceTask."""

    model = MaintenanceTask
    extra = 0


@admin.register(MaintenancePlan)
class MaintenancePlanAdmin(admin.ModelAdmin):
    """Admin interface for Maintenance Plan."""

    list_display = ['plan_code', 'plan_name', 'status', 'cycle_type', 'start_date']
    list_filter = ['status', 'cycle_type']
    search_fields = ['plan_code', 'plan_name']
    readonly_fields = ['created_at', 'updated_at', 'created_by', 'updated_by', 'deleted_by']
    inlines = [MaintenanceTaskInline]
    ordering = ['-created_at']


@admin.register(MaintenanceTask)
class MaintenanceTaskAdmin(admin.ModelAdmin):
    """Admin interface for Maintenance Task."""

    list_display = ['task_no', 'plan', 'asset', 'scheduled_date', 'status']
    list_filter = ['status', 'scheduled_date']
    search_fields = ['task_no', 'asset__asset_code', 'asset__asset_name']
    readonly_fields = ['task_no', 'created_at', 'updated_at', 'created_by', 'updated_by', 'deleted_by']
    ordering = ['scheduled_date']


class DisposalItemInline(admin.TabularInline):
    """Inline admin for DisposalItem."""

    model = DisposalItem
    extra = 0


@admin.register(DisposalRequest)
class DisposalRequestAdmin(admin.ModelAdmin):
    """Admin interface for Disposal Request."""

    list_display = ['request_no', 'disposal_type', 'applicant', 'request_date', 'status']
    list_filter = ['disposal_type', 'status', 'request_date']
    search_fields = ['request_no', 'applicant__username']
    readonly_fields = ['request_no', 'created_at', 'updated_at', 'created_by', 'updated_by', 'deleted_by']
    inlines = [DisposalItemInline]
    ordering = ['-request_date']
