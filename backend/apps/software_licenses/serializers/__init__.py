from rest_framework import serializers
from apps.common.serializers.base import BaseModelSerializer
from apps.software_licenses.models import Software, SoftwareLicense, LicenseAllocation


class SoftwareSerializer(BaseModelSerializer):
    """Software Catalog Serializer"""

    class Meta(BaseModelSerializer.Meta):
        model = Software
        fields = BaseModelSerializer.Meta.fields + [
            'code', 'name', 'version', 'vendor', 'software_type',
            'license_type', 'category', 'is_active',
        ]


class SoftwareListSerializer(BaseModelSerializer):
    """Lightweight serializer for list views"""

    class Meta(BaseModelSerializer.Meta):
        model = Software
        fields = BaseModelSerializer.Meta.fields + [
            'code', 'name', 'version', 'vendor', 'software_type', 'is_active',
        ]


class SoftwareDetailSerializer(BaseModelSerializer):
    """Detailed serializer with nested category"""

    category_name = serializers.CharField(source='category.name', read_only=True)

    class Meta(BaseModelSerializer.Meta):
        model = Software
        fields = SoftwareSerializer.Meta.fields + ['category_name']


class SoftwareLicenseSerializer(BaseModelSerializer):
    """Software License Serializer"""
    software_name = serializers.CharField(source='software.name', read_only=True)
    software_version = serializers.CharField(source='software.version', read_only=True)
    available_units = serializers.IntegerField(read_only=True)
    utilization_rate = serializers.FloatField(read_only=True)
    is_expired = serializers.BooleanField(read_only=True)

    class Meta(BaseModelSerializer.Meta):
        model = SoftwareLicense
        fields = BaseModelSerializer.Meta.fields + [
            'license_no', 'software', 'software_name', 'software_version',
            'license_key', 'total_units', 'used_units', 'available_units',
            'utilization_rate', 'purchase_date', 'expiry_date', 'is_expired',
            'purchase_price', 'annual_cost', 'status', 'license_type',
            'agreement_no', 'vendor', 'notes',
        ]
        extra_kwargs = {
            'license_key': {'write_only': True},
        }


class SoftwareLicenseListSerializer(BaseModelSerializer):
    """Lightweight license serializer for lists"""
    software_name = serializers.CharField(source='software.name', read_only=True)
    available_units = serializers.IntegerField(read_only=True)
    utilization_rate = serializers.FloatField(read_only=True)

    class Meta(BaseModelSerializer.Meta):
        model = SoftwareLicense
        fields = [
            'id', 'license_no', 'software', 'software_name',
            'total_units', 'used_units', 'available_units',
            'utilization_rate', 'expiry_date', 'status',
            'created_at', 'updated_at',
        ]


class SoftwareLicenseDetailSerializer(BaseModelSerializer):
    """Detailed license serializer"""
    software_name = serializers.CharField(source='software.name', read_only=True)
    software_version = serializers.CharField(source='software.version', read_only=True)
    software_type = serializers.CharField(source='software.software_type', read_only=True)
    available_units = serializers.IntegerField(read_only=True)
    utilization_rate = serializers.FloatField(read_only=True)
    is_expired = serializers.BooleanField(read_only=True)
    vendor_name = serializers.CharField(source='vendor.name', read_only=True)

    class Meta(BaseModelSerializer.Meta):
        model = SoftwareLicense
        fields = SoftwareLicenseSerializer.Meta.fields + [
            'software_type', 'vendor_name',
        ]


class LicenseAllocationSerializer(BaseModelSerializer):
    """License Allocation Serializer"""
    software_name = serializers.CharField(source='license.software.name', read_only=True)
    asset_name = serializers.CharField(source='asset.asset_name', read_only=True)
    asset_code = serializers.CharField(source='asset.asset_code', read_only=True)
    allocated_by_name = serializers.CharField(source='allocated_by.username', read_only=True)
    deallocated_by_name = serializers.CharField(source='deallocated_by.username', read_only=True)

    class Meta(BaseModelSerializer.Meta):
        model = LicenseAllocation
        fields = BaseModelSerializer.Meta.fields + [
            'license', 'software_name', 'asset', 'asset_name', 'asset_code',
            'allocated_date', 'allocated_by', 'allocated_by_name',
            'deallocated_date', 'deallocated_by', 'deallocated_by_name',
            'allocation_key', 'is_active', 'notes',
        ]
        extra_kwargs = {
            'allocated_date': {'required': False, 'read_only': True},
            'allocated_by': {'required': False, 'read_only': True},
        }


class LicenseAllocationListSerializer(BaseModelSerializer):
    """Lightweight allocation serializer for lists"""

    class Meta(BaseModelSerializer.Meta):
        model = LicenseAllocation
        fields = [
            'id', 'license', 'asset', 'allocated_date',
            'is_active', 'deallocated_date', 'created_at',
        ]


class LicenseAllocationDetailSerializer(BaseModelSerializer):
    """Detailed allocation serializer"""
    software_name = serializers.CharField(source='license.software.name', read_only=True)
    license_no = serializers.CharField(source='license.license_no', read_only=True)
    asset_name = serializers.CharField(source='asset.asset_name', read_only=True)
    asset_code = serializers.CharField(source='asset.asset_code', read_only=True)
    allocated_by_name = serializers.CharField(source='allocated_by.username', read_only=True)
    deallocated_by_name = serializers.CharField(source='deallocated_by.username', read_only=True)

    class Meta(BaseModelSerializer.Meta):
        model = LicenseAllocation
        fields = LicenseAllocationSerializer.Meta.fields + [
            'software_name', 'license_no', 'asset_name', 'asset_code',
        ]


__all__ = [
    'SoftwareSerializer',
    'SoftwareListSerializer',
    'SoftwareDetailSerializer',
    'SoftwareLicenseSerializer',
    'SoftwareLicenseListSerializer',
    'SoftwareLicenseDetailSerializer',
    'LicenseAllocationSerializer',
    'LicenseAllocationListSerializer',
    'LicenseAllocationDetailSerializer',
]
