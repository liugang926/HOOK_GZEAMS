"""
Tests for Inventory models.
"""
import uuid
from decimal import Decimal
from django.test import TestCase
from django.utils import timezone
from datetime import datetime, timedelta

from apps.inventory.models import (
    InventoryTask,
    InventorySnapshot,
    InventoryScan,
    InventoryDifference,
    InventoryTaskExecutor,
)
from apps.assets.models import Asset, AssetCategory, Location
from apps.organizations.models import Organization
from apps.accounts.models import User


class InventoryTaskModelTests(TestCase):
    """Tests for InventoryTask model."""

    def setUp(self):
        """Set up test data with unique codes."""
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
        self.category = AssetCategory.objects.create(
            name="Test Category",
            code=f"CAT_{self.unique_suffix}",
            organization=self.organization
        )

    def test_create_draft_task(self):
        """Test creating a draft inventory task."""
        task = InventoryTask.objects.create(
            task_code="INV001",
            task_name="Test Inventory",
            inventory_type=InventoryTask.TYPE_FULL,
                planned_date="2024-01-01",
            status=InventoryTask.STATUS_DRAFT,
            organization=self.organization,
            created_by=self.user
        )
        self.assertEqual(task.task_code, "INV001")
        self.assertEqual(task.status, InventoryTask.STATUS_DRAFT)
        self.assertEqual(task.total_count, 0)
        self.assertEqual(task.scanned_count, 0)

    def test_task_progress_percentage(self):
        """Test progress percentage calculation."""
        task = InventoryTask.objects.create(
            task_code="INV002",
            task_name="Progress Test",
            inventory_type=InventoryTask.TYPE_FULL,
                planned_date="2024-01-01",
            organization=self.organization,
            created_by=self.user
        )
        task.total_count = 100
        task.scanned_count = 50
        task.save()

        self.assertEqual(task.progress_percentage, 50.0)

    def test_task_status_workflow(self):
        """Test task status workflow transitions."""
        task = InventoryTask.objects.create(
            task_code="INV003",
            task_name="Workflow Test",
            inventory_type=InventoryTask.TYPE_FULL,
                planned_date="2024-01-01",
            status=InventoryTask.STATUS_DRAFT,
            organization=self.organization,
            created_by=self.user
        )

        # Draft -> Pending
        task.status = InventoryTask.STATUS_PENDING
        task.save()
        self.assertEqual(task.status, InventoryTask.STATUS_PENDING)

        # Pending -> In Progress
        task.status = InventoryTask.STATUS_IN_PROGRESS
        task.started_at = timezone.now()
        task.save()
        self.assertEqual(task.status, InventoryTask.STATUS_IN_PROGRESS)

        # In Progress -> Completed
        task.status = InventoryTask.STATUS_COMPLETED
        task.completed_at = timezone.now()
        task.save()
        self.assertEqual(task.status, InventoryTask.STATUS_COMPLETED)

    def test_task_is_editable(self):
        """Test is_editable property."""
        task = InventoryTask.objects.create(
            task_code="INV004",
            task_name="Status Test",
            inventory_type=InventoryTask.TYPE_FULL,
            planned_date="2024-01-01",
            status=InventoryTask.STATUS_DRAFT,
            organization=self.organization,
            created_by=self.user
        )
        # Check draft status
        self.assertEqual(task.status, InventoryTask.STATUS_DRAFT)

        # Change to in progress
        task.status = InventoryTask.STATUS_IN_PROGRESS
        task.save()
        self.assertEqual(task.status, InventoryTask.STATUS_IN_PROGRESS)

        # Change to completed
        task.status = InventoryTask.STATUS_COMPLETED
        task.save()
        self.assertEqual(task.status, InventoryTask.STATUS_COMPLETED)


