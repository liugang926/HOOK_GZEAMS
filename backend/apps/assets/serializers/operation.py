"""
Serializers for Asset Operation Models (Pickup, Transfer, Return, Loan).

All serializers inherit from BaseModelSerializer for automatic serialization
of common fields (id, organization, is_deleted, created_at, etc.).
"""
from rest_framework import serializers
from apps.common.serializers.base import (
    BaseModelSerializer,
    BaseModelWithAuditSerializer,
    BaseListSerializer,
    UserSerializer
)
from apps.assets.models import (
    AssetPickup,
    PickupItem,
    AssetTransfer,
    TransferItem,
    AssetReturn,
    ReturnItem,
    AssetLoan,
    LoanItem,
    Asset,
    Location,
)
from apps.organizations.models import Department
from apps.accounts.models import User


# ========== Department and User Serializers ==========

class LightweightDepartmentSerializer(serializers.ModelSerializer):
    """Lightweight department serializer for nested display"""
    class Meta:
        model = Department
        fields = ['id', 'name', 'code']


class ExtendedUserSerializer(UserSerializer):
    """Extended user serializer with real_name field"""
    real_name = serializers.CharField(source='get_full_name', read_only=True)

    class Meta(UserSerializer.Meta):
        fields = UserSerializer.Meta.fields + ['real_name']


# ========== Asset Serializers for Operations ==========

class LightweightAssetSerializer(serializers.ModelSerializer):
    """Lightweight asset serializer for operation items"""
    asset_code = serializers.CharField(read_only=True)
    asset_name = serializers.CharField(read_only=True)
    asset_status = serializers.CharField(read_only=True)
    asset_status_display = serializers.CharField(source='get_asset_status_display', read_only=True)

    class Meta:
        model = Asset
        fields = ['id', 'asset_code', 'asset_name', 'asset_status', 'asset_status_display']


class LightweightLocationSerializer(serializers.ModelSerializer):
    """Lightweight location serializer for nested display"""
    class Meta:
        model = Location
        fields = ['id', 'name', 'path', 'location_type']


# ========== Pickup Order Serializers ==========

class PickupItemSerializer(BaseModelSerializer):
    """Serializer for pickup order line items"""
    asset = LightweightAssetSerializer(read_only=True)
    asset_id = serializers.UUIDField(write_only=True)
    snapshot_original_location = LightweightLocationSerializer(read_only=True)
    snapshot_original_custodian = ExtendedUserSerializer(read_only=True)

    class Meta(BaseModelSerializer.Meta):
        model = PickupItem
        fields = BaseModelSerializer.Meta.fields + [
            'asset', 'asset_id', 'quantity', 'remark',
            'snapshot_original_location', 'snapshot_original_custodian'
        ]


class PickupItemListSerializer(BaseModelSerializer):
    """Optimized serializer for pickup items in list views"""
    asset_id = serializers.UUIDField(read_only=True)
    asset_name = serializers.CharField(source='asset.asset_name', read_only=True)
    asset_code = serializers.CharField(source='asset.asset_code', read_only=True)

    class Meta(BaseModelSerializer.Meta):
        model = PickupItem
        fields = BaseModelSerializer.Meta.fields + [
            'asset_id', 'asset_name', 'asset_code', 'quantity', 'remark'
        ]


class AssetPickupListSerializer(BaseListSerializer):
    """Optimized serializer for pickup order list views"""
    pickup_no = serializers.CharField(read_only=True)
    applicant = ExtendedUserSerializer(read_only=True)
    department = LightweightDepartmentSerializer(read_only=True)
    pickup_date = serializers.DateField(read_only=True)
    status = serializers.CharField(read_only=True)
    status_label = serializers.CharField(source='get_status_label', read_only=True)
    items_count = serializers.SerializerMethodField()

    class Meta(BaseListSerializer.Meta):
        model = AssetPickup
        fields = BaseListSerializer.Meta.fields + [
            'pickup_no', 'applicant', 'department', 'pickup_date',
            'pickup_reason', 'status', 'status_label', 'items_count',
            'approved_at', 'completed_at'
        ]

    def get_items_count(self, obj):
        """Get count of items in the pickup order"""
        return obj.items.count()


