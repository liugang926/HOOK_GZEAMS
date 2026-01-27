"""
Serializers for Asset Receipt and related models.

Provides serializers for:
- AssetReceiptItem: Line items for asset receipts
- AssetReceipt: Asset receipt and quality inspection CRUD operations
"""
from rest_framework import serializers
from django.contrib.auth import get_user_model
from apps.common.serializers.base import (
    BaseModelSerializer,
    BaseModelWithAuditSerializer,
    BaseListSerializer
)
from apps.lifecycle.models import (
    AssetReceipt,
    AssetReceiptItem,
    AssetReceiptStatus,
    PurchaseRequest,
)
from apps.assets.models import AssetCategory
from apps.lifecycle.serializers.purchase import LightweightAssetCategorySerializer

User = get_user_model()


# ========== Lightweight Nested Serializers ==========

class LightweightPurchaseRequestSerializer(serializers.ModelSerializer):
    """Lightweight purchase request serializer for nested display."""

    class Meta:
        model = PurchaseRequest
        fields = ['id', 'request_no', 'status']


# ========== Asset Receipt Item Serializers ==========

class AssetReceiptItemSerializer(BaseModelSerializer):
    """Serializer for Asset Receipt Item."""

    asset_category_name = serializers.CharField(
        source='asset_category.name',
        read_only=True
    )
    asset_category_code = serializers.CharField(
        source='asset_category.code',
        read_only=True
    )
    status_display = serializers.SerializerMethodField()

    class Meta(BaseModelSerializer.Meta):
        model = AssetReceiptItem
        fields = BaseModelSerializer.Meta.fields + [
            'asset_receipt',
            'sequence',
            'asset_category',
            'asset_category_name',
            'asset_category_code',
            'item_name',
            'specification',
            'brand',
            'ordered_quantity',
            'received_quantity',
            'qualified_quantity',
            'defective_quantity',
            'unit_price',
            'total_amount',
            'asset_generated',
            'remark',
            'status_display',
        ]

    def get_status_display(self, obj):
        """Get the asset receipt status display."""
        if obj.asset_receipt:
            return obj.asset_receipt.get_status_display()
        return ''


class AssetReceiptItemCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating asset receipt items."""

    class Meta:
        model = AssetReceiptItem
        fields = [
            'sequence',
            'asset_category',
            'item_name',
            'specification',
            'brand',
            'ordered_quantity',
            'received_quantity',
            'qualified_quantity',
            'defective_quantity',
            'unit_price',
            'total_amount',
            'remark',
        ]

    def validate(self, data):
        """Validate receipt item data."""
        received_quantity = data.get('received_quantity', 0)
        qualified_quantity = data.get('qualified_quantity', 0)

        # Calculate defective quantity if not set
        if 'defective_quantity' not in data:
            data['defective_quantity'] = received_quantity - qualified_quantity

        # Calculate total amount if not set
        if 'total_amount' not in data:
            unit_price = data.get('unit_price', 0)
            data['total_amount'] = received_quantity * unit_price

        # Validate qualified quantity
        if qualified_quantity > received_quantity:
            raise serializers.ValidationError({
                'qualified_quantity': 'Qualified quantity cannot exceed received quantity.'
            })

        return data


# ========== Asset Receipt Serializers ==========

class AssetReceiptListSerializer(BaseListSerializer):
    """Optimized serializer for asset receipt list views."""

    receipt_no = serializers.CharField(read_only=True)
    status = serializers.CharField(read_only=True)
    status_display = serializers.CharField(
        source='get_status_display',
        read_only=True
    )
    receipt_date = serializers.DateField(read_only=True)
    receipt_type = serializers.CharField(read_only=True)
    receipt_type_display = serializers.CharField(
        source='get_receipt_type_display',
        read_only=True
    )
    supplier = serializers.CharField(read_only=True, allow_null=True)
    receiver_name = serializers.CharField(
        source='receiver.username',
        read_only=True
    )
    inspector_name = serializers.CharField(
        source='inspector.username',
        read_only=True,
        allow_null=True
    )
    items_count = serializers.SerializerMethodField()
    passed_at = serializers.DateTimeField(read_only=True, allow_null=True)
    purchase_request_no = serializers.CharField(
        source='purchase_request.request_no',
        read_only=True,
        allow_null=True
    )

    class Meta(BaseListSerializer.Meta):
        model = AssetReceipt
        fields = BaseListSerializer.Meta.fields + [
            'receipt_no',
            'status',
            'status_display',
            'receipt_date',
            'receipt_type',
            'receipt_type_display',
            'supplier',
            'delivery_no',
            'receiver',
            'receiver_name',
            'inspector',
            'inspector_name',
            'items_count',
            'passed_at',
            'purchase_request',
            'purchase_request_no',
        ]

    def get_items_count(self, obj):
        """Get the number of items in the receipt."""
        return obj.items.count()


class AssetReceiptDetailSerializer(BaseModelWithAuditSerializer):
    """Detailed serializer for asset receipt with all related data."""

    status_display = serializers.CharField(
        source='get_status_display',
        read_only=True
    )
    receipt_type_display = serializers.CharField(
        source='get_receipt_type_display',
        read_only=True
    )
    purchase_request = LightweightPurchaseRequestSerializer(read_only=True)
    receiver_name = serializers.CharField(
        source='receiver.username',
        read_only=True
    )
    inspector_name = serializers.CharField(
        source='inspector.username',
        read_only=True,
        allow_null=True
    )
    items = AssetReceiptItemSerializer(many=True, read_only=True)
    items_count = serializers.SerializerMethodField()
    total_amount = serializers.SerializerMethodField()

    class Meta(BaseModelWithAuditSerializer.Meta):
        model = AssetReceipt
        fields = BaseModelWithAuditSerializer.Meta.fields + [
            'receipt_no',
            'status',
            'status_display',
            'purchase_request',
            'm18_purchase_order_no',
            'receipt_date',
            'receipt_type',
            'receipt_type_display',
            'supplier',
            'delivery_no',
            'receiver',
            'receiver_name',
            'inspector',
            'inspector_name',
            'inspection_result',
            'passed_at',
            'remark',
            'items',
            'items_count',
            'total_amount',
        ]
        read_only_fields = ['receipt_no', 'status']

    def get_items_count(self, obj):
        """Get the number of items in the receipt."""
        return obj.items.count()

    def get_total_amount(self, obj):
        """Calculate total amount from items."""
        return sum(item.total_amount for item in obj.items.all())


class AssetReceiptCreateSerializer(BaseModelSerializer):
    """Serializer for creating asset receipts."""

    items = AssetReceiptItemCreateSerializer(many=True)

    class Meta(BaseModelSerializer.Meta):
        model = AssetReceipt
        fields = BaseModelSerializer.Meta.fields + [
            'purchase_request',
            'm18_purchase_order_no',
            'receipt_date',
            'receipt_type',
            'supplier',
            'delivery_no',
            'receiver',
            'inspector',
            'remark',
            'items',
        ]

    def create(self, validated_data):
        """Create asset receipt with items."""
        items_data = validated_data.pop('items', [])
        asset_receipt = AssetReceipt.objects.create(**validated_data)

        for item_data in items_data:
            AssetReceiptItem.objects.create(
                asset_receipt=asset_receipt,
                **item_data
            )

        return asset_receipt

    def update(self, instance, validated_data):
        """Update asset receipt and its items."""
        items_data = validated_data.pop('items', None)

        # Update basic fields
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        # Update items if provided
        if items_data is not None:
            # Delete existing items
            instance.items.all().delete()

            # Create new items
            for item_data in items_data:
                AssetReceiptItem.objects.create(
                    asset_receipt=instance,
                    **item_data
                )

        return instance


class AssetReceiptInspectionSerializer(BaseModelSerializer):
    """Serializer for recording inspection results."""

    class Meta(BaseModelSerializer.Meta):
        model = AssetReceipt
        fields = BaseModelSerializer.Meta.fields + [
            'status',
            'inspector',
            'inspection_result',
            'passed_at',
        ]

    def validate_status(self, value):
        """Validate status is either passed or rejected."""
        if value not in [AssetReceiptStatus.PASSED, AssetReceiptStatus.REJECTED]:
            raise serializers.ValidationError(
                'Status must be either passed or rejected after inspection.'
            )
        return value
