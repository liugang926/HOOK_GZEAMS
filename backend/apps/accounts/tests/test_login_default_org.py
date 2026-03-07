import pytest


@pytest.mark.django_db
def test_login_assigns_default_organization_for_superuser(api_client, organization):
    from django.contrib.auth import get_user_model
    from apps.accounts.models import UserOrganization

    User = get_user_model()
    user = User.objects.create_superuser(
        username='bootstrapadmin',
        email='bootstrapadmin@example.com',
        password='adminpass123'
    )

    response = api_client.post(
        '/api/auth/login/',
        {'username': 'bootstrapadmin', 'password': 'adminpass123'},
        format='json'
    )

    user.refresh_from_db()
    membership = UserOrganization.objects.get(user=user, organization=organization)

    assert response.status_code == 200
    assert response.data['success'] is True
    assert response.data['data']['organization']['id'] == str(organization.id)
    assert membership.role == 'admin'
    assert membership.is_primary is True
    assert user.current_organization == organization
