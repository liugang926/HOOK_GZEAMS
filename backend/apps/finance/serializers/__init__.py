"""
Finance Module Serializers

Serializers for financial vouchers, voucher entries, and voucher templates.
"""
from rest_framework import serializers
from apps.common.serializers.base import BaseModelSerializer
from apps.finance.models import FinanceVoucher, VoucherEntry, VoucherTemplate


class VoucherEntrySerializer(BaseModelSerializer):
    """Voucher Entry Serializer"""

    class Meta(BaseModelSerializer.Meta):
        model = VoucherEntry
        fields = BaseModelSerializer.Meta.fields + [
            'voucher', 'account_code', 'account_name',
            'debit_amount', 'credit_amount', 'description', 'line_no',
        ]


class VoucherEntryListSerializer(BaseModelSerializer):
    """Lightweight voucher entry serializer for lists"""

    class Meta(BaseModelSerializer.Meta):
        model = VoucherEntry
        fields = [
            'id', 'voucher', 'account_code', 'account_name',
            'debit_amount', 'credit_amount', 'description', 'line_no',
        ]


class VoucherEntryDetailSerializer(BaseModelSerializer):
    """Detailed voucher entry serializer"""
    voucher_no = serializers.CharField(source='voucher.voucher_no', read_only=True)

    class Meta(BaseModelSerializer.Meta):
        model = VoucherEntry
        fields = VoucherEntrySerializer.Meta.fields + ['voucher_no']


class FinanceVoucherSerializer(BaseModelSerializer):
    """Finance Voucher Serializer"""
    entries = VoucherEntrySerializer(many=True, read_only=True)
    entry_count = serializers.IntegerField(source='entries.count', read_only=True)
    is_balanced = serializers.BooleanField(read_only=True)

    class Meta(BaseModelSerializer.Meta):
        model = FinanceVoucher
        fields = BaseModelSerializer.Meta.fields + [
            'voucher_no', 'voucher_date', 'business_type',
            'summary', 'total_amount', 'status', 'notes',
            'erp_voucher_no', 'posted_at', 'posted_by',
            'entries', 'entry_count', 'is_balanced',
        ]


class FinanceVoucherListSerializer(BaseModelSerializer):
    """Lightweight voucher serializer for lists"""
    entry_count = serializers.IntegerField(source='entries.count', read_only=True)
    created_by_name = serializers.CharField(source='created_by.username', read_only=True)

    class Meta(BaseModelSerializer.Meta):
        model = FinanceVoucher
        fields = [
            'id', 'voucher_no', 'voucher_date', 'business_type',
            'summary', 'total_amount', 'status', 'entry_count',
            'created_by_name', 'created_at', 'updated_at',
        ]


class FinanceVoucherDetailSerializer(BaseModelSerializer):
    """Detailed voucher serializer with nested entries"""
    entries = VoucherEntryDetailSerializer(many=True, read_only=True)
    entry_count = serializers.IntegerField(source='entries.count', read_only=True)
    is_balanced = serializers.BooleanField(read_only=True)
    created_by_name = serializers.CharField(source='created_by.username', read_only=True)
    posted_by_name = serializers.CharField(source='posted_by.username', read_only=True)

    class Meta(BaseModelSerializer.Meta):
        model = FinanceVoucher
        fields = FinanceVoucherSerializer.Meta.fields + [
            'created_by_name', 'posted_by_name',
        ]


class VoucherTemplateSerializer(BaseModelSerializer):
    """Voucher Template Serializer"""

    class Meta(BaseModelSerializer.Meta):
        model = VoucherTemplate
        fields = BaseModelSerializer.Meta.fields + [
            'name', 'code', 'business_type',
            'template_config', 'is_active', 'description',
        ]


class VoucherTemplateListSerializer(BaseModelSerializer):
    """Lightweight template serializer for lists"""

    class Meta(BaseModelSerializer.Meta):
        model = VoucherTemplate
        fields = [
            'id', 'code', 'name', 'business_type',
            'is_active', 'created_at', 'updated_at',
        ]


class VoucherTemplateDetailSerializer(BaseModelSerializer):
    """Detailed template serializer"""

    class Meta(BaseModelSerializer.Meta):
        model = VoucherTemplate
        fields = VoucherTemplateSerializer.Meta.fields


__all__ = [
    'VoucherEntrySerializer',
    'VoucherEntryListSerializer',
    'VoucherEntryDetailSerializer',
    'FinanceVoucherSerializer',
    'FinanceVoucherListSerializer',
    'FinanceVoucherDetailSerializer',
    'VoucherTemplateSerializer',
    'VoucherTemplateListSerializer',
    'VoucherTemplateDetailSerializer',
]
