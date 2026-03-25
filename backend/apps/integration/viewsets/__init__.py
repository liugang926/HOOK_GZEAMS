from apps.integration.viewsets.config_viewsets import IntegrationConfigViewSet
from apps.integration.viewsets.sync_task_viewsets import IntegrationSyncTaskViewSet
from apps.integration.viewsets.log_viewsets import IntegrationLogViewSet
from apps.integration.viewsets.mapping_viewsets import DataMappingTemplateViewSet

__all__ = [
    'IntegrationConfigViewSet',
    'IntegrationSyncTaskViewSet',
    'IntegrationLogViewSet',
    'DataMappingTemplateViewSet',
]
