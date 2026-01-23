"""
Pytest configuration for organizations app tests.

Provides fixtures for testing organizations module.
"""
from rest_framework.test import APIRequestFactory
from apps.common.middleware import set_current_organization


@pytest.fixture
def auth_client(db, client, user):
    """
    Create an authenticated test client.

    This fixture creates a Django test client that is authenticated
    as the test user and has organization context set.
    """
    from django.contrib.auth import get_user_model

    # Force authenticate the client
    client.force_authenticate(user=user)

    # Set organization in thread-local storage
    # Get the user's primary organization
    from apps.accounts.models import UserOrganization
    user_org = UserOrganization.objects.filter(
        user=user,
        is_primary=True
    ).first()

    if user_org:
        set_current_organization(user_org.organization)
        # Store organization on client for middleware to access
        client.organization = user_org.organization
    else:
        # Fallback: use user's organization field
        set_current_organization(user.organization)
        client.organization = user.organization

    return client


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
