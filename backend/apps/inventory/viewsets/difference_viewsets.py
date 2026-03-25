"""
ViewSets for Inventory Difference model.
"""
from rest_framework.decorators import action
from django.utils.translation import gettext_lazy as _

from apps.common.viewsets.base import BaseModelViewSetWithBatch
from apps.common.responses.base import success_response, error_response
from apps.inventory.models import InventoryDifference
from apps.inventory.serializers import (
    InventoryDifferenceSerializer,
    InventoryDifferenceListSerializer,
    InventoryDifferenceResolveSerializer,
)
from apps.inventory.filters import InventoryDifferenceFilter
from apps.inventory.services import DifferenceService


class InventoryDifferenceViewSet(BaseModelViewSetWithBatch):
    """
    ViewSet for inventory difference management.

    Provides:
    - Standard CRUD operations (list, retrieve)
    - Resolve differences
    - Batch resolve
    - Difference summary
    - Pending differences list
    """

    queryset = InventoryDifference.objects.all()
    filterset_class = InventoryDifferenceFilter
    search_fields = ['asset__asset_code', 'asset__asset_name', 'description', 'resolution']

    def get_serializer_class(self):
        """Get appropriate serializer based on action."""
        if self.action == 'list':
            return InventoryDifferenceListSerializer
        elif self.action == 'retrieve':
            return InventoryDifferenceSerializer
        elif self.action == 'resolve':
            return InventoryDifferenceResolveSerializer
        return InventoryDifferenceSerializer

    def retrieve(self, request, *args, **kwargs):
        """Retrieve a single difference with standard response format."""
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return success_response(data=serializer.data)

    def create(self, request, *args, **kwargs):
        """Differences are auto-generated when task is completed."""
        return error_response(
            code='METHOD_NOT_ALLOWED',
            message=_('Differences are automatically generated when completing an inventory task.'),
            http_status=405
        )

    def update(self, request, *args, **kwargs):
        """Use the resolve action to update difference status."""
        return error_response(
            code='METHOD_NOT_ALLOWED',
            message=_('Use the resolve action to update difference status.'),
            http_status=405
        )

    @action(detail=True, methods=['post'], url_path='resolve')
    def resolve(self, request, pk=None):
        """
        Resolve a difference.

        POST /api/inventory/differences/{id}/resolve/
        {
            "status": "resolved" | "ignored",
            "resolution": "Resolution description"
        }
        """
        difference = self.get_object()
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        service = DifferenceService()
        try:
            resolved = service.resolve_difference(
                difference_id=str(difference.id),
                user_id=str(request.user.id),
                status=serializer.validated_data['status'],
                resolution=serializer.validated_data.get('resolution', '')
            )
            response_serializer = InventoryDifferenceSerializer(resolved)
            return success_response(
                data=response_serializer.data,
                message=_('Difference resolved successfully.')
            )
        except Exception as e:
            return error_response(
                code='VALIDATION_ERROR',
                message=_('Failed to resolve difference.'),
                details={'error': str(e)}
            )

    @action(detail=False, methods=['post'], url_path='batch-resolve')
    def batch_resolve(self, request, *args, **kwargs):
        """
        Batch resolve differences.

        POST /api/inventory/differences/batch-resolve/
        {
            "ids": ["id1", "id2", ...],
            "status": "resolved" | "ignored",
            "resolution": "Resolution description"
        }
        """
        difference_ids = request.data.get('ids', [])
        resolve_status = request.data.get('status')
        resolution = request.data.get('resolution', '')

        if not difference_ids:
            return error_response(
                code='VALIDATION_ERROR',
                message=_('Difference IDs are required.')
            )

        if resolve_status not in ['resolved', 'ignored']:
            return error_response(
                code='VALIDATION_ERROR',
                message=_('Status must be "resolved" or "ignored".')
            )

        service = DifferenceService()
        results = service.batch_resolve_differences(
            difference_ids=difference_ids,
            user_id=str(request.user.id),
            status=resolve_status,
            resolution=resolution
        )

        message = _('Batch resolve completed.') if results['failed'] == 0 else _('Batch resolve completed with some failures.')
        return success_response(data=results, message=message)

    @action(detail=False, methods=['get'], url_path='pending')
    def pending(self, request, *args, **kwargs):
        """
        Get all pending differences for a task.

        GET /api/inventory/differences/pending/?task=task_id
        """
        task_id = request.query_params.get('task')
        if not task_id:
            return error_response(
                code='VALIDATION_ERROR',
                message=_('Task ID is required.')
            )

        service = DifferenceService()
        differences = service.get_pending_differences(task_id)

        serializer = InventoryDifferenceListSerializer(differences, many=True)
        return success_response(data={
            'count': len(differences),
            'results': serializer.data
        })

    @action(detail=False, methods=['get'], url_path='by-type')
    def by_type(self, request, *args, **kwargs):
        """
        Get differences filtered by type.

        GET /api/inventory/differences/by-type/?task=task_id&type=missing
        """
        task_id = request.query_params.get('task')
        difference_type = request.query_params.get('type')

        if not task_id:
            return error_response(
                code='VALIDATION_ERROR',
                message=_('Task ID is required.')
            )

        if not difference_type:
            return error_response(
                code='VALIDATION_ERROR',
                message=_('Difference type is required.')
            )

        service = DifferenceService()
        differences = service.get_differences_by_type(task_id, difference_type)

        serializer = InventoryDifferenceListSerializer(differences, many=True)
        return success_response(data={
            'count': len(differences),
            'results': serializer.data
        })

    @action(detail=False, methods=['get'], url_path='summary')
    def summary(self, request, *args, **kwargs):
        """
        Get summary of differences for a task.

        GET /api/inventory/differences/summary/?task=task_id
        """
        task_id = request.query_params.get('task')
        if not task_id:
            return error_response(
                code='VALIDATION_ERROR',
                message=_('Task ID is required.')
            )

        service = DifferenceService()
        summary = service.get_difference_summary(task_id)
        return success_response(data=summary)

    @action(detail=True, methods=['post'], url_path='sync-asset')
    def sync_asset(self, request, pk=None):
        """
        Sync difference data back to asset.

        For location/custodian changes, updates the asset accordingly.

        POST /api/inventory/differences/{id}/sync-asset/
        """
        difference = self.get_object()

        if difference.status != InventoryDifference.STATUS_RESOLVED:
            return error_response(
                code='VALIDATION_ERROR',
                message=_('Only resolved differences can be synced.')
            )

        try:
            from apps.assets.models import Asset
            from apps.assets.models import Location
            from apps.accounts.models import User

            asset = Asset.objects.get(id=difference.asset_id, is_deleted=False)

            # Sync location for location changes
            if difference.difference_type == InventoryDifference.TYPE_LOCATION_MISMATCH:
                if difference.actual_location_id:
                    try:
                        location = Location.objects.get(id=difference.actual_location_id)
                        asset.location = location
                    except Location.DoesNotExist:
                        pass

            # Sync custodian for custodian changes
            if difference.difference_type == InventoryDifference.TYPE_CUSTODIAN_MISMATCH:
                if difference.actual_custodian_id:
                    try:
                        custodian = User.objects.get(id=difference.actual_custodian_id)
                        asset.custodian = custodian
                    except User.DoesNotExist:
                        pass

            # Update status for damaged assets
            if difference.difference_type == InventoryDifference.TYPE_DAMAGED:
                asset.status = 'damaged'

            asset.save()

            return success_response(message=_('Asset synced successfully.'))
        except Exception as e:
            return error_response(
                code='SERVER_ERROR',
                message=_('Failed to sync asset.'),
                details={'error': str(e)}
            )
