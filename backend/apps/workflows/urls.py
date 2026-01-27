"""
URL configuration for workflows app.

Registers all workflow-related API routes.
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter

from apps.workflows.viewsets.workflow_definition_viewsets import WorkflowDefinitionViewSet
from apps.workflows.viewsets.workflow_template_viewsets import WorkflowTemplateViewSet
from apps.workflows.viewsets.workflow_operation_log_viewsets import WorkflowOperationLogViewSet
from apps.workflows.viewsets.workflow_execution_viewsets import (
    WorkflowInstanceViewSet,
    WorkflowTaskViewSet,
    WorkflowStatisticsViewSet,
)


# Create router for workflow ViewSets
router = DefaultRouter()
router.register(r'definitions', WorkflowDefinitionViewSet, basename='workflow-definition')
router.register(r'templates', WorkflowTemplateViewSet, basename='workflow-template')
router.register(r'logs', WorkflowOperationLogViewSet, basename='workflow-operation-log')
router.register(r'instances', WorkflowInstanceViewSet, basename='workflow-instance')
router.register(r'tasks', WorkflowTaskViewSet, basename='workflow-task')
router.register(r'statistics', WorkflowStatisticsViewSet, basename='workflow-statistics')

app_name = 'workflows'

urlpatterns = [
    # Include all router-generated URLs
    path('', include(router.urls)),
]

# Available routes:
#
# WorkflowDefinition:
# - GET    /api/workflows/definitions/                    - List workflows
# - POST   /api/workflows/definitions/                    - Create workflow
# - GET    /api/workflows/definitions/{id}/               - Retrieve workflow
# - PUT    /api/workflows/definitions/{id}/               - Update workflow
# - PATCH  /api/workflows/definitions/{id}/               - Partial update
# - DELETE /api/workflows/definitions/{id}/               - Delete workflow
# - POST   /api/workflows/definitions/batch-delete/       - Batch delete
# - POST   /api/workflows/definitions/batch-restore/      - Batch restore
# - POST   /api/workflows/definitions/batch-update/       - Batch update
# - GET    /api/workflows/definitions/deleted/            - List deleted
# - POST   /api/workflows/definitions/{id}/restore/       - Restore deleted
# - GET    /api/workflows/definitions/by-business-object/ - Filter by business object
# - POST   /api/workflows/definitions/{id}/validate/      - Validate workflow
# - POST   /api/workflows/definitions/{id}/publish/       - Publish workflow
# - POST   /api/workflows/definitions/{id}/unpublish/     - Unpublish workflow
# - POST   /api/workflows/definitions/{id}/duplicate/     - Duplicate workflow
# - GET    /api/workflows/definitions/{id}/versions/      - Get version history
# - GET    /api/workflows/definitions/categories/         - Get categories
# - GET    /api/workflows/definitions/business_objects/   - Get business objects
#
# WorkflowTemplate:
# - GET    /api/workflows/templates/                      - List templates
# - POST   /api/workflows/templates/                      - Create template
# - GET    /api/workflows/templates/{id}/                 - Retrieve template
# - PUT    /api/workflows/templates/{id}/                 - Update template
# - PATCH  /api/workflows/templates/{id}/                 - Partial update
# - DELETE /api/workflows/templates/{id}/                 - Delete template
# - POST   /api/workflows/templates/batch-delete/         - Batch delete
# - POST   /api/workflows/templates/batch-restore/        - Batch restore
# - POST   /api/workflows/templates/batch-update/         - Batch update
# - GET    /api/workflows/templates/deleted/              - List deleted
# - POST   /api/workflows/templates/{id}/restore/         - Restore deleted
# - POST   /api/workflows/templates/{id}/instantiate/     - Create workflow from template
# - GET    /api/workflows/templates/featured/             - Get featured templates
# - GET    /api/workflows/templates/by-business-object/   - Filter by business object
# - GET    /api/workflows/templates/categories/           - Get categories
#
# WorkflowOperationLog:
# - GET    /api/workflows/logs/                           - List logs
# - GET    /api/workflows/logs/{id}/                      - Retrieve log entry
# - GET    /api/workflows/logs/statistics/                - Get operation statistics
# - GET    /api/workflows/logs/by-workflow/               - Get logs for workflow
# - GET    /api/workflows/logs/recent/                    - Get recent logs
#
# WorkflowInstance (Execution):
# - GET    /api/workflows/instances/                     - List instances
# - POST   /api/workflows/instances/start/                - Start new workflow
# - GET    /api/workflows/instances/{id}/                - Retrieve instance
# - PATCH  /api/workflows/instances/{id}/                - Partial update
# - POST   /api/workflows/instances/{id}/withdraw/       - Withdraw instance
# - POST   /api/workflows/instances/{id}/terminate/      - Terminate instance
# - GET    /api/workflows/instances/my_instances/        - Get my instances
# - GET    /api/workflows/instances/{id}/timeline/        - Get instance timeline
#
# WorkflowTask:
# - GET    /api/workflows/tasks/                         - List my tasks
# - GET    /api/workflows/tasks/{id}/                    - Retrieve task
# - GET    /api/workflows/tasks/my_tasks/                 - Get tasks grouped by status
# - POST   /api/workflows/tasks/{id}/approve/            - Approve task
# - POST   /api/workflows/tasks/{id}/reject/             - Reject task
# - POST   /api/workflows/tasks/{id}/return_task/        - Return task
# - POST   /api/workflows/tasks/{id}/delegate/           - Delegate task
# - POST   /api/workflows/tasks/{id}/reassign/           - Reassign task (admin)
#
# WorkflowStatistics:
# - GET    /api/workflows/statistics/                    - Get workflow statistics
