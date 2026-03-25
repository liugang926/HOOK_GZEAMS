"""
Admin configuration for integration module.

Registers integration models with Django admin.
"""
from django.contrib import admin
from apps.integration.models import (
    IntegrationConfig,
    IntegrationSyncTask,
    IntegrationLog,
    DataMappingTemplate,
)


@admin.register(IntegrationConfig)
class IntegrationConfigAdmin(admin.ModelAdmin):
    """Admin interface for IntegrationConfig."""

    list_display = [
        'system_name',
        'system_type',
        'organization',
        'is_enabled',
        'health_status',
        'last_sync_at',
        'last_sync_status',
        'created_at',
    ]
    list_filter = ['system_type', 'is_enabled', 'health_status', 'last_sync_status']
    search_fields = ['system_name', 'system_type']
    readonly_fields = ['last_health_check_at', 'last_sync_at']


@admin.register(IntegrationSyncTask)
class IntegrationSyncTaskAdmin(admin.ModelAdmin):
    """Admin interface for IntegrationSyncTask."""

    list_display = [
        'task_id',
        'config',
        'business_type',
        'direction',
        'module_type',
        'status',
        'total_count',
        'success_count',
        'failed_count',
        'started_at',
        'completed_at',
        'created_at',
    ]
    list_filter = ['status', 'module_type', 'direction', 'business_type']
    search_fields = ['task_id', 'business_type']
    readonly_fields = [
        'task_id',
        'config',
        'module_type',
        'direction',
        'business_type',
        'sync_params',
        'status',
        'total_count',
        'success_count',
        'failed_count',
        'error_summary',
        'started_at',
        'completed_at',
        'duration_ms',
        'celery_task_id',
    ]


@admin.register(IntegrationLog)
class IntegrationLogAdmin(admin.ModelAdmin):
    """Admin interface for IntegrationLog."""

    list_display = [
        'id',
        'system_type',
        'action',
        'request_method',
        'status_code',
        'success',
        'duration_ms',
        'created_at',
    ]
    list_filter = ['system_type', 'action', 'success', 'status_code']
    search_fields = ['request_url', 'business_type', 'business_id']
    readonly_fields = [
        'sync_task',
        'system_type',
        'integration_type',
        'action',
        'request_method',
        'request_url',
        'request_headers',
        'request_body',
        'status_code',
        'response_headers',
        'response_body',
        'success',
        'error_message',
        'duration_ms',
        'business_type',
        'business_id',
        'external_id',
    ]


@admin.register(DataMappingTemplate)
class DataMappingTemplateAdmin(admin.ModelAdmin):
    """Admin interface for DataMappingTemplate."""

    list_display = [
        'template_name',
        'system_type',
        'business_type',
        'organization',
        'is_active',
        'created_at',
    ]
    list_filter = ['system_type', 'business_type', 'is_active']
    search_fields = ['template_name', 'business_type']
