import pytest
from django.test import TestCase
from rest_framework.test import APIClient
from apps.software_licenses.models import Software, SoftwareLicense, LicenseAllocation
from apps.assets.models import Asset, AssetCategory
from apps.organizations.models import Organization
from apps.accounts.models import User


class SoftwareViewSetTest(TestCase):
    """Software API Tests"""

    def setUp(self):
        """Set up test data"""
        self.client = APIClient()
        self.unique_suffix = "api1234"

        self.org = Organization.objects.create(
            name=f'Test Organization {self.unique_suffix}',
            code=f'TESTORG_{self.unique_suffix}'
        )
        self.user = User.objects.create_user(
            username=f'testuser_{self.unique_suffix}',
            email=f'test{self.unique_suffix}@example.com',
            organization=self.org
        )
        self.client.force_authenticate(user=self.user)

    def test_create_software(self):
        """Test creating software via API"""
        url = '/api/software-licenses/software/'
        data = {
            'code': 'WIN11',
            'name': 'Windows 11',
            'version': 'Pro',
            'vendor': 'Microsoft',
            'software_type': 'os'
        }

        response = self.client.post(url, data, format='json')

        # Debug: print response data if not 201
        if response.status_code != 201:
            print(f"Status: {response.status_code}")
            print(f"Response data: {response.data}")

        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data['code'], 'WIN11')

    def test_list_software(self):
        """Test listing software"""
        Software.objects.create(
            organization=self.org,
            code='TEST1',
            name='Test Software',
            created_by=self.user
        )

        url = '/api/software-licenses/software/'
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertGreaterEqual(response.data['data']['count'], 1)


class SoftwareLicenseViewSetTest(TestCase):
    """Software License API Tests"""

    def setUp(self):
        """Set up test data"""
        self.client = APIClient()
        self.unique_suffix = "lic5678"

        self.org = Organization.objects.create(
            name=f'Test Organization {self.unique_suffix}',
            code=f'TESTORG_{self.unique_suffix}'
        )
        self.user = User.objects.create_user(
            username=f'testuser_{self.unique_suffix}',
            email=f'test{self.unique_suffix}@example.com',
            organization=self.org
        )
        self.client.force_authenticate(user=self.user)

        self.software = Software.objects.create(
            organization=self.org,
            code='WIN11',
            name='Windows 11',
            version='Pro',
            created_by=self.user
        )

    def test_create_license(self):
        """Test creating software license"""
        url = '/api/software-licenses/licenses/'
        data = {
            'license_no': 'LIC-001',
            'software': str(self.software.id),
            'total_units': 10,
            'purchase_date': '2026-01-01',
            'expiry_date': '2027-01-01'
        }

        response = self.client.post(url, data, format='json')

        # Debug: print response data if not 201
        if response.status_code != 201:
            print(f"Status: {response.status_code}")
            print(f"Response data: {response.data}")

        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data['total_units'], 10)
        self.assertEqual(response.data['used_units'], 0)

    def test_expiring_endpoint(self):
        """Test expiring licenses endpoint"""
        from django.utils import timezone
        from datetime import timedelta

        # Create license expiring in 15 days
        SoftwareLicense.objects.create(
            organization=self.org,
            license_no='LIC-EXP001',
            software=self.software,
            total_units=1,
            purchase_date='2026-01-01',
            expiry_date=timezone.now().date() + timedelta(days=15),
            status='active',
            created_by=self.user
        )

        url = '/api/software-licenses/licenses/expiring/'
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertGreater(len(response.data['data']), 0)

    def test_compliance_report(self):
        """Test compliance report endpoint"""
        # Create over-utilized license
        SoftwareLicense.objects.create(
            organization=self.org,
            license_no='LIC-OVER',
            software=self.software,
            total_units=10,
            used_units=12,
            purchase_date='2026-01-01',
            status='active',
            created_by=self.user
        )

        url = '/api/software-licenses/licenses/compliance_report/'
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertGreater(len(response.data['data']['over_utilized']), 0)


class LicenseAllocationViewSetTest(TestCase):
    """License Allocation API Tests"""

    def setUp(self):
        """Set up test data"""
        self.client = APIClient()
        self.unique_suffix = "alloc9012"

        self.org = Organization.objects.create(
            name=f'Test Organization {self.unique_suffix}',
            code=f'TESTORG_{self.unique_suffix}'
        )
        self.user = User.objects.create_user(
            username=f'testuser_{self.unique_suffix}',
            email=f'test{self.unique_suffix}@example.com',
            organization=self.org
        )
        self.client.force_authenticate(user=self.user)

        self.software = Software.objects.create(
            organization=self.org,
            code='OFF365',
            name='Office 365',
            created_by=self.user
        )

        self.license = SoftwareLicense.objects.create(
            organization=self.org,
            license_no='LIC-ALLOC',
            software=self.software,
            total_units=5,
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

    def test_create_allocation(self):
        """Test creating allocation via API"""
        url = '/api/software-licenses/license-allocations/'
        data = {
            'license': str(self.license.id),
            'asset': str(self.asset.id),
            'notes': 'Test allocation'
        }

        response = self.client.post(url, data, format='json')

        # Debug: print response data if not 201
        if response.status_code != 201:
            print(f"Status: {response.status_code}")
            print(f"Response data: {response.data}")

        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data['software_name'], 'Office 365')

        # Verify license usage increased
        self.license.refresh_from_db()
        self.assertEqual(self.license.used_units, 1)

    def test_deallocate_action(self):
        """Test deallocate action"""
        # First create allocation
        from django.utils import timezone
        allocation = LicenseAllocation.objects.create(
            organization=self.org,
            license=self.license,
            asset=self.asset,
            allocated_date=timezone.now().date(),
            allocated_by=self.user,
            created_by=self.user
        )

        url = f'/api/software-licenses/license-allocations/{allocation.id}/deallocate/'
        response = self.client.post(url, {'notes': 'No longer needed'}, format='json')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['success'], True)

        # Verify license usage decreased
        self.license.refresh_from_db()
        self.assertEqual(self.license.used_units, 0)

    def test_no_available_licenses_error(self):
        """Test allocation when no licenses available"""
        # Use up all licenses via direct DB update
        SoftwareLicense.objects.filter(id=self.license.id).update(
            used_units=self.license.total_units
        )

        # Verify the update worked
        self.license.refresh_from_db()
        print(f"License total_units: {self.license.total_units}, used_units: {self.license.used_units}")
        print(f"Available units: {self.license.available_units()}")

        url = '/api/software-licenses/license-allocations/'
        data = {
            'license': str(self.license.id),
            'asset': str(self.asset.id)
        }

        response = self.client.post(url, data, format='json')

        self.assertEqual(response.status_code, 400)
        # Check error is in details
        self.assertIn('No available licenses', str(response.data))
