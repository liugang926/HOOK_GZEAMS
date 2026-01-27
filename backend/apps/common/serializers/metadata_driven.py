"""
Metadata-driven serializer for zero-code CRUD.

Dynamically generates serializers based on BusinessObject and FieldDefinition.
"""
from rest_framework import serializers
from typing import Dict, List, Any, Optional, Type
from django.core.exceptions import ObjectDoesNotExist


class FieldDefinitionMapper:
    """
    Maps FieldDefinition.field_type to DRF serializer fields.
    """

    FIELD_TYPE_MAPPING = {
        'text': serializers.CharField,
        'textarea': serializers.CharField,
        'number': serializers.DecimalField,
        'integer': serializers.IntegerField,
        'float': serializers.FloatField,
        'boolean': serializers.BooleanField,
        'date': serializers.DateField,
        'datetime': serializers.DateTimeField,
        'time': serializers.TimeField,
        'email': serializers.EmailField,
        'url': serializers.URLField,
        'choice': serializers.ChoiceField,
        'multi_choice': serializers.MultipleChoiceField,
        'file': serializers.FileField,
        'image': serializers.ImageField,
        'reference': serializers.UUIDField,
        'user': serializers.UUIDField,
        'department': serializers.UUIDField,
        'formula': serializers.ReadOnlyField,
        'json': serializers.JSONField,
    }

    @classmethod
    def get_field_class(cls, field_type: str) -> Type[serializers.Field]:
        """Get DRF field class for field type."""
        return cls.FIELD_TYPE_MAPPING.get(field_type, serializers.CharField)

    @classmethod
    def get_field_kwargs(cls, field_def) -> Dict[str, Any]:
        """
        Build field kwargs from FieldDefinition.

        Args:
            field_def: FieldDefinition instance

        Returns:
            Dict of serializer field kwargs
        """
        kwargs = {
            'required': field_def.is_required,
            'read_only': field_def.is_readonly,
            'label': field_def.name,
            'help_text': field_def.description or '',
            'allow_null': not field_def.is_required,
        }

        # Default value
        if field_def.default_value is not None:
            kwargs['default'] = field_def.default_value

        # String max length
        if field_def.max_length and field_def.field_type in ['text', 'textarea']:
            kwargs['max_length'] = field_def.max_length

        # Numeric constraints
        if field_def.field_type in ['number', 'integer', 'float']:
            if field_def.min_value is not None:
                kwargs['min_value'] = field_def.min_value
            if field_def.max_value is not None:
                kwargs['max_value'] = field_def.max_value
            if field_def.field_type == 'number':
                kwargs['decimal_places'] = getattr(field_def, 'decimal_places', 2) or 2
                kwargs['max_digits'] = getattr(field_def, 'max_digits', 10) or 10

        # Choice fields
        if field_def.field_type in ['choice', 'multi_choice']:
            options = field_def.options or {}
            if isinstance(options, dict):
                kwargs['choices'] = [(k, v) for k, v in options.items()]
            elif isinstance(options, list):
                kwargs['choices'] = [(opt, opt) for opt in options]

        return kwargs


