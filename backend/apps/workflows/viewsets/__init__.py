"""
ViewSets for workflow management.
"""
from apps.workflows.viewsets.workflow_definition_viewsets import (
    WorkflowDefinitionViewSet,
)
from apps.workflows.viewsets.workflow_template_viewsets import (
    WorkflowTemplateViewSet,
)
from apps.workflows.viewsets.workflow_operation_log_viewsets import (
    WorkflowOperationLogViewSet,
)
from apps.workflows.viewsets.workflow_execution_viewsets import (
    WorkflowInstanceViewSet,
    WorkflowTaskViewSet,
    WorkflowStatisticsViewSet,
)

__all__ = [
    'WorkflowDefinitionViewSet',
    'WorkflowTemplateViewSet',
    'WorkflowOperationLogViewSet',
    'WorkflowInstanceViewSet',
    'WorkflowTaskViewSet',
    'WorkflowStatisticsViewSet',
]
