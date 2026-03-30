"""
Tag filters for system tag management.
"""
from django_filters import rest_framework as filters

from apps.common.filters.base import BaseModelFilter
from apps.system.models import Tag


class TagFilter(BaseModelFilter):
    """Filter set for tag list and admin management views."""

    name = filters.CharFilter(
        lookup_expr='icontains',
        label='Tag Name',
    )
    biz_type = filters.CharFilter(
        lookup_expr='exact',
        label='Business Object Code',
    )
    bizType = filters.CharFilter(
        field_name='biz_type',
        lookup_expr='exact',
        label='Business Object Code',
    )
    color = filters.CharFilter(
        lookup_expr='icontains',
        label='Tag Color',
    )
    has_assignments = filters.BooleanFilter(
        method='filter_has_assignments',
        label='Has Assignments',
    )
    hasAssignments = filters.BooleanFilter(
        method='filter_has_assignments',
        label='Has Assignments',
    )

    class Meta(BaseModelFilter.Meta):
        model = Tag
        fields = [
            'name',
            'biz_type',
            'color',
            'has_assignments',
        ]

    def filter_has_assignments(self, queryset, name, value):
        """Filter tags by active usage state."""
        if value is None:
            return queryset
        if value:
            return queryset.filter(usage_count__gt=0)
        return queryset.filter(usage_count=0)
