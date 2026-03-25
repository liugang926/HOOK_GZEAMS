"""
Pytest fixtures for common app tests.
"""
import pytest
from django.contrib.auth import get_user_model
from apps.organizations.models import Organization
from apps.accounts.models import UserOrganization

User = get_user_model()


@pytest.fixture
def organization(db):
    """Create a test organization."""
    org = Organization.objects.create(
        name='Test Organization',
        code='TEST_ORG',
        org_type='company'
    )
    return org


@pytest.fixture
def second_organization(db):
    """Create a second test organization."""
    org = Organization.objects.create(
        name='Second Organization',
        code='SECOND_ORG',
        org_type='company'
    )
    return org


@pytest.fixture
def user(db, organization):
    """Create a test user with organization membership."""
    user = User.objects.create_user(
        username='testuser',
        email='testuser@example.com',
        password='testpass123'
    )
    UserOrganization.objects.create(
        user=user,
        organization=organization,
        role='member',
        is_primary=True
    )
    user.current_organization = organization
    user.save()
    return user


@pytest.fixture
def admin_user(db, organization):
    """Create an admin user with organization membership."""
    user = User.objects.create_user(
        username='adminuser',
        email='admin@example.com',
        password='adminpass123',
        is_staff=True
    )
    UserOrganization.objects.create(
        user=user,
        organization=organization,
        role='admin',
        is_primary=True
    )
    user.current_organization = organization
    user.save()
    return user


@pytest.fixture
def superuser(db):
    """Create a superuser."""
    return User.objects.create_superuser(
        username='superuser',
        email='super@example.com',
        password='superpass123'
    )


@pytest.fixture
def api_client():
    """Create a DRF API client."""
    from rest_framework.test import APIClient
    return APIClient()


@pytest.fixture
def authenticated_client(api_client, user):
    """Create an authenticated API client."""
    api_client.force_authenticate(user=user)
    return api_client


@pytest.fixture
def auth_client(authenticated_client, organization):
    """Create an authenticated client with organization context for legacy tests."""
    from apps.common.middleware import clear_current_organization, set_current_organization

    authenticated_client.credentials(
        HTTP_X_ORGANIZATION_ID=str(organization.id)
    )

    session = authenticated_client.session
    session['current_organization_id'] = str(organization.id)
    session.save()

    set_current_organization(str(organization.id))
    yield authenticated_client
    clear_current_organization()


@pytest.fixture
def admin_client(api_client, admin_user):
    """Create an admin-authenticated API client."""
    api_client.force_authenticate(user=admin_user)
    return api_client


@pytest.fixture
def mock_request(user, organization):
    """Create a mock request object with organization context."""
    from unittest.mock import Mock
    request = Mock()
    request.user = user
    request.organization_id = str(organization.id)
    request.current_organization = organization
    request.method = 'GET'
    request.META = {}
    request.session = {}
    request.GET = {}
    return request


@pytest.fixture
def asset_category(db, organization, user):
    """Create a minimal asset category for common pagination tests."""
    from apps.assets.models import AssetCategory

    return AssetCategory.objects.create(
        organization=organization,
        code='COMMON_ASSET_CATEGORY',
        name='Common Asset Category',
        created_by=user,
    )


@pytest.fixture
def asset(db, organization, user, asset_category):
    """Create a minimal asset for pagination and base endpoint tests."""
    from decimal import Decimal
    from apps.assets.models import Asset

    return Asset.objects.create(
        organization=organization,
        asset_name='Common Test Asset',
        asset_category=asset_category,
        purchase_price=Decimal('1000.00'),
        purchase_date='2024-01-01',
        created_by=user,
    )
