"""
Serializers for DataPermissionExpand model.
"""
from rest_framework import serializers

from apps.common.serializers.base import BaseModelSerializer
from apps.permissions.models.data_permission_expand import DataPermissionExpand


class DataPermissionExpandSerializer(BaseModelSerializer):
    """
    Serializer for DataPermissionExpand.
    """
    data_permission_display = serializers.CharField(
        source='data_permission.__str__',
        read_only=True
    )
    is_active_display = serializers.BooleanField(
        source='is_active',
        read_only=True
    )

    class Meta(BaseModelSerializer.Meta):
        model = DataPermissionExpand
        fields = BaseModelSerializer.Meta.fields + [
            'data_permission',
            'data_permission_display',
            'filter_conditions',
            'allowed_fields',
            'denied_fields',
            'actions',
            'priority',
            'is_active',
            'is_active_display',
            'description',
        ]
        read_only_fields = BaseModelSerializer.Meta.read_only_fields


class DataPermissionExpandCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating DataPermissionExpand."""

    class Meta:
        model = DataPermissionExpand
        fields = [
            'data_permission',
            'filter_conditions',
            'allowed_fields',
            'denied_fields',
            'actions',
            'priority',
            'is_active',
            'description',
        ]

    def to_representation(self, instance):
        """Use detail serializer for response."""
        return DataPermissionExpandSerializer(instance, context=self.context).data


class DataPermissionExpandUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating DataPermissionExpand."""

    class Meta:
        model = DataPermissionExpand
        fields = [
            'filter_conditions',
            'allowed_fields',
            'denied_fields',
            'actions',
            'priority',
            'is_active',
            'description',
        ]
