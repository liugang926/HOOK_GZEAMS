"""
Pytest Configuration for Accounts Tests

Fixtures and configuration for testing Accounts module.
"""
import os
import sys

# Add project root to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))

# Configure Django settings before any Django imports
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.development')

import django
django.setup()

import pytest
from django.contrib.auth import get_user_model
from apps.organizations.models import Organization, Department
from apps.accounts.models import UserOrganization

User = get_user_model()


@pytest.fixture
def organization(db):
    """Create a test organization."""
    org = Organization.objects.create(
        name='Test Organization',
        code='TEST_ORG',
        is_active=True
    )
    return org


@pytest.fixture
def user(organization):
    """Create a test user."""
    user = User.objects.create_user(
        username='testuser',
        email='test@example.com',
        password='testpass123',
    )
    # Add to organization
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
def admin_user(organization):
    """Create an admin user."""
    user = User.objects.create_user(
        username='adminuser',
        email='admin@example.com',
        password='adminpass123',
        is_staff=True,
        is_superuser=True,
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
def second_organization(db):
    """Create a second test organization for multi-org tests."""
    org = Organization.objects.create(
        name='Second Organization',
        code='SECOND_ORG',
        is_active=True
    )
    return org


@pytest.fixture
def api_client():
    """Create an API test client."""
    from rest_framework.test import APIClient
    return APIClient()


@pytest.fixture
def authenticated_client(api_client, user, organization):
    """Create an authenticated API client with organization context."""
    api_client.force_authenticate(user=user)
    api_client.credentials(HTTP_X_ORGANIZATION_ID=str(organization.id))
    return api_client


@pytest.fixture
def admin_client(api_client, admin_user, organization):
    """Create an authenticated admin API client."""
    api_client.force_authenticate(user=admin_user)
    api_client.credentials(HTTP_X_ORGANIZATION_ID=str(organization.id))
    return api_client


@pytest.fixture
def department(organization):
    """Create a test department."""
    dept = Department.objects.create(
        organization=organization,
        name='Engineering',
        code='ENG',
        is_active=True
    )
    return dept
