from rest_framework import permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from apps.common.viewsets.base import BaseModelViewSetWithBatch
from apps.common.permissions.base import IsOrganizationMember
from .models import Software, SoftwareLicense, LicenseAllocation
from .serializers import (
    SoftwareSerializer, SoftwareListSerializer, SoftwareDetailSerializer,
    SoftwareLicenseSerializer, SoftwareLicenseListSerializer, SoftwareLicenseDetailSerializer,
    LicenseAllocationSerializer, LicenseAllocationListSerializer, LicenseAllocationDetailSerializer
)
from .filters import SoftwareFilter, SoftwareLicenseFilter, LicenseAllocationFilter


# Base permission classes
BASE_PERMISSION_CLASSES = [permissions.IsAuthenticated, IsOrganizationMember]


class SoftwareViewSet(BaseModelViewSetWithBatch):
    """
    Software Catalog ViewSet

    Provides:
    - Standard CRUD operations
    - Batch operations (delete, restore, update)
    """
    queryset = Software.objects.select_related('organization', 'category').all()
    permission_classes = BASE_PERMISSION_CLASSES
    filterset_class = SoftwareFilter
    search_fields = ['name', 'vendor', 'version', 'code']
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
    Software License ViewSet

    Provides:
    - Standard CRUD operations
    - Batch operations (delete, restore, update)
    - Custom action: expiring (licenses expiring within 30 days)
    - Custom action: compliance_report
    """
    queryset = SoftwareLicense.objects.select_related(
        'software', 'vendor', 'organization'
    ).all()
    permission_classes = BASE_PERMISSION_CLASSES
    filterset_class = SoftwareLicenseFilter
    search_fields = ['software__name', 'license_no', 'agreement_no']
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

        GET /api/software-licenses/licenses/expiring/
        """
        from django.utils import timezone
        from datetime import timedelta

        thirty_days_from_now = timezone.now().date() + timedelta(days=30)
        queryset = self.get_queryset().filter(
            expiry_date__lte=thirty_days_from_now,
            expiry_date__gte=timezone.now().date(),
            status='active'
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

    @action(detail=False, methods=['get'])
    def compliance_report(self, request):
        """
        Get software compliance report.

        GET /api/software-licenses/licenses/compliance-report/

        Returns:
        - total_licenses: Total active licenses
        - expiring_licenses: Count expiring within 30 days
        - over_utilized: List of licenses with >100% utilization
        """
        from django.utils import timezone
        from datetime import timedelta

        queryset = self.get_queryset().filter(status='active')
        total_licenses = queryset.count()

        # Expiring within 30 days
        thirty_days_from_now = timezone.now().date() + timedelta(days=30)
        expiring_licenses = queryset.filter(
            expiry_date__lte=thirty_days_from_now
        ).count()

        # Over-utilized licenses
        over_utilized = []
        for license in queryset:
            if license.utilization_rate() > 100:
                over_utilized.append({
                    'id': str(license.id),
                    'license_no': license.license_no,
                    'software': license.software.name,
                    'utilization': round(license.utilization_rate(), 1)
                })

        return Response({
            'success': True,
            'data': {
                'total_licenses': total_licenses,
                'expiring_licenses': expiring_licenses,
                'over_utilized': over_utilized
            }
        })


class LicenseAllocationViewSet(BaseModelViewSetWithBatch):
    """
    License Allocation ViewSet

    Provides:
    - Standard CRUD operations
    - Batch operations (delete, restore, update)
    - Custom action: deallocate (deallocate a license from an asset)
    """
    queryset = LicenseAllocation.objects.select_related(
        'license', 'license__software', 'asset',
        'allocated_by', 'deallocated_by', 'organization'
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

    def perform_create(self, serializer):
        """Validate license availability before allocation."""
        license_obj = serializer.validated_data['license']

        if license_obj.available_units() <= 0:
            return Response(
                {
                    'success': False,
                    'error': {
                        'code': 'NO_AVAILABLE_LICENSES',
                        'message': 'No available licenses for this software'
                    }
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        from django.utils import timezone
        serializer.save(
            allocated_by=self.request.user,
            allocated_date=timezone.now().date()
        )

    @action(detail=True, methods=['post'])
    def deallocate(self, request, pk=None):
        """
        Deallocate a license from an asset.

        POST /api/software-licenses/license-allocations/{id}/deallocate/

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
        allocation.is_active = False
        allocation.notes = request.data.get('notes', allocation.notes)
        allocation.save()

        # Update license usage
        if allocation.license.used_units > 0:
            allocation.license.used_units -= 1
            allocation.license.save()

        serializer = self.get_serializer(allocation)
        return Response({
            'success': True,
            'message': 'License deallocated successfully',
            'data': serializer.data
        })


__all__ = [
    'SoftwareViewSet',
    'SoftwareLicenseViewSet',
    'LicenseAllocationViewSet',
]
