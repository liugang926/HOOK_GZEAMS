"""
Base Serializers for Consumable Management.

All serializers inherit from BaseModelSerializer for automatic
serialization of common fields (organization, is_deleted, created_at, etc.)
"""
from rest_framework import serializers
from apps.common.serializers.base import (
    BaseModelSerializer,
    BaseModelWithAuditSerializer,
    UserSerializer,
)
from apps.organizations.serializers import OrganizationSerializer
from apps.assets.serializers.asset import SupplierSerializer, LocationSerializer
from apps.consumables.models import (
    ConsumableCategory,
    Consumable,
    ConsumableStock,
    ConsumablePurchase,
    PurchaseItem,
    ConsumableIssue,
    IssueItem,
    TransactionType,
)


# ========== Category Serializers ==========

class ConsumableCategoryListSerializer(serializers.Serializer):
    """Optimized serializer for category list views"""
    id = serializers.UUIDField(read_only=True)
    code = serializers.CharField(read_only=True)
    name = serializers.CharField(read_only=True)
    parent_id = serializers.UUIDField(source='parent.id', read_only=True)
    parent_name = serializers.CharField(source='parent.name', read_only=True)
    level = serializers.IntegerField(read_only=True)
    path = serializers.CharField(read_only=True)
    is_active = serializers.BooleanField(read_only=True)
    enable_alert = serializers.BooleanField(read_only=True)
    min_stock = serializers.IntegerField(read_only=True)
    max_stock = serializers.IntegerField(read_only=True)
    reorder_point = serializers.IntegerField(read_only=True)
    unit = serializers.CharField(read_only=True)
    children_count = serializers.SerializerMethodField()

    def get_children_count(self, obj):
        return obj.children.count() if obj.id else 0


class ConsumableCategoryDetailSerializer(BaseModelSerializer):
    """Full serializer for category detail views"""
    parent = ConsumableCategoryListSerializer(read_only=True, allow_null=True)
    parent_id = serializers.UUIDField(write_only=True, required=False, allow_null=True)
    default_supplier = SupplierSerializer(read_only=True, allow_null=True)
    default_supplier_id = serializers.UUIDField(write_only=True, required=False, allow_null=True)
    children = ConsumableCategoryListSerializer(many=True, read_only=True)
    status_label = serializers.SerializerMethodField()

    class Meta(BaseModelSerializer.Meta):
        model = ConsumableCategory
        fields = BaseModelSerializer.Meta.fields + [
            'code', 'name', 'parent', 'parent_id', 'level', 'path',
            'enable_alert', 'min_stock', 'max_stock', 'reorder_point',
            'unit', 'default_supplier', 'default_supplier_id',
            'is_active', 'children', 'status_label',
        ]

    def get_status_label(self, obj):
        return 'Active' if obj.is_active else 'Inactive'


class ConsumableCategoryCreateSerializer(BaseModelSerializer):
    """Serializer for creating categories"""

    class Meta(BaseModelSerializer.Meta):
        model = ConsumableCategory
        fields = BaseModelSerializer.Meta.fields + [
            'code', 'name', 'parent_id', 'enable_alert',
            'min_stock', 'max_stock', 'reorder_point',
            'unit', 'default_supplier_id', 'is_active',
        ]


class ConsumableCategoryUpdateSerializer(BaseModelSerializer):
    """Serializer for updating categories"""

    class Meta(BaseModelSerializer.Meta):
        model = ConsumableCategory
        fields = BaseModelSerializer.Meta.fields + [
            'name', 'parent_id', 'enable_alert',
            'min_stock', 'max_stock', 'reorder_point',
            'unit', 'default_supplier_id', 'is_active',
        ]


class ConsumableCategorySerializer(BaseModelSerializer):
    """Default category serializer"""

    class Meta(BaseModelSerializer.Meta):
        model = ConsumableCategory
        fields = BaseModelSerializer.Meta.fields + [
            'code', 'name', 'parent', 'level', 'path',
            'enable_alert', 'min_stock', 'max_stock', 'reorder_point',
            'unit', 'default_supplier', 'is_active',
        ]


# ========== Consumable Serializers ==========

