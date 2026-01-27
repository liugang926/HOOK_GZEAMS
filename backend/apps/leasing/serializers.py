"""
Leasing management serializers.
"""

from rest_framework import serializers
from apps.common.serializers.base import BaseModelSerializer
from .models import (
    LeaseContract, LeaseItem, RentPayment,
    LeaseReturn, LeaseExtension
)


class LeaseItemSerializer(BaseModelSerializer):
    """Lease Item Serializer."""
    asset_name = serializers.CharField(source='asset.asset_name', read_only=True)
    asset_code = serializers.CharField(source='asset.asset_code', read_only=True)
    days_leased = serializers.ReadOnlyField()
    total_rent = serializers.ReadOnlyField()

    class Meta(BaseModelSerializer.Meta):
        model = LeaseItem
        fields = BaseModelSerializer.Meta.fields + [
            'contract', 'asset', 'asset_name', 'asset_code',
            'daily_rate', 'insured_value',
            'actual_start_date', 'actual_end_date',
            'start_condition', 'return_condition', 'damage_description',
            'days_leased', 'total_rent', 'notes',
        ]


class RentPaymentSerializer(BaseModelSerializer):
    """Rent Payment Serializer."""
    contract_no = serializers.CharField(source='contract.contract_no', read_only=True)
    lessee_name = serializers.CharField(source='contract.lessee_name', read_only=True)
    outstanding_amount = serializers.ReadOnlyField()
    is_overdue = serializers.ReadOnlyField()

    class Meta(BaseModelSerializer.Meta):
        model = RentPayment
        fields = BaseModelSerializer.Meta.fields + [
            'contract', 'contract_no', 'lessee_name',
            'payment_no', 'due_date', 'amount', 'paid_amount',
            'outstanding_amount', 'is_overdue',
            'status', 'paid_date', 'payment_method', 'payment_reference',
            'invoice_no', 'invoice_date', 'notes',
        ]


class LeaseContractSerializer(BaseModelSerializer):
    """Lease Contract Serializer."""
    lessee_name = serializers.CharField(required=True)
    items = LeaseItemSerializer(many=True, read_only=True)
    payments = RentPaymentSerializer(many=True, read_only=True)
    is_active = serializers.BooleanField(read_only=True)
    days_remaining = serializers.IntegerField(read_only=True)
    total_days = serializers.IntegerField(read_only=True)
    unpaid_amount = serializers.DecimalField(
        max_digits=14, decimal_places=2, read_only=True
    )
    approved_by_name = serializers.CharField(
        source='approved_by.username', read_only=True
    )

    class Meta(BaseModelSerializer.Meta):
        model = LeaseContract
        fields = BaseModelSerializer.Meta.fields + [
            # Contract
            'contract_no', 'contract_name',
            # Lessee
            'lessee_name', 'lessee_type', 'lessee_contact',
            'lessee_phone', 'lessee_email', 'lessee_address', 'lessee_id_number',
            # Dates
            'start_date', 'end_date', 'actual_start_date', 'actual_end_date',
            # Financial
            'payment_type', 'total_rent', 'deposit_amount', 'deposit_paid',
            # Status
            'status', 'is_active', 'days_remaining', 'total_days',
            # Approval
            'approved_by', 'approved_by_name', 'approved_at',
            # Relations
            'items', 'payments', 'unpaid_amount',
            # Terms
            'terms', 'notes',
        ]

    def validate(self, data):
        """Validate contract dates."""
        start_date = data.get('start_date')
        end_date = data.get('end_date')

        if start_date and end_date and end_date <= start_date:
            raise serializers.ValidationError({
                'end_date': 'End date must be after start date'
            })

        return data


class LeaseReturnSerializer(BaseModelSerializer):
    """Lease Return Serializer."""
    contract_no = serializers.CharField(source='contract.contract_no', read_only=True)
    lessee_name = serializers.CharField(source='contract.lessee_name', read_only=True)
    asset_name = serializers.CharField(source='asset.asset_name', read_only=True)
    asset_code = serializers.CharField(source='asset.asset_code', read_only=True)
    received_by_name = serializers.CharField(
        source='received_by.username', read_only=True
    )

    class Meta(BaseModelSerializer.Meta):
        model = LeaseReturn
        fields = BaseModelSerializer.Meta.fields + [
            'contract', 'contract_no', 'lessee_name',
            'asset', 'asset_name', 'asset_code',
            'return_no', 'return_date', 'received_by', 'received_by_name',
            'condition', 'damage_description',
            'damage_fee', 'deposit_deduction', 'refund_amount',
            'photos', 'notes',
        ]


class LeaseExtensionSerializer(BaseModelSerializer):
    """Lease Extension Serializer."""
    contract_no = serializers.CharField(source='contract.contract_no', read_only=True)
    lessee_name = serializers.CharField(source='contract.lessee_name', read_only=True)
    approved_by_name = serializers.CharField(
        source='approved_by.username', read_only=True
    )
    additional_days = serializers.ReadOnlyField()

    class Meta(BaseModelSerializer.Meta):
        model = LeaseExtension
        fields = BaseModelSerializer.Meta.fields + [
            'contract', 'contract_no', 'lessee_name',
            'extension_no', 'original_end_date', 'new_end_date', 'additional_days',
            'additional_rent', 'reason', 'notes',
            'approved_by', 'approved_by_name', 'approved_at',
        ]
