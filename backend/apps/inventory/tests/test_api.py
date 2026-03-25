"""
Tests for Inventory API endpoints.
"""
import uuid
from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase, APIClient

from apps.inventory.models import (
    InventoryTask,
    InventorySnapshot,
    InventoryScan,
    InventoryDifference,
)
from apps.inventory.utils.qr_code import QRCodeGenerator
from apps.assets.models import Asset, Location, AssetCategory
from apps.organizations.models import Organization
from apps.accounts.models import User


class InventoryTaskAPITests(APITestCase):
    """Tests for InventoryTask API endpoints."""

    def setUp(self):
        """Set up test data with unique codes."""
        # Clear thread-local organization context to prevent test pollution
        from apps.common.middleware import clear_current_organization
        clear_current_organization()

        self.unique_suffix = uuid.uuid4().hex[:8]

        self.organization = Organization.objects.create(
            name=f"Test Organization {self.unique_suffix}",
            code=f"TESTORG_{self.unique_suffix}"
        )
        self.user = User.objects.create_user(
            username=f"testuser_{self.unique_suffix}",
            email=f"test{self.unique_suffix}@example.com",
            organization=self.organization
        )

    def _make_client(self):
        """Create a fresh API client for each request."""
        client = APIClient()
        client.force_authenticate(user=self.user)
        client.credentials(HTTP_X_ORGANIZATION_ID=str(self.organization.id))
        return client

    def tearDown(self):
        """Clean up after each test."""
        # Clear thread-local organization context
        from apps.common.middleware import clear_current_organization
        clear_current_organization()

    def _create_test_data(self):
        """Create common test data (location, category, assets)."""
        # Use all_objects to bypass TenantManager's organization filtering
        self.location = Location.all_objects.create(
            name="Test Location",
            path="Test Location",
            organization=self.organization
        )
        self.category = AssetCategory.all_objects.create(
            name="Test Category",
            code=f"CAT_{self.unique_suffix}",
            organization=self.organization
        )

        # Create test assets
        for i in range(3):
            Asset.all_objects.create(
                asset_code=f"ASSET_{self.unique_suffix}_{i:03d}",
                asset_name=f"Test Asset {i}",
                asset_category=self.category,
                location=self.location,
                purchase_price=0,
                purchase_date="2024-01-01",
                organization=self.organization,
                created_by=self.user
            )

    def test_list_inventory_tasks(self):
        """Test listing inventory tasks."""
        self._create_test_data()

        # Create some tasks using all_objects to bypass organization filtering
        for i in range(3):
            InventoryTask.all_objects.create(
                task_code=f"INV_{self.unique_suffix}_{i:03d}",
                task_name=f"Inventory {i}",
                inventory_type=InventoryTask.TYPE_FULL,
                planned_date="2024-01-01",
                organization=self.organization,
                created_by=self.user
            )

        url = '/api/inventory/tasks/'
        client = self._make_client()
        # Don't pass header - let middleware use user's primary organization
        response = client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(response.data['data']['count'], 3)

    def test_create_inventory_task(self):
        """Test creating an inventory task."""
        self._create_test_data()

        url = '/api/inventory/tasks/'
        data = {
            'task_name': 'New Inventory Task',
            'inventory_type': InventoryTask.TYPE_FULL,
            'planned_date': '2024-12-31'
        }
        client = self._make_client()
        response = client.post(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['data']['task_name'], 'New Inventory Task')

        # Check snapshots were created
        task_id = response.data['data']['id']
        snapshots_count = InventorySnapshot.objects.filter(task_id=task_id).count()
        self.assertEqual(snapshots_count, 3)

    def test_retrieve_inventory_task(self):
        """Test retrieving a single task."""
        # Use all_objects to bypass TenantManager's organization filtering
        task = InventoryTask.all_objects.create(
            task_code=f"INV_{uuid.uuid4().hex[:8]}",
            task_name="Test Task",
            inventory_type=InventoryTask.TYPE_FULL,
                planned_date="2024-01-01",
            organization=self.organization,
            created_by=self.user
        )

        url = f'/api/inventory/tasks/{task.id}/'
        client = self._make_client()
        response = client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['data']['task_code'], task.task_code)

    def test_start_inventory_task(self):
        """Test starting an inventory task."""
        task = InventoryTask.all_objects.create(
            task_code=f"INV_{uuid.uuid4().hex[:8]}",
            task_name="Test Task",
            inventory_type=InventoryTask.TYPE_FULL,
                planned_date="2024-01-01",
            status=InventoryTask.STATUS_DRAFT,
            organization=self.organization,
            created_by=self.user
        )

        url = f'/api/inventory/tasks/{task.id}/start/'
        client = self._make_client()
        response = client.post(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        task.refresh_from_db()
        self.assertEqual(task.status, InventoryTask.STATUS_IN_PROGRESS)

    def test_complete_inventory_task(self):
        """Test completing an inventory task."""
        task = InventoryTask.all_objects.create(
            task_code=f"INV_{uuid.uuid4().hex[:8]}",
            task_name="Test Task",
            inventory_type=InventoryTask.TYPE_FULL,
                planned_date="2024-01-01",
            status=InventoryTask.STATUS_IN_PROGRESS,
            started_at=timezone.now(),
            organization=self.organization,
            created_by=self.user
        )

        url = f'/api/inventory/tasks/{task.id}/complete/'
        client = self._make_client()
        response = client.post(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        task.refresh_from_db()
        self.assertEqual(task.status, InventoryTask.STATUS_COMPLETED)

    def test_get_task_statistics(self):
        """Test getting task statistics."""
        # Create a location and category for snapshots
        location = Location.all_objects.create(
            name="Stats Location",
            path="Stats Location",
            organization=self.organization
        )
        category = AssetCategory.all_objects.create(
            name="Stats Category",
            code="STATCAT",
            organization=self.organization
        )

        task = InventoryTask.all_objects.create(
            task_code=f"INV_{uuid.uuid4().hex[:8]}",
            task_name="Test Task",
            inventory_type=InventoryTask.TYPE_FULL,
                planned_date="2024-01-01",
            total_count=10,
            scanned_count=5,
            organization=self.organization,
            created_by=self.user
        )
        # Create 10 unique assets and their snapshots
        for i in range(10):
            asset = Asset.all_objects.create(
                asset_code=f"STATASSET{i:03d}",
                asset_name=f"Stats Test Asset {i}",
                asset_category=category,
                location=location,
                purchase_price=0,
                purchase_date="2024-01-01",
                organization=self.organization,
                created_by=self.user
            )
            InventorySnapshot.all_objects.create(
                task=task,
                asset=asset,
                asset_code=asset.asset_code,
                asset_name=asset.asset_name,
                location_id=str(location.id),
                location_name=location.name,
                organization=self.organization,
                created_by=self.user
            )

        url = f'/api/inventory/tasks/{task.id}/statistics/'
        client = self._make_client()
        response = client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Statistics are in the progress sub-object
        # After update_statistics, total_count is based on actual snapshots
        self.assertEqual(response.data['data']['progress']['total_count'], 10)
        self.assertEqual(response.data['data']['snapshots']['total_snapshots'], 10)


class InventoryScanAPITests(APITestCase):
    """Tests for InventoryScan API endpoints."""

    def setUp(self):
        """Set up test data with unique codes."""
        # Clear thread-local organization context to prevent test pollution
        from apps.common.middleware import clear_current_organization
        clear_current_organization()

        self.unique_suffix = uuid.uuid4().hex[:8]

        self.organization = Organization.objects.create(
            name=f"Test Organization {self.unique_suffix}",
            code=f"TESTORG_{self.unique_suffix}"
        )
        self.user = User.objects.create_user(
            username=f"testuser_{self.unique_suffix}",
            email=f"test{self.unique_suffix}@example.com",
            organization=self.organization
        )

    def _make_client(self):
        """Create a fresh API client for each request."""
        client = APIClient()
        client.force_authenticate(user=self.user)
        client.credentials(HTTP_X_ORGANIZATION_ID=str(self.organization.id))
        return client

    def tearDown(self):
        """Clean up after each test."""
        # Clear thread-local organization context
        from apps.common.middleware import clear_current_organization
        clear_current_organization()

    def _create_test_data(self):
        """Create common test data for scan tests."""
        self.location = Location.all_objects.create(
            name="Test Location",
            path="Test Location",
            organization=self.organization
        )
        self.category = AssetCategory.all_objects.create(
            name="Test Category",
            code=f"CAT_{self.unique_suffix}",
            organization=self.organization
        )
        self.asset = Asset.all_objects.create(
            asset_code=f"ASSET_{self.unique_suffix}_001",
            asset_name="Test Asset",
            asset_category=self.category,
            location=self.location,
            purchase_price=0,
            purchase_date="2024-01-01",
            organization=self.organization,
            created_by=self.user
        )
        self.task = InventoryTask.all_objects.create(
            task_code=f"INV_{uuid.uuid4().hex[:8]}",
            task_name="Test Inventory",
            inventory_type=InventoryTask.TYPE_FULL,
            planned_date="2024-01-01",
            status=InventoryTask.STATUS_IN_PROGRESS,
            organization=self.organization,
            created_by=self.user
        )
        InventorySnapshot.all_objects.create(
            task=self.task,
            asset=self.asset,
            asset_code=self.asset.asset_code,
            asset_name=self.asset.asset_name,
            location_id=str(self.location.id),
            location_name=self.location.name,
            organization=self.organization,
            created_by=self.user
        )
        self.qr_generator = QRCodeGenerator()

    def test_validate_qr_code(self):
        """Test QR code validation endpoint."""
        self._create_test_data()

        # Verify the user's organization matches
        self.assertEqual(self.user.organization_id, self.organization.id)
        self.assertEqual(self.asset.organization_id, self.organization.id)

        qr_data = self.qr_generator.generate_asset_qr_data(
            str(self.asset.id),
            self.asset.asset_code,
            str(self.organization.id)
        )

        url = '/api/inventory/scans/validate-qr/'
        data = {'qr_code': qr_data}
        client = self._make_client()
        response = client.post(url, data, format='json')

        # Debug: print response if not 200
        if response.status_code != status.HTTP_200_OK:
            print(f"Response status: {response.status_code}")
            print(f"Response data: {response.data}")
            print(f"User org_id: {self.user.organization_id}")
            print(f"Asset org_id: {self.asset.organization_id}")
            print(f"Expected org_id: {self.organization.id}")
            # Parse QR data to see what's in it
            from apps.inventory.utils.qr_code import QRCodeGenerator
            parsed = self.qr_generator.parse_qr_code(qr_data)
            print(f"Parsed QR org_id: {parsed.get('org_id')}")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['data']['valid'])

    def test_record_scan(self):
        """Test recording a scan."""
        self._create_test_data()

        qr_data = self.qr_generator.generate_asset_qr_data(
            str(self.asset.id),
            self.asset.asset_code,
            str(self.organization.id)
        )

        url = '/api/inventory/scans/'
        data = {
            'task': str(self.task.id),
            'qr_code': qr_data,
            'scan_method': 'qr',
            'scan_status': 'normal'
        }
        client = self._make_client()
        response = client.post(url, data, format='json')

        if response.status_code != status.HTTP_201_CREATED:
            print(f"Response status: {response.status_code}")
            print(f"Response data: {response.data}")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        # Check asset_code matches the created asset
        self.assertEqual(response.data['data']['asset_code'], self.asset.asset_code)

    def test_batch_scan(self):
        """Test batch scan endpoint."""
        self._create_test_data()

        qr_data1 = self.qr_generator.generate_asset_qr_data(
            str(self.asset.id),
            self.asset.asset_code,
            str(self.organization.id)
        )

        url = '/api/inventory/scans/batch-scan/'
        data = {
            'task': str(self.task.id),
            'scans': [
                {'qr_code': qr_data1, 'scan_method': 'qr'},
            ]
        }
        client = self._make_client()
        response = client.post(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['data']['succeeded'], 1)

    def test_get_scan_summary(self):
        """Test getting scan summary."""
        self._create_test_data()

        url = f'/api/inventory/scans/summary/?task={self.task.id}'
        client = self._make_client()
        response = client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)