class AssetPickupDetailSerializer(BaseModelWithAuditSerializer):
    """Full detail serializer for pickup orders"""
    pickup_no = serializers.CharField(read_only=True)
    applicant = ExtendedUserSerializer(read_only=True)
    department = LightweightDepartmentSerializer(read_only=True)
    status = serializers.CharField(read_only=True)
    status_label = serializers.CharField(source='get_status_label', read_only=True)
    approved_by = ExtendedUserSerializer(read_only=True)
    items = PickupItemSerializer(many=True, read_only=True)
    items_count = serializers.SerializerMethodField()

    # Write-only fields for creation
    department_id = serializers.UUIDField(write_only=True, required=False)
    applicant_id = serializers.UUIDField(write_only=True, required=False)

    class Meta(BaseModelWithAuditSerializer.Meta):
        model = AssetPickup
        fields = BaseModelWithAuditSerializer.Meta.fields + [
            'pickup_no', 'applicant', 'applicant_id', 'department', 'department_id',
            'pickup_date', 'pickup_reason', 'status', 'status_label',
            'approved_by', 'approved_at', 'approval_comment',
            'completed_at', 'items', 'items_count'
        ]
        read_only_fields = ['pickup_no', 'approved_at', 'completed_at']

    def get_items_count(self, obj):
        """Get count of items in the pickup order"""
        return obj.items.count()


class AssetPickupCreateSerializer(BaseModelSerializer):
    """Serializer for creating pickup orders with items"""
    items = serializers.ListField(
        child=serializers.DictField(),
        write_only=True,
        required=True,
        help_text='List of items with asset_id and optional quantity/remark'
    )

    class Meta(BaseModelSerializer.Meta):
        model = AssetPickup
        fields = BaseModelSerializer.Meta.fields + [
            'department', 'pickup_date', 'pickup_reason', 'items'
        ]

    def create(self, validated_data):
        """Create pickup order with items"""
        items_data = validated_data.pop('items')
        pickup = AssetPickup.objects.create(**validated_data)

        # Create pickup items with snapshots
        for item_data in items_data:
            asset_id = item_data.get('asset_id')
            try:
                asset = Asset.objects.get(id=asset_id)
                PickupItem.objects.create(
                    pickup=pickup,
                    asset=asset,
                    quantity=item_data.get('quantity', 1),
                    remark=item_data.get('remark', ''),
                    snapshot_original_location=asset.location,
                    snapshot_original_custodian=asset.custodian
                )
            except Asset.DoesNotExist:
                pass  # Skip invalid assets

        return pickup


class AssetPickupUpdateSerializer(BaseModelSerializer):
    """Serializer for updating pickup orders"""

    class Meta(BaseModelSerializer.Meta):
        model = AssetPickup
        fields = BaseModelSerializer.Meta.fields + [
            'department', 'pickup_date', 'pickup_reason'
        ]


class PickupApprovalSerializer(serializers.Serializer):
    """Serializer for pickup approval action"""
    approval = serializers.ChoiceField(
        choices=['approved', 'rejected'],
        required=True,
        help_text='Approval decision'
    )
    comment = serializers.CharField(
        required=False,
        allow_blank=True,
        help_text='Approval comment'
    )


# ========== Transfer Order Serializers ==========

class TransferItemSerializer(BaseModelSerializer):
    """Serializer for transfer order line items"""
    asset = LightweightAssetSerializer(read_only=True)
    asset_id = serializers.UUIDField(write_only=True)
    from_location = LightweightLocationSerializer(read_only=True)
    from_custodian = ExtendedUserSerializer(read_only=True)
    to_location = LightweightLocationSerializer(read_only=True)
    to_location_id = serializers.UUIDField(write_only=True, required=False, allow_null=True)

    class Meta(BaseModelSerializer.Meta):
        model = TransferItem
        fields = BaseModelSerializer.Meta.fields + [
            'asset', 'asset_id', 'from_location', 'from_custodian',
            'to_location', 'to_location_id', 'remark'
        ]


