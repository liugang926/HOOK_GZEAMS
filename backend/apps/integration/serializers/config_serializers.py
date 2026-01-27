"""
Serializers for integration configuration models.

Provides serializers for IntegrationConfig model following BaseModelSerializer pattern.
"""
from rest_framework import serializers
from django.utils.translation import gettext_lazy as _

from apps.common.serializers.base import BaseModelSerializer
from apps.integration.models import IntegrationConfig
from apps.integration.constants import SyncStatus, HealthStatus


class IntegrationConfigListSerializer(BaseModelSerializer):
    """Lightweight serializer for list views."""

    system_type_display = serializers.CharField(source='get_system_type_display', read_only=True)
    health_status_display = serializers.CharField(source='get_health_status_display', read_only=True)
    last_sync_status_display = serializers.CharField(source='get_last_sync_status_display', read_only=True)
    enabled_modules_count = serializers.SerializerMethodField()

    class Meta(BaseModelSerializer.Meta):
        model = IntegrationConfig
        fields = BaseModelSerializer.Meta.fields + [
            'system_type',
            'system_type_display',
            'system_name',
            'is_enabled',
            'enabled_modules_count',
            'health_status',
            'health_status_display',
            'last_sync_at',
            'last_sync_status',
            'last_sync_status_display',
        ]

    def get_enabled_modules_count(self, obj):
        """Get count of enabled modules."""
        return len(obj.enabled_modules) if isinstance(obj.enabled_modules, list) else 0


class IntegrationConfigDetailSerializer(BaseModelSerializer):
    """Detailed serializer for single instance view."""

    system_type_display = serializers.CharField(source='get_system_type_display', read_only=True)
    health_status_display = serializers.CharField(source='get_health_status_display', read_only=True)
    last_sync_status_display = serializers.CharField(source='get_last_sync_status_display', read_only=True)
    sync_tasks_count = serializers.SerializerMethodField()
    recent_logs = serializers.SerializerMethodField()

    class Meta(BaseModelSerializer.Meta):
        model = IntegrationConfig
        fields = BaseModelSerializer.Meta.fields + [
            'system_type',
            'system_type_display',
            'system_name',
            'connection_config',
            'enabled_modules',
            'sync_config',
            'mapping_config',
            'is_enabled',
            'health_status',
            'health_status_display',
            'last_sync_at',
            'last_sync_status',
            'last_sync_status_display',
            'last_health_check_at',
            'sync_tasks_count',
            'recent_logs',
        ]

    def get_sync_tasks_count(self, obj):
        """Get count of sync tasks."""
        return obj.sync_tasks.count()

    def get_recent_logs(self, obj):
        """Get recent integration logs."""
        from apps.integration.models import IntegrationLog
        recent_logs = IntegrationLog.objects.filter(
            system_type=obj.system_type,
            organization=obj.organization
        ).order_by('-created_at')[:5]
        return IntegrationLogListSerializer(recent_logs, many=True).data


class IntegrationConfigCreateSerializer(BaseModelSerializer):
    """Serializer for creating integration configurations."""

    class Meta(BaseModelSerializer.Meta):
        model = IntegrationConfig
        fields = BaseModelSerializer.Meta.fields + [
            'system_type',
            'system_name',
            'connection_config',
            'enabled_modules',
            'sync_config',
            'mapping_config',
            'is_enabled',
        ]

    def validate_system_type(self, value):
        """Validate system type."""
        valid_types = dict(IntegrationConfig._meta.get_field('system_type').choices).keys()
        if value not in valid_types:
            raise serializers.ValidationError(_('Invalid system type.'))
        return value

    def validate_connection_config(self, value):
        """Validate connection config is a dict."""
        if not isinstance(value, dict):
            raise serializers.ValidationError(_('Connection config must be a JSON object.'))
        return value


class IntegrationConfigUpdateSerializer(BaseModelSerializer):
    """Serializer for updating integration configurations."""

    class Meta(BaseModelSerializer.Meta):
        model = IntegrationConfig
        fields = [
            'system_name',
            'connection_config',
            'enabled_modules',
            'sync_config',
            'mapping_config',
            'is_enabled',
        ]


class TestConnectionSerializer(serializers.Serializer):
    """Serializer for testing connection response."""

    success = serializers.BooleanField(read_only=True)
    message = serializers.CharField(read_only=True)
    response_time_ms = serializers.IntegerField(read_only=True, allow_null=True)
    details = serializers.JSONField(read_only=True, allow_null=True)
