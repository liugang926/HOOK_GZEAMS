"""
Tests for AssetCategory model.
"""
from django.test import TestCase
from apps.assets.models import AssetCategory, Asset
from apps.organizations.models import Organization
from apps.accounts.models import User
from decimal import Decimal
from datetime import date


class AssetCategoryModelTest(TestCase):
    """Test AssetCategory model functionality."""

    def setUp(self):
        """Set up test data."""
        self.org = Organization.objects.create(
            name='Test Organization',
            code='TEST_ORG'
        )
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            organization=self.org
        )

    def test_create_root_category(self):
        """Test creating a root category."""
        category = AssetCategory.objects.create(
            organization=self.org,
            code='ELECTRONICS',
            name='Electronics',
            created_by=self.user
        )
        self.assertEqual(category.code, 'ELECTRONICS')
        self.assertEqual(category.name, 'Electronics')
        self.assertIsNone(category.parent)
        self.assertEqual(category.level, 0)
        self.assertTrue(category.is_active)

    def test_create_child_category(self):
        """Test creating a child category."""
        parent = AssetCategory.objects.create(
            organization=self.org,
            code='ELECTRONICS',
            name='Electronics',
            created_by=self.user
        )
        child = AssetCategory.objects.create(
            organization=self.org,
            code='COMPUTERS',
            name='Computers',
            parent=parent,
            created_by=self.user
        )
        self.assertEqual(child.parent, parent)
        self.assertEqual(child.level, 1)
        self.assertIn('Electronics', child.full_name)

    def test_get_tree(self):
        """Test get_tree class method."""
        parent = AssetCategory.objects.create(
            organization=self.org,
            code='ELECTRONICS',
            name='Electronics',
            created_by=self.user
        )
        child = AssetCategory.objects.create(
            organization=self.org,
            code='COMPUTERS',
            name='Computers',
            parent=parent,
            created_by=self.user
        )

        tree = AssetCategory.get_tree(str(self.org.id))
        self.assertEqual(len(tree), 1)
        self.assertEqual(tree[0]['code'], 'ELECTRONICS')
        self.assertEqual(len(tree[0]['children']), 1)

        # Verify is_leaf field
        self.assertIn('is_leaf', tree[0])
        self.assertFalse(tree[0]['is_leaf'], 'Parent category should not be a leaf')
        self.assertTrue(tree[0]['children'][0]['is_leaf'], 'Child category should be a leaf')

        # Verify asset_count field
        self.assertIn('asset_count', tree[0])
        self.assertEqual(tree[0]['asset_count'], 0, 'Parent should have 0 assets')
        self.assertEqual(tree[0]['children'][0]['asset_count'], 0, 'Child should have 0 assets')

    def test_get_tree_with_asset_count(self):
        """Test get_tree with actual assets."""
        # Create categories
        parent = AssetCategory.objects.create(
            organization=self.org,
            code='ELECTRONICS',
            name='Electronics',
            created_by=self.user
        )
        child = AssetCategory.objects.create(
            organization=self.org,
            code='COMPUTERS',
            name='Computers',
            parent=parent,
            created_by=self.user
        )

        # Create assets in child category
        Asset.objects.create(
            organization=self.org,
            asset_code='ZC2026010001',
            asset_name='Test Laptop 1',
            asset_category=child,
            purchase_price=Decimal('5000.00'),
            purchase_date=date.today(),
            created_by=self.user
        )
        Asset.objects.create(
            organization=self.org,
            asset_code='ZC2026010002',
            asset_name='Test Laptop 2',
            asset_category=child,
            purchase_price=Decimal('6000.00'),
            purchase_date=date.today(),
            created_by=self.user
        )

        # Get tree and verify counts
        tree = AssetCategory.get_tree(str(self.org.id))
        self.assertEqual(len(tree), 1)
        self.assertEqual(tree[0]['asset_count'], 0, 'Parent should have 0 assets')
        self.assertEqual(tree[0]['children'][0]['asset_count'], 2, 'Child should have 2 assets')

    def test_get_tree_is_leaf_field(self):
        """Test is_leaf field in get_tree."""
        # Create multi-level category tree
        root = AssetCategory.objects.create(
            organization=self.org,
            code='ROOT',
            name='Root Category',
            created_by=self.user
        )
        child1 = AssetCategory.objects.create(
            organization=self.org,
            code='CHILD1',
            name='Child 1',
            parent=root,
            created_by=self.user
        )
        child2 = AssetCategory.objects.create(
            organization=self.org,
            code='CHILD2',
            name='Child 2',
            parent=root,
            created_by=self.user
        )
        grandchild = AssetCategory.objects.create(
            organization=self.org,
            code='GRANDCHILD',
            name='Grandchild',
            parent=child1,
            created_by=self.user
        )

        tree = AssetCategory.get_tree(str(self.org.id))

        # Root has children, so not a leaf
        self.assertFalse(tree[0]['is_leaf'])

        # Child1 has grandchild, so not a leaf
        child1_data = [c for c in tree[0]['children'] if c['code'] == 'CHILD1'][0]
        self.assertFalse(child1_data['is_leaf'])

        # Child2 has no children, so it's a leaf
        child2_data = [c for c in tree[0]['children'] if c['code'] == 'CHILD2'][0]
        self.assertTrue(child2_data['is_leaf'])

        # Grandchild has no children, so it's a leaf
        self.assertTrue(child1_data['children'][0]['is_leaf'])

    def test_can_delete_with_children(self):
        """Test can_delete returns False when category has children."""
        parent = AssetCategory.objects.create(
            organization=self.org,
            code='ELECTRONICS',
            name='Electronics',
            created_by=self.user
        )
        AssetCategory.objects.create(
            organization=self.org,
            code='COMPUTERS',
            name='Computers',
            parent=parent,
            created_by=self.user
        )

        self.assertFalse(parent.can_delete())

    def test_can_delete_without_children(self):
        """Test can_delete returns True when category has no children."""
        category = AssetCategory.objects.create(
            organization=self.org,
            code='ELECTRONICS',
            name='Electronics',
            created_by=self.user
        )

        self.assertTrue(category.can_delete())

    def test_soft_delete(self):
        """Test soft delete functionality."""
        category = AssetCategory.objects.create(
            organization=self.org,
            code='ELECTRONICS',
            name='Electronics',
            created_by=self.user
        )
        category.soft_delete()

        self.assertTrue(category.is_deleted)
        self.assertIsNotNone(category.deleted_at)

    def test_depreciation_method_choices(self):
        """Test depreciation method choices."""
        category = AssetCategory.objects.create(
            organization=self.org,
            code='ELECTRONICS',
            name='Electronics',
            depreciation_method='straight_line',
            default_useful_life=60,
            residual_rate=5.00,
            created_by=self.user
        )
        self.assertEqual(category.depreciation_method, 'straight_line')
        self.assertEqual(category.default_useful_life, 60)
        self.assertEqual(float(category.residual_rate), 5.00)
