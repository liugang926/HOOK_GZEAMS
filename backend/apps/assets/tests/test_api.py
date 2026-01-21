"""
Tests for AssetCategory, Asset, and Operation API endpoints.

IMPORTANT: Due to multi-tenant organization isolation using thread-local storage,
each test creates a fresh APIClient instance to ensure proper organization context.
"""
import pytest
from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from decimal import Decimal
from datetime import date, timedelta
from apps.assets.models import (
    AssetCategory, Asset, Supplier, Location,
    AssetPickup, PickupItem, AssetTransfer, AssetReturn, AssetLoan
)
from apps.organizations.models import Organization, Department
from apps.accounts.models import User


class AssetCategoryAPITest(APITestCase):
    """Test AssetCategory API endpoints."""

    def setUp(self):
        """Set up test data."""
        import uuid
        self.org = Organization.objects.create(
            name='Test Organization',
            code=f'TEST_ORG_CAT_{uuid.uuid4().hex[:8]}'
        )
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123',
            organization=self.org
        )

        # Create test categories
        self.parent = AssetCategory.objects.create(
            organization=self.org,
            code='ELECTRONICS',
            name='Electronics',
            created_by=self.user
        )
        self.child = AssetCategory.objects.create(
            organization=self.org,
            code='COMPUTERS',
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
        self.assertEqual(response.data['data']['code'], 'ELECTRONICS')

    def test_create_category(self):
        """Test POST /api/assets/categories/"""
        url = '/api/assets/categories/'
        data = {
            'code': 'FURNITURE',
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
            'code': 'ELECTRONICS',
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

    def test_add_child_action(self):
        """Test POST /api/assets/categories/{id}/add_child/"""
        url = f'/api/assets/categories/{self.parent.id}/add_child/'
        data = {
            'code': 'PHONES',
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
        """Set up test data."""
        self.client = APIClient()
        import uuid
        self.org = Organization.objects.create(
            name='Test Organization',
            code=f'TEST_ORG_ASSET_{uuid.uuid4().hex[:8]}'
        )
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123',
            organization=self.org
        )
        self.client.force_authenticate(user=self.user)
        self.client.credentials(HTTP_X_ORGANIZATION_ID=str(self.org.id))

        # Create test category
        self.category = AssetCategory.objects.create(
            organization=self.org,
            code='COMPUTER',
            name='Computer Equipment',
            created_by=self.user
        )

        # Create test department
        self.department = Department.objects.create(
            organization=self.org,
            name='IT Department',
            code='IT'
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
            code='DELL',
            name='Dell Inc.',
            created_by=self.user
        )

    def test_list_assets(self):
        """Test GET /api/assets/"""
        Asset.objects.create(
            organization=self.org,
            asset_name='Test Laptop',
            asset_category=self.category,
            purchase_price=Decimal('1000.00'),
            purchase_date='2024-01-01',
            created_by=self.user
        )

        url = '/api/assets/'
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Standard pagination format wrapped in BaseResponse
        self.assertIn('count', response.data['data'])

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
        """Test POST /api/assets/{id}/change_status/"""
        asset = Asset.objects.create(
            organization=self.org,
            asset_name='Test Laptop',
            asset_category=self.category,
            purchase_price=Decimal('1000.00'),
            purchase_date='2024-01-01',
            asset_status='pending',
            created_by=self.user
        )

        url = f'/api/assets/{asset.id}/change_status/'
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


class SupplierAPITest(APITestCase):
    """Test Supplier API endpoints."""

    def setUp(self):
        """Set up test data."""
        self.client = APIClient()
        import uuid
        self.org = Organization.objects.create(
            name='Test Organization',
            code=f'TEST_ORG_SUPP_{uuid.uuid4().hex[:8]}'
        )
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123',
            organization=self.org
        )
        self.client.force_authenticate(user=self.user)
        self.client.credentials(HTTP_X_ORGANIZATION_ID=str(self.org.id))

    def test_create_supplier(self):
        """Test POST /api/assets/suppliers/"""
        url = '/api/assets/suppliers/'
        data = {
            'code': 'DELL',
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
            code='DELL',
            name='Dell Inc.',
            created_by=self.user
        )

        url = '/api/assets/suppliers/'
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)


