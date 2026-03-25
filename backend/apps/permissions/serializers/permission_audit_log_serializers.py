"""
Serializers for PermissionAuditLog model.
"""
from rest_framework import serializers
from django.contrib.contenttypes.models import ContentType

from apps.common.serializers.base import BaseModelSerializer, BaseListSerializer
from apps.permissions.models.permission_audit_log import PermissionAuditLog


class PermissionAuditLogSerializer(BaseModelSerializer):
    """
    Serializer for PermissionAuditLog - list view.
    """
    actor_display = serializers.CharField(
        source='actor.username',
        read_only=True,
        allow_null=True
    )
    target_user_display = serializers.CharField(
        source='target_user.username',
        read_only=True,
        allow_null=True
    )
    operation_type_display = serializers.CharField(
        source='get_operation_type_display',
        read_only=True
    )
    target_type_display = serializers.CharField(
        source='get_target_type_display',
        read_only=True
    )
    result_display = serializers.CharField(
        source='get_result_display',
        read_only=True
    )

    class Meta(BaseModelSerializer.Meta):
        model = PermissionAuditLog
        fields = BaseModelSerializer.Meta.fields + [
            'actor',
            'actor_display',
            'target_user',
            'target_user_display',
            'operation_type',
            'operation_type_display',
            'target_type',
            'target_type_display',
            'permission_details',
            'content_type',
            'object_id',
            'result',
            'result_display',
            'error_message',
            'ip_address',
            'user_agent',
            'request_metadata',
        ]
        read_only_fields = BaseModelSerializer.Meta.read_only_fields + [
            'actor', 'operation_type', 'target_type', 'permission_details',
            'result', 'content_type', 'object_id', 'error_message',
            'ip_address', 'user_agent', 'request_metadata',
        ]


class PermissionAuditLogDetailSerializer(PermissionAuditLogSerializer):
    """
    Detailed serializer for PermissionAuditLog.

    Includes full nested objects for detail view.
    """
    actor = serializers.SerializerMethodField()
    target_user = serializers.SerializerMethodField()
    content_type = serializers.SerializerMethodField()

    class Meta(PermissionAuditLogSerializer.Meta):
        fields = PermissionAuditLogSerializer.Meta.fields

    def get_actor(self, obj):
        """Get actor data."""
        if obj.actor:
            return {
                'id': str(obj.actor.id),
                'username': obj.actor.username,
                'email': obj.actor.email,
            }
        return None

    def get_target_user(self, obj):
        """Get target user data."""
        if obj.target_user:
            return {
                'id': str(obj.target_user.id),
                'username': obj.target_user.username,
                'email': obj.target_user.email,
            }
        return None

    def get_content_type(self, obj):
        """Get content type data."""
        if obj.content_type:
            return {
                'id': obj.content_type.id,
                'app_label': obj.content_type.app_label,
                'model': obj.content_type.model,
            }
        return None


class PermissionAuditLogCreateSerializer(serializers.ModelSerializer):
    """
    Serializer for creating PermissionAuditLog.

    Note: Audit logs are typically created automatically by the system,
    not via direct API calls. This serializer is provided for completeness
    and testing purposes.
    """

    content_type_app_label = serializers.CharField(write_only=True, required=False)
    content_type_model = serializers.CharField(write_only=True, required=False)
    actor_username = serializers.CharField(write_only=True, required=False)
    target_user_username = serializers.CharField(write_only=True, required=False)

    class Meta:
        model = PermissionAuditLog
        fields = [
            'actor',
            'actor_username',
            'target_user',
            'target_user_username',
            'operation_type',
            'target_type',
            'permission_details',
            'content_type',
            'content_type_app_label',
            'content_type_model',
            'object_id',
            'result',
            'error_message',
            'ip_address',
            'user_agent',
            'request_metadata',
        ]

    def validate(self, attrs):
        """Handle foreign key lookups from codes/usernames."""
        from django.contrib.auth import get_user_model

        User = get_user_model()

        # Handle actor
        if not attrs.get('actor'):
            actor_username = attrs.get('actor_username')
            if actor_username:
                try:
                    attrs['actor'] = User.objects.get(username=actor_username, is_deleted=False)
                except User.DoesNotExist:
                    raise serializers.ValidationError({
                        'actor_username': ['User with this username does not exist.']
                    })

        # Handle target_user
        if not attrs.get('target_user'):
            target_user_username = attrs.get('target_user_username')
            if target_user_username:
                try:
                    attrs['target_user'] = User.objects.get(username=target_user_username, is_deleted=False)
                except User.DoesNotExist:
                    raise serializers.ValidationError({
                        'target_user_username': ['User with this username does not exist.']
                    })

        # Handle content_type
        if not attrs.get('content_type'):
            app_label = attrs.get('content_type_app_label')
            model = attrs.get('content_type_model')

            if app_label and model:
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

    def to_representation(self, instance):
        """Use detail serializer for response."""
        return PermissionAuditLogDetailSerializer(instance, context=self.context).data
