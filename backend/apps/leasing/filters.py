"""
Leasing management filters.
"""

from django_filters import rest_framework as filters
from apps.common.filters.base import BaseModelFilter
from .models import (
    LeaseContract, LeaseItem, RentPayment,
    LeaseReturn, LeaseExtension
)


class LeaseContractFilter(BaseModelFilter):
    """Lease Contract Filter."""

    status = filters.ChoiceFilter(choices=LeaseContract.STATUS_CHOICES)
    lessee_name = filters.CharFilter(lookup_expr='icontains')
    payment_type = filters.ChoiceFilter(choices=LeaseContract.PAYMENT_TYPE_CHOICES)
    lessee_type = filters.ChoiceFilter(choices=[('individual', 'Individual'), ('company', 'Company')])
    contract_no = filters.CharFilter(lookup_expr='icontains')
    date_from = filters.DateFilter(field_name='start_date', lookup_expr='gte')
    date_to = filters.DateFilter(field_name='end_date', lookup_expr='lte')
    start_date_from = filters.DateFilter(field_name='start_date', lookup_expr='gte')
    start_date_to = filters.DateFilter(field_name='start_date', lookup_expr='lte')
    end_date_from = filters.DateFilter(field_name='end_date', lookup_expr='gte')
    end_date_to = filters.DateFilter(field_name='end_date', lookup_expr='lte')
    expires_soon = filters.BooleanFilter(method='filter_expires_soon')
    total_rent_min = filters.NumberFilter(field_name='total_rent', lookup_expr='gte')
    total_rent_max = filters.NumberFilter(field_name='total_rent', lookup_expr='lte')

    def filter_expires_soon(self, queryset, name, value):
        """Filter contracts expiring within 30 days."""
        if value:
            from django.utils import timezone
            from datetime import timedelta
            delta = timezone.now().date() + timedelta(days=30)
            return queryset.filter(
                end_date__lte=delta,
                status='active'
            )
        return queryset

    class Meta(BaseModelFilter.Meta):
        model = LeaseContract
        fields = BaseModelFilter.Meta.fields + [
            'status', 'lessee_name', 'payment_type', 'lessee_type', 'contract_no',
            'start_date', 'end_date', 'date_from', 'date_to',
            'start_date_from', 'start_date_to', 'end_date_from', 'end_date_to',
            'expires_soon', 'total_rent_min', 'total_rent_max',
        ]


class LeaseItemFilter(BaseModelFilter):
    """Lease Item Filter."""

    contract = filters.UUIDFilter(field_name='contract__id')
    asset = filters.UUIDFilter(field_name='asset__id')
    start_condition = filters.ChoiceFilter(choices=LeaseItem.CONDITION_CHOICES)
    return_condition = filters.ChoiceFilter(choices=LeaseItem.CONDITION_CHOICES)

    class Meta(BaseModelFilter.Meta):
        model = LeaseItem
        fields = BaseModelFilter.Meta.fields + [
            'contract', 'asset', 'start_condition', 'return_condition',
        ]


class RentPaymentFilter(BaseModelFilter):
    """Rent Payment Filter."""

    status = filters.ChoiceFilter(choices=RentPayment.STATUS_CHOICES)
    contract = filters.UUIDFilter(field_name='contract__id')
    due_from = filters.DateFilter(field_name='due_date', lookup_expr='gte')
    due_to = filters.DateFilter(field_name='due_date', lookup_expr='lte')
    due_date_from = filters.DateFilter(field_name='due_date', lookup_expr='gte')
    due_date_to = filters.DateFilter(field_name='due_date', lookup_expr='lte')
    overdue_only = filters.BooleanFilter(method='filter_overdue')
    payment_no = filters.CharFilter(lookup_expr='icontains')

    def filter_overdue(self, queryset, name, value):
        """Filter only overdue payments."""
        if value:
            from django.utils import timezone
            return queryset.filter(
                due_date__lt=timezone.now().date(),
                status__in=['pending', 'partial']
            )
        return queryset

    class Meta(BaseModelFilter.Meta):
        model = RentPayment
        fields = BaseModelFilter.Meta.fields + [
            'status', 'contract', 'due_date', 'payment_no',
            'due_from', 'due_to', 'due_date_from', 'due_date_to', 'overdue_only',
        ]


class LeaseReturnFilter(BaseModelFilter):
    """Lease Return Filter."""

    condition = filters.ChoiceFilter(choices=LeaseReturn.CONDITION_CHOICES)
    contract = filters.UUIDFilter(field_name='contract__id')
    asset = filters.UUIDFilter(field_name='asset__id')
    date_from = filters.DateFilter(field_name='return_date', lookup_expr='gte')
    date_to = filters.DateFilter(field_name='return_date', lookup_expr='lte')
    return_date_from = filters.DateFilter(field_name='return_date', lookup_expr='gte')
    return_date_to = filters.DateFilter(field_name='return_date', lookup_expr='lte')
    return_no = filters.CharFilter(lookup_expr='icontains')

    class Meta(BaseModelFilter.Meta):
        model = LeaseReturn
        fields = BaseModelFilter.Meta.fields + [
            'condition', 'contract', 'asset', 'return_date', 'return_no',
            'date_from', 'date_to', 'return_date_from', 'return_date_to',
        ]


class LeaseExtensionFilter(BaseModelFilter):
    """Lease Extension Filter."""

    contract = filters.UUIDFilter(field_name='contract__id')
    extension_no = filters.CharFilter(lookup_expr='icontains')
    original_end_date_from = filters.DateFilter(field_name='original_end_date', lookup_expr='gte')
    original_end_date_to = filters.DateFilter(field_name='original_end_date', lookup_expr='lte')
    new_end_date_from = filters.DateFilter(field_name='new_end_date', lookup_expr='gte')
    new_end_date_to = filters.DateFilter(field_name='new_end_date', lookup_expr='lte')

    class Meta(BaseModelFilter.Meta):
        model = LeaseExtension
        fields = BaseModelFilter.Meta.fields + [
            'contract', 'extension_no',
            'original_end_date_from', 'original_end_date_to',
            'new_end_date_from', 'new_end_date_to',
        ]
