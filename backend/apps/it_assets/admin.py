"""
Django Admin configuration for IT Assets models.

Provides admin interface for:
- ITAssetInfo: IT-specific hardware/software information
- Software: Software catalog
- SoftwareLicense: License tracking
- LicenseAllocation: License to asset assignments
- ITMaintenanceRecord: IT maintenance activities
- ConfigurationChange: Configuration change audit trail
"""
from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from django.utils.html import format_html

from .models import (
    ITAssetInfo,
    Software,
    SoftwareLicense,
    LicenseAllocation,
    ITMaintenanceRecord,
    ConfigurationChange,
)


@admin.register(ITAssetInfo)
class ITAssetInfoAdmin(admin.ModelAdmin):
    """Admin interface for IT Asset Info."""

    list_display = [
        'asset_link', 'cpu_model', 'ram_capacity', 'disk_capacity',
        'os_name', 'mac_address', 'ip_address', 'antivirus_enabled'
    ]
    list_filter = [
        'disk_type', 'disk_encrypted', 'antivirus_enabled',
        'os_name', 'ram_type'
    ]
    search_fields = [
        'asset__asset_code', 'asset__asset_name', 'cpu_model',
        'mac_address', 'ip_address', 'hostname', 'os_name'
    ]
    readonly_fields = [
        'id', 'created_at', 'updated_at', 'created_by',
        'updated_by', 'deleted_at', 'deleted_by'
    ]
    fieldsets = (
        (_('Asset'), {
            'fields': ('asset', 'organization')
        }),
        (_('CPU Information'), {
            'fields': ('cpu_model', 'cpu_cores', 'cpu_threads')
        }),
        (_('RAM Information'), {
            'fields': ('ram_capacity', 'ram_type', 'ram_slots')
        }),
        (_('Disk Information'), {
            'fields': ('disk_type', 'disk_capacity', 'disk_count')
        }),
        (_('GPU Information'), {
            'fields': ('gpu_model', 'gpu_memory')
        }),
        (_('Network Information'), {
            'fields': ('mac_address', 'ip_address', 'hostname')
        }),
        (_('Operating System'), {
            'fields': ('os_name', 'os_version', 'os_architecture', 'os_license_key')
        }),
        (_('Security'), {
            'fields': ('disk_encrypted', 'antivirus_software', 'antivirus_enabled')
        }),
        (_('Active Directory'), {
            'fields': ('ad_domain', 'ad_computer_name')
        }),
        (_('Audit'), {
            'fields': (
                'id', 'created_at', 'updated_at', 'created_by',
                'updated_by', 'deleted_at', 'deleted_by', 'is_deleted'
            ),
            'classes': ('collapse',)
        }),
    )
    ordering = ['-created_at']

    def asset_link(self, obj):
        """Display clickable link to asset."""
        if obj.asset:
            return format_html(
                '<a href="/admin/assets/asset/{}/change/">{}</a>',
                obj.asset.id,
                obj.asset.asset_name
            )
        return '-'
    asset_link.short_description = _('Asset')


@admin.register(Software)
class SoftwareAdmin(admin.ModelAdmin):
    """Admin interface for Software."""

    list_display = ['name', 'vendor', 'version', 'category', 'license_type_display', 'licenses_count']
    list_filter = ['license_type', 'category', 'vendor']
    search_fields = ['name', 'vendor', 'version', 'category']
    readonly_fields = [
        'id', 'created_at', 'updated_at', 'created_by',
        'updated_by', 'deleted_at', 'deleted_by'
    ]
    fieldsets = (
        (_('Basic Information'), {
            'fields': ('organization', 'name', 'vendor', 'version', 'category')
        }),
        (_('License'), {
            'fields': ('license_type',)
        }),
        (_('Details'), {
            'fields': ('description', 'website_url')
        }),
        (_('Audit'), {
            'fields': (
                'id', 'created_at', 'updated_at', 'created_by',
                'updated_by', 'deleted_at', 'deleted_by', 'is_deleted'
            ),
            'classes': ('collapse',)
        }),
    )
    ordering = ['name', 'version']

    def license_type_display(self, obj):
        return obj.get_license_type_display()
    license_type_display.short_description = _('License Type')

    def licenses_count(self, obj):
        return obj.licenses.count()
    licenses_count.short_description = _('Licenses')


