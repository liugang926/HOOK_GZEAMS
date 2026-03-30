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
    InventoryExceptionClosureService,
)
from apps.inventory.models import (
    InventoryTask,
    InventorySnapshot,
    InventoryScan,
    InventoryDifference,
    InventoryFollowUp,
)
from apps.inventory.utils.qr_code import QRCodeGenerator
from apps.assets.models import Asset, Location, AssetCategory
from apps.lifecycle.models import Maintenance
from apps.notifications.models import Notification
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
        self.owner = User.objects.create_user(
            username=f"owner_{self.unique_suffix}",
            email=f"owner{self.unique_suffix}@example.com",
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
        self.owner = User.objects.create_user(
            username=f"owner_{self.unique_suffix}",
            email=f"owner{self.unique_suffix}@example.com",
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
        self.exception_closure_service = InventoryExceptionClosureService()
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
        self.assertEqual(summary['pending_confirmation_count'], 1)
        self.assertEqual(summary['pending_closure_count'], 1)
        self.assertEqual(summary['by_type'][InventoryDifference.TYPE_MISSING], 1)
        self.assertEqual(summary['by_type'][InventoryDifference.TYPE_SURPLUS], 1)

    def test_inventory_difference_closure_flow(self):
        """Test the confirm-review-approve-execute-close lifecycle."""
        asset = Asset.objects.create(
            asset_code=f"ASSET_{self.unique_suffix}_FLOW",
            purchase_price=0,
            purchase_date="2024-01-01",
            asset_name="Flow Asset",
            asset_category=self.category,
            location=self.location1,
            organization=self.organization,
            created_by=self.user
        )
        diff = InventoryDifference.objects.create(
            task=self.task,
            asset=asset,
            difference_type=InventoryDifference.TYPE_LOCATION_MISMATCH,
            status=InventoryDifference.STATUS_PENDING,
            actual_location=self.location2.name,
            organization=self.organization,
            created_by=self.user
        )

        confirmed = self.service.confirm_difference(
            difference_id=str(diff.id),
            user_id=str(self.user.id),
            owner_id=str(self.owner.id),
        )
        self.assertEqual(confirmed.status, InventoryDifference.STATUS_CONFIRMED)
        self.assertEqual(str(confirmed.owner_id), str(self.owner.id))

        in_review = self.service.submit_review(
            difference_id=str(diff.id),
            user_id=str(self.owner.id),
            resolution="Move asset to the scanned location",
            closure_type=InventoryDifference.CLOSURE_TYPE_LOCATION_CORRECTION,
            evidence_refs=['photo://inventory/1'],
        )
        self.assertEqual(in_review.status, InventoryDifference.STATUS_IN_REVIEW)
        self.assertEqual(in_review.closure_type, InventoryDifference.CLOSURE_TYPE_LOCATION_CORRECTION)

        approved = self.service.approve_resolution(
            difference_id=str(diff.id),
            user_id=str(self.user.id),
        )
        self.assertEqual(approved.status, InventoryDifference.STATUS_APPROVED)

        resolved = self.service.execute_resolution(
            difference_id=str(diff.id),
            user_id=str(self.owner.id),
        )
        self.assertEqual(resolved.status, InventoryDifference.STATUS_RESOLVED)
        asset.refresh_from_db()
        self.assertEqual(asset.location_id, self.location2.id)

        closed = self.service.close_difference(
            difference_id=str(diff.id),
            user_id=str(self.user.id),
            closure_notes="Closure completed",
        )
        self.assertEqual(closed.status, InventoryDifference.STATUS_CLOSED)
        self.assertIsNotNone(closed.closure_completed_at)

    def test_save_difference_draft_without_status_transition(self):
        """Test saving draft handling data does not change the workflow status."""
        asset = Asset.objects.create(
            asset_code=f"ASSET_{self.unique_suffix}_DRAFT",
            purchase_price=0,
            purchase_date="2024-01-01",
            asset_name="Draft Asset",
            asset_category=self.category,
            location=self.location1,
            organization=self.organization,
            created_by=self.user
        )
        diff = InventoryDifference.objects.create(
            task=self.task,
            asset=asset,
            difference_type=InventoryDifference.TYPE_MISSING,
            status=InventoryDifference.STATUS_CONFIRMED,
            organization=self.organization,
            created_by=self.user
        )

        updated = self.service.save_draft(
            difference_id=str(diff.id),
            resolution="Asset still missing after second count",
            closure_type=InventoryDifference.CLOSURE_TYPE_FINANCIAL_ADJUSTMENT,
            linked_action_code="finance_adjustment",
            evidence_refs=["photo://draft/1", "ticket://draft/2"],
            closure_notes="Waiting for reviewer confirmation",
        )

        self.assertEqual(updated.status, InventoryDifference.STATUS_CONFIRMED)
        self.assertEqual(updated.resolution, "Asset still missing after second count")
        self.assertEqual(updated.closure_type, InventoryDifference.CLOSURE_TYPE_FINANCIAL_ADJUSTMENT)
        self.assertEqual(updated.linked_action_code, "finance_adjustment")
        self.assertEqual(updated.evidence_refs, ["photo://draft/1", "ticket://draft/2"])
        self.assertEqual(updated.closure_notes, "Waiting for reviewer confirmation")

    def test_execute_resolution_runs_linked_maintenance_action(self):
        """Test executing a linked maintenance action during difference resolution."""
        asset = Asset.objects.create(
            asset_code=f"ASSET_{self.unique_suffix}_MAINT",
            purchase_price=0,
            purchase_date="2024-01-01",
            asset_name="Maintenance Asset",
            asset_category=self.category,
            location=self.location1,
            organization=self.organization,
            created_by=self.user
        )
        diff = InventoryDifference.objects.create(
            task=self.task,
            asset=asset,
            difference_type=InventoryDifference.TYPE_DAMAGED,
            status=InventoryDifference.STATUS_APPROVED,
            resolution="Create a maintenance record for inspection",
            closure_type=InventoryDifference.CLOSURE_TYPE_REPAIR,
            linked_action_code="asset.create_maintenance",
            organization=self.organization,
            created_by=self.user
        )

        resolved = self.service.execute_resolution(
            difference_id=str(diff.id),
            user_id=str(self.user.id),
            sync_asset=False,
        )

        self.assertEqual(resolved.status, InventoryDifference.STATUS_RESOLVED)
        execution_state = resolved.custom_fields.get('linked_action_execution', {})
        self.assertEqual(execution_state.get('status'), 'executed')
        self.assertEqual(execution_state.get('action_code'), 'asset.create_maintenance')
        self.assertEqual(execution_state.get('target_object_code'), 'Maintenance')

        maintenance = Maintenance.objects.get(id=execution_state.get('target_id'))
        self.assertEqual(maintenance.asset_id, asset.id)
        self.assertEqual(maintenance.reporter_id, self.user.id)

    def test_execute_resolution_creates_manual_follow_up_notification(self):
        """Test manual follow-up execution creates an inbox notification for the owner."""
        asset = Asset.objects.create(
            asset_code=f"ASSET_{self.unique_suffix}_FOLLOW",
            purchase_price=0,
            purchase_date="2024-01-01",
            asset_name="Follow-up Asset",
            asset_category=self.category,
            location=self.location1,
            organization=self.organization,
            created_by=self.user
        )
        diff = InventoryDifference.objects.create(
            task=self.task,
            asset=asset,
            difference_type=InventoryDifference.TYPE_MISSING,
            status=InventoryDifference.STATUS_APPROVED,
            resolution="Finance adjustment required",
            closure_type=InventoryDifference.CLOSURE_TYPE_FINANCIAL_ADJUSTMENT,
            linked_action_code="finance_adjustment",
            owner=self.owner,
            organization=self.organization,
            created_by=self.user
        )

        resolved = self.service.execute_resolution(
            difference_id=str(diff.id),
            user_id=str(self.user.id),
            sync_asset=False,
        )

        execution_state = resolved.custom_fields.get('linked_action_execution', {})
        self.assertEqual(execution_state.get('status'), 'manual_follow_up')
        self.assertEqual(execution_state.get('follow_up_assignee_id'), str(self.owner.id))
        self.assertEqual(execution_state.get('follow_up_sent_count'), 1)
        self.assertTrue(execution_state.get('follow_up_notification_id'))
        self.assertEqual(execution_state.get('follow_up_task_status'), InventoryFollowUp.STATUS_PENDING)
        self.assertTrue(execution_state.get('follow_up_task_code'))
        self.assertTrue(execution_state.get('follow_up_task_url'))

        notification = Notification.all_objects.get(id=execution_state.get('follow_up_notification_id'))
        self.assertEqual(notification.recipient_id, self.owner.id)
        self.assertEqual(notification.organization_id, self.organization.id)
        self.assertEqual(notification.data.get('actionUrl'), f'/objects/InventoryItem/{diff.id}')

        follow_up = InventoryFollowUp.all_objects.get(difference_id=diff.id)
        self.assertEqual(follow_up.assignee_id, self.owner.id)
        self.assertEqual(follow_up.status, InventoryFollowUp.STATUS_PENDING)
        self.assertEqual(follow_up.linked_action_code, 'finance_adjustment')

    def test_get_difference_summary_includes_manual_follow_up_open_count(self):
        """Test difference summary exposes open manual follow-up counts and stage."""
        asset = Asset.objects.create(
            asset_code=f"ASSET_{self.unique_suffix}_FOLLOW_SUM",
            purchase_price=0,
            purchase_date="2024-01-01",
            asset_name="Follow-up Summary Asset",
            asset_category=self.category,
            location=self.location1,
            organization=self.organization,
            created_by=self.user
        )
        InventoryDifference.objects.create(
            task=self.task,
            asset=asset,
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

        summary = self.service.get_difference_summary(str(self.task.id))

        self.assertEqual(summary['manual_follow_up_total_count'], 1)
        self.assertEqual(summary['manual_follow_up_open_count'], 1)
        self.assertEqual(summary['closure_stage_label'], 'Awaiting follow-up')
        self.assertEqual(summary['closure_blocker'], 'Manual downstream follow-up is still pending completion.')

    def test_get_difference_summary_counts_follow_up_ledger_rows(self):
        """Test difference summary prefers follow-up ledger rows when they exist."""
        asset = Asset.objects.create(
            asset_code=f"ASSET_{self.unique_suffix}_FOLLOW_LEDGER",
            purchase_price=0,
            purchase_date="2024-01-01",
            asset_name="Follow-up Ledger Asset",
            asset_category=self.category,
            location=self.location1,
            organization=self.organization,
            created_by=self.user
        )
        diff = InventoryDifference.objects.create(
            task=self.task,
            asset=asset,
            difference_type=InventoryDifference.TYPE_MISSING,
            status=InventoryDifference.STATUS_RESOLVED,
            resolution="Finance adjustment required",
            closure_type=InventoryDifference.CLOSURE_TYPE_FINANCIAL_ADJUSTMENT,
            linked_action_code="finance_adjustment",
            owner=self.owner,
            organization=self.organization,
            created_by=self.user,
        )
        InventoryFollowUp.all_objects.create(
            task=self.task,
            difference=diff,
            asset=asset,
            title="Manual finance follow-up",
            closure_type=InventoryDifference.CLOSURE_TYPE_FINANCIAL_ADJUSTMENT,
            linked_action_code="finance_adjustment",
            status=InventoryFollowUp.STATUS_PENDING,
            assignee=self.owner,
            assigned_at=timezone.now(),
            organization=self.organization,
            created_by=self.user,
        )

        summary = self.service.get_difference_summary(str(self.task.id))

        self.assertEqual(summary['manual_follow_up_total_count'], 1)
        self.assertEqual(summary['manual_follow_up_open_count'], 1)
        self.assertEqual(summary['closure_stage_label'], 'Awaiting follow-up')

    def test_send_follow_up_resends_manual_follow_up_notification(self):
        """Test sending a follow-up reminder refreshes notification metadata."""
        asset = Asset.objects.create(
            asset_code=f"ASSET_{self.unique_suffix}_REMIND",
            purchase_price=0,
            purchase_date="2024-01-01",
            asset_name="Reminder Asset",
            asset_category=self.category,
            location=self.location1,
            organization=self.organization,
            created_by=self.user
        )
        diff = InventoryDifference.objects.create(
            task=self.task,
            asset=asset,
            difference_type=InventoryDifference.TYPE_MISSING,
            status=InventoryDifference.STATUS_RESOLVED,
            resolution="Finance adjustment required",
            closure_type=InventoryDifference.CLOSURE_TYPE_FINANCIAL_ADJUSTMENT,
            linked_action_code="finance_adjustment",
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

        updated = self.service.send_follow_up(
            difference_id=str(diff.id),
            user_id=str(self.user.id),
        )

        execution_state = updated.custom_fields.get('linked_action_execution', {})
        self.assertEqual(execution_state.get('follow_up_assignee_id'), str(self.owner.id))
        self.assertEqual(execution_state.get('follow_up_sent_count'), 2)
        self.assertTrue(execution_state.get('follow_up_notification_id'))
        self.assertIn('Follow-up reminder sent', execution_state.get('message', ''))

    def test_complete_follow_up_unblocks_difference_closure(self):
        """Test a difference cannot close until the manual follow-up is completed."""
        asset = Asset.objects.create(
            asset_code=f"ASSET_{self.unique_suffix}_FOLLOW_CLOSE",
            purchase_price=0,
            purchase_date="2024-01-01",
            asset_name="Follow-up Close Asset",
            asset_category=self.category,
            location=self.location1,
            organization=self.organization,
            created_by=self.user
        )
        diff = InventoryDifference.objects.create(
            task=self.task,
            asset=asset,
            difference_type=InventoryDifference.TYPE_MISSING,
            status=InventoryDifference.STATUS_APPROVED,
            resolution="Finance adjustment required",
            closure_type=InventoryDifference.CLOSURE_TYPE_FINANCIAL_ADJUSTMENT,
            linked_action_code="finance_adjustment",
            owner=self.owner,
            organization=self.organization,
            created_by=self.user
        )

        resolved = self.service.execute_resolution(
            difference_id=str(diff.id),
            user_id=str(self.user.id),
            sync_asset=False,
        )

        with self.assertRaises(ValidationError):
            self.service.close_difference(
                difference_id=str(diff.id),
                user_id=str(self.user.id),
                closure_notes="Attempted before follow-up completion",
            )

        updated = self.service.complete_follow_up(
            difference_id=str(diff.id),
            user_id=str(self.owner.id),
            completion_notes="Finance adjustment posted",
            evidence_refs=['ticket://finance-adjustment-1'],
        )

        execution_state = updated.custom_fields.get('linked_action_execution', {})
        self.assertEqual(execution_state.get('follow_up_task_status'), InventoryFollowUp.STATUS_COMPLETED)
        self.assertFalse(execution_state.get('can_send_follow_up'))

        closed = self.service.close_difference(
            difference_id=str(diff.id),
            user_id=str(self.user.id),
            closure_notes="Closed after finance completion",
        )
        self.assertEqual(closed.status, InventoryDifference.STATUS_CLOSED)

    def test_inventory_exception_closure_summary_normalizes_difference_state(self):
        """Test unified closure summary for differences includes next action and blocker."""
        asset = Asset.objects.create(
            asset_code=f"ASSET_{self.unique_suffix}_SUMMARY",
            purchase_price=0,
            purchase_date="2024-01-01",
            asset_name="Summary Asset",
            asset_category=self.category,
            location=self.location1,
            organization=self.organization,
            created_by=self.user,
        )
        diff = InventoryDifference.objects.create(
            task=self.task,
            asset=asset,
            difference_type=InventoryDifference.TYPE_MISSING,
            status=InventoryDifference.STATUS_CONFIRMED,
            owner=self.owner,
            organization=self.organization,
            created_by=self.user,
        )

        summary = self.exception_closure_service.build_difference_summary(diff)

        self.assertEqual(summary['stage'], 'Awaiting review submission')
        self.assertEqual(summary['owner'], self.owner.username)
        self.assertEqual(summary['next_action_code'], 'submit_review')
        self.assertIn('review', summary['blocker'].lower())

    def test_inventory_exception_closure_summary_normalizes_follow_up_state(self):
        """Test unified closure summary for follow-up tasks exposes completion action."""
        asset = Asset.objects.create(
            asset_code=f"ASSET_{self.unique_suffix}_FOLLOW_SUMMARY",
            purchase_price=0,
            purchase_date="2024-01-01",
            asset_name="Follow-up Summary Asset",
            asset_category=self.category,
            location=self.location1,
            organization=self.organization,
            created_by=self.user,
        )
        diff = InventoryDifference.objects.create(
            task=self.task,
            asset=asset,
            difference_type=InventoryDifference.TYPE_MISSING,
            status=InventoryDifference.STATUS_RESOLVED,
            owner=self.owner,
            organization=self.organization,
            created_by=self.user,
        )
        follow_up = InventoryFollowUp.objects.create(
            task=self.task,
            difference=diff,
            asset=asset,
            title='Finance follow-up',
            status=InventoryFollowUp.STATUS_PENDING,
            assignee=self.owner,
            assigned_at=timezone.now(),
            organization=self.organization,
            created_by=self.user,
        )

        summary = self.exception_closure_service.build_follow_up_summary(follow_up)

        self.assertEqual(summary['stage'], 'Awaiting follow-up')
        self.assertEqual(summary['owner'], self.owner.username)
        self.assertEqual(summary['next_action_code'], 'complete')
        self.assertIn('pending', summary['blocker'].lower())
