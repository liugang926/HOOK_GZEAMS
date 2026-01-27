"""
Serializers for Inventory Snapshot model.
"""
from rest_framework import serializers
from django.utils.translation import gettext_lazy as _

from apps.common.serializers.base import BaseModelSerializer
from apps.inventory.models import InventorySnapshot


class InventorySnapshotSerializer(BaseModelSerializer):
    """Serializer for inventory snapshot."""

    class Meta(BaseModelSerializer.Meta):
        model = InventorySnapshot
        fields = [
            'id',
            'task',
            'asset',
            'asset_code',
            'asset_name',
            'asset_category_id',
            'asset_category_name',
            'location_id',
            'location_name',
            'custodian_id',
            'custodian_name',
            'department_id',
            'department_name',
            'asset_status',
            'snapshot_data',
            'scanned',
            'scanned_at',
            'scan_count',
        ]


class InventorySnapshotListSerializer(BaseModelSerializer):
    """Serializer for inventory snapshot list view."""

    task_code = serializers.CharField(source='task.task_code', read_only=True)
    scanned = serializers.BooleanField(read_only=True)

    class Meta(BaseModelSerializer.Meta):
        model = InventorySnapshot
        fields = [
            'id',
            'task',
            'task_code',
            'asset',
            'asset_code',
            'asset_name',
            'location_name',
            'custodian_name',
            'department_name',
            'asset_status',
            'scanned',
            'scanned_at',
            'scan_count',
        ]
