"""
Serializers for DataPermission model.
"""
from rest_framework import serializers
from django.contrib.contenttypes.models import ContentType
from django.contrib.auth import get_user_model

from apps.common.serializers.base import BaseModelSerializer
from apps.permissions.models.data_permission import DataPermission

User = get_user_model()


class DataPermissionSerializer(BaseModelSerializer):
    """
    Serializer for DataPermission - list view.

    Optimized for list endpoints.
    """
    user_display = serializers.CharField(source='user.username', read_only=True, allow_null=True)
    content_type_display = serializers.CharField(source='content_type.model', read_only=True)
    scope_type_display = serializers.CharField(source='get_scope_type_display', read_only=True)

    class Meta(BaseModelSerializer.Meta):
        model = DataPermission
        fields = BaseModelSerializer.Meta.fields + [
            'user',
            'content_type',
            'scope_type',
            'scope_type_display',
            'scope_value',
            'department_field',
            'user_field',
            'description',
            'user_display',
            'content_type_display',
        ]
        read_only_fields = BaseModelSerializer.Meta.read_only_fields


class DataPermissionDetailSerializer(DataPermissionSerializer):
    """
    Detailed serializer for DataPermission.

    Includes full nested objects for detail view.
    """
    user = serializers.SerializerMethodField()
    content_type = serializers.SerializerMethodField()

    class Meta(DataPermissionSerializer.Meta):
        fields = DataPermissionSerializer.Meta.fields

    def get_user(self, obj):
        """Get user data."""
        if obj.user:
            return {
                'id': str(obj.user.id),
                'username': obj.user.username,
                'email': obj.user.email,
            }
        return None

    def get_content_type(self, obj):
        """Get content type data."""
        return {
            'id': obj.content_type.id,
            'app_label': obj.content_type.app_label,
            'model': obj.content_type.model,
        }


class DataPermissionCreateSerializer(serializers.ModelSerializer):
    """
    Serializer for creating DataPermission.

    Accepts content_type as app_label and model for easier input.
    Also accepts user as UUID string or User object.
    """
    content_type_app_label = serializers.CharField(write_only=True, required=False)
    content_type_model = serializers.CharField(write_only=True, required=False)
    user_username = serializers.CharField(write_only=True, required=False, allow_null=True)

    class Meta:
        model = DataPermission
        fields = [
            'user',
            'content_type',
            'content_type_app_label',
            'content_type_model',
            'user_username',
            'scope_type',
            'scope_value',
            'department_field',
            'user_field',
            'description',
        ]
        extra_kwargs = {
            'user': {'required': False, 'allow_null': True},
            'content_type': {'required': False},
        }

    def validate(self, attrs):
        """Validate that user is specified."""
        user = attrs.get('user')

        # Handle user as UUID string
        if user and isinstance(user, str):
            try:
                attrs['user'] = User.objects.get(id=user, is_deleted=False)
            except User.DoesNotExist:
                raise serializers.ValidationError({
                    'user': ['User with this ID does not exist.']
                })

        if not attrs.get('user'):
            # Try to get from username
            user_username = attrs.get('user_username')

            if user_username:
                try:
                    attrs['user'] = User.objects.get(username=user_username, is_deleted=False)
                except User.DoesNotExist:
                    raise serializers.ValidationError({
                        'user_username': ['User with this username does not exist.']
                    })
            else:
                raise serializers.ValidationError({
                    'non_field_errors': ['User must be specified.']
                })

        # Validate scope_value based on scope_type
        scope_type = attrs.get('scope_type', 'self_dept')
        scope_value = attrs.get('scope_value', {})

        if scope_type == 'specified':
            if not scope_value.get('department_ids'):
                raise serializers.ValidationError({
                    'scope_value': ['department_ids is required for specified scope.']
                })

        elif scope_type == 'custom':
            if not scope_value.get('filter_expression'):
                raise serializers.ValidationError({
                    'scope_value': ['filter_expression is required for custom scope.']
                })

        # Handle content_type from ID or app_label and model
        content_type = attrs.get('content_type')

        # Handle content_type as integer ID
        if content_type and isinstance(content_type, int):
            try:
                attrs['content_type'] = ContentType.objects.get(id=content_type)
            except ContentType.DoesNotExist:
                raise serializers.ValidationError({
                    'content_type': [f'ContentType with ID {content_type} does not exist.']
                })

        # Handle content_type from app_label and model
        if not attrs.get('content_type'):
            app_label = attrs.get('content_type_app_label')
            model = attrs.get('content_type_model')

            if not app_label or not model:
                raise serializers.ValidationError({
                    'content_type': ['Either content_type or content_type_app_label + content_type_model must be specified.']
                })

            try:
                attrs['content_type'] = ContentType.objects.get(
                    app_label=app_label,
                    model=model.lower()
                )
            except ContentType.DoesNotExist:
                raise serializers.ValidationError({
                    'content_type': [f'ContentType for {app_label}.{model} does not exist.']
                })

        return attrs

    def create(self, validated_data):
        """Create data permission and set organization from user."""
        user = validated_data.get('user')
        # Get organization from user
        if user and hasattr(user, 'current_organization'):
            validated_data['organization'] = user.current_organization
        return super().create(validated_data)

    def to_representation(self, instance):
        """Use detail serializer for response."""
        return DataPermissionDetailSerializer(instance, context=self.context).data


class DataPermissionUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating DataPermission."""

    class Meta:
        model = DataPermission
        fields = [
            'scope_type',
            'scope_value',
            'department_field',
            'user_field',
            'description',
        ]

    def validate(self, attrs):
        """Validate scope_value based on scope_type."""
        scope_type = attrs.get('scope_type', self.instance.scope_type)
        scope_value = attrs.get('scope_value', self.instance.scope_value)

        if scope_type == 'specified':
            department_ids = scope_value.get('department_ids', [])
            if not department_ids:
                raise serializers.ValidationError({
                    'scope_value': ['department_ids is required for specified scope.']
                })

        elif scope_type == 'custom':
            filter_expression = scope_value.get('filter_expression')
            if not filter_expression:
                raise serializers.ValidationError({
                    'scope_value': ['filter_expression is required for custom scope.']
                })

        return attrs
