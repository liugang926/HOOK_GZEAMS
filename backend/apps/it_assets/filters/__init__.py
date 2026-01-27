"""
Filter Classes for IT Assets Module.

All filters inherit from BaseModelFilter for common filtering capabilities.
"""
import django_filters
from django_filters import rest_framework as filters
from django.db import models
from apps.common.filters.base import BaseModelFilter
from apps.it_assets.models import (
    ITAssetInfo,
    Software,
    SoftwareLicense,
    LicenseAllocation,
    ITMaintenanceRecord,
    ConfigurationChange
)


# ========== IT Asset Info Filter ==========

class ITAssetInfoFilter(BaseModelFilter):
    """Filter for ITAssetInfo queries."""

    asset_id = filters.UUIDFilter(field_name='asset__id')
    asset_code = filters.CharFilter(field_name='asset__asset_code', lookup_expr='icontains')
    asset_name = filters.CharFilter(field_name='asset__asset_name', lookup_expr='icontains')
    cpu_model = filters.CharFilter(lookup_expr='icontains')
    disk_type = filters.ChoiceFilter(choices=ITAssetInfo.DISK_TYPE_CHOICES)
    os_name = filters.CharFilter(lookup_expr='icontains')
    mac_address = filters.CharFilter(lookup_expr='icontains')
    ip_address = filters.CharFilter(lookup_expr='icontains')
    hostname = filters.CharFilter(lookup_expr='icontains')
    disk_encrypted = filters.BooleanFilter()
    antivirus_enabled = filters.BooleanFilter()

    # RAM range filters
    ram_capacity_min = filters.NumberFilter(field_name='ram_capacity', lookup_expr='gte')
    ram_capacity_max = filters.NumberFilter(field_name='ram_capacity', lookup_expr='lte')

    # Disk range filters
    disk_capacity_min = filters.NumberFilter(field_name='disk_capacity', lookup_expr='gte')
    disk_capacity_max = filters.NumberFilter(field_name='disk_capacity', lookup_expr='lte')

    class Meta:
        model = ITAssetInfo
        fields = [
            'asset_id', 'asset_code', 'asset_name', 'cpu_model', 'disk_type',
            'os_name', 'mac_address', 'ip_address', 'hostname',
            'disk_encrypted', 'antivirus_enabled',
            'ram_capacity_min', 'ram_capacity_max',
            'disk_capacity_min', 'disk_capacity_max',
        ]


# ========== Software Filter ==========

class SoftwareFilter(BaseModelFilter):
    """Filter for Software queries."""

    name = filters.CharFilter(lookup_expr='icontains')
    vendor = filters.CharFilter(lookup_expr='icontains')
    version = filters.CharFilter(lookup_expr='icontains')
    category = filters.CharFilter(lookup_expr='icontains')
    license_type = filters.ChoiceFilter(choices=Software.LICENSE_TYPE_CHOICES)

    class Meta:
        model = Software
        fields = ['name', 'vendor', 'version', 'category', 'license_type']


# ========== Software License Filter ==========

class SoftwareLicenseFilter(BaseModelFilter):
    """Filter for SoftwareLicense queries."""

    software_id = filters.UUIDFilter(field_name='software__id')
    software_name = filters.CharFilter(field_name='software__name', lookup_expr='icontains')
    license_key = filters.CharFilter(lookup_expr='icontains')
    status = filters.ChoiceFilter(choices=SoftwareLicense.LICENSE_STATUS_CHOICES)
    vendor_reference = filters.CharFilter(lookup_expr='icontains')

    # Date range filters
    purchase_date_from = filters.DateFilter(field_name='purchase_date', lookup_expr='gte')
    purchase_date_to = filters.DateFilter(field_name='purchase_date', lookup_expr='lte')
    expiry_date_from = filters.DateFilter(field_name='expiry_date', lookup_expr='gte')
    expiry_date_to = filters.DateFilter(field_name='expiry_date', lookup_expr='lte')

    # Cost range filters
    cost_min = filters.NumberFilter(field_name='cost', lookup_expr='gte')
    cost_max = filters.NumberFilter(field_name='cost', lookup_expr='lte')

    # Seat filters
    seats_available = filters.BooleanFilter(method='filter_seats_available')
    seats_min = filters.NumberFilter(field_name='seats', lookup_expr='gte')
    seats_max = filters.NumberFilter(field_name='seats', lookup_expr='lte')

    # Expiring soon filter (within 30 days)
    expiring_soon = filters.BooleanFilter(method='filter_expiring_soon')

    class Meta:
        model = SoftwareLicense
        fields = [
            'software_id', 'software_name', 'license_key', 'status',
            'vendor_reference', 'currency',
            'purchase_date_from', 'purchase_date_to',
            'expiry_date_from', 'expiry_date_to',
            'cost_min', 'cost_max',
            'seats_min', 'seats_max',
            'seats_available', 'expiring_soon',
        ]

    def filter_seats_available(self, queryset, name, value):
        """Filter by available seats."""
        if value is True:
            return queryset.filter(seats_used__lt=models.F('seats'))
        return queryset

    def filter_expiring_soon(self, queryset, name, value):
        """Filter licenses expiring within 30 days."""
        if value is True:
            from django.utils import timezone
            from datetime import timedelta
            thirty_days_from_now = timezone.now().date() + timedelta(days=30)
            return queryset.filter(
                expiry_date__lte=thirty_days_from_now,
                expiry_date__gte=timezone.now().date()
            )
        return queryset


