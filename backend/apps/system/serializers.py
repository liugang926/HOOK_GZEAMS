"""
Serializers for the metadata-driven low-code engine.

All serializers inherit from BaseModelSerializer to automatically get:
- Common field serialization (id, organization, is_deleted, timestamps, created_by)
- custom_fields handling
- Nested user/organization serialization
"""
from rest_framework import serializers
from apps.common.serializers.base import (
    BaseModelSerializer,
    BaseModelWithAuditSerializer
)
from apps.system.models import (
    BusinessObject,
    FieldDefinition,
    ModelFieldDefinition,
    PageLayout,
    LayoutHistory,
    DynamicData,
    DynamicSubTableData
)


class BusinessObjectSerializer(BaseModelSerializer):
    """
    Business Object serializer.

    Inherits from BaseModelSerializer which provides:
    - id, organization, is_deleted, deleted_at
    - created_at, updated_at, created_by (with nested user info)
    - custom_fields handling
    """

    field_count = serializers.ReadOnlyField()
    layout_count = serializers.ReadOnlyField()

    class Meta(BaseModelSerializer.Meta):
        model = BusinessObject
        fields = BaseModelSerializer.Meta.fields + [
            'code',
            'name',
            'name_en',
            'description',
            'is_hardcoded',
            'django_model_path',
            'enable_workflow',
            'enable_version',
            'enable_soft_delete',
            'default_form_layout',
            'default_list_layout',
            'table_name',
            'field_count',
            'layout_count',
        ]


class BusinessObjectDetailSerializer(BaseModelWithAuditSerializer):
    """
    Detailed Business Object serializer with full audit info.
    """

    field_count = serializers.ReadOnlyField()
    layout_count = serializers.ReadOnlyField()
    field_definitions = serializers.SerializerMethodField()
    page_layouts = serializers.SerializerMethodField()

    class Meta(BaseModelWithAuditSerializer.Meta):
        model = BusinessObject
        fields = BaseModelWithAuditSerializer.Meta.fields + [
            'code',
            'name',
            'name_en',
            'description',
            'enable_workflow',
            'enable_version',
            'enable_soft_delete',
            'is_hardcoded',
            'django_model_path',
            'default_form_layout',
            'default_list_layout',
            'table_name',
            'field_count',
            'layout_count',
            'field_definitions',
            'page_layouts',
        ]

    def get_field_definitions(self, obj):
        """Get field definitions for this business object.

        For hardcoded objects (is_hardcoded=True), use ModelFieldDefinition.
        For low-code objects (is_hardcoded=False), use FieldDefinition.
        """
        from .models import ModelFieldDefinition

        if obj.is_hardcoded:
            # For hardcoded objects, use ModelFieldDefinition
            fields = ModelFieldDefinition.objects.filter(
                business_object=obj,
                is_deleted=False
            ).order_by('sort_order')
            # Use ModelFieldDefinition serializer if available, otherwise use FieldDefinition
            return ModelFieldDefinitionSerializer(fields, many=True).data
        else:
            # For low-code objects, use FieldDefinition
            fields = obj.field_definitions.filter(is_deleted=False).order_by('sort_order')
            return FieldDefinitionSerializer(fields, many=True).data

    def get_page_layouts(self, obj):
        """Get page layouts for this business object."""
        layouts = obj.page_layouts.filter(is_active=True, is_deleted=False)
        return PageLayoutSerializer(layouts, many=True).data


class ModelFieldDefinitionSerializer(BaseModelSerializer):
    """
    Model Field Definition serializer for hardcoded Django model fields.

    This serializer handles the ModelFieldDefinition model which exposes
    fields from hardcoded Django models for use in the low-code system.
    """

    field_type_display = serializers.CharField(
        source='get_field_type_display',
        read_only=True
    )

    class Meta(BaseModelSerializer.Meta):
        model = ModelFieldDefinition
        fields = BaseModelSerializer.Meta.fields + [
            'business_object',
            'field_name',
            'display_name',
            'display_name_en',
            'field_type',
            'field_type_display',
            'is_required',
            'is_readonly',
            'is_editable',
            'is_unique',
            'django_field_type',
            'reference_model_path',
            'decimal_places',
            'max_digits',
            'max_length',
            'sort_order',
            'show_in_list',
            'show_in_detail',
            'show_in_form',
            'show_in_filter',
        ]