class ConsumableListSerializer(serializers.Serializer):
    """Optimized serializer for consumable list views"""
    id = serializers.UUIDField(read_only=True)
    code = serializers.CharField(read_only=True)
    name = serializers.CharField(read_only=True)
    category_id = serializers.UUIDField(source='category.id', read_only=True)
    category_name = serializers.CharField(source='category.name', read_only=True)
    category_code = serializers.CharField(source='category.code', read_only=True)
    specification = serializers.CharField(read_only=True)
    brand = serializers.CharField(read_only=True)
    unit = serializers.CharField(read_only=True)
    current_stock = serializers.IntegerField(read_only=True)
    available_stock = serializers.IntegerField(read_only=True)
    locked_stock = serializers.IntegerField(read_only=True)
    purchase_price = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    average_price = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    min_stock = serializers.IntegerField(read_only=True)
    max_stock = serializers.IntegerField(read_only=True)
    reorder_point = serializers.IntegerField(read_only=True)
    status = serializers.CharField(read_only=True)
    status_label = serializers.CharField(source='get_status_label', read_only=True)
    is_low_stock = serializers.SerializerMethodField()
    warehouse_id = serializers.UUIDField(source='warehouse.id', read_only=True, allow_null=True)
    warehouse_name = serializers.CharField(source='warehouse.name', read_only=True, allow_null=True)

    def get_is_low_stock(self, obj):
        return obj.available_stock <= obj.reorder_point


class ConsumableDetailSerializer(BaseModelSerializer):
    """Full serializer for consumable detail views"""
    category = ConsumableCategorySerializer(read_only=True)
    category_id = serializers.UUIDField(write_only=True)
    warehouse = LocationSerializer(read_only=True, allow_null=True)
    warehouse_id = serializers.UUIDField(write_only=True, required=False, allow_null=True)
    status_label = serializers.CharField(source='get_status_label', read_only=True)
    is_low_stock = serializers.SerializerMethodField()
    created_by = UserSerializer(read_only=True)

    class Meta(BaseModelSerializer.Meta):
        model = Consumable
        fields = BaseModelSerializer.Meta.fields + [
            'code', 'name', 'category', 'category_id',
            'specification', 'brand', 'unit',
            'current_stock', 'available_stock', 'locked_stock',
            'purchase_price', 'average_price',
            'min_stock', 'max_stock', 'reorder_point',
            'status', 'status_label', 'is_low_stock',
            'warehouse', 'warehouse_id', 'remark',
        ]

    def get_is_low_stock(self, obj):
        return obj.available_stock <= obj.reorder_point


class ConsumableCreateSerializer(BaseModelSerializer):
    """Serializer for creating consumables"""

    class Meta(BaseModelSerializer.Meta):
        model = Consumable
        fields = BaseModelSerializer.Meta.fields + [
            'code', 'name', 'category_id',
            'specification', 'brand', 'unit',
            'purchase_price', 'min_stock', 'max_stock', 'reorder_point',
            'warehouse_id', 'remark',
        ]


class ConsumableUpdateSerializer(BaseModelSerializer):
    """Serializer for updating consumables"""

    class Meta(BaseModelSerializer.Meta):
        model = Consumable
        fields = BaseModelSerializer.Meta.fields + [
            'name', 'category_id', 'specification', 'brand',
            'purchase_price', 'min_stock', 'max_stock', 'reorder_point',
            'status', 'warehouse_id', 'remark',
        ]


class ConsumableSerializer(BaseModelSerializer):
    """Default consumable serializer"""

    class Meta(BaseModelSerializer.Meta):
        model = Consumable
        fields = BaseModelSerializer.Meta.fields + [
            'code', 'name', 'category', 'specification', 'brand', 'unit',
            'current_stock', 'available_stock', 'locked_stock',
            'purchase_price', 'average_price',
            'min_stock', 'max_stock', 'reorder_point',
            'status', 'warehouse', 'remark',
        ]


# ========== Stock Transaction Serializers ==========

class ConsumableStockListSerializer(serializers.Serializer):
    """Optimized serializer for stock transaction list views"""
    id = serializers.UUIDField(read_only=True)
    consumable_id = serializers.UUIDField(source='consumable.id', read_only=True)
    consumable_name = serializers.CharField(source='consumable.name', read_only=True)
    consumable_code = serializers.CharField(source='consumable.code', read_only=True)
    transaction_type = serializers.CharField(read_only=True)
    transaction_type_label = serializers.CharField(source='get_transaction_type_display', read_only=True)
    quantity = serializers.IntegerField(read_only=True)
    before_stock = serializers.IntegerField(read_only=True)
    after_stock = serializers.IntegerField(read_only=True)
    source_type = serializers.CharField(read_only=True)
    source_id = serializers.CharField(read_only=True)
    source_no = serializers.CharField(read_only=True)
    handler = UserSerializer(read_only=True, allow_null=True)
    created_at = serializers.DateTimeField(read_only=True)


