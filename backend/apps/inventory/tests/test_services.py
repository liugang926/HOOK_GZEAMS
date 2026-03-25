"""
Tests for Inventory services.
"""
import uuid
from django.test import TestCase
from django.utils import timezone
from datetime import datetime

from apps.inventory.services import (
    InventoryService,
    ScanService,
    SnapshotService,
    DifferenceService,
)
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
from django.core.exceptions import ValidationError


class QRCodeGeneratorTests(TestCase):
    """Tests for QRCodeGenerator utility."""

    def setUp(self):
        """Set up test data with unique codes."""
        self.unique_suffix = uuid.uuid4().hex[:8]
        self.generator = QRCodeGenerator()
        self.organization = Organization.objects.create(
            name=f"Test Organization {self.unique_suffix}",
            code=f"TESTORG_{self.unique_suffix}"
        )

    def test_generate_asset_qr_data(self):
        """Test generating QR code data for an asset."""
        asset_id = "123e4567-e89b-12d3-a456-426614174000"
        asset_code = "ASSET001"
        org_id = str(self.organization.id)

        qr_data = self.generator.generate_asset_qr_data(asset_id, asset_code, org_id)

        import json
        parsed = json.loads(qr_data)

        self.assertEqual(parsed['type'], self.generator.TYPE_ASSET)
        self.assertEqual(parsed['asset_id'], asset_id)
        self.assertEqual(parsed['asset_code'], asset_code)
        self.assertEqual(parsed['org_id'], org_id)
        self.assertIn('checksum', parsed)
        self.assertIn('version', parsed)

    def test_parse_qr_code(self):
        """Test parsing QR code string."""
        asset_id = "123e4567-e89b-12d3-a456-426614174000"
        asset_code = "ASSET001"
        org_id = str(self.organization.id)

        qr_data = self.generator.generate_asset_qr_data(asset_id, asset_code, org_id)
        parsed = self.generator.parse_qr_code(qr_data)

        self.assertEqual(parsed['asset_id'], asset_id)
        self.assertEqual(parsed['asset_code'], asset_code)
        self.assertEqual(parsed['org_id'], org_id)

    def test_validate_qr_code_valid(self):
        """Test validating a correct QR code."""
        asset_id = "123e4567-e89b-12d3-a456-426614174000"
        asset_code = "ASSET001"
        org_id = str(self.organization.id)

        qr_data = self.generator.generate_asset_qr_data(asset_id, asset_code, org_id)

        is_valid, error_msg, parsed_data = self.generator.validate_qr_code(qr_data, asset_code, org_id)
        self.assertTrue(is_valid)
        self.assertEqual(error_msg, "Valid")

    def test_validate_qr_code_invalid_checksum(self):
        """Test validating QR code with wrong checksum."""
        import json
        qr_data = {
            "type": "asset",
            "version": "1.0",
            "asset_id": "123e4567-e89b-12d3-a456-426614174000",
            "asset_code": "ASSET001",
            "org_id": str(self.organization.id),
            "checksum": "invalid_checksum"
        }

        is_valid, error_msg, parsed_data = self.generator.validate_qr_code(
            json.dumps(qr_data),
            "ASSET001",
            str(self.organization.id)
        )
        self.assertFalse(is_valid)
        self.assertIn("Checksum mismatch", error_msg)


