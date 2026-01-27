"""
Tests for Asset, Supplier, Location, and AssetStatusLog models.

Tests cover:
- BaseModel inheritance compliance
- Asset model functionality (code generation, QR code, properties)
- Supplier model functionality
- Location model tree structure
- AssetStatusLog model functionality
"""
import uuid
from django.test import TestCase
from django.core.exceptions import ValidationError
from decimal import Decimal
from apps.assets.models import (
    Asset,
    Supplier,
    Location,
    AssetStatusLog,
    AssetCategory
)
from apps.organizations.models import Organization, Department
from apps.accounts.models import User


class AssetModelTest(TestCase):
    """Test Asset model functionality."""

    def setUp(self):
        """Set up test data with unique codes."""
        # Generate unique suffix for this test run
        self.unique_suffix = uuid.uuid4().hex[:8]

        self.org = Organization.objects.create(
            name=f'Test Organization {self.unique_suffix}',
            code=f'TEST_ORG_{self.unique_suffix}'
        )
        self.user = User.objects.create_user(
            username=f'testuser_{self.unique_suffix}',
            email=f'test{self.unique_suffix}@example.com',
            organization=self.org
        )
        self.category = AssetCategory.objects.create(
            organization=self.org,
            code=f'COMPUTER_{self.unique_suffix}',
            name='Computer Equipment',
            created_by=self.user
        )
        self.department = Department.objects.create(
            organization=self.org,
            name='IT Department',
            code=f'IT_{self.unique_suffix}'
        )
        self.supplier = Supplier.objects.create(
            organization=self.org,
            code=f'DELL_{self.unique_suffix}',
            name='Dell Inc.',
            created_by=self.user
        )
        self.location = Location.objects.create(
            organization=self.org,
            name='Server Room',
            location_type='room',
            created_by=self.user
        )

    def test_create_asset_minimal(self):
        """Test creating an asset with minimal required fields."""
        asset = Asset.objects.create(
            organization=self.org,
            asset_name='Test Laptop',
            asset_category=self.category,
            purchase_price=Decimal('1000.00'),
            purchase_date='2024-01-01',
            created_by=self.user
        )

        self.assertIsNotNone(asset.asset_code)
        self.assertTrue(asset.asset_code.startswith('ZC'))
        self.assertIsNotNone(asset.qr_code)
        self.assertEqual(asset.asset_name, 'Test Laptop')
        self.assertEqual(asset.asset_status, 'pending')

    def test_asset_code_generation(self):
        """Test automatic asset code generation."""
        asset1 = Asset.objects.create(
            organization=self.org,
            asset_name='Asset 1',
            asset_category=self.category,
            purchase_price=Decimal('1000.00'),
            purchase_date='2024-01-01',
            created_by=self.user
        )
        asset2 = Asset.objects.create(
            organization=self.org,
            asset_name='Asset 2',
            asset_category=self.category,
            purchase_price=Decimal('2000.00'),
            purchase_date='2024-01-01',
            created_by=self.user
        )

        self.assertRegex(asset1.asset_code, r'ZC\d{8}\d{4}')
        self.assertRegex(asset2.asset_code, r'ZC\d{8}\d{4}')

        # Second asset should have higher sequence
        seq1 = int(asset1.asset_code[-4:])
        seq2 = int(asset2.asset_code[-4:])
        self.assertEqual(seq2, seq1 + 1)

    def test_qr_code_generation(self):
        """Test automatic QR code generation."""
        asset = Asset.objects.create(
            organization=self.org,
            asset_name='Test Asset',
            asset_category=self.category,
            purchase_price=Decimal('1000.00'),
            purchase_date='2024-01-01',
            created_by=self.user
        )

        self.assertIsNotNone(asset.qr_code)
        self.assertEqual(len(asset.qr_code), 36)  # UUID length

    def test_depreciation_start_date_default(self):
        """Test depreciation_start_date defaults to purchase_date."""
        asset = Asset.objects.create(
            organization=self.org,
            asset_name='Test Asset',
            asset_category=self.category,
            purchase_price=Decimal('1000.00'),
            purchase_date='2024-01-15',
            created_by=self.user
        )

        self.assertEqual(
            asset.depreciation_start_date,
            asset.purchase_date
        )

    def test_net_value_property(self):
        """Test net_value calculated property."""
        asset = Asset.objects.create(
            organization=self.org,
            asset_name='Test Asset',
            asset_category=self.category,
            purchase_price=Decimal('10000.00'),
            accumulated_depreciation=Decimal('2000.00'),
            purchase_date='2024-01-01',
            created_by=self.user
        )

        self.assertEqual(asset.net_value, 8000.00)

    def test_residual_value_property(self):
        """Test residual_value calculated property."""
        asset = Asset.objects.create(
            organization=self.org,
            asset_name='Test Asset',
            asset_category=self.category,
            purchase_price=Decimal('10000.00'),
            residual_rate=Decimal('5.00'),
            purchase_date='2024-01-01',
            created_by=self.user
        )

        self.assertEqual(asset.residual_value, 500.00)

    def test_get_status_label(self):
        """Test get_status_label method."""
        asset = Asset.objects.create(
            organization=self.org,
            asset_name='Test Asset',
            asset_category=self.category,
            purchase_price=Decimal('1000.00'),
            asset_status='in_use',
            purchase_date='2024-01-01',
            created_by=self.user
        )

        label = asset.get_status_label()
        self.assertEqual(label, 'In Use')



    def test_asset_with_all_fields(self):
        """Test creating an asset with all fields populated."""
        asset = Asset.objects.create(
            organization=self.org,
            asset_name='Dell Latitude 7420',
            asset_category=self.category,
            specification='i7-1165G7, 16GB RAM, 512GB SSD',
            brand='Dell',
            model='Latitude 7420',
            unit='台',
            serial_number='DL123456789',
            purchase_price=Decimal('15000.00'),
            current_value=Decimal('12000.00'),
            accumulated_depreciation=Decimal('3000.00'),
            purchase_date='2024-01-01',
            depreciation_start_date='2024-02-01',
            useful_life=60,
            residual_rate=Decimal('5.00'),
            supplier=self.supplier,
            supplier_order_no='PO-2024-001',
            invoice_no='INV-2024-001',
            department=self.department,
            location=self.location,
            custodian=self.user,
            asset_status='in_use',
            rfid_code='RFID123456',
            images=['image1.jpg', 'image2.jpg'],
            attachments=['manual.pdf'],
            remarks='Test asset with all fields',
            created_by=self.user
        )

        self.assertEqual(asset.brand, 'Dell')
        self.assertEqual(asset.model, 'Latitude 7420')
        self.assertEqual(asset.serial_number, 'DL123456789')
        self.assertEqual(asset.supplier, self.supplier)
        self.assertEqual(asset.department, self.department)
        self.assertEqual(asset.location, self.location)
        self.assertEqual(asset.custodian, self.user)
        self.assertEqual(asset.rfid_code, 'RFID123456')
        self.assertEqual(len(asset.images), 2)


