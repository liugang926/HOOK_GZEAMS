"""
ViewSets for Inventory Snapshot model.
"""
from rest_framework.decorators import action
from django.utils.translation import gettext_lazy as _

from apps.common.viewsets.base import BaseModelViewSetWithBatch
from apps.common.responses.base import success_response, error_response
from apps.inventory.models import InventorySnapshot
from apps.inventory.serializers import (
    InventorySnapshotSerializer,
    InventorySnapshotListSerializer,
)
from apps.inventory.filters import InventorySnapshotFilter
from apps.inventory.services import SnapshotService


class InventorySnapshotViewSet(BaseModelViewSetWithBatch):
    """
    ViewSet for inventory snapshot management.

    Provides:
    - List and retrieve operations (snapshots are auto-generated)
    - Unscanned snapshots list
    - Snapshot comparison with current asset state
    - Snapshot summary
    """

    queryset = InventorySnapshot.objects.all()
    filterset_class = InventorySnapshotFilter
    search_fields = ['asset_code', 'asset_name', 'location_name', 'custodian_name']

    def get_serializer_class(self):
        """Get appropriate serializer based on action."""
        if self.action == 'list':
            return InventorySnapshotListSerializer
        return InventorySnapshotSerializer

    def create(self, request, *args, **kwargs):
        """Snapshots are auto-generated when task is created."""
        return error_response(
            code='METHOD_NOT_ALLOWED',
            message=_('Snapshots are automatically generated when creating an inventory task.'),
            http_status=405
        )

    def update(self, request, *args, **kwargs):
        """Snapshots are immutable and cannot be updated."""
        return error_response(
            code='METHOD_NOT_ALLOWED',
            message=_('Snapshots are immutable and cannot be updated.'),
            http_status=405
        )

    def destroy(self, request, *args, **kwargs):
        """Snapshots are deleted when the task is deleted."""
        return error_response(
            code='METHOD_NOT_ALLOWED',
            message=_('Snapshots cannot be directly deleted. Delete the inventory task instead.'),
            http_status=405
        )

    @action(detail=False, methods=['get'], url_path='unscanned')
    def unscanned(self, request, *args, **kwargs):
        """
        Get all unscanned snapshots for a task.

        GET /api/inventory/snapshots/unscanned/?task=task_id
        """
        task_id = request.query_params.get('task')
        if not task_id:
            return error_response(
                code='VALIDATION_ERROR',
                message=_('Task ID is required.')
            )

        service = SnapshotService()
        snapshots = service.get_unscanned_snapshots(task_id)

        serializer = InventorySnapshotListSerializer(snapshots, many=True)
        return success_response(data={
            'count': len(snapshots),
            'results': serializer.data
        })

    @action(detail=False, methods=['get'], url_path='scanned')
    def scanned(self, request, *args, **kwargs):
        """
        Get all scanned snapshots for a task.

        GET /api/inventory/snapshots/scanned/?task=task_id
        """
        task_id = request.query_params.get('task')
        if not task_id:
            return error_response(
                code='VALIDATION_ERROR',
                message=_('Task ID is required.')
            )

        service = SnapshotService()
        snapshots = service.get_scanned_snapshots(task_id)

        serializer = InventorySnapshotListSerializer(snapshots, many=True)
        return success_response(data={
            'count': len(snapshots),
            'results': serializer.data
        })

    @action(detail=True, methods=['get'], url_path='compare')
    def compare(self, request, pk=None):
        """
        Compare snapshot data with current asset state.

        GET /api/inventory/snapshots/{id}/compare/
        """
        snapshot = self.get_object()
        service = SnapshotService()
        comparison = service.compare_with_current(str(snapshot.id))
        return success_response(data=comparison)

    @action(detail=False, methods=['get'], url_path='summary')
    def summary(self, request, *args, **kwargs):
        """
        Get summary statistics for snapshots in a task.

        GET /api/inventory/snapshots/summary/?task=task_id
        """
        task_id = request.query_params.get('task')
        if not task_id:
            return error_response(
                code='VALIDATION_ERROR',
                message=_('Task ID is required.')
            )

        service = SnapshotService()
        summary = service.get_snapshot_summary(task_id)
        return success_response(data=summary)

    @action(detail=True, methods=['get'], url_path='asset-info')
    def asset_info(self, request, pk=None):
        """
        Get full snapshot data including stored snapshot_data JSON.

        GET /api/inventory/snapshots/{id}/asset-info/
        """
        snapshot = self.get_object()
        return success_response(data={
            'id': str(snapshot.id),
            'task_id': str(snapshot.task_id),
            'asset_id': str(snapshot.asset_id),
            'asset_code': snapshot.asset_code,
            'asset_name': snapshot.asset_name,
            'category': {
                'id': snapshot.asset_category_id,
                'name': snapshot.asset_category_name,
            },
            'location': {
                'id': snapshot.location_id,
                'name': snapshot.location_name,
            },
            'custodian': {
                'id': snapshot.custodian_id,
                'name': snapshot.custodian_name,
            },
            'department': {
                'id': snapshot.department_id,
                'name': snapshot.department_name,
            },
            'asset_status': snapshot.asset_status,
            'snapshot_data': snapshot.snapshot_data,
            'scanned': snapshot.scanned,
            'scanned_at': snapshot.scanned_at.isoformat() if snapshot.scanned_at else None,
            'scan_count': snapshot.scan_count,
        })
