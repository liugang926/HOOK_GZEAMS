"""
Snapshot service for managing inventory snapshots.
"""
import uuid
import json
from typing import List, Dict, Optional, Any
from django.db import transaction
from django.utils.translation import gettext_lazy as _
from django.core.exceptions import ValidationError
from django.utils import timezone

from apps.common.services.base_crud import BaseCRUDService
from apps.inventory.models import InventorySnapshot, InventoryTask
from apps.assets.models import Asset


class SnapshotService(BaseCRUDService):
    """Service for inventory snapshot management."""

    def __init__(self):
        super().__init__(InventorySnapshot)

    def create_snapshots(
        self,
        task_id: str,
        assets: List[Asset]
    ) -> List[InventorySnapshot]:
        """
        Create snapshots for assets in a task.

        Args:
            task_id: Inventory task ID
            assets: List of Asset instances to snapshot

        Returns:
            List of created InventorySnapshot instances
        """
        task = InventoryTask.objects.get(id=task_id)

        snapshots_to_create = []
        for asset in assets:
            snapshot_data = self._generate_snapshot_data(asset)
            snapshots_to_create.append(
                InventorySnapshot(
                    id=uuid.uuid4(),
                    task_id=task_id,
                    asset_id=asset.id,
                    asset_code=asset.asset_code,
                    asset_name=asset.asset_name,
                    asset_category_id=str(asset.asset_category_id) if asset.asset_category_id else None,
                    asset_category_name=asset.asset_category.name if asset.asset_category else '',
                    location_id=str(asset.location_id) if asset.location_id else None,
                    location_name=asset.location.name if asset.location else '',
                    custodian_id=str(asset.custodian_id) if asset.custodian_id else None,
                    custodian_name=asset.custodian.get_full_name() if asset.custodian else '',
                    department_id=str(asset.department_id) if asset.department_id else None,
                    department_name=asset.department.name if asset.department else '',
                    asset_status=asset.asset_status,
                    snapshot_data=snapshot_data,
                    organization_id=asset.organization_id,
                    scanned=False,
                    scan_count=0,
                )
            )

        if snapshots_to_create:
            InventorySnapshot.objects.bulk_create(snapshots_to_create, batch_size=500)

        return list(InventorySnapshot.objects.filter(
            task_id=task_id,
            asset_id__in=[a.id for a in assets]
        ))

    def _generate_snapshot_data(self, asset: Asset) -> Dict[str, Any]:
        """
        Generate snapshot data JSON for an asset.

        Args:
            asset: Asset instance

        Returns:
            Dictionary with snapshot data
        """
        return {
            'asset_id': str(asset.id),
            'asset_code': asset.asset_code,
            'asset_name': asset.asset_name,
            'category': {
                'id': str(asset.asset_category_id) if asset.asset_category_id else None,
                'name': asset.asset_category.name if asset.asset_category else None,
            },
            'location': {
                'id': str(asset.location_id) if asset.location_id else None,
                'name': asset.location.name if asset.location else None,
            },
            'custodian': {
                'id': str(asset.custodian_id) if asset.custodian_id else None,
                'name': asset.custodian.get_full_name() if asset.custodian else None,
            },
            'department': {
                'id': str(asset.department_id) if asset.department_id else None,
                'name': asset.department.name if asset.department else None,
            },
            'status': asset.asset_status,
            'purchase_date': asset.purchase_date.isoformat() if asset.purchase_date else None,
            'purchase_price': float(asset.purchase_price) if asset.purchase_price else None,
        }

    def get_snapshot_by_asset(
        self,
        task_id: str,
        asset_id: str
    ) -> Optional[InventorySnapshot]:
        """
        Get snapshot for a specific asset in a task.

        Args:
            task_id: Task ID
            asset_id: Asset ID

        Returns:
            InventorySnapshot instance or None
        """
        try:
            return InventorySnapshot.objects.get(
                task_id=task_id,
                asset_id=asset_id,
                is_deleted=False
            )
        except InventorySnapshot.DoesNotExist:
            return None

    def get_unscanned_snapshots(self, task_id: str) -> List[InventorySnapshot]:
        """
        Get all unscanned snapshots for a task.

        Args:
            task_id: Task ID

        Returns:
            List of unscanned InventorySnapshot instances
        """
        return list(InventorySnapshot.objects.filter(
            task_id=task_id,
            scanned=False,
            is_deleted=False
        ).select_related('asset'))

    def get_scanned_snapshots(self, task_id: str) -> List[InventorySnapshot]:
        """
        Get all scanned snapshots for a task.

        Args:
            task_id: Task ID

        Returns:
            List of scanned InventorySnapshot instances
        """
        return list(InventorySnapshot.objects.filter(
            task_id=task_id,
            scanned=True,
            is_deleted=False
        ).select_related('asset'))

    def compare_with_current(
        self,
        snapshot_id: str
    ) -> Dict[str, Any]:
        """
        Compare snapshot data with current asset state.

        Args:
            snapshot_id: Snapshot ID

        Returns:
            Dictionary with comparison results
        """
        snapshot = self.get_by_id(snapshot_id)

        try:
            asset = Asset.objects.get(
                id=snapshot.asset_id,
                is_deleted=False
            )
        except Asset.DoesNotExist:
            return {
                'snapshot_id': str(snapshot.id),
                'asset_id': str(snapshot.asset_id),
                'asset_exists': False,
                'changes': []
            }

        changes = []

        # Compare location
        if str(snapshot.location_id) != str(asset.location_id or ''):
            changes.append({
                'field': 'location',
                'snapshot_value': snapshot.location_name,
                'current_value': asset.location.name if asset.location else None,
            })

        # Compare custodian
        if str(snapshot.custodian_id) != str(asset.custodian_id or ''):
            changes.append({
                'field': 'custodian',
                'snapshot_value': snapshot.custodian_name,
                'current_value': asset.custodian.get_full_name() if asset.custodian else None,
            })

        # Compare status
        if snapshot.asset_status != asset.status:
            changes.append({
                'field': 'status',
                'snapshot_value': snapshot.asset_status,
                'current_value': asset.status,
            })

        # Compare department
        if str(snapshot.department_id) != str(asset.department_id or ''):
            changes.append({
                'field': 'department',
                'snapshot_value': snapshot.department_name,
                'current_value': asset.department.name if asset.department else None,
            })

        return {
            'snapshot_id': str(snapshot.id),
            'asset_id': str(snapshot.asset_id),
            'asset_code': snapshot.asset_code,
            'asset_exists': True,
            'has_changes': len(changes) > 0,
            'changes': changes,
        }

    def delete_snapshots_for_task(self, task_id: str) -> int:
        """
        Soft delete all snapshots for a task.

        Args:
            task_id: Task ID

        Returns:
            Number of snapshots deleted
        """
        count = InventorySnapshot.objects.filter(
            task_id=task_id,
            is_deleted=False
        ).update(is_deleted=True, deleted_at=timezone.now())

        return count

    def get_snapshot_summary(self, task_id: str) -> Dict[str, Any]:
        """
        Get summary statistics for snapshots in a task.

        Args:
            task_id: Task ID

        Returns:
            Dictionary with snapshot summary
        """
        from django.db.models import Count, Q

        snapshots = InventorySnapshot.objects.filter(
            task_id=task_id,
            is_deleted=False
        )

        total = snapshots.count()
        scanned = snapshots.filter(scanned=True).count()
        unscanned = total - scanned

        # Count by status
        status_counts = snapshots.values('asset_status').annotate(
            count=Count('id')
        )

        status_summary = {}
        for item in status_counts:
            status_summary[item['asset_status']] = item['count']

        # Count by department
        dept_counts = snapshots.values('department_name').annotate(
            count=Count('id')
        ).order_by('-count')

        return {
            'task_id': task_id,
            'total_snapshots': total,
            'scanned_count': scanned,
            'unscanned_count': unscanned,
            'scan_progress': round((scanned / total * 100) if total > 0 else 0, 2),
            'by_status': status_summary,
            'by_department': [
                {
                    'department': item['department_name'] or 'Unassigned',
                    'count': item['count']
                }
                for item in dept_counts
            ]
        }
