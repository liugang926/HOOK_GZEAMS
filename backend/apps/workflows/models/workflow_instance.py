"""
WorkflowInstance model for storing running workflow instances.

This model represents a running instance of a workflow definition,
tracking its execution state, current position, and business context.
"""
from django.db import models
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from django.core.exceptions import ValidationError

from apps.common.models import BaseModel


class WorkflowInstance(BaseModel):
    """
    Workflow Instance model.

    Represents a running instance of a workflow definition with:
    - Business object binding (what business entity is being processed)
    - Execution state tracking (status, current node, progress)
    - Audit trail (initiator, timeline)
    - Variable storage (form data, process variables)
    """

    # Status choices for workflow instance
    STATUS_DRAFT = 'draft'
    STATUS_RUNNING = 'running'
    STATUS_PENDING_APPROVAL = 'pending_approval'
    STATUS_APPROVED = 'approved'
    STATUS_REJECTED = 'rejected'
    STATUS_CANCELLED = 'cancelled'
    STATUS_TERMINATED = 'terminated'

    STATUS_CHOICES = [
        (STATUS_DRAFT, _('Draft')),
        (STATUS_RUNNING, _('Running')),
        (STATUS_PENDING_APPROVAL, _('Pending Approval')),
        (STATUS_APPROVED, _('Approved')),
        (STATUS_REJECTED, _('Rejected')),
        (STATUS_CANCELLED, _('Cancelled')),
        (STATUS_TERMINATED, _('Terminated')),
    ]

    # Terminal statuses (no further processing possible)
    TERMINAL_STATUSES = {STATUS_APPROVED, STATUS_REJECTED, STATUS_CANCELLED, STATUS_TERMINATED}

    # Active statuses (can process tasks)
    ACTIVE_STATUSES = {STATUS_RUNNING, STATUS_PENDING_APPROVAL}

    # Workflow definition relationship
    definition = models.ForeignKey(
        'workflows.WorkflowDefinition',
        on_delete=models.PROTECT,
        related_name='instances',
        verbose_name=_('Workflow Definition'),
        help_text=_('The workflow definition this instance is based on')
    )

    # Instance identifier
    instance_no = models.CharField(
        max_length=50,
        unique=True,
        db_index=True,
        verbose_name=_('Instance No'),
        help_text=_('Unique identifier for this instance (e.g., WI-20240115-0001)')
    )

    # Business object binding
    business_object_code = models.CharField(
        max_length=50,
        db_index=True,
        verbose_name=_('Business Object Code'),
        help_text=_('Code of the business object type (e.g., asset_pickup, asset_return)')
    )

    business_id = models.CharField(
        max_length=100,
        db_index=True,
        verbose_name=_('Business ID'),
        help_text=_('ID of the business data being processed')
    )

    business_no = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        verbose_name=_('Business No'),
        help_text=_('Business document number (e.g., LY-2024-001)')
    )

    # Workflow status
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default=STATUS_DRAFT,
        db_index=True,
        verbose_name=_('Status'),
        help_text=_('Current status of the workflow instance')
    )

    # Current position in workflow
    current_node_id = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        verbose_name=_('Current Node ID'),
        help_text=_('ID of the current node in the workflow graph')
    )

    current_node_name = models.CharField(
        max_length=200,
        blank=True,
        null=True,
        verbose_name=_('Current Node Name'),
        help_text=_('Name of the current node for display')
    )

    # Progress tracking
    total_tasks = models.IntegerField(
        default=0,
        verbose_name=_('Total Tasks'),
        help_text=_('Total number of tasks in this workflow')
    )

    completed_tasks = models.IntegerField(
        default=0,
        verbose_name=_('Completed Tasks'),
        help_text=_('Number of completed tasks')
    )

    # Timeline tracking
    started_at = models.DateTimeField(
        blank=True,
        null=True,
        verbose_name=_('Started At'),
        help_text=_('When the workflow was started')
    )

    completed_at = models.DateTimeField(
        blank=True,
        null=True,
        verbose_name=_('Completed At'),
        help_text=_('When the workflow was completed')
    )

    # Termination tracking
    terminated_at = models.DateTimeField(
        blank=True,
        null=True,
        verbose_name=_('Terminated At'),
        help_text=_('When the workflow was terminated')
    )

    terminated_by = models.ForeignKey(
        'accounts.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='terminated_instances',
        verbose_name=_('Terminated By'),
        help_text=_('User who terminated the workflow')
    )

    termination_reason = models.TextField(
        blank=True,
        null=True,
        verbose_name=_('Termination Reason'),
        help_text=_('Reason for workflow termination')
    )

    # Workflow initiator
    initiator = models.ForeignKey(
        'accounts.User',
        on_delete=models.PROTECT,
        related_name='initiated_instances',
        verbose_name=_('Initiator'),
        help_text=_('User who initiated this workflow')
    )

    # Workflow variables (form data, process data)
    variables = models.JSONField(
        default=dict,
        blank=True,
        verbose_name=_('Variables'),
        help_text=_('Workflow variables and form data')
    )

    # Snapshot of graph data at time of instance creation
    graph_snapshot = models.JSONField(
        default=dict,
        blank=True,
        verbose_name=_('Graph Snapshot'),
        help_text=_('Snapshot of workflow graph at instance creation')
    )

    # Additional context
    title = models.CharField(
        max_length=200,
        blank=True,
        null=True,
        verbose_name=_('Title'),
        help_text=_('Custom title for this instance')
    )

    description = models.TextField(
        blank=True,
        null=True,
        verbose_name=_('Description'),
        help_text=_('Description or notes for this instance')
    )

    priority = models.CharField(
        max_length=20,
        choices=[
            ('low', _('Low')),
            ('normal', _('Normal')),
            ('high', _('High')),
            ('urgent', _('Urgent')),
        ],
        default='normal',
        verbose_name=_('Priority'),
        help_text=_('Priority level of this workflow instance')
    )

    # Estimated completion
    estimated_hours = models.DecimalField(
        max_digits=5,
        decimal_places=1,
        null=True,
        blank=True,
        verbose_name=_('Estimated Hours'),
        help_text=_('Estimated hours to complete this workflow')
    )

    class Meta:
        db_table = 'workflow_instances'
        verbose_name = _('Workflow Instance')
        verbose_name_plural = _('Workflow Instances')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['instance_no']),
            models.Index(fields=['status']),
            models.Index(fields=['business_object_code', 'business_id']),
            models.Index(fields=['initiator']),
            models.Index(fields=['definition']),
            models.Index(fields=['-created_at']),
            models.Index(fields=['started_at']),
            models.Index(fields=['completed_at']),
        ]

    def __str__(self):
        """String representation."""
        return f'{self.instance_no} - {self.title or self.definition.name} ({self.get_status_display()})'

    def clean(self):
        """Validate workflow instance data."""
        super().clean()

        # Validate business_object_code and business_id are set
        if not self.business_object_code:
            raise ValidationError({'business_object_code': _('Business object code is required.')})

        if not self.business_id:
            raise ValidationError({'business_id': _('Business ID is required.')})

        # Validate status transitions
        if self.pk:
            old_instance = WorkflowInstance.objects.get(pk=self.pk)
            if old_instance.status in self.TERMINAL_STATUSES and old_instance.status != self.status:
                raise ValidationError({
                    'status': _('Cannot change status from %(old_status)s to %(new_status)s.') % {
                        'old_status': old_instance.get_status_display(),
                        'new_status': self.get_status_display(),
                    }
                })

    @property
    def progress_percentage(self):
        """Calculate progress percentage."""
        if self.total_tasks <= 0:
            return 0
        return int((self.completed_tasks / self.total_tasks) * 100)

    @property
    def is_active(self):
        """Check if workflow is still active."""
        return self.status in self.ACTIVE_STATUSES

    @property
    def is_terminal(self):
        """Check if workflow is in terminal state."""
        return self.status in self.TERMINAL_STATUSES

    @property
    def pending_tasks_count(self):
        """Get count of pending tasks."""
        return self.tasks.filter(status='pending').count()

    @property
    def duration_hours(self):
        """Calculate workflow duration in hours."""
        if not self.started_at:
            return 0

        end_time = self.completed_at or self.terminated_at or timezone.now()
        delta = end_time - self.started_at
        return round(delta.total_seconds() / 3600, 2)

    def start(self, user=None):
        """
        Start the workflow instance.

        Args:
            user: The user starting the workflow (defaults to initiator)

        Returns:
            bool: True if started successfully
        """
        if self.status not in (self.STATUS_DRAFT,):
            raise ValueError(_('Only draft workflows can be started.'))

        self.status = self.STATUS_RUNNING
        self.started_at = timezone.now()
        self.save(update_fields=['status', 'started_at', 'updated_at'])

        # Log the start
        from apps.workflows.models.workflow_operation_log import WorkflowOperationLog
        WorkflowOperationLog.log_create(
            actor=user or self.initiator,
            workflow_instance=self
        )

        return True

    def complete(self):
        """
        Mark the workflow as completed/approved.

        Returns:
            bool: True if completed successfully
        """
        if self.status not in self.ACTIVE_STATUSES:
            raise ValueError(_('Only active workflows can be completed.'))

        self.status = self.STATUS_APPROVED
        self.completed_at = timezone.now()
        self.current_node_id = None
        self.current_node_name = None
        self.save(update_fields=['status', 'completed_at', 'current_node_id', 'current_node_name', 'updated_at'])

        # Log the completion
        from apps.workflows.models.workflow_operation_log import WorkflowOperationLog
        WorkflowOperationLog.log_operation(
            operation_type='complete',
            actor=self.initiator,
            workflow_instance=self,
            result='success'
        )

        return True

    def reject(self, reason=None):
        """
        Mark the workflow as rejected.

        Args:
            reason: Optional rejection reason

        Returns:
            bool: True if rejected successfully
        """
        if self.status not in self.ACTIVE_STATUSES:
            raise ValueError(_('Only active workflows can be rejected.'))

        self.status = self.STATUS_REJECTED
        self.completed_at = timezone.now()
        self.termination_reason = reason
        self.save(update_fields=['status', 'completed_at', 'termination_reason', 'updated_at'])

        return True

    def cancel(self, user=None):
        """
        Cancel the workflow instance.

        Args:
            user: The user cancelling the workflow

        Returns:
            bool: True if cancelled successfully
        """
        if self.status not in self.ACTIVE_STATUSES | {self.STATUS_DRAFT}:
            raise ValueError(_('Cannot cancel workflow in current status.'))

        old_status = self.status
        self.status = self.STATUS_CANCELLED
        self.completed_at = timezone.now()
        self.save(update_fields=['status', 'completed_at', 'updated_at'])

        # Cancel all pending tasks
        self.tasks.filter(status='pending').update(
            status='cancelled',
            cancelled_at=timezone.now()
        )

        # Log the cancellation
        from apps.workflows.models.workflow_operation_log import WorkflowOperationLog
        WorkflowOperationLog.log_operation(
            operation_type='cancel',
            actor=user or self.initiator,
            workflow_instance=self,
            result='success',
            details={'old_status': old_status}
        )

        return True

    def terminate(self, user=None, reason=None):
        """
        Terminate the workflow instance (admin action).

        Args:
            user: The admin user terminating the workflow
            reason: Reason for termination

        Returns:
            bool: True if terminated successfully
        """
        if self.status in self.TERMINAL_STATUSES:
            raise ValueError(_('Workflow is already in terminal state.'))

        old_status = self.status
        self.status = self.STATUS_TERMINATED
        self.terminated_at = timezone.now()
        self.terminated_by = user
        self.termination_reason = reason
        self.save(update_fields=['status', 'terminated_at', 'terminated_by', 'termination_reason', 'updated_at'])

        # Terminate all pending tasks
        self.tasks.filter(status='pending').update(
            status='terminated',
            terminated_at=timezone.now()
        )

        # Log the termination
        from apps.workflows.models.workflow_operation_log import WorkflowOperationLog
        WorkflowOperationLog.log_operation(
            operation_type='terminate',
            actor=user,
            workflow_instance=self,
            result='success',
            details={'old_status': old_status, 'reason': reason}
        )

        return True

    def update_progress(self):
        """Update progress tracking (total and completed tasks)."""
        from apps.workflows.models.workflow_task import WorkflowTask

        self.total_tasks = self.tasks.count()
        self.completed_tasks = self.tasks.filter(
            status__in=[WorkflowTask.STATUS_APPROVED, WorkflowTask.STATUS_REJECTED]
        ).count()
        self.save(update_fields=['total_tasks', 'completed_tasks', 'updated_at'])

    def get_variable(self, key, default=None):
        """
        Get a workflow variable value.

        Args:
            key: Variable key (supports dot notation for nested values)
            default: Default value if key not found

        Returns:
            The variable value or default
        """
        keys = key.split('.')
        value = self.variables

        for k in keys:
            if isinstance(value, dict):
                value = value.get(k)
            else:
                return default

        return value if value is not None else default

    def set_variable(self, key, value):
        """
        Set a workflow variable value.

        Args:
            key: Variable key (supports dot notation for nested values)
            value: Value to set
        """
        keys = key.split('.')
        data = self.variables

        for k in keys[:-1]:
            if k not in data or not isinstance(data[k], dict):
                data[k] = {}
            data = data[k]

        data[keys[-1]] = value
        self.save(update_fields=['variables', 'updated_at'])

    def get_approval_chain(self):
        """
        Get the approval chain (history of approvals).

        Returns:
            list: List of approval records ordered by creation time
        """
        approvals = []
        for task in self.tasks.all().order_by('created_at'):
            for approval in task.approvals.all().order_by('created_at'):
                approvals.append({
                    'task_name': task.node_name,
                    'approver': approval.approver.get_full_name() or approval.approver.username,
                    'action': approval.get_action_display(),
                    'comment': approval.comment,
                    'created_at': approval.created_at,
                })
        return approvals

    def get_current_tasks(self):
        """
        Get currently pending tasks.

        Returns:
            QuerySet: Pending tasks for this instance
        """
        return self.tasks.filter(status='pending').select_related('assignee')