class InventoryDifferenceAPITests(APITestCase):
    """Tests for InventoryDifference API endpoints."""

    def setUp(self):
        """Set up test data with unique codes."""
        # Clear thread-local organization context to prevent test pollution
        from apps.common.middleware import clear_current_organization
        clear_current_organization()

        self.unique_suffix = uuid.uuid4().hex[:8]

        self.organization = Organization.objects.create(
            name=f"Test Organization {self.unique_suffix}",
            code=f"TESTORG_{self.unique_suffix}"
        )
        self.user = User.objects.create_user(
            username=f"testuser_{self.unique_suffix}",
            email=f"test{self.unique_suffix}@example.com",
            organization=self.organization
        )

    def _make_client(self):
        """Create a fresh API client for each request."""
        client = APIClient()
        client.force_authenticate(user=self.user)
        client.credentials(HTTP_X_ORGANIZATION_ID=str(self.organization.id))
        return client

    def tearDown(self):
        """Clean up after each test."""
        # Clear thread-local organization context
        from apps.common.middleware import clear_current_organization
        clear_current_organization()

    def _create_test_data(self):
        """Create common test data for difference tests."""
        self.location = Location.all_objects.create(
            name="Test Location",
            path="Test Location",
            organization=self.organization
        )
        self.category = AssetCategory.all_objects.create(
            name="Test Category",
            code=f"CAT_{self.unique_suffix}",
            organization=self.organization
        )
        self.asset = Asset.all_objects.create(
            asset_code=f"ASSET_{self.unique_suffix}_001",
            asset_name="Test Asset",
            asset_category=self.category,
            location=self.location,
            purchase_price=0,
            purchase_date="2024-01-01",
            organization=self.organization,
            created_by=self.user
        )
        self.task = InventoryTask.all_objects.create(
            task_code=f"INV_{uuid.uuid4().hex[:8]}",
            task_name="Test Inventory",
            inventory_type=InventoryTask.TYPE_FULL,
                planned_date="2024-01-01",
            organization=self.organization,
            created_by=self.user
        )

    def test_list_differences(self):
        """Test listing inventory differences."""
        self._create_test_data()

        # Create some differences
        for i in range(3):
            InventoryDifference.all_objects.create(
                task=self.task,
                asset=self.asset,
                difference_type=InventoryDifference.TYPE_MISSING,
                status=InventoryDifference.STATUS_PENDING,
                organization=self.organization,
                created_by=self.user
            )

        url = '/api/inventory/differences/'
        client = self._make_client()
        response = client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(response.data['data']['count'], 3)

    def test_get_pending_differences(self):
        """Test getting pending differences."""
        self._create_test_data()

        InventoryDifference.all_objects.create(
            task=self.task,
            asset=self.asset,
            difference_type=InventoryDifference.TYPE_MISSING,
            status=InventoryDifference.STATUS_PENDING,
            organization=self.organization,
            created_by=self.user
        )

        url = f'/api/inventory/differences/pending/?task={self.task.id}'
        client = self._make_client()
        response = client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['data']['count'], 1)

    def test_resolve_difference(self):
        """Test resolving a difference."""
        self._create_test_data()

        diff = InventoryDifference.all_objects.create(
            task=self.task,
            asset=self.asset,
            difference_type=InventoryDifference.TYPE_MISSING,
            status=InventoryDifference.STATUS_PENDING,
            organization=self.organization,
            created_by=self.user
        )

        url = f'/api/inventory/differences/{diff.id}/resolve/'
        data = {
            'status': 'resolved',
            'resolution': 'Asset found in storage room'
        }
        client = self._make_client()
        response = client.post(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        diff.refresh_from_db()
        self.assertEqual(diff.status, InventoryDifference.STATUS_RESOLVED)

    def test_batch_resolve_differences(self):
        """Test batch resolving differences."""
        self._create_test_data()

        diff1 = InventoryDifference.all_objects.create(
            task=self.task,
            asset=self.asset,
            difference_type=InventoryDifference.TYPE_MISSING,
            status=InventoryDifference.STATUS_PENDING,
            organization=self.organization,
            created_by=self.user
        )
        diff2 = InventoryDifference.all_objects.create(
            id="123e4567-e89b-12d3-a456-426614174002",
            task=self.task,
            asset=self.asset,
            difference_type=InventoryDifference.TYPE_SURPLUS,
            status=InventoryDifference.STATUS_PENDING,
            organization=self.organization,
            created_by=self.user
        )

        url = '/api/inventory/differences/batch-resolve/'
        data = {
            'ids': [str(diff1.id), str(diff2.id)],
            'status': 'resolved',
            'resolution': 'Batch resolved'
        }
        client = self._make_client()
        response = client.post(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['data']['succeeded'], 2)

    def test_get_difference_summary(self):
        """Test getting difference summary."""
        self._create_test_data()

        InventoryDifference.all_objects.create(
            task=self.task,
            asset=self.asset,
            difference_type=InventoryDifference.TYPE_MISSING,
            status=InventoryDifference.STATUS_PENDING,
            organization=self.organization,
            created_by=self.user
        )

        url = f'/api/inventory/differences/summary/?task={self.task.id}'
        client = self._make_client()
        response = client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['data']['total_differences'], 1)

    def test_create_not_allowed(self):
        """Test that manual difference creation is not allowed."""
        self._create_test_data()

        url = '/api/inventory/differences/'
        data = {
            'task': str(self.task.id),
            'difference_type': InventoryDifference.TYPE_MISSING
        }
        client = self._make_client()
        response = client.post(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)


# Import for timezone
from django.utils import timezone
