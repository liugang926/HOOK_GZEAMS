"""
DepartmentPermissionInheritance Model - Permission inheritance between departments.

Defines how permissions are inherited within the department hierarchy.
"""
from django.db import models
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

from apps.common.models import BaseModel


class DepartmentPermissionInheritance(BaseModel):
    """
    Permission inheritance based on department hierarchy.

    Allows permissions defined for a department to be inherited
    by its descendant departments in the organization tree.
    """

    # Source department (permissions originate here)
    source_department = models.ForeignKey(
        'organizations.Department',
        on_delete=models.CASCADE,
        related_name='permission_inheritances_as_source',
        verbose_name=_('Source Department'),
        db_comment='Department whose permissions are inherited'
    )

    # Target department (permissions are inherited to)
    target_department = models.ForeignKey(
        'organizations.Department',
        on_delete=models.CASCADE,
        related_name='permission_inheritances_as_target',
        verbose_name=_('Target Department'),
        db_comment='Department that inherits permissions'
    )

    # Inheritance type
    INHERITANCE_TYPE_CHOICES = [
        ('data', _('Data Permissions')),  # Inherit data scope permissions
        ('field', _('Field Permissions')),  # Inherit field access permissions
        ('both', _('Both Permissions')),  # Inherit both data and field permissions
    ]

    inheritance_type = models.CharField(
        max_length=20,
        choices=INHERITANCE_TYPE_CHOICES,
        default='both',
        verbose_name=_('Inheritance Type'),
        db_comment='Type of permissions to inherit'
    )

    # Is this inheritance active
    is_active = models.BooleanField(
        default=True,
        verbose_name=_('Is Active'),
        db_comment='Whether this inheritance is currently active'
    )

    # Allow override (can target department override inherited permissions?)
    allow_override = models.BooleanField(
        default=True,
        verbose_name=_('Allow Override'),
        db_comment='Whether target can override inherited permissions'
    )

    # Priority for conflict resolution
    priority = models.IntegerField(
        default=0,
        verbose_name=_('Priority'),
        db_comment='Priority when multiple inheritances conflict'
    )

    # Metadata
    description = models.TextField(
        blank=True,
        verbose_name=_('Description'),
        db_comment='Description of this inheritance relationship'
    )

    class Meta:
        db_table = 'permissions_department_inheritance'
        verbose_name = _('Department Permission Inheritance')
        verbose_name_plural = _('Department Permission Inheritances')
        indexes = [
            models.Index(fields=['source_department', 'target_department']),
            models.Index(fields=['target_department', 'is_active']),
            models.Index(fields=['inheritance_type']),
            models.Index(fields=['priority']),
            models.Index(fields=['-created_at']),
        ]
        unique_together = [['source_department', 'target_department']]
        ordering = ['-priority', 'created_at']

    def __str__(self):
        return f'{self.target_department.name} <- {self.source_department.name} ({self.get_inheritance_type_display()})'

    def clean(self):
        """Validate that source and target are different."""
        if self.source_department_id == self.target_department_id:
            raise ValidationError(_('Source and target departments cannot be the same.'))

    def save(self, *args, **kwargs):
        """Run validation before saving."""
        self.clean()
        super().save(*args, **kwargs)

    def check_permission_inherited(self, permission_type):
        """
        Check if a specific permission type is inherited.

        Args:
            permission_type: Type of permission ('data', 'field', or 'both')

        Returns:
            True if permission should be inherited
        """
        if not self.is_active:
            return False

        if self.inheritance_type == 'both':
            return True

        return self.inheritance_type == permission_type

    @classmethod
    def get_inherited_permissions(cls, department, permission_type='both'):
        """
        Get all permissions inherited by a department.

        Args:
            department: Department instance
            permission_type: Type to check ('data', 'field', or 'both')

        Returns:
            QuerySet of active inheritance relationships
        """
        queryset = cls.objects.filter(
            target_department=department,
            is_active=True,
            is_deleted=False
        )

        if permission_type != 'both':
            queryset = queryset.filter(inheritance_type__in=[permission_type, 'both'])

        return queryset.select_related('source_department').order_by('-priority')

    @classmethod
    def sync_hierarchy_inheritances(cls, department_id):
        """
        Sync inheritances for a department based on hierarchy.

        Creates inheritances from all ancestor departments.

        Args:
            department_id: Department ID to sync for
        """
        from apps.organizations.models import Department

        department = Department.objects.get(id=department_id)
        ancestors = department.get_ancestors()

        # Create inheritances from ancestors
        for ancestor in ancestors:
            cls.objects.get_or_create(
                source_department=ancestor,
                target_department=department,
                defaults={
                    'inheritance_type': 'both',
                    'is_active': True,
                    'organization': department.organization,
                }
            )