# ========== License Allocation Filter ==========

class LicenseAllocationFilter(BaseModelFilter):
    """Filter for LicenseAllocation queries."""

    license_id = filters.UUIDFilter(field_name='license__id')
    software_name = filters.CharFilter(field_name='license__software__name', lookup_expr='icontains')
    asset_id = filters.UUIDFilter(field_name='asset__id')
    asset_code = filters.CharFilter(field_name='asset__asset_code', lookup_expr='icontains')
    asset_name = filters.CharFilter(field_name='asset__asset_name', lookup_expr='icontains')
    allocated_by_id = filters.UUIDFilter(field_name='allocated_by__id')
    deallocated_by_id = filters.UUIDFilter(field_name='deallocated_by__id')
    is_active = filters.BooleanFilter(method='filter_is_active')

    # Date range filters
    allocated_date_from = filters.DateFilter(field_name='allocated_date', lookup_expr='gte')
    allocated_date_to = filters.DateFilter(field_name='allocated_date', lookup_expr='lte')
    deallocated_date_from = filters.DateFilter(field_name='deallocated_date', lookup_expr='gte')
    deallocated_date_to = filters.DateFilter(field_name='deallocated_date', lookup_expr='lte')

    class Meta:
        model = LicenseAllocation
        fields = [
            'license_id', 'software_name', 'asset_id', 'asset_code', 'asset_name',
            'allocated_by_id', 'deallocated_by_id', 'is_active',
            'allocated_date_from', 'allocated_date_to',
            'deallocated_date_from', 'deallocated_date_to',
        ]

    def filter_is_active(self, queryset, name, value):
        """Filter by active status."""
        if value is True:
            return queryset.filter(deallocated_date__isnull=True)
        elif value is False:
            return queryset.filter(deallocated_date__isnull=False)
        return queryset


# ========== IT Maintenance Record Filter ==========

class ITMaintenanceRecordFilter(BaseModelFilter):
    """Filter for ITMaintenanceRecord queries."""

    asset_id = filters.UUIDFilter(field_name='asset__id')
    asset_code = filters.CharFilter(field_name='asset__asset_code', lookup_expr='icontains')
    asset_name = filters.CharFilter(field_name='asset__asset_name', lookup_expr='icontains')
    maintenance_type = filters.ChoiceFilter(choices=ITMaintenanceRecord.MAINTENANCE_TYPE_CHOICES)
    title = filters.CharFilter(lookup_expr='icontains')
    performed_by_id = filters.UUIDFilter(field_name='performed_by__id')
    vendor = filters.CharFilter(lookup_expr='icontains')

    # Date range filters
    maintenance_date_from = filters.DateFilter(field_name='maintenance_date', lookup_expr='gte')
    maintenance_date_to = filters.DateFilter(field_name='maintenance_date', lookup_expr='lte')

    # Cost range filters
    cost_min = filters.NumberFilter(field_name='cost', lookup_expr='gte')
    cost_max = filters.NumberFilter(field_name='cost', lookup_expr='lte')

    class Meta:
        model = ITMaintenanceRecord
        fields = [
            'asset_id', 'asset_code', 'asset_name', 'maintenance_type', 'title',
            'performed_by_id', 'vendor',
            'maintenance_date_from', 'maintenance_date_to',
            'cost_min', 'cost_max',
        ]


# ========== Configuration Change Filter ==========

class ConfigurationChangeFilter(BaseModelFilter):
    """Filter for ConfigurationChange queries."""

    asset_id = filters.UUIDFilter(field_name='asset__id')
    asset_code = filters.CharFilter(field_name='asset__asset_code', lookup_expr='icontains')
    asset_name = filters.CharFilter(field_name='asset__asset_name', lookup_expr='icontains')
    field_name = filters.CharFilter(lookup_expr='icontains')
    changed_by_id = filters.UUIDFilter(field_name='changed_by__id')

    # Date range filters
    change_date_from = filters.DateFilter(field_name='change_date', lookup_expr='gte')
    change_date_to = filters.DateFilter(field_name='change_date', lookup_expr='lte')

    class Meta:
        model = ConfigurationChange
        fields = [
            'asset_id', 'asset_code', 'asset_name', 'field_name',
            'changed_by_id',
            'change_date_from', 'change_date_to',
        ]
