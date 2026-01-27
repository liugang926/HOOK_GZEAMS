"""
Tests for User and UserOrganization models.
"""
import pytest
from django.core.exceptions import ValidationError
from django.contrib.auth import get_user_model
from apps.organizations.models import Organization
from apps.accounts.models import UserOrganization

User = get_user_model()


class TestUser:
    """Test User model."""

    def test_create_user(self, db):
        """Test creating a standard user."""
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        assert user.username == 'testuser'
        assert user.email == 'test@example.com'
        assert user.check_password('testpass123')
        assert not user.is_staff
        assert not user.is_superuser

    def test_create_superuser(self, db):
        """Test creating a superuser."""
        user = User.objects.create_superuser(
            username='admin',
            email='admin@example.com',
            password='adminpass123'
        )
        assert user.is_staff
        assert user.is_superuser

    def test_user_str_representation(self, db):
        """Test user string representation."""
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        user.first_name = 'Test'
        user.last_name = 'User'
        user.save()
        assert str(user) == 'testuser (Test User)'

    def test_sso_fields(self, db):
        """Test SSO integration fields are stored correctly."""
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123',
            wework_userid='WW123',
            wework_unionid='WWU123',
            dingtalk_userid='DT123',
            dingtalk_unionid='DTU123',
            feishu_userid='FS123',
            feishu_unionid='FSU123',
        )
        assert user.wework_userid == 'WW123'
        assert user.dingtalk_userid == 'DT123'
        assert user.feishu_userid == 'FS123'

    def test_soft_delete(self, db):
        """Test User soft delete functionality."""
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        user_id = user.id

        # Soft delete
        user.soft_delete(None)
        user.refresh_from_db()

        assert user.is_deleted
        assert user.deleted_at is not None

        # User model doesn't use TenantManager (no org field)
        # So we need to check is_deleted field directly
        assert User.objects.filter(id=user_id, is_deleted=False).count() == 0
        assert User.all_objects.filter(id=user_id).exists()

    def test_get_accessible_organizations(self, user, organization, second_organization):
        """Test getting user's accessible organizations."""
        # Add user to second organization
        UserOrganization.objects.create(
            user=user,
            organization=second_organization,
            role='auditor'
        )

        orgs = user.get_accessible_organizations()
        assert orgs.count() == 2

    def test_get_org_role(self, user, organization):
        """Test getting user's role in an organization."""
        role = user.get_org_role(organization.id)
        assert role == 'member'

    def test_get_org_role_no_membership(self, user, second_organization):
        """Test getting role when user is not a member."""
        role = user.get_org_role(second_organization.id)
        assert role is None

    def test_get_primary_organization(self, user, organization):
        """Test getting user's primary organization."""
        primary = user.get_primary_organization()
        assert primary == organization

    def test_switch_organization(self, user, organization, second_organization):
        """Test switching user's current organization."""
        # Add to second org
        UserOrganization.objects.create(
            user=user,
            organization=second_organization,
            role='admin',
            is_primary=True
        )

        result = user.switch_organization(second_organization.id)
        assert result is True

        user.refresh_from_db()
        assert user.current_organization == second_organization

    def test_switch_organization_not_accessible(self, user, second_organization):
        """Test switching to non-accessible organization fails."""
        result = user.switch_organization(second_organization.id)
        assert result is False


class TestUserOrganization:
    """Test UserOrganization model."""

    def test_create_user_organization(self, db, organization):
        """Test creating user-organization relationship."""
        test_user = User.objects.create_user(
            username='testuser2',
            email='test2@example.com',
            password='testpass123'
        )
        user_org = UserOrganization.objects.create(
            user=test_user,
            organization=organization,
            role='admin'
        )
        assert user_org.user == test_user
        assert user_org.organization == organization
        assert user_org.role == 'admin'
        assert user_org.is_active

    def test_str_representation(self, db, organization):
        """Test string representation."""
        test_user = User.objects.create_user(
            username='testuser3',
            email='test3@example.com',
            password='testpass123'
        )
        user_org = UserOrganization.objects.create(
            user=test_user,
            organization=organization,
            role='admin'
        )
        assert 'testuser3' in str(user_org)
        assert 'Test Organization' in str(user_org)
        assert 'admin' in str(user_org)

    def test_only_one_primary_organization(self, user, organization, second_organization):
        """Test that only one organization can be primary."""
        # First org is already primary from fixture
        first_org = UserOrganization.objects.get(
            user=user, organization=organization
        )
        assert first_org.is_primary

        # Create second org as primary
        second_org = UserOrganization.objects.create(
            user=user,
            organization=second_organization,
            role='member',
            is_primary=True
        )

        # First should no longer be primary
        first_org.refresh_from_db()
        assert not first_org.is_primary
        assert second_org.is_primary

    def test_unique_user_organization(self, db, organization):
        """Test that user-org combination is unique."""
        test_user = User.objects.create_user(
            username='testuser4',
            email='test4@example.com',
            password='testpass123'
        )
        UserOrganization.objects.create(
            user=test_user,
            organization=organization,
            role='member'
        )

        # Try to create duplicate
        with pytest.raises(Exception):  # IntegrityError
            UserOrganization.objects.create(
                user=test_user,
                organization=organization,
                role='admin'
            )

    def test_role_choices(self, db, organization):
        """Test that only valid roles can be set."""
        # Create separate users for each role to avoid unique constraint violations
        for i, role in enumerate(['admin', 'member', 'auditor']):
            user = User.objects.create_user(
                username=f'testuser_role_{i}',
                email=f'test_role_{i}@example.com',
                password='testpass123'
            )
            user_org = UserOrganization.objects.create(
                user=user,
                organization=organization,
                role=role
            )
            assert user_org.role == role