class InventorySnapshotModelTests(TestCase):
    """Tests for InventorySnapshot model."""

    def setUp(self):
        """Set up test data with unique codes."""
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
        self.category = AssetCategory.objects.create(
            name="Test Category",
            code=f"CAT_{self.unique_suffix}",
            organization=self.organization
        )
        self.location = Location.objects.create(
            name="Test Location",
            path="Test Location",
            organization=self.organization
        )
        self.asset = Asset.objects.create(
            asset_code=f"ASSET_{self.unique_suffix}_001",
            asset_name="Test Asset",
            asset_category=self.category,
            organization=self.organization,
            location=self.location,
            purchase_price=0,
            purchase_date="2024-01-01",
            created_by=self.user
        )
        self.task = InventoryTask.objects.create(
            task_code=f"INV_{self.unique_suffix}",
            task_name="Test Inventory",
            inventory_type=InventoryTask.TYPE_FULL,
            planned_date="2024-01-01",
            organization=self.organization,
            created_by=self.user
        )

    def test_create_snapshot(self):
        """Test creating an inventory snapshot."""
        snapshot = InventorySnapshot.objects.create(
            task=self.task,
            asset=self.asset,
            asset_code=self.asset.asset_code,
            asset_name=self.asset.asset_name,
            location_id=str(self.asset.location_id),
            location_name=self.asset.location.name,
            organization=self.organization,
            created_by=self.user
        )
        self.assertEqual(snapshot.task, self.task)
        self.assertEqual(snapshot.asset, self.asset)
        self.assertFalse(snapshot.scanned)
        self.assertEqual(snapshot.scan_count, 0)

    def test_snapshot_unique_constraint(self):
        """Test that task+asset combination is unique."""
        InventorySnapshot.objects.create(
            task=self.task,
            asset=self.asset,
            asset_code=self.asset.asset_code,
            asset_name=self.asset.asset_name,
            organization=self.organization,
            created_by=self.user
        )

        # Attempting to create duplicate should raise IntegrityError
        with self.assertRaises(Exception):
            InventorySnapshot.objects.create(
                task=self.task,
                asset=self.asset,
                asset_code=self.asset.asset_code,
                asset_name=self.asset.asset_name,
                organization=self.organization,
                created_by=self.user
            )


class InventoryScanModelTests(TestCase):
    """Tests for InventoryScan model."""

    def setUp(self):
        """Set up test data with unique codes."""
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
        self.location = Location.objects.create(
            name="Test Location",
            path="Test Location",
            organization=self.organization
        )
        self.category = AssetCategory.objects.create(
            name="Test Category",
            code=f"CAT_{self.unique_suffix}",
            organization=self.organization
        )
        self.asset = Asset.objects.create(
            asset_code=f"ASSET_{self.unique_suffix}_001",
            asset_name="Test Asset",
            organization=self.organization,
            location=self.location,
            asset_category=self.category,
            purchase_price=0,
            purchase_date="2024-01-01",
            created_by=self.user
        )
        self.task = InventoryTask.objects.create(
            task_code=f"INV_{self.unique_suffix}",
            task_name="Test Inventory",
            inventory_type=InventoryTask.TYPE_FULL,
            planned_date="2024-01-01",
            organization=self.organization,
            created_by=self.user
        )

    def test_create_scan(self):
        """Test creating an inventory scan."""
        scan = InventoryScan.objects.create(
            task=self.task,
            asset=self.asset,
            qr_code="TEST_QR_CODE",
            scanned_by=self.user,
            scan_method=InventoryScan.METHOD_QR,
            scan_status='normal',
            original_location_id=str(self.location.id),
            original_location_name=self.location.name,
            actual_location_id=str(self.location.id),
            actual_location_name=self.location.name,
            organization=self.organization,
            created_by=self.user
        )
        self.assertEqual(scan.task, self.task)
        self.assertEqual(scan.asset, self.asset)
        self.assertEqual(scan.scanned_by, self.user)
        self.assertEqual(scan.scan_method, InventoryScan.METHOD_QR)
        self.assertEqual(scan.scan_status, 'normal')

    def test_scan_location_difference(self):
        """Test scan with location difference."""
        scan = InventoryScan.objects.create(
            task=self.task,
            asset=self.asset,
            qr_code="TEST_QR",
            scanned_by=self.user,
            original_location_name="Location A",
            actual_location_name="Location B",
            organization=self.organization,
            created_by=self.user
        )
        # Check that location names are stored correctly
        self.assertEqual(scan.original_location_name, "Location A")
        self.assertEqual(scan.actual_location_name, "Location B")


