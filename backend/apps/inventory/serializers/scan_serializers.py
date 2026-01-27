"""
Serializers for Inventory Scan model.
"""
from rest_framework import serializers
from django.utils.translation import gettext_lazy as _

from apps.common.serializers.base import BaseModelSerializer
from apps.accounts.serializers import UserBasicSerializer
from apps.inventory.serializers.task_serializers import InventoryTaskListSerializer
from apps.inventory.models import InventoryScan


class InventoryScanListSerializer(BaseModelSerializer):
    """Serializer for inventory scan list view."""

    scan_status_label = serializers.CharField(source='get_scan_status_label', read_only=True)
    scan_method_label = serializers.CharField(source='get_scan_method_display', read_only=True)

    # Simplified nested data
    task_code = serializers.CharField(source='task.task_code', read_only=True)
    task_name = serializers.CharField(source='task.task_name', read_only=True)
    asset_code = serializers.CharField(source='asset.asset_code', read_only=True)
    asset_name = serializers.CharField(source='asset.asset_name', read_only=True)
    scanned_by_name = serializers.CharField(source='scanned_by.get_full_name', read_only=True)

    class Meta(BaseModelSerializer.Meta):
        model = InventoryScan
        fields = BaseModelSerializer.Meta.fields + [
            'task',
            'task_code',
            'task_name',
            'asset',
            'asset_code',
            'asset_name',
            'qr_code',
            'scanned_by',
            'scanned_by_name',
            'scanned_at',
            'scan_method',
            'scan_method_label',
            'scan_status',
            'scan_status_label',
            'original_location_name',
            'original_custodian_name',
            'actual_location_name',
            'actual_custodian_name',
            'remark',
            'latitude',
            'longitude',
        ]


class InventoryScanDetailSerializer(BaseModelSerializer):
    """Serializer for inventory scan detail view."""

    scan_status_label = serializers.CharField(source='get_scan_status_label', read_only=True)
    scan_method_label = serializers.CharField(source='get_scan_method_display', read_only=True)

    task = InventoryTaskListSerializer(read_only=True)
    asset_code = serializers.CharField(source='asset.asset_code', read_only=True)
    asset_name = serializers.CharField(source='asset.asset_name', read_only=True)
    scanned_by = UserBasicSerializer(read_only=True)

    class Meta(BaseModelSerializer.Meta):
        model = InventoryScan
        fields = BaseModelSerializer.Meta.fields + [
            'task',
            'asset',
            'asset_code',
            'asset_name',
            'qr_code',
            'scanned_by',
            'scanned_at',
            'scan_method',
            'scan_method_label',
            'scan_status',
            'scan_status_label',
            'original_location_id',
            'original_location_name',
            'original_custodian_id',
            'original_custodian_name',
            'actual_location_id',
            'actual_location_name',
            'actual_custodian_id',
            'actual_custodian_name',
            'photos',
            'remark',
            'latitude',
            'longitude',
        ]


class InventoryScanCreateSerializer(serializers.Serializer):
    """Serializer for creating inventory scan records."""

    task = serializers.CharField(
        required=True,
        help_text=_('Inventory Task ID')
    )
    qr_code = serializers.CharField(
        required=True,
        max_length=500,
        help_text=_('Scanned QR code')
    )
    scan_method = serializers.CharField(
        required=False,
        default='qr',
        help_text=_('Scan method')
    )
    scan_status = serializers.CharField(
        required=False,
        default='normal',
        help_text=_('Scan status')
    )
    actual_location_id = serializers.CharField(
        required=False,
        allow_null=True,
        help_text=_('Actual location ID')
    )
    actual_location_name = serializers.CharField(
        required=False,
        allow_blank=True,
        help_text=_('Actual location name')
    )
    actual_custodian_id = serializers.CharField(
        required=False,
        allow_null=True,
        help_text=_('Actual custodian ID')
    )
    actual_custodian_name = serializers.CharField(
        required=False,
        allow_blank=True,
        help_text=_('Actual custodian name')
    )
    photos = serializers.ListField(
        required=False,
        child=serializers.CharField(),
        help_text=_('Photo URLs')
    )
    remark = serializers.CharField(
        required=False,
        allow_blank=True,
        help_text=_('Scan remark')
    )
    latitude = serializers.DecimalField(
        required=False,
        allow_null=True,
        max_digits=10,
        decimal_places=7,
        help_text=_('GPS latitude')
    )
    longitude = serializers.DecimalField(
        required=False,
        allow_null=True,
        max_digits=10,
        decimal_places=7,
        help_text=_('GPS longitude')
    )

    def validate_qr_code(self, value):
        """Validate QR code is provided."""
        if not value:
            raise serializers.ValidationError(_('QR code is required.'))
        return value

    def validate_task(self, value):
        """Validate task is provided."""
        if not value:
            raise serializers.ValidationError(_('Task is required.'))
        return value


class InventoryScanUpdateSerializer(BaseModelSerializer):
    """Serializer for updating inventory scan records."""

    class Meta(BaseModelSerializer.Meta):
        model = InventoryScan
        fields = [
            'scan_status',
            'actual_location_id',
            'actual_location_name',
            'actual_custodian_id',
            'actual_custodian_name',
            'photos',
            'remark',
        ]


class InventoryBatchScanSerializer(serializers.Serializer):
    """Serializer for batch scan operations."""

    task = serializers.CharField(
        required=False,
        help_text=_('Task ID for the scan operation')
    )
    scans = serializers.ListField(
        child=serializers.DictField(),
        help_text=_('List of scan records')
    )

    class Meta:
        fields = ['task', 'scans']

    def validate_scans(self, value):
        """Validate scan records list."""
        if not value:
            raise serializers.ValidationError(_('At least one scan record is required.'))

        required_fields = ['qr_code']
        for idx, scan in enumerate(value):
            for field in required_fields:
                if field not in scan or not scan[field]:
                    raise serializers.ValidationError({
                        f'scans.{idx}.{field}': _('This field is required.')
                    })

        return value


class InventoryScanValidateSerializer(serializers.Serializer):
    """Serializer for validating QR codes."""

    qr_code = serializers.CharField(
        max_length=500,
        help_text=_('QR code content to validate')
    )

    class Meta:
        fields = ['qr_code']
