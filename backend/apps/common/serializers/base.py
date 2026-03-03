from rest_framework import serializers
from django.contrib.auth import get_user_model
from apps.common.models import BaseModel

User = get_user_model()

# Import Organization model for nested serialization
# Using lazy import to avoid circular dependency
def get_organization_model():
    """Lazy load Organization model to avoid circular imports."""
    from apps.organizations.models import Organization
    return Organization


# Lightweight organization serializer for nested display
class OrganizationSerializer(serializers.ModelSerializer):
    """Lightweight organization serializer for nested display"""
    class Meta:
        model = get_organization_model()
        fields = ['id', 'name', 'code']


# Lightweight user serializer for nested display
class UserSerializer(serializers.ModelSerializer):
    """Lightweight user serializer for nested display"""
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name']


class BaseModelSerializer(serializers.ModelSerializer):
    """
    Base serializer for all models inheriting from BaseModel.

    Automatically serializes all BaseModel public fields:
    - id, organization, is_deleted, deleted_at
    - created_at, updated_at, created_by
    - custom_fields (JSONB dynamic fields)

    Nested serializers:
    - organization → OrganizationSerializer (lightweight)
    - created_by → UserSerializer (lightweight)
    """

    # Automatic field mapping
    id = serializers.UUIDField(read_only=True)
    organization = OrganizationSerializer(read_only=True)
    is_deleted = serializers.BooleanField(read_only=True)
    deleted_at = serializers.DateTimeField(read_only=True)
    created_at = serializers.DateTimeField(read_only=True)
    updated_at = serializers.DateTimeField(read_only=True)
    created_by = UserSerializer(read_only=True)
    updated_by = UserSerializer(read_only=True)
    deleted_by = UserSerializer(read_only=True)
    custom_fields = serializers.JSONField(read_only=True)

    class Meta:
        model = BaseModel
        fields = ['id', 'organization', 'is_deleted', 'deleted_at',
                  'created_at', 'updated_at', 'created_by', 'updated_by',
                  'deleted_by', 'custom_fields']
        read_only_fields = ['id', 'created_at', 'updated_at']

    @staticmethod
    def _extract_reference_id(value):
        """
        Normalize expanded reference objects into primary key values.

        Some clients submit relation fields as full objects (e.g. {'id': '...'}).
        DRF PK/UUID fields expect scalar IDs, so we coerce here.
        """
        if isinstance(value, dict):
            return value.get('id', value)
        if hasattr(value, 'id'):
            return getattr(value, 'id')
        return value

    def _normalize_reference_like_inputs(self, data):
        """Pre-process input payload for PK/UUID relation fields."""
        if not isinstance(data, dict):
            return data

        normalized = dict(data)
        for field_name, field in self.fields.items():
            if field.read_only or field_name not in normalized:
                continue

            raw_value = normalized.get(field_name)
            if raw_value is None:
                continue

            if isinstance(field, serializers.ManyRelatedField):
                if isinstance(raw_value, list):
                    normalized[field_name] = [
                        self._extract_reference_id(item) for item in raw_value
                    ]
                continue

            if isinstance(field, serializers.PrimaryKeyRelatedField):
                normalized[field_name] = self._extract_reference_id(raw_value)
                continue

            if isinstance(field, serializers.UUIDField):
                normalized[field_name] = self._extract_reference_id(raw_value)
                continue

            if (
                isinstance(field, serializers.ListField)
                and isinstance(field.child, serializers.UUIDField)
                and isinstance(raw_value, list)
            ):
                normalized[field_name] = [
                    self._extract_reference_id(item) for item in raw_value
                ]

        return normalized

    def to_internal_value(self, data):
        """Normalize relation payloads before DRF field validation."""
        normalized_data = self._normalize_reference_like_inputs(data)
        return super().to_internal_value(normalized_data)


class BaseModelWithAuditSerializer(BaseModelSerializer):
    """
    Base serializer with full audit trail including updated_by and deleted_by.

    Extends BaseModelSerializer to include:
    - updated_by: User who last updated the record
    - deleted_by: User who soft deleted the record

    Use when you need complete audit information for list/detail views.
    """

    updated_by = UserSerializer(read_only=True)
    deleted_by = UserSerializer(read_only=True)

    class Meta(BaseModelSerializer.Meta):
        model = BaseModel
        fields = BaseModelSerializer.Meta.fields + ['updated_by', 'deleted_by']


class BaseListSerializer(BaseModelSerializer):
    """
    Optimized serializer for list views.

    Excludes nested serializers to reduce query count.
    Use for list endpoints where full detail is not needed.
    """

    organization = serializers.UUIDField(read_only=True)
    created_by = serializers.UUIDField(read_only=True)

    class Meta(BaseModelSerializer.Meta):
        model = BaseModel
        fields = ['id', 'organization', 'is_deleted', 'created_at', 'updated_at', 'created_by']
