"""
Sync Serializers

Serializers for sync log and sync management.
"""
from rest_framework import serializers
from apps.common.serializers.base import BaseModelSerializer, BaseModelWithAuditSerializer
from apps.sso.models import SyncLog


class SyncLogSerializer(BaseModelSerializer):
    """Sync log serializer - inherits from BaseModelSerializer."""

    # Additional business fields
    duration = serializers.SerializerMethodField()
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    sync_type_display = serializers.CharField(source='get_sync_type_display', read_only=True)
    sync_source_display = serializers.CharField(source='get_sync_source_display', read_only=True)

    class Meta(BaseModelSerializer.Meta):
        model = SyncLog
        # Inherit public fields + business fields
        fields = BaseModelSerializer.Meta.fields + [
            'sync_type',
            'sync_type_display',
            'sync_source',
            'sync_source_display',
            'status',
            'status_display',
            'started_at',
            'finished_at',
            'duration',
            'total_count',
            'created_count',
            'updated_count',
            'deleted_count',
            'failed_count',
            'error_message',
            'error_details',
        ]

    def get_duration(self, obj):
        """Get sync duration in seconds."""
        if obj.finished_at and obj.started_at:
            return int((obj.finished_at - obj.started_at).total_seconds())
        return None


class SyncLogDetailSerializer(BaseModelWithAuditSerializer):
    """Sync log detail serializer - includes full audit info."""

    duration = serializers.SerializerMethodField()
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    sync_type_display = serializers.CharField(source='get_sync_type_display', read_only=True)

    class Meta(BaseModelWithAuditSerializer.Meta):
        model = SyncLog
        # Inherit all audit fields + business fields
        fields = BaseModelWithAuditSerializer.Meta.fields + [
            'sync_type',
            'sync_type_display',
            'sync_source',
            'status',
            'status_display',
            'started_at',
            'finished_at',
            'duration',
            'total_count',
            'created_count',
            'updated_count',
            'deleted_count',
            'failed_count',
            'error_message',
            'error_details',
        ]

    def get_duration(self, obj):
        """Get sync duration in seconds."""
        if obj.finished_at and obj.started_at:
            return int((obj.finished_at - obj.started_at).total_seconds())
        return None


class SyncStatusSerializer(serializers.Serializer):
    """Sync status response serializer."""

    status = serializers.CharField()
    last_sync_time = serializers.DateTimeField(allow_null=True)
    stats = serializers.DictField()


class SyncTriggerSerializer(serializers.Serializer):
    """Trigger sync request serializer."""

    sync_type = serializers.ChoiceField(
        choices=['full', 'department', 'user'],
        default='full',
        required=False,
        help_text='Sync type: full, department, or user only'
    )


class SyncConfigSerializer(serializers.Serializer):
    """Sync configuration response serializer."""

    enabled = serializers.BooleanField()
    corp_name = serializers.CharField(allow_null=True, required=False)
    agent_id = serializers.IntegerField(allow_null=True, required=False)
    auto_sync_enabled = serializers.BooleanField(default=True)
    sync_department = serializers.BooleanField(default=True)
    sync_user = serializers.BooleanField(default=True)
