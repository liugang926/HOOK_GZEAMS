"""
Serializers for the metadata-driven low-code engine.

All serializers inherit from BaseModelSerializer to automatically get:
- Common field serialization (id, organization, is_deleted, timestamps, created_by)
- custom_fields handling
- Nested user/organization serialization
"""
from uuid import UUID
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
    DynamicSubTableData,
    UserColumnPreference,
    TabConfig,
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
            'object_role',
            'is_top_level_navigable',
            'allow_standalone_query',
            'allow_standalone_route',
            'inherit_permissions',
            'inherit_workflow',
            'inherit_status',
            'inherit_lifecycle',
            'enable_workflow',
            'enable_version',
            'enable_soft_delete',
            'default_form_layout',
            'default_list_layout',
            'table_name',
            'field_count',
            'layout_count',
            'menu_category',
            'is_menu_hidden',
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
            'object_role',
            'is_top_level_navigable',
            'allow_standalone_query',
            'allow_standalone_route',
            'inherit_permissions',
            'inherit_workflow',
            'inherit_status',
            'inherit_lifecycle',
            'default_form_layout',
            'default_list_layout',
            'table_name',
            'field_count',
            'layout_count',
            'field_definitions',
            'page_layouts',
            'menu_category',
            'is_menu_hidden',
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
        ]


