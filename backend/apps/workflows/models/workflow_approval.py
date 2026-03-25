"""
WorkflowApproval model for storing approval action records.

This model records each approval action taken on a workflow task,
providing a complete audit trail of who did what and when.
"""
from django.db import models
from django.utils.translation import gettext_lazy as _

from apps.common.models import BaseModel


class WorkflowApproval(BaseModel):
    """
    Workflow Approval model.

    Records individual approval actions on workflow tasks.
    Each task can have multiple approval records (e.g., for delegation history).
    """

    # Action choices
    ACTION_APPROVE = 'approve'
    ACTION_REJECT = 'reject'
    ACTION_RETURN = 'return'
    ACTION_DELEGATE = 'delegate'
    ACTION_WITHDRAW = 'withdraw'

    ACTION_CHOICES = [
        (ACTION_APPROVE, _('Approve')),
        (ACTION_REJECT, _('Reject')),
        (ACTION_RETURN, _('Return')),
        (ACTION_DELEGATE, _('Delegate')),
        (ACTION_WITHDRAW, _('Withdraw')),
    ]

    # Task relationship
    task = models.ForeignKey(
        'workflows.WorkflowTask',
        on_delete=models.CASCADE,
        related_name='approvals',
        verbose_name=_('Task'),
        help_text=_('The task this approval belongs to')
    )

    # Approver
    approver = models.ForeignKey(
        'accounts.User',
        on_delete=models.PROTECT,
        related_name='approvals',
        verbose_name=_('Approver'),
        help_text=_('User who performed this approval action')
    )

    # Action taken
    action = models.CharField(
        max_length=20,
        choices=ACTION_CHOICES,
        db_index=True,
        verbose_name=_('Action'),
        help_text=_('The approval action taken')
    )

    # Approval comment
    comment = models.TextField(
        blank=True,
        null=True,
        verbose_name=_('Comment'),
        help_text=_('Comment or reason for this approval action')
    )

    # Attachment (optional file attachment)
    attachment = models.CharField(
        max_length=500,
        blank=True,
        null=True,
        verbose_name=_('Attachment'),
        help_text=_('Optional attachment URL for this approval')
    )

    # IP address tracking
    ip_address = models.GenericIPAddressField(
        null=True,
        blank=True,
        verbose_name=_('IP Address'),
        help_text=_('IP address from which the approval was made')
    )

    # User agent tracking
    user_agent = models.CharField(
        max_length=500,
        blank=True,
        null=True,
        verbose_name=_('User Agent'),
        help_text=_('Browser/user agent of the approval device')
    )

    # Delegation info (for delegate actions)
    delegated_to = models.ForeignKey(
        'accounts.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='received_workflow_delegations',
        verbose_name=_('Delegated To'),
        help_text=_('User who received the delegation (for delegate actions)')
    )

    # Previous state (before this action)
    previous_status = models.CharField(
        max_length=20,
        blank=True,
        null=True,
        verbose_name=_('Previous Status'),
        help_text=_('Task status before this action')
    )

    # New state (after this action)
    new_status = models.CharField(
        max_length=20,
        blank=True,
        null=True,
        verbose_name=_('New Status'),
        help_text=_('Task status after this action')
    )

    # Processing time (milliseconds)
    processing_time_ms = models.IntegerField(
        null=True,
        blank=True,
        verbose_name=_('Processing Time (ms)'),
        help_text=_('Time taken to process the action in milliseconds')
    )

    class Meta:
        db_table = 'workflow_approvals'
        verbose_name = _('Workflow Approval')
        verbose_name_plural = _('Workflow Approvals')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['task', '-created_at']),
            models.Index(fields=['approver', '-created_at']),
            models.Index(fields=['action']),
            models.Index(fields=['-created_at']),
        ]

    def __str__(self):
        """String representation."""
        return f'{self.get_action_display()} - {self.approver.get_full_name() or self.approver.username} on {self.task.node_name}'

    @property
    def action_display(self):
        """Get display name for action."""
        return self.get_action_display()

    @classmethod
    def get_approvals_for_task(cls, task_id):
        """
        Get all approvals for a specific task.

        Args:
            task_id: The task ID

        Returns:
            QuerySet: Approvals for the task ordered by creation time
        """
        return cls.objects.filter(task_id=task_id).order_by('created_at')

    @classmethod
    def get_approvals_for_instance(cls, instance_id):
        """
        Get all approvals for a workflow instance.

        Args:
            instance_id: The workflow instance ID

        Returns:
            QuerySet: Approvals for the instance ordered by creation time
        """
        return cls.objects.filter(task__instance_id=instance_id).select_related(
            'task', 'approver'
        ).order_by('created_at')

    @classmethod
    def get_user_approvals(cls, user_id):
        """
        Get all approvals by a specific user.

        Args:
            user_id: The user ID

        Returns:
            QuerySet: Approvals by the user ordered by creation time
        """
        return cls.objects.filter(approver_id=user_id).select_related(
            'task', 'task__instance'
        ).order_by('-created_at')