class LicenseAllocationInline(admin.TabularInline):
    """Inline admin for LicenseAllocation."""

    model = LicenseAllocation
    extra = 0
    readonly_fields = ['id', 'allocated_date', 'deallocated_date']
    fields = ['asset', 'allocated_date', 'deallocated_date', 'notes']


@admin.register(SoftwareLicense)
class SoftwareLicenseAdmin(admin.ModelAdmin):
    """Admin interface for Software License."""

    list_display = [
        'software_link', 'license_key', 'seats', 'seats_used',
        'available_seats', 'status_display', 'expiry_date', 'is_expired'
    ]
    list_filter = ['status', 'expiry_date', 'purchase_date', 'software']
    search_fields = ['software__name', 'license_key', 'vendor_reference']
    readonly_fields = [
        'id', 'available_seats', 'is_expired', 'created_at', 'updated_at',
        'created_by', 'updated_by', 'deleted_at', 'deleted_by'
    ]
    inlines = [LicenseAllocationInline]
    fieldsets = (
        (_('Basic Information'), {
            'fields': ('organization', 'software', 'license_key')
        }),
        (_('Seats'), {
            'fields': ('seats', 'seats_used', 'available_seats')
        }),
        (_('Dates'), {
            'fields': ('purchase_date', 'expiry_date')
        }),
        (_('Cost'), {
            'fields': ('cost', 'currency')
        }),
        (_('Status'), {
            'fields': ('status', 'is_expired')
        }),
        (_('Details'), {
            'fields': ('vendor_reference', 'notes')
        }),
        (_('Audit'), {
            'fields': (
                'id', 'created_at', 'updated_at', 'created_by',
                'updated_by', 'deleted_at', 'deleted_by', 'is_deleted'
            ),
            'classes': ('collapse',)
        }),
    )
    ordering = ['-created_at']

    def software_link(self, obj):
        """Display clickable link to software."""
        if obj.software:
            return format_html(
                '<a href="/admin/it_assets/software/{}/change/">{}</a>',
                obj.software.id,
                obj.software.name
            )
        return '-'
    software_link.short_description = _('Software')

    def status_display(self, obj):
        return obj.get_status_display()
    status_display.short_description = _('Status')

    def available_seats(self, obj):
        return obj.available_seats()
    available_seats.short_description = _('Available Seats')

    def is_expired(self, obj):
        return obj.is_expired()
    is_expired.short_description = _('Is Expired')
    is_expired.boolean = True


@admin.register(LicenseAllocation)
class LicenseAllocationAdmin(admin.ModelAdmin):
    """Admin interface for License Allocation."""

    list_display = [
        'license_link', 'asset_link', 'allocated_date',
        'deallocated_date', 'is_active'
    ]
    list_filter = ['allocated_date', 'deallocated_date', 'license__software']
    search_fields = [
        'license__software__name', 'asset__asset_code',
        'asset__asset_name'
    ]
    readonly_fields = [
        'id', 'is_active', 'created_at', 'updated_at',
        'created_by', 'updated_by', 'deleted_at', 'deleted_by'
    ]
    fieldsets = (
        (_('Allocation'), {
            'fields': ('organization', 'license', 'asset')
        }),
        (_('Dates'), {
            'fields': ('allocated_date', 'deallocated_date')
        }),
        (_('Users'), {
            'fields': ('allocated_by', 'deallocated_by')
        }),
        (_('Status'), {
            'fields': ('is_active',)
        }),
        (_('Details'), {
            'fields': ('notes',)
        }),
        (_('Audit'), {
            'fields': (
                'id', 'created_at', 'updated_at', 'created_by',
                'updated_by', 'deleted_at', 'deleted_by', 'is_deleted'
            ),
            'classes': ('collapse',)
        }),
    )
    ordering = ['-allocated_date']

    def license_link(self, obj):
        """Display clickable link to license."""
        if obj.license:
            return format_html(
                '<a href="/admin/it_assets/softwarelicense/{}/change/">{}</a>',
                obj.license.id,
                obj.license.software.name
            )
        return '-'
    license_link.short_description = _('License')

    def asset_link(self, obj):
        """Display clickable link to asset."""
        if obj.asset:
            return format_html(
                '<a href="/admin/assets/asset/{}/change/">{}</a>',
                obj.asset.id,
                obj.asset.asset_name
            )
        return '-'
    asset_link.short_description = _('Asset')

    def is_active(self, obj):
        return obj.is_active()
    is_active.short_description = _('Is Active')
    is_active.boolean = True


