"""
ViewSets for Asset and related models.

Provides:
- AssetViewSet: Asset CRUD with status change and statistics
- SupplierViewSet: Supplier CRUD
- LocationViewSet: Location CRUD with tree support
- AssetStatusLogViewSet: Status log viewing
"""
from django.conf import settings
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework import status
from django.http import HttpResponse
from apps.common.viewsets.base import BaseModelViewSetWithBatch
from apps.common.responses.base import BaseResponse
from apps.assets.models import Asset, Supplier, Location, AssetStatusLog
from apps.assets.serializers import (
    AssetListSerializer,
    AssetDetailSerializer,
    AssetCreateSerializer,
    AssetUpdateSerializer,
    AssetStatusSerializer,
    AssetSerializer,
    SupplierSerializer,
    SupplierListSerializer,
    LocationSerializer,
    LocationListSerializer,
    AssetStatusLogSerializer,
    AssetStatusLogListSerializer,
)
from apps.assets.filters import AssetFilter, SupplierFilter, LocationFilter, AssetStatusLogFilter
from apps.assets.services import AssetService, SupplierService, LocationService, AssetStatusLogService


class AssetViewSet(BaseModelViewSetWithBatch):
    """
    ViewSet for Asset management.

    Provides:
    - Standard CRUD operations
    - Status change with audit logging
    - QR/RFID code lookup
    - Asset statistics
    - Bulk import/export
    """

    queryset = Asset.objects.select_related(
        'asset_category',
        'supplier',
        'department',
        'location',
        'custodian',
        'user',
        'created_by'
    ).all()
    serializer_class = AssetSerializer
    filterset_class = AssetFilter
    service = AssetService()

    # Search fields for search query parameter
    search_fields = ['asset_code', 'asset_name', 'specification', 'brand', 'model', 'serial_number']

    def get_serializer_class(self):
        """Return appropriate serializer based on action."""
        if self.action == 'list':
            return AssetListSerializer
        if self.action == 'retrieve':
            return AssetDetailSerializer
        if self.action == 'create':
            return AssetCreateSerializer
        if self.action == 'update':
            return AssetUpdateSerializer
        return super().get_serializer_class()

    def get_serializer_context(self):
        """Add organization_id to serializer context."""
        context = super().get_serializer_context()
        # Try to get organization_id from request attribute (set by middleware)
        if hasattr(self.request, 'organization_id') and self.request.organization_id:
            context['organization_id'] = str(self.request.organization_id)
        # Fallback to user's organization_id if available
        elif hasattr(self.request, 'user') and hasattr(self.request.user, 'organization_id'):
            context['organization_id'] = str(self.request.user.organization_id)
        return context

    def perform_create(self, serializer):
        """Set organization and created_by on create."""
        organization_id = getattr(self.request, 'organization_id', None)
        serializer.save(
            organization_id=organization_id,
            created_by=self.request.user
        )

    def create(self, request, *args, **kwargs):
        """Override to wrap response in standard format."""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)

        return BaseResponse.created(
            data=serializer.data,
            message='Asset created successfully'
        )

    def retrieve(self, request, *args, **kwargs):
        """Override to wrap response in standard format."""
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return BaseResponse.success(
                data=serializer.data,
                message='Query successful'
            )

    def update(self, request, *args, **kwargs):
        """Override to wrap response in standard format."""
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(
            instance, data=request.data, partial=partial
        )
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)

        return BaseResponse.success(
                data=serializer.data,
                message='Asset updated successfully'
            )

    def destroy(self, request, *args, **kwargs):
        """Override to wrap response in standard format."""
        instance = self.get_object()
        self.perform_destroy(instance)
        return BaseResponse.success(message='Asset deleted successfully')

    @action(detail=False, methods=['get'], url_path='statistics')
    def statistics(self, request):
        """
        Get asset statistics for current organization.

        GET /api/assets/statistics/

        Returns:
        {
            "success": true,
            "data": {
                "total": 100,
                "by_status": {...},
                "total_value": 1000000.00,
                "total_net_value": 800000.00,
                "by_category": {...}
            }
        }
        """
        organization_id = getattr(request, 'organization_id', None)

        if not organization_id:
            return BaseResponse.error(
                    code='UNAUTHORIZED',
                    message='Organization context required'
                )

        stats = self.service.get_asset_statistics(organization_id)

        return BaseResponse.success(
                data=stats,
                message='Statistics retrieved successfully'
            )

    @action(detail=False, methods=['get'], url_path='depreciation-summary')
    def depreciation_summary(self, request):
        """
        Get depreciation summary for current organization.

        GET /api/assets/depreciation-summary/
        """
        organization_id = getattr(request, 'organization_id', None)

        if not organization_id:
            return BaseResponse.error(
                    code='UNAUTHORIZED',
                    message='Organization context required'
                )

        summary = self.service.get_depreciation_summary(organization_id)

        return BaseResponse.success(
                data=summary,
                message='Depreciation summary retrieved successfully'
            )

    @action(detail=True, methods=['post'], url_path='change-status')
    def change_status(self, request, pk=None):
        """
        Change asset status with audit logging.

        POST /api/assets/{id}/change_status/
        Body:
        {
            "new_status": "in_use",
            "reason": "Asset assigned to user"
        }
        """
        asset = self.get_object()
        serializer = AssetStatusSerializer(data=request.data)

        serializer.is_valid(raise_exception=True)

        try:
            updated_asset = self.service.change_status(
                asset_id=asset.id,
                new_status=serializer.validated_data['new_status'],
                user=request.user,
                reason=serializer.validated_data.get('reason', '')
            )
        except ValueError as e:
            return BaseResponse.error(
                code='VALIDATION_ERROR',
                message=str(e)
            )

        response_serializer = AssetDetailSerializer(updated_asset)

        return BaseResponse.success(
                data=response_serializer.data,
                message='Asset status changed successfully'
            )

    @action(detail=False, methods=['get'], url_path='lookup')
    def lookup(self, request):
        """
        Lookup asset by QR code or RFID code.

        GET /api/assets/lookup/?qr_code=xxx or ?rfid_code=xxx
        """
        qr_code = request.query_params.get('qr_code')
        rfid_code = request.query_params.get('rfid_code')

        if not qr_code and not rfid_code:
            return BaseResponse.error(
                    code='VALIDATION_ERROR',
                    message='Either qr_code or rfid_code parameter is required'
                )

        organization_id = getattr(request, 'organization_id', None)
        asset = None

        if qr_code:
            asset = self.service.get_by_qr_code(qr_code, organization_id)
        elif rfid_code:
            asset = self.service.get_by_rfid_code(rfid_code, organization_id)

        if not asset:
            return BaseResponse.error(
                    code='NOT_FOUND',
                    message='Asset not found'
                )

        serializer = AssetDetailSerializer(asset)
        return BaseResponse.success(
                data=serializer.data,
                message='Asset found'
            )

    @action(detail=False, methods=['get'], url_path='by-category/(?P<category_id>[^/.]+)')
    def by_category(self, request, category_id=None):
        """
        Get assets by category.

        GET /api/assets/by-category/{category_id}/?include_children=true
        """
        organization_id = getattr(request, 'organization_id', None)
        include_children = request.query_params.get('include_children', 'true').lower() == 'true'

        queryset = self.service.query_by_category(
            category_id=category_id,
            organization_id=organization_id,
            include_children=include_children
        )

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = AssetListSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = AssetListSerializer(queryset, many=True)
        return BaseResponse.success(
                data=serializer.data,
                message='Query successful'
            )

    @action(detail=False, methods=['get'], url_path='by-department/(?P<department_id>[^/.]+)')
    def by_department(self, request, department_id=None):
        """
        Get assets by department.

        GET /api/assets/by-department/{department_id}/
        """
        organization_id = getattr(request, 'organization_id', None)

        queryset = self.service.query_by_department(
            department_id=department_id,
            organization_id=organization_id
        )

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = AssetListSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = AssetListSerializer(queryset, many=True)
        return BaseResponse.success(
                data=serializer.data,
                message='Query successful'
            )

    @action(detail=False, methods=['get'], url_path='by-location/(?P<location_id>[^/.]+)')
    def by_location(self, request, location_id=None):
        """
        Get assets by location.

        GET /api/assets/by-location/{location_id}/?include_children=true
        """
        organization_id = getattr(request, 'organization_id', None)
        include_children = request.query_params.get('include_children', 'true').lower() == 'true'

        queryset = self.service.query_by_location(
            location_id=location_id,
            organization_id=organization_id,
            include_children=include_children
        )

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = AssetListSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = AssetListSerializer(queryset, many=True)
        return BaseResponse.success(
                data=serializer.data,
                message='Query successful'
            )

    @action(detail=True, methods=['get'], url_path='status-history')
    def status_history(self, request, pk=None):
        """
        Get status change history for an asset.

        GET /api/assets/{id}/status-history/
        """
        asset = self.get_object()
        logs = self.service.status_log_service.get_asset_history(asset.id)

        page = self.paginate_queryset(logs)
        if page is not None:
            serializer = AssetStatusLogListSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = AssetStatusLogListSerializer(logs, many=True)
        return BaseResponse.success(
                data=serializer.data,
                message='Status history retrieved successfully'
            )

    @action(detail=True, methods=['get'], url_path='qr_code')
    def qr_code(self, request, pk=None):
        """
        Generate QR code for an asset.

        GET /api/assets/{id}/qr_code/

        Returns a PNG image containing the QR code.
        The QR code contains the asset URL for quick scanning.
        """
        import qrcode
        from io import BytesIO

        asset = self.get_object()

        # Build QR code data - asset detail URL
        frontend_url = getattr(settings, 'FRONTEND_URL', 'http://localhost:5173')
        qr_data = f'{frontend_url}/assets/{asset.id}'

        # Generate QR code
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(qr_data)
        qr.make(fit=True)

        # Create image
        img = qr.make_image(fill_color='black', back_color='white')

        # Convert to bytes
        buffer = BytesIO()
        img.save(buffer, format='PNG')
        buffer.seek(0)

        # Return as image response
        return HttpResponse(
            buffer.read(),
            content_type='image/png'
        )

    @action(detail=False, methods=['post'], url_path='bulk-qr-codes')
    def bulk_qr_codes(self, request):
        """
        Generate QR codes for multiple assets as a ZIP file.

        POST /api/assets/bulk-qr-codes/
        Body:
        {
            "ids": ["uuid1", "uuid2", "uuid3"]
        }

        Returns a ZIP file containing PNG images.
        """
        import qrcode
        from io import BytesIO
        from zipfile import ZipFile

        ids = request.data.get('ids', [])
        if not ids:
            return BaseResponse.error(
                code='VALIDATION_ERROR',
                message='ids parameter is required'
            )

        organization_id = getattr(request, 'organization_id', None)
        assets = Asset.objects.filter(
            id__in=ids,
            organization_id=organization_id,
            is_deleted=False
        )

        # Create ZIP file in memory
        zip_buffer = BytesIO()
        frontend_url = getattr(settings, 'FRONTEND_URL', 'http://localhost:5173')

        with ZipFile(zip_buffer, 'w') as zip_file:
            for asset in assets:
                qr_data = f'{frontend_url}/assets/{asset.id}'
                qr = qrcode.QRCode(
                    version=1,
                    error_correction=qrcode.constants.ERROR_CORRECT_L,
                    box_size=10,
                    border=4,
                )
                qr.add_data(qr_data)
                qr.make(fit=True)
                img = qr.make_image(fill_color='black', back_color='white')

                img_buffer = BytesIO()
                img.save(img_buffer, format='PNG')
                img_buffer.seek(0)

                filename = f"QR_{asset.asset_code or asset.id}.png"
                zip_file.writestr(filename, img_buffer.read())

        zip_buffer.seek(0)

        return HttpResponse(
            zip_buffer.read(),
            content_type='application/zip',
            headers={
                'Content-Disposition': 'attachment; filename="asset_qr_codes.zip"'
            }
        )

    @action(detail=False, methods=['post'], url_path='bulk-import')
    def bulk_import(self, request):
        """
        Bulk import assets.

        POST /api/assets/bulk-import/
        Body:
        {
            "assets": [
                {"asset_name": "...", "asset_category_id": "...", ...},
                ...
            ]
        }
        """
        from apps.assets.serializers import AssetBulkImportSerializer

        serializer = AssetBulkImportSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        organization_id = getattr(request, 'organization_id', None)

        result = self.service.bulk_create(
            assets_data=serializer.validated_data['assets'],
            user=request.user,
            organization_id=organization_id
        )

        http_status = status.HTTP_200_OK if result['failed'] == 0 else status.HTTP_207_MULTI_STATUS

        return BaseResponse.success(
            data=result,
            message=f'Bulk import completed: {result["succeeded"]} succeeded, {result["failed"]} failed',
            http_status=http_status
        )

    @action(detail=False, methods=['post'], url_path='batch_change_status')
    def batch_change_status(self, request):
        """
        Batch change asset status.

        POST /api/assets/batch_change_status/
        Body:
        {
            "ids": ["uuid1", "uuid2", ...],
            "new_status": "maintenance"
        }
        """
        ids = request.data.get('ids', [])
        new_status = request.data.get('new_status')

        if not ids:
            return Response(
                {'success': False, 'error': {'code': 'MISSING_IDS', 'message': 'IDs are required'}},
                status=status.HTTP_400_BAD_REQUEST
            )

        if not new_status:
            return Response(
                {'success': False, 'error': {'code': 'MISSING_STATUS', 'message': 'New status is required'}},
                status=status.HTTP_400_BAD_REQUEST
            )

        results = []
        succeeded = 0
        failed = 0
        organization_id = getattr(request, 'organization_id', None)

        for asset_id in ids:
            try:
                asset = Asset.objects.get(id=asset_id, organization_id=organization_id)
                asset.asset_status = new_status
                asset.save()
                succeeded += 1
                results.append({'id': str(asset_id), 'success': True})
            except Asset.DoesNotExist:
                failed += 1
                results.append({'id': str(asset_id), 'success': False, 'error': 'Asset not found'})

        return Response({
            'success': True,
            'message': f'Batch status change completed',
            'summary': {
                'total': len(ids),
                'succeeded': succeeded,
                'failed': failed
            },
            'results': results
        })


