"""
ViewSets for Inventory Scan model.
"""
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.utils.translation import gettext_lazy as _

from apps.common.viewsets.base import BaseModelViewSetWithBatch
from apps.common.responses.base import success_response, error_response
from apps.inventory.models import InventoryScan
from apps.inventory.serializers import (
    InventoryScanListSerializer,
    InventoryScanDetailSerializer,
    InventoryScanCreateSerializer,
    InventoryScanUpdateSerializer,
    InventoryBatchScanSerializer,
    InventoryScanValidateSerializer,
)
from apps.inventory.filters import InventoryScanFilter
from apps.inventory.services import ScanService


class InventoryScanViewSet(BaseModelViewSetWithBatch):
    """
    ViewSet for inventory scan management.

    Provides:
    - Standard CRUD operations
    - QR code validation
    - Batch scan upload
    - Scan summary
    """

    queryset = InventoryScan.objects.all()
    filterset_class = InventoryScanFilter
    search_fields = ['qr_code', 'asset__asset_code', 'asset__asset_name']

    def get_serializer_class(self):
        """Get appropriate serializer based on action."""
        if self.action == 'list':
            return InventoryScanListSerializer
        elif self.action == 'retrieve':
            return InventoryScanDetailSerializer
        elif self.action == 'create':
            return InventoryScanCreateSerializer
        elif self.action in ['update', 'partial_update']:
            return InventoryScanUpdateSerializer
        elif self.action == 'batch_scan':
            return InventoryBatchScanSerializer
        elif self.action == 'validate_qr':
            return InventoryScanValidateSerializer
        return InventoryScanDetailSerializer

    def retrieve(self, request, *args, **kwargs):
        """Retrieve a single scan with standard response format."""
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return success_response(data=serializer.data)

    def create(self, request, *args, **kwargs):
        """
        Create a new scan record.

        Validates QR code and records scan with location/custodian info.
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        service = ScanService()
        try:
            scan = service.record_scan(
                task_id=serializer.validated_data['task'],
                qr_code=serializer.validated_data['qr_code'],
                scanned_by_id=str(request.user.id),
                organization_id=request.user.organization_id,
                scan_method=serializer.validated_data.get('scan_method', InventoryScan.METHOD_QR),
                scan_status=serializer.validated_data.get('scan_status', 'normal'),
                actual_location_id=serializer.validated_data.get('actual_location_id'),
                actual_location_name=serializer.validated_data.get('actual_location_name'),
                actual_custodian_id=serializer.validated_data.get('actual_custodian_id'),
                actual_custodian_name=serializer.validated_data.get('actual_custodian_name'),
                photos=serializer.validated_data.get('photos'),
                remark=serializer.validated_data.get('remark'),
                latitude=serializer.validated_data.get('latitude'),
                longitude=serializer.validated_data.get('longitude'),
            )

            response_serializer = InventoryScanDetailSerializer(scan)
            return success_response(
                data=response_serializer.data,
                message=_('Scan recorded successfully.'),
                http_status=status.HTTP_201_CREATED
            )
        except Exception as e:
            return error_response(
                code='VALIDATION_ERROR',
                message=_('Failed to record scan.'),
                details={'error': str(e)}
            )

    def update(self, request, *args, **kwargs):
        """
        Update an existing scan record.
        """
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)

        service = ScanService()
        try:
            scan = service.update_scan(
                scan_id=str(instance.id),
                user_id=str(request.user.id),
                organization_id=request.user.organization_id,
                scan_status=serializer.validated_data.get('scan_status'),
                actual_location_id=serializer.validated_data.get('actual_location_id'),
                actual_location_name=serializer.validated_data.get('actual_location_name'),
                actual_custodian_id=serializer.validated_data.get('actual_custodian_id'),
                actual_custodian_name=serializer.validated_data.get('actual_custodian_name'),
                photos=serializer.validated_data.get('photos'),
                remark=serializer.validated_data.get('remark'),
            )

            response_serializer = InventoryScanDetailSerializer(scan)
            return success_response(
                data=response_serializer.data,
                message=_('Scan updated successfully.')
            )
        except Exception as e:
            return error_response(
                code='VALIDATION_ERROR',
                message=_('Failed to update scan.'),
                details={'error': str(e)}
            )

    @action(detail=False, methods=['post'], url_path='batch-scan')
    def batch_scan(self, request, *args, **kwargs):
        """
        Batch record scan operations.

        POST /api/inventory/scans/batch-scan/
        {
            "task": "task_id",
            "scans": [
                {"qr_code": "...", "scan_method": "qr", ...},
                ...
            ]
        }
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        service = ScanService()
        results = service.batch_record_scans(
            task_id=serializer.validated_data.get('task'),
            scans_data=serializer.validated_data.get('scans', []),
            scanned_by_id=str(request.user.id),
            organization_id=request.user.organization_id,
        )

        message = _('Batch scan completed.') if results['failed'] == 0 else _('Batch scan completed with some failures.')
        return success_response(data=results, message=message)

    @action(detail=False, methods=['post'], url_path='validate-qr')
    def validate_qr(self, request, *args, **kwargs):
        """
        Validate a QR code and return asset information.

        POST /api/inventory/scans/validate-qr/
        {
            "qr_code": "QR code content",
            "task_id": "optional_task_id"
        }
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        service = ScanService()
        result = service.validate_qr_code(
            qr_code=serializer.validated_data['qr_code'],
            organization_id=str(request.user.organization_id),
            task_id=serializer.validated_data.get('task_id')
        )

        if result['valid']:
            return success_response(data=result)
        else:
            return error_response(
                code='VALIDATION_ERROR',
                message=_('QR code validation failed.'),
                details={'error': result.get('error')}
            )

    @action(detail=True, methods=['post'], url_path='sync-asset')
    def sync_asset(self, request, pk=None):
        """
        Sync scan data back to asset (location, custodian).

        POST /api/inventory/scans/{id}/sync-asset/
        """
        scan = self.get_object()

        if not scan.actual_location_id and not scan.actual_custodian_id:
            return error_response(
                code='VALIDATION_ERROR',
                message=_('No location or custodian data to sync.')
            )

        try:
            from apps.assets.models import Asset

            asset = Asset.objects.get(id=scan.asset_id, is_deleted=False)

            if scan.actual_location_id:
                from apps.assets.models import Location
                try:
                    location = Location.objects.get(id=scan.actual_location_id)
                    asset.location = location
                except Location.DoesNotExist:
                    pass

            if scan.actual_custodian_id:
                from apps.accounts.models import User
                try:
                    custodian = User.objects.get(id=scan.actual_custodian_id)
                    asset.custodian = custodian
                except User.DoesNotExist:
                    pass

            asset.save(update_fields=['location', 'custodian'])

            return success_response(message=_('Asset synced successfully.'))
        except Exception as e:
            return error_response(
                code='SERVER_ERROR',
                message=_('Failed to sync asset.'),
                details={'error': str(e)}
            )

    @action(detail=False, methods=['get'], url_path='summary')
    def summary(self, request, *args, **kwargs):
        """
        Get scan summary for a task.

        GET /api/inventory/scans/summary/?task=task_id
        """
        task_id = request.query_params.get('task')
        if not task_id:
            return error_response(
                code='VALIDATION_ERROR',
                message=_('Task ID is required.')
            )

        service = ScanService()
        summary = service.get_scan_summary(task_id)
        return success_response(data=summary)

    @action(detail=False, methods=['get'], url_path='my-scans')
    def my_scans(self, request, *args, **kwargs):
        """
        Get scans performed by current user.

        GET /api/inventory/scans/my-scans/?task=task_id
        """
        queryset = self.filter_queryset(
            self.get_queryset().filter(scanned_by=request.user)
        )

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = InventoryScanListSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = InventoryScanListSerializer(queryset, many=True)
        return success_response(data={'results': serializer.data})

    @action(detail=False, methods=['get'], url_path='by-task/(?P<task_id>[^/.]+)')
    def by_task(self, request, task_id=None):
        """
        Get all scans for a specific task.

        GET /api/inventory/scans/by-task/{task_id}/

        Returns all scan records for the specified inventory task.
        Useful for reviewing all scans made during a task.
        """
        queryset = self.filter_queryset(
            self.get_queryset().filter(task_id=task_id)
        ).order_by('-scanned_at')

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = InventoryScanListSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = InventoryScanListSerializer(queryset, many=True)
        return success_response(data={'results': serializer.data})

    @action(detail=False, methods=['post'], url_path='batch')
    def batch(self, request):
        """
        Batch create scan records.

        POST /api/inventory/scans/batch/
        {
            "task": "task_id",
            "scans": [
                {"qr_code": "...", "scan_method": "qr", ...},
                ...
            ]
        }

        This is an alias for the batch_scan endpoint for consistency.
        """
        return self.batch_scan(request)
