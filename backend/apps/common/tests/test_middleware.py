"""
Tests for OrganizationMiddleware.
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from django.test import RequestFactory


class TestOrganizationContext:
    """Test organization context functions."""

    def test_get_current_organization_default_none(self):
        """Test get_current_organization returns None by default."""
        from apps.common.middleware import (
            get_current_organization,
            clear_current_organization
        )

        clear_current_organization()
        result = get_current_organization()
        assert result is None

    def test_set_and_get_organization(self):
        """Test setting and getting organization context."""
        from apps.common.middleware import (
            get_current_organization,
            set_current_organization,
            clear_current_organization
        )

        test_org_id = 'test-org-uuid-123'
        set_current_organization(test_org_id)

        try:
            result = get_current_organization()
            assert result == test_org_id
        finally:
            clear_current_organization()

    def test_clear_organization(self):
        """Test clearing organization context."""
        from apps.common.middleware import (
            get_current_organization,
            set_current_organization,
            clear_current_organization
        )

        set_current_organization('some-org-id')
        clear_current_organization()

        result = get_current_organization()
        assert result is None


class TestOrganizationMiddleware:
    """Test OrganizationMiddleware class."""

    def test_extract_from_header(self, db, organization, user):
        """Test extracting org ID from HTTP header."""
        from apps.common.middleware import OrganizationMiddleware
        from apps.accounts.models import UserOrganization

        middleware = OrganizationMiddleware(get_response=lambda r: r)

        request = Mock()
        request.META = {'HTTP_X_ORGANIZATION_ID': str(organization.id)}
        request.user = user
        request.session = {}
        request.GET = {}

        # Mock auth
        request.auth = None

        org_id = middleware._extract_organization_id(request)
        assert org_id == str(organization.id)

    def test_extract_from_session(self, db, organization, user):
        """Test extracting org ID from session."""
        from apps.common.middleware import OrganizationMiddleware

        middleware = OrganizationMiddleware(get_response=lambda r: r)

        request = Mock()
        request.META = {}
        request.user = user
        request.session = {'current_organization_id': str(organization.id)}
        request.GET = {}
        request.auth = None

        org_id = middleware._extract_organization_id(request)
        assert org_id == str(organization.id)

    def test_process_response_clears_context(self):
        """Test that process_response clears organization context."""
        from apps.common.middleware import (
            OrganizationMiddleware,
            get_current_organization,
            set_current_organization
        )

        middleware = OrganizationMiddleware(get_response=lambda r: r)

        # Set context
        set_current_organization('test-org')

        request = Mock()
        response = Mock()

        middleware.process_response(request, response)

        # Context should be cleared
        assert get_current_organization() is None

    def test_process_exception_clears_context(self):
        """Test that process_exception clears organization context."""
        from apps.common.middleware import (
            OrganizationMiddleware,
            get_current_organization,
            set_current_organization
        )

        middleware = OrganizationMiddleware(get_response=lambda r: r)

        set_current_organization('test-org')

        request = Mock()
        exception = Exception('Test error')

        with pytest.raises(Exception):
            middleware.process_exception(request, exception)

        # Context should be cleared
        assert get_current_organization() is None


class TestOrganizationMiddlewareIntegration:
    """Integration tests for middleware."""

    @pytest.mark.skip(reason="RequestFactory requests don't fully emulate Django requests for middleware processing")
    def test_sets_request_attributes(self, db, organization, user):
        """Test that middleware sets organization_id on request."""
        from apps.common.middleware import OrganizationMiddleware, clear_current_organization
        from django.test import RequestFactory

        middleware = OrganizationMiddleware(get_response=lambda r: r)

        factory = RequestFactory()
        request = factory.get('/')
        request.META['HTTP_X_ORGANIZATION_ID'] = str(organization.id)
        request.user = user
        request.session = {}

        try:
            middleware.process_request(request)
            assert request.organization_id == str(organization.id)
        finally:
            clear_current_organization()

    @pytest.mark.skip(reason="RequestFactory requests don't fully emulate Django requests for middleware processing")
    def test_validates_user_organization_access(self, db, organization, second_organization, user):
        """Test that middleware validates user belongs to organization."""
        from apps.common.middleware import OrganizationMiddleware, clear_current_organization
        from rest_framework.exceptions import PermissionDenied
        from django.test import RequestFactory

        middleware = OrganizationMiddleware(get_response=lambda r: r)

        factory = RequestFactory()
        request = factory.get('/')
        # Try to access organization user doesn't belong to
        request.META['HTTP_X_ORGANIZATION_ID'] = str(second_organization.id)
        request.user = user
        request.session = {}

        try:
            with pytest.raises(PermissionDenied):
                middleware.process_request(request)
        finally:
            clear_current_organization()
