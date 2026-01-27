from rest_framework import serializers
from apps.common.serializers.base import BaseModelSerializer
from apps.depreciation.models import DepreciationConfig, DepreciationRecord, DepreciationRun


class DepreciationConfigSerializer(BaseModelSerializer):
    """Depreciation Configuration Serializer"""

    category_name = serializers.CharField(source='category.name', read_only=True)
    category_code = serializers.CharField(source='category.code', read_only=True)
    monthly_rate = serializers.FloatField(read_only=True)

    class Meta(BaseModelSerializer.Meta):
        model = DepreciationConfig
        fields = BaseModelSerializer.Meta.fields + [
            'category', 'category_name', 'category_code',
            'depreciation_method', 'useful_life', 'salvage_value_rate',
            'monthly_rate', 'is_active', 'notes',
        ]


class DepreciationConfigListSerializer(BaseModelSerializer):
    """Lightweight serializer for list views"""

    category_name = serializers.CharField(source='category.name', read_only=True)
    depreciation_method_display = serializers.CharField(source='get_depreciation_method_display', read_only=True)

    class Meta(BaseModelSerializer.Meta):
        model = DepreciationConfig
        fields = [
            'id', 'category', 'category_name', 'depreciation_method',
            'depreciation_method_display', 'useful_life', 'salvage_value_rate',
            'is_active', 'created_at', 'updated_at',
        ]


class DepreciationConfigDetailSerializer(BaseModelSerializer):
    """Detailed configuration serializer"""

    category_name = serializers.CharField(source='category.name', read_only=True)
    category_code = serializers.CharField(source='category.code', read_only=True)
    category_parent_name = serializers.CharField(source='category.parent.name', read_only=True, allow_null=True)
    depreciation_method_display = serializers.CharField(source='get_depreciation_method_display', read_only=True)
    monthly_rate = serializers.FloatField(read_only=True)

    class Meta(BaseModelSerializer.Meta):
        model = DepreciationConfig
        fields = DepreciationConfigSerializer.Meta.fields + [
            'category_parent_name', 'depreciation_method_display',
        ]


class DepreciationRecordSerializer(BaseModelSerializer):
    """Depreciation Record Serializer"""

    asset_code = serializers.CharField(source='asset.asset_code', read_only=True)
    asset_name = serializers.CharField(source='asset.asset_name', read_only=True)
    category_name = serializers.CharField(source='asset.asset_category.name', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)

    class Meta(BaseModelSerializer.Meta):
        model = DepreciationRecord
        fields = BaseModelSerializer.Meta.fields + [
            'asset', 'asset_code', 'asset_name', 'category_name',
            'period', 'depreciation_amount', 'accumulated_amount',
            'net_value', 'status', 'status_display', 'post_date',
            'notes',
        ]


class DepreciationRecordListSerializer(BaseModelSerializer):
    """Lightweight record serializer for lists"""

    asset_code = serializers.CharField(source='asset.asset_code', read_only=True)
    asset_name = serializers.CharField(source='asset.asset_name', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)

    class Meta(BaseModelSerializer.Meta):
        model = DepreciationRecord
        fields = [
            'id', 'asset', 'asset_code', 'asset_name',
            'period', 'depreciation_amount', 'net_value',
            'status', 'status_display', 'post_date',
            'created_at', 'updated_at',
        ]


class DepreciationRecordDetailSerializer(BaseModelSerializer):
    """Detailed record serializer"""

    asset_code = serializers.CharField(source='asset.asset_code', read_only=True)
    asset_name = serializers.CharField(source='asset.asset_name', read_only=True)
    category_name = serializers.CharField(source='asset.asset_category.name', read_only=True)
    original_cost = serializers.DecimalField(source='asset.original_cost', max_digits=14, decimal_places=2, read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)

    class Meta(BaseModelSerializer.Meta):
        model = DepreciationRecord
        fields = DepreciationRecordSerializer.Meta.fields + [
            'category_name', 'original_cost', 'status_display',
        ]


class DepreciationRunSerializer(BaseModelSerializer):
    """Depreciation Run Serializer"""

    status_display = serializers.CharField(source='get_status_display', read_only=True)
    success_count = serializers.IntegerField(read_only=True)
    failed_count = serializers.IntegerField(read_only=True)

    class Meta(BaseModelSerializer.Meta):
        model = DepreciationRun
        fields = BaseModelSerializer.Meta.fields + [
            'period', 'run_date', 'status', 'status_display',
            'total_assets', 'total_amount', 'error_message',
            'success_count', 'failed_count', 'notes',
        ]


class DepreciationRunListSerializer(BaseModelSerializer):
    """Lightweight run serializer for lists"""

    status_display = serializers.CharField(source='get_status_display', read_only=True)

    class Meta(BaseModelSerializer.Meta):
        model = DepreciationRun
        fields = [
            'id', 'period', 'run_date', 'status', 'status_display',
            'total_assets', 'total_amount', 'created_at', 'updated_at',
        ]


class DepreciationRunDetailSerializer(BaseModelSerializer):
    """Detailed run serializer with statistics"""

    status_display = serializers.CharField(source='get_status_display', read_only=True)
    success_count = serializers.IntegerField(read_only=True)
    failed_count = serializers.IntegerField(read_only=True)

    class Meta(BaseModelSerializer.Meta):
        model = DepreciationRun
        fields = DepreciationRunSerializer.Meta.fields + [
            'status_display',
        ]


__all__ = [
    'DepreciationConfigSerializer',
    'DepreciationConfigListSerializer',
    'DepreciationConfigDetailSerializer',
    'DepreciationRecordSerializer',
    'DepreciationRecordListSerializer',
    'DepreciationRecordDetailSerializer',
    'DepreciationRunSerializer',
    'DepreciationRunListSerializer',
    'DepreciationRunDetailSerializer',
]
