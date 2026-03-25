"""
Filters for integration configuration models.

Provides filter classes for IntegrationConfig model following BaseModelFilter pattern.
"""
import django_filters

from apps.common.filters.base import BaseModelFilter
from apps.integration.models import IntegrationConfig


class IntegrationConfigFilter(BaseModelFilter):
    """Filter for IntegrationConfig model."""

    class Meta(BaseModelFilter.Meta):
        model = IntegrationConfig
        fields = BaseModelFilter.Meta.fields + [
            'system_type',
            'is_enabled',
            'health_status',
            'last_sync_status',
        ]

    system_type = django_filters.CharFilter(lookup_expr='iexact')
    is_enabled = django_filters.BooleanFilter()
    health_status = django_filters.CharFilter(lookup_expr='iexact')
    last_sync_status = django_filters.CharFilter(lookup_expr='iexact')
    system_name = django_filters.CharFilter(lookup_expr='icontains')
