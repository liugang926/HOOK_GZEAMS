"""
Serializers for integration sync task models.

Provides serializers for IntegrationSyncTask model following BaseModelSerializer pattern.
"""
from rest_framework import serializers
from django.utils.translation import gettext_lazy as _

from apps.common.serializers.base import BaseModelSerializer
from apps.integration.models import IntegrationSyncTask
from apps.integration.constants import SyncStatus


class IntegrationSyncTaskListSerializer(BaseModelSerializer):
    """Lightweight serializer for list views."""

    system_type = serializers.CharField(source='config.system_type', read_only=True)
    system_name = serializers.CharField(source='config.system_name', read_only=True)
    module_type_display = serializers.CharField(source='get_module_type_display', read_only=True)
    direction_display = serializers.CharField(source='get_direction_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    progress_percentage = serializers.SerializerMethodField()
    duration_seconds = serializers.FloatField(source='duration_ms', read_only=True)

    class Meta(BaseModelSerializer.Meta):
        model = IntegrationSyncTask
        fields = [
            'id',
            'task_id',
            'config',
            'system_type',
            'system_name',
            'module_type',
            'module_type_display',
            'direction',
            'direction_display',
            'business_type',
            'status',
            'status_display',
            'total_count',
            'success_count',
            'failed_count',
            'progress_percentage',
            'duration_seconds',
            'started_at',
            'completed_at',
            'created_at',
        ]

    def get_progress_percentage(self, obj):
        """Calculate progress percentage."""
        if obj.total_count == 0:
            return 0
        return int((obj.success_count + obj.failed_count) / obj.total_count * 100)


class IntegrationSyncTaskDetailSerializer(BaseModelSerializer):
    """Detailed serializer for single instance view."""

    config_display = serializers.SerializerMethodField()
    module_type_display = serializers.CharField(source='get_module_type_display', read_only=True)
    direction_display = serializers.CharField(source='get_direction_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    progress_percentage = serializers.SerializerMethodField()
    duration_seconds = serializers.FloatField(read_only=True)
    is_completed = serializers.SerializerMethodField()
    is_running = serializers.SerializerMethodField()
    is_failed = serializers.SerializerMethodField()
    recent_logs = serializers.SerializerMethodField()

    class Meta(BaseModelSerializer.Meta):
        model = IntegrationSyncTask
        fields = BaseModelSerializer.Meta.fields + [
            'task_id',
            'config',
            'config_display',
            'module_type',
            'module_type_display',
            'direction',
            'direction_display',
            'business_type',
            'sync_params',
            'status',
            'status_display',
            'total_count',
            'success_count',
            'failed_count',
            'error_summary',
            'progress_percentage',
            'duration_seconds',
            'started_at',
            'completed_at',
            'is_completed',
            'is_running',
            'is_failed',
            'celery_task_id',
            'recent_logs',
        ]

    def get_config_display(self, obj):
        """Get simplified config info."""
        return {
            'id': str(obj.config.id),
            'system_type': obj.config.system_type,
            'system_name': obj.config.system_name,
        }

    def get_progress_percentage(self, obj):
        """Calculate progress percentage."""
        if obj.total_count == 0:
            return 0
        return int((obj.success_count + obj.failed_count) / obj.total_count * 100)

    def get_is_completed(self, obj):
        """Check if task is completed."""
        return obj.status in [SyncStatus.SUCCESS, SyncStatus.PARTIAL_SUCCESS, SyncStatus.FAILED]

    def get_is_running(self, obj):
        """Check if task is running."""
        return obj.status == SyncStatus.RUNNING

    def get_is_failed(self, obj):
        """Check if task failed."""
        return obj.status == SyncStatus.FAILED

    def get_recent_logs(self, obj):
        """Get recent logs for this task."""
        from apps.integration.serializers import IntegrationLogListSerializer
        recent_logs = obj.logs.order_by('-created_at')[:10]
        return IntegrationLogListSerializer(recent_logs, many=True).data


class CreateSyncTaskSerializer(serializers.Serializer):
    """Serializer for creating sync tasks."""

    config_id = serializers.UUIDField(required=True)
    module_type = serializers.ChoiceField(
        choices=['procurement', 'finance', 'inventory', 'hr', 'crm'],
        required=True
    )
    direction = serializers.ChoiceField(
        choices=['pull', 'push', 'bidirectional'],
        required=True
    )
    business_type = serializers.CharField(max_length=50, required=True)
    sync_params = serializers.JSONField(required=False, default=dict)

    def validate_config_id(self, value):
        """Validate config exists and is enabled."""
        from apps.integration.models import IntegrationConfig
        try:
            config = IntegrationConfig.objects.get(id=value, is_deleted=False)
            if not config.is_enabled:
                raise serializers.ValidationError(_('Integration config is not enabled.'))
            return config
        except IntegrationConfig.DoesNotExist:
            raise serializers.ValidationError(_('Integration config not found.'))


class CancelTaskSerializer(serializers.Serializer):
    """Serializer for cancel task response."""

    success = serializers.BooleanField()
    message = serializers.CharField()
