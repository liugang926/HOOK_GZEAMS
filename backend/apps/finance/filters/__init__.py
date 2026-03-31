"""
Finance Module Filters

Filter classes for financial vouchers, voucher entries, and voucher templates.
"""
import django_filters
from django_filters import rest_framework as filters
from apps.common.filters.base import BaseModelFilter
from apps.finance.models import FinanceVoucher, VoucherEntry, VoucherTemplate


class FinanceVoucherFilter(BaseModelFilter):
    """Finance Voucher Filter"""

    voucher_no = filters.CharFilter(lookup_expr='icontains')
    business_type = filters.CharFilter()
    status = filters.CharFilter()
    department = filters.UUIDFilter(method='filter_department')
    source_asset = filters.UUIDFilter(method='filter_source_asset')
    source_purchase_request = filters.CharFilter(method='filter_source_purchase_request')
    source_receipt = filters.CharFilter(method='filter_source_receipt')
    source_object_code = filters.CharFilter(method='filter_source_object_code')
    source_id = filters.CharFilter(method='filter_source_id')
    voucher_date_from = filters.DateFilter(field_name='voucher_date', lookup_expr='gte')
    voucher_date_to = filters.DateFilter(field_name='voucher_date', lookup_expr='lte')
    total_amount_from = filters.NumberFilter(field_name='total_amount', lookup_expr='gte')
    total_amount_to = filters.NumberFilter(field_name='total_amount', lookup_expr='lte')
    posted_to_erp = filters.BooleanFilter(field_name='erp_voucher_no', lookup_expr='isnull')

    def filter_department(self, queryset, name, value):
        """Filter vouchers by the creator's primary department."""
        if not value:
            return queryset
        return queryset.filter(
            created_by__user_departments__department_id=value,
            created_by__user_departments__is_primary=True,
            created_by__user_departments__is_deleted=False,
        ).distinct()

    def filter_source_asset(self, queryset, name, value):
        """Filter vouchers linked to an asset through source trace fields."""
        if not value:
            return queryset
        return queryset.filter(custom_fields__asset_id_index__icontains=f'|{value}|')

    def filter_source_object_code(self, queryset, name, value):
        """Filter vouchers by source object code from source trace."""
        normalized = str(value or '').strip()
        if not normalized:
            return queryset
        return queryset.filter(custom_fields__source_object_code=normalized)

    def filter_source_purchase_request(self, queryset, name, value):
        """Filter vouchers by linked purchase request id from source trace."""
        normalized = str(value or '').strip()
        if not normalized:
            return queryset
        return queryset.filter(custom_fields__source_purchase_request_id=normalized)

    def filter_source_receipt(self, queryset, name, value):
        """Filter vouchers by linked asset receipt id from source trace."""
        normalized = str(value or '').strip()
        if not normalized:
            return queryset
        return queryset.filter(custom_fields__source_receipt_id=normalized)

    def filter_source_id(self, queryset, name, value):
        """Filter vouchers by source business id from source trace."""
        normalized = str(value or '').strip()
        if not normalized:
            return queryset
        return queryset.filter(custom_fields__source_id=normalized)

    class Meta(BaseModelFilter.Meta):
        model = FinanceVoucher
        fields = BaseModelFilter.Meta.fields + [
            'voucher_no', 'business_type', 'status', 'department',
            'source_asset', 'source_purchase_request', 'source_receipt',
            'source_object_code', 'source_id',
            'voucher_date', 'total_amount',
        ]


class VoucherEntryFilter(BaseModelFilter):
    """Voucher Entry Filter"""

    voucher = filters.CharFilter(field_name='voucher__voucher_no', lookup_expr='icontains')
    account_code = filters.CharFilter(lookup_expr='icontains')
    account_name = filters.CharFilter(lookup_expr='icontains')
    debit_amount_from = filters.NumberFilter(field_name='debit_amount', lookup_expr='gte')
    debit_amount_to = filters.NumberFilter(field_name='debit_amount', lookup_expr='lte')
    credit_amount_from = filters.NumberFilter(field_name='credit_amount', lookup_expr='gte')
    credit_amount_to = filters.NumberFilter(field_name='credit_amount', lookup_expr='lte')

    class Meta(BaseModelFilter.Meta):
        model = VoucherEntry
        fields = BaseModelFilter.Meta.fields + [
            'voucher', 'account_code', 'account_name',
            'debit_amount', 'credit_amount',
        ]


class VoucherTemplateFilter(BaseModelFilter):
    """Voucher Template Filter"""

    code = filters.CharFilter(lookup_expr='icontains')
    name = filters.CharFilter(lookup_expr='icontains')
    business_type = filters.CharFilter()
    is_active = filters.BooleanFilter()

    class Meta(BaseModelFilter.Meta):
        model = VoucherTemplate
        fields = BaseModelFilter.Meta.fields + [
            'code', 'name', 'business_type', 'is_active',
        ]


__all__ = [
    'FinanceVoucherFilter',
    'VoucherEntryFilter',
    'VoucherTemplateFilter',
]