class TransferItemListSerializer(BaseModelSerializer):
    """Optimized serializer for transfer items in list views"""
    asset_id = serializers.UUIDField(read_only=True)
    asset_name = serializers.CharField(source='asset.asset_name', read_only=True)
    asset_code = serializers.CharField(source='asset.asset_code', read_only=True)

    class Meta(BaseModelSerializer.Meta):
        model = TransferItem
        fields = BaseModelSerializer.Meta.fields + [
            'asset_id', 'asset_name', 'asset_code', 'remark'
        ]


class AssetTransferListSerializer(BaseListSerializer):
    """Optimized serializer for transfer order list views"""
    transfer_no = serializers.CharField(read_only=True)
    from_department = LightweightDepartmentSerializer(read_only=True)
    to_department = LightweightDepartmentSerializer(read_only=True)
    transfer_date = serializers.DateField(read_only=True)
    status = serializers.CharField(read_only=True)
    status_label = serializers.CharField(source='get_status_label', read_only=True)
    items_count = serializers.SerializerMethodField()

    class Meta(BaseListSerializer.Meta):
        model = AssetTransfer
        fields = BaseListSerializer.Meta.fields + [
            'transfer_no', 'from_department', 'to_department',
            'transfer_date', 'transfer_reason', 'status', 'status_label',
            'items_count', 'from_approved_at', 'to_approved_at', 'completed_at'
        ]

    def get_items_count(self, obj):
        """Get count of items in the transfer order"""
        return obj.items.count()


class AssetTransferDetailSerializer(BaseModelWithAuditSerializer):
    """Full detail serializer for transfer orders"""
    transfer_no = serializers.CharField(read_only=True)
    from_department = LightweightDepartmentSerializer(read_only=True)
    to_department = LightweightDepartmentSerializer(read_only=True)
    status = serializers.CharField(read_only=True)
    status_label = serializers.CharField(source='get_status_label', read_only=True)
    from_approved_by = ExtendedUserSerializer(read_only=True)
    to_approved_by = ExtendedUserSerializer(read_only=True)
    items = TransferItemSerializer(many=True, read_only=True)
    items_count = serializers.SerializerMethodField()

    # Write-only fields
    from_department_id = serializers.UUIDField(write_only=True, required=False)
    to_department_id = serializers.UUIDField(write_only=True, required=False)

    class Meta(BaseModelWithAuditSerializer.Meta):
        model = AssetTransfer
        fields = BaseModelWithAuditSerializer.Meta.fields + [
            'transfer_no', 'from_department', 'from_department_id',
            'to_department', 'to_department_id', 'transfer_date',
            'transfer_reason', 'status', 'status_label',
            'from_approved_by', 'from_approved_at', 'from_approve_comment',
            'to_approved_by', 'to_approved_at', 'to_approve_comment',
            'completed_at', 'items', 'items_count'
        ]
        read_only_fields = ['transfer_no', 'from_approved_at', 'to_approved_at', 'completed_at']

    def get_items_count(self, obj):
        """Get count of items in the transfer order"""
        return obj.items.count()


class AssetTransferCreateSerializer(BaseModelSerializer):
    """Serializer for creating transfer orders with items"""
    items = serializers.ListField(
        child=serializers.DictField(),
        write_only=True,
        required=True
    )

    class Meta(BaseModelSerializer.Meta):
        model = AssetTransfer
        fields = BaseModelSerializer.Meta.fields + [
            'from_department', 'to_department', 'transfer_date',
            'transfer_reason', 'items'
        ]

    def validate(self, data):
        """Validate that from and to departments are different"""
        if data.get('from_department') == data.get('to_department'):
            raise serializers.ValidationError({
                'to_department': 'Source and target departments must be different'
            })
        return data

    def create(self, validated_data):
        """Create transfer order with items"""
        items_data = validated_data.pop('items')
        transfer = AssetTransfer.objects.create(**validated_data)

        # Create transfer items with snapshots
        for item_data in items_data:
            asset_id = item_data.get('asset_id')
            try:
                asset = Asset.objects.get(id=asset_id)
                TransferItem.objects.create(
                    transfer=transfer,
                    asset=asset,
                    from_location=asset.location,
                    from_custodian=asset.custodian,
                    to_location_id=item_data.get('to_location_id'),
                    remark=item_data.get('remark', '')
                )
            except Asset.DoesNotExist:
                pass

        return transfer