class InventoryServiceTests(TestCase):
    """Tests for InventoryService."""

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
        # Create test assets
        for i in range(5):
            Asset.objects.create(
                asset_code=f"ASSET_{self.unique_suffix}_{i:03d}",
                asset_name=f"Test Asset {i}",
                asset_category=self.category,
                location=self.location,
                purchase_price=0,
                purchase_date="2024-01-01",
                organization=self.organization,
                created_by=self.user
            )
        self.service = InventoryService()

    def test_create_full_inventory_task(self):
        """Test creating a full inventory task."""
        task = self.service.create_task(
            task_name="Full Inventory 2024",
            inventory_type=InventoryTask.TYPE_FULL,
                planned_date="2024-01-01",
            organization_id=str(self.organization.id),
            created_by_id=str(self.user.id)
        )

        self.assertEqual(task.inventory_type, InventoryTask.TYPE_FULL)
        self.assertEqual(task.status, InventoryTask.STATUS_DRAFT)
        self.assertIsNotNone(task.task_code)

        # Check snapshots were created
        snapshots = InventorySnapshot.objects.filter(task=task)
        self.assertEqual(snapshots.count(), 5)  # All 5 assets

    def test_create_category_inventory_task(self):
        """Test creating a category-restricted inventory task."""
        task = self.service.create_task(
            task_name="Category Inventory",
            inventory_type=InventoryTask.TYPE_CATEGORY,
            category_id=str(self.category.id),
            planned_date="2024-01-01",
            organization_id=str(self.organization.id),
            created_by_id=str(self.user.id)
        )

        self.assertEqual(task.inventory_type, InventoryTask.TYPE_CATEGORY)
        self.assertEqual(task.category, self.category)

        # Check snapshots were created for category assets only
        snapshots = InventorySnapshot.objects.filter(task=task)
        self.assertEqual(snapshots.count(), 5)

    def test_start_task(self):
        """Test starting an inventory task."""
        task = self.service.create_task(
            task_name="Test Task",
            inventory_type=InventoryTask.TYPE_FULL,
            planned_date="2024-01-01",
            organization_id=str(self.organization.id),
            created_by_id=str(self.user.id)
        )

        started_task = self.service.start_task(
            task_id=str(task.id),
            user_id=str(self.user.id)
        )

        self.assertEqual(started_task.status, InventoryTask.STATUS_IN_PROGRESS)
        self.assertIsNotNone(started_task.started_at)

    def test_complete_task_generates_differences(self):
        """Test completing a task generates differences."""
        task = self.service.create_task(
            task_name="Test Task",
            inventory_type=InventoryTask.TYPE_FULL,
            planned_date="2024-01-01",
            organization_id=str(self.organization.id),
            created_by_id=str(self.user.id)
        )

        # Start the task first
        self.service.start_task(str(task.id), str(self.user.id))

        # Create one scan
        asset = Asset.objects.first()
        InventoryScan.objects.create(
            task=task,
            asset=asset,
            qr_code="TEST_QR",
            scanned_by=self.user,
            original_location_name=self.location.name,
            actual_location_name=self.location.name,
            organization=self.organization,
            created_by=self.user
        )

        completed_task = self.service.complete_task(
            task_id=str(task.id),
            user_id=str(self.user.id)
        )

        self.assertEqual(completed_task.status, InventoryTask.STATUS_COMPLETED)
        self.assertIsNotNone(completed_task.completed_at)

        # Check differences were generated
        differences = InventoryDifference.objects.filter(task=task)
        self.assertGreater(differences.count(), 0)  # Should have missing assets

    def test_update_statistics(self):
        """Test updating task statistics."""
        task = self.service.create_task(
            task_name="Test Task",
            inventory_type=InventoryTask.TYPE_FULL,
            planned_date="2024-01-01",
            organization_id=str(self.organization.id),
            created_by_id=str(self.user.id)
        )

        # Create some scans
        for i in range(3):
            asset = Asset.objects.all()[i]
            InventoryScan.objects.create(
                task=task,
                asset=asset,
                qr_code=f"QR_{i}",
                scanned_by=self.user,
                original_location_name=self.location.name,
                actual_location_name=self.location.name,
                organization=self.organization,
                created_by=self.user
            )

        self.service.update_statistics(str(task.id))

        task.refresh_from_db()
        self.assertEqual(task.scanned_count, 3)
        self.assertEqual(task.total_count, 5)


