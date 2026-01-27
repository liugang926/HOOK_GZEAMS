"""
Filter Classes for Mobile Enhancement Module.

All filters inherit from BaseModelFilter for common filtering capabilities.
"""
import django_filters
from django_filters import rest_framework as filters
from apps.common.filters.base import BaseModelFilter
from apps.mobile.models import (
    MobileDevice,
    DeviceSecurityLog,
    OfflineData,
    SyncConflict,
    SyncLog,
    ApprovalDelegate,
)


# ========== Mobile Device Filter ==========

class MobileDeviceFilter(BaseModelFilter):
    """Filter for MobileDevice queries."""

    device_type = filters.ChoiceFilter(choices=MobileDevice.DEVICE_TYPES)
    is_bound = filters.BooleanFilter()
    is_active = filters.BooleanFilter()
    user_id = filters.UUIDFilter(field_name='user__id')
    username = filters.CharFilter(field_name='user__username', lookup_expr='icontains')

    # Date range filters
    last_login_from = filters.DateTimeFilter(field_name='last_login_at', lookup_expr='gte')
    last_login_to = filters.DateTimeFilter(field_name='last_login_at', lookup_expr='lte')
    last_sync_from = filters.DateTimeFilter(field_name='last_sync_at', lookup_expr='gte')
    last_sync_to = filters.DateTimeFilter(field_name='last_sync_at', lookup_expr='lte')

    class Meta:
        model = MobileDevice
        fields = [
            'device_type', 'is_bound', 'is_active', 'user_id',
            'last_login_from', 'last_login_to', 'last_sync_from', 'last_sync_to',
        ]


class DeviceSecurityLogFilter(BaseModelFilter):
    """Filter for DeviceSecurityLog queries."""

    event_type = filters.ChoiceFilter(choices=DeviceSecurityLog.EVENT_TYPES)
    device_id = filters.UUIDFilter(field_name='device__id')
    ip_address = filters.CharFilter(lookup_expr='icontains')

    # Date range filters
    created_at_from = filters.DateTimeFilter(field_name='created_at', lookup_expr='gte')
    created_at_to = filters.DateTimeFilter(field_name='created_at', lookup_expr='lte')

    class Meta:
        model = DeviceSecurityLog
        fields = [
            'event_type', 'device_id', 'ip_address',
            'created_at_from', 'created_at_to',
        ]


# ========== Sync Data Filter ==========

class OfflineDataFilter(BaseModelFilter):
    """Filter for OfflineData queries."""

    table_name = filters.CharFilter(lookup_expr='iexact')
    operation = filters.ChoiceFilter(choices=OfflineData.OPERATION_TYPES)
    sync_status = filters.ChoiceFilter(choices=OfflineData.SYNC_STATUS)
    user_id = filters.UUIDFilter(field_name='user__id')
    device_id = filters.UUIDFilter(field_name='device__id')

    # Date range filters
    client_created_from = filters.DateTimeFilter(field_name='client_created_at', lookup_expr='gte')
    client_created_to = filters.DateTimeFilter(field_name='client_created_at', lookup_expr='lte')
    synced_at_from = filters.DateTimeFilter(field_name='synced_at', lookup_expr='gte')
    synced_at_to = filters.DateTimeFilter(field_name='synced_at', lookup_expr='lte')

    class Meta:
        model = OfflineData
        fields = [
            'table_name', 'operation', 'sync_status', 'user_id', 'device_id',
            'client_created_from', 'client_created_to',
            'synced_at_from', 'synced_at_to',
        ]


class SyncConflictFilter(BaseModelFilter):
    """Filter for SyncConflict queries."""

    conflict_type = filters.ChoiceFilter(choices=SyncConflict.CONFLICT_TYPES)
    resolution = filters.ChoiceFilter(choices=SyncConflict.RESOLUTIONS)
    table_name = filters.CharFilter(lookup_expr='iexact')
    user_id = filters.UUIDFilter(field_name='user__id')
    is_resolved = filters.BooleanFilter(method='filter_is_resolved')

    # Date range filters
    resolved_at_from = filters.DateTimeFilter(field_name='resolved_at', lookup_expr='gte')
    resolved_at_to = filters.DateTimeFilter(field_name='resolved_at', lookup_expr='lte')

    class Meta:
        model = SyncConflict
        fields = [
            'conflict_type', 'resolution', 'table_name', 'user_id',
            'resolved_at_from', 'resolved_at_to',
        ]

    def filter_is_resolved(self, queryset, name, value):
        """Filter by resolution status."""
        if value is True:
            return queryset.filter(resolution__in=['server_wins', 'client_wins', 'merge'])
        elif value is False:
            return queryset.filter(resolution='pending')
        return queryset


class SyncLogFilter(BaseModelFilter):
    """Filter for SyncLog queries."""

    sync_type = filters.ChoiceFilter(choices=SyncLog.SYNC_TYPES)
    sync_direction = filters.ChoiceFilter(choices=SyncLog.SYNC_DIRECTIONS)
    status = filters.ChoiceFilter(choices=SyncLog.SYNC_STATUS)
    user_id = filters.UUIDFilter(field_name='user__id')
    device_id = filters.UUIDFilter(field_name='device__id')

    # Date range filters
    started_from = filters.DateTimeFilter(field_name='started_at', lookup_expr='gte')
    started_to = filters.DateTimeFilter(field_name='started_at', lookup_expr='lte')
    finished_from = filters.DateTimeFilter(field_name='finished_at', lookup_expr='gte')
    finished_to = filters.DateTimeFilter(field_name='finished_at', lookup_expr='lte')

    # Duration range
    duration_min = filters.NumberFilter(field_name='duration', lookup_expr='gte')
    duration_max = filters.NumberFilter(field_name='duration', lookup_expr='lte')

    class Meta:
        model = SyncLog
        fields = [
            'sync_type', 'sync_direction', 'status', 'user_id', 'device_id',
            'started_from', 'started_to', 'finished_from', 'finished_to',
            'duration_min', 'duration_max',
        ]


# ========== Approval Delegate Filter ==========

class ApprovalDelegateFilter(BaseModelFilter):
    """Filter for ApprovalDelegate queries."""

    delegate_type = filters.ChoiceFilter(choices=ApprovalDelegate.DELEGATE_TYPES)
    delegate_scope = filters.ChoiceFilter(choices=ApprovalDelegate.DELEGATE_SCOPES)
    is_active = filters.BooleanFilter()
    is_revoked = filters.BooleanFilter()
    delegator_id = filters.UUIDFilter(field_name='delegator__id')
    delegate_id = filters.UUIDFilter(field_name='delegate__id')

    # Date range filters
    start_time_from = filters.DateTimeFilter(field_name='start_time', lookup_expr='gte')
    start_time_to = filters.DateTimeFilter(field_name='start_time', lookup_expr='lte')
    end_time_from = filters.DateTimeFilter(field_name='end_time', lookup_expr='gte')
    end_time_to = filters.DateTimeFilter(field_name='end_time', lookup_expr='lte')

    class Meta:
        model = ApprovalDelegate
        fields = [
            'delegate_type', 'delegate_scope', 'is_active', 'is_revoked',
            'delegator_id', 'delegate_id',
            'start_time_from', 'start_time_to',
            'end_time_from', 'end_time_to',
        ]