class FieldDefinitionSerializer(BaseModelSerializer):
    """Field Definition serializer."""

    field_type_display = serializers.CharField(
        source='get_field_type_display',
        read_only=True
    )
    relation_display_mode_display = serializers.CharField(
        source='get_relation_display_mode_display',
        read_only=True,
        allow_null=True
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
            'show_in_form',
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
            # Reverse relation handling fields (DEPRECATED — use ObjectRelationDefinition)
            'is_reverse_relation',
            'reverse_relation_model',
            'reverse_relation_field',
            'relation_display_mode',
            'relation_display_mode_display',
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
    relation_display_mode_display = serializers.CharField(
        source='get_relation_display_mode_display',
        read_only=True,
        allow_null=True
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
            'show_in_form',
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
            # Reverse relation handling fields (DEPRECATED — use ObjectRelationDefinition)
            'is_reverse_relation',
            'reverse_relation_model',
            'reverse_relation_field',
            'relation_display_mode',
            'relation_display_mode_display',
        ]


class PageLayoutSerializer(BaseModelSerializer):
    """Page Layout serializer."""

    _MODE_TO_LAYOUT_TYPE = {
        'edit': 'form',
        # Single-layout model: readonly/search requests also persist to shared form layout.
        'readonly': 'form',
        'search': 'form',
        'detail': 'form',
        'form': 'form',
    }
    _LAYOUT_TYPE_TO_MODE = {
        'form': 'edit',
        # Legacy layout types are normalized to the shared edit mode on write.
        'detail': 'edit',
        'list': 'edit',
        'search': 'edit',
    }

    layout_type_display = serializers.CharField(
        source='get_layout_type_display',
        read_only=True
    )
    # New mode field for unified layout system
    view_mode_display = serializers.CharField(
        source='get_view_mode_display',
        read_only=True
    )
    mode_display = serializers.CharField(
        source='get_mode_display',
        read_only=True
    )
    status_display = serializers.CharField(
        source='get_status_display',
        read_only=True
    )
    priority_display = serializers.CharField(
        source='get_priority_display',
        read_only=True
    )
    context_type_display = serializers.CharField(
        source='get_context_type_display',
        read_only=True,
        allow_null=True
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
            'view_mode',
            'view_mode_display',
            'mode',  # New unified mode field
            'mode_display',  # Display value for mode
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
            # Layout priority and context fields
            'priority',
            'priority_display',
            'context_type',
            'context_type_display',
            'diff_config',
        ]

    @classmethod
    def _is_uuid_like(cls, value) -> bool:
        try:
            UUID(str(value))
            return True
        except Exception:
            return False

    @classmethod
    def _normalize_mode(cls, raw_mode):
        mode = str(raw_mode or '').strip().lower()
        if mode in cls._MODE_TO_LAYOUT_TYPE:
            return 'edit'
        return None

    @classmethod
    def _normalize_layout_type(cls, raw_layout_type):
        layout_type = str(raw_layout_type or '').strip().lower()
        if layout_type in cls._LAYOUT_TYPE_TO_MODE:
            return 'form'
        return None

    def _resolve_business_object_id(self, raw_value):
        if raw_value in (None, ''):
            return raw_value
        if self._is_uuid_like(raw_value):
            return str(raw_value)

        by_code = BusinessObject.objects.filter(
            code=str(raw_value).strip(),
            is_deleted=False
        ).values_list('id', flat=True).first()
        if by_code:
            return str(by_code)
        return raw_value

    def to_internal_value(self, data):
        """
        Backward-compatible payload normalization for page-layout create/update:
        - layout_mode/layoutMode -> mode
        - auto-sync mode <-> layout_type
        - business_object accepts both UUID and object code
        """
        if hasattr(data, 'copy'):
            normalized = data.copy()
        elif isinstance(data, dict):
            normalized = dict(data)
        else:
            normalized = data

        if isinstance(normalized, dict):
            legacy_mode = (
                normalized.get('mode')
                or normalized.get('layout_mode')
                or normalized.get('layoutMode')
            )
            mode = self._normalize_mode(legacy_mode)
            if mode:
                normalized['mode'] = mode

            raw_layout_type = normalized.get('layout_type') or normalized.get('layoutType')
            layout_type = self._normalize_layout_type(raw_layout_type)

            if mode and not layout_type:
                normalized['layout_type'] = self._MODE_TO_LAYOUT_TYPE.get(mode, 'form')
            elif layout_type and not mode:
                normalized['mode'] = self._LAYOUT_TYPE_TO_MODE.get(layout_type, 'edit')
            elif mode and layout_type:
                normalized['layout_type'] = self._MODE_TO_LAYOUT_TYPE.get(mode, layout_type)

            if 'business_object' not in normalized and 'businessObject' in normalized:
                normalized['business_object'] = normalized.get('businessObject')

            if 'business_object' in normalized:
                normalized['business_object'] = self._resolve_business_object_id(
                    normalized.get('business_object')
                )

        return super().to_internal_value(normalized)

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
        from apps.system.validators import (
            validate_layout_config,
            normalize_layout_config_structure,
            validate_layout_workbench_config,
        )
        try:
            # Fill missing section/field ids for legacy payload compatibility.
            value = normalize_layout_config_structure(value)

            # Sanitize obvious bad field codes (e.g. "asset code" -> "asset_code") before validation/persistence.
            # This is the backend safety-net; the frontend designer also normalizes before save.
            business_object = None
            try:
                bo_id = None
                if isinstance(getattr(self, 'initial_data', None), dict):
                    bo_id = self.initial_data.get('business_object')
                if bo_id:
                    business_object = (
                        BusinessObject.objects.filter(id=bo_id).first()
                        or BusinessObject.objects.filter(code=str(bo_id)).first()
                    )
                if not business_object and getattr(self, 'instance', None) is not None:
                    business_object = getattr(self.instance, 'business_object', None)
            except Exception:
                business_object = None

            if business_object:
                from apps.system.validators import sanitize_layout_config_field_codes
                allowed = set()
                # Union of hardcoded + custom fields (some deployments allow custom fields on hardcoded objects)
                try:
                    allowed.update(ModelFieldDefinition.objects.filter(business_object=business_object).values_list('field_name', flat=True))
                except Exception:
                    pass
                try:
                    allowed.update(FieldDefinition.objects.filter(business_object=business_object).values_list('code', flat=True))
                except Exception:
                    pass
                if allowed:
                    value = sanitize_layout_config_field_codes(value, allowed)

            # Prefer mode over layout_type for validation
            mode = self._normalize_mode(self.initial_data.get('mode'))
            layout_type = self._normalize_layout_type(self.initial_data.get('layout_type'))

            # Use mode if available, otherwise derive from layout_type
            if mode:
                from apps.system.validators import validate_layout_config_by_mode
                validate_layout_config_by_mode(value, mode)
            else:
                validate_layout_config(value, layout_type or 'form')

            validate_layout_workbench_config(value)
        except Exception as e:
            raise serializers.ValidationError(str(e))
        return value


class PageLayoutDetailSerializer(BaseModelWithAuditSerializer):
    """Detailed Page Layout serializer with full audit info."""

    layout_type_display = serializers.CharField(
        source='get_layout_type_display',
        read_only=True
    )
    # New mode field for unified layout system
    view_mode_display = serializers.CharField(
        source='get_view_mode_display',
        read_only=True
    )
    mode_display = serializers.CharField(
        source='get_mode_display',
        read_only=True
    )
    status_display = serializers.CharField(
        source='get_status_display',
        read_only=True
    )
    priority_display = serializers.CharField(
        source='get_priority_display',
        read_only=True
    )
    context_type_display = serializers.CharField(
        source='get_context_type_display',
        read_only=True,
        allow_null=True
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
            'view_mode',
            'view_mode_display',
            'mode',  # New unified mode field
            'mode_display',  # Display value for mode
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
            # Layout priority and context fields
            'priority',
            'priority_display',
            'context_type',
            'context_type_display',
            'diff_config',
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


# ============================================================================
# Column Preference and Tab Configuration Serializers
# ============================================================================

from apps.common.serializers.base import BaseListSerializer


class UserColumnPreferenceSerializer(BaseModelSerializer):
    """
    Serializer for User Column Preference.

    Handles user-specific column display configurations for list views.
    """

    username = serializers.CharField(
        source='user.username',
        read_only=True
    )

    class Meta(BaseModelSerializer.Meta):
        model = UserColumnPreference
        fields = BaseModelSerializer.Meta.fields + [
            'user',
            'username',
            'object_code',
            'column_config',
            'config_name',
            'is_default',
        ]

    def validate_column_config(self, value):
        """Validate column_config is a valid JSON object."""
        if not isinstance(value, dict):
            raise serializers.ValidationError('column_config must be a JSON object')

        # Validate structure
        if 'columns' in value and not isinstance(value['columns'], list):
            raise serializers.ValidationError('columns must be a list')

        if 'columnOrder' in value and not isinstance(value['columnOrder'], list):
            raise serializers.ValidationError('columnOrder must be a list')

        return value


class UserColumnPreferenceListSerializer(BaseListSerializer):
    """
    Optimized serializer for column preference list views.
    """

    username = serializers.CharField(
        source='user.username',
        read_only=True
    )

    class Meta(BaseListSerializer.Meta):
        model = UserColumnPreference
        fields = BaseListSerializer.Meta.fields + [
            'user',
            'username',
            'object_code',
            'config_name',
            'is_default',
        ]


class UserColumnPreferenceUpsertSerializer(serializers.Serializer):
    """
    Serializer for upserting column preferences.

    Used by the API endpoint that saves/updates user preferences.
    """

    column_config = serializers.JSONField(
        required=True,
        help_text='Column configuration with columns and columnOrder'
    )

    def validate_column_config(self, value):
        """Validate column_config structure."""
        if not isinstance(value, dict):
            raise serializers.ValidationError('column_config must be a JSON object')

        # Ensure columns is a list
        if 'columns' in value and not isinstance(value['columns'], list):
            raise serializers.ValidationError('columns must be a list')

        # Ensure columnOrder is a list
        if 'columnOrder' in value and not isinstance(value['columnOrder'], list):
            raise serializers.ValidationError('columnOrder must be a list')

        # Validate each column has field_code
        if 'columns' in value:
            for col in value['columns']:
                if not isinstance(col, dict):
                    raise serializers.ValidationError('Each column must be an object')
                if 'field_code' not in col and 'prop' not in col:
                    raise serializers.ValidationError('Each column must have field_code or prop')

        return value


class TabConfigSerializer(BaseModelSerializer):
    """
    Serializer for Tab Configuration.

    Handles tab layout settings for forms and detail pages.
    """

    business_object_code = serializers.CharField(
        source='business_object.code',
        read_only=True
    )
    business_object_name = serializers.CharField(
        source='business_object.name',
        read_only=True
    )
    position_display = serializers.CharField(
        source='get_position_display',
        read_only=True
    )
    type_style_display = serializers.CharField(
        source='get_type_style_display',
        read_only=True
    )

    class Meta(BaseModelSerializer.Meta):
        model = TabConfig
        fields = BaseModelSerializer.Meta.fields + [
            'business_object',
            'business_object_code',
            'business_object_name',
            'name',
            'position',
            'position_display',
            'type_style',
            'type_style_display',
            'stretch',
            'lazy',
            'animated',
            'addable',
            'draggable',
            'tabs_config',
            'is_active',
        ]

    def validate_tabs_config(self, value):
        """Validate tabs_config is a valid JSON array."""
        if not isinstance(value, list):
            raise serializers.ValidationError('tabs_config must be a JSON array')

        # Validate each tab has required fields
        for tab in value:
            if not isinstance(tab, dict):
                raise serializers.ValidationError('Each tab must be an object')
            if 'id' not in tab:
                raise serializers.ValidationError('Each tab must have an id')
            if 'title' not in tab:
                raise serializers.ValidationError('Each tab must have a title')

        return value


class TabConfigListSerializer(BaseListSerializer):
    """
    Optimized serializer for tab configuration list views.
    """

    business_object_code = serializers.CharField(
        source='business_object.code',
        read_only=True
    )
    position_display = serializers.CharField(
        source='get_position_display',
        read_only=True
    )

    class Meta(BaseListSerializer.Meta):
        model = TabConfig
        fields = BaseListSerializer.Meta.fields + [
            'business_object',
            'business_object_code',
            'name',
            'position',
            'position_display',
            'type_style',
            'is_active',
        ]


# ============================================================================
# Business Rule Serializers
# ============================================================================

class BusinessRuleSerializer(BaseModelSerializer):
    """
    Serializer for Business Rule CRUD operations.
    """

    business_object_code = serializers.CharField(
        source='business_object.code',
        read_only=True
    )
    business_object_name = serializers.CharField(
        source='business_object.name',
        read_only=True
    )
    rule_type_display = serializers.CharField(
        source='get_rule_type_display',
        read_only=True
    )

    class Meta(BaseModelSerializer.Meta):
        from apps.system.models import BusinessRule
        model = BusinessRule
        fields = BaseModelSerializer.Meta.fields + [
            'business_object',
            'business_object_code',
            'business_object_name',
            'rule_code',
            'rule_name',
            'description',
            'rule_type',
            'rule_type_display',
            'priority',
            'is_active',
            'condition',
            'action',
            'target_field',
            'trigger_events',
            'error_message',
            'error_message_en',
        ]


class BusinessRuleCreateSerializer(BaseModelSerializer):
    """
    Serializer for creating Business Rules.
    Accepts business_object_code instead of business_object ID.
    """

    business_object_code = serializers.CharField(write_only=True)

    class Meta(BaseModelSerializer.Meta):
        from apps.system.models import BusinessRule
        model = BusinessRule
        fields = BaseModelSerializer.Meta.fields + [
            'business_object_code',
            'rule_code',
            'rule_name',
            'description',
            'rule_type',
            'priority',
            'is_active',
            'condition',
            'action',
            'target_field',
            'trigger_events',
            'error_message',
            'error_message_en',
        ]

    def create(self, validated_data):
        from apps.system.models import BusinessObject
        
        bo_code = validated_data.pop('business_object_code', None)
        if bo_code:
            try:
                business_object = BusinessObject.objects.get(code=bo_code, is_deleted=False)
                validated_data['business_object'] = business_object
            except BusinessObject.DoesNotExist:
                raise serializers.ValidationError({
                    'business_object_code': f"Business object '{bo_code}' not found."
                })
        return super().create(validated_data)


class RuleExecutionSerializer(BaseModelSerializer):
    """
    Read-only serializer for Rule Execution logs.
    """

    rule_code = serializers.CharField(source='rule.rule_code', read_only=True)
    rule_name = serializers.CharField(source='rule.rule_name', read_only=True)

    class Meta(BaseModelSerializer.Meta):
        from apps.system.models import RuleExecution
        model = RuleExecution
        fields = BaseModelSerializer.Meta.fields + [
            'rule',
            'rule_code',
            'rule_name',
            'target_record_id',
            'target_record_type',
            'trigger_event',
            'input_data',
            'condition_result',
            'action_executed',
            'execution_result',
            'executed_at',
            'execution_time_ms',
            'has_error',
            'error_message',
        ]
        read_only_fields = fields


class RuleEvaluationRequestSerializer(serializers.Serializer):
    """
    Request serializer for rule evaluation endpoints.
    """

    record = serializers.JSONField(
        help_text='Record data to evaluate rules against'
    )
    event = serializers.ChoiceField(
        choices=['create', 'update', 'submit', 'approve'],
        default='update',
        help_text='Event type for rule evaluation'
    )


# =============================================================================
# Configuration Package Serializers
# =============================================================================

class ConfigPackageSerializer(BaseModelSerializer):
    """
    Serializer for Configuration Package read operations.
    """

    exported_by_name = serializers.CharField(
        source='exported_by.username',
        read_only=True,
        allow_null=True
    )
    package_type_display = serializers.CharField(
        source='get_package_type_display',
        read_only=True
    )
    object_count = serializers.SerializerMethodField()

    class Meta(BaseModelSerializer.Meta):
        from apps.system.models import ConfigPackage
        model = ConfigPackage
        fields = BaseModelSerializer.Meta.fields + [
            'name',
            'version',
            'description',
            'package_type',
            'package_type_display',
            'included_objects',
            'object_count',
            'exported_by',
            'exported_by_name',
            'exported_at',
            'source_environment',
            'checksum',
            'is_valid',
            'validation_errors',
        ]
        read_only_fields = [
            'exported_at', 'checksum', 'is_valid', 'validation_errors'
        ]

    def get_object_count(self, obj):
        return len(obj.included_objects or [])


class ConfigPackageExportSerializer(serializers.Serializer):
    """
    Request serializer for exporting a configuration package.
    """

    name = serializers.CharField(max_length=100)
    version = serializers.CharField(max_length=20)
    description = serializers.CharField(required=False, allow_blank=True)
    object_codes = serializers.ListField(
        child=serializers.CharField(),
        help_text='List of business object codes to export'
    )
    package_type = serializers.ChoiceField(
        choices=['full', 'partial', 'diff'],
        default='full'
    )


class ConfigPackageImportSerializer(serializers.Serializer):
    """
    Request serializer for importing a configuration package.
    """

    package_id = serializers.UUIDField(
        required=False,
        help_text='ID of existing package to import'
    )
    config_data = serializers.JSONField(
        required=False,
        help_text='Configuration data if uploading directly'
    )
    strategy = serializers.ChoiceField(
        choices=['merge', 'replace', 'skip'],
        default='merge',
        help_text='Import strategy'
    )
    target_environment = serializers.CharField(
        required=False,
        allow_blank=True
    )


class ConfigImportLogSerializer(BaseModelSerializer):
    """
    Serializer for Configuration Import Log.
    """

    package_name = serializers.CharField(
        source='package.name',
        read_only=True
    )
    package_version = serializers.CharField(
        source='package.version',
        read_only=True
    )
    imported_by_name = serializers.CharField(
        source='imported_by.username',
        read_only=True,
        allow_null=True
    )
    status_display = serializers.CharField(
        source='get_status_display',
        read_only=True
    )
    strategy_display = serializers.CharField(
        source='get_import_strategy_display',
        read_only=True
    )

    class Meta(BaseModelSerializer.Meta):
        from apps.system.models import ConfigImportLog
        model = ConfigImportLog
        fields = BaseModelSerializer.Meta.fields + [
            'package',
            'package_name',
            'package_version',
            'imported_by',
            'imported_by_name',
            'imported_at',
            'target_environment',
            'import_strategy',
            'strategy_display',
            'status',
            'status_display',
            'import_result',
            'objects_created',
            'objects_updated',
            'objects_skipped',
            'objects_failed',
            'can_rollback',
            'rolled_back_at',
            'error_message',
        ]
        read_only_fields = fields


class ConfigDiffSerializer(serializers.Serializer):
    """
    Serializer for configuration diff results.
    """

    items = serializers.ListField(child=serializers.DictField())
    summary = serializers.DictField()


# ============================================================================
# System File Serializers
# ============================================================================

class SystemFileSerializer(BaseModelSerializer):
    """
    Full serializer for SystemFile model with thumbnail and watermark URL.
    """

    url = serializers.CharField(read_only=True)
    thumbnail_url = serializers.SerializerMethodField()
    watermarked_url = serializers.SerializerMethodField()

    class Meta(BaseModelSerializer.Meta):
        from apps.system.models import SystemFile
        model = SystemFile
        fields = BaseModelSerializer.Meta.fields + [
            'file_name',
            'file_path',
            'file_size',
            'file_type',
            'file_extension',
            'url',
            'thumbnail_url',
            'thumbnail_path',
            'watermarked_url',
            'watermarked_path',
            'width',
            'height',
            'is_compressed',
            'original_file_id',
            'object_code',
            'instance_id',
            'field_code',
            'biz_type',
            'biz_id',
            'description',
            'file_hash',
        ]

    def get_thumbnail_url(self, obj):
        if obj.thumbnail_path:
            from django.conf import settings
            return f"{settings.MEDIA_URL}{obj.thumbnail_path}"
        return None

    def get_watermarked_url(self, obj):
        if obj.watermarked_path:
            from django.conf import settings
            return f"{settings.MEDIA_URL}{obj.watermarked_path}"
        return None


class SystemFileListSerializer(BaseModelSerializer):
    """
    Lightweight serializer for file list views.
    """

    url = serializers.CharField(read_only=True)
    thumbnail_url = serializers.SerializerMethodField()

    class Meta(BaseModelSerializer.Meta):
        from apps.system.models import SystemFile
        model = SystemFile
        fields = [
            'id',
            'file_name',
            'file_size',
            'file_type',
            'file_extension',
            'url',
            'thumbnail_url',
            'width',
            'height',
            'object_code',
            'instance_id',
            'field_code',
            'created_at',
        ]

    def get_thumbnail_url(self, obj):
        if obj.thumbnail_path:
            from django.conf import settings
            return f"{settings.MEDIA_URL}{obj.thumbnail_path}"
        return None


class SystemFileUploadSerializer(serializers.Serializer):
    """
    Serializer for file upload requests.
    """

    file = serializers.FileField(
        max_length=52428800,
        help_text="File to upload"
    )
    object_code = serializers.CharField(required=False, max_length=100)
    instance_id = serializers.UUIDField(required=False)
    field_code = serializers.CharField(required=False, max_length=100)
    description = serializers.CharField(required=False, allow_blank=True)

    def validate_file(self, value):
        if value.size == 0:
            raise serializers.ValidationError("File cannot be empty.")
        if not value.name:
            raise serializers.ValidationError("File must have a name.")
        return value


class SystemFileBatchDeleteSerializer(serializers.Serializer):
    """
    Serializer for batch delete requests.
    """

    ids = serializers.ListField(
        child=serializers.UUIDField(),
        min_length=1,
        help_text="List of file IDs to delete"
    )

    def validate_ids(self, value):
        if not value:
            raise serializers.ValidationError("At least one file ID must be provided.")
        return value


# ============================================================================
# Internationalization (i18n) Serializers
# ============================================================================

class LanguageSerializer(BaseModelSerializer):
    """
    Serializer for Language model.

    Handles language configuration for the i18n system.
    """

    class Meta(BaseModelSerializer.Meta):
        from apps.system.models import Language
        model = Language
        fields = BaseModelSerializer.Meta.fields + [
            'code',
            'name',
            'native_name',
            'is_default',
            'is_active',
            'sort_order',
            'flag_emoji',
            'locale',
        ]


class LanguageListSerializer(BaseModelSerializer):
    """
    Lightweight serializer for language list views.
    """

    class Meta(BaseModelSerializer.Meta):
        from apps.system.models import Language
        model = Language
        fields = [
            'id',
            'code',
            'name',
            'native_name',
            'is_default',
            'is_active',
            'sort_order',
            'flag_emoji',
            'locale',
        ]


class TranslationSerializer(BaseModelSerializer):
    """
    Serializer for Translation model.

    Handles both namespace/key translations and GenericForeignKey translations.
    """

    content_type_model = serializers.CharField(
        source='content_type.model',
        read_only=True,
        allow_null=True
    )

    class Meta(BaseModelSerializer.Meta):
        from apps.system.models import Translation
        model = Translation
        fields = BaseModelSerializer.Meta.fields + [
            'namespace',
            'key',
            'content_type',
            'object_id',
            'content_type_model',
            'field_name',
            'language_code',
            'text',
            'context',
            'type',
            'is_system',
        ]


class TranslationListSerializer(BaseModelSerializer):
    """
    Optimized serializer for translation list views.
    """

    content_type_model = serializers.CharField(
        source='content_type.model',
        read_only=True,
        allow_null=True
    )

    class Meta(BaseModelSerializer.Meta):
        from apps.system.models import Translation
        model = Translation
        fields = [
            'id',
            'namespace',
            'key',
            'content_type_model',
            'object_id',
            'field_name',
            'language_code',
            'text',
            'context',
            'type',
            'is_system',
            'created_at',
            'updated_at',
        ]


class TranslationCreateSerializer(serializers.Serializer):
    """
    Serializer for creating translations with flexible input.
    """

    namespace = serializers.CharField(required=False, allow_blank=True, default='')
    key = serializers.CharField(required=False, allow_blank=True, default='')
    content_type = serializers.CharField(required=False, allow_null=True, allow_blank=True)
    object_id = serializers.UUIDField(required=False, allow_null=True)
    field_name = serializers.CharField(required=False, allow_blank=True, default='')
    language_code = serializers.CharField(max_length=10)
    text = serializers.CharField()
    context = serializers.CharField(required=False, allow_blank=True, default='')
    type = serializers.CharField(required=False, default='label')

    def validate(self, data):
        """Validate that either namespace/key or content_type/object_id is provided."""
        namespace = data.get('namespace', '')
        key = data.get('key', '')
        content_type = data.get('content_type')
        object_id = data.get('object_id')

        has_namespace_key = bool(namespace and key)
        has_gfk = bool(content_type and object_id is not None)

        if not has_namespace_key and not has_gfk:
            raise serializers.ValidationError(
                "Either namespace/key or content_type/object_id must be provided."
            )

        return data


class TranslationBulkSerializer(serializers.Serializer):
    """
    Serializer for bulk translation operations.
    """

    translations = serializers.ListField(
        child=TranslationCreateSerializer(),
        help_text="List of translations to create/update"
    )

    def validate_translations(self, value):
        """Validate translations list."""
        if not value:
            raise serializers.ValidationError("At least one translation must be provided.")
        if len(value) > 1000:
            raise serializers.ValidationError("Maximum 1000 translations per bulk operation.")
        return value


# ============================================================================
# Closed-Loop Dashboard Snapshot Serializers
# ============================================================================

class ClosedLoopDashboardSnapshotListSerializer(BaseModelSerializer):
    """Serializer for closed-loop dashboard snapshot list rows."""

    class Meta(BaseModelSerializer.Meta):
        from apps.system.models import ClosedLoopDashboardSnapshot
        model = ClosedLoopDashboardSnapshot
        fields = BaseModelSerializer.Meta.fields + [
            'dashboard_code',
            'label',
            'window_key',
            'object_codes',
        ]


class ClosedLoopDashboardSnapshotDetailSerializer(ClosedLoopDashboardSnapshotListSerializer):
    """Serializer returning the full stored dashboard payload."""

    payload = serializers.SerializerMethodField()

    class Meta(ClosedLoopDashboardSnapshotListSerializer.Meta):
        fields = ClosedLoopDashboardSnapshotListSerializer.Meta.fields + ['payload']

    def get_payload(self, obj):
        return {
            'overview': obj.overview_payload or {},
            'by_object_items': obj.by_object_payload or [],
            'queues': obj.queues_payload or [],
            'bottlenecks': obj.bottlenecks_payload or [],
        }


class ClosedLoopDashboardSnapshotCreateSerializer(serializers.Serializer):
    """Validate snapshot create requests."""

    label = serializers.CharField(max_length=120)
    window_key = serializers.ChoiceField(choices=('7d', '30d', '90d'))
    object_codes = serializers.ListField(
        child=serializers.CharField(max_length=100),
        required=False,
        allow_empty=True,
    )

    def validate_label(self, value):
        normalized_value = str(value).strip()
        if not normalized_value:
            raise serializers.ValidationError("Snapshot label is required.")
        return normalized_value


class ObjectTranslationSerializer(serializers.Serializer):
    """
    Serializer for object-scoped translation operations.

    Used for getting/setting all translations for a specific object.
    """

    translations = serializers.DictField(
        child=serializers.DictField(child=serializers.CharField()),
        help_text="Nested dict: {locale: {field: translation}}"
    )

    def validate_translations(self, value):
        """Validate translations structure."""
        if not isinstance(value, dict):
            raise serializers.ValidationError("Translations must be a dictionary.")

        for locale, fields in value.items():
            if not isinstance(locale, str) or len(locale) < 2:
                raise serializers.ValidationError(f"Invalid locale code: {locale}")
            if not isinstance(fields, dict):
                raise serializers.ValidationError(f"Translations for {locale} must be a dictionary.")

        return value


from apps.system.tag_serializer import TagObjectActionSerializer, TagSerializer  # noqa: E402
