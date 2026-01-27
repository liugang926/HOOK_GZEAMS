"""
ViewSets for WorkflowOperationLog model.

Provides read-only access to workflow operation logs.
"""
from rest_framework.decorators import action
from rest_framework.response import Response
from django.utils.translation import gettext_lazy as _

from apps.common.viewsets.base import BaseModelViewSet
from apps.workflows.models.workflow_operation_log import WorkflowOperationLog
from apps.workflows.serializers.workflow_operation_log_serializers import (
    WorkflowOperationLogSerializer,
    WorkflowOperationLogListSerializer,
)


class WorkflowOperationLogViewSet(BaseModelViewSet):
    """
    Read-only ViewSet for WorkflowOperationLog model.

    Provides filtering and search capabilities for audit logs.
    Does not allow creating, updating, or deleting logs directly
    (logs are created automatically by the system).
    """

    queryset = WorkflowOperationLog.objects.filter(is_deleted=False)
    serializer_class = WorkflowOperationLogSerializer
    filterset_fields = ['operation_type', 'target_type', 'result']
    search_fields = ['target_name', 'target_code', 'error_message']

    def get_serializer_class(self):
        """Return appropriate serializer based on action."""
        if self.action == 'list':
            return WorkflowOperationLogListSerializer
        return WorkflowOperationLogSerializer

    def get_queryset(self):
        """Filter queryset based on user permissions."""
        queryset = super().get_queryset()

        # Non-superusers can only see logs for their organization
        user = self.request.user
        if user and not user.is_superuser:
            queryset = queryset.filter(organization=user.organization)

        return queryset

    @action(detail=False, methods=['get'])
    def statistics(self, request):
        """
        Get operation log statistics.

        Returns counts grouped by operation type and result.
        """
        queryset = self.get_queryset()

        # Count by operation type
        operation_stats = {}
        for op_type, _ in WorkflowOperationLog.OPERATION_TYPE_CHOICES:
            count = queryset.filter(operation_type=op_type).count()
            operation_stats[op_type] = count

        # Count by result
        result_stats = {}
        for result_type, _ in WorkflowOperationLog.RESULT_CHOICES:
            count = queryset.filter(result=result_type).count()
            result_stats[result_type] = count

        # Count by target type
        target_stats = {}
        for target_type, _ in WorkflowOperationLog.TARGET_TYPE_CHOICES:
            count = queryset.filter(target_type=target_type).count()
            target_stats[target_type] = count

        return Response({
            'success': True,
            'data': {
                'total': queryset.count(),
                'by_operation_type': operation_stats,
                'by_result': result_stats,
                'by_target_type': target_stats,
            }
        })

    @action(detail=False, methods=['get'])
    def by_workflow(self, request):
        """
        Get logs for a specific workflow.

        Query params:
        - workflow_id: The workflow definition ID
        """
        workflow_id = request.query_params.get('workflow_id')

        if not workflow_id:
            return Response({
                'success': False,
                'error': {
                    'code': 'MISSING_PARAM',
                    'message': _('workflow_id parameter is required.')
                }
            })

        queryset = self.get_queryset().filter(workflow_definition_id=workflow_id)
        serializer = self.get_serializer(queryset, many=True)

        return Response({
            'success': True,
            'data': serializer.data
        })

    @action(detail=False, methods=['get'])
    def recent(self, request):
        """
        Get recent operation logs.

        Query params:
        - limit: Number of logs to return (default: 50)
        """
        limit = int(request.query_params.get('limit', 50))
        limit = min(limit, 100)  # Max 100

        queryset = self.get_queryset().order_by('-created_at')[:limit]
        serializer = self.get_serializer(queryset, many=True)

        return Response({
            'success': True,
            'data': serializer.data
        })
