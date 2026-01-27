"""
ViewSets for IT Assets Module.

All ViewSets inherit from BaseModelViewSetWithBatch for common functionality including:
- Organization isolation
- Soft delete handling
- Audit field management
- Batch operations (delete, restore, update)
"""
from rest_framework import permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from apps.common.viewsets.base import BaseModelViewSetWithBatch
from apps.common.permissions.base import IsOrganizationMember
from apps.it_assets.models import (
    ITAssetInfo,
    Software,
    SoftwareLicense,
    LicenseAllocation,
    ITMaintenanceRecord,
    ConfigurationChange
)
from apps.it_assets.serializers import (
    ITAssetInfoSerializer,
    ITAssetInfoListSerializer,
    ITAssetInfoDetailSerializer,
    SoftwareSerializer,
    SoftwareListSerializer,
    SoftwareDetailSerializer,
    SoftwareLicenseSerializer,
    SoftwareLicenseListSerializer,
    SoftwareLicenseDetailSerializer,
    LicenseAllocationSerializer,
    LicenseAllocationListSerializer,
    LicenseAllocationDetailSerializer,
    ITMaintenanceRecordSerializer,
    ITMaintenanceRecordListSerializer,
    ITMaintenanceRecordDetailSerializer,
    ConfigurationChangeSerializer,
    ConfigurationChangeListSerializer,
    ConfigurationChangeDetailSerializer,
)
from apps.it_assets.filters import (
    ITAssetInfoFilter,
    SoftwareFilter,
    SoftwareLicenseFilter,
    LicenseAllocationFilter,
    ITMaintenanceRecordFilter,
    ConfigurationChangeFilter,
)


# Base permission classes for IT Assets
BASE_PERMISSION_CLASSES = [permissions.IsAuthenticated, IsOrganizationMember]


class ITAssetInfoViewSet(BaseModelViewSetWithBatch):
    """
    ViewSet for ITAssetInfo model.

    Provides:
    - Standard CRUD operations
    - Batch operations (delete, restore, update)
    - List of deleted records
    - Single record restore
    """
    queryset = ITAssetInfo.objects.select_related('asset', 'organization').all()
    permission_classes = BASE_PERMISSION_CLASSES
    filterset_class = ITAssetInfoFilter
    search_fields = ['asset__asset_code', 'asset__asset_name', 'cpu_model', 'os_name', 'hostname']
    ordering_fields = ['created_at', 'updated_at', 'ram_capacity', 'disk_capacity', 'cpu_model']
    ordering = ['-created_at']

    def get_serializer_class(self):
        """Return appropriate serializer based on action."""
        if self.action == 'list':
            return ITAssetInfoListSerializer
        if self.action == 'retrieve':
            return ITAssetInfoDetailSerializer
        return ITAssetInfoSerializer


class SoftwareViewSet(BaseModelViewSetWithBatch):
    """
    ViewSet for Software model.

    Provides:
    - Standard CRUD operations
    - Batch operations (delete, restore, update)
    - List of deleted records
    - Single record restore
    """
    queryset = Software.objects.select_related('organization').all()
    permission_classes = BASE_PERMISSION_CLASSES
    filterset_class = SoftwareFilter
    search_fields = ['name', 'vendor', 'version', 'category']
    ordering_fields = ['created_at', 'updated_at', 'name', 'vendor', 'version']
    ordering = ['name', 'version']

    def get_serializer_class(self):
        """Return appropriate serializer based on action."""
        if self.action == 'list':
            return SoftwareListSerializer
        if self.action == 'retrieve':
            return SoftwareDetailSerializer
        return SoftwareSerializer


class SoftwareLicenseViewSet(BaseModelViewSetWithBatch):
    """
    ViewSet for SoftwareLicense model.

    Provides:
    - Standard CRUD operations
    - Batch operations (delete, restore, update)
    - List of deleted records
    - Single record restore
    - Custom action: expiring (licenses expiring within 30 days)
    """
    queryset = SoftwareLicense.objects.select_related(
        'software', 'organization'
    ).all()
    permission_classes = BASE_PERMISSION_CLASSES
    filterset_class = SoftwareLicenseFilter
    search_fields = ['software__name', 'license_key', 'vendor_reference']
    ordering_fields = ['created_at', 'updated_at', 'expiry_date', 'software__name']
    ordering = ['-created_at']

    def get_serializer_class(self):
        """Return appropriate serializer based on action."""
        if self.action == 'list':
            return SoftwareLicenseListSerializer
        if self.action == 'retrieve':
            return SoftwareLicenseDetailSerializer
        return SoftwareLicenseSerializer

    @action(detail=False, methods=['get'])
    def expiring(self, request):
        """
        Get licenses expiring within 30 days.

        GET /api/it-assets/licenses/expiring/
        """
        from django.utils import timezone
        from datetime import timedelta

        thirty_days_from_now = timezone.now().date() + timedelta(days=30)
        queryset = self.get_queryset().filter(
            expiry_date__lte=thirty_days_from_now,
            expiry_date__gte=timezone.now().date(),
            is_deleted=False
        )

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response({
            'success': True,
            'data': serializer.data
        })