class MetadataDrivenSerializer(serializers.Serializer):
    """
    Serializer that dynamically builds fields from BusinessObject metadata.

    Usage:
        # Factory method
        AssetSerializer = MetadataDrivenSerializer.for_business_object('Asset')
        serializer = AssetSerializer(instance)

        # Direct instantiation
        serializer = MetadataDrivenSerializer(
            instance,
            business_object_code='Asset',
            layout_type='form'
        )
    """

    # Class attributes (set by subclass or factory)
    business_object_code: Optional[str] = None
    layout_type: str = 'form'  # 'form' or 'list'

    # Runtime metadata
    _business_object = None
    _field_definitions = None

    # Base fields always included
    id = serializers.UUIDField(read_only=True)
    created_at = serializers.DateTimeField(read_only=True)
    updated_at = serializers.DateTimeField(read_only=True)

    def __init__(self, *args, **kwargs):
        # Extract metadata parameters
        self._init_business_object_code = kwargs.pop('business_object_code', None)
        self._init_layout_type = kwargs.pop('layout_type', None)

        super().__init__(*args, **kwargs)

        # Load metadata and build dynamic fields
        self._load_metadata()
        if self._business_object and self._field_definitions:
            self._build_dynamic_fields()

    def _load_metadata(self):
        """Load BusinessObject and FieldDefinitions."""
        code = self._init_business_object_code or self.business_object_code
        if not code:
            return

        try:
            from apps.system.models import BusinessObject
            self._business_object = BusinessObject.objects.get(
                code=code,
                is_active=True
            )
            self._field_definitions = self._business_object.field_definitions.filter(
                is_active=True
            ).order_by('sort_order')
        except ObjectDoesNotExist:
            raise serializers.ValidationError(
                f"BusinessObject '{code}' not found"
            )

    def _build_dynamic_fields(self):
        """Build serializer fields from FieldDefinitions."""
        layout_type = self._init_layout_type or self.layout_type

        for field_def in self._field_definitions:
            # Check visibility in layout
            if not self._is_field_visible(field_def, layout_type):
                continue

            # Get field class and kwargs
            field_class = FieldDefinitionMapper.get_field_class(field_def.field_type)
            field_kwargs = FieldDefinitionMapper.get_field_kwargs(field_def)

            # Create and register field
            self.fields[field_def.code] = field_class(**field_kwargs)

    def _is_field_visible(self, field_def, layout_type: str) -> bool:
        """Check if field should be visible in current layout."""
        # For now, show all active fields
        # Future: check PageLayout configuration
        if layout_type == 'list':
            return getattr(field_def, 'show_in_list', True)
        return True

    def to_representation(self, instance):
        """Serialize instance, expanding custom_fields."""
        data = super().to_representation(instance)

        # Handle DynamicData instances
        if hasattr(instance, 'custom_fields') and isinstance(instance.custom_fields, dict):
            custom_fields = instance.custom_fields

            # Expand custom_fields to top level
            if self._field_definitions:
                for field_def in self._field_definitions:
                    if field_def.code in custom_fields:
                        value = custom_fields[field_def.code]
                        data[field_def.code] = self._format_field_value(field_def, value)

        return data

    def to_internal_value(self, data):
        """Deserialize input data."""
        result = super().to_internal_value(data)

        # For DynamicData, pack fields into custom_fields
        if self._business_object:
            custom_fields = {}
            for field_def in self._field_definitions:
                if field_def.code in result:
                    custom_fields[field_def.code] = result.pop(field_def.code)
            if custom_fields:
                result['custom_fields'] = custom_fields
                result['business_object'] = self._business_object

        return result

    def _format_field_value(self, field_def, value: Any) -> Any:
        """Format field value for output."""
        if value is None:
            return None

        # Choice fields: return value with label
        if field_def.field_type in ['choice', 'multi_choice']:
            options = field_def.options or {}
            if field_def.field_type == 'choice':
                return {
                    'value': value,
                    'label': options.get(value, value) if isinstance(options, dict) else value
                }
            else:
                return {
                    'value': value,
                    'labels': [options.get(v, v) if isinstance(options, dict) else v for v in (value or [])]
                }

        # Reference fields: return ID with display
        if field_def.field_type in ['reference', 'user', 'department']:
            return {
                'id': value,
                'display': str(value)  # TODO: resolve display name
            }

        return value

    @classmethod
    def for_business_object(
        cls,
        business_object_code: str,
        layout_type: str = 'form'
    ) -> Type['MetadataDrivenSerializer']:
        """
        Factory method to create serializer class for a BusinessObject.

        Args:
            business_object_code: BusinessObject code
            layout_type: 'form' or 'list'

        Returns:
            Serializer class
        """
        class GeneratedSerializer(cls):
            pass

        GeneratedSerializer.business_object_code = business_object_code
        GeneratedSerializer.layout_type = layout_type
        GeneratedSerializer.__name__ = f'{business_object_code.title()}Serializer'

        return GeneratedSerializer


class DynamicDataSerializer(MetadataDrivenSerializer):
    """
    Serializer specifically for DynamicData model instances.

    Includes additional base fields from BaseModel.
    """

    organization = serializers.SerializerMethodField()
    created_by = serializers.SerializerMethodField()

    def get_organization(self, obj):
        if hasattr(obj, 'organization') and obj.organization:
            return {
                'id': str(obj.organization.id),
                'name': obj.organization.name
            }
        return None

    def get_created_by(self, obj):
        if hasattr(obj, 'created_by') and obj.created_by:
            return {
                'id': str(obj.created_by.id),
                'username': obj.created_by.username
            }
        return None
