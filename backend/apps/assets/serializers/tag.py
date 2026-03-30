"""
Serializers for asset tag groups, tags, and asset-tag relations.
"""
import re

from rest_framework import serializers

from apps.assets.models import AssetTag, AssetTagRelation, TagGroup
from apps.common.serializers.base import BaseModelSerializer, UserSerializer


HEX_COLOR_PATTERN = re.compile(r'^#(?:[0-9a-fA-F]{3}|[0-9a-fA-F]{6}|[0-9a-fA-F]{8})$')
NAMED_COLOR_PATTERN = re.compile(r'^[A-Za-z][A-Za-z0-9_-]*$')


class TagColorValidationMixin:
    """Shared validation helpers for tag-related serializers."""

    @staticmethod
    def _normalize_color(value):
        normalized_value = str(value or '').strip()
        if not normalized_value:
            return normalized_value
        if HEX_COLOR_PATTERN.match(normalized_value) or NAMED_COLOR_PATTERN.match(normalized_value):
            return normalized_value
        raise serializers.ValidationError('Invalid color value.')

    @staticmethod
    def _normalize_text(value):
        return str(value or '').strip()

    def validate_name(self, value):
        """Normalize display names before persistence."""
        normalized_value = self._normalize_text(value)
        if not normalized_value:
            raise serializers.ValidationError('Name is required.')
        return normalized_value

    def validate_code(self, value):
        """Normalize codes before persistence."""
        normalized_value = self._normalize_text(value)
        if not normalized_value:
            raise serializers.ValidationError('Code is required.')
        return normalized_value

    def validate_color(self, value):
        """Accept common hex values and semantic aliases."""
        normalized_value = self._normalize_color(value)
        if not normalized_value:
            raise serializers.ValidationError('Color is required.')
        return normalized_value

    def validate_description(self, value):
        """Trim description fields."""
        return self._normalize_text(value)

    def validate_icon(self, value):
        """Trim icon names."""
        return self._normalize_text(value)


class AssetTagSummarySerializer(serializers.ModelSerializer):
    """Compact serializer for rendering tag chips."""

    tag_group = serializers.UUIDField(source='tag_group_id', read_only=True)
    group_name = serializers.CharField(source='tag_group.name', read_only=True)
    group_color = serializers.CharField(source='tag_group.color', read_only=True)
    asset_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = AssetTag
        fields = [
            'id',
            'tag_group',
            'group_name',
            'group_color',
            'name',
            'code',
            'color',
            'icon',
            'asset_count',
        ]


class TagGroupSerializer(TagColorValidationMixin, BaseModelSerializer):
    """Serializer for asset tag group CRUD responses."""

    tags_count = serializers.SerializerMethodField()
    tags = serializers.SerializerMethodField()

    class Meta(BaseModelSerializer.Meta):
        model = TagGroup
        fields = BaseModelSerializer.Meta.fields + [
            'name',
            'code',
            'description',
            'color',
            'icon',
            'sort_order',
            'is_system',
            'is_active',
            'tags_count',
            'tags',
        ]

    def get_tags_count(self, obj):
        """Return the number of active non-deleted tags in the group."""
        prefetched_tags = getattr(obj, 'prefetched_tags', None)
        if prefetched_tags is not None:
            return len(prefetched_tags)
        return obj.tags.filter(is_deleted=False, is_active=True).count()

    def get_tags(self, obj):
        """Return nested active tags for grouped selector use cases."""
        prefetched_tags = getattr(obj, 'prefetched_tags', None)
        if prefetched_tags is None:
            prefetched_tags = obj.tags.filter(
                is_deleted=False,
                is_active=True,
            ).select_related('tag_group').order_by('sort_order', 'name')
        return AssetTagSummarySerializer(prefetched_tags, many=True).data


