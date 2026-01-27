"""
Serializers for Asset and related models.

Provides serializers for:
- Supplier
- Location
- AssetStatusLog
- Asset (list, detail, create, status change)
"""
from rest_framework import serializers
from django.contrib.auth import get_user_model
from apps.common.serializers.base import (
    BaseModelSerializer,
    BaseModelWithAuditSerializer,
    BaseListSerializer
)
from apps.assets.models import (
    Supplier,
    Location,
    AssetStatusLog,
    Asset
)

User = get_user_model()


# ========== Supplier Serializers ==========

class SupplierSerializer(BaseModelSerializer):
    """Serializer for Supplier CRUD operations."""

    class Meta(BaseModelSerializer.Meta):
        model = Supplier
        fields = BaseModelSerializer.Meta.fields + [
            'code', 'name', 'contact', 'phone', 'email', 'address'
        ]


class SupplierListSerializer(BaseListSerializer):
    """Optimized serializer for supplier list views."""

    class Meta(BaseListSerializer.Meta):
        model = Supplier
        fields = BaseListSerializer.Meta.fields + [
            'code', 'name', 'contact', 'phone'
        ]


# ========== Location Serializers ==========

class LocationSerializer(BaseModelSerializer):
    """Serializer for Location CRUD operations."""

    parent_name = serializers.CharField(source='parent.name', read_only=True)
    location_type_display = serializers.CharField(
        source='get_location_type_display',
        read_only=True
    )
    has_children = serializers.SerializerMethodField()

    class Meta(BaseModelSerializer.Meta):
        model = Location
        fields = BaseModelSerializer.Meta.fields + [
            'name', 'parent', 'parent_name', 'path', 'level',
            'location_type', 'location_type_display', 'has_children'
        ]
        extra_kwargs = {
            'parent': {'required': False, 'allow_null': True},
            'path': {'required': False, 'read_only': True}  # Auto-generated
        }

    def get_has_children(self, obj):
        """Check if location has children."""
        return obj.children.filter(is_deleted=False).exists()

    def validate(self, data):
        """Prevent circular reference in parent."""
        parent = data.get('parent')
        if parent and self.instance:
            if self._is_descendant(parent, self.instance):
                raise serializers.ValidationError({
                    'parent': 'Cannot set a descendant as parent.'
                })
        return data

    def _is_descendant(self, parent, child):
        """Check if parent is a descendant of child (circular reference)."""
        current = child
        while current.parent_id:
            if current.parent_id == parent.id:
                return True
            current = current.parent
        return False


class LocationListSerializer(BaseListSerializer):
    """Optimized serializer for location list views."""

    class Meta(BaseListSerializer.Meta):
        model = Location
        fields = BaseListSerializer.Meta.fields + [
            'name', 'path', 'level', 'location_type'
        ]


# ========== AssetStatusLog Serializers ==========

class AssetStatusLogSerializer(BaseModelSerializer):
    """Serializer for AssetStatusLog."""

    asset_code = serializers.CharField(source='asset.asset_code', read_only=True)
    asset_name = serializers.CharField(source='asset.asset_name', read_only=True)

    class Meta(BaseModelSerializer.Meta):
        model = AssetStatusLog
        fields = BaseModelSerializer.Meta.fields + [
            'asset', 'asset_code', 'asset_name',
            'old_status', 'new_status', 'reason'
        ]


class AssetStatusLogListSerializer(BaseListSerializer):
    """Optimized serializer for status log list views."""

    old_status_display = serializers.CharField(
        source='get_old_status_display',
        read_only=True
    )
    new_status_display = serializers.CharField(
        source='get_new_status_display',
        read_only=True
    )

    class Meta(BaseListSerializer.Meta):
        model = AssetStatusLog
        fields = BaseListSerializer.Meta.fields + [
            'asset', 'old_status', 'old_status_display',
            'new_status', 'new_status_display', 'reason'
        ]


# ========== Asset Serializers ==========

