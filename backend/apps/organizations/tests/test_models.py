"""
Tests for Organization model.
"""
from django.test import TestCase
from apps.organizations.models import Organization


class OrganizationModelTest(TestCase):
    """Test Organization model functionality."""

    def setUp(self):
        """Set up test data."""
        self.root_org = Organization.objects.create(
            name='Root Organization',
            code='ROOT',
            org_type='group'
        )

    def test_create_root_organization(self):
        """Test creating a root organization."""
        org = Organization.objects.get(code='ROOT')
        self.assertEqual(org.name, 'Root Organization')
        self.assertEqual(org.level, 0)
        self.assertEqual(org.path, '/ROOT')
        self.assertIsNone(org.parent)

    def test_create_child_organization(self):
        """Test creating a child organization."""
        child = Organization.objects.create(
            name='Child Company',
            code='CHILD',
            parent=self.root_org,
            org_type='company'
        )
        self.assertEqual(child.parent, self.root_org)
        self.assertEqual(child.level, 1)
        self.assertEqual(child.path, '/ROOT/CHILD')

    def test_get_all_children(self):
        """Test get_all_children method."""
        # Create children
        Organization.objects.create(
            name='Child 1',
            code='CHILD1',
            parent=self.root_org
        )
        Organization.objects.create(
            name='Child 2',
            code='CHILD2',
            parent=self.root_org
        )
        # Create grandchild
        child1 = Organization.objects.get(code='CHILD1')
        Organization.objects.create(
            name='Grandchild',
            code='GRAND',
            parent=child1
        )

        children = self.root_org.get_all_children()
        self.assertEqual(children.count(), 3)

    def test_invite_code_generation(self):
        """Test invite code generation."""
        org = Organization.objects.create(
            name='Test Org',
            code='TEST'
        )
        self.assertIsNotNone(org.invite_code)
        self.assertEqual(len(org.invite_code), 8)
        self.assertTrue(org.is_invite_code_valid())

    def test_regenerate_invite_code(self):
        """Test invite code regeneration."""
        org = Organization.objects.get(code='ROOT')
        old_code = org.invite_code
        org.regenerate_invite_code()
        self.assertNotEqual(org.invite_code, old_code)

    def test_get_default_organization(self):
        """Test default organization initialization."""
        default_org = Organization.get_default_organization()
        self.assertIsNotNone(default_org)
        self.assertEqual(default_org.code, 'DEFAULT')

    def test_organization_type_choices(self):
        """Test organization type choices."""
        org = Organization.objects.get(code='ROOT')
        self.assertEqual(org.org_type, 'group')
        self.assertIn(org.org_type, ['group', 'company', 'branch', 'department'])

    def test_soft_delete_flag(self):
        """Test soft delete flag."""
        org = Organization.objects.get(code='ROOT')
        self.assertFalse(org.is_deleted)
        org.is_deleted = True
        org.save()
        org.refresh_from_db()
        self.assertTrue(org.is_deleted)
