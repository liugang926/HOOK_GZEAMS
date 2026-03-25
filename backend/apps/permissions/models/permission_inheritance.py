"""
PermissionInheritance Model - Permission inheritance between roles.

Defines how permissions are inherited from parent roles to child roles.
"""
from django.db import models
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

from apps.common.models import BaseModel


class PermissionInheritance(BaseModel):
    """
    Permission inheritance relationship between roles.

    Allows child roles to inherit permissions from parent roles.
    Supports multiple inheritance paths with priority control.
    """

    # Parent role (source of permissions)
    parent_role = models.ForeignKey(
        'accounts.Role',
        on_delete=models.CASCADE,
        related_name='inherited_by_children',
        verbose_name=_('Parent Role'),
        db_comment='Role whose permissions are inherited'
    )

    # Child role (receiver of permissions)
    child_role = models.ForeignKey(
        'accounts.Role',
        on_delete=models.CASCADE,
        related_name='inherited_from_parents',
        verbose_name=_('Child Role'),
        db_comment='Role that inherits permissions'
    )

    # Inheritance type
    INHERITANCE_TYPE_CHOICES = [
        ('full', _('Full Inheritance')),  # Inherit all permissions
        ('partial', _('Partial Inheritance')),  # Inherit only specified permissions
        ('exclude', _('Exclude Inheritance')),  # Inherit all except specified
    ]

    inheritance_type = models.CharField(
        max_length=20,
        choices=INHERITANCE_TYPE_CHOICES,
        default='full',
        verbose_name=_('Inheritance Type'),
        db_comment='How permissions are inherited'
    )

    # Specific permissions to include/exclude (for partial/exclude types)
    permission_types = models.JSONField(
        default=list,
        blank=True,
        verbose_name=_('Permission Types'),
        db_comment='List of permission type names to include/exclude'
    )

    # Is this inheritance active
    is_active = models.BooleanField(
        default=True,
        verbose_name=_('Is Active'),
        db_comment='Whether this inheritance is currently active'
    )

    # Priority for conflict resolution (higher = takes precedence)
    priority = models.IntegerField(
        default=0,
        verbose_name=_('Priority'),
        db_comment='Priority when multiple inheritance paths conflict'
    )

    # Metadata
    description = models.TextField(
        blank=True,
        verbose_name=_('Description'),
        db_comment='Description of this inheritance relationship'
    )

    class Meta:
        db_table = 'permissions_inheritance'
        verbose_name = _('Permission Inheritance')
        verbose_name_plural = _('Permission Inheritances')
        indexes = [
            models.Index(fields=['parent_role', 'child_role']),
            models.Index(fields=['child_role', 'is_active']),
            models.Index(fields=['priority']),
            models.Index(fields=['-created_at']),
        ]
        unique_together = [['parent_role', 'child_role']]
        ordering = ['-priority', 'created_at']

    def __str__(self):
        return f'{self.child_role.name} <- {self.parent_role.name} ({self.get_inheritance_type_display()})'

    def clean(self):
        """Validate that parent and child are different."""
        if self.parent_role_id == self.child_role_id:
            raise ValidationError(_('Parent and child roles cannot be the same.'))

    def save(self, *args, **kwargs):
        """Run validation before saving."""
        self.clean()
        super().save(*args, **kwargs)

    def check_permission_inherited(self, permission_type):
        """
        Check if a specific permission type is inherited.

        Args:
            permission_type: Type of permission to check

        Returns:
            True if permission should be inherited
        """
        if not self.is_active:
            return False

        if self.inheritance_type == 'full':
            return True

        elif self.inheritance_type == 'partial':
            return permission_type in self.permission_types

        elif self.inheritance_type == 'exclude':
            return permission_type not in self.permission_types

        return False

    @classmethod
    def get_all_parent_roles(cls, role):
        """
        Get all parent roles for a given role recursively.

        Args:
            role: Role instance

        Returns:
            QuerySet of all parent roles
        """
        from apps.accounts.models import Role

        parent_ids = set()
        to_process = {role.id}

        while to_process:
            current_id = to_process.pop()
            parents = cls.objects.filter(
                child_role_id=current_id,
                is_active=True,
                is_deleted=False
            ).values_list('parent_role_id', flat=True)

            for parent_id in parents:
                if parent_id not in parent_ids:
                    parent_ids.add(parent_id)
                    to_process.add(parent_id)

        return Role.objects.filter(id__in=parent_ids)

    @classmethod
    def get_all_child_roles(cls, role):
        """
        Get all child roles for a given role recursively.

        Args:
            role: Role instance

        Returns:
            QuerySet of all child roles
        """
        from apps.accounts.models import Role

        child_ids = set()
        to_process = {role.id}

        while to_process:
            current_id = to_process.pop()
            children = cls.objects.filter(
                parent_role_id=current_id,
                is_active=True,
                is_deleted=False
            ).values_list('child_role_id', flat=True)

            for child_id in children:
                if child_id not in child_ids:
                    child_ids.add(child_id)
                    to_process.add(child_id)

        return Role.objects.filter(id__in=child_ids)
