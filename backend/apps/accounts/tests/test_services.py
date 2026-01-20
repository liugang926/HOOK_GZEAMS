"""
Tests for UserService.
"""
import pytest
from django.core.exceptions import ValidationError
from django.contrib.auth import get_user_model
from apps.organizations.models import Organization
from apps.accounts.models import UserOrganization
from apps.accounts.services.user_service import UserService

User = get_user_model()


class TestUserService:
    """Test UserService class."""

    def test_create_user(self, db, organization):
        """Test creating a user via service."""
        service = UserService()
        user_data = {
            'username': 'newuser',
            'email': 'new@example.com',
            'first_name': 'New',
            'last_name': 'User',
        }
        user = service.create(user_data, organization)
        user.set_password('newpass123')
        user.save()

        assert user.username == 'newuser'
        assert user.email == 'new@example.com'
        assert user.check_password('newpass123')

    def test_get_user_by_id(self, user):
        """Test getting user by ID."""
        service = UserService()
        retrieved = service.get(str(user.id))
        assert retrieved == user

    def test_update_user(self, user):
        """Test updating user via service."""
        service = UserService()
        updated = service.update(str(user.id), {
            'first_name': 'Updated',
            'last_name': 'Name'
        })

        user.refresh_from_db()
        assert user.first_name == 'Updated'
        assert user.last_name == 'Name'

    def test_soft_delete_user(self, user):
        """Test soft deleting user via service."""
        service = UserService()
        service.delete(str(user.id))

        user.refresh_from_db()
        assert user.is_deleted

    def test_activate_user(self, user):
        """Test activating a user."""
        user.is_active = False
        user.save()

        service = UserService()
        service.activate_user(str(user.id))

        user.refresh_from_db()
        assert user.is_active

    def test_deactivate_user(self, user):
        """Test deactivating a user."""
        service = UserService()
        service.deactivate_user(str(user.id))

        user.refresh_from_db()
        assert not user.is_active

    def test_get_accessible_users(self, user, organization):
        """Test getting users accessible to an organization."""
        service = UserService()
        users = service.get_accessible_users(organization.id)

        assert user in users

    def test_get_accessible_users_with_filters(self, user, organization):
        """Test filtering accessible users."""
        # Create another inactive user
        inactive = User.objects.create_user(
            username='inactive',
            email='inactive@example.com',
            password='pass123',
            is_active=False
        )
        UserOrganization.objects.create(
            user=inactive,
            organization=organization,
            role='member'
        )

        service = UserService()
        users = service.get_accessible_users(organization.id, {'is_active': True})

        assert user in users
        assert inactive not in users

    def test_add_to_organization(self, user, second_organization):
        """Test adding user to an organization."""
        service = UserService()
        user_org = service.add_to_organization(
            str(user.id),
            str(second_organization.id),
            role='auditor'
        )

        assert user_org.user == user
        assert user_org.organization == second_organization
        assert user_org.role == 'auditor'

    def test_remove_from_organization(self, user, organization):
        """Test removing user from an organization."""
        service = UserService()
        service.remove_from_organization(str(user.id), str(organization.id))

        exists = UserOrganization.objects.filter(
            user=user,
            organization=organization,
            is_active=True
        ).exists()
        assert not exists

    def test_switch_organization(self, user, organization, second_organization):
        """Test switching user's organization via service."""
        # Add to second org
        UserOrganization.objects.create(
            user=user,
            organization=second_organization,
            role='admin',
            is_primary=True
        )

        service = UserService()
        result = service.switch_organization(str(user.id), str(second_organization.id))

        assert result is True
        user.refresh_from_db()
        assert user.current_organization == second_organization

    def test_get_user_stats(self, user, organization):
        """Test getting user statistics for an organization."""
        service = UserService()
        stats = service.get_user_stats(str(organization.id))

        assert 'total' in stats
        assert 'admins' in stats
        assert 'members' in stats
        assert 'auditors' in stats
        assert stats['total'] >= 1
        assert stats['members'] >= 1

    def test_query_with_pagination(self, user, organization):
        """Test querying users with pagination."""
        service = UserService()
        # First query users for this organization
        users_queryset = service.get_accessible_users(organization.id)
        # Then paginate the results
        result = service.paginate(users_queryset, page=1, page_size=10)

        assert 'results' in result
        assert 'count' in result
        assert 'results' in result
        assert result['count'] >= 1

    def test_batch_delete_users(self, db, organization):
        """Test batch deleting users."""
        users = []
        for i in range(3):
            test_user = User.objects.create_user(
                username=f'user{i}',
                email=f'user{i}@example.com',
                password='pass123'
            )
            UserOrganization.objects.create(
                user=test_user,
                organization=organization,
                role='member'
            )
            users.append(test_user)

        service = UserService()
        user_ids = [str(u.id) for u in users]
        result = service.batch_delete(user_ids, organization)

        assert result['total'] == 3
        assert result['succeeded'] == 3

        # Verify soft delete
        for test_user in users:
            test_user.refresh_from_db()
            assert test_user.is_deleted