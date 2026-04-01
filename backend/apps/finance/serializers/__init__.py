"""
Finance Module Serializers

Serializers for financial vouchers, voucher entries, and voucher templates.
"""
import re

from rest_framework import serializers
from apps.common.serializers.base import BaseModelSerializer
from apps.finance.models import FinanceVoucher, VoucherEntry, VoucherTemplate


def _humanize_object_code(value: str) -> str:
    """Convert an object code into a readable label."""
    normalized = str(value or '').strip()
    if not normalized:
        return ''
    return re.sub(r'(?<!^)(?=[A-Z])', ' ', normalized).replace('_', ' ').strip()


def _read_source_summary(voucher: FinanceVoucher) -> dict:
    """Read normalized voucher source trace data from custom fields."""
    custom_fields = voucher.custom_fields if isinstance(voucher.custom_fields, dict) else {}
    source_trace = custom_fields.get('source_trace')
    if not isinstance(source_trace, dict):
        source_trace = {}

    asset_ids = source_trace.get('asset_ids')
    if not isinstance(asset_ids, list):
        asset_ids = custom_fields.get('asset_ids')
    if not isinstance(asset_ids, list):
        asset_ids = []
    normalized_asset_ids = [str(item).strip() for item in asset_ids if str(item).strip()]

    asset_codes = source_trace.get('asset_codes')
    if not isinstance(asset_codes, list):
        asset_codes = custom_fields.get('asset_codes')
    if not isinstance(asset_codes, list):
        asset_codes = []
    normalized_asset_codes = [str(item).strip() for item in asset_codes if str(item).strip()]

    source_object_code = str(
        source_trace.get('source_object_code')
        or custom_fields.get('source_object_code')
        or ''
    ).strip()
    source_id = str(
        source_trace.get('source_id')
        or custom_fields.get('source_id')
        or ''
    ).strip()
    source_record_no = str(
        source_trace.get('source_record_no')
        or custom_fields.get('source_record_no')
        or ''
    ).strip()
    source_object_label = str(
        source_trace.get('source_object_label')
        or custom_fields.get('source_object_label')
        or _humanize_object_code(source_object_code)
    ).strip()

    return {
        'object_code': source_object_code,
        'object_label': source_object_label,
        'source_id': source_id,
        'record_no': source_record_no,
        'asset_count': len(normalized_asset_ids),
        'asset_ids': normalized_asset_ids,
        'asset_codes': normalized_asset_codes,
        'purchase_request_id': str(
            source_trace.get('source_purchase_request_id')
            or custom_fields.get('source_purchase_request_id')
            or ''
        ).strip(),
        'purchase_request_no': str(
            source_trace.get('source_purchase_request_no')
            or custom_fields.get('source_purchase_request_no')
            or ''
        ).strip(),
        'receipt_id': str(
            source_trace.get('source_receipt_id')
            or custom_fields.get('source_receipt_id')
            or ''
        ).strip(),
        'receipt_no': str(
            source_trace.get('source_receipt_no')
            or custom_fields.get('source_receipt_no')
            or ''
        ).strip(),
        'requested_business_id': str(
            source_trace.get('requested_business_id')
            or custom_fields.get('requested_business_id')
            or ''
        ).strip(),
    }


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
    source_summary = serializers.SerializerMethodField()
    source_object_code = serializers.SerializerMethodField()
    source_object_label = serializers.SerializerMethodField()
    source_id = serializers.SerializerMethodField()
    source_record_no = serializers.SerializerMethodField()
    source_asset_count = serializers.SerializerMethodField()

    class Meta(BaseModelSerializer.Meta):
        model = FinanceVoucher
        fields = BaseModelSerializer.Meta.fields + [
            'voucher_no', 'voucher_date', 'business_type',
            'summary', 'total_amount', 'status', 'notes',
            'erp_voucher_no', 'posted_at', 'posted_by',
            'source_summary', 'source_object_code', 'source_object_label',
            'source_id', 'source_record_no', 'source_asset_count',
            'entries', 'entry_count', 'is_balanced',
        ]

    def get_source_summary(self, obj):
        return _read_source_summary(obj)

    def get_source_object_code(self, obj):
        return _read_source_summary(obj).get('object_code', '')

    def get_source_object_label(self, obj):
        return _read_source_summary(obj).get('object_label', '')

    def get_source_id(self, obj):
        return _read_source_summary(obj).get('source_id', '')

    def get_source_record_no(self, obj):
        return _read_source_summary(obj).get('record_no', '')

    def get_source_asset_count(self, obj):
        return _read_source_summary(obj).get('asset_count', 0)


class FinanceVoucherListSerializer(BaseModelSerializer):
    """Lightweight voucher serializer for lists"""
    entry_count = serializers.IntegerField(source='entries.count', read_only=True)
    created_by_name = serializers.CharField(source='created_by.username', read_only=True)
    source_object_label = serializers.SerializerMethodField()
    source_record_no = serializers.SerializerMethodField()

    class Meta(BaseModelSerializer.Meta):
        model = FinanceVoucher
        fields = [
            'id', 'voucher_no', 'voucher_date', 'business_type',
            'summary', 'total_amount', 'status', 'entry_count',
            'created_by_name', 'source_object_label', 'source_record_no',
            'created_at', 'updated_at',
        ]

    def get_source_object_label(self, obj):
        return _read_source_summary(obj).get('object_label', '')

    def get_source_record_no(self, obj):
        return _read_source_summary(obj).get('record_no', '')


class FinanceVoucherDetailSerializer(FinanceVoucherSerializer):
    """Detailed voucher serializer with nested entries"""
    entries = VoucherEntryDetailSerializer(many=True, read_only=True)
    entry_count = serializers.IntegerField(source='entries.count', read_only=True)
    is_balanced = serializers.BooleanField(read_only=True)
    created_by_name = serializers.CharField(source='created_by.username', read_only=True)
    posted_by_name = serializers.CharField(source='posted_by.username', read_only=True)

    class Meta(FinanceVoucherSerializer.Meta):
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
