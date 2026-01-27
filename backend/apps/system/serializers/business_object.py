"""
Serializers for Business Objects in the hybrid architecture.

Provides serializers for both hardcoded Django models and low-code
custom business objects.
"""
from rest_framework import serializers

from apps.common.serializers.base import (
    BaseModelSerializer,
    BaseModelWithAuditSerializer,
    BaseListSerializer
)
from apps.system.models import (
    BusinessObject,
    ModelFieldDefinition,
    FieldDefinition,
    PageLayout,
)


# Core hardcoded model names (for display name mapping)
HARDCODED_OBJECT_NAMES = {
    'Asset': ('资产', 'Asset'),
    'AssetCategory': ('资产分类', 'Asset Category'),
    'Supplier': ('供应商', 'Supplier'),
    'Location': ('位置', 'Location'),
    'AssetStatusLog': ('资产状态日志', 'Asset Status Log'),
    'AssetPickup': ('资产领用', 'Asset Pickup'),
    'PickupItem': ('领用明细', 'Pickup Item'),
    'AssetTransfer': ('资产调拨', 'Asset Transfer'),
    'TransferItem': ('调拨明细', 'Transfer Item'),
    'AssetReturn': ('资产归还', 'Asset Return'),
    'ReturnItem': ('归还明细', 'Return Item'),
    'AssetLoan': ('资产借用', 'Asset Loan'),
    'LoanItem': ('借用明细', 'Loan Item'),
    'Consumable': ('耗材', 'Consumable'),
    'ConsumableCategory': ('耗材分类', 'Consumable Category'),
    'ConsumableStock': ('耗材库存', 'Consumable Stock'),
    'ConsumablePurchase': ('耗材采购', 'Consumable Purchase'),
    'ConsumableIssue': ('耗材领用', 'Consumable Issue'),
    'PurchaseRequest': ('采购申请', 'Purchase Request'),
    'AssetReceipt': ('资产入库', 'Asset Receipt'),
    'Maintenance': ('维修记录', 'Maintenance'),
    'MaintenancePlan': ('维修计划', 'Maintenance Plan'),
    'DisposalRequest': ('报废申请', 'Disposal Request'),
    'InventoryTask': ('盘点任务', 'Inventory Task'),
    'InventorySnapshot': ('资产快照', 'Inventory Snapshot'),
    'Organization': ('组织', 'Organization'),
    'Department': ('部门', 'Department'),
    'User': ('用户', 'User'),
    'Role': ('角色', 'Role'),
    'WorkflowDefinition': ('工作流定义', 'Workflow Definition'),
    'WorkflowInstance': ('工作流实例', 'Workflow Instance'),
}


class BusinessObjectSerializer(BaseModelSerializer):
    """
    Serializer for Business Object CRUD operations.

    Handles both hardcoded and custom business objects.
    """

    # Read-only fields for hardcoded objects
    is_hardcoded = serializers.BooleanField(read_only=True)
    django_model_path = serializers.CharField(read_only=True)

    # Computed properties
    field_count = serializers.IntegerField(read_only=True)
    layout_count = serializers.IntegerField(read_only=True)

    # Nested serializers
    default_form_layout_name = serializers.CharField(
        source='default_form_layout.layout_name',
        read_only=True,
        allow_null=True
    )
    default_list_layout_name = serializers.CharField(
        source='default_list_layout.layout_name',
        read_only=True,
        allow_null=True
    )

    class Meta(BaseModelSerializer.Meta):
        model = BusinessObject
        fields = BaseModelSerializer.Meta.fields + [
            'code', 'name', 'name_en', 'description',
            'is_hardcoded', 'django_model_path',
            'enable_workflow', 'enable_version', 'enable_soft_delete',
            'default_form_layout', 'default_list_layout',
            'default_form_layout_name', 'default_list_layout_name',
            'table_name',
            'field_count', 'layout_count',
        ]

    def validate(self, data):
        """Validate business object constraints."""
        # Hardcoded objects must have django_model_path
        if data.get('is_hardcoded') and not data.get('django_model_path'):
            raise serializers.ValidationError({
                'django_model_path': 'Required for hardcoded objects'
            })

        # Custom objects must have table_name
        if not data.get('is_hardcoded') and not data.get('table_name'):
            # Auto-generate table_name from code if not provided
            code = data.get('code') or (self.instance.code if self.instance else '')
            if code:
                data['table_name'] = f"dynamic_data_{code.lower()}"

        return data


