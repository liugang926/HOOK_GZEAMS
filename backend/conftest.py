"""
Root pytest configuration for the project.

Configures Django cache backend for testing without requiring Redis.
Also provides fixtures for test isolation.
"""
import os
import sys
import pytest

# Add project root to Python path
sys.path.insert(0, os.path.dirname(__file__))

# Configure Django settings before any Django imports
# Use test settings when running pytest
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.test')

import django
from django.conf import settings

# Override cache settings for testing to use in-memory cache
# This avoids requiring Redis to be running during tests
if not settings.configured:
    django.setup()
else:
    # Cache was already configured, we need to override it
    settings.CACHES = {
        'default': {
            'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
            'LOCATION': 'unique-snowflake',
        }
    }


# ============================================================================
# Test Isolation Fixtures
# ============================================================================

@pytest.fixture(autouse=True)
def reset_organization_context():
    """
    Automatically reset the thread-local organization context before and after each test.
    This prevents test pollution where one test's organization context
    leaks into another test.
    """
    # Clean up BEFORE the test (in case previous test left state)
    try:
        from apps.common.middleware import clear_current_organization
        clear_current_organization()
    except ImportError:
        pass  # Module not available, skip cleanup

    yield  # Run the test

    # Clean up AFTER the test
    try:
        from apps.common.middleware import clear_current_organization
        clear_current_organization()
    except ImportError:
        pass  # Module not available, skip cleanup


@pytest.fixture(autouse=True, scope="function")
def clear_django_cache():
    """
    Clear Django cache between tests to prevent state leakage.
    """
    yield
    from django.core.cache import cache
    cache.clear()


def pytest_configure(config):
    """
    Pytest configuration hook.
    Ensures proper isolation between test runs.
    """
    # Set up Django before any tests run
    import django
    from django.conf import settings
    if not settings.configured:
        django.setup()


def pytest_runtest_teardown(item, nextitem):
    """
    Hook to clean up after each test.
    Ensures database transactions are properly reset.
    """
    # Clear any pending database transactions
    from django.db import connections
    for conn in connections.all():
        conn.close()


@pytest.fixture
def organization(db):
    """Create a test organization with unique code."""
    import uuid
    from apps.organizations.models import Organization
    unique_suffix = uuid.uuid4().hex[:8]
    return Organization.objects.create(
        name=f"Test Organization {unique_suffix}",
        code=f"TESTORG_{unique_suffix}"
    )


@pytest.fixture
def user(db, organization):
    """Create a test user with unique username."""
    import uuid
    from apps.accounts.models import User, UserOrganization
    unique_suffix = uuid.uuid4().hex[:8]
    test_user = User.objects.create_user(
        username=f"testuser_{unique_suffix}",
        email=f"test{unique_suffix}@example.com",
        password="testpass123",
        organization=organization
    )
    UserOrganization.objects.create(
        user=test_user,
        organization=organization,
        role='member',
        is_primary=True
    )
    return test_user


@pytest.fixture
def admin_user(db, organization):
    """Create a test admin user with unique username."""
    import uuid
    from apps.accounts.models import User, UserOrganization
    unique_suffix = uuid.uuid4().hex[:8]
    admin = User.objects.create_user(
        username=f"admin_{unique_suffix}",
        email=f"admin{unique_suffix}@example.com",
        password="adminpass123",
        organization=organization,
        is_staff=True
    )
    UserOrganization.objects.create(
        user=admin,
        organization=organization,
        role='admin',
        is_primary=True
    )
    return admin


@pytest.fixture
def second_organization(db):
    """Create a second test organization for multi-org tests."""
    import uuid
    from apps.organizations.models import Organization
    unique_suffix = uuid.uuid4().hex[:8]
    return Organization.objects.create(
        name=f"Second Organization {unique_suffix}",
        code=f"SECONDORG_{unique_suffix}"
    )