class ScanServiceTests(TestCase):
    """Tests for ScanService."""

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
            asset_category=self.category,
            location=self.location,
            purchase_price=0,
            purchase_date="2024-01-01",
            organization=self.organization,
            created_by=self.user
        )
        self.task = InventoryTask.objects.create(
            task_code=f"INV_{self.unique_suffix}",
            task_name="Test Inventory",
            inventory_type=InventoryTask.TYPE_FULL,
            planned_date="2024-01-01",
            status=InventoryTask.STATUS_IN_PROGRESS,
            organization=self.organization,
            created_by=self.user
        )
        # Create snapshot for the asset
        InventorySnapshot.objects.create(
            task=self.task,
            asset=self.asset,
            asset_code=self.asset.asset_code,
            asset_name=self.asset.asset_name,
            location_id=str(self.location.id),
            location_name=self.location.name,
            organization=self.organization,
            created_by=self.user
        )
        self.service = ScanService()
        self.qr_generator = QRCodeGenerator()

    def test_record_scan(self):
        """Test recording a scan."""
        qr_data = self.qr_generator.generate_asset_qr_data(
            str(self.asset.id),
            self.asset.asset_code,
            str(self.organization.id)
        )

        scan = self.service.record_scan(
            task_id=str(self.task.id),
            qr_code=qr_data,
            scanned_by_id=str(self.user.id),
            organization_id=str(self.organization.id)
        )

        self.assertEqual(scan.task, self.task)
        self.assertEqual(scan.asset, self.asset)
        self.assertEqual(scan.scanned_by, self.user)

    def test_record_scan_updates_snapshot(self):
        """Test that recording a scan updates the snapshot."""
        qr_data = self.qr_generator.generate_asset_qr_data(
            str(self.asset.id),
            self.asset.asset_code,
            str(self.organization.id)
        )

        self.service.record_scan(
            task_id=str(self.task.id),
            qr_code=qr_data,
            scanned_by_id=str(self.user.id),
            organization_id=str(self.organization.id)
        )

        snapshot = InventorySnapshot.objects.get(task=self.task, asset=self.asset)
        self.assertTrue(snapshot.scanned)
        self.assertGreater(snapshot.scan_count, 0)

    def test_validate_qr_code(self):
        """Test QR code validation."""
        qr_data = self.qr_generator.generate_asset_qr_data(
            str(self.asset.id),
            self.asset.asset_code,
            str(self.organization.id)
        )

        result = self.service.validate_qr_code(
            qr_code=qr_data,
            organization_id=str(self.organization.id)
        )

        self.assertTrue(result['valid'])
        self.assertIn('asset', result)
        self.assertEqual(result['asset']['asset_code'], self.asset.asset_code)

    def test_validate_qr_code_with_task(self):
        """Test QR code validation with task check."""
        qr_data = self.qr_generator.generate_asset_qr_data(
            str(self.asset.id),
            self.asset.asset_code,
            str(self.organization.id)
        )

        result = self.service.validate_qr_code(
            qr_code=qr_data,
            organization_id=str(self.organization.id),
            task_id=str(self.task.id)
        )

        self.assertTrue(result['valid'])
        self.assertTrue(result['in_task'])

    def test_get_scan_summary(self):
        """Test getting scan summary for a task."""
        # Create some scans
        for i in range(3):
            asset = Asset.objects.create(
                asset_code=f"ASSET_{self.unique_suffix}_{i:02d}",
                purchase_price=0,
                purchase_date="2024-01-01",
                asset_category=self.category,
                asset_name=f"Asset {i}",
                organization=self.organization,
                created_by=self.user
            )
            InventorySnapshot.objects.create(
                task=self.task,
                asset=asset,
                asset_code=asset.asset_code,
                asset_name=asset.asset_name,
                organization=self.organization,
                created_by=self.user
            )
            qr_data = self.qr_generator.generate_asset_qr_data(
                str(asset.id),
                asset.asset_code,
                str(self.organization.id)
            )
            self.service.record_scan(
                task_id=str(self.task.id),
                qr_code=qr_data,
                scanned_by_id=str(self.user.id),
                organization_id=str(self.organization.id)
            )

        summary = self.service.get_scan_summary(str(self.task.id))

        self.assertEqual(summary['total_scans'], 3)
        self.assertEqual(summary['unique_assets'], 3)


