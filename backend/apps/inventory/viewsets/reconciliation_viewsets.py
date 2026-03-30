"""
ViewSets for inventory reconciliation and report objects.
"""
from django.utils.translation import gettext_lazy as _
from rest_framework import status
from rest_framework.decorators import action

from apps.common.responses.base import error_response, success_response
from apps.common.viewsets.base import BaseModelViewSetWithBatch
from apps.inventory.filters import InventoryReconciliationFilter, InventoryReportFilter
from apps.inventory.models import InventoryReconciliation, InventoryReport
from apps.inventory.serializers import (
    InventoryReconciliationCreateSerializer,
    InventoryReconciliationDecisionSerializer,
    InventoryReconciliationListSerializer,
    InventoryReconciliationSerializer,
    InventoryReportCreateSerializer,
    InventoryReportDecisionSerializer,
    InventoryReportListSerializer,
    InventoryReportSerializer,
)
from apps.inventory.services import (
    InventoryReconciliationService,
    InventoryReportService,
)


class InventoryReconciliationViewSet(BaseModelViewSetWithBatch):
    """ViewSet for inventory reconciliation records."""

    queryset = InventoryReconciliation.objects.select_related(
        'task',
        'reconciled_by',
        'current_approver',
    ).all()
    filterset_class = InventoryReconciliationFilter
    search_fields = ['reconciliation_no', 'task__task_code', 'task__task_name', 'note']

    def get_serializer_class(self):
        """Return the serializer for the current action."""
        if self.action == 'list':
            return InventoryReconciliationListSerializer
        if self.action == 'create':
            return InventoryReconciliationCreateSerializer
        if self.action in {'approve', 'reject'}:
            return InventoryReconciliationDecisionSerializer
        return InventoryReconciliationSerializer

    def retrieve(self, request, *args, **kwargs):
        """Retrieve a reconciliation with the standard success envelope."""
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return success_response(data=serializer.data)

    def create(self, request, *args, **kwargs):
        """Create a reconciliation from a completed task."""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        service = InventoryReconciliationService()
        try:
            reconciliation = service.create_reconciliation(
                task_id=str(serializer.validated_data['task'].id),
                user=request.user,
                note=serializer.validated_data.get('note', ''),
            )
            return success_response(
                data=InventoryReconciliationSerializer(reconciliation).data,
                message=_('Inventory reconciliation created successfully.'),
                http_status=status.HTTP_201_CREATED,
            )
        except Exception as exc:
            return error_response(
                code='VALIDATION_ERROR',
                message=_('Failed to create inventory reconciliation.'),
                details={'error': str(exc)},
            )

    def update(self, request, *args, **kwargs):
        """Use explicit approval actions instead of direct updates."""
        return error_response(
            code='METHOD_NOT_ALLOWED',
            message=_('Use submit, approve, or reject actions to update reconciliation status.'),
            http_status=405,
        )

    def partial_update(self, request, *args, **kwargs):
        """Use explicit approval actions instead of direct updates."""
        return self.update(request, *args, **kwargs)

    @action(detail=True, methods=['post'], url_path='submit')
    def submit(self, request, pk=None):
        """Submit a reconciliation for approval."""
        reconciliation = self.get_object()
        service = InventoryReconciliationService()
        try:
            updated = service.submit(str(reconciliation.id), request.user)
            return success_response(
                data=InventoryReconciliationSerializer(updated).data,
                message=_('Inventory reconciliation submitted successfully.'),
            )
        except Exception as exc:
            return error_response(
                code='VALIDATION_ERROR',
                message=_('Failed to submit inventory reconciliation.'),
                details={'error': str(exc)},
            )

    @action(detail=True, methods=['post'], url_path='approve')
    def approve(self, request, pk=None):
        """Approve a submitted reconciliation."""
        reconciliation = self.get_object()
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        service = InventoryReconciliationService()
        try:
            updated = service.approve(
                str(reconciliation.id),
                user=request.user,
                comment=serializer.validated_data.get('comment', ''),
            )
            return success_response(
                data=InventoryReconciliationSerializer(updated).data,
                message=_('Inventory reconciliation approved successfully.'),
            )
        except Exception as exc:
            return error_response(
                code='VALIDATION_ERROR',
                message=_('Failed to approve inventory reconciliation.'),
                details={'error': str(exc)},
            )

    @action(detail=True, methods=['post'], url_path='reject')
    def reject(self, request, pk=None):
        """Reject a submitted reconciliation."""
        reconciliation = self.get_object()
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        service = InventoryReconciliationService()
        try:
            updated = service.reject(
                str(reconciliation.id),
                user=request.user,
                reason=serializer.validated_data.get('reason', ''),
            )
            return success_response(
                data=InventoryReconciliationSerializer(updated).data,
                message=_('Inventory reconciliation rejected successfully.'),
            )
        except Exception as exc:
            return error_response(
                code='VALIDATION_ERROR',
                message=_('Failed to reject inventory reconciliation.'),
                details={'error': str(exc)},
            )


