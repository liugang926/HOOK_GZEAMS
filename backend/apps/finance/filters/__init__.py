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
    voucher_date_from = filters.DateFilter(field_name='voucher_date', lookup_expr='gte')
    voucher_date_to = filters.DateFilter(field_name='voucher_date', lookup_expr='lte')
    total_amount_from = filters.NumberFilter(field_name='total_amount', lookup_expr='gte')
    total_amount_to = filters.NumberFilter(field_name='total_amount', lookup_expr='lte')
    posted_to_erp = filters.BooleanFilter(field_name='erp_voucher_no', lookup_expr='isnull')

    class Meta(BaseModelFilter.Meta):
        model = FinanceVoucher
        fields = BaseModelFilter.Meta.fields + [
            'voucher_no', 'business_type', 'status',
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
