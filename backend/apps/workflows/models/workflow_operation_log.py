"""
WorkflowOperationLog Model - Audit trail for workflow operations.

Logs all workflow-related operations for compliance and debugging.
Tracks create, update, delete, publish, unpublish, duplicate, import, export, and validate operations.
"""
from django.db import models
from django.utils.translation import gettext_lazy as _

from apps.common.models import BaseModel


class WorkflowOperationLog(BaseModel):
    """
    Audit log for workflow-related operations.

    Tracks all workflow definition operations for audit purposes.

    Inherits from BaseModel:
    - organization: Multi-tenant data isolation
    - is_deleted: Soft delete support
    - created_at, updated_at: Audit timestamps
    - created_by: User who performed the operation
    - custom_fields: Additional metadata storage
    """

    # === Operation Type Choices ===
    OPERATION_TYPE_CHOICES = [
        ('create', _('Create')),
        ('update', _('Update')),
        ('delete', _('Delete')),
        ('restore', _('Restore')),
        ('publish', _('Publish')),
        ('unpublish', _('Unpublish')),
        ('duplicate', _('Duplicate/Clone')),
        ('import', _('Import')),
        ('export', _('Export')),
        ('validate', _('Validate')),
        ('activate', _('Activate')),
        ('deactivate', _('Deactivate')),
        ('start', _('Start')),
        ('complete', _('Complete')),
        ('approve', _('Approve')),
        ('reject', _('Reject')),
        ('return', _('Return')),
        ('delegate', _('Delegate')),
        ('cancel', _('Cancel')),
        ('terminate', _('Terminate')),
        ('withdraw', _('Withdraw')),
    ]

    # === Target Type Choices ===
    TARGET_TYPE_CHOICES = [
        ('workflow_definition', _('Workflow Definition')),
        ('workflow_template', _('Workflow Template')),
        ('workflow_instance', _('Workflow Instance')),
        ('workflow_task', _('Workflow Task')),
    ]

    # === User who performed the operation ===
    actor = models.ForeignKey(
        'accounts.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='workflow_operation_logs',
        verbose_name=_('Actor'),
        db_comment='User who performed this operation'
    )

    # === Operation Details ===
    operation_type = models.CharField(
        max_length=20,
        choices=OPERATION_TYPE_CHOICES,
        verbose_name=_('Operation Type'),
        db_comment='Type of operation performed'
    )

    target_type = models.CharField(
        max_length=50,
        choices=TARGET_TYPE_CHOICES,
        verbose_name=_('Target Type'),
        db_comment='Type of object the operation was performed on'
    )

    # === Target Object References ===
    workflow_definition = models.ForeignKey(
        'WorkflowDefinition',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='operation_logs',
        verbose_name=_('Workflow Definition'),
        db_comment='Workflow definition affected by this operation'
    )

    workflow_template = models.ForeignKey(
        'WorkflowTemplate',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='operation_logs',
        verbose_name=_('Workflow Template'),
        db_comment='Workflow template affected by this operation'
    )

    workflow_instance = models.ForeignKey(
        'WorkflowInstance',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='operation_logs',
        verbose_name=_('Workflow Instance'),
        db_comment='Workflow instance affected by this operation'
    )

    workflow_task = models.ForeignKey(
        'WorkflowTask',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='operation_logs',
        verbose_name=_('Workflow Task'),
        db_comment='Workflow task affected by this operation'
    )

    target_name = models.CharField(
        max_length=200,
        blank=True,
        verbose_name=_('Target Name'),
        db_comment='Name of the target object (for reference)'
    )

    target_code = models.CharField(
        max_length=50,
        blank=True,
        verbose_name=_('Target Code'),
        db_comment='Code of the target object (for reference)'
    )

    # === Operation Details ===
    operation_details = models.JSONField(
        default=dict,
        blank=True,
        verbose_name=_('Operation Details'),
        db_comment='Details about the operation (changes made, parameters, etc.)'
    )

    # === Previous State (for update operations) ===
    previous_state = models.JSONField(
        default=dict,
        blank=True,
        verbose_name=_('Previous State'),
        db_comment='State of the object before the operation'
    )

    # === Result ===
    RESULT_CHOICES = [
        ('success', _('Success')),
        ('failure', _('Failure')),
        ('partial', _('Partial Success')),
    ]

    result = models.CharField(
        max_length=20,
        choices=RESULT_CHOICES,
        default='success',
        verbose_name=_('Result'),
        db_comment='Result of the operation'
    )

    error_message = models.TextField(
        blank=True,
        verbose_name=_('Error Message'),
        db_comment='Error details if operation failed'
    )

    # === Request Metadata ===
    ip_address = models.GenericIPAddressField(
        null=True,
        blank=True,
        verbose_name=_('IP Address'),
        db_comment='IP address from which the request originated'
    )

    user_agent = models.TextField(
        blank=True,
        verbose_name=_('User Agent'),
        db_comment='User agent string of the request'
    )

    request_metadata = models.JSONField(
        default=dict,
        blank=True,
        verbose_name=_('Request Metadata'),
        db_comment='Additional request metadata'
    )

    class Meta:
        db_table = 'workflow_operation_logs'
        verbose_name = _('Workflow Operation Log')
        verbose_name_plural = _('Workflow Operation Logs')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['actor', '-created_at']),
            models.Index(fields=['operation_type', '-created_at']),
            models.Index(fields=['target_type', '-created_at']),
            models.Index(fields=['result', '-created_at']),
            models.Index(fields=['workflow_definition', '-created_at']),
            models.Index(fields=['workflow_template', '-created_at']),
            models.Index(fields=['workflow_instance', '-created_at']),
            models.Index(fields=['workflow_task', '-created_at']),
            models.Index(fields=['-created_at']),
        ]

    def __str__(self):
        target = self.target_name or self.target_code or 'Unknown'
        return f'{self.get_operation_type_display()} - {target} ({self.get_result_display()})'

    @classmethod
    def log_create(cls, actor, workflow_definition, **kwargs):
        """Log a workflow creation operation."""
        return cls.objects.create(
            actor=actor,
            operation_type='create',
            target_type='workflow_definition',
            workflow_definition=workflow_definition,
            target_name=workflow_definition.name,
            target_code=workflow_definition.code,
            operation_details={
                'business_object_code': workflow_definition.business_object_code,
                'status': workflow_definition.status,
            },
            result='success',
            **kwargs
        )

    @classmethod
    def log_update(cls, actor, workflow_definition, changes, previous_state=None, **kwargs):
        """Log a workflow update operation."""
        return cls.objects.create(
            actor=actor,
            operation_type='update',
            target_type='workflow_definition',
            workflow_definition=workflow_definition,
            target_name=workflow_definition.name,
            target_code=workflow_definition.code,
            operation_details={'changes': changes},
            previous_state=previous_state or {},
            result='success',
            **kwargs
        )

    @classmethod
    def log_delete(cls, actor, workflow_definition, **kwargs):
        """Log a workflow deletion operation."""
        return cls.objects.create(
            actor=actor,
            operation_type='delete',
            target_type='workflow_definition',
            target_name=workflow_definition.name,
            target_code=workflow_definition.code,
            operation_details={
                'business_object_code': workflow_definition.business_object_code,
            },
            result='success',
            **kwargs
        )

    @classmethod
    def log_publish(cls, actor, workflow_definition, **kwargs):
        """Log a workflow publish operation."""
        return cls.objects.create(
            actor=actor,
            operation_type='publish',
            target_type='workflow_definition',
            workflow_definition=workflow_definition,
            target_name=workflow_definition.name,
            target_code=workflow_definition.code,
            operation_details={
                'version': workflow_definition.version,
            },
            result='success',
            **kwargs
        )

    @classmethod
    def log_duplicate(cls, actor, source_workflow, new_workflow, **kwargs):
        """Log a workflow duplicate/clone operation."""
        return cls.objects.create(
            actor=actor,
            operation_type='duplicate',
            target_type='workflow_definition',
            workflow_definition=new_workflow,
            target_name=new_workflow.name,
            target_code=new_workflow.code,
            operation_details={
                'source_workflow_code': source_workflow.code,
                'source_workflow_name': source_workflow.name,
            },
            result='success',
            **kwargs
        )

    @classmethod
    def log_import(cls, actor, summary, **kwargs):
        """Log a workflow import operation."""
        return cls.objects.create(
            actor=actor,
            operation_type='import',
            target_type='workflow_definition',
            operation_details=summary,
            result='success' if summary.get('failed', 0) == 0 else 'partial',
            **kwargs
        )

    @classmethod
    def log_export(cls, actor, workflow_codes, **kwargs):
        """Log a workflow export operation."""
        return cls.objects.create(
            actor=actor,
            operation_type='export',
            target_type='workflow_definition',
            operation_details={
                'workflow_codes': workflow_codes,
                'count': len(workflow_codes),
            },
            result='success',
            **kwargs
        )

    @classmethod
    def log_validate(cls, actor, workflow_definition, is_valid, errors=None, **kwargs):
        """Log a workflow validation operation."""
        return cls.objects.create(
            actor=actor,
            operation_type='validate',
            target_type='workflow_definition',
            workflow_definition=workflow_definition,
            target_name=workflow_definition.name,
            target_code=workflow_definition.code,
            operation_details={
                'is_valid': is_valid,
                'errors': errors or [],
            },
            result='success' if is_valid else 'failure',
            error_message='\n'.join(errors) if errors else None,
            **kwargs
        )

    @classmethod
    def log_operation(cls, operation_type, actor, workflow_instance=None,
                     workflow_task=None, result='success', details=None, **kwargs):
        """
        Log a generic workflow operation.

        Args:
            operation_type: Type of operation (start, complete, approve, reject, etc.)
            actor: User performing the operation
            workflow_instance: Related workflow instance (optional)
            workflow_task: Related workflow task (optional)
            result: Operation result (success, failure, partial)
            details: Additional operation details
            **kwargs: Additional fields

        Returns:
            WorkflowOperationLog: The created log entry
        """
        # Determine target type and name
        if workflow_instance:
            target_type = 'workflow_instance'
            target_name = workflow_instance.instance_no
            target_code = workflow_instance.instance_no
        elif workflow_task:
            target_type = 'workflow_task'
            target_name = workflow_task.node_name
            target_code = workflow_task.node_id
        else:
            target_type = 'workflow_definition'
            target_name = None
            target_code = None

        return cls.objects.create(
            actor=actor,
            operation_type=operation_type,
            target_type=target_type,
            workflow_instance=workflow_instance,
            workflow_task=workflow_task,
            target_name=target_name,
            target_code=target_code,
            operation_details=details or {},
            result=result,
            **kwargs
        )