class BusinessObjectListSerializer(BaseListSerializer):
    """
    Optimized serializer for business object list views.

    Includes type indicator for UI grouping.
    """

    is_hardcoded = serializers.BooleanField(read_only=True)
    field_count = serializers.IntegerField(read_only=True)
    object_type = serializers.SerializerMethodField()

    class Meta(BaseListSerializer.Meta):
        model = BusinessObject
        fields = BaseListSerializer.Meta.fields + [
            'code', 'name', 'name_en',
            'is_hardcoded', 'table_name',
            'field_count', 'enable_workflow', 'object_type'
        ]

    def get_object_type(self, obj):
        """Get object type for UI grouping."""
        return 'hardcoded' if obj.is_hardcoded else 'custom'


class BusinessObjectDetailSerializer(BaseModelWithAuditSerializer):
    """
    Full serializer for business object detail views.

    Includes nested field definitions and layouts.
    """

    is_hardcoded = serializers.BooleanField(read_only=True)
    django_model_path = serializers.CharField(read_only=True)

    # Field definitions (different for hardcoded vs custom)
    field_definitions = serializers.SerializerMethodField()
    page_layouts = serializers.SerializerMethodField()

    class Meta(BaseModelWithAuditSerializer.Meta):
        model = BusinessObject
        fields = BaseModelWithAuditSerializer.Meta.fields + [
            'code', 'name', 'name_en', 'description',
            'is_hardcoded', 'django_model_path',
            'enable_workflow', 'enable_version', 'enable_soft_delete',
            'default_form_layout', 'default_list_layout',
            'table_name',
            'field_definitions', 'page_layouts',
        ]

    def get_field_definitions(self, obj):
        """Get field definitions based on object type."""
        if obj.is_hardcoded:
            # Use ModelFieldDefinition for hardcoded objects
            fields = obj.model_fields.filter(is_deleted=False).order_by('sort_order')
            return ModelFieldDefinitionSerializer(fields, many=True).data
        else:
            # Use FieldDefinition for custom objects
            fields = obj.field_definitions.filter(is_deleted=False).order_by('sort_order')
            return FieldDefinitionSerializer(fields, many=True).data

    def get_page_layouts(self, obj):
        """Get page layouts."""
        layouts = obj.page_layouts.filter(is_deleted=False)
        return PageLayoutSerializer(layouts, many=True).data


class ModelFieldDefinitionSerializer(BaseModelSerializer):
    """
    Serializer for Model Field Definition.

    Read-only serializer for fields exposed from hardcoded Django models.
    """

    business_object_code = serializers.CharField(
        source='business_object.code',
        read_only=True
    )
    business_object_name = serializers.CharField(
        source='business_object.name',
        read_only=True
    )

    class Meta(BaseModelSerializer.Meta):
        model = ModelFieldDefinition
        fields = BaseModelSerializer.Meta.fields + [
            'business_object', 'business_object_code', 'business_object_name',
            'field_name', 'display_name', 'display_name_en',
            'field_type', 'django_field_type',
            'is_required', 'is_readonly', 'is_editable', 'is_unique',
            'show_in_list', 'show_in_detail', 'show_in_form',
            'sort_order',
            'reference_model_path', 'reference_display_field',
            'decimal_places', 'max_digits', 'max_length',
        ]
        read_only_fields = [
            'business_object', 'field_name', 'field_type', 'django_field_type',
            'is_required', 'is_readonly', 'is_editable', 'is_unique',
            'reference_model_path', 'decimal_places', 'max_digits', 'max_length',
        ]


