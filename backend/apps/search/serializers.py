"""Serializers for smart search APIs."""
from django.contrib.auth import get_user_model
from rest_framework import serializers

from apps.common.serializers.base import BaseModelSerializer, UserSerializer
from apps.search.models import SavedSearch, SearchHistory, SearchSuggestion, SearchType

User = get_user_model()

ALLOWED_FILTER_FIELDS = {
    'category',
    'status',
    'location',
    'brand',
    'tags',
    'purchase_price_min',
    'purchase_price_max',
    'purchase_date_from',
    'purchase_date_to',
}


class SearchHistorySerializer(BaseModelSerializer):
    """Serializer for search history records."""

    user = serializers.UUIDField(source='user_id', read_only=True)
    user_detail = UserSerializer(source='user', read_only=True)

    class Meta(BaseModelSerializer.Meta):
        model = SearchHistory
        fields = BaseModelSerializer.Meta.fields + [
            'user',
            'user_detail',
            'search_type',
            'keyword',
            'filters',
            'result_count',
            'search_count',
            'last_searched_at',
        ]
        read_only_fields = BaseModelSerializer.Meta.read_only_fields + [
            'user',
            'user_detail',
            'search_count',
            'last_searched_at',
        ]


class SavedSearchSerializer(BaseModelSerializer):
    """Serializer for saved search presets."""

    user = serializers.UUIDField(source='user_id', read_only=True)
    user_detail = UserSerializer(source='user', read_only=True)
    search_type_display = serializers.CharField(
        source='get_search_type_display',
        read_only=True,
    )

    class Meta(BaseModelSerializer.Meta):
        model = SavedSearch
        fields = BaseModelSerializer.Meta.fields + [
            'user',
            'user_detail',
            'name',
            'search_type',
            'search_type_display',
            'keyword',
            'filters',
            'is_shared',
            'use_count',
        ]
        read_only_fields = BaseModelSerializer.Meta.read_only_fields + [
            'user',
            'user_detail',
            'search_type_display',
            'use_count',
        ]

    def validate(self, attrs):
        """Ensure saved search names are unique per user."""
        request = self.context.get('request')
        if request is None or request.user.is_anonymous:
            return attrs

        name = attrs.get('name', getattr(self.instance, 'name', None))
        if not name:
            return attrs

        queryset = SavedSearch.objects.filter(
            organization_id=getattr(request, 'organization_id', None) or request.user.organization_id,
            user=request.user,
            name=name,
        )
        if self.instance:
            queryset = queryset.exclude(pk=self.instance.pk)
        if queryset.exists():
            raise serializers.ValidationError({'name': 'A saved search with this name already exists.'})

        return attrs


class SearchSuggestionSerializer(BaseModelSerializer):
    """Serializer for suggestion cache entries."""

    class Meta(BaseModelSerializer.Meta):
        model = SearchSuggestion
        fields = BaseModelSerializer.Meta.fields + [
            'search_type',
            'query',
            'frequency',
            'last_used',
        ]
        read_only_fields = BaseModelSerializer.Meta.read_only_fields + [
            'frequency',
            'last_used',
        ]


class SearchRequestSerializer(serializers.Serializer):
    """Serializer for asset search requests."""

    search_type = serializers.ChoiceField(
        choices=SearchType.choices,
        default=SearchType.ASSET,
        required=False,
    )
    keyword = serializers.CharField(max_length=200, required=False, allow_blank=True)
    filters = serializers.JSONField(default=dict)
    sort_by = serializers.ChoiceField(
        choices=['relevance', 'date', 'price', 'code'],
        default='relevance',
    )
    sort_order = serializers.ChoiceField(
        choices=['asc', 'desc'],
        default='desc',
    )
    page = serializers.IntegerField(default=1, min_value=1)
    page_size = serializers.IntegerField(default=20, min_value=1, max_value=100)

    def validate_filters(self, value):
        """Restrict search filters to the supported allowlist."""
        if not isinstance(value, dict):
            raise serializers.ValidationError('Filters must be an object.')
        unsupported = sorted(set(value.keys()) - ALLOWED_FILTER_FIELDS)
        if unsupported:
            raise serializers.ValidationError(
                f'Unsupported filter fields: {", ".join(unsupported)}'
            )
        return value


class SuggestionQuerySerializer(serializers.Serializer):
    """Serializer for suggestion queries."""

    keyword = serializers.CharField(max_length=200, allow_blank=False)
    type = serializers.ChoiceField(
        choices=SearchType.choices,
        default=SearchType.ASSET,
        required=False,
    )
    limit = serializers.IntegerField(default=10, min_value=1, max_value=20, required=False)


class SearchResultSerializer(serializers.Serializer):
    """Serializer describing search result payload shape."""

    id = serializers.CharField()
    asset_code = serializers.CharField()
    asset_name = serializers.CharField()
    asset_category = serializers.CharField(allow_null=True)
    asset_category_name = serializers.CharField(allow_blank=True, allow_null=True)
    asset_status = serializers.CharField()
    status_label = serializers.CharField()
    specification = serializers.CharField(allow_blank=True)
    brand = serializers.CharField(allow_blank=True)
    model = serializers.CharField(allow_blank=True)
    serial_number = serializers.CharField(allow_blank=True)
    purchase_price = serializers.DecimalField(max_digits=14, decimal_places=2, allow_null=True)
    current_value = serializers.DecimalField(max_digits=14, decimal_places=2, allow_null=True)
    purchase_date = serializers.DateField(allow_null=True)
    location = serializers.CharField(allow_blank=True, allow_null=True)
    location_path = serializers.CharField(allow_blank=True, allow_null=True)
    department = serializers.CharField(allow_blank=True, allow_null=True)
    department_name = serializers.CharField(allow_blank=True, allow_null=True)
    custodian = serializers.CharField(allow_blank=True, allow_null=True)
    custodian_name = serializers.CharField(allow_blank=True, allow_null=True)
    supplier = serializers.CharField(allow_blank=True, allow_null=True)
    supplier_name = serializers.CharField(allow_blank=True, allow_null=True)
    tags = serializers.ListField(child=serializers.CharField(), default=list)
    tag_names = serializers.ListField(child=serializers.CharField(), default=list)
    highlight = serializers.JSONField(default=dict)
    score = serializers.FloatField(default=0.0)
