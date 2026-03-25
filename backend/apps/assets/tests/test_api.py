"""
Tests for AssetCategory, Asset, and Operation API endpoints.

IMPORTANT: Due to multi-tenant organization isolation using thread-local storage,
each test creates a fresh APIClient instance to ensure proper organization context.
"""
import uuid
import pytest
from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APITestCase, APIClient, APITransactionTestCase
from rest_framework import status
from decimal import Decimal
from datetime import date, timedelta
from apps.assets.models import (
    AssetCategory, Asset, Supplier, Location,
    AssetPickup, PickupItem, AssetTransfer, AssetReturn, AssetLoan
)
from apps.organizations.models import Organization, Department
from apps.accounts.models import User
from apps.projects.models import AssetProject, ProjectAsset


class AssetCategoryAPITest(APITestCase):
    """Test AssetCategory API endpoints."""

    def setUp(self):
        """Set up test data with unique codes."""
        self.unique_suffix = uuid.uuid4().hex[:8]
        self.org = Organization.objects.create(
            name=f'Test Organization {self.unique_suffix}',
            code=f'TEST_ORG_CAT_{self.unique_suffix}'
        )
        self.user = User.objects.create_user(
            username=f'testuser_{self.unique_suffix}',
            email=f'test{self.unique_suffix}@example.com',
            password='testpass123',
            organization=self.org
        )

        # Create test categories
        self.parent = AssetCategory.objects.create(
            organization=self.org,
            code=f'ELECTRONICS_{self.unique_suffix}',
            name='Electronics',
            created_by=self.user
        )
        self.child = AssetCategory.objects.create(
            organization=self.org,
            code=f'COMPUTERS_{self.unique_suffix}',
            name='Computers',
            parent=self.parent,
            created_by=self.user
        )

    def _make_client(self):
        """Create a fresh API client for each request."""
        client = APIClient()
        client.force_authenticate(user=self.user)
        client.credentials(HTTP_X_ORGANIZATION_ID=str(self.org.id))
        return client

    def tearDown(self):
        """Clean up after each test."""
        # Clear thread-local organization context
        from apps.common.middleware import clear_current_organization
        clear_current_organization()
        # Call parent tearDown for proper Django TestCase cleanup
        super().tearDown()

    def test_list_categories(self):
        """Test GET /api/assets/categories/"""
        url = '/api/assets/categories/'
        client = self._make_client()
        response = client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # List endpoint uses standard pagination format wrapped in BaseResponse
        self.assertTrue(response.data['success'])
        self.assertIn('count', response.data['data'])

    def test_retrieve_category(self):
        """Test GET /api/assets/categories/{id}/"""
        url = f'/api/assets/categories/{self.parent.id}/'
        client = self._make_client()
        response = client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        self.assertEqual(response.data['data']['code'], f'ELECTRONICS_{self.unique_suffix}')

    def test_create_category(self):
        """Test POST /api/assets/categories/"""
        url = '/api/assets/categories/'
        data = {
            'code': f'FURNITURE_{uuid.uuid4().hex[:8].upper()}',
            'name': 'Furniture',
            'depreciation_method': 'straight_line',
            'default_useful_life': 120,
            'residual_rate': 5.00
        }
        client = self._make_client()
        response = client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(response.data['success'])

    def test_update_category(self):
        """Test PUT /api/assets/categories/{id}/"""
        url = f'/api/assets/categories/{self.parent.id}/'
        data = {
            'code': f'ELECTRONICS_{self.unique_suffix}',
            'name': 'Electronics Updated',
            'depreciation_method': 'double_declining',
            'default_useful_life': 48,
            'residual_rate': 10.00
        }
        client = self._make_client()
        response = client.put(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        self.assertEqual(response.data['data']['name'], 'Electronics Updated')

    def test_delete_category(self):
        """Test DELETE /api/assets/categories/{id}/ (soft delete)"""
        url = f'/api/assets/categories/{self.child.id}/'
        client = self._make_client()
        response = client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

        # Verify soft delete
        self.child.refresh_from_db()
        self.assertTrue(self.child.is_deleted)

    def test_tree_endpoint(self):
        """Test GET /api/assets/categories/tree/"""
        url = '/api/assets/categories/tree/'
        client = self._make_client()
        response = client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        self.assertIsInstance(response.data['data'], list)

    def test_category_path_endpoint(self):
        """Test GET /api/assets/categories/{id}/path/"""
        url = f'/api/assets/categories/{self.child.id}/path/'
        client = self._make_client()
        response = client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        self.assertIsInstance(response.data['data'], list)
        # Verify path has 2 items (parent -> child)
        self.assertEqual(len(response.data['data']), 2)
        # Verify path order is root to leaf
        self.assertEqual(response.data['data'][0]['code'], f'ELECTRONICS_{self.unique_suffix}')
        self.assertEqual(response.data['data'][1]['code'], f'COMPUTERS_{self.unique_suffix}')

    def test_add_child_action(self):
        """Test POST /api/assets/categories/{id}/add_child/"""
        url = f'/api/assets/categories/{self.parent.id}/add_child/'
        data = {
            'code': f'PHONES_{uuid.uuid4().hex[:8].upper()}',
            'name': 'Phones',
            'depreciation_method': 'straight_line'
        }
        client = self._make_client()
        response = client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(response.data['success'])

        # Verify child was created
        children = AssetCategory.objects.filter(parent=self.parent, is_deleted=False)
        self.assertGreaterEqual(children.count(), 2)

    def test_filter_by_code(self):
        """Test filtering categories by code."""
        url = '/api/assets/categories/?code=ELECT'
        client = self._make_client()
        response = client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_search_filter(self):
        """Test searching categories."""
        url = '/api/assets/categories/?search=Elect'
        client = self._make_client()
        response = client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)


