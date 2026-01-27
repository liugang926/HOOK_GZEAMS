"""
Serializers for workflow models.
"""
from apps.workflows.serializers.workflow_definition_serializers import (
    WorkflowDefinitionSerializer,
    WorkflowDefinitionDetailSerializer,
    WorkflowDefinitionListSerializer,
)
from apps.workflows.serializers.workflow_template_serializers import (
    WorkflowTemplateSerializer,
    WorkflowTemplateDetailSerializer,
)
from apps.workflows.serializers.workflow_operation_log_serializers import (
    WorkflowOperationLogSerializer,
)
from apps.workflows.serializers.workflow_instance_serializers import (
    WorkflowInstanceListSerializer,
    WorkflowInstanceDetailSerializer,
    WorkflowInstanceCreateSerializer,
    WorkflowInstanceUpdateSerializer,
    WorkflowInstanceStartSerializer,
    WorkflowTaskListSerializer,
    WorkflowTaskDetailSerializer,
    WorkflowTaskActionSerializer,
    WorkflowTaskDelegateSerializer,
    WorkflowTaskReassignSerializer,
    WorkflowApprovalSerializer,
    MyTasksSerializer,
    TaskDetailWithInstanceSerializer,
    WorkflowStatisticsSerializer,
)

__all__ = [
    'WorkflowDefinitionSerializer',
    'WorkflowDefinitionDetailSerializer',
    'WorkflowDefinitionListSerializer',
    'WorkflowTemplateSerializer',
    'WorkflowTemplateDetailSerializer',
    'WorkflowOperationLogSerializer',
    'WorkflowInstanceListSerializer',
    'WorkflowInstanceDetailSerializer',
    'WorkflowInstanceCreateSerializer',
    'WorkflowInstanceUpdateSerializer',
    'WorkflowInstanceStartSerializer',
    'WorkflowTaskListSerializer',
    'WorkflowTaskDetailSerializer',
    'WorkflowTaskActionSerializer',
    'WorkflowTaskDelegateSerializer',
    'WorkflowTaskReassignSerializer',
    'WorkflowApprovalSerializer',
    'MyTasksSerializer',
    'TaskDetailWithInstanceSerializer',
    'WorkflowStatisticsSerializer',
]