class LicenseAllocationViewSet(BaseModelViewSetWithBatch):
    """
    ViewSet for LicenseAllocation model.

    Provides:
    - Standard CRUD operations
    - Batch operations (delete, restore, update)
    - List of deleted records
    - Single record restore
    - Custom action: deallocate (deallocate a license from an asset)
    """
    queryset = LicenseAllocation.objects.select_related(
        'license', 'license__software', 'asset', 'allocated_by', 'deallocated_by', 'organization'
    ).all()
    permission_classes = BASE_PERMISSION_CLASSES
    filterset_class = LicenseAllocationFilter
    search_fields = ['asset__asset_code', 'asset__asset_name', 'license__software__name']
    ordering_fields = ['created_at', 'updated_at', 'allocated_date', 'deallocated_date']
    ordering = ['-allocated_date']

    def get_serializer_class(self):
        """Return appropriate serializer based on action."""
        if self.action == 'list':
            return LicenseAllocationListSerializer
        if self.action == 'retrieve':
            return LicenseAllocationDetailSerializer
        return LicenseAllocationSerializer

    @action(detail=True, methods=['post'])
    def deallocate(self, request, pk=None):
        """
        Deallocate a license from an asset.

        POST /api/it-assets/license-allocations/{id}/deallocate/

        Request body:
        {
            "notes": "Optional notes about deallocation"
        }
        """
        from datetime import date

        allocation = self.get_object()

        if allocation.deallocated_date is not None:
            return Response({
                'success': False,
                'error': {
                    'code': 'VALIDATION_ERROR',
                    'message': 'License is already deallocated'
                }
            }, status=400)

        # Update allocation
        allocation.deallocated_date = date.today()
        allocation.deallocated_by = request.user
        allocation.notes = request.data.get('notes', allocation.notes)
        allocation.save()

        serializer = self.get_serializer(allocation)
        return Response({
            'success': True,
            'message': 'License deallocated successfully',
            'data': serializer.data
        })


class ITMaintenanceRecordViewSet(BaseModelViewSetWithBatch):
    """
    ViewSet for ITMaintenanceRecord model.

    Provides:
    - Standard CRUD operations
    - Batch operations (delete, restore, update)
    - List of deleted records
    - Single record restore
    """
    queryset = ITMaintenanceRecord.objects.select_related(
        'asset', 'performed_by', 'organization'
    ).all()
    permission_classes = BASE_PERMISSION_CLASSES
    filterset_class = ITMaintenanceRecordFilter
    search_fields = ['asset__asset_code', 'asset__asset_name', 'title', 'vendor']
    ordering_fields = ['created_at', 'updated_at', 'maintenance_date', 'maintenance_type']
    ordering = ['-maintenance_date']

    def get_serializer_class(self):
        """Return appropriate serializer based on action."""
        if self.action == 'list':
            return ITMaintenanceRecordListSerializer
        if self.action == 'retrieve':
            return ITMaintenanceRecordDetailSerializer
        return ITMaintenanceRecordSerializer


class ConfigurationChangeViewSet(BaseModelViewSetWithBatch):
    """
    ViewSet for ConfigurationChange model.

    Provides:
    - Standard CRUD operations
    - Batch operations (delete, restore, update)
    - List of deleted records
    - Single record restore
    """
    queryset = ConfigurationChange.objects.select_related(
        'asset', 'changed_by', 'organization'
    ).all()
    permission_classes = BASE_PERMISSION_CLASSES
    filterset_class = ConfigurationChangeFilter
    search_fields = ['asset__asset_code', 'asset__asset_name', 'field_name', 'change_reason']
    ordering_fields = ['created_at', 'updated_at', 'change_date', 'field_name']
    ordering = ['-change_date']

    def get_serializer_class(self):
        """Return appropriate serializer based on action."""
        if self.action == 'list':
            return ConfigurationChangeListSerializer
        if self.action == 'retrieve':
            return ConfigurationChangeDetailSerializer
        return ConfigurationChangeSerializer