class SupplierViewSet(BaseModelViewSetWithBatch):
    """
    ViewSet for Supplier management.

    Provides standard CRUD operations for suppliers.
    """

    queryset = Supplier.objects.all()
    serializer_class = SupplierSerializer
    filterset_class = SupplierFilter
    service = SupplierService()

    def get_serializer_class(self):
        """Return appropriate serializer based on action."""
        if self.action == 'list':
            return SupplierListSerializer
        return super().get_serializer_class()

    def get_serializer_context(self):
        """Add organization_id to serializer context."""
        context = super().get_serializer_context()
        # Try to get organization_id from request attribute (set by middleware)
        if hasattr(self.request, 'organization_id') and self.request.organization_id:
            context['organization_id'] = str(self.request.organization_id)
        # Fallback to user's organization_id if available
        elif hasattr(self.request, 'user') and hasattr(self.request.user, 'organization_id'):
            context['organization_id'] = str(self.request.user.organization_id)
        return context

    def perform_create(self, serializer):
        """Set organization and created_by on create."""
        organization_id = getattr(self.request, 'organization_id', None)
        serializer.save(
            organization_id=organization_id,
            created_by=self.request.user
        )

    def create(self, request, *args, **kwargs):
        """Override to wrap response in standard format."""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)

        return BaseResponse.created(
            data=serializer.data,
            message='Supplier created successfully'
        )

    def retrieve(self, request, *args, **kwargs):
        """Override to wrap response in standard format."""
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return BaseResponse.success(
                data=serializer.data,
                message='Query successful'
            )

    def update(self, request, *args, **kwargs):
        """Override to wrap response in standard format."""
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(
            instance, data=request.data, partial=partial
        )
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)

        return BaseResponse.success(
                data=serializer.data,
                message='Supplier updated successfully'
            )

    def destroy(self, request, *args, **kwargs):
        """Override to wrap response in standard format."""
        instance = self.get_object()
        self.perform_destroy(instance)
        return BaseResponse.success(message='Supplier deleted successfully')


