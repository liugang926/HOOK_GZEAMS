"""
Tests for Asset services.

Tests cover:
- AssetService CRUD operations
- AssetService status change with logging
- AssetService statistics and queries
- SupplierService CRUD operations
- LocationService tree operations
- AssetStatusLogService operations
"""
from django.test import TestCase
from decimal import Decimal
from apps.assets.models import (
    Asset,
    Supplier,
    Location,
    AssetStatusLog,
    AssetCategory
)
from apps.assets.services import (
    AssetService,
    SupplierService,
    LocationService,
    AssetStatusLogService
)
from apps.organizations.models import Organization, Department
from apps.accounts.models import User


class AssetServiceTest(TestCase):
    """Test AssetService functionality."""

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
        self.service = AssetService()

        self.category = AssetCategory.objects.create(
            organization=self.org,
            code='COMPUTER',
            name='Computer Equipment',
            created_by=self.user
        )

    def test_create_asset(self):
        """Test creating an asset via service."""
        data = {
            'asset_name': 'Test Laptop',
            'asset_category': self.category,
            'purchase_price': Decimal('1000.00'),
            'purchase_date': '2024-01-01',
            'organization_id': self.org.id
        }

        asset = self.service.create(data, self.user)

        self.assertIsNotNone(asset.id)
        self.assertEqual(asset.asset_name, 'Test Laptop')
        self.assertTrue(asset.asset_code.startswith('ZC'))
        self.assertIsNotNone(asset.qr_code)

    def test_get_by_code(self):
        """Test retrieving asset by code."""
        asset = Asset.objects.create(
            organization=self.org,
            asset_name='Test Laptop',
            asset_category=self.category,
            purchase_price=Decimal('1000.00'),
            purchase_date='2024-01-01',
            created_by=self.user
        )

        found = self.service.get_by_code(asset.asset_code, str(self.org.id))

        self.assertIsNotNone(found)
        self.assertEqual(found.id, asset.id)

    def test_get_by_qr_code(self):
        """Test retrieving asset by QR code."""
        asset = Asset.objects.create(
            organization=self.org,
            asset_name='Test Laptop',
            asset_category=self.category,
            purchase_price=Decimal('1000.00'),
            purchase_date='2024-01-01',
            created_by=self.user
        )

        found = self.service.get_by_qr_code(asset.qr_code, str(self.org.id))

        self.assertIsNotNone(found)
        self.assertEqual(found.id, asset.id)

    def test_change_status(self):
        """Test changing asset status with logging."""
        asset = Asset.objects.create(
            organization=self.org,
            asset_name='Test Laptop',
            asset_category=self.category,
            purchase_price=Decimal('1000.00'),
            purchase_date='2024-01-01',
            asset_status='pending',
            created_by=self.user
        )

        updated = self.service.change_status(
            asset_id=str(asset.id),
            new_status='in_use',
            user=self.user,
            reason='Issued to employee'
        )

        self.assertEqual(updated.asset_status, 'in_use')

        # Verify status log was created
        log = AssetStatusLog.objects.filter(asset=asset).first()
        self.assertIsNotNone(log)
        self.assertEqual(log.old_status, 'pending')
        self.assertEqual(log.new_status, 'in_use')
        self.assertEqual(log.reason, 'Issued to employee')

    def test_change_status_same_status(self):
        """Test changing to same status raises error."""
        asset = Asset.objects.create(
            organization=self.org,
            asset_name='Test Laptop',
            asset_category=self.category,
            purchase_price=Decimal('1000.00'),
            purchase_date='2024-01-01',
            asset_status='in_use',
            created_by=self.user
        )

        with self.assertRaises(ValueError) as context:
            self.service.change_status(
                asset_id=str(asset.id),
                new_status='in_use',
                user=self.user
            )

        self.assertIn('already in', str(context.exception))

    def test_get_asset_statistics(self):
        """Test getting asset statistics."""
        # Create multiple assets with different statuses
        Asset.objects.create(
            organization=self.org,
            asset_name='Asset 1',
            asset_category=self.category,
            purchase_price=Decimal('10000.00'),
            asset_status='in_use',
            purchase_date='2024-01-01',
            created_by=self.user
        )
        Asset.objects.create(
            organization=self.org,
            asset_name='Asset 2',
            asset_category=self.category,
            purchase_price=Decimal('5000.00'),
            asset_status='idle',
            purchase_date='2024-01-01',
            created_by=self.user
        )

        stats = self.service.get_asset_statistics(str(self.org.id))

        self.assertEqual(stats['total'], 2)
        self.assertIn('by_status', stats)
        self.assertIn('total_value', stats)
        self.assertEqual(stats['total_value'], 15000.00)

    def test_query_by_category(self):
        """Test querying assets by category."""
        other_category = AssetCategory.objects.create(
            organization=self.org,
            code='FURNITURE',
            name='Furniture',
            created_by=self.user
        )

        Asset.objects.create(
            organization=self.org,
            asset_name='Computer',
            asset_category=self.category,
            purchase_price=Decimal('1000.00'),
            purchase_date='2024-01-01',
            created_by=self.user
        )
        Asset.objects.create(
            organization=self.org,
            asset_name='Desk',
            asset_category=other_category,
            purchase_price=Decimal('500.00'),
            purchase_date='2024-01-01',
            created_by=self.user
        )

        queryset = self.service.query_by_category(
            category_id=str(self.category.id),
            organization_id=str(self.org.id)
        )

        self.assertEqual(queryset.count(), 1)
        self.assertEqual(queryset.first().asset_name, 'Computer')

    def test_search_assets(self):
        """Test searching assets by keyword."""
        Asset.objects.create(
            organization=self.org,
            asset_name='Dell Laptop',
            asset_category=self.category,
            brand='Dell',
            model='Latitude 7420',
            purchase_price=Decimal('1000.00'),
            purchase_date='2024-01-01',
            created_by=self.user
        )
        Asset.objects.create(
            organization=self.org,
            asset_name='HP Desktop',
            asset_category=self.category,
            brand='HP',
            model='EliteDesk',
            purchase_price=Decimal('800.00'),
            purchase_date='2024-01-01',
            created_by=self.user
        )

        # Search by brand
        results = self.service.search_assets(str(self.org.id), 'Dell')
        self.assertEqual(results.count(), 1)

        # Search by name
        results = self.service.search_assets(str(self.org.id), 'HP')
        self.assertEqual(results.count(), 1)


