"""
Insurance management serializers.

This module contains serializers for all insurance-related models.
"""

from rest_framework import serializers
from apps.common.serializers.base import BaseModelSerializer
from .models import (
    InsuranceCompany, InsurancePolicy, InsuredAsset,
    PremiumPayment, ClaimRecord, PolicyRenewal
)


class InsuranceCompanySerializer(BaseModelSerializer):
    """Insurance Company Serializer."""

    class Meta(BaseModelSerializer.Meta):
        model = InsuranceCompany
        fields = BaseModelSerializer.Meta.fields + [
            'code', 'name', 'short_name', 'company_type',
            'contact_person', 'contact_phone', 'contact_email', 'website', 'address',
            'claims_phone', 'claims_email',
            'notes', 'is_active',
        ]


class InsuredAssetSerializer(BaseModelSerializer):
    """Insured Asset Serializer."""
    asset_name = serializers.CharField(source='asset.asset_name', read_only=True)
    asset_code = serializers.CharField(source='asset.asset_code', read_only=True)

    class Meta(BaseModelSerializer.Meta):
        model = InsuredAsset
        fields = BaseModelSerializer.Meta.fields + [
            'policy', 'asset', 'asset_name', 'asset_code',
            'insured_amount', 'premium_amount',
            'asset_location', 'asset_usage',
            'valuation_method', 'valuation_date',
            'notes',
        ]


class PremiumPaymentSerializer(BaseModelSerializer):
    """Premium Payment Serializer."""
    policy_no = serializers.CharField(source='policy.policy_no', read_only=True)
    company_name = serializers.CharField(source='policy.company.name', read_only=True)
    outstanding_amount = serializers.ReadOnlyField()
    is_overdue = serializers.ReadOnlyField()

    class Meta(BaseModelSerializer.Meta):
        model = PremiumPayment
        fields = BaseModelSerializer.Meta.fields + [
            'policy', 'policy_no', 'company_name',
            'payment_no', 'due_date', 'amount', 'paid_amount',
            'outstanding_amount', 'is_overdue',
            'status', 'paid_date', 'payment_method', 'payment_reference',
            'invoice_no', 'receipt_document', 'notes',
        ]


class InsurancePolicySerializer(BaseModelSerializer):
    """Insurance Policy Serializer."""
    company_name = serializers.CharField(source='company.name', read_only=True)
    company_short_name = serializers.CharField(source='company.short_name', read_only=True)
    insured_assets = InsuredAssetSerializer(many=True, read_only=True)
    payments = PremiumPaymentSerializer(many=True, read_only=True)
    is_active = serializers.BooleanField(read_only=True)
    days_until_expiry = serializers.IntegerField(read_only=True)
    is_expiring_soon = serializers.BooleanField(read_only=True)
    unpaid_premium = serializers.DecimalField(max_digits=14, decimal_places=2, read_only=True)

    # Statistics
    total_insured_assets = serializers.IntegerField(read_only=True)
    total_claims = serializers.IntegerField(read_only=True)
    total_claim_amount = serializers.DecimalField(max_digits=14, decimal_places=2, read_only=True)

    class Meta(BaseModelSerializer.Meta):
        model = InsurancePolicy
        fields = BaseModelSerializer.Meta.fields + [
            # Policy
            'policy_no', 'policy_name', 'company', 'company_name', 'company_short_name',
            # Type
            'insurance_type', 'coverage_type',
            # Period
            'start_date', 'end_date', 'renewal_date',
            # Financial
            'total_insured_amount', 'total_premium', 'payment_frequency',
            'deductible_amount', 'deductible_type',
            # Status
            'status', 'is_active', 'days_until_expiry', 'is_expiring_soon',
            # Relations & Stats
            'insured_assets', 'payments', 'unpaid_premium',
            'total_insured_assets', 'total_claims', 'total_claim_amount',
            # Documents
            'policy_document',
            # Terms
            'coverage_description', 'exclusion_clause', 'notes',
        ]


class ClaimRecordSerializer(BaseModelSerializer):
    """Claim Record Serializer."""
    policy_no = serializers.CharField(source='policy.policy_no', read_only=True)
    company_name = serializers.CharField(source='policy.company.name', read_only=True)
    asset_name = serializers.CharField(source='asset.asset_name', read_only=True)
    asset_code = serializers.CharField(source='asset.asset_code', read_only=True)
    payout_ratio = serializers.FloatField(read_only=True)

    class Meta(BaseModelSerializer.Meta):
        model = ClaimRecord
        fields = BaseModelSerializer.Meta.fields + [
            'policy', 'policy_no', 'company_name',
            'asset', 'asset_name', 'asset_code',
            'claim_no', 'incident_date', 'incident_type', 'incident_description',
            'incident_location', 'claim_date', 'claimed_amount',
            'status', 'approved_amount', 'paid_amount', 'paid_date', 'payout_ratio',
            'adjuster_name', 'adjuster_contact',
            'photos', 'supporting_documents',
            'settlement_date', 'settlement_notes',
            'notes',
        ]


class PolicyRenewalSerializer(BaseModelSerializer):
    """Policy Renewal Serializer."""
    original_policy_no = serializers.CharField(source='original_policy.policy_no', read_only=True)
    renewed_policy_no = serializers.CharField(source='renewed_policy.policy_no', read_only=True)
    premium_change = serializers.ReadOnlyField()
    premium_change_percent = serializers.FloatField(read_only=True)

    class Meta(BaseModelSerializer.Meta):
        model = PolicyRenewal
        fields = BaseModelSerializer.Meta.fields + [
            'original_policy', 'original_policy_no',
            'renewed_policy', 'renewed_policy_no',
            'renewal_no', 'original_end_date', 'new_start_date', 'new_end_date',
            'original_premium', 'new_premium', 'premium_change', 'premium_change_percent',
            'coverage_changes', 'notes',
        ]
