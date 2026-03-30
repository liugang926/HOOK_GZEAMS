"""
Filters for Asset and related models.

Provides:
- AssetFilter: Filter for asset list/search
- SupplierFilter: Filter for supplier list
- LocationFilter: Filter for location list
- AssetStatusLogFilter: Filter for status log list
"""
import django_filters
import uuid
from django.contrib.contenttypes.models import ContentType
from django.db.models import Count, Q
from django.db.models import CharField
from django.db.models.functions import Cast
from apps.common.filters.base import BaseModelFilter
from apps.assets.models import Asset, AssetStatusLog, AssetTag, Location, Supplier
from apps.system.models import Tag, TagAssignment


class AssetFilter(BaseModelFilter):
    """
    Filter for Asset list endpoint.

    Provides filters for:
    - Text search (code, name, specification, brand, model, serial_number)
    - Category, department, location filters
    - Status and date range filters
    - Financial range filters (purchase price)
    - Custodian and user filters
    """

    class Meta:
        model = Asset
        fields = [
            'asset_code', 'asset_name', 'asset_category', 'asset_status',
            'department', 'location', 'custodian', 'user', 'supplier',
            'purchase_date', 'created_by', 'is_deleted',
            'source_receipt', 'source_purchase_request'
        ]

    # Text search filters
    asset_code = django_filters.CharFilter(lookup_expr='icontains')
    asset_name = django_filters.CharFilter(lookup_expr='icontains')
    specification = django_filters.CharFilter(lookup_expr='icontains')
    brand = django_filters.CharFilter(lookup_expr='icontains')
    model = django_filters.CharFilter(lookup_expr='icontains')
    serial_number = django_filters.CharFilter(lookup_expr='icontains')

    # Related object filters
    asset_category = django_filters.CharFilter(method='filter_asset_category')
    department = django_filters.CharFilter(method='filter_department')
    location = django_filters.CharFilter(method='filter_location')
    custodian = django_filters.CharFilter(method='filter_custodian')
    user = django_filters.CharFilter(method='filter_user')
    supplier = django_filters.CharFilter(method='filter_supplier')
    source_receipt = django_filters.UUIDFilter(field_name='source_receipt_id')
    source_purchase_request = django_filters.UUIDFilter(field_name='source_purchase_request_id')

    # Status filter - supports exact code match and fuzzy text search.
    asset_status = django_filters.CharFilter(method='filter_asset_status')

    # Date range filters for purchase_date
    purchase_date_from = django_filters.DateFilter(
        field_name='purchase_date',
        lookup_expr='gte'
    )
    purchase_date_to = django_filters.DateFilter(
        field_name='purchase_date',
        lookup_expr='lte'
    )

    # Financial range filters
    purchase_price_from = django_filters.NumberFilter(
        field_name='purchase_price',
        lookup_expr='gte'
    )
    purchase_price = django_filters.CharFilter(method='filter_purchase_price')
    purchase_price_to = django_filters.NumberFilter(
        field_name='purchase_price',
        lookup_expr='lte'
    )
    current_value = django_filters.CharFilter(method='filter_current_value')

    # Combined search filter
    search = django_filters.CharFilter(method='filter_search')
    tag_ids = django_filters.CharFilter(method='filter_tag_ids')
    tagIds = django_filters.CharFilter(method='filter_tag_ids')

    @staticmethod
    def _is_uuid(value):
        try:
            uuid.UUID(str(value))
            return True
        except (TypeError, ValueError, AttributeError):
            return False

    @staticmethod
    def _text_cast_filter(queryset, field_name, value):
        alias = f'{field_name.replace("__", "_")}_text'
        return queryset.annotate(
            **{alias: Cast(field_name, output_field=CharField())}
        ).filter(**{f'{alias}__icontains': value})

    def _filter_relation_or_uuid(self, queryset, value, *, id_field, text_fields):
        if self._is_uuid(value):
            return queryset.filter(**{id_field: value})

        query = Q()
        for field_name in text_fields:
            query |= Q(**{f'{field_name}__icontains': value})
        return queryset.filter(query)

    def filter_search(self, queryset, name, value):
        """
        Search across multiple text fields.

        Searches visible list fields including numbers and relation names.
        """
        annotated = queryset.annotate(
            purchase_price_text=Cast('purchase_price', output_field=CharField()),
            current_value_text=Cast('current_value', output_field=CharField()),
            purchase_date_text=Cast('purchase_date', output_field=CharField()),
        )
        return annotated.filter(
            Q(asset_code__icontains=value) |
            Q(asset_name__icontains=value) |
            Q(specification__icontains=value) |
            Q(brand__icontains=value) |
            Q(model__icontains=value) |
            Q(serial_number__icontains=value) |
            Q(asset_category__name__icontains=value) |
            Q(department__name__icontains=value) |
            Q(location__name__icontains=value) |
            Q(location__path__icontains=value) |
            Q(custodian__username__icontains=value) |
            Q(custodian__first_name__icontains=value) |
            Q(custodian__last_name__icontains=value) |
            Q(supplier__name__icontains=value) |
            Q(asset_status__icontains=value) |
            Q(purchase_price_text__icontains=value) |
            Q(current_value_text__icontains=value) |
            Q(purchase_date_text__icontains=value)
        )

    def filter_asset_category(self, queryset, name, value):
        return self._filter_relation_or_uuid(
            queryset,
            value,
            id_field='asset_category_id',
            text_fields=['asset_category__name', 'asset_category__code']
        )

    def filter_department(self, queryset, name, value):
        return self._filter_relation_or_uuid(
            queryset,
            value,
            id_field='department_id',
            text_fields=['department__name', 'department__code', 'department__full_path_name']
        )

    def filter_location(self, queryset, name, value):
        return self._filter_relation_or_uuid(
            queryset,
            value,
            id_field='location_id',
            text_fields=['location__name', 'location__path']
        )

    def filter_custodian(self, queryset, name, value):
        return self._filter_relation_or_uuid(
            queryset,
            value,
            id_field='custodian_id',
            text_fields=['custodian__username', 'custodian__first_name', 'custodian__last_name']
        )

    def filter_user(self, queryset, name, value):
        return self._filter_relation_or_uuid(
            queryset,
            value,
            id_field='user_id',
            text_fields=['user__username', 'user__first_name', 'user__last_name']
        )

    def filter_supplier(self, queryset, name, value):
        return self._filter_relation_or_uuid(
            queryset,
            value,
            id_field='supplier_id',
            text_fields=['supplier__name', 'supplier__code']
        )

    def filter_asset_status(self, queryset, name, value):
        return queryset.filter(asset_status__icontains=value)

    def filter_purchase_price(self, queryset, name, value):
        return self._text_cast_filter(queryset, 'purchase_price', value)

    def filter_current_value(self, queryset, name, value):
        return self._text_cast_filter(queryset, 'current_value', value)

    def filter_tag_ids(self, queryset, name, value):
        """Filter assets by asset tags and legacy generic tags."""
        if value in (None, ''):
            return queryset

        if isinstance(value, (list, tuple)):
            raw_values = value
        else:
            raw_values = str(value).split(',')

        tag_ids = [str(item).strip() for item in raw_values if str(item).strip()]
        if not tag_ids:
            return queryset

        tag_logic = (
            str(
                self.data.get('tag_logic')
                or self.data.get('tagLogic')
                or self.data.get('match_type')
                or self.data.get('matchType')
                or 'or'
            )
            .strip()
            .lower()
        )
        if tag_logic not in {'and', 'or'}:
            tag_logic = 'or'

        asset_tag_ids = list(
            AssetTag.all_objects.filter(
                id__in=tag_ids,
                is_deleted=False,
                is_active=True,
            ).values_list('id', flat=True)
        )
        generic_tag_ids = list(
            Tag.all_objects.filter(
                id__in=tag_ids,
                is_deleted=False,
            ).values_list('id', flat=True)
        )
        resolved_tag_count = len(asset_tag_ids) + len(generic_tag_ids)
        if resolved_tag_count != len(set(tag_ids)):
            return queryset.none()

        content_type = ContentType.objects.get_for_model(Asset, for_concrete_model=False)

        filtered_queryset = queryset
        if asset_tag_ids and tag_logic == 'and':
            filtered_queryset = filtered_queryset.annotate(
                asset_tag_match_count=Count(
                    'asset_tag_relations__tag',
                    filter=Q(
                        asset_tag_relations__tag_id__in=asset_tag_ids,
                        asset_tag_relations__is_deleted=False,
                        asset_tag_relations__tag__is_deleted=False,
                        asset_tag_relations__tag__is_active=True,
                    ),
                    distinct=True,
                )
            ).filter(asset_tag_match_count=len(asset_tag_ids))

        if generic_tag_ids and tag_logic == 'and':
            generic_tagged_asset_ids = (
                TagAssignment.all_objects
                .filter(
                    content_type=content_type,
                    tag_id__in=generic_tag_ids,
                    is_deleted=False,
                )
                .values('object_id')
                .annotate(match_count=Count('tag_id', distinct=True))
                .filter(match_count=len(generic_tag_ids))
                .values_list('object_id', flat=True)
            )
            filtered_queryset = filtered_queryset.filter(id__in=generic_tagged_asset_ids)

        if tag_logic == 'and':
            return filtered_queryset.distinct()

        or_query = Q()
        if asset_tag_ids:
            or_query |= Q(
                asset_tag_relations__tag_id__in=asset_tag_ids,
                asset_tag_relations__is_deleted=False,
                asset_tag_relations__tag__is_deleted=False,
                asset_tag_relations__tag__is_active=True,
            )

        if generic_tag_ids:
            generic_tagged_asset_ids = (
                TagAssignment.all_objects
                .filter(
                    content_type=content_type,
                    tag_id__in=generic_tag_ids,
                    is_deleted=False,
                )
                .values_list('object_id', flat=True)
            )
            or_query |= Q(id__in=generic_tagged_asset_ids)

        return filtered_queryset.filter(or_query).distinct()


