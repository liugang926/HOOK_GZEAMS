"""
Serializers for Mobile Device and Security Log models.
"""
from rest_framework import serializers
from apps.common.serializers.base import (
    BaseModelSerializer,
    BaseModelWithAuditSerializer,
    BaseListSerializer
)
from apps.mobile.models import MobileDevice, DeviceSecurityLog


class MobileDeviceSerializer(BaseModelSerializer):
    """Serializer for MobileDevice."""

    device_type_display = serializers.CharField(source='get_device_type_display', read_only=True)

    class Meta(BaseModelSerializer.Meta):
        model = MobileDevice
        fields = BaseModelSerializer.Meta.fields + [
            'user',
            'device_id',
            'device_name',
            'device_type',
            'device_type_display',
            'os_version',
            'app_version',
            'device_info',
            'is_bound',
            'is_active',
            'last_login_at',
            'last_login_ip',
            'last_sync_at',
            'last_location',
            'enable_biometric',
            'allow_offline',
        ]


class MobileDeviceListSerializer(BaseListSerializer):
    """Optimized serializer for mobile device list views."""

    device_type_display = serializers.CharField(source='get_device_type_display', read_only=True)
    username = serializers.CharField(source='user.username', read_only=True)
    user_email = serializers.CharField(source='user.email', read_only=True)

    class Meta(BaseListSerializer.Meta):
        model = MobileDevice
        fields = BaseListSerializer.Meta.fields + [
            'user',
            'username',
            'user_email',
            'device_id',
            'device_name',
            'device_type',
            'device_type_display',
            'os_version',
            'app_version',
            'is_bound',
            'is_active',
            'last_login_at',
            'last_sync_at',
        ]


class MobileDeviceDetailSerializer(BaseModelWithAuditSerializer):
    """Detailed serializer for mobile device."""

    device_type_display = serializers.CharField(source='get_device_type_display', read_only=True)
    username = serializers.CharField(source='user.username', read_only=True)
    user_email = serializers.CharField(source='user.email', read_only=True)

    class Meta(BaseModelWithAuditSerializer.Meta):
        model = MobileDevice
        fields = BaseModelWithAuditSerializer.Meta.fields + [
            'user',
            'username',
            'user_email',
            'device_id',
            'device_name',
            'device_type',
            'device_type_display',
            'os_version',
            'app_version',
            'device_info',
            'is_bound',
            'is_active',
            'last_login_at',
            'last_login_ip',
            'last_sync_at',
            'last_location',
            'enable_biometric',
            'allow_offline',
        ]


class DeviceSecurityLogSerializer(BaseModelSerializer):
    """Serializer for DeviceSecurityLog."""

    event_type_display = serializers.CharField(source='get_event_type_display', read_only=True)
    device_name = serializers.CharField(source='device.device_name', read_only=True)

    class Meta(BaseModelSerializer.Meta):
        model = DeviceSecurityLog
        fields = BaseModelSerializer.Meta.fields + [
            'device',
            'device_name',
            'event_type',
            'event_type_display',
            'ip_address',
            'location',
            'user_agent',
            'details',
        ]
