"""
Serializers for Inventory Difference model.
"""
from rest_framework import serializers
from django.utils.translation import gettext_lazy as _

from apps.common.serializers.base import BaseModelSerializer, BaseModelWithAuditSerializer
from apps.accounts.serializers import UserBasicSerializer
from apps.inventory.serializers.task_serializers import InventoryTaskListSerializer
from apps.inventory.models import InventoryDifference


class InventoryDifferenceSerializer(BaseModelSerializer):
    """Serializer for inventory difference."""

    difference_type_label = serializers.CharField(source='get_difference_type_display', read_only=True)
    status_label = serializers.CharField(source='get_status_display', read_only=True)

    task_code = serializers.CharField(source='task.task_code', read_only=True)
    asset_code = serializers.CharField(source='asset.asset_code', read_only=True)
    asset_name = serializers.CharField(source='asset.asset_name', read_only=True)

    resolved_by = UserBasicSerializer(read_only=True)

    class Meta(BaseModelSerializer.Meta):
        model = InventoryDifference
        fields = BaseModelSerializer.Meta.fields + [
            'task',
            'task_code',
            'asset',
            'asset_code',
            'asset_name',
            'difference_type',
            'difference_type_label',
            'description',
            'expected_quantity',
            'actual_quantity',
            'quantity_difference',
            'expected_location',
            'actual_location',
            'expected_custodian',
            'actual_custodian',
            'status',
            'status_label',
            'resolution',
            'resolved_by',
            'resolved_at',
        ]


class InventoryDifferenceListSerializer(BaseModelSerializer):
    """Serializer for inventory difference list view."""

    difference_type_label = serializers.CharField(source='get_difference_type_display', read_only=True)
    status_label = serializers.CharField(source='get_status_display', read_only=True)

    task_code = serializers.CharField(source='task.task_code', read_only=True)
    asset_code = serializers.CharField(source='asset.asset_code', read_only=True)
    asset_name = serializers.CharField(source='asset.asset_name', read_only=True)

    class Meta(BaseModelSerializer.Meta):
        model = InventoryDifference
        fields = [
            'id',
            'task',
            'task_code',
            'asset',
            'asset_code',
            'asset_name',
            'difference_type',
            'difference_type_label',
            'description',
            'expected_quantity',
            'actual_quantity',
            'quantity_difference',
            'expected_location',
            'actual_location',
            'expected_custodian',
            'actual_custodian',
            'status',
            'status_label',
            'created_at',
        ]


class InventoryDifferenceResolveSerializer(serializers.Serializer):
    """Serializer for resolving inventory differences."""

    status = serializers.ChoiceField(
        choices=['resolved', 'ignored'],
        help_text=_('New status for the difference')
    )
    resolution = serializers.CharField(
        required=False,
        allow_blank=True,
        help_text=_('Resolution description')
    )

    class Meta:
        fields = ['status', 'resolution']