class DifferenceServiceTests(TestCase):
    """Tests for DifferenceService."""

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
        self.location1 = Location.objects.create(
            name="Location 1",
            path="Location 1",
            organization=self.organization
        )
        self.location2 = Location.objects.create(
            name="Location 2",
            path="Location 2",
            organization=self.organization
        )
        self.category = AssetCategory.objects.create(
            name="Test Category",
            code=f"CAT_{self.unique_suffix}",
            organization=self.organization
        )
        self.task = InventoryTask.objects.create(
            task_code=f"INV_{self.unique_suffix}",
            task_name="Test Inventory",
            inventory_type=InventoryTask.TYPE_FULL,
            planned_date="2024-01-01",
            organization=self.organization,
            created_by=self.user
        )
        self.service = DifferenceService()
        self.qr_generator = QRCodeGenerator()

    def test_generate_missing_differences(self):
        """Test generating differences for missing assets."""
        # Create a snapshot but no scan
        asset = Asset.objects.create(
            asset_code=f"ASSET_{self.unique_suffix}_MISS",
            purchase_price=0,
            purchase_date="2024-01-01",
            asset_name="Missing Asset",
            asset_category=self.category,
            location=self.location1,
            organization=self.organization,
            created_by=self.user
        )
        InventorySnapshot.objects.create(
            task=self.task,
            asset=asset,
            asset_code=asset.asset_code,
            asset_name=asset.asset_name,
            location_name=self.location1.name,
            organization=self.organization,
            created_by=self.user
        )

        differences = self.service.generate_differences(str(self.task.id))

        missing_diffs = [d for d in differences if d.difference_type == InventoryDifference.TYPE_MISSING]
        self.assertEqual(len(missing_diffs), 1)

    def test_generate_location_differences(self):
        """Test generating differences for location changes."""
        asset = Asset.objects.create(
            asset_code=f"ASSET_{self.unique_suffix}_LOC",
            purchase_price=0,
            purchase_date="2024-01-01",
            asset_name="Moved Asset",
            asset_category=self.category,
            location=self.location1,
            organization=self.organization,
            created_by=self.user
        )
        InventorySnapshot.objects.create(
            task=self.task,
            asset=asset,
            asset_code=asset.asset_code,
            asset_name=asset.asset_name,
            location_name=self.location1.name,
            organization=self.organization,
            created_by=self.user
        )

        # Scan at different location
        qr_data = self.qr_generator.generate_asset_qr_data(
            str(asset.id),
            asset.asset_code,
            str(self.organization.id)
        )
        InventoryScan.objects.create(
            id="123e4567-e89b-12d3-a456-426614174001",
            task=self.task,
            asset=asset,
            qr_code=qr_data,
            scanned_by=self.user,
            original_location_name=self.location1.name,
            actual_location_name=self.location2.name,
            organization=self.organization,
            created_by=self.user
        )

        differences = self.service.generate_differences(str(self.task.id))

        location_diffs = [d for d in differences if d.difference_type == InventoryDifference.TYPE_LOCATION_MISMATCH]
        self.assertEqual(len(location_diffs), 1)

    def test_resolve_difference(self):
        """Test resolving a difference."""
        asset = Asset.objects.create(
            asset_code=f"ASSET_{self.unique_suffix}_RES",
            purchase_price=0,
            purchase_date="2024-01-01",
            asset_name="Test Asset",
            asset_category=self.category,
            location=self.location1,
            organization=self.organization,
            created_by=self.user
        )
        diff = InventoryDifference.objects.create(
            task=self.task,
            asset=asset,
            difference_type=InventoryDifference.TYPE_MISSING,
            status=InventoryDifference.STATUS_PENDING,
            organization=self.organization,
            created_by=self.user
        )

        resolved = self.service.resolve_difference(
            difference_id=str(diff.id),
            user_id=str(self.user.id),
            status=InventoryDifference.STATUS_RESOLVED,
            resolution="Asset found in storage"
        )

        self.assertEqual(resolved.status, InventoryDifference.STATUS_RESOLVED)
        self.assertEqual(resolved.resolution, "Asset found in storage")
        self.assertIsNotNone(resolved.resolved_at)

    def test_get_difference_summary(self):
        """Test getting difference summary."""
        # Create some differences
        asset1 = Asset.objects.create(
            asset_code=f"ASSET_{self.unique_suffix}_SUM1",
            purchase_price=0,
            purchase_date="2024-01-01",
            asset_name="Asset 1",
            asset_category=self.category,
            organization=self.organization,
            created_by=self.user
        )
        asset2 = Asset.objects.create(
            asset_code=f"ASSET_{self.unique_suffix}_SUM2",
            purchase_price=0,
            purchase_date="2024-01-01",
            asset_name="Asset 2",
            asset_category=self.category,
            organization=self.organization,
            created_by=self.user
        )

        InventoryDifference.objects.create(
            task=self.task,
            asset=asset1,
            difference_type=InventoryDifference.TYPE_MISSING,
            status=InventoryDifference.STATUS_PENDING,
            organization=self.organization,
            created_by=self.user
        )
        InventoryDifference.objects.create(
            task=self.task,
            asset=asset2,
            difference_type=InventoryDifference.TYPE_SURPLUS,
            status=InventoryDifference.STATUS_RESOLVED,
            organization=self.organization,
            created_by=self.user,
            resolved_by=self.user,
            resolved_at=timezone.now()
        )

        summary = self.service.get_difference_summary(str(self.task.id))

        self.assertEqual(summary['total_differences'], 2)
        self.assertEqual(summary['pending'], 1)
        self.assertEqual(summary['resolved'], 1)
