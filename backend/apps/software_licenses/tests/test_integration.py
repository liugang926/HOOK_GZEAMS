# backend/apps/software_licenses/tests/test_integration.py

import pytest
from django.test import TestCase
from rest_framework.test import APIClient
from apps.software_licenses.models import Software, SoftwareLicense, LicenseAllocation
from apps.assets.models import Asset, AssetCategory
from apps.organizations.models import Organization
from apps.accounts.models import User


class SoftwareLicenseIntegrationTest(TestCase):
    """Software License Integration Tests"""

    def setUp(self):
        """Set up test data"""
        self.client = APIClient()
        self.unique_suffix = "int9876"

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

    def test_full_allocation_workflow(self):
        """Test full license allocation workflow"""
        # Create license
        license_response = self.client.post('/api/software-licenses/licenses/', {
            'license_no': 'LIC-WORKFLOW-001',
            'software': str(self.software.id),
            'total_units': 5,
            'purchase_date': '2026-01-01'
        }, format='json')
        self.assertEqual(license_response.status_code, 201)
        license_id = license_response.data['id']

        # Allocate to asset
        allocation_response = self.client.post('/api/software-licenses/license-allocations/', {
            'license': license_id,
            'asset': str(self.asset.id),
            'notes': 'Test allocation'
        }, format='json')
        self.assertEqual(allocation_response.status_code, 201)

        # Verify license usage increased
        license_detail = self.client.get(f'/api/software-licenses/licenses/{license_id}/')
        self.assertEqual(license_detail.data['used_units'], 1)

        # Deallocate
        dealloc_url = f"/api/software-licenses/license-allocations/{allocation_response.data['id']}/deallocate/"
        dealloc_response = self.client.post(dealloc_url, {'notes': 'Test deallocation'}, format='json')
        self.assertEqual(dealloc_response.status_code, 200)

        # Verify license usage decreased
        license_detail = self.client.get(f'/api/software-licenses/licenses/{license_id}/')
        self.assertEqual(license_detail.data['used_units'], 0)

    def test_no_available_licenses_error(self):
        """Test allocation when no licenses available"""
        # Create license with 1 unit
        license_response = self.client.post('/api/software-licenses/licenses/', {
            'license_no': 'LIC-NO-AVAIL-001',
            'software': str(self.software.id),
            'total_units': 1,
            'purchase_date': '2026-01-01'
        }, format='json')
        license_id = license_response.data['id']

        # Use up the license
        self.client.post('/api/software-licenses/license-allocations/', {
            'license': license_id,
            'asset': str(self.asset.id)
        }, format='json')

        # Try to allocate again - should fail
        second_asset = Asset.objects.create(
            organization=self.org,
            asset_code='PC002',
            asset_name='Second PC',
            asset_category=self.category,
            purchase_price=4000,
            purchase_date='2026-01-01',
            created_by=self.user
        )

        error_response = self.client.post('/api/software-licenses/license-allocations/', {
            'license': license_id,
            'asset': str(second_asset.id)
        }, format='json')
        self.assertEqual(error_response.status_code, 400)
        self.assertIn('No available licenses', str(error_response.data))

    def test_compliance_report_accuracy(self):
        """Test compliance report returns accurate data"""
        from django.utils import timezone
        from datetime import timedelta

        # Create various licenses
        SoftwareLicense.objects.create(
            organization=self.org,
            license_no='LIC-COMP-001',
            software=self.software,
            total_units=10,
            used_units=0,
            purchase_date='2026-01-01',
            status='active',
            created_by=self.user
        )

        SoftwareLicense.objects.create(
            organization=self.org,
            license_no='LIC-COMP-002',
            software=self.software,
            total_units=5,
            used_units=6,
            purchase_date='2026-01-01',
            status='active',
            created_by=self.user
        )

        SoftwareLicense.objects.create(
            organization=self.org,
            license_no='LIC-COMP-003',
            software=self.software,
            total_units=1,
            purchase_date='2026-01-01',
            expiry_date=timezone.now().date() + timedelta(days=15),
            status='active',
            created_by=self.user
        )

        response = self.client.get('/api/software-licenses/licenses/compliance_report/')

        self.assertEqual(response.status_code, 200)
        data = response.data['data']
        self.assertEqual(data['total_licenses'], 3)
        self.assertEqual(data['expiring_licenses'], 1)
        self.assertEqual(len(data['over_utilized']), 1)
        self.assertEqual(data['over_utilized'][0]['utilization'], 120.0)
