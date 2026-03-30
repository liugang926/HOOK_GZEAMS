"""
Filters for asset tag groups, tags, and asset-tag relations.
"""
import django_filters
from django.db.models import Q

from apps.assets.models import AssetTag, AssetTagRelation, TagGroup
from apps.common.filters.base import BaseModelFilter


class TagGroupFilter(BaseModelFilter):
    """Filter set for asset tag group queries."""

    name = django_filters.CharFilter(lookup_expr='icontains')
    code = django_filters.CharFilter(lookup_expr='icontains')
    is_active = django_filters.BooleanFilter()
    is_system = django_filters.BooleanFilter()
    search = django_filters.CharFilter(method='filter_search')

    class Meta(BaseModelFilter.Meta):
        model = TagGroup
        fields = BaseModelFilter.Meta.fields + [
            'name',
            'code',
            'is_active',
            'is_system',
        ]

    def filter_search(self, queryset, name, value):
        """Search tag groups by name, code, or description."""
        return queryset.filter(
            Q(name__icontains=value) |
            Q(code__icontains=value) |
            Q(description__icontains=value)
        )


class AssetTagFilter(BaseModelFilter):
    """Filter set for asset tag queries."""

    name = django_filters.CharFilter(lookup_expr='icontains')
    code = django_filters.CharFilter(lookup_expr='icontains')
    tag_group = django_filters.UUIDFilter(field_name='tag_group_id')
    is_active = django_filters.BooleanFilter()
    search = django_filters.CharFilter(method='filter_search')

    class Meta(BaseModelFilter.Meta):
        model = AssetTag
        fields = BaseModelFilter.Meta.fields + [
            'name',
            'code',
            'tag_group',
            'is_active',
        ]

    def filter_search(self, queryset, name, value):
        """Search tags by name, code, description, or group name."""
        return queryset.filter(
            Q(name__icontains=value) |
            Q(code__icontains=value) |
            Q(description__icontains=value) |
            Q(tag_group__name__icontains=value)
        )


class AssetTagRelationFilter(BaseModelFilter):
    """Filter set for asset-tag relation queries."""

    asset = django_filters.UUIDFilter(field_name='asset_id')
    tag = django_filters.UUIDFilter(field_name='tag_id')
    tagged_by = django_filters.UUIDFilter(field_name='tagged_by_id')

    class Meta(BaseModelFilter.Meta):
        model = AssetTagRelation
        fields = BaseModelFilter.Meta.fields + [
            'asset',
            'tag',
            'tagged_by',
        ]