class AssetAPITest(APITestCase):
    """Test Asset API endpoints."""

    def setUp(self):
        """Set up test data with unique codes."""
        self.client = APIClient()
        self.unique_suffix = uuid.uuid4().hex[:8]
        self.org = Organization.objects.create(
            name=f'Test Organization {self.unique_suffix}',
            code=f'TEST_ORG_ASSET_{self.unique_suffix}'
        )
        self.user = User.objects.create_user(
            username=f'testuser_{self.unique_suffix}',
            email=f'test{self.unique_suffix}@example.com',
            password='testpass123',
            organization=self.org
        )
        self.client.force_authenticate(user=self.user)
        self.client.credentials(HTTP_X_ORGANIZATION_ID=str(self.org.id))

        # Create test category
        self.category = AssetCategory.objects.create(
            organization=self.org,
            code=f'COMPUTER_{self.unique_suffix}',
            name='Computer Equipment',
            created_by=self.user
        )

        # Create test department
        self.department = Department.objects.create(
            organization=self.org,
            name='IT Department',
            code=f'IT_{self.unique_suffix}'
        )

        # Create test location
        self.location = Location.objects.create(
            organization=self.org,
            name='Server Room',
            location_type='room',
            created_by=self.user
        )

        # Create test supplier
        self.supplier = Supplier.objects.create(
            organization=self.org,
            code=f'DELL_{self.unique_suffix}',
            name='Dell Inc.',
            created_by=self.user
        )

    def test_list_assets(self):
        """Test GET /api/assets/"""
        Asset.objects.create(
            organization=self.org,
            asset_name='Test Laptop',
            asset_category=self.category,
            department=self.department,
            location=self.location,
            custodian=self.user,
            purchase_price=Decimal('1000.00'),
            purchase_date='2024-01-01',
            created_by=self.user
        )

        url = '/api/assets/'
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Standard pagination format wrapped in BaseResponse
        self.assertIn('count', response.data['data'])
        first = response.data['data']['results'][0]
        self.assertEqual(str(first['department']), str(self.department.id))
        self.assertEqual(str(first['location']), str(self.location.id))
        self.assertEqual(str(first['custodian']), str(self.user.id))
        self.assertEqual(first['department_name'], self.department.name)
        self.assertEqual(first['location_path'], self.location.path)
        self.assertEqual(first['custodian_username'], self.user.username)

    def test_create_asset(self):
        """Test POST /api/assets/"""
        url = '/api/assets/'
        data = {
            'asset_name': 'Dell Laptop',
            'asset_category': str(self.category.id),
            'specification': 'i7-1165G7, 16GB RAM',
            'brand': 'Dell',
            'model': 'Latitude 7420',
            'purchase_price': '15000.00',
            'purchase_date': '2024-01-01',
            'supplier': str(self.supplier.id),
            'department': str(self.department.id),
            'location': str(self.location.id),
        }
        response = self.client.post(url, data, format='json')
        if response.status_code != status.HTTP_201_CREATED:
            print(f"DEBUG Response Status: {response.status_code}")
            print(f"DEBUG Response Data: {response.data}")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(response.data['success'])
        self.assertIn('asset_code', response.data['data'])
        self.assertIn('qr_code', response.data['data'])

    def test_retrieve_asset(self):
        """Test GET /api/assets/{id}/"""
        asset = Asset.objects.create(
            organization=self.org,
            asset_name='Test Laptop',
            asset_category=self.category,
            purchase_price=Decimal('1000.00'),
            purchase_date='2024-01-01',
            created_by=self.user
        )

        url = f'/api/assets/{asset.id}/'
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        self.assertEqual(response.data['data']['asset_name'], 'Test Laptop')

    def test_update_asset(self):
        """Test PUT /api/assets/{id}/"""
        asset = Asset.objects.create(
            organization=self.org,
            asset_name='Test Laptop',
            asset_category=self.category,
            purchase_price=Decimal('1000.00'),
            purchase_date='2024-01-01',
            created_by=self.user
        )

        url = f'/api/assets/{asset.id}/'
        data = {
            'asset_name': 'Updated Laptop',
            'asset_category': str(self.category.id),
            'purchase_price': '15000.00',
            'purchase_date': '2024-01-01',
        }
        response = self.client.put(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['data']['asset_name'], 'Updated Laptop')

    def test_update_asset_accepts_expanded_reference_objects(self):
        """PUT should accept expanded relation objects and coerce them to IDs."""
        asset = Asset.objects.create(
            organization=self.org,
            asset_name='Reference Payload Laptop',
            asset_category=self.category,
            supplier=self.supplier,
            location=self.location,
            custodian=self.user,
            purchase_price=Decimal('1000.00'),
            purchase_date='2024-01-01',
            created_by=self.user
        )

        url = f'/api/assets/{asset.id}/'
        data = {
            'asset_name': 'Reference Payload Laptop Updated',
            'asset_category': {
                'id': str(self.category.id),
                'code': self.category.code,
                'name': self.category.name
            },
            'supplier': {
                'id': str(self.supplier.id),
                'code': self.supplier.code,
                'name': self.supplier.name
            },
            'location': {
                'id': str(self.location.id),
                'name': self.location.name
            },
            'custodian': {
                'id': str(self.user.id),
                'username': self.user.username
            },
            'purchase_price': '1200.00',
            'purchase_date': '2024-01-01',
        }

        response = self.client.put(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        self.assertEqual(response.data['data']['asset_name'], 'Reference Payload Laptop Updated')

    def test_delete_asset(self):
        """Test DELETE /api/assets/{id}/ (soft delete)"""
        asset = Asset.objects.create(
            organization=self.org,
            asset_name='Test Laptop',
            asset_category=self.category,
            purchase_price=Decimal('1000.00'),
            purchase_date='2024-01-01',
            created_by=self.user
        )

        url = f'/api/assets/{asset.id}/'
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Verify soft delete
        asset.refresh_from_db()
        self.assertTrue(asset.is_deleted)

    def test_change_status(self):
        """Test POST /api/assets/{id}/change-status/"""
        asset = Asset.objects.create(
            organization=self.org,
            asset_name='Test Laptop',
            asset_category=self.category,
            purchase_price=Decimal('1000.00'),
            purchase_date='2024-01-01',
            asset_status='pending',
            created_by=self.user
        )

        url = f'/api/assets/{asset.id}/change-status/'
        data = {
            'new_status': 'in_use',
            'reason': 'Issued to employee'
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Verify status changed
        asset.refresh_from_db()
        self.assertEqual(asset.asset_status, 'in_use')

    def test_statistics_endpoint(self):
        """Test GET /api/assets/statistics/"""
        Asset.objects.create(
            organization=self.org,
            asset_name='Asset 1',
            asset_category=self.category,
            purchase_price=Decimal('10000.00'),
            asset_status='in_use',
            purchase_date='2024-01-01',
            created_by=self.user
        )

        url = '/api/assets/statistics/'
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        self.assertIn('total', response.data['data'])

    def test_filter_by_status(self):
        """Test filtering assets by status."""
        Asset.objects.create(
            organization=self.org,
            asset_name='Asset 1',
            asset_category=self.category,
            purchase_price=Decimal('1000.00'),
            asset_status='in_use',
            purchase_date='2024-01-01',
            created_by=self.user
        )
        Asset.objects.create(
            organization=self.org,
            asset_name='Asset 2',
            asset_category=self.category,
            purchase_price=Decimal('2000.00'),
            asset_status='idle',
            purchase_date='2024-01-01',
            created_by=self.user
        )

        url = '/api/assets/?asset_status=in_use'
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Should only return in_use assets

    def test_search_assets(self):
        """Test searching assets."""
        Asset.objects.create(
            organization=self.org,
            asset_name='Dell Laptop',
            asset_category=self.category,
            brand='Dell',
            purchase_price=Decimal('1000.00'),
            purchase_date='2024-01-01',
            created_by=self.user
        )
        Asset.objects.create(
            organization=self.org,
            asset_name='HP Desktop',
            asset_category=self.category,
            brand='HP',
            purchase_price=Decimal('800.00'),
            purchase_date='2024-01-01',
            created_by=self.user
        )

        url = '/api/assets/?search=Dell'
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Should only return Dell assets

    def test_status_history(self):
        """Test GET /api/assets/{id}/status-history/"""
        asset = Asset.objects.create(
            organization=self.org,
            asset_name='Test Laptop',
            asset_category=self.category,
            purchase_price=Decimal('1000.00'),
            purchase_date='2024-01-01',
            asset_status='pending',
            created_by=self.user
        )

        url = f'/api/assets/{asset.id}/status-history/'
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_get_asset_qr_code(self):
        """Test GET /api/assets/{id}/qr_code/ - Get asset QR code image."""
        asset = Asset.objects.create(
            organization=self.org,
            asset_name='Test Laptop',
            asset_category=self.category,
            purchase_price=Decimal('1000.00'),
            purchase_date='2024-01-01',
            asset_status='pending',
            created_by=self.user
        )

        url = f'/api/assets/{asset.id}/qr_code/'
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response['Content-Type'], 'image/png')
        # Verify image data is returned
        self.assertGreater(len(response.content), 0)

    def test_batch_change_status(self):
        """Test POST /api/assets/batch_change_status/ - Batch change asset status."""
        unique_suffix = uuid.uuid4().hex[:8]

        assets = []
        for i in range(3):
            asset = Asset.objects.create(
                organization=self.org,
                asset_category=self.category,
                asset_code=f"AST-{unique_suffix}-{i}",
                asset_name=f"Test Asset {i}",
                purchase_price=Decimal('10000.00'),
                purchase_date='2024-01-01',
                asset_status='in_use',
                created_by=self.user
            )
            assets.append(asset)

        url = '/api/assets/batch_change_status/'
        data = {
            'ids': [str(a.id) for a in assets],
            'new_status': 'maintenance'
        }
        response = self.client.post(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['summary']['succeeded'], 3)

        # Verify all assets updated
        for asset in assets:
            asset.refresh_from_db()
            self.assertEqual(asset.asset_status, 'maintenance')

    def test_bulk_qr_codes_success(self):
        """Test bulk QR code generation."""
        unique_suffix = uuid.uuid4().hex[:8]

        asset1 = Asset.objects.create(
            organization=self.org,
            asset_category=self.category,
            asset_code=f'TEST{unique_suffix}001',
            asset_name='Test Asset 1',
            purchase_price=Decimal('1000.00'),
            purchase_date='2024-01-01',
            created_by=self.user
        )
        asset2 = Asset.objects.create(
            organization=self.org,
            asset_category=self.category,
            asset_code=f'TEST{unique_suffix}002',
            asset_name='Test Asset 2',
            purchase_price=Decimal('2000.00'),
            purchase_date='2024-01-01',
            created_by=self.user
        )

        url = '/api/assets/bulk-qr-codes/'
        data = {'ids': [str(asset1.id), str(asset2.id)]}
        response = self.client.post(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response['Content-Type'], 'application/zip')
        self.assertIn('attachment', response['Content-Disposition'])
        # Verify ZIP file content is returned
        self.assertGreater(len(response.content), 0)

    def test_bulk_qr_codes_empty_ids(self):
        """Test bulk QR code generation with empty ids array."""
        url = '/api/assets/bulk-qr-codes/'
        data = {'ids': []}
        response = self.client.post(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(response.data['success'])
        self.assertEqual(response.data['error']['code'], 'VALIDATION_ERROR')
        self.assertIn('cannot be empty', response.data['error']['message'])

    def test_bulk_qr_codes_invalid_type(self):
        """Test bulk QR code generation with invalid ids type (not a list)."""
        url = '/api/assets/bulk-qr-codes/'
        data = {'ids': 'not-a-list'}  # String instead of list
        response = self.client.post(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(response.data['success'])
        self.assertEqual(response.data['error']['code'], 'VALIDATION_ERROR')
        self.assertIn('must be a list', response.data['error']['message'])

    def test_bulk_qr_codes_too_many_ids(self):
        """Test bulk QR code generation with too many ids (> 1000)."""
        # Generate 1001 asset IDs (exceeds MAX_BULK_QR_LIMIT)
        url = '/api/assets/bulk-qr-codes/'
        too_many_ids = [str(uuid.uuid4()) for _ in range(1001)]
        data = {'ids': too_many_ids}
        response = self.client.post(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(response.data['success'])
        self.assertEqual(response.data['error']['code'], 'VALIDATION_ERROR')
        self.assertIn('Cannot generate more than', response.data['error']['message'])

    def test_bulk_qr_codes_filename_sanitization(self):
        """Test that asset codes with invalid characters are sanitized in filenames."""
        unique_suffix = uuid.uuid4().hex[:8]

        # Create asset with code containing invalid filename characters
        asset = Asset.objects.create(
            organization=self.org,
            asset_category=self.category,
            asset_code=f'TEST{unique_suffix}<>:"/\\|?*001',  # Invalid filename chars
            asset_name='Test Asset',
            purchase_price=Decimal('1000.00'),
            purchase_date='2024-01-01',
            created_by=self.user
        )

        url = '/api/assets/bulk-qr-codes/'
        data = {'ids': [str(asset.id)]}
        response = self.client.post(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response['Content-Type'], 'application/zip')
        # Verify ZIP file is generated successfully (sanitization worked)
        self.assertGreater(len(response.content), 0)

    def tearDown(self):
        """Clean up after each test."""
        # Clear thread-local organization context
        from apps.common.middleware import clear_current_organization
        clear_current_organization()
        # Call parent tearDown for proper Django TestCase cleanup
        super().tearDown()


class SupplierAPITest(APITestCase):
    """Test Supplier API endpoints."""

    def setUp(self):
        """Set up test data with unique codes."""
        self.client = APIClient()
        self.unique_suffix = uuid.uuid4().hex[:8]
        self.org = Organization.objects.create(
            name=f'Test Organization {self.unique_suffix}',
            code=f'TEST_ORG_SUPP_{self.unique_suffix}'
        )
        self.user = User.objects.create_user(
            username=f'testuser_{self.unique_suffix}',
            email=f'test{self.unique_suffix}@example.com',
            password='testpass123',
            organization=self.org
        )
        self.client.force_authenticate(user=self.user)
        self.client.credentials(HTTP_X_ORGANIZATION_ID=str(self.org.id))

    def test_create_supplier(self):
        """Test POST /api/assets/suppliers/"""
        url = '/api/assets/suppliers/'
        data = {
            'code': f'DELL_{uuid.uuid4().hex[:8].upper()}',
            'name': 'Dell Inc.',
            'contact': 'John Doe',
            'phone': '123-456-7890',
            'email': 'sales@dell.com'
        }
        response = self.client.post(url, data, format='json')
        if response.status_code != status.HTTP_201_CREATED:
            print(f"DEBUG Response Status: {response.status_code}")
            print(f"DEBUG Response Data: {response.data}")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_list_suppliers(self):
        """Test GET /api/assets/suppliers/"""
        Supplier.objects.create(
            organization=self.org,
            code=f'DELL_{uuid.uuid4().hex[:8].upper()}',
            name='Dell Inc.',
            created_by=self.user
        )

        url = '/api/assets/suppliers/'
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def tearDown(self):
        """Clean up after each test."""
        # Clear thread-local organization context
        from apps.common.middleware import clear_current_organization
        clear_current_organization()
        # Call parent tearDown for proper Django TestCase cleanup
        super().tearDown()


class LocationAPITest(APITestCase):
    """Test Location API endpoints."""

    def setUp(self):
        """Set up test data with unique codes."""
        self.client = APIClient()
        self.unique_suffix = uuid.uuid4().hex[:8]
        self.org = Organization.objects.create(
            name=f'Test Organization {self.unique_suffix}',
            code=f'TEST_ORG_LOC_{self.unique_suffix}'
        )
        self.user = User.objects.create_user(
            username=f'testuser_{self.unique_suffix}',
            email=f'test{self.unique_suffix}@example.com',
            password='testpass123',
            organization=self.org
        )
        self.client.force_authenticate(user=self.user)
        self.client.credentials(HTTP_X_ORGANIZATION_ID=str(self.org.id))

    def test_create_location(self):
        """Test POST /api/assets/locations/"""
        url = '/api/assets/locations/'
        data = {
            'name': 'Building A',
            'location_type': 'building'
        }
        response = self.client.post(url, data, format='json')
        if response.status_code != status.HTTP_201_CREATED:
            print(f"DEBUG Response Status: {response.status_code}")
            print(f"DEBUG Response Data: {response.data}")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_tree_endpoint(self):
        """Test GET /api/assets/locations/tree/"""
        Location.objects.create(
            organization=self.org,
            name='Building A',
            location_type='building',
            created_by=self.user
        )

        url = '/api/assets/locations/tree/'
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        self.assertIsInstance(response.data['data'], list)

    def tearDown(self):
        """Clean up after each test."""
        # Clear thread-local organization context
        from apps.common.middleware import clear_current_organization
        clear_current_organization()
        # Call parent tearDown for proper Django TestCase cleanup
        super().tearDown()


# ========== Operation API Tests ==========


class AssetPickupAPITest(APITransactionTestCase):
    """Test Asset Pickup API endpoints."""

    def setUp(self):
        """Set up test data with unique codes."""
        from apps.common.middleware import clear_current_organization, set_current_organization

        clear_current_organization()
        self.client = APIClient()
        self.unique_suffix = uuid.uuid4().hex[:8]
        self.org = Organization.objects.create(
            name=f'Test Org {self.unique_suffix}',
            code=f'TEST_PICKUP_{self.unique_suffix}'
        )
        self.user = User.objects.create_user(
            username=f'applicant_{self.unique_suffix}',
            password='pass',
            organization=self.org
        )
        self.approver = User.objects.create_user(
            username=f'approver_{self.unique_suffix}',
            password='pass',
            organization=self.org
        )
        self.dept = Department.objects.create(
            organization=self.org,
            name='IT',
            code=f'IT_{self.unique_suffix}'
        )
        self.category = AssetCategory.objects.create(
            organization=self.org,
            code=f'PC_{self.unique_suffix}',
            name='Computer',
            created_by=self.user
        )
        self.asset = Asset.objects.create(
            organization=self.org,
            asset_name='Test Laptop',
            asset_category=self.category,
            purchase_price=Decimal('1000'),
            purchase_date=date.today(),
            asset_status='idle',
            created_by=self.user
        )
        self.client.force_authenticate(user=self.user)
        self.client.credentials(HTTP_X_ORGANIZATION_ID=str(self.org.id))
        set_current_organization(str(self.org.id))

    def test_create_pickup(self):
        """Test POST /api/assets/pickups/"""
        url = '/api/assets/pickups/'
        data = {
            'department': str(self.dept.id),
            'pickup_date': str(date.today()),
            'pickup_reason': 'New equipment',
            'items': [
                {'asset_id': str(self.asset.id), 'quantity': 1}
            ]
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_update_pickup_items_supports_add_update_delete(self):
        """PUT should update existing pickup items, create new ones, and delete omitted ones."""
        pickup = AssetPickup.objects.create(
            organization=self.org,
            applicant=self.user,
            department=self.dept,
            pickup_date=date.today(),
            pickup_reason='Old reason'
        )
        item_keep = PickupItem.objects.create(
            organization=self.org,
            pickup=pickup,
            asset=self.asset,
            quantity=1,
            remark='Old remark'
        )
        asset_2 = Asset.objects.create(
            organization=self.org,
            asset_name='Second Laptop',
            asset_category=self.category,
            purchase_price=Decimal('1200'),
            purchase_date=date.today(),
            asset_status='idle',
            created_by=self.user
        )
        asset_3 = Asset.objects.create(
            organization=self.org,
            asset_name='Third Laptop',
            asset_category=self.category,
            purchase_price=Decimal('1300'),
            purchase_date=date.today(),
            asset_status='idle',
            created_by=self.user
        )
        PickupItem.objects.create(
            organization=self.org,
            pickup=pickup,
            asset=asset_2,
            quantity=1,
            remark='Delete me'
        )

        response = self.client.put(
            f'/api/assets/pickups/{pickup.id}/',
            {
                'department': str(self.dept.id),
                'pickup_date': str(date.today()),
                'pickup_reason': 'Updated reason',
                'items': [
                    {
                        'id': str(item_keep.id),
                        'asset': str(asset_3.id),
                        'quantity': 2,
                        'remark': 'Updated remark'
                    },
                    {
                        'asset': str(asset_2.id),
                        'quantity': 1,
                        'remark': 'Created item'
                    }
                ]
            },
            format='json'
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        pickup.refresh_from_db()
        updated_items = list(pickup.items.order_by('created_at'))
        self.assertEqual(len(updated_items), 2)
        item_keep.refresh_from_db()
        self.assertEqual(item_keep.asset_id, asset_3.id)
        self.assertEqual(item_keep.quantity, 2)
        self.assertEqual(item_keep.remark, 'Updated remark')
        self.assertTrue(any(item.asset_id == asset_2.id and item.remark == 'Created item' for item in updated_items))

    def test_update_pickup_rejects_cross_document_item_id(self):
        """PUT should reject nested item ids that belong to a different pickup order."""
        pickup = AssetPickup.objects.create(
            organization=self.org,
            applicant=self.user,
            department=self.dept,
            pickup_date=date.today()
        )
        other_pickup = AssetPickup.objects.create(
            organization=self.org,
            applicant=self.user,
            department=self.dept,
            pickup_date=date.today()
        )
        foreign_item = PickupItem.objects.create(
            organization=self.org,
            pickup=other_pickup,
            asset=self.asset,
            quantity=1
        )

        response = self.client.put(
            f'/api/assets/pickups/{pickup.id}/',
            {
                'department': str(self.dept.id),
                'pickup_date': str(date.today()),
                'pickup_reason': 'Updated reason',
                'items': [
                    {
                        'id': str(foreign_item.id),
                        'asset': str(self.asset.id),
                        'quantity': 1
                    }
                ]
            },
            format='json'
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_update_pickup_items_supports_swapping_existing_assets(self):
        """PUT should allow two existing pickup rows to swap assets without unique conflicts."""
        pickup = AssetPickup.objects.create(
            organization=self.org,
            applicant=self.user,
            department=self.dept,
            pickup_date=date.today(),
            pickup_reason='Swap reason'
        )
        asset_2 = Asset.objects.create(
            organization=self.org,
            asset_name='Swap Laptop',
            asset_category=self.category,
            purchase_price=Decimal('1200'),
            purchase_date=date.today(),
            asset_status='idle',
            created_by=self.user
        )
        item_a = PickupItem.objects.create(
            organization=self.org,
            pickup=pickup,
            asset=self.asset,
            quantity=1,
            remark='Row A'
        )
        item_b = PickupItem.objects.create(
            organization=self.org,
            pickup=pickup,
            asset=asset_2,
            quantity=2,
            remark='Row B'
        )

        response = self.client.put(
            f'/api/assets/pickups/{pickup.id}/',
            {
                'department': str(self.dept.id),
                'pickup_date': str(date.today()),
                'pickup_reason': 'Swap updated',
                'items': [
                    {
                        'id': str(item_a.id),
                        'asset': str(asset_2.id),
                        'quantity': 10,
                        'remark': 'Row A swapped'
                    },
                    {
                        'id': str(item_b.id),
                        'asset': str(self.asset.id),
                        'quantity': 20,
                        'remark': 'Row B swapped'
                    }
                ]
            },
            format='json'
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        item_a.refresh_from_db()
        item_b.refresh_from_db()
        self.assertEqual(item_a.asset_id, asset_2.id)
        self.assertEqual(item_a.quantity, 10)
        self.assertEqual(item_a.remark, 'Row A swapped')
        self.assertEqual(item_b.asset_id, self.asset.id)
        self.assertEqual(item_b.quantity, 20)
        self.assertEqual(item_b.remark, 'Row B swapped')

    def test_list_pickups(self):
        """Test GET /api/assets/pickups/"""
        AssetPickup.objects.create(
            organization=self.org,
            applicant=self.user,
            department=self.dept,
            pickup_date=date.today()
        )

        url = '/api/assets/pickups/'
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_submit_pickup(self):
        """Test POST /api/assets/pickups/{id}/submit/"""
        pickup = AssetPickup.objects.create(
            organization=self.org,
            applicant=self.user,
            department=self.dept,
            pickup_date=date.today()
        )
        PickupItem.objects.create(
            organization=self.org,
            pickup=pickup,
            asset=self.asset
        )

        url = f'/api/assets/pickups/{pickup.id}/submit/'
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        pickup.refresh_from_db()
        self.assertEqual(pickup.status, 'pending')

    def test_approve_pickup(self):
        """Test POST /api/assets/pickups/{id}/approve/"""
        pickup = AssetPickup.objects.create(
            organization=self.org,
            applicant=self.user,
            department=self.dept,
            pickup_date=date.today(),
            status='pending'
        )
        PickupItem.objects.create(
            organization=self.org,
            pickup=pickup,
            asset=self.asset
        )

        url = f'/api/assets/pickups/{pickup.id}/approve/'
        data = {'approval': 'approved', 'comment': 'OK'}
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        pickup.refresh_from_db()
        self.assertEqual(pickup.status, 'approved')

    def test_complete_pickup(self):
        """Test POST /api/assets/pickups/{id}/complete/"""
        pickup = AssetPickup.objects.create(
            organization=self.org,
            applicant=self.user,
            department=self.dept,
            pickup_date=date.today(),
            status='approved'
        )

        url = f'/api/assets/pickups/{pickup.id}/complete/'
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def tearDown(self):
        """Clean up after each test."""
        # Clear thread-local organization context
        from apps.common.middleware import clear_current_organization
        clear_current_organization()
        # Call parent tearDown for proper Django TestCase cleanup
        super().tearDown()


class AssetTransferAPITest(APITransactionTestCase):
    """Test Asset Transfer API endpoints."""

    def setUp(self):
        """Set up test data with unique codes."""
        from apps.common.middleware import clear_current_organization, set_current_organization

        clear_current_organization()
        self.client = APIClient()
        self.unique_suffix = uuid.uuid4().hex[:8]
        self.org = Organization.objects.create(
            name=f'Test Org {self.unique_suffix}',
            code=f'TEST_TRANSFER_{self.unique_suffix}'
        )
        self.user = User.objects.create_user(
            username=f'mgr_{self.unique_suffix}',
            password='pass',
            organization=self.org
        )
        self.from_dept = Department.objects.create(
            organization=self.org,
            name='IT',
            code=f'IT_{self.unique_suffix}'
        )
        self.to_dept = Department.objects.create(
            organization=self.org,
            name='HR',
            code=f'HR_{self.unique_suffix}'
        )
        self.category = AssetCategory.objects.create(
            organization=self.org,
            code=f'PC_{self.unique_suffix}',
            name='Computer',
            created_by=self.user
        )
        self.location = Location.objects.create(
            organization=self.org,
            name='Office',
            location_type='area'
        )
        self.asset = Asset.objects.create(
            organization=self.org,
            asset_name='Test Laptop',
            asset_category=self.category,
            purchase_price=Decimal('1000'),
            purchase_date=date.today(),
            department=self.from_dept,
            location=self.location,
            custodian=self.user,
            created_by=self.user
        )
        self.client.force_authenticate(user=self.user)
        self.client.credentials(HTTP_X_ORGANIZATION_ID=str(self.org.id))
        set_current_organization(str(self.org.id))

    def test_create_transfer(self):
        """Test POST /api/assets/transfers/"""
        url = '/api/assets/transfers/'
        data = {
            'from_department': str(self.from_dept.id),
            'to_department': str(self.to_dept.id),
            'transfer_date': str(date.today()),
            'items': [
                {'asset_id': str(self.asset.id)}
            ]
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_update_transfer_items_supports_add_update_delete(self):
        """PUT should diff transfer line items using the unified items contract."""
        transfer = AssetTransfer.objects.create(
            organization=self.org,
            from_department=self.from_dept,
            to_department=self.to_dept,
            transfer_date=date.today(),
            transfer_reason='Old transfer reason'
        )
        from apps.assets.models import TransferItem
        item_keep = TransferItem.objects.create(
            organization=self.org,
            transfer=transfer,
            asset=self.asset,
            from_location=self.location,
            from_custodian=self.user,
            to_location=self.location,
            remark='Old transfer item'
        )
        asset_2 = Asset.objects.create(
            organization=self.org,
            asset_name='Transfer Laptop B',
            asset_category=self.category,
            purchase_price=Decimal('1100'),
            purchase_date=date.today(),
            department=self.from_dept,
            location=self.location,
            custodian=self.user,
            created_by=self.user
        )
        asset_3 = Asset.objects.create(
            organization=self.org,
            asset_name='Transfer Laptop C',
            asset_category=self.category,
            purchase_price=Decimal('1250'),
            purchase_date=date.today(),
            department=self.from_dept,
            location=self.location,
            custodian=self.user,
            created_by=self.user
        )
        TransferItem.objects.create(
            organization=self.org,
            transfer=transfer,
            asset=asset_2,
            from_location=self.location,
            from_custodian=self.user,
            to_location=self.location,
            remark='Delete me'
        )
        target_location = Location.objects.create(
            organization=self.org,
            name='Branch Office',
            location_type='area'
        )

        response = self.client.put(
            f'/api/assets/transfers/{transfer.id}/',
            {
                'from_department': str(self.from_dept.id),
                'to_department': str(self.to_dept.id),
                'transfer_date': str(date.today()),
                'transfer_reason': 'Updated transfer reason',
                'items': [
                    {
                        'id': str(item_keep.id),
                        'asset': str(asset_3.id),
                        'toLocation': str(target_location.id),
                        'remark': 'Updated transfer item'
                    },
                    {
                        'asset': str(asset_2.id),
                        'toLocation': str(target_location.id),
                        'remark': 'Created transfer item'
                    }
                ]
            },
            format='json'
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        transfer.refresh_from_db()
        updated_items = list(transfer.items.order_by('created_at'))
        self.assertEqual(len(updated_items), 2)
        item_keep.refresh_from_db()
        self.assertEqual(item_keep.asset_id, asset_3.id)
        self.assertEqual(item_keep.to_location_id, target_location.id)
        self.assertEqual(item_keep.remark, 'Updated transfer item')
        self.assertTrue(any(item.asset_id == asset_2.id and item.remark == 'Created transfer item' for item in updated_items))

    def test_approve_from(self):
        """Test POST /api/assets/transfers/{id}/approve-from/"""
        transfer = AssetTransfer.objects.create(
            organization=self.org,
            from_department=self.from_dept,
            to_department=self.to_dept,
            transfer_date=date.today(),
            status='pending'
        )

        url = f'/api/assets/transfers/{transfer.id}/approve-from/'
        response = self.client.post(url, {'comment': 'OK'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def tearDown(self):
        """Clean up after each test."""
        # Clear thread-local organization context
        from apps.common.middleware import clear_current_organization
        clear_current_organization()
        # Call parent tearDown for proper Django TestCase cleanup
        super().tearDown()


class AssetReturnAPITest(APITransactionTestCase):
    """Test Asset Return API endpoints."""

    def setUp(self):
        """Set up test data with unique codes."""
        from apps.common.middleware import clear_current_organization, set_current_organization

        clear_current_organization()
        self.client = APIClient()
        self.unique_suffix = uuid.uuid4().hex[:8]
        self.org = Organization.objects.create(
            name=f'Test Org {self.unique_suffix}',
            code=f'TEST_RETURN_{self.unique_suffix}'
        )
        self.user = User.objects.create_user(
            username=f'user_{self.unique_suffix}',
            password='pass',
            organization=self.org
        )
        self.admin = User.objects.create_user(
            username=f'admin_{self.unique_suffix}',
            password='pass',
            organization=self.org
        )
        self.location = Location.objects.create(
            organization=self.org,
            name='Warehouse',
            location_type='warehouse'
        )
        self.department = Department.objects.create(
            organization=self.org,
            code=f'RD_{self.unique_suffix}',
            name='R&D'
        )
        self.category = AssetCategory.objects.create(
            organization=self.org,
            code=f'PC_{self.unique_suffix}',
            name='Computer',
            created_by=self.user
        )
        self.asset = Asset.objects.create(
            organization=self.org,
            asset_name='Test Laptop',
            asset_category=self.category,
            purchase_price=Decimal('1000'),
            purchase_date=date.today(),
            custodian=self.user,
            created_by=self.user
        )
        self.project = AssetProject.objects.create(
            organization=self.org,
            project_name='Return Flow Project',
            project_type='development',
            project_manager=self.user,
            department=self.department,
            start_date=date.today(),
            status='active',
            created_by=self.user
        )
        self.project_allocation = ProjectAsset.objects.create(
            organization=self.org,
            project=self.project,
            asset=self.asset,
            allocation_date=date.today(),
            allocation_type='temporary',
            allocated_by=self.user,
            custodian=self.user,
            return_status='in_use',
            created_by=self.user
        )
        self.client.force_authenticate(user=self.user)
        self.client.credentials(HTTP_X_ORGANIZATION_ID=str(self.org.id))
        set_current_organization(str(self.org.id))

    def test_create_return(self):
        """Test POST /api/assets/returns/"""
        url = '/api/assets/returns/'
        data = {
            'return_date': str(date.today()),
            'return_location': str(self.location.id),
            'items': [
                {'asset_id': str(self.asset.id), 'asset_status': 'idle'}
            ]
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_create_return_accepts_project_allocation_context(self):
        """POST should accept project allocation linkage in nested items."""
        url = '/api/assets/returns/'
        data = {
            'return_date': str(date.today()),
            'return_location': str(self.location.id),
            'items': [
                {
                    'asset_id': str(self.asset.id),
                    'project_allocation_id': str(self.project_allocation.id),
                    'asset_status': 'idle'
                }
            ]
        }
        response = self.client.post(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        return_order = AssetReturn.objects.get(id=response.data['data']['id'])
        self.assertEqual(return_order.items.get().project_allocation_id, self.project_allocation.id)

    def test_update_return_items_supports_add_update_delete(self):
        """PUT should diff return line items and accept camelCase nested fields."""
        return_order = AssetReturn.objects.create(
            organization=self.org,
            returner=self.user,
            return_date=date.today(),
            return_location=self.location,
            return_reason='Old return reason'
        )
        from apps.assets.models import ReturnItem
        item_keep = ReturnItem.objects.create(
            organization=self.org,
            asset_return=return_order,
            asset=self.asset,
            asset_status='idle',
            condition_description='Old condition',
            remark='Old return item'
        )
        asset_2 = Asset.objects.create(
            organization=self.org,
            asset_name='Return Laptop B',
            asset_category=self.category,
            purchase_price=Decimal('1100'),
            purchase_date=date.today(),
            custodian=self.user,
            created_by=self.user
        )
        asset_3 = Asset.objects.create(
            organization=self.org,
            asset_name='Return Laptop C',
            asset_category=self.category,
            purchase_price=Decimal('1200'),
            purchase_date=date.today(),
            custodian=self.user,
            created_by=self.user
        )
        ReturnItem.objects.create(
            organization=self.org,
            asset_return=return_order,
            asset=asset_2,
            asset_status='idle',
            remark='Delete me'
        )

        response = self.client.put(
            f'/api/assets/returns/{return_order.id}/',
            {
                'return_date': str(date.today()),
                'return_location': str(self.location.id),
                'return_reason': 'Updated return reason',
                'items': [
                    {
                        'id': str(item_keep.id),
                        'asset': str(asset_3.id),
                        'assetStatus': 'maintenance',
                        'conditionDescription': 'Updated condition',
                        'remark': 'Updated return item'
                    },
                    {
                        'asset': str(asset_2.id),
                        'assetStatus': 'idle',
                        'remark': 'Created return item'
                    }
                ]
            },
            format='json'
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        return_order.refresh_from_db()
        updated_items = list(return_order.items.order_by('created_at'))
        self.assertEqual(len(updated_items), 2)
        item_keep.refresh_from_db()
        self.assertEqual(item_keep.asset_id, asset_3.id)
        self.assertEqual(item_keep.asset_status, 'maintenance')
        self.assertEqual(item_keep.condition_description, 'Updated condition')
        self.assertEqual(item_keep.remark, 'Updated return item')
        self.assertTrue(any(item.asset_id == asset_2.id and item.remark == 'Created return item' for item in updated_items))

    def test_list_returns_supports_project_filter(self):
        """GET should filter return orders by linked project."""
        other_project = AssetProject.objects.create(
            organization=self.org,
            project_name='Another Project',
            project_type='development',
            project_manager=self.user,
            department=self.department,
            start_date=date.today(),
            status='active',
            created_by=self.user
        )
        other_asset = Asset.objects.create(
            organization=self.org,
            asset_name='Other Laptop',
            asset_category=self.category,
            purchase_price=Decimal('900'),
            purchase_date=date.today(),
            custodian=self.user,
            created_by=self.user
        )
        other_allocation = ProjectAsset.objects.create(
            organization=self.org,
            project=other_project,
            asset=other_asset,
            allocation_date=date.today(),
            allocation_type='temporary',
            allocated_by=self.user,
            custodian=self.user,
            return_status='in_use',
            created_by=self.user
        )

        project_return = AssetReturn.objects.create(
            organization=self.org,
            returner=self.user,
            return_date=date.today(),
            return_location=self.location,
            status='pending'
        )
        AssetReturn.objects.create(
            organization=self.org,
            returner=self.user,
            return_date=date.today(),
            return_location=self.location,
            status='pending'
        )
        from apps.assets.models import ReturnItem
        ReturnItem.objects.create(
            organization=self.org,
            asset_return=project_return,
            asset=self.asset,
            project_allocation=self.project_allocation,
            asset_status='idle'
        )
        unrelated_return = AssetReturn.objects.filter(
            organization=self.org,
            status='pending'
        ).exclude(id=project_return.id).order_by('-created_at').first()
        ReturnItem.objects.create(
            organization=self.org,
            asset_return=unrelated_return,
            asset=other_asset,
            project_allocation=other_allocation,
            asset_status='idle'
        )

        response = self.client.get(
            f'/api/assets/returns/?project={self.project.id}',
            format='json'
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        result_ids = [row['id'] for row in response.data['data']['results']]
        self.assertEqual(result_ids, [str(project_return.id)])

    def test_confirm_return(self):
        """Test POST /api/assets/returns/{id}/confirm/"""
        return_order = AssetReturn.objects.create(
            organization=self.org,
            returner=self.user,
            return_date=date.today(),
            return_location=self.location,
            status='pending'
        )
        from apps.assets.models import ReturnItem
        ReturnItem.objects.create(
            organization=self.org,
            asset_return=return_order,
            asset=self.asset,
            project_allocation=self.project_allocation,
            asset_status='idle'
        )

        url = f'/api/assets/returns/{return_order.id}/confirm/'
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.project_allocation.refresh_from_db()
        self.project.refresh_from_db()
        self.assertEqual(self.project_allocation.return_status, 'returned')
        self.assertEqual(self.project.active_assets, 0)

    def test_reject_return_appends_project_allocation_tracking_note(self):
        """Rejecting a project-linked return should keep allocation active and sync the note."""
        return_order = AssetReturn.objects.create(
            organization=self.org,
            returner=self.user,
            return_date=date.today(),
            return_location=self.location,
            status='pending'
        )
        from apps.assets.models import ReturnItem
        ReturnItem.objects.create(
            organization=self.org,
            asset_return=return_order,
            asset=self.asset,
            project_allocation=self.project_allocation,
            asset_status='idle'
        )

        response = self.client.post(
            f'/api/assets/returns/{return_order.id}/reject/',
            {'reason': 'Missing charger'},
            format='json'
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.project_allocation.refresh_from_db()
        self.assertEqual(self.project_allocation.return_status, 'in_use')
        self.assertIn('Return rejected via', self.project_allocation.notes)
        self.assertIn('Missing charger', self.project_allocation.notes)

    def test_project_filtered_return_list_includes_reject_reason_for_history_panel(self):
        """Project-scoped return history should expose reject reason in list payloads."""
        return_order = AssetReturn.objects.create(
            organization=self.org,
            returner=self.user,
            return_date=date.today(),
            return_location=self.location,
            status='rejected',
            reject_reason='Missing charger'
        )
        from apps.assets.models import ReturnItem
        ReturnItem.objects.create(
            organization=self.org,
            asset_return=return_order,
            asset=self.asset,
            project_allocation=self.project_allocation,
            asset_status='idle'
        )

        response = self.client.get(
            f'/api/assets/returns/?project={self.project.id}&status=rejected',
            format='json'
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        row = response.data['data']['results'][0]
        self.assertEqual(row['reject_reason'], 'Missing charger')

    def tearDown(self):
        """Clean up after each test."""
        # Clear thread-local organization context
        from apps.common.middleware import clear_current_organization
        clear_current_organization()
        # Call parent tearDown for proper Django TestCase cleanup
        super().tearDown()


class AssetLoanAPITest(APITransactionTestCase):
    """Test Asset Loan API endpoints."""

    def setUp(self):
        """Set up test data with unique codes."""
        from apps.common.middleware import clear_current_organization, set_current_organization

        clear_current_organization()
        self.client = APIClient()
        self.unique_suffix = uuid.uuid4().hex[:8]
        self.org = Organization.objects.create(
            name=f'Test Org {self.unique_suffix}',
            code=f'TEST_LOAN_{self.unique_suffix}'
        )
        self.user = User.objects.create_user(
            username=f'borrower_{self.unique_suffix}',
            password='pass',
            organization=self.org
        )
        self.admin = User.objects.create_user(
            username=f'admin_{self.unique_suffix}',
            password='pass',
            organization=self.org
        )
        self.category = AssetCategory.objects.create(
            organization=self.org,
            code=f'PC_{self.unique_suffix}',
            name='Computer',
            created_by=self.user
        )
        self.asset = Asset.objects.create(
            organization=self.org,
            asset_name='Test Laptop',
            asset_category=self.category,
            purchase_price=Decimal('1000'),
            purchase_date=date.today(),
            asset_status='idle',
            created_by=self.user
        )
        self.client.force_authenticate(user=self.user)
        self.client.credentials(HTTP_X_ORGANIZATION_ID=str(self.org.id))
        set_current_organization(str(self.org.id))

    def test_create_loan(self):
        """Test POST /api/assets/loans/"""
        url = '/api/assets/loans/'
        data = {
            'borrow_date': str(date.today()),
            'expected_return_date': str(date.today() + timedelta(days=30)),
            'items': [
                {'asset_id': str(self.asset.id)}
            ]
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_update_loan_items_supports_add_update_delete(self):
        """PUT should diff loan line items and allow asset replacement."""
        loan = AssetLoan.objects.create(
            organization=self.org,
            borrower=self.user,
            borrow_date=date.today(),
            expected_return_date=date.today() + timedelta(days=30),
            loan_reason='Old loan reason'
        )
        from apps.assets.models import LoanItem
        item_keep = LoanItem.objects.create(
            organization=self.org,
            loan=loan,
            asset=self.asset,
            remark='Old loan item'
        )
        asset_2 = Asset.objects.create(
            organization=self.org,
            asset_name='Loan Laptop B',
            asset_category=self.category,
            purchase_price=Decimal('1200'),
            purchase_date=date.today(),
            asset_status='idle',
            created_by=self.user
        )
        asset_3 = Asset.objects.create(
            organization=self.org,
            asset_name='Loan Laptop C',
            asset_category=self.category,
            purchase_price=Decimal('1300'),
            purchase_date=date.today(),
            asset_status='idle',
            created_by=self.user
        )
        LoanItem.objects.create(
            organization=self.org,
            loan=loan,
            asset=asset_2,
            remark='Delete me'
        )

        response = self.client.put(
            f'/api/assets/loans/{loan.id}/',
            {
                'borrow_date': str(date.today()),
                'expected_return_date': str(date.today() + timedelta(days=20)),
                'loan_reason': 'Updated loan reason',
                'items': [
                    {
                        'id': str(item_keep.id),
                        'asset': str(asset_3.id),
                        'remark': 'Updated loan item'
                    },
                    {
                        'asset': str(asset_2.id),
                        'remark': 'Created loan item'
                    }
                ]
            },
            format='json'
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        loan.refresh_from_db()
        updated_items = list(loan.items.order_by('created_at'))
        self.assertEqual(len(updated_items), 2)
        item_keep.refresh_from_db()
        self.assertEqual(item_keep.asset_id, asset_3.id)
        self.assertEqual(item_keep.remark, 'Updated loan item')
        self.assertTrue(any(item.asset_id == asset_2.id and item.remark == 'Created loan item' for item in updated_items))

    def test_approve_loan(self):
        """Test POST /api/assets/loans/{id}/approve/"""
        loan = AssetLoan.objects.create(
            organization=self.org,
            borrower=self.user,
            borrow_date=date.today(),
            expected_return_date=date.today() + timedelta(days=30),
            status='pending'
        )
        from apps.assets.models import LoanItem
        LoanItem.objects.create(
            organization=self.org,
            loan=loan,
            asset=self.asset
        )

        url = f'/api/assets/loans/{loan.id}/approve/'
        data = {'approval': 'approved'}
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def tearDown(self):
        """Clean up after each test."""
        # Clear thread-local organization context
        from apps.common.middleware import clear_current_organization
        clear_current_organization()
        # Call parent tearDown for proper Django TestCase cleanup
        super().tearDown()
