"""
Serializers for IT Assets module.
"""
from .it_assets import (
    ITAssetInfoSerializer,
    ITAssetInfoListSerializer,
    ITAssetInfoDetailSerializer,
    SoftwareSerializer,
    SoftwareListSerializer,
    SoftwareDetailSerializer,
    SoftwareLicenseSerializer,
    SoftwareLicenseListSerializer,
    SoftwareLicenseDetailSerializer,
    LicenseAllocationSerializer,
    LicenseAllocationListSerializer,
    LicenseAllocationDetailSerializer,
    ITMaintenanceRecordSerializer,
    ITMaintenanceRecordListSerializer,
    ITMaintenanceRecordDetailSerializer,
    ConfigurationChangeSerializer,
    ConfigurationChangeListSerializer,
    ConfigurationChangeDetailSerializer,
)

__all__ = [
    'ITAssetInfoSerializer',
    'ITAssetInfoListSerializer',
    'ITAssetInfoDetailSerializer',
    'SoftwareSerializer',
    'SoftwareListSerializer',
    'SoftwareDetailSerializer',
    'SoftwareLicenseSerializer',
    'SoftwareLicenseListSerializer',
    'SoftwareLicenseDetailSerializer',
    'LicenseAllocationSerializer',
    'LicenseAllocationListSerializer',
    'LicenseAllocationDetailSerializer',
    'ITMaintenanceRecordSerializer',
    'ITMaintenanceRecordListSerializer',
    'ITMaintenanceRecordDetailSerializer',
    'ConfigurationChangeSerializer',
    'ConfigurationChangeListSerializer',
    'ConfigurationChangeDetailSerializer',
]