class TransferApprovalSerializer(serializers.Serializer):
    """Serializer for transfer approval action"""
    comment = serializers.CharField(
        required=False,
        allow_blank=True,
        help_text='Approval comment'
    )


# ========== Return Order Serializers ==========

class ReturnItemSerializer(BaseModelSerializer):
    """Serializer for return order line items"""
    asset = LightweightAssetSerializer(read_only=True)
    asset_id = serializers.UUIDField(write_only=True)
    asset_status_display = serializers.CharField(source='get_asset_status_display', read_only=True)

    class Meta(BaseModelSerializer.Meta):
        model = ReturnItem
        fields = BaseModelSerializer.Meta.fields + [
            'asset', 'asset_id', 'asset_status', 'asset_status_display',
            'condition_description', 'remark'
        ]


class ReturnItemListSerializer(BaseModelSerializer):
    """Optimized serializer for return items in list views"""
    asset_id = serializers.UUIDField(read_only=True)
    asset_name = serializers.CharField(source='asset.asset_name', read_only=True)
    asset_code = serializers.CharField(source='asset.asset_code', read_only=True)

    class Meta(BaseModelSerializer.Meta):
        model = ReturnItem
        fields = BaseModelSerializer.Meta.fields + [
            'asset_id', 'asset_name', 'asset_code', 'asset_status'
        ]


class AssetReturnListSerializer(BaseListSerializer):
    """Optimized serializer for return order list views"""
    return_no = serializers.CharField(read_only=True)
    returner = ExtendedUserSerializer(read_only=True)
    return_date = serializers.DateField(read_only=True)
    return_location = LightweightLocationSerializer(read_only=True)
    status = serializers.CharField(read_only=True)
    status_label = serializers.CharField(source='get_status_label', read_only=True)
    items_count = serializers.SerializerMethodField()

    class Meta(BaseListSerializer.Meta):
        model = AssetReturn
        fields = BaseListSerializer.Meta.fields + [
            'return_no', 'returner', 'return_date', 'return_reason',
            'return_location', 'status', 'status_label', 'items_count',
            'confirmed_at', 'completed_at'
        ]

    def get_items_count(self, obj):
        """Get count of items in the return order"""
        return obj.items.count()


class AssetReturnDetailSerializer(BaseModelWithAuditSerializer):
    """Full detail serializer for return orders"""
    return_no = serializers.CharField(read_only=True)
    returner = ExtendedUserSerializer(read_only=True)
    return_location = LightweightLocationSerializer(read_only=True)
    status = serializers.CharField(read_only=True)
    status_label = serializers.CharField(source='get_status_label', read_only=True)
    confirmed_by = ExtendedUserSerializer(read_only=True)
    items = ReturnItemSerializer(many=True, read_only=True)
    items_count = serializers.SerializerMethodField()

    # Write-only fields
    return_location_id = serializers.UUIDField(write_only=True, required=False)

    class Meta(BaseModelWithAuditSerializer.Meta):
        model = AssetReturn
        fields = BaseModelWithAuditSerializer.Meta.fields + [
            'return_no', 'returner', 'return_date', 'return_reason',
            'return_location', 'return_location_id', 'status', 'status_label',
            'confirmed_by', 'confirmed_at', 'reject_reason',
            'completed_at', 'items', 'items_count'
        ]
        read_only_fields = ['return_no', 'confirmed_at', 'completed_at']

    def get_items_count(self, obj):
        """Get count of items in the return order"""
        return obj.items.count()


