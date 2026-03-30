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
    InventoryDifferenceAssignOwnerSerializer,
    InventoryDifferenceSubmitReviewSerializer,
    InventoryDifferenceDraftSerializer,
    InventoryDifferenceDecisionSerializer,
    InventoryDifferenceExecuteSerializer,
    InventoryDifferenceIgnoreSerializer,
    InventoryDifferenceCloseSerializer,
    InventoryDifferenceFollowUpSerializer,
    InventoryDifferenceCompleteFollowUpSerializer,
    InventoryDifferenceReopenFollowUpSerializer,
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
        elif self.action == 'assign_owner':
            return InventoryDifferenceAssignOwnerSerializer
        elif self.action == 'submit_review':
            return InventoryDifferenceSubmitReviewSerializer
        elif self.action == 'save_draft':
            return InventoryDifferenceDraftSerializer
        elif self.action in ['approve_resolution', 'reject_resolution']:
            return InventoryDifferenceDecisionSerializer
        elif self.action == 'execute_resolution':
            return InventoryDifferenceExecuteSerializer
        elif self.action == 'send_follow_up':
            return InventoryDifferenceFollowUpSerializer
        elif self.action == 'complete_follow_up':
            return InventoryDifferenceCompleteFollowUpSerializer
        elif self.action == 'reopen_follow_up':
            return InventoryDifferenceReopenFollowUpSerializer
        elif self.action == 'ignore':
            return InventoryDifferenceIgnoreSerializer
        elif self.action == 'close_difference':
            return InventoryDifferenceCloseSerializer
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

    @action(detail=True, methods=['post'], url_path='confirm')
    def confirm(self, request, pk=None):
        """Confirm a difference and optionally assign an owner."""
        difference = self.get_object()
        owner_id = request.data.get('owner_id')

        service = DifferenceService()
        try:
            updated = service.confirm_difference(
                difference_id=str(difference.id),
                user_id=str(request.user.id),
                owner_id=owner_id,
            )
            return success_response(
                data=InventoryDifferenceSerializer(updated).data,
                message=_('Difference confirmed successfully.'),
            )
        except Exception as e:
            return error_response(
                code='VALIDATION_ERROR',
                message=_('Failed to confirm difference.'),
                details={'error': str(e)},
            )

    @action(detail=True, methods=['post'], url_path='assign-owner')
    def assign_owner(self, request, pk=None):
        """Assign an owner for a difference."""
        difference = self.get_object()
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        service = DifferenceService()
        try:
            updated = service.assign_owner(
                difference_id=str(difference.id),
                owner_id=serializer.validated_data['owner_id'],
            )
            return success_response(
                data=InventoryDifferenceSerializer(updated).data,
                message=_('Difference owner assigned successfully.'),
            )
        except Exception as e:
            return error_response(
                code='VALIDATION_ERROR',
                message=_('Failed to assign difference owner.'),
                details={'error': str(e)},
            )

    @action(detail=True, methods=['post'], url_path='submit-review')
    def submit_review(self, request, pk=None):
        """Submit a difference resolution for review."""
        difference = self.get_object()
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        service = DifferenceService()
        try:
            updated = service.submit_review(
                difference_id=str(difference.id),
                user_id=str(request.user.id),
                resolution=serializer.validated_data.get('resolution'),
                closure_type=serializer.validated_data.get('closure_type'),
                linked_action_code=serializer.validated_data.get('linked_action_code'),
                evidence_refs=serializer.validated_data.get('evidence_refs'),
            )
            return success_response(
                data=InventoryDifferenceSerializer(updated).data,
                message=_('Difference submitted for review successfully.'),
            )
        except Exception as e:
            return error_response(
                code='VALIDATION_ERROR',
                message=_('Failed to submit difference for review.'),
                details={'error': str(e)},
            )

    @action(detail=True, methods=['post'], url_path='save-draft')
    def save_draft(self, request, pk=None):
        """Persist editable difference handling fields without changing status."""
        difference = self.get_object()
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        service = DifferenceService()
        try:
            updated = service.save_draft(
                difference_id=str(difference.id),
                resolution=serializer.validated_data.get('resolution'),
                closure_type=serializer.validated_data.get('closure_type'),
                linked_action_code=serializer.validated_data.get('linked_action_code'),
                evidence_refs=serializer.validated_data.get('evidence_refs'),
                closure_notes=serializer.validated_data.get('closure_notes'),
            )
            return success_response(
                data=InventoryDifferenceSerializer(updated).data,
                message=_('Difference draft saved successfully.'),
            )
        except Exception as e:
            return error_response(
                code='VALIDATION_ERROR',
                message=_('Failed to save difference draft.'),
                details={'error': str(e)},
            )

    @action(detail=True, methods=['post'], url_path='approve-resolution')
    def approve_resolution(self, request, pk=None):
        """Approve a submitted difference resolution."""
        difference = self.get_object()
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        service = DifferenceService()
        try:
            updated = service.approve_resolution(
                difference_id=str(difference.id),
                user_id=str(request.user.id),
                closure_notes=serializer.validated_data.get('closure_notes'),
            )
            return success_response(
                data=InventoryDifferenceSerializer(updated).data,
                message=_('Difference resolution approved successfully.'),
            )
        except Exception as e:
            return error_response(
                code='VALIDATION_ERROR',
                message=_('Failed to approve difference resolution.'),
                details={'error': str(e)},
            )

    @action(detail=True, methods=['post'], url_path='reject-resolution')
    def reject_resolution(self, request, pk=None):
        """Reject a submitted difference resolution."""
        difference = self.get_object()
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        service = DifferenceService()
        try:
            updated = service.reject_resolution(
                difference_id=str(difference.id),
                closure_notes=serializer.validated_data.get('closure_notes'),
            )
            return success_response(
                data=InventoryDifferenceSerializer(updated).data,
                message=_('Difference resolution rejected successfully.'),
            )
        except Exception as e:
            return error_response(
                code='VALIDATION_ERROR',
                message=_('Failed to reject difference resolution.'),
                details={'error': str(e)},
            )

    @action(detail=True, methods=['post'], url_path='execute-resolution')
    def execute_resolution(self, request, pk=None):
        """Execute an approved difference resolution."""
        difference = self.get_object()
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        service = DifferenceService()
        try:
            updated = service.execute_resolution(
                difference_id=str(difference.id),
                user_id=str(request.user.id),
                resolution=serializer.validated_data.get('resolution'),
                sync_asset=serializer.validated_data.get('sync_asset', True),
                linked_action_code=serializer.validated_data.get('linked_action_code'),
            )
            message = _('Difference resolution executed successfully.')
            linked_action_execution = {}
            if isinstance(updated.custom_fields, dict):
                linked_action_execution = updated.custom_fields.get('linked_action_execution') or {}
            linked_action_message = ''
            if isinstance(linked_action_execution, dict):
                linked_action_message = str(linked_action_execution.get('message') or '').strip()
            if linked_action_message:
                message = f'{message} {linked_action_message}'
            return success_response(
                data=InventoryDifferenceSerializer(updated).data,
                message=message,
            )
        except Exception as e:
            return error_response(
                code='VALIDATION_ERROR',
                message=_('Failed to execute difference resolution.'),
                details={'error': str(e)},
            )

    @action(detail=True, methods=['post'], url_path='ignore')
    def ignore(self, request, pk=None):
        """Ignore a difference without syncing asset data."""
        difference = self.get_object()
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        service = DifferenceService()
        try:
            updated = service.ignore_difference(
                difference_id=str(difference.id),
                user_id=str(request.user.id),
                resolution=serializer.validated_data.get('resolution'),
                closure_notes=serializer.validated_data.get('closure_notes'),
            )
            return success_response(
                data=InventoryDifferenceSerializer(updated).data,
                message=_('Difference ignored successfully.'),
            )
        except Exception as e:
            return error_response(
                code='VALIDATION_ERROR',
                message=_('Failed to ignore difference.'),
                details={'error': str(e)},
            )

    @action(detail=True, methods=['post'], url_path='send-follow-up')
    def send_follow_up(self, request, pk=None):
        """Create or resend a manual follow-up inbox notification."""
        difference = self.get_object()
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        service = DifferenceService()
        try:
            updated = service.send_follow_up(
                difference_id=str(difference.id),
                user_id=str(request.user.id),
            )
            return success_response(
                data=InventoryDifferenceSerializer(updated).data,
                message=_('Difference follow-up reminder sent successfully.'),
            )
        except Exception as e:
            return error_response(
                code='VALIDATION_ERROR',
                message=_('Failed to send difference follow-up reminder.'),
                details={'error': str(e)},
            )

    @action(detail=True, methods=['post'], url_path='complete-follow-up')
    def complete_follow_up(self, request, pk=None):
        """Complete the current manual follow-up task linked to the difference."""
        difference = self.get_object()
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        service = DifferenceService()
        try:
            updated = service.complete_follow_up(
                difference_id=str(difference.id),
                user_id=str(request.user.id),
                completion_notes=serializer.validated_data.get('completion_notes'),
                evidence_refs=serializer.validated_data.get('evidence_refs'),
            )
            return success_response(
                data=InventoryDifferenceSerializer(updated).data,
                message=_('Difference follow-up completed successfully.'),
            )
        except Exception as e:
            return error_response(
                code='VALIDATION_ERROR',
                message=_('Failed to complete the difference follow-up.'),
                details={'error': str(e)},
            )

    @action(detail=True, methods=['post'], url_path='reopen-follow-up')
    def reopen_follow_up(self, request, pk=None):
        """Reopen the current manual follow-up task linked to the difference."""
        difference = self.get_object()
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        service = DifferenceService()
        try:
            updated = service.reopen_follow_up(
                difference_id=str(difference.id),
                user_id=str(request.user.id),
            )
            return success_response(
                data=InventoryDifferenceSerializer(updated).data,
                message=_('Difference follow-up reopened successfully.'),
            )
        except Exception as e:
            return error_response(
                code='VALIDATION_ERROR',
                message=_('Failed to reopen the difference follow-up.'),
                details={'error': str(e)},
            )

    @action(detail=True, methods=['post'], url_path='close-difference')
    def close_difference(self, request, pk=None):
        """Close a resolved or ignored difference."""
        difference = self.get_object()
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        service = DifferenceService()
        try:
            updated = service.close_difference(
                difference_id=str(difference.id),
                user_id=str(request.user.id),
                closure_notes=serializer.validated_data.get('closure_notes'),
                evidence_refs=serializer.validated_data.get('evidence_refs'),
            )
            return success_response(
                data=InventoryDifferenceSerializer(updated).data,
                message=_('Difference closed successfully.'),
            )
        except Exception as e:
            return error_response(
                code='VALIDATION_ERROR',
                message=_('Failed to close difference.'),
                details={'error': str(e)},
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
            DifferenceService()._sync_asset_from_difference(difference)

            return success_response(message=_('Asset synced successfully.'))
        except Exception as e:
            return error_response(
                code='SERVER_ERROR',
                message=_('Failed to sync asset.'),
                details={'error': str(e)}
            )
