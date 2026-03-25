"""
Integration models for ERP system integration framework.

Provides models for integration configuration, sync tasks, logs, and data mapping.
All models inherit from BaseModel for organization isolation and soft delete.
"""
import uuid
from django.db import models

from apps.common.models import BaseModel
from apps.integration.constants import (
    IntegrationSystemType,
    IntegrationModuleType,
    SyncDirection,
    SyncStatus,
    HealthStatus,
)


class IntegrationConfig(BaseModel):
    """
    Integration configuration model.

    Stores configuration for connecting to external ERP systems.
    Inherits from BaseModel for organization isolation, soft delete, and audit fields.
    """

    class Meta:
        db_table = 'integration_config'
        verbose_name = 'Integration Config'
        verbose_name_plural = 'Integration Configs'
        ordering = ['-created_at']
        unique_together = [['organization', 'system_type']]

    # ==================== Basic Configuration ====================

    system_type = models.CharField(
        max_length=20,
        choices=IntegrationSystemType.CHOICES,
        verbose_name='System Type',
        help_text='External ERP system type'
    )

    system_name = models.CharField(
        max_length=100,
        verbose_name='System Name',
        help_text='Custom name, e.g., "Production M18"'
    )

    # ==================== Connection Configuration ====================

    connection_config = models.JSONField(
        default=dict,
        verbose_name='Connection Config',
        help_text='API endpoint, auth info, etc. Structure defined by adapters'
    )

    # ==================== Module Configuration ====================

    enabled_modules = models.JSONField(
        default=list,
        verbose_name='Enabled Modules',
        help_text='Enabled integration modules, e.g., ["procurement", "finance"]'
    )

    # ==================== Sync Configuration ====================

    sync_config = models.JSONField(
        default=dict,
        verbose_name='Sync Config',
        help_text='Sync interval, auto-sync settings'
    )

    # ==================== Data Mapping Configuration ====================

    mapping_config = models.JSONField(
        default=dict,
        verbose_name='Mapping Config',
        help_text='Field mapping configuration'
    )

    # ==================== Status Management ====================

    is_enabled = models.BooleanField(
        default=True,
        verbose_name='Is Enabled',
        db_index=True
    )

    last_sync_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='Last Sync At'
    )

    last_sync_status = models.CharField(
        max_length=20,
        choices=SyncStatus.CHOICES,
        default=SyncStatus.PENDING,
        verbose_name='Last Sync Status'
    )

    # ==================== Health Monitoring ====================

    health_status = models.CharField(
        max_length=20,
        choices=HealthStatus.CHOICES,
        default=HealthStatus.UNHEALTHY,
        verbose_name='Health Status',
        db_index=True
    )

    last_health_check_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='Last Health Check At'
    )

    def __str__(self):
        return f"{self.organization.name} - {self.get_system_type_display()}"


class IntegrationSyncTask(BaseModel):
    """
    Integration sync task model.

    Records detailed information for each sync execution.
    Inherits from BaseModel for organization isolation and audit fields.
    """

    class Meta:
        db_table = 'integration_sync_task'
        verbose_name = 'Integration Sync Task'
        verbose_name_plural = 'Integration Sync Tasks'
        ordering = ['-created_at']

    # ==================== Relations ====================

    config = models.ForeignKey(
        IntegrationConfig,
        on_delete=models.CASCADE,
        related_name='sync_tasks',
        verbose_name='Integration Config'
    )

    # ==================== Task Identifier ====================

    task_id = models.CharField(
        max_length=100,
        unique=True,
        verbose_name='Task ID',
        help_text='Globally unique task identifier'
    )

    # ==================== Sync Information ====================

    module_type = models.CharField(
        max_length=20,
        choices=IntegrationModuleType.CHOICES,
        verbose_name='Module Type'
    )

    direction = models.CharField(
        max_length=20,
        choices=SyncDirection.CHOICES,
        verbose_name='Sync Direction'
    )

    business_type = models.CharField(
        max_length=50,
        verbose_name='Business Type',
        help_text='e.g., purchase_order, voucher'
    )

    # ==================== Execution Parameters ====================

    sync_params = models.JSONField(
        default=dict,
        verbose_name='Sync Params',
        help_text='Execution parameters for this sync'
    )

    # ==================== Execution Status ====================

    status = models.CharField(
        max_length=20,
        choices=SyncStatus.CHOICES,
        default=SyncStatus.PENDING,
        verbose_name='Status',
        db_index=True
    )

    # ==================== Execution Result Statistics ====================

    total_count = models.IntegerField(
        default=0,
        verbose_name='Total Count'
    )

    success_count = models.IntegerField(
        default=0,
        verbose_name='Success Count'
    )

    failed_count = models.IntegerField(
        default=0,
        verbose_name='Failed Count'
    )

    error_summary = models.JSONField(
        default=list,
        verbose_name='Error Summary',
        help_text='Detailed failure information'
    )

    # ==================== Execution Time ====================

    started_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='Started At',
        db_index=True
    )

    completed_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='Completed At',
        db_index=True
    )

    duration_ms = models.IntegerField(
        null=True,
        blank=True,
        verbose_name='Duration (ms)'
    )

    # ==================== Celery Task Association ====================

    celery_task_id = models.CharField(
        max_length=100,
        blank=True,
        verbose_name='Celery Task ID',
        help_text='Associated Celery async task ID'
    )

    def __str__(self):
        return f"{self.task_id} - {self.business_type}"


