from django.db import models
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey
from django.utils.translation import gettext_lazy as _

from apps.common.models import BaseModel


class ActivityLog(BaseModel):
    """
    ActivityLog Model - Audit trail for business object lifecycle.

    Records generic CRUD operations and custom actions performed on any business object.
    
    Inherits from BaseModel:
    - organization: Multi-tenant data isolation
    - is_deleted: Soft delete support
    - created_at, updated_at: Audit timestamps
    - created_by: User who performed the operation (handled as actor)
    - custom_fields: Additional metadata
    """

    ACTION_CHOICES = [
        ('create', _('Created')),
        ('update', _('Updated')),
        ('delete', _('Deleted')),
        ('status_change', _('Status Changed')),
        ('assign', _('Assigned')),
        ('unassign', _('Unassigned')),
        ('custom', _('Custom Action')),
    ]

    actor = models.ForeignKey(
        'accounts.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='activity_logs',
        verbose_name=_('Actor'),
        db_comment='User who performed the action'
    )

    action = models.CharField(
        max_length=50,
        choices=ACTION_CHOICES,
        default='update',
        verbose_name=_('Action'),
        db_comment='Action performed'
    )

    # Generic relation to target object
    content_type = models.ForeignKey(
        ContentType,
        on_delete=models.CASCADE,
        verbose_name=_('Content Type'),
        db_comment='Type of the target object'
    )
    object_id = models.CharField(
        max_length=255,
        verbose_name=_('Object ID'),
        db_comment='ID of the target object'
    )
    content_object = GenericForeignKey('content_type', 'object_id')

    changes = models.JSONField(
        null=True,
        blank=True,
        verbose_name=_('Changes'),
        db_comment='JSON array of changes. Format: [{"fieldLabel": "Status", "oldValue": "Draft", "newValue": "Published"}]'
    )

    description = models.TextField(
        null=True,
        blank=True,
        verbose_name=_('Description'),
        db_comment='Human readable description of the action'
    )

    class Meta:
        db_table = 'system_activity_logs'
        verbose_name = _('Activity Log')
        verbose_name_plural = _('Activity Logs')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['content_type', 'object_id', '-created_at']),
            models.Index(fields=['actor', '-created_at']),
        ]

    def __str__(self):
        return f"{self.actor} {self.action} {self.content_type} {self.object_id}"
