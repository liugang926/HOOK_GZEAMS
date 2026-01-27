"""
Filter Classes for Consumable Management.

All filters inherit from BaseModelFilter for common filtering capabilities.
"""
import django_filters
from django_filters import rest_framework as filters
from django.db.models import F
from apps.common.filters.base import BaseModelFilter
from apps.consumables.models import (
    ConsumableCategory,
    Consumable,
    ConsumableStock,
    ConsumablePurchase,
    ConsumableIssue,
    TransactionType,
)


# ========== Category Filter ==========

class ConsumableCategoryFilter(BaseModelFilter):
    """Filter for ConsumableCategory queries"""

    code = filters.CharFilter(field_name='code', lookup_expr='icontains')
    name = filters.CharFilter(field_name='name', lookup_expr='icontains')
    parent_id = filters.UUIDFilter(field_name='parent__id')
    level = filters.NumberFilter(field_name='level')
    is_active = filters.BooleanFilter(field_name='is_active')
    enable_alert = filters.BooleanFilter(field_name='enable_alert')

    class Meta:
        model = ConsumableCategory
        fields = [
            'code', 'name', 'parent_id', 'level', 'is_active', 'enable_alert',
        ]


# ========== Consumable Filter ==========

class ConsumableFilter(BaseModelFilter):
    """Filter for Consumable queries"""

    code = filters.CharFilter(field_name='code', lookup_expr='icontains')
    name = filters.CharFilter(field_name='name', lookup_expr='icontains')
    category_id = filters.UUIDFilter(field_name='category__id')
    category_code = filters.CharFilter(field_name='category__code', lookup_expr='icontains')
    specification = filters.CharFilter(field_name='specification', lookup_expr='icontains')
    brand = filters.CharFilter(field_name='brand', lookup_expr='icontains')
    status = filters.CharFilter(field_name='status', lookup_expr='iexact')
    warehouse_id = filters.UUIDFilter(field_name='warehouse__id')
    unit = filters.CharFilter(field_name='unit', lookup_expr='iexact')

    # Stock range filters
    current_stock_min = filters.NumberFilter(field_name='current_stock', lookup_expr='gte')
    current_stock_max = filters.NumberFilter(field_name='current_stock', lookup_expr='lte')
    available_stock_min = filters.NumberFilter(field_name='available_stock', lookup_expr='gte')
    available_stock_max = filters.NumberFilter(field_name='available_stock', lookup_expr='lte')

    # Low stock filter
    is_low_stock = filters.BooleanFilter(method='filter_low_stock')

    # Price range filters
    purchase_price_min = filters.NumberFilter(field_name='purchase_price', lookup_expr='gte')
    purchase_price_max = filters.NumberFilter(field_name='purchase_price', lookup_expr='lte')

    class Meta:
        model = Consumable
        fields = [
            'code', 'name', 'category_id', 'category_code', 'specification',
            'brand', 'status', 'warehouse_id', 'unit',
        ]

    def filter_low_stock(self, queryset, name, value):
        """Filter consumables at or below reorder point"""
        if value is True:
            return queryset.filter(available_stock__lte=F('reorder_point'))
        elif value is False:
            return queryset.filter(available_stock__gt=F('reorder_point'))
        return queryset


# ========== Stock Transaction Filter ==========

class ConsumableStockFilter(BaseModelFilter):
    """Filter for ConsumableStock queries"""

    consumable_id = filters.UUIDFilter(field_name='consumable__id')
    consumable_code = filters.CharFilter(field_name='consumable__code', lookup_expr='icontains')
    consumable_name = filters.CharFilter(field_name='consumable__name', lookup_expr='icontains')
    transaction_type = filters.ChoiceFilter(field_name='transaction_type', choices=TransactionType.choices)
    source_type = filters.CharFilter(field_name='source_type', lookup_expr='iexact')
    source_no = filters.CharFilter(field_name='source_no', lookup_expr='icontains')
    handler_id = filters.UUIDFilter(field_name='handler__id')

    # Quantity filters
    quantity_min = filters.NumberFilter(field_name='quantity', lookup_expr='gte')
    quantity_max = filters.NumberFilter(field_name='quantity', lookup_expr='lte')

    # Transaction type filters for in/out
    is_inflow = filters.BooleanFilter(method='filter_inflow')

    class Meta:
        model = ConsumableStock
        fields = [
            'consumable_id', 'consumable_code', 'consumable_name',
            'transaction_type', 'source_type', 'source_no', 'handler_id',
        ]

    def filter_inflow(self, queryset, name, value):
        """Filter for inflow (positive) or outflow (negative) transactions"""
        if value is True:
            return queryset.filter(quantity__gt=0)
        elif value is False:
            return queryset.filter(quantity__lt=0)
        return queryset


