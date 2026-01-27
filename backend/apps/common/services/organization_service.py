"""
Organization service for multi-tenant support.

Provides:
- Organization context management
- Organization tree operations
- Cross-organization permission checks
- User-organization relationship management
"""
from typing import List, Optional, Set
from django.db.models import QuerySet


class BaseOrganizationService:
    """
    Service class for organization-related operations.

    Provides static methods for:
    - Getting/setting organization context
    - Querying organization hierarchies
    - Filtering querysets by organization
    - Checking organization access permissions
    """

    @staticmethod
    def get_current_organization_id() -> Optional[str]:
        """
        Get the current organization ID from thread-local storage.

        Returns:
            str or None: Current organization ID
        """
        from apps.common.middleware import get_current_organization
        return get_current_organization()

    @staticmethod
    def set_organization_context(org_id: str) -> None:
        """
        Set the organization context in thread-local storage.

        Args:
            org_id: Organization ID to set
        """
        from apps.common.middleware import set_current_organization
        set_current_organization(org_id)

    @staticmethod
    def clear_organization_context() -> None:
        """Clear the organization context from thread-local storage."""
        from apps.common.middleware import clear_current_organization
        clear_current_organization()

    @staticmethod
    def get_organization_info(org_id: str) -> Optional[dict]:
        """
        Get basic organization information.

        Args:
            org_id: Organization ID

        Returns:
            dict or None: Organization info with id, name, code, etc.
        """
        try:
            from apps.organizations.models import Organization
            org = Organization.objects.filter(id=org_id, is_deleted=False).first()
            if org:
                return {
                    'id': str(org.id),
                    'name': org.name,
                    'code': org.code,
                    'parent_id': str(org.parent_id) if org.parent_id else None,
                }
            return None
        except Exception:
            return None

    @staticmethod
    def get_organization_tree(org_id: str) -> Optional[dict]:
        """
        Get organization with full tree information.

        Args:
            org_id: Organization ID

        Returns:
            dict: Organization info with ancestors and descendants
        """
        info = BaseOrganizationService.get_organization_info(org_id)
        if not info:
            return None

        info['ancestor_ids'] = list(BaseOrganizationService.get_ancestor_ids(org_id))
        info['descendant_ids'] = list(BaseOrganizationService.get_descendant_ids(org_id))
        return info

    @staticmethod
    def get_ancestor_ids(org_id: str) -> Set[str]:
        """
        Get all ancestor organization IDs.

        Args:
            org_id: Organization ID

        Returns:
            Set[str]: Set of ancestor organization IDs
        """
        ancestors = set()
        try:
            from apps.organizations.models import Organization
            org = Organization.objects.filter(id=org_id).first()
            while org and org.parent_id:
                ancestors.add(str(org.parent_id))
                org = Organization.objects.filter(id=org.parent_id).first()
        except Exception:
            pass
        return ancestors

    @staticmethod
    def get_descendant_ids(org_id: str, include_self: bool = False) -> Set[str]:
        """
        Get all descendant organization IDs.

        Args:
            org_id: Organization ID
            include_self: Whether to include the organization itself

        Returns:
            Set[str]: Set of descendant organization IDs
        """
        descendants = set()
        if include_self:
            descendants.add(org_id)

        try:
            from apps.organizations.models import Organization

            def collect_descendants(parent_id):
                children = Organization.objects.filter(
                    parent_id=parent_id,
                    is_deleted=False
                ).values_list('id', flat=True)
                for child_id in children:
                    descendants.add(str(child_id))
                    collect_descendants(child_id)

            collect_descendants(org_id)
        except Exception:
            pass
        return descendants

    @staticmethod
    def get_all_family_ids(org_id: str, include_self: bool = True) -> Set[str]:
        """
        Get all organization IDs in the family (self + descendants).

        Args:
            org_id: Organization ID
            include_self: Whether to include the organization itself

        Returns:
            Set[str]: Set of all family organization IDs
        """
        return BaseOrganizationService.get_descendant_ids(org_id, include_self=include_self)

    @staticmethod
    def filter_by_organization(
        queryset: QuerySet,
        org_id: Optional[str] = None,
        include_descendants: bool = False
    ) -> QuerySet:
        """
        Filter queryset by organization.

        Args:
            queryset: Django QuerySet to filter
            org_id: Organization ID (defaults to current context)
            include_descendants: Whether to include child organizations

        Returns:
            QuerySet: Filtered queryset
        """
        if org_id is None:
            org_id = BaseOrganizationService.get_current_organization_id()

        if not org_id:
            return queryset

        if include_descendants:
            org_ids = BaseOrganizationService.get_all_family_ids(org_id, include_self=True)
            return queryset.filter(organization_id__in=org_ids)
        else:
            return queryset.filter(organization_id=org_id)

    @staticmethod
    def check_organization_access(
        user,
        target_org_id: str,
        allow_cross_org: bool = False
    ) -> bool:
        """
        Check if user has access to target organization.

        Args:
            user: User instance
            target_org_id: Target organization ID
            allow_cross_org: Whether to allow cross-organization access

        Returns:
            bool: True if access is allowed
        """
        if not user or not user.is_authenticated:
            return False

        # Superusers have access to all organizations
        if user.is_superuser:
            return True

        try:
            from apps.accounts.models import UserOrganization
            return UserOrganization.objects.filter(
                user_id=user.id,
                organization_id=target_org_id,
                is_active=True
            ).exists()
        except Exception:
            return False

    @staticmethod
    def check_data_organization(instance, user, allow_cross_org: bool = False) -> bool:
        """
        Check if user can access a data object based on organization.

        Args:
            instance: Model instance with organization_id
            user: User instance
            allow_cross_org: Whether to allow cross-organization access

        Returns:
            bool: True if access is allowed
        """
        if not hasattr(instance, 'organization_id'):
            return True  # Object has no organization constraint

        return BaseOrganizationService.check_organization_access(
            user,
            str(instance.organization_id),
            allow_cross_org
        )

    @staticmethod
    def validate_organization_user(user, org_id: str) -> bool:
        """
        Validate if user belongs to organization.

        Args:
            user: User instance
            org_id: Organization ID

        Returns:
            bool: True if user belongs to organization
        """
        return BaseOrganizationService.check_organization_access(user, org_id)

    @staticmethod
    def get_user_accessible_organizations(user) -> List[dict]:
        """
        Get list of organizations user can access.

        Args:
            user: User instance

        Returns:
            List[dict]: List of organization info dicts
        """
        if not user or not user.is_authenticated:
            return []

        try:
            from apps.accounts.models import UserOrganization
            from apps.organizations.models import Organization

            user_org_ids = UserOrganization.objects.filter(
                user_id=user.id,
                is_active=True
            ).values_list('organization_id', flat=True)

            orgs = Organization.objects.filter(
                id__in=user_org_ids,
                is_deleted=False
            ).values('id', 'name', 'code')

            return [
                {'id': str(org['id']), 'name': org['name'], 'code': org['code']}
                for org in orgs
            ]
        except Exception:
            return []

    @staticmethod
    def get_department_tree(org_id: str) -> List[dict]:
        """
        Get department tree for an organization.

        Args:
            org_id: Organization ID

        Returns:
            List[dict]: Department tree structure
        """
        try:
            from apps.organizations.models import Department

            def build_tree(parent_id=None):
                departments = Department.objects.filter(
                    organization_id=org_id,
                    parent_id=parent_id,
                    is_deleted=False
                ).order_by('sort_order', 'name')

                return [
                    {
                        'id': str(dept.id),
                        'name': dept.name,
                        'code': getattr(dept, 'code', ''),
                        'children': build_tree(dept.id)
                    }
                    for dept in departments
                ]

            return build_tree()
        except Exception:
            return []


