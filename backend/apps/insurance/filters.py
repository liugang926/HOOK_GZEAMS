"""
Insurance management filters.

This module contains filter classes for insurance-related models.
"""

from django_filters import rest_framework as filters
from apps.common.filters.base import BaseModelFilter
from .models import (
    InsuranceCompany, InsurancePolicy, InsuredAsset,
    PremiumPayment, ClaimRecord, PolicyRenewal
)


class InsuranceCompanyFilter(BaseModelFilter):
    """Insurance Company Filter."""

    company_type = filters.CharFilter(lookup_expr='icontains')
    name = filters.CharFilter(lookup_expr='icontains')
    is_active = filters.BooleanFilter()

    class Meta(BaseModelFilter.Meta):
        model = InsuranceCompany
        fields = BaseModelFilter.Meta.fields + [
            'code', 'name', 'short_name', 'company_type', 'is_active',
        ]


class InsurancePolicyFilter(BaseModelFilter):
    """Insurance Policy Filter."""

    status = filters.ChoiceFilter(choices=InsurancePolicy.STATUS_CHOICES)
    insurance_type = filters.CharFilter(lookup_expr='icontains')
    payment_frequency = filters.ChoiceFilter(choices=InsurancePolicy.PAYMENT_FREQUENCY_CHOICES)
    company = filters.UUIDFilter(field_name='company__id')
    policy_no = filters.CharFilter(lookup_expr='icontains')
    start_date_from = filters.DateFilter(field_name='start_date', lookup_expr='gte')
    start_date_to = filters.DateFilter(field_name='start_date', lookup_expr='lte')
    end_date_from = filters.DateFilter(field_name='end_date', lookup_expr='gte')
    end_date_to = filters.DateFilter(field_name='end_date', lookup_expr='lte')
    expires_soon = filters.BooleanFilter(method='filter_expires_soon')
    days = filters.NumberFilter(method='filter_expires_soon')
    is_active = filters.BooleanFilter(method='filter_is_active')
    total_premium_min = filters.NumberFilter(field_name='total_premium', lookup_expr='gte')
    total_premium_max = filters.NumberFilter(field_name='total_premium', lookup_expr='lte')

    def filter_expires_soon(self, queryset, name, value):
        """Filter policies expiring within specified days (default 30).

        The 'days' parameter can be used to customize the threshold.
        Use ?expires_soon=true&days=60 for policies expiring within 60 days.
        """
        # Check if expires_soon filter is active
        expires_soon_value = self.data.get('expires_soon')
        # Get days parameter with default of 30
        days_value = self.data.get('days')

        if name == 'expires_soon' and not value:
            return queryset

        if name == 'days' and not expires_soon_value:
            # If only days is specified without expires_soon, don't filter
            return queryset

        # Determine the number of days
        if days_value:
            try:
                days = int(days_value)
            except (ValueError, TypeError):
                days = 30
        else:
            days = 30

        from django.utils import timezone
        from datetime import timedelta
        delta = timezone.now().date() + timedelta(days=days)
        return queryset.filter(
            end_date__lte=delta,
            end_date__gte=timezone.now().date(),
            status='active'
        )

    def filter_is_active(self, queryset, name, value):
        """Filter currently active policies."""
        if value:
            from django.utils import timezone
            today = timezone.now().date()
            return queryset.filter(
                status='active',
                start_date__lte=today,
                end_date__gte=today
            )
        return queryset

    class Meta(BaseModelFilter.Meta):
        model = InsurancePolicy
        fields = BaseModelFilter.Meta.fields + [
            'status', 'insurance_type', 'payment_frequency', 'company', 'policy_no',
            'start_date', 'end_date', 'start_date_from', 'start_date_to',
            'end_date_from', 'end_date_to', 'expires_soon', 'days', 'is_active',
            'total_premium_min', 'total_premium_max',
        ]


class InsuredAssetFilter(BaseModelFilter):
    """Insured Asset Filter."""

    policy = filters.UUIDFilter(field_name='policy__id')
    asset = filters.UUIDFilter(field_name='asset__id')
    valuation_method = filters.CharFilter(lookup_expr='icontains')
    insured_amount_min = filters.NumberFilter(field_name='insured_amount', lookup_expr='gte')
    insured_amount_max = filters.NumberFilter(field_name='insured_amount', lookup_expr='lte')

    class Meta(BaseModelFilter.Meta):
        model = InsuredAsset
        fields = BaseModelFilter.Meta.fields + [
            'policy', 'asset', 'valuation_method',
            'insured_amount_min', 'insured_amount_max',
        ]


