"""
WeWork Serializers

All serializers inherit from BaseModelSerializer for automatic
serialization of common fields and custom_fields support.
"""
from rest_framework import serializers
from apps.common.serializers.base import (
    BaseModelSerializer,
    BaseModelWithAuditSerializer
)
from apps.sso.models import WeWorkConfig, UserMapping, OAuthState


class WeWorkConfigSerializer(BaseModelSerializer):
    """WeWork configuration serializer."""

    class Meta(BaseModelSerializer.Meta):
        model = WeWorkConfig
        fields = BaseModelSerializer.Meta.fields + [
            'corp_id',
            'corp_name',
            'agent_id',
            'agent_secret',
            'sync_department',
            'sync_user',
            'auto_create_user',
            'default_role_id',
            'redirect_uri',
            'is_enabled',
        ]
        extra_kwargs = {
            'agent_secret': {'write_only': True}
        }


class WeWorkConfigDetailSerializer(BaseModelWithAuditSerializer):
    """WeWork configuration detail serializer with full audit info."""

    class Meta(BaseModelWithAuditSerializer.Meta):
        model = WeWorkConfig
        fields = BaseModelWithAuditSerializer.Meta.fields + [
            'corp_id',
            'corp_name',
            'agent_id',
            'agent_secret',
            'sync_department',
            'sync_user',
            'auto_create_user',
            'default_role_id',
            'redirect_uri',
            'is_enabled',
        ]
        extra_kwargs = {
            'agent_secret': {'write_only': True}
        }


class UserMappingSerializer(BaseModelSerializer):
    """User platform mapping serializer."""

    system_user_info = serializers.SerializerMethodField()
    platform_display = serializers.CharField(
        source='get_platform_display',
        read_only=True
    )

    class Meta(BaseModelSerializer.Meta):
        model = UserMapping
        fields = BaseModelSerializer.Meta.fields + [
            'system_user',
            'system_user_info',
            'platform',
            'platform_display',
            'platform_userid',
            'platform_unionid',
            'platform_name',
            'extra_data',
        ]

    def get_system_user_info(self, obj):
        """Get system user info."""
        if obj.system_user:
            return {
                'id': str(obj.system_user.id),
                'username': obj.system_user.username,
                'real_name': getattr(obj.system_user, 'real_name', ''),
                'email': obj.system_user.email,
                'mobile': getattr(obj.system_user, 'mobile', ''),
            }
        return None


class OAuthStateSerializer(BaseModelSerializer):
    """OAuth state serializer."""

    is_valid = serializers.BooleanField(read_only=True)

    class Meta(BaseModelSerializer.Meta):
        model = OAuthState
        fields = [
            'id',
            'state',
            'platform',
            'session_data',
            'expires_at',
            'consumed',
            'consumed_at',
            'is_valid',
            'created_at',
        ]
