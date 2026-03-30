"""Runtime ViewSets for inventory follow-up queue management."""

from django.utils.translation import gettext_lazy as _
from rest_framework.decorators import action

from apps.common.responses.base import error_response, success_response
from apps.common.viewsets.base import BaseModelViewSetWithBatch
from apps.inventory.filters import InventoryFollowUpFilter
from apps.inventory.models import InventoryFollowUp
from apps.inventory.serializers import (
    InventoryFollowUpCompleteSerializer,
    InventoryFollowUpListSerializer,
    InventoryFollowUpReopenSerializer,
    InventoryFollowUpSerializer,
)
from apps.inventory.services import InventoryFollowUpService


class InventoryFollowUpViewSet(BaseModelViewSetWithBatch):
    """ViewSet for inventory follow-up queue records."""

    queryset = InventoryFollowUp.objects.all()
    serializer_class = InventoryFollowUpSerializer
    filterset_class = InventoryFollowUpFilter
    search_fields = ['follow_up_code', 'title', 'task__task_code', 'asset__asset_code', 'asset__asset_name']

    def get_serializer_class(self):
        """Return the serializer that matches the current action."""
        if self.action == 'list':
            return InventoryFollowUpListSerializer
        if self.action == 'complete':
            return InventoryFollowUpCompleteSerializer
        if self.action == 'reopen':
            return InventoryFollowUpReopenSerializer
        return InventoryFollowUpSerializer

    def create(self, request, *args, **kwargs):
        """Follow-up tasks are created from inventory difference execution."""
        return error_response(
            code='METHOD_NOT_ALLOWED',
            message=_('Follow-up tasks are created automatically from difference execution.'),
            http_status=405,
        )

    def update(self, request, *args, **kwargs):
        """Use explicit lifecycle actions instead of direct updates."""
        return error_response(
            code='METHOD_NOT_ALLOWED',
            message=_('Use complete or reopen actions to update follow-up status.'),
            http_status=405,
        )

    def retrieve(self, request, *args, **kwargs):
        """Retrieve a follow-up task with the standard response payload."""
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return success_response(data=serializer.data)

    @action(detail=True, methods=['post'], url_path='complete')
    def complete(self, request, pk=None):
        """Complete an inventory follow-up task."""
        follow_up = self.get_object()
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        service = InventoryFollowUpService()
        updated = service.complete_follow_up(
            follow_up_id=str(follow_up.id),
            user_id=str(request.user.id),
            completion_notes=serializer.validated_data.get('completion_notes', ''),
            evidence_refs=serializer.validated_data.get('evidence_refs'),
        )
        return success_response(
            data=InventoryFollowUpSerializer(updated).data,
            message=_('Follow-up task completed successfully.'),
        )

    @action(detail=True, methods=['post'], url_path='reopen')
    def reopen(self, request, pk=None):
        """Reopen a completed follow-up task."""
        follow_up = self.get_object()
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        service = InventoryFollowUpService()
        updated = service.reopen_follow_up(
            follow_up_id=str(follow_up.id),
            user_id=str(request.user.id),
        )
        return success_response(
            data=InventoryFollowUpSerializer(updated).data,
            message=_('Follow-up task reopened successfully.'),
        )