class PremiumPaymentFilter(BaseModelFilter):
    """Premium Payment Filter."""

    status = filters.ChoiceFilter(choices=PremiumPayment.STATUS_CHOICES)
    policy = filters.UUIDFilter(field_name='policy__id')
    payment_no = filters.CharFilter(lookup_expr='icontains')
    due_from = filters.DateFilter(field_name='due_date', lookup_expr='gte')
    due_to = filters.DateFilter(field_name='due_date', lookup_expr='lte')
    due_date_from = filters.DateFilter(field_name='due_date', lookup_expr='gte')
    due_date_to = filters.DateFilter(field_name='due_date', lookup_expr='lte')
    overdue_only = filters.BooleanFilter(method='filter_overdue')
    paid_date_from = filters.DateFilter(field_name='paid_date', lookup_expr='gte')
    paid_date_to = filters.DateFilter(field_name='paid_date', lookup_expr='lte')
    amount_min = filters.NumberFilter(field_name='amount', lookup_expr='gte')
    amount_max = filters.NumberFilter(field_name='amount', lookup_expr='lte')

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
        model = PremiumPayment
        fields = BaseModelFilter.Meta.fields + [
            'status', 'policy', 'payment_no', 'due_date',
            'due_from', 'due_to', 'due_date_from', 'due_date_to',
            'overdue_only', 'paid_date_from', 'paid_date_to',
            'amount_min', 'amount_max',
        ]


class ClaimRecordFilter(BaseModelFilter):
    """Claim Record Filter."""

    status = filters.ChoiceFilter(choices=ClaimRecord.STATUS_CHOICES)
    incident_type = filters.ChoiceFilter(choices=ClaimRecord.TYPE_CHOICES)
    policy = filters.UUIDFilter(field_name='policy__id')
    asset = filters.UUIDFilter(field_name='asset__id')
    claim_no = filters.CharFilter(lookup_expr='icontains')
    incident_date_from = filters.DateFilter(field_name='incident_date', lookup_expr='gte')
    incident_date_to = filters.DateFilter(field_name='incident_date', lookup_expr='lte')
    claim_date_from = filters.DateFilter(field_name='claim_date', lookup_expr='gte')
    claim_date_to = filters.DateFilter(field_name='claim_date', lookup_expr='lte')
    claimed_amount_min = filters.NumberFilter(field_name='claimed_amount', lookup_expr='gte')
    claimed_amount_max = filters.NumberFilter(field_name='claimed_amount', lookup_expr='lte')

    class Meta(BaseModelFilter.Meta):
        model = ClaimRecord
        fields = BaseModelFilter.Meta.fields + [
            'status', 'incident_type', 'policy', 'asset', 'claim_no',
            'incident_date', 'incident_date_from', 'incident_date_to',
            'claim_date', 'claim_date_from', 'claim_date_to',
            'claimed_amount_min', 'claimed_amount_max',
        ]


class PolicyRenewalFilter(BaseModelFilter):
    """Policy Renewal Filter."""

    original_policy = filters.UUIDFilter(field_name='original_policy__id')
    renewed_policy = filters.UUIDFilter(field_name='renewed_policy__id')
    renewal_no = filters.CharFilter(lookup_expr='icontains')
    new_start_date_from = filters.DateFilter(field_name='new_start_date', lookup_expr='gte')
    new_start_date_to = filters.DateFilter(field_name='new_start_date', lookup_expr='lte')
    new_end_date_from = filters.DateFilter(field_name='new_end_date', lookup_expr='gte')
    new_end_date_to = filters.DateFilter(field_name='new_end_date', lookup_expr='lte')

    class Meta(BaseModelFilter.Meta):
        model = PolicyRenewal
        fields = BaseModelFilter.Meta.fields + [
            'original_policy', 'renewed_policy', 'renewal_no',
            'new_start_date_from', 'new_start_date_to',
            'new_end_date_from', 'new_end_date_to',
        ]