# ========== Purchase Order Filter ==========

class ConsumablePurchaseFilter(BaseModelFilter):
    """Filter for ConsumablePurchase queries"""

    purchase_no = filters.CharFilter(field_name='purchase_no', lookup_expr='icontains')
    supplier_id = filters.UUIDFilter(field_name='supplier__id')
    supplier_name = filters.CharFilter(field_name='supplier__name', lookup_expr='icontains')
    status = filters.CharFilter(field_name='status', lookup_expr='iexact')
    approved_by_id = filters.UUIDFilter(field_name='approved_by__id')
    received_by_id = filters.UUIDFilter(field_name='received_by__id')

    # Date range filters
    purchase_date_from = filters.DateFilter(field_name='purchase_date', lookup_expr='gte')
    purchase_date_to = filters.DateFilter(field_name='purchase_date', lookup_expr='lte')
    approved_at_from = filters.DateTimeFilter(field_name='approved_at', lookup_expr='gte')
    approved_at_to = filters.DateTimeFilter(field_name='approved_at', lookup_expr='lte')
    received_at_from = filters.DateTimeFilter(field_name='received_at', lookup_expr='gte')
    received_at_to = filters.DateTimeFilter(field_name='received_at', lookup_expr='lte')

    # Amount range filters
    total_amount_min = filters.NumberFilter(field_name='total_amount', lookup_expr='gte')
    total_amount_max = filters.NumberFilter(field_name='total_amount', lookup_expr='lte')

    class Meta:
        model = ConsumablePurchase
        fields = [
            'purchase_no', 'supplier_id', 'supplier_name', 'status',
            'approved_by_id', 'received_by_id',
        ]


# ========== Issue Order Filter ==========

class ConsumableIssueFilter(BaseModelFilter):
    """Filter for ConsumableIssue queries"""

    issue_no = filters.CharFilter(field_name='issue_no', lookup_expr='icontains')
    applicant_id = filters.UUIDFilter(field_name='applicant__id')
    applicant_name = filters.CharFilter(field_name='applicant__username', lookup_expr='icontains')
    department_id = filters.UUIDFilter(field_name='department__id')
    department_name = filters.CharFilter(field_name='department__name', lookup_expr='icontains')
    status = filters.CharFilter(field_name='status', lookup_expr='iexact')
    approved_by_id = filters.UUIDFilter(field_name='approved_by__id')
    issued_by_id = filters.UUIDFilter(field_name='issued_by__id')

    # Date range filters
    issue_date_from = filters.DateFilter(field_name='issue_date', lookup_expr='gte')
    issue_date_to = filters.DateFilter(field_name='issue_date', lookup_expr='lte')
    approved_at_from = filters.DateTimeFilter(field_name='approved_at', lookup_expr='gte')
    approved_at_to = filters.DateTimeFilter(field_name='approved_at', lookup_expr='lte')
    issued_at_from = filters.DateTimeFilter(field_name='issued_at', lookup_expr='gte')
    issued_at_to = filters.DateTimeFilter(field_name='issued_at', lookup_expr='lte')

    class Meta:
        model = ConsumableIssue
        fields = [
            'issue_no', 'applicant_id', 'applicant_name', 'department_id',
            'department_name', 'status', 'approved_by_id', 'issued_by_id',
        ]
