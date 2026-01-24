import pytest
from django.test import TestCase
from apps.software_licenses.models import Software, SoftwareLicense, LicenseAllocation
from apps.assets.models import Asset, AssetCategory
from apps.organizations.models import Organization
from apps.accounts.models import User


class SoftwareModelTest(TestCase):
    """Software Model Tests"""

    def setUp(self):
        """Set up test data"""
        self.unique_suffix = "test1234"
        self.org = Organization.objects.create(
            name=f'Test Organization {self.unique_suffix}',
            code=f'TESTORG_{self.unique_suffix}'
        )
        self.user = User.objects.create_user(
            username=f'testuser_{self.unique_suffix}',
            email=f'test{self.unique_suffix}@example.com',
            organization=self.org
        )

    def test_create_software(self):
        """Test creating a software catalog entry"""
        software = Software.objects.create(
            organization=self.org,
            code='WIN11',
            name='Windows 11',
            version='Pro',
            vendor='Microsoft',
            software_type='os',
            created_by=self.user
        )

        self.assertEqual(software.code, 'WIN11')
        self.assertEqual(software.name, 'Windows 11')
        self.assertEqual(software.software_type, 'os')
        self.assertTrue(software.is_active)

    def test_software_str(self):
        """Test software string representation"""
        software = Software.objects.create(
            organization=self.org,
            code='OFF365',
            name='Microsoft Office 365',
            version='2021',
            created_by=self.user
        )

        str_repr = str(software)
        self.assertIn('Microsoft Office 365', str_repr)
        self.assertIn('2021', str_repr)


class SoftwareLicenseModelTest(TestCase):
    """Software License Model Tests"""

    def setUp(self):
        """Set up test data"""
        self.unique_suffix = "test5678"
        self.org = Organization.objects.create(
            name=f'Test Organization {self.unique_suffix}',
            code=f'TESTORG_{self.unique_suffix}'
        )
        self.user = User.objects.create_user(
            username=f'testuser_{self.unique_suffix}',
            email=f'test{self.unique_suffix}@example.com',
            organization=self.org
        )

        self.software = Software.objects.create(
            organization=self.org,
            code='OFF365',
            name='Microsoft Office 365',
            version='2021',
            vendor='Microsoft',
            software_type='office',
            created_by=self.user
        )

    def test_license_utilization_rate(self):
        """Test license utilization calculation"""
        license = SoftwareLicense.objects.create(
            organization=self.org,
            license_no='LIC-001',
            software=self.software,
            total_units=10,
            used_units=7,
            purchase_date='2026-01-01',
            created_by=self.user
        )

        self.assertEqual(license.utilization_rate(), 70.0)
        self.assertEqual(license.available_units(), 3)

    def test_is_expired(self):
        """Test license expiration check"""
        from django.utils import timezone

        # Perpetual license
        perpetual_license = SoftwareLicense.objects.create(
            organization=self.org,
            license_no='LIC-002',
            software=self.software,
            total_units=1,
            purchase_date='2026-01-01',
            expiry_date=None,
            created_by=self.user
        )
        self.assertFalse(perpetual_license.is_expired())

        # Expired license
        from datetime import date
        expired_license = SoftwareLicense.objects.create(
            organization=self.org,
            license_no='LIC-003',
            software=self.software,
            total_units=1,
            purchase_date=date(2020, 1, 1),
            expiry_date=date(2023, 1, 1),
            created_by=self.user
        )
        self.assertTrue(expired_license.is_expired())


class LicenseAllocationModelTest(TestCase):
    """License Allocation Model Tests"""

    def setUp(self):
        """Set up test data"""
        self.unique_suffix = "test9012"
        self.org = Organization.objects.create(
            name=f'Test Organization {self.unique_suffix}',
            code=f'TESTORG_{self.unique_suffix}'
        )
        self.user = User.objects.create_user(
            username=f'testuser_{self.unique_suffix}',
            email=f'test{self.unique_suffix}@example.com',
            organization=self.org
        )

        self.software = Software.objects.create(
            organization=self.org,
            code='WIN11',
            name='Windows 11',
            created_by=self.user
        )

        self.license = SoftwareLicense.objects.create(
            organization=self.org,
            license_no='LIC-ALLOC-001',
            software=self.software,
            total_units=5,
            used_units=0,
            purchase_date='2026-01-01',
            created_by=self.user
        )

        self.category = AssetCategory.objects.create(
            organization=self.org,
            code='PC',
            name='Computer'
        )

        self.asset = Asset.objects.create(
            organization=self.org,
            asset_code='PC001',
            asset_name='Test PC',
            asset_category=self.category,
            purchase_price=5000,
            purchase_date='2026-01-01',
            created_by=self.user
        )

    def test_allocation_increases_usage(self):
        """Test that allocation increases license usage"""
        from django.utils import timezone

        # Get fresh reference to license from DB
        license_id = self.license.id
        initial_used = SoftwareLicense.objects.get(id=license_id).used_units

        LicenseAllocation.objects.create(
            organization=self.org,
            license_id=license_id,
            asset=self.asset,
            allocated_date=timezone.now().date(),
            allocated_by=self.user,
            created_by=self.user
        )

        # Query DB to verify the increment
        updated_used = SoftwareLicense.objects.get(id=license_id).used_units
        self.assertEqual(updated_used, initial_used + 1)

    def test_unique_allocation_constraint(self):
        """Test that duplicate allocations are prevented"""
        from django.utils import timezone
        from django.db import IntegrityError

        LicenseAllocation.objects.create(
            organization=self.org,
            license=self.license,
            asset=self.asset,
            allocated_date=timezone.now().date(),
            allocated_by=self.user,
            created_by=self.user
        )

        # Try to create duplicate
        with self.assertRaises(IntegrityError):
            LicenseAllocation.objects.create(
                organization=self.org,
                license=self.license,
                asset=self.asset,
                allocated_date=timezone.now().date(),
                allocated_by=self.user,
                created_by=self.user
            )
