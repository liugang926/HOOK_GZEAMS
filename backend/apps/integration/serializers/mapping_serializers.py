"""
Serializers for data mapping template models.

Provides serializers for DataMappingTemplate model following BaseModelSerializer pattern.
"""
from rest_framework import serializers

from apps.common.serializers.base import BaseModelSerializer
from apps.integration.models import DataMappingTemplate


class DataMappingTemplateSerializer(BaseModelSerializer):
    """Serializer for data mapping templates."""

    system_type_display = serializers.CharField(source='get_system_type_display', read_only=True)
    field_mappings_count = serializers.SerializerMethodField()
    value_mappings_count = serializers.SerializerMethodField()
    transform_rules_count = serializers.SerializerMethodField()

    class Meta(BaseModelSerializer.Meta):
        model = DataMappingTemplate
        fields = BaseModelSerializer.Meta.fields + [
            'system_type',
            'system_type_display',
            'business_type',
            'template_name',
            'field_mappings',
            'value_mappings',
            'transform_rules',
            'is_active',
            'field_mappings_count',
            'value_mappings_count',
            'transform_rules_count',
        ]

    def get_field_mappings_count(self, obj):
        """Get count of field mappings."""
        return len(obj.field_mappings) if isinstance(obj.field_mappings, dict) else 0

    def get_value_mappings_count(self, obj):
        """Get count of value mappings."""
        return len(obj.value_mappings) if isinstance(obj.value_mappings, dict) else 0

    def get_transform_rules_count(self, obj):
        """Get count of transform rules."""
        return len(obj.transform_rules) if isinstance(obj.transform_rules, list) else 0
