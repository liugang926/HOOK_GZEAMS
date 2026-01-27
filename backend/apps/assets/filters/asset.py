"""
Filters for Asset and related models.

Provides:
- AssetFilter: Filter for asset list/search
- SupplierFilter: Filter for supplier list
- LocationFilter: Filter for location list
- AssetStatusLogFilter: Filter for status log list
"""
import django_filters
from django.db.models import Q
from apps.common.filters.base import BaseModelFilter
from apps.assets.models import Asset, Supplier, Location, AssetStatusLog


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
            'purchase_date', 'created_by', 'is_deleted'
        ]

    # Text search filters
    asset_code = django_filters.CharFilter(lookup_expr='icontains')
    asset_name = django_filters.CharFilter(lookup_expr='icontains')
    specification = django_filters.CharFilter(lookup_expr='icontains')
    brand = django_filters.CharFilter(lookup_expr='icontains')
    model = django_filters.CharFilter(lookup_expr='icontains')
    serial_number = django_filters.CharFilter(lookup_expr='icontains')

    # Related object filters
    asset_category = django_filters.UUIDFilter(field_name='asset_category_id')
    department = django_filters.UUIDFilter(field_name='department_id')
    location = django_filters.UUIDFilter(field_name='location_id')
    custodian = django_filters.UUIDFilter(field_name='custodian_id')
    user = django_filters.UUIDFilter(field_name='user_id')
    supplier = django_filters.UUIDFilter(field_name='supplier_id')

    # Status filter - use CharFilter since status values are from Dictionary (ASSET_STATUS)\n    asset_status = django_filters.CharFilter(lookup_expr='exact')

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
    purchase_price_to = django_filters.NumberFilter(
        field_name='purchase_price',
        lookup_expr='lte'
    )

    # Combined search filter
    search = django_filters.CharFilter(method='filter_search')

    def filter_search(self, queryset, name, value):
        """
        Search across multiple text fields.

        Searches: asset_code, asset_name, specification, brand, model, serial_number
        """
        return queryset.filter(
            Q(asset_code__icontains=value) |
            Q(asset_name__icontains=value) |
            Q(specification__icontains=value) |
            Q(brand__icontains=value) |
            Q(model__icontains=value) |
            Q(serial_number__icontains=value)
        )


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