class AssetReturnCreateSerializer(BaseModelSerializer):
    """Serializer for creating return orders with items"""
    items = serializers.ListField(
        child=serializers.DictField(),
        write_only=True,
        required=True
    )

    class Meta(BaseModelSerializer.Meta):
        model = AssetReturn
        fields = BaseModelSerializer.Meta.fields + [
            'return_date', 'return_reason', 'return_location', 'items'
        ]

    def create(self, validated_data):
        """Create return order with items"""
        items_data = validated_data.pop('items')
        return_order = AssetReturn.objects.create(**validated_data)

        # Create return items
        for item_data in items_data:
            asset_id = item_data.get('asset_id')
            try:
                asset = Asset.objects.get(id=asset_id)
                ReturnItem.objects.create(
                    asset_return=return_order,
                    asset=asset,
                    asset_status=item_data.get('asset_status', 'idle'),
                    condition_description=item_data.get('condition_description', ''),
                    remark=item_data.get('remark', '')
                )
            except Asset.DoesNotExist:
                pass

        return return_order


class ReturnConfirmSerializer(serializers.Serializer):
    """Serializer for return confirmation action"""
    status = serializers.ChoiceField(
        choices=['approved', 'rejected'],
        required=True
    )
    reason = serializers.CharField(
        required=False,
        allow_blank=True,
        help_text='Reason for rejection (if rejected)'
    )


# ========== Loan Order Serializers ==========

class LoanItemSerializer(BaseModelSerializer):
    """Serializer for loan order line items"""
    asset = LightweightAssetSerializer(read_only=True)
    asset_id = serializers.UUIDField(write_only=True)

    class Meta(BaseModelSerializer.Meta):
        model = LoanItem
        fields = BaseModelSerializer.Meta.fields + ['asset', 'asset_id', 'remark']


class LoanItemListSerializer(BaseModelSerializer):
    """Optimized serializer for loan items in list views"""
    asset_id = serializers.UUIDField(read_only=True)
    asset_name = serializers.CharField(source='asset.asset_name', read_only=True)
    asset_code = serializers.CharField(source='asset.asset_code', read_only=True)

    class Meta(BaseModelSerializer.Meta):
        model = LoanItem
        fields = BaseModelSerializer.Meta.fields + [
            'asset_id', 'asset_name', 'asset_code'
        ]


class AssetLoanListSerializer(BaseListSerializer):
    """Optimized serializer for loan order list views"""
    loan_no = serializers.CharField(read_only=True)
    borrower = ExtendedUserSerializer(read_only=True)
    borrow_date = serializers.DateField(read_only=True)
    expected_return_date = serializers.DateField(read_only=True)
    actual_return_date = serializers.DateField(read_only=True)
    status = serializers.CharField(read_only=True)
    status_label = serializers.CharField(source='get_status_label', read_only=True)
    items_count = serializers.SerializerMethodField()
    is_overdue = serializers.SerializerMethodField()

    class Meta(BaseListSerializer.Meta):
        model = AssetLoan
        fields = BaseListSerializer.Meta.fields + [
            'loan_no', 'borrower', 'borrow_date', 'expected_return_date',
            'actual_return_date', 'loan_reason', 'status', 'status_label',
            'items_count', 'is_overdue', 'approved_at', 'lent_at', 'returned_at'
        ]

    def get_items_count(self, obj):
        """Get count of items in the loan order"""
        return obj.items.count()

    def get_is_overdue(self, obj):
        """Check if loan is overdue"""
        return obj.is_overdue()


