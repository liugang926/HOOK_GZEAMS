"""
Filters for Asset models.
"""
import django_filters
from django.db.models import Q
from apps.common.filters.base import BaseModelFilter
from apps.assets.models import AssetCategory


class AssetCategoryFilter(BaseModelFilter):
    """Filter for AssetCategory list endpoint."""

    class Meta:
        model = AssetCategory
        fields = [
            'code', 'parent', 'is_custom', 'is_active',
            'depreciation_method', 'created_by', 'is_deleted'
        ]

    # Custom filters
    code = django_filters.CharFilter(lookup_expr='icontains')
    parent = django_filters.UUIDFilter(field_name='parent_id')
    is_custom = django_filters.BooleanFilter()
    is_active = django_filters.BooleanFilter()
    search = django_filters.CharFilter(method='filter_search')

    def filter_search(self, queryset, name, value):
        """Search by code or name using Q objects."""
        return queryset.filter(
            Q(code__icontains=value) | Q(name__icontains=value)
        )
