"""
Filters for WorkflowOperationLog model.

Provides filtering and searching capabilities for workflow operation logs.
"""
import django_filters
from django.utils.translation import gettext_lazy as _

from apps.common.filters.base import BaseModelFilter
from apps.workflows.models.workflow_operation_log import WorkflowOperationLog


class WorkflowOperationLogFilter(BaseModelFilter):
    """
    FilterSet for WorkflowOperationLog model.

    Extends BaseModelFilter to provide common filtering plus log-specific filters.
    """

    # Operation type filter
    operation_type = django_filters.ChoiceFilter(
        choices=WorkflowOperationLog.OPERATION_TYPE_CHOICES,
        field_name='operation_type',
        label=_('Operation Type')
    )

    # Target type filter
    target_type = django_filters.ChoiceFilter(
        choices=WorkflowOperationLog.TARGET_TYPE_CHOICES,
        field_name='target_type',
        label=_('Target Type')
    )

    # Result filter
    result = django_filters.ChoiceFilter(
        choices=WorkflowOperationLog.RESULT_CHOICES,
        field_name='result',
        label=_('Result')
    )

    # Actor filter
    actor = django_filters.UUIDFilter(
        field_name='actor_id',
        label=_('Actor (User ID)')
    )

    # Workflow definition filter
    workflow_definition = django_filters.UUIDFilter(
        field_name='workflow_definition_id',
        label=_('Workflow Definition ID')
    )

    # Workflow template filter
    workflow_template = django_filters.UUIDFilter(
        field_name='workflow_template_id',
        label=_('Workflow Template ID')
    )

    # Target code filter
    target_code = django_filters.CharFilter(
        field_name='target_code',
        lookup_expr='iexact',
        label=_('Target Code')
    )

    target_code_contains = django_filters.CharFilter(
        field_name='target_code',
        lookup_expr='icontains',
        label=_('Target Code Contains')
    )

    # Target name filter
    target_name = django_filters.CharFilter(
        field_name='target_name',
        lookup_expr='icontains',
        label=_('Target Name Contains')
    )

    # IP address filter
    ip_address = django_filters.CharFilter(
        field_name='ip_address',
        lookup_expr='iexact',
        label=_('IP Address')
    )

    # Failed operations filter (result = failure)
    has_error = django_filters.BooleanFilter(
        method='filter_has_error',
        label=_('Has Error')
    )

    class Meta(BaseModelFilter.Meta):
        model = WorkflowOperationLog
        fields = BaseModelFilter.Meta.fields + [
            'operation_type',
            'target_type',
            'result',
            'actor',
            'workflow_definition',
            'workflow_template',
            'target_code',
            'ip_address',
        ]

    def filter_has_error(self, queryset, name, value):
        """Filter logs that have errors."""
        if value:
            return queryset.filter(result='failure', error_message__isnull=False)
        return queryset.exclude(result='failure')
