"""
Tests for UserSelectorViewSet API endpoints.
"""
import pytest
from django.urls import reverse
from apps.accounts.models import User, UserOrganization
from apps.organizations.models import Organization


@pytest.mark.django_db
class TestUserSelectorViewSet:
    """Test suite for UserSelectorViewSet."""

    def test_search_users_by_username(self, authenticated_client, organization):
        """Test user search endpoint by username."""
        # Create test users
        User.objects.create_user(
            username='john.doe',
            email='john@example.com',
            first_name='John',
            last_name='Doe',
        )
        UserOrganization.objects.create(
            user=User.objects.get(username='john.doe'),
            organization=organization,
            role='member',
            is_primary=True
        )

        User.objects.create_user(
            username='jane.smith',
            email='jane@example.com',
            first_name='Jane',
            last_name='Smith',
        )
        UserOrganization.objects.create(
            user=User.objects.get(username='jane.smith'),
            organization=organization,
            role='member',
            is_primary=True
        )

        url = '/api/auth/users/selector/search/'
        response = authenticated_client.get(url, {'q': 'john'})

        assert response.status_code == 200
        data = response.json()
        assert data['success'] is True
        assert len(data['data']) >= 1
        # Check that at least one result contains 'john'
        results = data['data']
        assert any('john' in result['username'].lower() for result in results)

    def test_search_users_by_email(self, authenticated_client, organization):
        """Test user search endpoint by email."""
        User.objects.create_user(
            username='bob.wilson',
            email='bob@example.com',
            first_name='Bob',
            last_name='Wilson',
        )
        UserOrganization.objects.create(
            user=User.objects.get(username='bob.wilson'),
            organization=organization,
            role='member',
            is_primary=True
        )

        url = '/api/auth/users/selector/search/'
        response = authenticated_client.get(url, {'q': 'bob@example.com'})

        assert response.status_code == 200
        data = response.json()
        assert data['success'] is True
        assert len(data['data']) >= 1

    def test_search_users_with_limit(self, authenticated_client, organization):
        """Test user search endpoint with limit parameter."""
        # Create multiple users
        for i in range(10):
            User.objects.create_user(
                username=f'user{i}',
                email=f'user{i}@example.com',
                first_name=f'First{i}',
                last_name=f'Last{i}',
            )
            UserOrganization.objects.create(
                user=User.objects.get(username=f'user{i}'),
                organization=organization,
                role='member',
                is_primary=True
            )

        url = '/api/auth/users/selector/search/'
        response = authenticated_client.get(url, {'q': 'user', 'limit': 5})

        assert response.status_code == 200
        data = response.json()
        assert data['success'] is True
        assert len(data['data']) <= 5

    def test_search_users_empty_query(self, authenticated_client, organization):
        """Test user search endpoint with empty query returns all users."""
        url = '/api/auth/users/selector/search/'
        response = authenticated_client.get(url, {})

        assert response.status_code == 200
        data = response.json()
        assert data['success'] is True
        # Should return at least the authenticated user
        assert len(data['data']) >= 1

    def test_by_organization(self, authenticated_client, organization):
        """Test getting users by organization."""
        # Create test users in the organization
        user1 = User.objects.create_user(
            username='org.user1',
            email='orguser1@example.com',
            first_name='Org',
            last_name='User1',
        )
        UserOrganization.objects.create(
            user=user1,
            organization=organization,
            role='member',
            is_primary=True
        )

        user2 = User.objects.create_user(
            username='org.user2',
            email='orguser2@example.com',
            first_name='Org',
            last_name='User2',
        )
        UserOrganization.objects.create(
            user=user2,
            organization=organization,
            role='member',
            is_primary=True
        )

        url = f'/api/auth/users/selector/by-organization/{organization.id}/'
        response = authenticated_client.get(url)

        assert response.status_code == 200
        data = response.json()
        assert data['success'] is True
        assert len(data['data']) >= 2
        usernames = [user['username'] for user in data['data']]
        assert 'org.user1' in usernames
        assert 'org.user2' in usernames

    def test_current_user(self, authenticated_client):
        """Test current user endpoint."""
        url = '/api/auth/users/selector/current/'
        response = authenticated_client.get(url)

        assert response.status_code == 200
        data = response.json()
        assert data['success'] is True
        assert 'value' in data['data']
        assert 'username' in data['data']
        assert 'label' in data['data']
        assert 'email' in data['data']

    def test_current_user_unauthenticated(self, api_client):
        """Test current user endpoint requires authentication."""
        url = '/api/auth/users/selector/current/'
        response = api_client.get(url)

        assert response.status_code == 401

    def test_user_selector_serializer_fields(self, authenticated_client, organization):
        """Test that UserSelectorSerializer returns correct fields."""
        User.objects.create_user(
            username='serializer.test',
            email='serializer@example.com',
            first_name='Test',
            last_name='Serializer',
        )
        UserOrganization.objects.create(
            user=User.objects.get(username='serializer.test'),
            organization=organization,
            role='member',
            is_primary=True
        )

        url = '/api/auth/users/selector/search/'
        response = authenticated_client.get(url, {'q': 'serializer'})

        assert response.status_code == 200
        data = response.json()
        assert data['success'] is True

        user_data = data['data'][0]
        # Check for required fields
        assert 'value' in user_data
        assert 'username' in user_data
        assert 'full_name' in user_data
        assert 'email' in user_data
        assert 'label' in user_data

        # Check that label contains full name and username
        assert 'Test Serializer' in user_data['label']
        assert 'serializer.test' in user_data['label']

    def test_search_filters_by_organization(self, authenticated_client, organization):
        """Test that search respects organization filtering."""
        # Create user in the test organization
        org_user = User.objects.create_user(
            username='org.member',
            email='orgmember@example.com',
            first_name='Org',
            last_name='Member',
        )
        UserOrganization.objects.create(
            user=org_user,
            organization=organization,
            role='member',
            is_primary=True
        )

        # Create user in another organization
        other_org = Organization.objects.create(
            name='Other Organization',
            code='OTHER_ORG',
            is_active=True
        )
        other_user = User.objects.create_user(
            username='other.member',
            email='othermember@example.com',
            first_name='Other',
            last_name='Member',
        )
        UserOrganization.objects.create(
            user=other_user,
            organization=other_org,
            role='member',
            is_primary=True
        )

        # Search without organization_id should filter by current org
        url = '/api/auth/users/selector/search/'
        response = authenticated_client.get(url, {'q': 'member'})

        assert response.status_code == 200
        data = response.json()
        assert data['success'] is True

        usernames = [user['username'] for user in data['data']]
        # Should include org.member but not other.member
        assert 'org.member' in usernames
        assert 'other.member' not in usernames

    def test_search_with_specific_organization(self, authenticated_client, organization):
        """Test search with explicit organization_id parameter."""
        other_org = Organization.objects.create(
            name='Another Organization',
            code='ANOTHER_ORG',
            is_active=True
        )

        # Create user in other organization
        other_user = User.objects.create_user(
            username='another.user',
            email='another@example.com',
            first_name='Another',
            last_name='User',
        )
        UserOrganization.objects.create(
            user=other_user,
            organization=other_org,
            role='member',
            is_primary=True
        )

        # Search explicitly for other_org users
        url = '/api/auth/users/selector/search/'
        response = authenticated_client.get(url, {
            'q': 'another',
            'organization_id': other_org.id
        })

        assert response.status_code == 200
        data = response.json()
        assert data['success'] is True

        usernames = [user['username'] for user in data['data']]
        assert 'another.user' in usernames
