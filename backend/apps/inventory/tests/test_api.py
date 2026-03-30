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
    InventoryTaskExecutor,
    InventorySnapshot,
    InventoryScan,
    InventoryDifference,
    InventoryFollowUp,
    InventoryReconciliation,
    InventoryReport,
)
from apps.inventory.utils.qr_code import QRCodeGenerator
from apps.assets.models import Asset, Location, AssetCategory
from apps.organizations.models import Department, Organization
from apps.accounts.models import User
from apps.system.models import BusinessObject
from apps.lifecycle.models import Maintenance
from apps.notifications.models import Notification


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
        self.owner = User.objects.create_user(
            username=f"owner_{self.unique_suffix}",
            email=f"owner{self.unique_suffix}@example.com",
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

        self.assertEqual(response.status_code, status.HTTP_200_OK, getattr(response, 'data', None))
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

        self.assertEqual(response.status_code, status.HTTP_200_OK, getattr(response, 'data', response.content))
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

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
            getattr(response, 'data', getattr(response, 'content', b'')),
        )

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

    def test_list_task_executors(self):
        """Test listing executors for an inventory task."""
        task = InventoryTask.all_objects.create(
            task_code=f"INV_{uuid.uuid4().hex[:8]}",
            task_name="Executor Task",
            inventory_type=InventoryTask.TYPE_FULL,
            planned_date="2024-01-01",
            organization=self.organization,
            created_by=self.user,
        )
        InventoryTaskExecutor.all_objects.create(
            task=task,
            executor=self.user,
            organization=self.organization,
            created_by=self.user,
        )
        InventoryTaskExecutor.all_objects.create(
            task=task,
            executor=self.owner,
            is_primary=True,
            organization=self.organization,
            created_by=self.user,
        )

        client = self._make_client()
        response = client.get(f'/api/inventory/tasks/{task.id}/executors/')

        self.assertEqual(response.status_code, status.HTTP_200_OK, getattr(response, 'data', None))
        self.assertEqual(len(response.data['data']), 2)
        self.assertEqual(response.data['data'][0]['executor_id'], str(self.owner.id))
        self.assertIn('assigned_at', response.data['data'][0])

    def test_get_task_executor_progress(self):
        """Test per-executor progress endpoint for an inventory task."""
        task = InventoryTask.all_objects.create(
            task_code=f"INV_{uuid.uuid4().hex[:8]}",
            task_name="Executor Progress Task",
            inventory_type=InventoryTask.TYPE_FULL,
            planned_date="2024-01-01",
            status=InventoryTask.STATUS_IN_PROGRESS,
            total_count=5,
            organization=self.organization,
            created_by=self.user,
        )
        relation = InventoryTaskExecutor.all_objects.create(
            task=task,
            executor=self.user,
            organization=self.organization,
            created_by=self.user,
        )
        InventoryScan.all_objects.create(
            task=task,
            qr_code="QR-1",
            scanned_by=self.user,
            scanned_at=timezone.now(),
            scan_status=InventoryScan.STATUS_NORMAL,
            organization=self.organization,
            created_by=self.user,
        )
        InventoryScan.all_objects.create(
            task=task,
            qr_code="QR-2",
            scanned_by=self.user,
            scanned_at=timezone.now(),
            scan_status=InventoryScan.STATUS_DAMAGED,
            organization=self.organization,
            created_by=self.user,
        )

        client = self._make_client()
        response = client.get(f'/api/inventory/tasks/{task.id}/executors/progress/')

        self.assertEqual(response.status_code, status.HTTP_200_OK, getattr(response, 'data', None))
        self.assertEqual(len(response.data['data']), 1)
        row = response.data['data'][0]
        self.assertEqual(row['assignment_id'], str(relation.id))
        self.assertEqual(row['assignee_id'], str(self.user.id))
        self.assertEqual(row['scanned_count'], 2)
        self.assertEqual(row['abnormal_count'], 1)
        self.assertEqual(row['progress'], 40.0)


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
        self.owner = User.objects.create_user(
            username=f"owner_{self.unique_suffix}",
            email=f"owner{self.unique_suffix}@example.com",
            organization=self.organization
        )
        BusinessObject.objects.create(
            code='InventoryItem',
            name='Inventory Item',
            is_hardcoded=True,
            django_model_path='apps.inventory.models.InventoryDifference',
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
        self.owner = User.objects.create_user(
            username=f"owner_{self.unique_suffix}",
            email=f"owner{self.unique_suffix}@example.com",
            organization=self.organization
        )
        self.inventory_item_object = BusinessObject.objects.create(
            code='InventoryItem',
            name='Inventory Item',
            is_hardcoded=True,
            django_model_path='apps.inventory.models.InventoryDifference',
        )
        self.inventory_follow_up_object = BusinessObject.objects.create(
            code='InventoryFollowUp',
            name='Inventory Follow-up',
            is_hardcoded=True,
            django_model_path='apps.inventory.models.InventoryFollowUp',
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
        self.assertEqual(response.data['data']['pending_confirmation_count'], 1)

    def test_difference_closure_actions(self):
        """Test the staged inventory difference closure API actions."""
        self._create_test_data()

        diff = InventoryDifference.all_objects.create(
            task=self.task,
            asset=self.asset,
            difference_type=InventoryDifference.TYPE_MISSING,
            status=InventoryDifference.STATUS_PENDING,
            organization=self.organization,
            created_by=self.user
        )

        client = self._make_client()

        confirm_response = client.post(
            f'/api/inventory/differences/{diff.id}/confirm/',
            {'owner_id': str(self.owner.id)},
            format='json',
        )
        self.assertEqual(confirm_response.status_code, status.HTTP_200_OK)

        draft_response = client.post(
            f'/api/inventory/differences/{diff.id}/save-draft/',
            {
                'resolution': 'Asset confirmed as missing after recount',
                'closure_type': InventoryDifference.CLOSURE_TYPE_FINANCIAL_ADJUSTMENT,
                'linked_action_code': 'finance_adjustment',
                'evidence_refs': ['file://recount-sheet'],
                'closure_notes': 'Need finance review before approval',
            },
            format='json',
        )
        self.assertEqual(draft_response.status_code, status.HTTP_200_OK)

        review_response = client.post(
            f'/api/inventory/differences/{diff.id}/submit-review/',
            {
                'resolution': 'Asset confirmed as missing after recount',
                'closure_type': InventoryDifference.CLOSURE_TYPE_FINANCIAL_ADJUSTMENT,
            },
            format='json',
        )
        self.assertEqual(review_response.status_code, status.HTTP_200_OK)

        approve_response = client.post(
            f'/api/inventory/differences/{diff.id}/approve-resolution/',
            {},
            format='json',
        )
        self.assertEqual(approve_response.status_code, status.HTTP_200_OK)

        execute_response = client.post(
            f'/api/inventory/differences/{diff.id}/execute-resolution/',
            {},
            format='json',
        )
        self.assertEqual(execute_response.status_code, status.HTTP_200_OK)

        complete_follow_up_response = client.post(
            f'/api/inventory/differences/{diff.id}/complete-follow-up/',
            {
                'completion_notes': 'Finance acknowledgement received',
                'evidence_refs': ['ticket://finance-ack'],
            },
            format='json',
        )
        self.assertEqual(complete_follow_up_response.status_code, status.HTTP_200_OK)

        close_response = client.post(
            f'/api/inventory/differences/{diff.id}/close-difference/',
            {
                'closure_notes': 'Closed after finance acknowledgement',
                'evidence_refs': ['file://recount-sheet'],
            },
            format='json',
        )
        self.assertEqual(close_response.status_code, status.HTTP_200_OK)

        diff.refresh_from_db()
        self.assertEqual(diff.status, InventoryDifference.STATUS_CLOSED)
        self.assertEqual(diff.closure_type, InventoryDifference.CLOSURE_TYPE_FINANCIAL_ADJUSTMENT)
        self.assertEqual(diff.linked_action_code, 'finance_adjustment')
        self.assertEqual(
            diff.custom_fields.get('linked_action_execution', {}).get('follow_up_task_status'),
            InventoryFollowUp.STATUS_COMPLETED,
        )
        self.assertTrue(
            diff.custom_fields.get('linked_action_execution', {}).get('follow_up_notification_id')
        )

    def test_execute_resolution_can_create_maintenance_from_linked_action(self):
        """Test execute-resolution triggers linked maintenance creation."""
        self._create_test_data()

        diff = InventoryDifference.all_objects.create(
            task=self.task,
            asset=self.asset,
            difference_type=InventoryDifference.TYPE_DAMAGED,
            status=InventoryDifference.STATUS_APPROVED,
            resolution='Create maintenance for damaged asset',
            closure_type=InventoryDifference.CLOSURE_TYPE_REPAIR,
            linked_action_code='asset.create_maintenance',
            organization=self.organization,
            created_by=self.user,
        )

        client = self._make_client()
        response = client.post(
            f'/api/inventory/differences/{diff.id}/execute-resolution/',
            {
                'resolution': 'Create maintenance for damaged asset',
                'sync_asset': False,
                'linked_action_code': 'asset.create_maintenance',
            },
            format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        diff.refresh_from_db()
        self.assertEqual(diff.status, InventoryDifference.STATUS_RESOLVED)
        execution_state = diff.custom_fields.get('linked_action_execution', {})
        self.assertEqual(execution_state.get('status'), 'executed')
        self.assertEqual(execution_state.get('target_object_code'), 'Maintenance')

        maintenance = Maintenance.objects.get(id=execution_state.get('target_id'))
        self.assertEqual(maintenance.asset_id, self.asset.id)

    def test_send_follow_up_can_resend_manual_notification_from_object_route(self):
        """Test InventoryItem object route can resend manual follow-up reminders."""
        self._create_test_data()

        diff = InventoryDifference.all_objects.create(
            task=self.task,
            asset=self.asset,
            difference_type=InventoryDifference.TYPE_MISSING,
            status=InventoryDifference.STATUS_RESOLVED,
            resolution='Finance adjustment required',
            closure_type=InventoryDifference.CLOSURE_TYPE_FINANCIAL_ADJUSTMENT,
            linked_action_code='finance_adjustment',
            owner=self.owner,
            organization=self.organization,
            created_by=self.user,
            custom_fields={
                'linked_action_execution': {
                    'action_code': 'finance_adjustment',
                    'status': 'manual_follow_up',
                    'message': 'Linked action recorded for manual financial adjustment follow-up.',
                    'executed_at': timezone.now().isoformat(),
                    'follow_up_sent_count': 1,
                }
            },
        )

        client = self._make_client()
        response = client.post(
            f'/api/system/objects/InventoryItem/{diff.id}/send-follow-up/',
            {},
            format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        diff.refresh_from_db()
        execution_state = diff.custom_fields.get('linked_action_execution', {})
        self.assertEqual(execution_state.get('follow_up_assignee_id'), str(self.owner.id))
        self.assertEqual(execution_state.get('follow_up_sent_count'), 2)
        self.assertTrue(execution_state.get('follow_up_notification_id'))

        notification = Notification.all_objects.get(id=execution_state.get('follow_up_notification_id'))
        self.assertEqual(notification.recipient_id, self.owner.id)

        follow_up = InventoryFollowUp.all_objects.get(difference_id=diff.id)
        self.assertEqual(follow_up.status, InventoryFollowUp.STATUS_PENDING)

    def test_inventory_item_object_route_complete_follow_up_unblocks_close(self):
        """Test InventoryItem object route completes a follow-up before closing the difference."""
        self._create_test_data()

        diff = InventoryDifference.all_objects.create(
            task=self.task,
            asset=self.asset,
            difference_type=InventoryDifference.TYPE_MISSING,
            status=InventoryDifference.STATUS_APPROVED,
            resolution='Finance adjustment required',
            closure_type=InventoryDifference.CLOSURE_TYPE_FINANCIAL_ADJUSTMENT,
            linked_action_code='finance_adjustment',
            owner=self.owner,
            organization=self.organization,
            created_by=self.user,
        )

        client = self._make_client()
        execute_response = client.post(
            f'/api/system/objects/InventoryItem/{diff.id}/execute-resolution/',
            {
                'resolution': 'Finance adjustment required',
                'syncAsset': False,
                'linkedActionCode': 'finance_adjustment',
            },
            format='json',
        )
        self.assertEqual(execute_response.status_code, status.HTTP_200_OK)

        blocked_close_response = client.post(
            f'/api/system/objects/InventoryItem/{diff.id}/close-difference/',
            {
                'closureNotes': 'Attempt close before follow-up completion',
            },
            format='json',
        )
        self.assertEqual(blocked_close_response.status_code, status.HTTP_400_BAD_REQUEST)

        complete_response = client.post(
            f'/api/system/objects/InventoryItem/{diff.id}/complete-follow-up/',
            {
                'completionNotes': 'Finance adjustment posted',
                'evidenceRefs': ['ticket://finance-adjustment-1'],
            },
            format='json',
        )
        self.assertEqual(complete_response.status_code, status.HTTP_200_OK)

        close_response = client.post(
            f'/api/system/objects/InventoryItem/{diff.id}/close-difference/',
            {
                'closureNotes': 'Closed after finance completion',
                'evidenceRefs': ['ticket://finance-adjustment-1'],
            },
            format='json',
        )
        self.assertEqual(close_response.status_code, status.HTTP_200_OK)

        diff.refresh_from_db()
        self.assertEqual(diff.status, InventoryDifference.STATUS_CLOSED)
        self.assertEqual(
            diff.custom_fields.get('linked_action_execution', {}).get('follow_up_task_status'),
            InventoryFollowUp.STATUS_COMPLETED,
        )

    def test_inventory_item_object_route_retrieve_includes_unified_closure_summary(self):
        """Test InventoryItem object route exposes the unified exception closure payload."""
        self._create_test_data()

        diff = InventoryDifference.all_objects.create(
            task=self.task,
            asset=self.asset,
            difference_type=InventoryDifference.TYPE_MISSING,
            status=InventoryDifference.STATUS_CONFIRMED,
            owner=self.owner,
            organization=self.organization,
            created_by=self.user,
        )

        client = self._make_client()
        response = client.get(f'/api/system/objects/InventoryItem/{diff.id}/')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        closure_summary = response.data['data']['closure_summary']
        self.assertEqual(closure_summary['stage'], 'Awaiting review submission')
        self.assertEqual(closure_summary['owner'], self.owner.username)
        self.assertEqual(closure_summary['next_action_code'], 'submit_review')

    def test_inventory_follow_up_object_route_supports_complete_and_reopen(self):
        """Test InventoryFollowUp object route can complete and reopen follow-up tasks."""
        self._create_test_data()

        diff = InventoryDifference.all_objects.create(
            task=self.task,
            asset=self.asset,
            difference_type=InventoryDifference.TYPE_MISSING,
            status=InventoryDifference.STATUS_RESOLVED,
            owner=self.owner,
            closure_type=InventoryDifference.CLOSURE_TYPE_FINANCIAL_ADJUSTMENT,
            linked_action_code='finance_adjustment',
            organization=self.organization,
            created_by=self.user,
        )
        follow_up = InventoryFollowUp.all_objects.create(
            task=self.task,
            difference=diff,
            asset=self.asset,
            title='Finance follow-up',
            closure_type=InventoryDifference.CLOSURE_TYPE_FINANCIAL_ADJUSTMENT,
            linked_action_code='finance_adjustment',
            status=InventoryFollowUp.STATUS_PENDING,
            assignee=self.owner,
            assigned_at=timezone.now(),
            organization=self.organization,
            created_by=self.user,
        )

        client = self._make_client()
        retrieve_response = client.get(f'/api/system/objects/InventoryFollowUp/{follow_up.id}/')
        self.assertEqual(retrieve_response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            retrieve_response.data['data']['closure_summary']['next_action_code'],
            'complete',
        )

        complete_response = client.post(
            f'/api/system/objects/InventoryFollowUp/{follow_up.id}/complete/',
            {
                'completionNotes': 'Finance adjustment posted',
                'evidenceRefs': ['ticket://finance-adjustment-2'],
            },
            format='json',
        )
        self.assertEqual(complete_response.status_code, status.HTTP_200_OK)

        follow_up.refresh_from_db()
        self.assertEqual(follow_up.status, InventoryFollowUp.STATUS_COMPLETED)

        reopen_response = client.post(
            f'/api/system/objects/InventoryFollowUp/{follow_up.id}/reopen/',
            {},
            format='json',
        )
        self.assertEqual(reopen_response.status_code, status.HTTP_200_OK)

        follow_up.refresh_from_db()
        self.assertEqual(follow_up.status, InventoryFollowUp.STATUS_PENDING)

    def test_inventory_follow_up_rest_route_lists_pending_queue(self):
        """Test follow-up REST route is registered for inventory queue access."""
        self._create_test_data()

        diff = InventoryDifference.all_objects.create(
            task=self.task,
            asset=self.asset,
            difference_type=InventoryDifference.TYPE_MISSING,
            status=InventoryDifference.STATUS_RESOLVED,
            owner=self.owner,
            organization=self.organization,
            created_by=self.user,
        )
        InventoryFollowUp.all_objects.create(
            task=self.task,
            difference=diff,
            asset=self.asset,
            title='Pending finance follow-up',
            linked_action_code='finance_adjustment',
            status=InventoryFollowUp.STATUS_PENDING,
            assignee=self.owner,
            assigned_at=timezone.now(),
            organization=self.organization,
            created_by=self.user,
        )

        client = self._make_client()
        response = client.get(
            f'/api/inventory/follow-ups/?task={self.task.id}&assignee={self.owner.id}&open_only=true'
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['data']['count'], 1)
        result = response.data['data']['results'][0]
        self.assertEqual(result['status'], InventoryFollowUp.STATUS_PENDING)
        self.assertEqual(result['closure_summary']['next_action_code'], 'complete')

    def test_inventory_item_object_route_save_draft_accepts_camel_case_payload(self):
        """Test InventoryItem object route save-draft action using frontend payload shape."""
        self._create_test_data()

        diff = InventoryDifference.all_objects.create(
            task=self.task,
            asset=self.asset,
            difference_type=InventoryDifference.TYPE_MISSING,
            status=InventoryDifference.STATUS_CONFIRMED,
            organization=self.organization,
            created_by=self.user
        )

        client = self._make_client()
        response = client.post(
            f'/api/system/objects/InventoryItem/{diff.id}/save-draft/',
            {
                'resolution': 'Drafted from dynamic object route',
                'closureType': InventoryDifference.CLOSURE_TYPE_FINANCIAL_ADJUSTMENT,
                'linkedActionCode': 'finance_adjustment',
                'evidenceRefs': ['file://object-route-proof'],
                'closureNotes': 'Saved through the unified object endpoint',
            },
            format='json',
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
            getattr(response, 'data', getattr(response, 'content', b'')),
        )

        diff.refresh_from_db()
        self.assertEqual(diff.status, InventoryDifference.STATUS_CONFIRMED)
        self.assertEqual(diff.resolution, 'Drafted from dynamic object route')
        self.assertEqual(diff.closure_type, InventoryDifference.CLOSURE_TYPE_FINANCIAL_ADJUSTMENT)
        self.assertEqual(diff.linked_action_code, 'finance_adjustment')
        self.assertEqual(diff.evidence_refs, ['file://object-route-proof'])
        self.assertEqual(diff.closure_notes, 'Saved through the unified object endpoint')

    def test_inventory_item_object_route_execute_resolution_runs_linked_action(self):
        """Test InventoryItem object route execute-resolution uses camelCase payload and linked actions."""
        self._create_test_data()

        diff = InventoryDifference.all_objects.create(
            task=self.task,
            asset=self.asset,
            difference_type=InventoryDifference.TYPE_DAMAGED,
            status=InventoryDifference.STATUS_APPROVED,
            resolution='Create maintenance from object route',
            closure_type=InventoryDifference.CLOSURE_TYPE_REPAIR,
            linked_action_code='asset.create_maintenance',
            organization=self.organization,
            created_by=self.user,
        )

        client = self._make_client()
        response = client.post(
            f'/api/system/objects/InventoryItem/{diff.id}/execute-resolution/',
            {
                'resolution': 'Create maintenance from object route',
                'syncAsset': False,
                'linkedActionCode': 'asset.create_maintenance',
            },
            format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK, getattr(response, 'data', getattr(response, 'content', b'')))

        diff.refresh_from_db()
        self.assertEqual(diff.status, InventoryDifference.STATUS_RESOLVED)
        execution_state = diff.custom_fields.get('linked_action_execution', {})
        self.assertEqual(execution_state.get('status'), 'executed')
        self.assertEqual(execution_state.get('target_object_code'), 'Maintenance')

        maintenance = Maintenance.objects.get(id=execution_state.get('target_id'))
        self.assertEqual(maintenance.asset_id, self.asset.id)

    def test_task_detail_includes_difference_summary(self):
        """Test task detail payload exposes aggregated difference closure summary."""
        self._create_test_data()

        InventoryDifference.all_objects.create(
            task=self.task,
            asset=self.asset,
            difference_type=InventoryDifference.TYPE_MISSING,
            status=InventoryDifference.STATUS_PENDING,
            organization=self.organization,
            created_by=self.user
        )
        InventoryDifference.all_objects.create(
            task=self.task,
            asset=self.asset,
            difference_type=InventoryDifference.TYPE_DAMAGED,
            status=InventoryDifference.STATUS_RESOLVED,
            organization=self.organization,
            created_by=self.user,
            resolved_by=self.user,
            resolved_at=timezone.now()
        )

        client = self._make_client()
        response = client.get(f'/api/inventory/tasks/{self.task.id}/')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        summary = response.data['data']['difference_summary']
        self.assertEqual(summary['total_differences'], 2)
        self.assertEqual(summary['pending_confirmation_count'], 1)
        self.assertEqual(summary['pending_closure_count'], 1)

    def test_task_detail_difference_summary_includes_manual_follow_up_metrics(self):
        """Test task detail summary exposes manual follow-up metrics."""
        self._create_test_data()

        InventoryDifference.all_objects.create(
            task=self.task,
            asset=self.asset,
            difference_type=InventoryDifference.TYPE_MISSING,
            status=InventoryDifference.STATUS_RESOLVED,
            organization=self.organization,
            created_by=self.user,
            custom_fields={
                'linked_action_execution': {
                    'status': 'manual_follow_up',
                    'can_send_follow_up': True,
                }
            },
        )

        client = self._make_client()
        response = client.get(f'/api/inventory/tasks/{self.task.id}/')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        summary = response.data['data']['difference_summary']
        self.assertEqual(summary['manual_follow_up_total_count'], 1)
        self.assertEqual(summary['manual_follow_up_open_count'], 1)
        self.assertEqual(summary['closure_stage_label'], 'Awaiting follow-up')

    def test_inventory_item_object_route_filters_manual_follow_up_queue(self):
        """Test InventoryItem object route supports manual follow-up filtering."""
        self._create_test_data()

        manual_follow_up_diff = InventoryDifference.all_objects.create(
            task=self.task,
            asset=self.asset,
            difference_type=InventoryDifference.TYPE_MISSING,
            status=InventoryDifference.STATUS_RESOLVED,
            organization=self.organization,
            created_by=self.user,
            custom_fields={
                'linked_action_execution': {
                    'status': 'manual_follow_up',
                    'can_send_follow_up': True,
                }
            },
        )
        InventoryDifference.all_objects.create(
            task=self.task,
            asset=self.asset,
            difference_type=InventoryDifference.TYPE_DAMAGED,
            status=InventoryDifference.STATUS_RESOLVED,
            organization=self.organization,
            created_by=self.user,
            custom_fields={
                'linked_action_execution': {
                    'status': 'executed',
                }
            },
        )

        client = self._make_client()
        response = client.get(
            f'/api/system/objects/InventoryItem/?task={self.task.id}&manual_follow_up_only=true&unresolved_only=true'
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        results = response.data['data']['results']
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]['id'], str(manual_follow_up_diff.id))

    def test_inventory_item_object_route_supports_department_filter(self):
        """Test InventoryItem object route supports filtering by inventory department."""
        self._create_test_data()
        self.task.department = Department.objects.create(
            organization=self.organization,
            code=f"INV_DEPT_{self.unique_suffix}",
            name="Inventory Department",
            created_by=self.user,
        )
        self.task.save(update_fields=['department'])

        matching_diff = InventoryDifference.all_objects.create(
            task=self.task,
            asset=self.asset,
            difference_type=InventoryDifference.TYPE_MISSING,
            status=InventoryDifference.STATUS_PENDING,
            organization=self.organization,
            created_by=self.user,
        )
        other_task = InventoryTask.all_objects.create(
            task_code=f"INV_{uuid.uuid4().hex[:8]}",
            task_name="Other Department Inventory",
            inventory_type=InventoryTask.TYPE_FULL,
            planned_date="2024-01-01",
            organization=self.organization,
            created_by=self.user,
        )
        InventoryDifference.all_objects.create(
            task=other_task,
            asset=self.asset,
            difference_type=InventoryDifference.TYPE_DAMAGED,
            status=InventoryDifference.STATUS_PENDING,
            organization=self.organization,
            created_by=self.user,
        )

        client = self._make_client()
        response = client.get(
            f'/api/system/objects/InventoryItem/?department={self.task.department_id}&unresolved_only=true'
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        results = response.data['data']['results']
        self.assertEqual([item['id'] for item in results], [str(matching_diff.id)])

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


class InventoryReconciliationReportObjectRouteTests(APITestCase):
    """Tests for reconciliation and report object routes."""

    def setUp(self):
        """Create a completed inventory task with differences."""
        from apps.common.middleware import clear_current_organization

        clear_current_organization()
        self.unique_suffix = uuid.uuid4().hex[:8]

        self.organization = Organization.objects.create(
            name=f"Reconciliation Org {self.unique_suffix}",
            code=f"RECONORG_{self.unique_suffix}",
        )
        self.user = User.objects.create_user(
            username=f"recon_user_{self.unique_suffix}",
            email=f"recon{self.unique_suffix}@example.com",
            organization=self.organization,
        )
        self.owner = User.objects.create_user(
            username=f"recon_owner_{self.unique_suffix}",
            email=f"owner{self.unique_suffix}@example.com",
            organization=self.organization,
        )
        BusinessObject.objects.get_or_create(
            code='InventoryReconciliation',
            defaults={
                'name': 'Inventory Reconciliation',
                'is_hardcoded': True,
                'django_model_path': 'apps.inventory.models.InventoryReconciliation',
            },
        )
        BusinessObject.objects.get_or_create(
            code='InventoryReport',
            defaults={
                'name': 'Inventory Report',
                'is_hardcoded': True,
                'django_model_path': 'apps.inventory.models.InventoryReport',
            },
        )

        self.location = Location.all_objects.create(
            name="Reconciliation Location",
            path="Reconciliation Location",
            organization=self.organization,
        )
        self.category = AssetCategory.all_objects.create(
            name="Reconciliation Category",
            code=f"RECONCAT_{self.unique_suffix}",
            organization=self.organization,
        )
        self.asset = Asset.all_objects.create(
            asset_code=f"RECON_ASSET_{self.unique_suffix}",
            asset_name="Reconciliation Asset",
            asset_category=self.category,
            location=self.location,
            purchase_price=0,
            purchase_date="2024-01-01",
            organization=self.organization,
            created_by=self.user,
        )
        self.task = InventoryTask.all_objects.create(
            task_code=f"RECON_TASK_{self.unique_suffix}",
            task_name="Completed Inventory Task",
            inventory_type=InventoryTask.TYPE_FULL,
            planned_date="2024-01-01",
            status=InventoryTask.STATUS_COMPLETED,
            total_count=5,
            scanned_count=4,
            normal_count=3,
            missing_count=1,
            damaged_count=1,
            completed_at=timezone.now(),
            organization=self.organization,
            created_by=self.owner,
        )
        InventoryDifference.all_objects.create(
            task=self.task,
            asset=self.asset,
            difference_type=InventoryDifference.TYPE_MISSING,
            description='Missing during reconciliation test',
            status=InventoryDifference.STATUS_PENDING,
            organization=self.organization,
            created_by=self.user,
        )
        InventoryDifference.all_objects.create(
            task=self.task,
            asset=self.asset,
            difference_type=InventoryDifference.TYPE_DAMAGED,
            description='Damaged during reconciliation test',
            status=InventoryDifference.STATUS_RESOLVED,
            resolution='Sent to maintenance',
            resolved_at=timezone.now(),
            organization=self.organization,
            created_by=self.user,
        )

    def tearDown(self):
        """Clear request-scoped organization state after each test."""
        from apps.common.middleware import clear_current_organization

        clear_current_organization()

    def _make_client(self):
        """Create an authenticated client with organization context."""
        client = APIClient()
        client.force_authenticate(user=self.user)
        client.credentials(HTTP_X_ORGANIZATION_ID=str(self.organization.id))
        return client

    def test_inventory_reconciliation_object_route_supports_create_submit_approve(self):
        """Test InventoryReconciliation object create and approval actions."""
        client = self._make_client()

        create_response = client.post(
            '/api/system/objects/InventoryReconciliation/',
            {
                'task': str(self.task.id),
                'note': 'Generated from the unified object route',
            },
            format='json',
        )
        self.assertEqual(create_response.status_code, status.HTTP_201_CREATED)
        create_payload = create_response.json()['data']
        self.assertTrue(create_response.json()['success'])
        reconciliation_id = create_payload['id']
        self.assertEqual(create_payload['differenceCount'], 2)
        self.assertEqual(create_payload['adjustmentCount'], 1)

        list_response = client.get(
            f'/api/system/objects/InventoryReconciliation/?task={self.task.id}'
        )
        self.assertEqual(list_response.status_code, status.HTTP_200_OK)
        self.assertEqual(list_response.json()['data']['count'], 1)

        submit_response = client.post(
            f'/api/system/objects/InventoryReconciliation/{reconciliation_id}/submit/',
            {},
            format='json',
        )
        self.assertEqual(submit_response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            submit_response.json()['data']['status'],
            InventoryReconciliation.STATUS_SUBMITTED,
        )

        approve_response = client.post(
            f'/api/system/objects/InventoryReconciliation/{reconciliation_id}/approve/',
            {'comment': 'Approved through unified object route'},
            format='json',
        )
        self.assertEqual(approve_response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            approve_response.json()['data']['status'],
            InventoryReconciliation.STATUS_APPROVED,
        )

    def test_inventory_report_object_route_supports_generate_submit_and_export(self):
        """Test InventoryReport object create, submit, and export actions."""
        client = self._make_client()

        create_response = client.post(
            '/api/system/objects/InventoryReport/',
            {
                'task': str(self.task.id),
                'templateId': 'STANDARD',
            },
            format='json',
        )
        self.assertEqual(create_response.status_code, status.HTTP_201_CREATED)
        create_payload = create_response.json()['data']
        self.assertTrue(create_response.json()['success'])
        report_id = create_payload['id']
        self.assertEqual(create_payload['summary']['differenceCount'], 2)

        submit_response = client.post(
            f'/api/system/objects/InventoryReport/{report_id}/submit/',
            {},
            format='json',
        )
        self.assertEqual(submit_response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            submit_response.json()['data']['status'],
            InventoryReport.STATUS_PENDING_APPROVAL,
        )

        pdf_response = client.get(
            f'/api/system/objects/InventoryReport/{report_id}/export/?fileFormat=pdf'
        )
        self.assertEqual(pdf_response.status_code, status.HTTP_200_OK)
        self.assertIn('application/pdf', pdf_response['Content-Type'])

        xlsx_response = client.get(
            f'/api/system/objects/InventoryReport/{report_id}/export/?fileFormat=excel'
        )
        self.assertEqual(xlsx_response.status_code, status.HTTP_200_OK)
        self.assertIn(
            'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            xlsx_response['Content-Type'],
        )


# Import for timezone
from django.utils import timezone
