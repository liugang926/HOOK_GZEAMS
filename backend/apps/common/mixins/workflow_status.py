"""
Workflow Status Mixin for business models.

Provides workflow-aware status tracking fields and hooks
that any business model can inherit to participate in
workflow-driven approval processes.
"""
from django.db import models
from django.utils.translation import gettext_lazy as _


class WorkflowStatusMixin(models.Model):
    """
    Mixin to add workflow-aware status tracking to business models.

    Adds approval_status field and lifecycle hooks that are invoked
    by BusinessStateSyncService when workflow state changes occur.

    Usage:
        class AssetPickup(BaseModel, WorkflowStatusMixin):
            ...
            def on_workflow_approved(self):
                self.status = 'active'
                self.save(update_fields=['status', 'updated_at'])
    """

    APPROVAL_DRAFT = 'draft'
    APPROVAL_PENDING = 'pending_approval'
    APPROVAL_APPROVED = 'approved'
    APPROVAL_REJECTED = 'rejected'
    APPROVAL_CANCELLED = 'cancelled'

    APPROVAL_STATUS_CHOICES = [
        (APPROVAL_DRAFT, _('Draft')),
        (APPROVAL_PENDING, _('Pending Approval')),
        (APPROVAL_APPROVED, _('Approved')),
        (APPROVAL_REJECTED, _('Rejected')),
        (APPROVAL_CANCELLED, _('Cancelled')),
    ]

    approval_status = models.CharField(
        max_length=20,
        choices=APPROVAL_STATUS_CHOICES,
        default=APPROVAL_DRAFT,
        db_index=True,
        verbose_name=_('Approval Status'),
        help_text=_('Current workflow approval status of this document'),
    )

    workflow_instance_id = models.UUIDField(
        null=True,
        blank=True,
        db_index=True,
        verbose_name=_('Workflow Instance ID'),
        help_text=_('ID of the linked WorkflowInstance'),
    )

    submitted_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_('Submitted At'),
        help_text=_('Timestamp when the document was submitted for approval'),
    )

    approved_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_('Approved At'),
        help_text=_('Timestamp when the document was approved'),
    )

    class Meta:
        abstract = True

    # --- Lifecycle hooks for subclasses ---

    def on_workflow_submitted(self):
        """Hook called when document is submitted for approval.

        Override in subclass to implement business-specific submission logic.
        """
        pass

    def on_workflow_approved(self):
        """Hook called when document is approved.

        Override in subclass to implement business-specific approval logic
        (e.g., activate an asset, finalize a transfer).
        """
        pass

    def on_workflow_rejected(self):
        """Hook called when document is rejected.

        Override in subclass to implement business-specific rejection logic.
        """
        pass

    def on_workflow_cancelled(self):
        """Hook called when workflow is cancelled or withdrawn.

        Override in subclass to implement business-specific cancellation logic.
        """
        pass
