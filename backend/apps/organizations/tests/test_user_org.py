"""
Tests for User and UserOrganization models.
"""
from django.test import TestCase
from django.core.exceptions import ValidationError
from apps.accounts.models import User, UserOrganization
from apps.organizations.models import Organization


class UserOrganizationTest(TestCase):
    """Test User-Organization relationship."""

    def setUp(self):
        """Set up test data."""
        self.org1 = Organization.objects.create(
            name='Organization 1',
            code='ORG1'
        )
        self.org2 = Organization.objects.create(
            name='Organization 2',
            code='ORG2'
        )
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com'
        )

    def test_add_user_to_organization(self):
        """Test adding user to organization."""
        user_org = UserOrganization.objects.create(
            user=self.user,
            organization=self.org1,
            role='member'
        )
        self.assertEqual(user_org.role, 'member')
        self.assertTrue(user_org.is_active)

    def test_get_accessible_organizations(self):
        """Test getting user's accessible organizations."""
        UserOrganization.objects.create(
            user=self.user,
            organization=self.org1,
            role='admin',
            is_primary=True
        )
        UserOrganization.objects.create(
            user=self.user,
            organization=self.org2,
            role='member'
        )

        accessible = self.user.get_accessible_organizations()
        self.assertEqual(accessible.count(), 2)

    def test_get_org_role(self):
        """Test getting user role in organization."""
        UserOrganization.objects.create(
            user=self.user,
            organization=self.org1,
            role='admin'
        )

        role = self.user.get_org_role(self.org1.id)
        self.assertEqual(role, 'admin')

    def test_switch_organization(self):
        """Test switching user's current organization."""
        UserOrganization.objects.create(
            user=self.user,
            organization=self.org1,
            role='member'
        )
        UserOrganization.objects.create(
            user=self.user,
            organization=self.org2,
            role='member'
        )

        result = self.user.switch_organization(self.org2.id)
        self.assertTrue(result)
        self.assertEqual(self.user.current_organization, self.org2)

    def test_is_primary_uniqueness(self):
        """Test that only one organization can be primary."""
        UserOrganization.objects.create(
            user=self.user,
            organization=self.org1,
            role='member',
            is_primary=True
        )

        user_org2 = UserOrganization.objects.create(
            user=self.user,
            organization=self.org2,
            role='member',
            is_primary=False
        )

        # Set second org as primary
        user_org2.is_primary = True
        user_org2.save()

        # First should no longer be primary
        user_org1 = UserOrganization.objects.get(
            user=self.user,
            organization=self.org1
        )
        self.assertFalse(user_org1.is_primary)
        self.assertTrue(user_org2.is_primary)

    def test_get_primary_organization(self):
        """Test getting user's primary organization."""
        UserOrganization.objects.create(
            user=self.user,
            organization=self.org1,
            role='admin',
            is_primary=True
        )

        primary = self.user.get_primary_organization()
        self.assertEqual(primary, self.org1)

    def test_unique_constraint(self):
        """Test unique constraint on user+organization."""
        UserOrganization.objects.create(
            user=self.user,
            organization=self.org1,
            role='member'
        )

        # Try to create duplicate
        with self.assertRaises(ValidationError):
            duplicate = UserOrganization(
                user=self.user,
                organization=self.org1,
                role='admin'
            )
            duplicate.clean()
