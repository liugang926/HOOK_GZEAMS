"""
Tests for Organization middleware and TenantManager.
"""
from django.test import TestCase, RequestFactory
from django.contrib.sessions.backends.db import SessionStore
from apps.common.middleware import (
    get_current_organization,
    set_current_organization,
    clear_current_organization,
    OrganizationMiddleware
)
from apps.organizations.models import Organization
from apps.accounts.models import User, UserOrganization
from apps.assets.models import AssetCategory


class OrganizationMiddlewareTest(TestCase):
    """Test organization middleware functionality."""

    def setUp(self):
        """Set up test data."""
        self.factory = RequestFactory()
        self.org = Organization.objects.create(
            name='Test Organization',
            code='TESTORG'
        )
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com'
        )
        UserOrganization.objects.create(
            user=self.user,
            organization=self.org,
            role='admin'
        )

    def test_thread_local_storage(self):
        """Test thread-local organization storage."""
        # Clear any existing
        clear_current_organization()
        self.assertIsNone(get_current_organization())

        # Set organization
        set_current_organization(str(self.org.id))
        self.assertEqual(get_current_organization(), str(self.org.id))

        # Clear
        clear_current_organization()
        self.assertIsNone(get_current_organization())

    def test_middleware_extracts_from_header(self):
        """Test middleware extracts org ID from header."""
        middleware = OrganizationMiddleware(get_response=lambda r: r)
        request = self.factory.get('/')
        request.META['HTTP_X_ORGANIZATION_ID'] = str(self.org.id)
        request.user = self.user
        # Add session to request (RequestFactory doesn't include it by default)
        request.session = SessionStore()

        middleware.process_request(request)

        self.assertEqual(request.organization_id, str(self.org.id))

    def test_tenant_manager_filters_by_organization(self):
        """Test TenantManager filters by organization context."""
        # Create test data
        cat1 = AssetCategory.objects.create(
            code='CAT1',
            name='Category 1',
            organization_id=self.org.id
        )

        # Create another organization with category
        org2 = Organization.objects.create(name='Org2', code='ORG2')
        cat2 = AssetCategory.objects.create(
            code='CAT2',
            name='Category 2',
            organization_id=org2.id
        )

        # Set organization context
        set_current_organization(str(self.org.id))

        # Query with TenantManager
        categories = AssetCategory.objects.all()
        self.assertEqual(categories.count(), 1)
        self.assertEqual(categories.first().code, 'CAT1')

        # Query with all_objects (no filter)
        all_categories = AssetCategory.all_objects.all()
        self.assertEqual(all_categories.count(), 2)

        clear_current_organization()
