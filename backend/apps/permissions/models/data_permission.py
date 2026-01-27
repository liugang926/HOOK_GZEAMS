"""
DataPermission Model - Data-level (row-level) permission control.

Defines row-level access permissions based on data scope.
Supports organizational hierarchy-based data filtering.
"""
from django.db import models
from django.contrib.contenttypes.models import ContentType
from django.utils.translation import gettext_lazy as _

from apps.common.models import BaseModel


class DataPermission(BaseModel):
    """
    Row-level permission for controlling data access scope.

    Scope types:
    - all: Access to all data
    - self_dept: Access to own department data only
    - self_and_sub: Access to own department and all sub-departments
    - specified: Access to specified departments only
    - custom: Custom SQL filter expression
    - self: Access to own data only
    """

    # Data scope type choices
    SCOPE_TYPE_CHOICES = [
        ('all', _('All Data')),
        ('self', _('Own Data Only')),
        ('self_dept', _('Own Department')),
        ('self_and_sub', _('Department and Sub-departments')),
        ('specified', _('Specified Departments')),
        ('custom', _('Custom Filter')),
    ]

    # Target assignment (user-specific)
    user = models.ForeignKey(
        'accounts.User',
        on_delete=models.CASCADE,
        null=False,
        blank=False,
        related_name='data_permissions',
        verbose_name=_('User'),
        db_comment='User this permission applies to'
    )

    # Content type binding (which model)
    content_type = models.ForeignKey(
        ContentType,
        on_delete=models.CASCADE,
        related_name='data_permissions',
        verbose_name=_('Content Type'),
        db_comment='Model this permission applies to'
    )

    # Permission scope configuration
    scope_type = models.CharField(
        max_length=20,
        choices=SCOPE_TYPE_CHOICES,
        default='self_dept',
        verbose_name=_('Scope Type'),
        db_comment='Data access scope type'
    )

    # JSON field for storing scope values (department IDs for 'specified', custom filter for 'custom')
    scope_value = models.JSONField(
        default=dict,
        blank=True,
        verbose_name=_('Scope Value'),
        db_comment='Configuration for scope (dept IDs, custom filter, etc.)'
    )

    # Department field to use for filtering (default: department)
    department_field = models.CharField(
        max_length=100,
        default='department',
        blank=True,
        verbose_name=_('Department Field'),
        db_comment='Field name for department reference in the target model'
    )

    # User field to use for filtering (default: created_by)
    user_field = models.CharField(
        max_length=100,
        default='created_by',
        blank=True,
        verbose_name=_('User Field'),
        db_comment='Field name for user reference in the target model'
    )

    # Metadata
    description = models.TextField(
        blank=True,
        verbose_name=_('Description'),
        db_comment='Description of what this permission controls'
    )

    class Meta:
        db_table = 'permissions_data_permission'
        verbose_name = _('Data Permission')
        verbose_name_plural = _('Data Permissions')
        indexes = [
            models.Index(fields=['content_type', 'scope_type']),
            models.Index(fields=['user', 'scope_type']),
            models.Index(fields=['-created_at']),
        ]
        unique_together = [
            ['user', 'content_type'],
        ]
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.content_type.model} - {self.get_scope_type_display()} ({self.user.username})'

    def get_scope_department_ids(self, user):
        """
        Get department IDs for filtering based on scope type and user.

        Args:
            user: User instance to evaluate scope for

        Returns:
            Set of department IDs for filtering, or None for all/self
        """
        if self.scope_type == 'all':
            return None  # No filtering

        elif self.scope_type == 'self':
            return set()  # Will use user field filter

        elif self.scope_type == 'self_dept':
            # Get user's primary department
            from apps.organizations.models import UserDepartment
            user_dept = UserDepartment.objects.filter(
                user=user,
                is_primary=True,
                is_deleted=False
            ).first()
            if user_dept:
                return {user_dept.department_id}
            return set()

        elif self.scope_type == 'self_and_sub':
            # Get user's primary department and all descendants
            from apps.organizations.models import UserDepartment
            user_dept = UserDepartment.objects.filter(
                user=user,
                is_primary=True,
                is_deleted=False
            ).first()
            if user_dept:
                dept_ids = {user_dept.department_id}
                # Add descendant departments
                descendants = user_dept.department.get_descendants()
                dept_ids.update(d.id for d in descendants)
                return dept_ids
            return set()

        elif self.scope_type == 'specified':
            # Return specified department IDs
            dept_ids = self.scope_value.get('department_ids', [])
            return set(dept_ids)

        return set()

    def get_custom_filter(self):
        """
        Get custom filter expression for 'custom' scope type.

        Returns:
            Dict filter expression or None
        """
        if self.scope_type == 'custom':
            return self.scope_value.get('filter_expression')
        return None

    @classmethod
    def get_effective_permission(cls, user, content_type):
        """
        Get the effective data permission for a user.

        Args:
            user: User instance
            content_type: ContentType instance

        Returns:
            DataPermission instance or None
        """
        from apps.accounts.models import User

        if not isinstance(user, User) or not user.is_authenticated:
            return None

        # Superusers get all access
        if user.is_superuser:
            # Return a permission-like object with 'all' scope
            return type('obj', (object,), {'scope_type': 'all', 'get_scope_department_ids': lambda u: None})()

        # Check user-specific permission
        try:
            user_perm = cls.objects.filter(
                user=user,
                content_type=content_type,
                is_deleted=False
            ).first()

            return user_perm
        except cls.DoesNotExist:
            pass

        # Default: return own data only
        return type('obj', (object,), {
            'scope_type': 'self',
            'get_scope_department_ids': lambda u: set(),
            'department_field': 'department',
            'user_field': 'created_by'
        })()

    def apply_to_queryset(self, queryset, user):
        """
        Apply this data permission to a queryset.

        Args:
            queryset: QuerySet to filter
            user: User to apply permission for

        Returns:
            Filtered QuerySet
        """
        dept_ids = self.get_scope_department_ids(user)

        if self.scope_type == 'all':
            return queryset

        elif self.scope_type == 'self':
            # Filter by user field
            user_field = self.user_field or 'created_by'
            return queryset.filter(**{user_field: user})

        elif dept_ids is not None:
            # Filter by department field
            dept_field = self.department_field or 'department'
            return queryset.filter(**{f'{dept_field}_id__in': dept_ids})

        # Default: return only user's own data
        return queryset.filter(created_by=user)