class ConsumableStockSerializer(BaseModelSerializer):
    """Full serializer for stock transactions"""
    consumable = ConsumableListSerializer(read_only=True)
    consumable_id = serializers.UUIDField(write_only=True)
    transaction_type_label = serializers.CharField(source='get_transaction_type_display', read_only=True)
    handler = UserSerializer(read_only=True, allow_null=True)

    class Meta(BaseModelSerializer.Meta):
        model = ConsumableStock
        fields = BaseModelSerializer.Meta.fields + [
            'consumable', 'consumable_id',
            'transaction_type', 'transaction_type_label',
            'quantity', 'before_stock', 'after_stock',
            'source_type', 'source_id', 'source_no',
            'handler', 'remark',
        ]


# ========== Purchase Order Serializers ==========

class PurchaseItemSerializer(BaseModelSerializer):
    """Serializer for purchase order line items"""
    id = serializers.UUIDField(read_only=True)
    consumable_id = serializers.UUIDField(source='consumable.id', read_only=True)
    consumable_name = serializers.CharField(source='consumable.name', read_only=True)
    consumable_code = serializers.CharField(source='consumable.code', read_only=True)

    class Meta(BaseModelSerializer.Meta):
        model = PurchaseItem
        fields = BaseModelSerializer.Meta.fields + [
            'consumable', 'consumable_id', 'consumable_name', 'consumable_code',
            'quantity', 'unit_price', 'amount', 'remark',
        ]


class PurchaseItemCreateSerializer(serializers.Serializer):
    """Serializer for creating purchase items"""
    consumable_id = serializers.UUIDField(required=True)
    quantity = serializers.IntegerField(min_value=1)
    unit_price = serializers.DecimalField(max_digits=10, decimal_places=2, min_value=0)
    remark = serializers.CharField(required=False, allow_blank=True)


class ConsumablePurchaseListSerializer(serializers.Serializer):
    """Optimized serializer for purchase order list views"""
    id = serializers.UUIDField(read_only=True)
    purchase_no = serializers.CharField(read_only=True)
    purchase_date = serializers.DateField(read_only=True)
    supplier_id = serializers.UUIDField(source='supplier.id', read_only=True)
    supplier_name = serializers.CharField(source='supplier.name', read_only=True)
    total_amount = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)
    status = serializers.CharField(read_only=True)
    status_label = serializers.CharField(source='get_status_label', read_only=True)
    items_count = serializers.SerializerMethodField()
    created_by = UserSerializer(read_only=True)
    created_at = serializers.DateTimeField(read_only=True)

    def get_items_count(self, obj):
        return obj.items.count()


class ConsumablePurchaseDetailSerializer(BaseModelWithAuditSerializer):
    """Full serializer for purchase order detail views"""
    supplier = SupplierSerializer(read_only=True)
    supplier_id = serializers.UUIDField(write_only=True)
    approved_by = UserSerializer(read_only=True, allow_null=True)
    received_by = UserSerializer(read_only=True, allow_null=True)
    items = PurchaseItemSerializer(many=True, read_only=True)
    status_label = serializers.CharField(source='get_status_label', read_only=True)

    class Meta(BaseModelWithAuditSerializer.Meta):
        model = ConsumablePurchase
        fields = BaseModelWithAuditSerializer.Meta.fields + [
            'purchase_no', 'purchase_date', 'supplier', 'supplier_id',
            'total_amount', 'status', 'status_label',
            'approved_by', 'approved_at', 'approval_comment',
            'received_by', 'received_at',
            'items', 'remark',
        ]


class ConsumablePurchaseCreateSerializer(BaseModelSerializer):
    """Serializer for creating purchase orders with items"""
    items = PurchaseItemCreateSerializer(many=True, write_only=True, required=True)

    class Meta(BaseModelSerializer.Meta):
        model = ConsumablePurchase
        fields = BaseModelSerializer.Meta.fields + [
            'purchase_date', 'supplier_id', 'items', 'remark',
        ]


class ConsumablePurchaseUpdateSerializer(BaseModelSerializer):
    """Serializer for updating purchase orders"""

    class Meta(BaseModelSerializer.Meta):
        model = ConsumablePurchase
        fields = BaseModelSerializer.Meta.fields + [
            'purchase_date', 'supplier_id', 'remark',
        ]


class ConsumablePurchaseSerializer(BaseModelSerializer):
    """Default purchase order serializer"""

    class Meta(BaseModelSerializer.Meta):
        model = ConsumablePurchase
        fields = BaseModelSerializer.Meta.fields + [
            'purchase_no', 'purchase_date', 'supplier',
            'total_amount', 'status',
            'approved_by', 'approved_at',
            'received_by', 'received_at', 'remark',
        ]


