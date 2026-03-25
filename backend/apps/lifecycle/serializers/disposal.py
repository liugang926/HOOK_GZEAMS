"""
Serializers for Disposal Request and related models.

Provides serializers for:
- DisposalItem: Line items for disposal requests with appraisal
- DisposalRequest: Disposal request CRUD operations
"""
from rest_framework import serializers
from django.contrib.auth import get_user_model
from apps.common.serializers.base import (
    BaseModelSerializer,
    BaseModelWithAuditSerializer,
    BaseListSerializer
)
from apps.lifecycle.models import (
    DisposalRequest,
    DisposalItem,
    DisposalRequestStatus,
    DisposalType,
    DisposalReason,
)
from apps.assets.models import Asset

User = get_user_model()


# ========== Lightweight Nested Serializers ==========

class LightweightAssetSerializer(serializers.ModelSerializer):
    """Lightweight asset serializer for nested display."""

    class Meta:
        model = Asset
        fields = ['id', 'asset_code', 'asset_name', 'asset_status']


# ========== Disposal Item Serializers ==========

class DisposalItemSerializer(BaseModelSerializer):
    """Serializer for Disposal Item."""

    asset_code = serializers.CharField(
        source='asset.asset_code',
        read_only=True
    )
    asset_name = serializers.CharField(
        source='asset.asset_name',
        read_only=True
    )
    asset_category_name = serializers.CharField(
        source='asset.asset_category.name',
        read_only=True
    )
    appraiser_name = serializers.CharField(
        source='appraised_by.username',
        read_only=True,
        allow_null=True
    )
    status_display = serializers.SerializerMethodField()

    class Meta(BaseModelSerializer.Meta):
        model = DisposalItem
        fields = BaseModelSerializer.Meta.fields + [
            'disposal_request',
            'sequence',
            'asset',
            'asset_code',
            'asset_name',
            'asset_category_name',
            'original_value',
            'accumulated_depreciation',
            'net_value',
            'appraisal_result',
            'residual_value',
            'appraised_by',
            'appraiser_name',
            'appraised_at',
            'disposal_executed',
            'executed_at',
            'actual_residual_value',
            'buyer_info',
            'remark',
            'status_display',
        ]

    def get_status_display(self, obj):
        """Get the disposal request status display."""
        if obj.disposal_request:
            return obj.disposal_request.get_status_display()
        return ''


class DisposalItemCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating disposal items."""

    asset_code = serializers.CharField(
        source='asset.asset_code',
        read_only=True
    )
    asset_name = serializers.CharField(
        source='asset.asset_name',
        read_only=True
    )

    class Meta:
        model = DisposalItem
        fields = [
            'sequence',
            'asset',
            'asset_code',
            'asset_name',
            'original_value',
            'accumulated_depreciation',
            'net_value',
            'remark',
        ]


class DisposalItemAppraisalSerializer(BaseModelSerializer):
    """Serializer for recording technical appraisal."""

    class Meta(BaseModelSerializer.Meta):
        model = DisposalItem
        fields = BaseModelSerializer.Meta.fields + [
            'appraisal_result',
            'residual_value',
            'appraised_by',
            'appraised_at',
        ]


class DisposalItemExecutionSerializer(BaseModelSerializer):
    """Serializer for recording disposal execution."""

    class Meta(BaseModelSerializer.Meta):
        model = DisposalItem
        fields = BaseModelSerializer.Meta.fields + [
            'disposal_executed',
            'executed_at',
            'actual_residual_value',
            'buyer_info',
        ]


# ========== Disposal Request Serializers ==========

class DisposalRequestListSerializer(BaseListSerializer):
    """Optimized serializer for disposal request list views."""

    request_no = serializers.CharField(read_only=True)
    status = serializers.CharField(read_only=True)
    status_display = serializers.CharField(
        source='get_status_display',
        read_only=True
    )
    disposal_type = serializers.CharField(read_only=True)
    disposal_type_display = serializers.CharField(
        source='get_disposal_type_display',
        read_only=True
    )
    reason_type = serializers.CharField(read_only=True)
    reason_type_display = serializers.CharField(
        source='get_reason_type_display',
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
    items_count = serializers.SerializerMethodField()
    current_approver_name = serializers.CharField(
        source='current_approver.username',
        read_only=True,
        allow_null=True
    )
    total_net_value = serializers.SerializerMethodField()

    class Meta(BaseListSerializer.Meta):
        model = DisposalRequest
        fields = BaseListSerializer.Meta.fields + [
            'request_no',
            'status',
            'status_display',
            'disposal_type',
            'disposal_type_display',
            'reason_type',
            'reason_type_display',
            'applicant',
            'applicant_name',
            'department',
            'department_name',
            'request_date',
            'items_count',
            'current_approver',
            'current_approver_name',
            'total_net_value',
        ]

    def get_items_count(self, obj):
        """Get the number of items in the request."""
        return obj.items.count()

    def get_total_net_value(self, obj):
        """Calculate total net value from items."""
        return sum(item.net_value for item in obj.items.all())


class DisposalRequestDetailSerializer(BaseModelWithAuditSerializer):
    """Detailed serializer for disposal request with all related data."""

    status_display = serializers.CharField(
        source='get_status_display',
        read_only=True
    )
    disposal_type_display = serializers.CharField(
        source='get_disposal_type_display',
        read_only=True
    )
    reason_type_display = serializers.CharField(
        source='get_reason_type_display',
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
    current_approver_name = serializers.CharField(
        source='current_approver.username',
        read_only=True,
        allow_null=True
    )
    items = DisposalItemSerializer(many=True, read_only=True)
    items_count = serializers.SerializerMethodField()
    total_net_value = serializers.SerializerMethodField()
    total_residual_value = serializers.SerializerMethodField()

    class Meta(BaseModelWithAuditSerializer.Meta):
        model = DisposalRequest
        fields = BaseModelWithAuditSerializer.Meta.fields + [
            'request_no',
            'status',
            'status_display',
            'disposal_type',
            'disposal_type_display',
            'applicant',
            'applicant_name',
            'department',
            'department_name',
            'request_date',
            'disposal_reason',
            'reason_type',
            'reason_type_display',
            'current_approver',
            'current_approver_name',
            'remark',
            'items',
            'items_count',
            'total_net_value',
            'total_residual_value',
        ]
        read_only_fields = ['request_no', 'status']

    def get_items_count(self, obj):
        """Get the number of items in the request."""
        return obj.items.count()

    def get_total_net_value(self, obj):
        """Calculate total net value from items."""
        return sum(item.net_value for item in obj.items.all())

    def get_total_residual_value(self, obj):
        """Calculate total residual value from appraised items."""
        total = 0
        for item in obj.items.all():
            if item.residual_value:
                total += item.residual_value
        return total


class DisposalRequestCreateSerializer(BaseModelSerializer):
    """Serializer for creating disposal requests."""

    items = DisposalItemCreateSerializer(many=True)

    class Meta(BaseModelSerializer.Meta):
        model = DisposalRequest
        fields = BaseModelSerializer.Meta.fields + [
            'disposal_type',
            'department',
            'request_date',
            'disposal_reason',
            'reason_type',
            'remark',
            'items',
        ]

    def create(self, validated_data):
        """Create disposal request with items."""
        items_data = validated_data.pop('items', [])
        request = self.context.get('request')

        # Set applicant from context
        if request and request.user:
            validated_data['applicant'] = request.user

        disposal_request = DisposalRequest.objects.create(**validated_data)

        for item_data in items_data:
            DisposalItem.objects.create(
                disposal_request=disposal_request,
                **item_data
            )

        return disposal_request

    def update(self, instance, validated_data):
        """Update disposal request and its items."""
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
                DisposalItem.objects.create(
                    disposal_request=instance,
                    **item_data
                )

        return instance


class DisposalRequestUpdateSerializer(BaseModelSerializer):
    """Serializer for updating disposal requests (approval workflow)."""

    class Meta(BaseModelSerializer.Meta):
        model = DisposalRequest
        fields = BaseModelSerializer.Meta.fields + [
            'status',
            'current_approver',
        ]

    def validate_status(self, value):
        """Validate status transitions."""
        if not self.instance:
            return value

        valid_transitions = {
            DisposalRequestStatus.DRAFT: [DisposalRequestStatus.SUBMITTED, DisposalRequestStatus.CANCELLED],
            DisposalRequestStatus.SUBMITTED: [DisposalRequestStatus.APPRAISING, DisposalRequestStatus.REJECTED, DisposalRequestStatus.CANCELLED],
            DisposalRequestStatus.APPRAISING: [DisposalRequestStatus.APPROVED, DisposalRequestStatus.REJECTED, DisposalRequestStatus.CANCELLED],
            DisposalRequestStatus.APPROVED: [DisposalRequestStatus.EXECUTING, DisposalRequestStatus.CANCELLED],
            DisposalRequestStatus.EXECUTING: [DisposalRequestStatus.COMPLETED],
            DisposalRequestStatus.COMPLETED: [],
            DisposalRequestStatus.REJECTED: [DisposalRequestStatus.SUBMITTED],
            DisposalRequestStatus.CANCELLED: [],
        }

        current_status = self.instance.status
        if value not in valid_transitions.get(current_status, []):
            raise serializers.ValidationError(
                f'Cannot transition from {current_status} to {value}'
            )

        return value
