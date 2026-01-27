"""
Pytest Configuration for SSO Tests

Fixtures and configuration for testing SSO module.
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
from apps.organizations.models import Organization
from apps.sso.models import WeWorkConfig, UserMapping, OAuthState

User = get_user_model()


@pytest.fixture
def db():
    """Ensure database is available."""
    from django.db import connection
    connection.ensure_connection()


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
    user = User.objects.create(
        username='testuser',
        email='test@example.com',
        organization=organization,
        is_active=True
    )
    return user


@pytest.fixture
def wework_config(organization):
    """Create a test WeWork configuration."""
    config = WeWorkConfig.objects.create(
        organization=organization,
        corp_id='ww123456789',
        corp_name='Test Corp',
        agent_id=1000001,
        agent_secret='test_secret',
        is_enabled=True,
        auto_create_user=True
    )
    return config


@pytest.fixture
def user_mapping(user, organization):
    """Create a test user mapping."""
    mapping = UserMapping.objects.create(
        organization=organization,
        system_user=user,
        platform='wework',
        platform_userid='USER123',
        platform_name='Test User'
    )
    return mapping


@pytest.fixture
def oauth_state(organization):
    """Create a test OAuth state."""
    from django.utils import timezone
    from datetime import timedelta

    state = OAuthState.objects.create(
        organization=organization,
        state='test_state_token',
        platform='wework',
        session_data={'test': 'data'},
        expires_at=timezone.now() + timedelta(minutes=10)
    )
    return state