class SupplierModelTest(TestCase):
    """Test Supplier model functionality."""

    def setUp(self):
        """Set up test data with unique codes."""
        self.unique_suffix = uuid.uuid4().hex[:8]
        self.org = Organization.objects.create(
            name=f'Test Organization {self.unique_suffix}',
            code=f'TEST_ORG_{self.unique_suffix}'
        )
        self.user = User.objects.create_user(
            username=f'testuser_{self.unique_suffix}',
            email=f'test{self.unique_suffix}@example.com',
            organization=self.org
        )

    def test_create_supplier(self):
        """Test creating a supplier."""
        supplier = Supplier.objects.create(
            organization=self.org,
            code='DELL',
            name='Dell Inc.',
            contact='John Doe',
            phone='123-456-7890',
            email='sales@dell.com',
            address='123 Dell Way, Round Rock, TX',
            created_by=self.user
        )

        self.assertEqual(supplier.code, 'DELL')
        self.assertEqual(supplier.name, 'Dell Inc.')
        self.assertEqual(supplier.contact, 'John Doe')

    def test_supplier_base_model_fields(self):
        """Test Supplier has all BaseModel fields."""
        supplier = Supplier.objects.create(
            organization=self.org,
            code='HP',
            name='HP Inc.',
            created_by=self.user
        )

        self.assertIsNotNone(supplier.id)
        self.assertIsNotNone(supplier.created_at)
        self.assertEqual(supplier.organization, self.org)
        self.assertEqual(supplier.created_by, self.user)
        self.assertFalse(supplier.is_deleted)


