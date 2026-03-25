"""
Serializers for integration log models.

Provides serializers for IntegrationLog model following BaseModelSerializer pattern.
"""
from rest_framework import serializers

from apps.common.serializers.base import BaseModelSerializer
from apps.integration.models import IntegrationLog


class IntegrationLogListSerializer(BaseModelSerializer):
    """Lightweight serializer for list views."""

    system_type_display = serializers.CharField(source='get_system_type_display', read_only=True)
    action_display = serializers.CharField(source='get_action_display', read_only=True)
    duration_seconds = serializers.FloatField(source='duration_ms', read_only=True)
    task_id = serializers.CharField(source='sync_task.task_id', read_only=True, allow_null=True)

    class Meta(BaseModelSerializer.Meta):
        model = IntegrationLog
        fields = [
            'id',
            'sync_task',
            'task_id',
            'system_type',
            'system_type_display',
            'integration_type',
            'action',
            'action_display',
            'request_method',
            'request_url',
            'status_code',
            'success',
            'duration_seconds',
            'business_type',
            'business_id',
            'external_id',
            'created_at',
        ]


class IntegrationLogDetailSerializer(BaseModelSerializer):
    """Detailed serializer for single instance view."""

    system_type_display = serializers.CharField(source='get_system_type_display', read_only=True)
    action_display = serializers.CharField(source='get_action_display', read_only=True)
    duration_seconds = serializers.FloatField(source='duration_ms', read_only=True)
    task_info = serializers.SerializerMethodField()

    class Meta(BaseModelSerializer.Meta):
        model = IntegrationLog
        fields = BaseModelSerializer.Meta.fields + [
            'sync_task',
            'task_info',
            'system_type',
            'system_type_display',
            'integration_type',
            'action',
            'action_display',
            'request_method',
            'request_url',
            'request_headers',
            'request_body',
            'status_code',
            'response_headers',
            'response_body',
            'success',
            'error_message',
            'duration_seconds',
            'business_type',
            'business_id',
            'external_id',
        ]

    def get_task_info(self, obj):
        """Get task info if available."""
        if obj.sync_task:
            return {
                'id': str(obj.sync_task.id),
                'task_id': obj.sync_task.task_id,
                'business_type': obj.sync_task.business_type,
            }
        return None


class LogStatisticsSerializer(serializers.Serializer):
    """Serializer for log statistics."""

    total = serializers.IntegerField(read_only=True)
    success = serializers.IntegerField(read_only=True)
    failed = serializers.IntegerField(read_only=True)
    success_rate = serializers.FloatField(read_only=True)
    avg_duration_ms = serializers.FloatField(read_only=True)
    by_system = serializers.ListField(read_only=True)
    by_action = serializers.ListField(read_only=True)