class SupplierServiceTest(TestCase):
    """Test SupplierService functionality."""

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
        self.service = SupplierService()

    def test_create_supplier(self):
        """Test creating a supplier."""
        data = {
            'code': 'DELL',
            'name': 'Dell Inc.',
            'contact': 'John Doe',
            'phone': '123-456-7890',
            'organization_id': self.org.id
        }

        supplier = self.service.create(data, self.user)

        self.assertIsNotNone(supplier.id)
        self.assertEqual(supplier.code, 'DELL')
        self.assertEqual(supplier.name, 'Dell Inc.')

    def test_get_by_code(self):
        """Test retrieving supplier by code."""
        Supplier.objects.create(
            organization=self.org,
            code='DELL',
            name='Dell Inc.',
            created_by=self.user
        )

        found = self.service.get_by_code('DELL', str(self.org.id))

        self.assertIsNotNone(found)
        self.assertEqual(found.name, 'Dell Inc.')


class LocationServiceTest(TestCase):
    """Test LocationService functionality."""

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
        self.service = LocationService()

    def test_create_location(self):
        """Test creating a location."""
        data = {
            'name': 'Building A',
            'location_type': 'building',
            'organization_id': self.org.id
        }

        location = self.service.create(data, self.user)

        self.assertIsNotNone(location.id)
        self.assertEqual(location.name, 'Building A')
        self.assertEqual(location.location_type, 'building')

    def test_get_tree(self):
        """Test getting location tree."""
        building = Location.objects.create(
            organization=self.org,
            name='Building A',
            location_type='building',
            created_by=self.user
        )
        Location.objects.create(
            organization=self.org,
            name='Floor 1',
            parent=building,
            location_type='floor',
            created_by=self.user
        )

        tree = self.service.get_tree(str(self.org.id))

        self.assertEqual(len(tree), 1)
        self.assertEqual(tree[0]['name'], 'Building A')
        self.assertTrue(tree[0]['has_children'])
        self.assertEqual(len(tree[0]['children']), 1)

    def test_get_by_path(self):
        """Test retrieving location by path."""
        Location.objects.create(
            organization=self.org,
            name='Server Room',
            location_type='room',
            created_by=self.user
        )

        found = self.service.get_by_path('Server Room', str(self.org.id))

        self.assertIsNotNone(found)
        self.assertEqual(found.name, 'Server Room')


class AssetStatusLogServiceTest(TestCase):
    """Test AssetStatusLogService functionality."""

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
        self.category = AssetCategory.objects.create(
            organization=self.org,
            code='COMPUTER',
            name='Computer Equipment',
            created_by=self.user
        )
        self.asset = Asset.objects.create(
            organization=self.org,
            asset_name='Test Laptop',
            asset_category=self.category,
            purchase_price=Decimal('1000.00'),
            purchase_date='2024-01-01',
            created_by=self.user
        )
        self.service = AssetStatusLogService()

    def test_log_status_change(self):
        """Test logging a status change."""
        log = self.service.log_status_change(
            asset=self.asset,
            old_status='pending',
            new_status='in_use',
            user=self.user,
            reason='Issued to employee'
        )

        self.assertIsNotNone(log.id)
        self.assertEqual(log.asset, self.asset)
        self.assertEqual(log.old_status, 'pending')
        self.assertEqual(log.new_status, 'in_use')

    def test_get_asset_history(self):
        """Test getting status change history for an asset."""
        # Create multiple status changes
        self.service.log_status_change(
            asset=self.asset,
            old_status='pending',
            new_status='in_use',
            user=self.user,
            reason='First change'
        )
        self.service.log_status_change(
            asset=self.asset,
            old_status='in_use',
            new_status='idle',
            user=self.user,
            reason='Second change'
        )

        history = self.service.get_asset_history(str(self.asset.id))

        self.assertEqual(history.count(), 2)
        self.assertEqual(history.first().new_status, 'idle')  # Most recent first
