"""
Filters for integration sync task models.

Provides filter classes for IntegrationSyncTask model following BaseModelFilter pattern.
"""
import django_filters

from apps.common.filters.base import BaseModelFilter
from apps.integration.models import IntegrationSyncTask


class IntegrationSyncTaskFilter(BaseModelFilter):
    """Filter for IntegrationSyncTask model."""

    class Meta(BaseModelFilter.Meta):
        model = IntegrationSyncTask
        fields = BaseModelFilter.Meta.fields + [
            'config',
            'module_type',
            'direction',
            'business_type',
            'status',
        ]

    config = django_filters.UUIDFilter(field_name='config__id')
    module_type = django_filters.CharFilter(lookup_expr='iexact')
    direction = django_filters.CharFilter(lookup_expr='iexact')
    business_type = django_filters.CharFilter(lookup_expr='iexact')
    status = django_filters.CharFilter(lookup_expr='iexact')
    started_at_from = django_filters.DateTimeFilter(field_name='started_at', lookup_expr='gte')
    started_at_to = django_filters.DateTimeFilter(field_name='started_at', lookup_expr='lte')
    completed_at_from = django_filters.DateTimeFilter(field_name='completed_at', lookup_expr='gte')
    completed_at_to = django_filters.DateTimeFilter(field_name='completed_at', lookup_expr='lte')