class LightweightAssetCategorySerializer(serializers.ModelSerializer):
    """Lightweight category serializer for nested display."""

    class Meta:
        from apps.assets.models import AssetCategory
        model = AssetCategory
        fields = ['id', 'code', 'name', 'full_name']


class LightweightDepartmentSerializer(serializers.ModelSerializer):
    """Lightweight department/organization serializer for nested display.
    Departments are represented as Organization objects with org_type='department'.
    """

    class Meta:
        from apps.organizations.models import Organization
        model = Organization
        fields = ['id', 'name', 'code']


class AssetListSerializer(BaseListSerializer):
    """
    Optimized serializer for asset list views.

    Includes essential fields for display in list/grid views.
    Excludes heavy nested data for performance.
    """

    asset_code = serializers.CharField(read_only=True)
    asset_name = serializers.CharField(read_only=True)
    asset_category_name = serializers.CharField(source='asset_category.name', read_only=True)
    asset_status = serializers.CharField(read_only=True)
    asset_status_display = serializers.SerializerMethodField()
    purchase_price = serializers.DecimalField(max_digits=14, decimal_places=2, read_only=True)
    current_value = serializers.DecimalField(max_digits=14, decimal_places=2, read_only=True)

    class Meta(BaseListSerializer.Meta):
        model = Asset
        fields = BaseListSerializer.Meta.fields + [
            'asset_code', 'asset_name', 'asset_category_name',
            'specification', 'brand', 'model',
            'purchase_price', 'current_value',
            'asset_status', 'asset_status_display',
            'purchase_date'
        ]

    def get_asset_status_display(self, obj):
        """Get status label from DictionaryService."""
        return obj.get_status_label()


class AssetDetailSerializer(BaseModelWithAuditSerializer):
    """
    Full serializer for asset detail views.

    Includes all fields with nested serializers for related entities.
    Used for retrieve and update operations where complete data is needed.
    """

    # Basic Information
    asset_code = serializers.CharField(read_only=True)
    qr_code = serializers.CharField(read_only=True)

    # Related Objects - Nested Serializers
    asset_category = LightweightAssetCategorySerializer(read_only=True)
    supplier = SupplierSerializer(read_only=True)
    location = LocationSerializer(read_only=True)
    department = LightweightDepartmentSerializer(read_only=True)
    custodian = serializers.SerializerMethodField()
    user = serializers.SerializerMethodField()

    # Display Fields
    asset_status_display = serializers.SerializerMethodField()

    # Calculated Properties
    net_value = serializers.FloatField(read_only=True)
    residual_value = serializers.FloatField(read_only=True)

    # Status Log Count
    status_log_count = serializers.SerializerMethodField()

    class Meta(BaseModelWithAuditSerializer.Meta):
        model = Asset
        fields = BaseModelWithAuditSerializer.Meta.fields + [
            # Basic Information
            'asset_code', 'asset_name', 'asset_category',
            'specification', 'brand', 'model', 'unit', 'serial_number',
            # Financial Information
            'purchase_price', 'current_value', 'accumulated_depreciation',
            'purchase_date', 'depreciation_start_date',
            'useful_life', 'residual_rate',
            'net_value', 'residual_value',
            # Supplier Information
            'supplier', 'supplier_order_no', 'invoice_no',
            # Usage Information
            'department', 'location', 'custodian', 'user',
            # Status Information
            'asset_status', 'asset_status_display',
            # Label Information
            'qr_code', 'rfid_code',
            # Attachment Information
            'images', 'attachments', 'remarks',
            # Audit
            'status_log_count'
        ]

    def get_custodian(self, obj):
        """Get custodian info."""
        if obj.custodian:
            return {
                'id': str(obj.custodian.id),
                'username': obj.custodian.username,
                'email': obj.custodian.email
            }
        return None

    def get_user(self, obj):
        """Get actual user info."""
        if obj.user:
            return {
                'id': str(obj.user.id),
                'username': obj.user.username,
                'email': obj.user.email
            }
        return None

    def get_status_log_count(self, obj):
        """Get count of status change logs."""
        return obj.status_logs.filter(is_deleted=False).count()

    def get_asset_status_display(self, obj):
        """Get status label from DictionaryService."""
        return obj.get_status_label()


