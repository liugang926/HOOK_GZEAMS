from django.db import models
from django.contrib.auth import get_user_model
from django.conf import settings
import uuid


class TenantManager(models.Manager):
    """
    Tenant-aware manager that automatically filters by organization.

    Uses thread-local storage to get current organization context.
    Automatically filters out soft-deleted records.
    """

    def get_queryset(self):
        """
        Get queryset with automatic organization and soft-delete filtering.

        Returns:
            QuerySet: Filtered queryset
        """
        queryset = super().get_queryset()

        # Auto-filter by current organization from thread-local context
        from apps.common.middleware import get_current_organization
        org_id = get_current_organization()

        if org_id:
            queryset = queryset.filter(organization_id=org_id)

        # Auto-filter out soft-deleted records
        queryset = queryset.filter(is_deleted=False)

        return queryset


class BaseModel(models.Model):
    """
    Abstract base model for all GZEAMS models.

    Provides automatic:
    - Organization isolation (multi-tenancy)
    - Soft delete capability
    - Audit trail (created/updated timestamps and user tracking)
    - Dynamic custom fields (JSONB)
    """

    # Tenant-aware manager for automatic organization filtering
    objects = TenantManager()
    # All objects manager bypasses organization filtering (use carefully)
    all_objects = models.Manager()

    # Primary key - UUID for distributed systems
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        verbose_name='ID'
    )

    # Organization isolation - REQUIRED for multi-tenancy
    # Forward reference to Organization model to avoid circular imports
    # Null and blank allowed for models like User that may exist before org assignment
    organization = models.ForeignKey(
        'organizations.Organization',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='%(app_label)s_%(class)s_set',
        verbose_name='Organization',
        db_comment='Organization for multi-tenant data isolation'
    )

    # Soft delete fields
    is_deleted = models.BooleanField(
        default=False,
        db_index=True,
        verbose_name='Is Deleted',
        db_comment='Soft delete flag, records are filtered out by default'
    )
    deleted_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='Deleted At',
        db_comment='Timestamp when record was soft deleted'
    )

    # Audit trail fields
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Created At',
        db_comment='Timestamp when record was created'
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name='Updated At',
        db_comment='Timestamp when record was last updated'
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='%(app_label)s_%(class)s_created',
        verbose_name='Created By',
        db_comment='User who created this record'
    )
    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='%(app_label)s_%(class)s_updated',
        verbose_name='Updated By',
        db_comment='User who last updated this record'
    )
    deleted_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='%(app_label)s_%(class)s_deleted',
        verbose_name='Deleted By',
        db_comment='User who soft deleted this record'
    )

    # Dynamic custom fields for low-code platform
    custom_fields = models.JSONField(
        default=dict,
        blank=True,
        verbose_name='Custom Fields',
        db_comment='Dynamic fields for metadata-driven extensions'
    )

    class Meta:
        abstract = True  # This is an abstract base class
        indexes = [
            models.Index(fields=['-created_at']),
            models.Index(fields=['is_deleted']),
        ]

    def soft_delete(self, user=None):
        """
        Perform soft delete instead of hard delete.

        Args:
            user: Optional user who performed the deletion
        """
        from django.utils import timezone
        self.is_deleted = True
        self.deleted_at = timezone.now()
        if user:
            # Store deleted_by if the model has this field
            if hasattr(self, 'deleted_by'):
                self.deleted_by = user
        self.save(update_fields=['is_deleted', 'deleted_at', 'deleted_by', 'updated_at'])

    def hard_delete(self):
        """
        Perform actual hard delete from database.
        Use with caution - this cannot be undone.
        """
        self.delete()
