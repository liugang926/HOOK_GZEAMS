"""
Filters for integration log models.

Provides filter classes for IntegrationLog model following BaseModelFilter pattern.
"""
import django_filters

from apps.common.filters.base import BaseModelFilter
from apps.integration.models import IntegrationLog


class IntegrationLogFilter(BaseModelFilter):
    """Filter for IntegrationLog model."""

    class Meta(BaseModelFilter.Meta):
        model = IntegrationLog
        fields = BaseModelFilter.Meta.fields + [
            'sync_task',
            'system_type',
            'action',
            'success',
            'status_code',
        ]

    sync_task = django_filters.UUIDFilter(field_name='sync_task__id')
    system_type = django_filters.CharFilter(lookup_expr='iexact')
    action = django_filters.CharFilter(lookup_expr='iexact')
    success = django_filters.BooleanFilter()
    status_code = django_filters.NumberFilter()
    status_code_from = django_filters.NumberFilter(field_name='status_code', lookup_expr='gte')
    status_code_to = django_filters.NumberFilter(field_name='status_code', lookup_expr='lte')
    duration_ms_from = django_filters.NumberFilter(field_name='duration_ms', lookup_expr='gte')
    duration_ms_to = django_filters.NumberFilter(field_name='duration_ms', lookup_expr='lte')
    business_type = django_filters.CharFilter(lookup_expr='iexact')