class AssetCreateSerializer(BaseModelSerializer):
    """
    Serializer for creating new assets.

    Asset code and QR code are auto-generated.
    Depreciation start date defaults to purchase date if not provided.
    """

    # Read-only fields that are auto-generated
    asset_code = serializers.CharField(read_only=True)
    qr_code = serializers.CharField(read_only=True)

    class Meta(BaseModelSerializer.Meta):
        model = Asset
        fields = BaseModelSerializer.Meta.fields + [
            # Basic Information
            'asset_code', 'asset_name', 'asset_category',
            'specification', 'brand', 'model', 'unit', 'serial_number',
            # Financial Information
            'purchase_price', 'useful_life', 'residual_rate',
            'purchase_date', 'depreciation_start_date',
            # Supplier Information
            'supplier', 'supplier_order_no', 'invoice_no',
            # Usage Information
            'department', 'location', 'custodian', 'user',
            # Status Information
            'asset_status',
            # Label Information (qr_code auto-generated, not in input)
            'qr_code', 'rfid_code',
            # Attachment Information
            'images', 'attachments', 'remarks'
        ]
        extra_kwargs = {
            'asset_category': {'required': True, 'allow_null': False},
            'purchase_price': {'required': True},
            'purchase_date': {'required': True}
        }

    def validate_purchase_price(self, value):
        """Ensure purchase price is non-negative."""
        if value < 0:
            raise serializers.ValidationError("Purchase price cannot be negative.")
        return value

    def validate_asset_category(self, value):
        """Ensure category belongs to same organization."""
        org_id = self.context.get('organization_id')
        if org_id and str(value.organization_id) != str(org_id):
            raise serializers.ValidationError(
                "Asset category must belong to the same organization."
            )
        return value

    def validate_supplier(self, value):
        """Ensure supplier belongs to same organization."""
        if value is None:
            return value
        org_id = self.context.get('organization_id')
        if org_id and str(value.organization_id) != str(org_id):
            raise serializers.ValidationError(
                "Supplier must belong to the same organization."
            )
        return value

    def validate_location(self, value):
        """Ensure location belongs to same organization."""
        if value is None:
            return value
        org_id = self.context.get('organization_id')
        if org_id and str(value.organization_id) != str(org_id):
            raise serializers.ValidationError(
                "Location must belong to the same organization."
            )
        return value

    def validate_unit(self, value):
        """Validate unit exists in Dictionary."""
        if not value:
            return value
        from apps.system.services import DictionaryService
        if not DictionaryService.validate_value('UNIT', value):
            raise serializers.ValidationError(
                f"Invalid unit code: {value}. Please use a value from UNIT dictionary."
            )
        return value


class AssetUpdateSerializer(BaseModelSerializer):
    """
    Serializer for updating existing assets.

    Asset code and QR code cannot be modified (read-only).
    """

    asset_code = serializers.CharField(read_only=True)
    qr_code = serializers.CharField(read_only=True)

    class Meta(BaseModelSerializer.Meta):
        model = Asset
        fields = BaseModelSerializer.Meta.fields + [
            'asset_code', 'asset_name', 'asset_category',
            'specification', 'brand', 'model', 'unit', 'serial_number',
            'purchase_price', 'current_value', 'accumulated_depreciation',
            'purchase_date', 'depreciation_start_date',
            'useful_life', 'residual_rate',
            'supplier', 'supplier_order_no', 'invoice_no',
            'department', 'location', 'custodian', 'user',
            'asset_status', 'qr_code', 'rfid_code',
            'images', 'attachments', 'remarks'
        ]

    def validate_purchase_price(self, value):
        """Ensure purchase price is non-negative."""
        if value < 0:
            raise serializers.ValidationError("Purchase price cannot be negative.")
        return value

    def validate_unit(self, value):
        """Validate unit exists in Dictionary."""
        if not value:
            return value
        from apps.system.services import DictionaryService
        if not DictionaryService.validate_value('UNIT', value):
            raise serializers.ValidationError(
                f"Invalid unit code: {value}. Please use a value from UNIT dictionary."
            )
        return value