class SupplierFilter(BaseModelFilter):
    """Filter for Supplier list endpoint."""

    class Meta:
        model = Supplier
        fields = ['code', 'name', 'created_by', 'is_deleted']

    code = django_filters.CharFilter(lookup_expr='icontains')
    name = django_filters.CharFilter(lookup_expr='icontains')
    search = django_filters.CharFilter(method='filter_search')

    def filter_search(self, queryset, name, value):
        """Search by code or name."""
        return queryset.filter(
            Q(code__icontains=value) | Q(name__icontains=value)
        )


class LocationFilter(BaseModelFilter):
    """Filter for Location list endpoint."""

    class Meta:
        model = Location
        fields = ['name', 'parent', 'location_type', 'created_by', 'is_deleted']

    name = django_filters.CharFilter(lookup_expr='icontains')
    path = django_filters.CharFilter(lookup_expr='icontains')
    parent = django_filters.UUIDFilter(field_name='parent_id')
    location_type = django_filters.ChoiceFilter(choices=Location.LOCATION_TYPE_CHOICES)
    search = django_filters.CharFilter(method='filter_search')

    def filter_search(self, queryset, name, value):
        """Search by name or path."""
        return queryset.filter(
            Q(name__icontains=value) | Q(path__icontains=value)
        )


class AssetStatusLogFilter(BaseModelFilter):
    """Filter for AssetStatusLog list endpoint."""

    class Meta:
        model = AssetStatusLog
        fields = ['asset', 'old_status', 'new_status', 'created_by', 'is_deleted']

    asset = django_filters.UUIDFilter(field_name='asset_id')
    old_status = django_filters.CharFilter(lookup_expr='exact')
    new_status = django_filters.CharFilter(lookup_expr='exact')

    # Date range for status change
    changed_at_from = django_filters.DateTimeFilter(
        field_name='created_at',
        lookup_expr='gte'
    )
    changed_at_to = django_filters.DateTimeFilter(
        field_name='created_at',
        lookup_expr='lte'
    )