class PurchaseApprovalSerializer(serializers.Serializer):
    """Serializer for purchase approval action"""
    approval = serializers.ChoiceField(choices=['approved', 'rejected'])
    comment = serializers.CharField(required=False, allow_blank=True)


# ========== Issue Order Serializers ==========

class IssueItemSerializer(BaseModelSerializer):
    """Serializer for issue order line items"""
    id = serializers.UUIDField(read_only=True)
    consumable_id = serializers.UUIDField(source='consumable.id', read_only=True)
    consumable_name = serializers.CharField(source='consumable.name', read_only=True)
    consumable_code = serializers.CharField(source='consumable.code', read_only=True)

    class Meta(BaseModelSerializer.Meta):
        model = IssueItem
        fields = BaseModelSerializer.Meta.fields + [
            'consumable', 'consumable_id', 'consumable_name', 'consumable_code',
            'quantity', 'snapshot_before_stock', 'remark',
        ]


class IssueItemCreateSerializer(serializers.Serializer):
    """Serializer for creating issue items"""
    consumable_id = serializers.UUIDField(required=True)
    quantity = serializers.IntegerField(min_value=1)
    remark = serializers.CharField(required=False, allow_blank=True)


class ConsumableIssueListSerializer(serializers.Serializer):
    """Optimized serializer for issue order list views"""
    id = serializers.UUIDField(read_only=True)
    issue_no = serializers.CharField(read_only=True)
    issue_date = serializers.DateField(read_only=True)
    applicant_id = serializers.UUIDField(source='applicant.id', read_only=True)
    applicant_name = serializers.CharField(source='applicant.username', read_only=True)
    department_id = serializers.UUIDField(source='department.id', read_only=True)
    department_name = serializers.CharField(source='department.name', read_only=True)
    status = serializers.CharField(read_only=True)
    status_label = serializers.CharField(source='get_status_label', read_only=True)
    items_count = serializers.SerializerMethodField()
    created_by = UserSerializer(read_only=True)
    created_at = serializers.DateTimeField(read_only=True)

    def get_items_count(self, obj):
        return obj.items.count()


class ConsumableIssueDetailSerializer(BaseModelWithAuditSerializer):
    """Full serializer for issue order detail views"""
    applicant = UserSerializer(read_only=True)
    applicant_id = serializers.UUIDField(write_only=True)
    department = OrganizationSerializer(read_only=True)
    department_id = serializers.UUIDField(write_only=True)
    approved_by = UserSerializer(read_only=True, allow_null=True)
    issued_by = UserSerializer(read_only=True, allow_null=True)
    items = IssueItemSerializer(many=True, read_only=True)
    status_label = serializers.CharField(source='get_status_label', read_only=True)

    class Meta(BaseModelWithAuditSerializer.Meta):
        model = ConsumableIssue
        fields = BaseModelWithAuditSerializer.Meta.fields + [
            'issue_no', 'issue_date', 'applicant', 'applicant_id',
            'department', 'department_id',
            'issue_reason', 'status', 'status_label',
            'approved_by', 'approved_at', 'approval_comment',
            'issued_by', 'issued_at',
            'items', 'remark',
        ]


class ConsumableIssueCreateSerializer(BaseModelSerializer):
    """Serializer for creating issue orders with items"""
    items = IssueItemCreateSerializer(many=True, write_only=True, required=True)

    class Meta(BaseModelSerializer.Meta):
        model = ConsumableIssue
        fields = BaseModelSerializer.Meta.fields + [
            'issue_date', 'applicant_id', 'department_id',
            'issue_reason', 'items', 'remark',
        ]


class ConsumableIssueUpdateSerializer(BaseModelSerializer):
    """Serializer for updating issue orders"""

    class Meta(BaseModelSerializer.Meta):
        model = ConsumableIssue
        fields = BaseModelSerializer.Meta.fields + [
            'issue_date', 'issue_reason', 'remark',
        ]


class ConsumableIssueSerializer(BaseModelSerializer):
    """Default issue order serializer"""

    class Meta(BaseModelSerializer.Meta):
        model = ConsumableIssue
        fields = BaseModelSerializer.Meta.fields + [
            'issue_no', 'issue_date', 'applicant', 'department',
            'issue_reason', 'status',
            'approved_by', 'approved_at',
            'issued_by', 'issued_at', 'remark',
        ]


class IssueApprovalSerializer(serializers.Serializer):
    """Serializer for issue approval action"""
    approval = serializers.ChoiceField(choices=['approved', 'rejected'])
    comment = serializers.CharField(required=False, allow_blank=True)
