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

User = get_user_model()


@pytest.fixture
def user(db):
    """Create a test user."""
    return User.objects.create_user(
        username='testuser',
        email='test@example.com',
        password='testpass123',
    )


@pytest.fixture
def admin_user(db):
    """Create an admin user."""
    return User.objects.create_superuser(
        username='admin',
        email='admin@example.com',
        password='admin123',
    )


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
def admin_client(api_client, admin_user):
    """Return an admin authenticated API client."""
    api_client.force_authenticate(user=admin_user)
    return api_client


@pytest.fixture
def notification_template(user):
    """Create a test notification template."""
    from apps.notifications.models import NotificationTemplate
    return NotificationTemplate.objects.create(
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
def notification(user):
    """Create a test notification."""
    from apps.notifications.models import Notification
    return Notification.objects.create(
        recipient=user,
        notification_type='test',
        channel='inbox',
        title='Test Notification',
        content='Test Content',
        created_by=user,
    )


@pytest.fixture
def notification_config(user):
    """Create a test notification config."""
    from apps.notifications.models import NotificationConfig
    return NotificationConfig.objects.create(
        user=user,
        enable_inbox=True,
        enable_email=True,
    )