class LocationViewSet(BaseModelViewSetWithBatch):
    """
    ViewSet for Location management.

    Provides:
    - Standard CRUD operations
    - Tree endpoint for hierarchical data
    """

    queryset = Location.objects.all()
    serializer_class = LocationSerializer
    filterset_class = LocationFilter
    service = LocationService()

    def get_serializer_class(self):
        """Return appropriate serializer based on action."""
        if self.action == 'list':
            return LocationListSerializer
        return super().get_serializer_class()

    def get_serializer_context(self):
        """Add organization_id to serializer context."""
        context = super().get_serializer_context()
        # Try to get organization_id from request attribute (set by middleware)
        if hasattr(self.request, 'organization_id') and self.request.organization_id:
            context['organization_id'] = str(self.request.organization_id)
        # Fallback to user's organization_id if available
        elif hasattr(self.request, 'user') and hasattr(self.request.user, 'organization_id'):
            context['organization_id'] = str(self.request.user.organization_id)
        return context

    def perform_create(self, serializer):
        """Set organization and created_by on create."""
        organization_id = getattr(self.request, 'organization_id', None)
        serializer.save(
            organization_id=organization_id,
            created_by=self.request.user
        )

    def create(self, request, *args, **kwargs):
        """Override to wrap response in standard format."""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)

        return BaseResponse.created(
            data=serializer.data,
            message='Location created successfully'
        )

    def retrieve(self, request, *args, **kwargs):
        """Override to wrap response in standard format."""
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return BaseResponse.success(
                data=serializer.data,
                message='Query successful'
            )

    def update(self, request, *args, **kwargs):
        """Override to wrap response in standard format."""
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(
            instance, data=request.data, partial=partial
        )
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)

        return BaseResponse.success(
                data=serializer.data,
                message='Location updated successfully'
            )

    def destroy(self, request, *args, **kwargs):
        """Override to wrap response in standard format."""
        instance = self.get_object()
        self.perform_destroy(instance)
        return BaseResponse.success(message='Location deleted successfully')

    @action(detail=False, methods=['get'], url_path='tree')
    def tree(self, request):
        """
        Get complete location tree.

        GET /api/assets/locations/tree/
        """
        organization_id = getattr(request, 'organization_id', None)

        if not organization_id:
            return BaseResponse.error(
                    code='UNAUTHORIZED',
                    message='Organization context required'
                )

        tree_data = self.service.get_tree(organization_id)

        return BaseResponse.success(
                data=tree_data,
                message='Location tree retrieved successfully'
            )


class AssetStatusLogViewSet(BaseModelViewSetWithBatch):
    """
    ViewSet for Asset Status Log viewing.

    Status logs are read-only (created by status change actions).
    """

    queryset = AssetStatusLog.objects.select_related('asset', 'created_by').all()
    serializer_class = AssetStatusLogSerializer
    filterset_class = AssetStatusLogFilter

    def get_serializer_class(self):
        """Return appropriate serializer based on action."""
        if self.action == 'list':
            return AssetStatusLogListSerializer
        return super().get_serializer_class()

    def get_queryset(self):
        """Filter by organization through asset relation."""
        queryset = super().get_queryset()
        # Additional filtering can be added here if needed
        return queryset

    def retrieve(self, request, *args, **kwargs):
        """Override to wrap response in standard format."""
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return BaseResponse.success(
                data=serializer.data,
                message='Query successful'
            )

    def list(self, request, *args, **kwargs):
        """Override to wrap response in standard format."""
        queryset = self.filter_queryset(self.get_queryset())

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return BaseResponse.success(
                data=serializer.data,
                message='Query successful'
            )