# Context manager for organization context
class OrganizationContext:
    """
    Context manager for temporary organization context.

    Usage:
        with OrganizationContext(org_id):
            # Operations within this organization context
            assets = Asset.objects.all()
    """

    def __init__(self, org_id: str):
        self.org_id = org_id
        self.previous_org_id = None

    def __enter__(self):
        self.previous_org_id = BaseOrganizationService.get_current_organization_id()
        BaseOrganizationService.set_organization_context(self.org_id)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.previous_org_id:
            BaseOrganizationService.set_organization_context(self.previous_org_id)
        else:
            BaseOrganizationService.clear_organization_context()
        return False


def organization_context(org_id: str):
    """
    Function version of OrganizationContext for convenience.

    Usage:
        with organization_context(org_id):
            assets = Asset.objects.all()
    """
    return OrganizationContext(org_id)


# Decorators for organization context
def with_organization(org_id: str):
    """
    Decorator to run function within organization context.

    Usage:
        @with_organization('org-uuid')
        def process_org_data():
            assets = Asset.objects.all()
    """
    def decorator(func):
        from functools import wraps

        @wraps(func)
        def wrapper(*args, **kwargs):
            with OrganizationContext(org_id):
                return func(*args, **kwargs)
        return wrapper
    return decorator


def with_organization_from_arg(arg_name: str = 'org_id'):
    """
    Decorator to get organization ID from function argument.

    Usage:
        @with_organization_from_arg('organization_id')
        def process_data(organization_id):
            assets = Asset.objects.all()
    """
    def decorator(func):
        from functools import wraps

        @wraps(func)
        def wrapper(*args, **kwargs):
            org_id = kwargs.get(arg_name)
            if org_id:
                with OrganizationContext(org_id):
                    return func(*args, **kwargs)
            return func(*args, **kwargs)
        return wrapper
    return decorator


def require_organization(func):
    """
    Decorator to require organization context.

    Usage:
        @require_organization
        def org_required_function():
            # Will raise error if no organization context
            pass
    """
    from functools import wraps

    @wraps(func)
    def wrapper(*args, **kwargs):
        org_id = BaseOrganizationService.get_current_organization_id()
        if not org_id:
            raise ValueError("Organization context is required")
        return func(*args, **kwargs)
    return wrapper
