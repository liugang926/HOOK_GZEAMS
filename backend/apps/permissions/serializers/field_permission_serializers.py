"""
Serializers for FieldPermission model.
"""
from rest_framework import serializers
from django.contrib.contenttypes.models import ContentType
from django.contrib.auth import get_user_model

from apps.common.serializers.base import BaseModelSerializer
from apps.permissions.models.field_permission import FieldPermission

User = get_user_model()


# Lightweight nested serializers
class ContentTypeSerializer(serializers.ModelSerializer):
    """Serializer for ContentType."""
    class Meta:
        model = ContentType
        fields = ['id', 'app_label', 'model']


class FieldPermissionSerializer(BaseModelSerializer):
    """
    Serializer for FieldPermission - list view.

    Optimized for list endpoints with minimal nested data.
    """
    user_display = serializers.CharField(source='user.username', read_only=True, allow_null=True)
    content_type_display = serializers.CharField(source='content_type.model', read_only=True)
    permission_type_display = serializers.CharField(source='get_permission_type_display', read_only=True)
    mask_rule_display = serializers.CharField(source='get_mask_rule_display', read_only=True, allow_null=True)

    class Meta(BaseModelSerializer.Meta):
        model = FieldPermission
        fields = BaseModelSerializer.Meta.fields + [
            'user',
            'content_type',
            'field_name',
            'permission_type',
            'permission_type_display',
            'mask_rule',
            'mask_rule_display',
            'custom_mask_pattern',
            'condition',
            'priority',
            'description',
            'user_display',
            'content_type_display',
        ]
        read_only_fields = BaseModelSerializer.Meta.read_only_fields


class FieldPermissionDetailSerializer(FieldPermissionSerializer):
    """
    Detailed serializer for FieldPermission.

    Includes full nested objects for detail view.
    """
    user = serializers.SerializerMethodField()
    content_type = ContentTypeSerializer(read_only=True)

    class Meta(FieldPermissionSerializer.Meta):
        fields = FieldPermissionSerializer.Meta.fields

    def get_user(self, obj):
        """Get user data."""
        if obj.user:
            return {
                'id': str(obj.user.id),
                'username': obj.user.username,
                'email': obj.user.email,
            }
        return None


class FieldPermissionCreateSerializer(serializers.ModelSerializer):
    """
    Serializer for creating FieldPermission.

    Accepts content_type as app_label and model for easier input.
    Also accepts user as UUID string or User object.
    """
    content_type_app_label = serializers.CharField(write_only=True, required=False)
    content_type_model = serializers.CharField(write_only=True, required=False)
    user_username = serializers.CharField(write_only=True, required=False, allow_null=True)

    class Meta:
        model = FieldPermission
        fields = [
            'user',
            'content_type',
            'content_type_app_label',
            'content_type_model',
            'user_username',
            'field_name',
            'permission_type',
            'mask_rule',
            'custom_mask_pattern',
            'condition',
            'priority',
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

        # Validate mask_rule for masked permission type
        if attrs.get('permission_type') == 'masked' and not attrs.get('mask_rule'):
            raise serializers.ValidationError({
                'mask_rule': ['Mask rule is required when permission type is masked.']
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
        """Create field permission and set organization from user."""
        user = validated_data.get('user')
        # Get organization from user
        if user and hasattr(user, 'current_organization'):
            validated_data['organization'] = user.current_organization
        return super().create(validated_data)

    def to_representation(self, instance):
        """Use detail serializer for response."""
        return FieldPermissionDetailSerializer(instance, context=self.context).data


class FieldPermissionUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating FieldPermission."""

    class Meta:
        model = FieldPermission
        fields = [
            'permission_type',
            'mask_rule',
            'custom_mask_pattern',
            'condition',
            'priority',
            'description',
        ]

    def validate(self, attrs):
        """Validate mask_rule for masked permission type."""
        permission_type = attrs.get('permission_type', self.instance.permission_type)
        mask_rule = attrs.get('mask_rule', self.instance.mask_rule)

        if permission_type == 'masked' and not mask_rule:
            raise serializers.ValidationError({
                'mask_rule': ['Mask rule is required when permission type is masked.']
            })

        return attrs
