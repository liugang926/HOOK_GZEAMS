"""
Permission service for centralized permission management.

Provides:
- Unified permission checking
- Role-based access control
- Field-level permissions
- Data scope filtering
- Permission caching
"""
from typing import Set, List, Dict, Optional, Any
from django.db.models import QuerySet, Q
from django.contrib.auth import get_user_model

from apps.common.services.permission_cache import PermissionCache

User = get_user_model()


class PermissionService:
    """
    Centralized permission service.

    Provides static methods for all permission-related operations.
    """

    # Data scope constants
    DATA_SCOPE_ALL = 'all'      # All data
    DATA_SCOPE_ORG = 'org'      # Organization and subordinates
    DATA_SCOPE_DEPT = 'dept'    # Own department only
    DATA_SCOPE_SELF = 'self'    # Own data only
    DATA_SCOPE_CUSTOM = 'custom'  # Custom rules

    # Action constants
    ACTION_CREATE = 'create'
    ACTION_READ = 'read'
    ACTION_UPDATE = 'update'
    ACTION_DELETE = 'delete'
    ACTION_EXPORT = 'export'
    ACTION_IMPORT = 'import'
    ACTION_APPROVE = 'approve'

    @staticmethod
    def get_user_permissions(
        user,
        use_cache: bool = True
    ) -> Set[str]:
        """
        Get all permissions for a user.

        Combines:
        - Django system permissions
        - Custom role permissions

        Args:
            user: User instance
            use_cache: Whether to use cache

        Returns:
            Set of permission codes
        """
        if not user or not user.is_authenticated:
            return set()

        user_id = str(user.id)

        # Check cache
        if use_cache:
            cached = PermissionCache.get_user_permissions(user_id)
            if cached is not None:
                return cached

        # Collect permissions
        permissions = set()

        # 1. Django system permissions
        django_perms = user.get_all_permissions()
        permissions.update(django_perms)

        # 2. Custom role permissions
        try:
            from apps.permissions.models import UserRole
            user_roles = UserRole.objects.filter(
                user=user,
                is_active=True
            ).select_related('role')

            for user_role in user_roles:
                role = user_role.role
                if hasattr(role, 'permissions') and role.permissions:
                    if isinstance(role.permissions, list):
                        permissions.update(role.permissions)
                    elif isinstance(role.permissions, dict):
                        permissions.update(role.permissions.keys())
        except Exception:
            pass

        # Cache result
        if use_cache:
            PermissionCache.set_user_permissions(user_id, permissions)

        return permissions

    @staticmethod
    def get_user_roles(
        user,
        organization=None,
        use_cache: bool = True
    ) -> List[Dict]:
        """
        Get all roles for a user.

        Args:
            user: User instance
            organization: Optional organization filter
            use_cache: Whether to use cache

        Returns:
            List of role dicts with id, code, name
        """
        if not user or not user.is_authenticated:
            return []

        user_id = str(user.id)

        # Check cache
        if use_cache and organization is None:
            cached = PermissionCache.get_user_roles(user_id)
            if cached is not None:
                return cached

        roles = []
        try:
            from apps.permissions.models import UserRole
            query = UserRole.objects.filter(
                user=user,
                is_active=True
            ).select_related('role')

            if organization:
                query = query.filter(organization=organization)

            for user_role in query:
                role = user_role.role
                roles.append({
                    'id': str(role.id),
                    'code': role.code,
                    'name': role.name,
                    'data_scope': getattr(role, 'data_scope', PermissionService.DATA_SCOPE_SELF)
                })
        except Exception:
            pass

        # Cache result
        if use_cache and organization is None:
            PermissionCache.set_user_roles(user_id, roles)

        return roles

    @staticmethod
    def check_permission(
        user,
        permission_code: str,
        use_cache: bool = True
    ) -> bool:
        """
        Check if user has a specific permission.

        Supports wildcard matching:
        - 'assets.*' matches all asset permissions
        - 'assets.view_asset' matches exactly

        Args:
            user: User instance
            permission_code: Permission code to check
            use_cache: Whether to use cache

        Returns:
            bool: True if user has permission
        """
        if not user or not user.is_authenticated:
            return False

        # Superusers have all permissions
        if user.is_superuser:
            return True

        permissions = PermissionService.get_user_permissions(user, use_cache)

        # Exact match
        if permission_code in permissions:
            return True

        # Wildcard match: check if user has any permission in the module
        if '.' in permission_code:
            module = permission_code.split('.')[0]
            if f'{module}.*' in permissions:
                return True

        return False

    @staticmethod
    def check_any_permission(
        user,
        permission_codes: List[str],
        use_cache: bool = True
    ) -> bool:
        """
        Check if user has any of the specified permissions.

        Args:
            user: User instance
            permission_codes: List of permission codes
            use_cache: Whether to use cache

        Returns:
            bool: True if user has any permission
        """
        return any(
            PermissionService.check_permission(user, code, use_cache)
            for code in permission_codes
        )

    @staticmethod
    def check_all_permissions(
        user,
        permission_codes: List[str],
        use_cache: bool = True
    ) -> bool:
        """
        Check if user has all specified permissions.

        Args:
            user: User instance
            permission_codes: List of permission codes
            use_cache: Whether to use cache

        Returns:
            bool: True if user has all permissions
        """
        return all(
            PermissionService.check_permission(user, code, use_cache)
            for code in permission_codes
        )

    @staticmethod
    def get_field_permissions(
        user,
        business_object_code: str,
        use_cache: bool = True
    ) -> Dict[str, Dict[str, bool]]:
        """
        Get field-level permissions for a user on a business object.

        Args:
            user: User instance
            business_object_code: Business object code
            use_cache: Whether to use cache

        Returns:
            Dict mapping field_code to {'read': bool, 'write': bool}
        """
        if not user or not user.is_authenticated:
            return {}

        # Get user roles
        roles = PermissionService.get_user_roles(user, use_cache=use_cache)
        role_codes = [r['code'] for r in roles]

        if not role_codes:
            return {}

        # Check cache
        if use_cache:
            cached = PermissionCache.get_field_permissions(
                business_object_code,
                role_codes
            )
            if cached is not None:
                return cached

        # Query field permissions
        field_perms = {}
        try:
            from apps.permissions.models import FieldPermission

            perms = FieldPermission.objects.filter(
                business_object__code=business_object_code,
                role__code__in=role_codes,
                is_active=True
            ).select_related('field_definition')

            for perm in perms:
                field_code = perm.field_definition.code
                if field_code not in field_perms:
                    field_perms[field_code] = {'read': False, 'write': False}

                # Merge permissions (any role granting access wins)
                if perm.can_read:
                    field_perms[field_code]['read'] = True
                if perm.can_write:
                    field_perms[field_code]['write'] = True
        except Exception:
            pass

        # Cache result
        if use_cache:
            PermissionCache.set_field_permissions(
                business_object_code,
                role_codes,
                field_perms
            )

        return field_perms

    @staticmethod
    def check_field_permission(
        user,
        business_object_code: str,
        field_code: str,
        action: str = 'read',
        use_cache: bool = True
    ) -> bool:
        """
        Check if user has permission on a specific field.

        Args:
            user: User instance
            business_object_code: Business object code
            field_code: Field code
            action: 'read' or 'write'
            use_cache: Whether to use cache

        Returns:
            bool: True if user has permission
        """
        if not user or not user.is_authenticated:
            return False

        if user.is_superuser:
            return True

        field_perms = PermissionService.get_field_permissions(
            user, business_object_code, use_cache
        )

        if field_code in field_perms:
            return field_perms[field_code].get(action, False)

        # Default: allow read, deny write
        return action == 'read'

    @staticmethod
    def filter_queryset_by_data_scope(
        user,
        queryset: QuerySet,
        organization_field: str = 'organization',
        department_field: str = 'department',
        user_field: str = 'created_by'
    ) -> QuerySet:
        """
        Filter queryset based on user's role data scope.

        Args:
            user: User instance
            queryset: QuerySet to filter
            organization_field: Field name for organization FK
            department_field: Field name for department FK
            user_field: Field name for user FK

        Returns:
            Filtered QuerySet
        """
        if not user or not user.is_authenticated:
            return queryset.none()

        # Superusers see all
        if user.is_superuser:
            return queryset

        # Get user's highest data scope
        roles = PermissionService.get_user_roles(user)
        if not roles:
            # No roles = only own data
            return queryset.filter(**{f'{user_field}_id': user.id})

        # Priority: all > org > dept > self
        scopes = [r.get('data_scope', PermissionService.DATA_SCOPE_SELF) for r in roles]

        if PermissionService.DATA_SCOPE_ALL in scopes:
            return queryset

        if PermissionService.DATA_SCOPE_ORG in scopes:
            # Filter by organization and descendants
            try:
                from apps.common.services.organization_service import BaseOrganizationService
                org_id = BaseOrganizationService.get_current_organization_id()
                if org_id:
                    org_ids = BaseOrganizationService.get_all_family_ids(org_id)
                    return queryset.filter(**{f'{organization_field}_id__in': org_ids})
            except Exception:
                pass

        if PermissionService.DATA_SCOPE_DEPT in scopes:
            # Filter by department
            try:
                user_dept_id = getattr(user, 'department_id', None)
                if user_dept_id:
                    return queryset.filter(**{f'{department_field}_id': user_dept_id})
            except Exception:
                pass

        # Default: own data only
        return queryset.filter(**{f'{user_field}_id': user.id})

    @staticmethod
    def grant_permission(
        user,
        role,
        organization,
        department=None
    ):
        """
        Grant a role to a user.

        Args:
            user: User instance
            role: Role instance
            organization: Organization instance
            department: Optional department instance

        Returns:
            UserRole instance
        """
        try:
            from apps.permissions.models import UserRole

            user_role, created = UserRole.objects.get_or_create(
                user=user,
                role=role,
                organization=organization,
                defaults={
                    'department': department,
                    'is_active': True
                }
            )

            if not created:
                user_role.is_active = True
                user_role.department = department
                user_role.save()

            # Invalidate cache
            PermissionCache.invalidate_user(str(user.id))
            PermissionCache.invalidate_user_roles(str(user.id))

            return user_role
        except Exception as e:
            raise ValueError(f"Failed to grant permission: {e}")

    @staticmethod
    def revoke_permission(
        user,
        role,
        organization
    ) -> bool:
        """
        Revoke a role from a user.

        Args:
            user: User instance
            role: Role instance
            organization: Organization instance

        Returns:
            bool: True if revoked successfully
        """
        try:
            from apps.permissions.models import UserRole

            result = UserRole.objects.filter(
                user=user,
                role=role,
                organization=organization
            ).update(is_active=False)

            # Invalidate cache
            PermissionCache.invalidate_user(str(user.id))
            PermissionCache.invalidate_user_roles(str(user.id))

            return result > 0
        except Exception:
            return False

    @staticmethod
    def invalidate_cache(user_id: Optional[str] = None) -> None:
        """
        Invalidate permission cache.

        Args:
            user_id: Optional user ID. If None, clears all caches.
        """
        PermissionCache.invalidate_all(user_id)