@admin.register(ITMaintenanceRecord)
class ITMaintenanceRecordAdmin(admin.ModelAdmin):
    """Admin interface for IT Maintenance Record."""

    list_display = [
        'asset_link', 'maintenance_type_display', 'title',
        'performed_by', 'maintenance_date', 'cost'
    ]
    list_filter = ['maintenance_type', 'maintenance_date', 'vendor']
    search_fields = [
        'asset__asset_code', 'asset__asset_name', 'title',
        'description', 'vendor'
    ]
    readonly_fields = [
        'id', 'created_at', 'updated_at', 'created_by',
        'updated_by', 'deleted_at', 'deleted_by'
    ]
    fieldsets = (
        (_('Basic Information'), {
            'fields': ('organization', 'asset', 'maintenance_type', 'title')
        }),
        (_('Details'), {
            'fields': ('description', 'performed_by', 'vendor')
        }),
        (_('Schedule & Cost'), {
            'fields': ('maintenance_date', 'cost')
        }),
        (_('Notes'), {
            'fields': ('notes',)
        }),
        (_('Audit'), {
            'fields': (
                'id', 'created_at', 'updated_at', 'created_by',
                'updated_by', 'deleted_at', 'deleted_by', 'is_deleted'
            ),
            'classes': ('collapse',)
        }),
    )
    ordering = ['-maintenance_date']

    def asset_link(self, obj):
        """Display clickable link to asset."""
        if obj.asset:
            return format_html(
                '<a href="/admin/assets/asset/{}/change/">{}</a>',
                obj.asset.id,
                obj.asset.asset_name
            )
        return '-'
    asset_link.short_description = _('Asset')

    def maintenance_type_display(self, obj):
        return obj.get_maintenance_type_display()
    maintenance_type_display.short_description = _('Type')


@admin.register(ConfigurationChange)
class ConfigurationChangeAdmin(admin.ModelAdmin):
    """Admin interface for Configuration Change."""

    list_display = [
        'asset_link', 'field_name', 'old_value', 'new_value',
        'changed_by', 'change_date'
    ]
    list_filter = ['field_name', 'change_date']
    search_fields = [
        'asset__asset_code', 'asset__asset_name',
        'field_name', 'old_value', 'new_value', 'change_reason'
    ]
    readonly_fields = [
        'id', 'created_at', 'updated_at', 'created_by',
        'updated_by', 'deleted_at', 'deleted_by'
    ]
    fieldsets = (
        (_('Basic Information'), {
            'fields': ('organization', 'asset', 'field_name')
        }),
        (_('Change'), {
            'fields': ('old_value', 'new_value', 'change_reason')
        }),
        (_('Meta'), {
            'fields': ('changed_by', 'change_date')
        }),
        (_('Audit'), {
            'fields': (
                'id', 'created_at', 'updated_at', 'created_by',
                'updated_by', 'deleted_at', 'deleted_by', 'is_deleted'
            ),
            'classes': ('collapse',)
        }),
    )
    ordering = ['-change_date']

    def asset_link(self, obj):
        """Display clickable link to asset."""
        if obj.asset:
            return format_html(
                '<a href="/admin/assets/asset/{}/change/">{}</a>',
                obj.asset.id,
                obj.asset.asset_name
            )
        return '-'
    asset_link.short_description = _('Asset')
