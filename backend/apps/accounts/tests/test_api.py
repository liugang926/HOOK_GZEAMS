"""
Tests for Accounts API endpoints.
"""
import pytest
from rest_framework import status
from django.contrib.auth import get_user_model
from apps.organizations.models import Organization
from apps.accounts.models import UserOrganization

User = get_user_model()


class TestUserListAPI:
    """Test user list API endpoints."""

    def test_list_users_unauthorized(self, api_client):
        """Test that unauthorized users cannot list users."""
        url = '/api/auth/users/'
        response = api_client.get(url)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert response.data['success'] is False
        assert 'error' in response.data

    def test_list_users_authorized(self, authenticated_client, user):
        """Test listing users as authenticated user."""
        url = '/api/auth/users/'
        response = authenticated_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data['success'] is True
        assert 'results' in response.data['data'] or 'count' in response.data['data']

    def test_list_users_pagination(self, authenticated_client):
        """Test user list pagination."""
        url = '/api/auth/users/?page=1&page_size=10'
        response = authenticated_client.get(url)
        assert response.status_code == status.HTTP_200_OK

    def test_list_users_search(self, authenticated_client, user):
        """Test searching users."""
        url = '/api/auth/users/?search=test'
        response = authenticated_client.get(url)
        assert response.status_code == status.HTTP_200_OK

    def test_create_user(self, admin_client, organization):
        """Test creating a new user."""
        url = '/api/auth/users/'
        data = {
            'username': 'newuser',
            'email': 'new@example.com',
            'password': 'newpass123',
            'password_confirm': 'newpass123',
            'first_name': 'New',
            'last_name': 'User',
        }
        response = admin_client.post(url, data, format='json')
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['success'] is True

    def test_create_user_password_mismatch(self, admin_client):
        """Test creating user with mismatched passwords fails."""
        url = '/api/auth/users/'
        data = {
            'username': 'newuser',
            'email': 'new@example.com',
            'password': 'newpass123',
            'password_confirm': 'different',
        }
        response = admin_client.post(url, data, format='json')
        assert response.status_code == status.HTTP_400_BAD_REQUEST


class TestUserDetailAPI:
    """Test user detail API endpoints."""

    def test_get_user_detail(self, authenticated_client, user):
        """Test getting single user details."""
        url = f'/api/auth/users/{user.id}/'
        response = authenticated_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data['data']['username'] == 'testuser'

    def test_update_user(self, authenticated_client, user):
        """Test updating a user."""
        url = f'/api/auth/users/{user.id}/'
        data = {
            'first_name': 'Updated',
            'last_name': 'Name',
            'email': 'updated@example.com'
        }
        response = authenticated_client.patch(url, data, format='json')
        assert response.status_code == status.HTTP_200_OK

        user.refresh_from_db()
        assert user.first_name == 'Updated'

    def test_delete_user_by_admin(self, admin_client, user):
        """Test that admin can soft delete another user."""
        url = f'/api/auth/users/{user.id}/'
        response = admin_client.delete(url)
        assert response.status_code == status.HTTP_200_OK

        user.refresh_from_db()
        assert user.is_deleted

    def test_delete_self_forbidden(self, authenticated_client, user):
        """Test that user cannot delete themselves."""
        url = f'/api/auth/users/{user.id}/'
        response = authenticated_client.delete(url)
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'own account' in response.data['error']['message'].lower()


class TestUserMeAPI:
    """Test /me endpoints."""

    def test_get_current_user(self, authenticated_client, user):
        """Test getting current user info."""
        url = '/api/auth/users/me/'
        response = authenticated_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data['data']['username'] == 'testuser'

    def test_get_current_user_unauthorized(self, api_client):
        """Test that unauthorized users cannot get current user."""
        url = '/api/auth/users/me/'
        response = api_client.get(url)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert response.data['success'] is False
        assert 'error' in response.data

    def test_change_password(self, authenticated_client, user):
        """Test changing password."""
        url = '/api/auth/users/me/change-password/'
        data = {
            'old_password': 'testpass123',
            'new_password': 'newpass456',
            'new_password_confirm': 'newpass456'
        }
        response = authenticated_client.post(url, data, format='json')
        assert response.status_code == status.HTTP_200_OK

    def test_change_password_wrong_old(self, authenticated_client, user):
        """Test changing password with wrong old password fails."""
        url = '/api/auth/users/me/change-password/'
        data = {
            'old_password': 'wrongpass',
            'new_password': 'newpass456',
            'new_password_confirm': 'newpass456'
        }
        response = authenticated_client.post(url, data, format='json')
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_change_password_mismatch(self, authenticated_client, user):
        """Test changing password with mismatched confirmation fails."""
        url = '/api/auth/users/me/change-password/'
        data = {
            'old_password': 'testpass123',
            'new_password': 'newpass456',
            'new_password_confirm': 'different'
        }
        response = authenticated_client.post(url, data, format='json')
        assert response.status_code == status.HTTP_400_BAD_REQUEST


