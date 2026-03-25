"""
Organization Data Permission Service.

Provides data permission filtering based on organization structure.
Users can see data from:
1. Their own departments
2. Departments they lead (and all descendants)
"""
from typing import Set, List, Optional
from django.contrib.auth import get_user_model
from django.db.models import Q

from apps.organizations.models import Department, UserDepartment

User = get_user_model()


class OrgDataPermissionService:
    """
    Organization-based data permission service.

    Calculates what data a user can access based on their
    department memberships and leadership roles.
    """

    def __init__(self, user: User, organization_id: Optional[int] = None):
        """
        Initialize permission service for a user.

        Args:
            user: User instance
            organization_id: Organization ID (optional, defaults to user's org)
        """
        self.user = user
        self.organization_id = organization_id or getattr(user, 'organization_id', None)

        # Cache for department IDs
        self._viewable_department_ids: Optional[Set[int]] = None
        self._managed_department_ids: Optional[Set[int]] = None

    def get_viewable_department_ids(self, recursive: bool = True) -> Set[int]:
        """
        Get IDs of departments the user can view.

        Includes:
        - Departments the user belongs to
        - Departments the user leads (and descendants if recursive=True)

        Args:
            recursive: Include descendant departments of led departments

        Returns:
            Set of department IDs
        """
        if self._viewable_department_ids is not None:
            return self._viewable_department_ids

        dept_ids = set()

        # Get user's own departments
        user_depts = UserDepartment.objects.filter(
            user=self.user,
            organization_id=self.organization_id,
            is_deleted=False
        ).values_list('department_id', flat=True)
        dept_ids.update(user_depts)

        # Get departments user leads (and descendants if recursive)
        led_depts = Department.objects.filter(
            leader=self.user,
            organization_id=self.organization_id,
            is_deleted=False
        )

        for dept in led_depts:
            dept_ids.add(dept.id)
            if recursive:
                dept_ids.update(dept.get_descendant_ids())

        self._viewable_department_ids = dept_ids
        return dept_ids

    def get_managed_department_ids(self, recursive: bool = True) -> Set[int]:
        """
        Get IDs of departments the user manages (as leader).

        Args:
            recursive: Include descendant departments

        Returns:
            Set of department IDs
        """
        if self._managed_department_ids is not None:
            return self._managed_department_ids

        dept_ids = set()

        # Get departments where user is leader
        led_depts = Department.objects.filter(
            leader=self.user,
            organization_id=self.organization_id,
            is_deleted=False
        )

        for dept in led_depts:
            dept_ids.add(dept.id)
            if recursive:
                dept_ids.update(dept.get_descendant_ids())

        # Also check UserDepartment for is_leader flag
        user_leader_depts = UserDepartment.objects.filter(
            user=self.user,
            organization_id=self.organization_id,
            is_leader=True,
            is_deleted=False
        ).values_list('department_id', flat=True)

        dept_ids.update(user_leader_depts)

        self._managed_department_ids = dept_ids
        return dept_ids

    def get_viewable_user_ids(self, department_ids: Optional[Set[int]] = None) -> Set[int]:
        """
        Get IDs of users the current user can view.

        Args:
            department_ids: Optional department IDs to filter by

        Returns:
            Set of user IDs
        """
        if department_ids is None:
            department_ids = self.get_viewable_department_ids()

        # Get users in viewable departments
        user_ids = set(UserDepartment.objects.filter(
            department_id__in=department_ids,
            is_deleted=False
        ).values_list('user_id', flat=True))

        # Always include self
        user_ids.add(self.user.id)
        return user_ids

    def can_view_department(self, department_id: int) -> bool:
        """
        Check if user can view a specific department.

        Args:
            department_id: Department ID to check

        Returns:
            True if user can view the department
        """
        viewable_ids = self.get_viewable_department_ids()
        return department_id in viewable_ids

    def can_manage_department(self, department_id: int) -> bool:
        """
        Check if user can manage (edit/delete) a department.

        User can manage if they are a leader of that department
        or any of its ancestor departments.

        Args:
            department_id: Department ID to check

        Returns:
            True if user can manage the department
        """
        managed_ids = self.get_managed_department_ids()
        return department_id in managed_ids

    def can_view_user(self, user_id: int) -> bool:
        """
        Check if user can view another user.

        Users can view others who are in their viewable departments.

        Args:
            user_id: User ID to check

        Returns:
            True if user can view the other user
        """
        # Always can view self
        if user_id == self.user.id:
            return True

        viewable_user_ids = self.get_viewable_user_ids()
        return user_id in viewable_user_ids

    def get_data_scope(self) -> str:
        """
        Get user's data scope level.

        Returns:
            Data scope: 'all', 'department', 'department_and_children', or 'self'
        """
        if self.user.is_superuser:
            return 'all'

        managed_ids = self.get_managed_department_ids(recursive=True)
        if managed_ids:
            # Check if user manages all departments in org
            total_depts = Department.objects.filter(
                organization_id=self.organization_id,
                is_deleted=False
            ).count()
            if len(managed_ids) >= total_depts:
                return 'all'
            return 'department_and_children'

        # Check if user has any department membership
        viewable_ids = self.get_viewable_department_ids(recursive=False)
        if viewable_ids:
            return 'department'

        return 'self'

    def filter_queryset_by_permission(self, queryset, user_field='user', department_field='department'):
        """
        Filter a queryset based on user's data permissions.

        Args:
            queryset: QuerySet to filter
            user_field: Field name for user (default: 'user')
            department_field: Field name for department (default: 'department')

        Returns:
            Filtered QuerySet
        """
        if self.user.is_superuser:
            return queryset

        data_scope = self.get_data_scope()

        if data_scope == 'all':
            return queryset
        elif data_scope == 'department_and_children':
            dept_ids = self.get_managed_department_ids(recursive=True)
            return queryset.filter(**{f'{department_field}__id__in': list(dept_ids)})
        elif data_scope == 'department':
            dept_ids = self.get_viewable_department_ids(recursive=False)
            return queryset.filter(**{f'{department_field}__id__in': list(dept_ids)})
        else:  # self
            return queryset.filter(**{user_field: self.user})

    @staticmethod
    def get_users_with_permission(department_id: int, permission_type: str = 'view') -> List[int]:
        """
        Get users who have permission to access a department.

        Args:
            department_id: Department ID
            permission_type: 'view' or 'manage'

        Returns:
            List of user IDs
        """
        dept = Department.objects.filter(id=department_id).first()
        if not dept:
            return []

        user_ids = set()

        # Get all users in this department
        user_ids.update(UserDepartment.objects.filter(
            department=dept,
            is_deleted=False
        ).values_list('user_id', flat=True))

        if permission_type == 'manage':
            # Only include leaders
            leader_ids = set(UserDepartment.objects.filter(
                department=dept,
                is_leader=True,
                is_deleted=False
            ).values_list('user_id', flat=True))
            if dept.leader_id:
                leader_ids.add(dept.leader_id)
            return list(leader_ids)

        return list(user_ids)


def get_viewable_departments(user: User, organization_id: Optional[int] = None) -> List[Department]:
    """
    Get list of departments viewable by user.

    Convenience function for getting departments a user can access.

    Args:
        user: User instance
        organization_id: Organization ID

    Returns:
        List of Department objects
    """
    service = OrgDataPermissionService(user, organization_id)
    dept_ids = service.get_viewable_department_ids()

    return Department.objects.filter(
        id__in=dept_ids,
        is_deleted=False
    ).order_by('level', 'order', 'code')


def get_viewable_users(user: User, organization_id: Optional[int] = None) -> List[User]:
    """
    Get list of users viewable by current user.

    Convenience function for getting users a user can access.

    Args:
        user: Current user
        organization_id: Organization ID

    Returns:
        List of User objects
    """
    service = OrgDataPermissionService(user, organization_id)
    user_ids = service.get_viewable_user_ids()

    return User.objects.filter(
        id__in=user_ids
    ).distinct()