class AssetLoanDetailSerializer(BaseModelWithAuditSerializer):
    """Full detail serializer for loan orders"""
    loan_no = serializers.CharField(read_only=True)
    borrower = ExtendedUserSerializer(read_only=True)
    status = serializers.CharField(read_only=True)
    status_label = serializers.CharField(source='get_status_label', read_only=True)
    approved_by = ExtendedUserSerializer(read_only=True)
    lent_by = ExtendedUserSerializer(read_only=True)
    return_confirmed_by = ExtendedUserSerializer(read_only=True)
    items = LoanItemSerializer(many=True, read_only=True)
    items_count = serializers.SerializerMethodField()
    is_overdue = serializers.SerializerMethodField()
    overdue_days = serializers.SerializerMethodField()
    asset_condition_display = serializers.CharField(source='get_asset_condition_display', read_only=True)

    class Meta(BaseModelWithAuditSerializer.Meta):
        model = AssetLoan
        fields = BaseModelWithAuditSerializer.Meta.fields + [
            'loan_no', 'borrower', 'borrow_date', 'expected_return_date',
            'actual_return_date', 'loan_reason', 'status', 'status_label',
            'approved_by', 'approved_at', 'approval_comment',
            'lent_by', 'lent_at', 'returned_at', 'return_confirmed_by',
            'asset_condition', 'asset_condition_display', 'return_comment',
            'items', 'items_count', 'is_overdue', 'overdue_days'
        ]
        read_only_fields = ['loan_no', 'approved_at', 'lent_at', 'returned_at']

    def get_items_count(self, obj):
        """Get count of items in the loan order"""
        return obj.items.count()

    def get_is_overdue(self, obj):
        """Check if loan is overdue"""
        return obj.is_overdue()

    def get_overdue_days(self, obj):
        """Get overdue days count"""
        return obj.overdue_days()


class AssetLoanCreateSerializer(BaseModelSerializer):
    """Serializer for creating loan orders with items"""
    items = serializers.ListField(
        child=serializers.DictField(),
        write_only=True,
        required=True
    )

    class Meta(BaseModelSerializer.Meta):
        model = AssetLoan
        fields = BaseModelSerializer.Meta.fields + [
            'borrow_date', 'expected_return_date', 'loan_reason', 'items'
        ]

    def validate(self, data):
        """Validate loan dates"""
        borrow_date = data.get('borrow_date')
        return_date = data.get('expected_return_date')

        if borrow_date and return_date and return_date < borrow_date:
            raise serializers.ValidationError({
                'expected_return_date': 'Return date must be after borrow date'
            })

        # Limit loan duration to 90 days
        from datetime import timedelta
        if borrow_date and return_date:
            max_date = borrow_date + timedelta(days=90)
            if return_date > max_date:
                raise serializers.ValidationError({
                    'expected_return_date': 'Loan duration cannot exceed 90 days'
                })

        return data

    def create(self, validated_data):
        """Create loan order with items"""
        items_data = validated_data.pop('items')
        loan = AssetLoan.objects.create(**validated_data)

        # Create loan items
        for item_data in items_data:
            asset_id = item_data.get('asset_id')
            try:
                asset = Asset.objects.get(id=asset_id)
                LoanItem.objects.create(
                    loan=loan,
                    asset=asset,
                    remark=item_data.get('remark', '')
                )
            except Asset.DoesNotExist:
                pass

        return loan


class LoanApprovalSerializer(serializers.Serializer):
    """Serializer for loan approval action"""
    approval = serializers.ChoiceField(
        choices=['approved', 'rejected'],
        required=True
    )
    comment = serializers.CharField(
        required=False,
        allow_blank=True
    )


class LoanReturnConfirmSerializer(serializers.Serializer):
    """Serializer for confirming asset return"""
    condition = serializers.ChoiceField(
        choices=['good', 'minor_damage', 'major_damage', 'lost'],
        required=False,
        help_text='Asset condition upon return'
    )
    comment = serializers.CharField(
        required=False,
        allow_blank=True
    )


# ========== Dynamic Serializers for ViewSets ==========