class LocationModelTest(TestCase):
    """Test Location model functionality."""

    def setUp(self):
        """Set up test data with unique codes."""
        self.unique_suffix = uuid.uuid4().hex[:8]
        self.org = Organization.objects.create(
            name=f'Test Organization {self.unique_suffix}',
            code=f'TEST_ORG_{self.unique_suffix}'
        )
        self.user = User.objects.create_user(
            username=f'testuser_{self.unique_suffix}',
            email=f'test{self.unique_suffix}@example.com',
            organization=self.org
        )

    def test_create_root_location(self):
        """Test creating a root location."""
        location = Location.objects.create(
            organization=self.org,
            name='Building A',
            location_type='building',
            created_by=self.user
        )

        self.assertEqual(location.name, 'Building A')
        self.assertIsNone(location.parent)
        self.assertEqual(location.level, 0)
        self.assertEqual(location.path, 'Building A')

    def test_create_child_location(self):
        """Test creating a child location."""
        parent = Location.objects.create(
            organization=self.org,
            name='Building A',
            location_type='building',
            created_by=self.user
        )
        child = Location.objects.create(
            organization=self.org,
            name='Floor 1',
            parent=parent,
            location_type='floor',
            created_by=self.user
        )

        self.assertEqual(child.parent, parent)
        self.assertEqual(child.level, 1)
        self.assertEqual(child.path, 'Building A / Floor 1')

    def test_nested_location_path(self):
        """Test nested location path generation."""
        building = Location.objects.create(
            organization=self.org,
            name='Building A',
            location_type='building',
            created_by=self.user
        )
        floor = Location.objects.create(
            organization=self.org,
            name='Floor 1',
            parent=building,
            location_type='floor',
            created_by=self.user
        )
        room = Location.objects.create(
            organization=self.org,
            name='Room 101',
            parent=floor,
            location_type='room',
            created_by=self.user
        )

        self.assertEqual(room.path, 'Building A / Floor 1 / Room 101')
        self.assertEqual(room.level, 2)

    def test_all_location_type_choices(self):
        """Test all location type choices are available."""
        location_type_choices = [
            choice[0] for choice in Location.LOCATION_TYPE_CHOICES
        ]
        expected_types = [
            'building', 'floor', 'room', 'area',
            'warehouse', 'other'
        ]
        for location_type in expected_types:
            self.assertIn(location_type, location_type_choices)


class AssetStatusLogModelTest(TestCase):
    """Test AssetStatusLog model functionality."""

    def setUp(self):
        """Set up test data with unique codes."""
        self.unique_suffix = uuid.uuid4().hex[:8]
        self.org = Organization.objects.create(
            name=f'Test Organization {self.unique_suffix}',
            code=f'TEST_ORG_{self.unique_suffix}'
        )
        self.user = User.objects.create_user(
            username=f'testuser_{self.unique_suffix}',
            email=f'test{self.unique_suffix}@example.com',
            organization=self.org
        )
        self.category = AssetCategory.objects.create(
            organization=self.org,
            code=f'COMPUTER_{self.unique_suffix}',
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

    def test_create_status_log(self):
        """Test creating a status log entry."""
        log = AssetStatusLog.objects.create(
            organization=self.org,
            asset=self.asset,
            old_status='pending',
            new_status='in_use',
            reason='Issued to employee',
            created_by=self.user
        )

        self.assertEqual(log.asset, self.asset)
        self.assertEqual(log.old_status, 'pending')
        self.assertEqual(log.new_status, 'in_use')
        self.assertEqual(log.reason, 'Issued to employee')

    def test_status_log_str_representation(self):
        """Test status log string representation."""
        log = AssetStatusLog.objects.create(
            organization=self.org,
            asset=self.asset,
            old_status='pending',
            new_status='in_use',
            created_by=self.user
        )

        str_repr = str(log)
        self.assertIn(self.asset.asset_code, str_repr)
        self.assertIn('pending', str_repr)
        self.assertIn('in_use', str_repr)


class AssetRelationsTest(TestCase):
    """Test Asset model relationships with other models."""

    def setUp(self):
        """Set up test data with unique codes."""
        self.unique_suffix = uuid.uuid4().hex[:8]
        self.org = Organization.objects.create(
            name=f'Test Organization {self.unique_suffix}',
            code=f'TEST_ORG_{self.unique_suffix}'
        )
        self.user = User.objects.create_user(
            username=f'testuser_{self.unique_suffix}',
            email=f'test{self.unique_suffix}@example.com',
            organization=self.org
        )
        self.category = AssetCategory.objects.create(
            organization=self.org,
            code=f'COMPUTER_{self.unique_suffix}',
            name='Computer Equipment',
            created_by=self.user
        )

    def test_asset_category_relation(self):
        """Test Asset-AssetCategory relationship."""
        asset = Asset.objects.create(
            organization=self.org,
            asset_name='Test Laptop',
            asset_category=self.category,
            purchase_price=Decimal('1000.00'),
            purchase_date='2024-01-01',
            created_by=self.user
        )

        self.assertEqual(asset.asset_category, self.category)
        self.assertIn(asset, self.category.assets.all())

    def test_asset_status_logs_relation(self):
        """Test Asset-AssetStatusLog relationship."""
        asset = Asset.objects.create(
            organization=self.org,
            asset_name='Test Laptop',
            asset_category=self.category,
            purchase_price=Decimal('1000.00'),
            purchase_date='2024-01-01',
            created_by=self.user
        )

        log = AssetStatusLog.objects.create(
            organization=self.org,
            asset=asset,
            old_status='pending',
            new_status='in_use',
            created_by=self.user
        )

        self.assertIn(log, asset.status_logs.all())
        self.assertEqual(asset.status_logs.count(), 1)
