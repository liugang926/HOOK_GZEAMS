"""
WorkflowTask model for storing approval tasks.

This model represents individual approval tasks within a workflow instance,
assigning them to users and tracking their completion status.
"""
from django.db import models
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from django.core.exceptions import ValidationError

from apps.common.models import BaseModel


class WorkflowTask(BaseModel):
    """
    Workflow Task model.

    Represents a single approval task within a workflow instance.
    Each task is assigned to a specific user for action.
    """

    # Task status choices
    STATUS_PENDING = 'pending'
    STATUS_APPROVED = 'approved'
    STATUS_REJECTED = 'rejected'
    STATUS_RETURNED = 'returned'
    STATUS_CANCELLED = 'cancelled'
    STATUS_TERMINATED = 'terminated'
    STATUS_DELEGATED = 'delegated'
    STATUS_WITHDRAWN = 'withdrawn'

    STATUS_CHOICES = [
        (STATUS_PENDING, _('Pending')),
        (STATUS_APPROVED, _('Approved')),
        (STATUS_REJECTED, _('Rejected')),
        (STATUS_RETURNED, _('Returned')),
        (STATUS_CANCELLED, _('Cancelled')),
        (STATUS_TERMINATED, _('Terminated')),
        (STATUS_DELEGATED, _('Delegated')),
        (STATUS_WITHDRAWN, _('Withdrawn')),
    ]

    # Active tasks (can be processed)
    ACTIVE_STATUSES = {STATUS_PENDING}

    # Completed tasks (no further action)
    COMPLETED_STATUSES = {STATUS_APPROVED, STATUS_REJECTED, STATUS_RETURNED}

    # Node type choices
    NODE_TYPE_START = 'start'
    NODE_TYPE_APPROVAL = 'approval'
    NODE_TYPE_CONDITION = 'condition'
    NODE_TYPE_CC = 'cc'
    NODE_TYPE_NOTIFY = 'notify'
    NODE_TYPE_PARALLEL = 'parallel'
    NODE_TYPE_END = 'end'

    NODE_TYPE_CHOICES = [
        (NODE_TYPE_START, _('Start')),
        (NODE_TYPE_APPROVAL, _('Approval')),
        (NODE_TYPE_CONDITION, _('Condition')),
        (NODE_TYPE_CC, _('Carbon Copy')),
        (NODE_TYPE_NOTIFY, _('Notify')),
        (NODE_TYPE_PARALLEL, _('Parallel Gateway')),
        (NODE_TYPE_END, _('End')),
    ]

    # Approve type choices (how multiple approvers interact)
    APPROVE_TYPE_OR = 'or'  # Any one can approve
    APPROVE_TYPE_AND = 'and'  # All must approve
    APPROVE_TYPE_SEQUENCE = 'sequence'  # Approve in sequence

    APPROVE_TYPE_CHOICES = [
        (APPROVE_TYPE_OR, _('Or Sign - Any One')),
        (APPROVE_TYPE_AND, _('Countersign - All Must')),
        (APPROVE_TYPE_SEQUENCE, _('Sequential')),
    ]

    # Workflow instance relationship
    instance = models.ForeignKey(
        'workflows.WorkflowInstance',
        on_delete=models.CASCADE,
        related_name='tasks',
        verbose_name=_('Workflow Instance'),
        help_text=_('The workflow instance this task belongs to')
    )

    # Node information
    node_id = models.CharField(
        max_length=50,
        db_index=True,
        verbose_name=_('Node ID'),
        help_text=_('ID of the node in the workflow graph')
    )

    node_name = models.CharField(
        max_length=200,
        verbose_name=_('Node Name'),
        help_text=_('Display name of the node')
    )

    node_type = models.CharField(
        max_length=20,
        choices=NODE_TYPE_CHOICES,
        default=NODE_TYPE_APPROVAL,
        verbose_name=_('Node Type'),
        help_text=_('Type of the workflow node')
    )

    # Approval type for this task
    approve_type = models.CharField(
        max_length=20,
        choices=APPROVE_TYPE_CHOICES,
        default=APPROVE_TYPE_OR,
        verbose_name=_('Approve Type'),
        help_text=_('How multiple approvers interact (or/and/sequence)')
    )

    # Task assignee
    assignee = models.ForeignKey(
        'accounts.User',
        on_delete=models.PROTECT,
        related_name='assigned_tasks',
        verbose_name=_('Assignee'),
        help_text=_('User assigned to this task')
    )

    # Task status
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default=STATUS_PENDING,
        db_index=True,
        verbose_name=_('Status'),
        help_text=_('Current status of the task')
    )

    # Sequence number for sequential approval
    sequence = models.IntegerField(
        default=0,
        verbose_name=_('Sequence'),
        help_text=_('Order in sequence (0 for non-sequential)')
    )

    # Due date tracking
    due_date = models.DateTimeField(
        blank=True,
        null=True,
        verbose_name=_('Due Date'),
        help_text=_('Deadline for task completion')
    )

    # Completion tracking
    completed_at = models.DateTimeField(
        blank=True,
        null=True,
        verbose_name=_('Completed At'),
        help_text=_('When the task was completed')
    )

    completed_by = models.ForeignKey(
        'accounts.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='completed_tasks',
        verbose_name=_('Completed By'),
        help_text=_('User who completed the task')
    )

    # Cancellation tracking
    cancelled_at = models.DateTimeField(
        blank=True,
        null=True,
        verbose_name=_('Cancelled At'),
        help_text=_('When the task was cancelled')
    )

    # Termination tracking
    terminated_at = models.DateTimeField(
        blank=True,
        null=True,
        verbose_name=_('Terminated At'),
        help_text=_('When the task was terminated')
    )

    # Delegation tracking
    delegated_to = models.ForeignKey(
        'accounts.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='delegated_tasks',
        verbose_name=_('Delegated To'),
        help_text=_('User this task was delegated to')
    )

    delegated_from = models.ForeignKey(
        'accounts.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='delegated_by_tasks',
        verbose_name=_('Delegated From'),
        help_text=_('User who delegated this task')
    )

    delegated_at = models.DateTimeField(
        blank=True,
        null=True,
        verbose_name=_('Delegated At'),
        help_text=_('When the task was delegated')
    )

    delegation_reason = models.TextField(
        blank=True,
        null=True,
        verbose_name=_('Delegation Reason'),
        help_text=_('Reason for task delegation')
    )

    # Task priority
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
        help_text=_('Priority level of this task')
    )

    # Node properties snapshot
    node_properties = models.JSONField(
        default=dict,
        blank=True,
        verbose_name=_('Node Properties'),
        help_text=_('Snapshot of node properties at task creation')
    )

    class Meta:
        db_table = 'workflow_tasks'
        verbose_name = _('Workflow Task')
        verbose_name_plural = _('Workflow Tasks')
        ordering = ['instance', 'sequence', 'created_at']
        indexes = [
            models.Index(fields=['instance', 'status']),
            models.Index(fields=['assignee', 'status']),
            models.Index(fields=['status']),
            models.Index(fields=['due_date']),
            models.Index(fields=['node_id']),
            models.Index(fields=['-created_at']),
        ]

    def __str__(self):
        """String representation."""
        return f'{self.node_name} - {self.assignee.get_full_name() or self.assignee.username} ({self.get_status_display()})'

    def clean(self):
        """Validate task data."""
        super().clean()

        # Validate instance is active for new pending tasks
        if not self.pk and self.status == self.STATUS_PENDING:
            if self.instance.status not in (self.instance.STATUS_RUNNING, self.instance.STATUS_PENDING_APPROVAL):
                raise ValidationError({
                    'instance': _('Cannot create tasks for non-active workflow instances.')
                })

        # Validate status transitions
        if self.pk:
            old_task = WorkflowTask.objects.get(pk=self.pk)

            # Cannot change completed status
            if old_task.status in self.COMPLETED_STATUSES and old_task.status != self.status:
                raise ValidationError({
                    'status': _('Cannot change status from %(old_status)s.') % {
                        'old_status': old_task.get_status_display(),
                    }
                })

            # Cannot cancel/terminate already completed tasks
            if self.status in (self.STATUS_CANCELLED, self.STATUS_TERMINATED):
                if old_task.status in self.COMPLETED_STATUSES:
                    raise ValidationError({
                        'status': _('Cannot %(action)s a completed task.') % {
                            'action': 'cancel' if self.status == self.STATUS_CANCELLED else 'terminate'
                        }
                    })

    @property
    def is_pending(self):
        """Check if task is pending."""
        return self.status == self.STATUS_PENDING

    @property
    def is_completed(self):
        """Check if task is completed."""
        return self.status in self.COMPLETED_STATUSES

    @property
    def is_overdue(self):
        """Check if task is overdue."""
        if self.due_date is None or self.status != self.STATUS_PENDING:
            return False
        return timezone.now() > self.due_date

    @property
    def remaining_hours(self):
        """Get remaining hours until due date."""
        if self.due_date is None or self.status != self.STATUS_PENDING:
            return None

        delta = self.due_date - timezone.now()
        hours = delta.total_seconds() / 3600
        return round(hours, 1) if hours > 0 else 0

    @property
    def duration_hours(self):
        """Calculate task duration in hours."""
        if not self.completed_at:
            return 0

        delta = self.completed_at - self.created_at
        return round(delta.total_seconds() / 3600, 2)

    def approve(self, user, comment=None):
        """
        Approve the task.

        Args:
            user: User approving the task
            comment: Optional approval comment

        Returns:
            WorkflowApproval: The created approval record

        Raises:
            ValueError: If task cannot be approved
        """
        if self.status != self.STATUS_PENDING:
            raise ValueError(_('Only pending tasks can be approved.'))

        if self.assignee != user:
            raise ValueError(_('You are not authorized to approve this task.'))

        # Update task status
        self.status = self.STATUS_APPROVED
        self.completed_at = timezone.now()
        self.completed_by = user
        self.save(update_fields=['status', 'completed_at', 'completed_by', 'updated_at'])

        # Create approval record
        from apps.workflows.models.workflow_approval import WorkflowApproval
        approval = WorkflowApproval.objects.create(
            task=self,
            approver=user,
            action=WorkflowApproval.ACTION_APPROVE,
            comment=comment
        )

        return approval

    def reject(self, user, comment=None):
        """
        Reject the task.

        Args:
            user: User rejecting the task
            comment: Optional rejection comment

        Returns:
            WorkflowApproval: The created approval record

        Raises:
            ValueError: If task cannot be rejected
        """
        if self.status != self.STATUS_PENDING:
            raise ValueError(_('Only pending tasks can be rejected.'))

        if self.assignee != user:
            raise ValueError(_('You are not authorized to reject this task.'))

        # Update task status
        self.status = self.STATUS_REJECTED
        self.completed_at = timezone.now()
        self.completed_by = user
        self.save(update_fields=['status', 'completed_at', 'completed_by', 'updated_at'])

        # Create approval record
        from apps.workflows.models.workflow_approval import WorkflowApproval
        approval = WorkflowApproval.objects.create(
            task=self,
            approver=user,
            action=WorkflowApproval.ACTION_REJECT,
            comment=comment
        )

        return approval

    def return_task(self, user, comment=None):
        """
        Return the task to previous step.

        Args:
            user: User returning the task
            comment: Optional return comment

        Returns:
            WorkflowApproval: The created approval record

        Raises:
            ValueError: If task cannot be returned
        """
        if self.status != self.STATUS_PENDING:
            raise ValueError(_('Only pending tasks can be returned.'))

        if self.assignee != user:
            raise ValueError(_('You are not authorized to return this task.'))

        # Update task status
        self.status = self.STATUS_RETURNED
        self.completed_at = timezone.now()
        self.completed_by = user
        self.save(update_fields=['status', 'completed_at', 'completed_by', 'updated_at'])

        # Create approval record
        from apps.workflows.models.workflow_approval import WorkflowApproval
        approval = WorkflowApproval.objects.create(
            task=self,
            approver=user,
            action=WorkflowApproval.ACTION_RETURN,
            comment=comment
        )

        return approval

    def delegate(self, to_user, from_user, reason=None):
        """
        Delegate the task to another user.

        Args:
            to_user: User to delegate to
            from_user: User delegating the task
            reason: Optional delegation reason

        Returns:
            bool: True if delegated successfully

        Raises:
            ValueError: If task cannot be delegated
        """
        if self.status != self.STATUS_PENDING:
            raise ValueError(_('Only pending tasks can be delegated.'))

        if self.assignee != from_user:
            raise ValueError(_('You are not authorized to delegate this task.'))

        # Update delegation info
        old_assignee = self.assignee
        self.delegated_to = to_user
        self.delegated_from = from_user
        self.delegated_at = timezone.now()
        self.delegation_reason = reason
        self.assignee = to_user
        self.save(update_fields=['assignee', 'delegated_to', 'delegated_from', 'delegated_at', 'delegation_reason', 'updated_at'])

        # Log the delegation
        from apps.workflows.models.workflow_operation_log import WorkflowOperationLog
        WorkflowOperationLog.log_operation(
            operation_type='delegate',
            actor=from_user,
            workflow_instance=self.instance,
            workflow_task=self,
            result='success',
            details={
                'from_user': old_assignee.get_full_name() or old_assignee.username,
                'to_user': to_user.get_full_name() or to_user.username,
                'reason': reason
            }
        )

        return True

    def cancel(self):
        """
        Cancel the task.

        Returns:
            bool: True if cancelled successfully
        """
        if self.status != self.STATUS_PENDING:
            raise ValueError(_('Only pending tasks can be cancelled.'))

        self.status = self.STATUS_CANCELLED
        self.cancelled_at = timezone.now()
        self.save(update_fields=['status', 'cancelled_at', 'updated_at'])

        return True

    def withdraw(self, user):
        """
        Withdraw the task.

        Args:
            user: User withdrawing the task

        Returns:
            bool: True if withdrawn successfully
        """
        if self.status != self.STATUS_PENDING:
            raise ValueError(_('Only pending tasks can be withdrawn.'))

        # Check if user is the assignee or workflow initiator
        if self.assignee != user and self.instance.initiator != user:
            raise ValueError(_('You are not authorized to withdraw this task.'))

        self.status = self.STATUS_WITHDRAWN
        self.completed_at = timezone.now()
        self.completed_by = user
        self.save(update_fields=['status', 'completed_at', 'completed_by', 'updated_at'])

        return True

    def get_approvals_summary(self):
        """
        Get summary of approvals for this task.

        Returns:
            dict: Summary with approval counts and latest approval
        """
        approvals = self.approvals.all()

        return {
            'total': approvals.count(),
            'approved': approvals.filter(action='approve').count(),
            'rejected': approvals.filter(action='reject').count(),
            'returned': approvals.filter(action='return').count(),
            'latest': approvals.order_by('-created_at').first()
        }