class IntegrationLog(BaseModel):
    """
    Integration log model.

    Records complete information for each API call.
    Inherits from BaseModel for organization isolation and audit fields.
    """

    class Meta:
        db_table = 'integration_log'
        verbose_name = 'Integration Log'
        verbose_name_plural = 'Integration Logs'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['organization', 'system_type']),
            models.Index(fields=['created_at']),
            models.Index(fields=['success']),
            models.Index(fields=['-created_at']),
        ]

    # ==================== Relations ====================

    sync_task = models.ForeignKey(
        IntegrationSyncTask,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='logs',
        verbose_name='Sync Task'
    )

    # ==================== Integration Identifier ====================

    system_type = models.CharField(
        max_length=20,
        choices=IntegrationSystemType.CHOICES,
        verbose_name='System Type'
    )

    integration_type = models.CharField(
        max_length=50,
        verbose_name='Integration Type',
        help_text='e.g., m18_po, sap_fi'
    )

    # ==================== Request Information ====================

    action = models.CharField(
        max_length=20,
        choices=SyncDirection.CHOICES,
        verbose_name='Action'
    )

    request_method = models.CharField(
        max_length=10,
        verbose_name='Request Method',
        help_text='GET, POST, PUT, DELETE, etc.'
    )

    request_url = models.TextField(
        verbose_name='Request URL'
    )

    request_headers = models.JSONField(
        default=dict,
        verbose_name='Request Headers'
    )

    request_body = models.JSONField(
        default=dict,
        verbose_name='Request Body'
    )

    # ==================== Response Information ====================

    status_code = models.IntegerField(
        null=True,
        blank=True,
        verbose_name='HTTP Status Code'
    )

    response_body = models.JSONField(
        default=dict,
        verbose_name='Response Body'
    )

    response_headers = models.JSONField(
        default=dict,
        verbose_name='Response Headers'
    )

    # ==================== Execution Result ====================

    success = models.BooleanField(
        default=False,
        verbose_name='Success',
        db_index=True
    )

    error_message = models.TextField(
        blank=True,
        verbose_name='Error Message'
    )

    # ==================== Execution Time ====================

    duration_ms = models.IntegerField(
        null=True,
        blank=True,
        verbose_name='Duration (ms)'
    )

    # ==================== Business Association ====================

    business_type = models.CharField(
        max_length=50,
        blank=True,
        verbose_name='Business Type'
    )

    business_id = models.CharField(
        max_length=100,
        blank=True,
        verbose_name='Business ID'
    )

    external_id = models.CharField(
        max_length=100,
        blank=True,
        verbose_name='External System ID'
    )

    def __str__(self):
        return f"{self.system_type} - {self.action} - {self.request_method}"


class DataMappingTemplate(BaseModel):
    """
    Data mapping template model.

    Defines data mapping relationships between local and external systems.
    Inherits from BaseModel for organization isolation and audit fields.
    """

    class Meta:
        db_table = 'data_mapping_template'
        verbose_name = 'Data Mapping Template'
        verbose_name_plural = 'Data Mapping Templates'
        unique_together = [['organization', 'system_type', 'business_type']]

    # ==================== Basic Configuration ====================

    system_type = models.CharField(
        max_length=20,
        choices=IntegrationSystemType.CHOICES,
        verbose_name='System Type'
    )

    business_type = models.CharField(
        max_length=50,
        verbose_name='Business Type',
        help_text='e.g., purchase_order, asset, voucher'
    )

    template_name = models.CharField(
        max_length=100,
        verbose_name='Template Name'
    )

    # ==================== Mapping Configuration ====================

    field_mappings = models.JSONField(
        default=dict,
        verbose_name='Field Mappings',
        help_text='Format: {"local_field": "external_field", ...}'
    )

    value_mappings = models.JSONField(
        default=dict,
        verbose_name='Value Mappings',
        help_text='Format: {"field_name": {"local_value": "external_value"}}'
    )

    transform_rules = models.JSONField(
        default=list,
        verbose_name='Transform Rules',
        help_text='Data transformation rule list'
    )

    # ==================== Status Management ====================

    is_active = models.BooleanField(
        default=True,
        verbose_name='Is Active'
    )

    def __str__(self):
        return f"{self.get_system_type_display()} - {self.business_type} - {self.template_name}"