class TestUserActionAPI:
    """Test user action endpoints."""

    def test_activate_user(self, admin_client, user):
        """Test activating a user."""
        user.is_active = False
        user.save()

        url = f'/api/auth/users/{user.id}/activate/'
        response = admin_client.post(url)
        assert response.status_code == status.HTTP_200_OK

        user.refresh_from_db()
        assert user.is_active

    def test_deactivate_user(self, admin_client):
        """Test deactivating a user."""
        # Create a separate user to deactivate
        org = Organization.objects.first()
        target_user = User.objects.create_user(
            username='target',
            email='target@example.com',
            password='pass123'
        )
        UserOrganization.objects.create(
            user=target_user,
            organization=org,
            role='member'
        )

        url = f'/api/auth/users/{target_user.id}/deactivate/'
        response = admin_client.post(url)
        assert response.status_code == status.HTTP_200_OK

        target_user.refresh_from_db()
        assert not target_user.is_active

    def test_deactivate_self_forbidden(self, authenticated_client, user):
        """Test that user cannot deactivate themselves."""
        url = f'/api/auth/users/{user.id}/deactivate/'
        response = authenticated_client.post(url)
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_get_user_organizations(self, authenticated_client, user, organization):
        """Test getting user's organizations."""
        url = f'/api/auth/users/{user.id}/organizations/'
        response = authenticated_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['data']) >= 1

    def test_switch_organization(self, authenticated_client, user, second_organization):
        """Test switching user's organization."""
        # Add user to second org
        UserOrganization.objects.create(
            user=user,
            organization=second_organization,
            role='admin'
        )

        url = f'/api/auth/users/{user.id}/switch-org/'
        data = {'organization_id': str(second_organization.id)}
        response = authenticated_client.post(url, data, format='json')
        assert response.status_code == status.HTTP_200_OK

    def test_switch_org_forbidden_for_other_user(self, authenticated_client, admin_user, organization):
        """Test that user cannot switch another user's organization."""
        url = f'/api/auth/users/{admin_user.id}/switch-org/'
        data = {'organization_id': str(organization.id)}
        response = authenticated_client.post(url, data, format='json')
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_get_accessible_users(self, authenticated_client, user, organization):
        """Test getting accessible users endpoint."""
        url = '/api/auth/users/accessible/'
        response = authenticated_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert 'count' in response.data['data']

    def test_get_stats(self, authenticated_client, organization):
        """Test getting user statistics."""
        url = '/api/auth/users/stats/'
        response = authenticated_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert 'total' in response.data['data']


class TestOrganizationFilterAPI:
    """Test organization-based filtering."""

    def test_users_filtered_by_organization(self, authenticated_client, user, second_organization):
        """Test that users are filtered by current organization."""
        # user is only in first organization
        url = '/api/auth/users/'
        response = authenticated_client.get(url)
        assert response.status_code == status.HTTP_200_OK

        # Should only see users from current org
        results = response.data['data'].get('results', response.data['data'])
        if results:
            for u in results:
                assert u['username'] == 'testuser'  # Only our test user


class TestUserSelectorAPI:
    """Test user selector endpoints."""

    def test_selector_search(self, authenticated_client, user):
        """Test user selector search endpoint."""
        url = '/api/users/selector/search/?q=test'
        response = authenticated_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data['success'] is True
        assert 'data' in response.data

    def test_selector_by_organization(self, authenticated_client, user, organization):
        """Test getting users by organization via selector."""
        url = f'/api/users/selector/by-organization/{organization.id}/'
        response = authenticated_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data['success'] is True
        assert len(response.data['data']) >= 1

    def test_selector_by_department(self, authenticated_client, user, organization, department):
        """Test getting users by department via selector."""
        from apps.organizations.models import UserDepartment

        # Add user to department
        UserDepartment.objects.create(
            user=user,
            organization=organization,
            department=department,
            is_primary=True
        )

        url = f'/api/users/selector/by-department/{department.id}/'
        response = authenticated_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data['success'] is True
        assert len(response.data['data']) >= 1
        # Verify department field is present
        assert 'department' in response.data['data'][0]
        assert 'avatar_url' in response.data['data'][0]

    def test_selector_current_user(self, authenticated_client, user):
        """Test getting current user via selector."""
        url = '/api/users/selector/current/'
        response = authenticated_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data['success'] is True
        assert response.data['data']['username'] == 'testuser'
        # Verify department and avatar_url fields are present
        assert 'department' in response.data['data']
        assert 'avatar_url' in response.data['data']

    def test_selector_serializer_has_department_field(self, authenticated_client, user, organization, department):
        """Test that UserSelectorSerializer includes department field."""
        from apps.organizations.models import UserDepartment
        from apps.accounts.serializers import UserSelectorSerializer

        # Add user to department
        UserDepartment.objects.create(
            user=user,
            organization=organization,
            department=department,
            is_primary=True
        )

        serializer = UserSelectorSerializer(
            user,
            context={'organization_id': str(organization.id)}
        )
        data = serializer.data

        assert 'department' in data
        assert 'avatar_url' in data
        assert data['department'] is not None
        assert data['department']['id'] == str(department.id)

    def test_selector_serializer_without_department(self, authenticated_client, user):
        """Test UserSelectorSerializer when user has no department."""
        from apps.accounts.serializers import UserSelectorSerializer

        serializer = UserSelectorSerializer(user)
        data = serializer.data

        assert 'department' in data
        assert 'avatar_url' in data
        assert data['department'] is None
        assert data['avatar_url'] == ""
