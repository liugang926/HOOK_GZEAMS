"""
Serializers for tag management and object-tag association actions.
"""
import re

from rest_framework import serializers

from apps.common.serializers.base import BaseModelSerializer
from apps.system.models import BusinessObject, Tag


HEX_COLOR_PATTERN = re.compile(r'^#(?:[0-9a-fA-F]{3}|[0-9a-fA-F]{6}|[0-9a-fA-F]{8})$')
NAMED_COLOR_PATTERN = re.compile(r'^[A-Za-z][A-Za-z0-9_-]*$')


class TagSerializer(BaseModelSerializer):
    """Serializer for system tags."""

    class Meta(BaseModelSerializer.Meta):
        model = Tag
        fields = BaseModelSerializer.Meta.fields + [
            'name',
            'color',
            'description',
            'biz_type',
            'usage_count',
        ]
        read_only_fields = BaseModelSerializer.Meta.read_only_fields + ['usage_count']

    def validate_name(self, value):
        """Normalize tag names before persistence."""
        normalized_value = str(value or '').strip()
        if not normalized_value:
            raise serializers.ValidationError('Tag name is required.')
        return normalized_value

    def validate_color(self, value):
        """Accept common hex values and semantic color aliases."""
        normalized_value = str(value or '').strip()
        if not normalized_value:
            raise serializers.ValidationError('Tag color is required.')
        if HEX_COLOR_PATTERN.match(normalized_value) or NAMED_COLOR_PATTERN.match(normalized_value):
            return normalized_value
        raise serializers.ValidationError('Invalid tag color value.')

    def validate_biz_type(self, value):
        """Ensure the selected business object code exists when provided."""
        normalized_value = str(value or '').strip()
        if not normalized_value:
            return ''
        if not BusinessObject.objects.filter(code=normalized_value, is_deleted=False).exists():
            raise serializers.ValidationError('Unknown business object code.')
        return normalized_value

    def validate_description(self, value):
        """Trim description values for cleaner storage."""
        return str(value or '').strip()


class TagObjectActionSerializer(serializers.Serializer):
    """Validate batch tag association requests."""

    tag_ids = serializers.ListField(
        child=serializers.UUIDField(),
        allow_empty=False,
    )
    object_ids = serializers.ListField(
        child=serializers.UUIDField(),
        allow_empty=False,
    )
    biz_type = serializers.CharField(max_length=50)

    def validate_tag_ids(self, value):
        """Drop duplicates while preserving the original order."""
        deduplicated = []
        seen = set()
        for tag_id in value:
            if tag_id in seen:
                continue
            seen.add(tag_id)
            deduplicated.append(tag_id)
        if not deduplicated:
            raise serializers.ValidationError('At least one tag must be selected.')
        return deduplicated

    def validate_object_ids(self, value):
        """Drop duplicates while preserving the original order."""
        deduplicated = []
        seen = set()
        for object_id in value:
            if object_id in seen:
                continue
            seen.add(object_id)
            deduplicated.append(object_id)
        if not deduplicated:
            raise serializers.ValidationError('At least one target record must be selected.')
        return deduplicated

    def validate_biz_type(self, value):
        """Require a valid business object code for target resolution."""
        normalized_value = str(value or '').strip()
        if not normalized_value:
            raise serializers.ValidationError('Business object code is required.')
        if not BusinessObject.objects.filter(code=normalized_value, is_deleted=False).exists():
            raise serializers.ValidationError('Unknown business object code.')
        return normalized_value
