"""
Serializers for Offline Data, Sync Conflict, and Sync Log models.
"""
from rest_framework import serializers
from apps.common.serializers.base import (
    BaseModelSerializer,
    BaseModelWithAuditSerializer,
    BaseListSerializer
)
from apps.mobile.models import OfflineData, SyncConflict, SyncLog


class OfflineDataSerializer(BaseModelSerializer):
    """Serializer for OfflineData."""

    operation_display = serializers.CharField(source='get_operation_display', read_only=True)
    sync_status_display = serializers.CharField(source='get_sync_status_display', read_only=True)
    username = serializers.CharField(source='user.username', read_only=True)
    device_name = serializers.CharField(source='device.device_name', read_only=True, allow_null=True)

    class Meta(BaseModelSerializer.Meta):
        model = OfflineData
        fields = BaseModelSerializer.Meta.fields + [
            'user',
            'username',
            'device',
            'device_name',
            'table_name',
            'record_id',
            'operation',
            'operation_display',
            'data',
            'old_data',
            'sync_status',
            'sync_status_display',
            'synced_at',
            'sync_error',
            'client_version',
            'server_version',
            'client_created_at',
            'client_updated_at',
        ]


class OfflineDataListSerializer(BaseListSerializer):
    """Optimized serializer for offline data list views."""

    operation_display = serializers.CharField(source='get_operation_display', read_only=True)
    sync_status_display = serializers.CharField(source='get_sync_status_display', read_only=True)
    username = serializers.CharField(source='user.username', read_only=True)

    class Meta(BaseListSerializer.Meta):
        model = OfflineData
        fields = BaseListSerializer.Meta.fields + [
            'user',
            'username',
            'table_name',
            'operation',
            'operation_display',
            'sync_status',
            'sync_status_display',
            'client_created_at',
            'client_updated_at',
        ]


class SyncConflictSerializer(BaseModelSerializer):
    """Serializer for SyncConflict."""

    conflict_type_display = serializers.CharField(source='get_conflict_type_display', read_only=True)
    resolution_display = serializers.CharField(source='get_resolution_display', read_only=True)
    username = serializers.CharField(source='user.username', read_only=True)
    resolved_by_name = serializers.CharField(source='resolved_by.username', read_only=True, allow_null=True)

    class Meta(BaseModelSerializer.Meta):
        model = SyncConflict
        fields = BaseModelSerializer.Meta.fields + [
            'user',
            'username',
            'offline_data',
            'conflict_type',
            'conflict_type_display',
            'table_name',
            'record_id',
            'local_data',
            'server_data',
            'merged_data',
            'resolution',
            'resolution_display',
            'resolved_by',
            'resolved_by_name',
            'resolved_at',
            'resolution_note',
        ]


class SyncConflictDetailSerializer(BaseModelWithAuditSerializer):
    """Detailed serializer for SyncConflict."""

    conflict_type_display = serializers.CharField(source='get_conflict_type_display', read_only=True)
    resolution_display = serializers.CharField(source='get_resolution_display', read_only=True)
    username = serializers.CharField(source='user.username', read_only=True)
    resolved_by_name = serializers.CharField(source='resolved_by.username', read_only=True, allow_null=True)

    # Include offline data details
    offline_data_operation = serializers.CharField(source='offline_data.operation', read_only=True)
    offline_data_table = serializers.CharField(source='offline_data.table_name', read_only=True)

    class Meta(BaseModelWithAuditSerializer.Meta):
        model = SyncConflict
        fields = BaseModelWithAuditSerializer.Meta.fields + [
            'user',
            'username',
            'offline_data',
            'offline_data_operation',
            'offline_data_table',
            'conflict_type',
            'conflict_type_display',
            'table_name',
            'record_id',
            'local_data',
            'server_data',
            'merged_data',
            'resolution',
            'resolution_display',
            'resolved_by',
            'resolved_by_name',
            'resolved_at',
            'resolution_note',
        ]


class SyncLogSerializer(BaseModelSerializer):
    """Serializer for SyncLog."""

    sync_type_display = serializers.CharField(source='get_sync_type_display', read_only=True)
    sync_direction_display = serializers.CharField(source='get_sync_direction_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    username = serializers.CharField(source='user.username', read_only=True)
    device_name = serializers.CharField(source='device.device_name', read_only=True, allow_null=True)

    class Meta(BaseModelSerializer.Meta):
        model = SyncLog
        fields = BaseModelSerializer.Meta.fields + [
            'user',
            'username',
            'device',
            'device_name',
            'sync_type',
            'sync_type_display',
            'sync_direction',
            'sync_direction_display',
            'status',
            'status_display',
            'tables',
            'upload_count',
            'download_count',
            'conflict_count',
            'error_count',
            'started_at',
            'finished_at',
            'duration',
            'client_version',
            'server_version',
            'error_message',
            'error_details',
            'network_type',
            'data_size',
        ]
