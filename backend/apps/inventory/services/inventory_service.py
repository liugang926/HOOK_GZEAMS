"""
Inventory service for managing inventory tasks.
"""
import uuid
from datetime import datetime
from typing import List, Dict, Optional, Any
from django.db import transaction
from django.utils.translation import gettext_lazy as _
from django.core.exceptions import ValidationError

from apps.common.services.base_crud import BaseCRUDService
from apps.inventory.models import (
    InventoryTask,
    InventorySnapshot,
    InventoryTaskExecutor,
)
from apps.assets.models import Asset


class InventoryService(BaseCRUDService):
    """Service for inventory task management."""

    def __init__(self):
        super().__init__(InventoryTask)

    def generate_task_code(self) -> str:
        """Generate unique inventory task code."""
        from apps.inventory.utils.task_code import generate_task_code
        return generate_task_code()

    def create_task(
        self,
        task_name: str,
        inventory_type: str,
        organization_id: str,
        created_by_id: str,
        description: Optional[str] = None,
        department_id: Optional[str] = None,
        category_id: Optional[str] = None,
        sample_ratio: Optional[float] = None,
        planned_date: Optional[datetime] = None,
        notes: Optional[str] = None,
        executor_ids: Optional[List[str]] = None,
        primary_executor_id: Optional[str] = None,
    ) -> InventoryTask:
        """
        Create a new inventory task with snapshot generation.

        Args:
            task_name: Name of the inventory task
            inventory_type: Type of inventory (full, partial, department, category)
            organization_id: Organization ID
            created_by_id: User ID who creates the task
            description: Optional description
            department_id: Department ID for department inventory
            category_id: Category ID for category inventory
            sample_ratio: Sample ratio for partial inventory (0-1)
            planned_date: Planned execution date
            notes: Additional notes
            executor_ids: List of executor user IDs
            primary_executor_id: Primary executor user ID

        Returns:
            Created InventoryTask instance
        """
        from apps.inventory.services.snapshot_service import SnapshotService

        with transaction.atomic():
            # Generate task code
            task_code = self.generate_task_code()

            # Create task
            task = InventoryTask.objects.create(
                id=uuid.uuid4(),
                task_code=task_code,
                task_name=task_name,
                description=description or '',
                inventory_type=inventory_type,
                department_id=department_id,
                category_id=category_id,
                sample_ratio=sample_ratio,
                planned_date=planned_date,
                notes=notes or '',
                organization_id=organization_id,
                created_by_id=created_by_id,
                status=InventoryTask.STATUS_DRAFT,
            )

            # Add executors
            if executor_ids:
                self._add_executors(task, executor_ids, primary_executor_id)

            # Generate snapshot based on inventory type
            snapshot_service = SnapshotService()
            assets = self._get_assets_for_inventory(
                organization_id, inventory_type, department_id, category_id, sample_ratio
            )
            snapshot_service.create_snapshots(task.id, assets)

            # Update task counts
            task.refresh_from_db()
            task.total_count = task.snapshots.count()
            task.save(update_fields=['total_count'])

        return task

    def _add_executors(
        self,
        task: InventoryTask,
        executor_ids: List[str],
        primary_executor_id: Optional[str] = None
    ) -> None:
        """Add executors to inventory task."""
        from apps.accounts.models import User

        # Validate executors exist
        users = User.objects.filter(id__in=executor_ids, is_active=True)
        if users.count() != len(executor_ids):
            raise ValidationError(_("Some executor users are invalid or inactive."))

        # Create executor relationships
        executors_to_create = []
        for user_id in executor_ids:
            executors_to_create.append(
                InventoryTaskExecutor(
                    task=task,
                    executor_id=user_id,
                    is_primary=(user_id == primary_executor_id)
                )
            )
        InventoryTaskExecutor.objects.bulk_create(executors_to_create)

    def _get_assets_for_inventory(
        self,
        organization_id: str,
        inventory_type: str,
        department_id: Optional[str] = None,
        category_id: Optional[str] = None,
        sample_ratio: Optional[float] = None,
    ) -> List[Asset]:
        """Get asset list for inventory based on type."""
        from apps.assets.models import Asset

        # Base queryset - active assets in organization
        queryset = Asset.objects.filter(
            organization_id=organization_id,
            is_deleted=False
        ).select_related('asset_category', 'location', 'custodian', 'department')

        # Filter by inventory type
        if inventory_type == InventoryTask.TYPE_FULL:
            # All active assets
            pass
        elif inventory_type == InventoryTask.TYPE_DEPARTMENT:
            queryset = queryset.filter(department_id=department_id)
        elif inventory_type == InventoryTask.TYPE_CATEGORY:
            queryset = queryset.filter(asset_category_id=category_id)
        elif inventory_type == InventoryTask.TYPE_PARTIAL:
            # Sample ratio-based selection
            if sample_ratio and 0 < sample_ratio < 1:
                total = queryset.count()
                sample_size = int(total * sample_ratio)
                # Simple random sampling - in production use more sophisticated method
                queryset = queryset.order_by('?')[:sample_size]

        return list(queryset)

    def start_task(self, task_id: str, user_id: str) -> InventoryTask:
        """
        Start an inventory task.

        Args:
            task_id: Task ID
            user_id: User ID starting the task

        Returns:
            Updated task
        """
        task = self.get(task_id)

        if task.status != InventoryTask.STATUS_DRAFT:
            raise ValidationError(_("Only draft tasks can be started."))

        task.status = InventoryTask.STATUS_IN_PROGRESS
        task.started_at = datetime.utcnow()
        task.save(update_fields=['status', 'started_at'])

        return task

    def complete_task(
        self,
        task_id: str,
        user_id: str,
        notes: Optional[str] = None
    ) -> InventoryTask:
        """
        Complete an inventory task.

        Args:
            task_id: Task ID
            user_id: User ID completing the task
            notes: Optional completion notes

        Returns:
            Updated task
        """
        from apps.inventory.services.difference_service import DifferenceService

        task = self.get(task_id)

        if task.status != InventoryTask.STATUS_IN_PROGRESS:
            raise ValidationError(_("Only in-progress tasks can be completed."))

        with transaction.atomic():
            # Generate differences for any discrepancies
            diff_service = DifferenceService()
            diff_service.generate_differences(task_id)

            # Update task status
            task.status = InventoryTask.STATUS_COMPLETED
            task.completed_at = datetime.utcnow()
            if notes:
                task.notes = (task.notes or '') + f"\n\nCompletion: {notes}"
            task.save(update_fields=['status', 'completed_at', 'notes'])

            # Refresh to get updated counts
            task.refresh_from_db()

        return task

    def cancel_task(self, task_id: str, user_id: str, reason: Optional[str] = None) -> InventoryTask:
        """
        Cancel an inventory task.

        Args:
            task_id: Task ID
            user_id: User ID cancelling the task
            reason: Optional cancellation reason

        Returns:
            Updated task
        """
        task = self.get(task_id)

        if task.status == InventoryTask.STATUS_COMPLETED:
            raise ValidationError(_("Completed tasks cannot be cancelled."))

        task.status = InventoryTask.STATUS_CANCELLED
        if reason:
            task.notes = (task.notes or '') + f"\n\nCancelled: {reason}"
        task.save(update_fields=['status', 'notes'])

        return task

    def update_statistics(self, task_id: str) -> InventoryTask:
        """
        Update task statistics from scan results.

        Args:
            task_id: Task ID

        Returns:
            Updated task with refreshed statistics
        """
        from apps.inventory.models import InventoryScan, InventoryDifference

        task = self.get(task_id)

        # Count total snapshots
        total_count = task.snapshots.count()

        # Count scans
        scanned_count = InventoryScan.objects.filter(
            task_id=task_id,
            is_deleted=False
        ).count()

        # Count differences by type
        missing_count = InventoryDifference.objects.filter(
            task_id=task_id,
            difference_type=InventoryDifference.TYPE_MISSING,
            status=InventoryDifference.STATUS_PENDING,
            is_deleted=False
        ).count()

        surplus_count = InventoryDifference.objects.filter(
            task_id=task_id,
            difference_type=InventoryDifference.TYPE_SURPLUS,
            status=InventoryDifference.STATUS_PENDING,
            is_deleted=False
        ).count()

        damaged_count = InventoryDifference.objects.filter(
            task_id=task_id,
            difference_type=InventoryDifference.TYPE_DAMAGED,
            status=InventoryDifference.STATUS_PENDING,
            is_deleted=False
        ).count()

        location_changed_count = InventoryDifference.objects.filter(
            task_id=task_id,
            difference_type=InventoryDifference.TYPE_LOCATION_MISMATCH,
            status=InventoryDifference.STATUS_PENDING,
            is_deleted=False
        ).count()

        # Calculate normal count (scanned - all abnormal)
        normal_count = scanned_count - missing_count - surplus_count - damaged_count

        # Update task
        task.total_count = total_count
        task.scanned_count = scanned_count
        task.normal_count = normal_count
        task.surplus_count = surplus_count
        task.missing_count = missing_count
        task.damaged_count = damaged_count
        task.location_changed_count = location_changed_count
        task.save(update_fields=[
            'total_count', 'scanned_count', 'normal_count',
            'surplus_count', 'missing_count', 'damaged_count',
            'location_changed_count'
        ])

        return task

    def get_task_progress(self, task_id: str) -> Dict[str, Any]:
        """
        Get detailed progress information for a task.

        Args:
            task_id: Task ID

        Returns:
            Dictionary with progress details
        """
        task = self.get(task_id)

        return {
            'task_id': str(task.id),
            'task_code': task.task_code,
            'task_name': task.task_name,
            'status': task.status,
            'status_label': task.get_status_label(),
            'total_count': task.total_count,
            'scanned_count': task.scanned_count,
            'unscanned_count': task.total_count - task.scanned_count,
            'normal_count': task.normal_count,
            'surplus_count': task.surplus_count,
            'missing_count': task.missing_count,
            'damaged_count': task.damaged_count,
            'location_changed_count': task.location_changed_count,
            'progress_percentage': task.progress_percentage,
            'started_at': task.started_at.isoformat() if task.started_at else None,
            'completed_at': task.completed_at.isoformat() if task.completed_at else None,
        }

    def get_executor_statistics(self, task_id: str, executor_id: str) -> Dict[str, Any]:
        """
        Get statistics for a specific executor on a task.

        Args:
            task_id: Task ID
            executor_id: Executor user ID

        Returns:
            Dictionary with executor statistics
        """
        from apps.inventory.models import InventoryScan

        scans = InventoryScan.objects.filter(
            task_id=task_id,
            scanned_by_id=executor_id,
            is_deleted=False
        )

        return {
            'executor_id': executor_id,
            'task_id': task_id,
            'scan_count': scans.count(),
            'last_scan_at': scans.order_by('-scanned_at').first().scanned_at if scans.exists() else None,
        }

    def add_executors_to_task(
        self,
        task_id: str,
        executor_ids: List[str],
        primary_executor_id: Optional[str] = None
    ) -> List[InventoryTaskExecutor]:
        """
        Add executors to an existing task.

        Args:
            task_id: Task ID
            executor_ids: List of executor user IDs
            primary_executor_id: Primary executor ID

        Returns:
            List of created executor relationships
        """
        task = self.get(task_id)

        # Remove existing primary flag if new primary is set
        if primary_executor_id:
            InventoryTaskExecutor.objects.filter(
                task_id=task_id
            ).update(is_primary=False)

        executors_to_create = []
        for user_id in executor_ids:
            # Check if already exists
            if not InventoryTaskExecutor.objects.filter(
                task_id=task_id,
                executor_id=user_id
            ).exists():
                executors_to_create.append(
                    InventoryTaskExecutor(
                        task=task,
                        executor_id=user_id,
                        is_primary=(user_id == primary_executor_id)
                    )
                )

        if executors_to_create:
            InventoryTaskExecutor.objects.bulk_create(executors_to_create)

        return list(InventoryTaskExecutor.objects.filter(
            task_id=task_id,
            executor_id__in=executor_ids
        ))

    def remove_executor_from_task(self, task_id: str, executor_id: str) -> None:
        """
        Remove an executor from a task.

        Args:
            task_id: Task ID
            executor_id: Executor user ID to remove
        """
        InventoryTaskExecutor.objects.filter(
            task_id=task_id,
            executor_id=executor_id
        ).delete()
