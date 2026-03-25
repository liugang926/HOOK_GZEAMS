"""
Custom middleware for GZEAMS multi-organization support.

Handles organization context extraction and validation for multi-tenant data isolation.
Gracefully handles users without organization assignments to prevent 500 errors.
"""
from typing import List, Tuple

from django.utils.deprecation import MiddlewareMixin
from django.utils.functional import SimpleLazyObject
from rest_framework.exceptions import PermissionDenied
from django.contrib.auth.middleware import get_user
import logging

from apps.common.services.i18n_service import (
    TranslationService,
    clear_current_language,
    set_current_language,
)

logger = logging.getLogger(__name__)

# Thread-local storage for organization context
try:
    from threading import local
except ImportError:
    from threading import local as _local

_thread_locals = local()


def normalize_organization_id(org_id):
    """
    Normalize an organization identifier or model instance to a string UUID.

    Args:
        org_id: Organization UUID, model instance, or None

    Returns:
        str: Normalized organization UUID or None
    """
    if not org_id:
        return None
    return str(getattr(org_id, 'pk', org_id))


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
    normalized_org_id = normalize_organization_id(org_id)
    if normalized_org_id:
        _thread_locals.organization_id = normalized_org_id
    elif hasattr(_thread_locals, 'organization_id'):
        delattr(_thread_locals, 'organization_id')


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
    5. User current organization (fallback)
    6. User primary/default organization
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
        org_id = normalize_organization_id(request.META.get('HTTP_X_ORGANIZATION_ID'))
        if org_id:
            return org_id

        # 2. JWT Token (if using DRF JWT authentication)
        if hasattr(request, 'auth') and request.auth:
            # For JWT, payload should contain organization_id
            if hasattr(request.auth, 'payload'):
                org_id = normalize_organization_id(
                    request.auth.payload.get('organization_id')
                )
                if org_id:
                    return org_id

        # 3. Session
        org_id = normalize_organization_id(
            request.session.get('current_organization_id')
        )
        if org_id:
            return org_id

        # 4. URL Parameter (DEBUG mode only)
        from django.conf import settings
        org_id = normalize_organization_id(request.GET.get('org_id'))
        if org_id and settings.DEBUG:
            return org_id

        # 5. User's current organization when it is still accessible.
        # Note: Wrapped in try-except to gracefully handle users without org
        user = get_user(request)
        if user and user.is_authenticated:
            try:
                current_org_id = normalize_organization_id(
                    getattr(user, 'current_organization_id', None)
                )
                if current_org_id and user.user_orgs.filter(
                    organization_id=current_org_id,
                    is_active=True
                ).exists():
                    return current_org_id

                primary_org = user.get_primary_organization()
                if primary_org:
                    return normalize_organization_id(primary_org.id)
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
            return Organization.objects.get(
                id=normalize_organization_id(org_id),
                is_deleted=False
            )
        except Organization.DoesNotExist:
            return None


class LanguageContextMiddleware(MiddlewareMixin):
    """
    Language context middleware for i18n runtime behavior.

    Resolution priority:
    1. Query parameter: `locale` / `lang`
    2. HTTP Header: `Accept-Language`
    3. User preference: `preferred_language` (authenticated user)
    4. System default language
    """

    FALLBACK_LANGUAGE = TranslationService.DEFAULT_LANGUAGE

    def process_request(self, request):
        language = self._resolve_language(request)
        set_current_language(language)
        request.language_code = language
        request.locale = language
        return None

    def process_response(self, request, response):
        clear_current_language()
        return response

    def process_exception(self, request, exception):
        clear_current_language()
        raise exception

    def _resolve_language(self, request) -> str:
        # 1) Query parameter has highest priority for explicit override.
        query_locale = request.GET.get('locale') or request.GET.get('lang')
        normalized_query_locale = self._normalize_locale(query_locale)
        if normalized_query_locale:
            return normalized_query_locale

        # 2) Parse Accept-Language header.
        accept_language = request.META.get('HTTP_ACCEPT_LANGUAGE', '')
        for candidate in self._parse_accept_language(accept_language):
            normalized = self._normalize_locale(candidate)
            if normalized:
                return normalized

        # 3) User profile preference.
        user = get_user(request)
        preferred_language = getattr(user, 'preferred_language', None) if user and user.is_authenticated else None
        normalized_preferred_language = self._normalize_locale(preferred_language)
        if normalized_preferred_language:
            return normalized_preferred_language

        # 4) System default.
        return self.FALLBACK_LANGUAGE

    def _parse_accept_language(self, raw_header: str) -> List[str]:
        if not raw_header:
            return []

        candidates: List[Tuple[str, float]] = []
        for chunk in raw_header.split(','):
            part = chunk.strip()
            if not part:
                continue

            lang = part
            quality = 1.0
            if ';' in part:
                pieces = [p.strip() for p in part.split(';') if p.strip()]
                lang = pieces[0]
                for piece in pieces[1:]:
                    if piece.startswith('q='):
                        try:
                            quality = float(piece.split('=', 1)[1])
                        except (ValueError, TypeError):
                            quality = 0.0
                        break

            if lang:
                candidates.append((lang, quality))

        candidates.sort(key=lambda item: item[1], reverse=True)
        return [lang for lang, _ in candidates]

    def _normalize_locale(self, locale: str) -> str:
        if not locale:
            return ''

        cleaned = locale.strip().replace('_', '-')
        lowered = cleaned.lower()

        if lowered in {'zh', 'zh-cn', 'zh-hans', 'zh-hans-cn'}:
            return 'zh-CN'
        if lowered in {'en', 'en-us', 'en-gb'}:
            return 'en-US'
        if lowered in {'ja', 'ja-jp'}:
            return 'ja-JP'

        for supported in TranslationService.SUPPORTED_LANGUAGES:
            normalized_supported = supported.lower()
            if lowered == normalized_supported:
                return supported
            if lowered.startswith(f'{normalized_supported}-'):
                return supported

        if lowered.startswith('zh-'):
            return 'zh-CN'
        if lowered.startswith('en-'):
            return 'en-US'
        if lowered.startswith('ja-'):
            return 'ja-JP'

        return ''
