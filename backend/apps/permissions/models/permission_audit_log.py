"""
PermissionAuditLog Model - Audit trail for permission changes.

Logs all permission-related operations for compliance and debugging.
"""
from django.db import models
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey
from django.utils.translation import gettext_lazy as _

from apps.common.models import BaseModel


class PermissionAuditLog(BaseModel):
    """
    Audit log for permission-related operations.

    Tracks:
    - Permission grants and revocations
    - Permission modifications
    """

    # Operation type choices
    OPERATION_TYPE_CHOICES = [
        ('check', _('Permission Check')),
        ('grant', _('Grant Permission')),
        ('revoke', _('Revoke Permission')),
        ('modify', _('Modify Permission')),
        ('deny', _('Access Denied')),
    ]

    # Target type choices
    TARGET_TYPE_CHOICES = [
        ('field_permission', _('Field Permission')),
        ('data_permission', _('Data Permission')),
        ('user_permission', _('User Permission')),
    ]

    # User who performed the operation
    actor = models.ForeignKey(
        'accounts.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='permission_audit_logs',
        verbose_name=_('Actor'),
        db_comment='User who performed this operation'
    )

    # Target user (for user-specific permission operations)
    target_user = models.ForeignKey(
        'accounts.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='permission_audits',
        verbose_name=_('Target User'),
        db_comment='User affected by this operation'
    )

    # Operation details
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
        db_comment='Type of permission target'
    )

    # Permission details (JSON for flexibility)
    permission_details = models.JSONField(
        default=dict,
        blank=True,
        verbose_name=_('Permission Details'),
        db_comment='Details about the permission (field, scope, etc.)'
    )

    # Related object (generic relation for tracking specific permission object)
    content_type = models.ForeignKey(
        ContentType,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='permission_audit_logs',
        verbose_name=_('Content Type'),
    )
    object_id = models.UUIDField(
        null=True,
        blank=True,
        verbose_name=_('Object ID'),
    )
    content_object = GenericForeignKey(
        'content_type',
        'object_id'
    )

    # Operation result
    SUCCESS_CHOICES = [
        ('success', _('Success')),
        ('failure', _('Failure')),
        ('partial', _('Partial Success')),
    ]

    result = models.CharField(
        max_length=20,
        choices=SUCCESS_CHOICES,
        default='success',
        verbose_name=_('Result'),
        db_comment='Result of the operation'
    )

    # Error message (if operation failed)
    error_message = models.TextField(
        blank=True,
        verbose_name=_('Error Message'),
        db_comment='Error details if operation failed'
    )

    # IP address of the request
    ip_address = models.GenericIPAddressField(
        null=True,
        blank=True,
        verbose_name=_('IP Address'),
        db_comment='IP address from which the request originated'
    )

    # User agent
    user_agent = models.TextField(
        blank=True,
        verbose_name=_('User Agent'),
        db_comment='User agent string of the request'
    )

    # Request metadata
    request_metadata = models.JSONField(
        default=dict,
        blank=True,
        verbose_name=_('Request Metadata'),
        db_comment='Additional request metadata'
    )

    class Meta:
        db_table = 'permissions_audit_log'
        verbose_name = _('Permission Audit Log')
        verbose_name_plural = _('Permission Audit Logs')
        indexes = [
            models.Index(fields=['actor', '-created_at']),
            models.Index(fields=['target_user', '-created_at']),
            models.Index(fields=['operation_type', '-created_at']),
            models.Index(fields=['result', '-created_at']),
            models.Index(fields=['content_type', 'object_id']),
            models.Index(fields=['-created_at']),
        ]
        ordering = ['-created_at']

    def __str__(self):
        target = self.target_user.username if self.target_user else 'System'
        return f'{self.get_operation_type_display()} - {target} ({self.get_result_display()})'

    @classmethod
    def log_check(cls, user, target_type, permission_details, result='success', actor=None, **kwargs):
        """
        Log a permission check operation.

        Args:
            user: User being checked
            target_type: Type of permission
            permission_details: Details about the permission
            result: Result of the check
            actor: User who performed the check (defaults to user)
            **kwargs: Additional fields for the log
        """
        return cls.objects.create(
            actor=actor or user,
            target_user=user,
            operation_type='check' if result == 'success' else 'deny',
            target_type=target_type,
            permission_details=permission_details,
            result=result,
            **kwargs
        )

    @classmethod
    def log_grant(cls, actor, target_user=None, permission_details=None, content_object=None, **kwargs):
        """
        Log a permission grant operation.

        Args:
            actor: User granting the permission
            target_user: Target user
            permission_details: Details about the permission
            content_object: Related permission object
            **kwargs: Additional fields for the log
        """
        return cls.objects.create(
            actor=actor,
            target_user=target_user,
            operation_type='grant',
            target_type='user_permission',
            permission_details=permission_details or {},
            content_object=content_object,
            result='success',
            **kwargs
        )

    @classmethod
    def log_revoke(cls, actor, target_user=None, permission_details=None, content_object=None, **kwargs):
        """
        Log a permission revoke operation.

        Args:
            actor: User revoking the permission
            target_user: Target user
            permission_details: Details about the permission
            content_object: Related permission object
            **kwargs: Additional fields for the log
        """
        return cls.objects.create(
            actor=actor,
            target_user=target_user,
            operation_type='revoke',
            target_type='user_permission',
            permission_details=permission_details or {},
            content_object=content_object,
            result='success',
            **kwargs
        )

    @classmethod
    def log_modify(cls, actor, permission_details, content_object=None, result='success', **kwargs):
        """
        Log a permission modify operation.

        Args:
            actor: User modifying the permission
            permission_details: Details about the modification
            content_object: Related permission object
            result: Result of the operation
            **kwargs: Additional fields for the log
        """
        return cls.objects.create(
            actor=actor,
            operation_type='modify',
            target_type='field_permission',
            permission_details=permission_details,
            content_object=content_object,
            result=result,
            **kwargs
        )