class AssetStatusSerializer(serializers.Serializer):
    """
    Serializer for changing asset status.

    Creates an AssetStatusLog entry to record the change.
    Status values are validated against ASSET_STATUS dictionary.
    """

    new_status = serializers.CharField(required=True, max_length=50)
    reason = serializers.CharField(required=False, allow_blank=True, max_length=1000)

    def validate_new_status(self, value):
        """Validate status exists in Dictionary."""
        from apps.system.services import DictionaryService
        if not DictionaryService.validate_value('ASSET_STATUS', value):
            raise serializers.ValidationError(
                f"Invalid status '{value}'. Use DictionaryService.get_items('ASSET_STATUS') for valid options."
            )
        return value


class AssetSerializer(BaseModelSerializer):
    """
    Default serializer for Asset CRUD operations.

    Combines create and update functionality.
    Used as the default serializer_class in ViewSets.
    """

    asset_code = serializers.CharField(read_only=True)
    qr_code = serializers.CharField(read_only=True)
    asset_status_display = serializers.SerializerMethodField()
    asset_category_name = serializers.CharField(
        source='asset_category.name',
        read_only=True
    )
    department_name = serializers.CharField(
        source='department.name',
        read_only=True,
        allow_null=True
    )
    location_path = serializers.CharField(
        source='location.path',
        read_only=True,
        allow_null=True
    )
    supplier_name = serializers.CharField(
        source='supplier.name',
        read_only=True,
        allow_null=True
    )

    class Meta(BaseModelSerializer.Meta):
        model = Asset
        fields = BaseModelSerializer.Meta.fields + [
            'asset_code', 'asset_name', 'asset_category', 'asset_category_name',
            'specification', 'brand', 'model', 'unit', 'serial_number',
            'purchase_price', 'current_value', 'accumulated_depreciation',
            'purchase_date', 'depreciation_start_date',
            'useful_life', 'residual_rate',
            'supplier', 'supplier_name', 'supplier_order_no', 'invoice_no',
            'department', 'department_name',
            'location', 'location_path',
            'custodian', 'user',
            'asset_status', 'asset_status_display',
            'qr_code', 'rfid_code',
            'images', 'attachments', 'remarks'
        ]
        extra_kwargs = {
            'asset_category': {'required': True}
        }

    def get_asset_status_display(self, obj):
        """Get status label from DictionaryService."""
        return obj.get_status_label()


# ========== Bulk Import/Export Serializers ==========

class AssetBulkImportSerializer(serializers.Serializer):
    """
    Serializer for bulk asset import.

    Accepts a list of asset objects for batch creation.
    """

    assets = serializers.ListField(
        child=AssetCreateSerializer(),
        allow_empty=False
    )

    def validate_assets(self, value):
        """Ensure batch is not empty and within size limit."""
        if not value:
            raise serializers.ValidationError("Asset list cannot be empty.")
        if len(value) > 1000:
            raise serializers.ValidationError("Maximum 1000 assets per batch.")
        return value


class AssetBulkExportSerializer(serializers.Serializer):
    """
    Serializer for bulk asset export options.

    Supports filtering and field selection.
    """

    asset_status = serializers.CharField(
        required=False,
        help_text='Filter by asset status (use Dictionary code, or "all")'
    )
    asset_category = serializers.UUIDField(required=False, allow_null=True)
    date_from = serializers.DateField(required=False, allow_null=True)
    date_to = serializers.DateField(required=False, allow_null=True)
    fields = serializers.ListField(
        child=serializers.CharField(),
        required=False
    )
    format = serializers.ChoiceField(
        choices=['csv', 'excel', 'json'],
        default='excel'
    )
