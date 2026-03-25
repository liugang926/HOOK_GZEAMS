from django.contrib import admin
from .models import DepreciationConfig, DepreciationRecord, DepreciationRun


@admin.register(DepreciationConfig)
class DepreciationConfigAdmin(admin.ModelAdmin):
    """Django admin for Depreciation Config"""
    list_display = ['category', 'depreciation_method', 'useful_life', 'salvage_value_rate', 'is_active']
    list_filter = ['depreciation_method', 'is_active', 'created_at']
    search_fields = ['category__name', 'category__code', 'notes']
    ordering = ['category__name']
    readonly_fields = ['created_at', 'updated_at']


@admin.register(DepreciationRecord)
class DepreciationRecordAdmin(admin.ModelAdmin):
    """Django admin for Depreciation Record"""
    list_display = ['asset', 'period', 'depreciation_amount', 'accumulated_amount', 'net_value', 'status', 'post_date']
    list_filter = ['status', 'period', 'post_date', 'created_at']
    search_fields = ['asset__asset_code', 'asset__asset_name', 'notes']
    ordering = ['-period', '-created_at']
    readonly_fields = ['created_at', 'updated_at']


@admin.register(DepreciationRun)
class DepreciationRunAdmin(admin.ModelAdmin):
    """Django admin for Depreciation Run"""
    list_display = ['period', 'run_date', 'status', 'total_assets', 'total_amount']
    list_filter = ['status', 'run_date', 'created_at']
    search_fields = ['period', 'notes']
    ordering = ['-run_date', '-created_at']
    readonly_fields = ['created_at', 'updated_at']
