"""
Serializers for IT Asset models.
"""
from rest_framework import serializers
from apps.common.serializers.base import (
    BaseModelSerializer,
    BaseModelWithAuditSerializer,
    BaseListSerializer
)
from apps.it_assets.models import (
    ITAssetInfo,
    Software,
    SoftwareLicense,
    LicenseAllocation,
    ITMaintenanceRecord,
    ConfigurationChange
)


class ITAssetInfoSerializer(BaseModelSerializer):
    """Serializer for ITAssetInfo."""

    asset_code = serializers.CharField(source='asset.asset_code', read_only=True)
    asset_name = serializers.CharField(source='asset.asset_name', read_only=True)
    disk_type_display = serializers.CharField(source='get_disk_type_display', read_only=True)

    class Meta(BaseModelSerializer.Meta):
        model = ITAssetInfo
        fields = BaseModelSerializer.Meta.fields + [
            'asset',
            'asset_code',
            'asset_name',
            'cpu_model',
            'cpu_cores',
            'cpu_threads',
            'ram_capacity',
            'ram_type',
            'ram_slots',
            'disk_type',
            'disk_type_display',
            'disk_capacity',
            'disk_count',
            'gpu_model',
            'gpu_memory',
            'mac_address',
            'ip_address',
            'hostname',
            'os_name',
            'os_version',
            'os_architecture',
            'os_license_key',
            'disk_encrypted',
            'antivirus_software',
            'antivirus_enabled',
            'ad_domain',
            'ad_computer_name',
        ]


class ITAssetInfoListSerializer(BaseListSerializer):
    """Optimized serializer for IT asset info list views."""

    asset_code = serializers.CharField(source='asset.asset_code', read_only=True)
    asset_name = serializers.CharField(source='asset.asset_name', read_only=True)

    class Meta(BaseListSerializer.Meta):
        model = ITAssetInfo
        fields = BaseListSerializer.Meta.fields + [
            'asset',
            'asset_code',
            'asset_name',
            'cpu_model',
            'ram_capacity',
            'disk_capacity',
            'mac_address',
            'ip_address',
            'os_name',
            'os_version',
        ]


class ITAssetInfoDetailSerializer(BaseModelWithAuditSerializer):
    """Detailed serializer for IT asset info."""

    asset_code = serializers.CharField(source='asset.asset_code', read_only=True)
    asset_name = serializers.CharField(source='asset.asset_name', read_only=True)
    disk_type_display = serializers.CharField(source='get_disk_type_display', read_only=True)
    full_config = serializers.CharField(source='get_full_config', read_only=True)

    class Meta(BaseModelWithAuditSerializer.Meta):
        model = ITAssetInfo
        fields = BaseModelWithAuditSerializer.Meta.fields + [
            'asset',
            'asset_code',
            'asset_name',
            'cpu_model',
            'cpu_cores',
            'cpu_threads',
            'ram_capacity',
            'ram_type',
            'ram_slots',
            'disk_type',
            'disk_type_display',
            'disk_capacity',
            'disk_count',
            'gpu_model',
            'gpu_memory',
            'mac_address',
            'ip_address',
            'hostname',
            'os_name',
            'os_version',
            'os_architecture',
            'os_license_key',
            'disk_encrypted',
            'antivirus_software',
            'antivirus_enabled',
            'ad_domain',
            'ad_computer_name',
            'full_config',
        ]


class SoftwareSerializer(BaseModelSerializer):
    """Serializer for Software."""

    license_type_display = serializers.CharField(source='get_license_type_display', read_only=True)
    licenses_count = serializers.SerializerMethodField()

    class Meta(BaseModelSerializer.Meta):
        model = Software
        fields = BaseModelSerializer.Meta.fields + [
            'name',
            'vendor',
            'version',
            'category',
            'license_type',
            'license_type_display',
            'description',
            'website_url',
            'licenses_count',
        ]

    def get_licenses_count(self, obj):
        """Get the count of licenses for this software."""
        return obj.licenses.count()


class SoftwareListSerializer(BaseListSerializer):
    """Optimized serializer for software list views."""

    license_type_display = serializers.CharField(source='get_license_type_display', read_only=True)
    licenses_count = serializers.SerializerMethodField()

    class Meta(BaseListSerializer.Meta):
        model = Software
        fields = BaseListSerializer.Meta.fields + [
            'name',
            'vendor',
            'version',
            'category',
            'license_type',
            'license_type_display',
            'licenses_count',
        ]

    def get_licenses_count(self, obj):
        """Get the count of licenses for this software."""
        return obj.licenses.count()


class SoftwareDetailSerializer(BaseModelWithAuditSerializer):
    """Detailed serializer for Software."""

    license_type_display = serializers.CharField(source='get_license_type_display', read_only=True)
    licenses = serializers.SerializerMethodField()

    class Meta(BaseModelWithAuditSerializer.Meta):
        model = Software
        fields = BaseModelWithAuditSerializer.Meta.fields + [
            'name',
            'vendor',
            'version',
            'category',
            'license_type',
            'license_type_display',
            'description',
            'website_url',
            'licenses',
        ]

    def get_licenses(self, obj):
        """Get all licenses for this software."""
        from .it_assets import SoftwareLicenseListSerializer
        return SoftwareLicenseListSerializer(obj.licenses.all(), many=True).data


