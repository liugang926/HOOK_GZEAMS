"""
ViewSets for Mobile Device and Security Log models.
"""
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from apps.common.viewsets.base import BaseModelViewSetWithBatch
from apps.mobile.models import MobileDevice, DeviceSecurityLog
from apps.mobile.serializers import (
    MobileDeviceSerializer,
    MobileDeviceListSerializer,
    MobileDeviceDetailSerializer,
    DeviceSecurityLogSerializer,
)
from apps.mobile.services import DeviceService
from apps.mobile.filters import MobileDeviceFilter, DeviceSecurityLogFilter


class MobileDeviceViewSet(BaseModelViewSetWithBatch):
    """
    ViewSet for MobileDevice management.

    Inherits from BaseModelViewSetWithBatch to get:
    - Organization filtering
    - Soft delete support
    - Batch operations
    - Audit field auto-population
    """

    permission_classes = [IsAuthenticated]
    filterset_class = MobileDeviceFilter

    def get_queryset(self):
        """Get filtered queryset for current user."""
        return MobileDevice.objects.filter(user=self.request.user)

    def get_serializer_class(self):
        """Return appropriate serializer based on action."""
        if self.action == 'list':
            return MobileDeviceListSerializer
        if self.action == 'retrieve':
            return MobileDeviceDetailSerializer
        return MobileDeviceSerializer

    @action(detail=False, methods=['post'])
    def register(self, request):
        """
        Register a new device.

        POST /api/mobile/devices/register/
        {
            "device_id": "device_001",
            "device_info": {
                "device_name": "iPhone 13",
                "device_type": "ios",
                "os_version": "16.0",
                "app_version": "1.0.0",
                "ip_address": "192.168.1.100"
            }
        }
        """
        device_id = request.data.get('device_id')
        device_info = request.data.get('device_info', {})

        if not device_id:
            return Response(
                {'error': 'Device ID is required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Check device limit
        if not DeviceService.check_device_limit(request.user):
            # Unbind old devices, keep 2
            DeviceService.revoke_old_devices(request.user, keep_count=2)

        device = DeviceService.register_device(request.user, device_id, device_info)
        serializer = self.get_serializer(device)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def unbind(self, request, pk=None):
        """
        Unbind a device.

        POST /api/mobile/devices/{id}/unbind/
        """
        if DeviceService.unbind_device(request.user, pk):
            return Response({'message': 'Device unbind successfully'})
        return Response(
            {'error': 'Unbind failed'},
            status=status.HTTP_400_BAD_REQUEST
        )

    @action(detail=False, methods=['get'])
    def my_devices(self, request):
        """
        Get current user's devices.

        GET /api/mobile/devices/my_devices/
        """
        devices = DeviceService.get_user_devices(request.user)
        serializer = MobileDeviceListSerializer(devices, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['post'])
    def batch_unbind(self, request):
        """
        Batch unbind multiple devices.

        POST /api/mobile/devices/batch_unbind/
        {
            "ids": ["uuid1", "uuid2", "uuid3"]
        }
        """
        ids = request.data.get('ids', [])
        if not ids:
            return Response(
                {'error': 'No device IDs provided'},
                status=status.HTTP_400_BAD_REQUEST
            )

        results = []
        succeeded = 0
        failed = 0

        for device_id in ids:
            if DeviceService.unbind_device(request.user, device_id):
                succeeded += 1
                results.append({'id': device_id, 'success': True})
            else:
                failed += 1
                results.append({'id': device_id, 'success': False, 'error': 'Device not found'})

        return Response({
            'message': f'Batch unbind completed: {succeeded} succeeded, {failed} failed',
            'summary': {'total': len(ids), 'succeeded': succeeded, 'failed': failed},
            'results': results
        })


class DeviceSecurityLogViewSet(BaseModelViewSetWithBatch):
    """
    ViewSet for DeviceSecurityLog.

    Inherits from BaseModelViewSetWithBatch to get:
    - Organization filtering
    - Soft delete support
    - Batch operations
    - Audit field auto-population

    Read-only for security audit purposes.
    """

    permission_classes = [IsAuthenticated]
    filterset_class = DeviceSecurityLogFilter
    serializer_class = DeviceSecurityLogSerializer

    def get_queryset(self):
        """Get filtered queryset for current user's devices."""
        # Get current user's device IDs
        device_ids = MobileDevice.objects.filter(
            user=self.request.user
        ).values_list('id', flat=True)
        return DeviceSecurityLog.objects.filter(device_id__in=device_ids)

    # Read-only - disable modifications
    http_method_names = ['get', 'head', 'options']