class LocationAPITest(APITestCase):
    """Test Location API endpoints."""

    def setUp(self):
        """Set up test data."""
        self.client = APIClient()
        import uuid
        self.org = Organization.objects.create(
            name='Test Organization',
            code=f'TEST_ORG_LOC_{uuid.uuid4().hex[:8]}'
        )
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
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


# ========== Operation API Tests ==========


class AssetPickupAPITest(APITestCase):
    """Test Asset Pickup API endpoints."""

    def setUp(self):
        """Set up test data."""
        self.client = APIClient()
        import uuid
        self.org = Organization.objects.create(name='Test Org', code=f'TEST_PICKUP_{uuid.uuid4().hex[:8]}')
        self.user = User.objects.create_user(
            username='applicant', password='pass', organization=self.org
        )
        self.approver = User.objects.create_user(
            username='approver', password='pass', organization=self.org
        )
        self.dept = Department.objects.create(
            organization=self.org, name='IT', code='IT'
        )
        self.category = AssetCategory.objects.create(
            organization=self.org, code='PC', name='Computer', created_by=self.user
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


class AssetTransferAPITest(APITestCase):
    """Test Asset Transfer API endpoints."""

    def setUp(self):
        """Set up test data."""
        self.client = APIClient()
        import uuid
        self.org = Organization.objects.create(name='Test Org', code=f'TEST_TRANSFER_{uuid.uuid4().hex[:8]}')
        self.user = User.objects.create_user(
            username='mgr', password='pass', organization=self.org
        )
        self.from_dept = Department.objects.create(
            organization=self.org, name='IT', code='IT'
        )
        self.to_dept = Department.objects.create(
            organization=self.org, name='HR', code='HR'
        )
        self.category = AssetCategory.objects.create(
            organization=self.org, code='PC', name='Computer', created_by=self.user
        )
        self.location = Location.objects.create(
            organization=self.org, name='Office', location_type='area'
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


class AssetReturnAPITest(APITestCase):
    """Test Asset Return API endpoints."""

    def setUp(self):
        """Set up test data."""
        self.client = APIClient()
        import uuid
        self.org = Organization.objects.create(name='Test Org', code=f'TEST_RETURN_{uuid.uuid4().hex[:8]}')
        self.user = User.objects.create_user(
            username='user', password='pass', organization=self.org
        )
        self.admin = User.objects.create_user(
            username='admin', password='pass', organization=self.org
        )
        self.location = Location.objects.create(
            organization=self.org, name='Warehouse', location_type='warehouse'
        )
        self.category = AssetCategory.objects.create(
            organization=self.org, code='PC', name='Computer', created_by=self.user
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
        self.client.force_authenticate(user=self.user)
        self.client.credentials(HTTP_X_ORGANIZATION_ID=str(self.org.id))

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
            asset_status='idle'
        )

        url = f'/api/assets/returns/{return_order.id}/confirm/'
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)


class AssetLoanAPITest(APITestCase):
    """Test Asset Loan API endpoints."""

    def setUp(self):
        """Set up test data."""
        self.client = APIClient()
        import uuid
        self.org = Organization.objects.create(name='Test Org', code=f'TEST_LOAN_{uuid.uuid4().hex[:8]}')
        self.user = User.objects.create_user(
            username='borrower', password='pass', organization=self.org
        )
        self.admin = User.objects.create_user(
            username='admin', password='pass', organization=self.org
        )
        self.category = AssetCategory.objects.create(
            organization=self.org, code='PC', name='Computer', created_by=self.user
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
