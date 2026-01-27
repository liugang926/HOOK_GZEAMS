"""
Serializers for Purchase Request and related models.

Provides serializers for:
- PurchaseRequestItem: Line items for purchase requests
- PurchaseRequest: Purchase request CRUD operations
"""
from rest_framework import serializers
from django.contrib.auth import get_user_model
from apps.common.serializers.base import (
    BaseModelSerializer,
    BaseModelWithAuditSerializer,
    BaseListSerializer
)
from apps.lifecycle.models import (
    PurchaseRequest,
    PurchaseRequestItem,
    PurchaseRequestStatus,
)
from apps.assets.models import AssetCategory

User = get_user_model()


# ========== Lightweight Nested Serializers ==========

class LightweightAssetCategorySerializer(serializers.ModelSerializer):
    """Lightweight category serializer for nested display."""

    class Meta:
        model = AssetCategory
        fields = ['id', 'code', 'name', 'full_name']


# ========== Purchase Request Item Serializers ==========

class PurchaseRequestItemSerializer(BaseModelSerializer):
    """Serializer for Purchase Request Item."""

    asset_category_name = serializers.CharField(
        source='asset_category.name',
        read_only=True
    )
    status_display = serializers.SerializerMethodField()

    class Meta(BaseModelSerializer.Meta):
        model = PurchaseRequestItem
        fields = BaseModelSerializer.Meta.fields + [
            'purchase_request',
            'sequence',
            'asset_category',
            'asset_category_name',
            'item_name',
            'specification',
            'brand',
            'quantity',
            'unit',
            'unit_price',
            'total_amount',
            'suggested_supplier',
            'remark',
            'status_display',
        ]

    def get_status_display(self, obj):
        """Get the purchase request status display."""
        if obj.purchase_request:
            return obj.purchase_request.get_status_display()
        return ''


class PurchaseRequestItemCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating purchase request items."""

    class Meta:
        model = PurchaseRequestItem
        fields = [
            'sequence',
            'asset_category',
            'item_name',
            'specification',
            'brand',
            'quantity',
            'unit',
            'unit_price',
            'total_amount',
            'suggested_supplier',
            'remark',
        ]

    def validate(self, data):
        """Validate and calculate total amount."""
        if 'total_amount' not in data:
            quantity = data.get('quantity', 0)
            unit_price = data.get('unit_price', 0)
            data['total_amount'] = quantity * unit_price
        return data


# ========== Purchase Request Serializers ==========

class PurchaseRequestListSerializer(BaseListSerializer):
    """Optimized serializer for purchase request list views."""

    request_no = serializers.CharField(read_only=True)
    status = serializers.CharField(read_only=True)
    status_display = serializers.CharField(
        source='get_status_display',
        read_only=True
    )
    applicant_name = serializers.CharField(
        source='applicant.username',
        read_only=True
    )
    department_name = serializers.CharField(
        source='department.name',
        read_only=True
    )
    request_date = serializers.DateField(read_only=True)
    expected_date = serializers.DateField(read_only=True)
    budget_amount = serializers.DecimalField(
        max_digits=15,
        decimal_places=2,
        read_only=True
    )
    items_count = serializers.SerializerMethodField()
    current_approver_name = serializers.CharField(
        source='current_approver.username',
        read_only=True,
        allow_null=True
    )
    approved_at = serializers.DateTimeField(read_only=True, allow_null=True)

    class Meta(BaseListSerializer.Meta):
        model = PurchaseRequest
        fields = BaseListSerializer.Meta.fields + [
            'request_no',
            'status',
            'status_display',
            'applicant',
            'applicant_name',
            'department',
            'department_name',
            'request_date',
            'expected_date',
            'budget_amount',
            'items_count',
            'current_approver',
            'current_approver_name',
            'approved_at',
        ]

    def get_items_count(self, obj):
        """Get the number of items in the request."""
        return obj.items.count()


class PurchaseRequestDetailSerializer(BaseModelWithAuditSerializer):
    """Detailed serializer for purchase request with all related data."""

    status_display = serializers.CharField(
        source='get_status_display',
        read_only=True
    )
    applicant_name = serializers.CharField(
        source='applicant.username',
        read_only=True
    )
    department_name = serializers.CharField(
        source='department.name',
        read_only=True
    )
    cost_center_id = serializers.UUIDField(read_only=True, allow_null=True)
    current_approver_name = serializers.CharField(
        source='current_approver.username',
        read_only=True,
        allow_null=True
    )
    approved_by_name = serializers.CharField(
        source='approved_by.username',
        read_only=True,
        allow_null=True
    )
    items = PurchaseRequestItemSerializer(many=True, read_only=True)
    items_count = serializers.SerializerMethodField()
    total_amount = serializers.SerializerMethodField()

    class Meta(BaseModelWithAuditSerializer.Meta):
        model = PurchaseRequest
        fields = BaseModelWithAuditSerializer.Meta.fields + [
            'request_no',
            'status',
            'status_display',
            'applicant',
            'applicant_name',
            'department',
            'department_name',
            'request_date',
            'expected_date',
            'reason',
            'budget_amount',
            'cost_center',
            'current_approver',
            'current_approver_name',
            'approved_at',
            'approved_by',
            'approved_by_name',
            'approval_comment',
            'm18_purchase_order_no',
            'pushed_to_m18_at',
            'm18_sync_status',
            'remark',
            'items',
            'items_count',
            'total_amount',
        ]
        read_only_fields = ['request_no', 'status', 'approved_at', 'm18_purchase_order_no']

    def get_items_count(self, obj):
        """Get the number of items in the request."""
        return obj.items.count()

    def get_total_amount(self, obj):
        """Calculate total amount from items."""
        return obj.calculate_total_amount()


class PurchaseRequestCreateSerializer(BaseModelSerializer):
    """Serializer for creating purchase requests."""

    items = PurchaseRequestItemCreateSerializer(many=True)

    class Meta(BaseModelSerializer.Meta):
        model = PurchaseRequest
        fields = BaseModelSerializer.Meta.fields + [
            'request_date',
            'expected_date',
            'reason',
            'budget_amount',
            'cost_center',
            'department',
            'items',
            'remark',
        ]

    def create(self, validated_data):
        """Create purchase request with items."""
        items_data = validated_data.pop('items', [])
        purchase_request = PurchaseRequest.objects.create(**validated_data)

        for item_data in items_data:
            PurchaseRequestItem.objects.create(
                purchase_request=purchase_request,
                **item_data
            )

        return purchase_request

    def update(self, instance, validated_data):
        """Update purchase request and its items."""
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
                PurchaseRequestItem.objects.create(
                    purchase_request=instance,
                    **item_data
                )

        return instance


class PurchaseRequestUpdateSerializer(BaseModelSerializer):
    """Serializer for updating purchase requests (approval workflow)."""

    class Meta(BaseModelSerializer.Meta):
        model = PurchaseRequest
        fields = BaseModelSerializer.Meta.fields + [
            'status',
            'current_approver',
            'approval_comment',
            'm18_purchase_order_no',
            'pushed_to_m18_at',
            'm18_sync_status',
        ]

    def validate_status(self, value):
        """Validate status transitions."""
        if not self.instance:
            return value

        valid_transitions = {
            PurchaseRequestStatus.DRAFT: [PurchaseRequestStatus.SUBMITTED, PurchaseRequestStatus.CANCELLED],
            PurchaseRequestStatus.SUBMITTED: [PurchaseRequestStatus.APPROVED, PurchaseRequestStatus.REJECTED, PurchaseRequestStatus.CANCELLED],
            PurchaseRequestStatus.APPROVED: [PurchaseRequestStatus.PROCESSING, PurchaseRequestStatus.CANCELLED],
            PurchaseRequestStatus.PROCESSING: [PurchaseRequestStatus.COMPLETED, PurchaseRequestStatus.CANCELLED],
            PurchaseRequestStatus.COMPLETED: [],
            PurchaseRequestStatus.REJECTED: [PurchaseRequestStatus.SUBMITTED],
            PurchaseRequestStatus.CANCELLED: [],
        }

        current_status = self.instance.status
        if value not in valid_transitions.get(current_status, []):
            raise serializers.ValidationError(
                f'Cannot transition from {current_status} to {value}'
            )

        return value