class InventoryReportViewSet(BaseModelViewSetWithBatch):
    """ViewSet for generated inventory reports."""

    queryset = InventoryReport.objects.select_related(
        'task',
        'generated_by',
        'current_approver',
    ).all()
    filterset_class = InventoryReportFilter
    search_fields = ['report_no', 'task__task_code', 'task__task_name']

    def get_serializer_class(self):
        """Return the serializer for the current action."""
        if self.action == 'list':
            return InventoryReportListSerializer
        if self.action == 'create':
            return InventoryReportCreateSerializer
        if self.action in {'approve', 'reject'}:
            return InventoryReportDecisionSerializer
        return InventoryReportSerializer

    def retrieve(self, request, *args, **kwargs):
        """Retrieve a report with the standard success envelope."""
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return success_response(data=serializer.data)

    def create(self, request, *args, **kwargs):
        """Generate a report snapshot for a completed inventory task."""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        service = InventoryReportService()
        try:
            report = service.generate_report(
                task_id=str(serializer.validated_data['task'].id),
                user=request.user,
                template_id=serializer.validated_data.get('template_id', ''),
            )
            return success_response(
                data=InventoryReportSerializer(report).data,
                message=_('Inventory report generated successfully.'),
                http_status=status.HTTP_201_CREATED,
            )
        except Exception as exc:
            return error_response(
                code='VALIDATION_ERROR',
                message=_('Failed to generate inventory report.'),
                details={'error': str(exc)},
            )

    def update(self, request, *args, **kwargs):
        """Use submit and approval actions instead of direct updates."""
        return error_response(
            code='METHOD_NOT_ALLOWED',
            message=_('Use submit, approve, reject, or export actions to manage reports.'),
            http_status=405,
        )

    def partial_update(self, request, *args, **kwargs):
        """Use submit and approval actions instead of direct updates."""
        return self.update(request, *args, **kwargs)

    @action(detail=True, methods=['post'], url_path='submit')
    def submit(self, request, pk=None):
        """Submit a generated report for approval."""
        report = self.get_object()
        service = InventoryReportService()
        try:
            updated = service.submit(str(report.id), request.user)
            return success_response(
                data=InventoryReportSerializer(updated).data,
                message=_('Inventory report submitted successfully.'),
            )
        except Exception as exc:
            return error_response(
                code='VALIDATION_ERROR',
                message=_('Failed to submit inventory report.'),
                details={'error': str(exc)},
            )

    @action(detail=True, methods=['post'], url_path='approve')
    def approve(self, request, pk=None):
        """Approve a submitted report."""
        report = self.get_object()
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        service = InventoryReportService()
        try:
            updated = service.approve(
                str(report.id),
                user=request.user,
                opinion=serializer.validated_data.get('opinion', ''),
            )
            return success_response(
                data=InventoryReportSerializer(updated).data,
                message=_('Inventory report approved successfully.'),
            )
        except Exception as exc:
            return error_response(
                code='VALIDATION_ERROR',
                message=_('Failed to approve inventory report.'),
                details={'error': str(exc)},
            )

    @action(detail=True, methods=['post'], url_path='reject')
    def reject(self, request, pk=None):
        """Reject a submitted report."""
        report = self.get_object()
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        service = InventoryReportService()
        try:
            updated = service.reject(
                str(report.id),
                user=request.user,
                opinion=serializer.validated_data.get('opinion', ''),
            )
            return success_response(
                data=InventoryReportSerializer(updated).data,
                message=_('Inventory report rejected successfully.'),
            )
        except Exception as exc:
            return error_response(
                code='VALIDATION_ERROR',
                message=_('Failed to reject inventory report.'),
                details={'error': str(exc)},
            )

    @action(detail=True, methods=['get'], url_path='export')
    def export(self, request, pk=None):
        """Export the selected inventory report."""
        report = self.get_object()
        service = InventoryReportService()
        file_format = (
            request.query_params.get('fileFormat')
            or request.query_params.get('format')
            or 'pdf'
        )
        try:
            return service.export_report(
                str(report.id),
                user=request.user,
                file_format=file_format,
            )
        except Exception as exc:
            return error_response(
                code='VALIDATION_ERROR',
                message=_('Failed to export inventory report.'),
                details={'error': str(exc)},
            )
