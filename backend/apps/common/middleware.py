"""
Custom middleware for GZEAMS multi-organization support.

Handles organization context extraction and validation for multi-tenant data isolation.
Gracefully handles users without organization assignments to prevent 500 errors.
"""
from django.utils.deprecation import MiddlewareMixin
from django.utils.functional import SimpleLazyObject
from rest_framework.exceptions import PermissionDenied
from django.contrib.auth.middleware import get_user
import logging

logger = logging.getLogger(__name__)

# Thread-local storage for organization context
try:
    from threading import local
except ImportError:
    from threading import local as _local

_thread_locals = local()


def get_current_organization():
    """
    Get the current organization ID from thread-local storage.

    Returns:
        str: Organization ID or None
    """
    return getattr(_thread_locals, 'organization_id', None)


def set_current_organization(org_id):
    """
    Set the current organization ID in thread-local storage.

    Args:
        org_id: UUID string of the organization
    """
    _thread_locals.organization_id = org_id


def clear_current_organization():
    """Clear the current organization ID from thread-local storage."""
    if hasattr(_thread_locals, 'organization_id'):
        delattr(_thread_locals, 'organization_id')


class OrganizationMiddleware(MiddlewareMixin):
    """
    Organization context middleware for multi-tenant isolation.

    Extracts organization ID from request and validates user access.

    Organization ID extraction priority:
    1. HTTP Header: X-Organization-ID (highest - for API calls)
    2. JWT Token: organization_id claim
    3. Session: current_organization_id
    4. URL Parameter: org_id (DEBUG mode only)
    5. User primary organization (fallback)
    """

    def process_request(self, request):
        """
        Process incoming request to extract and set organization context.

        Sets on request:
        - organization_id: The validated organization ID
        - current_organization: Lazy-loaded Organization object

        Note: Gracefully handles requests without organization context.
        Some endpoints like login, me, and public endpoints don't require org context.
        """
        org_id = self._extract_organization_id(request)

        if org_id:
            # Validate user belongs to this organization (if authenticated)
            user = get_user(request)
            if user and user.is_authenticated:
                from apps.accounts.models import UserOrganization
                from apps.organizations.models import Organization

                # Check if user has access to this organization
                if not UserOrganization.objects.filter(
                    user_id=user.id,
                    organization_id=org_id,
                    is_active=True
                ).exists():
                    logger.warning(
                        f'User {user.username} attempted to access organization {org_id} '
                        f'without membership. Denying access.'
                    )
                    raise PermissionDenied(
                        f'User does not have access to organization: {org_id}'
                    )

            # Set thread-local context
            set_current_organization(org_id)
            request.organization_id = org_id

            # Add lazy-loaded organization object
            request.current_organization = SimpleLazyObject(
                lambda: self._get_organization(org_id)
            )
        else:
            # No organization context - this is acceptable for:
            # - Unauthenticated users (login page, registration)
            # - Users without organization assignments
            # - Public endpoints
            # - Superusers accessing system-wide data
            request.organization_id = None
            request.current_organization = None

        return None

    def process_response(self, request, response):
        """Clear organization context after request is processed."""
        clear_current_organization()
        return response

    def process_exception(self, request, exception):
        """Clear organization context on exception."""
        clear_current_organization()
        raise exception

    def _extract_organization_id(self, request):
        """
        Extract organization ID from request using priority order.

        Returns:
            str: Organization ID or None
        """
        # 1. HTTP Header (highest priority - for API calls)
        org_id = request.META.get('HTTP_X_ORGANIZATION_ID')
        if org_id:
            return org_id

        # 2. JWT Token (if using DRF JWT authentication)
        if hasattr(request, 'auth') and request.auth:
            # For JWT, payload should contain organization_id
            if hasattr(request.auth, 'payload'):
                org_id = request.auth.payload.get('organization_id')
                if org_id:
                    return str(org_id)

        # 3. Session
        org_id = request.session.get('current_organization_id')
        if org_id:
            return org_id

        # 4. URL Parameter (DEBUG mode only)
        from django.conf import settings
        org_id = request.GET.get('org_id')
        if org_id and settings.DEBUG:
            return org_id

        # 5. User's primary organization (fallback for authenticated users)
        # Note: Wrapped in try-except to gracefully handle users without org
        user = get_user(request)
        if user and user.is_authenticated:
            try:
                primary_org = user.get_primary_organization()
                if primary_org:
                    return str(primary_org.id)
            except Exception as e:
                # Log but don't fail - user may not have organization
                logger.debug(
                    f'Could not get primary organization for user {user.username}: {e}'
                )

        return None

    def _get_organization(self, org_id):
        """
        Get organization object by ID.

        Args:
            org_id: UUID string of the organization

        Returns:
            Organization: The organization object or None
        """
        from apps.organizations.models import Organization
        try:
            return Organization.objects.get(id=org_id, is_deleted=False)
        except Organization.DoesNotExist:
            return None
