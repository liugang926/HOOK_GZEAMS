import django_filters
from apps.common.filters.base import BaseModelFilter
from apps.depreciation.models import DepreciationConfig, DepreciationRecord, DepreciationRun


class DepreciationConfigFilter(BaseModelFilter):
    """Depreciation Configuration Filter"""

    category = django_filters.CharFilter(field_name='category__code')
    category_name = django_filters.CharFilter(lookup_expr='icontains')
    depreciation_method = django_filters.CharFilter()
    is_active = django_filters.BooleanFilter()

    class Meta(BaseModelFilter.Meta):
        model = DepreciationConfig
        fields = BaseModelFilter.Meta.fields + [
            'category', 'depreciation_method', 'is_active',
        ]


class DepreciationRecordFilter(BaseModelFilter):
    """Depreciation Record Filter"""

    asset = django_filters.CharFilter(field_name='asset__asset_code')
    asset_name = django_filters.CharFilter(lookup_expr='icontains')
    period = django_filters.CharFilter()
    status = django_filters.CharFilter()
    category = django_filters.CharFilter(field_name='asset__asset_category__code')

    # Period range filters
    period_from = django_filters.CharFilter(method='filter_period_from')
    period_to = django_filters.CharFilter(method='filter_period_to')

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
            'asset', 'period', 'status',
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
