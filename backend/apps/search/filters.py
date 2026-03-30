"""FilterSets for smart search models."""
import django_filters

from apps.common.filters.base import BaseModelFilter
from apps.search.models import SavedSearch, SearchHistory


class SearchHistoryFilter(BaseModelFilter):
    """FilterSet for search history records."""

    search_type = django_filters.CharFilter(lookup_expr='iexact')
    keyword = django_filters.CharFilter(lookup_expr='icontains')

    class Meta(BaseModelFilter.Meta):
        model = SearchHistory
        fields = BaseModelFilter.Meta.fields + ['search_type', 'keyword']


class SavedSearchFilter(BaseModelFilter):
    """FilterSet for saved searches."""

    search_type = django_filters.CharFilter(lookup_expr='iexact')
    name = django_filters.CharFilter(lookup_expr='icontains')
    is_shared = django_filters.BooleanFilter()

    class Meta(BaseModelFilter.Meta):
        model = SavedSearch
        fields = BaseModelFilter.Meta.fields + ['search_type', 'name', 'is_shared']
