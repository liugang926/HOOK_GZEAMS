"""
Base permission classes for GZEAMS.

Provides:
- BasePermission: Core permission with organization and object-level checks
- IsAdminOrReadOnly: Admin or read-only access
- IsOwnerOrReadOnly: Owner or read-only access
- IsOrganizationMember: Organization membership check
- AllowOptionsPermission: Allow CORS preflight requests
"""
from rest_framework import permissions
from functools import wraps


class BasePermission(permissions.BasePermission):
    """
    Base permission class with organization isolation and object-level checks.

    Automatically checks:
    - User authentication
    - Organization access
    - Role-based permissions
    - Object ownership
    """

    # HTTP method to permission action mapping
    ACTION_MAP = {
        'GET': 'view',
        'HEAD': 'view',
        'OPTIONS': 'view',
        'POST': 'create',
        'PUT': 'update',
        'PATCH': 'partial_update',
        'DELETE': 'delete',
    }

    def has_permission(self, request, view):
        """
        Check global permission.

        Args:
            request: HTTP request
            view: View being accessed

        Returns:
            bool: True if permission granted
        """
        # Allow unauthenticated OPTIONS requests (CORS preflight)
        if request.method == 'OPTIONS':
            return True

        # Require authentication
        if not request.user or not request.user.is_authenticated:
            return False

        # Superusers have full access
        if request.user.is_superuser:
            return True

        # Check organization access
        org_id = getattr(request, 'organization_id', None)
        if org_id and not self._check_organization_access(request.user, org_id):
            return False

        return True

    def has_object_permission(self, request, view, obj):
        """
        Check object-level permission.

        Args:
            request: HTTP request
            view: View being accessed
            obj: Object being accessed

        Returns:
            bool: True if permission granted
        """
        # Superusers have full access
        if request.user.is_superuser:
            return True

        # Check organization isolation
        if hasattr(obj, 'organization_id'):
            request_org_id = getattr(request, 'organization_id', None)
            if request_org_id and str(obj.organization_id) != str(request_org_id):
                return False

        # Check soft delete - deny access to deleted objects except for admins
        if hasattr(obj, 'is_deleted') and obj.is_deleted:
            if not request.user.is_staff:
                return False

        # Allow read operations for all authenticated users
        if request.method in permissions.SAFE_METHODS:
            return True

        # Check ownership for write operations
        return self._check_ownership(request.user, obj)

    def _check_organization_access(self, user, org_id):
        """Check if user has access to organization."""
        try:
            from apps.accounts.models import UserOrganization
            return UserOrganization.objects.filter(
                user_id=user.id,
                organization_id=org_id,
                is_active=True
            ).exists()
        except Exception:
            return False

    def _check_ownership(self, user, obj):
        """Check if user owns the object."""
        # Creator has full access
        if hasattr(obj, 'created_by_id') and obj.created_by_id == user.id:
            return True

        # Staff users have access
        if user.is_staff:
            return True

        return False


class IsAdminOrReadOnly(permissions.BasePermission):
    """
    Permission that allows admin users full access, others read-only.
    """

    def has_permission(self, request, view):
        # Allow read-only access
        if request.method in permissions.SAFE_METHODS:
            return True

        # Write access requires admin
        return request.user and request.user.is_staff


class IsOwnerOrReadOnly(permissions.BasePermission):
    """
    Permission that allows owners full access, others read-only.
    """

    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated

    def has_object_permission(self, request, view, obj):
        # Allow read-only access
        if request.method in permissions.SAFE_METHODS:
            return True

        # Write access requires ownership
        if hasattr(obj, 'created_by_id'):
            return obj.created_by_id == request.user.id
        if hasattr(obj, 'user_id'):
            return obj.user_id == request.user.id

        return False


class IsOrganizationMember(permissions.BasePermission):
    """
    Permission that requires user to be a member of the current organization.
    """

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False

        org_id = getattr(request, 'organization_id', None)
        if not org_id:
            return True  # No organization context, allow

        try:
            from apps.accounts.models import UserOrganization
            return UserOrganization.objects.filter(
                user_id=request.user.id,
                organization_id=org_id,
                is_active=True
            ).exists()
        except Exception:
            return False


class AllowOptionsPermission(permissions.BasePermission):
    """
    Permission that always allows OPTIONS requests (CORS preflight).
    """

    def has_permission(self, request, view):
        return request.method == 'OPTIONS'


# Permission decorators
def require_permissions(*required_perms):
    """
    Decorator to require specific permissions.

    Usage:
        @require_permissions('assets.view_asset', 'assets.change_asset')
        def my_view(request):
            ...
    """
    def decorator(func):
        @wraps(func)
        def wrapper(request, *args, **kwargs):
            if not request.user.has_perms(required_perms):
                from rest_framework.exceptions import PermissionDenied
                raise PermissionDenied('Insufficient permissions')
            return func(request, *args, **kwargs)
        return wrapper
    return decorator


def require_roles(*required_roles):
    """
    Decorator to require specific roles.

    Usage:
        @require_roles('admin', 'manager')
        def my_view(request):
            ...
    """
    def decorator(func):
        @wraps(func)
        def wrapper(request, *args, **kwargs):
            user_roles = getattr(request.user, 'roles', [])
            if isinstance(user_roles, str):
                user_roles = [user_roles]
            elif hasattr(user_roles, 'values_list'):
                user_roles = list(user_roles.values_list('name', flat=True))

            if not any(role in user_roles for role in required_roles):
                from rest_framework.exceptions import PermissionDenied
                raise PermissionDenied('Insufficient role')
            return func(request, *args, **kwargs)
        return wrapper
    return decorator
