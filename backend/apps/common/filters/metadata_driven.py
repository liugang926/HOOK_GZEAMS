"""
Metadata-driven filter for dynamic field filtering.

Generates filter conditions based on FieldDefinition configuration.
"""
import django_filters
from typing import Optional, Dict, Any, List
from django.db.models import QuerySet, Q


class MetadataDrivenFilter(django_filters.FilterSet):
    """
    Dynamic filter that builds filter fields from FieldDefinitions.

    Supports filtering on custom_fields JSON data.

    Usage:
        # Get filter class for a business object
        AssetFilter = MetadataDrivenFilter.for_business_object('Asset')

        # Use in ViewSet
        class AssetViewSet(viewsets.ModelViewSet):
            filterset_class = AssetFilter
    """

    # Business object reference
    business_object_code: Optional[str] = None
    _business_object = None
    _field_definitions = None

    # Type to filter mapping
    FILTER_TYPE_MAPPING = {
        'text': django_filters.CharFilter,
        'textarea': django_filters.CharFilter,
        'number': django_filters.NumberFilter,
        'integer': django_filters.NumberFilter,
        'float': django_filters.NumberFilter,
        'boolean': django_filters.BooleanFilter,
        'date': django_filters.DateFilter,
        'datetime': django_filters.DateTimeFilter,
        'choice': django_filters.ChoiceFilter,
        'multi_choice': django_filters.MultipleChoiceFilter,
        'reference': django_filters.UUIDFilter,
        'user': django_filters.UUIDFilter,
        'department': django_filters.UUIDFilter,
    }

    def __init__(self, *args, **kwargs):
        # Extract business object code
        self._init_business_object_code = kwargs.pop('business_object_code', None)
        super().__init__(*args, **kwargs)

        # Load metadata and build dynamic filters
        if self._init_business_object_code or self.business_object_code:
            self._load_metadata()
            self._build_dynamic_filters()

    def _load_metadata(self):
        """Load business object metadata."""
        code = self._init_business_object_code or self.business_object_code
        if not code:
            return

        try:
            from apps.system.models import BusinessObject
            self._business_object = BusinessObject.objects.get(
                code=code,
                is_active=True
            )
            self._field_definitions = self._business_object.field_definitions.filter(
                is_active=True,
                show_in_filter=True
            ).order_by('sort_order')
        except Exception:
            pass

    def _build_dynamic_filters(self):
        """Build filter fields from field definitions."""
        if not self._field_definitions:
            return

        for field_def in self._field_definitions:
            filter_class = self.FILTER_TYPE_MAPPING.get(
                field_def.field_type,
                django_filters.CharFilter
            )

            filter_kwargs = {
                'label': field_def.name,
                'method': self._make_custom_field_filter_method(field_def.code),
            }

            # Add choices for choice fields
            if field_def.field_type in ['choice', 'multi_choice'] and field_def.options:
                if isinstance(field_def.options, dict):
                    filter_kwargs['choices'] = [(k, v) for k, v in field_def.options.items()]
                elif isinstance(field_def.options, list):
                    filter_kwargs['choices'] = [(o, o) for o in field_def.options]

            # Create filter
            self.filters[field_def.code] = filter_class(**filter_kwargs)

    def _make_custom_field_filter_method(self, field_code: str):
        """Create a filter method for custom_fields JSON field."""
        def filter_method(queryset, name, value):
            if value is None or value == '':
                return queryset
            return queryset.filter(
                **{f'custom_fields__{field_code}': value}
            )
        return filter_method

    @classmethod
    def for_business_object(cls, business_object_code: str) -> type:
        """
        Factory method to create filter class for a business object.

        Args:
            business_object_code: BusinessObject code

        Returns:
            FilterSet class
        """
        class GeneratedFilter(cls):
            pass

        GeneratedFilter.business_object_code = business_object_code
        GeneratedFilter.__name__ = f'{business_object_code.title()}Filter'

        return GeneratedFilter


class DynamicDataFilter(MetadataDrivenFilter):
    """
    Filter specifically for DynamicData model.

    Adds base model filters in addition to dynamic field filters.
    """

    # Base filters
    created_at_from = django_filters.DateTimeFilter(
        field_name='created_at',
        lookup_expr='gte',
        label='Created From'
    )
    created_at_to = django_filters.DateTimeFilter(
        field_name='created_at',
        lookup_expr='lte',
        label='Created To'
    )
    created_by = django_filters.UUIDFilter(
        field_name='created_by_id',
        label='Created By'
    )

    class Meta:
        from apps.system.models import DynamicData
        model = DynamicData
        fields = ['created_at_from', 'created_at_to', 'created_by']


def build_dynamic_filter_query(
    field_definitions,
    filter_params: Dict[str, Any]
) -> Q:
    """
    Build a Q object for filtering based on field definitions.

    Args:
        field_definitions: QuerySet of FieldDefinition
        filter_params: Dict of filter parameters from request

    Returns:
        Q object for filtering
    """
    q = Q()

    for field_def in field_definitions:
        code = field_def.code
        value = filter_params.get(code)

        if value is None or value == '':
            continue

        field_type = field_def.field_type

        # Build lookup based on field type
        if field_type in ['text', 'textarea']:
            # Case-insensitive contains for text
            q &= Q(**{f'custom_fields__{code}__icontains': value})
        elif field_type in ['number', 'integer', 'float']:
            # Range filters
            value_from = filter_params.get(f'{code}_from')
            value_to = filter_params.get(f'{code}_to')
            if value_from:
                q &= Q(**{f'custom_fields__{code}__gte': value_from})
            if value_to:
                q &= Q(**{f'custom_fields__{code}__lte': value_to})
            if value and not value_from and not value_to:
                q &= Q(**{f'custom_fields__{code}': value})
        elif field_type in ['date', 'datetime']:
            # Date range
            value_from = filter_params.get(f'{code}_from')
            value_to = filter_params.get(f'{code}_to')
            if value_from:
                q &= Q(**{f'custom_fields__{code}__gte': value_from})
            if value_to:
                q &= Q(**{f'custom_fields__{code}__lte': value_to})
        elif field_type in ['choice', 'reference', 'user', 'department']:
            # Exact match
            q &= Q(**{f'custom_fields__{code}': value})
        elif field_type == 'multi_choice':
            # Contains for multi-choice
            if isinstance(value, list):
                for v in value:
                    q &= Q(**{f'custom_fields__{code}__contains': v})
            else:
                q &= Q(**{f'custom_fields__{code}__contains': value})
        elif field_type == 'boolean':
            # Boolean conversion
            bool_value = str(value).lower() in ('true', '1', 'yes')
            q &= Q(**{f'custom_fields__{code}': bool_value})

    return q
