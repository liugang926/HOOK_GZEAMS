import django_filters
from django.db.models import Q

from apps.common.filters.base import BaseModelFilter
from apps.depreciation.models import DepreciationConfig, DepreciationRecord, DepreciationRun


class DepreciationConfigFilter(BaseModelFilter):
    """Depreciation Configuration Filter"""

    category = django_filters.CharFilter(field_name='category__code', lookup_expr='iexact')
    category_id = django_filters.UUIDFilter(field_name='category_id')
    category_name = django_filters.CharFilter(field_name='category__name', lookup_expr='icontains')
    depreciation_method = django_filters.CharFilter(lookup_expr='iexact')
    is_active = django_filters.BooleanFilter()

    class Meta(BaseModelFilter.Meta):
        model = DepreciationConfig
        fields = BaseModelFilter.Meta.fields + [
            'category', 'category_id', 'depreciation_method', 'is_active',
        ]


class DepreciationRecordFilter(BaseModelFilter):
    """Depreciation Record Filter"""

    asset = django_filters.CharFilter(method='filter_asset_keyword')
    asset_id = django_filters.UUIDFilter(field_name='asset_id')
    asset_name = django_filters.CharFilter(field_name='asset__asset_name', lookup_expr='icontains')
    period = django_filters.CharFilter(lookup_expr='iexact')
    status = django_filters.CharFilter(lookup_expr='iexact')
    category = django_filters.CharFilter(field_name='asset__asset_category__code', lookup_expr='iexact')
    category_id = django_filters.UUIDFilter(field_name='asset__asset_category_id')
    depreciation_method = django_filters.CharFilter(
        field_name='asset__asset_category__depreciation_method',
        lookup_expr='iexact',
    )

    # Period range filters
    period_from = django_filters.CharFilter(method='filter_period_from')
    period_to = django_filters.CharFilter(method='filter_period_to')

    def filter_asset_keyword(self, queryset, name, value):
        """Filter by asset code or asset name for finance list keyword search."""
        if value:
            return queryset.filter(
                Q(asset__asset_code__icontains=value)
                | Q(asset__asset_name__icontains=value)
            )
        return queryset

    def filter_period_from(self, queryset, name, value):
        """Filter records from this period onwards."""
        if value:
            return queryset.filter(period__gte=value)
        return queryset

    def filter_period_to(self, queryset, name, value):
        """Filter records up to this period."""
        if value:
            return queryset.filter(period__lte=value)
        return queryset

    class Meta(BaseModelFilter.Meta):
        model = DepreciationRecord
        fields = BaseModelFilter.Meta.fields + [
            'asset', 'asset_id', 'asset_name', 'period', 'status',
            'category', 'category_id', 'depreciation_method',
        ]


class DepreciationRunFilter(BaseModelFilter):
    """Depreciation Run Filter"""

    period = django_filters.CharFilter()
    status = django_filters.CharFilter()

    # Period range filters
    period_from = django_filters.CharFilter(method='filter_period_from')
    period_to = django_filters.CharFilter(method='filter_period_to')

    # Run date range filters
    run_date_from = django_filters.DateFilter(field_name='run_date', lookup_expr='gte')
    run_date_to = django_filters.DateFilter(field_name='run_date', lookup_expr='lte')

    def filter_period_from(self, queryset, name, value):
        """Filter runs from this period onwards."""
        if value:
            return queryset.filter(period__gte=value)
        return queryset

    def filter_period_to(self, queryset, name, value):
        """Filter runs up to this period."""
        if value:
            return queryset.filter(period__lte=value)
        return queryset

    class Meta(BaseModelFilter.Meta):
        model = DepreciationRun
        fields = BaseModelFilter.Meta.fields + [
            'period', 'status', 'run_date',
        ]


__all__ = [
    'DepreciationConfigFilter',
    'DepreciationRecordFilter',
    'DepreciationRunFilter',
]