class AssetPickupSerializer(BaseModelWithAuditSerializer):
    """Dynamic serializer that switches based on context"""
    pickup_no = serializers.CharField(read_only=True)
    applicant = ExtendedUserSerializer(read_only=True)
    department = LightweightDepartmentSerializer(read_only=True)
    status = serializers.CharField(read_only=True)
    status_label = serializers.CharField(source='get_status_label', read_only=True)
    approved_by = ExtendedUserSerializer(read_only=True)
    items_count = serializers.SerializerMethodField()

    class Meta(BaseModelWithAuditSerializer.Meta):
        model = AssetPickup
        fields = BaseModelWithAuditSerializer.Meta.fields + [
            'pickup_no', 'applicant', 'department', 'pickup_date',
            'pickup_reason', 'status', 'status_label', 'approved_by',
            'approved_at', 'approval_comment', 'completed_at', 'items_count'
        ]

    def get_items_count(self, obj):
        return obj.items.count()


class AssetTransferSerializer(BaseModelWithAuditSerializer):
    """Dynamic serializer for transfer orders"""
    transfer_no = serializers.CharField(read_only=True)
    from_department = LightweightDepartmentSerializer(read_only=True)
    to_department = LightweightDepartmentSerializer(read_only=True)
    status = serializers.CharField(read_only=True)
    status_label = serializers.CharField(source='get_status_label', read_only=True)
    from_approved_by = ExtendedUserSerializer(read_only=True)
    to_approved_by = ExtendedUserSerializer(read_only=True)
    items_count = serializers.SerializerMethodField()

    class Meta(BaseModelWithAuditSerializer.Meta):
        model = AssetTransfer
        fields = BaseModelWithAuditSerializer.Meta.fields + [
            'transfer_no', 'from_department', 'to_department', 'transfer_date',
            'transfer_reason', 'status', 'status_label',
            'from_approved_by', 'from_approved_at', 'from_approve_comment',
            'to_approved_by', 'to_approved_at', 'to_approve_comment',
            'completed_at', 'items_count'
        ]

    def get_items_count(self, obj):
        return obj.items.count()


class AssetReturnSerializer(BaseModelWithAuditSerializer):
    """Dynamic serializer for return orders"""
    return_no = serializers.CharField(read_only=True)
    returner = ExtendedUserSerializer(read_only=True)
    return_location = LightweightLocationSerializer(read_only=True)
    status = serializers.CharField(read_only=True)
    status_label = serializers.CharField(source='get_status_label', read_only=True)
    confirmed_by = ExtendedUserSerializer(read_only=True)
    items_count = serializers.SerializerMethodField()

    class Meta(BaseModelWithAuditSerializer.Meta):
        model = AssetReturn
        fields = BaseModelWithAuditSerializer.Meta.fields + [
            'return_no', 'returner', 'return_date', 'return_reason',
            'return_location', 'status', 'status_label',
            'confirmed_by', 'confirmed_at', 'reject_reason',
            'completed_at', 'items_count'
        ]

    def get_items_count(self, obj):
        return obj.items.count()


class AssetLoanSerializer(BaseModelWithAuditSerializer):
    """Dynamic serializer for loan orders"""
    loan_no = serializers.CharField(read_only=True)
    borrower = ExtendedUserSerializer(read_only=True)
    status = serializers.CharField(read_only=True)
    status_label = serializers.CharField(source='get_status_label', read_only=True)
    approved_by = ExtendedUserSerializer(read_only=True)
    lent_by = ExtendedUserSerializer(read_only=True)
    return_confirmed_by = ExtendedUserSerializer(read_only=True)
    items_count = serializers.SerializerMethodField()
    is_overdue = serializers.SerializerMethodField()

    class Meta(BaseModelWithAuditSerializer.Meta):
        model = AssetLoan
        fields = BaseModelWithAuditSerializer.Meta.fields + [
            'loan_no', 'borrower', 'borrow_date', 'expected_return_date',
            'actual_return_date', 'loan_reason', 'status', 'status_label',
            'approved_by', 'approved_at', 'approval_comment',
            'lent_by', 'lent_at', 'returned_at', 'return_confirmed_by',
            'asset_condition', 'return_comment', 'items_count', 'is_overdue'
        ]

    def get_items_count(self, obj):
        return obj.items.count()

    def get_is_overdue(self, obj):
        return obj.is_overdue()
