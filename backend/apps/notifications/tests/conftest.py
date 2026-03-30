"""
Pytest configuration and fixtures for notification tests.
"""
import os
import sys
import pytest

# Configure Django settings before any Django imports
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.development')

import django
django.setup()

from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from apps.accounts.models import UserOrganization
from apps.common.middleware import clear_current_organization, set_current_organization

User = get_user_model()


@pytest.fixture
def user(db, organization):
    """Create a test user with organization membership."""
    test_user = User.objects.create_user(
        username='testuser',
        email='test@example.com',
        password='testpass123',
        organization=organization,
        current_organization=organization,
    )
    UserOrganization.objects.create(
        user=test_user,
        organization=organization,
        role='member',
        is_primary=True,
    )
    return test_user


@pytest.fixture
def other_user(db, organization):
    """Create another user in the same organization."""
    test_user = User.objects.create_user(
        username='otheruser',
        email='other@example.com',
        password='testpass123',
        organization=organization,
        current_organization=organization,
    )
    UserOrganization.objects.create(
        user=test_user,
        organization=organization,
        role='member',
        is_primary=True,
    )
    return test_user


@pytest.fixture
def admin_user(db, organization):
    """Create an admin user with organization membership."""
    admin = User.objects.create_user(
        username='admin',
        email='admin@example.com',
        password='admin123',
        organization=organization,
        current_organization=organization,
        is_staff=True,
        is_superuser=True,
    )
    UserOrganization.objects.create(
        user=admin,
        organization=organization,
        role='admin',
        is_primary=True,
    )
    return admin


@pytest.fixture
def api_client():
    """Return an API client."""
    return APIClient()


@pytest.fixture
def authenticated_client(api_client, user):
    """Return an authenticated API client."""
    api_client.force_authenticate(user=user)
    return api_client


@pytest.fixture
def auth_client(authenticated_client, organization):
    """Return an authenticated client with organization context."""
    authenticated_client.credentials(HTTP_X_ORGANIZATION_ID=str(organization.id))
    session = authenticated_client.session
    session['current_organization_id'] = str(organization.id)
    session.save()
    set_current_organization(str(organization.id))
    yield authenticated_client
    clear_current_organization()


@pytest.fixture
def admin_client(api_client, admin_user, organization):
    """Return an admin authenticated API client."""
    api_client.force_authenticate(user=admin_user)
    api_client.credentials(HTTP_X_ORGANIZATION_ID=str(organization.id))
    session = api_client.session
    session['current_organization_id'] = str(organization.id)
    session.save()
    set_current_organization(str(organization.id))
    yield api_client
    clear_current_organization()


@pytest.fixture
def notification_template(user, organization):
    """Create a test notification template."""
    from apps.notifications.models import NotificationTemplate
    return NotificationTemplate.objects.create(
        organization=organization,
        template_code='test_template',
        template_name='Test Template',
        template_type='test',
        channel='inbox',
        subject_template='Test Subject: {{ name }}',
        content_template='Test Content: {{ message }}',
        variables={
            'name': {'default': 'World'},
            'message': {'default': 'Hello'},
        },
        created_by=user,
    )


@pytest.fixture
def notification(user, organization):
    """Create a test notification."""
    from apps.notifications.models import Notification
    return Notification.objects.create(
        organization=organization,
        recipient=user,
        notification_type='test',
        channel='inbox',
        title='Test Notification',
        content='Test Content',
        created_by=user,
    )


@pytest.fixture
def notification_config(user, organization):
    """Create a test notification config."""
    from apps.notifications.models import NotificationConfig
    return NotificationConfig.objects.create(
        organization=organization,
        user=user,
        enable_inbox=True,
        enable_email=True,
    )
