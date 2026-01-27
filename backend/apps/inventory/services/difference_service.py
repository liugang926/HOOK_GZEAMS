"""
Difference service for managing inventory differences.
"""
import uuid
from datetime import datetime
from typing import List, Dict, Optional, Any
from django.db import transaction
from django.utils.translation import gettext_lazy as _
from django.core.exceptions import ValidationError
from django.utils import timezone

from apps.common.services.base_crud import BaseCRUDService
from apps.inventory.models import (
    InventoryDifference,
    InventorySnapshot,
    InventoryScan,
    InventoryTask,
)
from apps.assets.models import Asset


class DifferenceService(BaseCRUDService):
    """Service for inventory difference management."""

    def __init__(self):
        super().__init__(InventoryDifference)

    def generate_differences(self, task_id: str) -> List[InventoryDifference]:
        """
        Generate differences for a task by comparing snapshots and scans.

        Args:
            task_id: Task ID

        Returns:
            List of created InventoryDifference instances
        """
        task = InventoryTask.objects.get(id=task_id)

        with transaction.atomic():
            # Get all snapshots for the task
            snapshots = InventorySnapshot.objects.filter(
                task_id=task_id,
                is_deleted=False
            ).select_related('asset')

            # Get all scans for the task
            scans = {
                scan.asset_id: scan
                for scan in InventoryScan.objects.filter(
                    task_id=task_id,
                    is_deleted=False
                )
            }

            differences_to_create = []

            for snapshot in snapshots:
                asset_id = snapshot.asset_id
                scan = scans.get(asset_id)

                # Check for missing assets
                if scan is None:
                    differences_to_create.append(
                        self._create_missing_difference(snapshot)
                    )
                else:
                    # Check for location change
                    if self._has_location_changed(snapshot, scan):
                        differences_to_create.append(
                            self._create_location_difference(snapshot, scan)
                        )

                    # Check for custodian change
                    if self._has_custodian_changed(snapshot, scan):
                        differences_to_create.append(
                            self._create_custodian_difference(snapshot, scan)
                        )

                    # Check for damaged status
                    if scan.scan_status == 'damaged':
                        differences_to_create.append(
                            self._create_damaged_difference(snapshot, scan)
                        )

            # Check for surplus (scanned assets not in snapshot)
            scanned_asset_ids = set(scans.keys())
            snapshot_asset_ids = {s.asset_id for s in snapshots}
            surplus_asset_ids = scanned_asset_ids - snapshot_asset_ids

            for asset_id in surplus_asset_ids:
                scan = scans[asset_id]
                differences_to_create.append(
                    self._create_surplus_difference(task, scan)
                )

            # Create all differences
            if differences_to_create:
                InventoryDifference.objects.bulk_create(differences_to_create)

            return list(InventoryDifference.objects.filter(
                task_id=task_id,
                is_deleted=False
            ))

    def _create_missing_difference(self, snapshot: InventorySnapshot) -> InventoryDifference:
        """Create a missing asset difference record."""
        return InventoryDifference(
            id=uuid.uuid4(),
            task_id=snapshot.task_id,
            asset_id=snapshot.asset_id,
            difference_type=InventoryDifference.TYPE_MISSING,
            description=_("Asset not scanned during inventory"),
            expected_quantity=1,
            actual_quantity=0,
            quantity_difference=-1,
            expected_location=snapshot.location_name or '',
            actual_location='',
            expected_custodian=snapshot.custodian_name or '',
            actual_custodian='',
            status=InventoryDifference.STATUS_PENDING,
            organization_id=snapshot.organization_id,
        )

    def _create_location_difference(
        self,
        snapshot: InventorySnapshot,
        scan: InventoryScan
    ) -> InventoryDifference:
        """Create a location change difference record."""
        return InventoryDifference(
            id=uuid.uuid4(),
            task_id=snapshot.task_id,
            asset_id=snapshot.asset_id,
            difference_type=InventoryDifference.TYPE_LOCATION_MISMATCH,
            description=_("Asset location changed from {expected} to {actual}").format(
                expected=snapshot.location_name or '',
                actual=scan.actual_location_name or ''
            ),
            expected_location=snapshot.location_name or '',
            actual_location=scan.actual_location_name or '',
            expected_custodian=snapshot.custodian_name or '',
            actual_custodian=scan.actual_custodian_name or '',
            status=InventoryDifference.STATUS_PENDING,
            organization_id=snapshot.organization_id,
        )

    def _create_custodian_difference(
        self,
        snapshot: InventorySnapshot,
        scan: InventoryScan
    ) -> InventoryDifference:
        """Create a custodian change difference record."""
        return InventoryDifference(
            id=uuid.uuid4(),
            task_id=snapshot.task_id,
            asset_id=snapshot.asset_id,
            difference_type=InventoryDifference.TYPE_CUSTODIAN_MISMATCH,
            description=_("Asset custodian changed from {expected} to {actual}").format(
                expected=snapshot.custodian_name or '',
                actual=scan.actual_custodian_name or ''
            ),
            expected_location=snapshot.location_name or '',
            actual_location=scan.actual_location_name or '',
            expected_custodian=snapshot.custodian_name or '',
            actual_custodian=scan.actual_custodian_name or '',
            status=InventoryDifference.STATUS_PENDING,
            organization_id=snapshot.organization_id,
        )

    def _create_damaged_difference(
        self,
        snapshot: InventorySnapshot,
        scan: InventoryScan
    ) -> InventoryDifference:
        """Create a damaged asset difference record."""
        return InventoryDifference(
            id=uuid.uuid4(),
            task_id=snapshot.task_id,
            asset_id=snapshot.asset_id,
            difference_type=InventoryDifference.TYPE_DAMAGED,
            description=_("Asset reported as damaged"),
            expected_quantity=1,
            actual_quantity=1,
            quantity_difference=0,
            expected_location=snapshot.location_name or '',
            actual_location=scan.actual_location_name or '',
            expected_custodian=snapshot.custodian_name or '',
            actual_custodian=scan.actual_custodian_name or '',
            status=InventoryDifference.STATUS_PENDING,
            organization_id=snapshot.organization_id,
        )

    def _create_surplus_difference(self, task: InventoryTask, scan: InventoryScan) -> InventoryDifference:
        """Create a surplus asset difference record."""
        return InventoryDifference(
            id=uuid.uuid4(),
            task_id=task.id,
            asset_id=scan.asset_id,
            difference_type=InventoryDifference.TYPE_SURPLUS,
            description=_("Asset scanned but not in inventory snapshot"),
            expected_quantity=0,
            actual_quantity=1,
            quantity_difference=1,
            expected_location='',
            actual_location=scan.actual_location_name or '',
            expected_custodian='',
            actual_custodian=scan.actual_custodian_name or '',
            status=InventoryDifference.STATUS_PENDING,
            organization_id=task.organization_id,
        )

    def _has_location_changed(self, snapshot: InventorySnapshot, scan: InventoryScan) -> bool:
        """Check if location has changed."""
        return (
            scan.actual_location_name and
            scan.actual_location_name != snapshot.location_name
        )

    def _has_custodian_changed(self, snapshot: InventorySnapshot, scan: InventoryScan) -> bool:
        """Check if custodian has changed."""
        return (
            scan.actual_custodian_name and
            scan.actual_custodian_name != snapshot.custodian_name
        )

    def resolve_difference(
        self,
        difference_id: str,
        user_id: str,
        status: str,
        resolution: Optional[str] = None
    ) -> InventoryDifference:
        """
        Resolve a difference.

        Args:
            difference_id: Difference ID
            user_id: User ID resolving the difference
            status: New status (resolved or ignored)
            resolution: Optional resolution description

        Returns:
            Updated InventoryDifference instance
        """
        diff = self.get(difference_id)

        if diff.status != InventoryDifference.STATUS_PENDING:
            raise ValidationError(_("Difference is not in pending status."))

        if status not in [InventoryDifference.STATUS_RESOLVED, InventoryDifference.STATUS_IGNORED]:
            raise ValidationError(_("Invalid status value."))

        diff.status = status
        diff.resolution = resolution or ''
        diff.resolved_by_id = user_id
        diff.resolved_at = timezone.now()
        diff.save(update_fields=['status', 'resolution', 'resolved_by', 'resolved_at'])

        # Optionally sync asset data based on resolution
        if status == InventoryDifference.STATUS_RESOLVED:
            self._sync_asset_from_difference(diff)

        return diff

    def batch_resolve_differences(
        self,
        difference_ids: List[str],
        user_id: str,
        status: str,
        resolution: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Batch resolve differences.

        Args:
            difference_ids: List of difference IDs
            user_id: User ID resolving the differences
            status: New status (resolved or ignored)
            resolution: Optional resolution description

        Returns:
            Dictionary with results summary
        """
        results = {
            'total': len(difference_ids),
            'succeeded': 0,
            'failed': 0,
            'errors': []
        }

        for diff_id in difference_ids:
            try:
                self.resolve_difference(diff_id, user_id, status, resolution)
                results['succeeded'] += 1
            except Exception as e:
                results['failed'] += 1
                results['errors'].append({
                    'difference_id': diff_id,
                    'error': str(e)
                })

        return results

    def _sync_asset_from_difference(self, diff: InventoryDifference) -> None:
        """
        Sync asset data based on resolved difference.

        Args:
            diff: InventoryDifference instance
        """
        try:
            asset = Asset.objects.get(id=diff.asset_id, is_deleted=False)

            # Sync location for location changes
            if diff.difference_type == InventoryDifference.TYPE_LOCATION_MISMATCH:
                if diff.actual_location_id:
                    from apps.assets.models import Location
                    try:
                        location = Location.objects.get(id=diff.actual_location_id)
                        asset.location = location
                    except Location.DoesNotExist:
                        pass

            # Sync custodian for custodian changes
            if diff.difference_type == InventoryDifference.TYPE_CUSTODIAN_MISMATCH:
                if diff.actual_custodian_id:
                    from apps.accounts.models import User
                    try:
                        custodian = User.objects.get(id=diff.actual_custodian_id)
                        asset.custodian = custodian
                    except User.DoesNotExist:
                        pass

            # Update status for damaged assets
            if diff.difference_type == InventoryDifference.TYPE_DAMAGED:
                asset.status = 'damaged'

            asset.save()

        except Asset.DoesNotExist:
            # Asset might have been deleted
            pass

    def get_difference_summary(self, task_id: str) -> Dict[str, Any]:
        """
        Get summary of differences for a task.

        Args:
            task_id: Task ID

        Returns:
            Dictionary with difference summary
        """
        from django.db.models import Count, Q

        differences = InventoryDifference.objects.filter(
            task_id=task_id,
            is_deleted=False
        )

        total = differences.count()
        pending = differences.filter(status=InventoryDifference.STATUS_PENDING).count()
        resolved = differences.filter(status=InventoryDifference.STATUS_RESOLVED).count()
        ignored = differences.filter(status=InventoryDifference.STATUS_IGNORED).count()

        # Count by type
        type_counts = {}
        for diff_type, _label in InventoryDifference.DIFFERENCE_TYPE_CHOICES:
            count = differences.filter(difference_type=diff_type).count()
            if count > 0:
                type_counts[diff_type] = count

        return {
            'task_id': task_id,
            'total_differences': total,
            'pending': pending,
            'resolved': resolved,
            'ignored': ignored,
            'by_type': type_counts,
        }

    def get_differences_by_type(
        self,
        task_id: str,
        difference_type: str
    ) -> List[InventoryDifference]:
        """
        Get differences filtered by type.

        Args:
            task_id: Task ID
            difference_type: Difference type filter

        Returns:
            List of InventoryDifference instances
        """
        return list(InventoryDifference.objects.filter(
            task_id=task_id,
            difference_type=difference_type,
            is_deleted=False
        ).select_related('asset', 'task', 'resolved_by'))

    def get_pending_differences(self, task_id: str) -> List[InventoryDifference]:
        """
        Get all pending differences for a task.

        Args:
            task_id: Task ID

        Returns:
            List of pending InventoryDifference instances
        """
        return list(InventoryDifference.objects.filter(
            task_id=task_id,
            status=InventoryDifference.STATUS_PENDING,
            is_deleted=False
        ).select_related('asset', 'task'))

    def delete_differences_for_task(self, task_id: str) -> int:
        """
        Soft delete all differences for a task.

        Args:
            task_id: Task ID

        Returns:
            Number of differences deleted
        """
        count = InventoryDifference.objects.filter(
            task_id=task_id,
            is_deleted=False
        ).update(is_deleted=True, deleted_at=timezone.now())

        return count