class SoftwareLicenseSerializer(BaseModelSerializer):
    """Serializer for SoftwareLicense."""

    software_name = serializers.CharField(source='software.name', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    available_seats = serializers.ReadOnlyField()
    is_expired = serializers.ReadOnlyField()

    class Meta(BaseModelSerializer.Meta):
        model = SoftwareLicense
        fields = BaseModelSerializer.Meta.fields + [
            'software',
            'software_name',
            'license_key',
            'seats',
            'seats_used',
            'available_seats',
            'purchase_date',
            'expiry_date',
            'cost',
            'currency',
            'status',
            'status_display',
            'is_expired',
            'vendor_reference',
            'notes',
        ]


class SoftwareLicenseListSerializer(BaseListSerializer):
    """Optimized serializer for software license list views."""

    software_name = serializers.CharField(source='software.name', read_only=True)
    software_vendor = serializers.CharField(source='software.vendor', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    available_seats = serializers.ReadOnlyField()

    class Meta(BaseListSerializer.Meta):
        model = SoftwareLicense
        fields = BaseListSerializer.Meta.fields + [
            'software',
            'software_name',
            'software_vendor',
            'license_key',
            'seats',
            'seats_used',
            'available_seats',
            'purchase_date',
            'expiry_date',
            'cost',
            'currency',
            'status',
            'status_display',
            'is_expired',
        ]


class SoftwareLicenseDetailSerializer(BaseModelWithAuditSerializer):
    """Detailed serializer for SoftwareLicense."""

    software_name = serializers.CharField(source='software.name', read_only=True)
    software_vendor = serializers.CharField(source='software.vendor', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    available_seats = serializers.ReadOnlyField()
    is_expired = serializers.ReadOnlyField()
    allocations = serializers.SerializerMethodField()

    class Meta(BaseModelWithAuditSerializer.Meta):
        model = SoftwareLicense
        fields = BaseModelWithAuditSerializer.Meta.fields + [
            'software',
            'software_name',
            'software_vendor',
            'license_key',
            'seats',
            'seats_used',
            'available_seats',
            'purchase_date',
            'expiry_date',
            'cost',
            'currency',
            'status',
            'status_display',
            'is_expired',
            'vendor_reference',
            'notes',
            'allocations',
        ]

    def get_allocations(self, obj):
        """Get all allocations for this license."""
        from .it_assets import LicenseAllocationListSerializer
        active_allocations = obj.allocations.filter(deallocated_date__isnull=True)
        return LicenseAllocationListSerializer(active_allocations, many=True).data


class LicenseAllocationSerializer(BaseModelSerializer):
    """Serializer for LicenseAllocation."""

    asset_code = serializers.CharField(source='asset.asset_code', read_only=True)
    asset_name = serializers.CharField(source='asset.asset_name', read_only=True)
    software_name = serializers.CharField(source='license.software.name', read_only=True)
    allocated_by_username = serializers.CharField(source='allocated_by.username', read_only=True)
    deallocated_by_username = serializers.CharField(source='deallocated_by.username', read_only=True)
    is_active = serializers.ReadOnlyField()

    class Meta(BaseModelSerializer.Meta):
        model = LicenseAllocation
        fields = BaseModelSerializer.Meta.fields + [
            'license',
            'software_name',
            'asset',
            'asset_code',
            'asset_name',
            'allocated_by',
            'allocated_by_username',
            'allocated_date',
            'deallocated_by',
            'deallocated_by_username',
            'deallocated_date',
            'notes',
            'is_active',
        ]


class LicenseAllocationListSerializer(BaseListSerializer):
    """Optimized serializer for license allocation list views."""

    asset_code = serializers.CharField(source='asset.asset_code', read_only=True)
    asset_name = serializers.CharField(source='asset.asset_name', read_only=True)
    software_name = serializers.CharField(source='license.software.name', read_only=True)
    is_active = serializers.ReadOnlyField()

    class Meta(BaseListSerializer.Meta):
        model = LicenseAllocation
        fields = BaseListSerializer.Meta.fields + [
            'license',
            'software_name',
            'asset',
            'asset_code',
            'asset_name',
            'allocated_date',
            'deallocated_date',
            'is_active',
        ]


class LicenseAllocationDetailSerializer(BaseModelWithAuditSerializer):
    """Detailed serializer for LicenseAllocation."""

    asset_code = serializers.CharField(source='asset.asset_code', read_only=True)
    asset_name = serializers.CharField(source='asset.asset_name', read_only=True)
    software_name = serializers.CharField(source='license.software.name', read_only=True)
    allocated_by_username = serializers.CharField(source='allocated_by.username', read_only=True)
    deallocated_by_username = serializers.CharField(source='deallocated_by.username', read_only=True)
    is_active = serializers.ReadOnlyField()

    class Meta(BaseModelWithAuditSerializer.Meta):
        model = LicenseAllocation
        fields = BaseModelWithAuditSerializer.Meta.fields + [
            'license',
            'software_name',
            'asset',
            'asset_code',
            'asset_name',
            'allocated_by',
            'allocated_by_username',
            'allocated_date',
            'deallocated_by',
            'deallocated_by_username',
            'deallocated_date',
            'notes',
            'is_active',
        ]


class ITMaintenanceRecordSerializer(BaseModelSerializer):
    """Serializer for ITMaintenanceRecord."""

    asset_code = serializers.CharField(source='asset.asset_code', read_only=True)
    asset_name = serializers.CharField(source='asset.asset_name', read_only=True)
    maintenance_type_display = serializers.CharField(source='get_maintenance_type_display', read_only=True)
    performed_by_username = serializers.CharField(source='performed_by.username', read_only=True)

    class Meta(BaseModelSerializer.Meta):
        model = ITMaintenanceRecord
        fields = BaseModelSerializer.Meta.fields + [
            'asset',
            'asset_code',
            'asset_name',
            'maintenance_type',
            'maintenance_type_display',
            'title',
            'description',
            'performed_by',
            'performed_by_username',
            'maintenance_date',
            'cost',
            'vendor',
            'notes',
        ]


class ITMaintenanceRecordListSerializer(BaseListSerializer):
    """Optimized serializer for maintenance record list views."""

    asset_code = serializers.CharField(source='asset.asset_code', read_only=True)
    asset_name = serializers.CharField(source='asset.asset_name', read_only=True)
    maintenance_type_display = serializers.CharField(source='get_maintenance_type_display', read_only=True)

    class Meta(BaseListSerializer.Meta):
        model = ITMaintenanceRecord
        fields = BaseListSerializer.Meta.fields + [
            'asset',
            'asset_code',
            'asset_name',
            'maintenance_type',
            'maintenance_type_display',
            'title',
            'performed_by',
            'maintenance_date',
            'cost',
            'vendor',
        ]


class ITMaintenanceRecordDetailSerializer(BaseModelWithAuditSerializer):
    """Detailed serializer for ITMaintenanceRecord."""

    asset_code = serializers.CharField(source='asset.asset_code', read_only=True)
    asset_name = serializers.CharField(source='asset.asset_name', read_only=True)
    maintenance_type_display = serializers.CharField(source='get_maintenance_type_display', read_only=True)
    performed_by_username = serializers.CharField(source='performed_by.username', read_only=True)

    class Meta(BaseModelWithAuditSerializer.Meta):
        model = ITMaintenanceRecord
        fields = BaseModelWithAuditSerializer.Meta.fields + [
            'asset',
            'asset_code',
            'asset_name',
            'maintenance_type',
            'maintenance_type_display',
            'title',
            'description',
            'performed_by',
            'performed_by_username',
            'maintenance_date',
            'cost',
            'vendor',
            'notes',
        ]


class ConfigurationChangeSerializer(BaseModelSerializer):
    """Serializer for ConfigurationChange."""

    asset_code = serializers.CharField(source='asset.asset_code', read_only=True)
    asset_name = serializers.CharField(source='asset.asset_name', read_only=True)
    changed_by_username = serializers.CharField(source='changed_by.username', read_only=True)

    class Meta(BaseModelSerializer.Meta):
        model = ConfigurationChange
        fields = BaseModelSerializer.Meta.fields + [
            'asset',
            'asset_code',
            'asset_name',
            'field_name',
            'old_value',
            'new_value',
            'change_reason',
            'changed_by',
            'changed_by_username',
            'change_date',
        ]


class ConfigurationChangeListSerializer(BaseListSerializer):
    """Optimized serializer for configuration change list views."""

    asset_code = serializers.CharField(source='asset.asset_code', read_only=True)
    asset_name = serializers.CharField(source='asset.asset_name', read_only=True)

    class Meta(BaseListSerializer.Meta):
        model = ConfigurationChange
        fields = BaseListSerializer.Meta.fields + [
            'asset',
            'asset_code',
            'asset_name',
            'field_name',
            'old_value',
            'new_value',
            'change_reason',
            'changed_by',
            'change_date',
        ]


class ConfigurationChangeDetailSerializer(BaseModelWithAuditSerializer):
    """Detailed serializer for ConfigurationChange."""

    asset_code = serializers.CharField(source='asset.asset_code', read_only=True)
    asset_name = serializers.CharField(source='asset.asset_name', read_only=True)
    changed_by_username = serializers.CharField(source='changed_by.username', read_only=True)

    class Meta(BaseModelWithAuditSerializer.Meta):
        model = ConfigurationChange
        fields = BaseModelWithAuditSerializer.Meta.fields + [
            'asset',
            'asset_code',
            'asset_name',
            'field_name',
            'old_value',
            'new_value',
            'change_reason',
            'changed_by',
            'changed_by_username',
            'change_date',
        ]
