"""
SSO Serializers

All serializers inherit from BaseModelSerializer for automatic
serialization of common fields and custom_fields support.
"""
from apps.sso.serializers.wework_serializer import (
    WeWorkConfigSerializer,
    WeWorkConfigDetailSerializer,
    UserMappingSerializer,
    OAuthStateSerializer,
)
from apps.sso.serializers.sync_serializer import (
    SyncLogSerializer,
    SyncLogDetailSerializer,
    SyncStatusSerializer,
    SyncTriggerSerializer,
    SyncConfigSerializer,
)

__all__ = [
    'WeWorkConfigSerializer',
    'WeWorkConfigDetailSerializer',
    'UserMappingSerializer',
    'OAuthStateSerializer',
    'SyncLogSerializer',
    'SyncLogDetailSerializer',
    'SyncStatusSerializer',
    'SyncTriggerSerializer',
    'SyncConfigSerializer',
]
