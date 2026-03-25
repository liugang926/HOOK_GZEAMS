"""
Pytest configuration for organizations app tests.

Provides fixtures for testing organizations module.
"""
import pytest
from rest_framework.test import APIClient
from apps.common.middleware import set_current_organization


@pytest.fixture
def auth_client(db, user):
    """
    Create an authenticated test client.

    This fixture creates a Django test client that is authenticated
    as the test user and has organization context set.
    """
    client = APIClient()
    client.force_login(user)
    client.force_authenticate(user=user)

    # Set organization in thread-local storage
    # Get the user's primary organization
    from apps.accounts.models import UserOrganization
    user_org = UserOrganization.objects.filter(
        user=user,
        is_primary=True
    ).first()

    if user_org:
        organization_id = str(user_org.organization_id)
        set_current_organization(organization_id)
        client.defaults['HTTP_X_ORGANIZATION_ID'] = organization_id
        client.organization = user_org.organization
    else:
        organization_id = str(user.current_organization_id or user.organization_id)
        set_current_organization(organization_id)
        client.defaults['HTTP_X_ORGANIZATION_ID'] = organization_id
        client.organization_id = organization_id

    session = client.session
    session['current_organization_id'] = organization_id
    session.save()

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