class ModelFieldDefinitionListSerializer(BaseListSerializer):
    """Optimized serializer for model field list views."""

    business_object_code = serializers.CharField(
        source='business_object.code',
        read_only=True
    )
    field_type_display = serializers.CharField(
        source='get_field_type_display',
        read_only=True
    )

    class Meta(BaseListSerializer.Meta):
        model = ModelFieldDefinition
        fields = BaseListSerializer.Meta.fields + [
            'business_object_code',
            'field_name', 'display_name',
            'field_type', 'field_type_display',
            'is_required', 'is_readonly',
            'show_in_list', 'show_in_form',
            'sort_order',
        ]


class FieldDefinitionSerializer(BaseModelSerializer):
    """
    Serializer for Field Definition (low-code custom fields).

    Full CRUD serializer for custom object field definitions.
    """

    business_object_code = serializers.CharField(
        source='business_object.code',
        read_only=True
    )

    field_type_display = serializers.CharField(
        source='get_field_type_display',
        read_only=True
    )

    class Meta(BaseModelSerializer.Meta):
        model = FieldDefinition
        fields = BaseModelSerializer.Meta.fields + [
            'business_object', 'business_object_code',
            'code', 'name',
            'field_type', 'field_type_display',
            'is_required', 'is_unique', 'is_readonly', 'is_system', 'is_searchable',
            'show_in_list', 'show_in_detail', 'show_in_filter',
            'sort_order',
            'column_width', 'min_column_width', 'fixed', 'sortable',
            'default_value', 'options',
            'reference_object', 'reference_display_field',
            'decimal_places', 'min_value', 'max_value',
            'max_length', 'placeholder', 'regex_pattern',
            'formula', 'sub_table_fields',
        ]


class FieldDefinitionListSerializer(BaseListSerializer):
    """Optimized serializer for field definition list views."""

    business_object_code = serializers.CharField(
        source='business_object.code',
        read_only=True
    )
    field_type_display = serializers.CharField(
        source='get_field_type_display',
        read_only=True
    )

    class Meta(BaseListSerializer.Meta):
        model = FieldDefinition
        fields = BaseListSerializer.Meta.fields + [
            'business_object_code',
            'code', 'name',
            'field_type', 'field_type_display',
            'is_required', 'is_readonly', 'is_system',
            'show_in_list', 'show_in_detail',
            'sort_order',
        ]


class PageLayoutSerializer(BaseModelSerializer):
    """
    Serializer for Page Layout.

    Handles form, list, and detail layout configurations.
    """

    business_object_code = serializers.CharField(
        source='business_object.code',
        read_only=True
    )
    business_object_name = serializers.CharField(
        source='business_object.name',
        read_only=True
    )
    layout_type_display = serializers.CharField(
        source='get_layout_type_display',
        read_only=True
    )

    class Meta(BaseModelSerializer.Meta):
        model = PageLayout
        fields = BaseModelSerializer.Meta.fields + [
            'business_object', 'business_object_code', 'business_object_name',
            'layout_code', 'layout_name', 'layout_type', 'layout_type_display',
            'layout_config',
            'is_default', 'is_active',
        ]

    def validate_layout_config(self, value):
        """Validate layout configuration JSON."""
        if not isinstance(value, dict):
            raise serializers.ValidationError('layout_config must be a JSON object')

        layout_type = self.initial_data.get('layout_type')
        if layout_type == 'form' and not value.get('sections'):
            raise serializers.ValidationError('Form layout must contain sections')

        if layout_type == 'list' and not value.get('columns'):
            raise serializers.ValidationError('List layout must contain columns')

        return value


class PageLayoutListSerializer(BaseListSerializer):
    """Optimized serializer for page layout list views."""

    business_object_code = serializers.CharField(
        source='business_object.code',
        read_only=True
    )
    layout_type_display = serializers.CharField(
        source='get_layout_type_display',
        read_only=True
    )

    class Meta(BaseListSerializer.Meta):
        model = PageLayout
        fields = BaseListSerializer.Meta.fields + [
            'business_object_code',
            'layout_code', 'layout_name',
            'layout_type', 'layout_type_display',
            'is_default', 'is_active',
        ]