class FieldDefinitionSerializer(BaseModelSerializer):
    """Field Definition serializer."""

    field_type_display = serializers.CharField(
        source='get_field_type_display',
        read_only=True
    )

    class Meta(BaseModelSerializer.Meta):
        model = FieldDefinition
        fields = BaseModelSerializer.Meta.fields + [
            'business_object',
            'code',
            'name',
            'field_type',
            'field_type_display',
            'is_required',
            'is_unique',
            'is_readonly',
            'is_system',
            'is_searchable',
            'show_in_list',
            'show_in_detail',
            'show_in_filter',
            'sort_order',
            'column_width',
            'min_column_width',
            'fixed',
            'sortable',
            'default_value',
            'options',
            'reference_object',
            'reference_display_field',
            'decimal_places',
            'min_value',
            'max_value',
            'max_length',
            'placeholder',
            'regex_pattern',
            'formula',
            'sub_table_fields',
        ]


class FieldDefinitionDetailSerializer(BaseModelSerializer):
    """Detailed Field Definition serializer with sub-table fields expanded."""

    field_type_display = serializers.CharField(
        source='get_field_type_display',
        read_only=True
    )
    business_object_name = serializers.CharField(
        source='business_object.name',
        read_only=True
    )

    class Meta(BaseModelSerializer.Meta):
        model = FieldDefinition
        fields = BaseModelSerializer.Meta.fields + [
            'business_object',
            'business_object_name',
            'code',
            'name',
            'field_type',
            'field_type_display',
            'is_required',
            'is_unique',
            'is_readonly',
            'is_system',
            'is_searchable',
            'show_in_list',
            'show_in_detail',
            'show_in_filter',
            'sort_order',
            'column_width',
            'min_column_width',
            'fixed',
            'sortable',
            'default_value',
            'options',
            'reference_object',
            'reference_display_field',
            'decimal_places',
            'min_value',
            'max_value',
            'max_length',
            'placeholder',
            'regex_pattern',
            'formula',
            'sub_table_fields',
        ]


class PageLayoutSerializer(BaseModelSerializer):
    """Page Layout serializer."""

    layout_type_display = serializers.CharField(
        source='get_layout_type_display',
        read_only=True
    )
    status_display = serializers.CharField(
        source='get_status_display',
        read_only=True
    )
    published_by_info = serializers.SerializerMethodField()
    business_object_name = serializers.CharField(
        source='business_object.name',
        read_only=True
    )

    class Meta(BaseModelSerializer.Meta):
        model = PageLayout
        fields = BaseModelSerializer.Meta.fields + [
            'business_object',
            'business_object_name',
            'layout_code',
            'layout_name',
            'layout_type',
            'layout_type_display',
            'description',
            'layout_config',
            'status',
            'status_display',
            'version',
            'parent_version',
            'is_default',
            'is_active',
            'published_at',
            'published_by',
            'published_by_info',
        ]

    def get_published_by_info(self, obj):
        """Get published_by user info."""
        if obj.published_by:
            return {
                'id': str(obj.published_by.id),
                'username': obj.published_by.username,
                'email': obj.published_by.email,
            }
        return None

    def validate_layout_config(self, value):
        """Validate layout configuration."""
        from apps.system.validators import validate_layout_config
        try:
            # Get layout_type from parent data if available
            layout_type = self.initial_data.get('layout_type', 'form')
            validate_layout_config(value, layout_type)
        except Exception as e:
            raise serializers.ValidationError(str(e))
        return value


class PageLayoutDetailSerializer(BaseModelWithAuditSerializer):
    """Detailed Page Layout serializer with full audit info."""

    layout_type_display = serializers.CharField(
        source='get_layout_type_display',
        read_only=True
    )
    status_display = serializers.CharField(
        source='get_status_display',
        read_only=True
    )
    published_by_info = serializers.SerializerMethodField()
    business_object = BusinessObjectSerializer(read_only=True)
    history_count = serializers.SerializerMethodField()

    class Meta(BaseModelWithAuditSerializer.Meta):
        model = PageLayout
        fields = BaseModelWithAuditSerializer.Meta.fields + [
            'business_object',
            'layout_code',
            'layout_name',
            'layout_type',
            'layout_type_display',
            'description',
            'layout_config',
            'status',
            'status_display',
            'version',
            'parent_version',
            'is_default',
            'is_active',
            'published_at',
            'published_by',
            'published_by_info',
            'history_count',
        ]

    def get_published_by_info(self, obj):
        """Get published_by user info."""
        if obj.published_by:
            return {
                'id': str(obj.published_by.id),
                'username': obj.published_by.username,
                'email': obj.published_by.email,
            }
        return None

    def get_history_count(self, obj):
        """Get number of history records."""
        return obj.histories.count()


