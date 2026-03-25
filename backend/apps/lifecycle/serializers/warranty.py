"""
Serializers for Asset Warranty model.

Provides serializers for:
- AssetWarranty: Warranty record CRUD operations
"""
from rest_framework import serializers
from django.contrib.auth import get_user_model
from apps.common.serializers.base import (
    BaseModelSerializer,
    BaseModelWithAuditSerializer,
    BaseListSerializer,
)
from apps.lifecycle.models import (
    AssetWarranty,
    AssetWarrantyStatus,
    AssetWarrantyType,
)
from apps.assets.models import Asset

User = get_user_model()


# ========== Lightweight Nested Serializers ==========

class LightweightWarrantyAssetSerializer(serializers.ModelSerializer):
    """Lightweight asset serializer for nested display."""

    class Meta:
        model = Asset
        fields = ['id', 'asset_code', 'asset_name']


# ========== Asset Warranty Serializers ==========

class AssetWarrantyListSerializer(BaseListSerializer):
    """Optimized serializer for warranty list views."""

    warranty_no = serializers.CharField(read_only=True)
    status = serializers.CharField(read_only=True)
    status_display = serializers.CharField(
        source='get_status_display',
        read_only=True
    )
    warranty_type = serializers.CharField(read_only=True)
    warranty_type_display = serializers.CharField(
        source='get_warranty_type_display',
        read_only=True
    )
    asset_code = serializers.CharField(
        source='asset.asset_code',
        read_only=True
    )
    asset_name = serializers.CharField(
        source='asset.asset_name',
        read_only=True
    )
    start_date = serializers.DateField(read_only=True)
    end_date = serializers.DateField(read_only=True)
    warranty_provider = serializers.CharField(read_only=True)
    warranty_cost = serializers.DecimalField(
        max_digits=12,
        decimal_places=2,
        read_only=True
    )
    claim_count = serializers.IntegerField(read_only=True)

    class Meta(BaseListSerializer.Meta):
        model = AssetWarranty
        fields = BaseListSerializer.Meta.fields + [
            'warranty_no',
            'status',
            'status_display',
            'warranty_type',
            'warranty_type_display',
            'asset',
            'asset_code',
            'asset_name',
            'start_date',
            'end_date',
            'warranty_provider',
            'warranty_cost',
            'claim_count',
        ]


class AssetWarrantyDetailSerializer(BaseModelWithAuditSerializer):
    """Detailed serializer for warranty with all related data."""

    status_display = serializers.CharField(
        source='get_status_display',
        read_only=True
    )
    warranty_type_display = serializers.CharField(
        source='get_warranty_type_display',
        read_only=True
    )
    asset_code = serializers.CharField(
        source='asset.asset_code',
        read_only=True
    )
    asset_name = serializers.CharField(
        source='asset.asset_name',
        read_only=True
    )

    class Meta(BaseModelWithAuditSerializer.Meta):
        model = AssetWarranty
        fields = BaseModelWithAuditSerializer.Meta.fields + [
            'warranty_no',
            'status',
            'status_display',
            'warranty_type',
            'warranty_type_display',
            'asset',
            'asset_code',
            'asset_name',
            'start_date',
            'end_date',
            'coverage_description',
            'warranty_provider',
            'provider_contact',
            'provider_phone',
            'provider_email',
            'warranty_cost',
            'purchase_request',
            'contract_no',
            'document_urls',
            'claim_count',
            'last_claim_date',
            'remark',
            'activated_at',
            'expired_at',
        ]
        read_only_fields = ['warranty_no', 'status', 'claim_count']


class AssetWarrantyCreateSerializer(BaseModelSerializer):
    """Serializer for creating warranty records."""

    class Meta(BaseModelSerializer.Meta):
        model = AssetWarranty
        fields = BaseModelSerializer.Meta.fields + [
            'warranty_type',
            'asset',
            'start_date',
            'end_date',
            'coverage_description',
            'warranty_provider',
            'provider_contact',
            'provider_phone',
            'provider_email',
            'warranty_cost',
            'purchase_request',
            'contract_no',
            'document_urls',
            'remark',
        ]


class AssetWarrantyUpdateSerializer(BaseModelSerializer):
    """Serializer for updating warranty records."""

    class Meta(BaseModelSerializer.Meta):
        model = AssetWarranty
        fields = BaseModelSerializer.Meta.fields + [
            'warranty_type',
            'start_date',
            'end_date',
            'coverage_description',
            'warranty_provider',
            'provider_contact',
            'provider_phone',
            'provider_email',
            'warranty_cost',
            'contract_no',
            'document_urls',
            'remark',
        ]
