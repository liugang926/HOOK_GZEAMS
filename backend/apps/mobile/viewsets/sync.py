"""
ViewSets for Sync Data, Sync Conflict, and Sync Log models.
"""
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from apps.common.viewsets.base import BaseModelViewSetWithBatch
from apps.mobile.models import OfflineData, SyncConflict, SyncLog, MobileDevice
from apps.mobile.serializers import (
    OfflineDataSerializer,
    OfflineDataListSerializer,
    SyncConflictSerializer,
    SyncConflictDetailSerializer,
    SyncLogSerializer,
)
from apps.mobile.services import SyncService, SyncLogService
from apps.mobile.filters import OfflineDataFilter, SyncConflictFilter, SyncLogFilter


class DataSyncViewSet(BaseModelViewSetWithBatch):
    """
    ViewSet for data synchronization operations.

    Inherits from BaseModelViewSetWithBatch to get:
    - Organization filtering
    - Soft delete support
    - Batch operations
    - Audit field auto-population
    """

    permission_classes = [IsAuthenticated]
    filterset_class = OfflineDataFilter

    def get_queryset(self):
        """Get filtered queryset for current user."""
        return OfflineData.objects.filter(user=self.request.user)

    def get_serializer_class(self):
        """Return appropriate serializer based on action."""
        if self.action == 'list':
            return OfflineDataListSerializer
        return OfflineDataSerializer

    @action(detail=False, methods=['post'])
    def upload(self, request):
        """
        Upload offline data for synchronization.

        POST /api/mobile/sync/upload/
        {
            "device_id": "device_001",
            "data": [
                {
                    "table_name": "assets.Asset",
                    "record_id": "asset_001",
                    "operation": "update",
                    "data": {"status": "in_use"},
                    "version": 1
                }
            ]
        }
        """
        device_id = request.data.get('device_id')
        try:
            device = MobileDevice.objects.get(device_id=device_id, user=request.user)
        except MobileDevice.DoesNotExist:
            return Response(
                {'error': 'Device not found'},
                status=status.HTTP_400_BAD_REQUEST
            )

        sync_service = SyncService(user=request.user, device=device)
        results = sync_service.upload_offline_data(request.data.get('data', []))

        # Update device last sync time
        from django.utils import timezone
        device.last_sync_at = timezone.now()
        device.save()

        return Response(results)

    @action(detail=False, methods=['post'])
    def download(self, request):
        """
        Download server changes since last sync.

        POST /api/mobile/sync/download/
        {
            "last_sync_version": 1705316400,
            "tables": ["assets.Asset", "inventory.InventoryTask"]
        }
        """
        last_sync_version = request.data.get('last_sync_version', 0)
        tables = request.data.get('tables', [])

        sync_service = SyncService(user=request.user)
        changes = sync_service.download_changes(last_sync_version, tables)

        return Response({
            'version': SyncLogService._get_server_version(),
            'changes': changes
        })

    @action(detail=False, methods=['post'])
    def resolve_conflict(self, request):
        """
        Resolve a sync conflict.

        POST /api/mobile/sync/resolve_conflict/
        {
            "conflict_id": "conflict_001",
            "resolution": "server_wins",
            "merged_data": {}  // optional, for resolution="merge"
        }
        """
        conflict_id = request.data.get('conflict_id')
        resolution = request.data.get('resolution')
        merged_data = request.data.get('merged_data')

        sync_service = SyncService(user=request.user)
        success = sync_service.resolve_conflict(conflict_id, resolution, merged_data)

        if success:
            return Response({'message': 'Conflict resolved successfully'})
        return Response(
            {'error': 'Conflict resolution failed'},
            status=status.HTTP_400_BAD_REQUEST
        )

    @action(detail=False, methods=['get'])
    def pending_count(self, request):
        """
        Get pending sync data count.

        GET /api/mobile/sync/pending_count/
        """
        device_id = request.query_params.get('device_id')
        queryset = self.get_queryset()

        if device_id:
            queryset = queryset.filter(device__device_id=device_id)

        pending_count = queryset.filter(sync_status='pending').count()
        conflict_count = SyncConflict.objects.filter(
            user=request.user,
            resolution='pending'
        ).count()

        return Response({
            'pending_count': pending_count,
            'conflict_count': conflict_count
        })

    @action(detail=False, methods=['post'])
    def sync_all(self, request):
        """
        Perform full synchronization (upload + download).

        POST /api/mobile/sync/sync_all/
        {
            "device_id": "device_001",
            "last_sync_version": 1705316400,
            "tables": ["assets.Asset"]
        }
        """
        device_id = request.data.get('device_id')
        try:
            device = MobileDevice.objects.get(device_id=device_id, user=request.user)
        except MobileDevice.DoesNotExist:
            return Response(
                {'error': 'Device not found'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Create sync log
        sync_log = SyncLogService.create_sync_log(
            user=request.user,
            device=device,
            sync_type='full',
            sync_direction='bidirectional'
        )

        # Upload offline data
        upload_results = {
            'upload_count': 0,
            'download_count': 0,
            'conflict_count': 0,
            'error_count': 0
        }

        if request.data.get('data'):
            sync_service = SyncService(user=request.user, device=device)
            upload_result = sync_service.upload_offline_data(request.data.get('data', []))
            upload_results['upload_count'] = upload_result['success']
            upload_results['conflict_count'] = upload_result['conflicts']
            upload_results['error_count'] = upload_result['failed']

        # Download changes
        last_sync_version = request.data.get('last_sync_version', 0)
        tables = request.data.get('tables', [])
        if tables:
            sync_service = SyncService(user=request.user)
            changes = sync_service.download_changes(last_sync_version, tables)
            download_count = sum(len(items) for items in changes.values())
            upload_results['download_count'] = download_count

        # Finish sync log
        SyncLogService.finish_sync_log(sync_log, upload_results)

        return Response({
            'message': 'Synchronization completed',
            'summary': upload_results
        })


class SyncConflictViewSet(BaseModelViewSetWithBatch):
    """
    ViewSet for SyncConflict management.

    Inherits from BaseModelViewSetWithBatch to get:
    - Organization filtering
    - Soft delete support
    - Batch operations
    - Audit field auto-population
    """

    permission_classes = [IsAuthenticated]
    filterset_class = SyncConflictFilter

    def get_queryset(self):
        """Get filtered queryset for current user."""
        return SyncConflict.objects.filter(user=self.request.user)

    def get_serializer_class(self):
        """Return appropriate serializer based on action."""
        if self.action == 'retrieve':
            return SyncConflictDetailSerializer
        return SyncConflictSerializer

    @action(detail=False, methods=['get'])
    def pending(self, request):
        """
        Get pending (unresolved) conflicts.

        GET /api/mobile/conflicts/pending/
        """
        conflicts = self.get_queryset().filter(resolution='pending')
        serializer = SyncConflictSerializer(conflicts, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def resolve(self, request, pk=None):
        """
        Resolve a specific conflict.

        POST /api/mobile/conflicts/{id}/resolve/
        {
            "resolution": "server_wins",
            "merged_data": {},
            "note": "Optional resolution note"
        }
        """
        resolution = request.data.get('resolution')
        merged_data = request.data.get('merged_data')
        note = request.data.get('note', '')

        sync_service = SyncService(user=request.user)
        success = sync_service.resolve_conflict(pk, resolution, merged_data)

        if success:
            # Add resolution note
            conflict = SyncConflict.objects.get(pk=pk)
            conflict.resolution_note = note
            conflict.save()
            return Response({'message': 'Conflict resolved successfully'})
        return Response(
            {'error': 'Conflict resolution failed'},
            status=status.HTTP_400_BAD_REQUEST
        )


class SyncLogViewSet(BaseModelViewSetWithBatch):
    """
    ViewSet for SyncLog - Read-only for audit purposes.

    Inherits from BaseModelViewSetWithBatch to get:
    - Organization filtering
    - Soft delete support
    - Batch operations
    - Audit field auto-population
    """

    permission_classes = [IsAuthenticated]
    filterset_class = SyncLogFilter
    serializer_class = SyncLogSerializer

    def get_queryset(self):
        """Get filtered queryset for current user."""
        return SyncLog.objects.filter(user=self.request.user)

    # Read-only - disable modifications
    http_method_names = ['get', 'head', 'options']