class LayoutHistorySerializer(BaseModelSerializer):
    """Layout History serializer for tracking version changes."""

    action_display = serializers.CharField(
        source='get_action_display',
        read_only=True
    )
    published_by_info = serializers.SerializerMethodField()

    class Meta(BaseModelSerializer.Meta):
        model = LayoutHistory
        fields = BaseModelSerializer.Meta.fields + [
            'layout',
            'version',
            'config_snapshot',
            'action',
            'action_display',
            'change_summary',
            'published_by',
            'published_by_info',
        ]

    def get_published_by_info(self, obj):
        """Get published_by user info."""
        if obj.published_by:
            return {
                'id': str(obj.published_by.id),
                'username': obj.published_by.username,
                'email': obj.published_by.email,
            }
        return None


class DynamicDataSerializer(BaseModelSerializer):
    """Dynamic Data serializer for list views."""

    business_object_code = serializers.CharField(
        source='business_object.code',
        read_only=True
    )
    business_object_name = serializers.CharField(
        source='business_object.name',
        read_only=True
    )
    status_display = serializers.CharField(
        source='get_status_display',
        read_only=True
    )

    class Meta(BaseModelSerializer.Meta):
        model = DynamicData
        fields = BaseModelSerializer.Meta.fields + [
            'business_object',
            'business_object_code',
            'business_object_name',
            'data_no',
            'status',
            'status_display',
            'dynamic_fields',
            'submitted_at',
            'approved_at',
            'approved_by',
        ]


class DynamicDataDetailSerializer(BaseModelWithAuditSerializer):
    """
    Detailed Dynamic Data serializer with full audit info.
    Used for detail views and single record retrieval.
    """

    business_object = BusinessObjectSerializer(read_only=True)
    approved_by_info = serializers.SerializerMethodField()

    class Meta(BaseModelWithAuditSerializer.Meta):
        model = DynamicData
        fields = BaseModelWithAuditSerializer.Meta.fields + [
            'business_object',
            'data_no',
            'status',
            'dynamic_fields',
            'submitted_at',
            'approved_at',
            'approved_by',
            'approved_by_info',
        ]

    def get_approved_by_info(self, obj):
        """Get approved_by user info."""
        if obj.approved_by:
            return {
                'id': str(obj.approved_by.id),
                'username': obj.approved_by.username,
                'email': obj.approved_by.email,
            }
        return None


class DynamicDataCreateSerializer(serializers.Serializer):
    """
    Serializer for creating dynamic data.

    Accepts business_object_code and dynamic_fields.
    """

    business_object_code = serializers.CharField(
        max_length=50,
        write_only=True,
        help_text='Business object code'
    )
    dynamic_fields = serializers.JSONField(
        required=True,
        help_text='Dynamic field data'
    )
    status = serializers.CharField(
        max_length=50,
        required=False,
        default='draft',
        help_text='Initial status'
    )

    def validate_business_object_code(self, value):
        """Validate business object exists."""
        try:
            BusinessObject.objects.get(code=value, is_deleted=False)
        except BusinessObject.DoesNotExist:
            raise serializers.ValidationError(
                f"Business object '{value}' does not exist."
            )
        return value


class DynamicDataUpdateSerializer(serializers.Serializer):
    """Serializer for updating dynamic data."""

    dynamic_fields = serializers.JSONField(
        required=False,
        help_text='Dynamic field data to update'
    )
    status = serializers.CharField(
        max_length=50,
        required=False,
        help_text='Status update'
    )


class DynamicSubTableDataSerializer(BaseModelSerializer):
    """Dynamic Sub-Table Data serializer."""

    field_definition_code = serializers.CharField(
        source='field_definition.code',
        read_only=True
    )
    parent_data_no = serializers.CharField(
        source='parent_data.data_no',
        read_only=True
    )

    class Meta(BaseModelSerializer.Meta):
        model = DynamicSubTableData
        fields = BaseModelSerializer.Meta.fields + [
            'parent_data',
            'parent_data_no',
            'field_definition',
            'field_definition_code',
            'row_order',
            'row_data',
        ]


class DynamicSubTableDataCreateSerializer(serializers.Serializer):
    """Serializer for creating sub-table rows."""

    row_order = serializers.IntegerField(required=False, default=0)
    row_data = serializers.JSONField(required=True)


class DynamicSubTableDataUpdateSerializer(serializers.Serializer):
    """Serializer for updating sub-table rows."""

    row_data = serializers.JSONField(required=False)
    row_order = serializers.IntegerField(required=False)