class AssetTagSerializer(TagColorValidationMixin, BaseModelSerializer):
    """Serializer for asset tag CRUD responses."""

    tag_group_name = serializers.CharField(source='tag_group.name', read_only=True)
    group_color = serializers.CharField(source='tag_group.color', read_only=True)
    asset_count = serializers.IntegerField(read_only=True)

    class Meta(BaseModelSerializer.Meta):
        model = AssetTag
        fields = BaseModelSerializer.Meta.fields + [
            'tag_group',
            'tag_group_name',
            'group_color',
            'name',
            'code',
            'color',
            'icon',
            'description',
            'sort_order',
            'is_active',
            'asset_count',
        ]

    def validate_tag_group(self, value):
        """Ensure the selected tag group belongs to the current organization."""
        if value.is_deleted:
            raise serializers.ValidationError('Tag group does not exist.')

        request = self.context.get('request')
        organization_id = (
            getattr(request, 'organization_id', None)
            or getattr(getattr(request, 'user', None), 'current_organization_id', None)
        )
        if organization_id and str(value.organization_id) != str(organization_id):
            raise serializers.ValidationError('Tag group must belong to the same organization.')
        return value

    def validate_color(self, value):
        """Allow blank colors so tags can inherit the group color."""
        normalized_value = self._normalize_color(value)
        return normalized_value


class AssetTagRelationSerializer(BaseModelSerializer):
    """Serializer for asset-tag relation detail responses."""

    tag = AssetTagSummarySerializer(read_only=True)
    tagged_by = UserSerializer(read_only=True)

    class Meta(BaseModelSerializer.Meta):
        model = AssetTagRelation
        fields = BaseModelSerializer.Meta.fields + [
            'asset',
            'tag',
            'tagged_by',
            'tagged_at',
            'notes',
        ]


class AssetTagMutationSerializer(serializers.Serializer):
    """Validate single-asset tag add/remove requests."""

    tag_id = serializers.UUIDField(required=False)
    tag_ids = serializers.ListField(
        child=serializers.UUIDField(),
        required=False,
        allow_empty=False,
    )
    notes = serializers.CharField(max_length=200, required=False, allow_blank=True, default='')

    def validate(self, attrs):
        """Accept either tag_id or tag_ids and deduplicate the final list."""
        tag_values = []
        if attrs.get('tag_id'):
            tag_values.append(str(attrs['tag_id']))
        if attrs.get('tag_ids'):
            tag_values.extend(str(tag_id) for tag_id in attrs['tag_ids'])

        unique_tag_ids = []
        seen = set()
        for tag_id in tag_values:
            if tag_id in seen:
                continue
            seen.add(tag_id)
            unique_tag_ids.append(tag_id)

        if not unique_tag_ids:
            raise serializers.ValidationError({'tag_ids': ['At least one tag must be provided.']})

        attrs['tag_ids'] = unique_tag_ids
        attrs.pop('tag_id', None)
        attrs['notes'] = str(attrs.get('notes') or '').strip()
        return attrs


class AssetTagBatchMutationSerializer(serializers.Serializer):
    """Validate batch asset tagging requests."""

    asset_ids = serializers.ListField(
        child=serializers.UUIDField(),
        allow_empty=False,
    )
    tag_ids = serializers.ListField(
        child=serializers.UUIDField(),
        allow_empty=False,
    )
    notes = serializers.CharField(max_length=200, required=False, allow_blank=True, default='')

    def validate_asset_ids(self, value):
        """Deduplicate asset IDs while preserving order."""
        deduplicated = []
        seen = set()
        for asset_id in value:
            key = str(asset_id)
            if key in seen:
                continue
            seen.add(key)
            deduplicated.append(asset_id)
        return deduplicated

    def validate_tag_ids(self, value):
        """Deduplicate tag IDs while preserving order."""
        deduplicated = []
        seen = set()
        for tag_id in value:
            key = str(tag_id)
            if key in seen:
                continue
            seen.add(key)
            deduplicated.append(tag_id)
        return deduplicated

    def validate_notes(self, value):
        """Trim notes payloads."""
        return str(value or '').strip()


class AssetByTagsSerializer(serializers.Serializer):
    """Validate asset-by-tags search payloads."""

    MATCH_TYPE_CHOICES = (
        ('and', 'And'),
        ('or', 'Or'),
    )

    tag_ids = serializers.ListField(
        child=serializers.UUIDField(),
        allow_empty=False,
    )
    match_type = serializers.ChoiceField(choices=MATCH_TYPE_CHOICES, default='or')

    def validate_tag_ids(self, value):
        """Deduplicate tag IDs while preserving order."""
        deduplicated = []
        seen = set()
        for tag_id in value:
            key = str(tag_id)
            if key in seen:
                continue
            seen.add(key)
            deduplicated.append(tag_id)
        return deduplicated