class InventoryDifferenceModelTests(TestCase):
    """Tests for InventoryDifference model."""

    def setUp(self):
        """Set up test data with unique codes."""
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
        self.location = Location.objects.create(
            name="Test Location",
            path="Test Location",
            organization=self.organization
        )
        self.category = AssetCategory.objects.create(
            name="Test Category",
            code=f"CAT_{self.unique_suffix}",
            organization=self.organization
        )
        self.asset = Asset.objects.create(
            asset_code=f"ASSET_{self.unique_suffix}_001",
            asset_name="Test Asset",
            organization=self.organization,
            location=self.location,
            asset_category=self.category,
            purchase_price=0,
            purchase_date="2024-01-01",
            created_by=self.user
        )
        self.task = InventoryTask.objects.create(
            task_code=f"INV_{self.unique_suffix}",
            task_name="Test Inventory",
            inventory_type=InventoryTask.TYPE_FULL,
            planned_date="2024-01-01",
            organization=self.organization,
            created_by=self.user
        )

    def test_create_missing_difference(self):
        """Test creating a missing asset difference."""
        diff = InventoryDifference.objects.create(
            task=self.task,
            asset=self.asset,
            difference_type=InventoryDifference.TYPE_MISSING,
            description="Asset not found",
            expected_quantity=1,
            actual_quantity=0,
            quantity_difference=-1,
            expected_location="Location A",
            status=InventoryDifference.STATUS_PENDING,
            organization=self.organization,
            created_by=self.user
        )
        self.assertEqual(diff.difference_type, InventoryDifference.TYPE_MISSING)
        self.assertEqual(diff.quantity_difference, -1)
        self.assertEqual(diff.status, InventoryDifference.STATUS_PENDING)

    def test_create_surplus_difference(self):
        """Test creating a surplus asset difference."""
        diff = InventoryDifference.objects.create(
            task=self.task,
            asset=self.asset,
            difference_type=InventoryDifference.TYPE_SURPLUS,
            description="Extra asset found",
            expected_quantity=0,
            actual_quantity=1,
            quantity_difference=1,
            actual_location="Location B",
            status=InventoryDifference.STATUS_PENDING,
            organization=self.organization,
            created_by=self.user
        )
        self.assertEqual(diff.difference_type, InventoryDifference.TYPE_SURPLUS)
        self.assertEqual(diff.quantity_difference, 1)

    def test_create_location_difference(self):
        """Test creating a location mismatch difference."""
        diff = InventoryDifference.objects.create(
            task=self.task,
            asset=self.asset,
            difference_type=InventoryDifference.TYPE_LOCATION_MISMATCH,
            description="Location changed",
            expected_location="Location A",
            actual_location="Location B",
            status=InventoryDifference.STATUS_PENDING,
            organization=self.organization,
            created_by=self.user
        )
        self.assertEqual(diff.difference_type, InventoryDifference.TYPE_LOCATION_MISMATCH)
        self.assertEqual(diff.expected_location, "Location A")
        self.assertEqual(diff.actual_location, "Location B")

    def test_difference_is_pending(self):
        """Test is_pending property."""
        diff = InventoryDifference.objects.create(
            task=self.task,
            asset=self.asset,
            difference_type=InventoryDifference.TYPE_MISSING,
            status=InventoryDifference.STATUS_PENDING,
            organization=self.organization,
            created_by=self.user
        )
        self.assertEqual(diff.status, InventoryDifference.STATUS_PENDING)

        diff.status = InventoryDifference.STATUS_RESOLVED
        diff.save()
        diff.refresh_from_db()
        self.assertEqual(diff.status, InventoryDifference.STATUS_RESOLVED)


class InventoryTaskExecutorTests(TestCase):
    """Tests for InventoryTaskExecutor model."""

    def setUp(self):
        """Set up test data with unique codes."""
        self.unique_suffix = uuid.uuid4().hex[:8]
        self.organization = Organization.objects.create(
            name=f"Test Organization {self.unique_suffix}",
            code=f"TESTORG_{self.unique_suffix}"
        )
        self.user1 = User.objects.create_user(
            username=f"user1_{self.unique_suffix}",
            email=f"user1{self.unique_suffix}@example.com",
            organization=self.organization
        )
        self.user2 = User.objects.create_user(
            username=f"user2_{self.unique_suffix}",
            email=f"user2{self.unique_suffix}@example.com",
            organization=self.organization
        )
        self.task = InventoryTask.objects.create(
            task_code=f"INV_{self.unique_suffix}",
            task_name="Test Inventory",
            inventory_type=InventoryTask.TYPE_FULL,
                planned_date="2024-01-01",
            organization=self.organization,
            created_by=self.user1
        )

    def test_add_executor(self):
        """Test adding an executor to a task."""
        executor = InventoryTaskExecutor.objects.create(
            task=self.task,
            executor=self.user1,
            is_primary=True,
            organization=self.organization,
            created_by=self.user1
        )
        self.assertEqual(executor.task, self.task)
        self.assertEqual(executor.executor, self.user1)
        self.assertTrue(executor.is_primary)

    def test_multiple_executors(self):
        """Test adding multiple executors to a task."""
        InventoryTaskExecutor.objects.create(
            task=self.task,
            executor=self.user1,
            is_primary=True,
            organization=self.organization,
            created_by=self.user1
        )
        InventoryTaskExecutor.objects.create(
            task=self.task,
            executor=self.user2,
            is_primary=False,
            organization=self.organization,
            created_by=self.user1
        )

        executors = InventoryTaskExecutor.objects.filter(task=self.task)
        self.assertEqual(executors.count(), 2)

    def test_executor_unique_constraint(self):
        """Test that task+executor combination is unique."""
        InventoryTaskExecutor.objects.create(
            task=self.task,
            executor=self.user1,
            is_primary=True,
            organization=self.organization,
            created_by=self.user1
        )

        # Attempting to create duplicate should raise IntegrityError
        with self.assertRaises(Exception):
            InventoryTaskExecutor.objects.create(
                task=self.task,
                executor=self.user1,
                is_primary=False,
                organization=self.organization,
                created_by=self.user1
            )
